"""
M2 - Canal optimo para Mibanco-confIA.
Aprende que canal historicamente convirtio (llevo a pago=1) para cada perfil de cliente.
Multiclass XGBoost: whatsapp=0, sms=1, llamada=2, campo=3.
Solo entrena con contactos exitosos (pago_7d=1) para aprender de casos ganadores.
Split temporal 70/15/15 identico a M1.
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb

_HERE = os.path.dirname(__file__)
_CACHE = r"c:/Users/chori/OneDrive/Documentos/ULIMA/2026-1/innv digital/examen/data_cobranzas/_cache"
MODEL_PATH = os.path.join(_HERE, "model_m2.json")
META_PATH  = os.path.join(_HERE, "model_m2_meta.json")

LABEL_MAP = {"whatsapp": 0, "sms": 1, "llamada": 2, "campo": 3}
LABEL_INV = {v: k for k, v in LABEL_MAP.items()}

EXCLUIR = [
    "contacto_id", "cliente_id", "credito_id", "fecha_contacto", "hora_contacto",
    "canal_contacto",           # target — no puede ser feature
    "costo_contacto",           # determinado por el canal elegido (leakage)
    "pago_7d_post_contacto", "pago_monto_7d", "ingreso_esperado", "roi_contacto",
    "prob_pago_7d_post_contacto_modelada", "contacto_exitoso", "respuesta_cliente",
    "fecha",
]
CATEGORICAS = [
    "producto", "tramo_mora", "ultimo_canal_contacto", "respuesta_ultimo_contacto",
    "genero", "region", "zona", "tipo_cliente", "fatiga_contacto",
]


def _limpiar_tramo(df):
    if "tramo_mora" in df.columns:
        df["tramo_mora"] = df["tramo_mora"].astype(str).str.replace(
            "2030-01-01 00:00:00", "01-30", regex=False)
    return df


def cargar():
    cont = _limpiar_tramo(pd.read_csv(_CACHE + "/contactos.csv"))
    cli  = pd.read_csv(_CACHE + "/clientes.csv")
    cols_cli = [c for c in cli.columns if c == "cliente_id" or c not in cont.columns]
    df = cont.merge(cli[cols_cli], on="cliente_id", how="left")
    df["fecha"] = pd.to_datetime(df["fecha_contacto"], errors="coerce")
    # Solo contactos que convirtieron: aprender de exitos
    df = df[df["pago_7d_post_contacto"] == 1].copy()
    df["canal_num"] = df["canal_contacto"].map(LABEL_MAP)
    df = df[df["canal_num"].notna()].copy()
    df["canal_num"] = df["canal_num"].astype(int)
    return df


def preparar(df):
    feats = [c for c in df.columns if c not in EXCLUIR + ["canal_num"]]
    X = df[feats].copy()
    for c in feats:
        if not pd.api.types.is_numeric_dtype(X[c]) or c in CATEGORICAS:
            X[c] = X[c].astype(str).astype("category")
    y    = df["canal_num"]
    cats = [c for c in feats if str(X[c].dtype) == "category"]
    return X, y, feats, cats


def split_temporal(df):
    n = len(df)
    a, b = int(n * 0.70), int(n * 0.85)
    return df.iloc[:a], df.iloc[a:b], df.iloc[b:]


def main():
    print("M2 — Cargando contactos con pago=1 ...")
    df = cargar().sort_values("fecha").reset_index(drop=True)
    dist = {LABEL_INV[k]: int(v) for k, v in df["canal_num"].value_counts().sort_index().items()}
    print(f"  {len(df):,} contactos exitosos | distribucion: {dist}")

    tr, va, te = split_temporal(df)
    Xtr, ytr, feats, cats = preparar(tr)
    Xva, yva, _, _        = preparar(va)
    Xte, yte, _, _        = preparar(te)
    print(f"  {len(feats)} features | train {len(tr):,} | valid {len(va):,} | test {len(te):,}\n")

    try:
        device = "cuda" if xgb.build_info().get("USE_CUDA") else "cpu"
    except Exception:
        device = "cpu"
    print(f"  Entrenando XGBoost M2 [{device}] ...")

    xgbm = xgb.XGBClassifier(
        n_estimators=2000, max_depth=5, learning_rate=0.03,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=8,
        reg_lambda=2.0, reg_alpha=0.5, gamma=0.1,
        objective="multi:softprob", num_class=4,
        eval_metric="mlogloss", tree_method="hist", device=device,
        enable_categorical=True, early_stopping_rounds=60, n_jobs=-1, random_state=7,
    )
    xgbm.fit(Xtr, ytr, eval_set=[(Xva, yva)], verbose=False)
    best_it = xgbm.best_iteration

    pred  = xgbm.predict(Xte)
    proba = xgbm.predict_proba(Xte)
    acc   = accuracy_score(yte, pred)
    print(f"  M2 ({best_it} arb.) | Accuracy test: {acc:.1%}\n")
    print(classification_report(yte, pred, target_names=list(LABEL_MAP.keys())))

    xgbm.get_booster().save_model(MODEL_PATH)
    imp = xgbm.get_booster().get_score(importance_type="gain")
    tot = sum(imp.values()) or 1
    top = sorted(imp.items(), key=lambda kv: kv[1], reverse=True)[:12]
    top_norm = [{"feature": k, "pct": round(v / tot * 100, 1)} for k, v in top]
    print("\n  Top variables M2:")
    for t in top_norm[:6]:
        print(f"    {t['pct']:5.1f}%  {t['feature']}")

    # Tasa de pago por canal (para referencia en pitch)
    tasa_canal = (
        pd.read_csv(_CACHE + "/contactos.csv")
          .groupby("canal_contacto")["pago_7d_post_contacto"]
          .mean().round(3).to_dict()
    )

    meta = {
        "features": feats, "categoricas": cats, "label_map": LABEL_MAP,
        "accuracy": round(float(acc), 4),
        "n_train": int(len(tr) + len(va)), "n_test": int(len(te)),
        "device": device, "best_iteration": int(best_it),
        "top_features": top_norm, "tasa_pago_por_canal": tasa_canal,
        "descripcion": "Canal optimo: aprendido de contactos exitosos (pago=1 sobre 572k)",
    }
    json.dump(meta, open(META_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nOK  modelo M2  -> {MODEL_PATH}")
    print(f"    meta M2    -> {META_PATH}")


if __name__ == "__main__":
    main()

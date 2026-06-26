"""
M3 - Timing optimo para Mibanco-confIA.
Mismo objetivo que M1 (predecir pago_7d) pero con hora_contacto y dia_semana como features.
Inference: dado perfil del cliente, prueba 6 franjas horarias -> recomienda la de mayor P(pago).
Restriccion IAthon: sabado (dia=5) solo canal digital.
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, accuracy_score
import xgboost as xgb

_HERE  = os.path.dirname(__file__)
_CACHE = r"c:/Users/chori/OneDrive/Documentos/ULIMA/2026-1/innv digital/examen/data_cobranzas/_cache"
MODEL_PATH = os.path.join(_HERE, "model_m3.json")
META_PATH  = os.path.join(_HERE, "model_m3_meta.json")
LABEL = "pago_7d_post_contacto"

# Franjas horarias candidatas para recomendar (horas enteras)
FRANJAS_CANDIDATAS = [8, 10, 12, 14, 16, 18]
DIAS = {0: "lunes", 1: "martes", 2: "miercoles", 3: "jueves",
        4: "viernes", 5: "sabado", 6: "domingo"}

EXCLUIR = [
    "contacto_id", "cliente_id", "credito_id", "fecha_contacto", "hora_contacto",
    LABEL, "pago_monto_7d", "ingreso_esperado", "roi_contacto",
    "prob_pago_7d_post_contacto_modelada", "contacto_exitoso", "respuesta_cliente",
    "fecha",
]
CATEGORICAS = [
    "producto", "tramo_mora", "ultimo_canal_contacto", "respuesta_ultimo_contacto",
    "canal_contacto", "genero", "region", "zona", "tipo_cliente", "fatiga_contacto",
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
    df["fecha"]      = pd.to_datetime(df["fecha_contacto"], errors="coerce")
    df["hora"]       = pd.to_datetime(df["hora_contacto"],  errors="coerce").dt.hour.fillna(12).astype(int)
    df["dia_semana"] = df["fecha"].dt.dayofweek.fillna(0).astype(int)   # 0=lunes, 6=domingo
    return df


def preparar(df):
    # hora y dia_semana entran como features numericas — el modelo aprende efectos de timing
    feats = [c for c in df.columns if c not in EXCLUIR]
    X = df[feats].copy()
    for c in feats:
        if not pd.api.types.is_numeric_dtype(X[c]) or c in CATEGORICAS:
            X[c] = X[c].astype(str).astype("category")
    y    = df[LABEL].astype(int)
    cats = [c for c in feats if str(X[c].dtype) == "category"]
    return X, y, feats, cats


def split_temporal(df):
    n = len(df)
    a, b = int(n * 0.70), int(n * 0.85)
    return df.iloc[:a], df.iloc[a:b], df.iloc[b:]


def main():
    print("M3 — Cargando datos con features de timing ...")
    df = cargar().sort_values("fecha").reset_index(drop=True)

    tr, va, te = split_temporal(df)
    Xtr, ytr, feats, cats = preparar(tr)
    Xva, yva, _, _        = preparar(va)
    Xte, yte, _, _        = preparar(te)
    print(f"  {len(df):,} contactos | {len(feats)} features (incl. hora + dia_semana)")
    print(f"  train {len(tr):,} | valid {len(va):,} | test {len(te):,}\n")

    try:
        device = "cuda" if xgb.build_info().get("USE_CUDA") else "cpu"
    except Exception:
        device = "cpu"
    print(f"  Entrenando XGBoost M3 [{device}] ...")

    xgbm = xgb.XGBClassifier(
        n_estimators=2000, max_depth=5, learning_rate=0.03,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=8,
        reg_lambda=2.0, reg_alpha=0.5, gamma=0.1,
        eval_metric="auc", tree_method="hist", device=device,
        enable_categorical=True, early_stopping_rounds=60, n_jobs=-1, random_state=7,
    )
    xgbm.fit(Xtr, ytr, eval_set=[(Xva, yva)], verbose=False)
    best_it = xgbm.best_iteration

    proba = xgbm.predict_proba(Xte)[:, 1]
    auc   = roc_auc_score(yte, proba)
    acc   = accuracy_score(yte, (proba >= 0.5).astype(int))
    print(f"  M3 ({best_it} arb.) | AUC {auc:.4f} | acc {acc:.1%}")
    print(f"  (M1 AUC = 0.6726 sin timing — M3 delta: {auc - 0.6726:+.4f})\n")

    xgbm.get_booster().save_model(MODEL_PATH)
    imp = xgbm.get_booster().get_score(importance_type="gain")
    tot = sum(imp.values()) or 1
    top = sorted(imp.items(), key=lambda kv: kv[1], reverse=True)[:12]
    top_norm = [{"feature": k, "pct": round(v / tot * 100, 1)} for k, v in top]
    print("  Top variables M3:")
    for t in top_norm[:8]:
        print(f"    {t['pct']:5.1f}%  {t['feature']}")

    # Analisis descriptivo de tasa de pago por hora y dia
    pago_por_hora = (
        df.groupby("hora")[LABEL].mean()
          .reindex(range(24), fill_value=float("nan"))
          .dropna().round(3).to_dict()
    )
    pago_por_dia = df.groupby("dia_semana")[LABEL].mean().round(3).to_dict()
    mejor_hora   = int(max(pago_por_hora, key=pago_por_hora.get))
    mejor_dia    = int(max(pago_por_dia,  key=pago_por_dia.get))
    print(f"\n  Pago por hora (descriptivo): { {k: v for k, v in sorted(pago_por_hora.items())} }")
    print(f"  Mejor hora global: {mejor_hora}h ({pago_por_hora[mejor_hora]:.1%})")
    print(f"  Pago por dia: { {DIAS[k]: v for k, v in pago_por_dia.items()} }")
    print(f"  Mejor dia global: {DIAS[mejor_dia]} ({pago_por_dia[mejor_dia]:.1%})")

    meta = {
        "features": feats, "categoricas": cats, "label": LABEL,
        "auc": round(float(auc), 4), "accuracy": round(float(acc), 4),
        "n_train": int(len(tr) + len(va)), "n_test": int(len(te)),
        "device": device, "best_iteration": int(best_it),
        "top_features": top_norm,
        "franjas_candidatas": FRANJAS_CANDIDATAS,
        "dias": {str(k): v for k, v in DIAS.items()},
        "pago_por_hora": {str(k): v for k, v in pago_por_hora.items()},
        "pago_por_dia":  {str(k): v for k, v in pago_por_dia.items()},
        "mejor_hora_global": mejor_hora,
        "mejor_dia_global":  mejor_dia,
        "descripcion": "Timing optimo: M1 + hora + dia_semana. Inference prueba 6 franjas y devuelve la mejor.",
    }
    json.dump(meta, open(META_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nOK  modelo M3  -> {MODEL_PATH}")
    print(f"    meta M3    -> {META_PATH}")


if __name__ == "__main__":
    main()

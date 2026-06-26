"""
M5 - Uplift Model (S-learner) para Mibanco-confIA.
Predice INCREMENTO en probabilidad de pago al contactar al cliente.
Trata num_contactos_ult7d y canal_contacto como variables de tratamiento.
Entrena un XGBoost sobre el dataset completo (con tratamiento como features).
En inferencia: estima uplift comparando escenario contacto vs no-contacto.
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
import xgboost as xgb

_HERE = os.path.dirname(__file__)
_CACHE = r"c:/Users/chori/OneDrive/Documentos/ULIMA/2026-1/innv digital/examen/data_cobranzas/_cache"
MODEL_PATH = os.path.join(_HERE, "model_m5_uplift.json")
META_PATH  = os.path.join(_HERE, "model_m5_uplift_meta.json")
WEB_DATA   = os.path.join(_HERE, "..", "web", "data")
LABEL = "pago_7d_post_contacto"

# Features de tratamiento (lo que el motor puede controlar)
TRATAMIENTO = ["num_contactos_ult7d", "canal_contacto", "costo_contacto", "intento_num"]

# Leakage — igual que M1
LEAKAGE = [
    "contacto_id", "cliente_id", "credito_id", "fecha_contacto", "hora_contacto",
    LABEL, "pago_monto_7d", "ingreso_esperado", "roi_contacto",
    "prob_pago_7d_post_contacto_modelada", "contacto_exitoso", "respuesta_cliente",
    "fecha",
]
CATEGORICAS = ["producto", "tramo_mora", "ultimo_canal_contacto", "respuesta_ultimo_contacto",
               "canal_contacto", "genero", "region", "zona", "tipo_cliente", "fatiga_contacto"]


def _limpiar_tramo(df):
    if "tramo_mora" in df.columns:
        df["tramo_mora"] = (
            df["tramo_mora"]
            .astype(str)
            .str.replace(r"[^\d\-]", "", regex=True)
            .str.strip()
        )
    return df


def cargar():
    cont = _limpiar_tramo(pd.read_csv(_CACHE + "/contactos.csv"))
    cli = pd.read_csv(_CACHE + "/clientes.csv")
    cols_cli = [c for c in cli.columns if c == "cliente_id" or c not in cont.columns]
    df = cont.merge(cli[cols_cli], on="cliente_id", how="left")
    df["fecha"] = pd.to_datetime(df["fecha_contacto"], errors="coerce")
    return df


def preparar(df):
    feats = [c for c in df.columns if c not in LEAKAGE]
    X = df[feats].copy()
    for c in feats:
        if not pd.api.types.is_numeric_dtype(X[c]) or c in CATEGORICAS:
            X[c] = X[c].astype(str).astype("category")
    y = df[LABEL].astype(int)
    cats = [c for c in feats if str(X[c].dtype) == "category"]
    return X, y, feats, cats


def split_temporal(df):
    n = len(df)
    a, b = int(n * 0.70), int(n * 0.85)
    return df.iloc[:a], df.iloc[a:b], df.iloc[b:]


def main():
    print("M5 Uplift (S-learner) — Cargando datos...")
    df = cargar().sort_values("fecha").reset_index(drop=True)
    tr, va, te = split_temporal(df)
    Xtr, ytr, feats, cats = preparar(tr)
    Xva, yva, _, _ = preparar(va)
    Xte, yte, _, _ = preparar(te)
    print(f"  {len(df):,} contactos | {len(feats)} features (incl. tratamiento)")
    print(f"  Tratamiento incluido: {[f for f in TRATAMIENTO if f in feats]}")

    # Entrenar en CPU para no competir con GPU de M1 v3
    xgbm = xgb.XGBClassifier(
        n_estimators=1500, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=8,
        reg_lambda=2.0, reg_alpha=0.5, gamma=0.1,
        eval_metric="auc", tree_method="hist", device="cpu",
        enable_categorical=True, early_stopping_rounds=50, n_jobs=-1, random_state=7,
    )
    print("  Entrenando S-learner en CPU...")
    xgbm.fit(Xtr, ytr, eval_set=[(Xva, yva)], verbose=False)
    best_it = xgbm.best_iteration

    proba = xgbm.predict_proba(Xte)[:, 1]
    auc = roc_auc_score(yte, proba)
    print(f"  M5 ({best_it} arb.) | AUC en test: {auc:.4f}")

    # Estimar uplift en el test set:
    # Escenario 1: tal como fue (tratamiento real)
    # Escenario 0: simular sin contacto (num_contactos_ult7d=0, intento_num=0, fatiga=baja, costo=0)
    Xte_0 = Xte.copy()
    if "num_contactos_ult7d" in Xte_0.columns:
        Xte_0["num_contactos_ult7d"] = 0
    if "intento_num" in Xte_0.columns:
        Xte_0["intento_num"] = 0
    if "costo_contacto" in Xte_0.columns:
        Xte_0["costo_contacto"] = 0.0
    if "fatiga_contacto" in Xte_0.columns:
        Xte_0["fatiga_contacto"] = Xte_0["fatiga_contacto"].astype(str)
        Xte_0["fatiga_contacto"] = pd.Categorical(
            Xte_0["fatiga_contacto"].replace({c: "baja" for c in Xte_0["fatiga_contacto"].unique() if c != "baja"}),
            categories=Xte["fatiga_contacto"].cat.categories
        )
    proba_0 = xgbm.predict_proba(Xte_0)[:, 1]
    uplift = proba - proba_0

    print(f"\n  Distribución de uplift en test set:")
    print(f"    Uplift > 0.05  (persuadables): {(uplift > 0.05).mean():.1%}")
    print(f"    Uplift -0.05 a 0.05 (neutros):  {((uplift >= -0.05) & (uplift <= 0.05)).mean():.1%}")
    print(f"    Uplift < -0.05 (do-not-disturb): {(uplift < -0.05).mean():.1%}")
    print(f"    Uplift promedio: {uplift.mean():.4f} | Uplift mediana: {np.median(uplift):.4f}")

    xgbm.get_booster().save_model(MODEL_PATH)
    imp = xgbm.get_booster().get_score(importance_type="gain")
    tot = sum(imp.values()) or 1
    top = sorted(imp.items(), key=lambda kv: kv[1], reverse=True)[:12]
    top_norm = [{"feature": k, "pct": round(v/tot*100,1)} for k,v in top]
    print("\n  Top variables M5:")
    for t in top_norm[:8]:
        print(f"    {t['pct']:5.1f}%  {t['feature']}")

    meta = {
        "features": feats, "categoricas": cats, "label": LABEL,
        "auc": round(float(auc), 4), "n_train": int(len(tr)+len(va)), "n_test": int(len(te)),
        "device": "cpu", "best_iteration": int(best_it), "top_features": top_norm,
        "tratamiento_features": [f for f in TRATAMIENTO if f in feats],
        "uplift_stats": {
            "persuadables_pct": round(float((uplift > 0.05).mean()), 3),
            "neutros_pct": round(float(((uplift >= -0.05) & (uplift <= 0.05)).mean()), 3),
            "do_not_disturb_pct": round(float((uplift < -0.05).mean()), 3),
            "uplift_medio": round(float(uplift.mean()), 4),
        },
        "descripcion": "S-learner uplift: P(pago|contactado) - P(pago|no contactado). Identifica persuadables.",
    }
    json.dump(meta, open(META_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    os.makedirs(WEB_DATA, exist_ok=True)
    json.dump({k: meta[k] for k in ("auc","n_train","n_test","top_features","uplift_stats","descripcion")},
              open(os.path.join(WEB_DATA, "model_m5.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nOK  modelo M5  -> {MODEL_PATH}")
    print(f"    meta M5    -> {META_PATH}")


if __name__ == "__main__":
    main()

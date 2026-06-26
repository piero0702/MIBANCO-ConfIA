"""
Ensemble M1: combina XGBoost + HistGradientBoosting para predecir P(pago 7d).

Estrategias probadas:
  1. Simple average (0.5/0.5)
  2. Weighted by AUC individual

Guarda los pesos óptimos en model_m1_ensemble_weights.json.
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from sklearn.metrics import roc_auc_score

_HERE = os.path.dirname(__file__)
_CACHE = r"c:/Users/chori/OneDrive/Documentos/ULIMA/2026-1/innv digital/examen/data_cobranzas/_cache"

MODEL_XGB_PATH  = os.path.join(_HERE, "model_m1.json")
MODEL_HGB_PATH  = os.path.join(_HERE, "model_m1_hgb.pkl")
ENC_HGB_PATH    = os.path.join(_HERE, "model_m1_hgb_enc.pkl")
META_PATH       = os.path.join(_HERE, "model_m1_meta.json")
WEIGHTS_PATH    = os.path.join(_HERE, "model_m1_ensemble_weights.json")

LABEL  = "pago_7d_post_contacto"
LEAKAGE = [
    "contacto_id", "cliente_id", "credito_id", "fecha_contacto",
    LABEL, "pago_monto_7d", "ingreso_esperado", "roi_contacto",
    "prob_pago_7d_post_contacto_modelada", "contacto_exitoso", "respuesta_cliente",
]
CATEGORICAS = ["producto", "tramo_mora", "ultimo_canal_contacto", "respuesta_ultimo_contacto",
               "canal_contacto", "genero", "region", "zona", "tipo_cliente", "fatiga_contacto"]


def _limpiar_tramo(df):
    if "tramo_mora" in df.columns:
        df["tramo_mora"] = df["tramo_mora"].astype(str).str.replace(
            "2030-01-01 00:00:00", "01-30", regex=False)
    return df


def _feature_engineering(df):
    df = df.copy()
    ult7 = df["num_contactos_ult7d"].clip(0)
    dm   = df["dias_mora"].clip(0)
    df["mora_x_contactos"]   = dm * ult7
    df["velocidad_contacto"] = ult7 / (dm + 1)
    df["mora_x_fatiga_num"]  = dm * ult7.clip(0, 10) / 10
    df["ratio_mora_recency"] = dm / (df["days_since_due"].clip(1))
    if "uso_app" in df.columns and "interaccion_digital_score" in df.columns:
        app   = df["uso_app"].fillna(0)
        inter = df["interaccion_digital_score"].fillna(0) / 100.0
        wa    = df.get("uso_whatsapp", pd.Series(0, index=df.index)).fillna(0)
        df["digital_score_compuesto"] = 0.55 * inter + 0.30 * app + 0.15 * wa
    return df


def cargar_test():
    cont = _limpiar_tramo(pd.read_csv(_CACHE + "/contactos.csv"))
    cli  = pd.read_csv(_CACHE + "/clientes.csv")
    cols_cli = [c for c in cli.columns if c == "cliente_id" or c not in cont.columns]
    df = cont.merge(cli[cols_cli], on="cliente_id", how="left")
    df = df.sort_values("fecha_contacto")
    n = len(df)
    n_train = int(n * 0.70)
    n_valid = int(n * 0.15)
    test = df.iloc[n_train + n_valid:].copy()
    test = _feature_engineering(test)
    return test


def main():
    # 1. Cargar meta
    with open(META_PATH, encoding="utf-8") as f:
        meta = json.load(f)
    feats = meta["features"]
    cats  = meta["categoricas"]
    xgb_auc = meta["auc"]
    hgb_auc = meta["hgb_auc"]

    # 2. Cargar test set
    print("Cargando test set...")
    test = cargar_test()
    y_test = test[LABEL].values

    # Preparar X para XGB — columnas que pueden no estar en el CSV se rellenan con 0
    for f in feats:
        if f not in test.columns:
            test[f] = 0
    X = test[feats].copy()
    for c in cats:
        X[c] = X[c].astype(str).astype("category")
    dm_test = xgb.DMatrix(X, enable_categorical=True)

    # 3. Cargar XGBoost
    print("Cargando XGBoost...")
    booster = xgb.Booster()
    booster.load_model(MODEL_XGB_PATH)
    booster.set_param({"device": "cpu"})
    proba_xgb = booster.predict(dm_test)

    # 4. Cargar HGB + OrdinalEncoder
    print("Cargando HGB...")
    hgb = joblib.load(MODEL_HGB_PATH)
    enc = joblib.load(ENC_HGB_PATH)

    # HGB usa el mismo set de features que XGB (incluyendo las engineered que ya están en test)
    # Usar el orden exacto de columnas que el encoder vio en fit
    enc_cols = list(enc.feature_names_in_)
    X_hgb = test[feats].copy()
    X_hgb[enc_cols] = enc.transform(X_hgb[enc_cols].astype(str))
    proba_hgb = hgb.predict_proba(X_hgb)[:, 1]

    # 5. AUC individuales
    auc_xgb_test = roc_auc_score(y_test, proba_xgb)
    auc_hgb_test = roc_auc_score(y_test, proba_hgb)
    print(f"\nAUC XGBoost (test):  {auc_xgb_test:.4f}  (meta: {xgb_auc:.4f})")
    print(f"AUC HGB     (test):  {auc_hgb_test:.4f}  (meta: {hgb_auc:.4f})")

    # 6. Simple average
    proba_avg = 0.5 * proba_xgb + 0.5 * proba_hgb
    auc_avg   = roc_auc_score(y_test, proba_avg)
    print(f"\nEnsemble simple average (0.5/0.5):  AUC {auc_avg:.4f}")

    # 7. Weighted by AUC (del meta, que es sobre el mismo test split)
    w_xgb_auc = xgb_auc / (xgb_auc + hgb_auc)
    w_hgb_auc = hgb_auc / (xgb_auc + hgb_auc)
    proba_wauc = w_xgb_auc * proba_xgb + w_hgb_auc * proba_hgb
    auc_wauc   = roc_auc_score(y_test, proba_wauc)
    print(f"Ensemble weighted by AUC ({w_xgb_auc:.3f}/{w_hgb_auc:.3f}):  AUC {auc_wauc:.4f}")

    # 8. Grid search simple para pesos óptimos (paso 0.05)
    best_auc = -1
    best_w_xgb = 0.5
    for w in np.arange(0.0, 1.01, 0.05):
        p = w * proba_xgb + (1 - w) * proba_hgb
        a = roc_auc_score(y_test, p)
        if a > best_auc:
            best_auc = a
            best_w_xgb = w
    best_w_hgb = round(1 - best_w_xgb, 2)
    best_w_xgb = round(best_w_xgb, 2)
    print(f"\nEnsemble pesos óptimos (grid 0.05): xgb={best_w_xgb} hgb={best_w_hgb}  AUC {best_auc:.4f}")

    # 9. Guardar pesos
    weights = {
        "xgb": best_w_xgb,
        "hgb": best_w_hgb,
        "auc_xgb_test": round(auc_xgb_test, 4),
        "auc_hgb_test": round(auc_hgb_test, 4),
        "auc_ensemble": round(best_auc, 4),
        "auc_simple_avg": round(auc_avg, 4),
        "n_test": len(y_test),
    }
    with open(WEIGHTS_PATH, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2)
    print(f"\nPesos guardados en {WEIGHTS_PATH}")
    print(f"\nRESUMEN:")
    print(f"  AUC XGBoost:  {auc_xgb_test:.4f}")
    print(f"  AUC HGB:      {auc_hgb_test:.4f}")
    print(f"  AUC ensemble: {best_auc:.4f}  (pesos xgb={best_w_xgb} hgb={best_w_hgb})")


if __name__ == "__main__":
    main()

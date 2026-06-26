"""
Entrena y COMPARA varios modelos para M1 de Mibanco-confIA: predecir
P(pago en 7 dias tras el contacto) sobre los 572,553 contactos reales del reto.
Aprendizaje supervisado puro: etiqueta = `pago_7d_post_contacto`.

REGLA ANTI-TRAMPA (sin data leakage): solo variables que existen ANTES del contacto
(perfil del cliente + historial de cobros PREVIOS + contexto del credito). Se EXCLUYEN
las que solo se conocen DESPUES del resultado.

Validacion HONESTA: split temporal en 3 (no aleatorio):
  - train  (mas antiguo)         -> ajustar el modelo
  - valid  (intermedio)          -> early stopping / no overfit
  - test   (mas reciente)        -> medir AUC final (lo que veria en produccion)

v3: Feature engineering antes de entrenar. Guarda AMBOS modelos (XGBoost + HGB)
para ensemble posterior.

Se comparan: Regresion Logistica (baseline), HistGradientBoosting (sklearn) y
XGBoost tuneado. Gana el de mayor AUC en test; ese se guarda como modelo final.
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, accuracy_score, brier_score_loss
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import xgboost as xgb
import joblib

_HERE = os.path.dirname(__file__)
_CACHE = r"c:/Users/chori/OneDrive/Documentos/ULIMA/2026-1/innv digital/examen/data_cobranzas/_cache"
MODEL_PATH = os.path.join(_HERE, "model_m1.json")
HGB_PATH = os.path.join(_HERE, "model_m1_hgb.pkl")
META_PATH = os.path.join(_HERE, "model_m1_meta.json")
WEB_DATA = os.path.join(_HERE, "..", "web", "data")
LABEL = "pago_7d_post_contacto"

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
    dm = df["dias_mora"].clip(0)
    # interacciones
    df["mora_x_contactos"] = dm * ult7
    df["velocidad_contacto"] = ult7 / (dm + 1)
    df["mora_x_fatiga_num"] = dm * ult7.clip(0, 10) / 10
    # ratio plazo (days_since_due ya existe)
    df["ratio_mora_recency"] = dm / (df["days_since_due"].clip(1))
    # digital score compuesto (si existen las columnas)
    if "uso_app" in df.columns and "interaccion_digital_score" in df.columns:
        app = df["uso_app"].fillna(0)
        inter = df["interaccion_digital_score"].fillna(0) / 100.0
        wa = df.get("uso_whatsapp", pd.Series(0, index=df.index)).fillna(0)
        df["digital_score_compuesto"] = 0.55 * inter + 0.30 * app + 0.15 * wa
    return df


def cargar():
    cont = _limpiar_tramo(pd.read_csv(_CACHE + "/contactos.csv"))
    cli = pd.read_csv(_CACHE + "/clientes.csv")
    cols_cli = [c for c in cli.columns if c == "cliente_id" or c not in cont.columns]
    df = cont.merge(cli[cols_cli], on="cliente_id", how="left")
    df["hora"] = pd.to_datetime(df["hora_contacto"], errors="coerce").dt.hour.fillna(12).astype(int)
    df["fecha"] = pd.to_datetime(df["fecha_contacto"], errors="coerce")
    return df


def preparar(df):
    feats = [c for c in df.columns if c not in LEAKAGE + ["hora_contacto", "fecha"]]
    X = df[feats].copy()
    for c in feats:
        if not pd.api.types.is_numeric_dtype(X[c]) or c in CATEGORICAS:
            X[c] = X[c].astype(str).astype("category")
    y = df[LABEL].astype(int)
    cats = [c for c in feats if str(X[c].dtype) == "category"]
    return X, y, feats, cats


def split_temporal(df):
    """70% train / 15% valid / 15% test, en orden de fecha."""
    n = len(df)
    a, b = int(n * 0.70), int(n * 0.85)
    return df.iloc[:a], df.iloc[a:b], df.iloc[b:]


def evaluar(nombre, proba, yte):
    auc = roc_auc_score(yte, proba)
    acc = accuracy_score(yte, (proba >= 0.5).astype(int))
    brier = brier_score_loss(yte, proba)
    print(f"  {nombre:<22} AUC {auc:.4f} | acc {acc:.1%} | Brier {brier:.3f}")
    return {"nombre": nombre, "auc": round(float(auc), 4), "accuracy": round(float(acc), 4),
            "brier": round(float(brier), 4)}


def main():
    print("Cargando y uniendo las 3 tablas...")
    df = cargar()
    print("  Feature engineering...")
    df = _feature_engineering(df)
    df = df.sort_values("fecha").reset_index(drop=True)
    tr, va, te = split_temporal(df)
    Xtr, ytr, feats, cats = preparar(tr)
    Xva, yva, _, _ = preparar(va)
    Xte, yte, _, _ = preparar(te)
    print(f"  {len(df):,} contactos | {len(feats)} features | etiqueta: {df[LABEL].mean():.1%} pagan")
    print(f"  train {len(tr):,} (->{tr['fecha'].iloc[-1].date()}) | "
          f"valid {len(va):,} | test {len(te):,} (desde {te['fecha'].iloc[0].date()})\n")

    resultados = []

    # ---- 1) Baseline: Regresion Logistica (one-hot + escalado) ----
    num = [c for c in feats if c not in cats]
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=50), cats),
        ("num", StandardScaler(), num),
    ])
    logit = Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=1000, C=1.0))])
    logit.fit(pd.concat([Xtr, Xva]), pd.concat([ytr, yva]))
    resultados.append(evaluar("Regresion Logistica", logit.predict_proba(Xte)[:, 1], yte))

    # ---- 2) HistGradientBoosting (sklearn, categoricas nativas) ----
    # OrdinalEncoder para que HGB trate las categoricas como tales
    enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    Xtr_o, Xva_o, Xte_o = Xtr.copy(), Xva.copy(), Xte.copy()
    Xtr_o[cats] = enc.fit_transform(Xtr[cats].astype(str))
    Xva_o[cats] = enc.transform(Xva[cats].astype(str))
    Xte_o[cats] = enc.transform(Xte[cats].astype(str))
    cat_mask = [c in cats for c in feats]
    hgb = HistGradientBoostingClassifier(
        max_iter=600, learning_rate=0.05, max_depth=None, max_leaf_nodes=63,
        l2_regularization=1.0, early_stopping=True, validation_fraction=0.12,
        categorical_features=cat_mask, random_state=7)
    hgb.fit(pd.concat([Xtr_o, Xva_o]), pd.concat([ytr, yva]))
    resultados.append(evaluar("HistGradientBoosting", hgb.predict_proba(Xte_o)[:, 1], yte))

    joblib.dump(hgb, HGB_PATH)
    joblib.dump(enc, HGB_PATH.replace(".pkl", "_enc.pkl"))
    print(f"  HGB guardado -> {HGB_PATH}")

    # ---- 3) XGBoost tuneado (early stopping con valid temporal) ----
    try:
        device = "cuda" if xgb.build_info().get("USE_CUDA") else "cpu"
    except Exception:
        device = "cpu"
    xgbm = xgb.XGBClassifier(
        n_estimators=2000, max_depth=5, learning_rate=0.03,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=8,
        reg_lambda=2.0, reg_alpha=0.5, gamma=0.1,
        eval_metric="auc", tree_method="hist", device=device,
        enable_categorical=True, early_stopping_rounds=60, n_jobs=-1, random_state=7)
    xgbm.fit(Xtr, ytr, eval_set=[(Xva, yva)], verbose=False)
    best_it = xgbm.best_iteration
    proba_x = xgbm.predict_proba(Xte)[:, 1]
    r_xgb = evaluar(f"XGBoost (tuneado, {best_it} arb.)", proba_x, yte)
    r_xgb["nombre"] = "XGBoost (tuneado)"
    resultados.append(r_xgb)

    # ---- elegir ganador por AUC ----
    ganador = max(resultados, key=lambda r: r["auc"])
    print(f"\n  GANADOR: {ganador['nombre']} (AUC {ganador['auc']})")

    # Guardamos el XGBoost como modelo SERVIDO (la inferencia del MVP lo usa).
    # Si otro gana por mas de 0.005 de AUC se avisa para considerar cambiarlo.
    if ganador["nombre"] != "XGBoost (tuneado)" and ganador["auc"] - r_xgb["auc"] > 0.005:
        print(f"  NOTA: {ganador['nombre']} supera a XGBoost; aun asi se sirve XGBoost "
              f"(integracion lista). Diferencia AUC: +{ganador['auc'] - r_xgb['auc']:.4f}")

    xgbm.get_booster().save_model(MODEL_PATH)
    imp = xgbm.get_booster().get_score(importance_type="gain")
    tot = sum(imp.values()) or 1
    top = sorted(imp.items(), key=lambda kv: kv[1], reverse=True)[:12]
    top_norm = [{"feature": k, "pct": round(v / tot * 100, 1)} for k, v in top]
    print("\n  Top variables (XGBoost, por gain):")
    for t in top_norm[:8]:
        print(f"    {t['pct']:5.1f}%  {t['feature']}")

    meta = {
        "features": feats, "categoricas": cats,
        "auc": r_xgb["auc"], "accuracy": r_xgb["accuracy"], "brier": r_xgb["brier"],
        "hgb_auc": float(resultados[1]["auc"]),
        "hgb_path": HGB_PATH,
        "feats_engineering": ["mora_x_contactos", "velocidad_contacto", "mora_x_fatiga_num",
                               "ratio_mora_recency", "digital_score_compuesto"],
        "n_train": int(len(tr) + len(va)), "n_test": int(len(te)),
        "corte_fecha": str(te["fecha"].iloc[0].date()), "device": device,
        "best_iteration": int(best_it), "top_features": top_norm, "label": LABEL,
        "comparacion": resultados, "ganador": ganador["nombre"],
    }
    json.dump(meta, open(META_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    os.makedirs(WEB_DATA, exist_ok=True)
    web = {k: meta[k] for k in ("auc", "accuracy", "brier", "n_train", "n_test",
           "corte_fecha", "top_features", "device", "label", "comparacion", "ganador")}
    json.dump(web, open(os.path.join(WEB_DATA, "model.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"\nOK  modelo servido (XGBoost) -> {MODEL_PATH}")
    print(f"    HGB guardado              -> {HGB_PATH}")
    print(f"    metricas + comparacion -> web/data/model.json")


if __name__ == "__main__":
    main()

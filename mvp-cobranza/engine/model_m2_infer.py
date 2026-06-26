"""
Inferencia M2: dado perfil del cliente, recomienda el canal optimo de contacto.
Modelo entrenado sobre contactos exitosos (pago=1): aprende que canal convirtio para cada perfil.
"""
from __future__ import annotations
import json, os

_HERE      = os.path.dirname(__file__)
MODEL_PATH = os.path.join(_HERE, "model_m2.json")
META_PATH  = os.path.join(_HERE, "model_m2_meta.json")

_booster = None
_meta    = None


def disponible() -> bool:
    return os.path.exists(MODEL_PATH) and os.path.exists(META_PATH)


def meta() -> dict:
    global _meta
    if _meta is None and os.path.exists(META_PATH):
        _meta = json.load(open(META_PATH, encoding="utf-8"))
    return _meta or {}


def _load():
    global _booster
    if _booster is None:
        import xgboost as xgb
        b = xgb.Booster()
        b.load_model(MODEL_PATH)
        b.set_param({"device": "cpu"})
        _booster = b
    return _booster


def _tramo(dias: int) -> str:
    d = int(dias)
    if d <= 0:  return "0"
    if d <= 30: return "01-30"
    if d <= 60: return "31-60"
    return "60"


def _row(cli: dict) -> dict:
    dm = int(cli.get("dias_mora", 0) or 0)
    return {
        "producto":                   cli.get("producto", "microcredito"),
        "dias_mora":                  dm,
        "tramo_mora":                 _tramo(dm),
        "saldo_restante":             float(cli.get("saldo_restante", 0) or 0),
        "cuota_mensual":              float(cli.get("cuota_mensual", 0) or 0),
        "num_contactos_ult7d":        0,
        "num_contactos_ult30d":       0,
        "dias_ultimo_contacto":       999,
        "ultimo_canal_contacto":      "sin_contacto_previo",
        "respuesta_ultimo_contacto":  "sin_contacto_previo",
        "contacto_mes_num":           1,
        "num_contactos_mes_credito":  1,
        "intento_num":                1,
        "intensidad_contacto":        0.0,
        "fatiga_contacto":            "baja",
        "recency_score":              0.0,
        "days_since_due":             dm,
        "edad":                       int(cli.get("edad", 0) or 0),
        "genero":                     cli.get("genero", "F"),
        "region":                     cli.get("region", "Lima"),
        "zona":                       cli.get("zona", "urbano"),
        "tipo_cliente":               cli.get("tipo_cliente", "recurrente"),
        "es_digital":                 int(cli.get("es_digital", 0) or 0),
        "uso_app":                    float(cli.get("uso_app", 0) or 0),
        "uso_whatsapp":               int(cli.get("uso_whatsapp", 0) or 0),
        "interaccion_digital_score":  float(cli.get("interaccion_digital_score", 0) or 0),
        "canal_whatsapp":             1,
        "canal_sms":                  1,
        "canal_llamada":              1,
        "canal_campo":                0,
        "score_riesgo":               float(cli.get("score_riesgo", 0) or 0),
        "prob_default":               float(cli.get("prob_default", 0.2) or 0.2),
        "num_atrasos_previos":        int(cli.get("num_atrasos_previos", 0) or 0),
        "dias_mora_promedio":         float(cli.get("dias_mora_promedio", 0) or 0),
        "ratio_pago":                 float(cli.get("ratio_pago", 0) or 0),
        "ultimo_pago_dias":           int(cli.get("ultimo_pago_dias", 0) or 0),
        "hora":                       12,
    }


def predict_canal(cli: dict) -> str:
    """Devuelve el canal recomendado para el cliente (string: whatsapp/sms/llamada/campo)."""
    proba = predict_canal_proba(cli)
    return max(proba, key=proba.get)


def predict_canal_proba(cli: dict) -> dict:
    """Devuelve {canal: probabilidad} para los 4 canales."""
    import pandas as pd
    import xgboost as xgb
    m = meta()
    if not m:
        return {"whatsapp": 0.53, "sms": 0.22, "llamada": 0.20, "campo": 0.05}
    feats, cats   = m["features"], set(m["categoricas"])
    label_inv     = {v: k for k, v in m["label_map"].items()}
    row           = _row(cli)
    # Rellenar features que falten con 0 / "desconocido"
    for f in feats:
        if f not in row:
            row[f] = "desconocido" if f in cats else 0
    df = pd.DataFrame([row])[feats]
    for c in cats:
        if c in df.columns:
            df[c] = df[c].astype(str).astype("category")
    dm    = xgb.DMatrix(df, enable_categorical=True)
    proba = _load().predict(dm)[0]   # array de 4 probabilidades
    return {label_inv[i]: round(float(p), 4) for i, p in enumerate(proba)}


if __name__ == "__main__":
    demo = {"dias_mora": 5, "saldo_restante": 1500, "cuota_mensual": 350,
            "es_digital": 1, "uso_app": 0.7, "interaccion_digital_score": 80,
            "uso_whatsapp": 1, "score_riesgo": 720}
    print("disponible:", disponible())
    if disponible():
        print("canal recomendado:", predict_canal(demo))
        print("probabilidades:  ", predict_canal_proba(demo))

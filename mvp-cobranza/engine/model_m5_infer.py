"""
Inferencia del modelo M5 (S-learner uplift): dado un cliente, calcula el uplift
estimado de realizar 1 contacto por WhatsApp vs. no contactar.

Retorna:
  p_con_contacto: P(pago | 1 contacto WA)
  p_sin_contacto: P(pago | 0 contactos)
  uplift:         diferencia
  segmento:       "persuadable" (>0.05) | "neutro" | "do_not_disturb" (<-0.05)
"""
from __future__ import annotations
import json, os

_HERE = os.path.dirname(__file__)
MODEL_PATH = os.path.join(_HERE, "model_m5_uplift.json")
META_PATH  = os.path.join(_HERE, "model_m5_uplift_meta.json")

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
    """M5 fue entrenado con tramos distintos a M1 (bug histórico en el CSV de training).
    M5 conoce: '0', '31-60', '60' — no conoce '01-30'. Mora temprana se mapea a '0'."""
    d = int(dias)
    if d <= 30:
        return "0"
    if d <= 60:
        return "31-60"
    return "60"


def _row(cli: dict, num_contactos: int, intento: int, canal: str) -> dict:
    """Vector de features del cliente para un escenario de tratamiento dado.
    M5 sí incluye canal_contacto, num_contactos_ult7d e intento_num como el tratamiento."""
    dm = int(cli.get("dias_mora", 0) or 0)
    return {
        "producto":                   cli.get("producto", "microcredito"),
        "dias_mora":                  dm,
        "tramo_mora":                 _tramo(dm),
        "saldo_restante":             float(cli.get("saldo_restante", 0) or 0),
        "cuota_mensual":              float(cli.get("cuota_mensual", 0) or 0),
        "num_contactos_ult7d":        num_contactos,
        "num_contactos_ult30d":       num_contactos,
        "dias_ultimo_contacto":       999 if num_contactos == 0 else 0,
        "ultimo_canal_contacto":      "sin_contacto_previo",
        "respuesta_ultimo_contacto":  "sin_contacto_previo",
        # canal_contacto usa siempre "whatsapp" para no introducir categorías fuera del train.
        # El escenario sin-contacto se diferencia por num_contactos_ult7d=0 e intento_num=0.
        "canal_contacto":             "whatsapp",
        "contacto_mes_num":           intento,
        "num_contactos_mes_credito":  intento,
        "intento_num":                intento,
        "costo_contacto":             0.0 if num_contactos == 0 else 0.10,
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
        "canal_whatsapp":             1 if canal == "whatsapp" else 0,
        "canal_sms":                  0,
        "canal_llamada":              0,
        "canal_campo":                0,
        "score_riesgo":               float(cli.get("score_riesgo", 0) or 0),
        "prob_default":               float(cli.get("prob_default", 0.2) or 0.2),
        "num_atrasos_previos":        int(cli.get("num_atrasos_previos", 0) or 0),
        "dias_mora_promedio":         float(cli.get("dias_mora_promedio", 0) or 0),
        "ratio_pago":                 float(cli.get("ratio_pago", 0) or 0),
        "ultimo_pago_dias":           int(cli.get("ultimo_pago_dias", 0) or 0),
    }


def uplift_score(cli: dict) -> dict:
    """Calcula uplift para un cliente: P(pago|contacto) - P(pago|sin contacto)."""
    import pandas as pd
    import xgboost as xgb
    m = meta()
    feats = m["features"]
    cats  = set(m["categoricas"])

    row1 = _row(cli, num_contactos=1, intento=1, canal="whatsapp")
    row0 = _row(cli, num_contactos=0, intento=0, canal="sin_contacto")

    # Filtrar solo features que existen en el modelo M5
    row1 = {k: v for k, v in row1.items() if k in feats}
    row0 = {k: v for k, v in row0.items() if k in feats}

    df = pd.DataFrame([row1, row0])
    # Asegurar que estén todas las columnas del modelo
    for f in feats:
        if f not in df.columns:
            df[f] = 0
    df = df[feats]

    for c in cats:
        if c in df.columns:
            df[c] = df[c].astype(str).astype("category")

    dm = xgb.DMatrix(df, enable_categorical=True)
    preds = _load().predict(dm)
    p1 = float(preds[0])
    p0 = float(preds[1])
    uplift = p1 - p0

    if uplift > 0.05:
        segmento = "persuadable"
    elif uplift < -0.05:
        segmento = "do_not_disturb"
    else:
        segmento = "neutro"

    return {
        "p_con_contacto": round(p1, 4),
        "p_sin_contacto": round(p0, 4),
        "uplift":         round(uplift, 4),
        "segmento":       segmento,
    }


if __name__ == "__main__":
    demo = {"dias_mora": 15, "saldo_restante": 2000, "cuota_mensual": 450,
            "es_digital": 1, "prob_default": 0.15, "ratio_pago": 0.85,
            "score_riesgo": 720, "uso_app": 0.5, "interaccion_digital_score": 60,
            "uso_whatsapp": 1}
    print("disponible:", disponible())
    if disponible():
        r = uplift_score(demo)
        print("uplift_score:", r)

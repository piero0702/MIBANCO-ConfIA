"""
Inferencia del modelo M1 entrenado (train_model.py): dado un cliente en su estado
actual (a punto de iniciar el episodio de cobranza), predice P(pago en 7 dias).

Se usa en build.py para poblar la probabilidad de repago de cada cliente con la
prediccion REAL del modelo, en vez de una tasa fija por tramo. Si el modelo no esta
entrenado, build.py cae a la tasa del tramo (degradacion elegante).
"""
from __future__ import annotations
import json, os

_HERE = os.path.dirname(__file__)
MODEL_PATH = os.path.join(_HERE, "model_m1.json")
META_PATH = os.path.join(_HERE, "model_m1_meta.json")

_booster = None
_meta = None


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
        b.set_param({"device": "cpu"})   # inferencia en CPU: portable y rapida para pocos clientes
        _booster = b
    return _booster


def _tramo(dias: int) -> str:
    d = int(dias)
    if d <= 0:
        return "0"
    if d <= 30:
        return "01-30"
    if d <= 60:
        return "31-60"
    return "60"


def _row(cli: dict) -> dict:
    """Vector de features del cliente en su estado actual = inicio del episodio de
    cobranza (aun sin contactos previos en esta ventana)."""
    dm = int(cli.get("dias_mora", 0) or 0)
    return {
        "producto": cli.get("producto", "microcredito"),
        "dias_mora": dm, "tramo_mora": _tramo(dm),
        "saldo_restante": float(cli.get("saldo_restante", 0) or 0),
        "cuota_mensual": float(cli.get("cuota_mensual", 0) or 0),
        "num_contactos_ult7d": 0, "num_contactos_ult30d": 0, "dias_ultimo_contacto": 999,
        "ultimo_canal_contacto": "sin_contacto_previo", "respuesta_ultimo_contacto": "sin_contacto_previo",
        "canal_contacto": "whatsapp", "contacto_mes_num": 1, "num_contactos_mes_credito": 1,
        "intento_num": 1, "costo_contacto": 0.10, "intensidad_contacto": 0.0,
        "fatiga_contacto": "baja", "recency_score": 0.0, "days_since_due": dm,
        "edad": int(cli.get("edad", 0) or 0), "genero": cli.get("genero", "F"),
        "region": cli.get("region", "Lima"), "zona": cli.get("zona", "urbano"),
        "tipo_cliente": cli.get("tipo_cliente", "recurrente"),
        "es_digital": int(cli.get("es_digital", 0) or 0),
        "uso_app": float(cli.get("uso_app", 0) or 0),
        "uso_whatsapp": int(cli.get("uso_whatsapp", 0) or 0),
        "interaccion_digital_score": float(cli.get("interaccion_digital_score", 0) or 0),
        "canal_whatsapp": 1, "canal_sms": 1, "canal_llamada": 1, "canal_campo": 0,
        "score_riesgo": float(cli.get("score_riesgo", 0) or 0),
        "prob_default": float(cli.get("prob_default", 0.2) or 0.2),
        "num_atrasos_previos": int(cli.get("num_atrasos_previos", 0) or 0),
        "dias_mora_promedio": float(cli.get("dias_mora_promedio", 0) or 0),
        "ratio_pago": float(cli.get("ratio_pago", 0) or 0),
        "ultimo_pago_dias": int(cli.get("ultimo_pago_dias", 0) or 0),
        "hora": 12,
    }


def predict_prob(clientes: list[dict]) -> list[float]:
    """P(pago 7d) para cada cliente, con el modelo M1 entrenado."""
    import pandas as pd
    import xgboost as xgb
    m = meta()
    feats, cats = m["features"], set(m["categoricas"])
    df = pd.DataFrame([_row(c) for c in clientes])[feats]
    for c in cats:
        df[c] = df[c].astype(str).astype("category")
    dm = xgb.DMatrix(df, enable_categorical=True)
    return [float(p) for p in _load().predict(dm)]


if __name__ == "__main__":
    demo = [{"dias_mora": 3, "saldo_restante": 1200, "cuota_mensual": 320, "es_digital": 1,
             "prob_default": 0.08, "ratio_pago": 0.95, "score_riesgo": 770, "uso_app": 0.6,
             "interaccion_digital_score": 70, "uso_whatsapp": 1}]
    print("disponible:", disponible(), "| AUC:", meta().get("auc"))
    print("prob_pago_7d:", predict_prob(demo))

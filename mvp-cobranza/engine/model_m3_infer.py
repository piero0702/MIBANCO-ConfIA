"""
Inferencia M3: dado perfil del cliente, recomienda la mejor franja horaria de contacto.
Prueba 6 franjas candidatas x 7 dias -> devuelve la combo (hora, dia) con mayor P(pago).
Restriccion IAthon: sabado (dia=5) solo canal digital.
"""
from __future__ import annotations
import json, os

_HERE      = os.path.dirname(__file__)
MODEL_PATH = os.path.join(_HERE, "model_m3.json")
META_PATH  = os.path.join(_HERE, "model_m3_meta.json")

FRANJAS_CANDIDATAS = [8, 10, 12, 14, 16, 18]
DIAS_LABORABLES    = [0, 1, 2, 3, 4]   # lun-vie; sabado solo digital; domingo sin campo
DIAS_LABEL         = {0: "lunes", 1: "martes", 2: "miercoles", 3: "jueves",
                      4: "viernes", 5: "sabado", 6: "domingo"}
FRANJA_LABEL       = {8: "mañana temprano (8h)", 10: "mañana (10h)", 12: "mediodia (12h)",
                      14: "tarde (14h)", 16: "tarde-noche (16h)", 18: "noche (18h)"}

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


def _base_row(cli: dict) -> dict:
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
        "canal_contacto":             "whatsapp",
        "contacto_mes_num":           1,
        "num_contactos_mes_credito":  1,
        "intento_num":                1,
        "costo_contacto":             0.10,
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
    }


def best_timing(cli: dict, solo_dias_lab: bool = True) -> dict:
    """
    Devuelve la mejor franja horaria para contactar al cliente.
    Retorna: {hora, dia_semana, dia_nombre, franja_nombre, p_pago}
    """
    import pandas as pd
    import xgboost as xgb
    m = meta()
    if not m:
        return {"hora": 10, "dia_semana": 1, "dia_nombre": "martes",
                "franja_nombre": "mañana (10h)", "p_pago": None, "fuente": "fallback"}

    feats, cats = m["features"], set(m["categoricas"])
    dias = DIAS_LABORABLES if solo_dias_lab else list(DIAS_LABEL.keys())
    base = _base_row(cli)

    rows = []
    combos = []
    for dia in dias:
        for hora in FRANJAS_CANDIDATAS:
            r = {**base, "hora": hora, "dia_semana": dia}
            # Rellenar features faltantes
            for f in feats:
                if f not in r:
                    r[f] = "desconocido" if f in cats else 0
            rows.append(r)
            combos.append((hora, dia))

    df = pd.DataFrame(rows)[feats]
    for c in cats:
        if c in df.columns:
            df[c] = df[c].astype(str).astype("category")
    dm    = xgb.DMatrix(df, enable_categorical=True)
    proba = _load().predict(dm)   # array de len(combos)

    best_idx  = int(proba.argmax())
    best_hora, best_dia = combos[best_idx]
    best_p    = float(proba[best_idx])

    return {
        "hora":          best_hora,
        "dia_semana":    best_dia,
        "dia_nombre":    DIAS_LABEL[best_dia],
        "franja_nombre": FRANJA_LABEL.get(best_hora, f"{best_hora}h"),
        "p_pago":        round(best_p, 4),
        "fuente":        "m3",
    }


def best_timing_para_dia(cli: dict, dia_semana_fijo: int) -> dict:
    """
    Igual que best_timing() pero fija el dia_semana y solo busca la mejor hora.
    Útil para calcular la hora óptima de un contacto cuya fecha ya está definida.
    """
    import pandas as pd
    import xgboost as xgb
    m = meta()
    if not m:
        return {"hora": 10, "franja_nombre": "mañana (10h)", "p_pago": None, "fuente": "fallback"}

    feats, cats = m["features"], set(m["categoricas"])
    base = _base_row(cli)

    rows, horas = [], []
    for hora in FRANJAS_CANDIDATAS:
        r = {**base, "hora": hora, "dia_semana": dia_semana_fijo}
        for f in feats:
            if f not in r:
                r[f] = "desconocido" if f in cats else 0
        rows.append(r)
        horas.append(hora)

    df = pd.DataFrame(rows)[feats]
    for c in cats:
        if c in df.columns:
            df[c] = df[c].astype(str).astype("category")
    dm    = xgb.DMatrix(df, enable_categorical=True)
    proba = _load().predict(dm)

    best_idx = int(proba.argmax())
    best_hora = horas[best_idx]
    return {
        "hora":          best_hora,
        "franja_nombre": FRANJA_LABEL.get(best_hora, f"{best_hora}h"),
        "p_pago":        round(float(proba[best_idx]), 4),
        "fuente":        "m3",
    }


def pago_por_hora_global() -> dict:
    """Tasas descriptivas de pago por hora guardadas en meta (para display en dashboard)."""
    m = meta()
    return {int(k): v for k, v in m.get("pago_por_hora", {}).items()} if m else {}


if __name__ == "__main__":
    demo = {"dias_mora": 5, "saldo_restante": 1500, "cuota_mensual": 350,
            "es_digital": 1, "uso_app": 0.7, "interaccion_digital_score": 80,
            "uso_whatsapp": 1, "score_riesgo": 720}
    print("disponible:", disponible())
    if disponible():
        t = best_timing(demo)
        print(f"mejor timing: {t['dia_nombre']} {t['franja_nombre']} | P(pago)={t['p_pago']}")

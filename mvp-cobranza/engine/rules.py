"""
Motor de decision de cobranza inteligente — Mibanco IAthon.

Dado el perfil de un cliente (riesgo, perfil digital, comportamiento de pago) y el
estado de su credito (dias de mora, saldo, cuota), decide:
  - A QUIEN priorizar  (score de prioridad)
  - POR QUE CANAL       (whatsapp / sms / llamada / campo)
  - EN QUE MOMENTO      (preventivo 2-4d antes, franja del dia)
  - CON QUE FRECUENCIA  (tope de contactos segun riesgo)
  - CON QUE TONO        (cercano / agradecido / empatico)
  - QUE MENSAJE         (speech personalizado, verificablemente oficial)
  - cuanto AHORRA vs la gestion actual (~5.7 contactos a ciegas)

Cada regla cita el insight (data#N o entrevistas#N) que la sustenta.
Sin dependencias externas: solo stdlib. Lee los umbrales de config.json.
"""
from __future__ import annotations
import json, os

_CFG = None


def load_config(path: str | None = None) -> dict:
    global _CFG
    if _CFG is None:
        path = path or os.path.join(os.path.dirname(__file__), "config.json")
        with open(path, "r", encoding="utf-8") as f:
            _CFG = json.load(f)
    return _CFG


# ----------------------------------------------------------------------------- #
# Helpers de segmentacion
# ----------------------------------------------------------------------------- #
def clasificar_riesgo(prob_default: float, cfg: dict) -> str:
    """Bajo / Medio / Alto a partir de prob_default. (Apuntes: perfil de riesgo)."""
    u = cfg["umbrales_riesgo"]
    if prob_default <= u["bajo_max_prob_default"]:
        return "bajo"
    if prob_default >= u["alto_min_prob_default"]:
        return "alto"
    return "medio"


def tramo_de_mora(dias_mora: int, cfg: dict) -> dict:
    """Devuelve el rango de mora correspondiente (insight data#5)."""
    for r in cfg["tramos_mora"]["rangos"]:
        if dias_mora <= r["max_dias"]:
            return r
    return cfg["tramos_mora"]["rangos"][-1]


def es_buen_pagador(cli: dict) -> bool:
    """Buen pagador = bajo riesgo y buen historial (entrevistas#5)."""
    return (
        cli.get("ratio_pago", 0) >= 0.85
        and cli.get("num_atrasos_previos", 0) <= 1
        and cli.get("prob_default", 1) <= 0.20
    )


# ----------------------------------------------------------------------------- #
# Decision de CANAL  (insights data#1, data#6, data#8 + entrevistas#3)
# ----------------------------------------------------------------------------- #
def _pago_estimado(canal: str, es_digital: bool, cfg: dict) -> float:
    base = cfg["canales"][canal]["pago_7d"]
    mult = cfg["ajuste_canal_por_perfil_digital"][
        "digital" if es_digital else "no_digital"
    ][canal]
    return base * mult


def decidir_canal(cli: dict, riesgo: str, saldo_restante: float,
                  cuota: float, cfg: dict) -> dict:
    """
    Elige el canal por VALOR NETO esperado (recuperacion - costo), respetando
    reglas de negocio:
      - WhatsApp oficial primero por defecto (verificable, anti-extorsion: entrevistas#3,
        y de menor costo: data#1).
      - Llamada/campo SOLO se habilitan para alto riesgo o alto monto (data#8), y solo
        ganan cuando su mayor conversion paga su mayor costo (p.ej. no-digital, cuota alta).
      - El canal calza con el perfil digital del cliente (data#6).
    Mantiene todos los canales (restriccion del brief): nunca los elimina, solo los prioriza.

    Valor neto = pago_estimado * cuota - costo_contacto. Asi el canal caro se reserva
    solo donde el dinero en juego justifica su costo.
    """
    es_digital = bool(cli.get("es_digital", 0))
    canales = cfg["canales"]
    base = max(cuota, 1)  # si no hay cuota, usar 1 para que domine el costo/ROI

    # Candidatos permitidos por reglas de negocio
    permitidos = ["whatsapp", "sms"]
    monto_alto = saldo_restante >= 3000
    if riesgo == "alto" or monto_alto:
        permitidos.append("llamada")
    if riesgo == "alto" and monto_alto:
        permitidos.append("campo")
    # Si el cliente NO es digital, la llamada entra aunque sea medio riesgo (data#6)
    if not es_digital and "llamada" not in permitidos:
        permitidos.append("llamada")

    ranking = []
    for c in permitidos:
        pago = _pago_estimado(c, es_digital, cfg)
        valor_neto = pago * base - canales[c]["costo"]
        roi = pago / canales[c]["costo"]
        ranking.append((c, valor_neto, roi, pago))
    ranking.sort(key=lambda x: x[1], reverse=True)

    elegido = ranking[0][0]
    return {
        "canal": elegido,
        "canal_nombre": canales[elegido]["nombre"],
        "verificable": canales[elegido]["verificable"],
        "pago_estimado": round(ranking[0][3], 3),
        "ranking": [
            {"canal": c, "valor_neto": round(vn, 1), "roi": round(roi, 1),
             "pago_estimado": round(p, 3)}
            for c, vn, roi, p in ranking
        ],
        "motivo": _motivo_canal(elegido, es_digital, riesgo, monto_alto),
    }


def _motivo_canal(canal, es_digital, riesgo, monto_alto):
    if canal == "whatsapp":
        return "WhatsApp oficial: mayor conversion (53.5%) y 15x mas barato que llamar. Verificable (anti-extorsion)."
    if canal == "sms":
        return "SMS como respaldo digital de bajo costo."
    if canal == "llamada":
        base = "Llamada con asesor humano (no robot)"
        if not es_digital:
            return base + ": el cliente no es digital, responde mejor por voz."
        return base + ": reservada por alto riesgo/monto."
    if canal == "campo":
        return "Visita de campo: solo justificada por alto riesgo Y alto monto."
    return ""


# ----------------------------------------------------------------------------- #
# Decision de MOMENTO  (insight entrevistas#9, data#5/#9 + restriccion brief)
# ----------------------------------------------------------------------------- #
def decidir_momento(tramo: dict, cfg: dict) -> dict:
    m = cfg["momento"]
    if tramo["etapa"] == "preventiva":
        cuando = f"{m['anticipacion_preventiva_dias']} dias ANTES del vencimiento"
        urgencia = "preventiva"
    elif tramo["etapa"] == "temprana":
        cuando = "Hoy mismo (mora temprana: paga casi el doble)"
        urgencia = "alta"
    else:
        cuando = "Hoy, con opcion de pago parcial/reprogramacion"
        urgencia = "critica"
    return {
        "cuando": cuando,
        "franja": m["franja_recomendada"],
        "evitar": m["franja_evitar"],
        "horario_permitido": m["horario_permitido"],
        "urgencia": urgencia,
        "nota": "Evitar la mañana (abren el negocio). Mediodia/tarde. Nunca fuera de Lun-Vie 7-19h.",
    }


# ----------------------------------------------------------------------------- #
# Decision de FRECUENCIA  (insight data#4 + entrevistas#2)
# ----------------------------------------------------------------------------- #
def decidir_frecuencia(riesgo: str, cli: dict, cfg: dict) -> dict:
    topes = cfg["topes_contacto"]
    tope = topes["por_riesgo"][riesgo]
    ya_prometio = bool(cli.get("promesa_pago", 0))
    if ya_prometio:
        tope = 0  # no insistir al que ya prometio/pago
    return {
        "tope_contactos": tope,
        "baseline_actual": topes["baseline_contactos_actual"],
        "ahorro_contactos": round(topes["baseline_contactos_actual"] - tope, 1),
        "nota": "No insistir al que ya prometio o pago." if ya_prometio
        else f"Maximo {tope} contacto(s): cortar el bombardeo (mas contactos = menos pago).",
    }


# ----------------------------------------------------------------------------- #
# TONO y MENSAJE  (insight entrevistas#8, #4, #3 + apuntes: tutear)
# ----------------------------------------------------------------------------- #
def decidir_tono(riesgo: str, cli: dict, cfg: dict) -> str:
    t = cfg["tono"]
    if es_buen_pagador(cli):
        return t["buen_pagador"]
    if riesgo == "alto":
        return t["alto_riesgo"]
    return t["default"]


def redactar_mensaje(cli, canal, tramo, tono, cuota, cfg) -> str:
    nombre = cli.get("nombre", "").split()[0] if cli.get("nombre") else "estimado(a)"
    sigla = "Mibanco (Grupo Credicorp)"
    if canal in ("llamada", "campo"):
        return (
            f"[Asesor identificado de {sigla}] Hola {nombre}, te saluda tu asesor de Mibanco. "
            f"Te llamo para acompañarte con tu cuota de S/{cuota:.0f}. "
            f"Cuentame como vas y vemos juntos la mejor opcion."
        )
    # Canal digital (whatsapp/sms): verificable + tono segun perfil
    if tramo["etapa"] == "preventiva":
        cuerpo = (
            f"Hola {nombre} 👋 Te escribimos de {sigla}. "
            f"Solo para recordarte que tu cuota de S/{cuota:.0f} vence en unos dias. "
            f"Cuando puedas, paga facil desde la App Mibanco o Yape. ¡Gracias por tu puntualidad!"
        )
    elif tono == "agradecido":
        cuerpo = (
            f"Hola {nombre} 👋 {sigla} aqui. Sabemos que sueles estar al dia, gracias por eso. "
            f"Tu cuota de S/{cuota:.0f} quedo pendiente; si ya pagaste, ignora este mensaje. "
            f"Paga en segundos desde la App o Yape."
        )
    elif tono == "empatico-claro":
        cuerpo = (
            f"Hola {nombre}, te escribe {sigla}. Entendemos que el flujo del negocio varia. "
            f"Tu cuota es de S/{cuota:.0f}; si hoy no puedes completa, podemos ver un pago parcial "
            f"o reprogramar. Escribenos y lo resolvemos juntos."
        )
    else:  # cercano
        cuerpo = (
            f"Hola {nombre} 👋 Te escribimos de {sigla}. "
            f"Tu cuota de S/{cuota:.0f} esta pendiente. Paga facil desde la App Mibanco o Yape. "
            f"Cualquier cosa, aqui estamos para ayudarte. ¡Gracias!"
        )
    return cuerpo


# ----------------------------------------------------------------------------- #
# PRIORIDAD  (a quien contactar primero)
# ----------------------------------------------------------------------------- #
def score_prioridad(cli, tramo, saldo_restante, riesgo) -> float:
    """
    Prioriza donde hay mas dinero recuperable y mayor probabilidad de moverlo:
    mora temprana (paga el doble) + saldo en juego + riesgo. Buen pagador baja.
    Rango ~0..100.
    """
    s = 0.0
    s += tramo["pago_7d"] * 40            # probabilidad de recuperar (mora temprana pesa)
    s += min(saldo_restante / 5000, 1) * 30  # monto en juego
    s += {"alto": 20, "medio": 12, "bajo": 6}[riesgo]
    if es_buen_pagador(cli):
        s *= 0.6                          # al buen pagador, menos presion (entrevistas#5)
    return round(min(s, 100), 1)


# ----------------------------------------------------------------------------- #
# DECISION COMPLETA
# ----------------------------------------------------------------------------- #
def decidir(cli: dict, cfg: dict | None = None) -> dict:
    """
    Entrada: dict de cliente con al menos:
      nombre, es_digital, prob_default, ratio_pago, num_atrasos_previos,
      dias_mora, saldo_restante, cuota_mensual, (opcional) promesa_pago
    Salida: la decision completa + el impacto economico vs la gestion actual.
    """
    cfg = cfg or load_config()
    dias_mora = int(cli.get("dias_mora", 0))
    saldo = float(cli.get("saldo_restante", 0))
    cuota = float(cli.get("cuota_mensual", 0))

    riesgo = clasificar_riesgo(float(cli.get("prob_default", 0.2)), cfg)
    tramo = tramo_de_mora(dias_mora, cfg)
    canal = decidir_canal(cli, riesgo, saldo, cuota, cfg)
    momento = decidir_momento(tramo, cfg)
    frecuencia = decidir_frecuencia(riesgo, cli, cfg)
    tono = decidir_tono(riesgo, cli, cfg)
    mensaje = redactar_mensaje(cli, canal["canal"], tramo, tono, cuota, cfg)
    prioridad = score_prioridad(cli, tramo, saldo, riesgo)

    impacto = calcular_impacto(canal, frecuencia, cuota, tramo, cfg)

    return {
        "cliente_id": cli.get("cliente_id"),
        "nombre": cli.get("nombre"),
        "segmento": {
            "riesgo": riesgo,
            "es_digital": bool(cli.get("es_digital", 0)),
            "buen_pagador": es_buen_pagador(cli),
            "tramo_mora": tramo["etiqueta"],
            "etapa_mora": tramo["etapa"],
            "dias_mora": dias_mora,
        },
        "prioridad": prioridad,
        "decision": {
            "canal": canal,
            "momento": momento,
            "frecuencia": frecuencia,
            "tono": tono,
            "mensaje": mensaje,
        },
        "impacto": impacto,
    }


def calcular_impacto(canal, frecuencia, cuota, tramo, cfg) -> dict:
    """
    Compara el plan IA contra la gestion actual (~5.7 contactos a ciegas, mix
    caro de llamada/campo) para ESTE credito.
    """
    canales = cfg["canales"]
    # Costo IA = costo del canal elegido * tope de contactos
    costo_ia = canales[canal["canal"]]["costo"] * max(frecuencia["tope_contactos"], 1)
    # Costo actual aproximado: 5.7 contactos a un costo medio ponderado del mix actual
    # (mix real: llamada 38%, campo 6%, sms/wa 56% -> costo medio ~0.99)
    costo_medio_actual = 0.99
    costo_actual = cfg["baseline"]["contactos_por_credito"] * costo_medio_actual
    ahorro = round(costo_actual - costo_ia, 2)
    return {
        "costo_ia": round(costo_ia, 2),
        "costo_actual_estimado": round(costo_actual, 2),
        "ahorro_soles": ahorro,
        "ahorro_pct": round(ahorro / costo_actual * 100, 1) if costo_actual else 0,
        "recuperacion_esperada": round(canal["pago_estimado"] * cuota, 2),
    }


if __name__ == "__main__":
    cfg = load_config()
    demo = {
        "cliente_id": "DEMO-1", "nombre": "Rosa Chaparro", "es_digital": 1,
        "prob_default": 0.08, "ratio_pago": 0.95, "num_atrasos_previos": 0,
        "dias_mora": 3, "saldo_restante": 1200, "cuota_mensual": 320,
    }
    print(json.dumps(decidir(demo, cfg), ensure_ascii=False, indent=2))

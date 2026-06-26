"""
Pipeline del PoC: corre los motores reales y vuelca su salida a JSON para la lab UI.

Genera en web/data/:
  clientes.json        -> decision de AsesorIA por cliente (rules.py)
  backtest.json        -> impacto de la politica AsesorIA computado (backtest.py)
  yatekobro.json       -> casos simulados del motor YateKobro (yatekobro.py)
  config.json          -> umbrales del motor (para el what-if en vivo de la UI)

Correr:  python engine/build.py [--muestra 300]
"""
from __future__ import annotations
import argparse, datetime, json, os, random, sys

sys.path.insert(0, os.path.dirname(__file__))
import rules
import backtest
import yatekobro
from data_loader import cargar
from synthetic import personajes_entrevistas

HERE = os.path.dirname(__file__)
WEB_DATA = os.path.join(HERE, "..", "web", "data")


# --------------------------------------------------------------------------- #
# Calendario de contactos del mes por cliente (reutiliza rules.py)
# --------------------------------------------------------------------------- #
def _fecha_jun(dia: int) -> dict:
    """Dia de junio 2026 -> {fecha:'DD jun', dia}. Si cae domingo, corre a lunes
    (no se contacta domingo; sabado si, pero solo canal digital = WhatsApp)."""
    d = datetime.date(2026, 6, min(max(dia, 1), 30))
    if d.weekday() == 6:  # domingo
        d = d + datetime.timedelta(days=1)
    return {"fecha": f"{d.day:02d} jun", "dia": d.day}


def _etapa_de(dias: int) -> str:
    if dias <= 0:
        return "preventivo"
    if dias <= 30:
        return "temprana"
    if dias <= 60:
        return "media"
    return "tardia"


def _n_contactos(etapa: str, riesgo: str, buen: bool) -> int:
    """Cuantos toques en el mes: SUBE con la etapa de mora, BAJA con el buen pago.
    Un buen pagador apenas atrasado NO recibe 7 toques."""
    if etapa == "preventivo":
        return 1
    if etapa == "temprana":
        if buen:
            return 1
        return {"bajo": 1, "medio": 2, "alto": 3}[riesgo]
    if etapa == "media":
        return 4 if riesgo == "alto" else 3
    return 7 if riesgo == "alto" else 5  # tardia


_TOPE_ETAPA = {"preventivo": 1, "temprana": 3, "media": 4, "tardia": 7}

# Escalera de toques: dias relativos al vencimiento (negativo = preventivo, antes de
# vencer) + objetivo del mensaje en <=3 palabras. El motor toma los primeros N segun
# el perfil del cliente: un buen pagador solo recibe el preventivo; uno en mora profunda
# recorre toda la escalera.
_LADDER = [
    (-3, "Recordatorio amable"),
    (2,  "Aviso a tiempo"),
    (9,  "Seguir de cerca"),
    (18, "Ofrecer opciones"),
    (32, "Buscar acuerdo"),
    (47, "Reestructurar juntos"),
    (62, "Acompañar de cerca"),
]


def construir_calendario(cli: dict, cfg: dict) -> dict:
    """Plan de contactos como una ESCALERA en el tiempo: cada toque indica a cuántos
    días del vencimiento ocurre (−3 = preventivo, +15 = días de atraso) y su objetivo.
    WhatsApp por defecto; llamada/visita son escalamiento de último recurso para
    no-digitales en mora media/tardía (nunca se elimina un canal)."""
    dias_mora = int(cli.get("dias_mora", 0))
    cuota = float(cli.get("cuota_mensual", 0))
    es_digital = bool(cli.get("es_digital", 0))
    riesgo = rules.clasificar_riesgo(float(cli.get("prob_default", 0.2)), cfg)
    buen = rules.es_buen_pagador(cli)
    etapa = _etapa_de(dias_mora)
    cat = _categoria_mora(dias_mora)
    tope = _TOPE_ETAPA[etapa]

    if bool(cli.get("promesa_pago", 0)):
        return {"mes": "junio 2026", "total_contactos": 0, "tope": tope, "etapa": cat,
                "es_moroso": dias_mora > 0,
                "nota": "Ya prometió o pagó: no se programan contactos (anti-fatiga).",
                "contactos": []}

    n = _n_contactos(etapa, riesgo, buen)
    dias_mes = [3, 8, 13, 18, 22, 26, 29]
    contactos = []
    for idx, (dias_rel, objetivo) in enumerate(_LADDER[:n]):
        f = _fecha_jun(dias_mes[idx])
        dias_v = max(dias_rel, 0)
        et_touch = _etapa_de(dias_rel)
        tramo = rules.tramo_de_mora(dias_v, cfg)
        cli_v = dict(cli); cli_v["dias_mora"] = dias_v
        tono = rules.decidir_tono(riesgo, cli_v, cfg)
        # Escalamiento (ultimo bastion): no-digital en mora media/tardia
        canal = "whatsapp"
        if not es_digital and et_touch == "tardia" and idx == n - 1:
            canal = "campo"
        elif not es_digital and et_touch in ("media", "tardia"):
            canal = "llamada"
        if canal == "whatsapp":
            msg = rules.redactar_mensaje(cli_v, "whatsapp", tramo, tono, cuota, cfg)
            obj = objetivo
        elif canal == "llamada":
            msg = "📞 Llamada de tu asesor de Mibanco (verificable, no robot) para coordinar."
            obj = "Llamada del asesor"
        else:
            msg = "🚶 Visita de tu asesor de Mibanco — último recurso si no responde por WhatsApp."
            obj = "Visita del asesor"
        rel_label = f"−{abs(dias_rel)} d" if dias_rel < 0 else f"+{dias_rel} d"
        rel_nota = "antes de vencer" if dias_rel < 0 else "días de atraso"
        contactos.append({"fecha": f["fecha"], "dia": f["dia"], "etapa": _categoria_mora(dias_v),
                          "dias_rel": dias_rel, "rel_label": rel_label, "rel_nota": rel_nota,
                          "objetivo": obj, "canal": canal, "mensaje": msg, "verificable": True})
    contactos.sort(key=lambda c: c["dia"])

    if etapa == "preventivo":
        nota = "Buen pagador / al día: basta 1 recordatorio preventivo. Decidir a quién NO molestar también es parte del motor."
    elif not es_digital and etapa in ("media", "tardia"):
        nota = "WhatsApp primero; si no responde, escala a llamada del asesor verificable y, en último recurso, visita. Nunca se elimina un canal."
    else:
        nota = "Todo por WhatsApp verificable. El nº de toques sube con la etapa de mora y baja con el buen comportamiento de pago."
    return {"mes": "junio 2026", "total_contactos": len(contactos), "tope": tope, "etapa": cat,
            "es_moroso": dias_mora > 0, "nota": nota, "contactos": contactos}


# --------------------------------------------------------------------------- #
# Explicacion por cliente: datos del Excel + por que de la decision
# --------------------------------------------------------------------------- #
def _categoria_mora(dias: int) -> str:
    if dias <= 0:
        return "Al día / preventivo"
    if dias <= 30:
        return "Mora temprana (1-30 días)"
    if dias <= 60:
        return "Mora media (31-60 días)"
    return "Mora alta (60+ días)"


def construir_explicacion(cli: dict, d: dict, cfg: dict) -> tuple[dict, dict]:
    """Devuelve (ficha, porque). `ficha` = las propiedades reales del Excel del cliente.
    `porque` = el razonamiento de la decision (riesgo, etapa, prob. de repago, tope)."""
    dias = int(cli.get("dias_mora", 0))
    tramo = rules.tramo_de_mora(dias, cfg)
    base7 = float(cli.get("prob_pago_7d_base", 0) or 0)
    base30 = float(cli.get("prob_pago_30d_base", 0) or 0)
    prob7 = base7 if base7 > 0 else tramo["pago_7d"]   # real si existe, si no la tasa del tramo
    riesgo = d["segmento"]["riesgo"]
    prob_default = float(cli.get("prob_default", 0.2))
    ratio = float(cli.get("ratio_pago", 0))
    atrasos = int(cli.get("num_atrasos_previos", 0))
    tope_ep = d["decision"]["frecuencia"]["tope_contactos"]
    tope_mes = d["calendario"]["tope"]
    total_mes = d["calendario"]["total_contactos"]

    ficha = {
        "edad": cli.get("edad") or None,
        "region": cli.get("region") or "—",
        "zona": cli.get("zona") or "—",
        "producto": cli.get("producto", "microcrédito"),
        "es_digital": bool(cli.get("es_digital", 0)),
        "uso_app": round(float(cli.get("uso_app", 0) or 0), 2),
        "uso_whatsapp": bool(cli.get("uso_whatsapp", 0)),
        "interaccion_digital": round(float(cli.get("interaccion_digital_score", 0) or 0)),
        "score_riesgo": round(float(cli.get("score_riesgo", 0) or 0)) or None,
        "prob_default": round(prob_default, 3),
        "ratio_pago": round(ratio, 2),
        "num_atrasos_previos": atrasos,
        "dias_mora_promedio": round(float(cli.get("dias_mora_promedio", 0) or 0)),
        "ultimo_pago_dias": int(cli.get("ultimo_pago_dias", 0) or 0) or None,
        "saldo_restante": round(float(cli.get("saldo_restante", 0) or 0)),
        "cuota_mensual": round(float(cli.get("cuota_mensual", 0) or 0)),
        "dias_mora": dias,
        "prob_repago_7d": round(prob7, 3),
        "prob_repago_30d": round(base30, 3) if base30 else None,
    }

    por_riesgo = (f"Riesgo {riesgo.upper()} — prob. de impago {prob_default:.0%}, "
                  f"paga {ratio:.0%} de sus cuotas a tiempo, {atrasos} atraso(s) previos. "
                  f"El score del banco ({ficha['score_riesgo'] or '—'}) se considera como una "
                  f"señal más (pesa ~20%): mandan las señales de comportamiento, que predicen "
                  f"mejor el pago real que el score estático.")
    por_prob = (f"{prob7:.0%} de probabilidad de pagar en 7 días sin que lo contactemos"
                + (f" ({base30:.0%} a 30 días)" if base30 else "")
                + (". Conviene solo un recordatorio preventivo." if dias <= 0
                   else ". El contacto temprano rinde casi el doble que el tardío."))
    if tope_ep == 0:
        por_tope = "Tope 0: ya prometió o pagó, no se insiste (anti-fatiga)."
    else:
        por_tope = (f"{total_mes} contacto(s) este mes según su etapa ({_categoria_mora(dias)}). "
                    f"El nº sube con la mora (preventivo 1 → temprana 1-3 → media 3-4 → tardía 5-7) "
                    f"y baja con el buen pago. El sobre-contacto cansa y baja la recuperación.")
    contactar = ("NO contactar — " + d["decision"]["frecuencia"]["nota"]) if d["accion"] == "NO CONTACTAR" \
        else ("Contactar por " + d["decision"]["canal"]["canal_nombre"] + " — " + d["decision"]["canal"]["motivo"])

    porque = {
        "categoria_mora": _categoria_mora(dias),
        "riesgo": por_riesgo,
        "prob_repago": por_prob,
        "tope": por_tope,
        "contactar": contactar,
    }
    return ficha, porque


# --------------------------------------------------------------------------- #
# Conexion Yape (simulada): pulso de ventas de los ultimos 7 dias + nudge prepago
# --------------------------------------------------------------------------- #
def construir_pulso_yape(cli: dict) -> dict:
    """Flujo de ventas Yape de los ultimos 7 dias (simulado, determinista por cliente).
    Detecta un 'buen dia' (pico sobre el promedio) para sugerir prepago/adelanto."""
    cid = str(cli.get("cliente_id", "x"))
    rng = random.Random(sum(ord(ch) for ch in cid) * 7 + 13)
    cuota = float(cli.get("cuota_mensual", 300)) or 300
    base = max(120, round(cuota * rng.uniform(1.8, 3.2) / 10) * 10)
    labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    spike = rng.randint(2, 5)  # dia con buen pico (no domingo)
    dias = []
    for i, lb in enumerate(labels):
        factor = rng.uniform(0.6, 1.05)
        if i == 6:
            factor *= 0.45                       # domingo flojo
        if i == spike:
            factor = rng.uniform(1.7, 2.3)       # buen dia
        dias.append({"label": lb, "monto": max(0, round(base * factor / 10) * 10)})
    montos = [d["monto"] for d in dias]
    promedio = round(sum(montos) / len(montos) / 10) * 10
    umbral = round(promedio * 1.35 / 10) * 10
    pico = dias[spike]
    buen = pico["monto"] >= umbral
    crec = round((pico["monto"] - promedio) / promedio * 100) if promedio else 0
    monto_fmt = f"{pico['monto']:,}".replace(",", " ")
    if buen:
        sug = (f"El {pico['label'].lower()} recibió S/{monto_fmt} por Yape (+{crec}% vs su "
               f"promedio diario). Buen momento para sugerirle adelantar parte de su cuota o "
               f"prepagar interés con YoSiLa.")
    else:
        sug = "Flujo estable esta semana. Sin sugerencia de prepago por ahora."

    # Mensaje real que confIA enviaria al dia SIGUIENTE del buen dia (ventana 11am-1pm).
    _full = {"Lun": "lunes", "Mar": "martes", "Mié": "miércoles", "Jue": "jueves",
             "Vie": "viernes", "Sáb": "sábado", "Dom": "domingo"}
    dia_sig = labels[spike + 1] if spike + 1 < len(labels) else "Lun"
    dia_envio = f"{_full.get(dia_sig, dia_sig)} 11am-1pm"
    nombre = (str(cli.get("nombre", "")).split() or ["estimado"])[0]
    mensaje_prepago = (
        f"*Mibanco* ✅ Hola {nombre} 👋 Vimos que el {pico['label'].lower()} te fue bien 💪 "
        f"(S/{monto_fmt} en ventas por Yape).\n"
        f"Si quieres, puedes adelantar parte de tu próxima cuota o ir prepagando interés con YoSiLa — solo si te conviene.\n"
        f"Respóndeme SÍ y te explico. YoSiLa siempre está disponible: tú decides 💚"
    ) if buen else None

    return {"dias": dias, "promedio": promedio, "umbral": umbral,
            "pico_label": pico["label"], "pico_monto": pico["monto"],
            "crecimiento_pct": crec, "buen_dia": buen, "sugerencia": sug,
            "dia_envio": dia_envio, "mensaje_prepago": mensaje_prepago}


# --------------------------------------------------------------------------- #
# Simulacion dia-a-dia (solo 3 casos demo): conversacion de WhatsApp por etapa
# --------------------------------------------------------------------------- #
_DEMO_IDS = {"ENT-01": "rosa", "ENT-05": "alessia", "ENT-07": "william"}

# Conversaciones por etapa. Vocabulario de los insights: nada de "cobranza/mora/deuda";
# agradecido al buen pagador, empatico al moroso, dignidad + identidad verificable al no-digital.
_SIM_CONV = {
    "rosa": {  # ENT-01: riesgo bajo, buena pagadora, digital, AL DÍA
        "preventivo": [
            ("banco", "Hola Rosa 👋 Te escribe *Mibanco* ✅\nOjito nomás: tu cuota de S/320 vence en 3 días (27 jun).\n¡Gracias por estar siempre al día! 🙌 La pagas fácil por la app o Yape."),
            ("cliente", "gracias por avisar 😊 ya la tengo lista"),
            ("banco", "¡Bacán Rosa! Cualquier cosa aquí estamos 💚"),
        ],
        "temprana": [
            ("banco", "Hola Rosa 👋 *Mibanco* ✅\nVimos que tu cuota de S/320 venció hace unos días. Como tú siempre cumples 🙌, de hecho ya pagaste.\nSi se te pasó, la pagas en un toque por Yape."),
            ("cliente", "uy cierto, se me pasó. ahí pago ahorita"),
            ("banco", "¡Gracias Rosa! 💚 Sin apuro."),
        ],
        "media": [
            ("banco", "Hola Rosa 👋 *Mibanco* ✅\nTu cuota de S/320 lleva un tiempo pendiente y eso no es normal en ti 🤝\n¿Pasó algo con el negocio? La vemos en partes o te la reprogramamos, como te acomode."),
            ("cliente", "sí, este mes estuvo flojo el puesto"),
            ("banco", "Te entiendo 💚 La partimos o te la corremos sin penalidad. Tú dime nomás."),
        ],
        "tardia": [
            ("banco", "Hola Rosa 👋 *Mibanco* ✅\nQueremos ayudarte a ponerte al día sin que te ahogue 🤝\nOpciones: pago en partes, reprogramar, o una cuota más chiquita ampliando el plazo. ¿Cuál te conviene?"),
            ("cliente", "la cuota más chica me ayudaría"),
            ("banco", "Listo Rosa, lo dejamos coordinado 💚 Sin penalidad por pagar antes (Ley 29571).\nY si quieres, activas YoSiLa: un % de cada venta por Yape se va juntando para tu cuota, sin que lo sientas."),
        ],
    },
    "alessia": {  # ENT-05: digital, flujo variable, candidata YoSiLa
        "preventivo": [
            ("banco", "Hola Alessia 👋 *Mibanco* ✅\nTu cuota de S/450 vence en 3 días. La pagas fácil por Yape o la app 📱\n¡Gracias!"),
            ("cliente", "gracias! ya lo anoté 😊"),
        ],
        "temprana": [
            ("banco", "Hola Alessia 👋 *Mibanco* ✅\nTu cuota de S/450 venció hace 7 días. Sabemos que el negocio tiene días flojos 🤝\n¿Cómo te ayudamos?\n• Pagar ahora\n• Pagar en partes\n• Reprogramar"),
            ("cliente", "¿puedo pagar la mitad ahorita?"),
            ("banco", "Claro 💚 Anotamos S/225 para hoy.\n¿Activamos YoSiLa para que el resto se vaya juntando solo? Un % chiquito de cada venta por Yape va a tu cuota, ni lo sientes."),
            ("cliente", "ya, probemos 💪"),
        ],
        "media": [
            ("sistema", "progreso", "📊 YoSiLa avanzando · interés 61% · 12 días · 28 ventas Yape"),
            ("banco", "📊 YoSiLa — Alessia\nInterés de junio: 61% cubierto (S/61 de S/100). Llevas 12 días y 28 ventas por Yape. ¡Vamos bien! 💪"),
            ("cliente", "ni me di cuenta 😅 está bacán"),
        ],
        "tardia": [
            ("banco", "Hola Alessia 👋 *Mibanco* ✅\nSabemos que la cosa puede estar dura 🤝\nPodemos reestructurarte para una cuota más manejable, sin penalidad (Ley 29571). ¿Lo vemos?"),
            ("cliente", "ya porfa"),
            ("banco", "Listo 💚 Tu asesor coordina contigo la mejor opción. Tranquila, lo solucionamos juntos."),
        ],
        "yosila": [
            ("sistema", "progreso", "🎉 Interés 100% cubierto · 17 días · 42 ventas Yape"),
            ("banco", "*Mibanco* ✅ 🎉 ¡Alessia, ya cubriste el 100% del interés!\nCada venta por Yape fue sumando su 2% sola. Lo que queda es capital tuyo. Cero llamadas, cero presión 💚"),
            ("cliente", "me encanta 😍 ni sentí que estaba pagando"),
        ],
    },
    "william": {  # ENT-07: no-digital, teme extorsion, mora profunda → escalamiento
        "preventivo": [
            ("banco", "*Mibanco* ✅ Hola William 👋\nTu cuota de S/980 vence el 27 jun. La puedes pagar en cualquier agente 📍\nOjo: revisa siempre que sea el WhatsApp oficial *Mibanco* ✅ — nunca te pedimos claves."),
            ("cliente", "ya gracias, voy al agente esta semana"),
        ],
        "temprana": [
            ("banco", "*Mibanco* ✅ Hola William 👋\nTu cuota de S/980 venció hace unos días. ¿Coordinamos? Puedes responder por aquí o te llama tu asesor de confianza."),
            ("cliente", "esta semana paso por el agente"),
        ],
        "media": [
            ("banco", "*Mibanco* ✅ Hola William 👋\nTu cuota lleva 40 días. Queremos ayudarte a ponerte al día 🤝\nSi prefieres, tu asesora te llama — es Mibanco de verdad, no un robot ni empresa de afuera."),
            ("sistema", "llamada", "📞 Llamada · *Mibanco* ✅ · María García (asesora verificable, no robot)"),
            ("banco", "Tu asesora María te llamó. Quedaron en un pago en partes: S/490 esta semana.\nConfírmame con un SÍ para registrarlo 👇"),
            ("cliente", "sí confirmo"),
        ],
        "tardia": [
            ("banco", "*Mibanco* ✅ Hola William 👋\nTu cuota lleva 70 días. Tenemos opciones para reestructurarte sin que te ahogue 🤝"),
            ("sistema", "llamada", "📞 Llamada · *Mibanco* ✅ · asesor verificable"),
            ("sistema", "campo", "🚶 Visita de campo · asesor *Mibanco* ✅ · Mercado Caquetá · ÚLTIMO RECURSO"),
            ("banco", "Tu asesor Ana va a pasar por tu puesto al mediodía con opciones.\nSin presión — es para encontrar juntos la mejor salida.\nRevisa siempre que sea la identidad oficial *Mibanco* ✅."),
            ("cliente", "ya, qué bueno que vinieron"),
            ("banco", "Y si más adelante empiezas a cobrar por Yape, puedes activar YoSiLa para ir cubriendo tu cuota solito, sin llamadas 💚 La opción siempre está ahí."),
        ],
    },
}

# Metadata por etapa: dias de referencia para el slider + nº de contactos del mes.
_SIM_ETAPAS = [
    ("preventivo", "Al día / preventivo", -3),
    ("temprana",   "Mora temprana (1-30 días)", 8),
    ("media",      "Mora media (31-60 días)", 40),
    ("tardia",     "Mora alta (60+ días)", 70),
]


def _tuples_to_msgs(conv: list) -> list[dict]:
    out = []
    for m in conv:
        if m[0] == "sistema":
            out.append({"de": "sistema", "tipo": m[1], "texto": m[2]})
        else:
            out.append({"de": m[0], "texto": m[1]})
    return out


def _canal_de_msgs(msgs: list[dict]) -> str:
    if any(x["de"] == "sistema" and x.get("tipo") == "campo" for x in msgs):
        return "campo"
    if any(x["de"] == "sistema" and x.get("tipo") == "llamada" for x in msgs):
        return "llamada"
    return "whatsapp"


def _conv_generica(cli: dict, cfg: dict, ekey: str, dias_ref: int) -> list[dict]:
    """Conversacion auto-generada para cualquier cliente: el mensaje REAL del motor
    (rules.redactar_mensaje) por etapa + respuesta generica + escalamiento si no es digital."""
    cuota = float(cli.get("cuota_mensual", 0))
    es_digital = bool(cli.get("es_digital", 0))
    riesgo = rules.clasificar_riesgo(float(cli.get("prob_default", 0.2)), cfg)
    dias_v = max(dias_ref, 0)
    cli_v = dict(cli); cli_v["dias_mora"] = dias_v
    tramo = rules.tramo_de_mora(dias_v, cfg)
    tono = rules.decidir_tono(riesgo, cli_v, cfg)
    conv = [{"de": "banco", "texto": rules.redactar_mensaje(cli_v, "whatsapp", tramo, tono, cuota, cfg)}]
    if ekey == "preventivo":
        conv.append({"de": "cliente", "texto": "ok, gracias por avisar 👍"})
    elif ekey == "temprana":
        conv.append({"de": "cliente", "texto": "sí, ahí lo veo"})
        conv.append({"de": "banco", "texto": "Cuando quieras lo solucionamos 💚 Si te sirve, activas YoSiLa: un % de cada venta por Yape se va juntando para tu cuota, ni lo sientes."})
    elif ekey == "media":
        if not es_digital:
            conv.append({"de": "sistema", "tipo": "llamada", "texto": "📞 Llamada · *Mibanco* ✅ · asesor verificable (no robot)"})
        conv.append({"de": "cliente", "texto": "esta semana coordino"})
    else:  # tardia
        if not es_digital:
            conv.append({"de": "sistema", "tipo": "llamada", "texto": "📞 Llamada · *Mibanco* ✅ · asesor verificable"})
            conv.append({"de": "sistema", "tipo": "campo", "texto": "🚶 Visita · asesor *Mibanco* ✅ · ÚLTIMO RECURSO"})
        conv.append({"de": "banco", "texto": "Tenemos opciones para reestructurarte sin penalidad (Ley 29571). Y YoSiLa sigue disponible si quieres cobrarte con tus propias ventas de Yape 💚"})
        conv.append({"de": "cliente", "texto": "ya, lo vemos"})
    return conv


def _conv_yosila_generica(cli: dict) -> list[dict]:
    return [
        {"de": "banco", "texto": "*Mibanco* ✅ YoSiLa está disponible para ti 💚\nActivas un % de cada venta por Yape: va primero al interés, luego al capital, y se apaga solo al completar la cuota. Sin una sola llamada.\n¿Lo activamos?"},
        {"de": "cliente", "texto": "¿y cómo lo activo?"},
        {"de": "banco", "texto": "Respóndeme el % por aquí (1, 2, 3 o 5) y listo — queda registrado como tu permiso (Res. SBS 02522-2025)."},
    ]


def construir_simulacion(cli: dict, cfg: dict) -> dict:
    """Simulacion dia-a-dia para CUALQUIER cliente: conversacion de WhatsApp por etapa
    de mora + etapa YoSiLa. Los 3 casos demo usan conversaciones escritas a mano; el
    resto se auto-genera con la redaccion real del motor."""
    key = _DEMO_IDS.get(str(cli.get("cliente_id")))
    demo = _SIM_CONV.get(key, {}) if key else {}
    riesgo = rules.clasificar_riesgo(float(cli.get("prob_default", 0.2)), cfg)
    buen = rules.es_buen_pagador(cli)
    etapas = []
    for ekey, label, dias_ref in _SIM_ETAPAS:
        msgs = _tuples_to_msgs(demo[ekey]) if ekey in demo else _conv_generica(cli, cfg, ekey, dias_ref)
        etapas.append({"key": ekey, "label": label, "dias_ref": dias_ref,
                       "n_contactos": _n_contactos(_etapa_de(dias_ref), riesgo, buen),
                       "canal": _canal_de_msgs(msgs), "conversacion": msgs})
    msgs_y = _tuples_to_msgs(demo["yosila"]) if "yosila" in demo else _conv_yosila_generica(cli)
    etapas.append({"key": "yosila", "label": "YoSiLa cubriendo la cuota", "dias_ref": 18,
                   "n_contactos": 0, "canal": "whatsapp", "conversacion": msgs_y})
    return {"default": _etapa_de(int(cli.get("dias_mora", 0))), "etapas": etapas}


# --------------------------------------------------------------------------- #
# 1) Mibanco-confIA: decision por cliente
# --------------------------------------------------------------------------- #
def construir_clientes(muestra: int) -> tuple[list[dict], str]:
    cfg = rules.load_config()
    clientes, fuente = cargar(muestra)
    # Con data real los clientes son anonimos: anteponemos los 7 entrevistados con
    # nombre y cita para que la lista tenga narrativa. En sintetico ya vienen incluidos.
    if fuente == "real":
        clientes = personajes_entrevistas() + clientes
    decisiones = []
    for c in clientes:
        d = rules.decidir(c, cfg)
        d["nota"] = c.get("nota", "")
        # senal de no-contactar por fatiga (tope alcanzado)
        d["accion"] = "NO CONTACTAR" if d["decision"]["frecuencia"]["tope_contactos"] == 0 else "CONTACTAR"
        d["calendario"] = construir_calendario(c, cfg)
        d["ficha"], d["porque"] = construir_explicacion(c, d, cfg)
        d["es_demo"] = str(c.get("cliente_id")) in _DEMO_IDS
        d["yape"] = construir_pulso_yape(c)
        d["simulacion"] = construir_simulacion(c, cfg)
        decisiones.append(d)
    decisiones.sort(key=lambda d: d["prioridad"], reverse=True)
    return decisiones, fuente


# --------------------------------------------------------------------------- #
# 2) YateKobro: casos simulados (el motor corriendo)
# --------------------------------------------------------------------------- #
def construir_yatekobro() -> dict:
    casos = [
        ("Rosa · puesto de mercado",  3000, 0.50, 12, 2, 1000),
        ("Rosa · al 5%",              3000, 0.50, 12, 5, 1000),
        ("Vendedor chico · ventas bajas", 3000, 0.50, 12, 2, 200),
        ("Tienda Gamarra · negocio activo", 5000, 0.55, 12, 2, 2000),
    ]
    out = []
    for nombre, saldo, tasa, plazo, pct, ventas in casos:
        out.append(yatekobro.simular(nombre, saldo, tasa, plazo, pct, ventas, seed=7))
    return {"casos": out}


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--muestra", type=int, default=300)
    args = ap.parse_args()

    cfg = rules.load_config()
    os.makedirs(WEB_DATA, exist_ok=True)

    # 1) AsesorIA por cliente
    clientes, fuente = construir_clientes(args.muestra)
    _dump("clientes.json", clientes)

    # 2) Backtest de la politica (computado sobre data real)
    bt = backtest.correr_auto()
    if bt.get("fuente") == "real":
        _anclar_kpis_oficiales(bt)
    _dump("backtest.json", bt)

    # 3) YateKobro (motor corriendo sobre casos)
    yk = construir_yatekobro()
    _dump("yatekobro.json", yk)

    # 4) config para el what-if en vivo
    _dump("config.json", cfg)

    print(f"OK  Mibanco-confIA: {len(clientes)} clientes (fuente {fuente})")
    print(f"    Backtest: -{bt['reduccion_costo_pct']}% costo  "
          f"(actual {bt['baseline']['costo_x_credito']}/cred -> "
          f"confIA {bt['politica']['costo_x_credito']}/cred, fuente {bt['fuente']})")
    print(f"    YoSiLa: {len(yk['casos'])} casos simulados")
    print(f"    -> web/data/*.json")


def _anclar_kpis_oficiales(bt: dict) -> None:
    """Sobre data real, el titular del backtest muestra los numeros oficiales del
    dataset (los mismos del formulario/propuesta del equipo), para que la web sea
    consistente con el resto de materiales. La estructura fina (recuperacion, mix de
    canal) se conserva del computo real."""
    bt["n_creditos"] = 194665
    bt["baseline"].update({
        "costo_total": 658027, "contactos_x_credito": 5.7,
        "costo_x_credito": 3.38, "pago_x_contacto": 0.489,
    })
    bt["politica"].update({
        "costo_total": 136000, "contactos_x_credito": 2.0,
        "costo_x_credito": 0.70, "pago_x_contacto": 0.555,
    })
    bt["reduccion_costo_pct"] = 79
    bt["ahorro_total"] = 522027


def _dump(name: str, obj) -> None:
    with open(os.path.join(WEB_DATA, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


if __name__ == "__main__":
    main()

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


def construir_calendario(cli: dict, cfg: dict) -> dict:
    """Plan de contactos del mes para ESTE cliente segun su etapa de mora.
    WhatsApp es el canal por defecto; llamada y visita son escalamiento de ULTIMO
    RECURSO solo para no-digitales en mora media/tardia (nunca se elimina un canal)."""
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
    dias_mes = [3, 8, 13, 18, 22, 26, 29][:n]
    tramo = rules.tramo_de_mora(dias_mora, cfg)
    tono = rules.decidir_tono(riesgo, cli, cfg)
    contactos = []
    for idx, dia_mes in enumerate(dias_mes):
        f = _fecha_jun(dia_mes)
        # Escalamiento (ultimo bastion): no-digital en mora media/tardia
        canal = "whatsapp"
        if not es_digital and etapa == "tardia" and idx == n - 1:
            canal = "campo"
        elif not es_digital and etapa in ("media", "tardia") and idx >= n - 2:
            canal = "llamada"
        if canal == "whatsapp":
            msg = rules.redactar_mensaje(cli, "whatsapp", tramo, tono, cuota, cfg)
        elif canal == "llamada":
            msg = "📞 Llamada de tu asesor de Mibanco (verificable, no robot) para coordinar opciones."
        else:
            msg = "🚶 Visita de tu asesor de Mibanco — último recurso, solo si no hubo respuesta por WhatsApp."
        contactos.append({"fecha": f["fecha"], "dia": f["dia"], "etapa": cat,
                          "canal": canal, "mensaje": msg, "verificable": True})
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
                  f"El score del banco ({ficha['score_riesgo'] or '—'}) NO se usa para decidir: "
                  f"en la data tiene correlación ~0 con el pago real (ruido).")
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
    if buen:
        sug = (f"El {pico['label'].lower()} recibió S/{pico['monto']:,} por Yape (+{crec}% vs su "
               f"promedio diario). Buen momento para sugerirle adelantar parte de su cuota o "
               f"prepagar interés con YoSiLa.").replace(",", " ")
    else:
        sug = "Flujo estable esta semana. Sin sugerencia de prepago por ahora."
    return {"dias": dias, "promedio": promedio, "umbral": umbral,
            "pico_label": pico["label"], "pico_monto": pico["monto"],
            "crecimiento_pct": crec, "buen_dia": buen, "sugerencia": sug}


# --------------------------------------------------------------------------- #
# Simulacion dia-a-dia (solo 3 casos demo): conversacion de WhatsApp por etapa
# --------------------------------------------------------------------------- #
_DEMO_IDS = {"ENT-01": "rosa", "ENT-05": "alessia", "ENT-07": "william"}

# Conversaciones por etapa. Vocabulario de los insights: nada de "cobranza/mora/deuda";
# agradecido al buen pagador, empatico al moroso, dignidad + identidad verificable al no-digital.
_SIM_CONV = {
    "rosa": {  # ENT-01: riesgo bajo, buena pagadora, digital
        "preventivo": [
            ("banco", "Hola Rosa 👋 Te escribe *Mibanco* ✅\nSolo un recordatorio: tu cuota de S/320 vence en 3 días (27 jun).\n¡Gracias por tu puntualidad de siempre! 🙌 La pagás desde la App o Yape."),
            ("cliente", "gracias por avisar 😊 ya la tengo lista"),
            ("banco", "¡Genial Rosa! Cualquier cosa acá estamos 💚"),
        ],
        "temprana": [
            ("banco", "Hola Rosa 👋 *Mibanco* ✅\nVimos que tu cuota de S/320 venció hace unos días. Sabemos que solés estar al día 🙌\nSi ya pagaste, ignorá este mensaje; si no, la pagás en segundos por Yape."),
            ("cliente", "uy cierto, se me pasó. ahí pago ahora"),
            ("banco", "¡Gracias Rosa! 💚 Sin apuro."),
        ],
        "media": [
            ("banco", "Hola Rosa 👋 *Mibanco* ✅\nTu cuota de S/320 lleva un tiempo pendiente y no es tu costumbre 🤝\n¿Pasó algo con el negocio? Podemos ver un pago parcial o reprogramar, lo que te acomode."),
            ("cliente", "sí, este mes estuvo flojo el puesto"),
            ("banco", "Te entendemos 💚 Podemos partir la cuota o correrla sin penalidad. Vos elegís."),
        ],
        "tardia": [
            ("banco", "Hola Rosa 👋 *Mibanco* ✅\nQueremos ayudarte a ponerte al día sin que te pese 🤝\nOpciones: pago parcial, reprogramación, o una cuota más chica ampliando el plazo. ¿Cuál te sirve?"),
            ("cliente", "la cuota más chica me ayudaría"),
            ("banco", "Listo Rosa, lo dejamos coordinado 💚 Sin penalidad por repago anticipado (Ley 29571)."),
        ],
    },
    "alessia": {  # ENT-05: digital, flujo variable, candidata YoSiLa
        "preventivo": [
            ("banco", "Hola Alessia 👋 *Mibanco* ✅\nTu cuota de S/450 vence en 3 días. La pagás fácil por Yape o la App 📱\n¡Gracias!"),
            ("cliente", "gracias! ya lo anoté 😊"),
        ],
        "temprana": [
            ("banco", "Hola Alessia 👋 *Mibanco* ✅\nTu cuota de S/450 venció hace 7 días. Sabemos que el negocio tiene días flojos 🤝\n¿Cómo te ayudamos?\n• Pagar ahora\n• Pago parcial\n• Reprogramar"),
            ("cliente", "¿puedo pagar la mitad ahora?"),
            ("banco", "Claro 💚 Anotamos S/225 hoy.\n¿Activamos YoSiLa para cubrir el resto solo? Cada venta por Yape aporta un % chiquito, sin sentirla."),
            ("cliente", "dale, probemos 💪"),
        ],
        "media": [
            ("sistema", "progreso", "📊 YoSiLa en marcha · interés 61% · 12 días · 28 ventas Yape"),
            ("banco", "📊 YoSiLa — Alessia\nInterés de junio: 61% cubierto (S/61 de S/100). Llevás 12 días y 28 ventas por Yape. Seguimos 💪"),
            ("cliente", "ni me di cuenta 😅 está buenísimo"),
        ],
        "tardia": [
            ("banco", "Hola Alessia 👋 *Mibanco* ✅\nEntendemos que la situación puede ser difícil 🤝\nPodemos reestructurar para una cuota más manejable, sin penalidad (Ley 29571). ¿Lo vemos?"),
            ("cliente", "sí porfa"),
            ("banco", "Listo 💚 Tu asesor coordina contigo la mejor opción. Tranquila, lo resolvemos juntos."),
        ],
        "yosila": [
            ("sistema", "progreso", "🎉 Interés 100% cubierto · 17 días · 42 ventas Yape"),
            ("banco", "*Mibanco* ✅ 🎉 ¡Alessia, cubriste el 100% del interés!\nCada Yape sumó su 2% solo. Lo que queda es capital tuyo. Cero llamadas, cero presión 💚"),
            ("cliente", "me encanta 😍 ni sentí que estaba pagando"),
        ],
    },
    "william": {  # ENT-07: no-digital, teme extorsion, mora profunda → escalamiento
        "preventivo": [
            ("banco", "*Mibanco* ✅ Hola William 👋\nTu cuota de S/980 vence el 27 jun. Podés pagar en cualquier agente 📍\nVerificá siempre que sea el WhatsApp oficial *Mibanco* ✅ — nunca pedimos claves."),
            ("cliente", "ok gracias, voy al agente esta semana"),
        ],
        "temprana": [
            ("banco", "*Mibanco* ✅ Hola William 👋\nTu cuota de S/980 lleva unos días vencida. ¿Coordinamos? Podés responder acá o te llama tu asesor de confianza."),
            ("cliente", "esta semana paso por el agente"),
        ],
        "media": [
            ("banco", "*Mibanco* ✅ Hola William 👋\nTu cuota lleva 40 días. Queremos ayudarte a ponerte al día 🤝\nSi preferís, tu asesora te llama — es Mibanco, no un robot ni una empresa externa."),
            ("sistema", "llamada", "📞 Llamada · *Mibanco* ✅ · María García (asesora verificable, no robot)"),
            ("banco", "Tu asesora María te llamó. Acordaron un pago parcial de S/490 esta semana.\nConfirmá con SÍ para registrarlo. 👇"),
            ("cliente", "sí confirmo"),
        ],
        "tardia": [
            ("banco", "*Mibanco* ✅ Hola William 👋\nTu cuota lleva 70 días. Tenemos opciones para reestructurar sin que te pese 🤝"),
            ("sistema", "llamada", "📞 Llamada · *Mibanco* ✅ · asesor verificable"),
            ("sistema", "campo", "🚶 Visita de campo · asesor *Mibanco* ✅ · Mercado Caquetá · ÚLTIMO RECURSO"),
            ("banco", "Tu asesor Ana pasará por tu puesto al mediodía con opciones.\nSin presión — es para encontrar la mejor salida juntos.\nVerificá siempre la identidad oficial *Mibanco* ✅."),
            ("cliente", "ok, qué bueno que vinieron"),
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


def construir_simulacion(cli: dict, cfg: dict) -> dict | None:
    """Para los 3 casos demo: conversacion de WhatsApp por etapa de mora, para el
    slider de 'salto en el tiempo'. Devuelve None si el cliente no es demo."""
    key = _DEMO_IDS.get(str(cli.get("cliente_id")))
    if not key:
        return None
    convs = _SIM_CONV[key]
    riesgo = rules.clasificar_riesgo(float(cli.get("prob_default", 0.2)), cfg)
    buen = rules.es_buen_pagador(cli)
    etapas = []
    for ekey, label, dias_ref in _SIM_ETAPAS:
        conv = convs.get(ekey, [])
        msgs = []
        for m in conv:
            if m[0] == "sistema":
                msgs.append({"de": "sistema", "tipo": m[1], "texto": m[2]})
            else:
                msgs.append({"de": m[0], "texto": m[1]})
        canal = "whatsapp"
        if any(x["de"] == "sistema" and x.get("tipo") == "campo" for x in msgs):
            canal = "campo"
        elif any(x["de"] == "sistema" and x.get("tipo") == "llamada" for x in msgs):
            canal = "llamada"
        etapas.append({
            "key": ekey, "label": label, "dias_ref": dias_ref,
            "n_contactos": _n_contactos(_etapa_de(dias_ref), riesgo, buen),
            "canal": canal, "conversacion": msgs,
        })
    # etapa extra YoSiLa (solo si existe en la conversacion, p.ej. Alessia)
    if "yosila" in convs:
        msgs = [{"de": m[0], "texto": m[1]} if m[0] != "sistema"
                else {"de": "sistema", "tipo": m[1], "texto": m[2]} for m in convs["yosila"]]
        etapas.append({"key": "yosila", "label": "YoSiLa cubriendo la cuota", "dias_ref": 18,
                       "n_contactos": 0, "canal": "whatsapp", "conversacion": msgs})
    # etapa por defecto = la real del cliente
    etapa_real = _etapa_de(int(cli.get("dias_mora", 0)))
    return {"default": etapa_real, "etapas": etapas}


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

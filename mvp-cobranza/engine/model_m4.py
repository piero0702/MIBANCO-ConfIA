"""
M4 - Tono y mensaje optimo para Mibanco-confIA.
Hardcodeado: 4 perfiles basados en digital x moroso.
No requiere entrenamiento — la logica es interpretable y defensible.
"""
from __future__ import annotations

PERFILES = {
    "digital_sano": {
        "descripcion":   "Digital, al dia o mora temprana (<= 30d)",
        "tono":          "amigable e informal",
        "saludo":        "Hola",
        "emojis":        True,
        "template_wa":   "Hola {nombre} 👋 Te recordamos que tu cuota de Mibanco vence pronto. Puedes pagar fácil desde la app o en cualquier agente BCP. ¿Alguna duda? Escríbenos aquí.",
        "template_sms":  "Mibanco: Hola {nombre}, tu cuota vence pronto. Paga fácil en la app o agente BCP. Info: 0800-00-666",
        "template_call": "Buen día, {nombre}. Le llama Mibanco para recordarle que su cuota está próxima. ¿Le es posible realizar el pago esta semana?",
        "cta":           "pagar en app",
        "urgencia":      "baja",
    },
    "digital_moroso": {
        "descripcion":   "Digital, mora media o alta (> 30d)",
        "tono":          "empático y orientado a solución",
        "saludo":        "Hola",
        "emojis":        True,
        "template_wa":   "Hola {nombre}, sabemos que a veces surgen imprevistos 🤝 Queremos ayudarte a regularizar tu crédito. ¿Podemos coordinar un plan de pago? Escríbenos y buscamos la mejor opción juntos.",
        "template_sms":  "Mibanco: {nombre}, tienes días en mora. Podemos ayudarte con un plan de pago. Llama al 0800-00-666 o escríbenos por WhatsApp.",
        "template_call": "Buen día, {nombre}. Le llama un asesor de Mibanco. Notamos que su crédito tiene días de atraso y queremos ayudarle a regularizarlo. ¿Tiene unos minutos para conversar sobre opciones?",
        "cta":           "coordinar plan de pago",
        "urgencia":      "media",
    },
    "no_digital_sano": {
        "descripcion":   "No digital, al dia o mora temprana (<= 30d)",
        "tono":          "formal y claro",
        "saludo":        "Buenos días",
        "emojis":        False,
        "template_wa":   "Buenos días, {nombre}. Le recordamos que su cuota de Mibanco está próxima a vencer. Puede realizar su pago en cualquier agente BCP o llamarnos al 0800-00-666.",
        "template_sms":  "Mibanco: {nombre}, su cuota vence pronto. Pague en agente BCP. Consultas: 0800-00-666",
        "template_call": "Buenos días, señor/a {nombre}. Le llama Mibanco para informarle que su cuota está próxima a vencer. ¿Requiere ayuda para realizar el pago?",
        "cta":           "pagar en agente",
        "urgencia":      "baja",
    },
    "no_digital_moroso": {
        "descripcion":   "No digital, mora media o alta (> 30d)",
        "tono":          "formal y urgente, con oferta de asesor presencial",
        "saludo":        "Buenos días",
        "emojis":        False,
        "template_wa":   "Buenos días, {nombre}. Su crédito en Mibanco registra días de atraso. Un asesor se pondrá en contacto para ayudarle a regularizar su situación. También puede llamarnos al 0800-00-666.",
        "template_sms":  "Mibanco: {nombre}, tiene mora en su credito. Un asesor le contactara. Info: 0800-00-666",
        "template_call": "Buenos días, señor/a {nombre}. Le llama un asesor de Mibanco. Su crédito tiene días de mora y necesitamos coordinar con usted. ¿Tiene disponibilidad esta semana para una visita de nuestro ejecutivo?",
        "cta":           "hablar con asesor",
        "urgencia":      "alta",
    },
}


def asignar_perfil(cli: dict) -> str:
    """Asigna el perfil M4 dado el dict del cliente."""
    es_digital = bool(cli.get("es_digital", 0))
    # Score fino de digitalidad (igual que rules.py _digital_efectivo)
    inter = float(cli.get("interaccion_digital_score", 0) or 0) / 100.0
    app   = float(cli.get("uso_app", 0) or 0)
    wa    = 1.0 if int(cli.get("uso_whatsapp", 0) or 0) else 0.0
    if inter > 0 or app > 0 or wa > 0:
        score_dig = 0.55 * inter + 0.30 * app + 0.15 * wa
        es_digital = score_dig >= 0.5

    dm    = int(cli.get("dias_mora", 0) or 0)
    sano  = dm <= 30

    if es_digital and sano:     return "digital_sano"
    if es_digital and not sano: return "digital_moroso"
    if not es_digital and sano: return "no_digital_sano"
    return "no_digital_moroso"


def perfil(cli: dict) -> dict:
    """Devuelve el dict completo del perfil M4 para el cliente."""
    key = asignar_perfil(cli)
    p   = PERFILES[key].copy()
    p["perfil_key"] = key
    return p


def mensaje(cli: dict, canal: str = "wa") -> str:
    """Devuelve el mensaje personalizado para el canal dado."""
    p    = perfil(cli)
    nombre = cli.get("nombre", "cliente")
    tpl_key = {"wa": "template_wa", "sms": "template_sms",
                "llamada": "template_call", "campo": "template_call"}.get(canal, "template_wa")
    return p.get(tpl_key, "").replace("{nombre}", nombre)


if __name__ == "__main__":
    casos = [
        {"nombre": "Rosa", "es_digital": 1, "uso_app": 0.7, "dias_mora": 5},
        {"nombre": "Jorge", "es_digital": 0, "uso_app": 0.0, "dias_mora": 45},
        {"nombre": "Maria", "es_digital": 1, "uso_app": 0.6, "dias_mora": 60},
    ]
    for c in casos:
        p = perfil(c)
        print(f"{c['nombre']:10} -> {p['perfil_key']:20} | {mensaje(c, 'wa')[:60]}...")

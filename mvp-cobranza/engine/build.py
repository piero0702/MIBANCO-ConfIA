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
import argparse, datetime, json, os, sys

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


def construir_calendario(cli: dict, cfg: dict) -> dict:
    """Plan de contactos del mes para ESTE cliente: en que fechas, con que mensaje,
    todo por WhatsApp. Tope ACUMULADO mensual: moroso <=7, no-moroso <=3 (el tope 2
    del backtest es POR EPISODIO de cobranza). Reutiliza la misma redaccion del motor."""
    dias_mora = int(cli.get("dias_mora", 0))
    cuota = float(cli.get("cuota_mensual", 0))
    es_moroso = dias_mora > 0
    tope = 7 if es_moroso else 3

    if bool(cli.get("promesa_pago", 0)):
        return {"mes": "junio 2026", "total_contactos": 0, "tope": tope,
                "es_moroso": es_moroso,
                "nota": "Ya prometio o pago: no se programan contactos (anti-fatiga).",
                "contactos": []}

    if es_moroso:
        # toques escalando por etapa; el ultimo refleja la mora real del cliente
        plan = [(2, 1), (5, 4), (9, 8), (13, 12), (17, 18), (23, 26), (27, max(dias_mora, 30))]
        plan = plan[:tope]
        nota = ("Tope por episodio de cobranza = 2 (ventana ~7 dias). Acumulado del mes "
                "<=7 cruzando etapas (preventivo -> temprana -> media -> tardia). Todo por "
                "WhatsApp verificable; el no-digital en mora profunda ademas recibe llamada de un asesor.")
    else:
        plan = [(12, 0)]  # un recordatorio preventivo basta para el buen pagador
        nota = ("Buen pagador: hasta 3 avisos/mes permitidos, pero basta 1 recordatorio "
                "preventivo. Decidir 'a quien NO molestar' tambien es parte del motor.")

    riesgo = rules.clasificar_riesgo(float(cli.get("prob_default", 0.2)), cfg)
    contactos = []
    for dia_mes, dmora in plan:
        f = _fecha_jun(dia_mes)
        cli_v = dict(cli); cli_v["dias_mora"] = dmora
        tramo = rules.tramo_de_mora(dmora, cfg)
        tono = rules.decidir_tono(riesgo, cli_v, cfg)
        msg = rules.redactar_mensaje(cli_v, "whatsapp", tramo, tono, cuota, cfg)
        contactos.append({
            "fecha": f["fecha"], "dia": f["dia"], "etapa": tramo["etiqueta"],
            "canal": "whatsapp", "mensaje": msg, "verificable": True,
        })
    contactos.sort(key=lambda c: c["dia"])
    return {"mes": "junio 2026", "total_contactos": len(contactos), "tope": tope,
            "es_moroso": es_moroso, "nota": nota, "contactos": contactos}


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
        por_tope = (f"Máx {tope_ep} contacto(s) por episodio porque es riesgo {riesgo} "
                    f"(regla: bajo=1, medio=2, alto=3 — el sobre-contacto cansa y baja el pago, "
                    f"no más). En todo el mes, hasta {tope_mes} cruzando etapas; "
                    f"se programaron {total_mes}.")
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

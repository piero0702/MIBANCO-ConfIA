"""
Motor YateKobro — cobranza opt-in que el cliente se cobra solo.

Mecanica (sustentada en CONTEXTO PARA SOLUCION.mkd):
  - El cliente activa un % por cada venta que recibe por Yape.
  - Ese % se imputa PRIMERO al interes del mes, luego al capital
    (Res. SBS 3274-2017 Art. 29.2: el prepago va a capital reduciendo interes).
  - Se notifica SOLO en 3 momentos: interes 50%, interes 100% (estrella), cuota completa.
  - Al completar la cuota, YateKobro se apaga solo (auto-stop). Nunca persigue.

Es un motor real y determinista (seed): dada la venta diaria por Yape, produce
el ledger dia a dia, los eventos/notificaciones y el resumen. Sin dependencias.

Correr directo:  python yatekobro.py
"""
from __future__ import annotations
import json, random


# ----------------------------------------------------------------------------- #
# 1) Amortizacion: de donde sale "interes vs capital" de la cuota del mes
# ----------------------------------------------------------------------------- #
def amortizacion(saldo: float, tasa_ea: float, plazo_meses: int, mes: int = 1) -> dict:
    """
    Cuota francesa (constante) y descomposicion interes/capital del 'mes' dado.
    tasa_ea = tasa efectiva anual (0.50 = 50%). Devuelve montos del mes.
    """
    i = (1 + tasa_ea) ** (1 / 12) - 1                 # tasa efectiva mensual
    cuota = saldo * i / (1 - (1 + i) ** (-plazo_meses))
    s = saldo
    interes = capital = 0.0
    for m in range(1, mes + 1):
        interes = s * i
        capital = cuota - interes
        s -= capital
    return {
        "cuota": round(cuota, 2),
        "interes": round(interes, 2),
        "capital": round(capital, 2),
        "tasa_mensual": round(i, 5),
        "saldo_inicio_mes": round(saldo if mes == 1 else s + capital, 2),
    }


# ----------------------------------------------------------------------------- #
# 2) Simulacion del flujo de ventas Yape -> imputacion -> eventos
# ----------------------------------------------------------------------------- #
def simular(nombre: str, saldo: float, tasa_ea: float, plazo_meses: int,
            pct: float, ventas_dia_media: float, seed: int = 7,
            max_dias: int = 45, variabilidad: float = 0.35) -> dict:
    """
    Simula dia a dia: el cliente vende ~ventas_dia_media (con variabilidad real),
    aporta pct% de cada dia, se imputa a interes y luego capital, hasta completar
    la cuota o agotar max_dias. Determinista por seed.
    """
    am = amortizacion(saldo, tasa_ea, plazo_meses)
    interes_obj, capital_obj = am["interes"], am["capital"]
    cuota = am["cuota"]

    rng = random.Random(seed)
    interes_ac = capital_ac = 0.0
    ledger, eventos = [], []
    hito_50 = hito_100 = hito_cuota = False
    transacciones = 0

    for dia in range(1, max_dias + 1):
        # ventas del dia con variabilidad (negocio real: dias flojos y buenos)
        factor = 1 + rng.uniform(-variabilidad, variabilidad)
        venta = max(0.0, round(ventas_dia_media * factor, 2))
        # nro de transacciones Yape aprox (ticket promedio ~S/35)
        txs = max(1, round(venta / 35)) if venta > 0 else 0
        transacciones += txs
        aporte = round(venta * pct / 100, 2)

        # imputacion: interes primero, luego capital
        a_interes = min(aporte, max(0.0, interes_obj - interes_ac))
        resto = aporte - a_interes
        a_capital = min(resto, max(0.0, capital_obj - capital_ac))
        interes_ac = round(interes_ac + a_interes, 2)
        capital_ac = round(capital_ac + a_capital, 2)

        ledger.append({
            "dia": dia, "venta": venta, "txs": txs, "aporte": aporte,
            "a_interes": round(a_interes, 2), "a_capital": round(a_capital, 2),
            "interes_ac": interes_ac, "capital_ac": capital_ac,
            "interes_pct": round(interes_ac / interes_obj * 100, 1) if interes_obj else 100.0,
            "capital_pct": round(capital_ac / capital_obj * 100, 1) if capital_obj else 100.0,
        })

        # hitos / notificaciones (solo 3 momentos)
        if not hito_50 and interes_ac >= interes_obj * 0.5:
            hito_50 = True
            eventos.append(_evento("interes_50", dia, nombre, am, interes_ac, capital_ac, transacciones))
        if not hito_100 and interes_ac >= interes_obj - 0.01:
            hito_100 = True
            eventos.append(_evento("interes_100", dia, nombre, am, interes_ac, capital_ac, transacciones))
        if not hito_cuota and capital_ac >= capital_obj - 0.01:
            hito_cuota = True
            eventos.append(_evento("cuota_completa", dia, nombre, am, interes_ac, capital_ac, transacciones))
            break  # AUTO-STOP

    completo = hito_cuota
    return {
        "cliente": nombre,
        "credito": {"saldo": saldo, "tasa_ea": tasa_ea, "plazo_meses": plazo_meses},
        "cuota": cuota, "interes_obj": interes_obj, "capital_obj": capital_obj,
        "pct": pct, "ventas_dia_media": ventas_dia_media,
        "ledger": ledger, "eventos": eventos,
        "resumen": {
            "completo": completo,
            "dia_interes_vencido": next((e["dia"] for e in eventos if e["tipo"] == "interes_100"), None),
            "dia_cuota_completa": next((e["dia"] for e in eventos if e["tipo"] == "cuota_completa"), None),
            "dias_simulados": len(ledger),
            "total_aportado": round(interes_ac + capital_ac, 2),
            "transacciones": transacciones,
            "contactos_cobranza": 0,  # el diferenciador: cero llamadas
        },
    }


# ----------------------------------------------------------------------------- #
# 3) Mensajes WhatsApp verificables (identidad oficial, anti-extorsion)
# ----------------------------------------------------------------------------- #
def _evento(tipo: str, dia: int, nombre: str, am: dict,
            interes_ac: float, capital_ac: float, txs: int) -> dict:
    n = nombre.split()[0]
    cuota, interes, capital = am["cuota"], am["interes"], am["capital"]
    falta = round(max(0.0, (interes + capital) - (interes_ac + capital_ac)), 0)
    if tipo == "interes_50":
        msg = (f"📊 YoSiLa — {n}: ya cubriste el 50% del interes de este mes "
               f"(S/{interes_ac:.0f} de S/{interes:.0f}). Seguimos 💪")
        titulo = "Interes 50%"
    elif tipo == "interes_100":
        msg = (f"🎉 ¡{n}, ya cubriste el 100% del interes!\n"
               f"Lo que te queda (S/{capital:.0f}) es plata tuya que estas devolviendo, "
               f"no costo del banco. Llevas {dia} dias, {txs} transacciones.")
        titulo = "Interes 100% (estrella)"
    else:  # cuota_completa
        msg = (f"✅ ¡Cuota PAGADA, {n}! YoSiLa se paro automatico.\n"
               f"¿Quieres adelantar la proxima cuota y seguir reduciendo interes? "
               f"Responde SI o NO.")
        titulo = "Cuota completa -> auto-stop"
    return {"tipo": tipo, "dia": dia, "titulo": titulo,
            "mensaje": f"*Mibanco* ✅ {msg}", "verificable": True, "falta": falta}


# ----------------------------------------------------------------------------- #
# Demo CLI: ver el motor funcionar
# ----------------------------------------------------------------------------- #
def _print_demo(sim: dict) -> None:
    r, am_cuota = sim["resumen"], sim["cuota"]
    print(f"\n=== YateKobro · {sim['cliente']} ===")
    print(f"Credito S/{sim['credito']['saldo']:.0f} a {sim['credito']['plazo_meses']}m "
          f"({sim['credito']['tasa_ea']*100:.0f}% EA)  ->  cuota S/{am_cuota:.0f} "
          f"= interes S/{sim['interes_obj']:.0f} + capital S/{sim['capital_obj']:.0f}")
    print(f"Activa YateKobro al {sim['pct']:.0f}% · ventas Yape ~S/{sim['ventas_dia_media']:.0f}/dia\n")
    print(f"{'dia':>3} {'venta':>7} {'aporte':>7} {'interes':>13} {'capital':>13}")
    for L in sim["ledger"]:
        print(f"{L['dia']:>3} {L['venta']:>7.0f} {L['aporte']:>7.1f} "
              f"{('S/'+format(L['interes_ac'],'.0f')+'/'+format(sim['interes_obj'],'.0f')):>13} "
              f"{('S/'+format(L['capital_ac'],'.0f')+'/'+format(sim['capital_obj'],'.0f')):>13}")
    print("\n--- Notificaciones emitidas (solo 3 momentos) ---")
    for e in sim["eventos"]:
        print(f"  [dia {e['dia']:>2}] {e['titulo']}")
        for line in e["mensaje"].split("\n"):
            print(f"           {line}")
    print(f"\nInteres vencido el dia {r['dia_interes_vencido']} · "
          f"cuota completa el dia {r['dia_cuota_completa']} · "
          f"contactos de cobranza: {r['contactos_cobranza']}  (auto-stop)\n")


if __name__ == "__main__":
    # Caso Rosa del documento: S/3000, 12m, ~50% EA, 2%, ventas S/1000/dia
    sim = simular("Rosa Chaparro", saldo=3000, tasa_ea=0.50, plazo_meses=12,
                  pct=2, ventas_dia_media=1000, seed=7)
    _print_demo(sim)

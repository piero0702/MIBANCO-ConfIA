"""
Yosila — Procesador en tiempo real de yapeos para clientes YateKobro.

Cada vez que un cliente activo en YateKobro recibe una venta por Yape,
Yosila procesa el evento automaticamente:
  1. Recibe el yapeo (webhook en produccion: monto + telefono + timestamp).
  2. Calcula el aporte segun el % acordado por el cliente.
  3. Imputa: interes primero, luego capital (SBS 3274-2017 Art. 29.2).
  4. Detecta hitos (interes 50%, 100%, cuota completa).
  5. Emite notificacion WhatsApp solo si hay hito (no antes, no despues).
  6. Auto-stop al completar la cuota. Nunca persigue, nunca llama.

En produccion: webhook listener (FastAPI/Lambda) que recibe eventos de Yape,
consulta el plan activo en el CRM de Mibanco y ejecuta la imputacion.
Aqui: simula el stream de transacciones Yape dia a dia (determinista por seed).

Correr directo:  python yosila.py
"""
from __future__ import annotations
import random
from yatekobro import amortizacion, _evento


def generar_stream(nombre: str, saldo: float, tasa_ea: float, plazo_meses: int,
                   pct: float, ventas_dia_media: float,
                   n_dias: int = 7, seed: int = 7) -> dict:
    """
    Genera el stream de eventos Yape individuales para los primeros n_dias.
    Cada elemento = un yapeo entrante que Yosila procesa en tiempo real.
    Determinista por seed.
    """
    am = amortizacion(saldo, tasa_ea, plazo_meses)
    interes_obj, capital_obj = am["interes"], am["capital"]
    cuota = am["cuota"]

    rng = random.Random(seed)
    interes_ac = capital_ac = 0.0
    hito_50 = hito_100 = hito_cuota = False
    transacciones = 0
    stream = []

    for dia in range(1, n_dias + 1):
        if hito_cuota:
            break
        factor = 1 + rng.uniform(-0.35, 0.35)
        venta_dia = max(0.0, round(ventas_dia_media * factor, 2))
        n_txs = max(1, round(venta_dia / 35)) if venta_dia > 0 else 0
        venta_restante = venta_dia

        for _ in range(n_txs):
            if hito_cuota or venta_restante <= 0:
                break
            monto_tx = round(min(35 * rng.uniform(0.5, 1.8), venta_restante), 2)
            venta_restante = max(0, round(venta_restante - monto_tx, 2))
            transacciones += 1

            aporte = round(monto_tx * pct / 100, 2)
            if aporte < 0.01:
                continue

            # Imputacion: interes primero, luego capital (Art. 29.2)
            a_interes = min(aporte, max(0.0, interes_obj - interes_ac))
            resto = aporte - a_interes
            a_capital = min(resto, max(0.0, capital_obj - capital_ac))
            interes_ac = round(interes_ac + a_interes, 2)
            capital_ac = round(capital_ac + a_capital, 2)

            hora = rng.randint(8, 20)
            minuto = rng.randint(0, 59)
            hito = notif = None

            if not hito_50 and interes_ac >= interes_obj * 0.5:
                hito_50 = True
                ev = _evento("interes_50", dia, nombre, am, interes_ac, capital_ac, transacciones)
                hito, notif = "interes_50", ev["mensaje"]
            elif not hito_100 and interes_ac >= interes_obj - 0.01:
                hito_100 = True
                ev = _evento("interes_100", dia, nombre, am, interes_ac, capital_ac, transacciones)
                hito, notif = "interes_100", ev["mensaje"]
            elif not hito_cuota and capital_ac >= capital_obj - 0.01:
                hito_cuota = True
                ev = _evento("cuota_completa", dia, nombre, am, interes_ac, capital_ac, transacciones)
                hito, notif = "cuota_completa", ev["mensaje"]

            stream.append({
                "dia": dia,
                "hora": f"{hora:02d}:{minuto:02d}",
                "monto_tx": monto_tx,
                "aporte": aporte,
                "a_interes": round(a_interes, 2),
                "a_capital": round(a_capital, 2),
                "interes_ac": interes_ac,
                "capital_ac": capital_ac,
                "interes_pct": round(interes_ac / interes_obj * 100, 1) if interes_obj else 100.0,
                "capital_pct": round(capital_ac / capital_obj * 100, 1) if capital_obj else 100.0,
                "hito": hito,
                "notificacion": notif,
            })

    return {
        "cliente": nombre,
        "credito": {"saldo": saldo, "tasa_ea": tasa_ea, "plazo_meses": plazo_meses},
        "cuota": cuota,
        "interes_obj": interes_obj,
        "capital_obj": capital_obj,
        "pct": pct,
        "ventas_dia_media": ventas_dia_media,
        "stream": stream,
        "resumen": {
            "total_yapeos": len(stream),
            "dias_simulados": stream[-1]["dia"] if stream else 0,
            "interes_cubierto_pct": round(interes_ac / interes_obj * 100, 1) if interes_obj else 100.0,
            "capital_cubierto_pct": round(capital_ac / capital_obj * 100, 1) if capital_obj else 100.0,
            "total_aportado": round(interes_ac + capital_ac, 2),
            "hitos_alcanzados": sum([hito_50, hito_100, hito_cuota]),
            "auto_stop": hito_cuota,
            "contactos_cobranza": 0,
        },
    }


if __name__ == "__main__":
    sim = generar_stream("Rosa Chaparro", saldo=3000, tasa_ea=0.50, plazo_meses=12,
                         pct=2, ventas_dia_media=1000, n_dias=5, seed=7)
    print(f"\n=== Yosila Stream · {sim['cliente']} ===")
    print(f"Credito S/{sim['credito']['saldo']} · cuota S/{sim['cuota']:.0f} "
          f"= interes S/{sim['interes_obj']:.0f} + capital S/{sim['capital_obj']:.0f}")
    print(f"YateKobro activo al {sim['pct']}% por venta Yape\n")
    dia_prev = 0
    for e in sim["stream"]:
        if e["dia"] != dia_prev:
            dia_prev = e["dia"]
            print(f"--- Dia {dia_prev} ---")
        mark = "★" if e["hito"] else " "
        print(f"  {mark} {e['hora']} | Yape S/{e['monto_tx']:.0f} → "
              f"auto S/{e['aporte']:.2f} (int {e['interes_pct']:.0f}% / cap {e['capital_pct']:.0f}%)")
        if e["notificacion"]:
            print(f"    → {e['hito'].upper()}")
            for line in e["notificacion"].split("\n"):
                print(f"      {line}")
    r = sim["resumen"]
    print(f"\n{r['total_yapeos']} yapeos · int {r['interes_cubierto_pct']}% · "
          f"cap {r['capital_cubierto_pct']}% · {r['hitos_alcanzados']} hitos · "
          f"contactos cobranza: {r['contactos_cobranza']}")

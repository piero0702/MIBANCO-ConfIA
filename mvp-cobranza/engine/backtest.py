"""
Backtest de la politica AsesorIA sobre la tabla de contactos.

Compara la gestion ACTUAL (lo que hay en la data) contra la POLITICA AsesorIA:
  - Tope de 2 contactos por credito (anti-fatiga, insight data#4 + entrevistas#2).
  - Canal segun perfil digital (data#6): digital -> WhatsApp, no-digital -> llamada.
  - No se inventa el resultado: el costo se recalcula con los costos reales por canal
    (config.json) y la tasa de pago con las tasas por canal x perfil del dataset.

Corre sobre los xlsx reales si estan en ../data_cobranzas/. Si no, genera una tabla
de contactos sintetica consistente con las estadisticas del dataset (canal mix,
~5.7 contactos/credito, costos y tasas de config) y corre la MISMA politica.

Correr directo:  python backtest.py
"""
from __future__ import annotations
import os, random, glob

import rules
from data_loader import _limpiar_tramo_mora, _leer_tabla, datos_reales_disponibles


# ----------------------------------------------------------------------------- #
# Carga de la tabla de contactos (real o sintetica)
# ----------------------------------------------------------------------------- #
def cargar_contactos(max_filas: int | None = None) -> tuple[list[dict], str]:
    """Devuelve (contactos, fuente). Cada contacto: credito_id, es_digital,
    canal_contacto, costo_contacto, pago_7d_post_contacto, intento_num.
    Lee de la cache CSV (rapido) o el xlsx; si no hay, cae a sinteticos."""
    if datos_reales_disponibles():
        try:
            df = _limpiar_tramo_mora(_leer_tabla("contactos", ["*ontactos*.xlsx"]))
            # perfil digital desde clientes si esta
            cli = _leer_tabla("clientes", ["*Clientes*.xlsx"])
            if cli is not None and "es_digital" in cli.columns:
                df = df.merge(cli[["cliente_id", "es_digital"]], on="cliente_id", how="left")
            if max_filas:
                df = df.head(max_filas)
            cols = ["credito_id", "es_digital", "canal_contacto", "costo_contacto",
                    "pago_7d_post_contacto", "intento_num"]
            df = df[[c for c in cols if c in df.columns]].copy()
            return df.to_dict(orient="records"), "real"
        except Exception as e:  # pragma: no cover
            print(f"[backtest] No pude leer contactos reales ({e}); uso sinteticos.")
    return _contactos_sinteticos(), "sintetico"


def _contactos_sinteticos(n_creditos: int = 8000, seed: int = 7) -> list[dict]:
    """Tabla de contactos coherente con el dataset: canal mix real, ~5.7
    contactos/credito, costos de config, pago segun tasa por canal x perfil."""
    cfg = rules.load_config()
    canales = cfg["canales"]
    ajuste = cfg["ajuste_canal_por_perfil_digital"]
    rng = random.Random(seed)
    mix = [("llamada", 0.38), ("whatsapp", 0.34), ("sms", 0.22), ("campo", 0.06)]
    nombres, pesos = [m[0] for m in mix], [m[1] for m in mix]

    contactos = []
    for cid in range(1, n_creditos + 1):
        es_digital = 1 if rng.random() < 0.65 else 0
        # nro de contactos del credito: centrado en ~5.7 (1..12)
        n = max(1, min(12, round(rng.gauss(5.7, 2.0))))
        for intento in range(1, n + 1):
            canal = rng.choices(nombres, weights=pesos)[0]
            tasa = canales[canal]["pago_7d"] * ajuste["digital" if es_digital else "no_digital"][canal]
            # la fatiga baja el pago a mayor intento (insight data#4)
            tasa *= max(0.75, 1 - 0.03 * (intento - 1))
            contactos.append({
                "credito_id": cid,
                "es_digital": es_digital,
                "canal_contacto": canal,
                "costo_contacto": canales[canal]["costo"],
                "pago_7d_post_contacto": 1 if rng.random() < tasa else 0,
                "intento_num": intento,
            })
    return contactos


# ----------------------------------------------------------------------------- #
# Backtest
# ----------------------------------------------------------------------------- #
def correr(contactos: list[dict], cfg: dict | None = None) -> dict:
    cfg = cfg or rules.load_config()
    canales = cfg["canales"]
    ajuste = cfg["ajuste_canal_por_perfil_digital"]
    TOPE = cfg["topes_contacto"]["por_riesgo"]["medio"]  # tope base = 2

    # ---- BASELINE (gestion actual) ----
    base_costo = sum(c["costo_contacto"] for c in contactos)
    base_n = len(contactos)
    pagos = [c["pago_7d_post_contacto"] for c in contactos if c.get("pago_7d_post_contacto") is not None]
    base_pago = sum(pagos) / len(pagos) if pagos else 0

    # agrupar por credito
    por_credito: dict = {}
    for c in contactos:
        por_credito.setdefault(c["credito_id"], []).append(c)
    n_creditos = len(por_credito)

    # ---- POLITICA AsesorIA: tope 2 + canal por perfil ----
    pol_costo = 0.0
    pol_pago_contacto_sum = 0.0   # suma de tasas por contacto (para pago/contacto)
    pol_recup_credito = 0.0       # >=1 pago en <=2 intentos (recuperacion a nivel credito)
    pol_contactos = 0
    mix_canal = {"whatsapp": 0, "llamada": 0, "sms": 0, "campo": 0}
    for cid, lista in por_credito.items():
        lista = sorted(lista, key=lambda x: x.get("intento_num", 1))[:TOPE]  # tope
        es_digital = lista[0].get("es_digital", 0)
        canal = "whatsapp" if es_digital else "llamada"      # canal por perfil
        tasa = canales[canal]["pago_7d"] * ajuste["digital" if es_digital else "no_digital"][canal]
        for _ in lista:
            pol_costo += canales[canal]["costo"]
            pol_contactos += 1
            pol_pago_contacto_sum += tasa
            mix_canal[canal] += 1
        pol_recup_credito += 1 - (1 - tasa) ** len(lista)

    pol_pago_contacto = pol_pago_contacto_sum / pol_contactos if pol_contactos else 0
    pol_recup = pol_recup_credito / n_creditos if n_creditos else 0

    return {
        "fuente": None,  # lo setea el caller
        "n_creditos": n_creditos,
        "baseline": {
            "costo_total": round(base_costo, 2),
            "contactos": base_n,
            "contactos_x_credito": round(base_n / n_creditos, 2) if n_creditos else 0,
            "pago_x_contacto": round(base_pago, 4),
            "costo_x_credito": round(base_costo / n_creditos, 2) if n_creditos else 0,
        },
        "politica": {
            "costo_total": round(pol_costo, 2),
            "contactos": pol_contactos,
            "contactos_x_credito": round(pol_contactos / n_creditos, 2) if n_creditos else 0,
            "pago_x_contacto": round(pol_pago_contacto, 4),
            "recuperacion_x_credito": round(pol_recup, 4),
            "costo_x_credito": round(pol_costo / n_creditos, 2) if n_creditos else 0,
            "mix_canal": mix_canal,
        },
        "reduccion_costo_pct": round((base_costo - pol_costo) / base_costo * 100, 1) if base_costo else 0,
        "ahorro_total": round(base_costo - pol_costo, 2),
    }


def correr_auto(max_filas: int | None = None) -> dict:
    contactos, fuente = cargar_contactos(max_filas)
    res = correr(contactos)
    res["fuente"] = fuente
    return res


# ----------------------------------------------------------------------------- #
def _print(res: dict) -> None:
    b, p = res["baseline"], res["politica"]
    soles = lambda n: "S/" + format(round(n), ",d")
    print(f"\n=== Backtest AsesorIA  (fuente: {res['fuente']}, {res['n_creditos']:,} creditos) ===\n")
    print(f"{'':22}{'ACTUAL':>16}{'AsesorIA':>16}")
    print(f"{'Costo total':22}{soles(b['costo_total']):>16}{soles(p['costo_total']):>16}")
    print(f"{'Contactos/credito':22}{b['contactos_x_credito']:>16}{p['contactos_x_credito']:>16}")
    print(f"{'Costo/credito':22}{soles(b['costo_x_credito']):>16}{soles(p['costo_x_credito']):>16}")
    print(f"{'Pago/contacto':22}{format(b['pago_x_contacto']*100,'.1f')+'%':>16}"
          f"{format(p['pago_x_contacto']*100,'.1f')+'%':>16}")
    print(f"\n  -> Reduccion de costo: {res['reduccion_costo_pct']}%  "
          f"(ahorro {soles(res['ahorro_total'])})")
    print(f"  -> Recuperacion a nivel credito (>=1 pago en <=2 intentos): "
          f"{format(p['recuperacion_x_credito']*100,'.1f')}%")
    print(f"  -> Mix de canal de la politica: {p['mix_canal']}\n")


if __name__ == "__main__":
    _print(correr_auto())

"""
Generador de datos sinteticos de respaldo para el PoC.

Crea clientes coherentes con los insights documentados (distribucion de riesgo,
% digital, tramos de mora) e incluye como casos demo a los personajes reales de
las 7 entrevistas, para que el pitch conecte cualitativo + cuantitativo.

Se usa SOLO cuando no estan los xlsx reales en data_cobranzas/.
"""
from __future__ import annotations
import random

# Personajes de las entrevistas (entrevistas/*). Perfiles fieles a las transcripciones.
PERSONAJES = [
    # nombre, es_digital, prob_default, ratio_pago, atrasos, dias_mora, saldo, cuota, nota
    ("Rosa Chaparro",   1, 0.08, 0.96, 0, 0,   1200, 320, "Buena pagadora, al día. Harta del sobre-contacto. 'No me traten como deudora'."),
    ("Arnaldo Diaz",    1, 0.10, 0.94, 1, 0,   2600, 540, "Se autogestiona, valora aviso 3-4d antes (como Yape). Prefiere correo/digital."),
    ("Powel Aliaga",    0, 0.22, 0.80, 2, 6,    900, 260, "Abre a las 5am en Caqueta: nunca contactar en la mañana."),
    ("Jose (entrev.)",  0, 0.18, 0.85, 1, 12,  1500, 380, "Odia las llamadas robotizadas, prefiere correo. Tono cercano."),
    ("Alessia Borrelli",1, 0.28, 0.72, 3, 22,  1800, 450, "Flujo variable: pide flexibilidad / pago parcial."),
    ("Janet (entrev.)", 1, 0.35, 0.68, 4, 35,  3200, 700, "Bloquea todo por las 8-10 llamadas/dia. Miedo a extorsion: exige canal verificable."),
    ("William (entrev.)",0,0.46, 0.55, 6, 65,  4800, 980, "Rechaza llamadas no identificadas (extorsion). Alto riesgo, alto monto."),
]

REGIONES = ["Lima", "Arequipa", "Cusco", "Trujillo", "Piura", "Junin"]
ZONAS = ["urbano", "rural"]


def _rand_cliente(i: int, rng: random.Random) -> dict:
    riesgo_roll = rng.random()
    if riesgo_roll < 0.45:           # bajo
        prob_default = rng.uniform(0.02, 0.15); ratio = rng.uniform(0.88, 0.99); atrasos = rng.randint(0, 1)
    elif riesgo_roll < 0.80:         # medio
        prob_default = rng.uniform(0.15, 0.40); ratio = rng.uniform(0.70, 0.90); atrasos = rng.randint(1, 3)
    else:                            # alto
        prob_default = rng.uniform(0.40, 0.85); ratio = rng.uniform(0.40, 0.72); atrasos = rng.randint(3, 8)

    es_digital = 1 if rng.random() < 0.58 else 0
    # tramo de mora con sesgo a mora temprana (donde esta el dinero)
    dias_mora = rng.choices(
        [0, rng.randint(1, 7), rng.randint(8, 30), rng.randint(31, 60), rng.randint(61, 120)],
        weights=[30, 28, 22, 12, 8],
    )[0]
    cuota = rng.choice([180, 240, 320, 420, 560, 700, 900])
    saldo = round(cuota * rng.uniform(1.5, 8), 0)
    return {
        "cliente_id": f"SYN-{i:04d}",
        "nombre": f"Cliente {i:04d}",
        "edad": rng.randint(24, 62),
        "genero": rng.choice(["F", "M"]),
        "region": rng.choice(REGIONES),
        "zona": rng.choice(ZONAS),
        "tipo_cliente": rng.choice(["nuevo", "recurrente"]),
        "es_digital": es_digital,
        "prob_default": round(prob_default, 3),
        "ratio_pago": round(ratio, 3),
        "num_atrasos_previos": atrasos,
        "dias_mora": dias_mora,
        "saldo_restante": saldo,
        "cuota_mensual": cuota,
        "promesa_pago": 1 if rng.random() < 0.10 else 0,
        "nota": "",
    }


def personajes_entrevistas() -> list[dict]:
    """Los 7 entrevistados reales como clientes (ids ENT-01..07). Se usan tanto en
    modo sintetico como sobre data real (para que la lista tenga personas con nombre
    y cita, no solo ids anonimos)."""
    out = []
    for k, p in enumerate(PERSONAJES):
        nombre, dig, pd, rp, atr, mora, saldo, cuota, nota = p
        out.append({
            "cliente_id": f"ENT-{k+1:02d}",
            "nombre": nombre,
            "edad": 38, "genero": "F" if k % 2 == 0 else "M",
            "region": "Lima", "zona": "urbano", "tipo_cliente": "recurrente",
            "es_digital": dig, "prob_default": pd, "ratio_pago": rp,
            "num_atrasos_previos": atr, "dias_mora": mora,
            "saldo_restante": saldo, "cuota_mensual": cuota,
            "promesa_pago": 0, "nota": nota,
        })
    return out


def generar(n: int = 120, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    # 1) personajes reales primero (salen arriba en la demo)
    clientes = personajes_entrevistas()
    # 2) relleno sintetico
    for i in range(1, n - len(PERSONAJES) + 1):
        clientes.append(_rand_cliente(i, rng))
    return clientes


if __name__ == "__main__":
    cs = generar(20)
    print(f"{len(cs)} clientes generados. Primeros 2:")
    import json
    print(json.dumps(cs[:2], ensure_ascii=False, indent=2))

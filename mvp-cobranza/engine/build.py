"""
Pipeline del PoC: datos -> motor -> JSON para la web.

Corre:  python3 engine/build.py [--muestra 300]
Genera: web/data/clientes.json  (decision por cliente)
        web/data/kpis.json       (impacto agregado de la cartera)
        web/data/config.json      (copia de los umbrales, para 'what-if' en la web)
"""
from __future__ import annotations
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(__file__))
import rules
from data_loader import cargar

HERE = os.path.dirname(__file__)
WEB_DATA = os.path.join(HERE, "..", "web", "data")


def construir(muestra: int = 300) -> dict:
    cfg = rules.load_config()
    clientes, fuente = cargar(muestra)
    decisiones = [rules.decidir(c, cfg) for c in clientes]
    # adjuntar la nota del personaje (si la hay) para el storytelling
    for c, d in zip(clientes, decisiones):
        d["nota"] = c.get("nota", "")
    decisiones.sort(key=lambda d: d["prioridad"], reverse=True)
    kpis = agregar_kpis(decisiones, fuente, cfg)
    return {"clientes": decisiones, "kpis": kpis, "config": cfg}


def agregar_kpis(decisiones: list[dict], fuente: str, cfg: dict) -> dict:
    n = len(decisiones)
    ahorro_total = sum(d["impacto"]["ahorro_soles"] for d in decisiones)
    recup_total = sum(d["impacto"]["recuperacion_esperada"] for d in decisiones)
    costo_ia = sum(d["impacto"]["costo_ia"] for d in decisiones)
    costo_actual = sum(d["impacto"]["costo_actual_estimado"] for d in decisiones)

    # mix de canales que recomienda la IA
    mix = {}
    for d in decisiones:
        c = d["decision"]["canal"]["canal"]
        mix[c] = mix.get(c, 0) + 1
    mix_pct = {k: round(v / n * 100, 1) for k, v in mix.items()}

    contactos_ia = sum(max(d["decision"]["frecuencia"]["tope_contactos"], 0) for d in decisiones)
    contactos_actual = cfg["baseline"]["contactos_por_credito"] * n

    # Extrapolacion a la cartera total (50k clientes) — para el pitch
    factor = cfg["baseline"]["total_clientes"] / n if n else 0
    return {
        "fuente_datos": fuente,
        "n_clientes": n,
        "ahorro_muestra_soles": round(ahorro_total, 2),
        "ahorro_pct": round((costo_actual - costo_ia) / costo_actual * 100, 1) if costo_actual else 0,
        "recuperacion_esperada_soles": round(recup_total, 2),
        "contactos_ia": contactos_ia,
        "contactos_actual": round(contactos_actual, 0),
        "reduccion_contactos_pct": round((1 - contactos_ia / contactos_actual) * 100, 1) if contactos_actual else 0,
        "mix_canales_ia_pct": mix_pct,
        "digital_first_pct": round((mix.get("whatsapp", 0) + mix.get("sms", 0)) / n * 100, 1) if n else 0,
        "extrapolacion_cartera": {
            "clientes_totales": cfg["baseline"]["total_clientes"],
            "ahorro_anual_estimado_soles": round(ahorro_total * factor, 0),
            "nota": "Extrapolacion lineal de la muestra a 50k clientes. Referencial.",
        },
        "baseline": cfg["baseline"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--muestra", type=int, default=300)
    args = ap.parse_args()

    out = construir(args.muestra)
    os.makedirs(WEB_DATA, exist_ok=True)
    with open(os.path.join(WEB_DATA, "clientes.json"), "w", encoding="utf-8") as f:
        json.dump(out["clientes"], f, ensure_ascii=False)
    with open(os.path.join(WEB_DATA, "kpis.json"), "w", encoding="utf-8") as f:
        json.dump(out["kpis"], f, ensure_ascii=False, indent=2)
    with open(os.path.join(WEB_DATA, "config.json"), "w", encoding="utf-8") as f:
        json.dump(out["config"], f, ensure_ascii=False)

    k = out["kpis"]
    print(f"OK  fuente={k['fuente_datos']}  clientes={k['n_clientes']}")
    print(f"    ahorro muestra: S/{k['ahorro_muestra_soles']:.0f}  ({k['ahorro_pct']}% costo)")
    print(f"    contactos: {k['contactos_ia']} (IA) vs {k['contactos_actual']:.0f} (actual)  -{k['reduccion_contactos_pct']}%")
    print(f"    digital-first: {k['digital_first_pct']}%   mix={k['mix_canales_ia_pct']}")
    print(f"    -> web/data/*.json")


if __name__ == "__main__":
    main()

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
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(__file__))
import rules
import backtest
import yatekobro
from data_loader import cargar

HERE = os.path.dirname(__file__)
WEB_DATA = os.path.join(HERE, "..", "web", "data")


# --------------------------------------------------------------------------- #
# 1) AsesorIA: decision por cliente
# --------------------------------------------------------------------------- #
def construir_clientes(muestra: int) -> tuple[list[dict], str]:
    cfg = rules.load_config()
    clientes, fuente = cargar(muestra)
    decisiones = []
    for c in clientes:
        d = rules.decidir(c, cfg)
        d["nota"] = c.get("nota", "")
        # senal de no-contactar por fatiga (tope alcanzado) para la lab
        d["accion"] = "NO CONTACTAR" if d["decision"]["frecuencia"]["tope_contactos"] == 0 else "CONTACTAR"
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

    # 2) Backtest de la politica (computado)
    bt = backtest.correr_auto()
    _dump("backtest.json", bt)

    # 3) YateKobro (motor corriendo sobre casos)
    yk = construir_yatekobro()
    _dump("yatekobro.json", yk)

    # 4) config para el what-if en vivo
    _dump("config.json", cfg)

    print(f"OK  AsesorIA: {len(clientes)} clientes (fuente {fuente})")
    print(f"    Backtest: -{bt['reduccion_costo_pct']}% costo  "
          f"(actual {bt['baseline']['costo_x_credito']}/cred -> "
          f"AsesorIA {bt['politica']['costo_x_credito']}/cred, fuente {bt['fuente']})")
    print(f"    YateKobro: {len(yk['casos'])} casos simulados")
    print(f"    -> web/data/*.json")


def _dump(name: str, obj) -> None:
    with open(os.path.join(WEB_DATA, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


if __name__ == "__main__":
    main()

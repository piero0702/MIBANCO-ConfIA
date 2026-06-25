"""
Cargador de datos del PoC.

Si existen los xlsx reales del reto en ../data_cobranzas/ los carga, limpia y une
las 3 tablas (clientes + creditos + contactos) en un registro por cliente listo
para el motor. Si NO existen, cae a datos sinteticos (synthetic.py).

Tablas esperadas (ver README.md del proyecto):
  01 Tabla de Clientes.xlsx   (50,000)  -> perfil + riesgo + comportamiento
  02 Tabla de Creditos.xlsx   (194,664) -> historico mensual por credito
  03 Tabla_contactos (1).xlsx (572,553) -> 1 fila por intento de contacto
"""
from __future__ import annotations
import glob
import os

# Carpeta de datos reales. La primera ruta apunta al data_cobranzas del proyecto
# (raiz "innv digital/examen/"); las demas son fallbacks segun el README.
_HERE = os.path.dirname(__file__)
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "..", ".."))  # -> "innv digital"
DATA_DIRS = [
    os.path.join(_ROOT, "examen", "data_cobranzas"),
    os.path.join(_HERE, "..", "..", "data_cobranzas"),
    os.path.join(_HERE, "..", "data_cobranzas"),
    os.path.join(_HERE, "..", "..", "MIBANCO", "data_cobranzas"),
    r"c:\Users\chori\OneDrive\Documentos\ULIMA\2026-1\innv digital\examen\data_cobranzas",
]


def _find(patron: str) -> str | None:
    for d in DATA_DIRS:
        hits = glob.glob(os.path.join(d, patron))
        if hits:
            return hits[0]
    return None


def _cache_csv(kind: str) -> str | None:
    """Ruta al CSV de cache (_cache/{kind}.csv) si existe. Mucho mas rapido que el
    xlsx (el de contactos pesa ~98MB)."""
    for d in DATA_DIRS:
        c = os.path.join(d, "_cache", kind + ".csv")
        if os.path.exists(c):
            return c
    return None


def _leer_tabla(kind: str, patrones: list[str]):
    """Devuelve un DataFrame de la tabla `kind` (clientes/creditos/contactos),
    prefiriendo el CSV de cache; si no, el xlsx. None si no hay nada."""
    import pandas as pd
    c = _cache_csv(kind)
    if c:
        return pd.read_csv(c)
    for p in patrones:
        f = _find(p)
        if f:
            return pd.read_excel(f)
    return None


def datos_reales_disponibles() -> bool:
    return _cache_csv("clientes") is not None or _find("*Clientes*.xlsx") is not None


def _limpiar_tramo_mora(df):
    """Insight data#10: el tramo '01-30' se exporto corrupto como fecha
    '2030-01-01 00:00:00'. Lo normalizamos."""
    if "tramo_mora" not in df.columns:
        return df
    df["tramo_mora"] = (
        df["tramo_mora"].astype(str).str.replace("2030-01-01 00:00:00", "01-30", regex=False)
    )
    return df


def cargar_reales(muestra: int | None = 300) -> list[dict]:
    """Carga y une las 3 tablas reales (cache CSV o xlsx) -> lista de dicts por cliente."""
    cli = _leer_tabla("clientes", ["*Clientes*.xlsx"])
    cred = _leer_tabla("creditos", ["*[Cc]r*ditos*.xlsx", "*Creditos*.xlsx"])
    cont = _leer_tabla("contactos", ["*ontactos*.xlsx"])
    cred = _limpiar_tramo_mora(cred) if cred is not None else None
    cont = _limpiar_tramo_mora(cont) if cont is not None else None

    # Estado mas reciente del credito por cliente
    if cred is not None and "fecha_corte" in cred.columns:
        cred = cred.sort_values("fecha_corte").groupby("cliente_id", as_index=False).last()

    df = cli.copy()
    if cred is not None:
        cols = [c for c in ["cliente_id", "credito_id", "dias_mora", "tramo_mora",
                             "saldo_restante", "cuota_mensual", "estado_credito"]
                if c in cred.columns]
        df = df.merge(cred[cols], on="cliente_id", how="left")

    # Senal de promesa de pago desde contactos (ultimo resultado)
    if cont is not None and "respuesta_cliente" in cont.columns:
        ult = cont.sort_values("fecha_contacto").groupby("cliente_id", as_index=False).last() \
            if "fecha_contacto" in cont.columns else cont.groupby("cliente_id", as_index=False).last()
        ult["promesa_pago"] = ult["respuesta_cliente"].astype(str).str.contains(
            "promet", case=False, na=False).astype(int)
        df = df.merge(ult[["cliente_id", "promesa_pago"]], on="cliente_id", how="left")

    if muestra:
        # priorizar variedad: mezclar tramos de mora
        df = df.sample(min(muestra, len(df)), random_state=7)

    return [_normalizar(r) for r in df.to_dict(orient="records")]


def _normalizar(r: dict) -> dict:
    """Asegura los campos que el motor necesita, con defaults razonables."""
    def g(*keys, default=0):
        for k in keys:
            if k in r and r[k] == r[k]:  # not NaN
                return r[k]
        return default
    nombre = g("nombre", "cliente_nombre", default=None) or f"Cliente {g('cliente_id', default='?')}"
    return {
        "cliente_id": g("cliente_id", default=None),
        "nombre": nombre,
        "edad": g("edad"),
        "region": g("region", default=""),
        "zona": g("zona", default=""),
        "tipo_cliente": g("tipo_cliente", default=""),
        "es_digital": int(g("es_digital", default=0) or 0),
        "prob_default": float(g("prob_default", default=0.2) or 0.2),
        "ratio_pago": float(g("ratio_pago", default=0.8) or 0.8),
        "num_atrasos_previos": int(g("num_atrasos_previos", default=0) or 0),
        "dias_mora": int(g("dias_mora", default=0) or 0),
        "saldo_restante": float(g("saldo_restante", default=0) or 0),
        "cuota_mensual": float(g("cuota_mensual", default=0) or 0),
        "promesa_pago": int(g("promesa_pago", default=0) or 0),
        "nota": "",
    }


def cargar(muestra: int | None = 300) -> tuple[list[dict], str]:
    """Devuelve (clientes, fuente). fuente in {'real','sintetico'}."""
    if datos_reales_disponibles():
        try:
            return cargar_reales(muestra), "real"
        except Exception as e:  # pragma: no cover
            print(f"[data_loader] Error leyendo xlsx reales ({e}); uso sinteticos.")
    from synthetic import generar
    return generar(muestra or 120), "sintetico"


if __name__ == "__main__":
    cs, fuente = cargar(10)
    print(f"Fuente: {fuente} | {len(cs)} clientes")
    for c in cs[:3]:
        print(" -", c["nombre"], "| mora", c["dias_mora"], "| digital", c["es_digital"])

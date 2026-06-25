#!/usr/bin/env bash
# PoC Cobranza Inteligente — Mibanco IAthon
# 1) corre el motor sobre los datos (reales si estan en ../data_cobranzas, si no sinteticos)
# 2) levanta la web demo
set -e
cd "$(dirname "$0")"

MUESTRA="${1:-300}"
PORT="${2:-8765}"

echo "▶ Construyendo decisiones (muestra=$MUESTRA)…"
python3 engine/build.py --muestra "$MUESTRA"

echo
echo "▶ Web demo en  http://localhost:$PORT"
echo "  (Ctrl+C para detener)"
cd web
python3 -m http.server "$PORT"

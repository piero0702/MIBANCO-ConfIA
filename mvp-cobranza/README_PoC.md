# PoC — Motor de Cobranza Inteligente (Mibanco · IAthon)

Prueba de concepto del **Reto 1: Reinventando la Cobranza Inteligente**. Un motor de
decisión con IA + una web demo navegable que, para cada cliente, decide **a quién, por
qué canal, en qué momento, con qué frecuencia y con qué tono** contactar — para que
pague sin sentirse perseguido, recuperando más y gastando menos.

Cada regla del motor está sustentada en los insights del proyecto (entrevistas + 572k
contactos). Ver `engine/config.json` (cada constante cita su insight).

## Cómo correr

```bash
cd mvp-cobranza
./run.sh                 # build + servidor en http://localhost:8765
# o manual:
python3 engine/build.py --muestra 300
cd web && python3 -m http.server 8765
```

Abre **http://localhost:8765**.

## Datos: reales vs demo

- Si colocas los xlsx reales del reto en **`../data_cobranzas/`** (junto a `mvp-cobranza/`),
  el motor los carga, **limpia el bug de `tramo_mora`** (insight #10) y une las 3 tablas.
  Nombres esperados: `*Clientes*.xlsx`, `*Creditos*.xlsx`, `*ontactos*.xlsx`.
- Si no están, usa **datos sintéticos** coherentes con los insights, que incluyen como
  casos demo a los **7 entrevistados** (Rosa, Janet, William, …). La cabecera de la web
  indica qué fuente está usando.

## Arquitectura

```
mvp-cobranza/
├── engine/                  ← EL MOTOR (Python puro, sin deps salvo pandas para xlsx)
│   ├── config.json          ← constantes/umbrales (cada una cita su insight) ← SINGLE SOURCE OF TRUTH
│   ├── rules.py             ← lógica de decisión (canal/momento/frecuencia/tono/mensaje/prioridad/impacto)
│   ├── data_loader.py       ← carga xlsx reales + limpieza + join (fallback a sintético)
│   ├── synthetic.py         ← datos demo + personajes de las entrevistas
│   └── build.py             ← corre el motor sobre la cartera → web/data/*.json
├── web/                     ← LA DEMO (HTML/CSS/JS, cero dependencias)
│   ├── index.html · styles.css · app.js
│   └── data/                ← generado por build.py (clientes/kpis/config)
├── run.sh
└── README_PoC.md
```

## Qué decide el motor (y con qué insight)

| Decisión | Regla | Insight |
|---|---|---|
| **Canal** | Valor neto esperado (recuperación − costo). WhatsApp oficial por defecto; llamada/campo solo si el alto monto/riesgo paga su costo | data#1, #6, #8 · entrevistas#3 (verificable, anti-extorsión) |
| **Momento** | Preventivo 2-4d antes; evita la mañana; Lun-Vie 7-19h | entrevistas#9 · brief |
| **Frecuencia** | Tope por riesgo (1/2/3) vs ~5.7 actual; 0 si ya prometió/pagó | data#4 · entrevistas#2 |
| **Tono** | Cercano / agradecido (buen pagador) / empático (alto riesgo); tutear | entrevistas#8, #4 |
| **Prioridad** | Mora temprana + monto + riesgo; buen pagador baja | data#5, #7 |

## Para el pitch (3 min)

1. **KPIs arriba**: % menos costo, −% contactos, digital-first, recuperación, ahorro extrapolado a 50k.
2. **Cola de prioridad**: la IA ordena a quién contactar primero.
3. **Cliente → ANTES vs CON IA**: el contraste (5.7 llamadas ignoradas → 1 WhatsApp verificable y amable),
   con el mensaje renderizado y el *insight de la entrevista* del personaje.
4. **Simulador en vivo**: mueve mora/cuota/digital/riesgo y la IA re-decide al instante.

> El motor es la fuente de verdad (Python); la web muestra sus decisiones precomputadas y,
> para el what-if, usa el mismo `config.json`.

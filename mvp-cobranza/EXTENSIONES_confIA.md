# Extensiones técnicas — Mibanco-confIA

> Documento de ideas / roadmap técnico. **Nada de esto está implementado todavía.**
> Sirve para (a) el pitch, donde hay que mostrar el detalle técnico aunque el MVP esté
> hardcodeado, y (b) la siguiente iteración del dashboard del repo.
>
> Tres bloques:
> 1. **Feature nueva de confIA** — prepago sugerido por "buen día" en Yape (NO automático).
> 2. **Visualización** — pulso Yape estilo "Screen Time" de iPhone en el dashboard.
> 3. **Gráfico técnico** — la arquitectura ML/IA de la solución, para mostrarla en la web.

---

## 0. Aclaración: dónde vive cada cosa

| | YoSiLa | Prepago sugerido "buen día" |
|---|---|---|
| **Módulo** | YoSiLa (motor de imputación) | **confIA** (motor de decisión) |
| **Automatización** | Automático: descuenta un % de cada venta Yape | **Manual**: solo sugiere, el cliente decide |
| **Trigger** | Cada venta Yape, mientras esté activo | Un día con ingreso Yape sobre el umbral |
| **Activación** | Opt-in permanente que el cliente configura | Nudge puntual, responde SÍ/NO cada vez |
| **Quién controla el dinero** | El % configurado se mueve solo | Nada se mueve sin que el cliente confirme |
| **Dato Yape usado** | Monto de cada venta individual | Ingreso diario agregado + ticket promedio |

Son complementarios: YoSiLa para quien quiere automatizar y olvidarse; el nudge de "buen día"
para quien quiere mantener el control pero agradece el recordatorio inteligente cuando tiene caja.
Ambos atacan el mismo insight (el cliente quiere flexibilidad y autogestionarse, no que lo persigan).

---

## 1. Feature confIA — Prepago sugerido por "buen día" en Yape

### Idea en una línea
confIA mira el flujo de ventas Yape del cliente, detecta cuándo tuvo un día por encima de lo
normal, y **al día siguiente** (en la ventana de contacto permitida) le manda un mensaje
positivo sugiriéndole adelantar parte de su próxima cuota. No mueve plata: solo sugiere.

> Ejemplo de mensaje:
> *Mibanco* ✅ "Hola Rosa 👋 Vimos que ayer fue un buen día de ventas 💪 Si quieres, puedes
> adelantar una parte de tu próxima cuota y pagar menos intereses. Responde SÍ y te muestro cómo."

### Por qué funciona (sustento)
- **Mental accounting / efecto windfall**: la persona separa mentalmente la plata "extra" de un
  buen día y está más dispuesta a usarla para adelantarse. Es el momento de mayor disposición a pagar.
- **Enmarque positivo**: no dice "tienes una deuda", dice "te fue bien, aprovecha". No avergüenza.
  Esto encaja con el perfil 🟩 (no moroso digital) que se ofende si lo tratan como moroso, y con
  el 🟦 que necesita dignidad.
- **Preserva el control**: es una sugerencia con SÍ/NO, no un descuento automático. El insight de
  las entrevistas fue claro: el cliente no rechaza pagar, rechaza que decidan por él.
- **Convierte el contacto en algo bienvenido**: en vez de un "toque" de cobranza, es un mensaje que
  el cliente percibe como que el banco está de su lado. Re-enmarca toda la relación.

### Mecánica de cálculo (lo técnico)

Datos de entrada (vienen de Yape — Credicorp es dueño de Yape y Mibanco):
- Transacciones diarias del cliente por Yape: monto y conteo.

Métricas que confIA computa por cliente:
```
ticket_promedio        = monto_total_dia / num_transacciones_dia
ingreso_diario_dia     = suma de ventas Yape de hoy
ingreso_baseline       = mediana móvil del ingreso Yape diario de los últimos 30 días
                         (mediana, no promedio: robusta a outliers de un solo día bueno/malo)
umbral_buen_dia        = ingreso_baseline * (1 + α)      con α configurable (~0.30 a 0.40)
```

Disparo del nudge:
```
SI  ingreso_diario_dia > umbral_buen_dia                      (fue un buen día)
Y   el cliente tiene una cuota próxima sin prepagar
Y   NO se excede el tope de contactos del cliente (anti-fatiga)
Y   el cliente no pidió pausa / no tiene YoSiLa cubriendo ya la cuota
ENTONCES, al día siguiente, dentro de la ventana 13:00–18:00 (y respetando sábado = solo digital),
          confIA encola el mensaje de prepago sugerido.
```

### Por qué AL DÍA SIGUIENTE y no en el momento
- En tiempo real se sentiría vigilancia ("me están mirando las ventas al segundo") → invasivo.
- Al día siguiente, dentro del horario permitido, se siente como una reflexión, no monitoreo.
- Le da al cliente la noche: el "buen día" ya quedó en su cabeza como plata extra disponible.

### Encaje con el motor actual
- Es una **señal nueva** que entra a la decisión de momento y mensaje (Modelo 3 y 4, ver bloque 3).
- Respeta el tope de contactos: el nudge **cuenta como contacto**, así que compite con los demás.
  Si el cliente ya está en su tope, no se manda. Nunca rompe la regla anti-fatiga.
- Es un contacto de tipo "positivo/preventivo", distinto del de cobranza. En el ledger se marca aparte.

### Viabilidad legal
- Es solo una sugerencia: el prepago lo ejecuta el cliente manualmente → no necesita el consentimiento
  de débito automático de la Res. SBS 02522-2025 (eso es para YoSiLa).
- Si el cliente acepta, el prepago se imputa primero a interés (Art. 86 Ley 29571 + Res. SBS 3274-2017
  Art. 29.2), igual que YoSiLa.

---

## 2. Visualización — "Pulso Yape" estilo Screen Time

### Qué es
Igual que la pantalla de "Tiempo en pantalla" del iPhone (barras diarias), pero las barras son el
**ingreso Yape por día** del cliente. Hace visible y explicable la detección de "buen día".

```
  Ingreso Yape diario (últimos 14 días)                  ticket promedio: S/ 38
  S/                                                       ingreso típico/día: S/ 1,000
  2200 ┤                          █ ⭐                     umbral buen día: S/ 1,350
  1800 ┤              █ ⭐         █                       ─────────────────────────────
  1350 ┤· · · · · · · █ · · · · · █ · · · · · · ← umbral   ⭐ = día que dispara la
  1000 ┤    █    █    █    █    █  █    █    █             sugerencia de prepago al día
   600 ┤ █  █  █ █  █ █  █ █  █ █  █  █ █  █ █  █          siguiente
       └─────────────────────────────────────────
         L  M  M  J  V  S  D  L  M  M  J  V  S  D
                  ↑                    ↑
               día bueno            día bueno
               → 💬 nudge            → 💬 nudge
               al día sgte           al día sgte
```

### Elementos
- **Barras verticales**, una por día (14–30 días).
- **Línea horizontal punteada** = `umbral_buen_dia`.
- Barras **sobre la línea**: verdes con ⭐ → días que disparan el nudge.
- **Ícono 💬** en el día siguiente a un buen día → al hover muestra el mensaje que confIA enviaría.
- **Tooltip por barra**: monto total del día, número de transacciones, ticket promedio.
- **Encabezado**: ticket promedio, ingreso típico/día (la mediana), umbral.

### Por qué sirve para el pitch
- Toca directo dos criterios de la rúbrica: **Prototipo (25%)** y **Presentación/storytelling (10%)**.
- Hace tangible el "cruce por Yape": demuestra que la decisión no sale de la nada, sale de un dato real.
- Es visualmente familiar (todos conocen el Screen Time) → se entiende en 2 segundos.

### Dónde iría en el repo
- Nueva sección/tab en `web/index.html` (ej. tab "④ Pulso Yape") o dentro del detalle de cada cliente.
- Datos: en el MVP, generados por una corrida hardcodeada (como hoy hace `yatekobro.json`); en
  producción, el feed real de Yape. Etiquetarlo honestamente como demo.

---

## 3. Gráfico técnico — la arquitectura ML/IA de confIA

El MVP precalcula las decisiones (están en `web/data/clientes.json`, generadas por `engine/build.py`).
Eso está bien para demostrar, pero en el pitch hay que mostrar **qué haría el sistema real**. Este
gráfico es esa capa: deja claro que detrás hay 4 modelos entrenables, no reglas inventadas.

> Mensaje clave a poner en la web: *"En el MVP las decisiones están precalculadas. En producción,
> estos 4 modelos se entrenan sobre el dataset real (572,553 contactos con el resultado ya conocido
> = aprendizaje supervisado). El dato de pago real es la etiqueta."*

### Diagrama propuesto

```
  FUENTES DE DATOS
  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐  ┌──────────────┐
  │ Tabla         │  │ Tabla         │  │ Tabla Contactos   │  │ Feed Yape    │
  │ Clientes      │  │ Créditos      │  │ (572k filas con   │  │ (ventas      │
  │ (perfil,      │  │ (saldo,cuota, │  │  pago real = la   │  │  diarias)    │
  │  es_digital)  │  │  días_mora)   │  │  etiqueta a apr.) │  │              │
  └───────┬───────┘  └───────┬───────┘  └─────────┬─────────┘  └──────┬───────┘
          └──────────────────┴────────────────────┴───────────────────┘
                                      ↓
                          ┌───────────────────────┐
                          │  FEATURE ENGINEERING  │
                          │  · score digital      │
                          │  · índice de fatiga   │
                          │  · perfil emocional   │
                          │    (4 cuadrantes)     │
                          │  · días a vencimiento │
                          │  · pulso Yape (§1)    │
                          └───────────┬───────────┘
                                      ↓
        ┌─────────────────────── Mibanco-confIA ───────────────────────┐
        │                                                              │
        │  M1 · ¿Contactar?      P(pago | SIN contacto)  → no molestar │
        │       LightGBM             al que paga solo (buen pagador)   │
        │                                                              │
        │  M2 · ¿Qué canal?      P(pago | canal) por canal →           │
        │       4 clasificadores argmax[ P·cuota − costo ]             │
        │                                                              │
        │  M3 · ¿Cuándo?         franja óptima + buen día Yape (§1)    │
        │       árbol / logística   + restricción Lun-Vie 7-19, Sáb dig│
        │                                                              │
        │  M4 · ¿Tono y mensaje? clasifica perfil (digital×moroso) →   │
        │       reglas sobre 4      tono + canal + ¿ofrecer YoSiLa?    │
        │       perfiles emocion.                                      │
        └──────────────────────────────┬───────────────────────────────┘
                                        ↓
                         ┌─────────────────────────┐
                         │  DECISIÓN + MENSAJE      │
                         │  WhatsApp Business       │
                         │  *Mibanco* ✅ verificable │
                         └─────────────────────────┘
```

### Detalle de cada modelo

**M1 — ¿Vale la pena contactar?** (propensión a pagar solo)
- Predice `P(pago_7d | sin contacto)`. Si es alta → NO CONTACTAR (no gastar en quien paga solo).
- Algoritmo: Gradient Boosting (LightGBM) — liviano, bueno con tablas.
- Features: `ratio_pago`, `num_atrasos_previos`, `dias_mora_promedio`, `prob_pago_7d_base`,
  `tramo_mora`, `ultimo_pago_dias`.

**M2 — ¿Qué canal?** (valor neto esperado)
- Predice `P(pago_7d_post_contacto | canal)` para cada canal. Decide `argmax[ P·cuota − costo ]`.
- Algoritmo: 4 clasificadores binarios (uno por canal) tipo XGBoost.
- Features: `es_digital`, `interaccion_digital_score`, `uso_whatsapp`, `canal_*` (permisos),
  `fatiga_contacto`, `intento_num`, `respuesta_ultimo_contacto`, `tramo_mora`.
- Dato oficial del reto que valida el modelo: Digital→WhatsApp 50% vs Llamada 10% de pago/contacto.

**M3 — ¿Cuándo?** (timing)
- Predice `P(pago_7d | hora, día_semana, perfil)` + integra la señal de "buen día Yape" (§1).
- Algoritmo: regresión logística o árbol simple (los efectos de hora son casi lineales).
- Features: `hora_contacto`, `dia_semana`, `dias_mora`, `days_since_due`, `es_digital`, `tramo_mora`.
- Restricciones duras del brief: Lun-Vie 7am-7pm; **Sábado solo canal digital**; evitar mañana.

**M4 — ¿Tono y mensaje?** (mapeo a 4 perfiles)
- No es ML puro: clasifica el cuadrante y aplica reglas de redacción.
- Cuadrantes (digital × moroso):
  - 🟥 Moroso digital (Alessia): culpa/agobio → tono empático, ofrecer pago parcial.
  - 🟧 Moroso no digital (Powel): miedo/impotencia → llamada humana (no robot).
  - 🟩 No moroso digital (Arnaldo/Janet): orgullo/miedo a extorsión → "gracias por adelantarte".
  - 🟦 No moroso no digital (Rosa/Don José): invasión/estrés → tono de dignidad.
- Input: `es_digital` + `dias_mora` → eje moroso/no-moroso con `ratio_pago` + `num_atrasos_previos`.

### Campos del glosario que recién aprovechamos

| Campo (glosario) | Dónde entra |
|---|---|
| `prob_pago_7d_base` / `prob_pago_30d_base` | Feature de M1 (propensión basal) |
| `respuesta_cliente` (respondió/ignoró/prometió) | Feature de M2; si prometió → no contactar |
| `roi_contacto` | Validación del backtest vs nuestro EV calculado |
| `ingreso_esperado` | Denominar el ahorro/recuperación en soles |
| `days_since_due` | Feature de M3 (urgencia del timing) |
| `recency_score` | Feature de fatiga en M2 |
| `fatiga_contacto` | Feature anti-fatiga en M1 y M2 |

### Lo que lo diferencia de un chatbot genérico (para el pitch)
1. **Decide SI contactar** — la mayoría asume que hay que contactar a todos.
2. **Elige canal por valor neto**, no por regla fija.
3. **Aprende la curva de fatiga** — sabe que el 3er intento de llamada a un digital convierte ~0%.
4. **El nudge de "buen día" y YoSiLa** atacan el problema de raíz: el cliente paga cuando tiene caja,
   sin sentirse perseguido.

---

---

## 4. Backlog de cambios pendientes (atacar todo de una pasada)

> Estado del repo revisado el 2026-06-25. Orden sugerido de ataque.

### 🔴 BLOQUEANTE — `web/index.html` está truncado
- El archivo quedó en **71 líneas** y se corta dentro del primer `<section class="card">` del
  tab `#asesoria` (el header del backtest). Le falta TODO lo demás: lista de decisión por cliente,
  módulo YateKobro completo, tab de flujo, footer y el `<script src="app.js">`.
- `app.js` espera ~23 IDs que ya no existen (`#btTable`, `#decRows`, `#decDetail`, `#ykPresets`,
  `#ykSaldo/#ykTasa/#ykPlazo/#ykPct/#ykVentas`, `#ykAmort/#ykBars/#ykResumen/#ykLedger/#ykEvents`,
  `#ykMode/#ykLedMode`, `#flow`, `#footMeta`, `#srcBadge`, `#btFuente`). Sin ellos el dashboard
  no renderiza completo.
- Probable causa: sincronización a medias de OneDrive o guardado truncado. El CSS (`styles.css`,
  rediseño marca Mibanco) y el `chat.html`/`chat.css` SÍ están completos y consistentes.
- **Acción:** reconstruir `index.html` completo respetando el contrato de `app.js` y el CSS
  `app-header`/`tabs-inner`/`panel`/`card`. Recién sobre la base sana, sumar lo de abajo.

### 🟧 Feature A — Botón "🔧 Detalle técnico" (modal) en la pantalla principal
- Botón chiquito visible en el tab `#asesoria` (ej. en el `.card-h` del backtest o junto al header).
- Abre un **modal/overlay** (autocontenido, usa los tokens del CSS) que explica el approach de confIA:
  - Los **4 modelos** (M1 ¿contactar? · M2 ¿canal? · M3 ¿cuándo? · M4 ¿tono?) con qué predice cada uno.
  - El **flujo de datos** (3 tablas + Yape → feature engineering → 4 modelos → WhatsApp verificable).
  - Nota honesta: *"En el MVP las decisiones están precalculadas; en producción los 4 modelos se
    entrenan sobre 572,553 contactos reales con `pago_7d_post_contacto` como etiqueta."*
- Objetivo: demostrar el detalle técnico aunque el MVP esté hardcodeado (criterio Comprensión 25%).
- Contenido fuente: los bloques §1 y §3 de este mismo documento.

### 🟧 Feature B — Vista calendario de contactos del mes (por cliente)
- Mostrar, por cliente: **en qué fecha** se contacta, **con qué mensaje** y el **total de contactos del mes**.
- **Topes (márgenes fijos), todo por WhatsApp:**
  - Morosos (días_mora > 0): **máximo 6-7 contactos/mes**.
  - No morosos (preventivo): **máximo 3 contactos/mes**.
- ⚠️ **Reconciliar con el backtest para no contradecir el titular −79%:** el "tope 2" del backtest es
  **por episodio de cobranza** (un vencimiento, ventana ~7 días). El acumulado mensual ≤6-7 (morosos) /
  ≤3 (sanos) sale de que un moroso cruza varias etapas (preventivo + temprana + media…). Como TODO es
  WhatsApp a S/0.10, el costo igual se desploma (7 WA = S/0.70 vs 5.7 contactos mixtos hoy = S/5.64).
  → En la UI dejar explícita esa distinción "por episodio" vs "acumulado mensual".
- Nota de coherencia con el brief: la slide 9 dice "No se eliminan canales". Para el no-digital en mora
  profunda, el motor sigue permitiendo llamada; el calendario los muestra como WhatsApp por ser el
  canal héroe del pitch, pero conviene aclararlo en una nota chica.

### 🟨 Feature C — "Pulso Yape" estilo Screen Time (§2) + nudge "buen día" (§1)
- Nueva tab o sección con las barras de ingreso Yape diario + línea de umbral (ver §2).
- Nuevo módulo `engine/pulso_yape.py`: ticket promedio, baseline (mediana móvil 30d), índice de buen día.

### 🟦 Limpieza transversal
- [ ] Renombrar en TODO el repo "AsesorIA" → **Mibanco-confIA** y "YateKobro" → **YoSiLa**
      (títulos, header `brand-sub`, tabs, footer, comentarios de `*.py`, `chat.js`, `README_PoC.md`).
- [ ] `engine/config.json`: agregar restricción `sábado = solo_digital` (slide 9 del PDF del reto) y
      parámetro `α` del umbral buen día. Actualizar topes a la política morosos/no-morosos si se decide
      cambiar la del backtest.
- [ ] Ajustar tasas de canal del `config.json` a los números oficiales del PDF: **Digital 50% pago/contacto
      vs Llamada 10%** (hoy el config tiene llamada en 47.3%, menos drástico que el dato oficial).
- [ ] Capa visual de arquitectura técnica también dentro del tab "Flujo end-to-end" (refuerza Feature A).

### Cómo correr el PoC (para verificar antes/después)
```
# Desde mvp-cobranza/ (PowerShell o bash en Windows):
python engine/build.py --muestra 300      # genera web/data/*.json (sintético si no hay xlsx reales)
cd web
python -m http.server 8765                # abre http://localhost:8765
```
- Sin los xlsx reales en `../data_cobranzas/`, usa datos sintéticos (incluye a los 7 entrevistados).
- `build.py` solo necesita pandas si hay xlsx reales; en modo sintético corre con stdlib pura.
- ⚠️ Mientras `index.html` siga truncado, el dashboard renderiza incompleto; `chat.html` sí funciona.

# IAthon ULIMA x Mibanco — Carpeta de trabajo (Reto de Cobranzas)

Todo el contenido de la página de Notion del evento, scrapeado y organizado.
**Fuente:** https://lizard-art-ecd.notion.site/IAthon-Ulima-x-Mibanco-2e97695db41e8207874001a28447cbfc

> ⚠️ Compromiso de confidencialidad: la data de Mibanco es solo para el evento. No compartir ni publicar fuera del equipo.

---

## 📁 Estructura

```
MIBANCO/
├── README.md                ← este archivo (índice maestro)
├── data_cobranzas/          ← LAS 3 TABLAS DEL RETO (lo más importante)
│   ├── 01 Tabla de Clientes.xlsx     (50,000 clientes)
│   ├── 02 Tabla de Créditos.xlsx     (194,664 registros mensuales)
│   └── 03 Tabla_contactos (1).xlsx   (572,553 contactos de cobranza)
├── recursos/                ← presentaciones, PDFs, ejemplos de correos
│   ├── IAthon - Reto Cobranzas.pptx          (brief oficial del Reto 1)
│   ├── Presentación Metodología - IAthon Mibanco.pdf
│   ├── Manual de Marca Mibanco Perú.pdf
│   ├── Empatizar para agentizar - Gonzalo Lamas.pdf  (taller empatización)
│   ├── Reto IA mibanco_UL.pptx                (brief del Reto 2)
│   └── Test FIO / Test SHIRLEY .msg          (ejemplos de comunicación, Reto 2)
├── imagenes/                ← imágenes de la página (incluye rubric de evaluación)
├── retos/                   ← cada página de Notion en markdown
│   ├── conoce-los-desaf-os.md   ← descripción de los 2 retos
│   ├── registra-tu-proyecto.md
│   ├── evaluaci-n-de-tu-proyecto.md
│   ├── desarrollo-del-proyecto.md
│   ├── workshops.md
│   ├── open-day.md
│   ├── demo-day.md
│   └── preguntas-frecuentes.md
└── raw/                     ← JSON crudo de Notion + xlsx_schema.json (respaldo)
```

---

## 🎯 EL RETO 1 — Reinventando la Cobranza Inteligente

**Tema:** Cobranza personalizada con IA

> **¿Cómo podríamos mejorar la gestión de cobranza identificando el mejor canal, momento y tipo de interacción para cada cliente?**

En otras palabras: con la data de 50k clientes, sus créditos y su historial de contactos, construir algo (modelo / motor de decisión / MVP) que diga **a quién contactar, por qué canal, en qué momento y cómo**, para maximizar el pago y minimizar el costo y la fatiga del cliente.

Brief completo: `recursos/IAthon - Reto Cobranzas.pptx`

---

## 📊 Diccionario de datos (las 3 tablas se unen por `cliente_id` / `credito_id`)

### 01 Tabla de Clientes.xlsx — 50,000 filas, 20 columnas (1 fila por cliente)
| Columna | Qué es |
|---|---|
| `cliente_id` | ID único del cliente (llave) |
| `edad`, `genero`, `region`, `zona`, `tipo_cliente` | Perfil demográfico (zona: urbano/rural; tipo: nuevo/recurrente) |
| `es_digital`, `uso_app`, `uso_whatsapp`, `interaccion_digital_score` | Qué tan digital es el cliente |
| `canal_whatsapp`, `canal_sms`, `canal_llamada`, `canal_campo` | Canales disponibles para ese cliente (1=sí) |
| `score_riesgo`, `prob_default` | Riesgo crediticio |
| `num_atrasos_previos`, `dias_mora_promedio`, `ratio_pago`, `ultimo_pago_dias` | Comportamiento de pago histórico |

### 02 Tabla de Créditos.xlsx — 194,664 filas, 17 columnas (histórico mensual por crédito)
| Columna | Qué es |
|---|---|
| `credito_id`, `cliente_id` | Llaves |
| `periodo`, `fecha_corte` | Mes del registro |
| `producto`, `saldo_inicial`, `cuota_mensual`, `saldo_restante` | Datos del crédito |
| `dias_mora`, `tramo_mora`, `estado_credito` | Situación de mora (tramo: 01-30, etc.) |
| `pago_realizado_mes`, `monto_pagado_mes`, `fecha_pago` | Si pagó ese mes y cuánto |
| `prob_pago_7d_base`, `prob_pago_30d_base` | Probabilidad base de pago (sin contactar) |
| `num_creditos_activos` | Créditos activos del cliente |

### 03 Tabla_contactos (1).xlsx — 572,553 filas, 31 columnas (1 fila por intento de contacto)
| Columna | Qué es |
|---|---|
| `contacto_id`, `cliente_id`, `credito_id` | Llaves |
| `fecha_contacto`, `hora_contacto` | **Cuándo** se contactó (clave para "momento") |
| `dias_mora`, `tramo_mora`, `saldo_restante`, `cuota_mensual` | Estado al momento del contacto |
| `num_contactos_ult7d`, `num_contactos_ult30d`, `dias_ultimo_contacto` | Intensidad reciente de contacto |
| `canal_contacto`, `ultimo_canal_contacto` | **Por qué canal** (llamada, whatsapp, sms, campo) |
| `intento_num`, `num_contactos_mes_credito` | Nº de intento |
| `contacto_exitoso`, `respuesta_cliente`, `respuesta_ultimo_contacto` | Resultado del contacto (ej: "ignoro") |
| `costo_contacto`, `ingreso_esperado`, `roi_contacto` | **Economía** del contacto (ROI) |
| `prob_pago_7d_post_contacto_modelada`, `pago_7d_post_contacto`, `pago_monto_7d` | Pago después del contacto (variable objetivo) |
| `intensidad_contacto`, `fatiga_contacto`, `recency_score`, `days_since_due` | Señales de saturación/recencia |

> 💡 La variable a predecir/optimizar es básicamente `pago_7d_post_contacto` (¿pagó tras el contacto?) maximizando `roi_contacto` y cuidando `fatiga_contacto`.

---

## 🗓️ Cronograma y fechas clave

- **20 de junio** — Talleres: Levantamiento de info (9am), Empatización (11:30am), Prototipado y MVP (2pm)
- **Open Day** — Edificio O, 2do piso, Universidad de Lima
- **Lun 22 jun** — Desarrollo (híbrido: Edificio O / Zoom)
- **Mar 23 y Mié 24 jun** — Desarrollo (virtual, Zoom)
- **📌 Registro del proyecto: hasta el 25 de junio** (lo hace el líder del equipo vía formulario)
- **Demo day** — ver `retos/demo-day.md`

---

## ✅ Criterios de evaluación (presentación final, máx 3 min)

| Criterio | Pregunta | Peso |
|---|---|---|
| Comprensión del reto | ¿Entiende el problema y el público objetivo? | **25%** |
| Creatividad e innovación | ¿Enfoque distinto / disruptivo? | **20%** |
| Viabilidad y potencial | ¿Es factible? ¿Incluye insights del usuario? | **20%** |
| Prototipo | ¿Qué tan fácil y atractivo es interactuar con la solución? | **25%** |
| Presentación y storytelling | ¿Se comunicó con claridad y de forma atractiva? | **10%** |

> Recomendación oficial: agregar una sección de **valorización de la propuesta / % de ROI** para que sea más potente. Pueden usar videos, mockups, simulaciones. Canva o PowerPoint.

**Lectura del rubric:** Prototipo (25%) + Comprensión (25%) pesan la mitad. O sea: hay que **demostrar que entendieron el problema de cobranza Y tener un prototipo navegable**, no solo el modelo.

---

## 📨 Contacto / dudas
Yanira Caraza — ycaraza@ulima.edu.pe

*Carpeta generada scrapeando la página pública de Notion del evento (texto + 18 archivos adjuntos).*
</content>

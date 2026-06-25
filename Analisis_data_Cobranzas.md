# Análisis de la data — Reto Cobranza Mibanco

Análisis columna por columna de las 3 tablas + patrones clave para el MVP.

---

## 🔑 Hallazgos que mandan en el MVP (leer esto primero)

1. **WhatsApp gana en todo.** Paga más (53.5% vs 47.3% llamada), cuesta 15x menos (S/0.10 vs S/1.50) y su ROI es 17x el de la llamada (2987 vs 177). Hoy, sin embargo, el 38% de los contactos son por **llamada** y solo el 34% por WhatsApp → **plata mal gastada**. El contacto de **campo** es lo peor: ROI 32, cuesta S/8.
2. **Saturar al cliente baja el pago.** Con 0-1 contactos en 7 días pagan 54.8%; con 4-5 contactos cae a 39.6%. Y el 28% de los registros tienen 4 contactos en 7 días → los están **fatigando** y perdiendo pagos. Menos es más.
3. **El momento que importa es el del ciclo de mora, no la hora del día.** La hora casi no mueve la aguja (todas ~48-49%). Pero el tramo de mora sí: al día 55.4% → 01-30 días 47.4% → 31-60 días 37.8% → 60+ días 32.1%. **Mientras más tarde lo contactas, menos paga → cobranza preventiva / temprana.**
4. **La meta es generar respuesta, no insistir.** Quien responde paga 62%, quien promete pagar 72%, pero quien ignora solo 39% — y el **63% ignora**. WhatsApp (conversacional) saca respuesta donde la llamada se ignora.

**Ojo con la calidad de la data:**
- `tramo_mora` en contactos sale como `2030-01-01` por un error de Excel: en realidad es el tramo **"01-30"** (Excel lo leyó como fecha).
- `estado_credito` es siempre "vigente" → columna inútil.
- `score_riesgo`, `prob_default`, `ratio_pago`, `uso_app` tienen distribución uniforme (promedio exacto 0.50) → parecen **sintéticas / ruido**. Apóyate en los patrones fuertes (canal, fatiga, tramo de mora, respuesta), no en `prob_default` individual.


## Tabla `clientes` — 50,000 filas × 20 columnas

| Columna | Tipo | Nulos | Únicos | Resumen |
|---|---|---|---|---|
| `cliente_id` | int64 | 0 | 50,000 | min 1.00 · med 25000.50 · prom 25000.50 · max 50000.00 |
| `edad` | int64 | 0 | 49 | min 21.00 · med 45.00 · prom 44.99 · max 69.00 |
| `genero` | str | 0 | 2 | F (50%); M (50%) |
| `region` | str | 0 | 4 | Lima (25%); Norte (25%); Sur (25%); Centro (25%) |
| `zona` | str | 0 | 2 | urbano (70%); rural (30%) |
| `tipo_cliente` | str | 0 | 2 | recurrente (60%); nuevo (40%) |
| `es_digital` | int64 | 0 | 2 | 1 (65%); 0 (35%) |
| `uso_app` | float64 | 0 | 101 | min 0.00 · med 0.50 · prom 0.50 · max 1.00 |
| `uso_whatsapp` | int64 | 0 | 2 | 1 (70%); 0 (30%) |
| `interaccion_digital_score` | int64 | 0 | 101 | min 0.00 · med 49.00 · prom 49.73 · max 100.00 |
| `canal_whatsapp` | int64 | 0 | 2 | 1 (79%); 0 (21%) |
| `canal_sms` | int64 | 0 | 2 | 1 (80%); 0 (20%) |
| `canal_llamada` | int64 | 0 | 1 | 1 (100%) |
| `canal_campo` | int64 | 0 | 2 | 0 (60%); 1 (40%) |
| `score_riesgo` | int64 | 0 | 550 | min 300.00 · med 575.00 · prom 574.39 · max 849.00 |
| `prob_default` | float64 | 0 | 1,001 | min 0.00 · med 0.50 · prom 0.50 · max 1.00 |
| `num_atrasos_previos` | int64 | 0 | 11 | 2 (27%); 1 (27%); 3 (18%); 0 (13%); 4 (9%) |
| `dias_mora_promedio` | int64 | 0 | 60 | min 0.00 · med 30.00 · prom 29.46 · max 59.00 |
| `ratio_pago` | float64 | 0 | 101 | min 0.00 · med 0.50 · prom 0.50 · max 1.00 |
| `ultimo_pago_dias` | int64 | 0 | 90 | min 0.00 · med 45.00 · prom 44.44 · max 89.00 |

## Tabla `creditos` — 194,664 filas × 17 columnas

| Columna | Tipo | Nulos | Únicos | Resumen |
|---|---|---|---|---|
| `credito_id` | int64 | 0 | 64,888 | min 1.00 · med 32444.50 · prom 32444.50 · max 64888.00 |
| `cliente_id` | int64 | 0 | 50,000 | min 1.00 · med 24980.50 · prom 24992.27 · max 50000.00 |
| `periodo` | str | 0 | 3 | 2026-01 (33%); 2026-02 (33%); 2026-03 (33%) |
| `fecha_corte` | str | 0 | 3 | 2026-01-31 (33%); 2026-02-28 (33%); 2026-03-31 (33%) |
| `producto` | str | 0 | 3 | microcredito (34%); negocio (33%); consumo (33%) |
| `saldo_inicial` | float64 | 0 | 63,798 | min 500.36 · med 10271.88 · prom 10241.54 · max 19999.69 |
| `cuota_mensual` | float64 | 0 | 50,217 | min 16.63 · med 520.81 · prom 562.50 · max 1596.84 |
| `saldo_restante` | float64 | 0 | 109,951 | min 381.86 · med 9802.15 · prom 9802.13 · max 19999.49 |
| `dias_mora` | int64 | 0 | 204 | min 0.00 · med 9.00 · prom 31.27 · max 203.00 |
| `tramo_mora` | str | 0 | 4 | 0 (40%); 01-30 (24%); 60 (21%); 31-60 (15%) |
| `estado_credito` | str | 0 | 1 | vigente (100%) |
| `pago_realizado_mes` | int64 | 0 | 2 | 0 (62%); 1 (38%) |
| `monto_pagado_mes` | float64 | 0 | 55,930 | min 0.00 · med 0.00 · prom 216.03 · max 2045.39 |
| `fecha_pago` | str | 120,074 | 84 | 2026-01-22 (1%); 2026-01-18 (1%); 2026-01-17 (1%); 2026-01-28 (1%); 2026-01-15 (1%) |
| `prob_pago_7d_base` | float64 | 0 | 851 | min 0.05 · med 0.48 · prom 0.48 · max 0.90 |
| `prob_pago_30d_base` | float64 | 0 | 900 | min 0.10 · med 0.60 · prom 0.60 · max 1.00 |
| `num_creditos_activos` | int64 | 0 | 2 | 1 (54%); 2 (46%) |

## Tabla `contactos` — 572,553 filas × 31 columnas

| Columna | Tipo | Nulos | Únicos | Resumen |
|---|---|---|---|---|
| `contacto_id` | int64 | 0 | 572,553 | min 1.00 · med 286277.00 · prom 286277.00 · max 572553.00 |
| `cliente_id` | int64 | 0 | 32,728 | min 1.00 · med 16387.00 · prom 16358.99 · max 32728.00 |
| `credito_id` | int64 | 0 | 42,481 | min 1.00 · med 21245.00 · prom 21235.02 · max 42481.00 |
| `fecha_contacto` | str | 0 | 90 | 2026-02-19 (1%); 2026-02-23 (1%); 2026-02-25 (1%); 2026-02-16 (1%); 2026-02-02 (1%) |
| `hora_contacto` | str | 0 | 52 | 16:15:00 (3%); 16:30:00 (3%); 18:00:00 (3%); 16:45:00 (3%); 16:00:00 (3%) |
| `producto` | str | 0 | 3 | microcredito (34%); negocio (33%); consumo (33%) |
| `dias_mora` | int64 | 0 | 121 | min 0.00 · med 1.00 · prom 18.23 · max 120.00 |
| `tramo_mora` | str | 0 | 4 | 0 (50%); 2030-01-01 00:00:00 (30%); 31-60 (10%); 60 (10%) |
| `saldo_restante` | float64 | 0 | 494,996 | min 437.73 · med 9914.09 · prom 9925.78 · max 19999.69 |
| `cuota_mensual` | float64 | 0 | 35,780 | min 16.63 · med 521.56 · prom 563.16 · max 1596.84 |
| `num_contactos_ult7d` | int64 | 0 | 5 | 4 (28%); 0 (22%); 1 (19%); 2 (17%); 3 (14%) |
| `num_contactos_ult30d` | int64 | 0 | 9 | 8 (42%); 0 (7%); 1 (7%); 2 (7%); 3 (7%) |
| `dias_ultimo_contacto` | int64 | 0 | 60 | min 0.00 · med 5.00 · prom 79.74 · max 999.00 |
| `ultimo_canal_contacto` | str | 0 | 5 | llamada (35%); whatsapp (31%); sms (21%); sin_contacto_previo (7%); campo (6%) |
| `respuesta_ultimo_contacto` | str | 0 | 4 | ignoro (58%); respondio (21%); prometio_pagar (13%); sin_contacto_previo (7%) |
| `canal_contacto` | str | 0 | 4 | llamada (38%); whatsapp (34%); sms (22%); campo (6%) |
| `contacto_mes_num` | int64 | 0 | 8 | 1 (22%); 2 (19%); 3 (17%); 4 (14%); 5 (11%) |
| `num_contactos_mes_credito` | int64 | 0 | 8 | 8 (22%); 7 (19%); 6 (17%); 5 (14%); 4 (11%) |
| `intento_num` | int64 | 0 | 24 | min 1.00 · med 7.00 · prom 7.83 · max 24.00 |
| `contacto_exitoso` | int64 | 0 | 2 | 0 (63%); 1 (37%) |
| `respuesta_cliente` | str | 0 | 3 | ignoro (63%); respondio (23%); prometio_pagar (14%) |
| `costo_contacto` | float64 | 0 | 4 | 1.5 (38%); 0.1 (34%); 0.2 (22%); 8.0 (6%) |
| `prob_pago_7d_post_contacto_modelada` | float64 | 0 | 971 | min 0.01 · med 0.49 · prom 0.49 · max 0.98 |
| `pago_7d_post_contacto` | int64 | 0 | 2 | 0 (51%); 1 (49%) |
| `pago_monto_7d` | float64 | 0 | 102,245 | min 0.00 · med 0.00 · prom 220.03 · max 1894.60 |
| `ingreso_esperado` | float64 | 0 | 88,391 | min 0.17 · med 199.94 · prom 274.88 · max 1554.37 |
| `roi_contacto` | float64 | 0 | 133,096 | min -0.98 · med 383.11 · prom 1354.06 · max 15542.70 |
| `intensidad_contacto` | float64 | 0 | 9 | 0.267 (42%); 0.0 (7%); 0.033 (7%); 0.067 (7%); 0.1 (7%) |
| `fatiga_contacto` | str | 0 | 3 | baja (42%); media (31%); alta (28%) |
| `recency_score` | float64 | 0 | 47 | min 0.00 · med 0.17 · prom 0.26 · max 1.00 |
| `days_since_due` | int64 | 0 | 121 | min 0.00 · med 1.00 · prom 18.23 · max 120.00 |

---

# Patrones clave para el MVP

- **Tasa de pago a 7 días post-contacto (global):** 48.9%
- **Tasa de contacto exitoso (global):** 37.2%
- **ROI promedio por contacto:** 1354.06
- **Costo promedio por contacto:** 1.15


**Pago / ROI por CANAL de contacto**

| canal_contacto | n | tasa_pago | roi | costo |
|---|---|---|---|---|
| llamada | 217,360 | 47.3% | 176.91 | 1.50 |
| whatsapp | 192,118 | 53.5% | 2987.20 | 0.10 |
| sms | 127,157 | 45.1% | 1272.15 | 0.20 |
| campo | 35,918 | 47.2% | 32.38 | 8.00 |

**Pago / ROI por HORA del contacto**

| hora | n | tasa_pago | roi | costo |
|---|---|---|---|---|
| 16 | 57,678 | 48.7% | 1357.29 | 1.14 |
| 18 | 57,208 | 49.0% | 1344.13 | 1.14 |
| 17 | 56,952 | 49.0% | 1351.74 | 1.15 |
| 15 | 51,326 | 48.7% | 1359.26 | 1.14 |
| 12 | 46,000 | 48.9% | 1343.29 | 1.16 |
| 14 | 45,881 | 48.4% | 1341.39 | 1.16 |
| 13 | 45,795 | 48.9% | 1346.47 | 1.15 |
| 19 | 45,569 | 49.5% | 1356.87 | 1.15 |
| 11 | 40,167 | 48.4% | 1346.17 | 1.17 |
| 20 | 40,127 | 48.9% | 1380.66 | 1.14 |
| 10 | 34,402 | 49.0% | 1365.99 | 1.15 |
| 9 | 28,769 | 49.0% | 1342.73 | 1.16 |
| 8 | 22,679 | 49.2% | 1385.34 | 1.12 |

**Pago / ROI por RESPUESTA del cliente**

| respuesta_cliente | n | tasa_pago | roi | costo |
|---|---|---|---|---|
| ignoro | 359,804 | 38.7% | 1084.88 | 1.05 |
| respondio | 131,752 | 62.3% | 1716.00 | 1.31 |
| prometio_pagar | 80,997 | 72.1% | 1961.11 | 1.31 |

**Pago / ROI por TRAMO DE MORA**

| tramo_mora | n | tasa_pago | roi | costo |
|---|---|---|---|---|
| 0 | 286,238 | 55.4% | 1548.45 | 1.02 |
| 2030-01-01 00:00:00 | 172,026 | 47.4% | 1336.60 | 1.02 |
| 31-60 | 57,231 | 37.8% | 969.12 | 1.67 |
| 60 | 57,058 | 32.1% | 817.64 | 1.68 |

**Efecto FATIGA: pago según nº de contactos en últimos 7 días**

| bucket_7d | n | tasa_pago |
|---|---|---|
| 4-5 | 159,092 | 39.6% |
| 0 | 127,443 | 54.8% |
| 1 | 111,254 | 54.8% |
| 2 | 95,349 | 49.3% |
| 3 | 79,415 | 49.3% |

---

# Perfil de clientes (segmentación para el MVP)

- **es_digital:** 1 64.8%, 0 35.2%
- **tipo_cliente:** recurrente 60.2%, nuevo 39.8%
- **region:** Lima 25.2%, Norte 25.2%, Sur 24.9%, Centro 24.7%
- **zona:** urbano 70.1%, rural 29.9%
- **canal_whatsapp disponible:** 79.1%
- **canal_sms disponible:** 80.1%
- **canal_llamada disponible:** 100.0%
- **canal_campo disponible:** 39.9%
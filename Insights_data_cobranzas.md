# 10 Insights de la data de Cobranza (Mibanco)

Análisis sobre el dataset real del reto: **572,553 contactos**, **194,665 créditos**, **50,000 clientes**.
Cada insight está respaldado por el número y, donde aplica, cruzado con las 7 entrevistas.

> **Números cabecera:** de cada 100 contactos, **63 son ignorados** y **51 no terminan en pago**. El costo total de cobranza del dataset es **S/ 658,027**, de los cuales **S/ 346,319 (53%) se gastan en contactos que NO logran pago.** Hay muchísimo que optimizar.

---

## 1. WhatsApp es el canal rey: convierte más y cuesta casi nada
| Canal | % paga en 7d | Costo x contacto | ROI |
|---|---|---|---|
| **WhatsApp** | **53.5%** | **S/ 0.10** | **2,987** |
| SMS | 45.1% | S/ 0.20 | 1,272 |
| Llamada | 47.3% | S/ 1.50 | 177 |
| Campo | 47.2% | S/ 8.00 | 32 |

WhatsApp paga **más** que la llamada y cuesta **15 veces menos**. El campo es el que más "contacta" (47.9% éxito) pero el de peor ROI.
→ **Mover volumen de llamada a WhatsApp.** Cruza con entrevistas: Janet pide *"WhatsApp de mi asesor con la sigla del BCP"*; varios prefieren canal digital.

## 2. El 63% de los contactos son ignorados
`respuesta_cliente`: **ignoró 62.8%**, respondió 23.0%, prometió pagar 14.1%. Solo el **37.2%** de los contactos logra contacto efectivo.
→ La mayor parte del esfuerzo de cobranza cae en el vacío. Cruza directo con: Janet *"por eso bloqueo todo"*, José *"no me dan ganas de contestar a nadie"*.

## 3. Más de la mitad del presupuesto se quema en contactos que no cobran
**S/ 346,319 de S/ 658,027 (53%)** se gastan en contactos que NO derivan en pago a 7 días.
→ Solo con recortar contactos inútiles se libera medio presupuesto de cobranza. Este es el argumento de **reducción de costos** del brief, cuantificado.

## 4. El sobre-contacto NO ayuda: a más contactos, menos pago
| Contactos al mes (por crédito) | % paga 7d |
|---|---|
| 1-2 | ~54.7% |
| 3-4 | ~52.6% |
| 5-6 | ~48.6% |
| 7-8 | ~46.2% |

Y por intento: 1.er intento **55%** → 5.º intento **46%**. El ROI cae de 1,500 a 1,270.
→ **"No llamar 10 veces" confirmado con datos.** Cruza con Janet: *"te llaman 8-10 veces al día, por eso bloqueo todo."*
*(Matiz honesto: es correlacional — los casos difíciles reciben más contactos. Pero el ROI por contacto cae y las entrevistas confirman el hartazgo.)*

## 5. La mora temprana es donde está el dinero
| Días de mora | % paga 7d | ROI |
|---|---|---|
| **0 (al día)** | **55.4%** | **1,548** |
| 1-7 | 47.4% | 1,339 |
| 16-30 | 47.2% | 1,335 |
| 31-60 | 37.8% | 969 |
| 60+ | 32.1% | 818 |

Contactar en mora temprana paga **casi el doble** que en mora tardía.
→ **Actuar antes de que la mora crezca** (lo que pide el brief). El recordatorio preventivo > la cobranza tardía.

## 6. El canal debe calzar con el perfil digital del cliente
% que paga 7d, por canal y tipo de cliente:
| Canal | Cliente digital | Cliente NO digital |
|---|---|---|
| WhatsApp | **55.3%** | 46.2% |
| SMS | 47.8% | 38.0% |
| Llamada | 46.4% | **48.1%** |
| Campo | 46.5% | **48.7%** |

El digital responde mejor a **WhatsApp**; el no-digital responde mejor a **llamada/campo**.
→ No usar WhatsApp para todos: **segmentar canal por `es_digital`.** Cruza con el brief ("entender digitales vs no digitales").

## 7. Hoy se contacta a TODOS por igual, sin importar el riesgo
Todos los segmentos reciben **~5.7 contactos por crédito**, sin diferenciar:
| Perfil (score) | Contactos x crédito | % paga 7d |
|---|---|---|
| Buen score | 5.66 | **52.0%** |
| Medio | 5.67 | 49.0% |
| Score bajo | 5.66 | 45.7% |

El **buen pagador recibe la misma presión** que el riesgoso (≈5.7 contactos), aunque paga más solo.
→ **Aliviar el contacto al buen pagador** y concentrar esfuerzo en el riesgoso. Cruza con Rosa/Arnaldo: *"no quiero que me traten como deudor cuando siempre pago."*

## 8. Llamada + campo = 94% del costo, con el peor ROI
| Canal | % de contactos | % del costo total |
|---|---|---|
| Campo | 6% | **44%** (S/ 287,344) |
| Llamada | 38% | **50%** (S/ 326,040) |
| SMS + WhatsApp | 56% | 7% (S/ 44,643) |

El campo es el 6% de los contactos pero casi la mitad del costo.
→ **Reservar campo solo para alto riesgo / alto monto.** Lo demás, digital.

## 9. La hora del día casi no mueve la aguja
El pago a 7d se mantiene plano (**48-49%**) en todo el horario (8am-8pm); apenas un leve pico a las 7-8pm y 8am.
→ En esta data, el **canal**, la **etapa de mora** y la **frecuencia** importan MUCHO más que la hora exacta. *(Matiz: en las entrevistas la hora sí les importa subjetivamente —mañana mala, mediodía buena— así que sirve para el "speech", pero no es la palanca principal.)*

## 10. Ojo: hay un problema de calidad de datos que hay que limpiar
El campo `tramo_mora` tiene el tramo **"01-30" corrupto**: aparece como `"2030-01-01 00:00:00"` (Excel lo auto-convirtió a fecha al exportar). Son 172,026 filas.
→ Hay que **limpiar la data antes de modelar.** (Irónicamente refuerza lo que contó Janet: sistemas que registran mal y terminan marcando morosos que sí pagaron.)

---

## Lo que estos 10 insights le dicen a tu propuesta

1. **Empezar por WhatsApp en mora temprana** = la jugada de mayor ROI (insights 1, 5).
2. **Segmentar por riesgo + perfil digital**, no contactar a todos igual (insights 6, 7).
3. **Poner un tope de contactos** y matar los inútiles (insights 2, 3, 4).
4. **Reservar llamada/campo para alto riesgo** (insights 8).
5. La IA decide **a quién, por qué canal y en qué etapa de mora** — la hora es secundaria (insight 9).

Esto es exactamente "reinventar la cobranza con IA" con números que lo respaldan, y calza con que el cliente deje de sentirse perseguido (las 7 entrevistas).

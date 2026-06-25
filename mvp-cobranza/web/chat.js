"use strict";
/* ============================================================
Demo Conversación — Mibanco-confIA + YoSiLa · Mibanco IAthon
Chat WhatsApp: Alessia (digital) y Powel (no digital)
× 5 etapas de mora × animación mensaje a mensaje
============================================================ */

const PERFILES = {
alessia: {
id: "alessia",
nombre: "Alessia Borrelli",
tipo: "Morosa · Digital",
avatar: "AB",
color: "#00A94F",
cuota: 450,
canal: "whatsapp",
nota: "Flujo variable de negocio. Pide flexibilidad.",
},
powel: {
id: "powel",
nombre: "Powel Aliaga",
tipo: "Moroso · No digital",
avatar: "PA",
color: "#0f1b2d",
cuota: 260,
canal: "llamada",
nota: "Abre el mercado a las 5am. Teme extorsión.",
},
};

const ETAPAS = [
{ id: "preventivo", label: "Preventivo", sub: "Antes del vencimiento" },
{ id: "temprana", label: "Mora 1–15 días", sub: "Etapa temprana" },
{ id: "media", label: "Mora 16–30 días", sub: "Etapa media" },
{ id: "tardia", label: "Mora 30+ días", sub: "Etapa tardía" },
{ id: "yatekobro", label: "YoSiLa ✅", sub: "Cubriendo la cuota" },
];

const CONV = {
alessia: {
preventivo: [
{ de: "banco", delay: 600,
texto: "Hola Alessia 👋 Te escribe *Mibanco* ✅\nTu cuota de S/450 vence en 3 días (27 jun).\nPodés pagar fácil por Yape o la App Mibanco 📱\n¡Gracias por tu puntualidad! 🙌" },
{ de: "cliente", delay: 1200,
texto: "Hola! gracias por avisar 😊 ya lo tengo anotado" },
{ de: "banco", delay: 800,
texto: "¡Perfecto! Cualquier duda, aquí estamos Alessia 💙\nTe enviamos el link de pago por si lo necesitás." },
],
temprana: [
{ de: "banco", delay: 600,
texto: "Hola Alessia 👋 *Mibanco* ✅\nVemos que tu cuota de S/450 venció hace 7 días.\nSabemos que el negocio tiene días flojos 🤝\n¿Cómo te ayudamos?\n• Pagar ahora\n• Pago parcial\n• Reprogramar\nEscribinos y lo resolvemos juntos." },
{ de: "cliente", delay: 2000,
texto: "Uff sí, esta semana estuvo difícil... ¿puedo pagar la mitad ahora?" },
{ de: "banco", delay: 900,
texto: "Claro Alessia 💙 Sin problema.\nAnotamos S/225 para hoy.\n¿Querés que activemos YoSiLa para cubrir el resto automáticamente?\nCada venta por Yape aporta un % chiquito a tu cuota — sin sentirla." },
{ de: "cliente", delay: 1500,
texto: "¿Cómo funciona eso?" },
{ de: "banco", delay: 1000,
texto: "Muy simple Alessia 📊\n• Elegís el % (ej: 2%)\n• Cada Yape recibido → 2% va a tu cuota\n• Primero cubre el interés del mes ✅\n• Luego va al capital (lo que es tuyo)\n• Se para SOLO al completar la cuota\n¿Lo activamos al 2%?" },
{ de: "cliente", delay: 1800,
texto: "dale, probamos! 💪" },
{ de: "banco", delay: 1000,
texto: "✅ YoSiLa activado al 2%, Alessia.\nTe aviso en 3 momentos:\n1️⃣ Interés al 50%\n2️⃣ Interés al 100% (el momento estrella 🎉)\n3️⃣ Cuota completa → se para solo\n¡Éxitos con las ventas!" },
],
media: [
{ de: "sistema", tipo: "progreso",
titulo: "YoSiLa en marcha",
interes_pct: 61, capital_pct: 0,
sub: "12 días · 28 transacciones Yape",
delay: 400 },
{ de: "banco", delay: 700,
texto: "📊 YoSiLa — Alessia\nInterés de junio: 61% cubierto (S/61 de S/100)\nLlevas 12 días y 28 transacciones Yape.\nSeguimos 💪" },
{ de: "cliente", delay: 1400,
texto: "wow ni me di cuenta 😅 está buenísimo" },
{ de: "banco", delay: 900,
texto: "¡Así funciona! Cada venta suma sin que lo sientas 🙌\nAl ritmo actual, el interés lo vencés en ~5 días más." },
],
tardia: [
{ de: "banco", delay: 600,
texto: "Hola Alessia 👋 *Mibanco* ✅\nTu cuota de S/450 lleva 35 días vencida.\nEntendemos que la situación puede ser difícil 🤝\nTenemos opciones para ayudarte:\n• Pago parcial sin penalidad\n• Reprogramación del crédito\n• Cuota más chica ampliando el plazo\n¿Cuándo podemos hablar?" },
{ de: "cliente", delay: 2000,
texto: "la verdad es que el negocio estuvo muy malo..." },
{ de: "banco", delay: 1000,
texto: "Lo entendemos Alessia 🤝\nPodemos reestructurar tu crédito para que la cuota sea más manejable.\nSin penalidad por repago anticipado (Ley 29571).\n¿Te parece si tu asesor te llama hoy entre 14:00 y 17:00?" },
{ de: "cliente", delay: 1600,
texto: "sí, a las 15:00 estaría bien" },
{ de: "banco", delay: 800,
texto: "✅ Agendado para las 15:00, Alessia.\nTu asesor Juan García (verificable en mibanco.com.pe) te llamará desde el número oficial.\nNo es un robot, no es una empresa externa — es Mibanco directamente 🤝" },
],
yatekobro: [
{ de: "sistema", tipo: "progreso",
titulo: "🎉 ¡Interés 100% cubierto!",
interes_pct: 100, capital_pct: 40,
sub: "17 días · 42 transacciones · interés: VENCIDO ✅",
delay: 400 },
{ de: "banco", delay: 700,
texto: "*Mibanco* ✅ 🎉\n¡Alessia, ya cubriste el 100% del interés de junio!\nCada Yape que recibiste en tu negocio — el 2% fue automático a tu cuota.\nLo que te queda (S/350) es plata TUYA devolviendo capital, no costo del banco.\nLlevas 17 días y 42 transacciones." },
{ de: "cliente", delay: 1800,
texto: "😍 ¡me encanta! ni me di cuenta que estaba pagando la cuota" },
{ de: "banco", delay: 1000,
texto: "¡Así funciona! 📱 Cada vez que recibís un pago por Yape:\n🔓 Abrís la app e ingresás tu contraseña\n💜 Tocás «Yapear» y el pago entra al instante\n📊 El 2% va automático a tu cuota — primero interés ✅, luego capital\nVos solo cobrás. YoSiLa hace el resto." },
{ de: "cliente", delay: 1600,
texto: "ojalá lo hubiera activado antes 🙌 qué fácil" },
{ de: "banco", delay: 900,
texto: "¡Al ritmo actual tu cuota completa en ~10 días más!\nYoSiLa se para solo cuando llegue. 💙" },
{ de: "sistema", tipo: "progreso",
titulo: "✅ ¡Cuota PAGADA! Auto-stop",
interes_pct: 100, capital_pct: 100,
sub: "28 días · 67 transacciones · 0 llamadas de cobranza",
delay: 1200 },
{ de: "banco", delay: 800,
texto: "*Mibanco* ✅ ✅\n¡Cuota de junio PAGADA, Alessia! 🎉\nYoSiLa se paró automático.\nCero llamadas. Cero presión. Todo con tus ventas de Yape 💙\n¿Adelantamos julio?\nSÍ → seguimos al 2%\nNO → quedamos pausados" },
{ de: "cliente", delay: 1400,
texto: "SÍ por favor! 🙌" },
{ de: "banco", delay: 800,
texto: "✅ ¡Listo! YoSiLa activo para julio.\n¡Éxitos con el negocio, Alessia! 💙" },
],
},

powel: {
preventivo: [
{ de: "sistema", tipo: "llamada",
texto: "📞 Llamada entrante · *Mibanco* ✅ · 2 min · Juan García (asesor)",
delay: 400 },
{ de: "banco", delay: 600,
texto: "*Mibanco* ✅ Hola Powel 👋\nTu asesor Juan acaba de llamarte.\nTe dejamos el recordatorio acá:\nTu cuota de S/260 vence el 27 de junio.\nPodés pagar en cualquier agente BCP 📍\nCualquier consulta, respondé este mensaje. 🤝" },
{ de: "cliente", delay: 1600,
texto: "ok gracias, voy a ir al agente esta semana" },
{ de: "banco", delay: 700,
texto: "¡Perfecto Powel! ✅\nCualquier duda, aquí estamos. 🙌" },
],
temprana: [
{ de: "sistema", tipo: "llamada",
texto: "📞 Llamada entrante · *Mibanco* ✅ · 4 min · María García (asesora)",
delay: 400 },
{ de: "banco", delay: 700,
texto: "*Mibanco* ✅ Hola Powel 👋\nTu asesora María acaba de llamarte.\nTu cuota de S/260 lleva 6 días vencida.\nTe propuso reprogramar para el 5 de julio.\nConfirmá respondiendo SÍ o NO 👇" },
{ de: "cliente", delay: 1800,
texto: "sí, la reprogramación está bien" },
{ de: "banco", delay: 800,
texto: "✅ Listo Powel.\n📅 Nueva fecha: 5 de julio.\nSin penalidad. Sin más llamadas hasta esa fecha.\nCualquier cambio, escribinos acá. 🤝" },
],
media: [
{ de: "sistema", tipo: "llamada",
texto: "📞 Llamada entrante · *Mibanco* ✅ · 6 min · María García (asesora)",
delay: 400 },
{ de: "banco", delay: 700,
texto: "*Mibanco* ✅ Hola Powel 👋\nTu cuota lleva 22 días vencida.\nTu asesora María conversó con vos hoy sobre opciones.\nTe resumimos lo acordado:\n• Pago parcial de S/130 esta semana ✅\n• Resto (S/130) el 15 de julio\nConfirmá con SÍ para registrarlo. 👇" },
{ de: "cliente", delay: 1600,
texto: "sí confirmo" },
{ de: "banco", delay: 800,
texto: "✅ Registrado, Powel.\n→ S/130 antes del viernes\n→ S/130 el 15 de julio\nSin intereses adicionales por el acuerdo.\nCualquier imprevisto, escribinos antes y lo ajustamos. 🤝" },
],
tardia: [
{ de: "sistema", tipo: "campo",
texto: "🚶 Visita de campo · Asesor *Mibanco* ✅ · Mercado Caquetá · Agendada 12:00 pm",
delay: 400 },
{ de: "banco", delay: 700,
texto: "*Mibanco* ✅ Hola Powel 👋\nTu asesora Ana pasará por tu puesto en Caquetá hoy al mediodía.\nTraerá opciones para reestructurar tu crédito — cuota más chica, plazo extendido.\n¿Podés recibirla al mediodía?" },
{ de: "cliente", delay: 1800,
texto: "sí, al mediodía estoy en el puesto" },
{ de: "banco", delay: 800,
texto: "✅ Perfecto Powel.\nAna confirma para las 12:00.\nSin presión — es para encontrar la mejor salida juntos. 🤝\nRecordá: verificá siempre que el contacto sea del WhatsApp oficial de *Mibanco* ✅ — nunca pedimos datos por otro canal." },
{ de: "cliente", delay: 2000,
texto: "ok gracias, qué bueno que vinieron" },
{ de: "banco", delay: 700,
texto: "Para eso estamos Powel. Juntos lo resolvemos. 💙" },
],
yatekobro: [
{ de: "banco", delay: 600,
texto: "*Mibanco* ✅ Hola Powel 👋\nTenemos una forma de cubrir tu cuota sin llamadas ni visitas — se llama YoSiLa.\nCada pago Yape que recibís en tu negocio, un % va directo a tu cuota.\n¿Querés que te expliquemos cómo funciona?" },
{ de: "cliente", delay: 2000,
texto: "¿y eso cómo sería?" },
{ de: "banco", delay: 1000,
texto: "Primero necesitás tener Yape activo, Powel. Solo la primera vez:\n📱 Descargás Yape (Play Store o App Store)\n📋 Te registrás con tu número de celular\n🪪 Validás tu identidad con tu DNI — sin necesitar cuenta BCP\n🔐 Creás tu contraseña personal\n\n¿Ya tenés Yape instalado?" },
{ de: "cliente", delay: 2200,
texto: "no, todavía no lo tengo" },
{ de: "banco", delay: 1000,
texto: "Sin problema 🤝 Tu asesora María puede acompañarte en ese registro — es una sola vez y demora 5 minutos.\n\nDespués, cada vez que recibís un pago de un cliente por Yape es así de simple:\n🔓 Abrís Yape e ingresás tu contraseña\n💜 El pago entra al instante (botón morado «Yapear»)\n✅ Si el monto supera S/60, Yape te pide un código extra por seguridad\n📊 El % que elegís va automático a tu cuota\n\nTu límite diario es S/500 (podés subirlo a S/2,000 desde los ajustes)." },
{ de: "cliente", delay: 2000,
texto: "ah no sabía que era tan fácil. ¿y cómo se conecta con mi cuota?" },
{ de: "banco", delay: 1000,
texto: "Ahí entra YoSiLa, Powel 📊\nCada Yape que recibís → el % que elegís va a tu cuota:\n• Primero cubre el interés del mes ✅\n• Luego lo que es tuyo (capital)\n• Cuando la cuota está completa → para solo\n\nSin llamadas. Sin visitas. Se maneja solo. 💙" },
{ de: "cliente", delay: 1600,
texto: "me parece bien, ¿cómo lo activo?" },
{ de: "banco", delay: 900,
texto: "Respondé acá mismo con el número que elegís:\n1️⃣ = 1% por venta\n2️⃣ = 2% por venta\n3️⃣ = 5% por venta\nY listo — quedás registrado (Res. SBS 02522-2025). 📋" },
{ de: "cliente", delay: 1400,
texto: "2" },
{ de: "banco", delay: 800,
texto: "✅ YoSiLa activado al 2%, Powel.\nEn cuanto recibas Yapes, el % empieza a trabajar para vos. 💙\nTe avisamos cuando el interés esté cubierto y cuando la cuota esté completa.\nSin llamadas. Sin presión." },
],
},
};

let perfilActual = "alessia";
let etapaActual = "temprana";
const timeouts = [];

function fmt(str) {
return str
.replace(/\*(.*?)\*/g, "<b>$1</b>")
.replace(/\n/g, "<br>");
}
function hora() {
const now = new Date();
return now.getHours().toString().padStart(2,"0") + ":" + now.getMinutes().toString().padStart(2,"0");
}
function later(ms) { return new Promise(r => timeouts.push(setTimeout(r, ms))); }
function clearTimers() { timeouts.forEach(clearTimeout); timeouts.length = 0; }

const chatBody = () => document.getElementById("chatBody");

function scrollBottom() {
const b = chatBody();
b.scrollTop = b.scrollHeight;
}

function appendDateDivider(label) {
const el = document.createElement("div");
el.className = "date-divider";
el.innerHTML = `<span>${label}</span>`;
chatBody().appendChild(el);
scrollBottom();
}

function appendSysCard(msg) {
const el = document.createElement("div");
if (msg.tipo === "llamada") {
el.className = "sys-card sys-llamada";
} else if (msg.tipo === "campo") {
el.className = "sys-card sys-campo";
} else {
el.className = "sys-card";
}
if (msg.tipo !== "progreso") {
el.innerHTML = `<div class="msg-bubble" style="background:none;padding:0;box-shadow:none">${fmt(msg.texto)}</div>`;
}
chatBody().appendChild(el);
scrollBottom();
}

function appendProgressCard(msg) {
const el = document.createElement("div");
el.className = "yk-card";
const capPct = Math.min(100, msg.capital_pct);
const intPct = Math.min(100, msg.interes_pct);
el.innerHTML = `
<div class="yk-card-title">📊 ${msg.titulo}</div>
<div class="yk-bar-row">
<div class="yk-bar-label">Interés <span>${intPct}%${intPct >= 100 ? ' ✅' : ''}</span></div>
<div class="yk-track"><div class="yk-fill" style="width:${intPct}%"></div></div>
</div>
<div class="yk-bar-row">
<div class="yk-bar-label">Capital <span>${capPct}%${capPct >= 100 ? ' ✅' : ''}</span></div>
<div class="yk-track"><div class="yk-fill cap" style="width:${capPct}%"></div></div>
</div>
<div class="yk-sub">${msg.sub}</div>
<div class="yk-meta">${hora()} <span class="ticks">✓✓</span></div>`;
chatBody().appendChild(el);
scrollBottom();
}

function appendTyping() {
const el = document.createElement("div");
el.className = "msg msg-bank typing";
el.id = "typingDots";
el.innerHTML = `<div class="msg-bubble"><div class="dots"><span></span><span></span><span></span></div></div>`;
chatBody().appendChild(el);
scrollBottom();
return el;
}

function removeTyping() {
const el = document.getElementById("typingDots");
if (el) el.remove();
}

function appendBubble(msg) {
const el = document.createElement("div");
el.className = "msg msg-" + (msg.de === "banco" ? "bank" : "client");
const h = hora();
const ticks = msg.de === "banco" ? `<span class="ticks">✓✓</span>` : "";
el.innerHTML = `
<div class="msg-bubble">${fmt(msg.texto)}</div>
<div class="msg-meta">${h} ${ticks}</div>`;
chatBody().appendChild(el);
scrollBottom();
}

async function reproducir() {
const msgs = (CONV[perfilActual] || {})[etapaActual] || [];
const body = chatBody();
body.innerHTML = "";
appendDateDivider("hoy");

for (const msg of msgs) {
await later(msg.delay || 600);
if (msg.de === "sistema") {
if (msg.tipo === "progreso") {
appendProgressCard(msg);
} else {
appendSysCard(msg);
}
} else if (msg.de === "banco") {
const typDelay = 900 + msg.texto.length * 14;
appendTyping();
await later(Math.min(typDelay, 2000));
removeTyping();
appendBubble(msg);
} else {
appendBubble(msg);
}
}
}

function renderPerfiles() {
const cont = document.getElementById("profileList");
cont.innerHTML = Object.values(PERFILES).map(p => `
<div class="profile-card ${p.id === perfilActual ? 'active' : ''}" data-id="${p.id}">
<div class="profile-avatar" style="background:${p.color}">${p.avatar}</div>
<div class="profile-info">
<div class="profile-name">${p.nombre}</div>
<div class="profile-type">${p.tipo}</div>
<div class="profile-nota">${p.nota}</div>
<span class="canal-badge ${p.canal === 'whatsapp' ? 'canal-wa' : 'canal-llamada'}">
${p.canal === 'whatsapp' ? '💬 WhatsApp' : '📞 Llamada'}
</span>
</div>
</div>`).join("");
document.querySelectorAll(".profile-card").forEach(c =>
c.addEventListener("click", () => {
perfilActual = c.dataset.id;
renderPerfiles();
updateWAHeader();
resetAndPlay();
})
);
}

function renderEtapas() {
const cont = document.getElementById("etapaList");
cont.innerHTML = ETAPAS.map(e => `
<button class="stage-btn ${e.id === etapaActual ? 'active' : ''}" data-id="${e.id}">
<div class="stage-dot"></div>
<div>
<div class="stage-label">${e.label}</div>
<div class="stage-sub">${e.sub}</div>
</div>
</button>`).join("");
document.querySelectorAll(".stage-btn").forEach(b =>
b.addEventListener("click", () => {
etapaActual = b.dataset.id;
renderEtapas();
resetAndPlay();
})
);
}

function updateWAHeader() {
const p = PERFILES[perfilActual];
const hdr = document.getElementById("waHeader");
hdr.innerHTML = `
<div class="wa-avatar-wrap" style="background:${p.color}">${p.avatar}</div>
<div class="wa-contact">
<div class="wa-cname">Mibanco Cobranzas <span class="verified">✅ Verificado</span></div>
<div class="wa-status">en línea · ${p.nombre}</div>
</div>
<div class="wa-actions">📞 ⋮</div>`;
}

function resetAndPlay() {
clearTimers();
reproducir();
}

document.addEventListener("DOMContentLoaded", () => {
renderPerfiles();
renderEtapas();
updateWAHeader();
reproducir();
});

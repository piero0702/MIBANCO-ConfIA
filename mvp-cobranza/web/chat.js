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
titulo: "YoSiLa en marcha · día 12",
interes_pct: 72, capital_pct: 0,
sub: "12 días · 28 transacciones Yape",
delay: 400 },
{ de: "banco", delay: 700,
texto: "*Mibanco* ✅ 📊\n¡Alessia, van muy bien! Llevan 12 días.\nEl interés de junio va al 72% — cada Yape que recibís suma automático." },
{ de: "sistema", tipo: "yape-transaccion",
remitente: "Juan Quispe", monto: 95, pct: 2, interes_pct: 79,
delay: 1200 },
{ de: "cliente", delay: 1800,
texto: "😍 wow no me había dado cuenta de todo eso" },
{ de: "banco", delay: 900,
texto: "¡Así es Alessia! Cada cliente que te paga por Yape → el 2% va directo a la cuota.\nVos solo cobrás. YoSiLa hace el resto. 💙" },
{ de: "sistema", tipo: "progreso",
titulo: "🎉 ¡Interés 100% cubierto!",
interes_pct: 100, capital_pct: 40,
sub: "17 días · 42 transacciones · interés: VENCIDO ✅",
delay: 1200 },
{ de: "banco", delay: 700,
texto: "*Mibanco* ✅ 🎉\n¡Ya cubriste el 100% del interés de junio, Alessia!\nLo que te queda (S/350) es plata TUYA devolviendo capital, no costo del banco." },
{ de: "sistema", tipo: "yape-transaccion",
remitente: "Sofía Ramos", monto: 120, pct: 2, interes_pct: 100,
delay: 1000 },
{ de: "cliente", delay: 1600,
texto: "ojalá lo hubiera activado antes 🙌 qué fácil" },
{ de: "sistema", tipo: "progreso",
titulo: "✅ ¡Cuota PAGADA! Auto-stop",
interes_pct: 100, capital_pct: 100,
sub: "28 días · 67 transacciones · 0 llamadas de cobranza",
delay: 1400 },
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
texto: "*Mibanco* ✅ Hola Powel 👋\nTenemos una forma de cubrir tu cuota sin llamadas ni visitas — se llama YoSiLa.\nCada pago Yape que recibís en tu negocio, un % chico va directo a tu cuota. Se para solo al completar.\n¿Querés que te expliquemos cómo funciona?" },
{ de: "cliente", delay: 2000,
texto: "¿y eso cómo sería?" },
{ de: "banco", delay: 900,
texto: "Primero necesitás tener Yape, Powel. Es gratis y demora 5 minutos:" },
{ de: "sistema", tipo: "yape-registro", delay: 1200 },
{ de: "cliente", delay: 2200,
texto: "no, todavía no lo tengo" },
{ de: "banco", delay: 1000,
texto: "Sin problema 🤝 Tu asesora María te acompaña una sola vez.\nCuando ya tenés Yape, cada cliente que te paga por Yape se ve así:" },
{ de: "sistema", tipo: "yape-transaccion",
remitente: "Carmen Flores", monto: 75, pct: 2, interes_pct: 45,
delay: 1400 },
{ de: "cliente", delay: 2000,
texto: "no sabía que era tan fácil ¿y cómo lo activo para mi cuota?" },
{ de: "banco", delay: 900,
texto: "Con YoSiLa, ese % que ves arriba va automático a tu cuota:\n• Primero cubre el interés del mes ✅\n• Luego el capital (lo que es tuyo)\n• Se para solo al completar\n\nActivalo respondiendo acá mismo:\n1️⃣ = 1% · 2️⃣ = 2% · 3️⃣ = 5%" },
{ de: "cliente", delay: 1400,
texto: "2" },
{ de: "banco", delay: 800,
texto: "✅ YoSiLa activado al 2%, Powel.\nEn cuanto recibas Yapes, el % trabaja solo para tu cuota. 💙\nTe avisamos al cubrir el interés y al completar la cuota.\nSin llamadas. Sin presión." },
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

/* ── Yape second phone ── */

function setYapeContent(tipo, msg) {
const head = document.getElementById("yapeHead").querySelector(".yp-head-title");
const body = document.getElementById("yapeBody");
if (tipo === "registro") {
head.textContent = "Registro";
body.innerHTML = `
<div class="yp-reg">
  <div class="yp-reg-title">Registrate gratis · solo la primera vez</div>
  <div class="yp-step"><span class="yp-ic">✓</span><div><b>Descargá Yape</b><small>Google Play o App Store · gratis</small></div></div>
  <div class="yp-step"><span class="yp-ic">✓</span><div><b>Ingresá tu número de celular</b><small>Verificación por SMS automática</small></div></div>
  <div class="yp-step"><span class="yp-ic">✓</span><div><b>Validá con tu DNI</b><small>Sin necesitar cuenta BCP</small></div></div>
  <div class="yp-step active"><span class="yp-ic">→</span><div><b>Creá tu contraseña personal</b><small>¡Ya estás dentro de Yape! 🎉</small></div></div>
  <div class="yp-reg-ok">✅ Listo para recibir y enviar pagos · transferencias gratuitas</div>
</div>`;
} else if (tipo === "transaccion" && msg) {
head.textContent = "Pago recibido";
const pct = msg.pct || 2;
const aporte = (msg.monto * pct / 100).toFixed(2);
const intPct = Math.min(100, msg.interes_pct || 0);
body.innerHTML = `
<div class="yp-tx">
  <div class="yp-tx-hero">
    <div class="yp-tx-hero-ico">💰</div>
    <div class="yp-tx-hero-label">Pago recibido</div>
    <div class="yp-tx-hero-amount">+ S/ ${Number(msg.monto).toFixed(2)}</div>
    <div class="yp-tx-hero-from">de ${msg.remitente}</div>
    <div class="yp-tx-hero-time">${hora()} · Llegó al instante ✓</div>
  </div>
  <div class="yp-tx-body">
    <div class="yp-tx-row"><span>Monto recibido</span><span style="color:#16a34a">+ S/ ${Number(msg.monto).toFixed(2)}</span></div>
    <div class="yp-tx-row"><span>De</span><span>${msg.remitente}</span></div>
    <div class="yp-tx-row"><span>Estado</span><span>✅ Acreditado</span></div>
    <div class="yp-ys-strip">
      <div class="yp-ys-strip-h">⚡ YoSiLa · ${pct}% por venta → cuota Mibanco</div>
      <div class="yp-ys-strip-row">
        <span>S/ ${aporte} imputado a cuota</span>
        <span class="yp-ys-ok">✓ imputado</span>
      </div>
      <div class="yp-ys-prog-lbl"><span>Interés del mes</span><span>${intPct}%${intPct >= 100 ? ' ✅' : ''}</span></div>
      <div class="yp-ys-track"><div class="yp-ys-fill" style="width:${intPct}%"></div></div>
    </div>
  </div>
</div>`;
}
}

async function animateYapeSteps() {
const steps = document.querySelectorAll("#yapeBody .yp-step");
for (const step of steps) {
step.classList.add("yp-step-visible");
await later(650);
}
await later(2000);
}

async function showYapeScreen(tipo, msg) {
setYapeContent(tipo, msg);
document.getElementById("yapePhone").classList.add("yp-visible");
document.getElementById("waPhone").classList.add("yp-push");
if (tipo === "registro") {
await animateYapeSteps();
} else {
await later(3800);
}
document.getElementById("yapePhone").classList.remove("yp-visible");
document.getElementById("waPhone").classList.remove("yp-push");
await later(500);
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
} else if (msg.tipo === "yape-registro") {
await showYapeScreen("registro", null);
} else if (msg.tipo === "yape-transaccion") {
await showYapeScreen("transaccion", msg);
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
document.getElementById("yapePhone")?.classList.remove("yp-visible");
document.getElementById("waPhone")?.classList.remove("yp-push");
reproducir();
}

document.addEventListener("DOMContentLoaded", () => {
renderPerfiles();
renderEtapas();
updateWAHeader();
reproducir();
});

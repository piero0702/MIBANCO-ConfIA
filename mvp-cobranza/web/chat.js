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
{ de: "banco", delay: 500,
texto: "*Mibanco* ✅ Hola Alessia 👋\nTenemos una forma de cubrir tu cuota sin llamadas ni visitas — se llama *YoSiLa*.\nCada Yape que recibís en el negocio, un % chico va directo a tu cuota. Se para solo al completar.\n¿Querés que te expliquemos cómo?" },
{ de: "banco", tipo: "img-yosila", delay: 1000, datos: {
  nombre: "Alessia Borrelli",
  credito: "S/ 3,200 · 24 meses",
  cuota: 450, interes: 98, capital: 352,
  ventas_dia: 920, tx_promedio: 150, pct: 2, dias_interes: 6, dias_cuota: 25,
}},
{ de: "cliente", delay: 2000,
texto: "esto está buenísimo 😮 ¿cómo lo activo?" },
{ de: "banco", delay: 800,
texto: "Fácil — escríbeme el % que quieres:\n1️⃣ = 1% · *2️⃣ = 2%* · 3️⃣ = 5%\n(El 2% es lo más popular — cubres la cuota sin sentirla.)" },
{ de: "cliente", delay: 1200,
texto: "2" },
{ de: "banco", delay: 800,
texto: "✅ *YoSiLa activado al 2%*, Alessia.\nCada Yape que recibas → 2% va a tu cuota.\nTe avisamos en 3 momentos: interés 50% · interés 100% 🎉 · cuota completa → se para solo.\n¡A vender! 💙" },
{ de: "sistema", tipo: "yape-sender-demo",
remitente: "Juan Quispe", destinatario: "Alessia Borrelli", monto_bruto: 150, pct: 2, interes_pct: 12,
delay: 2200 },
{ de: "banco", delay: 700,
texto: "💜 *YoSiLa* ✅\nRecibiste *S/150.00* de Juan Quispe.\nSe descontaron automáticamente *S/3.00* de tu cuota.\nInterés de junio: *12% cubierto* · Quedan S/86 por cubrir." },
{ de: "cliente", delay: 1600,
texto: "oye! vi la notif de Yape y me llegó también acá 😮 esto es en serio automático" },
{ de: "banco", delay: 900,
texto: "¡Así es Alessia! Cada Yape que recibes → el 2% trabaja solo.\nTú solo cobras. YoSiLa hace el resto. 💙" },
{ de: "cliente", delay: 1400,
texto: "wow no me di cuenta que iba tan rápido 😍" },
{ de: "sistema", tipo: "yape-push",
remitente: "Sofía Ramos", monto_bruto: 200, pct: 2, interes_pct: 27,
delay: 2000 },
{ de: "banco", delay: 700,
texto: "💜 *YoSiLa* ✅\nRecibiste *S/200.00* de Sofía Ramos.\nSe descontaron automáticamente *S/4.00* de tu cuota.\nInterés de junio: *27% cubierto* · Quedan S/71 por cubrir." },
{ de: "sistema", tipo: "progreso",
titulo: "📊 YoSiLa · día 17",
interes_pct: 100, capital_pct: 35,
sub: "17 días · 42 transacciones · interés: ¡GANADO! ✅",
delay: 1000 },
{ de: "banco", delay: 600,
texto: "*Mibanco* ✅ 🎉\n¡Cubriste el 100% del interés de junio, Alessia!\nLo que queda (S/292) es plata TUYA devolviendo capital — no costo del banco. 💙" },
{ de: "sistema", tipo: "yape-push",
remitente: "Pedro Torres", monto_bruto: 180, pct: 2, interes_pct: 100,
delay: 1600 },
{ de: "banco", delay: 700,
texto: "💜 *YoSiLa* ✅\nRecibiste *S/180.00* de Pedro Torres.\nSe descontaron automáticamente *S/3.60*.\n🎉 Interés del mes: *¡GANADO!* ✅ Todo lo que sigue va directo a capital tuyo." },
{ de: "sistema", tipo: "progreso",
titulo: "✅ ¡Cuota PAGADA! Auto-stop",
interes_pct: 100, capital_pct: 100,
sub: "28 días · 67 transacciones · 0 llamadas de cobranza",
delay: 1000 },
{ de: "banco", delay: 700,
texto: "*Mibanco* ✅ ✅\n¡Cuota de junio PAGADA, Alessia! 🎉\nYoSiLa se paró automático.\nCero llamadas. Cero presión. Todo con tus ventas de Yape. 💙\n¿Adelantamos julio? SÍ / NO" },
{ de: "cliente", delay: 1300,
texto: "SÍ! ojalá lo hubiera activado mucho antes 🙌" },
{ de: "banco", delay: 700,
texto: "✅ YoSiLa activo para julio, Alessia.\n¡Éxitos con el negocio! 💙" },
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
texto: "*Mibanco* ✅ Hola Powel 👋\nTu asesora María acaba de llamarte.\nTu cuota de S/260 lleva 6 días vencida.\nTe propuso reprogramar para el 5 de julio.\nResponde SÍ o NO para confirmar 👇" },
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
texto: "*Mibanco* ✅ Hola Powel 👋\nTu cuota lleva 22 días vencida.\nTu asesora María conversó contigo hoy sobre opciones.\nTe resumimos lo acordado:\n• Pago parcial de S/130 esta semana ✅\n• Resto (S/130) el 15 de julio\nResponde SÍ para registrarlo. 👇" },
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
texto: "*Mibanco* ✅ Hola Powel 👋\nTenemos una forma de cubrir tu cuota sin llamadas ni visitas — se llama *YoSiLa*.\nCada Yape que recibís en el negocio, un % chico va directo a tu cuota. Se para solo al completar.\n¿Querés que te expliquemos cómo?" },
{ de: "banco", tipo: "img-yosila", delay: 1000, datos: {
  nombre: "Powel Aliaga",
  credito: "S/ 1,800 · 18 meses",
  cuota: 260, interes: 55, capital: 205,
  ventas_dia: 480, tx_promedio: 80, pct: 2, dias_interes: 6, dias_cuota: 28,
}},
{ de: "cliente", delay: 2200,
texto: "¿y eso cómo sería?" },
{ de: "banco", delay: 900,
texto: "Primero necesitás tener Yape, Powel 📱\nEs gratis y demora 5 minutos — tu asesora María te acompaña una sola vez:" },
{ de: "sistema", tipo: "yape-registro", delay: 1200 },
{ de: "cliente", delay: 2200,
texto: "listo, ya lo hice con María — ya tengo Yape 💪" },
{ de: "banco", delay: 1000,
texto: "¡Perfecto Powel! 💙 Ahora activamos YoSiLa.\nCada cliente que te pague por Yape → un % va automático a tu cuota:\n• Primero cubre el interés del mes ✅\n• Luego el capital (lo que es tuyo)\n• Se para solo al completar\n\nElegí el %:\n1️⃣ = 1% · *2️⃣ = 2%* · 3️⃣ = 5%" },
{ de: "cliente", delay: 1400,
texto: "2" },
{ de: "banco", delay: 800,
texto: "✅ *YoSiLa activado al 2%*, Powel.\nCuando alguien te pague por Yape, vas a ver algo así en tu notificación:" },
{ de: "sistema", tipo: "yape-sender-demo",
remitente: "Carmen Flores", destinatario: "Powel Aliaga", monto_bruto: 150, pct: 2, interes_pct: 7,
delay: 1500 },
{ de: "banco", delay: 700,
texto: "💜 *YoSiLa* ✅\nRecibiste *S/150.00* de Carmen Flores.\nSe descontaron automáticamente *S/3.00* de tu cuota Mibanco.\nInterés de junio: *7% cubierto* · Quedan S/51 por cubrir." },
{ de: "cliente", delay: 2000,
texto: "eso que me llegó es real? dice que Carmen me mandó 150 pero recibí 147..." },
{ de: "banco", delay: 900,
texto: "¡Exacto, Powel! ✅\nEsos S/3 que «no aparecen» fueron automáticamente a tu cuota Mibanco.\nYape los transfirió solo — tú no haces nada. Solo sigues cobrando como siempre. 💙" },
{ de: "cliente", delay: 1600,
texto: "eso está buenísimo... no sabía que era tan fácil" },
{ de: "sistema", tipo: "yape-push",
remitente: "Rosa Huanca", monto_bruto: 200, pct: 2, interes_pct: 20,
delay: 2000 },
{ de: "banco", delay: 700,
texto: "💜 *YoSiLa* ✅\nRecibiste *S/200.00* de Rosa Huanca.\nSe descontaron automáticamente *S/4.00* de tu cuota Mibanco.\nInterés de junio: *20% cubierto* · Quedan S/44 por cubrir." },
{ de: "sistema", tipo: "progreso",
titulo: "📊 YoSiLa · día 14",
interes_pct: 58, capital_pct: 0,
sub: "14 días · 31 transacciones Yape",
delay: 900 },
{ de: "banco", delay: 600,
texto: "*Mibanco* ✅ 📊 Powel, llevan 14 días.\nEl interés del mes va al 58% — cada Yape que recibís suma automático. 💪" },
{ de: "sistema", tipo: "yape-push",
remitente: "Luis Mamani", monto_bruto: 300, pct: 2, interes_pct: 72,
delay: 1800 },
{ de: "banco", delay: 700,
texto: "💜 *YoSiLa* ✅\nRecibiste *S/300.00* de Luis Mamani.\nSe descontaron automáticamente *S/6.00* de tu cuota Mibanco.\nInterés de junio: *72% cubierto* · Quedan S/15 por cubrir." },
{ de: "sistema", tipo: "progreso",
titulo: "🎉 ¡Interés 100% cubierto!",
interes_pct: 100, capital_pct: 30,
sub: "22 días · 52 transacciones · interés: ¡GANADO! ✅",
delay: 1000 },
{ de: "banco", delay: 700,
texto: "*Mibanco* ✅ 🎉 ¡Powel, cubriste el 100% del interés!\nLo que queda (S/182) es plata TUYA, no costo del banco. 💙" },
{ de: "sistema", tipo: "progreso",
titulo: "✅ ¡Cuota PAGADA! Auto-stop",
interes_pct: 100, capital_pct: 100,
sub: "31 días · 72 transacciones · 0 llamadas · 0 visitas",
delay: 1400 },
{ de: "banco", delay: 800,
texto: "*Mibanco* ✅ ✅ ¡Cuota PAGADA, Powel! 🎉\nYoSiLa se paró automático.\nSin una sola llamada. Sin visitas. Solo tus Yapes trabajando. 💙\n¿Seguimos el próximo mes?" },
{ de: "cliente", delay: 2000,
texto: "sí! muy bueno esto, gracias Mibanco 🙏" },
{ de: "banco", delay: 700,
texto: "✅ YoSiLa activo para julio, Powel.\n¡Éxitos en el mercado! 💙" },
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
const head = document.getElementById("yapeHeadTitle");
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
      <div class="yp-ys-strip-h">⚡ YoSiLa · ${pct}% por venta → cuota Mibanco <span class="yp-ys-live">● activo</span></div>
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

function appendImgYoSiLa(msg) {
const d = msg.datos;
const aporteDia  = Math.round(d.ventas_dia * d.pct / 100);
const aporteEj   = (d.tx_promedio * d.pct / 100).toFixed(2);
const netoEj     = (d.tx_promedio - aporteEj).toFixed(2);
const el = document.createElement("div");
el.className = "msg msg-bank";
const h = hora();
el.innerHTML = `
<div class="msg-img-bubble">
  <div class="yk-img-card">

    <div class="yk-img-head">
      <span class="yk-img-logo">💜 YoSiLa</span>
      <span class="yk-img-badge">Mibanco ✅</span>
    </div>
    <div class="yk-img-nombre">${d.nombre} · al ${d.pct}%</div>

    <!-- HERO: por transacción -->
    <div class="yk-img-hero">
      <div class="yk-img-hero-eyebrow">Por cada Yape que recibís:</div>
      <div class="yk-img-hero-ex">
        <div class="yk-img-hero-gross">
          <div class="yk-img-hero-amt">S/ ${Number(d.tx_promedio).toFixed(2)}</div>
          <div class="yk-img-hero-lbl">cobrado</div>
        </div>
        <div class="yk-img-hero-arr">→</div>
        <div class="yk-img-hero-cols">
          <div class="yk-img-hero-row-net">
            <span class="yk-img-hero-net-val">S/ ${netoEj}</span>
            <span class="yk-img-hero-net-lbl">para vos</span>
          </div>
          <div class="yk-img-hero-row-ap">
            <span class="yk-img-hero-ap-val">S/ ${aporteEj}</span>
            <span class="yk-img-hero-ap-lbl">→ cuota ✅</span>
          </div>
        </div>
      </div>
      <div class="yk-img-hero-note">automático · al instante · sin hacer nada</div>
    </div>

    <div class="yk-img-divider"></div>

    <!-- Cuota del mes (compacto) -->
    <div class="yk-img-cuota-row">
      <div class="yk-img-cuota-left">
        <div class="yk-img-cuota-label">Cuota del mes</div>
        <div class="yk-img-cuota-val">S/ ${d.cuota}</div>
      </div>
      <div class="yk-img-cuota-right">
        <div class="yk-img-br"><span class="yk-img-br-l">Interés</span><span class="yk-img-br-v int">S/ ${d.interes}</span></div>
        <div class="yk-img-br"><span class="yk-img-br-l">Capital</span><span class="yk-img-br-v">S/ ${d.capital}</span></div>
        <div class="yk-img-br yk-img-br-sm"><span class="yk-img-br-l">Crédito</span><span class="yk-img-br-v">${d.credito}</span></div>
      </div>
    </div>

    <div class="yk-img-divider"></div>

    <!-- Simulación -->
    <div class="yk-img-sim">
      <div class="yk-img-sim-row">
        <span>Aporte estimado / día</span>
        <span class="yk-img-green"><b>S/ ${aporteDia}</b></span>
      </div>
      <div class="yk-img-sim-row yk-img-sim-hl">
        <span>Cuota completa en aprox.</span>
        <span><b>~${d.dias_cuota} días</b></span>
      </div>
    </div>

    <div class="yk-img-foot">0 llamadas · 0 visitas · se para solo al completar</div>
  </div>
</div>
<div class="msg-time" style="margin-top:2px">${h} <span class="ticks">✓✓</span></div>`;
chatBody().appendChild(el);
scrollBottom();
}

async function showYapeSenderDemo(msg) {
const initials = n => n.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
const sI = initials(msg.remitente);

document.getElementById("senderBody").innerHTML = `
<div class="sp-pay" id="spPay">
  <div class="sp-pay-from">
    <div class="sp-avatar sp-avatar-sender">${sI}</div>
    <div class="sp-pay-from-name">${msg.remitente}</div>
    <div class="sp-pay-from-sub">enviando desde su Yape</div>
  </div>
  <div class="sp-pay-arrow">↓</div>
  <div class="sp-pay-to">
    <div class="sp-avatar sp-avatar-dest">
      <img src="icons/client-avatar.png" alt="${msg.destinatario}" class="sp-avatar-img" />
    </div>
    <div class="sp-pay-to-name">${msg.destinatario}</div>
    <div class="sp-pay-to-sub">💜 usuario Yape verificado</div>
  </div>
  <div class="sp-pay-amount">S/ ${Number(msg.monto_bruto).toFixed(2)}</div>
  <div class="sp-pay-amount-label">monto a enviar</div>
  <button class="sp-btn-confirm" id="spConfirmBtn">Confirmar yapeo →</button>
</div>
<div class="sp-success" id="spSuccess">
  <div class="sp-success-ic">✅</div>
  <div class="sp-success-title">¡Yapeo enviado!</div>
  <div class="sp-success-amt">S/ ${Number(msg.monto_bruto).toFixed(2)}</div>
  <div class="sp-success-to">a ${msg.destinatario}</div>
  <div class="sp-success-note">Llegó al instante · sin costo</div>
</div>`;

/* Celular de Juan Quispe entra por la izquierda; WA se corre a la derecha */
document.getElementById("phonesDuoWrap").classList.add("sp-active");

await later(1800);

const btn = document.getElementById("spConfirmBtn");
if (btn) btn.classList.add("sp-pressing");
await later(500);

const succ = document.getElementById("spSuccess");
if (succ) succ.classList.add("sp-success-show");
await later(1800);

document.getElementById("phonesDuoWrap").classList.remove("sp-active");
await later(500);

await showYapePush(msg);
}

async function showYapePush(msg) {
const aporte = +(msg.monto_bruto * msg.pct / 100).toFixed(2);
const neto   = +(msg.monto_bruto - aporte).toFixed(2);
const push = document.createElement("div");
push.className = "yape-push-notif";
push.innerHTML = `
<div class="ypn-inner">
  <div class="ypn-header">
    <span class="ypn-app">💜 yape</span>
    <span class="ypn-time">ahora</span>
  </div>
  <div class="ypn-title">${msg.remitente} te envió <b>S/ ${Number(msg.monto_bruto).toFixed(2)}</b></div>
  <div class="ypn-sub">Recibiste S/ ${neto.toFixed(2)} &nbsp;·&nbsp; <span class="ypn-ys">S/ ${aporte.toFixed(2)} → cuota Mibanco ✅</span></div>
</div>`;
document.getElementById("phoneContainer").appendChild(push);
await later(200);
push.classList.add("ypn-in");
await later(4200);
push.classList.remove("ypn-in");
await later(500);
push.remove();
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
document.getElementById("appLabel").classList.add("yp-mode");
document.getElementById("phoneContainer").classList.add("yp-shadow");
if (tipo === "registro") {
await animateYapeSteps();
} else {
await later(3800);
}
document.getElementById("yapePhone").classList.remove("yp-visible");
document.getElementById("waPhone").classList.remove("yp-push");
document.getElementById("appLabel").classList.remove("yp-mode");
document.getElementById("phoneContainer").classList.remove("yp-shadow");
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
el.innerHTML = fmt(msg.texto);
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
<div class="msg-bubble">${fmt(msg.texto)}<span class="msg-time">${h} ${ticks}</span></div>`;
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
} else if (msg.tipo === "yape-sender-demo") {
await showYapeSenderDemo(msg);
} else if (msg.tipo === "yape-push") {
await showYapePush(msg);
} else if (msg.tipo === "yape-transaccion") {
await showYapeScreen("transaccion", msg);
} else {
appendSysCard(msg);
}
} else if (msg.de === "banco") {
if (msg.tipo === "img-yosila") {
appendTyping();
await later(1200);
removeTyping();
appendImgYoSiLa(msg);
} else {
const typDelay = 900 + msg.texto.length * 14;
appendTyping();
await later(Math.min(typDelay, 2000));
removeTyping();
appendBubble(msg);
}
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
<div class="wa-back-btn">
  <svg width="11" height="18" viewBox="0 0 11 18" fill="none"
       stroke="rgba(255,255,255,.9)" stroke-width="2.3"
       stroke-linecap="round" stroke-linejoin="round">
    <polyline points="9 1 1 9 9 17"/>
  </svg>
</div>
<div class="wa-avatar-wrap">
  <img src="icons/mibanco-tigre.png" alt="Mibanco" class="wa-avatar-img" />
</div>
<div class="wa-contact">
  <span class="wa-cname">Mibanco Cobranzas</span>
  <span class="wa-verif" title="Cuenta de empresa verificada">✓</span>
</div>`;
}

function resetAndPlay() {
clearTimers();
document.getElementById("yapePhone")?.classList.remove("yp-visible");
document.getElementById("yapePhone")?.classList.remove("yp-visible");
document.getElementById("phonesDuoWrap")?.classList.remove("sp-active");
document.getElementById("waPhone")?.classList.remove("yp-push");
document.getElementById("phoneContainer")?.classList.remove("sp-push-right", "yp-shadow");
document.getElementById("phonesStage")?.classList.remove("sp-active");
document.getElementById("appLabel")?.classList.remove("yp-mode");
reproducir();
}

document.addEventListener("DOMContentLoaded", () => {
renderPerfiles();
renderEtapas();
updateWAHeader();
document.getElementById("replayBtn").addEventListener("click", resetAndPlay);
reproducir();
});

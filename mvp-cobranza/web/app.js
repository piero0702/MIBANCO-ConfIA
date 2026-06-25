/* ============================================================
   AsesorIA + YateKobro — demo del cliente final
   Vanilla JS, sin dependencias.
   ============================================================ */
"use strict";
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const soles = n => "S/ " + Math.round(n).toLocaleString("es-PE");
const wait = ms => new Promise(r => setTimeout(r, reduced ? 0 : ms));

/* ---------------------------------------------------------------
   1) GUION DE LA CONVERSACIÓN (mensajes reales del documento)
   Cada paso: quién habla, contenido, y respuestas que puede dar el cliente.
--------------------------------------------------------------- */
const NEXT = {};        // mapa: id de respuesta -> índice del paso siguiente
const SCRIPT = [
  { who: "in", t: `Hola Rosa 👋 Te escribe <strong>Mibanco</strong> ✅<br>Tu cuota de <strong>S/310</strong> vence en 7 días. Podés pagar por Yape, la app o un agente BCP. ¡Gracias por tu puntualidad! 🙌`, tm: "9:02" },
  { who: "in", t: `¿Querés activar <strong>YateKobro</strong>? Con un pequeño % de cada venta por Yape vas cubriendo tu cuota sin sentirla — y reducís lo que pagás de interés.`, tm: "9:02",
    replies: [
      { id: "act2", label: "Activar al 2%" },
      { id: "act5", label: "Mejor al 5%" },
      { id: "no",   label: "Ahora no" },
    ] },

  // rama: activar 2%
  { branch: "act2", who: "out", t: `2`, tm: "9:03" },
  { who: "in", t: `✅ <strong>YateKobro activado al 2%</strong>, Rosa.<br>Cada Yape que recibas, el 2% va directo a tu cuota. Primero cubre el interés del mes, después el capital.<br>Para pausarlo cuando quieras, escribí <strong>PARAR</strong>.`, tm: "9:03" },
  { who: "in", t: `📊 Ya cubriste el <strong>50% del interés</strong> de este mes (S/51 de S/103). Seguimos 💪`, tm: "Mar 11:20",
    yk: { intPct: 50, capPct: 0, intM: "S/51 / S/103", capM: "S/0 / S/207" } },
  { who: "in", win: true, t: `🎉 ¡Rosa, ya cubriste el <strong>100% del interés</strong> de junio!<br>Lo que te queda (S/207) es <strong>plata tuya que estás devolviendo</strong>, no costo del banco. Llevás 5 días, 21 transacciones.`, tm: "Jue 16:40",
    yk: { intPct: 100, capPct: 0, intM: "S/103 / S/103 ✓", capM: "S/0 / S/207" } },
  { who: "in", win: true, t: `✅ <strong>¡Cuota de junio PAGADA, Rosa!</strong> YateKobro se pausó automático.<br>¿Querés adelantar la cuota de julio y seguir reduciendo interés?`, tm: "Lun 12:10",
    yk: { intPct: 100, capPct: 100, intM: "S/103 / S/103 ✓", capM: "S/207 / S/207 ✓" },
    replies: [
      { id: "si", label: "Sí, seguir" },
      { id: "parar", label: "No, pausar" },
    ] },
  { branch: "si", who: "out", t: `Sí`, tm: "Lun 12:11" },
  { who: "in", t: `🙌 ¡Genial! Seguimos al 2% con la cuota de julio. Te dejamos tranquila y solo confirmamos cerca de la fecha.`, tm: "Lun 12:11", end: true },
  { branch: "parar", who: "out", t: `No`, tm: "Lun 12:11" },
  { who: "in", t: `✅ Listo Rosa, quedamos pausados hasta que se acerque julio. Cero llamadas, cero molestias. Gracias por tu confianza 🤝`, tm: "Lun 12:11", end: true },

  // rama: activar 5%
  { branch: "act5", who: "out", t: `5`, tm: "9:03" },
  { who: "in", t: `✅ <strong>YateKobro activado al 5%</strong>, Rosa. A este ritmo cubrís tu cuota mucho más rápido. Primero el interés, después el capital.`, tm: "9:03" },
  { who: "in", win: true, t: `🎉 ¡Rosa, ya cubriste el <strong>100% del interés</strong>! En 2 días. Lo que queda es plata tuya. Seguimos hasta completar la cuota.`, tm: "Mié 18:05",
    yk: { intPct: 100, capPct: 30, intM: "S/103 / S/103 ✓", capM: "S/62 / S/207" }, end: true },

  // rama: ahora no
  { branch: "no", who: "out", t: `Ahora no`, tm: "9:03" },
  { who: "in", t: `Sin problema, Rosa 🙂 Te dejamos el recordatorio amable y nada más. Si cambiás de idea, escribí <strong>YATEKOBRO</strong> cuando quieras.`, tm: "9:03", end: true },
];

// indexar ramas
SCRIPT.forEach((s, i) => { if (s.branch) NEXT[s.branch] = i; });

const body = $("#waBody");
const repliesBox = $("#waReplies");
let busy = false;

function clearReplies() { repliesBox.innerHTML = `<span class="wa-ph">Escribe un mensaje…</span>`; }

function bubble(step) {
  const el = document.createElement("div");
  el.className = `msg ${step.who}${step.win ? " win" : ""}`;
  let html = step.t;
  if (step.yk) html += ykBar(step.yk);
  html += `<span class="tm">${step.tm || ""}${step.who === "out" ? " ✓✓" : ""}</span>`;
  el.innerHTML = html;
  body.appendChild(el);
  body.scrollTop = body.scrollHeight;
  return el;
}

function ykBar(yk) {
  return `<div class="ykbar">
    <div class="ykrow"><span>Interés</span><span>${yk.intPct}%</span></div>
    <div class="yktrack"><div class="ykfill int" style="width:${yk.intPct}%"></div></div>
    <div class="ykrow"><span>Capital · tuyo</span><span>${yk.capPct}%</span></div>
    <div class="yktrack"><div class="ykfill cap" style="width:${yk.capPct}%"></div></div>
  </div>`;
}

async function typing(ms = 900) {
  const t = document.createElement("div");
  t.className = "typing";
  t.innerHTML = "<i></i><i></i><i></i>";
  body.appendChild(t);
  body.scrollTop = body.scrollHeight;
  await wait(ms);
  t.remove();
}

function showReplies(replies) {
  repliesBox.innerHTML = "";
  replies.forEach(r => {
    const b = document.createElement("button");
    b.className = "wa-reply";
    b.textContent = r.label;
    b.onclick = () => choose(r.id);
    repliesBox.appendChild(b);
  });
}

// reproduce pasos secuenciales hasta toparse con replies / end / branch
async function play(from) {
  if (busy) return; busy = true;
  let i = from;
  while (i < SCRIPT.length) {
    const step = SCRIPT[i];
    if (step.branch && i !== from) break;     // llegó a otra rama: parar
    if (step.who === "in") await typing(step.win ? 1100 : 850);
    bubble(step);
    await wait(step.win ? 700 : 380);
    if (step.replies) { showReplies(step.replies); busy = false; return; }
    if (step.end) { clearReplies(); busy = false; return; }
    i++;
  }
  busy = false;
}

async function choose(id) {
  if (busy) return;
  clearReplies();
  await play(NEXT[id]);
}

/* arranque del chat al cargar y con el botón */
let started = false;
async function startChat() {
  if (started) return; started = true;
  await play(0);
}
$("#ctaPlay").onclick = () => {
  if (started) { $("#demo").scrollIntoView({ behavior: "smooth", block: "center" }); }
  else startChat();
};
$("#waSend").onclick = startChat;

/* ---------------------------------------------------------------
   2) SIMULADOR YATEKOBRO (números del documento)
--------------------------------------------------------------- */
const CUOTA = 310, INTERES = 103, CAPITAL = 207;
let pct = 2, ventas = 1000;

function plural(n) { return n === 1 ? "día" : "días"; }

function renderSim() {
  const aporte = ventas * (pct / 100);                 // S/ por día a la cuota
  const dInt = Math.ceil(INTERES / aporte);
  const dCuota = Math.ceil(CUOTA / aporte);

  $("#ventasV").textContent = soles(ventas);
  $("#aporteDia").textContent = soles(aporte);
  $("#diasInteres").textContent = dInt + " " + plural(dInt);
  $("#diasCuota").textContent = dCuota + " " + plural(dCuota);

  // barras: estado "interés 100% + parte del capital" como en el caso estrella
  const capAcumDemo = Math.min(CAPITAL, Math.round(CAPITAL * 0.4)); // 40% capital de muestra
  setBar("int", 100, INTERES, INTERES);
  setBar("cap", Math.round(capAcumDemo / CAPITAL * 100), capAcumDemo, CAPITAL);
  $("#intWin").textContent = "¡vencido! ✓";

  // nota contextual honesta
  let nota = "";
  if (aporte * 31 < CUOTA) {
    nota = `Con ventas bajas, YateKobro cubre el interés (lo más caro) pero la cuota necesita un empujón extra a fin de mes — y aun así, sin una sola llamada de cobranza.`;
  } else if (dInt <= 3) {
    nota = `Un negocio activo de Gamarra vence su interés en ${dInt} ${plural(dInt)} y cancela la cuota en ${dCuota} ${plural(dCuota)} — todo con sus propias ventas, cero cobranza.`;
  } else {
    nota = `Rosa vence el interés en ${dInt} ${plural(dInt)} y completa su cuota en ${dCuota} ${plural(dCuota)}, sin sentir el descuento y sin recibir una sola llamada.`;
  }
  $("#simNote").textContent = nota;
}

function setBar(kind, p, monto, total) {
  $(`#${kind}Fill`).style.width = p + "%";
  $(`#${kind}Pct`).textContent = p + "%";
  $(`#${kind}Monto`).textContent = `S/${monto} de S/${total}`;
}

$$("#segPct button").forEach(b => b.onclick = () => {
  $$("#segPct button").forEach(x => x.classList.remove("on"));
  b.classList.add("on");
  pct = +b.dataset.v;
  renderSim();
});
$("#ventas").oninput = e => { ventas = +e.target.value; renderSim(); };

/* ---------------------------------------------------------------
   3) CONTADORES animados + REVEAL on scroll
--------------------------------------------------------------- */
function animateCount(el) {
  if (el.dataset.done) return;          // anima una sola vez
  el.dataset.done = "1";
  const target = parseFloat(el.dataset.count);
  const pre = el.dataset.prefix || "";
  const suf = el.dataset.suffix || "";
  const decimals = (String(target).split(".")[1] || "").length;
  if (reduced) { el.textContent = pre + Math.abs(target).toFixed(decimals) + suf; return; }
  const dur = 1100, t0 = performance.now(), sign = target < 0 ? "−" : "";
  const abs = Math.abs(target);
  function frame(now) {
    const k = Math.min(1, (now - t0) / dur);
    const e = 1 - Math.pow(1 - k, 3);
    el.textContent = (pre || sign) + (abs * e).toFixed(decimals) + suf;
    if (k < 1) requestAnimationFrame(frame);
    else el.textContent = (pre || sign) + abs.toFixed(decimals) + suf;
  }
  requestAnimationFrame(frame);
}

const io = new IntersectionObserver((entries) => {
  entries.forEach(en => {
    if (!en.isIntersecting) return;
    en.target.classList.add("in");
    if (en.target.dataset.count) animateCount(en.target);
    $$("[data-count]", en.target).forEach(animateCount);
    io.unobserve(en.target);
  });
}, { threshold: 0.2 });

// Cada contador vive dentro de un .reveal; observar solo .reveal evita doble animación.
$$(".reveal").forEach(el => io.observe(el));

/* init */
renderSim();
// auto-arranca el chat un instante después de cargar, para que el jurado vea movimiento
if (!reduced) setTimeout(startChat, 600); else startChat();

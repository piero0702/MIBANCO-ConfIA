/* ============================================================
   Lab UI — Motor de Cobranza Inteligente (AsesorIA + YateKobro)
   Lee la salida real de engine/*.py (web/data/*.json) y la muestra.
   El what-if de YateKobro replica la imputación del motor (yatekobro.py).
   ============================================================ */
"use strict";
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const soles = n => "S/ " + Math.round(n).toLocaleString("es-PE");
const milesK = n => "S/" + (Math.abs(n) >= 1000 ? (n / 1000).toFixed(0) + "k" : Math.round(n));
const CH = { whatsapp: "WhatsApp", sms: "SMS", llamada: "Llamada", campo: "Campo" };

let CLIENTES = [], BACKTEST = {}, YK = {}, CFG = {}, FILTER = "todos", SELC = null;

async function boot() {
  const get = f => fetch("data/" + f).then(r => r.json()).catch(() => null);
  [CLIENTES, BACKTEST, YK, CFG] = await Promise.all([
    get("clientes.json"), get("backtest.json"), get("yatekobro.json"), get("config.json"),
  ]);
  setupTabs();
  renderSource();
  renderBacktest();
  renderDecList(); if (CLIENTES.length) selectCli(CLIENTES[0].cliente_id);
  renderPresets(); recomputeYK();
  renderFlow();
  $("#footMeta").textContent =
    `AsesorIA: ${CLIENTES.length} clientes · backtest ${BACKTEST.fuente} · YateKobro ${YK.casos?.length||0} casos`;
}

/* ---------------- TABS ---------------- */
function activateTab(name) {
  const tab = $(`.tab[data-tab="${name}"]`); if (!tab) return;
  $$(".tab").forEach(x => x.classList.remove("active"));
  $$(".panel").forEach(x => x.classList.remove("active"));
  tab.classList.add("active");
  $("#tab-" + name).classList.add("active");
}
function setupTabs() {
  $$(".tab").forEach(t => t.onclick = () => { activateTab(t.dataset.tab); history.replaceState(null, "", "#" + t.dataset.tab); });
  const h = location.hash.replace("#", "");
  if (h) activateTab(h);
}
function renderSource() {
  const f = BACKTEST.fuente || "sintetico";
  const el = $("#srcBadge"); el.textContent = "fuente: " + f; el.classList.add(f);
  $("#btFuente").textContent = `Computado sobre ${(BACKTEST.n_creditos||0).toLocaleString("es-PE")} créditos (fuente: ${f}).`;
}

/* ---------------- BACKTEST ---------------- */
function renderBacktest() {
  const b = BACKTEST.baseline, p = BACKTEST.politica;
  if (!b) { $("#btTable").innerHTML = "<div class='empty'>sin datos de backtest</div>"; return; }
  const row = (k, now, ia) => `<div class="k">${k}</div><div class="v now">${now}</div><div class="v ia">${ia}</div>`;
  $("#btTable").innerHTML = `
    <div class="bt-head">
      <div class="bt-big">−${BACKTEST.reduccion_costo_pct}%</div>
      <div class="bt-big-l">costo de cobranza<br><b>${milesK(b.costo_total)} → ${milesK(p.costo_total)}</b> en la muestra</div>
    </div>
    <div class="bt-grid">
      <div class="h">métrica</div><div class="h now">Gestión actual</div><div class="h ia">Política AsesorIA</div>
      ${row("Contactos / crédito", b.contactos_x_credito, p.contactos_x_credito)}
      ${row("Costo / crédito", soles(b.costo_x_credito), soles(p.costo_x_credito))}
      ${row("Pago por contacto", (b.pago_x_contacto*100).toFixed(1)+"%", (p.pago_x_contacto*100).toFixed(1)+"%")}
      ${row("Costo total (muestra)", soles(b.costo_total), soles(p.costo_total))}
    </div>
    <div class="bt-note">Política: <b>máximo 2 contactos por crédito</b> + canal por perfil digital
      (digital → WhatsApp, no-digital → llamada). El costo se recalcula con los costos reales por canal
      y el pago con las tasas por canal × perfil. Recuperación a nivel crédito (≥1 pago en ≤2 intentos):
      <b>${(p.recuperacion_x_credito*100).toFixed(1)}%</b>.</div>`;
}

/* ---------------- DECISIÓN POR CLIENTE ---------------- */
function passF(d) {
  if (FILTER === "todos") return true;
  if (FILTER === "entrevistas") return String(d.cliente_id).startsWith("ENT");
  if (FILTER === "nocontactar") return d.accion === "NO CONTACTAR";
  return d.segmento.riesgo === FILTER;
}
function renderDecList() {
  const rows = CLIENTES.filter(passF).map(d => {
    const pr = Math.round(d.prioridad);
    const col = pr >= 55 ? "var(--mb-red)" : pr >= 35 ? "var(--warn)" : "var(--good)";
    const no = d.accion === "NO CONTACTAR";
    return `<div class="drow ${d.cliente_id===SELC?'on':''}" data-id="${d.cliente_id}">
      <span class="pr" style="background:${col}">${pr}</span>
      <span class="nm">${d.nombre}<small>${d.segmento.tramo_mora} · ${d.segmento.es_digital?'digital':'no digital'} · ${CH[d.decision.canal.canal]}</small></span>
      <span class="act ${no?'act-no':'act-si'}">${no?'no contactar':'contactar'}</span>
    </div>`;
  }).join("");
  $("#decRows").innerHTML = rows || "<div class='empty'>sin clientes</div>";
  $$("#decRows .drow").forEach(el => el.onclick = () => selectCli(el.dataset.id));
}
function selectCli(id) { SELC = id; renderDecList(); renderDecDetail(CLIENTES.find(d => d.cliente_id === id)); }

function renderDecDetail(d) {
  if (!d) return;
  const s = d.segmento, dec = d.decision;
  const no = d.accion === "NO CONTACTAR";
  const tags = [
    `<span class="tag ${s.riesgo==='alto'?'bad':s.riesgo==='bajo'?'good':'warn'}">riesgo ${s.riesgo}</span>`,
    `<span class="tag">${s.es_digital?'digital':'no digital'}</span>`,
    s.buen_pagador ? `<span class="tag good">buen pagador</span>` : "",
    `<span class="tag">${s.tramo_mora}</span>`,
  ].join("");
  const note = d.nota ? `<div class="dd-note">entrevista · ${d.nota}</div>` : "";

  const r = (k, v, why) => `<div class="dd-r"><div class="dk">${k}</div><div class="dv">${v}${why?`<span class="why">${why}</span>`:""}</div></div>`;
  let decide;
  if (no) {
    decide = `<div class="dd-decide">
      ${r("Acción", "⛔ NO CONTACTAR", "Ya prometió o pagó: no se insiste (anti-fatiga).")}
      ${r("Frecuencia", "Máx 0 contactos", dec.frecuencia.nota)}
    </div>`;
  } else {
    decide = `<div class="dd-decide">
      ${r("Acción", "✓ CONTACTAR")}
      ${r("Canal", CH[dec.canal.canal], dec.canal.motivo)}
      ${r("Momento", dec.momento.cuando, "Franja "+dec.momento.franja+" · evitar "+dec.momento.evitar)}
      ${r("Frecuencia", "Máx "+dec.frecuencia.tope_contactos+" contacto(s)", dec.frecuencia.nota)}
      ${r("Tono", cap(dec.tono), "Tutear, cercano y verificablemente Mibanco")}
    </div>
    <div class="dd-msg">
      <div class="dd-msg-h">${CH[dec.canal.canal]} ${dec.canal.verificable?'<span class="verif">✓ verificable</span>':''}</div>
      <div class="dd-bubble">${dec.mensaje}</div>
    </div>
    ${rankHtml(dec.canal.ranking)}`;
  }
  $("#decDetail").innerHTML = `
    <div class="dd-head">
      <div><div class="dd-name">${d.nombre}</div><div class="dd-tags">${tags}</div></div>
      <span class="pr" style="background:var(--navy);width:42px;height:42px;border-radius:10px;display:grid;place-items:center;color:#fff;font-family:var(--mono);font-weight:700;flex:none">${Math.round(d.prioridad)}</span>
    </div>${note}${decide}`;
}
function rankHtml(rank) {
  if (!rank || !rank.length) return "";
  const max = Math.max(...rank.map(r => r.valor_neto), 1);
  const bars = rank.map((r, i) => {
    const w = Math.max(3, r.valor_neto / max * 100);
    return `<div class="rk ${i===0?'win':''}"><span class="rkn">${CH[r.canal]}</span>
      <span class="track"><span class="fill" style="width:${w}%"></span></span>
      <span class="rkv">S/${Math.round(r.valor_neto)}</span></div>`;
  }).join("");
  return `<div class="rank"><div class="rank-h">¿Por qué ese canal? valor neto = recuperación − costo</div>${bars}</div>`;
}
function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; }

$$("#decFilters .chip").forEach(c => c.onclick = () => {
  $$("#decFilters .chip").forEach(x => x.classList.remove("on")); c.classList.add("on");
  FILTER = c.dataset.f; renderDecList();
});

/* ============================================================
   YATEKOBRO — motor de imputación
   Presets = corridas reales del motor Python (con variabilidad).
   What-if = misma lógica de imputación, ventas constantes (determinista).
   ============================================================ */
let ykPct = 2, ykMode = "live";

function renderPresets() {
  const casos = YK.casos || [];
  $("#ykPresets").innerHTML = casos.map((c, i) =>
    `<button class="preset" data-i="${i}">${c.cliente}
       <small>S/${c.credito.saldo} · ${c.pct}% · ventas S/${c.ventas_dia_media}/día</small></button>`
  ).join("");
  $$("#ykPresets .preset").forEach(b => b.onclick = () => loadPreset(+b.dataset.i));
}

function loadPreset(i) {
  const c = YK.casos[i]; if (!c) return;
  $$("#ykPresets .preset").forEach(x => x.classList.remove("on"));
  $$("#ykPresets .preset")[i].classList.add("on");
  $("#ykSaldo").value = c.credito.saldo;
  $("#ykTasa").value = Math.round(c.credito.tasa_ea * 100);
  $("#ykPlazo").value = c.credito.plazo_meses;
  setPct(c.pct);
  $("#ykVentas").value = c.ventas_dia_media; $("#ykVentasV").textContent = soles(c.ventas_dia_media);
  ykMode = "python";
  renderYK(c, "motor Python · variabilidad real");
}

function setPct(v) {
  ykPct = v;
  $$("#ykPct button").forEach(b => b.classList.toggle("on", +b.dataset.v === v));
  $("#ykPctV").textContent = v + "%";
}

/* ---- imputación (port de yatekobro.simular, ventas constantes) ---- */
function amort(saldo, tasaEA, plazo) {
  const i = Math.pow(1 + tasaEA, 1 / 12) - 1;
  const cuota = saldo * i / (1 - Math.pow(1 + i, -plazo));
  const interes = saldo * i, capital = cuota - interes;
  return { cuota, interes, capital, i };
}
function simulaLive(saldo, tasaEA, plazo, pct, ventas, maxDias = 60) {
  const am = amort(saldo, tasaEA, plazo);
  const aporte = ventas * pct / 100;
  const ledger = [], eventos = [];
  let intAc = 0, capAc = 0, h50 = false, h100 = false, hc = false, txs = 0;
  for (let dia = 1; dia <= maxDias; dia++) {
    txs += Math.max(1, Math.round(ventas / 35));
    const aInt = Math.min(aporte, Math.max(0, am.interes - intAc));
    const aCap = Math.min(aporte - aInt, Math.max(0, am.capital - capAc));
    intAc += aInt; capAc += aCap;
    ledger.push({ dia, venta: ventas, aporte, a_interes: aInt, a_capital: aCap,
      interes_ac: intAc, capital_ac: capAc,
      interes_pct: intAc / am.interes * 100, capital_pct: capAc / am.capital * 100 });
    if (!h50 && intAc >= am.interes * 0.5) { h50 = true; eventos.push(evt("interes_50", dia, am, intAc, txs)); }
    if (!h100 && intAc >= am.interes - 0.01) { h100 = true; eventos.push(evt("interes_100", dia, am, intAc, txs)); }
    if (!hc && capAc >= am.capital - 0.01) { hc = true; eventos.push(evt("cuota_completa", dia, am, intAc, txs)); break; }
  }
  return {
    cliente: "What-if", credito: { saldo, tasa_ea: tasaEA, plazo_meses: plazo },
    cuota: am.cuota, interes_obj: am.interes, capital_obj: am.capital, pct, ventas_dia_media: ventas,
    ledger, eventos,
    resumen: {
      completo: hc,
      dia_interes_vencido: (eventos.find(e => e.tipo === "interes_100") || {}).dia || null,
      dia_cuota_completa: (eventos.find(e => e.tipo === "cuota_completa") || {}).dia || null,
      dias_simulados: ledger.length, transacciones: txs, contactos_cobranza: 0,
    },
  };
}
function evt(tipo, dia, am, intAc, txs) {
  const cap = Math.round(am.capital);
  let titulo, mensaje;
  if (tipo === "interes_50") { titulo = "Interés 50%"; mensaje = `*Mibanco* ✅ 📊 YateKobro: ya cubriste el 50% del interés de este mes (S/${Math.round(intAc)} de S/${Math.round(am.interes)}). Seguimos 💪`; }
  else if (tipo === "interes_100") { titulo = "Interés 100% (estrella)"; mensaje = `*Mibanco* ✅ 🎉 ¡Ya cubriste el 100% del interés!\nLo que te queda (S/${cap}) es plata tuya que estás devolviendo, no costo del banco. Llevas ${dia} días, ${txs} transacciones.`; }
  else { titulo = "Cuota completa → auto-stop"; mensaje = `*Mibanco* ✅ ✅ ¡Cuota PAGADA! YateKobro se paró automático.\n¿Quieres adelantar la próxima cuota y seguir reduciendo interés? Responde SÍ o NO.`; }
  return { tipo, dia, titulo, mensaje, verificable: true };
}

function recomputeYK() {
  $$("#ykPresets .preset").forEach(x => x.classList.remove("on"));
  const saldo = +$("#ykSaldo").value, tasa = (+$("#ykTasa").value) / 100,
        plazo = +$("#ykPlazo").value, ventas = +$("#ykVentas").value;
  ykMode = "live";
  renderYK(simulaLive(saldo, tasa, plazo, ykPct, ventas), "what-if · ventas constantes");
}

function renderYK(sim, modeLabel) {
  const am = `cuota <b>${soles(sim.cuota)}</b> = interés <b>${soles(sim.interes_obj)}</b> + capital <b>${soles(sim.capital_obj)}</b>
    <span style="color:var(--muted)"> · crédito S/${sim.credito.saldo} a ${sim.credito.plazo_meses}m (${Math.round(sim.credito.tasa_ea*100)}% EA) · ${sim.pct}% por venta</span>`;
  $("#ykAmort").innerHTML = am;

  const last = sim.ledger[sim.ledger.length - 1] || { interes_pct: 0, capital_pct: 0, interes_ac: 0, capital_ac: 0 };
  $("#ykBars").innerHTML =
    bar("Interés del mes", last.interes_pct, last.interes_ac, sim.interes_obj, "int", last.interes_pct >= 99.9 ? "¡vencido! ✓" : "") +
    bar("Capital · lo que es tuyo", last.capital_pct, last.capital_ac, sim.capital_obj, "cap", "");

  const r = sim.resumen;
  $("#ykResumen").innerHTML = `
    <div class="yk-st"><div class="sv">${soles(sim.ventas_dia_media * sim.pct / 100)}</div><div class="sl">aporte por día</div></div>
    <div class="yk-st hl"><div class="sv">${r.dia_interes_vencido ? "día " + r.dia_interes_vencido : "—"}</div><div class="sl">interés vencido</div></div>
    <div class="yk-st"><div class="sv">${r.dia_cuota_completa ? "día " + r.dia_cuota_completa : "+" + r.dias_simulados}</div><div class="sl">${r.completo ? "cuota completa" : "no completa en " + r.dias_simulados + "d"}</div></div>
    <div class="yk-st hl"><div class="sv">0</div><div class="sl">contactos de cobranza</div></div>`;

  // ledger
  const evtDias = {}; sim.eventos.forEach(e => evtDias[e.dia] = e.tipo);
  const rows = sim.ledger.map(L => {
    const cls = evtDias[L.dia] === "cuota_completa" ? "evt-cuota" : evtDias[L.dia] ? "evt-int" : "";
    const iDone = L.interes_pct >= 99.9;
    return `<tr class="${cls}"><td>${L.dia}</td><td>${Math.round(L.venta)}</td><td>${L.aporte.toFixed(1)}</td>
      <td class="${iDone?'ok':''}">${Math.round(L.interes_ac)}/${Math.round(sim.interes_obj)}</td>
      <td>${Math.round(L.capital_ac)}/${Math.round(sim.capital_obj)}</td></tr>`;
  }).join("");
  $("#ykLedger").innerHTML = `<table><thead><tr><th>día</th><th>venta</th><th>aporte</th><th>interés</th><th>capital</th></tr></thead><tbody>${rows}</tbody></table>`;
  $("#ykLedMode").textContent = modeLabel;

  // eventos
  $("#ykEvents").innerHTML = sim.eventos.length ? sim.eventos.map(e =>
    `<div class="evt ${e.tipo==='interes_100'?'star':''}">
      <div class="evt-h"><span>${e.titulo}</span><span class="day">día ${e.dia}</span></div>
      <div class="evt-msg">${e.mensaje.replace(/\*Mibanco\* ✅/g,'<span class="mb">Mibanco ✅</span>')}</div>
    </div>`).join("") : `<div class="evt-empty">sin eventos (sube las ventas o el %)</div>`;

  $("#ykMode").innerHTML = ykMode === "python"
    ? "Mostrando una <b>corrida real del motor</b> <code>yatekobro.py</code> (ventas diarias con variabilidad). Mueve un control para pasar a what-if."
    : "<b>What-if en vivo</b>: misma lógica de imputación del motor, con ventas constantes (determinista). Elige un preset para ver una corrida real con variabilidad.";
}
function bar(label, pct, ac, obj, kind, win) {
  pct = Math.min(100, pct);
  return `<div class="ykbar"><div class="bh"><span>${label}</span><span>${pct.toFixed(0)}% ${win?'<i style="color:var(--good)">'+win+'</i>':''}</span></div>
    <div class="bt2"><div class="bf ${kind}" style="width:${pct}%"></div></div>
    <div class="bc">S/${Math.round(ac)} de S/${Math.round(obj)}</div></div>`;
}

$$("#ykPct button").forEach(b => b.onclick = () => { setPct(+b.dataset.v); recomputeYK(); });
["ykSaldo","ykTasa","ykPlazo"].forEach(id => $("#"+id).oninput = recomputeYK);
$("#ykVentas").oninput = e => { $("#ykVentasV").textContent = soles(+e.target.value); recomputeYK(); };

/* ---------------- FLUJO ---------------- */
function renderFlow() {
  const steps = [
    ["Transacciones Yape", "El ML estima el ingreso diario real del cliente (Credicorp es dueño de Yape y Mibanco)."],
    ["AsesorIA decide", "¿Contactar? ¿a quién no molestar? canal por perfil, tope 2, momento y tono. Sugiere YateKobro a los candidatos."],
    ["WhatsApp verificable", "Único canal: *Mibanco* ✅ oficial. Anti-extorsión. Oferta y configuración de YateKobro por chat."],
    ["Cliente activa y elige %", "Sin app, sin formulario. Responde un número por WhatsApp y queda registrado (consentimiento, Res. SBS 02522-2025)."],
    ["Motor de imputación", "Cada venta Yape: % → interés primero, luego capital (Art. 29.2, SBS 3274-2017). Ledger transparente."],
    ["Notificación en 3 momentos", "Interés 50%, interés 100% (el gancho emocional), cuota completa. Nada de spam."],
    ["Auto-stop", "Al completar la cuota, YateKobro se apaga solo. Cero llamadas. Nunca persigue."],
  ];
  $("#flow").innerHTML = steps.map((s, i) =>
    `<div class="fstep"><div class="fnum">${i+1}</div><div class="fbody"><b>${s[0]}</b><small>${s[1].replace(/\*Mibanco\* ✅/g,'<b>Mibanco ✅</b>')}</small></div></div>
     ${i<steps.length-1?'<div class="fconn"></div>':''}`).join("");
}

boot();

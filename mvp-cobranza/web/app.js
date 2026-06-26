/* ============================================================
   Motor de Cobranza Inteligente — Mibanco-confIA + YoSiLa
   ============================================================ */
"use strict";
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const soles = n => "S/ " + Math.round(n).toLocaleString("es-PE");
const milesK = n => "S/" + (Math.abs(n) >= 1000 ? (n / 1000).toFixed(0) + "k" : Math.round(n));
const CH = { whatsapp: "WhatsApp", sms: "SMS", llamada: "Llamada", campo: "Campo" };

let CLIENTES = [], BACKTEST = {}, YK = {}, CFG = {}, FILTER = "demo", SELC = null;

async function boot() {
  const get = f => fetch("data/" + f).then(r => r.json()).catch(() => null);
  [CLIENTES, BACKTEST, YK, CFG] = await Promise.all([
    get("clientes.json"), get("backtest.json"), get("yatekobro.json"), get("config.json"),
  ]);
  setupTabs();
  renderBacktest();
  renderDecList(); const _first = CLIENTES.filter(passF)[0] || CLIENTES[0]; if (_first) selectCli(_first.cliente_id);
  renderPresets(); recomputeYK();
  renderFlow();
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
      <div class="h">métrica</div><div class="h now">Gestión actual</div><div class="h ia">Con Mibanco-confIA</div>
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
  if (FILTER === "demo") return !!d.es_demo;
  if (FILTER === "entrevistas") return String(d.cliente_id).startsWith("ENT");
  if (FILTER === "nocontactar") return d.accion === "NO CONTACTAR";
  return d.segmento.riesgo === FILTER;
}
function renderDecList() {
  const rows = CLIENTES.filter(passF).map(d => {
    const pr = Math.round(d.prioridad);
    const col = pr >= 55 ? "var(--mb-red)" : pr >= 35 ? "var(--warn)" : "var(--good)";
    const no = d.accion === "NO CONTACTAR";
    return `<div class="drow ${String(d.cliente_id)===String(SELC)?'on':''}" data-id="${d.cliente_id}">
      <span class="pr" style="background:${col}">${pr}</span>
      <span class="nm">${d.es_nuevo?'<span class="nuevo-tag">NUEVO</span> ':''}${d.nombre}<small>${d.segmento.tramo_mora} · ${d.segmento.es_digital?'digital':'no digital'} · ${CH[d.decision.canal.canal]}</small></span>
      <span class="act ${no?'act-no':'act-si'}">${no?'no contactar':'contactar'}</span>
    </div>`;
  }).join("");
  $("#decRows").innerHTML = rows || "<div class='empty'>sin clientes</div>";
  $$("#decRows .drow").forEach(el => el.onclick = () => selectCli(el.dataset.id));
}
function selectCli(id) { SELC = id; renderDecList(); renderDecDetail(CLIENTES.find(d => String(d.cliente_id) === String(id))); }

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

  // bloque central: simulador día-a-día (todos los clientes)
  const central = d.simulacion ? simHtml(d) : calendarHtml(d.calendario);

  // detalle de la decisión (dentro del colapsable "Por qué")
  const r = (k, v, why) => `<div class="dd-r"><div class="dk">${k}</div><div class="dv">${v}${why?`<span class="why">${why}</span>`:""}</div></div>`;
  const decideRows = no
    ? `<div class="dd-decide">${r("Acción", "⛔ NO CONTACTAR", "Ya prometió o pagó: no se insiste.")}</div>`
    : `<div class="dd-decide">
        ${r("Canal", "💬 WhatsApp verificable", dec.canal.canal !== 'whatsapp' ? "Escala a llamada/visita solo si no responde (último recurso, no se elimina ningún canal)." : "Oficial, anti-extorsión. Mayor conversión y 15× más barato que llamar.")}
        ${r("Momento", dec.momento.cuando, "Franja " + dec.momento.franja + " · Lun-Vie 7-19h, sábado solo digital")}
        ${r("Tono", cap(dec.tono), "Cercano y verificablemente Mibanco")}
      </div>`;

  $("#decDetail").innerHTML = `
    <div class="dd-head">
      <div><div class="dd-name">${d.nombre}</div><div class="dd-tags">${tags}</div></div>
      <span class="pr" style="background:var(--navy);width:42px;height:42px;border-radius:10px;display:grid;place-items:center;color:#fff;font-family:var(--mono);font-weight:700;flex:none">${Math.round(d.prioridad)}</span>
    </div>${note}
    ${qsHtml(d)}
    ${yapeHtml(d.yape)}
    ${central}
    <details class="collap"><summary>Por qué esta decisión</summary><div class="collap-body">${porqueHtml(d.porque, d.segmento, d.ficha)}${decideRows}</div></details>
    <details class="collap"><summary>Datos del cliente (del Excel)</summary><div class="collap-body">${fichaHtml(d.ficha)}</div></details>
    ${d.simulacion ? `<details class="collap"><summary>Calendario del mes (resumen)</summary><div class="collap-body">${calendarHtml(d.calendario)}</div></details>` : ''}
  `;
  if (d.simulacion) mountSim(d);
}

/* ---------------- QUICK SCOPE (ejecutivo) ---------------- */
function qsHtml(d) {
  const cal = d.calendario, no = d.accion === "NO CONTACTAR";
  const prox = (cal.contactos && cal.contactos.length) ? cal.contactos[0].fecha : "—";
  const escala = !no && cal.contactos && cal.contactos.some(c => c.canal !== 'whatsapp');
  const canalTxt = no ? "—" : (escala ? "💬 WhatsApp → escala" : "💬 WhatsApp");
  const canalTip = escala ? "Empieza por WhatsApp; si no responde, escala a llamada y, en último recurso, visita." : "Solo WhatsApp oficial verificable.";
  return `<div class="dd-qs">
    <div class="qs-st"><div class="qs-v ${no?'muted':''}">${no ? 'No contactar' : cal.total_contactos + '/' + cal.tope}</div><div class="qs-l">contactos / mes</div></div>
    <div class="qs-st"><div class="qs-v">${cal.etapa || '—'}</div><div class="qs-l">etapa de mora</div></div>
    <div class="qs-st" title="${canalTip}"><div class="qs-v">${canalTxt}</div><div class="qs-l">canal</div></div>
    <div class="qs-st"><div class="qs-v">${no ? '—' : prox}</div><div class="qs-l">próximo contacto</div></div>
  </div>`;
}

/* ---------------- CONEXIÓN YAPE (mini-gráfico) ---------------- */
function yapeHtml(y) {
  if (!y) return "";
  const max = Math.max(...y.dias.map(d => d.monto), 1);
  const fmt = m => m >= 1000 ? "S/" + (m / 1000).toFixed(1) + "k" : "S/" + m;
  const bars = y.dias.map(d => {
    const h = Math.max(6, Math.round(d.monto / max * 100));
    const hot = d.monto >= y.umbral;
    return `<div class="yp-col">
      <span class="yp-val ${hot?'hot':''}">${fmt(d.monto)}${hot?' ⭐':''}</span>
      <div class="yp-track"><div class="yp-bar ${hot?'hot':''}" style="height:${h}%"></div></div>
      <span class="yp-lbl">${d.label}</span>
    </div>`;
  }).join("");
  const nudge = y.buen_dia
    ? `<div class="yp-nudge"><b>💡 Oportunidad de prepago.</b> ${y.sugerencia}</div>`
    : `<div class="yp-nudge calm">${y.sugerencia}</div>`;
  const prepay = (y.buen_dia && y.mensaje_prepago) ? `
    <div class="yp-msg">
      <div class="yp-msg-h">Lo que confIA le enviaría el <b>${y.dia_envio}</b> <span class="wa-verif" title="Cuenta verificada">✓</span> WhatsApp verificable</div>
      <div class="yp-msg-phone"><div class="sim-msg bank"><div class="sim-bubble">${fmtWA(y.mensaje_prepago)}</div></div></div>
    </div>` : "";
  return `<div class="dd-yape">
    <div class="dd-cal-h">Conexión Yape · ventas últimos 7 días <span class="cal-badge gris">promedio S/${y.promedio}</span></div>
    <div class="yp-chart">${bars}</div>
    ${nudge}
    ${prepay}
  </div>`;
}

/* ---------------- SIMULADOR día-a-día + mini-chat WhatsApp ---------------- */
function simHtml(d) {
  const et = d.simulacion.etapas;
  const TK = { preventivo: "Al día", temprana: "Temprana", media: "Media", tardia: "Tardía", yosila: "YoSiLa" };
  let idx = et.findIndex(e => e.key === d.simulacion.default); if (idx < 0) idx = 1;
  const ticks = et.map((e, i) => `<span class="${i===idx?'on':''}">${TK[e.key] || e.key}</span>`).join("");
  return `<div class="dd-sim">
    <div class="dd-cal-h">Simulador · ¿qué le mandamos según pasa el tiempo? <span class="cal-badge">mueve el slider</span></div>
    <div class="sim-slider">
      <input type="range" id="simRange" min="0" max="${et.length-1}" step="1" value="${idx}" />
      <div class="sim-ticks">${ticks}</div>
    </div>
    <div class="sim-meta" id="simMeta"></div>
    <div class="sim-phone"><div class="sim-head"><span class="sim-wa-avatar">m</span> Mibanco Cobranzas <span class="wa-verif" title="Cuenta de empresa verificada">✓</span></div><div class="sim-chat" id="simChat"></div></div>
    <button class="sim-play" id="simPlay">▶ reproducir conversación</button>
    <div class="sim-yosila">💚 <b>YoSiLa siempre disponible</b> — el cliente puede activarlo en cualquier etapa para cobrarse solo con un % de sus ventas Yape, sin llamadas.</div>
  </div>`;
}
let _simTimers = [];
function _clearSim() { _simTimers.forEach(clearTimeout); _simTimers.length = 0; }
function _simWait(ms) { return new Promise(r => _simTimers.push(setTimeout(r, ms))); }
function fmtWA(s) { return s.replace(/\*(.*?)\*/g, "<b>$1</b>").replace(/\n/g, "<br>"); }
function renderSimMeta(et) {
  const canal = et.canal === 'campo' ? '💬 WhatsApp → 📞 llamada → 🚶 visita (último recurso)'
    : et.canal === 'llamada' ? '💬 WhatsApp → 📞 llamada del asesor (si no responde)'
    : '💬 WhatsApp verificable';
  $("#simMeta").innerHTML = `<span class="sim-etapa">${et.label}</span> · <b>${et.n_contactos}</b> contacto(s) este mes · ${canal}`;
}
async function playSim(et) {
  _clearSim();
  const chat = $("#simChat"); if (!chat) return;
  chat.innerHTML = `<div class="sim-day">hoy</div>`;
  for (const m of et.conversacion) {
    await _simWait(420);
    if (!$("#simChat")) return; // panel cambió
    if (m.de === "sistema") {
      const cls = m.tipo === "campo" ? "campo" : m.tipo === "llamada" ? "llamada" : "prog";
      const el = document.createElement("div"); el.className = "sim-sys " + cls;
      el.innerHTML = fmtWA(m.texto); chat.appendChild(el);
    } else if (m.de === "banco") {
      const typ = document.createElement("div"); typ.className = "sim-msg bank typing";
      typ.innerHTML = `<div class="sim-bubble"><span class="dots"><span></span><span></span><span></span></span></div>`;
      chat.appendChild(typ); chat.scrollTop = chat.scrollHeight;
      await _simWait(Math.min(800 + m.texto.length * 9, 1600));
      if (!$("#simChat")) return; typ.remove();
      const el = document.createElement("div"); el.className = "sim-msg bank";
      el.innerHTML = `<div class="sim-bubble">${fmtWA(m.texto)}</div>`; chat.appendChild(el);
    } else {
      const el = document.createElement("div"); el.className = "sim-msg client";
      el.innerHTML = `<div class="sim-bubble">${fmtWA(m.texto)}</div>`; chat.appendChild(el);
    }
    chat.scrollTop = chat.scrollHeight;
  }
}
function mountSim(d) {
  const et = d.simulacion.etapas;
  const range = $("#simRange"); if (!range) return;
  const apply = () => { const e = et[+range.value]; renderSimMeta(e);
    $$("#decDetail .sim-ticks span").forEach((s, i) => s.classList.toggle("on", i === +range.value));
    playSim(e); };
  range.oninput = apply;
  $("#simPlay").onclick = () => playSim(et[+range.value]);
  apply();
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
function calendarHtml(cal) {
  if (!cal) return "";
  const ch = c => c.canal === 'llamada' ? '📞 Llamada' : c.canal === 'campo' ? '🚶 Visita' : '💬 WhatsApp';
  const items = (cal.contactos || []).map(c => `
    <div class="cal-item">
      <span class="cal-date">${c.fecha}${c.rel_label ? `<small class="cal-rel ${c.dias_rel < 0 ? 'pre' : 'mora'}" title="${c.rel_nota || ''}">${c.rel_label}</small>` : ''}</span>
      <div class="cal-body">
        <div class="cal-top">
          <span class="cal-etapa">${c.etapa}</span>
          ${c.objetivo ? `<span class="cal-obj">🎯 ${c.objetivo}</span>` : ''}
          <span class="cal-ch ${c.canal!=='whatsapp'?'esc':''}">${ch(c)}${c.verificable && c.canal==='whatsapp' ? ' <span class="verif">✓ verificable</span>' : ''}</span>
        </div>
        <div class="cal-msg">${c.mensaje}</div>
      </div>
    </div>`).join("");
  const body = cal.total_contactos
    ? items
    : `<div class="cal-empty">Sin contactos programados este mes.<br>${cal.nota || ''}</div>`;
  return `<div class="dd-cal">
    <div class="dd-cal-h">Calendario de contactos · ${cal.mes}
      <span class="cal-badge">${cal.total_contactos}/${cal.tope} este mes</span></div>
    ${body}
    ${cal.total_contactos ? `<div class="cal-note">${cal.nota}</div>` : ''}
  </div>`;
}
function porqueHtml(p, seg, f) {
  if (!p) return "";
  const probPct = Math.round((f?.prob_repago_7d || 0) * 100);
  return `<div class="dd-porque">
    <div class="dd-cal-h">Por qué esta decisión <span class="cal-badge">riesgo ${seg.riesgo} · ${p.categoria_mora}</span></div>
    <div class="pq-prob">
      <div class="pq-prob-h">Probabilidad de repago · 7 días, sin contactarlo</div>
      <div class="pq-bar"><div class="pq-bar-fill" style="width:${probPct}%"></div><span class="pq-bar-lbl">${probPct}%</span></div>
      <div class="pq-prob-note">${p.prob_repago}</div>
    </div>
    <div class="pq-list">
      <div class="pq-item"><b>Riesgo</b>${p.riesgo}</div>
      <div class="pq-item"><b>Cuántos contactos</b>${p.tope}</div>
      <div class="pq-item"><b>Decisión</b>${p.contactar}</div>
    </div>
  </div>`;
}
function fichaHtml(f) {
  if (!f) return "";
  const num = n => (n || 0).toLocaleString("es-PE");
  const cell = (k, v) => `<div class="fi"><span class="fi-k">${k}</span><span class="fi-v${(v === null || v === undefined || v === "" || v === "—") ? " muted" : ""}">${(v === null || v === undefined || v === "") ? "—" : v}</span></div>`;
  const si = b => b ? "Sí" : "No";
  return `<div class="dd-ficha">
    <div class="dd-cal-h">Datos del cliente <span class="cal-badge gris">del Excel del banco</span></div>
    <div class="fi-grid">
      ${cell("Edad", f.edad ? f.edad + " años" : null)}
      ${cell("Región", f.region)}
      ${cell("Zona", f.zona)}
      ${cell("Producto", f.producto)}
      ${cell("Saldo", "S/ " + num(f.saldo_restante))}
      ${cell("Cuota", "S/ " + num(f.cuota_mensual))}
      ${cell("Días de mora", f.dias_mora)}
      ${cell("Prob. impago", Math.round(f.prob_default * 100) + "%")}
      ${cell("Paga a tiempo", Math.round(f.ratio_pago * 100) + "%")}
      ${cell("Atrasos previos", f.num_atrasos_previos)}
      ${cell("Mora promedio", f.dias_mora_promedio ? f.dias_mora_promedio + " d" : null)}
      ${cell("Último pago", f.ultimo_pago_dias ? "hace " + f.ultimo_pago_dias + " d" : null)}
      ${cell("Digital", si(f.es_digital))}
      ${cell("Usa app", f.uso_app != null ? Math.round(f.uso_app * 100) + "%" : null)}
      ${cell("Usa WhatsApp", si(f.uso_whatsapp))}
      ${cell("Interacción digital", f.interaccion_digital ? f.interaccion_digital + "/100" : null)}
      ${cell("Score banco (apoyo)", f.score_riesgo)}
      ${cell("Prob. repago 30d", f.prob_repago_30d != null ? Math.round(f.prob_repago_30d * 100) + "%" : null)}
    </div>
  </div>`;
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
  // descomponer ventas_dia_media en txns × avg para los sliders
  const vd = c.ventas_dia_media || 1000;
  const avgV = Math.min(500, Math.max(10, Math.round(vd / 30 / 5) * 5));
  const txnV = Math.min(200, Math.max(5, Math.round(vd / avgV / 5) * 5));
  if ($("#ykTxns")) { $("#ykTxns").value = txnV; if ($("#ykTxnsV")) $("#ykTxnsV").textContent = txnV + " ventas"; }
  if ($("#ykAvg")) { $("#ykAvg").value = avgV; if ($("#ykAvgV")) $("#ykAvgV").textContent = soles(avgV); }
  if ($("#ykVentasV")) $("#ykVentasV").textContent = soles(txnV * avgV);
  ykMode = "python";
  renderYK(c, "ventas con variabilidad");
  renderPctCompare(c.credito.saldo, c.credito.tasa_ea, c.credito.plazo_meses, vd);
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
  if (tipo === "interes_50") { titulo = "Interés 50%"; mensaje = `*Mibanco* ✅ 📊 YoSiLa: ya cubriste el 50% del interés de este mes (S/${Math.round(intAc)} de S/${Math.round(am.interes)}). Seguimos 💪`; }
  else if (tipo === "interes_100") { titulo = "Interés 100% (estrella)"; mensaje = `*Mibanco* ✅ 🎉 ¡Ya cubriste el 100% del interés!\nLo que te queda (S/${cap}) es plata tuya que estás devolviendo, no costo del banco. Llevas ${dia} días, ${txs} transacciones.`; }
  else { titulo = "Cuota completa → auto-stop"; mensaje = `*Mibanco* ✅ ✅ ¡Cuota PAGADA! YoSiLa se paró automático.\n¿Quieres adelantar la próxima cuota y seguir reduciendo interés? Responde SÍ o NO.`; }
  return { tipo, dia, titulo, mensaje, verificable: true };
}

function recomputeYK() {
  $$("#ykPresets .preset").forEach(x => x.classList.remove("on"));
  const saldo = +$("#ykSaldo").value, tasa = (+$("#ykTasa").value) / 100, plazo = +$("#ykPlazo").value;
  const txns = +$("#ykTxns").value || 30, avg = +$("#ykAvg").value || 35;
  const ventas = txns * avg;
  if ($("#ykTxnsV")) $("#ykTxnsV").textContent = txns + " ventas";
  if ($("#ykAvgV")) $("#ykAvgV").textContent = soles(avg);
  if ($("#ykVentasV")) $("#ykVentasV").textContent = soles(ventas);
  ykMode = "live";
  renderYK(simulaLive(saldo, tasa, plazo, ykPct, ventas), "simulación · ventas constantes");
  renderPctCompare(saldo, tasa, plazo, ventas);
}

function renderPctCompare(saldo, tasa, plazo, ventas) {
  const el = $("#ykPctCompare"); if (!el) return;
  const PCTS = [1, 2, 3, 5];
  const cards = PCTS.map(p => {
    const sim = simulaLive(saldo, tasa, plazo, p, ventas);
    const r = sim.resumen;
    const aporte = ventas * p / 100;
    return `<div class="pct-card ${p === ykPct ? 'on' : ''}" onclick="setPct(${p});recomputeYK()">
      <div class="pct-card-h">${p}%</div>
      <div class="pct-card-aporte">${soles(aporte)}<small>/día</small></div>
      <div class="pct-card-rows">
        <div><span>Interés vencido</span><b>${r.dia_interes_vencido ? 'día ' + r.dia_interes_vencido : '—'}</b></div>
        <div><span>Cuota completa</span><b>${r.completo ? 'día ' + r.dia_cuota_completa : '+' + r.dias_simulados + 'd'}</b></div>
        <div><span>Ventas realizadas</span><b>${r.transacciones}</b></div>
      </div>
    </div>`;
  }).join("");
  el.innerHTML = `<div class="pct-compare-h">¿Cómo cambia la cuota según el %? <small>toca una tarjeta para simular</small></div>
    <div class="pct-compare-scroll">${cards}</div>`;
}

function renderYK(sim, modeLabel) {
  const iMen = Math.pow(1 + sim.credito.tasa_ea, 1 / 12) - 1;
  const am = `cuota <b>${soles(sim.cuota)}</b> = interés <b>${soles(sim.interes_obj)}</b> + capital <b>${soles(sim.capital_obj)}</b>
    <span style="color:var(--muted)"> · crédito S/${sim.credito.saldo} a ${sim.credito.plazo_meses}m (${Math.round(sim.credito.tasa_ea*100)}% EA) · ${sim.pct}% por venta</span>
    <div class="amort-formula">Cuota francesa &nbsp;·&nbsp; i = (1+EA)<sup>1/12</sup> − 1 = <b>${(iMen*100).toFixed(2)}%</b>/mes &nbsp;·&nbsp; cuota = saldo·i ⁄ (1−(1+i)<sup>−n</sup>) &nbsp;·&nbsp; interés del mes = saldo·i &nbsp;·&nbsp; capital = cuota − interés</div>`;
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
    ? "Caso de ejemplo con <b>ventas diarias con variabilidad</b> (como un negocio real). Mueve un control para simular tu propio caso."
    : "<b>Simulación en vivo</b>: misma lógica de imputación, con ventas constantes. Elige un caso de ejemplo para ver ventas con variabilidad.";
}
function bar(label, pct, ac, obj, kind, win) {
  pct = Math.min(100, pct);
  return `<div class="ykbar"><div class="bh"><span>${label}</span><span>${pct.toFixed(0)}% ${win?'<i style="color:var(--good)">'+win+'</i>':''}</span></div>
    <div class="bt2"><div class="bf ${kind}" style="width:${pct}%"></div></div>
    <div class="bc">S/${Math.round(ac)} de S/${Math.round(obj)}</div></div>`;
}

$$("#ykPct button").forEach(b => b.onclick = () => { setPct(+b.dataset.v); recomputeYK(); });
["ykSaldo","ykTasa","ykPlazo","ykTxns","ykAvg"].forEach(id => { const el = $("#"+id); if (el) el.oninput = recomputeYK; });

/* ---------------- FLUJO ---------------- */
function renderFlow() {
  const steps = [
    ["Transacciones Yape", "El ML estima el ingreso diario real del cliente (Credicorp es dueño de Yape y Mibanco)."],
    ["Mibanco-confIA decide", "¿Contactar? ¿a quién no molestar? canal por perfil, tope de contactos, momento y tono. Sugiere YoSiLa a los candidatos."],
    ["WhatsApp verificable", "Único canal: *Mibanco* ✅ oficial. Anti-extorsión. Oferta y configuración de YoSiLa por chat."],
    ["Cliente activa y elige %", "Sin app, sin formulario. Responde un número por WhatsApp y queda registrado (consentimiento, Res. SBS 02522-2025)."],
    ["Motor de imputación", "Cada venta Yape: % → interés primero, luego capital (Art. 29.2, SBS 3274-2017). Ledger transparente."],
    ["Notificación en 3 momentos", "Interés 50%, interés 100% (el gancho emocional), cuota completa. Nada de spam."],
    ["Auto-stop", "Al completar la cuota, YoSiLa se apaga solo. Cero llamadas. Nunca persigue."],
  ];
  $("#flow").innerHTML = steps.map((s, i) =>
    `<div class="fstep"><div class="fnum">${i+1}</div><div class="fbody"><b>${s[0]}</b><small>${s[1].replace(/\*Mibanco\* ✅/g,'<b>Mibanco ✅</b>')}</small></div></div>
     ${i<steps.length-1?'<div class="fconn"></div>':''}`).join("");
}

/* custom number spinner buttons */
document.addEventListener("click", e => {
  const b = e.target.closest(".nsb"); if (!b) return;
  const inp = document.getElementById(b.dataset.id); if (!inp) return;
  const step = +(inp.step) || 1, dir = +(b.dataset.dir);
  const newVal = Math.min(+(inp.max) || Infinity, Math.max(+(inp.min) || -Infinity, (+inp.value) + step * dir));
  inp.value = newVal;
  inp.dispatchEvent(new Event("input", { bubbles: true }));
});

boot();

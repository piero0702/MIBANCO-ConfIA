/* Cobranza Inteligente — Mibanco PoC (frontend) */
const CH_ICON = { whatsapp: "💬", sms: "✉️", llamada: "📞", campo: "🚶" };
const RISK_LABEL = { bajo: "Riesgo bajo", medio: "Riesgo medio", alto: "Riesgo alto" };

let CLIENTES = [], KPIS = {}, CFG = {}, SELECTED = null, FILTER = "todos";

async function boot() {
  const [c, k, cfg] = await Promise.all([
    fetch("data/clientes.json").then(r => r.json()),
    fetch("data/kpis.json").then(r => r.json()),
    fetch("data/config.json").then(r => r.json()),
  ]);
  CLIENTES = c; KPIS = k; CFG = cfg;
  renderFuente(); renderKpis(); renderList();
  if (CLIENTES.length) select(CLIENTES[0].cliente_id);
  document.getElementById("footN").textContent = CLIENTES.length;
  document.querySelectorAll("#filters .chip").forEach(b =>
    b.onclick = () => { FILTER = b.dataset.f; setActiveChip(b); renderList(); });
}

function setActiveChip(b){ document.querySelectorAll("#filters .chip").forEach(x=>x.classList.remove("active")); b.classList.add("active"); }

function renderFuente() {
  const el = document.getElementById("fuente");
  const real = KPIS.fuente_datos === "real";
  el.textContent = real ? "● Datos REALES del reto" : "● Datos sintéticos (demo)";
  el.classList.add(real ? "real" : "sintetico");
}

const soles = n => "S/ " + Math.round(n).toLocaleString("es-PE");

function renderKpis() {
  const ex = KPIS.extrapolacion_cartera || {};
  const cards = [
    { v: KPIS.ahorro_pct + "%", l: "Menos costo de cobranza", sub: "vs gestión actual", good:true },
    { v: "−" + KPIS.reduccion_contactos_pct + "%", l: "Menos contactos", sub: KPIS.contactos_actual + " → " + KPIS.contactos_ia, good:true },
    { v: KPIS.digital_first_pct + "%", l: "Digital-first", sub: "WhatsApp/SMS primero" },
    { v: soles(KPIS.recuperacion_esperada_soles), l: "Recuperación esperada", sub: KPIS.n_clientes + " clientes (muestra)" },
    { v: soles(ex.ahorro_anual_estimado_soles||0), l: "Ahorro extrapolado", sub: "a " + (ex.clientes_totales||0).toLocaleString("es-PE") + " clientes", good:true },
  ];
  document.getElementById("kpis").innerHTML = cards.map(c =>
    `<div class="kpi"><div class="v ${c.good?'good':''}">${c.v}</div><div class="l">${c.l}</div><div class="sub">${c.sub}</div></div>`
  ).join("");
}

function passFilter(d){
  if (FILTER === "todos") return true;
  if (FILTER === "entrevistas") return String(d.cliente_id).startsWith("ENT");
  return d.segmento.riesgo === FILTER;
}

function renderList() {
  const list = CLIENTES.filter(passFilter);
  document.getElementById("clientList").innerHTML = list.map(d => {
    const pr = d.prioridad, col = pr>=55?"var(--mb-red)":pr>=35?"var(--amber)":"var(--green)";
    return `<div class="client ${d.cliente_id===SELECTED?'active':''}" data-id="${d.cliente_id}">
      <div class="pri" style="background:${col}">${Math.round(pr)}</div>
      <div class="who"><div class="nm">${d.nombre}</div>
        <div class="meta">${d.segmento.tramo_mora} · ${d.segmento.es_digital?'digital':'no digital'}</div></div>
      <span class="badge b-${d.segmento.riesgo}">${d.segmento.riesgo}</span>
      <span class="ch-ico">${CH_ICON[d.decision.canal.canal]}</span>
    </div>`;
  }).join("");
  document.querySelectorAll(".client").forEach(el => el.onclick = () => select(el.dataset.id));
}

function select(id){ SELECTED = id; renderList(); renderDetail(CLIENTES.find(d=>d.cliente_id===id)); }

function renderDetail(d){
  if(!d) return;
  const s=d.segmento, dec=d.decision, im=d.impacto;
  const tags = [
    `<span class="badge b-${s.riesgo}">${RISK_LABEL[s.riesgo]}</span>`,
    `<span class="badge ${s.es_digital?'b-bajo':'b-medio'}">${s.es_digital?'Digital':'No digital'}</span>`,
    s.buen_pagador?`<span class="badge b-bajo">Buen pagador</span>`:"",
    `<span class="badge b-medio">${s.tramo_mora}</span>`,
  ].join("");

  const note = d.nota ? `<div class="note">🗣️ <b>Insight entrevista:</b> ${d.nota}</div>` : "";

  // ANTES (gestión actual)
  const before = `<div class="col before"><h3><b>● HOY</b> — gestión actual</h3>
    <div class="line"><span class="ic">📢</span><div><div class="k">Contactos</div>
      <div class="val strike">~${CFG.baseline.contactos_por_credito} al mes, a ciegas</div></div></div>
    <div class="line"><span class="ic">🎲</span><div><div class="k">Canal</div>
      <div class="val strike">Cualquiera, descoordinado (cada asesor por su lado)</div></div></div>
    <div class="line"><span class="ic">🙈</span><div><div class="k">Resultado típico</div>
      <div class="val strike">${Math.round(CFG.baseline.pct_ignorados*100)}% ignora · se siente perseguido</div></div></div>
    <div class="line"><span class="ic">💸</span><div><div class="k">Costo estimado</div>
      <div class="val strike">${soles(im.costo_actual_estimado)} / crédito</div></div></div>
  </div>`;

  // DESPUÉS (IA)
  const after = `<div class="col after"><h3><b>● CON IA</b> — decisión del motor</h3>
    ${drow(CH_ICON[dec.canal.canal], "Canal", dec.canal.canal_nombre, dec.canal.motivo)}
    ${drow("🗓️", "Momento", dec.momento.cuando, "Franja "+dec.momento.franja+" · evitar "+dec.momento.evitar)}
    ${drow("🎚️", "Frecuencia", "Máx "+dec.frecuencia.tope_contactos+" contacto(s)", dec.frecuencia.nota)}
    ${drow("💬", "Tono", capit(dec.tono), "Tutear, cercano y verificablemente Mibanco")}
    ${messagePreview(dec)}
  </div>`;

  const impact = `<div class="impact">
    <div class="istat"><div class="iv good">${im.ahorro_pct}%</div><div class="il">menos costo en este crédito (${soles(im.ahorro_soles)})</div></div>
    <div class="istat"><div class="iv">${soles(im.recuperacion_esperada)}</div><div class="il">recuperación esperada (pago × cuota)</div></div>
  </div>`;

  document.getElementById("detail").innerHTML = `
    <div class="detail-head"><div><div class="name">${d.nombre}</div><div class="tags">${tags}</div></div>
      <div class="pri" style="background:var(--navy);width:48px;height:48px;border-radius:12px;font-size:16px">${Math.round(d.prioridad)}</div></div>
    ${note}
    <div class="cols">${before}${after}</div>
    ${impact}
    ${rankingHtml(dec.canal.ranking)}
    ${whatifHtml(d)}`;

  wireWhatif(d);
}

function drow(ic,k,v,sub){
  return `<div class="drow"><div class="di">${ic}</div><div><div class="dk">${k}</div>
    <div class="dv">${v}</div><div class="dsub">${sub||""}</div></div></div>`;
}
function capit(s){return s? s.charAt(0).toUpperCase()+s.slice(1):s;}

function messagePreview(dec){
  const verif = dec.canal.verificable ? `<span class="wa-verif">✓ verificado</span>` : "";
  const isCall = dec.canal.canal==="llamada"||dec.canal.canal==="campo";
  return `<div class="phone">
    <div class="wa-head">${CH_ICON[dec.canal.canal]} ${dec.canal.canal_nombre} ${verif}</div>
    <div class="bubble ${isCall?'call':''}">${dec.mensaje}<div class="t">${dec.momento.franja.split('-')[0]} ✓✓</div></div>
  </div>`;
}

function rankingHtml(rank){
  if(!rank||!rank.length) return "";
  const max = Math.max(...rank.map(r=>r.valor_neto), 1);
  const bars = rank.map((r,i)=>{
    const w = Math.max(2, (r.valor_neto/max)*100);
    return `<div class="bar ${i===0?'win':''}"><span class="bn">${CH_ICON[r.canal]} ${r.canal}</span>
      <span class="track"><span class="fill" style="width:${w}%"></span></span>
      <span class="bv">S/${Math.round(r.valor_neto)}</span></div>`;
  }).join("");
  return `<div class="rank"><h4>¿Por qué ese canal? · valor neto esperado (recuperación − costo)</h4>${bars}</div>`;
}

/* ---------- WHAT-IF: port compacto del motor (rules.py) a JS ---------- */
function whatifHtml(d){
  const s=d.segmento;
  return `<div class="whatif"><h4>🔬 Simulador en vivo — cambia el escenario y la IA re-decide</h4>
    <div class="wi-row"><label>Días de mora</label>
      <input type="range" id="wiMora" min="0" max="120" value="${s.dias_mora}">
      <span class="wval" id="wiMoraV">${s.dias_mora} d</span></div>
    <div class="wi-row"><label>Cuota (S/)</label>
      <input type="range" id="wiCuota" min="120" max="1500" step="20" value="${Math.round(d._cuota||cuotaOf(d))}">
      <span class="wval" id="wiCuotaV">S/ ${Math.round(d._cuota||cuotaOf(d))}</span></div>
    <div class="wi-row"><label>Perfil digital</label>
      <span class="toggle" id="wiDig"><button data-v="1" class="${s.es_digital?'on':''}">Digital</button>
      <button data-v="0" class="${!s.es_digital?'on':''}">No digital</button></span></div>
    <div class="wi-row"><label>Riesgo</label>
      <span class="toggle" id="wiRiesgo">${["bajo","medio","alto"].map(r=>`<button data-v="${r}" class="${s.riesgo===r?'on':''}">${r}</button>`).join("")}</span></div>
    <div id="wiOut"></div></div>`;
}

function cuotaOf(d){ return d.impacto.recuperacion_esperada / d.decision.canal.pago_estimado; }

function wireWhatif(d){
  const st = { mora:d.segmento.dias_mora, cuota:Math.round(cuotaOf(d)),
               digital:d.segmento.es_digital?1:0, riesgo:d.segmento.riesgo,
               saldo:d.impacto?cuotaOf(d)*4:0 };
  const mora=document.getElementById("wiMora"), cuota=document.getElementById("wiCuota");
  mora.oninput=()=>{st.mora=+mora.value;document.getElementById("wiMoraV").textContent=st.mora+" d";recompute(st);};
  cuota.oninput=()=>{st.cuota=+cuota.value;document.getElementById("wiCuotaV").textContent="S/ "+st.cuota;st.saldo=st.cuota*4;recompute(st);};
  document.querySelectorAll("#wiDig button").forEach(b=>b.onclick=()=>{
    st.digital=+b.dataset.v;tog("#wiDig",b);recompute(st);});
  document.querySelectorAll("#wiRiesgo button").forEach(b=>b.onclick=()=>{
    st.riesgo=b.dataset.v;tog("#wiRiesgo",b);recompute(st);});
  recompute(st);
}
function tog(sel,btn){document.querySelectorAll(sel+" button").forEach(x=>x.classList.remove("on"));btn.classList.add("on");}

function tramoDe(dias){ for(const r of CFG.tramos_mora.rangos){ if(dias<=r.max_dias) return r; } }
function pagoEst(canal,dig){ return CFG.canales[canal].pago_7d * CFG.ajuste_canal_por_perfil_digital[dig?"digital":"no_digital"][canal]; }

function decidirJS(st){
  const tramo=tramoDe(st.mora), base=Math.max(st.cuota,1);
  let perm=["whatsapp","sms"], montoAlto=(st.saldo||st.cuota*4)>=3000;
  if(st.riesgo==="alto"||montoAlto) perm.push("llamada");
  if(st.riesgo==="alto"&&montoAlto) perm.push("campo");
  if(!st.digital&&!perm.includes("llamada")) perm.push("llamada");
  const rank=perm.map(c=>{const p=pagoEst(c,st.digital);return {canal:c,valor_neto:p*base-CFG.canales[c].costo,pago:p};})
    .sort((a,b)=>b.valor_neto-a.valor_neto);
  const elegido=rank[0].canal;
  const tope=CFG.topes_contacto.por_riesgo[st.riesgo];
  const costoIA=CFG.canales[elegido].costo*Math.max(tope,1);
  const costoActual=CFG.baseline.contactos_por_credito*0.99;
  return { canal:elegido, nombre:CFG.canales[elegido].nombre, tramo, tope,
    recup: rank[0].pago*st.cuota, ahorro:costoActual-costoIA,
    ahorroPct: Math.round((costoActual-costoIA)/costoActual*100) };
}

function recompute(st){
  const r=decidirJS(st);
  document.getElementById("wiOut").innerHTML=
    `<div class="drow" style="margin-top:12px;background:#eef9f2;border-color:#bce8cf">
      <div class="di" style="background:#d6f3e0">${CH_ICON[r.canal]}</div>
      <div><div class="dk">Nueva decisión IA · ${r.tramo.etiqueta} (${r.tramo.etapa})</div>
      <div class="dv">${r.nombre} · máx ${r.tope} contacto(s)</div>
      <div class="dsub">Recuperación esperada ${soles(r.recup)} · ${r.ahorroPct}% menos costo</div></div></div>`;
}

boot();

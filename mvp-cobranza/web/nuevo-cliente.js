"use strict";
/* ============================================================
   Simular ingreso de un cliente nuevo (flujo real de Mibanco)
   Cargas los datos del Excel → confIA procesa paso a paso → fila insertada.
   Calcula la decisión EN VIVO en el navegador (misma lógica que el motor).
   ============================================================ */
(function () {
  let _ncCount = 0;
  const Q = s => document.querySelector(s);
  const LADDER = [[-3, "Recordatorio amable"], [2, "Aviso a tiempo"], [9, "Seguir de cerca"],
                  [18, "Ofrecer opciones"], [32, "Buscar acuerdo"], [47, "Reestructurar juntos"], [62, "Acompañar de cerca"]];
  const DIAS_MES = [3, 8, 13, 18, 22, 26, 29];
  const ETAPAS = [["preventivo", "Al día / preventivo", -3], ["temprana", "Mora temprana (1-30 días)", 8],
                  ["media", "Mora media (31-60 días)", 40], ["tardia", "Mora alta (60+ días)", 70]];

  const etapaDe = d => d <= 0 ? "preventivo" : d <= 30 ? "temprana" : d <= 60 ? "media" : "tardia";
  const catMora = d => d <= 0 ? "Al día / preventivo" : d <= 30 ? "Mora temprana (1-30 días)" : d <= 60 ? "Mora media (31-60 días)" : "Mora alta (60+ días)";
  const riesgoDe = pd => { const u = (typeof CFG !== "undefined" && CFG.umbrales_riesgo) || { bajo_max_prob_default: .15, alto_min_prob_default: .40 }; return pd <= u.bajo_max_prob_default ? "bajo" : pd >= u.alto_min_prob_default ? "alto" : "medio"; };
  const buenDe = (r, a, pd) => r >= .85 && a <= 1 && pd <= .20;
  const nDe = (et, r, b) => et === "preventivo" ? 1 : et === "temprana" ? (b ? 1 : { bajo: 1, medio: 2, alto: 3 }[r]) : et === "media" ? (r === "alto" ? 4 : 3) : (r === "alto" ? 7 : 5);
  const tonoDe = (r, b) => b ? "agradecido" : r === "alto" ? "empatico-claro" : "cercano";
  function tramoP7(d) { const r = (typeof CFG !== "undefined" && CFG.tramos_mora && CFG.tramos_mora.rangos) || []; for (const x of r) { if (d <= x.max_dias) return x.pago_7d; } return r.length ? r[r.length - 1].pago_7d : .4; }

  function mensaje(nombre, etTouch, tono, cuota) {
    const n = (nombre || "vecino").split(" ")[0];
    if (etTouch === "preventivo") return `Hola ${n} 👋 Te escribe Mibanco. Ojito nomás: tu cuota de S/${cuota} vence en unos días. Cuando puedas, la pagas fácil por la app o Yape. ¡Gracias por estar al día! 💚`;
    if (tono === "agradecido") return `Hola ${n} 👋 Te escribe Mibanco. Sabemos que tú siempre cumples 🙌 Si se te pasó, tu cuota de S/${cuota} quedó pendiente — la pagas en un toque por la app o Yape.`;
    if (tono === "empatico-claro") return `Hola ${n} 👋 Te escribe Mibanco. Sabemos que el negocio tiene sus altos y bajos 🤝 Tu cuota es de S/${cuota}; si hoy no puedes toda, la vemos en partes o te la reprogramamos. Escríbenos nomás y lo solucionamos.`;
    return `Hola ${n} 👋 Te escribe Mibanco. Tu cuota de S/${cuota} está pendiente. La pagas fácil por la app o Yape, sin apuro. Cualquier cosa, aquí estamos 💚`;
  }

  function calendario(c) {
    const etapa = etapaDe(c.dias_mora), tope = { preventivo: 1, temprana: 3, media: 4, tardia: 7 }[etapa];
    const n = nDe(etapa, c.riesgo, c.buen), tono = tonoDe(c.riesgo, c.buen);
    const cont = LADDER.slice(0, n).map(([rel, obj], idx) => {
      const et = etapaDe(rel);
      const dd = new Date(2026, 5, Math.min(Math.max(DIAS_MES[idx], 1), 30));
      if (dd.getDay() === 0) dd.setDate(dd.getDate() + 1);
      let canal = "whatsapp", o = obj, m;
      if (!c.es_digital && et === "tardia" && idx === n - 1) canal = "campo";
      else if (!c.es_digital && (et === "media" || et === "tardia")) canal = "llamada";
      if (canal === "whatsapp") m = mensaje(c.nombre, et, tono, c.cuota);
      else if (canal === "llamada") { m = "📞 Llamada de tu asesor de Mibanco (verificable, no robot) para coordinar."; o = "Llamada del asesor"; }
      else { m = "🚶 Visita de tu asesor de Mibanco — último recurso si no responde por WhatsApp."; o = "Visita del asesor"; }
      return { fecha: String(dd.getDate()).padStart(2, "0") + " jun", dia: dd.getDate(), etapa: catMora(Math.max(rel, 0)),
        dias_rel: rel, rel_label: rel < 0 ? `−${Math.abs(rel)} d` : `+${rel} d`, rel_nota: rel < 0 ? "antes de vencer" : "días de atraso",
        objetivo: o, canal, mensaje: m, verificable: true };
    }).sort((a, b) => a.dia - b.dia);
    const nota = etapa === "preventivo" ? "Buen pagador / al día: basta 1 recordatorio preventivo. Decidir a quién NO molestar también es parte del motor."
      : (!c.es_digital && (etapa === "media" || etapa === "tardia")) ? "WhatsApp primero; si no responde, escala a llamada del asesor y, en último recurso, visita. Nunca se elimina un canal."
      : "Todo por WhatsApp verificable. El nº de toques sube con la etapa de mora y baja con el buen comportamiento de pago.";
    return { mes: "junio 2026", total_contactos: cont.length, tope, etapa: catMora(c.dias_mora), es_moroso: c.dias_mora > 0, nota, contactos: cont };
  }

  function yape(c) {
    const cuota = c.cuota || 300, base = Math.max(120, Math.round(cuota * (1.8 + Math.random() * 1.4) / 10) * 10);
    const labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"], spike = 2 + Math.floor(Math.random() * 4);
    const dias = labels.map((lb, i) => { let f = 0.6 + Math.random() * 0.45; if (i === 6) f *= 0.45; if (i === spike) f = 1.7 + Math.random() * 0.6; return { label: lb, monto: Math.max(0, Math.round(base * f / 10) * 10) }; });
    const montos = dias.map(d => d.monto), prom = Math.round(montos.reduce((a, b) => a + b, 0) / 7 / 10) * 10, umbral = Math.round(prom * 1.35 / 10) * 10;
    const pico = dias[spike], buen = pico.monto >= umbral, crec = prom ? Math.round((pico.monto - prom) / prom * 100) : 0;
    const full = { Lun: "lunes", Mar: "martes", "Mié": "miércoles", Jue: "jueves", Vie: "viernes", "Sáb": "sábado", Dom: "domingo" };
    const diaSig = labels[spike + 1] || "Lun", n = (c.nombre || "vecino").split(" ")[0], mf = pico.monto.toLocaleString("es-PE");
    return {
      dias, promedio: prom, umbral, pico_label: pico.label, pico_monto: pico.monto, crecimiento_pct: crec, buen_dia: buen,
      sugerencia: buen ? `El ${pico.label.toLowerCase()} recibió S/${mf} por Yape (+${crec}% vs su promedio diario). Buen momento para sugerirle adelantar parte de su cuota o prepagar interés con YoSiLa.` : "Flujo estable esta semana. Sin sugerencia de prepago por ahora.",
      dia_envio: `${full[diaSig] || diaSig} 11am-1pm`,
      mensaje_prepago: buen ? `*Mibanco* ✅ Hola ${n} 👋 Vimos que el ${pico.label.toLowerCase()} te fue bien 💪 (S/${mf} en ventas por Yape).\nSi quieres, puedes adelantar parte de tu próxima cuota o ir prepagando interés con YoSiLa — solo si te conviene.\nRespóndeme SÍ y te explico. YoSiLa siempre está disponible: tú decides 💚` : null
    };
  }

  function convGen(c, ekey, diasRef) {
    const tono = tonoDe(c.riesgo, c.buen);
    const conv = [{ de: "banco", texto: mensaje(c.nombre, etapaDe(diasRef), tono, c.cuota) }];
    if (ekey === "preventivo") conv.push({ de: "cliente", texto: "ya, gracias por avisar 👍" });
    else if (ekey === "temprana") { conv.push({ de: "cliente", texto: "sí, ahí lo veo" }); conv.push({ de: "banco", texto: "Cuando quieras lo solucionamos 💚 Si te sirve, activas YoSiLa: un % de cada venta por Yape se va juntando para tu cuota, ni lo sientes." }); }
    else if (ekey === "media") { if (!c.es_digital) conv.push({ de: "sistema", tipo: "llamada", texto: "📞 Llamada · *Mibanco* ✅ · asesor verificable (no robot)" }); conv.push({ de: "cliente", texto: "esta semana coordino" }); }
    else { if (!c.es_digital) { conv.push({ de: "sistema", tipo: "llamada", texto: "📞 Llamada · *Mibanco* ✅ · asesor verificable" }); conv.push({ de: "sistema", tipo: "campo", texto: "🚶 Visita · asesor *Mibanco* ✅ · ÚLTIMO RECURSO" }); } conv.push({ de: "banco", texto: "Tenemos opciones para reestructurarte sin penalidad (Ley 29571). Y YoSiLa sigue disponible si quieres cobrarte con tus propias ventas de Yape 💚" }); conv.push({ de: "cliente", texto: "ya, lo vemos" }); }
    return conv;
  }
  function simulacion(c) {
    const etapas = ETAPAS.map(([k, l, dr]) => { const msgs = convGen(c, k, dr); let canal = "whatsapp"; if (msgs.some(m => m.tipo === "campo")) canal = "campo"; else if (msgs.some(m => m.tipo === "llamada")) canal = "llamada"; return { key: k, label: l, dias_ref: dr, n_contactos: nDe(etapaDe(dr), c.riesgo, c.buen), canal, conversacion: msgs }; });
    etapas.push({ key: "yosila", label: "YoSiLa cubriendo la cuota", dias_ref: 18, n_contactos: 0, canal: "whatsapp", conversacion: [
      { de: "banco", texto: "*Mibanco* ✅ YoSiLa está disponible para ti 💚\nActivas un % de cada venta por Yape: va primero al interés, luego al capital, y se apaga solo al completar la cuota. Sin una sola llamada.\n¿Lo activamos?" },
      { de: "cliente", texto: "¿y cómo lo activo?" },
      { de: "banco", texto: "Respóndeme el % por aquí (1, 2, 3 o 5) y listo — queda registrado como tu permiso (Res. SBS 02522-2025)." }] });
    return { default: etapaDe(c.dias_mora), etapas };
  }

  function buildClient(f) {
    _ncCount++;
    const c = { nombre: f.nombre, edad: f.edad, region: f.region, es_digital: f.es_digital, dias_mora: f.dias_mora,
      saldo: f.saldo, cuota: f.cuota, prob_default: f.prob_default, ratio: f.ratio, atrasos: f.atrasos };
    c.riesgo = riesgoDe(c.prob_default); c.buen = buenDe(c.ratio, c.atrasos, c.prob_default);
    const etapa = etapaDe(c.dias_mora), cat = catMora(c.dias_mora), tono = tonoDe(c.riesgo, c.buen);
    const cal = calendario(c), prob7 = tramoP7(c.dias_mora);
    let s = prob7 * 40 + Math.min(c.saldo / 5000, 1) * 30 + { alto: 20, medio: 12, bajo: 6 }[c.riesgo]; if (c.buen) s *= 0.6;
    const prioridad = Math.round(Math.min(s, 100));
    const ficha = { edad: c.edad, region: c.region, zona: "urbano", producto: "microcrédito", es_digital: c.es_digital,
      uso_app: c.es_digital ? 0.5 : 0.08, uso_whatsapp: c.es_digital, interaccion_digital: c.es_digital ? 62 : 18, score_riesgo: null,
      prob_default: c.prob_default, ratio_pago: c.ratio, num_atrasos_previos: c.atrasos, dias_mora_promedio: 0, ultimo_pago_dias: null,
      saldo_restante: c.saldo, cuota_mensual: c.cuota, dias_mora: c.dias_mora, prob_repago_7d: prob7, prob_repago_30d: null };
    const porque = { categoria_mora: cat,
      riesgo: `Riesgo ${c.riesgo.toUpperCase()} — prob. de impago ${Math.round(c.prob_default * 100)}%, paga ${Math.round(c.ratio * 100)}% de sus cuotas a tiempo, ${c.atrasos} atraso(s) previos. El score del banco no se usa para decidir: en la data tiene correlación ~0 con el pago real.`,
      prob_repago: `${Math.round(prob7 * 100)}% de probabilidad de pagar en 7 días sin que lo contactemos. ${c.dias_mora <= 0 ? "Conviene solo un recordatorio preventivo." : "El contacto temprano rinde casi el doble que el tardío."}`,
      tope: `${cal.total_contactos} contacto(s) este mes según su etapa (${cat}). El nº sube con la mora (preventivo 1 → temprana 1-3 → media 3-4 → tardía 5-7) y baja con el buen pago.`,
      contactar: cal.total_contactos ? "Contactar por WhatsApp verificable. Llamada/visita solo como último recurso si no responde." : "NO contactar." };
    const decision = { canal: { canal: "whatsapp", canal_nombre: "WhatsApp oficial Mibanco", verificable: true, motivo: "Oficial, anti-extorsión. Mayor conversión y 15× más barato que llamar." },
      momento: { cuando: c.dias_mora <= 0 ? "Recordatorio preventivo, 2-4 días antes" : "Pronto (la mora temprana paga casi el doble)", franja: "13:00-18:00", evitar: "07:00-10:00" },
      frecuencia: { tope_contactos: { bajo: 1, medio: 2, alto: 3 }[c.riesgo], nota: "Máximo según etapa y riesgo; el sobre-contacto baja el pago." }, tono, mensaje: cal.contactos[0] ? cal.contactos[0].mensaje : "" };
    return { cliente_id: "NEW-" + _ncCount, nombre: c.nombre, prioridad, accion: cal.total_contactos ? "CONTACTAR" : "NO CONTACTAR",
      segmento: { riesgo: c.riesgo, es_digital: c.es_digital, buen_pagador: c.buen, tramo_mora: cat, etapa_mora: etapa, dias_mora: c.dias_mora },
      decision, ficha, porque, calendario: cal, yape: yape(c), simulacion: simulacion(c), nota: "", es_demo: false, es_nuevo: true };
  }

  /* ---------------- Modal + flujo ---------------- */
  const FORM = `
    <p class="nc-intro">Así ingresa Mibanco a un cliente nuevo: cargas sus datos del Excel y <b>Mibanco-confIA</b> decide al instante qué hacer con él.</p>
    <div class="nc-grid">
      <label>Nombre<input id="ncNombre" value="Carmen Quispe" /></label>
      <label>Edad<input id="ncEdad" type="number" value="41" /></label>
      <label>Región<select id="ncRegion"><option>Lima</option><option>Norte</option><option>Centro</option><option>Sur</option><option>Oriente</option></select></label>
      <label>Saldo (S/)<input id="ncSaldo" type="number" value="2800" /></label>
      <label>Cuota (S/)<input id="ncCuota" type="number" value="380" /></label>
      <label>Días de mora<input id="ncMora" type="number" value="5" /></label>
      <label>Prob. de impago (%)<input id="ncPd" type="number" value="18" min="0" max="100" /></label>
      <label>Paga a tiempo (%)<input id="ncRatio" type="number" value="82" min="0" max="100" /></label>
      <label>Atrasos previos<input id="ncAtr" type="number" value="1" /></label>
      <label class="nc-toggle"><input id="ncDig" type="checkbox" checked /> Usa canales digitales (app / Yape / WhatsApp)</label>
    </div>
    <button class="nc-go" id="ncGo">⚙ Procesar con Mibanco-confIA</button>`;

  const STEPS = ["Leyendo los datos del cliente (Excel)", "Modelo M1 · ¿vale la pena contactar?",
    "Modelo M2 · canal óptimo (valor neto)", "Modelo M3 · momento + pulso de Yape",
    "Modelo M4 · tono y mensaje según su perfil", "Generando calendario y conversación de WhatsApp"];

  function readForm() {
    return {
      nombre: (Q("#ncNombre").value || "").trim() || "Cliente nuevo",
      edad: +Q("#ncEdad").value || 40, region: Q("#ncRegion").value,
      saldo: +Q("#ncSaldo").value || 1000, cuota: +Q("#ncCuota").value || 200,
      dias_mora: Math.max(0, +Q("#ncMora").value || 0),
      prob_default: Math.min(1, Math.max(0, (+Q("#ncPd").value || 0) / 100)),
      ratio: Math.min(1, Math.max(0, (+Q("#ncRatio").value || 0) / 100)),
      atrasos: Math.max(0, +Q("#ncAtr").value || 0), es_digital: Q("#ncDig").checked,
    };
  }
  function openModal() { Q("#ncBody").innerHTML = FORM; Q("#ncModal").hidden = false; Q("#ncGo").onclick = procesar; }
  function closeModal() { Q("#ncModal").hidden = true; }

  function procesar() {
    const f = readForm();
    Q("#ncBody").innerHTML = `<div class="nc-loading">${STEPS.map((s, i) => `<div class="nc-step" id="ncStep${i}"><span class="nc-spin"></span><span>${s}</span></div>`).join("")}</div>`;
    let i = 0;
    const tick = () => {
      if (i > 0) { const p = Q("#ncStep" + (i - 1)); if (p) { p.classList.add("done"); p.classList.remove("active"); p.querySelector(".nc-spin").textContent = "✓"; } }
      if (i < STEPS.length) { const cur = Q("#ncStep" + i); if (cur) cur.classList.add("active"); i++; setTimeout(tick, 620); }
      else { finalizar(f); }
    };
    tick();
  }

  function finalizar(f) {
    const d = buildClient(f);
    if (typeof CLIENTES === "undefined") return;
    CLIENTES.unshift(d);
    Q("#ncBody").innerHTML = `<div class="nc-done">
      <div class="nc-done-ic">✅</div>
      <b>Cliente procesado e insertado</b>
      <p><b>${d.nombre}</b> · riesgo ${d.segmento.riesgo} · ${d.calendario.etapa} · ${d.calendario.total_contactos} contacto(s)/mes por WhatsApp.</p>
      <button class="nc-go" id="ncSee">Ver su decisión →</button>
    </div>`;
    Q("#ncSee").onclick = () => {
      closeModal();
      // mostrar en la lista (filtro Todos) y seleccionar
      FILTER = "todos";
      document.querySelectorAll("#decFilters .chip").forEach(c => c.classList.toggle("on", c.dataset.f === "todos"));
      if (typeof renderDecList === "function") renderDecList();
      if (typeof selectCli === "function") selectCli(d.cliente_id);
      const det = Q("#decDetail"); if (det) det.scrollIntoView({ behavior: "smooth", block: "start" });
    };
  }

  document.addEventListener("click", e => {
    if (e.target.closest("#addCliBtn")) openModal();
    else if (e.target.closest("#ncClose")) closeModal();
    else if (e.target.classList && e.target.classList.contains("modal-ov")) closeModal();
  });
})();

// ============================================================
// sketch.js — Render y animación de la demo VERA (p5.js).
// NO calcula rutas: usa window.VERA (modelo.js) y window.DATOS (datos.js).
// ============================================================
const W = 1160, H = 740;

let pab, nodo = {};            // nodo[id] = {x,y,...}
let ocupacion = {};            // aula -> personas (escenario)
let asignacion = {}, carga = {};
let algoritmo = "DIJKSTRA";
let corriendo = false, velocidad = 1.0, tiempo = 0;

let personas = [];             // agentes en movimiento
let spawnCont = {};            // aula -> personas ya generadas
let evacCont = {};             // aula -> personas evacuadas
let frameSpawn = 0;
let SC = 1;                    // factor de escala del lienzo (responsive)

const COL = {
  pend: "#6b7a99", trans: "#4aa3ff", evac: "#37d67a", sinruta: "#ff5c6c",
  salida: "#2fd98a", bloq: "#ff5c6c", pasillo: "#2a3a5c", descanso: "#38496e",
};

// ---------- setup ----------
function setup() {
  const cont = document.getElementById("lienzo");
  const cw = (cont && cont.clientWidth) || 1000;
  SC = cw / W;
  const c = createCanvas(cw, Math.round(H * SC));
  c.parent("lienzo");
  pixelDensity(Math.min(2, window.devicePixelRatio || 1));
  textFont("Segoe UI");

  pab = new VERA.Pabellon(DATOS);
  Object.values(pab.nodos).forEach((n) => (nodo[n.id] = n));
  aplicarOcupacion(DATOS.ocupacionDefault || 30);
  bindUI();
  recomputar(true);
}

// ---------- lógica de escenario ----------
function aplicarOcupacion(n) {
  ocupacion = {};
  pab.getAulas().forEach((a) => (ocupacion[a] = n));
}

function recomputar(reset) {
  const r = VERA.asignarTodas(pab, ocupacion, algoritmo);
  asignacion = r.asignacion; carga = r.carga;
  if (reset) reiniciarPersonas();
  actualizarPanel();
}

function reiniciarPersonas() {
  personas = []; tiempo = 0; frameSpawn = 0;
  spawnCont = {}; evacCont = {};
  pab.getAulas().forEach((a) => { spawnCont[a] = 0; evacCont[a] = 0; });
}

// ---------- animación ----------
function draw() {
  background("#05080f");
  push();
  scale(SC);                     // dibuja en espacio de diseño 1160×740
  dibujarPisos();
  dibujarTramos();
  dibujarNodos();
  if (corriendo) {
    tiempo += (deltaTime / 1000) * velocidad;
    generarPersonas();
    moverPersonas();
  }
  dibujarPersonas();
  pop();
  actualizarPanel();
}

function windowResized() {
  const cont = document.getElementById("lienzo");
  const cw = (cont && cont.clientWidth) || 1000;
  SC = cw / W;
  resizeCanvas(cw, Math.round(H * SC));
}

function generarPersonas() {
  frameSpawn++;
  if (frameSpawn % Math.max(2, Math.round(6 / velocidad)) !== 0) return;
  // ordena por prioridad CCRP para que salgan primero los pisos altos
  const aulas = Object.keys(ocupacion).map(Number)
    .filter((a) => asignacion[a] && spawnCont[a] < ocupacion[a])
    .sort((a, b) => pab.nodos[b].piso - pab.nodos[a].piso);
  for (const a of aulas.slice(0, 3)) {
    spawnCont[a]++;
    personas.push(nuevaPersona(a, asignacion[a]));
  }
}

function nuevaPersona(aula, ruta) {
  const o = nodo[ruta[0]];
  return {
    aula, ruta, seg: 0, p: 0,
    x: o.x + random(-10, 10), y: o.y + random(-6, 6),
    vel: random(0.9, 1.25), jitter: random(-6, 6),
  };
}

function moverPersonas() {
  const px = 2.1; // pixeles base por frame
  for (const ag of personas) {
    if (ag.done) continue;
    const A = nodo[ag.ruta[ag.seg]], B = nodo[ag.ruta[ag.seg + 1]];
    if (!B) { ag.done = true; continue; }
    const d = dist(A.x, A.y, B.x, B.y) || 1;
    ag.p += (px * ag.vel * velocidad) / d;
    while (ag.p >= 1 && ag.seg < ag.ruta.length - 1) {
      ag.p -= 1; ag.seg++;
      if (ag.seg >= ag.ruta.length - 1) {
        ag.done = true; evacCont[ag.aula]++; break;
      }
    }
    if (!ag.done) {
      const C = nodo[ag.ruta[ag.seg]], D = nodo[ag.ruta[ag.seg + 1]] || C;
      ag.x = lerp(C.x, D.x, ag.p);
      ag.y = lerp(C.y, D.y, ag.p) + Math.sin(ag.p * 6 + ag.jitter) * 1.5;
    }
  }
  personas = personas.filter((a) => !a.done || a._keep);
}

// ---------- dibujo ----------
function fondo() {
  background("#0b1220");
}

function dibujarPisos() {
  const pisos = [
    { y: 140, label: "PISO 2" },
    { y: 350, label: "PISO 1" },
    { y: 560, label: "PLANTA BAJA" },
  ];
  noFill(); stroke(44, 60, 92); strokeWeight(2.5);     // marco del edificio
  rect(66, 92, W - 150, 536, 12);
  for (const b of pisos) {
    noStroke(); fill(255, 255, 255, 7);
    rect(72, b.y - 80, W - 162, 160, 6);
    stroke(34, 46, 72); strokeWeight(1.5);             // losa
    line(72, b.y + 80, W - 90, b.y + 80);
    noStroke(); fill("#55678f"); textSize(11); textAlign(LEFT, CENTER); textStyle(BOLD);
    text(b.label, 84, b.y - 66); textStyle(NORMAL);
  }
}

function colorCarga(t) {
  const cap = t.capacidad || 1;
  const frac = Math.min(1, (carga[t.id] || 0) / cap);
  // verde -> amarillo -> rojo
  const c1 = color("#37d67a"), c2 = color("#f5a623"), c3 = color("#ff5c6c");
  return frac < 0.5 ? lerpColor(c1, c2, frac / 0.5) : lerpColor(c2, c3, (frac - 0.5) / 0.5);
}

function dibujarTramos() {
  strokeCap(ROUND);
  for (const t of Object.values(pab.tramos)) {
    const A = nodo[t.origen], B = nodo[t.destino];
    const bloq = t.estado === "BLOQUEADO";
    const usado = (carga[t.id] || 0) > 0;
    const w = t.tipo === "PASILLO" ? 16 : t.tipo === "ESCALERA" ? 14 : 11;
    stroke(14, 20, 34); strokeWeight(w + 5);           // contorno del corredor
    line(A.x, A.y, B.x, B.y);
    if (bloq) {
      stroke(COL.bloq); strokeWeight(w);
      drawingContext.setLineDash([8, 7]); line(A.x, A.y, B.x, B.y);
      drawingContext.setLineDash([]); dibujarX(A, B);
    } else {
      stroke(usado ? colorCarga(t) : color(42, 56, 86)); strokeWeight(w);
      line(A.x, A.y, B.x, B.y);
      if (t.tipo === "ESCALERA") dibujarPeldanos(A, B, w);
    }
  }
  strokeCap(PROJECT);
}

function dibujarPeldanos(A, B, w) {           // Opción A: escalones
  stroke(14, 20, 34); strokeWeight(2);
  const dx = B.x - A.x, dy = B.y - A.y, L = Math.hypot(dx, dy) || 1;
  const px = (-dy / L) * (w / 2 - 1), py = (dx / L) * (w / 2 - 1);
  for (let i = 1; i <= 5; i++) {
    const t = i / 6, x = lerp(A.x, B.x, t), y = lerp(A.y, B.y, t);
    line(x - px, y - py, x + px, y + py);
  }
}

function dibujarX(A, B) {
  const mx = (A.x + B.x) / 2, my = (A.y + B.y) / 2;
  stroke(COL.bloq); strokeWeight(3);
  line(mx - 7, my - 7, mx + 7, my + 7); line(mx - 7, my + 7, mx + 7, my - 7);
}

function dibujarNodos() {
  textAlign(CENTER, CENTER);
  for (const n of Object.values(nodo)) {
    if (n.tipo === "AULA") dibujarAula(n);
    else if (n.tipo === "SALIDA") dibujarSalida(n);
    else if (n.id === 50) dibujarVestibulo(n);
    else dibujarNodoPaso(n);
  }
}

function dibujarAula(n) {
  const est = estadoAula(n.id);
  const key = est === "SIN_RUTA" ? "sinruta" : est;
  const col = color(COL[key] || COL.pend);
  const total = ocupacion[n.id];
  const enSalon = Math.max(0, total - (spawnCont[n.id] || 0));  // los que aún no salieron
  const x = n.x, w = 98, h = 66, top = n.y - 78;
  noStroke(); fill(28, 36, 56); rect(x - w / 2, top, w, h, 5);  // piso de la sala
  // pupitres (2 filas × 5) + estudiantes encima (se van vaciando)
  const slots = 10, cols = 5, ocup = Math.round((enSalon / Math.max(1, total)) * slots);
  for (let i = 0; i < slots; i++) {
    const cx = x - 36 + (i % cols) * 18;
    const cy = top + 26 + Math.floor(i / cols) * 17;
    noStroke(); fill(44, 56, 82); rect(cx - 6, cy + 3, 12, 5, 1);          // pupitre
    if (i < ocup) {                                                        // estudiante
      const jx = Math.sin(frameCount * 0.06 + i) * 1.1;
      const jy = Math.cos(frameCount * 0.06 + i * 2) * 1.1;
      noStroke(); fill(56, 116, 200); ellipse(cx + jx, cy + jy, 6, 7);
      fill(242, 221, 190); circle(cx + jx, cy - 1.2 + jy, 3.6);
    }
  }
  stroke(col); strokeWeight(2.4); noFill(); const g = 12;        // paredes + hueco de puerta
  line(x - w / 2, top, x + w / 2, top);
  line(x - w / 2, top, x - w / 2, top + h);
  line(x + w / 2, top, x + w / 2, top + h);
  line(x - w / 2, top + h, x - g, top + h);
  line(x + g, top + h, x + w / 2, top + h);
  noStroke(); fill("#eaf1fc"); textSize(11); textStyle(BOLD);
  text(n.label, x, top + 11); textStyle(NORMAL);
  fill(col); textSize(10.5);
  const et = est === "SIN_RUTA" ? "⚠ SIN RUTA" : est === "evac" ? "✓ evacuada" : enSalon + " en aula";
  text(et, x, top + h - 7);
}

function dibujarVestibulo(n) {
  noStroke(); fill(28, 40, 64);
  rect(n.x - 48, n.y - 17, 96, 34, 7);
  stroke(70, 86, 120); strokeWeight(1.5); noFill();
  rect(n.x - 48, n.y - 17, 96, 34, 7);
  noStroke(); fill("#9db0d0"); textSize(10.5); text(n.label, n.x, n.y);
}

function dibujarSalida(n) {
  noStroke(); fill(COL.salida);
  rect(n.x - 32, n.y - 15, 64, 30, 6);
  fill("#06251a"); textSize(11); textStyle(BOLD);
  text("SALIDA", n.x, n.y - 1); textStyle(NORMAL);
  fill(COL.salida); triangle(n.x - 6, n.y + 21, n.x + 6, n.y + 21, n.x, n.y + 29);
}

function dibujarNodoPaso(n) {
  noStroke(); fill(n.tipo === "PASO" ? "#33466b" : "#3c5080");
  circle(n.x, n.y, 13);
  fill("#64769a"); textSize(9); text(n.label, n.x, n.y + 17);
}

function dibujarPersonas() {
  for (const ag of personas) {
    noStroke();
    fill(56, 116, 200); ellipse(ag.x, ag.y + 0.5, 9, 10.5);      // hombros
    fill(56, 116, 200, 210); circle(ag.x - 4.6, ag.y, 3.4); circle(ag.x + 4.6, ag.y, 3.4);  // brazos
    fill(242, 221, 190); circle(ag.x, ag.y - 1.5, 5.4);          // cabeza
  }
}

// ---------- estado / panel ----------
function estadoAula(a) {
  if (!asignacion[a]) return ocupacion[a] > 0 ? "SIN_RUTA" : "evac";
  if ((evacCont[a] || 0) >= ocupacion[a]) return "evac";
  if (corriendo && (spawnCont[a] || 0) > 0) return "trans";
  return "pend";
}
function claseEstado(a) {
  const e = estadoAula(a);
  return e === "evac" ? "EVACUADA" : e === "trans" ? "EN_TRANSITO"
    : e === "SIN_RUTA" ? "SIN_RUTA" : "PENDIENTE";
}

function actualizarPanel() {
  const aulas = pab.getAulas();
  let dentro = 0, evac = 0, sinruta = 0, distSum = 0, distN = 0;
  for (const a of aulas) {
    const e = estadoAula(a);
    evac += evacCont[a] || 0;
    if (e === "SIN_RUTA") sinruta += ocupacion[a];
    dentro += ocupacion[a] - (evacCont[a] || 0);
    if (asignacion[a]) { distSum += VERA.largoRuta(pab, asignacion[a]); distN++; }
  }
  const transito = personas.length;
  $("stDentro").textContent = dentro;
  $("stTransito").textContent = transito;
  $("stEvac").textContent = evac;
  $("stSinRuta").textContent = sinruta;
  $("stTiempo").textContent = tiempo.toFixed(1) + " s";
  $("stDist").textContent = (distN ? Math.round(distSum / distN) : 0) + " m";
  $("stAlg").textContent = algoritmo === "BFS" ? "BFS" : "Dijkstra";

  const inv = VERA.verificar(pab, asignacion, carga, ocupacion);
  setInv("I1", inv.I1); setInv("I2", inv.I2); setInv("I3", inv.I3);
  setInv("I4", inv.I4); setInv("I5", true);
}

function setInv(k, ok) {
  const el = document.querySelector(`.inv[data-k="${k}"]`);
  if (el) { el.classList.toggle("ok", ok); el.classList.toggle("bad", !ok); }
}
function $(id) { return document.getElementById(id); }

// ---------- interacción ----------
function mousePressed() {
  const mx = mouseX / SC, my = mouseY / SC;   // a espacio de diseño
  if (mx < 0 || mx > W || my < 0 || my > H) return;
  let mejor = null, md = 10;
  for (const t of Object.values(pab.tramos)) {
    const A = nodo[t.origen], B = nodo[t.destino];
    const d = distSeg(mx, my, A.x, A.y, B.x, B.y);
    if (d < md) { md = d; mejor = t.id; }
  }
  if (mejor != null) { pab.alternar(mejor); recomputar(false); }
}

function distSeg(px, py, x1, y1, x2, y2) {
  const dx = x2 - x1, dy = y2 - y1;
  const l2 = dx * dx + dy * dy || 1;
  let t = ((px - x1) * dx + (py - y1) * dy) / l2;
  t = Math.max(0, Math.min(1, t));
  return dist(px, py, x1 + t * dx, y1 + t * dy);
}

function bindUI() {
  $("btnPlay").onclick = () => {
    corriendo = !corriendo;
    $("btnPlay").textContent = corriendo ? "⏸ Pausar" : "▶ Iniciar";
    $("btnPlay").classList.toggle("primario", !corriendo);
  };
  $("btnReset").onclick = () => { reiniciarPersonas(); corriendo = false;
    $("btnPlay").textContent = "▶ Iniciar"; $("btnPlay").classList.add("primario"); };

  document.querySelectorAll("#toggleAlg button").forEach((b) => {
    b.onclick = () => {
      document.querySelectorAll("#toggleAlg button").forEach((x) => x.classList.remove("on"));
      b.classList.add("on"); algoritmo = b.dataset.alg; recomputar(true);
    };
  });
  $("velocidad").oninput = (e) => { velocidad = +e.target.value; $("velVal").textContent = velocidad.toFixed(2) + "×"; };
  $("ocupacion").oninput = (e) => {
    aplicarOcupacion(+e.target.value); $("ocupVal").textContent = e.target.value;
    recomputar(true);
  };
  document.querySelectorAll(".btn.esc").forEach((b) => {
    b.onclick = () => aplicarEscenario(b.dataset.esc);
  });
  const bc = $("btnCargar"), ia = $("inputArchivo");
  if (bc && ia) {
    bc.onclick = () => ia.click();
    ia.onchange = (e) => { const f = e.target.files[0]; if (f) cargarArchivo(f); e.target.value = ""; };
  }
}

// Carga medidas reales desde un Excel (.xlsx) o CSV subido por el usuario.
// Mantiene la topología; solo actualiza ancho/largo y recalcula capacidad y rutas.
function cargarArchivo(f) {
  const ext = (f.name.split(".").pop() || "").toLowerCase();
  const aplicar = (filas) => {
    if (!filas || !filas.length) { alert("Archivo vacío."); return; }
    const head = filas[0].map((s) => (s == null ? "" : String(s)).toLowerCase());
    const iId = head.findIndex((h) => h.includes("elemento") || h === "id");
    const iA = head.findIndex((h) => h.includes("ancho"));
    const iL = head.findIndex((h) => h.includes("largo"));
    if (iId < 0 || iA < 0 || iL < 0) {
      alert("No encuentro las columnas elemento_id / ancho_m / largo_m."); return;
    }
    let n = 0;
    for (let i = 1; i < filas.length; i++) {
      const r = filas[i]; if (!r || r[iId] == null) continue;
      const id = +r[iId], anc = +r[iA], lar = +r[iL];
      if (!id || !anc || !lar) continue;
      const t = DATOS.tramos.find((x) => x.id === id); if (!t) continue;
      t.ancho = anc; t.largo = lar;
      t.capacidad = Math.floor(anc / (t.tipo === "ESCALERA" ? 0.008 : 0.005));
      n++;
    }
    pab = new VERA.Pabellon(DATOS);
    nodo = {}; Object.values(pab.nodos).forEach((x) => (nodo[x.id] = x));
    recomputar(true);
    alert("✓ Datos cargados: " + n + " tramos actualizados con tus medidas reales.");
  };
  if (ext === "xlsx" && window.XLSX) {
    const r = new FileReader();
    r.onload = () => {
      const wb = XLSX.read(new Uint8Array(r.result), { type: "array" });
      const ws = wb.Sheets[wb.SheetNames[0]];
      aplicar(XLSX.utils.sheet_to_json(ws, { header: 1, blankrows: false }));
    };
    r.readAsArrayBuffer(f);
  } else {
    const r = new FileReader();
    r.onload = () => {
      const filas = r.result.split(/\r?\n/)
        .filter((l) => l && !l.trim().startsWith("#")).map((l) => l.split(","));
      aplicar(filas);
    };
    r.readAsText(f);
  }
}

function aplicarEscenario(esc) {
  Object.keys(pab.tramos).forEach((id) => pab.habilitar(+id)); // limpia bloqueos
  if (esc === "normal") { aplicarOcupacion(30); setSlider(30); }
  if (esc === "aforo")  { aplicarOcupacion(60); setSlider(60); }
  if (esc === "dobleP2") { aplicarOcupacion(30); setSlider(30); pab.bloquear(2261); pab.bloquear(2262); }
  recomputar(true);
}
function setSlider(v) { $("ocupacion").value = v; $("ocupVal").textContent = v; }

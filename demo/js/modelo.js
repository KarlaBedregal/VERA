// ============================================================
// modelo.js — Lógica de ruteo de VERA (fiel a la especificación VDM++).
// NO dibuja nada. Funciona en el navegador (window.VERA) y en Node (require).
//   · capacidad A.130      ↔ Tipos`capacidad
//   · buscarRutaDijkstra   ↔ Planificador`buscarRutaDijkstra (RF04)
//   · buscarRutaBFS        ↔ Planificador`buscarRuta
//   · asignarTodas (CCRP)  ↔ Planificador`asignarTodas
//   · verificar (I1/I2/I3) ↔ SistemaEvacuacion`verificarI*
// ============================================================
(function (global) {
  "use strict";

  function capacidad(t) {
    const factor = t.tipo === "ESCALERA" ? 0.008 : 0.005;
    return Math.floor(t.ancho / factor);
  }
  function capacidadResidual(t, carga) {
    const cap = t.capacidad != null ? t.capacidad : capacidad(t);
    const c = carga || 0;
    return c >= cap ? 0 : cap - c;
  }

  class Pabellon {
    constructor(data) {
      this.nodos = {};
      this.tramos = {};
      data.nodos.forEach((n) => (this.nodos[n.id] = Object.assign({}, n)));
      data.tramos.forEach((t) => (this.tramos[t.id] = Object.assign({}, t)));
    }
    getAulas() {
      return Object.values(this.nodos).filter((n) => n.tipo === "AULA").map((n) => n.id);
    }
    getSalidas() {
      return new Set(Object.values(this.nodos).filter((n) => n.tipo === "SALIDA").map((n) => n.id));
    }
    getTramosDesde(nid) {
      return Object.values(this.tramos).filter((t) => t.origen === nid);
    }
    getTramoEntre(o, d) {
      return Object.values(this.tramos).find((t) => t.origen === o && t.destino === d) || null;
    }
    bloquear(tid)  { if (this.tramos[tid]) this.tramos[tid].estado = "BLOQUEADO"; }
    habilitar(tid) { if (this.tramos[tid]) this.tramos[tid].estado = "HABILITADO"; }
    alternar(tid)  {
      const t = this.tramos[tid]; if (!t) return;
      t.estado = t.estado === "HABILITADO" ? "BLOQUEADO" : "HABILITADO";
    }
  }

  function reconstruir(prev, origen, destino) {
    const ruta = [destino];
    let a = destino;
    while (a !== origen) { a = prev[a]; ruta.unshift(a); }
    return ruta;
  }

  // Dijkstra: ruta de MENOR DISTANCIA (largo) con capacidad residual suficiente.
  function buscarRutaDijkstra(pab, origen, personas, carga) {
    carga = carga || {};
    const dist = {}, prev = {}, visit = new Set();
    const salidas = pab.getSalidas();
    dist[origen] = 0;
    while (true) {
      let u = null, best = Infinity;
      for (const k in dist) {
        const n = +k;
        if (!visit.has(n) && dist[n] < best) { best = dist[n]; u = n; }
      }
      if (u === null) return null;
      visit.add(u);
      if (salidas.has(u)) return reconstruir(prev, origen, u);
      for (const t of pab.getTramosDesde(u)) {
        if (t.estado !== "HABILITADO") continue;
        if (capacidadResidual(t, carga[t.id] || 0) < personas) continue;
        if (visit.has(t.destino)) continue;
        const nd = dist[u] + t.largo;
        if (!(t.destino in dist) || nd < dist[t.destino]) {
          dist[t.destino] = nd; prev[t.destino] = u;
        }
      }
    }
  }

  // BFS: ruta de MENOR NÚMERO DE TRAMOS con capacidad residual suficiente.
  function buscarRutaBFS(pab, origen, personas, carga) {
    carga = carga || {};
    const salidas = pab.getSalidas();
    const cola = [[origen, [origen]]];
    const visit = new Set([origen]);
    while (cola.length) {
      const [nodo, camino] = cola.shift();
      if (salidas.has(nodo)) return camino;
      for (const t of pab.getTramosDesde(nodo)) {
        if (t.estado !== "HABILITADO") continue;
        if (capacidadResidual(t, carga[t.id] || 0) < personas) continue;
        if (visit.has(t.destino)) continue;
        visit.add(t.destino);
        cola.push([t.destino, camino.concat(t.destino)]);
      }
    }
    return null;
  }

  function largoRuta(pab, ruta) {
    let s = 0;
    for (let i = 0; i < ruta.length - 1; i++) {
      const t = pab.getTramoEntre(ruta[i], ruta[i + 1]);
      if (t) s += t.largo;
    }
    return Math.round(s * 10) / 10;
  }

  function reservar(pab, carga, ruta, personas) {
    for (let i = 0; i < ruta.length - 1; i++) {
      const t = pab.getTramoEntre(ruta[i], ruta[i + 1]);
      if (t) carga[t.id] = (carga[t.id] || 0) + personas;
    }
  }

  // CCRP: asigna todas las aulas por prioridad (piso más alto, luego más ocupación),
  // reservando capacidad al asignar cada ruta. algoritmo: "DIJKSTRA" | "BFS".
  function asignarTodas(pab, ocupacion, algoritmo) {
    const buscar = algoritmo === "BFS" ? buscarRutaBFS : buscarRutaDijkstra;
    const carga = {};
    const aulas = Object.keys(ocupacion).map(Number).filter((a) => ocupacion[a] > 0);
    aulas.sort((a, b) => {
      const pa = pab.nodos[a].piso, pb = pab.nodos[b].piso;
      if (pb !== pa) return pb - pa;              // piso más alto primero
      return ocupacion[b] - ocupacion[a];         // mayor ocupación primero
    });
    const asignacion = {};
    for (const a of aulas) {
      const ruta = buscar(pab, a, ocupacion[a], carga);
      asignacion[a] = ruta;                        // null = SIN_RUTA
      if (ruta) reservar(pab, carga, ruta, ocupacion[a]);
    }
    return { asignacion, carga };
  }

  function rutaUsaTramo(pab, ruta, tid) {
    const t = pab.tramos[tid];
    if (!t) return false;
    for (let i = 0; i < ruta.length - 1; i++) {
      if (t.origen === ruta[i] && t.destino === ruta[i + 1]) return true;
    }
    return false;
  }

  // Verifica invariantes I1, I2, I3 sobre una asignación (para el panel formal).
  function verificar(pab, asignacion, carga, ocupacion) {
    const salidas = pab.getSalidas();
    let I1 = true, I2 = true, I3 = true, I4 = true;
    for (const id in carga) {
      const t = pab.tramos[id];
      if (t && carga[id] > (t.capacidad != null ? t.capacidad : capacidad(t))) I2 = false;
    }
    for (const a in asignacion) {
      const r = asignacion[a];
      if (!r) continue;
      if (!salidas.has(r[r.length - 1])) I1 = false;
      for (let i = 0; i < r.length - 1; i++) {
        const t = pab.getTramoEntre(r[i], r[i + 1]);
        if (!t || t.estado !== "HABILITADO") I1 = false;
        if (t && t.estado === "BLOQUEADO") I3 = false;
      }
    }
    if (ocupacion) {
      for (const a in ocupacion) {
        if (ocupacion[a] > 0 && !(a in asignacion)) I4 = false; // toda aula ocupada considerada
      }
    }
    return { I1, I2, I3, I4 };
  }

  const API = {
    Pabellon, capacidad, capacidadResidual,
    buscarRutaDijkstra, buscarRutaBFS, asignarTodas,
    largoRuta, reservar, rutaUsaTramo, verificar, reconstruir,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  global.VERA = API;
})(typeof window !== "undefined" ? window : globalThis);

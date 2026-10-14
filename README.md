# VERA

**Especificación Formal y Validación en VDM++ de un Sistema de Evacuación Sísmica con Rutas Adaptativas para un Pabellón Universitario**

> Curso: Aspectos Formales de Especificación y Verificación · UNSA 2026-B  
> Equipo: C1 · C2 · C3 · C4 · C5

---

## ¿Qué es VERA?

VERA es una especificación formal en VDM++ de un sistema que, ante una alerta sísmica, asigna dinámicamente rutas de evacuación a cada aula de un pabellón universitario, garantizando que:

- Ninguna ruta pasa por un tramo bloqueado.
- Ningún pasillo, escalera o puerta supera la capacidad establecida por la **Norma A.130 RNE**.
- Si una escalera o pasillo queda bloqueado, el sistema **recalcula** las rutas afectadas.
- El sistema nunca declara la evacuación finalizada si hay personas adentro.

Las propiedades anteriores se verifican mediante **invariantes, precondiciones y postcondiciones en VDM++** (Parte 1) y mediante **model checking en UPPAAL** (Parte 2).

---

## Estructura del repositorio

```
VERA/
├── model/                    # Especificación VDM++
│   ├── Tipos.vdmpp           # Tipos, records y función capacidad (A.130)
│   ├── Pabellon.vdmpp        # Grafo del edificio e invariantes estructurales
│   ├── Planificador.vdmpp    # BFS con capacidad y asignación estilo CCRP
│   ├── SistemaEvacuacion.vdmpp  # Ciclo de vida e invariantes de seguridad
│   ├── PabellonUNSA.vdmpp   # Instancia con datos reales del pabellón UNSA
│   └── GeneradorPabellon.vdmpp  # Generador de pabellones de N pisos (escalabilidad)
├── tests/
│   ├── Test.vdmpp            # Escenarios T1–T9
│   └── Traces.vdmpp          # Pruebas combinatorias
├── uppaal/
│   ├── vera.xml              # Modelo UPPAAL (Sprint 2)
│   └── propiedades.q         # Consultas CTL (Sprint 2)
├── data/
│   └── pabellon-medidas.csv  # Mediciones reales del pabellón
├── docs/
│   ├── grafo-pabellon.png    # Grafo del edificio con IDs de nodos
│   ├── diagrama-clases.png   # Diagrama de clases VDM++
│   ├── diagrama-estados.png  # Diagrama de estados del sistema
│   └── capturas/             # Capturas del intérprete y UPPAAL
├── paper/                    # Artículo IEEE
├── PLANIFICACION.md          # Plan de proyecto por sprints
└── README.md
```

---

## Herramientas necesarias

| Herramienta | Para qué | Cómo instalar |
|---|---|---|
| VS Code | Editor principal | [code.visualstudio.com](https://code.visualstudio.com) |
| VDM VSCode | Extensión para VDM++ (sintaxis, intérprete, POG) | Buscar `vdm-vscode` en el marketplace |
| Overture | Intérprete VDM++ (incluido con la extensión) | Se instala automáticamente |
| UPPAAL | Model checker (Sprint 2) | [uppaal.org](https://uppaal.org) |

### Verificar instalación

1. Abrir VS Code.
2. Abrir la carpeta `model/`.
3. Abrir `Tipos.vdmpp` → debe aparecer el ícono de Overture en la barra lateral.
4. Click derecho → **Run interpreter** → debe ejecutar sin errores.

---

## Reglas de trabajo

- **Nadie sube directo a `main`.** Todo entra por Pull Request desde `develop` o desde una rama de tarea.
- Ramas de tarea: `feature/E3-XX-descripcion` (ej. `feature/E3-13-bfs`).
- Todo PR debe ser aprobado por el **revisor** asignado a la tarea.
- Commits con prefijo semántico:
  - `feat(E3-16): BFS con capacidad residual`
  - `test(E3-24): escenario T2 bloqueo de escalera`
  - `fix(E3-28): precondición de finalizarEvacuacion`
  - `docs(E3-30): sección modelo en el artículo`

### Definición de Hecho (DoD)

- [ ] El archivo compila sin errores en VDM VSCode.
- [ ] Tiene invariantes y/o pre/post donde corresponde.
- [ ] Al menos una prueba lo ejecuta.
- [ ] Entró a `develop` mediante PR aprobado por el revisor.
- [ ] Si aplica, está redactado en el artículo con su figura o tabla.

---

## Entregas

| Entregable | Fecha | Qué incluye |
|---|---|---|
| Parte 1 — VDM++ | 18 oct 2026 | Artículo IEEE · Video · Diapositivas · Código + release `v1.0-parte1` |
| Parte 2 — UPPAAL | 1 nov 2026 | Diagrama de estados · Propiedades verificadas |
| Final | 15 nov 2026 | PDF único (artículo + diapositivas) · Video final · Repo con README |

---

## Integrantes

| Código | Nombre | Rol en Sprint 1 |
|---|---|---|
| C1 | — | Coordinador · Artículo (Discusión, Abstract, trazabilidad) |
| C2 | — | Núcleo VDM++ (`Tipos`, `Pabellon`, `SistemaEvacuacion`) |
| C3 | — | Datos reales · Pruebas · Artículo (Intro, Resultados) |
| C4 | — | Grafo · Instancia real · Diagramas · Presentación |
| C5 | — | Algoritmos (BFS, `asignarTodas`, generador) · Pruebas combinatorias |

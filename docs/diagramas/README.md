# VERA — Diagramas UML

Diagramas de la especificación VDM++ (issue #18). Fuentes en **PlantUML**
(`.puml`) y versiones **Mermaid** editables abajo. Los PNG se ven directamente
en GitHub.

## 1. Diagrama de clases

![Diagrama de clases](VERA-diagrama-clases.png)

Seis clases en dos capas: **datos** (`Tipos`, `Pabellon`, `PabellonUNSA`,
`GeneradorPabellon`) y **lógica** (`Planificador`, `SistemaEvacuacion`).
`PabellonUNSA` hereda de `Pabellon`; `SistemaEvacuacion` agrega un `Pabellon` y
un `Planificador`.

## 2. Diagrama de estados — SistemaEvacuacion

![Estados del sistema](VERA-estados-sistema.png)

Ciclo de vida `INACTIVO → ALERTA → EVACUANDO → FINALIZADO` (tipo `EstadoSist`).
Durante `EVACUANDO`, `bloquearTramo` y `confirmarEvacuada` son transiciones
internas (reasignación y liberación de capacidad).

## 3. Diagrama de estados — Aula

![Estados del aula](VERA-estados-aula.png)

Estados de evacuación de cada aula (tipo `EstadoAula`).

---

## Cómo regenerar los PNG

```sh
# requiere Java + Graphviz (dot); plantuml.jar se descarga una vez
java -jar plantuml.jar -tpng *.puml
```
O con la extensión **PlantUML** de VS Code: abrir el `.puml` → `Alt+D` para
previsualizar, exportar a PNG/SVG.

---

## Versiones Mermaid (editables sin PlantUML)

### Estados del sistema
```mermaid
stateDiagram-v2
    [*] --> INACTIVO
    INACTIVO --> ALERTA : activarAlerta()
    ALERTA --> EVACUANDO : asignarRutas()
    EVACUANDO --> EVACUANDO : bloquearTramo(tid)
    EVACUANDO --> EVACUANDO : confirmarEvacuada(a)
    EVACUANDO --> FINALIZADO : finalizarEvacuacion() [I5]
    FINALIZADO --> [*]
```

### Estados del aula
```mermaid
stateDiagram-v2
    [*] --> PENDIENTE
    PENDIENTE --> EN_TRANSITO : asignarRutas() [ruta<>nil]
    PENDIENTE --> SIN_RUTA : asignarRutas() [ruta=nil]
    PENDIENTE --> EVACUADA : asignarRutas() [ocupacion=0]
    EN_TRANSITO --> EN_TRANSITO : bloquearTramo() [reasignada]
    EN_TRANSITO --> SIN_RUTA : bloquearTramo() [sin alternativa]
    EN_TRANSITO --> EVACUADA : confirmarEvacuada()
    EVACUADA --> [*]
```

### Clases (resumen)
```mermaid
classDiagram
    class Tipos
    class Pabellon
    class PabellonUNSA
    class Planificador
    class SistemaEvacuacion
    class GeneradorPabellon
    PabellonUNSA --|> Pabellon
    Planificador o--> Pabellon
    SistemaEvacuacion o--> Pabellon
    SistemaEvacuacion o--> Planificador
    GeneradorPabellon ..> Pabellon : crea
    Pabellon ..> Tipos : usa
    Planificador ..> Tipos : usa
    SistemaEvacuacion ..> Tipos : usa
```

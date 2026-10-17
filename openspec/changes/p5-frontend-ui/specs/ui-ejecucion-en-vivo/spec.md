## ADDED Requirements

### Requirement: Estado derivado de eventos
El estado de la UI SHALL derivarse de un reductor puro sobre los eventos, idéntico en vivo y en replay; el replay solo se distingue por una insignia «Replay» (RF-F1-35, RF-F3-03).

#### Scenario: Reproducir eventos guardados
- **WHEN** se reproducen los eventos de un run ya terminado
- **THEN** la UI queda idéntica a la del run en vivo

### Requirement: Reconexión del SSE
La UI SHALL mostrar estados vacío, cargando y error, y reconectarse al SSE con `Last-Event-ID` (RF-F1-36).

#### Scenario: Corte de red de 5 s
- **WHEN** se corta la red 5 s y se restaura
- **THEN** el stream se reanuda sin pantalla en blanco

### Requirement: Grafo vivo de agentes
El grafo SHALL mostrar Supervisor, Riesgo, Personal y Equipo con su estado (inactivo, trabajando, completado, error) y las herramientas invocadas (RF-F1-31).

#### Scenario: Paralelismo visible
- **WHEN** Personal y Equipo trabajan a la vez
- **THEN** ambos nodos se ven en «trabajando» al mismo tiempo

### Requirement: Semáforo y evidencia
Cada control y requisito SHALL mostrar icono y texto de su estado, si es bloqueante y la insignia «simulado» según su fuente; al elegir un requisito SHALL abrirse un cajón con la evidencia, el agente que lo verificó, la fuente y los incidentes similares (RF-F1-32, RF-F1-33, RT-07).

#### Scenario: CUMPLE con evidencia
- **WHEN** el usuario abre un requisito `CUMPLE`
- **THEN** ve al menos una evidencia y quién la verificó

## ADDED Requirements

### Requirement: Reparto de requisitos
El Supervisor SHALL convertir los controles en `RequisitoAVerificar` y enviar cada requisito exactamente una vez: `competencia` al Agente Personal, `equipo` al Agente Equipo; `condicion_campo` SHALL quedar `NO_VERIFICABLE` en la primera pasada (RF-F1-11).

#### Scenario: Cada requisito una sola vez
- **WHEN** se reparten los requisitos de E1
- **THEN** cada requisito aparece en exactamente un `AgenteSolicitud`

### Requirement: Personal y Equipo en paralelo
Los agentes Personal y Equipo SHALL ejecutarse en paralelo con `asyncio.gather` (RF-F1-12).

#### Scenario: Tiempo total
- **WHEN** cada agente tarda 1 s simulado
- **THEN** el reparto completo tarda cerca de 1 s, no 2 s

### Requirement: Secuencia de eventos de E1
El Supervisor SHALL emitir, en orden, `run.iniciado`, los eventos de agentes, `supervisor.consolidado`, `plan.listo` y `humano.decision_requerida` (RF-F1-05, RF-F1-17, RF-F1-18).

#### Scenario: Orden de E1
- **WHEN** se corre E1 en modo fake
- **THEN** los tipos de evento siguen ese orden

### Requirement: Fallo de agente sin falso CUMPLE
Si un agente falla (excepción, tiempo límite o salida inválida), el Supervisor SHALL marcar sus requisitos `NO_VERIFICABLE` o emitir `run.error`, y el run no SHALL quedar colgado (RF-F1-06, RF-F1-07).

#### Scenario: Agente que lanza excepción
- **WHEN** `verificar_equipo` lanza una excepción
- **THEN** sus requisitos quedan `NO_VERIFICABLE` o el run termina en `ERROR`

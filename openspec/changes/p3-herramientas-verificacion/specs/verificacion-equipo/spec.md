## ADDED Requirements

### Requirement: Herramientas deterministas de equipo
Las herramientas de Equipo SHALL verificar la disponibilidad en el turno, el `EstadoEquipo` y el tipo requerido; los `tipos_equivalentes` SHALL usarse solo cuando `permitir_equivalencias` sea verdadero (RF-F1-14, RT-06).

#### Scenario: Equipo en mantenimiento
- **WHEN** el equipo asignado está en `mantenimiento`
- **THEN** el requisito queda `NO_CUMPLE` con la evidencia del registro del equipo

#### Scenario: Primera pasada estricta
- **WHEN** solo hay un equipo equivalente disponible y `permitir_equivalencias` es falso
- **THEN** el requisito queda `NO_CUMPLE`

### Requirement: Resultado con evidencia y traza
El Agente Equipo SHALL devolver `ResultadoRequisito` con evidencia y emitir `agente.herramienta` por cada llamada (RF-F1-15, RF-F1-16).

#### Scenario: Traza visible
- **WHEN** el agente consulta el estado de un equipo
- **THEN** se emite `agente.herramienta` con nombre, entrada, salida resumida y duración

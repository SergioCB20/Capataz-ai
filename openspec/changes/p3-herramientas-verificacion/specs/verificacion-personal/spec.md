## ADDED Requirements

### Requirement: Herramientas deterministas de personal
Las herramientas de Personal SHALL listar el personal disponible en un `TurnoRef`, verificar la vigencia de cada certificación a la fecha del turno y detectar la doble asignación en el mismo turno (RF-F1-13).

#### Scenario: Certificación vencida
- **WHEN** la certificación requerida vence antes de la fecha del turno
- **THEN** la persona no cuenta como competente y el requisito queda `NO_CUMPLE`

#### Scenario: Doble asignación
- **WHEN** la misma persona está asignada a otra tarea en el mismo turno
- **THEN** el requisito queda `NO_CUMPLE` con esa evidencia

### Requirement: Resultado con evidencia y traza
El Agente Personal SHALL devolver un `ResultadoRequisito` con `Evidencia` y `verificado_por` por cada requisito, y emitir `agente.herramienta` con `TraceHerramienta` por cada llamada; un resultado `CUMPLE` sin evidencia SHALL rechazarse (RF-F1-15, RF-F1-16).

#### Scenario: CUMPLE sin evidencia
- **WHEN** una herramienta produce `CUMPLE` sin evidencia
- **THEN** el agente lo convierte en `NO_VERIFICABLE`

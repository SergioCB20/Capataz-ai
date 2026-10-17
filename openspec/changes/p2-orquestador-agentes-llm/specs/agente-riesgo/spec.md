## ADDED Requirements

### Requirement: Controles solo del catálogo
El Agente Riesgo SHALL devolver una `EvaluacionRiesgo` cuyos IDs de control pertenezcan al catálogo y apliquen al tipo de tarea; los IDs inventados SHALL descartarse (RF-F1-10).

#### Scenario: Descripción ambigua
- **WHEN** la descripción de la tarea es ambigua
- **THEN** los IDs de control devueltos son un subconjunto del catálogo

### Requirement: Incidentes similares verificados
Cada `PeligroDetectado` SHALL incluir `incidentes_similares` con IDs devueltos por `buscar_incidentes`; los incidentes pueden sumar controles adicionales del catálogo, nunca controles inventados (RF-F1-10, RF-F1-19).

#### Scenario: ID de incidente inexistente
- **WHEN** el LLM cita un incidente que no existe
- **THEN** ese ID se descarta y no aparece en el resultado

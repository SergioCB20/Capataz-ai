## ADDED Requirements

### Requirement: Reporte de detección
El script `evaluar` SHALL ejecutar los casos de `data/evaluacion.json` con herramientas reales y LLM fake, y reportar el % de fallas inyectadas detectadas, los falsos positivos y las fallas por tipo, separando «detectado por checklist base» de «detectado por incidentes», en tabla y JSON (RF-F3-21).

#### Scenario: Reporte reproducible
- **WHEN** se ejecuta `evaluar` dos veces seguidas
- **THEN** ambos reportes son idénticos

### Requirement: Métrica sobre datos simulados
El reporte SHALL indicar que la métrica se calcula sobre datos simulados (RF-F3-22).

#### Scenario: Encabezado del reporte
- **WHEN** se genera el reporte
- **THEN** su encabezado dice que los datos son simulados

## ADDED Requirements

### Requirement: Búsqueda determinista de incidentes
`buscar_incidentes(equipo, actividad, riesgo_critico)` SHALL devolver como máximo 5 incidentes del catálogo ordenados por relevancia y `nivel_potencial`, sin usar el LLM (RF-F1-19).

#### Scenario: Sostenimiento en roca inestable
- **WHEN** se busca con la actividad de sostenimiento en roca inestable
- **THEN** los primeros resultados son incidentes de caída de rocas

#### Scenario: Límite de resultados
- **WHEN** coinciden más de 5 incidentes
- **THEN** se devuelven solo 5

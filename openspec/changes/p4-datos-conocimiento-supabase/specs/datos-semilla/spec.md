## ADDED Requirements

### Requirement: Seeds mínimos válidos
`data/*.json` SHALL contener al menos 3 peligros, 4 tipos de tarea, 6 controles (con `bloqueante`, `aplica_a` y `fuente`), 8 personas con certificaciones y vigencias, 8 equipos con estado y los escenarios E1, E2, E2c y E3, todo marcado como simulado salvo la normativa real (RF-F0-09, RT-07).

#### Scenario: Referencias cruzadas
- **WHEN** se cargan los seeds
- **THEN** cada escenario referencia solo IDs existentes

### Requirement: Escenarios con resultado esperado
Cada escenario SHALL producir su resultado esperado: E1 `RECOMENDADO`, E2 `BLOQUEADO` con al menos una alternativa verificable, E2c `REQUIERE_CAMPO` y E3 `BLOQUEADO` sin alternativa segura y con escalamiento.

#### Scenario: E2 tiene salida
- **WHEN** se evalúa E2 permitiendo equivalencias
- **THEN** existe al menos una combinación de equipo y personal que cumple los bloqueantes

### Requirement: Conjunto de evaluación
`data/evaluacion.json` SHALL tener al menos 15 casos con la falla inyectada, incluir casos limpios y al menos 3 casos detectables solo por el patrón de incidentes; el resultado esperado SHALL fijarlo el equipo, no el LLM (RF-F3-20).

#### Scenario: Caso con falla inyectada
- **WHEN** se lee un caso de evaluación
- **THEN** indica qué falla se inyectó y su resultado esperado

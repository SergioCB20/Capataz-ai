## ADDED Requirements

### Requirement: Guion de demo
El equipo SHALL tener un guion de 5 minutos como máximo: problema con dato fuente, E1 rápido, E2 completo, E3 breve, y métrica con sus límites (datos simulados), indicando quién habla y qué clic hace (RF-F3-40, RF-F3-22).

#### Scenario: Ensayo
- **WHEN** se ensaya con cronómetro
- **THEN** la demo dura 5 minutos o menos

### Requirement: Checklist y plan B
El equipo SHALL tener un checklist previo (backend arrancado, frontend local, `VITE_API_URL`, CORS probado, Supabase despierto o `memory`, `LLM_MODE`, replays) y un plan B documentado (RF-F3-41, RF-F3-42).

#### Scenario: Falla la red en la sala
- **WHEN** no hay Internet al empezar la demo
- **THEN** el plan B indica pasar a replay con `STORE_BACKEND=memory`

### Requirement: Material para la rúbrica
El equipo SHALL preparar una sección o slide por criterio de la rúbrica con evidencia mostrable (RF-F3-44).

#### Scenario: Cobertura de criterios
- **WHEN** se revisa el material
- **THEN** cada criterio tiene al menos un ejemplo concreto

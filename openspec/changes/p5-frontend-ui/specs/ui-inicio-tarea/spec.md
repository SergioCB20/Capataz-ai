## ADDED Requirements

### Requirement: Inicio de tarea
La pantalla de inicio SHALL ofrecer presets E1, E2, E2c y E3 que rellenan el formulario, un modo libre (tipo de tarea, descripción, zona, turno) y un selector vivo/replay (RF-F1-30).

#### Scenario: Iniciar E1 en dos clics
- **WHEN** el usuario pulsa «Escenario 1» y luego «Evaluar»
- **THEN** se crea el run y la vista pasa a la ejecución en vivo

### Requirement: Textos en español
Todos los textos visibles SHALL estar en español y usar el vocabulario del sector (RF-F3-14).

#### Scenario: Revisión de textos
- **WHEN** se recorre la UI completa
- **THEN** no hay textos en inglés visibles para el usuario

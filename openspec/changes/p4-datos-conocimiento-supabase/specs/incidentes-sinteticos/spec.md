## ADDED Requirements

### Requirement: Incidentes sintéticos versionados
`data/incidentes.json` SHALL contener al menos 50 incidentes sintéticos con los campos mínimos de RF-F0-16, todos con `fuente.tipo = simulado`, y al menos 3 por cada tipo de tarea del catálogo (RF-F0-16).

#### Scenario: Cobertura por tipo de tarea
- **WHEN** se cuentan los incidentes por tipo de tarea
- **THEN** cada tipo tiene al menos 3

### Requirement: Generador reproducible con revisión humana
`scripts/gen_sintetico.py` SHALL generar borradores con semilla fija y temperatura baja; una persona SHALL revisarlos antes de versionarlos, y el sistema no SHALL regenerarlos durante la demo (RF-F0-17).

#### Scenario: Sin citas inventadas
- **WHEN** se revisa la salida del generador
- **THEN** no contiene citas normativas y todo está marcado como simulado

### Requirement: Estructura de Kaggle sin inventar columnas
El modelo `Incidente` SHALL basarse en las columnas reales del dataset de Kaggle cuando el CSV esté disponible; mientras no lo esté, las columnas SHALL figurar como «POR VERIFICAR» (RF-F0-16).

#### Scenario: CSV disponible
- **WHEN** el CSV está en `data/referencia/`
- **THEN** los campos del modelo se ajustan a sus cabeceras reales

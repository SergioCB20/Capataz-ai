## ADDED Requirements

### Requirement: Vista de conflicto y alternativas
La UI SHALL mostrar el control en conflicto con su causa y evidencia, y las alternativas en tarjetas lado a lado con cambios, veredicto (verificada o falló, con motivo), explicación e indicador de ronda (RF-F2-30, RF-F2-35).

#### Scenario: E2 con alternativas
- **WHEN** se corre E2
- **THEN** se ven al menos 2 alternativas y al menos una verificada

### Requirement: Comparación de planes
La UI SHALL mostrar el «Plan (PTW borrador)» con un diff de asignaciones frente al plan original (RF-F2-31, RF-F1-18).

#### Scenario: Cambio identificable
- **WHEN** el usuario mira la comparación
- **THEN** identifica qué persona o equipo cambió y por qué

### Requirement: Confirmación de campo
Para E2c la UI SHALL mostrar una pregunta por requisito con Sí/No y nota, y actualizar el semáforo sin recargar (RF-F2-32).

#### Scenario: Enviar confirmaciones
- **WHEN** el usuario confirma todas las preguntas
- **THEN** el semáforo y el estado del plan se actualizan

### Requirement: Decisión humana
La barra de decisión SHALL ofrecer Aprobar y Rechazar con comentario obligatorio; con un plan `BLOQUEADO` SHALL ofrecer solo Rechazar y mostrar el motivo y el escalamiento sugerido (RF-F1-34, RF-F2-33, RT-04).

#### Scenario: Plan bloqueado
- **WHEN** el plan es `BLOQUEADO`
- **THEN** el botón Aprobar no existe o está deshabilitado con explicación

### Requirement: Línea de tiempo de auditoría
La UI SHALL listar los eventos clave con actor y hora, y permitir exportar la auditoría (RF-F2-34, RF-F3-30).

#### Scenario: Recorrer E2
- **WHEN** termina E2
- **THEN** la línea de tiempo muestra conflicto, alternativas y decisión

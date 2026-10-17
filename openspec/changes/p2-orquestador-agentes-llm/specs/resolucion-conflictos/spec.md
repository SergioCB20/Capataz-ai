## ADDED Requirements

### Requirement: Detección de conflicto
Si algún control bloqueante queda `NO_CUMPLE`, el Supervisor SHALL emitir `conflicto.detectado` con control, requisito, causa y evidencia (RF-F2-01).

#### Scenario: Equipo en mantenimiento
- **WHEN** en E2 el equipo requerido está en `mantenimiento`
- **THEN** se emite `conflicto.detectado` con la evidencia del registro del equipo

### Requirement: Alternativas verificadas con herramientas
Las alternativas propuestas por el LLM SHALL referenciar solo IDs del catálogo, no quitar requisitos, y re-verificarse con Personal y Equipo permitiendo equivalencias; el veredicto SHALL venir de las herramientas, no del LLM (RF-F2-02, RF-F2-03, RF-F2-05, RT-01).

#### Scenario: Alternativa que el LLM cree válida
- **WHEN** una alternativa falla la verificación de herramientas
- **THEN** queda con `cumple_bloqueantes = false` y su motivo

### Requirement: Máximo dos rondas
La resolución SHALL tener como máximo 2 rondas; en la ronda 2 el LLM recibe los motivos de fallo de la ronda 1 (RF-F2-04, RT-06).

#### Scenario: Sin ronda 3
- **WHEN** ninguna alternativa pasa en la ronda 2
- **THEN** no se generan más alternativas

### Requirement: Plan con cambios o bloqueo con escalamiento
Con al menos una alternativa verificada, el Supervisor SHALL armar el plan con los cambios aplicados; sin ninguna tras 2 rondas, SHALL emitir un plan `BLOQUEADO` con motivo y escalamiento, y `humano.decision_requerida` con `solo_rechazo = true` (RF-F2-06, RF-F2-07, RF-F2-21).

#### Scenario: E3 sin alternativa segura
- **WHEN** se corre E3
- **THEN** el plan queda `BLOQUEADO` con recomendación de escalamiento

### Requirement: Explicación separada del veredicto
Cada alternativa SHALL llevar una explicación del LLM en un campo distinto del veredicto determinista (RF-F2-08).

#### Scenario: Campos distintos
- **WHEN** se emite `conflicto.alternativa_verificada`
- **THEN** `explicacion` y `cumple_bloqueantes` vienen en campos separados

### Requirement: Condiciones de campo
Si solo quedan requisitos `NO_VERIFICABLE` sin incumplimientos bloqueantes, el Supervisor SHALL emitir `humano.campo_requerido`; `confirmar_campo` SHALL recalcular el estado y, ante un «no se cumple», entrar al flujo de conflicto (RF-F2-10, RF-F2-11).

#### Scenario: Confirmar todo en E2c
- **WHEN** se confirman todas las preguntas de campo de E2c
- **THEN** el plan pasa a `RECOMENDADO`

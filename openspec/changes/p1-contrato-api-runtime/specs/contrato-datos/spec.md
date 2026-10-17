## ADDED Requirements

### Requirement: Contrato único de datos
El sistema SHALL definir todos los modelos, enums y eventos compartidos en `backend/app/contract.py`, con los nombres fijados en los acuerdos de interfaz del diseño (RF-F0-02).

#### Scenario: Tests del contrato en verde
- **WHEN** se ejecuta `pytest backend`
- **THEN** los tests de `test_contract.py` pasan

### Requirement: Consolidación con tres estados
`consolidar_control` SHALL devolver el peor estado entre los requisitos de un control, y un requisito sin resultado SHALL contar como `NO_VERIFICABLE`, nunca como `CUMPLE` (RT-02).

#### Scenario: Gana el peor estado
- **WHEN** un control tiene un requisito `CUMPLE` y otro `NO_CUMPLE`
- **THEN** el control queda `NO_CUMPLE`

#### Scenario: Requisito sin resultado
- **WHEN** un requisito del control no tiene `ResultadoRequisito`
- **THEN** el control no puede quedar `CUMPLE`

### Requirement: Estado del plan
`calcular_estado_sistema` SHALL devolver `BLOQUEADO` si algún control bloqueante es `NO_CUMPLE`, `REQUIERE_CAMPO` si hay algún `NO_VERIFICABLE` y `RECOMENDADO` en otro caso (RT-03).

#### Scenario: Control bloqueante incumplido
- **WHEN** un control con `bloqueante = true` queda `NO_CUMPLE`
- **THEN** el estado del sistema es `BLOQUEADO`

### Requirement: Payload validado por tipo de evento
Cada `Evento` SHALL tener un payload válido según `PAYLOAD_POR_TIPO`, comprobable con `validar_payload` (RF-F1-02).

#### Scenario: Payload inválido
- **WHEN** se valida un evento `plan.listo` sin `plan`
- **THEN** `validar_payload` lanza un error

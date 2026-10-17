## ADDED Requirements

### Requirement: Interfaz Store intercambiable
El dominio SHALL depender solo de la interfaz `Store`; `MemoryStore` SHALL implementarla con volcado JSONL (RF-F0-06).

#### Scenario: Misma suite para ambas implementaciones
- **WHEN** se corre la suite de `Store` contra `MemoryStore`
- **THEN** todas las pruebas pasan, y la misma suite sirve para `SupabaseStore`

### Requirement: Evento persistido antes de emitirse
`emitir` SHALL asignar un `seq` monótono por run sin huecos, persistir el evento y solo después publicarlo al SSE (RT-05, RF-F1-02).

#### Scenario: Secuencia sin huecos
- **WHEN** termina un run de E1
- **THEN** los `seq` van de 1 a N sin saltos

### Requirement: Idempotencia por run y secuencia
`agregar_evento` SHALL ser idempotente por `(run_id, seq)`.

#### Scenario: Reintento de un evento
- **WHEN** se agrega dos veces el mismo `(run_id, seq)`
- **THEN** solo queda un evento

### Requirement: Plan y decisión persistidos
El plan y la decisión SHALL guardarse en el `Store` (RF-F1-21).

#### Scenario: Run aprobado consultable
- **WHEN** se aprueba E1 y se consulta el run
- **THEN** el run trae el plan y la decisión

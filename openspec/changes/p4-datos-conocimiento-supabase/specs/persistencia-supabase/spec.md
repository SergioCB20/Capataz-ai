## ADDED Requirements

### Requirement: Esquema con RLS
La migración `supabase/migrations/0001_init.sql` SHALL crear las tablas del anexo de Supabase (incluida `incidentes`) con RLS activada y sin políticas para `anon` (RF-F0-04, RF-F0-14).

#### Scenario: Clave anónima
- **WHEN** se consulta `runs` con la clave `anon`
- **THEN** devuelve 0 filas o error

### Requirement: SupabaseStore
`SupabaseStore` SHALL implementar la interfaz `Store` acordada y pasar la misma suite que `MemoryStore` (RF-F0-06).

#### Scenario: Suite compartida
- **WHEN** se corre la suite de `Store` con `STORE_BACKEND=supabase`
- **THEN** todas las pruebas pasan

### Requirement: Cargador de seeds idempotente
`scripts/cargar_seeds.py` SHALL validar `data/*.json` con el contrato y hacer *upsert*; un JSON inválido SHALL abortar la carga (RF-F0-08).

#### Scenario: Carga repetida
- **WHEN** se ejecuta el cargador dos veces
- **THEN** no se duplican filas

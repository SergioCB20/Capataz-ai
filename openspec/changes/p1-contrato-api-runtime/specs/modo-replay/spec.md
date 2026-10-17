## ADDED Requirements

### Requirement: Grabar replays
Un comando SHALL exportar los eventos de un run a `replays/<escenario_id>.json` con la misma estructura `Evento` del SSE (RF-F3-01).

#### Scenario: Replay válido
- **WHEN** se graba el run de E2
- **THEN** cada evento del archivo pasa `validar_payload`

### Requirement: Reproducir sin red
`POST /api/runs` con `modo = "replay"` SHALL reproducir el archivo por SSE respetando los tiempos relativos, sin LLM ni Supabase, y aceptar decisiones simuladas (RF-F3-02, RF-F3-05, RT-08).

#### Scenario: Demo sin Internet
- **WHEN** la red está apagada y se pide el replay de E3
- **THEN** la UI recibe todos los eventos de E3 y se puede rechazar el plan sin error

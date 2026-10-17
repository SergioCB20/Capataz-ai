## 1. Contrato (prioridad máxima: subir a main ~15:10)

- [x] 1.1 Crear `backend/` con `uv`, FastAPI, Pydantic v2 y pytest (RF-F0-01)
- [x] 1.2 Escribir enums y modelos de `contract.py` según los acuerdos de interfaz (RF-F0-02)
- [x] 1.3 Implementar `consolidar_control`, `calcular_estado_sistema`, `PAYLOAD_POR_TIPO` y `validar_payload` (RT-02, RT-03)
- [x] 1.4 Subir `contract.py` a main y avisar al equipo
- [x] 1.5 Tests del contrato: peor estado, requisito faltante, bloqueado, payload inválido, rechazo sin comentario (RF-F0-02)

## 2. Store y arranque

- [ ] 2.1 `Store` (Protocol) y `MemoryStore` con volcado JSONL (RF-F0-06)
- [ ] 2.2 Carga del catálogo desde `data/*.json`, con un seed de juguete hasta que P4 suba el real (RF-F0-08)
- [ ] 2.3 `.env.example` con `OPENROUTER_API_KEY`, `LLM_MODEL`, `SUPABASE_URL=https://shjpypqcetndpokklycy.supabase.co`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL` (con la contraseña como marcador), `STORE_BACKEND`, `LLM_MODE`, `CORS_ORIGINS` (RF-F0-05)
- [ ] 2.4 `GET /api/health` y `GET /api/catalogo`; CORS desde `CORS_ORIGINS` (RF-F0-07, RF-F0-10, RF-F0-18)

## 3. Runs y eventos (hito 15:45: E1 de punta a punta)

- [ ] 3.1 `emitir`: `seq` monótono, persistir y luego publicar en una cola por run (RT-05)
- [ ] 3.2 `POST /api/runs` que lanza `ejecutar_run` de P2 en segundo plano; usar un stub mientras P2 no suba el suyo (RF-F1-01)
- [ ] 3.3 SSE `GET /api/runs/{id}/eventos` con `Last-Event-ID` y cierre correcto (RF-F1-03)
- [ ] 3.4 `GET /api/runs/{id}` (RF-F1-04)
- [ ] 3.5 Actualizar `EstadoRun` a partir de los eventos del orquestador (`plan.listo`, `humano.*`, `run.*`)

## 4. Decisión humana y campo (hito 16:20)

- [ ] 4.1 `POST /api/runs/{id}/decision` con 409/422 y bloqueado solo rechazo (RF-F1-20, RF-F2-20, RF-F2-22)
- [ ] 4.2 Guardar plan y decisión en el `Store` (RF-F1-21)
- [ ] 4.3 `POST /api/runs/{id}/campo` que llama a `confirmar_campo` de P2 (RF-F2-11)
- [ ] 4.4 Test de transiciones: un run terminal no acepta más decisiones ni confirmaciones (RF-F2-23)

## 5. Replay (hito 16:35)

- [ ] 5.1 Modo replay en `POST /api/runs` leyendo `replays/<escenario_id>.json` con factor de velocidad (RF-F3-02)
- [ ] 5.2 Decisiones simuladas en replay sin persistir en Supabase (RF-F3-05)
- [ ] 5.3 `scripts/grabar_replay.py` y grabar E1, E2, E2c y E3 junto con P2 (RF-F3-01, RF-F3-04)

## 6. Apoyo tras el congelamiento

- [ ] 6.1 Ayudar a P5 con la integración del SSE y con el checklist previo a la demo (RF-F3-41)

## 1. Arranque sin dependencias (desde el minuto 0)

- [x] 1.1 `backend/app/llm/client.py`: OpenRouter con `LLM_MODEL`, tiempo límite, un reintento y registro de uso (RF-F0-11)
- [x] 1.2 Modo `fake` con respuestas fijas por agente y escenario (E1, E2, E2c, E3) (RF-F0-11)
- [x] 1.3 `agents/_stubs.py` con `verificar_personal`, `verificar_equipo` y `buscar_incidentes` según las firmas acordadas

## 2. Agente Riesgo

- [x] 2.1 Prompt y *function calling* con `buscar_incidentes` como herramienta (RF-F1-10, RF-F1-19)
- [x] 2.2 Filtro post-LLM: controles e incidentes solo del catálogo (RF-F1-10)
- [x] 2.3 Test: descripción ambigua no produce controles inexistentes (RF-F1-10)

## 3. Supervisor (hito 15:45: E1 de punta a punta)

- [x] 3.1 `ejecutar_run`: derivar requisitos y repartirlos (RF-F1-11)
- [x] 3.2 Personal y Equipo con `asyncio.gather` y límites de tiempo (RF-F1-07, RF-F1-12)
- [x] 3.3 Consolidar con funciones del contrato y emitir `supervisor.consolidado` (RF-F1-17)
- [x] 3.4 Armar el `Plan` y emitir `plan.listo` + `humano.decision_requerida` (RF-F1-18)
- [x] 3.5 Fallo de agente ⇒ `NO_VERIFICABLE` o `run.error` (RF-F1-06)
- [x] 3.6 Test de integración de la secuencia de E1 en modo fake (RF-F1-05)
- [ ] 3.7 Cambiar stubs por los agentes reales de P3 en cuanto estén

## 4. Conflictos y campo (hito 16:20)

- [x] 4.1 `conflicto.detectado` con evidencia (RF-F2-01)
- [x] 4.2 Ronda de alternativas del LLM con filtro de IDs y de requisitos eliminados (RF-F2-02, RF-F2-05)
- [x] 4.3 Re-verificación con `permitir_equivalencias = True` y `conflicto.alternativa_verificada` (RF-F2-03)
- [x] 4.4 Ronda 2 con motivos de fallo; tope de 2 rondas (RF-F2-04)
- [x] 4.5 Plan con cambios (varias alternativas ⇒ `planes_alternativos`) o `BLOQUEADO` con escalamiento (RF-F2-06, RF-F2-07, RF-F2-21)
- [x] 4.6 Explicación separada del veredicto (RF-F2-08)
- [x] 4.7 `humano.campo_requerido` y `confirmar_campo` (RF-F2-10, RF-F2-11)

## 5. Cierre (hito 16:35)

- [ ] 5.1 Correr E1–E3 con el LLM real a temperatura baja y grabar los replays con P1 (RF-F3-04)
- [ ] 5.2 (Opcional) Resumen ejecutivo de ≤ 3 líneas a partir de datos verificados (RF-F3-11)

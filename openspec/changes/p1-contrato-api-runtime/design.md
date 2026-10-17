## Context

Cinco personas trabajan en paralelo durante ~2 h. El contrato (`contract.py`) es la única dependencia real entre frentes. Para que nadie lo espere, este documento **congela los nombres y firmas** desde el minuto 0: cada quien programa contra ellos y P1 los materializa en código.

## Goals / Non-Goals

**Goals:**
- Fijar la interfaz compartida (sección «Acuerdos de interfaz»).
- Backend que corre E1–E3 con `STORE_BACKEND=memory` y `LLM_MODE=fake`.
- Eventos persistidos antes de emitirse; SSE que reconstruye el estado al recargar.

**Non-Goals:**
- Lógica de agentes, herramientas o LLM (P2, P3).
- `SupabaseStore` y migración SQL (P4).
- Autenticación de usuarios finales.

## Decisions

- **Contrato primero, en un solo archivo.** `contract.py` contiene modelos y funciones puras (`consolidar_control`, `calcular_estado_sistema`, `validar_payload`). Alternativa descartada: un paquete de modelos por frente, porque multiplica los puntos de choque.
- **El orquestador recibe una función `emitir`.** P1 implementa `emitir` (asigna `seq`, persiste y publica al SSE); P2 solo la llama. Así P2 no conoce ni el `Store` ni FastAPI.
- **SSE con `sse-starlette` o `StreamingResponse`.** Reenvía lo persistido desde `Last-Event-ID` y luego lo nuevo mediante una cola `asyncio` por run.
- **Replay en el mismo endpoint.** `POST /api/runs` con `modo="replay"` lee `replays/<escenario_id>.json` y emite los eventos con sus tiempos relativos; el frontend no distingue.

## Acuerdos de interfaz (congelados)

> Cambiar algo de esta sección requiere avisar a todo el equipo. Agregar campos opcionales sí se permite sin avisar.

### Estructura de archivos

```
backend/app/contract.py            P1
backend/app/api/main.py            P1  (FastAPI, rutas, SSE, CORS)
backend/app/store/base.py          P1  (Protocol Store)
backend/app/store/memory.py        P1
backend/app/store/supabase_store.py P4
backend/app/llm/client.py          P2
backend/app/agents/riesgo.py       P2
backend/app/agents/supervisor.py   P2  (ejecutar_run, confirmar_campo)
backend/app/agents/personal.py     P3
backend/app/agents/equipo.py       P3
backend/app/tools/*.py             P3
data/*.json, knowledge/*.md        P4
replays/<escenario_id>.json        P1 (grabados) · P5 (e1.json a mano, provisional)
frontend/                          P5
```

### Enums

- `EstadoControl`: `CUMPLE`, `NO_VERIFICABLE`, `NO_CUMPLE` (orden de gravedad creciente).
- `EstadoSistema`: `RECOMENDADO`, `REQUIERE_CAMPO`, `BLOQUEADO`.
- `EstadoRun`: `EVALUANDO`, `RESOLVIENDO_CONFLICTO`, `ESPERANDO_CAMPO`, `ESPERANDO_DECISION`, `APROBADA`, `RECHAZADA`, `BLOQUEADA`, `ERROR`. Terminales: `APROBADA`, `RECHAZADA`, `BLOQUEADA`, `ERROR`.
- `TipoRequisito`: `competencia`, `equipo`, `condicion_campo`.
- `EstadoEquipo`: `operativo`, `mantenimiento`, `fuera_servicio`.
- `TipoFuente`: `normativa`, `guia`, `simulado`.
- `TipoCambio`: `reprogramar_turno`, `equipo_equivalente`, `certificacion_equivalente`.

### Modelos (campos mínimos)

- `Fuente(tipo, referencia, url=None)`
- `TurnoRef(fecha: date, turno: "dia"|"noche")`
- `Requisito(id, tipo: TipoRequisito, descripcion, certificacion=None, tipo_equipo=None, pregunta_campo=None)`
- `Control(id, nombre, peligro_id, bloqueante: bool, aplica_a: list[str], requisitos: list[Requisito], fuente)`
- `Certificacion(codigo, vence: date)` · `Persona(id, nombre, rol, certificaciones, turnos: list[TurnoRef], fuente)`
- `Equipo(id, nombre, tipo_equipo, estado: EstadoEquipo, tipos_equivalentes: list[str], fuente)`
- `Incidente(id, fecha, planta, nivel_real, nivel_potencial, riesgo_critico, descripcion, equipo, actividad, tipo_tarea, causa_raiz, control_fallido, fuente)`
- `Asignacion(personas: list[str], equipos: list[str])`
- `Tarea(id, tipo_tarea, descripcion, zona, turno: TurnoRef, asignacion: Asignacion)` — la asignación es la propuesta original del supervisor de turno.
- `Escenario(id, nombre, tarea: Tarea, resultado_esperado: EstadoSistema, escalamiento: str|None)`
- `Catalogo(peligros, tipos_tarea, controles, personas, equipos, incidentes, escenarios)`
- `PeligroDetectado(peligro_id, justificacion, controles: list[str], incidentes_similares: list[str])` · `EvaluacionRiesgo(peligros: list[PeligroDetectado])`
- `RequisitoAVerificar(control_id, requisito: Requisito)`
- `AgenteSolicitud(agente, tarea: Tarea, requisitos: list[RequisitoAVerificar], permitir_equivalencias: bool)`
- `Evidencia(registro, campo, valor, fuente: Fuente)`
- `ResultadoRequisito(control_id, requisito_id, estado: EstadoControl, evidencia: list[Evidencia], verificado_por, detalle)`
- `ResultadoControl(control_id, bloqueante, estado, requisitos: list[ResultadoRequisito])`
- `TraceHerramienta(nombre, entrada: dict, salida_resumen: str, duracion_ms: int)`
- `Cambio(tipo: TipoCambio, desde, hacia, motivo)` · `Alternativa(id, ronda: 1|2, cambios, explicacion, cumple_bloqueantes: bool|None, motivo_fallo=None)`
- `Plan(id, run_id, estado_sistema, asignacion, cambios, resultados: list[ResultadoControl], escalamiento=None)`
- `DecisionHumana(plan_id, decision: "aprobar"|"rechazar", comentario=None, usuario)` — validador: rechazar exige comentario.
- `ConfirmacionesCampo(usuario, ts, respuestas: list[{requisito_id, cumple: bool, nota}])`
- `RunCrear(modo: "vivo"|"replay", escenario_id=None, tarea: Tarea|None)` · `RunCreado(run_id)` · `Run(id, estado, modo, tarea, plan=None, decision=None)`
- `Evento(run_id, seq, ts, tipo: TipoEvento, actor, payload: dict)`
- `CasoEvaluacion(id, tarea, falla_inyectada, detectable_por: "checklist"|"incidentes"|None, resultado_esperado: EstadoSistema)`

### Funciones del contrato

- `consolidar_control(control, resultados: list[ResultadoRequisito]) -> ResultadoControl` — gana el peor; requisito sin resultado ⇒ `NO_VERIFICABLE`.
- `calcular_estado_sistema(resultados: list[ResultadoControl]) -> EstadoSistema` — algún bloqueante `NO_CUMPLE` ⇒ `BLOQUEADO`; algún `NO_VERIFICABLE` ⇒ `REQUIERE_CAMPO`; si no ⇒ `RECOMENDADO`.
- `validar_payload(evento) -> None` — lanza si el payload no cumple `PAYLOAD_POR_TIPO`.

### Eventos (`TipoEvento`) y payload

| Tipo | Payload |
|---|---|
| `run.iniciado` | `{tarea}` |
| `agente.iniciado` | `{agente}` |
| `agente.herramienta` | `{agente, trace: TraceHerramienta}` |
| `agente.completado` | `{agente, resumen, resultados?: list[ResultadoRequisito], evaluacion?: EvaluacionRiesgo}` |
| `supervisor.consolidado` | `{resultados: list[ResultadoControl], estado_sistema}` |
| `conflicto.detectado` | `{control_id, requisito_id, causa, evidencia}` |
| `conflicto.alternativas` | `{ronda, alternativas: list[Alternativa]}` |
| `conflicto.alternativa_verificada` | `{alternativa: Alternativa}` |
| `plan.listo` | `{plan: Plan, planes_alternativos?: list[Plan]}` |
| `humano.campo_requerido` | `{preguntas: list[{requisito_id, pregunta}]}` |
| `humano.campo_confirmado` | `{confirmaciones: ConfirmacionesCampo}` |
| `humano.decision_requerida` | `{plan_id, solo_rechazo: bool}` |
| `humano.decision_tomada` | `{decision: DecisionHumana}` |
| `run.finalizado` | `{estado: EstadoRun}` |
| `run.error` | `{mensaje}` |

**Actores:** `capataz:agente-supervisor`, `capataz:agente-riesgo`, `capataz:agente-personal`, `capataz:agente-equipo`, `sistema`, `humano:<usuario>`.

### Firmas entre personas

```python
# P1 → P2
Emitir = Callable[[TipoEvento, str, dict], Awaitable[Evento]]   # (tipo, actor, payload)

# P2 (backend/app/agents/supervisor.py), llamado por P1
async def ejecutar_run(run: Run, catalogo: Catalogo, emitir: Emitir) -> Plan
async def confirmar_campo(run: Run, catalogo: Catalogo, conf: ConfirmacionesCampo, emitir: Emitir) -> Plan

# P3 (backend/app/agents/personal.py y equipo.py), llamados por P2
async def verificar_personal(sol: AgenteSolicitud, catalogo: Catalogo, emitir: Emitir) -> list[ResultadoRequisito]
async def verificar_equipo(sol: AgenteSolicitud, catalogo: Catalogo, emitir: Emitir) -> list[ResultadoRequisito]

# P3 (backend/app/tools/incidentes.py), llamado por P2 como herramienta del LLM
def buscar_incidentes(catalogo: Catalogo, equipo: str|None, actividad: str|None,
                      riesgo_critico: str|None, limite: int = 5) -> list[Incidente]

# P1 (backend/app/store/base.py), implementado por P1 (memoria) y P4 (Supabase)
class Store(Protocol):
    async def cargar_catalogo(self) -> Catalogo
    async def crear_run(self, run: Run) -> None
    async def leer_run(self, run_id: str) -> Run | None
    async def actualizar_run(self, run: Run) -> None
    async def agregar_evento(self, evento: Evento) -> None        # idempotente por (run_id, seq)
    async def listar_eventos(self, run_id: str, desde_seq: int = 0) -> list[Evento]
    async def guardar_plan(self, plan: Plan) -> None
    async def guardar_decision(self, run_id: str, decision: DecisionHumana) -> None
```

### API

| Método y ruta | Entrada → salida |
|---|---|
| `GET /api/health` | → `{store, llm_mode}` |
| `GET /api/catalogo` | → `Catalogo` |
| `POST /api/runs` | `RunCrear` → `RunCreado` |
| `GET /api/runs/{id}` | → `Run` |
| `GET /api/runs/{id}/eventos` | SSE de `Evento` (`id:` = `seq`) |
| `POST /api/runs/{id}/decision` | `DecisionHumana` → `Run` (409 / 422 según reglas) |
| `POST /api/runs/{id}/campo` | `ConfirmacionesCampo` → `Run` |

## Risks / Trade-offs

- [P1 tarda en publicar `contract.py`] → Los demás programan contra estos acuerdos; P1 sube primero los modelos y después los tests.
- [Cambios de última hora en el contrato rompen a otros] → Solo se agregan campos opcionales sin avisar; renombrar exige aviso.
- [El SSE se corta] → Reenvío desde `Last-Event-ID`; el frontend reconecta.

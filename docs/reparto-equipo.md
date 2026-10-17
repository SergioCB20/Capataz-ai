# Reparto del equipo (5 personas)

Cada persona tiene un cambio de OpenSpec con su propuesta, specs, diseño y tareas:

| Persona | Cambio (`openspec/changes/…`) | Qué entrega | Carpetas propias |
|---|---|---|---|
| **P1** | `p1-contrato-api-runtime` | `contract.py`, `Store` en memoria, API FastAPI + SSE, decisiones, campo, replay | `backend/app/contract.py`, `backend/app/api/`, `backend/app/store/base.py`, `backend/app/store/memory.py`, `scripts/grabar_replay.py` |
| **P2** | `p2-orquestador-agentes-llm` | Cliente LLM (OpenRouter + fake), Agente Riesgo, Supervisor, conflictos y alternativas | `backend/app/llm/`, `backend/app/agents/riesgo.py`, `backend/app/agents/supervisor.py` |
| **P3** | `p3-herramientas-verificacion` | Herramientas deterministas, Agentes Personal y Equipo, `buscar_incidentes`, script de evaluación | `backend/app/tools/`, `backend/app/agents/personal.py`, `backend/app/agents/equipo.py`, `scripts/evaluar.py` |
| **P4** | `p4-datos-conocimiento-supabase` | Seeds y escenarios, incidentes sintéticos, `knowledge/`, Supabase + `SupabaseStore`, guion de demo | `data/`, `knowledge/`, `supabase/`, `backend/app/store/supabase_store.py`, `scripts/gen_sintetico.py`, `scripts/cargar_seeds.py` |
| **P5** | `p5-frontend-ui` | Toda la UI, reductor de eventos, replay en el navegador, despliegue en Vercel | `frontend/`, `replays/e1.json` (a mano, provisional) |

**Regla de oro:** cada quien edita solo sus carpetas. Lo compartido se acuerda en la sección «Acuerdos de interfaz» de `openspec/changes/p1-contrato-api-runtime/design.md`.

## Cómo se evita esperar

- **Nadie espera a `contract.py`.** Los nombres de modelos, eventos, endpoints y firmas ya están fijados en los acuerdos de interfaz; cada quien programa contra esos nombres desde el minuto 0. P1 sube `contract.py` lo antes posible (objetivo: 15:10) y los demás solo cambian el `import`.
- **P2 no espera a P3:** usa *stubs* de `verificar_personal`/`verificar_equipo`/`buscar_incidentes` con la firma acordada que devuelven `NO_VERIFICABLE`.
- **P5 no espera al backend:** desarrolla contra `replays/e1.json` escrito a mano con los tipos de evento acordados.
- **P1 no espera a P4:** arranca con un seed mínimo de juguete en memoria; cuando P4 sube `data/*.json`, se cambia la ruta.
- **P3 no espera a P4:** escribe sus pruebas con *fixtures* pequeñas dentro de `tests/`.

## Hitos de integración (hora real)

| Hora | Hito | Quién integra |
|---|---|---|
| 14:50 | Todos leen los acuerdos de interfaz (5 min) y arrancan | Todos |
| 15:10 | `contract.py` en `main`; seed mínimo E1 en `data/` | P1, P4 |
| 15:45 | **E1 de punta a punta** con `LLM_MODE=fake` y `STORE_BACKEND=memory`, visto en la UI | P1 + P2 + P3 + P5 |
| 16:20 | **E2, E2c y E3** de punta a punta; evaluación base corriendo | Todos |
| 16:35 | Grabar los 4 replays desde corridas reales | P1 + P2 |
| 16:45 | **Congelamiento**: solo correcciones | Todos |
| 16:45–17:00 | Ensayo con el guion (P4 dirige) | Todos |

Si el tiempo no alcanza: **E1 + E2 + replay + evaluación base**. Lo primero que se corta está en la lista de recortes de `docs/requisitos/04-fase-3-ux-evaluacion-demo.md`.

## Ramas y commits

- Una rama por persona (`p1/…`, `p2/…`) y *merge* a `main` en cada hito; como cada quien toca carpetas distintas, no debería haber conflictos.
- Al terminar cada tarea, marcar su casilla en `tasks.md` (`- [x]`). `openspec list` muestra el avance de los 5 cambios.

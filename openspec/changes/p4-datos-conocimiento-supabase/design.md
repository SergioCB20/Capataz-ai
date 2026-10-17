## Context

Los datos se escriben contra los modelos de los acuerdos de interfaz (`p1-contrato-api-runtime/design.md`). Supabase es opcional para la demo: si falla, todo corre con `MemoryStore`.

## Goals / Non-Goals

**Goals:**
- Seed mínimo de E1 subido a las 15:10 para desbloquear a P1, P2 y P5.
- Escenarios diseñados para producir exactamente el resultado esperado.

**Non-Goals:**
- Lógica de verificación (P3) o de agentes (P2).
- Supabase Realtime y métricas (recortables).

## Decisions

- **Seed mínimo primero, completo después.** A las 15:10 basta con 1 tipo de tarea, 2 controles, 3 personas, 2 equipos y E1. El resto se agrega sin cambiar los IDs ya publicados.
- **Escenarios diseñados hacia atrás.** Para cada escenario se escribe primero el resultado esperado y luego los datos que lo provocan:
  - E1: todo vigente y operativo ⇒ `RECOMENDADO`.
  - E2: equipo asignado en `mantenimiento` y persona sin certificación vigente; existe un equipo equivalente y una persona certificada en otro turno ⇒ `BLOQUEADO` → alternativa → `RECOMENDADO`.
  - E2c: todo cumple salvo un requisito `condicion_campo` ⇒ `REQUIERE_CAMPO`.
  - E3: ningún equivalente ni persona certificada disponible ⇒ `BLOQUEADO`, con a quién escalar.
- **Incidentes con generador, revisados a mano.** `gen_sintetico.py` (semilla fija, temperatura baja) produce borradores; una persona los revisa antes de versionarlos. El resultado esperado de la evaluación lo fija el equipo, no el LLM.
- **Proyecto existente.** Se usa `shjpypqcetndpokklycy`; no se crea otro. La conexión directa puede ser solo IPv6, así que se tiene a mano la cadena del pooler IPv4.
- **Supabase guarda jsonb.** Tablas con `id` + `data jsonb` + pocas columnas para consultar, según `docs/requisitos/90-anexo-supabase.md`.

## Risks / Trade-offs

- [Las columnas reales de Kaggle no se conocen] → Bajar el CSV a `data/referencia/`, leer cabeceras y ajustar; si no hay tiempo, usar los campos mínimos de RF-F0-16.
- [Un PDF no tiene texto seleccionable] → Se resume solo lo verificable o se omite; nunca se inventan citas.
- [Supabase pausado o lento en la sala] → `STORE_BACKEND=memory`.

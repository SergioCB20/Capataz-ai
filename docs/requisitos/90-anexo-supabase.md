# Anexo — Supabase en CAPATAZ

## Decisión

Supabase (Postgres) es la **persistencia** de catálogo, runs, eventos (auditoría), planes y decisiones. **No** reemplaza el flujo en vivo ni la red de seguridad de la demo:

| Función | Tecnología | Motivo |
|---|---|---|
| Datos de catálogo, runs, auditoría, decisiones | **Supabase / Postgres** | Persistencia real, consultable con SQL, base para historial y métricas. |
| Flujo en vivo hacia la UI | **SSE desde FastAPI** (local) | El contrato de eventos ya está definido; el backend es la única fuente de `seq`. Corre en local, así que no depende de los límites de Vercel. |
| Demo sin red | **Replay + `MemoryStore`** | RT-08: la demo no puede depender de Internet ni de un proyecto en la nube. |
| Historial en vivo (opcional) | Supabase Realtime | Solo `RF-F3-32`; no es necesario para el núcleo. |

**Qué no se usa:** Supabase Auth de usuarios finales (el MVP no tiene login), Storage, Edge Functions, `pgvector` (la base de conocimiento va en contexto y los incidentes se filtran con la herramienta determinista `buscar_incidentes`, sin búsqueda vectorial).

## Proyecto

El proyecto **ya existe**; no se crea otro.

| Dato | Valor |
|---|---|
| Referencia | `shjpypqcetndpokklycy` |
| `SUPABASE_URL` | `https://shjpypqcetndpokklycy.supabase.co` |
| `DATABASE_URL` (conexión directa) | `postgresql://postgres:<CONTRASEÑA>@db.shjpypqcetndpokklycy.supabase.co:5432/postgres` |

- La contraseña y la `service_role` van **solo** en `.env` y se comparten por canal privado (RT-09).
- La conexión directa (`db.<ref>.supabase.co:5432`) puede ser **solo IPv6**. Si la red no tiene IPv6 (habitual en redes de eventos), usar la cadena del **pooler** («Session pooler», compatible con IPv4) que da el panel en *Connect*. Verificar antes de la demo.
- La migración se aplica con `psql "$DATABASE_URL" -f supabase/migrations/0001_init.sql` o pegándola en el SQL Editor del panel.

## Principio de datos

El **contrato Pydantic es la fuente de verdad**. Las tablas guardan los objetos del contrato como `jsonb` con unas pocas columnas relacionales para consultar y ordenar. Así un cambio de campo no exige migrar SQL y los datos siempre se validan con Pydantic al leer y al escribir.

## Esquema inicial (`supabase/migrations/0001_init.sql`)

```sql
-- Catálogo (objetos del contrato guardados como jsonb)
create table if not exists peligros     (id text primary key, data jsonb not null);
create table if not exists tipos_tarea  (id text primary key, data jsonb not null);
create table if not exists controles    (id text primary key, peligro_id text not null, bloqueante boolean not null default true, data jsonb not null);
create table if not exists personas     (id text primary key, data jsonb not null);
create table if not exists equipos      (id text primary key, tipo_equipo text not null, data jsonb not null);
create table if not exists escenarios   (id text primary key, data jsonb not null);
create table if not exists incidentes   (id text primary key, tipo_tarea_id text not null, data jsonb not null);

-- Ejecución
create table if not exists runs (
  id          text primary key,
  estado      text not null,                 -- EstadoRun
  modo        text not null default 'vivo',  -- 'vivo' | 'replay'
  escenario_id text,
  tarea       jsonb not null,
  creado_en   timestamptz not null default now(),
  actualizado_en timestamptz not null default now()
);

create table if not exists eventos (         -- auditoría: el flujo de eventos persistido
  run_id  text not null references runs(id) on delete cascade,
  seq     integer not null,
  ts      timestamptz not null,
  tipo    text not null,                     -- TipoEvento
  actor   text not null,
  payload jsonb not null,
  primary key (run_id, seq)                  -- idempotencia al reintentar
);
create index if not exists eventos_tipo_idx on eventos (tipo);

create table if not exists planes (
  id     text primary key,
  run_id text not null references runs(id) on delete cascade,
  estado_sistema text not null,              -- EstadoSistema
  data   jsonb not null
);

create table if not exists decisiones (
  id        bigint generated always as identity primary key,
  run_id    text not null references runs(id) on delete cascade,
  plan_id   text not null,
  decision  text not null check (decision in ('aprobar','rechazar')),
  comentario text,
  usuario   text not null default 'supervisor',
  ts        timestamptz not null default now(),
  check (decision <> 'rechazar' or length(trim(coalesce(comentario,''))) > 0)
);

-- Futuro: no se crea en el MVP (hoja de ruta NANDA, ver 05-hoja-de-ruta-nanda.md)
-- create table if not exists agent_registry (id text primary key, data jsonb not null);

-- Seguridad: RLS activada, sin políticas para anon/authenticated.
-- El backend usa la service_role key (que ignora RLS) y nunca la expone al navegador.
alter table peligros enable row level security;
alter table tipos_tarea enable row level security;
alter table controles enable row level security;
alter table personas enable row level security;
alter table equipos enable row level security;
alter table escenarios enable row level security;
alter table incidentes enable row level security;
alter table runs enable row level security;
alter table eventos enable row level security;
alter table planes enable row level security;
alter table decisiones enable row level security;
-- alter table agent_registry enable row level security;  -- futuro
```

## Reglas de uso

1. **Solo el backend habla con Supabase.** El frontend consume `/api/*`. Evita exponer claves y reglas de acceso. El «ciclo cerrado» del diagrama (eventos, plan y decisión guardados) también pasa por la API: Frontend → FastAPI → `Store` → Supabase.
2. **`SUPABASE_SERVICE_ROLE_KEY` nunca va al frontend ni al repositorio** (RT-09). Si se llega a necesitar acceso desde el navegador (p. ej. Realtime), se hace con la clave pública y políticas de solo lectura explícitas.
3. **Eventos inmutables:** solo `insert`; sin `update`/`delete` desde el código de aplicación.
4. **Idempotencia:** `(run_id, seq)` como clave primaria; reintentar un evento no duplica.
5. **Interfaz `Store`** con `SupabaseStore` y `MemoryStore` (RF-F0-06): todo el código de dominio depende de la interfaz.
6. **Seeds** versionados en `data/*.json` y cargados con el script idempotente (RF-F0-08); la base puede recrearse en minutos.
7. **Tiempos:** llamadas a Supabase con *timeout* corto; si falla durante un run, se continúa en memoria y se avisa (el run no se pierde).

## Para verificar al configurar (no confirmado aquí)

- Límites del plan gratuito (según supabase.com/pricing, consultado 2026-10-17): 500 MB de base de datos por proyecto, 2 proyectos activos, 200 conexiones Realtime simultáneas, 2 M de mensajes Realtime/mes, 5 GB de egress, y **pausa tras 7 días de inactividad**. Suficiente para el MVP; lo crítico es la pausa: crear el proyecto con antelación y hacer una consulta justo antes de la demo. Volver a revisar la página por si cambió.
- Versión y comportamiento actuales de Realtime (cambios en Postgres vs. *broadcast*) si se llega a usar `RF-F3-32`.
- Latencia desde la sala del evento hacia la región del proyecto (elegir región cercana, p. ej. São Paulo, si está disponible).
- Si el cliente `supabase-py` o `psycopg`/`asyncpg` encaja mejor con el orquestador asíncrono (ver ejecución de operaciones dentro de `asyncio`).
- Desarrollo local con la CLI de Supabase (`supabase start`) requiere Docker; el plan del proyecto era no usar Docker, por eso se usa el proyecto en la nube ya existente + `MemoryStore` como respaldo.
- Si el proyecto está pausado (plan gratuito, 7 días sin actividad), reactivarlo desde el panel antes de empezar.

## Consultas útiles para la demo y las métricas

```sql
-- Línea de tiempo de un run
select seq, ts, tipo, actor from eventos where run_id = :run order by seq;

-- Runs por estado
select estado, count(*) from runs group by estado;

-- Conflictos detectados y cuántos terminaron aprobados
select count(*) filter (where e.tipo = 'conflicto.detectado') as conflictos,
       count(*) filter (where r.estado = 'APROBADA') as aprobados
from runs r left join eventos e on e.run_id = r.id;

-- Incidentes por tipo de tarea (verifica RF-F0-16: ≥ 3 por tipo)
select tipo_tarea_id, count(*) from incidentes group by tipo_tarea_id order by 2;
```

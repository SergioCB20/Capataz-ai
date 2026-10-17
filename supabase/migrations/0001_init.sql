-- CAPATAZ: esquema inicial (RF-F0-04, RF-F0-14). Ver docs/requisitos/90-anexo-supabase.md.
-- Principio: el contrato Pydantic es la fuente de verdad. Los objetos se guardan como jsonb
-- y las columnas relacionales sirven solo para consultar y ordenar.
-- Es idempotente: se puede aplicar más de una vez.

-- Catálogo (los carga scripts/cargar_seeds.py desde data/*.json). `orden` conserva la posición
-- de cada fila en su archivo: el orden del catálogo importa (qué candidato se prueba primero, orden en la UI).
create table if not exists peligros     (id text primary key, orden integer not null default 0, data jsonb not null);
create table if not exists tipos_tarea  (id text primary key, orden integer not null default 0, data jsonb not null);
create table if not exists controles    (id text primary key, orden integer not null default 0, peligro_id text not null, bloqueante boolean not null default true, data jsonb not null);
create table if not exists personas     (id text primary key, orden integer not null default 0, data jsonb not null);
create table if not exists equipos      (id text primary key, orden integer not null default 0, tipo_equipo text not null, data jsonb not null);
create table if not exists incidentes   (id text primary key, orden integer not null default 0, tipo_tarea text, riesgo_critico text, data jsonb not null);
create table if not exists escenarios   (id text primary key, orden integer not null default 0, data jsonb not null);

-- Ejecución
create table if not exists runs (
  id             text primary key,
  estado         text not null,                 -- EstadoRun
  modo           text not null default 'vivo',  -- 'vivo' (los replays no se persisten, RF-F3-02)
  escenario_id   text,
  tarea          jsonb not null,
  data           jsonb not null,                -- el Run completo (plan, alternativas y decisión incluidos)
  creado_en      timestamptz not null default now(),
  actualizado_en timestamptz not null default now()
);

create table if not exists eventos (            -- auditoría: el flujo de eventos persistido
  run_id  text not null references runs(id) on delete cascade,
  seq     integer not null,
  ts      timestamptz not null,
  tipo    text not null,                        -- TipoEvento
  actor   text not null,
  payload jsonb not null,
  primary key (run_id, seq)                     -- idempotencia al reintentar
);
create index if not exists eventos_tipo_idx on eventos (tipo);

create table if not exists planes (
  id             text primary key,
  run_id         text not null references runs(id) on delete cascade,
  estado_sistema text not null,                 -- EstadoSistema
  data           jsonb not null
);
create index if not exists planes_run_idx on planes (run_id);

create table if not exists decisiones (
  id         bigint generated always as identity primary key,
  run_id     text not null references runs(id) on delete cascade,
  plan_id    text not null,
  decision   text not null check (decision in ('aprobar', 'rechazar')),
  comentario text,
  usuario    text not null default 'supervisor',
  ts         timestamptz not null default now(),
  check (decision <> 'rechazar' or length(trim(coalesce(comentario, ''))) > 0)
);

-- Solo hoja de ruta NANDA (no se usa en el MVP)
create table if not exists agent_registry (id text primary key, data jsonb not null);

-- Seguridad: RLS activada y sin políticas para anon/authenticated.
-- El backend usa la service_role key (ignora RLS) y nunca la expone al navegador.
alter table peligros       enable row level security;
alter table tipos_tarea    enable row level security;
alter table controles      enable row level security;
alter table personas       enable row level security;
alter table equipos        enable row level security;
alter table incidentes     enable row level security;
alter table escenarios     enable row level security;
alter table runs           enable row level security;
alter table eventos        enable row level security;
alter table planes         enable row level security;
alter table decisiones     enable row level security;
alter table agent_registry enable row level security;

-- Permisos: solo service_role (el backend) accede a estas tablas. Se otorgan de forma explícita por si el
-- proyecto no concede permisos por defecto. anon y authenticated no reciben ninguno.
grant usage on schema public to service_role;
grant all on table peligros, tipos_tarea, controles, personas, equipos, incidentes, escenarios,
                   runs, eventos, planes, decisiones, agent_registry to service_role;
grant usage, select on sequence decisiones_id_seq to service_role;

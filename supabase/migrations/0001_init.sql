-- CAPATAZ: esquema inicial (docs/requisitos/90-anexo-supabase.md).
-- Aplicar en el SQL Editor del panel de Supabase o con: psql "$DATABASE_URL" -f supabase/migrations/0001_init.sql

-- Catálogo (objetos del contrato guardados como jsonb)
create table if not exists peligros     (id text primary key, data jsonb not null);
create table if not exists tipos_tarea  (id text primary key, data jsonb not null);
create table if not exists controles    (id text primary key, peligro_id text not null, bloqueante boolean not null default true, data jsonb not null);
create table if not exists personas     (id text primary key, data jsonb not null);
create table if not exists equipos      (id text primary key, tipo_equipo text not null, data jsonb not null);
create table if not exists escenarios   (id text primary key, data jsonb not null);
create table if not exists incidentes   (id text primary key, tipo_tarea_id text, data jsonb not null);

-- Ejecución
create table if not exists runs (
  id             text primary key,
  estado         text not null,                 -- EstadoRun
  modo           text not null default 'vivo',  -- 'vivo' | 'replay'
  escenario_id   text,
  tarea          jsonb not null,
  data           jsonb not null,                -- Run completo del contrato (plan, decisión, alternativas)
  creado_en      timestamptz not null default now(),
  actualizado_en timestamptz not null default now()
);

create table if not exists eventos (           -- auditoría: el flujo de eventos persistido
  run_id  text not null references runs(id) on delete cascade,
  seq     integer not null,
  ts      timestamptz not null,
  tipo    text not null,                       -- TipoEvento
  actor   text not null,
  payload jsonb not null,
  primary key (run_id, seq)                    -- idempotencia al reintentar
);
create index if not exists eventos_tipo_idx on eventos (tipo);

create table if not exists planes (
  id             text primary key,
  run_id         text not null references runs(id) on delete cascade,
  estado_sistema text not null,                -- EstadoSistema
  data           jsonb not null
);

create table if not exists decisiones (
  id         bigint generated always as identity primary key,
  run_id     text not null references runs(id) on delete cascade,
  plan_id    text not null,
  decision   text not null check (decision in ('aprobar','rechazar')),
  comentario text,
  usuario    text not null default 'supervisor',
  ts         timestamptz not null default now(),
  check (decision <> 'rechazar' or length(trim(coalesce(comentario,''))) > 0)
);

-- Futuro: no se crea en el MVP (hoja de ruta NANDA, ver 05-hoja-de-ruta-nanda.md)
-- create table if not exists agent_registry (id text primary key, data jsonb not null);

-- Seguridad: RLS activada, sin políticas para anon/authenticated.
-- El backend usa la clave secreta (ignora RLS) y nunca la expone al navegador.
alter table peligros    enable row level security;
alter table tipos_tarea enable row level security;
alter table controles   enable row level security;
alter table personas    enable row level security;
alter table equipos     enable row level security;
alter table escenarios  enable row level security;
alter table incidentes  enable row level security;
alter table runs        enable row level security;
alter table eventos     enable row level security;
alter table planes      enable row level security;
alter table decisiones  enable row level security;

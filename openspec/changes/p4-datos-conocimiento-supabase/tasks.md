## 1. Seed mínimo (subir a main ~15:10)

- [ ] 1.1 `data/` con 1 tipo de tarea, 2 controles, 3 personas, 2 equipos y el escenario E1, según los modelos acordados (RF-F0-09)
- [ ] 1.2 Avisar a P1, P2 y P5 de que el seed está en main

## 2. Datos completos (antes de las 15:45)

- [ ] 2.1 Completar peligros, tipos de tarea, controles, personas y equipos hasta los mínimos (RF-F0-09)
- [ ] 2.2 Escenarios E2, E2c y E3 diseñados hacia atrás desde su resultado esperado, con escalamiento en E3
- [ ] 2.3 Validar con P3 que E2 tiene al menos una alternativa verificable y E3 ninguna

## 3. Incidentes y evaluación (en paralelo con lo anterior)

- [ ] 3.1 Bajar el CSV de Kaggle a `data/referencia/` y anotar cabeceras y valores únicos; si no se puede, dejar «POR VERIFICAR» (RF-F0-16)
- [ ] 3.2 `scripts/gen_sintetico.py` con semilla fija y temperatura baja (RF-F0-17)
- [ ] 3.3 Generar y revisar ≥ 50 incidentes, ≥ 3 por tipo de tarea, todos simulados (RF-F0-16)
- [ ] 3.4 `data/evaluacion.json` con ≥ 15 casos, casos limpios y ≥ 3 detectables por incidentes; resultado esperado fijado a mano (RF-F3-20)

## 4. Base de conocimiento

- [ ] 4.1 Descargar los 5 PDFs de RF-F0-12 y comprobar que tienen texto seleccionable
- [ ] 4.2 Un `knowledge/*.md` por PDF con *front-matter* y solo citas verificadas (RF-F0-12, RT-10)

## 5. Supabase (recortable: si falla, todo sigue en memoria)

- [ ] 5.1 Usar el proyecto existente `shjpypqcetndpokklycy`: confirmar que no está pausado, obtener la `service_role` y la cadena del pooler IPv4 si la conexión directa falla, y compartirlas por canal privado (RF-F0-04)
- [ ] 5.2 `supabase/migrations/0001_init.sql` con RLS, aplicada con `psql "$DATABASE_URL"` o el SQL Editor (RF-F0-04, RF-F0-14)
- [ ] 5.3 `scripts/cargar_seeds.py` idempotente (RF-F0-08)
- [ ] 5.4 `backend/app/store/supabase_store.py` que pase la suite de `Store` de P1 (RF-F0-06)

## 6. Preparación de la demo (desde 16:20)

- [ ] 6.1 Guion de ≤ 5 min con quién habla y qué clic (RF-F3-40)
- [ ] 6.2 Checklist previo y plan B (RF-F3-41, RF-F3-42)
- [ ] 6.3 Material por criterio de la rúbrica (RF-F3-44)
- [ ] 6.4 Dirigir el ensayo de 16:45 a 17:00

# Fase 3 — UX, replay, evaluación y demo (2:50 – 3:30)

**Objetivo:** convertir un sistema que funciona en una demo que convence. **A las 3:30 se congelan las funcionalidades.** Entre 3:30 y 5:00 solo se corrigen errores, se ensaya y se prepara el pitch.

## A. Modo replay (red de seguridad)

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F3-01 | Grabación de runs: un comando exporta los eventos de un run a `replays/<escenario_id>.json` (misma estructura `Evento` que el SSE en vivo). | M | EJ | Archivo valida evento por evento con `validar_payload()`. |
| RF-F3-02 | `POST /api/runs` con `modo="replay"` y `escenario_id` reproduce el archivo por SSE respetando tiempos relativos (con factor de velocidad configurable). No usa LLM ni Supabase. | M | EJ | Con la red apagada, E1, E2, E2c y E3 se reproducen completos. |
| RF-F3-03 | Mismo formato y mismo cliente: el frontend no distingue vivo de replay salvo por una insignia discreta «Replay». | M | UX | El reductor de la UI es el mismo (RF-F1-35). |
| RF-F3-04 | Existe un replay por cada escenario (E1, E2, E2c, E3), generados desde corridas reales aprobadas por el equipo. | M | EJ | Cuatro archivos en `replays/`. |
| RF-F3-05 | En replay, las decisiones y confirmaciones del usuario se aceptan y se simulan sin persistir en Supabase. | S | EJ | Se puede «aprobar» en replay sin errores. |

## B. Pulido de experiencia de usuario

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F3-10 | Transiciones animadas (Motion) en el grafo y el semáforo: un nodo que pasa a «trabajando» o un control que cambia de estado se nota sin distraer. | S | UX, IN | Revisión visual del equipo. |
| RF-F3-11 | **Resumen ejecutivo** arriba del resultado: estado del plan, qué cambió, qué requiere acción humana, en ≤ 3 líneas, redactado por el LLM a partir de datos ya verificados. | S | UX, IN | El texto no afirma nada que no esté en los `ResultadoControl`. |
| RF-F3-12 | Diseño responsivo usable en tableta (supuesto de uso en campo; no es un dato validado). | S | UX | Pantalla de 1024 px sin desplazamiento horizontal. |
| RF-F3-13 | Accesibilidad básica: contraste suficiente, estado nunca solo por color, navegación con teclado en tarjetas y botones. | S | UX | Revisión manual con teclado. |
| RF-F3-14 | Textos y etiquetas en español, coherentes con el vocabulario del contrato y del sector (control crítico, bloqueante, turno, certificación). | M | UX, AP | Sin textos en inglés visibles para el usuario. |
| RF-F3-15 | Pantalla «Acerca del sistema»: qué verifica, qué **no** garantiza (datos simulados), principio de decisión humana. | C | AP | Visible desde el encabezado. |
| RF-F3-16 | Historial: lista de runs previos con estado y enlace para reabrirlos (usa persistencia). | C | UX, EJ | Reabrir un run reconstruye la vista desde sus eventos. |

## C. Evaluación

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F3-20 | Conjunto de evaluación `data/evaluacion.json` con casos `CasoEvaluacion`: tareas con **fallas inyectadas** (certificación vencida, equipo en mantenimiento, doble asignación, requisito sin verificar, etc.) y su resultado esperado. ≥ 15 casos, incluyendo casos limpios para medir falsos positivos y ≥ 3 casos cuya falla solo se detecta por el **patrón de incidentes** (control adicional sumado por RF-F1-10). El **resultado esperado lo fija el equipo** a partir de la falla inyectada, nunca el LLM (evita una métrica circular; ver RF-F0-17). | M | AP, PT | El archivo valida contra el contrato; cada caso indica qué falla se inyectó. |
| RF-F3-21 | Script `evaluar` que ejecuta los casos (modo `fake` para el LLM, herramientas reales) y reporta: % de fallas inyectadas detectadas, falsos positivos, y fallas por tipo, separando «detectado por checklist base» de «detectado por incidentes». Salida en tabla y JSON. | M | AP, PT | Reporte reproducible con un comando. |
| RF-F3-22 | La métrica se presenta como **sobre datos simulados**: valida que el sistema detecta lo que se le inyecta, no que reduzca accidentes reales. El texto de la UI/pitch lo dice. | M | AP | Redacción revisada por el equipo (RT-07). |
| RF-F3-23 | Ejecutar la evaluación con LLM real sobre un subconjunto (los casos donde el LLM interviene: Riesgo y alternativas) y reportar estabilidad. | C | PT | Resultado documentado, aunque sea parcial. |

## D. Persistencia y auditoría (uso de Supabase)

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F3-30 | Exportar la auditoría de un run (eventos + decisión) como JSON/Markdown descargable desde la UI. | S | AP | El archivo contiene eventos en orden, actor y decisión. |
| RF-F3-31 | Panel de métricas simple (opcional): runs por estado, conflictos resueltos, tiempo promedio, leído de Supabase. | C | AP, IN | Se alimenta con consultas SQL sobre `runs` y `eventos`. |
| RF-F3-32 | Supabase Realtime en el historial (nuevos runs aparecen sin recargar). Solo si el equipo ya domina la herramienta; el flujo principal sigue en SSE (ver anexo). | C | PT | No es necesario para ninguna demo. |

## E. Guion de demo y preparación

| ID | Requisito | Prio | Rúbrica | Aceptación |
|---|---|---|---|---|
| RF-F3-40 | Guion de demo de ≤ 5 min: problema (con dato fuente) → E1 rápido → **E2 completo** → E3 breve → métrica y límites (la métrica es **sobre datos simulados** y no promete reducir accidentes reales, RF-F3-22). Cada paso con quién habla y qué clic hace. | M | EJ, AP | Ensayado ≥ 2 veces con cronómetro. |
| RF-F3-41 | Lista de verificación previa a la demo: frontend local construido y servido (RF-F3-45), `.env` cargado, Supabase accesible o `STORE_BACKEND=memory`, `LLM_MODE` decidido, replays presentes, navegador y zoom fijados. | M | EJ | Checklist impresa/compartida. |
| RF-F3-42 | Plan B documentado: si falla la red/LLM ⇒ replay; si falla Supabase ⇒ `memory`; si falla el front ⇒ capturas/video de respaldo. | M | EJ | Se probó cambiar de modo en vivo al menos una vez. |
| RF-F3-43 | Video/capturas de respaldo de E2 grabados. | S | EJ | Archivo disponible en el equipo del presentador. |
| RF-F3-44 | Material para la rúbrica: un slide o sección por criterio con la evidencia concreta (ver `91-matriz-trazabilidad.md`). | M | todos | Cada criterio tiene un ejemplo mostrable. |
| RF-F3-45 | **Topología de la demo:** se presenta con el frontend **local** (`pnpm build && pnpm preview`) y el backend local (`uvicorn :8000`). No depende de Vercel ni de Internet en modo `replay` + `memory`. El despliegue en Vercel es una **vitrina pública** del front; no se usa en la demo porque un sitio público que llama a `localhost` depende de CORS y de los permisos de red local del navegador. | M | EJ | Con el Wi-Fi apagado, E1–E3 en replay corren desde el frontend local. |
| RF-F3-46 | **Vitrina autónoma en Vercel:** los archivos de `replays/` se publican como estáticos y el navegador los reproduce con el mismo reductor (RF-F1-35), sin backend. Decisiones simuladas, insignia «Replay». | C | UX, EJ | Abrir la URL de Vercel sin backend reproduce E2 completo. |

## Criterios de salida (congelamiento)

- [ ] Los 4 replays funcionan sin red.
- [ ] Reporte de evaluación generado y revisado.
- [ ] Demo ensayada de principio a fin con cronómetro.
- [ ] Todo requisito **M** de las fases 0–3 cumplido o con decisión explícita de recorte.

## Recortes sugeridos si se retrasa (en este orden)

1. RF-F3-31/32/46 (métricas, Realtime, vitrina autónoma en Vercel) → fuera.
2. RF-F3-15/16 (acerca, historial) → fuera.
3. RF-F3-10/11 (animaciones, resumen LLM) → versión simple.
4. RF-F3-23 (evaluación con LLM real) → fuera.
5. **Nunca** recortar: replay (RF-F3-01–04), evaluación base (RF-F3-20–22), plan B (RF-F3-42), frontend local para la demo (RF-F3-45).

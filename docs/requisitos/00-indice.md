# CAPATAZ — Requisitos funcionales (índice)

Sistema multiagente que verifica, antes de ejecutar una tarea minera, que los controles críticos de seguridad pueden ejecutarse de verdad (personal competente, equipo disponible y en buen estado, condiciones de campo). Propone la asignación más segura; **un humano siempre decide**.

> Contexto: hackathon Sundai LATAM x NTT Data (Perú Tech Week, 17 oct 2026), sector Minería, reto M1 (PTW dinámico). Cierre del equipo a las **17:00**; el jurado evalúa hacia las **17:30**. Los datos son **sintéticos** (la única excepción son los documentos oficiales en PDF); el MVP demuestra la arquitectura, no una reducción real de accidentes.

## Archivos

| Archivo | Contenido | Ventana (hora real, 17 oct) |
|---|---|---|
| `00-indice.md` | Este índice, convenciones, escenarios y reglas transversales | — |
| `01-fase-0-fundaciones.md` | Repo, contrato, Supabase, seeds, esqueleto front/back | 14:30 – 15:00 |
| `02-fase-1-nucleo-verificacion.md` | Escenario 1 (caso limpio) de punta a punta | 15:00 – 15:45 |
| `03-fase-2-conflicto-y-decision.md` | Escenarios 2 y 3, alternativas, campo, decisión humana | 15:45 – 16:20 |
| `04-fase-3-ux-evaluacion-demo.md` | Pulido de UX, replay, evaluación, guion de demo | 16:20 – 16:45 (**congelamiento de funcionalidades a las 16:45**) |
| `05-hoja-de-ruta-nanda.md` | Registro de agentes inspirado en NANDA — **hoja de ruta (no se implementa)** | — |
| `90-anexo-supabase.md` | Esquema SQL, rol de Supabase, seguridad, decisiones | — |
| `91-matriz-trazabilidad.md` | Requisito ↔ criterio de la rúbrica ↔ escenario | — |

De 16:45 a 17:00: ensayo, correcciones, pitch. **No se agregan funcionalidades.**

> Las horas son una referencia tomando como inicio las 14:30. **El equipo debe ajustarlas a la hora real de arranque.** Si el tiempo no alcanza, priorizar **E1 + E2 + replay + evaluación base**.

## Convenciones

- **ID**: `RF-F<fase>-<nn>` (ej. `RF-F2-04`). Los IDs no se reutilizan.
- **Prioridad** (MoSCoW): **M** = debe, **S** = debería, **C** = podría. **F** = futuro: hoja de ruta, no se implementa en el hackatón ni cuenta en los recuentos M/S/C.
- **Rúbrica** (20 % cada una): `EJ` Ejecución · `AP` Aplicación práctica · `UX` Experiencia de usuario · `IN` Innovación · `PT` Propuesta técnica (agentes de IA).
- **Escenarios**: `E1` caso limpio · `E2` conflicto (el principal de la demo) · `E3` bloqueo sin alternativa segura. Variante de campo: `E2c` (requisito `condicion_campo` por confirmar).
- **Contrato**: `backend/app/contract.py` es la **única fuente de verdad** de los datos. Los requisitos nombran modelos y eventos de ese archivo (`TipoEvento`, `EstadoControl`, `EstadoSistema`, `EstadoRun`, etc.). Si un requisito choca con el contrato, se cambia el contrato primero y se corren sus tests.
- **Criterios de aceptación**: formato *Dado / Cuando / Entonces* solo donde aporta; el resto son verificables por inspección.

## Glosario

- **PTW** = permiso de trabajo (en Perú, **PETAR**). CAPATAZ entrega un **borrador** («Plan (PTW borrador)»); la persona lo firma. El código no firma ni autoriza.

## Reglas transversales (aplican a todas las fases)

| ID | Regla | Prio |
|---|---|---|
| RT-01 | **El código verifica; el LLM razona.** Disponibilidad, vigencia de certificaciones y estado de equipos se calculan con herramientas deterministas. El LLM propone alternativas, explica y redacta; nunca decide un `CUMPLE`. | M |
| RT-02 | **Tres estados** de control: `CUMPLE`, `NO_VERIFICABLE`, `NO_CUMPLE`. Gana el peor. Un requisito sin resultado nunca es `CUMPLE` (usar `consolidar_control`, no reimplementar). | M |
| RT-03 | **Estado del plan** solo con `calcular_estado_sistema`: `BLOQUEADO`, `REQUIERE_CAMPO` o `RECOMENDADO`. | M |
| RT-04 | **Humano en el circuito.** Un plan `BLOQUEADO` solo admite rechazo (sin *override* en el MVP), forzado en el backend. Rechazar exige comentario. | M |
| RT-05 | **Auditoría = flujo de eventos.** Cada evento se persiste antes de emitirse; `seq` monótono por run. | M |
| RT-06 | **Primera pasada estricta**; las equivalencias (`equipo_equivalente`, `certificacion_equivalente`) solo se usan al evaluar alternativas. Máximo **2 rondas** de resolución de conflicto. | M |
| RT-07 | **Todo dato simulado se muestra como tal** en la UI (insignia «simulado» cuando `Fuente.tipo == simulado`). | M |
| RT-08 | **La demo no depende de la red.** Modo `replay` y almacén en memoria funcionan sin Supabase ni LLM. La demo se presenta con frontend y backend **locales**; el despliegue en Vercel es solo una vitrina (RF-F3-45). | M |
| RT-09 | Las claves (`OPENROUTER_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL` con su contraseña) viven solo en el backend; nunca en el frontend ni en el repo. | M |
| RT-10 | Las citas normativas deben ser reales o marcarse `simulado`; no se inventan referencias. | M |

## Escenarios de demo (definición común)

| Id | Nombre | Qué demuestra | Resultado esperado |
|---|---|---|---|
| E1 | Caso limpio | Flujo completo sin fricción | `RECOMENDADO`; humano aprueba |
| E2 | Conflicto | Equipo requerido en mantenimiento y sin personal certificado ese turno; el sistema encuentra alternativas verificadas | `BLOQUEADO` → alternativas → plan `RECOMENDADO`; humano aprueba una |
| E2c | Campo | Un requisito `condicion_campo` no es verificable por datos | `REQUIERE_CAMPO` → confirmación → `RECOMENDADO` |
| E3 | Bloqueo | Ninguna alternativa segura en 2 rondas | `BLOQUEADO`; solo rechazo con comentario; escalamiento |

## Qué queda fuera del MVP

Agente de Costo · autenticación de usuarios finales · *override* de planes bloqueados · datos reales de la operación · RAG vectorial (la base de **conocimiento** es pequeña y va en contexto; los **incidentes**, ≥ 50 registros, no van al contexto: se consultan con la herramienta `buscar_incidentes`) · integración con sistemas de la mina · registro de agentes inspirado en NANDA (hoja de ruta, no se implementa; ver `05-hoja-de-ruta-nanda.md`).

## Preguntas abiertas (confirmar con organizadores)

1. Formato de entrega/demo.
2. Créditos de OpenRouter durante el evento y límites de uso de GPT-6 Luna.
3. Si hay Internet estable en la sala: Supabase y el LLM en vivo la necesitan; el replay es el respaldo (RT-08).

**Resueltas:** modelo → GPT-6 Luna vía OpenRouter · backend → local (`uvicorn :8000`), frontend en Vercel solo como vitrina.

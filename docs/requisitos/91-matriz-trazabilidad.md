# Matriz de trazabilidad

## Criterio de la rúbrica → evidencia → requisitos

| Criterio (20 %) | Qué mostrar en la demo | Requisitos principales |
|---|---|---|
| **Ejecución** — el prototipo funciona y muestra el flujo en vivo | E1 y E2 corriendo con eventos en vivo; replay como respaldo | RF-F1-01–05, RF-F1-20, RF-F2-01–07, RF-F0-18, RF-F3-01–04, RF-F3-40–42, RF-F3-45 |
| **Aplicación práctica** — responde al reto y aporta valor al sector | Problema real («el control existe pero no se ejecuta efectivamente»), E2 con alternativas verificadas, E3 con escalamiento, métrica de detección | RF-F0-09, RF-F0-16, RF-F1-10, RF-F1-16, RF-F1-19, RF-F2-05–07, RF-F2-20, RF-F3-20–22 |
| **Experiencia de usuario** — interacción clara que ayuda a resolver la tarea | Presets, grafo vivo, semáforo con icono+texto, cajón de evidencia, comparación lado a lado, barra de decisión | RF-F1-30–36, RF-F2-30–35, RF-F3-10–14 |
| **Innovación** | Verificación de *ejecutabilidad* del control (no solo checklist), alternativas re-verificadas con herramientas, humano en el circuito, checklist dinámico por incidentes | RF-F1-10, RF-F1-19, RF-F2-02–03, RF-F2-08, RF-F3-11 |
| **Propuesta técnica** — agentes de IA integrados | Orquestación asíncrona, agentes paralelos, separación código-verifica / LLM-razona, contrato tipado, auditoría por eventos | RT-01–06, RF-F1-10–19, RF-F2-02–04 |
| **Hoja de ruta (no se implementa):** registro de agentes inspirado en NANDA | No se muestra en la demo | `05-hoja-de-ruta-nanda.md` (prioridad F) |

## Escenario → requisitos que lo habilitan

| Escenario | Fases | Requisitos clave |
|---|---|---|
| E1 caso limpio | F1 | RF-F1-01–05, 10–18, 20, 30–34 |
| E2 conflicto | F2 | RF-F2-01–08, 21, 30–31, 34–35 |
| E2c campo | F2 | RF-F2-10–12, 32 |
| E3 bloqueo | F2 | RF-F2-07, 20, 33 |
| Todos en replay | F3 | RF-F3-01–05 |

## Reglas transversales → dónde se verifican

| Regla | Verificación |
|---|---|
| RT-01 código verifica / LLM razona | RF-F1-13/14/16, RF-F2-03 |
| RT-02 tres estados | Tests del contrato; RF-F1-17 |
| RT-03 estado del plan | RF-F1-17/18 |
| RT-04 humano decide | RF-F1-20, RF-F2-20/22/23 |
| RT-05 auditoría por eventos | RF-F1-02/03, RF-F2-34, RF-F3-30 |
| RT-06 estricto primero, 2 rondas | RF-F2-04 |
| RT-07 insignia «simulado» | RF-F1-32, RF-F3-22 |
| RT-08 demo sin red | RF-F0-06/07/11, RF-F3-01–04, RF-F3-42, RF-F3-45 |
| RT-09 claves solo en backend | RF-F0-05/14 |
| RT-10 citas reales o simuladas | RF-F0-09/12/16/17, RF-F1-19 |

## Recuento de requisitos funcionales (RF)

| Fase | Total | Debe (M) | Debería (S) | Podría (C) |
|---|---|---|---|---|
| F0 Fundaciones | 19 | 14 | 4 | 1 |
| F1 Núcleo | 26 | 24 | 2 | 0 |
| F2 Conflicto y decisión | 21 | 18 | 3 | 0 |
| F3 UX, evaluación, demo | 26 | 13 | 7 | 6 |
| **Total MVP** | **92** | **69** | **16** | **7** |

Aparte: hoja de ruta NANDA (`05-hoja-de-ruta-nanda.md`), **11 requisitos con prioridad F** (futuro), fuera del recuento. Las reglas transversales (RT-01 a RT-10) también se cuentan aparte.

# Material por criterio de la rúbrica (RF-F3-44)

Cada criterio vale 20 %. Debajo, qué mostrar y **dónde está la evidencia**. Matriz completa: [`91-matriz-trazabilidad.md`](../requisitos/91-matriz-trazabilidad.md).

| Criterio | Qué mostrar | Evidencia concreta |
|---|---|---|
| **Ejecución**: el prototipo funciona y muestra el flujo en vivo | E1, E2 y E3 de punta a punta, con los agentes trabajando en vivo; el modo Replay como respaldo sin red. | Cuatro escenarios con su resultado esperado, comprobados por pruebas automáticas (`backend/tests/test_datos_p4.py`). Toda la suite (153 pruebas al momento de escribir esto) corre con `cd backend && uv run pytest`. |
| **Aplicación práctica**: responde al reto y aporta valor | El problema real (el control existe pero no se ejecuta bien) y E2: el sistema no solo dice «no», propone alternativas verificadas; en E3 se detiene y dice a quién escalar. | Dato del ICMM verificado: 83 % de las muertes de 2024 se asociaron a controles críticos no efectivos (*Safety Performance Insights*, pág. 4). La verificación del ICMM «no es una auditoría: busca detectar brechas **antes** del evento» (guía, pág. PDF 47). |
| **Experiencia de usuario**: interacción clara | Dos clics (escenario + Evaluar), grafo de agentes en vivo, semáforo con ícono y texto, evidencia a un clic, comparación de planes, decisión humana con comentario obligatorio al rechazar. | La interfaz de `frontend/` (P5). El plan se llama «Plan (PTW borrador)»: la persona firma, el sistema no autoriza. |
| **Innovación** | Se verifica la **ejecutabilidad** del control (¿hay personas certificadas y equipo operativo en ese turno?), no solo un checklist; las alternativas se **re-verifican con herramientas**; el checklist se amplía con el patrón de incidentes parecidos. | E2 (alternativa A rechazada por las herramientas, B verificada) y el control «supervisor de seguridad presente» que en E1 llega solo por los incidentes. |
| **Propuesta técnica**: agentes de IA integrados | Supervisor determinista + agente Riesgo con LLM; Personal y Equipo en paralelo con herramientas deterministas; contrato tipado; auditoría como flujo de eventos. **El código verifica, el LLM razona y explica.** | `backend/app/agents/` y `backend/app/tools/`; reporte de `scripts/evaluar.py`; cada evento se valida contra el contrato antes de emitirse. |
| **Reconocimiento NANDA** (opcional) | **No se implementó** (hoja de ruta, `docs/requisitos/05-hoja-de-ruta-nanda.md`). No presentarlo como parte del MVP. | — |

## Límites que conviene decir antes de que pregunten

- Los datos son **simulados** y los escribió el equipo; la métrica prueba coherencia del mecanismo, no desempeño real.
- La solución **no está validada** con personal de planificación o seguridad minera.
- El modelo de lenguaje real (GPT-6 Luna por OpenRouter) **no se ha probado de punta a punta**; la demo usa el modo `fake`, que responde con reglas fijas.
- Supabase se probó con un cliente falso, no contra el proyecto real.

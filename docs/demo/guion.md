# Guion de la demo (≤ 5 minutos)

> Estado: **sin ensayar**. Falta cronometrar al menos dos veces (RF-F3-40). Los tiempos son una propuesta.
> Las descripciones de pantalla siguen los componentes de `frontend/` (nombres reales de botones y pantallas), pero **no se ejecutó la interfaz** al escribirlo: confirmarlas en el primer ensayo.
> Roles: **Presentador** (habla) y **Operador** (maneja el teclado). Pueden ser la misma persona.
> Antes de empezar, recorrer el [checklist](checklist.md). Si algo falla, el [plan B](plan-b.md).

Todo lo que se muestra son **datos simulados**; el sistema entrega un «Plan (PTW borrador)» y **una persona decide**.

| Tiempo | Quién | Qué dice | Qué clic hace |
|---|---|---|---|
| 0:00–0:40 | Presentador | **El problema.** «En 2024, la falta de controles críticos efectivos explicó el 83 % de las muertes en las empresas del ICMM. No faltan reglas: el control existe y no se ejecuta bien en el momento crítico. CAPATAZ revisa, **antes** de la tarea, si esos controles se pueden ejecutar de verdad.» Fuente: ICMM, *Safety Performance Insights 2020–2024* (julio de 2025), pág. 4. | Pantalla de inicio. |
| 0:40–1:30 | Operador | **E1, caso limpio.** «Un sostenimiento con operadora y supervisora certificadas y un empernador operativo.» Señalar el grafo (los agentes trabajan, Personal y Equipo a la vez) y el semáforo en verde. «El tercer control, *supervisor de seguridad presente*, no estaba en la lista base: lo sumó el patrón de incidentes parecidos.» | Elegir **E1** → **Evaluar**. Abrir un control para ver su evidencia. **Aprobar**. |
| 1:30–3:30 | Operador y Presentador | **E2, conflicto (el caso principal).** «La perforación tiene el jumbo en mantenimiento y la operadora con la certificación vencida. El sistema bloquea y propone alternativas.» Mostrar las dos: la **A falla** (*Marta Soto no está disponible esa noche*) y la **B se verifica** (jumbo equivalente y otro operador). «El modelo propone; **las herramientas verifican**. Nunca decide un cumplimiento.» Mostrar la comparación con el plan original. | Elegir **E2** → **Evaluar**. Abrir la alternativa B y la comparación de planes. **Aprobar** la alternativa verificada. |
| 3:30–4:15 | Presentador | **E3, bloqueo.** «Plataforma fuera de servicio y nadie certificado disponible ni reprogramando. Tras dos rondas no hay alternativa segura: solo se puede rechazar, con comentario, y el sistema dice a quién escalar.» | Elegir **E3** → **Evaluar**. **Rechazar** → escribir un comentario → **Confirmar rechazo**. |
| 4:15–5:00 | Presentador | **Métrica y límites.** «Medimos si detecta lo que le inyectamos, sobre **datos simulados**: de 16 fallas inyectadas detecta las 16 (3 solo por el patrón de incidentes) y no da falsos positivos en 4 casos limpios. Es una prueba de que el mecanismo funciona; **no promete reducir accidentes reales** ni está validado con personal de planificación o seguridad minera.» | Mostrar el reporte de `scripts/evaluar.py` (ver abajo). |

Si sobra tiempo: **E2c** (condición de campo): «todo cumple salvo si se verificó energía cero; el sistema no puede saberlo y lo pregunta».

## Cifras que se pueden decir (todas reproducibles)

- **83 %**: ICMM, *Safety Performance Insights 2020–2024*, pág. 4 (en inglés). Verificado en el texto del PDF.
- **16 de 16 fallas, 0 falsos positivos en 4 limpios, 3 solo por incidentes**: sale de `uv run --project backend python scripts/evaluar.py` sobre `data/evaluacion.json` (20 casos). Ojo: el equipo escribió los datos y los casos, así que es una prueba de coherencia del mecanismo, **no** una medición independiente. Decirlo.

## Lo que NO se debe decir

- «19 de 26 incidentes fatales del ICMM»: **no se encontró en ninguno de los cinco PDFs oficiales** (ver [fuentes verificadas](../fuentes-verificadas.md)). Si el equipo tiene otra fuente, citarla antes de usarlo.
- «Reduce accidentes», «está validado» o «cumple la norma»: no hay evidencia.
- Las citas normativas salen solo de `knowledge/`; los controles de la demo son simulados y no citan norma.

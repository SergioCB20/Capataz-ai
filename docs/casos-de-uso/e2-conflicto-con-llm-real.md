# Caso de uso — E2: el empernador está en mantenimiento y el operador tiene la certificación vencida

> Corrida real del 17/10/2026 con el backend completo (P1 + P2 + P3, datos de P4) y el **LLM real** (GPT-6 Luna vía OpenRouter). Run `run-58471760`, 38 eventos, **≈ 27 s** de punta a punta. Termina en **verde**: plan `RECOMENDADO` aprobado por la persona.
> Todos los datos (personas, equipos, incidentes) son **simulados**. El plan es un **PTW borrador**: CAPATAZ no firma ni autoriza.

## En una frase

Un supervisor de turno quiere iniciar un sostenimiento con pernos. CAPATAZ descubre **antes de empezar** que el operador asignado tiene la certificación vencida y que el empernador está en mantenimiento, propone dos alternativas que **vuelve a verificar con herramientas**, pide confirmar dos condiciones de campo y deja que **la persona apruebe** el plan seguro.

## Actores

| Actor | Qué hace | ¿Usa LLM? |
|---|---|---|
| **Supervisor de turno** (persona) | Elige la tarea, confirma en campo y aprueba o rechaza. | — |
| **Agente Riesgo** | Detecta peligros, busca incidentes parecidos y elige los controles del catálogo que aplican. | **Sí** (razona y justifica) |
| **Supervisor** (orquestador) | Reparte requisitos, consolida resultados, detecta el conflicto y pide alternativas. | Sí, solo para **proponer** alternativas |
| **Agente Personal** | Verifica turnos, certificaciones y doble asignación. | **No**: herramientas deterministas |
| **Agente Equipo** | Verifica tipo, estado y disponibilidad del equipo. | **No**: herramientas deterministas |

## Precondiciones

- Tarea **TAR-E2**: *Sostenimiento con pernos en la galería 310* · Nivel 2 · turno día del **21/10/2026**.
- Asignación original: **Luis Huamán** (PER-02) con el **Empernador 01** (EQ-EMP-01).
- Catálogo con 8 controles, 8 personas, 8 equipos y 8 incidentes históricos (sintéticos).

## Flujo principal (lo que pasó de verdad)

| # | Tiempo | Qué hace la persona / qué ve en pantalla | Qué pasa por dentro |
|---|---|---|---|
| 1 | 0 s | En **Nueva evaluación** elige «Conflicto: empernador en mantenimiento…» y pulsa **Evaluar tarea** (modo *En vivo*). | Se crea el run; el stream SSE empieza a mandar eventos. |
| 2 | 0–11 s | En **Agentes**, el nodo *Agente Riesgo* pasa a «Trabajando». | El LLM llama 3 veces a `buscar_incidentes` (caída de rocas, interacción con equipo móvil, energía) y encuentra INC-01…INC-07. |
| 3 | 11 s | **Progreso → Riesgo ✓**: «1 peligro · 4 incidentes similares». | Riesgo concluye **caída de rocas** y exige **4 controles**. Dos vienen del tipo de tarea (operador certificado, empernador operativo) y **dos los suma por los incidentes** (*checklist dinámico*): INC-02 (desatado hecho por una sola persona) e INC-04 (labor sin tabla geomecánica). |
| 4 | 11 s | *Personal* y *Equipo* pasan a «Completado» casi al instante (son herramientas, no LLM). | Personal: `verificar_certificacion` → «Luis Huamán: SOST **venció el 30/09/2026**». Equipo: `consultar_estado_equipo` → «Empernador 01 **está en mantenimiento**». |
| 5 | 11 s | **Controles críticos** muestra 2 `NO_CUMPLE` y 2 por verificar; al elegir una fila, **Evidencia** muestra el registro consultado (`personas/PER-02 · certificaciones.SOST.vence = 2026-09-30`). | El Supervisor consolida: **plan original BLOQUEADO**. Emite un `conflicto.detectado` por cada requisito que falla. |
| 6 | 14 s | Aparece **Conflicto y alternativas** con las 2 causas en rojo y, debajo, 2 tarjetas. | El LLM propone (ronda 1): **alt-9e64841d** → Rosa Mamani + Empernador 02; **alt-1d59d310** → Ana Quispe + Empernador 04. |
| 7 | 14 s | Cada tarjeta pasa a **«Verificada»**. Arriba, la explicación del LLM; **separada**, el veredicto de las herramientas. | Las herramientas **re-verifican** cada alternativa: «Rosa Mamani: SOST-B vigente hasta el 01/05/2027», «0 otras tareas en el turno», «Empernador 02 operativo y disponible el 21/10 día». El LLM no decide ningún `CUMPLE`. |
| 8 | 14 s | **Confirmación en campo requerida** con 2 preguntas. Progreso: «Falta confirmar en la labor». | Los controles de rocas añadidos por los incidentes no se pueden verificar con datos: quedan `NO_VERIFICABLE` hasta que alguien mire la labor. |
| 9 | 19 s | La persona responde **Sí** a: «¿Está publicada la tabla geomecánica vigente del mes?» y «¿Se completó el desatado total, con dos personas?». | Se registra quién y cuándo. El Supervisor recalcula: **alt-9e64841d pasa a `RECOMENDADO`** (4 de 4 controles `CUMPLE`). |
| 10 | 19 s | En la tabla, el interruptor **Plan original / Plan elegido** muestra el contraste: *original* 0 cumplen · 2 no cumplen → *elegido* 4 cumplen. **Qué cambia**: Luis Huamán → Rosa Mamani; Empernador 01 → Empernador 02. | La UI compara los `resultados` del plan original con los del plan elegido (`Plan.id == Alternativa.id`). |
| 11 | 27 s | En **Tu decisión** pulsa **Aprobar plan**. | `humano.decision_tomada` → `run.finalizado: APROBADA`. Todo queda en la **línea de tiempo** y se puede **exportar la auditoría** (JSON). |

### Lo que escribió el LLM (textual)

- **Justificación del riesgo:** «La instalación de pernos en galería expone a desprendimientos durante el sostenimiento. Los incidentes INC-01, INC-02, INC-03 e INC-04 vinculan este riesgo con la zona sostenida, el desatado, la capacitación y la información geomecánica.»
- **alt-9e64841d:** «Sustituye a la persona por una operadora con certificación equivalente vigente y al equipo en mantenimiento por un empernador operativo. Mantiene el turno previsto.»
- **alt-1d59d310:** «Propone otra operadora con SOST vigente y un empernador operativo, ambos disponibles para el turno. Mantiene la fecha y el turno previstos.»

## Quién decidió qué

| Decisión | La tomó |
|---|---|
| Qué peligros y controles aplican | **LLM**, limitado a IDs del catálogo |
| Que Luis tiene la certificación vencida / que el Empernador 01 no está disponible | **Herramienta** (fecha de vencimiento, estado del equipo) |
| Qué alternativas probar | **LLM** (propone) |
| Que Rosa y el Empernador 02 sirven | **Herramienta** (re-verificación con equivalencias) |
| Que la labor está en condiciones | **Persona en campo** |
| Que el plan se ejecuta | **Persona** (aprobación) |

## Flujos alternativos

- **Responde «No» en campo:** el requisito pasa a `NO_CUMPLE` y el plan no se puede aprobar.
- **Elige la otra alternativa (alt-1d59d310):** sigue en `REQUIERE_CAMPO`, porque P2 recalcula solo la mejor tras confirmar campo. La UI desactiva «Aprobar» y explica por qué; se puede volver a la recomendada o rechazar.
- **Rechaza:** el comentario es obligatorio; queda `RECHAZADA` en la auditoría.
- **Sin Internet:** el mismo caso corre en modo **Replay** (`replays/e2.json`, grabado con el LLM real); la decisión la pone quien presenta.

## Por qué importa (para el jurado)

1. **Ejecución:** el flujo completo corre en vivo con LLM real en menos de 30 s; si la red falla, el replay es idéntico.
2. **Aplicación práctica:** detecta dos fallas reales del día a día (certificación vencida y equipo en mantenimiento) **antes** de exponer a nadie, y entrega un borrador de PTW listo para firmar.
3. **Experiencia de usuario:** en una sola pantalla se ve qué pasó, por qué, con qué evidencia y qué cambia; la persona solo decide.
4. **Innovación:** no es un checklist estático: los incidentes históricos **agregan controles** (tabla geomecánica, desatado con dos personas) y cada alternativa se **re-verifica**.
5. **Uso de IA inmerso:** el LLM razona y propone; el código verifica; la persona aprueba. Nadie puede «convencer» al sistema de un `CUMPLE` sin evidencia.

## Límites honestos

- Datos **simulados**: demuestra la arquitectura, no reduce accidentes reales todavía.
- El LLM **no es determinista**: otra corrida puede proponer otras alternativas, o sumar otros controles por incidentes.
- Aviso a P2: con el LLM real, el checklist dinámico a veces suma controles de **otro tipo de tarea** (visto en E2c). Pendiente de acotar en `backend/app/agents/riesgo.py`.

## Guion de 90 segundos

1. «Luis va a sostener la galería 310 con el Empernador 01. Parece un día normal.» → **Evaluar**.
2. «El Agente Riesgo revisa incidentes parecidos y suma dos controles que el checklist no tenía.» → señalar **Agentes** y **Riesgo ✓**.
3. «Personal y Equipo lo verifican con herramientas, en milisegundos: la certificación de Luis venció el 30 de septiembre y el empernador está en mantenimiento.» → abrir **Evidencia**.
4. «El LLM propone alternativas, pero no decide: las herramientas las vuelven a verificar.» → tarjetas **Verificada**, explicación separada.
5. «Lo que no se puede saber con datos se confirma en la labor.» → responder **Sí**.
6. «Plan original: dos controles fallan. Plan elegido: los cuatro cumplen.» → interruptor de la tabla y **Qué cambia**.
7. «Y quien firma es la persona.» → **Aprobar** y mostrar la **línea de tiempo**.

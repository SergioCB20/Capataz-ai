# Plan B (RF-F3-42)

| Si falla… | Hacer | Estado |
|---|---|---|
| **La red** o el LLM | Elegir **Replay (corrida grabada, sin red)** en la pantalla de inicio. El backend y el frontend son locales; el modo `fake` ya no usa red. | El replay funciona; faltan los replays reales de E2, E2c y E3 (hoy son ejemplos escritos a mano por P5). |
| **Supabase** (pausado, lento, sin credenciales) | `STORE_BACKEND=memory` y reiniciar el backend. Si Supabase cae a mitad de un run, el backend ya sigue en memoria y lo registra en el log (`SupabaseStore.degradado`). | Probado con un cliente falso; **no** con el Supabase real. |
| **El modelo real** (si se usó `LLM_MODE=real`) | `LLM_MODE=fake` y reiniciar el backend. | Probado en modo `fake`; el modo real no se ha probado de punta a punta. |
| **El backend** | Frontend local en modo **Replay** (no necesita backend). | Funciona con los replays locales del frontend. |
| **El frontend** | Capturas o video de E2 grabados de antemano (RF-F3-43). | **Pendiente: no existen todavía.** |

## Prueba de que el plan B funciona (pendiente)

- [ ] Cambiar de «En vivo» a «Replay» con el Wi-Fi apagado y completar E2.
- [ ] Reiniciar el backend con `STORE_BACKEND=memory` y repetir E1.
- [ ] Grabar el video de respaldo de E2 y guardarlo en el equipo del presentador.

## Qué decir si algo falla en vivo

«Lo que ven ahora es una corrida grabada de este mismo flujo.» (Es verdad en modo Replay: la insignia «Replay» está en pantalla.) No fingir que es en vivo.

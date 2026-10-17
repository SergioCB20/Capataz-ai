## 1. Arranque sin backend (desde el minuto 0)

- [x] 1.1 Proyecto Vite + React + TS + Tailwind + shadcn/ui con proxy `/api` → `:8000` y `VITE_API_URL` (RF-F0-13, RF-F0-18)
- [x] 1.2 Tipos TS a mano según los acuerdos de interfaz
- [x] 1.3 `replays/e1.json` a mano con la secuencia de eventos de E1 (RF-F1-05)
- [x] 1.4 Reductor puro `reducir(estado, evento)` y fuente de eventos desde archivo con velocidad (RF-F1-35)

## 2. Vista de E1 (hito 15:45 con el backend real)

- [x] 2.1 Pantalla de inicio con presets, modo libre y selector vivo/replay (RF-F1-30)
- [x] 2.2 Grafo de agentes con React Flow y herramientas invocadas (RF-F1-31)
- [x] 2.3 Semáforo con icono + texto, bloqueante e insignia «simulado» (RF-F1-32, RT-07)
- [x] 2.4 Cajón de evidencia con agente, fuente e incidentes similares (RF-F1-33)
- [x] 2.5 Barra de decisión con comentario obligatorio al rechazar; rótulo «Plan (PTW borrador)» (RF-F1-34)
- [x] 2.6 Fuente SSE con reconexión y estados vacío/cargando/error; conectar al backend de P1 (RF-F1-36)

## 3. E2, E2c y E3 (hito 16:20)

- [x] 3.1 Vista de conflicto con tarjetas de alternativas e indicador de ronda (RF-F2-30, RF-F2-35)
- [x] 3.2 Comparación plan original vs. alternativa elegida; elegir `plan_id` si hay varias (RF-F2-31, RF-F2-21)
- [x] 3.3 Formulario de confirmación de campo (RF-F2-32)
- [x] 3.4 Estado bloqueado: motivo, escalamiento y solo «Rechazar» (RF-F2-33)
- [x] 3.5 Línea de tiempo de auditoría (RF-F2-34)

## 4. Pulido y despliegue (hasta 16:45)

- [x] 4.1 Insignia «Replay» y revisión de textos en español (RF-F3-03, RF-F3-14)
- [x] 4.2 Build local con `pnpm build && pnpm preview` probado sin Wi-Fi (RF-F3-45)
- [ ] 4.3 Desplegar en Vercel como vitrina (RF-F0-19)
- [ ] 4.4 Grabar video o capturas de respaldo de E2 (RF-F3-43)
- [ ] 4.5 (Recortable) Exportar auditoría, animaciones, tableta, replays sin backend en Vercel (RF-F3-30, RF-F3-10, RF-F3-12, RF-F3-46)

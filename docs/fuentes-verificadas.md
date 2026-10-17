# Fuentes oficiales: qué se verificó y qué no (RT-10)

Los cinco PDFs de `knowledge/` se descargaron el 2026-10-17 y se leyeron con `pypdf` (los cinco tienen texto seleccionable). Solo se cita lo que figura en el texto, con su página del PDF.

| Documento | Páginas | Texto | Qué se cita |
|---|---|---|---|
| ICMM, *Gestión de Controles Críticos: guía de buenas prácticas* | 78 | sí | definición de control crítico (pág. 6, 34), los nueve pasos (19), la verificación (47), ejemplo de desprendimiento de rocas (26) |
| ICMM, *2020–2024 Safety Performance: Insights* (inglés) | 4 | sí | 83 % de muertes de 2024 asociado a controles críticos no efectivos (pág. 4); equipo móvil, minería subterránea, permiso de trabajo y bloqueo (págs. 2–3) |
| Gold Fields SSYMA-P04.10 v13 (PETAR) | 10 | sí | definición, validez por turno/equipo/área, nuevo permiso ante cambios (págs. 1, 3–5, 7–8) |
| DS 024-2016-EM | 56 | sí | arts. 36, 38, 39, 129, 134 y 213 |
| DS 023-2017-EM | 22 | sí | arts. 75 y 214 en su versión modificada |

## Discrepancias encontradas con lo que decían los documentos del proyecto

1. **DS 024-2016-EM no está truncado.** La nota de RF-F0-12 dice que el extracto llega solo hasta el art. 44. El PDF descargado tiene 56 páginas y los **417 artículos**. La regla que importa se mantiene: solo se citan artículos que se leyeron en el texto.
2. **El dato «19 de 26 incidentes fatales analizados por el ICMM en 2025» no figura en ninguno de los cinco PDFs.** Aparece en `CLAUDE.md` y en `docs/capataz-stack-y-contrato.html`. Lo que sí está verificado es el 83 % de *Safety Performance Insights* (pág. 4) y la frase cualitativa de la guía (pág. 19: las investigaciones de incidentes graves suelen mostrar que los controles conocidos para peligros conocidos no se implementaron de manera eficaz). Si el dato viene de otra fuente del ICMM, citarla; si no, reemplazarlo.
3. **Año de la guía del ICMM:** el repositorio la llama «2026», pero las páginas leídas no indican el año de edición.

## No verificado

- Si hubo **modificaciones posteriores a 2017** de los artículos citados del DS 024-2016-EM.
- Las columnas reales del dataset de Kaggle (no se descargó el CSV): los campos de `Incidente` son los mínimos de RF-F0-16 y siguen «POR VERIFICAR».

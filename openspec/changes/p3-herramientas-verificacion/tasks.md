## 1. Herramientas puras (desde el minuto 0, con fixtures propias)

- [ ] 1.1 Fixtures pequeñas en `backend/tests/fixtures/` (3 personas, 3 equipos, 6 incidentes)
- [ ] 1.2 `tools/personal.py`: disponibles en turno, vigencia a la fecha del turno, doble asignación (RF-F1-13)
- [ ] 1.3 `tools/equipo.py`: disponibilidad, estado, tipo requerido y equivalentes con bandera (RF-F1-14)
- [ ] 1.4 `tools/incidentes.py`: `buscar_incidentes` con límite 5 y orden por `nivel_potencial` (RF-F1-19)
- [ ] 1.5 Pruebas unitarias: certificación vencida, mantenimiento, doble asignación, primera pasada estricta, caída de rocas primero

## 2. Agentes Personal y Equipo (entregar a P2 antes de las 15:40)

- [ ] 2.1 `agents/personal.py` y `agents/equipo.py` con las firmas acordadas
- [ ] 2.2 `ResultadoRequisito` con `Evidencia` y `verificado_por`; `CUMPLE` sin evidencia ⇒ `NO_VERIFICABLE` (RF-F1-16)
- [ ] 2.3 `TraceHerramienta` y evento `agente.herramienta` por llamada (RF-F1-15)
- [ ] 2.4 Avisar a P2 para reemplazar los stubs

## 3. Integración con datos reales (hito 16:20)

- [ ] 3.1 Correr las pruebas también contra `data/*.json` de P4 y ajustar
- [ ] 3.2 Comprobar con P4 que E2 produce los `NO_CUMPLE` esperados y que existe al menos una alternativa verificable

## 4. Evaluación

- [ ] 4.1 `scripts/evaluar.py` sobre `data/evaluacion.json` con reporte en tabla y JSON (RF-F3-21)
- [ ] 4.2 Separar «checklist base» y «por incidentes» en el reporte (RF-F3-21)
- [ ] 4.3 Encabezado «datos simulados» y reporte final revisado con P4 (RF-F3-22)
- [ ] 4.4 (Opcional) Evaluación con LLM real sobre un subconjunto (RF-F3-23)

## Why

El valor de CAPATAZ está en el flujo de agentes: detectar peligros, repartir requisitos, consolidar y, cuando hay conflicto, proponer alternativas que luego se re-verifican con herramientas. P2 es dueño de ese «cerebro» y de la única puerta al LLM.

## What Changes

- Cliente LLM aislado (OpenRouter, GPT-6 Luna, *function calling*) con tiempo límite, un reintento, registro de uso y modo `fake`.
- Agente Riesgo: peligros, controles del catálogo e incidentes similares vía `buscar_incidentes`.
- Supervisor (`ejecutar_run`): reparte requisitos, corre Personal y Equipo en paralelo, consolida y arma el plan.
- Resolución de conflictos: hasta 2 rondas de alternativas del LLM, filtradas por catálogo y re-verificadas con las herramientas de P3.
- Flujo de campo (`confirmar_campo`) y escalamiento cuando no hay alternativa segura.
- Resumen ejecutivo opcional redactado por el LLM.

## Capabilities

### New Capabilities
- `cliente-llm`: módulo único de acceso al LLM, con modo fake.
- `agente-riesgo`: detección de peligros, controles aplicables e incidentes similares.
- `orquestacion-supervisor`: reparto de requisitos, paralelismo, consolidación y plan.
- `resolucion-conflictos`: alternativas en 2 rondas, re-verificación, campo y escalamiento.

### Modified Capabilities
<!-- Ninguna. -->

## Impact

- Código: `backend/app/llm/`, `backend/app/agents/riesgo.py`, `backend/app/agents/supervisor.py`.
- Consume: `contract.py` y `emitir` (P1), `verificar_personal`, `verificar_equipo` y `buscar_incidentes` (P3).
- Requisitos: RF-F0-11 · RF-F1-05, 06, 07, 10, 11, 12, 17, 18 · RF-F2-01–08, 10, 21 · RF-F3-11 · RT-01, RT-06.

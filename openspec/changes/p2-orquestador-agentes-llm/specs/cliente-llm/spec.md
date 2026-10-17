## ADDED Requirements

### Requirement: Cliente LLM aislado
El acceso al LLM SHALL pasar por un único módulo que use OpenRouter con el modelo de `LLM_MODEL`, con tiempo límite, un reintento acotado y registro de uso (RF-F0-11).

#### Scenario: Tiempo límite
- **WHEN** el LLM no responde dentro del tiempo límite
- **THEN** el cliente reintenta una vez y, si vuelve a fallar, lanza un error controlado

### Requirement: Modo fake sin red
Con `LLM_MODE=fake` el cliente SHALL devolver respuestas fijas por agente y escenario sin llamar a la red (RF-F0-11).

#### Scenario: E1 sin red
- **WHEN** se corre E1 con `LLM_MODE=fake` y sin conexión
- **THEN** el run termina con plan `RECOMENDADO`

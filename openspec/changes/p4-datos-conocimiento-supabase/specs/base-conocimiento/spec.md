## ADDED Requirements

### Requirement: Un resumen por PDF oficial
`knowledge/` SHALL tener un archivo Markdown por PDF oficial listado en RF-F0-12, con *front-matter* (`fuente`, `url`, `pagina`), un resumen corto y solo artículos o páginas verificados en el texto (RF-F0-12, RT-10).

#### Scenario: Extracto truncado
- **WHEN** se resume el DS 024-2016-EM
- **THEN** no se cita ningún artículo posterior al 44

#### Scenario: PDF escaneado
- **WHEN** un PDF no tiene texto seleccionable
- **THEN** no se inventan citas: se omite o se resume solo lo verificable

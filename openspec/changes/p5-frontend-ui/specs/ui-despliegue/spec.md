## ADDED Requirements

### Requirement: Frontend local para la demo
El frontend SHALL poder construirse con `VITE_API_URL` y servirse en local con `pnpm preview`, sin depender de Vercel ni de Internet en modo replay (RF-F0-18, RF-F3-45).

#### Scenario: Sin Wi-Fi
- **WHEN** la red está apagada
- **THEN** E1–E3 en replay corren desde el frontend local

### Requirement: Vitrina en Vercel
El frontend SHALL desplegarse en Vercel como vitrina pública; si el tiempo alcanza, SHALL reproducir los replays en el navegador sin backend (RF-F0-19, RF-F3-46).

#### Scenario: Abrir la vitrina
- **WHEN** se abre la URL de Vercel
- **THEN** la página carga y muestra los escenarios disponibles

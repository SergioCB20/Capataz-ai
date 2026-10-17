// Genera src/api/schema.d.ts desde el OpenAPI de FastAPI (RF-F0-03).
// No necesita el servidor arrancado: importa la app con `uv` y vuelca app.openapi().
// Uso: pnpm gen:types   (o, con el backend arriba: pnpm gen:types:url)
import { execFileSync } from 'node:child_process'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const raiz = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const backend = resolve(raiz, '../backend')
const salidaJson = resolve(raiz, 'openapi.json')

const volcar = resolve(raiz, 'scripts/volcar_openapi.py')

// uv es un .exe: sin shell, así las rutas con espacios no se rompen.
execFileSync('uv', ['run', 'python', volcar, salidaJson], { cwd: backend, stdio: 'inherit' })
execFileSync('pnpm', ['exec', 'openapi-typescript', 'openapi.json', '-o', 'src/api/schema.d.ts'], {
  cwd: raiz,
  stdio: 'inherit',
  shell: process.platform === 'win32',
})
// Catálogo real (data/ de P4) para el modo sin servidor: mismos IDs que los replays grabados.
execFileSync('uv', ['run', 'python', resolve(raiz, 'scripts/volcar_catalogo.py'), resolve(raiz, 'src/datos/catalogo.json')], {
  cwd: backend,
  stdio: 'inherit',
})
console.log('Catálogo local actualizado (src/datos/catalogo.json).')
console.log('Tipos regenerados. Corre `pnpm typecheck` para ver si el contrato cambió algo que el frontend usa.')

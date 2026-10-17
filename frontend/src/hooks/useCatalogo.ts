import { useEffect, useState } from 'react'
import { api } from '@/api/cliente'
import type { Catalogo } from '@/api/types'
import catalogoJson from '@/datos/catalogo.json'

export interface EstadoCatalogo {
  catalogo: Catalogo
  /** true si el backend respondió; false = catálogo empaquetado en el build. */
  conBackend: boolean
  cargando: boolean
}

// Catálogo empaquetado: data/ de P4 validado por el backend (`pnpm gen:types` lo actualiza).
// Tiene los mismos IDs que los replays grabados, así que el modo sin servidor muestra nombres reales.
const catalogoLocal = catalogoJson as unknown as Catalogo

/** Catálogo del backend (GET /api/catalogo); si no responde, el empaquetado (RF-F0-13, RF-F3-45). */
export function useCatalogo(): EstadoCatalogo {
  const [estado, setEstado] = useState<EstadoCatalogo>({ catalogo: catalogoLocal, conBackend: false, cargando: true })

  useEffect(() => {
    let vivo = true
    api
      .health()
      .then(() => api.catalogo())
      .then((catalogo) => vivo && setEstado({ catalogo, conBackend: true, cargando: false }))
      .catch(() => vivo && setEstado({ catalogo: catalogoLocal, conBackend: false, cargando: false }))
    return () => {
      vivo = false
    }
  }, [])

  return estado
}

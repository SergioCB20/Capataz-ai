import { useEffect, useState } from 'react'
import { api } from '@/api/cliente'
import type { Catalogo } from '@/api/types'
import { catalogoDemo } from '@/datos/catalogoDemo'

export interface EstadoCatalogo {
  catalogo: Catalogo
  /** true si el backend respondió; false = catálogo de demostración local. */
  conBackend: boolean
  cargando: boolean
}

/** Catálogo del backend (GET /api/catalogo); si no responde, el de demostración (RF-F0-13). */
export function useCatalogo(): EstadoCatalogo {
  const [estado, setEstado] = useState<EstadoCatalogo>({ catalogo: catalogoDemo, conBackend: false, cargando: true })

  useEffect(() => {
    let vivo = true
    api
      .health()
      .then(() => api.catalogo())
      .then((catalogo) => vivo && setEstado({ catalogo, conBackend: true, cargando: false }))
      .catch(() => vivo && setEstado({ catalogo: catalogoDemo, conBackend: false, cargando: false }))
    return () => {
      vivo = false
    }
  }, [])

  return estado
}

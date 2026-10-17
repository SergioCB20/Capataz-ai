import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { MotionConfig } from 'motion/react'
import { InicioTarea } from '@/componentes/InicioTarea'
import { MenuLateral, type Pantalla } from '@/componentes/MenuLateral'
import { VistaEjecucion } from '@/componentes/VistaEjecucion'
import { useCatalogo } from '@/hooks/useCatalogo'
import { useRun, type PeticionRun } from '@/hooks/useRun'

export default function App() {
  const { catalogo, conBackend, cargando } = useCatalogo()
  const run = useRun()
  const [pantalla, setPantalla] = useState<Pantalla>('inicio')

  const iniciar = async (p: PeticionRun) => {
    await run.iniciar(p)
    setPantalla('ejecucion')
  }
  const enEjecucion = pantalla === 'ejecucion' && !!run.sesion

  return (
    <MotionConfig reducedMotion="user" transition={{ duration: 0.25, ease: 'easeOut' }}>
      <div className="min-h-screen bg-lila p-4 font-sans text-tinta sm:p-6">
        <div className="mx-auto flex max-w-[1392px] flex-wrap items-start gap-5">
          <MenuLateral pantalla={enEjecucion ? 'ejecucion' : 'inicio'} hayEjecucion={!!run.sesion} onIr={setPantalla} />
          <main className="flex min-w-0 flex-[999_1_760px] flex-col gap-5">
            {cargando ? (
              <div className="flex items-center justify-center gap-2 rounded-[28px] bg-white p-16 text-sm text-tenue">
                <Loader2 className="size-4 animate-spin" aria-hidden /> Cargando catálogo…
              </div>
            ) : enEjecucion ? (
              <VistaEjecucion run={run} catalogo={catalogo} onNuevaTarea={() => setPantalla('inicio')} />
            ) : (
              <InicioTarea
                catalogo={catalogo}
                conBackend={conBackend}
                iniciando={run.iniciando}
                error={run.errorInicio}
                onIniciar={iniciar}
              />
            )}
          </main>
        </div>
      </div>
    </MotionConfig>
  )
}

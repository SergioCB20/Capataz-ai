import { Loader2, ShieldCheck } from 'lucide-react'
import { MotionConfig } from 'motion/react'
import { InicioTarea } from '@/componentes/InicioTarea'
import { VistaEjecucion } from '@/componentes/VistaEjecucion'
import { useCatalogo } from '@/hooks/useCatalogo'
import { useRun } from '@/hooks/useRun'

export default function App() {
  const { catalogo, conBackend, cargando } = useCatalogo()
  const run = useRun()

  return (
    <MotionConfig reducedMotion="user" transition={{ duration: 0.25, ease: 'easeOut' }}>
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="mx-auto flex max-w-7xl items-center gap-2 px-6 py-3">
          <ShieldCheck aria-hidden className="size-5" />
          <span className="font-semibold">CAPATAZ</span>
          <span className="text-sm text-muted-foreground">· verificación de controles críticos antes de la tarea · datos simulados</span>
        </div>
      </header>

      {cargando ? (
        <div className="flex items-center justify-center gap-2 p-16 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" aria-hidden /> Cargando catálogo…
        </div>
      ) : run.sesion ? (
        <VistaEjecucion run={run} catalogo={catalogo} />
      ) : (
        <InicioTarea
          catalogo={catalogo}
          conBackend={conBackend}
          iniciando={run.iniciando}
          error={run.errorInicio}
          onIniciar={run.iniciar}
        />
      )}
    </div>
    </MotionConfig>
  )
}

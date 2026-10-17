// Confirmación de campo para E2c (RF-F2-32): una pregunta por requisito, Sí/No + nota.
// Al enviar, el semáforo se actualiza con los eventos siguientes (sin recargar).
import { useState } from 'react'
import { ClipboardCheck, Loader2 } from 'lucide-react'
import type { RespuestaCampo } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Textarea } from '@/components/ui/textarea'

export function FormCampo({ preguntas, enviando, error, onEnviar }: {
  preguntas: { requisito_id: string; pregunta: string }[]
  enviando: boolean
  error: string | null
  onEnviar: (respuestas: RespuestaCampo[]) => void
}) {
  const [cumple, setCumple] = useState<Record<string, boolean | undefined>>({})
  const [notas, setNotas] = useState<Record<string, string>>({})
  const [faltan, setFaltan] = useState(false)

  const enviar = () => {
    if (preguntas.some((p) => cumple[p.requisito_id] === undefined)) return setFaltan(true)
    onEnviar(preguntas.map((p) => ({ requisito_id: p.requisito_id, cumple: !!cumple[p.requisito_id], nota: notas[p.requisito_id] ?? '' })))
  }

  return (
    <Card className="gap-4 rounded-[28px] border-2 border-[#F2C76B] bg-white py-6 ring-0">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ClipboardCheck aria-hidden className="size-5 text-amber-600" /> Confirmación en campo requerida
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        <p className="text-sm text-muted-foreground">
          Estos requisitos no se pueden verificar con datos. Confírmalos en la labor; tu respuesta queda en la auditoría con tu usuario y la hora.
        </p>
        {preguntas.map((p) => (
          <fieldset key={p.requisito_id} className="grid gap-2 rounded-md border p-3">
            <legend className="px-1 text-sm font-medium">{p.pregunta}</legend>
            <RadioGroup
              value={cumple[p.requisito_id] === undefined ? '' : cumple[p.requisito_id] ? 'si' : 'no'}
              onValueChange={(v) => {
                setCumple((c) => ({ ...c, [p.requisito_id]: v === 'si' }))
                setFaltan(false)
              }}
              className="flex gap-6"
            >
              <label className="flex items-center gap-2 text-sm"><RadioGroupItem value="si" /> Sí, se cumple</label>
              <label className="flex items-center gap-2 text-sm"><RadioGroupItem value="no" /> No se cumple</label>
            </RadioGroup>
            <Textarea
              aria-label={`Nota para ${p.requisito_id}`}
              placeholder="Nota (opcional): qué se midió o vio"
              value={notas[p.requisito_id] ?? ''}
              onChange={(e) => setNotas((n) => ({ ...n, [p.requisito_id]: e.target.value }))}
            />
          </fieldset>
        ))}
        {faltan && <p className="text-sm text-red-700 dark:text-red-300">Responde Sí o No en cada pregunta antes de enviar.</p>}
        {error && <p role="alert" className="text-sm text-amber-800 dark:text-amber-200">{error}</p>}
        <div>
          <Button onClick={enviar} disabled={enviando} className="min-h-12 rounded-full bg-acento px-6 text-[15px] font-extrabold text-white hover:bg-acento/90">
            {enviando && <Loader2 className="animate-spin" aria-hidden />}
            Enviar confirmación
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

"""Genera los incidentes sintéticos de la demo (RF-F0-16, RF-F0-17). TODO es simulado.

Uso (desde la raíz del repo):
    uv run --project backend python scripts/gen_sintetico.py                  # plantillas -> data/incidentes.json
    uv run --project backend python scripts/gen_sintetico.py --modo llm -n 10 # borradores del LLM -> data/borradores/

Modo plantillas (por defecto): reproducible, sin red. Las plantillas de abajo se revisan a mano; con
la misma semilla siempre sale el mismo `data/incidentes.json`, que se versiona en Git. El sistema
nunca lo regenera al arrancar ni durante la demo.

Modo llm: pide al LLM borradores adicionales y los guarda en `data/borradores/` para revisión humana;
nunca sobrescribe `data/incidentes.json`. Requiere `LLM_MODE=real`, `LLM_MODEL` y `OPENROUTER_API_KEY`.

No genera citas normativas (RT-10) ni el resultado esperado de los casos de evaluación (RF-F3-20).
Estructura inspirada en el dataset de Kaggle «Industrial Safety and Health Analytics Database»; sus
columnas reales están POR VERIFICAR (no se descargó el CSV) y sus datos no se usan.

Diseño: el Agente Riesgo consulta los incidentes más graves de cada tipo de tarea (los 2 de mayor
`nivel_potencial` que coinciden). Por eso en cada tipo los dos primeros están pensados a propósito:
en sostenimiento, el segundo apunta a `C-SSO-PRESENTE`, el control que solo llega por incidentes.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

SEMILLA = 20261017
PLANTAS = ["Mina Santa Rosa (simulada)", "Mina Cerro Alto (simulada)", "Mina Las Lomas (simulada)"]
FUENTE = {"tipo": "simulado", "referencia": "Incidente sintético para la demo; no corresponde a un evento real"}

R_ROCA, R_MOV = "Caída de rocas", "Colisión con equipo móvil"
R_ENE, R_ALT = "Energía peligrosa no aislada", "Caída desde altura"

# (tipo_tarea, actividad, riesgo_critico, nivel_potencial, nivel_real, control_fallido, equipo, descripción, causa raíz)
SOST = ("TT-SOST", "Sostenimiento con pernos de roca", R_ROCA)
PERF = ("TT-PERF", "Perforación de frentes con jumbo")
LOTO = ("TT-LOTO", "Mantenimiento con bloqueo y etiquetado de energía", R_ENE)
ALT = ("TT-ALT", "Trabajo en altura en estructura de mina", R_ALT)

PLANTILLAS: list[tuple] = [
    # --- Sostenimiento: los dos primeros (VI y V) son los que consulta el Agente Riesgo ---
    (*SOST, "VI", "II", "C-SOST-EQ", "empernador",
     "Un bloque de roca cayó sobre la cabina del empernador mientras se instalaban pernos; el operador salió ileso gracias a la cabina protegida.",
     "Falla del sistema de empuje del empernador sin inspección previa al turno"),
    (*SOST, "V", "I", "C-SSO-PRESENTE", "empernador",
     "Desprendimiento de roca en la corona durante el sostenimiento; no había supervisor de seguridad en la labor y el desatado quedó incompleto.",
     "Sostenimiento iniciado sin supervisor de seguridad presente"),
    (*SOST, "IV", "I", "C-SOST-OPER", "empernador",
     "Pernos instalados con longitud menor a la especificada por un operador sin certificación vigente; se detectó en la inspección.",
     "Certificación del operador vencida y no revisada"),
    (*SOST, "IV", "II", "C-SOST-OPER", "jumbo empernador",
     "Un operador sin entrenamiento actualizado instaló la malla sin ajustar las placas y cayeron fragmentos de roca, sin heridos.",
     "Entrenamiento de actualización pendiente"),
    (*SOST, "IV", "I", "C-SSO-PRESENTE", "empernador",
     "Con el supervisor de seguridad ausente se sostuvo una zona fracturada y al día siguiente se halló un perno sin tensar.",
     "Supervisor de seguridad ausente durante el empernado"),
    (*SOST, "III", "I", "C-SOST-EQ", "empernador",
     "Mangueras hidráulicas deterioradas del empernador derramaron aceite en el piso de la labor; riesgo de resbalón para la cuadrilla.",
     "Mantenimiento preventivo vencido del empernador"),
    (*SOST, "III", "I", "C-SSO-PRESENTE", "empernador",
     "La cuadrilla continuó el sostenimiento tras una voladura sin esperar la revisión del supervisor de seguridad.",
     "Presión por producción y falta de supervisión"),
    (*SOST, "III", "II", "C-SOST-EQ", "jumbo empernador",
     "El empernador quedó inoperativo a mitad del turno por una falla eléctrica y se continuó con sostenimiento manual improvisado.",
     "Sin equipo de reemplazo disponible"),
    (*SOST, "II", "I", None, "empernador",
     "Un fragmento pequeño de roca golpeó el casco de un ayudante; el desatado se había hecho con una barretilla en mal estado.",
     "Herramienta de desatado en mal estado"),
    (*SOST, "II", "I", "C-SOST-OPER", "empernador",
     "El operador omitió el registro de pernos instalados y hubo que reinspeccionar la labor.",
     "Falta de registro del sostenimiento"),
    (*SOST, "II", "I", None, "empernador",
     "Cayeron trozos pequeños de roca al cambiar una broca; nadie estaba bajo el área expuesta.",
     "Cambio de broca sin retirarse de la zona de caída"),
    (*SOST, "I", "I", None, "empernador",
     "Desprendimiento menor de roca durante el pintado de la labor; sin lesiones.",
     "Roca suelta no detectada en la inspección visual"),
    # --- Perforación con jumbo: riesgo roca (V y IV primeros) y riesgo colisión (VI y V primeros) ---
    (*PERF, R_ROCA, "V", "II", "C-PERF-OPER", "jumbo",
     "Desprendimiento de roca del frente durante la perforación; el operador del jumbo no tenía vigente su certificación y no reconoció el aviso de roca suelta.",
     "Operador sin certificación vigente"),
    (*PERF, R_ROCA, "IV", "I", "C-PERF-EQ", "jumbo",
     "El brazo del jumbo con holgura excesiva desvió el barreno y aflojó la cara del frente.",
     "Holgura en el brazo del jumbo por mantenimiento atrasado"),
    (*PERF, R_ROCA, "III", "I", "C-PERF-OPER", "jumbo",
     "Un operador nuevo perforó fuera del diseño y dejó una cara irregular que luego soltó roca.",
     "Falta de acompañamiento al operador en su primera semana"),
    (*PERF, R_ROCA, "III", "I", None, "jumbo",
     "Caída de bloques pequeños al terminar la perforación, antes del desatado; sin personas en el área.",
     "Desatado postergado"),
    (*PERF, R_ROCA, "II", "I", "C-PERF-OPER", "jumbo",
     "Se perforó un taladro adicional sin autorización; se corrigió en la revisión del turno.",
     "Instrucción de perforación poco clara"),
    (*PERF, R_ROCA, "I", "I", None, "jumbo empernador",
     "Pequeño desprendimiento de roca en la caja izquierda mientras se posicionaba el equipo.",
     "Posicionamiento del equipo sin inspección de la caja"),
    (*PERF, R_MOV, "VI", "III", "C-PERF-EQ", "jumbo",
     "Un jumbo con frenos defectuosos golpeó un vehículo auxiliar en la rampa; hubo daños materiales y un lesionado leve.",
     "Frenos del jumbo fuera de especificación"),
    (*PERF, R_MOV, "V", "II", "C-PERF-OPER", "jumbo",
     "Un operador sin certificación vigente maniobró el jumbo cerca de personal a pie y lo rozó.",
     "Certificación vencida y maniobra sin señalero"),
    (*PERF, R_MOV, "III", "I", "C-PERF-EQ", "jumbo",
     "La alarma de retroceso del jumbo no sonaba y casi atropella a un ayudante.",
     "Alarma de retroceso sin verificar al inicio del turno"),
    (*PERF, R_MOV, "III", "I", "C-PERF-OPER", "jumbo",
     "El operador del jumbo no respetó la prioridad de paso en una intersección.",
     "Capacitación de tránsito subterráneo incompleta"),
    (*PERF, R_MOV, "II", "I", None, "jumbo",
     "Un jumbo quedó estacionado sin calzas en la rampa y se desplazó unos metros.",
     "Procedimiento de estacionamiento omitido"),
    (*PERF, R_MOV, "I", "I", None, "jumbo",
     "Roce leve del jumbo con la pared de la galería al girar.",
     "Visibilidad reducida por polvo"),
    # --- Bloqueo y etiquetado: los dos primeros (VI y V) ---
    (*LOTO, "VI", "III", "C-LOTO-APLICADO", "bomba de achique",
     "Un técnico inició el mantenimiento de una bomba sin comprobar energía cero; el equipo arrancó y le causó una amputación parcial.",
     "No se verificó la energía cero antes de intervenir"),
    (*LOTO, "V", "II", "C-LOTO-OPER", "tablero eléctrico",
     "Mantenimiento eléctrico a cargo de personal sin certificación de bloqueo y etiquetado; aislaron el interruptor equivocado.",
     "Personal no certificado en bloqueo y etiquetado"),
    (*LOTO, "IV", "I", "C-LOTO-KIT", "faja transportadora",
     "Faltaban candados en el kit de bloqueo y se usó un candado compartido sin identificación.",
     "Kit de bloqueo incompleto"),
    (*LOTO, "IV", "II", "C-LOTO-APLICADO", "faja transportadora",
     "Otro equipo de trabajo retiró una etiqueta de bloqueo antes de que terminara el mantenimiento.",
     "Etiqueta sin nombre ni fecha del responsable"),
    (*LOTO, "III", "I", "C-LOTO-OPER", "bomba de achique",
     "Un ayudante sin certificación colocó los candados sin supervisión del electricista.",
     "Delegación del bloqueo a personal no certificado"),
    (*LOTO, "III", "I", "C-LOTO-KIT", "tablero eléctrico",
     "El kit de bloqueo no tenía detector de tensión y se confió en la desconexión visual.",
     "Kit sin detector de tensión"),
    (*LOTO, "III", "II", "C-LOTO-APLICADO", "compresor",
     "Un compresor se presurizó durante la limpieza porque no se liberó la energía residual.",
     "Energía residual no liberada"),
    (*LOTO, "II", "I", None, "bomba de achique",
     "Se encontró un candado sin etiqueta durante la inspección de rutina.",
     "Control de candados deficiente"),
    (*LOTO, "II", "I", "C-LOTO-OPER", "faja transportadora",
     "El electricista realizó el bloqueo con una certificación próxima a vencer y sin registrar la renovación.",
     "Seguimiento de vigencias deficiente"),
    (*LOTO, "II", "I", "C-LOTO-APLICADO", "tablero eléctrico",
     "No se registró la hora de retiro del bloqueo y la reenergización tardó más de lo previsto.",
     "Registro de bloqueo incompleto"),
    (*LOTO, "I", "I", None, "compresor",
     "Etiqueta de bloqueo ilegible por humedad; se reemplazó antes de intervenir.",
     "Etiquetas no resistentes a la humedad"),
    (*LOTO, "I", "I", None, "bomba de achique",
     "Demora en conseguir el kit de bloqueo; no hubo intervención sin bloqueo.",
     "Kit compartido entre varias áreas"),
    # --- Trabajo en altura: los dos primeros (VI y V) ---
    (*ALT, "VI", "III", "C-ALT-EQ", "plataforma elevadora",
     "Una plataforma elevadora con el sistema de nivelación averiado se inclinó durante el trabajo y el técnico quedó colgado de su línea de vida.",
     "Sistema de nivelación sin inspección previa"),
    (*ALT, "V", "II", "C-ALT-OPER", "plataforma elevadora",
     "Un técnico sin certificación vigente de trabajo en altura ancló su arnés a un punto no certificado.",
     "Certificación vencida y punto de anclaje sin verificar"),
    (*ALT, "IV", "I", "C-ALT-OPER", "andamio",
     "Un trabajador sin entrenamiento en rescate en altura se retrasó en auxiliar a un compañero suspendido.",
     "Entrenamiento de rescate pendiente"),
    (*ALT, "IV", "I", "C-ALT-EQ", "plataforma elevadora",
     "La canasta de la plataforma no tenía la compuerta de seguridad bien trabada.",
     "Inspección diaria incompleta"),
    (*ALT, "III", "I", None, "andamio",
     "Cayó una herramienta desde una estructura; el área inferior no estaba delimitada.",
     "Falta de delimitación del área inferior"),
    (*ALT, "III", "II", "C-ALT-OPER", "plataforma elevadora",
     "El trabajador usó el arnés con la línea de vida enredada y casi pierde el equilibrio.",
     "Uso incorrecto del arnés"),
    (*ALT, "II", "I", None, "andamio",
     "Una escalera portátil resbaló en el piso húmedo; el trabajador logró sujetarse.",
     "Piso húmedo sin señalizar"),
    (*ALT, "II", "I", "C-ALT-EQ", "plataforma elevadora",
     "El freno de la plataforma elevadora se soltó al detenerse en pendiente.",
     "Mantenimiento de frenos postergado"),
    (*ALT, "I", "I", None, "andamio",
     "Tropiezo en una plataforma de acceso sin barandas completas; sin lesiones.",
     "Barandas desmontadas y no repuestas"),
    (*ALT, "III", "I", "C-ALT-OPER", "andamio",
     "El supervisor autorizó el trabajo sin revisar las certificaciones del personal.",
     "Revisión de certificaciones omitida"),
    (*ALT, "II", "I", "C-ALT-EQ", "plataforma elevadora",
     "La plataforma no tenía el registro de inspección del día y se usó igual.",
     "Registro de inspección ausente"),
    (*ALT, "I", "I", None, "andamio",
     "Casco mal ajustado cayó desde una plataforma elevada; sin personas debajo.",
     "Barbiquejo sin usar"),
    # --- Otros incidentes (no son de los cuatro tipos de tarea) ---
    (None, "Transporte de mineral en rampa", R_MOV, "IV", "II", None, "volquete",
     "Un volquete cargado perdió el control en una curva de la rampa y rozó la pared.", "Exceso de velocidad en curva"),
    (None, "Transporte de mineral en rampa", R_MOV, "III", "I", None, "volquete",
     "Dos volquetes se cruzaron en una zona de una sola vía sin comunicación por radio.", "Falta de radio en uno de los equipos"),
    (None, "Ventilación de labores", "Atmósfera deficiente", "IV", "I", None, "detector de gases",
     "Lectura baja de oxígeno en un fondo de saco; el personal fue evacuado a tiempo.", "Ventilación auxiliar apagada"),
    (None, "Ventilación de labores", "Atmósfera deficiente", "III", "I", None, "detector de gases",
     "El detector de gases del supervisor estaba sin calibrar.", "Calibración vencida"),
    (None, "Carguío de explosivos", "Explosión no planificada", "V", "I", None, "camión fábrica",
     "Se detectó un taladro fallado sin señalizar antes del siguiente turno.", "Registro de taladros fallados incompleto"),
    (None, "Mantenimiento mecánico en taller", "Atrapamiento", "II", "I", None, "prensa hidráulica",
     "Pellizco de dedos al sujetar una pieza en la prensa.", "Falta de herramienta para sujetar piezas"),
    (None, "Operación de compresores", "Ruido", "I", "I", None, "compresor",
     "Exposición a ruido sin protección auditiva en la sala de compresores.", "Señalización de uso de tapones ausente"),
    (None, "Almacenamiento de insumos", "Incendio", "III", "I", None, "almacén",
     "Aerosoles almacenados junto a una fuente de calor; se reubicaron.", "Almacenamiento sin clasificar"),
]


def construir() -> list[dict]:
    rng = random.Random(SEMILLA)
    inicio = date(2023, 1, 1)
    incidentes = []
    for n, plantilla in enumerate(PLANTILLAS, start=1):
        tipo, actividad, riesgo, pot, real, control, equipo, descripcion, causa = plantilla
        incidentes.append({
            "id": f"INC-{n:03d}",
            "fecha": (inicio + timedelta(days=rng.randrange(0, 1260))).isoformat(),
            "planta": rng.choice(PLANTAS),
            "nivel_real": real,
            "nivel_potencial": pot,
            "riesgo_critico": riesgo,
            "descripcion": descripcion,
            "equipo": equipo,
            "actividad": actividad,
            "tipo_tarea": tipo,
            "causa_raiz": causa,
            "control_fallido": control,
            "fuente": FUENTE,
        })
    return incidentes


async def borradores_llm(cantidad: int) -> list[dict]:
    from pydantic import BaseModel

    from app.catalogo import cargar_catalogo_desde_dir
    from app.contract import Incidente
    from app.llm import ClienteLLM

    catalogo = cargar_catalogo_desde_dir(RAIZ / "data")

    class Borradores(BaseModel):
        incidentes: list[Incidente]

    sistema = (
        "Generas incidentes de seguridad MINERA SINTÉTICOS para una demo. Todo es inventado: no cites normas "
        "ni hechos reales, usa plantas ficticias y marca fuente.tipo = simulado. `control_fallido` debe ser el ID "
        "de un control de la lista o null. Escribe en español. Termina llamando a `responder`."
    )
    usuario = json.dumps({
        "cantidad": cantidad,
        "tipos_de_tarea": [{"id": t.id, "nombre": t.nombre} for t in catalogo.tipos_tarea],
        "peligros": [p.nombre for p in catalogo.peligros],
        "controles": [{"id": c.id, "nombre": c.nombre} for c in catalogo.controles],
    }, ensure_ascii=False)
    cliente = ClienteLLM.desde_entorno()
    cliente.temperatura = 0.2
    resultado = await cliente.completar(agente="gen_incidentes", sistema=sistema, usuario=usuario, esquema=Borradores)
    return [json.loads(i.model_dump_json()) for i in resultado.incidentes]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modo", choices=["plantillas", "llm"], default="plantillas")
    parser.add_argument("-n", type=int, default=10, help="cantidad de borradores (modo llm)")
    args = parser.parse_args()

    if args.modo == "plantillas":
        destino = RAIZ / "data" / "incidentes.json"
        datos = construir()
    else:
        destino = RAIZ / "data" / "borradores" / "incidentes_llm.json"
        try:
            datos = asyncio.run(borradores_llm(args.n))
        except Exception as e:  # sin clave, sin red o salida inválida
            print(f"No se pudieron generar borradores con el LLM: {type(e).__name__}: {e}", file=sys.stderr)
            return 2
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(datos)} incidentes -> {destino.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

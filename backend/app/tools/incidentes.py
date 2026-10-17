"""`buscar_incidentes` (RF-F1-19): búsqueda determinista de incidentes similares, sin LLM.

Cada criterio dado (equipo, actividad, riesgo crítico) suma puntos si comparte alguna palabra con el
incidente (sin tildes ni mayúsculas, con una raíz simple): 2 si coincide con el campo propio del
incidente y 1 si solo coincide con su descripción. Se ordena por puntos, luego por `nivel_potencial`
(mayor primero), fecha reciente e id; se devuelven como máximo 5.
"""
import re
import unicodedata

from app.contract import Catalogo, Incidente

MAX_RESULTADOS = 5

# Orden de `nivel_potencial`. El dataset de Kaggle usa niveles romanos I–VI; los valores en
# palabras cubren textos libres. Un valor desconocido pesa 0. Ajustable cuando P4 confirme el formato.
ORDEN_NIVEL: dict[str, int] = {
    "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6,
    "bajo": 1, "medio": 3, "alto": 4, "critico": 5, "catastrofico": 6,
}
_PALABRAS_VACIAS = {"con", "del", "los", "las", "una", "uno", "por", "para", "que", "sus", "como"}


def nivel_ordinal(nivel: str | None, orden: dict[str, int] = ORDEN_NIVEL) -> int:
    clave = _sin_tildes(nivel or "").strip()
    return orden.get(clave) or (int(clave) if clave.isdigit() else 0)


def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(c))


def _raiz(palabra: str) -> str:
    return (re.sub(r"(es|s)$", "", palabra) if len(palabra) > 4 else palabra)[:6]


def _palabras(*textos: str | None) -> set[str]:
    encontradas = re.findall(r"[a-z0-9]+", _sin_tildes(" ".join(t for t in textos if t)))
    return {_raiz(p) for p in encontradas if len(p) > 2 and p not in _PALABRAS_VACIAS}


def buscar_incidentes(
    catalogo: Catalogo,
    equipo: str | None = None,
    actividad: str | None = None,
    riesgo_critico: str | None = None,
    limite: int = MAX_RESULTADOS,
) -> list[Incidente]:
    criterios = [
        (_palabras(equipo), [(lambda i: _palabras(i.equipo), 2)]),
        (_palabras(actividad), [(lambda i: _palabras(i.actividad, i.tipo_tarea), 2)]),
        (_palabras(riesgo_critico), [(lambda i: _palabras(i.riesgo_critico), 2), (lambda i: _palabras(i.descripcion), 1)]),
    ]
    criterios = [(consulta, campos) for consulta, campos in criterios if consulta]

    def puntos(incidente: Incidente) -> int:
        return sum(max((p for campo, p in campos if consulta & campo(incidente)), default=0)
                   for consulta, campos in criterios)

    puntuados = [(puntos(i), i) for i in catalogo.incidentes]
    if criterios:
        puntuados = [(n, i) for n, i in puntuados if n > 0]
    puntuados.sort(key=lambda p: (-p[0], -nivel_ordinal(p[1].nivel_potencial), -p[1].fecha.toordinal(), p[1].id))
    return [i for _, i in puntuados][:max(0, min(limite, MAX_RESULTADOS))]

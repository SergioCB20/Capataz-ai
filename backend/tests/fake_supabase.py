"""Cliente de Supabase falso para las pruebas: imita solo lo que usa `SupabaseStore` (select, eq, gt, order,
upsert con on_conflict e ignore_duplicates, insert) sobre tablas en memoria. NO prueba el servidor real."""
import asyncio
import json
from collections import defaultdict


class _Respuesta:
    def __init__(self, data):
        self.data = data


class _Consulta:
    def __init__(self, bd, tabla):
        self._bd, self._tabla = bd, tabla
        self._op, self._filtros, self._orden, self._cols = "select", [], None, "*"

    def select(self, cols="*"):
        self._op, self._cols = "select", cols
        return self

    def eq(self, col, valor):
        self._filtros.append(lambda f: f.get(col) == valor)
        return self

    def gt(self, col, valor):
        self._filtros.append(lambda f: f.get(col) > valor)
        return self

    def order(self, col):
        self._orden = col
        return self

    def upsert(self, filas, on_conflict="", ignore_duplicates=False):
        self._op, self._args = "upsert", (filas, on_conflict, ignore_duplicates)
        return self

    def insert(self, filas):
        self._op, self._args = "insert", (filas,)
        return self

    async def execute(self):
        await self._bd.antes_de_ejecutar(self._tabla)
        filas = self._tabla and self._bd.tablas[self._tabla]
        if self._op == "select":
            res = [f for f in filas if all(flt(f) for flt in self._filtros)]
            if self._orden:
                res.sort(key=lambda f: f[self._orden])
            if self._cols != "*":
                res = [{c: f[c] for c in self._cols.split(",")} for f in res]
            return _Respuesta(json.loads(json.dumps(res)))
        nuevas = self._args[0] if isinstance(self._args[0], list) else [self._args[0]]
        for fila in nuevas:
            fila = json.loads(json.dumps(fila))  # falla si no es JSON puro, como PostgREST
            if self._op == "insert":
                fila["id"] = len(filas) + 1
                filas.append(fila)
                continue
            _, on_conflict, ignorar = self._args
            claves = on_conflict.split(",") if on_conflict else ["id"]
            existente = next((f for f in filas if all(f.get(c) == fila.get(c) for c in claves)), None)
            if existente is None:
                filas.append(fila)
            elif not ignorar:
                existente.update(fila)
        return _Respuesta(nuevas)


class FakeSupabase:
    def __init__(self):
        self.tablas = defaultdict(list)
        self.llamadas = 0
        self.fallo = None      # excepción a lanzar en cada llamada
        self.demora_s = 0.0    # espera antes de responder

    def table(self, nombre):
        return _Consulta(self, nombre)

    async def antes_de_ejecutar(self, tabla):
        self.llamadas += 1
        if self.demora_s:
            await asyncio.sleep(self.demora_s)
        if self.fallo:
            raise self.fallo

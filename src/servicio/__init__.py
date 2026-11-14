"""Fachada única: orquestación, registro, modo de respaldo, salud y auditoría.

Dueño: Anderson. La app SOLO importa este módulo (y contratos):

    cargar_archivo(origen) -> ReporteCalidad
    consultar(customer_id, fecha, metodo="modelo") -> Decision
    responder(propuesta_id, accion) -> dict          accion: "aprobar" | "rechazar"
    salud() -> dict                                  p50, p95, tasa_error, tasa_respaldo, consultas
    auditar(registro_id) -> dict                     entradas, decisión, hashes y si se reproduce

Flujo de consultar: ingesta -> (modelo | regla2 | regla1) -> motor -> registro.
Respaldo: si el método pedido falla (no implementado, historia insuficiente, sin
modelo entrenado, modelo no adoptado), se usa el siguiente escalón y
Decision.respaldo es True. Nada se ejecuta: responder solo anota la decisión.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import time
from datetime import date, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import pandas as pd

from contratos import (
    COLUMNAS_MOVIMIENTO,
    Accion,
    Config,
    Decision,
    EstadoPersona,
    Metodo,
    Pronostico,
    ReporteCalidad,
    cargar_config,
    hash_config,
    validar_historia,
)
from servicio import observabilidad as _salud
from servicio.registro import (
    agregar_jsonl,
    buscar,
    construir_registro,
    leer_jsonl,
    leer_registros,
    nuevo_id,
    registrar,
    ruta_absoluta,
)

METODOS: tuple[str, ...] = ("regla1", "regla2", "modelo")
ESCALERA: dict[str, tuple[str, ...]] = {
    "modelo": ("modelo", "regla2", "regla1"),
    "regla2": ("regla2", "regla1"),
    "regla1": ("regla1",),
}
MENSAJE_SIMULACION = "Simulación: no se movió ningún dinero."


class ErrorServicio(Exception):
    """Error con un mensaje para la persona (qué corregir) y un detalle técnico."""

    def __init__(self, mensaje_usuario: str, detalle: str = "") -> None:
        super().__init__(mensaje_usuario)
        self.mensaje_usuario = mensaje_usuario
        self.detalle = detalle


# --------------------------------------------------------------------------- #
# Estado del proceso (datos cargados, configuración, modelo en memoria)
# --------------------------------------------------------------------------- #

_ESTADO: dict[str, Any] = {}


def reiniciar() -> None:
    """Olvida datos, configuración y modelo cargados (pruebas y cambio de archivo)."""
    _ESTADO.clear()
    _ESTADO.update(cfg=None, movimientos=None, pagos=None, reporte=None, origen=None, modelo=None)


reiniciar()


def _cfg() -> Config:
    if _ESTADO["cfg"] is None:
        _ESTADO["cfg"] = cargar_config()
    return _ESTADO["cfg"]


def _capa(nombre: str) -> ModuleType:
    """Importa una capa interna. Las pruebas lo reemplazan por dobles."""
    return importlib.import_module(nombre)


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #


def _a_fecha(fecha: date | datetime | str) -> date:
    if isinstance(fecha, datetime):
        return fecha.date()
    if isinstance(fecha, date):
        return fecha
    try:
        return date.fromisoformat(str(fecha))
    except ValueError:
        raise ErrorServicio(f"Fecha inválida: '{fecha}'. Usa el formato AAAA-MM-DD.") from None


def _describir_origen(origen: Any) -> str:
    if isinstance(origen, (str, Path)):
        ruta = Path(origen).resolve()
        try:
            return ruta.relative_to(ruta_absoluta(".").resolve()).as_posix()
        except ValueError:
            return str(ruta)
    return f"<archivo subido: {getattr(origen, 'name', type(origen).__name__)}>"


def _a_dict(pago: Any) -> dict[str, Any]:
    return pago.model_dump() if hasattr(pago, "model_dump") else dict(pago)


def _como(clase: type, valor: Any) -> Any:
    """Acepta el contrato aunque venga de otra copia del módulo (p. ej. src.contratos)."""
    if isinstance(valor, clase):
        return valor
    return clase.model_validate(valor.model_dump() if hasattr(valor, "model_dump") else valor)


def _hash_historia(historia: pd.DataFrame) -> str:
    columnas = [c for c in COLUMNAS_MOVIMIENTO if c in historia.columns]
    csv = historia[columnas].to_csv(index=False, lineterminator="\n")
    return hashlib.sha256(csv.encode("utf-8")).hexdigest()[:16]


def _saldo(historia: pd.DataFrame) -> float:
    """Último saldo informado; si no hay, la suma de los montos."""
    if "saldo" in historia.columns:
        con_saldo = historia["saldo"].dropna()
        if not con_saldo.empty:
            return float(con_saldo.iloc[-1])
    return float(historia["monto"].sum())


def _cronometro(operacion: str, metodo: str | None = None):
    """Mide la operación y la anota en logs/salud.jsonl (también si falla)."""

    class _Medida:
        def __init__(self) -> None:
            self.metodo = metodo
            self.respaldo = False

        def __enter__(self) -> _Medida:
            self.t0 = time.perf_counter()
            return self

        def __exit__(self, tipo, error, tb) -> bool:
            ms = (time.perf_counter() - self.t0) * 1000
            _salud.anotar(
                _cfg()["ruta_salud"],
                operacion,
                ms,
                metodo=self.metodo,
                respaldo=self.respaldo,
                error=type(error).__name__ if error else None,
            )
            return False

    return _Medida()


# --------------------------------------------------------------------------- #
# Datos
# --------------------------------------------------------------------------- #


def _ingerir(origen: Any, cfg: Config) -> tuple[pd.DataFrame, ReporteCalidad, list[dict[str, Any]]]:
    df, reporte, pagos = _capa("ingesta").cargar(origen, cfg)
    return df, _como(ReporteCalidad, reporte), [_a_dict(p) for p in pagos]


def cargar_archivo(origen: Any) -> ReporteCalidad:
    """Valida y limpia un archivo con el contrato de datos y lo deja activo para consultar."""
    cfg = _cfg()
    with _cronometro("cargar_archivo"):
        df, reporte, pagos = _ingerir(origen, cfg)
        _ESTADO.update(movimientos=df, pagos=pagos, reporte=reporte, origen=_describir_origen(origen))
    return reporte


def _datos_activos() -> dict[str, Any]:
    if _ESTADO["movimientos"] is None:
        for ruta in _cfg()["rutas_datos"]:
            if ruta_absoluta(ruta).exists():
                cargar_archivo(ruta_absoluta(ruta))
                break
        else:
            raise ErrorServicio(
                "No hay datos cargados. Genera los datos con `python tareas.py datos` o carga un archivo.",
                detalle=f"no existe ninguna de {list(_cfg()['rutas_datos'])}",
            )
    return _ESTADO


def _datos_para_auditar(origen: str, cfg: Config) -> tuple[pd.DataFrame, list[dict[str, Any]]] | None:
    if _ESTADO["movimientos"] is not None and _ESTADO["origen"] == origen:
        return _ESTADO["movimientos"], _ESTADO["pagos"]
    ruta = ruta_absoluta(origen)
    if origen.startswith("<") or not ruta.exists():
        return None
    df, _, pagos = _ingerir(ruta, cfg)
    return df, pagos


# --------------------------------------------------------------------------- #
# Pronóstico con escalera de respaldo
# --------------------------------------------------------------------------- #


def _modelo_adoptado(cfg: Config) -> tuple[bool, str]:
    """Sin eval/resultados/adopcion.json todavía no hay veredicto: se intenta el modelo."""
    ruta = ruta_absoluta(cfg["ruta_adopcion"])
    if not ruta.exists():
        return True, "sin veredicto de adopción todavía"
    veredicto = json.loads(ruta.read_text(encoding="utf-8"))
    return bool(veredicto.get("adopta")), str(veredicto.get("razon", ""))


def _modelo_entrenado(cfg: Config) -> Any:
    ruta = ruta_absoluta(cfg["ruta_modelo"])
    if not ruta.exists():
        raise FileNotFoundError(f"no hay modelo entrenado en {cfg['ruta_modelo']}")
    marca = (str(ruta), ruta.stat().st_mtime_ns)
    if _ESTADO["modelo"] is None or _ESTADO["modelo"][0] != marca:
        _ESTADO["modelo"] = (marca, _capa("modelo").Modelo.cargar(ruta))
    return _ESTADO["modelo"][1]


def _predecir(metodo: str, historia: pd.DataFrame, fecha: date, cfg: Config) -> Pronostico:
    if metodo == "modelo":
        adoptado, razon = _modelo_adoptado(cfg)
        if not adoptado:
            raise RuntimeError(f"modelo no adoptado: {razon}")
        pron = _modelo_entrenado(cfg).predecir(historia, fecha)
    else:
        pron = getattr(_capa("reglas"), metodo)(historia, fecha, cfg)
    return _como(Pronostico, pron)


def _pronosticar(
    historia: pd.DataFrame, fecha: date, metodo: str, cfg: Config
) -> tuple[Pronostico, str, list[str]]:
    motivos: list[str] = []
    for escalon in ESCALERA[metodo]:
        try:
            return _predecir(escalon, historia, fecha, cfg), escalon, motivos
        except Exception as e:  # noqa: BLE001 - cualquier falla baja un escalón (modo de respaldo)
            motivos.append(f"{escalon}: {type(e).__name__}: {e}")
    raise ErrorServicio(
        "No pudimos calcular el pronóstico para esta persona y fecha.", detalle=" | ".join(motivos)
    )


# --------------------------------------------------------------------------- #
# Cálculo puro de una recomendación (lo usan consultar y auditar)
# --------------------------------------------------------------------------- #


def _armar(
    customer_id: str,
    fecha: date,
    metodo: str,
    movimientos: pd.DataFrame,
    pagos: list[dict[str, Any]],
    cfg: Config,
) -> tuple[EstadoPersona, Pronostico, str, list[str], pd.DataFrame]:
    """Estado de la persona y pronóstico con la escalera de respaldo (lo comparten consultar y simular)."""
    ingesta = _capa("ingesta")
    de_la_persona = movimientos[movimientos["customer_id"] == customer_id]
    if de_la_persona.empty:
        raise ErrorServicio(f"No hay movimientos para la persona '{customer_id}'.")
    historia = de_la_persona[de_la_persona["fecha_hora"] < pd.Timestamp(fecha)]
    historia = historia.sort_values(["fecha_hora", "transaction_id"], kind="mergesort")
    if historia.empty:
        raise ErrorServicio(f"La persona '{customer_id}' no tiene movimientos antes del {fecha:%d/%m/%Y}.")
    validar_historia(historia)

    estado = EstadoPersona(
        customer_id=customer_id,
        fecha_corte=fecha,
        saldo=_saldo(historia),
        pagos=ingesta.proximos_pagos(pagos, customer_id, fecha, cfg["ventana_dias"]),
        colchon=cfg["colchon"] or 0.0,
        semanas_historia=ingesta.semanas_historia(movimientos, customer_id, fecha),
    )
    pron, metodo_usado, motivos = _pronosticar(historia, fecha, metodo, cfg)
    return estado, pron, metodo_usado, motivos, historia


def _calcular(
    customer_id: str,
    fecha: date,
    metodo: str,
    movimientos: pd.DataFrame,
    pagos: list[dict[str, Any]],
    cfg: Config,
) -> tuple[Decision, dict[str, Any]]:
    estado, pron, metodo_usado, motivos, historia = _armar(customer_id, fecha, metodo, movimientos, pagos, cfg)
    decision = _como(Decision, _capa("motor").decidir(estado, pron, cfg))
    decision = decision.model_copy(update={"respaldo": metodo_usado != metodo})
    info = {
        "metodo_usado": metodo_usado,
        "motivos_respaldo": motivos,
        "hash_historia": _hash_historia(historia),
    }
    return decision, info


def _sin_id(decision: dict[str, Any] | None) -> dict[str, Any] | None:
    return None if decision is None else {k: v for k, v in decision.items() if k != "registro_id"}


# --------------------------------------------------------------------------- #
# API pública
# --------------------------------------------------------------------------- #


def consultar(customer_id: str, fecha: date | datetime | str, metodo: Metodo = "modelo") -> Decision:
    """Número de hoy para una persona y fecha de corte, con su registro auditable."""
    cfg = _cfg()
    with _cronometro("consultar", metodo) as medida:
        if metodo not in METODOS:
            raise ErrorServicio(f"Método desconocido '{metodo}'. Usa uno de {list(METODOS)}.")
        fecha = _a_fecha(fecha)
        datos = _datos_activos()
        decision, info = _calcular(customer_id, fecha, metodo, datos["movimientos"], datos["pagos"], cfg)

        registro_id = nuevo_id()
        decision = decision.model_copy(update={"registro_id": registro_id})
        entradas = {
            "customer_id": customer_id,
            "fecha": fecha.isoformat(),
            "metodo_pedido": metodo,
            "origen": datos["origen"],
            **info,
        }
        registrar(
            construir_registro(entradas, cfg, registro_id, decision.model_dump(mode="json")),
            cfg["ruta_registro"],
        )
        medida.metodo = info["metodo_usado"]
        medida.respaldo = decision.respaldo
    return decision


def simular(customer_id: str, fecha: date | datetime | str, escenario: Any) -> Decision:
    """Decision de un escenario hipotético ("¿y si cobro S/200 el día 5?") con motor.simular y el mismo estado y
    pronóstico que consultar. No se registra: no es una recomendación. `respaldo` marca si el pronóstico bajó de escalón."""
    cfg = _cfg()
    with _cronometro("simular", "modelo") as medida:
        fecha = _a_fecha(fecha)
        datos = _datos_activos()
        estado, pron, metodo_usado, _, _ = _armar(customer_id, fecha, "modelo", datos["movimientos"], datos["pagos"], cfg)
        decision = _como(Decision, _capa("motor.simular").simular(estado, pron, escenario, cfg))
        decision = decision.model_copy(update={"respaldo": metodo_usado != "modelo"})
        medida.metodo, medida.respaldo = metodo_usado, decision.respaldo
    return decision


def responder(propuesta_id: str, accion: Accion) -> dict[str, Any]:
    """Anota si la persona aprueba o rechaza una propuesta. No ejecuta nada."""
    cfg = _cfg()
    with _cronometro("responder"):
        if accion not in ("aprobar", "rechazar"):
            raise ErrorServicio(f"Acción desconocida '{accion}'. Usa 'aprobar' o 'rechazar'.")
        registro_id = next(
            (
                r.registro_id
                for r in reversed(leer_registros(cfg["ruta_registro"]))
                if r.decision
                and any(p.get("propuesta_id") == propuesta_id for p in r.decision.get("propuestas", []))
            ),
            None,
        )
        if registro_id is None:
            raise ErrorServicio(f"No existe la propuesta '{propuesta_id}'. Vuelve a consultar el número de hoy.")
        previas = [r for r in leer_jsonl(cfg["ruta_respuestas"]) if r.get("propuesta_id") == propuesta_id]
        if previas:
            return {
                "ok": False,
                "propuesta_id": propuesta_id,
                "accion": previas[-1]["accion"],
                "registro_id": registro_id,
                "mensaje": f"Esta propuesta ya fue respondida ({previas[-1]['accion']}). {MENSAJE_SIMULACION}",
            }
        agregar_jsonl(
            {
                "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
                "propuesta_id": propuesta_id,
                "accion": accion,
                "registro_id": registro_id,
            },
            cfg["ruta_respuestas"],
        )
    return {
        "ok": True,
        "propuesta_id": propuesta_id,
        "accion": accion,
        "registro_id": registro_id,
        "mensaje": MENSAJE_SIMULACION,
    }


def salud() -> dict[str, Any]:
    """Resumen de logs/salud.jsonl: p50 y p95 en ms, tasas de error y de respaldo, consultas."""
    return _salud.resumen(_cfg()["ruta_salud"])


def auditar(registro_id: str) -> dict[str, Any]:
    """Reconstruye una recomendación desde su identificador y dice si se reproduce."""
    cfg = _cfg()
    registro = buscar(registro_id, cfg["ruta_registro"])
    if registro is None:
        return {"registro_id": registro_id, "encontrado": False, "se_reproduce": False,
                "motivo": "No existe ese identificador en el registro."}

    e = registro.entradas
    salida: dict[str, Any] = {
        "registro_id": registro_id,
        "encontrado": True,
        "entradas": e,
        "decision": registro.decision,
        "version_generador": registro.version_generador,
        "version_modelo": registro.version_modelo,
        "semilla": registro.semilla,
        "hash_config": registro.hash_config,
        "hash_config_actual": hash_config(cfg),
        "misma_config": registro.hash_config == hash_config(cfg),
    }
    datos = _datos_para_auditar(e["origen"], cfg)
    if datos is None:
        return {**salida, "se_reproduce": False, "motivo": f"Los datos de origen ya no están: {e['origen']}"}

    try:
        decision, info = _calcular(e["customer_id"], _a_fecha(e["fecha"]), e["metodo_pedido"], *datos, cfg)
    except Exception as err:  # noqa: BLE001 - el resultado de la auditoría lo informa
        return {**salida, "se_reproduce": False, "motivo": f"No se pudo recalcular: {type(err).__name__}: {err}"}

    nueva = _sin_id(decision.model_dump(mode="json"))
    guardada = _sin_id(registro.decision)
    diferencias = sorted(k for k in (nueva or {}) if (guardada or {}).get(k) != nueva[k])
    mismos_datos = info["hash_historia"] == e.get("hash_historia")
    mismo_metodo = info["metodo_usado"] == e.get("metodo_usado")
    return {
        **salida,
        "mismos_datos": mismos_datos,
        "mismo_metodo": mismo_metodo,
        "diferencias": diferencias,
        "se_reproduce": not diferencias and mismos_datos and mismo_metodo,
    }


__all__ = [
    "ErrorServicio",
    "auditar",
    "cargar_archivo",
    "consultar",
    "reiniciar",
    "responder",
    "salud",
    "simular",
]

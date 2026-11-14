"""Contratos entre módulos (Anexo A de la v7 y Anexo 4 de los planes individuales).

Cualquier cambio en este archivo necesita la aprobación de Anderson y de Gino
y se anota en DECISIONES.md. La prueba tests/contract/ falla si un campo cambia.

Donde la v7 y los planes difieren se eligió la forma compatible con ambos
(ver DECISIONES.md, entradas 9 a 17).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# --------------------------------------------------------------------------- #
# Tipos comunes
# --------------------------------------------------------------------------- #

Tipo = Literal["ingreso", "gasto"]
Semaforo = Literal["verde", "ambar", "rojo"]
Confianza = Literal["alta", "media", "baja"]
Metodo = Literal["regla1", "regla2", "modelo"]
Accion = Literal["aprobar", "rechazar"]
FuenteExplicacion = Literal["plantilla", "generativa"]
Horizonte = Literal[3, 7, 14]

HORIZONTES: tuple[int, ...] = (3, 7, 14)
NOMBRES_CUANTILES: tuple[str, ...] = ("p5", "p20", "p50", "p80")

# Columnas del CSV del generador (sección 6). Las etiquetas de referencia son la
# verdad conocida por el generador y SOLO se usan para evaluar: nunca entran al
# modelo, al motor ni a la interfaz (regla anti fuga).
COLUMNAS_MOVIMIENTO: tuple[str, ...] = (
    "customer_id",
    "transaction_id",
    "fecha_hora",
    "monto",
    "moneda",
    "tipo",
    "categoria",
    "comercio",
    "saldo",
)
# ingreso_recurrente: opcional del generador. atipico_detectado: la agrega la ingesta (Anexo 5).
COLUMNAS_OPCIONALES: tuple[str, ...] = ("ingreso_recurrente", "atipico_detectado")
ETIQUETAS_REFERENCIA: tuple[str, ...] = (
    "es_duplicado",
    "es_atipico",
    "pago_con_fecha",
    "arquetipo",
)
CATEGORIAS: tuple[str, ...] = (
    "alquiler",
    "servicios",
    "alimentacion",
    "transporte",
    "deuda",
    "suscripcion",
    "otros",
)


class _Contrato(BaseModel):
    """Base: inmutable, rechaza campos desconocidos y valores no finitos."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, frozen=True)


# --------------------------------------------------------------------------- #
# Datos e ingesta
# --------------------------------------------------------------------------- #


class Movimiento(_Contrato):
    customer_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    fecha_hora: datetime
    monto: float
    moneda: Literal["PEN"] = "PEN"
    tipo: Tipo
    categoria: str
    comercio: str
    saldo: float | None = None

    @model_validator(mode="after")
    def _signo_coherente(self) -> Movimiento:
        # Sección 6: positivo para ingresos y negativo para gastos.
        if self.tipo == "ingreso" and self.monto < 0:
            raise ValueError("un ingreso no puede tener monto negativo")
        if self.tipo == "gasto" and self.monto > 0:
            raise ValueError("un gasto no puede tener monto positivo")
        return self


class PagoInferido(_Contrato):
    """Pago con fecha inferido por la ingesta (mismo comercio, monto parecido,
    día del mes repetido). La ingesta puede devolverlo como dict con estas
    mismas claves; el servicio lo convierte en PagoConFecha con
    ingesta.proximos_pagos para una fecha de corte."""

    customer_id: str = Field(min_length=1)
    comercio: str
    categoria: str
    monto: float = Field(ge=0, description="Monto típico en soles, en positivo")
    dia_mes: int = Field(ge=1, le=31)
    ocurrencias: int | None = Field(default=None, ge=1)


class ReporteCalidad(_Contrato):
    filas_entrada: int = Field(ge=0)
    filas_salida: int = Field(ge=0)
    duplicados_eliminados: int = Field(ge=0)
    faltantes: dict[str, int] = Field(default_factory=dict)
    atipicos: int = Field(ge=0)
    suscripciones_duplicadas: list[dict[str, Any]] = Field(default_factory=list)
    pagos_inferidos: list[PagoInferido] = Field(default_factory=list)
    pii_enmascarado: int = Field(default=0, ge=0)
    columnas_sensibles_descartadas: list[str] = Field(default_factory=list)
    rechazos: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _filas(self) -> ReporteCalidad:
        if self.filas_salida > self.filas_entrada:
            raise ValueError("filas_salida no puede superar filas_entrada")
        return self


# --------------------------------------------------------------------------- #
# Estado, pronóstico y decisión
# --------------------------------------------------------------------------- #


class PagoConFecha(_Contrato):
    pago_id: str = Field(min_length=1)
    dia: int = Field(ge=0, description="Días desde la fecha de corte hasta el pago")
    monto: float = Field(ge=0)
    categoria: str


class EstadoPersona(_Contrato):
    customer_id: str = Field(min_length=1)
    fecha_corte: date
    saldo: float
    pagos: list[PagoConFecha] = Field(default_factory=list)
    colchon: float = Field(default=0.0, ge=0)
    semanas_historia: int = Field(default=0, ge=0)


class Cuantiles(_Contrato):
    """Ingreso acumulado: nunca negativo y ordenado (Anexo C: se rechazan negativos)."""

    p5: float = Field(ge=0)
    p20: float = Field(ge=0)
    p50: float = Field(ge=0)
    p80: float = Field(ge=0)

    @model_validator(mode="after")
    def _ordenados(self) -> Cuantiles:
        if not (self.p5 <= self.p20 <= self.p50 <= self.p80):
            raise ValueError(
                "cuantiles cruzados: debe cumplirse p5 <= p20 <= p50 <= p80 "
                "(ordénalos después de predecir)"
            )
        return self


class Pronostico(_Contrato):
    """Ingreso acumulado pronosticado a 3, 7 y 14 días."""

    por_horizonte: dict[Horizonte, Cuantiles]

    @field_validator("por_horizonte", mode="before")
    @classmethod
    def _claves_json_a_entero(cls, v: Any) -> Any:
        # En JSON las claves son texto ("3"); en Python son enteros (3).
        if isinstance(v, dict):
            return {int(k) if isinstance(k, str) and k.isdigit() else k: c for k, c in v.items()}
        return v

    @field_validator("por_horizonte")
    @classmethod
    def _todos_los_horizontes(cls, v: dict[int, Cuantiles]) -> dict[int, Cuantiles]:
        faltan = set(HORIZONTES) - set(v)
        if faltan:
            raise ValueError(f"faltan horizontes: {sorted(faltan)}")
        return v


class DecisionPago(_Contrato):
    pago_id: str = Field(min_length=1)
    dia: int = Field(ge=0)
    monto: float = Field(ge=0)
    permitido: float
    semaforo: Semaforo


# Nombre que usan los planes individuales (Anexo 4). Es la misma clase.
PagoDecision = DecisionPago


class Propuesta(_Contrato):
    propuesta_id: str = Field(min_length=1)
    texto: str
    monto: float = Field(ge=0)
    pago_id: str = Field(min_length=1)
    antes: dict[str, Any]
    despues: dict[str, Any]
    confianza: Confianza


class Decision(_Contrato):
    # Acepta entero (soles redondeados hacia abajo, como en el plan del motor) o decimal.
    numero_hoy: float = Field(ge=0)
    por_pago: list[DecisionPago] = Field(default_factory=list)
    confianza: Confianza
    desglose: dict[str, Any] = Field(default_factory=dict)
    limites: list[str] = Field(default_factory=list)
    supuestos: list[str] = Field(default_factory=list)
    evidencia: dict[str, Any] = Field(default_factory=dict)
    propuestas: list[Propuesta] = Field(default_factory=list)
    respaldo: bool = False
    registro_id: str = ""
    mensaje_falta: str | None = None
    explicacion: str = ""
    explicacion_fuente: FuenteExplicacion = "plantilla"


class Registro(_Contrato):
    """Una línea JSON por recomendación, para poder reproducirla y auditarla."""

    registro_id: str = Field(min_length=1)
    entradas: dict[str, Any]
    version_generador: str
    version_modelo: str
    semilla: int
    hash_config: str = Field(min_length=1)
    decision: dict[str, Any] | None = None


__all__ = [
    "Accion",
    "CATEGORIAS",
    "COLUMNAS_MOVIMIENTO",
    "COLUMNAS_OPCIONALES",
    "Confianza",
    "Cuantiles",
    "Decision",
    "DecisionPago",
    "ETIQUETAS_REFERENCIA",
    "EstadoPersona",
    "FuenteExplicacion",
    "HORIZONTES",
    "Horizonte",
    "Metodo",
    "Movimiento",
    "NOMBRES_CUANTILES",
    "PagoConFecha",
    "PagoDecision",
    "PagoInferido",
    "Pronostico",
    "Propuesta",
    "Registro",
    "ReporteCalidad",
    "Semaforo",
    "Tipo",
]

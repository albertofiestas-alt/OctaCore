"""Conformidad de los esquemas con el plan de ingesta (Anexos 1, 2, 4 y 5 y sección 5).

No prueba la lógica de la ingesta (eso va en las demás pruebas de esta carpeta):
fija que los contratos, la configuración y las firmas que la ingesta consume y
produce sigan siendo los del plan. Si una falla, avisa a Anderson y a Gino antes
de tocar nada en src/contratos.
"""

from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import ingesta
from contratos import (
    COLUMNAS_MOVIMIENTO,
    ETIQUETAS_REFERENCIA,
    EstadoPersona,
    HistoriaInvalida,
    Movimiento,
    PagoConFecha,
    ReporteCalidad,
    cargar_config,
    validar_historia,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


@pytest.fixture(scope="module")
def cfg():
    return cargar_config()


# --------------------------------------------------------------------------- #
# Anexo 4: campos de los modelos que toca la ingesta
# --------------------------------------------------------------------------- #

CAMPOS_PLAN = {
    Movimiento: {
        "customer_id", "transaction_id", "fecha_hora", "monto", "moneda",
        "tipo", "categoria", "comercio", "saldo",
    },
    PagoConFecha: {"pago_id", "dia", "monto", "categoria"},
    EstadoPersona: {"customer_id", "fecha_corte", "saldo", "pagos", "colchon", "semanas_historia"},
    ReporteCalidad: {
        "filas_entrada", "filas_salida", "duplicados_eliminados", "faltantes", "atipicos",
        "suscripciones_duplicadas", "pagos_inferidos", "pii_enmascarado",
        "columnas_sensibles_descartadas", "rechazos",
    },
}


@pytest.mark.parametrize("modelo", CAMPOS_PLAN, ids=lambda m: m.__name__)
def test_campos_del_anexo_4(modelo):
    assert set(modelo.model_fields) == CAMPOS_PLAN[modelo]


def test_columnas_de_movimiento_siguen_el_anexo_4():
    assert set(COLUMNAS_MOVIMIENTO) == CAMPOS_PLAN[Movimiento]


def test_etiquetas_de_referencia_son_las_cuatro_del_plan():
    assert set(ETIQUETAS_REFERENCIA) == {"es_duplicado", "es_atipico", "pago_con_fecha", "arquetipo"}


def test_movimiento_solo_acepta_pen():
    base = dict(customer_id="P0001", transaction_id="t1", fecha_hora="2025-01-01T10:00:00",
                monto=-10.0, tipo="gasto", categoria="otros", comercio="X")
    assert Movimiento(**base).moneda == "PEN"
    with pytest.raises(ValidationError):
        Movimiento(**base, moneda="USD")


def test_modelos_rechazan_campos_extra_como_edad():
    # Anti fuga y privacidad: un campo sensible no puede colarse en un contrato.
    with pytest.raises(ValidationError):
        Movimiento(customer_id="P0001", transaction_id="t1", fecha_hora="2025-01-01T10:00:00",
                   monto=-10.0, tipo="gasto", categoria="otros", comercio="X", edad=30)


def test_reporte_calidad_acepta_la_salida_prevista_de_cargar():
    # Defaults del plan: pii_enmascarado 0, sensibles [], rechazos {}.
    r = ReporteCalidad(
        filas_entrada=10, filas_salida=9, duplicados_eliminados=1, faltantes={}, atipicos=0,
        suscripciones_duplicadas=[],
        pagos_inferidos=[{"customer_id": "P0001", "comercio": "Casero", "categoria": "alquiler",
                          "dia_mes": 5, "monto": 800.0, "ocurrencias": 4}],
    )
    assert (r.pii_enmascarado, r.columnas_sensibles_descartadas, r.rechazos) == (0, [], {})


def test_reporte_calidad_rechaza_mas_salida_que_entrada():
    with pytest.raises(ValidationError):
        ReporteCalidad(filas_entrada=1, filas_salida=2, duplicados_eliminados=0,
                       faltantes={}, atipicos=0, suscripciones_duplicadas=[], pagos_inferidos=[])


def test_fixture_de_reporte_cumple_el_contrato():
    datos = json.loads((FIXTURES / "reporte_calidad_ejemplo.json").read_text(encoding="utf-8"))
    ReporteCalidad.model_validate(datos)


# --------------------------------------------------------------------------- #
# Anexo 5: firmas y excepción de la ingesta
# --------------------------------------------------------------------------- #

FIRMAS_PLAN = {
    "cargar": ["origen", "cfg"],
    "proximos_pagos": ["pagos_inferidos", "customer_id", "fecha_corte", "ventana"],
    "semanas_historia": ["movimientos", "customer_id", "fecha_corte"],
    "cargar_etiquetas": ["origen"],
    "detectar_pii": ["texto", "cfg"],
    "enmascarar_pii": ["df", "cfg"],
}


@pytest.mark.parametrize("nombre,params", FIRMAS_PLAN.items())
def test_firma_de_ingesta(nombre, params):
    assert list(inspect.signature(getattr(ingesta, nombre)).parameters) == params


def test_ventana_por_defecto_es_14():
    assert inspect.signature(ingesta.proximos_pagos).parameters["ventana"].default == 14


def test_error_ingesta_expone_mensaje_usuario_y_detalle():
    e = ingesta.ErrorIngesta("Falta la columna monto", "columnas: monto")
    assert e.mensaje_usuario == "Falta la columna monto"
    assert e.detalle == "columnas: monto"
    assert isinstance(e, Exception)


# --------------------------------------------------------------------------- #
# Anexo 2: configuración común
# --------------------------------------------------------------------------- #


def test_variables_sensibles_son_las_del_plan(cfg):
    assert set(cfg["variables_sensibles"]) == {
        "edad", "genero", "ubicacion", "distrito", "nombre", "dni", "telefono"
    }


def test_patrones_pii_en_el_orden_del_plan(cfg):
    # La tarjeta va primero para que no se parta en pedazos de teléfono o DNI.
    assert list(cfg["patrones_pii"]) == ["tarjeta", "telefono", "dni", "correo"]


@pytest.mark.parametrize(
    "texto,tipo",
    [
        ("4111 1111 1111 1111", "tarjeta"),
        ("4111-1111-1111-1111", "tarjeta"),
        ("4111111111111111", "tarjeta"),
        ("987654321", "telefono"),
        ("12345678", "dni"),
        ("ana.perez+x@correo.com.pe", "correo"),
    ],
)
def test_patron_pii_detecta_su_tipo(cfg, texto, tipo):
    assert re.search(cfg["patrones_pii"][tipo], texto)


@pytest.mark.parametrize("texto", ["P0001", "SIN_COMERCIO", "alquiler", "Tienda 24 horas", "1234567"])
def test_patrones_pii_no_marcan_identificadores_ni_texto_comun(cfg, texto):
    assert not any(re.search(p, texto) for p in cfg["patrones_pii"].values())


def test_dni_de_9_digitos_no_es_dni(cfg):
    # Aislado de otros dígitos: 9 dígitos que no empiezan en 9 no deben marcarse como DNI.
    assert not re.search(cfg["patrones_pii"]["dni"], "123456789")


# --------------------------------------------------------------------------- #
# config/ingesta.yaml (sección 5, "PII y columnas sensibles")
# --------------------------------------------------------------------------- #


def test_config_de_ingesta_tiene_los_valores_del_plan(cfg):
    assert dict(cfg["ingesta"]) == {
        "max_mb": 50,
        "mad_k": 5,
        "tol_monto": 0.10,
        "tol_dia": 3,
        "min_ocurrencias": 3,
        "ventana_suscripcion_dias": 30,
    }


# --------------------------------------------------------------------------- #
# Movimientos limpios: columnas y anti fuga (contratos.historia)
# --------------------------------------------------------------------------- #


def _historia():
    import pandas as pd

    return pd.DataFrame(
        {
            "customer_id": ["P0001"], "transaction_id": ["t1"],
            "fecha_hora": pd.to_datetime(["2025-01-01 10:00"]), "monto": [-10.0],
            "moneda": ["PEN"], "tipo": ["gasto"], "categoria": ["otros"],
            "comercio": ["X"], "saldo": [None], "atipico_detectado": [False],
        }
    )


def test_historia_limpia_con_atipico_detectado_es_valida():
    validar_historia(_historia())


@pytest.mark.parametrize("etiqueta", sorted(ETIQUETAS_REFERENCIA))
def test_historia_con_etiqueta_es_rechazada_por_fuga(etiqueta):
    df = _historia()
    df[etiqueta] = False
    with pytest.raises(HistoriaInvalida):
        validar_historia(df)

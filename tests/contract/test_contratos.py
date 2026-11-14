"""Pruebas de contrato (P0, dueño: Anderson).

Fallan si alguien cambia un campo de src/contratos sin aprobación: la lista de
campos esperados está escrita aquí a propósito, copiada del Anexo A.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from contratos import (
    ETIQUETAS_REFERENCIA,
    Config,
    Cuantiles,
    Decision,
    EstadoPersona,
    HistoriaInvalida,
    Movimiento,
    PagoConFecha,
    PagoInferido,
    Pronostico,
    Propuesta,
    Registro,
    ReporteCalidad,
    cargar_config,
    hash_config,
    validar_historia,
)
from contratos.modelos import DecisionPago

CAMPOS_ANEXO_A = {
    Movimiento: ["customer_id", "transaction_id", "fecha_hora", "monto", "moneda", "tipo",
                 "categoria", "comercio", "saldo"],
    ReporteCalidad: ["filas_entrada", "filas_salida", "duplicados_eliminados", "faltantes",
                     "atipicos", "suscripciones_duplicadas", "pagos_inferidos"],
    PagoConFecha: ["pago_id", "dia", "monto", "categoria"],
    PagoInferido: ["customer_id", "comercio", "categoria", "monto", "dia_mes"],
    EstadoPersona: ["customer_id", "fecha_corte", "saldo", "pagos", "colchon"],
    Cuantiles: ["p5", "p20", "p50", "p80"],
    Pronostico: ["por_horizonte"],
    DecisionPago: ["pago_id", "permitido", "semaforo"],
    Decision: ["numero_hoy", "por_pago", "confianza", "desglose", "limites", "propuestas"],
    Propuesta: ["propuesta_id", "texto", "monto", "pago_id", "antes", "despues", "confianza"],
    Registro: ["entradas", "version_generador", "version_modelo", "semilla", "hash_config"],
}


@pytest.mark.parametrize("modelo", list(CAMPOS_ANEXO_A), ids=lambda m: m.__name__)
def test_campos_no_cambian_sin_aprobacion(modelo):
    assert list(modelo.model_fields) == CAMPOS_ANEXO_A[modelo], (
        f"{modelo.__name__} cambió. Requiere aprobación de Anderson y Gino y una entrada en DECISIONES.md"
    )


# --------------------------------------------------------------------------- #
# Todas las fixtures cumplen el contrato
# --------------------------------------------------------------------------- #

def test_fixtures_validan(estado_orden_pagos, pronostico_orden_pagos, decision_orden_pagos,
                          estado_tipico, pronostico_tipico, decision_tipica,
                          decision_sin_historia, reporte_calidad, registro):
    assert decision_orden_pagos.numero_hoy == 0
    assert any("faltan S/200" in l for l in decision_orden_pagos.limites)
    assert decision_tipica.propuestas, "la fixture típica debe traer una propuesta para maquetar"
    assert decision_sin_historia.propuestas == []


def test_fixtures_ida_y_vuelta_json(decision_tipica, pronostico_tipico):
    assert Decision.model_validate_json(decision_tipica.model_dump_json()) == decision_tipica
    assert Pronostico.model_validate_json(pronostico_tipico.model_dump_json()) == pronostico_tipico


def test_pronostico_acepta_claves_texto_de_json(pronostico_tipico):
    assert set(pronostico_tipico.por_horizonte) == {3, 7, 14}


# --------------------------------------------------------------------------- #
# Reglas que el contrato hace cumplir
# --------------------------------------------------------------------------- #

def test_cuantiles_cruzados_se_rechazan():
    with pytest.raises(ValidationError, match="cuantiles cruzados"):
        Cuantiles(p5=10, p20=5, p50=20, p80=30)


def test_cuantiles_iguales_se_aceptan():
    Cuantiles(p5=0, p20=0, p50=0, p80=0)


def test_pronostico_exige_los_tres_horizontes():
    c = {"p5": 0, "p20": 1, "p50": 2, "p80": 3}
    with pytest.raises(ValidationError, match="faltan horizontes"):
        Pronostico(por_horizonte={3: c, 7: c})


def test_pronostico_rechaza_horizonte_desconocido():
    c = {"p5": 0, "p20": 1, "p50": 2, "p80": 3}
    with pytest.raises(ValidationError):
        Pronostico(por_horizonte={3: c, 7: c, 14: c, 30: c})


def test_numero_hoy_nunca_negativo():
    with pytest.raises(ValidationError):
        Decision(numero_hoy=-1, confianza="alta")


@pytest.mark.parametrize("valor", [float("nan"), float("inf"), float("-inf")])
def test_no_finitos_se_rechazan(valor):
    with pytest.raises(ValidationError):
        EstadoPersona(customer_id="C1", fecha_corte=date(2025, 1, 1), saldo=valor, colchon=0)


def test_campos_extra_se_rechazan():
    with pytest.raises(ValidationError):
        PagoConFecha(pago_id="x", dia=1, monto=1, categoria="otros", arquetipo="conductor")


def test_semaforo_y_confianza_cerrados():
    with pytest.raises(ValidationError):
        DecisionPago(pago_id="x", permitido=0, semaforo="amarillo")
    with pytest.raises(ValidationError):
        Decision(numero_hoy=0, confianza="muy alta")


@pytest.mark.parametrize("tipo,monto", [("ingreso", -5.0), ("gasto", 5.0)])
def test_signo_del_monto_coherente_con_tipo(tipo, monto):
    with pytest.raises(ValidationError):
        Movimiento(customer_id="C1", transaction_id="T1", fecha_hora=datetime(2025, 1, 1),
                   monto=monto, tipo=tipo, categoria="otros", comercio="X")


def test_contratos_son_inmutables(decision_tipica):
    with pytest.raises(ValidationError):
        decision_tipica.numero_hoy = 999


def test_reporte_no_puede_crear_filas():
    with pytest.raises(ValidationError):
        ReporteCalidad(filas_entrada=1, filas_salida=2, duplicados_eliminados=0, atipicos=0)


# --------------------------------------------------------------------------- #
# Historia (DataFrame) y regla anti fuga
# --------------------------------------------------------------------------- #

def test_historia_minima_valida(historia_minima):
    validar_historia(historia_minima)


def test_csv_crudo_con_etiquetas_es_fuga(ruta_movimientos_minimo):
    crudo = pd.read_csv(ruta_movimientos_minimo, parse_dates=["fecha_hora"])
    assert set(ETIQUETAS_REFERENCIA) <= set(crudo.columns)
    with pytest.raises(HistoriaInvalida, match="fuga"):
        validar_historia(crudo)


def test_historia_sin_columnas_dice_cuales_faltan(historia_minima):
    with pytest.raises(HistoriaInvalida, match="monto"):
        validar_historia(historia_minima.drop(columns=["monto"]))


# --------------------------------------------------------------------------- #
# Configuración
# --------------------------------------------------------------------------- #

def test_config_carga_y_respeta_anexo_b(cfg: Config):
    assert cfg.horizontes_dias == (3, 7, 14)
    assert cfg.cuantiles == (0.05, 0.20, 0.50, 0.80)
    assert cfg.cuantil_conservador == 0.20
    assert len(cfg.semillas_evaluacion) >= 20


def test_hash_config_estable(cfg):
    assert hash_config(cfg) == hash_config(cargar_config())
    assert len(hash_config(cfg)) == 16


def test_hash_config_cambia_con_un_parametro(cfg):
    otro = cfg.model_copy(update={"cuantil_conservador": 0.05})
    assert hash_config(otro) != hash_config(cfg)


def test_config_rechaza_valores_desconocidos(tmp_path: Path):
    ruta = tmp_path / "c.yaml"
    ruta.write_text("horizontes_dias: [3, 7, 14]\nparametro_magico: 1\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        cargar_config(ruta)

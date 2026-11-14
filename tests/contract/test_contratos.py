"""Pruebas de contrato (P0, dueño: Anderson).

Fallan si alguien cambia un campo de src/contratos sin aprobación: la lista de
campos esperados está escrita aquí a propósito, copiada del Anexo A de la v7.
"""

from __future__ import annotations

import copy
import pickle
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
from contratos.modelos import DecisionPago, PagoDecision

CAMPOS_ANEXO_A = {
    Movimiento: ["customer_id", "transaction_id", "fecha_hora", "monto", "moneda", "tipo",
                 "categoria", "comercio", "saldo"],
    ReporteCalidad: ["filas_entrada", "filas_salida", "duplicados_eliminados", "faltantes",
                     "atipicos", "suscripciones_duplicadas", "pagos_inferidos",
                     "pii_enmascarado", "columnas_sensibles_descartadas", "rechazos"],
    PagoConFecha: ["pago_id", "dia", "monto", "categoria"],
    PagoInferido: ["customer_id", "comercio", "categoria", "monto", "dia_mes", "ocurrencias"],
    EstadoPersona: ["customer_id", "fecha_corte", "saldo", "pagos", "colchon", "semanas_historia"],
    Cuantiles: ["p5", "p20", "p50", "p80"],
    Pronostico: ["por_horizonte"],
    DecisionPago: ["pago_id", "dia", "monto", "permitido", "semaforo"],
    Decision: ["numero_hoy", "por_pago", "confianza", "desglose", "limites", "supuestos",
               "evidencia", "propuestas", "respaldo", "registro_id", "mensaje_falta",
               "explicacion", "explicacion_fuente"],
    Propuesta: ["propuesta_id", "texto", "monto", "pago_id", "antes", "despues", "confianza"],
    Registro: ["registro_id", "entradas", "version_generador", "version_modelo", "semilla",
               "hash_config", "decision"],
}


@pytest.mark.parametrize("modelo", list(CAMPOS_ANEXO_A), ids=lambda m: m.__name__)
def test_campos_no_cambian_sin_aprobacion(modelo):
    assert list(modelo.model_fields) == CAMPOS_ANEXO_A[modelo], (
        f"{modelo.__name__} cambió. Requiere aprobación de Anderson y Gino y una entrada en DECISIONES.md"
    )


# --------------------------------------------------------------------------- #
# Todas las fixtures cumplen el contrato
# --------------------------------------------------------------------------- #

def test_fixtures_validan(estado_caso_orden_pagos, pronostico_caso_orden_pagos, decision_sin_alcance,
                          estado_tipico, pronostico_tipico, decision_verde, decision_rojo,
                          decision_confianza_baja, reporte_calidad_ejemplo, registro):
    assert decision_sin_alcance.numero_hoy == 0
    assert "faltan S/200" in decision_sin_alcance.mensaje_falta
    assert decision_rojo.numero_hoy == 0 and decision_rojo.mensaje_falta
    assert any(p.semaforo == "rojo" for p in decision_rojo.por_pago)
    assert decision_verde.propuestas, "la fixture verde debe traer una propuesta para maquetar"
    assert decision_confianza_baja.confianza == "baja"
    assert decision_confianza_baja.propuestas == []
    assert reporte_calidad_ejemplo.columnas_sensibles_descartadas == ["edad"]
    assert estado_caso_orden_pagos.semanas_historia == 12


@pytest.mark.parametrize("nombre", ["decision_verde", "decision_rojo", "decision_confianza_baja",
                                    "decision_sin_alcance"])
def test_fixtures_de_decision_traen_supuestos_evidencia_y_limites(nombre, request):
    """P0 del pack: toda Decision trae supuestos, evidencia, límites y confianza no vacíos."""
    d = request.getfixturevalue(nombre)
    assert d.supuestos and d.evidencia and d.limites and d.confianza
    assert "rango_14d" in d.evidencia, "la pantalla Por qué lee evidencia['rango_14d']"


def test_fixtures_ida_y_vuelta_json(decision_verde, pronostico_tipico):
    assert Decision.model_validate_json(decision_verde.model_dump_json()) == decision_verde
    assert Pronostico.model_validate_json(pronostico_tipico.model_dump_json()) == pronostico_tipico


def test_pronostico_acepta_claves_texto_de_json(pronostico_tipico):
    assert set(pronostico_tipico.por_horizonte) == {3, 7, 14}


def test_nombres_antiguos_de_fixtures_siguen_funcionando(decision_tipica, decision_verde,
                                                         estado_orden_pagos, estado_caso_orden_pagos):
    assert decision_tipica == decision_verde
    assert estado_orden_pagos == estado_caso_orden_pagos


# --------------------------------------------------------------------------- #
# Reglas que el contrato hace cumplir
# --------------------------------------------------------------------------- #

def test_cuantiles_cruzados_se_rechazan():
    with pytest.raises(ValidationError, match="cuantiles cruzados"):
        Cuantiles(p5=10, p20=5, p50=20, p80=30)


def test_cuantiles_iguales_se_aceptan():
    Cuantiles(p5=0, p20=0, p50=0, p80=0)


def test_cuantiles_negativos_se_rechazan():
    """Anexo C: pronóstico con valores negativos. Recorta a 0 antes de construir."""
    with pytest.raises(ValidationError):
        Cuantiles(p5=-1, p20=0, p50=1, p80=2)


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


def test_numero_hoy_acepta_entero_y_decimal():
    assert Decision(numero_hoy=20, confianza="alta").numero_hoy == 20
    assert Decision(numero_hoy=17.5, confianza="alta").numero_hoy == 17.5


def test_decision_minima_tiene_valores_por_defecto():
    d = Decision(numero_hoy=0, confianza="baja")
    assert d.respaldo is False and d.registro_id == "" and d.mensaje_falta is None
    assert d.explicacion_fuente == "plantilla" and d.supuestos == [] and d.evidencia == {}


def test_explicacion_fuente_cerrada():
    with pytest.raises(ValidationError):
        Decision(numero_hoy=0, confianza="baja", explicacion_fuente="chatbot")


def test_pago_decision_es_el_mismo_contrato():
    assert PagoDecision is DecisionPago


def test_estado_acepta_semanas_historia_y_colchon_por_defecto():
    e = EstadoPersona(customer_id="P1", fecha_corte=date(2025, 1, 1), saldo=0)
    assert e.colchon == 0 and e.semanas_historia == 0


def test_reporte_acepta_pagos_inferidos_como_dict_de_la_ingesta():
    r = ReporteCalidad(filas_entrada=1, filas_salida=1, duplicados_eliminados=0, atipicos=0,
                       pagos_inferidos=[{"customer_id": "P1", "comercio": "X", "categoria": "alquiler",
                                         "monto": 300, "dia_mes": 5, "ocurrencias": 3}])
    assert r.pagos_inferidos[0].dia_mes == 5
    assert r.pii_enmascarado == 0 and r.columnas_sensibles_descartadas == [] and r.rechazos == {}


@pytest.mark.parametrize("valor", [float("nan"), float("inf"), float("-inf")])
def test_no_finitos_se_rechazan(valor):
    with pytest.raises(ValidationError):
        EstadoPersona(customer_id="C1", fecha_corte=date(2025, 1, 1), saldo=valor, colchon=0)


def test_campos_extra_se_rechazan():
    with pytest.raises(ValidationError):
        PagoConFecha(pago_id="x", dia=1, monto=1, categoria="otros", arquetipo="conductor")


def test_semaforo_y_confianza_cerrados():
    with pytest.raises(ValidationError):
        DecisionPago(pago_id="x", dia=1, monto=1, permitido=0, semaforo="amarillo")
    with pytest.raises(ValidationError):
        Decision(numero_hoy=0, confianza="muy alta")


@pytest.mark.parametrize("tipo,monto", [("ingreso", -5.0), ("gasto", 5.0)])
def test_signo_del_monto_coherente_con_tipo(tipo, monto):
    with pytest.raises(ValidationError):
        Movimiento(customer_id="C1", transaction_id="T1", fecha_hora=datetime(2025, 1, 1),
                   monto=monto, tipo=tipo, categoria="otros", comercio="X")


def test_contratos_son_inmutables(decision_verde):
    with pytest.raises(ValidationError):
        decision_verde.numero_hoy = 999


def test_reporte_no_puede_crear_filas():
    with pytest.raises(ValidationError):
        ReporteCalidad(filas_entrada=1, filas_salida=2, duplicados_eliminados=0, atipicos=0)


# --------------------------------------------------------------------------- #
# Historia (DataFrame) y regla anti fuga
# --------------------------------------------------------------------------- #

def test_historia_minima_valida(historia_minima):
    validar_historia(historia_minima)


def test_historia_admite_atipico_detectado(historia_minima):
    validar_historia(historia_minima.assign(atipico_detectado=False))


def test_csv_crudo_con_etiquetas_es_fuga(ruta_movimientos_minimo):
    crudo = pd.read_csv(ruta_movimientos_minimo, parse_dates=["fecha_hora"])
    assert set(ETIQUETAS_REFERENCIA) <= set(crudo.columns)
    with pytest.raises(HistoriaInvalida, match="fuga"):
        validar_historia(crudo)


def test_historia_sin_columnas_dice_cuales_faltan(historia_minima):
    with pytest.raises(HistoriaInvalida, match="monto"):
        validar_historia(historia_minima.drop(columns=["monto"]))


# --------------------------------------------------------------------------- #
# Configuración (base.yaml + un archivo por dueño)
# --------------------------------------------------------------------------- #

BASE = Path(__file__).resolve().parents[2] / "config" / "base.yaml"


def _carpeta_config(tmp_path: Path, **otros: str) -> Path:
    (tmp_path / "base.yaml").write_text(BASE.read_text(encoding="utf-8"), encoding="utf-8")
    for nombre, texto in otros.items():
        (tmp_path / f"{nombre}.yaml").write_text(texto, encoding="utf-8")
    return tmp_path / "base.yaml"


def test_config_carga_y_respeta_anexo_b(cfg: Config):
    assert cfg["horizontes_dias"] == (3, 7, 14)
    assert cfg["cuantiles"] == (0.05, 0.20, 0.50, 0.80)
    assert cfg["cuantil_conservador"] == 0.20
    assert len(cfg["semillas_evaluacion"]) >= 20
    assert {"edad", "genero", "ubicacion", "nombre"} <= set(cfg["variables_sensibles"])
    assert set(cfg["patrones_pii"]) == {"tarjeta", "telefono", "dni", "correo"}
    assert cfg["generativa"]["activada"] is False


def test_config_se_lee_como_dict_y_como_atributo(cfg):
    assert isinstance(cfg, dict)
    assert cfg["cuantil_conservador"] == cfg.cuantil_conservador
    assert cfg["generativa"]["max_palabras"] == cfg.generativa.max_palabras


def test_config_une_el_archivo_de_cada_duenio(tmp_path):
    ruta = _carpeta_config(tmp_path, ingesta="max_mb: 50\nmad_k: 5\n", motor="")
    cfg = cargar_config(ruta)
    assert cfg["ingesta"]["max_mb"] == 50
    assert cfg["motor"] == {}


def test_config_rechaza_archivo_que_choca_con_base(tmp_path):
    ruta = _carpeta_config(tmp_path, colchon="x: 1\n")
    with pytest.raises(ValueError, match="choca"):
        cargar_config(ruta)


def test_config_es_de_solo_lectura(cfg):
    with pytest.raises(TypeError):
        cfg["colchon"] = 10
    with pytest.raises(TypeError):
        cfg.colchon = 10
    with pytest.raises(TypeError):
        cfg["generativa"]["activada"] = True


def test_config_con_devuelve_copia(cfg):
    otro = cfg.con(cuantil_conservador=0.05)
    assert otro["cuantil_conservador"] == 0.05 and cfg["cuantil_conservador"] == 0.20


def test_config_se_puede_guardar_con_pickle(cfg):
    """El modelo se guarda con joblib junto con su cfg."""
    assert pickle.loads(pickle.dumps(cfg)) == cfg
    assert copy.deepcopy(cfg) == cfg


def test_hash_config_estable(cfg):
    assert hash_config(cfg) == hash_config(cargar_config())
    assert len(hash_config(cfg)) == 16


def test_hash_config_cambia_con_un_parametro(cfg):
    assert hash_config(cfg.con(cuantil_conservador=0.05)) != hash_config(cfg)


def test_config_rechaza_valores_desconocidos(tmp_path: Path):
    ruta = tmp_path / "c.yaml"
    ruta.write_text("horizontes_dias: [3, 7, 14]\nparametro_magico: 1\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        cargar_config(ruta)


def test_generativa_no_se_enciende_sin_decision(tmp_path):
    ruta = _carpeta_config(tmp_path)
    ruta.write_text(ruta.read_text(encoding="utf-8").replace("activada: false", "activada: true"),
                    encoding="utf-8")
    with pytest.raises(ValidationError, match="opción B"):
        cargar_config(ruta)

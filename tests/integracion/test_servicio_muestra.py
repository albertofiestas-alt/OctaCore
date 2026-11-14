"""Punta a punta con capas REALES y tres personas de data/muestra (ingesta, reglas, motor, servicio).

Sin dobles: archivo -> ingesta -> escalera modelo/regla2/regla1 -> motor -> Registro -> salud -> auditoría.
"""

from __future__ import annotations

import json
from datetime import date

import pytest

import servicio
from contratos import Decision

PERSONAS = ["P0001", "P0002", "P0003"]
FECHA = date(2026, 11, 14)


@pytest.fixture
def srv(cfg, tmp_path):
    servicio.reiniciar()
    servicio._ESTADO["cfg"] = cfg.con(
        rutas_datos=["data/muestra/movimientos.csv"],
        ruta_modelo=str(tmp_path / "modelo.joblib"),
        ruta_adopcion=str(tmp_path / "adopcion.json"),
        ruta_registro=str(tmp_path / "recomendaciones.jsonl"),
        ruta_respuestas=str(tmp_path / "respuestas.jsonl"),
        ruta_salud=str(tmp_path / "salud.jsonl"),
    )
    yield servicio
    servicio.reiniciar()


def _lineas(ruta):
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines()]


@pytest.mark.parametrize("persona", PERSONAS)
def test_decision_completa_con_regla2(srv, persona, tmp_path):
    d = srv.consultar(persona, FECHA, "regla2")
    assert isinstance(d, Decision)
    assert d.numero_hoy >= 0 and d.numero_hoy == int(d.numero_hoy)
    assert d.respaldo is False
    assert d.registro_id.startswith("R-")
    assert len(d.supuestos) == 5 and len(d.limites) >= 3 and d.explicacion
    assert d.evidencia["semanas_historia"] > 0
    assert d.desglose["puntos_de_control"] and d.desglose["cuantil"] == "p20"
    assert d.confianza in ("alta", "media", "baja")
    assert all(p.semaforo in ("verde", "ambar", "rojo") for p in d.por_pago)
    # registro, salud y auditoría
    (linea,) = _lineas(tmp_path / "recomendaciones.jsonl")
    assert linea["registro_id"] == d.registro_id and linea["entradas"]["customer_id"] == persona
    assert srv.auditar(d.registro_id)["se_reproduce"] is True
    assert srv.salud()["consultas"] == 1


def test_modelo_no_adoptado_usa_regla2_con_respaldo(srv, tmp_path):
    (tmp_path / "adopcion.json").write_text(json.dumps({"adopta": False, "razon": "no supera a regla2"}), "utf-8")
    pedido = srv.consultar("P0002", FECHA, "modelo")
    base = srv.consultar("P0002", FECHA, "regla2")
    assert pedido.respaldo is True and base.respaldo is False
    assert pedido.numero_hoy == base.numero_hoy  # es la regla2 en ambos casos
    entradas = _lineas(tmp_path / "recomendaciones.jsonl")[0]["entradas"]
    assert entradas["metodo_usado"] == "regla2"
    assert "modelo no adoptado" in " ".join(entradas["motivos_respaldo"])


def test_sin_veredicto_ni_modelo_cae_a_regla2(srv, tmp_path):
    d = srv.consultar("P0001", FECHA, "modelo")  # sin adopcion.json se intenta el modelo; no hay entrenado
    assert d.respaldo is True
    entradas = _lineas(tmp_path / "recomendaciones.jsonl")[0]["entradas"]
    assert entradas["metodo_usado"] == "regla2"
    assert "no hay modelo entrenado" in entradas["motivos_respaldo"][0]
    assert srv.salud()["tasa_respaldo"] == 1.0


def test_persona_o_fecha_sin_datos_da_mensaje_claro(srv):
    with pytest.raises(servicio.ErrorServicio, match="No hay movimientos para la persona 'P9999'"):
        srv.consultar("P9999", FECHA, "regla2")
    with pytest.raises(servicio.ErrorServicio, match="no tiene movimientos antes del"):
        srv.consultar("P0001", date(2020, 1, 1), "regla2")
    with pytest.raises(servicio.ErrorServicio, match="Fecha inválida"):
        srv.consultar("P0001", "14/11/2026", "regla2")


def test_simular_con_el_motor_oficial(srv):
    from contratos import Escenario, IngresoExtra

    base = srv.consultar("P0001", FECHA, "regla2")
    vacio = srv.simular("P0001", FECHA, Escenario())
    assert int(vacio.numero_hoy) == int(base.numero_hoy)  # escenario vacío = decidir
    gasto = srv.simular("P0001", FECHA, Escenario(gasto_hoy=80))
    assert int(gasto.numero_hoy) <= int(base.numero_hoy) and gasto.evidencia["escenario"]["gasto_hoy"] == 80.0
    cobro = srv.simular("P0001", FECHA, Escenario(ingresos_extra=[IngresoExtra(dia=5, monto=200.0)]))
    assert int(cobro.numero_hoy) >= int(base.numero_hoy)

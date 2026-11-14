"""Flujo de punta a punta con las capas REALES (P0, dueño: Anderson). Meta del control 1 (13:00).

archivo -> ingesta -> regla 2 -> motor -> servicio -> Decision registrada y auditable.

Está marcado xfail(strict=True) mientras ingesta, reglas y motor sean esqueletos.
Cuando las tres capas funcionen, esta prueba empieza a pasar, `strict` la marca
como fallo y Anderson quita la marca: ese es el aviso de que el control 1 está listo.
"""

from __future__ import annotations

from datetime import date

import pytest

import servicio
from contratos import Decision


@pytest.fixture
def srv_real(cfg, tmp_path, ruta_movimientos_minimo):
    servicio.reiniciar()
    servicio._ESTADO["cfg"] = cfg.con(
        rutas_datos=[str(ruta_movimientos_minimo)],
        ruta_modelo=str(tmp_path / "modelo.joblib"),
        ruta_adopcion=str(tmp_path / "adopcion.json"),
        ruta_registro=str(tmp_path / "recomendaciones.jsonl"),
        ruta_respuestas=str(tmp_path / "respuestas.jsonl"),
        ruta_salud=str(tmp_path / "salud.jsonl"),
    )
    yield servicio
    servicio.reiniciar()


@pytest.mark.xfail(strict=True, raises=NotImplementedError,
                   reason="control 1 (13:00): faltan ingesta (Mathias), regla 2 (Rafael) y motor (Sebastián)")
def test_flujo_completo_con_regla2(srv_real):
    d = srv_real.consultar("P0002", date(2025, 11, 20), "regla2")
    assert isinstance(d, Decision)
    assert d.registro_id and d.supuestos and d.evidencia and d.limites
    assert srv_real.auditar(d.registro_id)["se_reproduce"] is True
    assert srv_real.salud()["consultas"] == 1

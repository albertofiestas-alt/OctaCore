from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from contratos import Pronostico
from modelo import HistoriaInsuficiente, Modelo, entrenar

FECHAS = [date(2025, 6, 10), date(2025, 9, 15), date(2026, 3, 3), date(2026, 11, 20)]
NOMBRES = ("p5", "p20", "p50", "p80")


def _flat(p: Pronostico) -> list[float]:
    return [getattr(p.por_horizonte[h], n) for h in (3, 7, 14) for n in NOMBRES]


def test_hay_12_modelos(modelo_entrenado):
    assert len(modelo_entrenado.modelos) == 12


@pytest.mark.parametrize("fecha", FECHAS)
def test_pronostico_valido_ordenado_y_no_negativo(modelo_entrenado, historia, fecha):
    p = modelo_entrenado.predecir(historia, fecha)
    assert isinstance(p, Pronostico)
    assert set(p.por_horizonte) == {3, 7, 14}
    for c in p.por_horizonte.values():
        assert 0 <= c.p5 <= c.p20 <= c.p50 <= c.p80
    Pronostico.model_validate(p.model_dump())  # el contrato pydantic lo acepta


def test_cuantiles_ordenados_en_todas_las_personas(modelo_entrenado, movimientos):
    for _, h in movimientos.groupby("customer_id"):
        p = modelo_entrenado.predecir(h, date(2026, 6, 1))
        for c in p.por_horizonte.values():
            assert 0 <= c.p5 <= c.p20 <= c.p50 <= c.p80


def test_determinismo_misma_semilla_mismas_predicciones(movimientos, cfg_modelo, historia):
    a = entrenar(movimientos, cfg_modelo, 7)
    b = entrenar(movimientos, cfg_modelo, 7)
    for f in FECHAS:
        assert _flat(a.predecir(historia, f)) == _flat(b.predecir(historia, f))


def test_guardar_y_cargar_predice_igual(modelo_entrenado, historia, tmp_path):
    ruta = tmp_path / "m.joblib"
    modelo_entrenado.guardar(ruta)
    cargado = Modelo.cargar(ruta)
    assert isinstance(cargado, Modelo)
    for f in FECHAS:
        assert _flat(cargado.predecir(historia, f)) == _flat(modelo_entrenado.predecir(historia, f))


def test_historia_corta_lanza_historia_insuficiente(modelo_entrenado, historia):
    dos_semanas = historia["fecha_hora"].min().normalize() + pd.Timedelta(days=14)
    corta = historia[historia["fecha_hora"] < dos_semanas]
    with pytest.raises(HistoriaInsuficiente):
        modelo_entrenado.predecir(corta, dos_semanas.date())


def test_entrenar_rechaza_etiquetas_de_referencia(movimientos, cfg_modelo):
    sucio = movimientos.assign(arquetipo="asalariado")
    with pytest.raises(ValueError):
        entrenar(sucio, cfg_modelo, 1)


def test_el_modelo_distingue_personas(modelo_entrenado, movimientos):
    """El P50 a 14 días no puede ser idéntico para todas las personas (señal mínima)."""
    p50 = {
        cid: modelo_entrenado.predecir(h, date(2026, 6, 1)).por_horizonte[14].p50
        for cid, h in movimientos.groupby("customer_id")
    }
    assert len({round(v, 2) for v in p50.values()}) > 1
    assert np.isfinite(list(p50.values())).all()

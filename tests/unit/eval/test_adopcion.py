"""Regla de adopción pre-registrada (eval/adopcion.py) con fronteras de juguete.

eval/ no es un paquete: el módulo se carga por ruta.
Frontera de juguete: regla2 en P20 deja 10 % de pagos descubiertos con gasto 100.
El modelo, interpolado a ese 10 %, permite el gasto que cada prueba indique.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[3]


def _cargar():
    spec = importlib.util.spec_from_file_location("eval_adopcion", RAIZ / "eval" / "adopcion.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def adopcion(tmp_path, monkeypatch):
    mod = _cargar()
    monkeypatch.setattr(mod, "RUTA_SALIDA", tmp_path / "adopcion.json")
    return mod


def _p(metodo, cuantil, pct, gasto):
    return {"metodo": metodo, "cuantil": cuantil, "pct_descubiertos": pct, "gasto_permitido": gasto}


def frontera(gasto_modelo_en_10pct):
    """regla2: (P5 0.02, 60) (P20 0.10, 100) (P50 0.30, 160). modelo: pasa por (0.10, g) y (0.02, g-30) y (0.30, g+40)."""
    g = gasto_modelo_en_10pct
    return [
        _p("regla2", 0.05, 0.02, 60), _p("regla2", 0.20, 0.10, 100), _p("regla2", 0.50, 0.30, 160),
        _p("modelo", 0.05, 0.02, g - 30), _p("modelo", 0.20, 0.10, g), _p("modelo", 0.50, 0.30, g + 40),
    ]


PREREG = {"umbral_adopcion_mejora": 10, "cuantil_conservador": 0.20}


def test_adopta_si_mejora_en_prueba_y_perturbado(adopcion):
    r = adopcion.decidir_adopcion(frontera(115), frontera(112), [], PREREG)
    assert r["adopta"] is True
    assert "prueba" in r["razon"] and "perturbado" in r["razon"]


def test_no_adopta_si_la_mejora_es_menor_al_umbral(adopcion):
    r = adopcion.decidir_adopcion(frontera(105), frontera(105), [], PREREG)
    assert r["adopta"] is False


def test_umbral_exacto_adopta(adopcion):
    assert adopcion.decidir_adopcion(frontera(110), frontera(110), [], PREREG)["adopta"] is True


def test_gana_solo_en_la_prueba_no_adopta(adopcion):
    r = adopcion.decidir_adopcion(frontera(130), frontera(95), [], PREREG)
    assert r["adopta"] is False
    assert "perturbado" in r["razon"]


def test_gana_solo_en_el_perturbado_no_adopta(adopcion):
    r = adopcion.decidir_adopcion(frontera(95), frontera(130), [], PREREG)
    assert r["adopta"] is False
    assert "prueba" in r["razon"]


def test_interpola_al_pct_de_regla2(adopcion):
    # El modelo no tiene punto en 10 %: (0.02, 80) y (0.30, 220) -> en 0.10 interpola 120.
    f = [_p("regla2", 0.20, 0.10, 100),
         _p("modelo", 0.05, 0.02, 80), _p("modelo", 0.50, 0.30, 220)]
    r = adopcion.decidir_adopcion(f, f, [], PREREG)
    assert r["adopta"] is True


def test_sin_cruce_de_rango_no_adopta_ni_extrapola(adopcion):
    # El modelo siempre deja mas pagos descubiertos que regla2: no hay punto comparable.
    f = [_p("regla2", 0.20, 0.10, 100), _p("modelo", 0.20, 0.25, 500), _p("modelo", 0.50, 0.40, 900)]
    r = adopcion.decidir_adopcion(f, f, [], PREREG)
    assert r["adopta"] is False
    assert "sin punto comparable" in r["razon"]


def test_escribe_el_json_del_veredicto(adopcion):
    r = adopcion.decidir_adopcion(frontera(115), frontera(115), [], PREREG)
    escrito = json.loads(adopcion.RUTA_SALIDA.read_text(encoding="utf-8"))
    assert escrito == r
    assert set(escrito) == {"adopta", "razon"}
    assert isinstance(escrito["adopta"], bool) and isinstance(escrito["razon"], str)


@pytest.mark.parametrize("prereg", [
    {"umbral_adopcion_mejora": None, "cuantil_conservador": 0.20},
    {"cuantil_conservador": 0.20},
    {"umbral_adopcion_mejora": 10, "cuantil_conservador": None},
])
def test_pre_registro_pendiente_es_error_y_no_escribe(adopcion, prereg):
    with pytest.raises(ValueError, match="pre-registro pendiente"):
        adopcion.decidir_adopcion(frontera(200), frontera(200), [], prereg)
    assert not adopcion.RUTA_SALIDA.exists()


def test_frontera_sin_metodo_es_error_claro(adopcion):
    solo_modelo = [p for p in frontera(115) if p["metodo"] == "modelo"]
    with pytest.raises(ValueError, match="regla2"):
        adopcion.decidir_adopcion(solo_modelo, frontera(115), [], PREREG)


def test_sin_punto_regla2_en_el_cuantil_preregistrado_es_error(adopcion):
    with pytest.raises(ValueError, match="cuantil"):
        adopcion.decidir_adopcion(frontera(115), frontera(115), [], {**PREREG, "cuantil_conservador": 0.33})


# --- config/preregistro.yaml -------------------------------------------------

CAMPOS = ["umbral_adopcion_mejora", "cuantil_conservador", "colchon", "umbral_historia_semanas",
          "umbrales_confianza", "umbral_alerta_sesgo", "semillas_evaluacion"]


def _prereg_real():
    return yaml.safe_load((RAIZ / "config" / "preregistro.yaml").read_text(encoding="utf-8"))


def test_preregistro_tiene_los_campos_del_plan():
    assert set(CAMPOS) <= set(_prereg_real())


def test_preregistro_con_null_no_se_puede_usar_con_la_regla(adopcion):
    """Mientras Gino no fije el umbral, usar el archivo real con la regla debe fallar. Ya fijado, debe funcionar."""
    prereg = _prereg_real()
    if prereg["umbral_adopcion_mejora"] is None or prereg["cuantil_conservador"] is None:
        with pytest.raises(ValueError, match="pre-registro pendiente"):
            adopcion.decidir_adopcion(frontera(200), frontera(200), [], prereg)
    else:
        adopcion.decidir_adopcion(frontera(200), frontera(200), [], prereg)

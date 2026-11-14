"""Simulador de RESPALDO (eval/_simulador_respaldo.py), con casos de juguete calculados a mano.

Es un respaldo hasta que existan eval/simular.py (Rafael) y motor.decidir (Sebastián). eval/ no es un paquete.
Caso de cuatro días: saldo 1000, un pago real de 300 el día 4 (a 3 días desde el día 1), sin otros ingresos,
pronóstico en cero. A mano (cuantil P20, colchón 0, divisor max(d, 1)):
  día 1: pago a d=3 -> (1000-300)/3 = 233.33; d=14 -> (1000-300)/14 = 50      -> mínimo 50      -> numero_hoy 50
  día 2: saldo 950: d=2 -> 325; d=14 -> 650/14 = 46.43                          -> 46
  día 3: saldo 904: d=1 -> 604; d=14 -> 604/14 = 43.14                          -> 43
  día 4: saldo 861: pago hoy d=0 -> 561; d=14 -> 561/14 = 40.07                 -> 40; saldo 821, paga 300 -> 521 >= 0
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from contratos import ETIQUETAS_REFERENCIA, Cuantiles, Pronostico, cargar_config

RAIZ = Path(__file__).resolve().parents[3]


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location(f"eval_{nombre}", RAIZ / "eval" / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def sim():
    mod = _cargar("_simulador_respaldo")
    mod._CACHE.clear()
    return mod


@pytest.fixture(scope="module")
def cfg():
    return cargar_config()


def _pron(h3=0.0, h7=0.0, h14=0.0):
    def q(v):
        return Cuantiles(p5=v, p20=v, p50=v, p80=v)

    return Pronostico(por_horizonte={3: q(h3), 7: q(h7), 14: q(h14)})


def _fila(cid, tid, ts, monto, saldo, categoria="alimentacion", comercio="Mercado", pago=False, dup=False):
    return {"customer_id": cid, "transaction_id": tid, "fecha_hora": pd.Timestamp(ts), "monto": monto,
            "moneda": "PEN", "tipo": "ingreso" if monto > 0 else "gasto", "categoria": categoria,
            "comercio": comercio, "saldo": saldo, "ingreso_recurrente": False, "es_duplicado": dup,
            "es_atipico": False, "pago_con_fecha": pago, "arquetipo": "asalariado"}


def _datos(filas):
    df = pd.DataFrame(filas)
    etiquetas = df.set_index("transaction_id")[list(ETIQUETAS_REFERENCIA)]
    return df.drop(columns=list(ETIQUETAS_REFERENCIA)), etiquetas


def _caso(saldo=1000.0, pago=300.0, dia_pago="2026-09-04 10:00", extra=()):
    filas = [_fila("T1", "t0", "2026-08-31 09:00", -10.0, saldo),
             _fila("T1", "t1", dia_pago, -pago, saldo - pago, "alquiler", "Dueno", pago=True), *extra]
    return _datos(filas)


def _parchar(sim, monkeypatch, pron):
    monkeypatch.setattr(sim, "_pronosticar", lambda metodo, hist, fecha, modelo, cfg: pron)
    monkeypatch.setattr(sim, "_pagos_inferidos", lambda hist, mes_inicio: [{"dia_mes": 4, "monto": 300.0}])


# --- fórmula del número de hoy ---

@pytest.mark.parametrize("d,esperado", [(0, 0.0), (2, 0.0), (3, 3.0), (6, 3.0), (7, 7.0), (13, 7.0), (14, 14.0)])
def test_ingreso_conservador_usa_el_mayor_horizonte_que_cabe(sim, d, esperado):
    pron = _pron(3.0, 7.0, 14.0)
    assert sim._ingreso_conservador(pron, d, "p20") == esperado


def test_numero_hoy_del_caso_orden_de_pagos_es_cero(sim):
    # fixture del plan: saldo 100, pago 300 el día 3, ingreso de 400 recién el día 10 (h14 p20 = 400)
    pron = _pron(0.0, 0.0, 400.0)
    assert sim._numero_hoy(100.0, [(3, 300.0)], pron, "p20", colchon=0.0) == 0


def test_numero_hoy_redondea_hacia_abajo_y_no_es_negativo(sim):
    assert sim._numero_hoy(1000.0, [(3, 300.0)], _pron(), "p20", colchon=0.0) == 50  # 700/14 = 50.0
    assert sim._numero_hoy(861.0, [(0, 300.0)], _pron(), "p20", colchon=0.0) == 40  # 561/14 = 40.07
    assert sim._numero_hoy(-5.0, [], _pron(), "p20", colchon=0.0) == 0


def test_el_colchon_se_resta(sim):
    assert sim._numero_hoy(1000.0, [(3, 300.0)], _pron(), "p20", colchon=70.0) == 45  # 630/14


# --- simulación de cuatro días a mano ---

def test_caso_de_juguete_a_mano_cuatro_dias(sim, cfg, monkeypatch):
    _parchar(sim, monkeypatch, _pron())
    hist, etiquetas = _caso()
    r = sim.simular_persona(hist, etiquetas, cfg, "regla2", 0.20)
    assert r["pagos_totales"] == 1 and r["pagos_descubiertos"] == 0
    assert r["gasto_permitido_dia"] == pytest.approx((50 + 46 + 43 + 40) / 4)


def test_pago_descubierto_cuando_el_saldo_no_alcanza(sim, cfg, monkeypatch):
    _parchar(sim, monkeypatch, _pron())
    hist, etiquetas = _caso(saldo=100.0)  # 100 contra un pago de 300
    r = sim.simular_persona(hist, etiquetas, cfg, "regla2", 0.20)
    assert r["pagos_totales"] == 1 and r["pagos_descubiertos"] == 1
    assert r["gasto_permitido_dia"] == 0.0  # nunca alcanza: numero_hoy 0 todos los días


def test_gasto_cero_no_gasta(sim, cfg, monkeypatch):
    _parchar(sim, monkeypatch, _pron())
    hist, etiquetas = _caso()
    r = sim.simular_persona(hist, etiquetas, cfg, "gasto_cero", None)
    assert r == {"pagos_descubiertos": 0, "pagos_totales": 1, "gasto_permitido_dia": 0.0}


def test_los_duplicados_no_cuentan_como_pagos_ni_como_flujo(sim, cfg, monkeypatch):
    _parchar(sim, monkeypatch, _pron())
    duplicado = _fila("T1", "t2", "2026-09-04 10:00", -300.0, 700.0, "alquiler", "Dueno", pago=True, dup=True)
    hist, etiquetas = _caso(extra=[duplicado])
    r = sim.simular_persona(hist, etiquetas, cfg, "regla2", 0.20)
    assert r["pagos_totales"] == 1


def test_el_ingreso_real_del_dia_suma_al_saldo(sim, cfg, monkeypatch):
    _parchar(sim, monkeypatch, _pron())
    ingreso = _fila("T1", "t3", "2026-09-04 08:00", 500.0, 1200.0, "sueldo", "Empresa")
    hist, etiquetas = _caso(saldo=100.0, extra=[ingreso])
    r = sim.simular_persona(hist, etiquetas, cfg, "regla2", 0.20)
    assert r["pagos_descubiertos"] == 0  # 100 + 500 - 0 gasto - 300 = 300 >= 0


def test_no_se_mira_el_futuro_el_pronostico_recibe_solo_historia_previa(sim, cfg, monkeypatch):
    vistos = []

    def espia(metodo, hist, fecha, modelo, cfg):
        vistos.append((pd.Timestamp(fecha), hist["fecha_hora"].max()))
        return _pron()

    monkeypatch.setattr(sim, "_pronosticar", espia)
    monkeypatch.setattr(sim, "_pagos_inferidos", lambda hist, mes_inicio: [])
    hist, etiquetas = _caso()
    sim.simular_persona(hist, etiquetas, cfg, "regla2", 0.20)
    assert vistos and all(ultimo < dia for dia, ultimo in vistos)


def test_el_modelo_sin_historia_cae_a_regla2(sim, cfg, monkeypatch):
    from modelo import HistoriaInsuficiente

    class Corto:
        def predecir(self, hist, fecha):
            raise HistoriaInsuficiente()

    llamadas = []
    monkeypatch.setattr(sim, "_regla", lambda nombre, hist, fecha, cfg: llamadas.append(nombre) or _pron())
    monkeypatch.setattr(sim, "_pagos_inferidos", lambda hist, mes_inicio: [])
    hist, etiquetas = _caso()
    sim.simular_persona(hist, etiquetas, cfg, "modelo", 0.20, Corto())
    assert set(llamadas) == {"regla2"}


def test_metodo_desconocido_falla_claro(sim, cfg):
    hist, etiquetas = _caso()
    with pytest.raises(ValueError):
        sim.simular_persona(hist, etiquetas, cfg, "magia", 0.20)


# --- inferencia de pagos sin etiquetas ---

def test_inferir_pagos_encuentra_el_alquiler_y_descarta_el_gasto_frecuente(sim):
    filas = []
    n = 0
    for mes in range(1, 7):  # enero a junio de 2026
        filas.append(_fila("T1", f"a{n}", f"2026-{mes:02d}-02 10:00", -400.0, 0.0, "alquiler", "Dueno"))
        for dia in (3, 9, 15, 21, 27):  # supermercado: 5 veces al mes, no es un pago con fecha
            n += 1
            filas.append(_fila("T1", f"s{n}", f"2026-{mes:02d}-{dia:02d} 12:00", -30.0 - dia, 0.0))
        n += 1
    hist, _ = _datos(filas)
    pagos = sim._pagos_inferidos(hist, pd.Timestamp("2026-07-01"))
    assert [(p["dia_mes"], p["monto"]) for p in pagos] == [(2, 400.0)]


def test_inferir_pagos_no_usa_datos_posteriores_a_mes_inicio(sim):
    filas = [_fila("T1", f"a{m}", f"2026-{m:02d}-05 10:00", -250.0, 0.0, "suscripcion", "Streaming")
             for m in range(1, 9)]
    hist, _ = _datos(filas)
    assert sim._pagos_inferidos(hist, pd.Timestamp("2026-03-01")) == []  # solo 2 meses previos: no alcanza
    assert len(sim._pagos_inferidos(hist, pd.Timestamp("2026-07-01"))) == 1


def test_proximos_pagos_arma_los_dias_hasta_el_pago(sim):
    pagos = [{"dia_mes": 4, "monto": 300.0}, {"dia_mes": 31, "monto": 50.0}]
    # desde el 2026-09-01: el día 4 está a 3 días; el 31 no existe en septiembre -> cae el 30 (a 29 días, fuera de 14)
    assert sim._proximos(pagos, pd.Timestamp("2026-09-01")) == [(3, 300.0)]
    # desde el 2026-09-28: el día 31 -> 30 de septiembre (a 2 días); el 4 de octubre (a 6 días)
    assert sim._proximos(pagos, pd.Timestamp("2026-09-28")) == [(2, 50.0), (6, 300.0)]


# --- frontera usa el respaldo cuando simular.py sigue en esqueleto ---

def test_frontera_cae_al_respaldo_si_simular_es_esqueleto():
    frontera = _cargar("frontera")
    with pytest.warns(UserWarning, match="RESPALDO"):
        simular = frontera._cargar_simulador()
    assert callable(simular)

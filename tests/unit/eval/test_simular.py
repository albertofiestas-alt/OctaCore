"""eval/simular.py: juguete calculado a mano, contrato con eval/frontera.py, anti fuga y validación contra
verdad_eventos.csv (dueño: Rafael). eval/ no es un paquete: se carga por ruta."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from contratos import ETIQUETAS_REFERENCIA, cargar_config

RAIZ = Path(__file__).resolve().parents[3]
MUESTRA = RAIZ / "data" / "muestra" / "movimientos.csv"
VERDAD = RAIZ / "data" / "muestra" / "verdad_eventos.csv"
CFG = cargar_config()


def _cargar():
    spec = importlib.util.spec_from_file_location("eval_simular", RAIZ / "eval" / "simular.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sim = _cargar()


@pytest.fixture(autouse=True)
def _sin_cache():
    sim.limpiar_cache()
    yield
    sim.limpiar_cache()


# --------------------------------------------------------------------------- #
# Juguete de 3 días (1 al 3 de septiembre de 2026 = mes 21, el primero de la prueba)
# --------------------------------------------------------------------------- #

def _fila(i, fecha, monto, tipo, categoria, saldo=None, pcf=False, dup=False):
    return {"customer_id": "P0001", "transaction_id": f"T{i:07d}", "fecha_hora": fecha, "monto": monto, "moneda": "PEN",
            "tipo": tipo, "categoria": categoria, "comercio": "ComercioFicticio", "saldo": saldo,
            "ingreso_recurrente": False, "es_duplicado": dup, "es_atipico": False, "pago_con_fecha": pcf,
            "arquetipo": "conductor"}


def _juguete(saldo_previo=100.0, extra_previo=None):
    """Saldo 100 antes de la prueba. 1-sep: ingreso 50, suscripción doble 25 (no discrecional) y alquiler 120 (pago).
    2-sep: gasto discrecional 40 y luz 20 (pago, con una copia duplicada). 3-sep: ingreso 100 (fin de los datos)."""
    filas = [_fila(1, "2026-07-01 10:00:00", -184.0, "gasto", "alimentacion"),     # discrecional previo: 184 / 184 días
             _fila(2, "2026-08-31 10:00:00", 10.0, "ingreso", "ingreso", saldo=saldo_previo),
             _fila(3, "2026-09-01 08:00:00", 50.0, "ingreso", "ingreso"),
             _fila(4, "2026-09-01 09:00:00", -25.0, "gasto", "suscripcion"),
             _fila(5, "2026-09-01 10:00:00", -120.0, "gasto", "alquiler", pcf=True),
             _fila(6, "2026-09-02 09:00:00", -40.0, "gasto", "alimentacion"),
             _fila(7, "2026-09-02 10:00:00", -20.0, "gasto", "servicios", pcf=True),
             _fila(8, "2026-09-02 10:00:00", -20.0, "gasto", "servicios", pcf=True, dup=True),
             _fila(9, "2026-09-03 12:00:00", 100.0, "ingreso", "ingreso")]
    df = pd.DataFrame(filas + (extra_previo or []))
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
    df = df.sort_values("fecha_hora", kind="mergesort").reset_index(drop=True)
    return df.drop(columns=list(ETIQUETAS_REFERENCIA)), df.set_index("transaction_id")[list(ETIQUETAS_REFERENCIA)]


def test_juguete_gasto_cero_a_mano():
    # 1-sep: 100 + 50 - 0 - 25 - 120 = 5 (cubierto) ; 2-sep: 5 - 0 - 20 = -15 (DESCUBIERTO; la copia no cuenta)
    h, e = _juguete()
    r = sim.simular_persona(h, e, CFG, "gasto_cero", None)
    assert (r["pagos_descubiertos"], r["pagos_totales"], r["gasto_permitido_dia"]) == (1, 2, 0.0)
    assert [ev["saldo"] for ev in r["eventos"]] == [5.0, -15.0]
    assert [ev["descubierto"] for ev in r["eventos"]] == [False, True]


def test_juguete_gasto_observado_y_fijo_a_mano():
    h, e = _juguete()
    obs = sim.simular_persona(h, e, CFG, "gasto_observado", None)
    # 2-sep: 5 - 40 - 20 = -55 ; gasto medio (0 + 40 + 0) / 3
    assert [ev["saldo"] for ev in obs["eventos"]] == [5.0, -55.0]
    assert obs["gasto_permitido_dia"] == pytest.approx(40 / 3)
    fijo = sim.simular_persona(h, e, CFG, "gasto_fijo", None)
    # 184 soles de discrecional entre el 1-mar y el 31-ago (184 días) -> 1 sol por día
    assert fijo["gasto_permitido_dia"] == pytest.approx(1.0)
    assert [ev["saldo"] for ev in fijo["eventos"]] == [4.0, -17.0]


def test_gasto_cero_sin_descubiertos_si_el_saldo_alcanza():
    h, e = _juguete(saldo_previo=1000.0)
    r = sim.simular_persona(h, e, CFG, "gasto_cero", None)
    assert r["pagos_descubiertos"] == 0 and r["pagos_totales"] == 2


def test_el_numero_de_hoy_sale_de_motor_decidir(monkeypatch):
    """Cableado: el gasto del día es Decision.numero_hoy del motor oficial (aquí un motor espía que devuelve 7)."""
    import motor
    import reglas

    llamadas = []

    class _Decision:
        numero_hoy = 7

    def espia(estado, pronostico, cfg):
        llamadas.append((estado.fecha_corte, estado.saldo, cfg["cuantil_conservador"]))
        return _Decision()

    monkeypatch.setattr(motor, "decidir", espia)
    monkeypatch.setattr(reglas, "regla2", lambda hist, fecha, cfg: reglas.regla1(hist, fecha, cfg))
    h, e = _juguete()
    r = sim.simular_persona(h, e, CFG, "regla2", 0.05)
    assert r["gasto_permitido_dia"] == 7.0 and r["motor_usado"] == "motor.decidir"
    assert [c[2] for c in llamadas] == [0.05] * 3                  # el cuantil de la frontera llega al motor
    # saldo simulado al empezar cada día: 100 ; 100 + 50 - 7 - 25 - 120 = -2 ; -2 - 7 - 20 = -29
    assert [c[1] for c in llamadas] == [100.0, -2.0, -29.0]


# --------------------------------------------------------------------------- #
# Contrato con eval/frontera.py
# --------------------------------------------------------------------------- #


def test_no_parece_esqueleto_para_la_frontera():
    """frontera._es_esqueleto llama simular(None, None, None, "regla2", 0.20): debe fallar SIN NotImplementedError."""
    with pytest.raises(Exception) as info:
        sim.simular_persona(None, None, None, "regla2", 0.20)
    assert not isinstance(info.value, NotImplementedError)


def test_claves_y_validaciones():
    h, e = _juguete()
    r = sim.simular_persona(h, e, CFG, "gasto_fijo", None)
    assert {"pagos_descubiertos", "pagos_totales", "gasto_permitido_dia", "customer_id", "metodo", "cuantil",
            "calibracion_p20", "motor_usado", "eventos"} <= set(r)
    assert set(r["eventos"][0]) == {"fecha", "pago", "monto", "saldo", "numero", "descubierto"}
    with pytest.raises(ValueError, match="desconocido"):
        sim.simular_persona(h, e, CFG, "magia", 0.2)
    with pytest.raises(ValueError, match="cuantil"):
        sim.simular_persona(h, e, CFG, "regla2", None)


# --------------------------------------------------------------------------- #
# Con la muestra real: anti fuga, motor real y validación contra la verdad
# --------------------------------------------------------------------------- #


def _persona_muestra(cid="P0010"):
    df = pd.read_csv(MUESTRA, keep_default_na=False, na_values=[""])
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
    g = df[df["customer_id"] == cid].sort_values("fecha_hora").reset_index(drop=True)
    return g.drop(columns=list(ETIQUETAS_REFERENCIA)), g.set_index("transaction_id")[list(ETIQUETAS_REFERENCIA)]


@pytest.mark.skipif(not MUESTRA.exists(), reason="sin data/muestra")
def test_anti_fuga_alterar_el_futuro_no_cambia_el_dia_t():
    h, e = _persona_muestra()
    t = pd.Timestamp("2026-10-15")
    base = sim._Persona(h, e, CFG)
    pron = sim._pronosticar(base, "regla2", t, None)
    hist, pagos, semanas = base.contexto(t)

    alterada = h.copy()
    futuro = alterada["fecha_hora"] >= t
    alterada.loc[futuro, "monto"] = alterada.loc[futuro, "monto"] * 10
    otra = sim._Persona(alterada, e, CFG)
    hist2, pagos2, semanas2 = otra.contexto(t)
    assert sim._pronosticar(otra, "regla2", t, None) == pron
    assert hist2["fecha_hora"].max() < t and len(hist2) == len(hist)
    assert pagos2 == pagos and semanas2 == semanas


@pytest.mark.skipif(not MUESTRA.exists(), reason="sin data/muestra")
def test_motor_real_da_cuantiles_ordenados_en_la_frontera():
    """Con el motor y la ingesta reales: un cuantil más conservador nunca permite más gasto."""
    h, e = _persona_muestra()
    gasto = [sim.simular_persona(h, e, CFG, "regla2", q)["gasto_permitido_dia"] for q in (0.05, 0.5)]
    assert gasto[0] <= gasto[1]


@pytest.mark.skipif(not (MUESTRA.exists() and VERDAD.exists()), reason="sin data/muestra")
def test_con_gasto_observado_reproduce_verdad_eventos():
    """Con el gasto real, los descubiertos simulados deben ser los pago_con_saldo_negativo del generador.
    Medido el 14-nov en la muestra (meses 21-24): 40 de 42 (recall 0,952) y ninguno de más (precisión 1,000).
    Los 2 que faltan: el generador ordena por hora (pago a las 9 h antes del ingreso de la tarde) y la simulación
    es diaria (el ingreso del día entra antes que los pagos)."""
    df = pd.read_csv(MUESTRA, keep_default_na=False, na_values=[""])
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
    verdad = pd.read_csv(VERDAD)
    verdad = verdad[verdad["evento"] == "pago_con_saldo_negativo"]
    fecha = df.set_index("transaction_id")["fecha_hora"]
    ver = set(verdad.loc[fecha.reindex(verdad["transaction_id"]).to_numpy() >= pd.Timestamp("2026-09-01"), "transaction_id"])
    simulados = set()
    for _, g in df.groupby("customer_id"):
        g = g.sort_values("fecha_hora").reset_index(drop=True)
        r = sim.simular_persona(g.drop(columns=list(ETIQUETAS_REFERENCIA)),
                                g.set_index("transaction_id")[list(ETIQUETAS_REFERENCIA)], CFG, "gasto_observado", None)
        simulados |= {ev["pago"] for ev in r["eventos"] if ev["descubierto"]}
    ambos = ver & simulados
    assert len(ambos) / len(simulados) >= 0.95, "precisión"
    assert len(ambos) / len(ver) >= 0.90, "recall"

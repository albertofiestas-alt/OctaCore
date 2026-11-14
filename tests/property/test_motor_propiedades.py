"""Propiedades del motor con hypothesis (plan de Sebastián, secciones 4 tarea 5 y 10).

Las estrategias generan EstadoPersona y Pronostico VÁLIDOS según los contratos:
saldo puede ser negativo, 0 a 5 pagos (día 0..20, monto 0..2000), colchón 0..200,
semanas 0..30 y cuantiles no negativos ordenados p5 <= p20 <= p50 <= p80 en cada horizonte.

Para comprobar el número de hoy se usa un oráculo propio (_minimo_p20), escrito aquí
desde la fórmula del plan y no importado de decidir.py.
"""

from __future__ import annotations

import math
from datetime import date

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from contratos import CATEGORIAS, Cuantiles, Decision, EstadoPersona, PagoConFecha, Pronostico, cargar_config
from motor import decidir
from motor.plantillas import LIMITES_FIJOS
from motor.verificador import textos_sin_origen

CFG = cargar_config()
AJUSTES = settings(max_examples=1000, deadline=None, suppress_health_check=[HealthCheck.too_slow])
TOL = 1e-6

# --------------------------------------------------------------------------- #
# Estrategias
# --------------------------------------------------------------------------- #


def _flotante(minimo: float, maximo: float) -> st.SearchStrategy[float]:
    """Mezcla de montos con 2 decimales (lo realista) y flotantes cualesquiera."""
    centavos = st.integers(int(minimo * 100), int(maximo * 100)).map(lambda c: c / 100)
    libre = st.floats(minimo, maximo, allow_nan=False, allow_infinity=False)
    return st.one_of(centavos, libre)


@st.composite
def pagos(draw, maximo: int = 5) -> list[PagoConFecha]:
    n = draw(st.integers(0, maximo))
    return [
        PagoConFecha(
            pago_id=f"PG{i}",
            dia=draw(st.integers(0, 20)),
            monto=draw(_flotante(0, 2000)),
            categoria=draw(st.sampled_from(CATEGORIAS)),
        )
        for i in range(n)
    ]


@st.composite
def estados(draw) -> EstadoPersona:
    return EstadoPersona(
        customer_id="PROP",
        fecha_corte=date(2026, 3, 1),
        saldo=draw(_flotante(-3000, 5000)),
        pagos=draw(pagos()),
        colchon=draw(_flotante(0, 200)),
        semanas_historia=draw(st.integers(0, 30)),
    )


@st.composite
def cuantiles(draw) -> Cuantiles:
    valores = sorted(draw(st.lists(_flotante(0, 3000), min_size=4, max_size=4)))
    return Cuantiles(p5=valores[0], p20=valores[1], p50=valores[2], p80=valores[3])


@st.composite
def pronosticos(draw) -> Pronostico:
    return Pronostico(por_horizonte={h: draw(cuantiles()) for h in (3, 7, 14)})


# --------------------------------------------------------------------------- #
# Oráculo independiente (fórmula del plan, sección 6)
# --------------------------------------------------------------------------- #


def _ingreso(pron: Pronostico, d: int, attr: str) -> float:
    hs = [h for h in (3, 7, 14) if h <= min(d, 14)]
    return float(getattr(pron.por_horizonte[max(hs)], attr)) if hs else 0.0


def _numerador(estado: EstadoPersona, pron: Pronostico, d: int, attr: str) -> float:
    pagado = sum(p.monto for p in estado.pagos if p.dia <= d)
    return estado.saldo + _ingreso(pron, d, attr) - pagado - estado.colchon


def _puntos(estado: EstadoPersona) -> list[int]:
    return sorted({p.dia for p in estado.pagos} | {14})


def _minimo(estado: EstadoPersona, pron: Pronostico, attr: str) -> float:
    return min(_numerador(estado, pron, d, attr) / max(d, 1) for d in _puntos(estado))


# --------------------------------------------------------------------------- #
# Propiedades
# --------------------------------------------------------------------------- #


@AJUSTES
@given(estados(), pronosticos())
def test_1_numero_hoy_entero_no_negativo(estado, pron):
    d = decidir(estado, pron, CFG)
    assert isinstance(d, Decision)
    assert isinstance(d.desglose["numero_hoy"], int)
    assert float(d.numero_hoy).is_integer()
    assert d.numero_hoy >= 0


@AJUSTES
@given(estados(), pronosticos(), _flotante(0, 3000))
def test_2a_mas_saldo_no_baja_el_numero(estado, pron, extra):
    base = decidir(estado, pron, CFG).numero_hoy
    mas = estado.model_copy(update={"saldo": estado.saldo + extra})
    assert decidir(mas, pron, CFG).numero_hoy >= base


@AJUSTES
@given(estados(), pronosticos(), st.integers(0, 20), _flotante(0, 2000), st.sampled_from(CATEGORIAS))
def test_2b_agregar_un_pago_no_sube_el_numero(estado, pron, dia, monto, categoria):
    base = decidir(estado, pron, CFG).numero_hoy
    nuevo = PagoConFecha(pago_id="EXTRA", dia=dia, monto=monto, categoria=categoria)
    con_pago = estado.model_copy(update={"pagos": [*estado.pagos, nuevo]})
    assert decidir(con_pago, pron, CFG).numero_hoy <= base


@AJUSTES
@given(estados(), pronosticos())
def test_3_propuesta_cubre_todo_en_p5(estado, pron):
    d = decidir(estado, pron, CFG)
    for prop in d.propuestas:
        g = prop.despues["numero_hoy"]
        assert isinstance(g, int) and 0 <= g < d.numero_hoy
        assert prop.monto == d.numero_hoy - g
        for dia in _puntos(estado):
            assert _numerador(estado, pron, dia, "p5") - g * max(dia, 1) >= -TOL, dia


@AJUSTES
@given(estados(), pronosticos())
def test_4_pureza(estado, pron):
    e0, p0 = estado.model_dump(), pron.model_dump()
    d1 = decidir(estado, pron, CFG)
    d2 = decidir(estado, pron, CFG)
    assert estado.model_dump() == e0
    assert pron.model_dump() == p0
    assert d1 == d2


@AJUSTES
@given(estados(), pronosticos())
def test_5_supuestos_evidencia_limites_confianza_siempre(estado, pron):
    d = decidir(estado, pron, CFG)
    assert d.supuestos and all(s.strip() for s in d.supuestos)
    assert d.evidencia
    assert d.limites
    for frase in LIMITES_FIJOS:
        assert frase in d.limites
    assert d.confianza in ("alta", "media", "baja")
    assert d.explicacion


@AJUSTES
@given(estados(), pronosticos())
def test_6_toda_cifra_de_los_textos_tiene_origen(estado, pron):
    d = decidir(estado, pron, CFG)
    assert textos_sin_origen(estado, d) == []


@AJUSTES
@given(estados(), pronosticos())
def test_7_mensaje_falta_si_no_alcanza(estado, pron):
    d = decidir(estado, pron, CFG)
    minimo = _minimo(estado, pron, "p20")
    if d.numero_hoy == 0 and minimo < 0:
        assert d.mensaje_falta is not None
        assert "faltan S/" in d.mensaje_falta
        faltante = d.desglose["faltante"]
        assert isinstance(faltante, int) and faltante > 0
        assert d.mensaje_falta.endswith(f"faltan S/{faltante}")
    if minimo >= 0:
        assert d.mensaje_falta is None


@AJUSTES
@given(estados(), pronosticos())
def test_8_redondeo_conservador(estado, pron):
    d = decidir(estado, pron, CFG)
    minimo = _minimo(estado, pron, "p20")
    if minimo >= 0:
        assert d.numero_hoy <= minimo + TOL
        assert d.numero_hoy + 1 > minimo
        assert d.numero_hoy == math.floor(minimo) or abs(minimo - round(minimo)) < TOL
    else:
        assert d.numero_hoy == 0


# --------------------------------------------------------------------------- #
# Simulación (opción C): motor.simular
# --------------------------------------------------------------------------- #

from contratos import Escenario, IngresoExtra  # noqa: E402
from motor.simular import simular  # noqa: E402


@st.composite
def escenarios(draw) -> Escenario:
    ingresos = draw(
        st.lists(st.builds(IngresoExtra, dia=st.integers(0, 14), monto=_flotante(0, 10000)), max_size=3)
    )
    return Escenario(ingresos_extra=tuple(ingresos), gasto_hoy=draw(_flotante(0, 10000)))


@AJUSTES
@given(estados(), pronosticos())
def test_s1_escenario_vacio_es_identico_a_decidir(estado, pron):
    assert simular(estado, pron, Escenario(), CFG) == decidir(estado, pron, CFG)


@AJUSTES
@given(estados(), pronosticos(), escenarios(), st.integers(0, 14), _flotante(0, 10000))
def test_s2_un_ingreso_extra_mas_no_baja_el_numero(estado, pron, esc, dia, monto):
    if len(esc.ingresos_extra) >= 3:
        esc = esc.model_copy(update={"ingresos_extra": esc.ingresos_extra[:2]})
    con_mas = esc.model_copy(update={"ingresos_extra": (*esc.ingresos_extra, IngresoExtra(dia=dia, monto=monto))})
    assert simular(estado, pron, con_mas, CFG).numero_hoy >= simular(estado, pron, esc, CFG).numero_hoy


@AJUSTES
@given(estados(), pronosticos(), escenarios(), _flotante(0, 3000))
def test_s3_gastar_mas_hoy_no_sube_el_numero(estado, pron, esc, mas):
    gasta_mas = esc.model_copy(update={"gasto_hoy": min(10000.0, esc.gasto_hoy + mas)})
    assert simular(estado, pron, gasta_mas, CFG).numero_hoy <= simular(estado, pron, esc, CFG).numero_hoy


@AJUSTES
@given(estados(), pronosticos(), escenarios())
def test_s4_simulacion_completa_y_sin_cifras_inventadas(estado, pron, esc):
    d = simular(estado, pron, esc, CFG)
    assert d.numero_hoy >= 0
    assert d.supuestos and d.evidencia and d.limites
    assert textos_sin_origen(estado, d) == []
    for prop in d.propuestas:
        assert prop.propuesta_id.endswith(":simulada") or (not esc.ingresos_extra and not esc.gasto_hoy)

"""Pruebas del clasificador de intención y de los parámetros (Gino). Sin APIs reales: el proveedor es falso."""

from __future__ import annotations

import json

import pytest

from asistente import intenciones as it
from contratos import Escenario, cargar_config


@pytest.fixture(scope="module")
def cfg():
    return cargar_config()


@pytest.fixture(scope="module")
def cfg2(cfg):
    return cfg.con(asistente={**cfg["asistente"], "modo": 2})


class ProveedorFalso:
    def __init__(self, respuesta=None, error=None):
        self.respuesta, self.error, self.llamadas = respuesta, error, []

    def generar(self, sistema, usuario):
        self.llamadas.append((sistema, usuario))
        if self.error:
            raise self.error
        return self.respuesta


# ---------------------------------------------------------------- exactitud medida (se reporta, no se fuerza)
def test_exactitud_en_particion_80_20(cfg, record_property):
    _, exactitud = it.entrenar_clasificador(cfg["asistente"]["csv_preguntas"], cfg["asistente"]["semilla_clasificador"])
    record_property("exactitud_80_20", exactitud)
    print(f"\nEXACTITUD 80/20 estratificada (con gemelas de plantilla a ambos lados): {exactitud:.3f}")
    assert 1 / len(it.INTENCIONES) < exactitud <= 1  # solo por encima del azar; sin umbral


def test_exactitud_sin_fuga_de_plantillas(cfg, record_property):
    exactitud, n = it.exactitud_sin_fuga(cfg["asistente"]["csv_preguntas"], cfg["asistente"]["semilla_clasificador"])
    record_property("exactitud_sin_fuga", exactitud)
    print(f"\nEXACTITUD sin fuga (plantillas gemelas agrupadas), n_prueba={n}: {exactitud:.3f}")
    assert 1 / len(it.INTENCIONES) < exactitud <= 1


def test_entrenamiento_es_reproducible(cfg):
    a = it.entrenar_clasificador(cfg["asistente"]["csv_preguntas"], 7)[1]
    b = it.entrenar_clasificador(cfg["asistente"]["csv_preguntas"], 7)[1]
    assert a == b


# ---------------------------------------------------------------- 10 frases nuevas escritas por Gino
FRASES_NUEVAS = [
    ("¿Por qué mi límite de hoy es tan bajo?", "explicar_numero"),
    ("¿Alcanzará mi dinero para pagar la mensualidad del gimnasio el día 9?", "estado_pago"),
    ("¿Qué ocurriría si me depositan S/300 el día 6?", "que_pasa_si"),
    ("Quiero una recomendación para no fallar en mi cuota", "propuesta"),
    ("¿Qué quiere decir P20?", "concepto"),
    ("¿Me conviene comprar criptomonedas?", "fuera_de_alcance"),
    ("Explícame cómo calcularon mi cifra de hoy", "explicar_numero"),
    ("¿Está cubierta mi factura de internet del día 4?", "estado_pago"),
    ("Y si hoy me gasto S/60 en una cena", "que_pasa_si"),
    ("¿Qué es el colchón?", "concepto"),
]


@pytest.mark.parametrize("texto,esperada", FRASES_NUEVAS, ids=[f[0][:30] for f in FRASES_NUEVAS])
def test_frases_nuevas(cfg, texto, esperada):
    intent = it.clasificar(texto, cfg)
    assert intent.nombre == esperada, f"{intent.nombre} ({intent.confianza:.2f})"


def test_clasificar_devuelve_intencion_valida(cfg):
    intent = it.clasificar("¿cuánto puedo gastar hoy?", cfg)
    assert intent.nombre in it.INTENCIONES and 0.0 <= intent.confianza <= 1.0


# ---------------------------------------------------------------- palabras clave de respaldo
def test_palabras_clave_mandan_con_confianza_baja(cfg):
    bajo = it.Intencion("concepto", 0.2)
    assert it._ajustar_con_palabras_clave(bajo, "dame un préstamo", cfg).nombre == "fuera_de_alcance"


def test_palabras_clave_no_pisan_confianza_alta(cfg):
    alto = it.Intencion("concepto", 0.9)
    assert it._ajustar_con_palabras_clave(alto, "dame un préstamo", cfg).nombre == "concepto"


# ---------------------------------------------------------------- modo 2 con proveedor falso
def _json(**kw):
    return json.dumps({"intencion": "que_pasa_si", "monto": 200, "dia": 5, "pago_ref": None, **kw})


def test_modo2_usa_json_valido(cfg2):
    prov = ProveedorFalso(_json())
    intent = it.clasificar("y si cobro 200 el dia 5", cfg2, prov)
    assert (intent.nombre, intent.monto, intent.dia) == ("que_pasa_si", 200.0, 5)
    assert len(prov.llamadas) == 1
    sistema, usuario = prov.llamadas[0]
    assert "y si cobro 200" not in sistema  # la pregunta nunca va en el prompt del sistema
    assert json.loads(usuario)  # viaja dentro de un JSON


@pytest.mark.parametrize(
    "respuesta",
    [
        "esto no es json",
        _json(intencion="dame_prestamo"),  # fuera de la lista cerrada
        _json(dia=40),  # fuera de rango
        _json(monto=-5),
        _json(monto="mucho"),
        json.dumps({"intencion": "concepto", "monto": None, "dia": None, "pago_ref": None, "extra": 1}),  # clave de más
        json.dumps({"intencion": "concepto"}),  # faltan claves
        json.dumps(["concepto"]),  # no es objeto
    ],
)
def test_modo2_respuesta_invalida_cae_al_ml(cfg2, respuesta):
    intent = it.clasificar("¿qué es el colchón?", cfg2, ProveedorFalso(respuesta))
    assert intent.nombre in it.INTENCIONES and intent.confianza < cfg2["asistente"]["confianza_llm"]


def test_modo2_proveedor_que_lanza_cae_al_ml(cfg2):
    intent = it.clasificar("¿qué es el colchón?", cfg2, ProveedorFalso(error=TimeoutError("sin red")))
    assert intent.nombre in it.INTENCIONES and intent.confianza < cfg2["asistente"]["confianza_llm"]


def test_modo1_no_llama_al_proveedor(cfg):
    prov = ProveedorFalso(_json())
    it.clasificar("¿qué es el colchón?", cfg, prov)
    assert prov.llamadas == []


def test_sin_proveedor_en_modo2_usa_ml(cfg2):
    assert it.clasificar("¿qué es el colchón?", cfg2).nombre in it.INTENCIONES


# ---------------------------------------------------------------- parametros
def _p(texto, cfg, nombre="que_pasa_si", **kw):
    return it.parametros(texto, it.Intencion(nombre, 1.0, **kw), cfg)


@pytest.mark.parametrize(
    "texto,ingresos,gasto",
    [
        ("¿Y si cobro S/200 el día 5?", [(5, 200.0)], 0.0),
        ("y si cobro s/200 el dia 5", [(5, 200.0)], 0.0),  # sin tildes
        ("y si me pagan 150 soles el día 10", [(10, 150.0)], 0.0),
        ("y si cobro 100 el dia 7", [(7, 100.0)], 0.0),  # monto sin moneda
        ("y si el día 12 entra un pago de S/250", [(12, 250.0)], 0.0),
        ("y si me adelantan s/50", [(0, 50.0)], 0.0),  # sin día = hoy
        ("¿Y si hoy cobro 80 soles?", [(0, 80.0)], 0.0),
        ("y si gasto 80 hoy", [], 80.0),
        ("¿Qué pasaría si hoy gasto S/150?", [], 150.0),
        ("si cobro S/200 el día 5 y gasto 80 hoy", [(5, 200.0)], 80.0),
        ("y si cobro S/1,500.50 el día 3", [(3, 1500.5)], 0.0),
        ("y si no entra ningún ingreso esta semana", [], 0.0),
        ("¿Cuánto podría gastar si cobro S/250 el día 3?", [(3, 250.0)], 0.0),  # 'gastar' pero el monto es un cobro
        ("cuanto podria gastar si cobro s/400 el dia 12", [(12, 400.0)], 0.0),
        ("y si gasto s/300 en una compra", [], 300.0),
    ],
)
def test_parametros_que_pasa_si(cfg, texto, ingresos, gasto):
    p = _p(texto, cfg)
    assert [(i["dia"], i["monto"]) for i in p["ingresos_extra"]] == ingresos
    assert p["gasto_hoy"] == gasto


def test_parametros_encaja_en_escenario(cfg):
    e = Escenario.model_validate(_p("y si cobro S/200 el día 5 y gasto 80 hoy", cfg))
    assert e.gasto_hoy == 80.0 and e.ingresos_extra[0].dia == 5


def test_parametros_dia_en_estado_pago(cfg):
    assert _p("¿me alcanza para el alquiler del día 3?", cfg, "estado_pago")["dia"] == 3


@pytest.mark.parametrize(
    "texto,motivo",
    [
        ("y si cobro S/200 el día 20", "dia_fuera_de_rango"),
        ("y si cobro S/20000 el día 5", "monto_fuera_de_rango"),
        ("y si gasto S/50000 hoy", "monto_fuera_de_rango"),
        ("y si cobro 10 el día 1, 20 el día 2, 30 el día 3 y 40 el día 4", "demasiados_ingresos"),
    ],
)
def test_parametros_fuera_de_rango_se_rechaza(cfg, texto, motivo):
    with pytest.raises(ValueError, match=motivo):
        _p(texto, cfg)


def test_parametros_toma_los_del_llm_si_el_texto_no_los_trae(cfg):
    p = _p("y si me depositan algo", cfg, monto=120.0, dia=4)
    assert [(i["dia"], i["monto"]) for i in p["ingresos_extra"]] == [(4, 120.0)]


def test_parametros_sobre_todas_las_que_pasa_si_del_csv(cfg):
    """Regresión: ninguna fila se rechaza y un texto con 'cobro/recibo/...' y sin 'gasto' nunca da gasto_hoy."""
    import pandas as pd

    filas = pd.read_csv(it._ruta(cfg["asistente"]["csv_preguntas"]))
    for texto in filas[filas.intencion == "que_pasa_si"].texto:
        p = _p(texto, cfg)
        if any(c.isdigit() for c in texto):
            assert p["ingresos_extra"] or p["gasto_hoy"] > 0, texto
        t = texto.lower()
        if any(w in t for w in ("cobro", "recibo", "pagan", "gano", "ingreso de", "adelantan", "entra un")) and "si gasto" not in t:
            assert p["gasto_hoy"] == 0.0, texto


@pytest.mark.parametrize(
    "texto,esperada",
    [
        ("¿Por qué está tan bajo mi número?", "explicar_numero"),  # 'que es' no es subcadena de 'que esta'
        ("¿hoy sí me alcanza para la luz?", "estado_pago"),  # 'y si' no es subcadena de 'hoy si'
        ("¿qué acciones puedo tomar?", None),  # 'acciones' no manda al rechazo fijo
    ],
)
def test_palabras_clave_respetan_limites_de_palabra(cfg, texto, esperada):
    bajo = it.Intencion("concepto", 0.1)
    nombre = it._ajustar_con_palabras_clave(bajo, texto, cfg).nombre
    assert nombre != "fuera_de_alcance"
    if esperada:
        assert nombre == esperada


def test_parametros_del_llm_tambien_se_validan(cfg):
    with pytest.raises(ValueError, match="dia_fuera_de_rango"):
        _p("y si me depositan algo", cfg, monto=120.0, dia=99)

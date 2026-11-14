"""Flujo del asistente (modo 1, sin LLM): guardia -> intención -> parámetros -> herramientas -> plantilla -> verificador.

Servicio falso con una Decision del motor real (fixtures), para probar cada capa sin datos ni red.
"""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

import motor
from asistente import flujo, plantillas
from asistente.intenciones import Intencion
from contratos import Respuesta
from contratos.config import RAIZ
from servicio import ErrorServicio

FECHA = date(2025, 11, 14)


class FakeServicio:
    def __init__(self, cfg, decision=None, error=None, simular=None):
        self._c, self._d, self._e = cfg, decision, error
        self.consultas: list[tuple] = []
        if simular is not None:
            self.simular = simular

    def _cfg(self):
        return self._c

    def consultar(self, customer_id, fecha, metodo="modelo"):
        self.consultas.append((customer_id, fecha, metodo))
        if self._e:
            raise self._e
        return self._d


@pytest.fixture
def cfg_chat(cfg, tmp_path):
    return cfg.con(asistente={**cfg["asistente"], "ruta_registro_chat": str(tmp_path / "chat.jsonl")})


@pytest.fixture
def decision(cfg, estado_tipico, pronostico_tipico):
    return motor.decidir(estado_tipico, pronostico_tipico, cfg)


@pytest.fixture
def srv(cfg_chat, decision):
    return FakeServicio(cfg_chat, decision)


def preguntar(servicio, texto):
    return flujo.preguntar(servicio, "P0002", FECHA, texto)


def esperado_despues(decision, gasto=0.0, extras=()):
    """Número de hoy con un escenario, recalculado a mano desde el desglose (fórmula del diseño)."""
    d = decision.desglose
    minimo = min(
        (d["saldo"] - gasto + p["ingreso_conservador"] + sum(m for dia, m in extras if dia <= p["dia"])
         - p["pagos_acumulados"] - d["colchon"]) / max(p["dia"], 1)
        for p in d["puntos_de_control"]
    )
    return int(math.floor(max(0.0, minimo)))


def lineas(cfg):
    ruta = Path(cfg["asistente"]["ruta_registro_chat"])
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines()]


# --- guardia -----------------------------------------------------------------

def test_los_12_ataques_se_rechazan_en_la_guardia_sin_llamar_al_servicio(srv):
    ataques = pd.read_csv(Path(RAIZ) / "data" / "chat" / "ataques.csv")
    for texto in ataques["texto"]:
        r = preguntar(srv, texto)
        assert isinstance(r, Respuesta)
        assert (r.fuente, r.datos["capa"]) == ("rechazo", "guardia"), texto[:40]
        assert r.registro_id and r.texto
    assert srv.consultas == []


def test_texto_no_str_no_lanza(srv):
    r = preguntar(srv, None)
    assert r.fuente == "rechazo" and r.datos["motivo"] == "vacio"


# --- intención -----------------------------------------------------------------

def test_fuera_de_alcance_se_rechaza_en_la_intencion(srv):
    r = preguntar(srv, "dame un prestamo")
    assert (r.fuente, r.intencion, r.datos["capa"]) == ("rechazo", "fuera_de_alcance", "intencion")
    assert "no doy asesoría" in r.texto.lower() and srv.consultas == []


def test_bajo_el_umbral_pide_reformular_con_tres_sugerencias(srv, monkeypatch):
    monkeypatch.setattr(flujo.intenciones, "clasificar", lambda t, c, proveedor=None: Intencion("explicar_numero", 0.10))
    r = preguntar(srv, "asdf qwer")
    assert (r.fuente, r.intencion) == ("plantilla", "reformular")
    assert r.acciones == plantillas.SUGERENCIAS and len(r.acciones) == 3
    assert srv.consultas == []


def test_baja_confianza_en_fuera_de_alcance_tambien_pide_reformular(srv):
    r = preguntar(srv, "asdf qwer zxcv")  # el clasificador da fuera_de_alcance con confianza 0.23 < 0.30
    assert r.intencion == "reformular"


# --- parámetros ------------------------------------------------------------------

@pytest.mark.parametrize("texto,motivo,frase", [
    ("y si cobro S/100 el dia 20", "dia_fuera_de_rango", "solo veo hasta 14 dias"),
    ("y si cobro 20000 soles el dia 3", "monto_fuera_de_rango", "10000"),
    ("y si cobro 100 el dia 1, 100 el dia 2, 100 el dia 3 y 100 el dia 4", "demasiados_ingresos", "3 ingresos"),
])
def test_parametros_fuera_de_rango_son_rechazo_amable(srv, texto, motivo, frase):
    r = preguntar(srv, texto)
    assert (r.fuente, r.datos["capa"], r.datos["motivo"]) == ("rechazo", "parametros", motivo)
    assert frase in r.texto.lower() and srv.consultas == []


# --- herramientas y plantillas ---------------------------------------------------

def test_explicar_numero(srv, decision):
    r = preguntar(srv, "por que hoy puedo gastar menos que ayer")
    assert (r.fuente, r.intencion, r.datos["verificacion"]) == ("motor", "explicar_numero", "ok")
    assert f"S/{int(decision.numero_hoy)}" in r.texto and r.acciones
    assert srv.consultas == [("P0002", FECHA, "modelo")]


def test_estado_pago_nombra_el_pago_y_su_semaforo(srv, decision):
    pago = decision.por_pago[0]
    r = preguntar(srv, f"me alcanza para el pago del dia {pago.dia}")
    assert (r.intencion, r.datos["verificacion"]) == ("estado_pago", "ok") and str(pago.dia) in r.texto
    assert plantillas.ETIQUETA[pago.semaforo] in r.texto
    assert f"S/{int(pago.monto)}" in r.texto


def test_estado_pago_sin_pago_ese_dia(srv):
    r = preguntar(srv, "me alcanza para el pago del dia 2")
    assert r.intencion == "estado_pago" and "no hay un pago con fecha el día 2" in r.texto.lower()
    assert r.datos["verificacion"] == "ok"  # sin pago que nombrar no hay cifra clave que exigir


def test_que_pasa_si_gasto(srv, decision):
    r = preguntar(srv, "y si gasto 80 soles hoy")
    esperado = esperado_despues(decision, gasto=80)
    assert (r.fuente, r.intencion) == ("motor", "que_pasa_si")
    assert r.datos["antes"]["numero_hoy"] == int(decision.numero_hoy)
    assert r.datos["despues"]["numero_hoy"] == esperado <= int(decision.numero_hoy)
    assert f"S/{esperado}" in r.texto and f"S/{int(decision.numero_hoy)}" in r.texto
    assert "simulación" in r.texto.lower()


def test_que_pasa_si_cobro(srv, decision):
    r = preguntar(srv, "y si cobro S/200 el dia 5")
    esperado = esperado_despues(decision, extras=[(5, 200.0)])
    assert r.datos["despues"]["numero_hoy"] == esperado >= int(decision.numero_hoy)


def test_escenario_sin_cambios_da_el_mismo_numero(decision):
    assert esperado_despues(decision) == int(decision.numero_hoy)  # la fórmula de la prueba coincide con el motor


def test_que_pasa_si_sin_monto_pide_el_monto(srv):
    r = preguntar(srv, "y si no entra ningun ingreso esta semana")
    assert (r.fuente, r.datos["motivo"]) == ("plantilla", "sin_monto") and srv.consultas == []


def test_propuesta_con_propuesta_del_motor(srv, decision):
    (prop,) = decision.propuestas
    r = preguntar(srv, "que hago para llegar a mi pago")
    assert r.intencion == "propuesta" and f"S/{int(prop.monto)}" in r.texto


def test_propuesta_sin_propuesta(cfg_chat, estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg):
    d = motor.decidir(estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg)
    r = preguntar(FakeServicio(cfg_chat, d), "que hago para llegar a mi pago")
    assert r.intencion == "propuesta" and "no hay una propuesta" in r.texto.lower()
    assert r.datos["verificacion"] == "ok"


def test_concepto_solo_conocimiento_no_consulta_el_servicio(srv):
    r = preguntar(srv, "que significa confianza media")
    assert r.intencion == "concepto" and "confianza" in r.texto.lower()
    assert srv.consultas == []


# --- errores ----------------------------------------------------------------------

def test_error_del_servicio_es_rechazo_con_su_mensaje(cfg_chat):
    srv = FakeServicio(cfg_chat, error=ErrorServicio("No hay movimientos para la persona 'P0002'."))
    r = preguntar(srv, "por que hoy puedo gastar menos que ayer")
    assert (r.fuente, r.datos["capa"]) == ("rechazo", "servicio") and "No hay movimientos" in r.texto


def test_error_inesperado_nunca_llega_a_la_app(cfg_chat):
    r = preguntar(FakeServicio(cfg_chat, error=RuntimeError("boom")), "por que hoy puedo gastar menos que ayer")
    assert (r.fuente, r.datos["motivo"]) == ("rechazo", "error_interno") and "boom" not in r.texto


# --- verificador y puntos de enchufe ------------------------------------------------

def test_respuesta_que_no_verifica_cae_a_la_plantilla_segura(srv, monkeypatch):
    monkeypatch.setattr(plantillas, "plantilla", lambda i, r: ("Hoy puedes gastar hasta S/99999.", []))
    r = preguntar(srv, "por que hoy puedo gastar menos que ayer")
    assert r.fuente == "plantilla" and "99999" not in r.texto
    assert "cifra_inventada" in r.datos["verificacion"]


def test_enchufe_de_plantillas_de_sebastian(srv, decision, monkeypatch):
    visto = {}

    def real(intencion, resultados):
        visto.update(intencion=intencion, numero=resultados["numero_hoy"])
        return f"Hoy puedes gastar hasta S/{int(resultados['numero_hoy'])}.", ["Ver la pantalla Hoy"]

    monkeypatch.setattr(plantillas, "plantilla", real)
    r = preguntar(srv, "por que hoy puedo gastar menos que ayer")
    assert r.texto.startswith("Hoy puedes gastar hasta") and r.acciones == ["Ver la pantalla Hoy"]
    assert visto == {"intencion": "explicar_numero", "numero": int(decision.numero_hoy)}


def test_enchufe_de_servicio_simular(cfg_chat, decision, estado_tipico, pronostico_tipico, cfg):
    despues = motor.decidir(estado_tipico.model_copy(update={"saldo": estado_tipico.saldo - 1000}), pronostico_tipico, cfg)
    llamadas = []

    def simular(customer_id, fecha, escenario):
        llamadas.append(escenario)
        return despues

    srv = FakeServicio(cfg_chat, decision, simular=simular)
    r = preguntar(srv, "y si gasto 1000 soles hoy")
    assert llamadas[0].gasto_hoy == 1000.0
    assert r.datos["despues"]["numero_hoy"] == int(despues.numero_hoy)


# --- registro ------------------------------------------------------------------------

def test_registro_con_la_pregunta_enmascarada(srv, cfg_chat):
    preguntar(srv, "Mi DNI es 12345678, ¿me alcanza?")
    preguntar(srv, "por que hoy puedo gastar menos que ayer")
    rechazo, ok = lineas(cfg_chat)
    assert "12345678" not in json.dumps(rechazo) and "***" in rechazo["pregunta"]
    assert rechazo["capa"] == "guardia"
    assert {"registro_id", "pregunta", "intencion", "fuente", "verificacion", "latencia_ms",
            "decision_registro_id"} <= set(ok)
    assert ok["fuente"] == "motor" and ok["verificacion"] == "ok"

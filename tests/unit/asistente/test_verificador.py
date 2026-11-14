"""Verificador de salida del asistente: cada cifra tiene origen, citas reales, sin nombres internos ni URL."""

from __future__ import annotations

import pytest

from asistente.verificador import verificar_respuesta

RESULTADOS = {
    "intencion": "explicar_numero",
    "numero_hoy": 370,
    "saldo": 4816.92,
    "pagos": [{"dia": 6, "monto": 110.78}, {"dia": 7, "monto": 220.0}],
    "dia_limitante": 14,
}
PASAJES = [{"id": "kb:glosario#2", "texto": "El P20 es una semana mala moderada; usa 14 dias."}]
BUENA = "Datos: puedes gastar S/370 hoy. Que significa: el pago de S/220 del dia 7 queda cubierto."


def ok(obj, resultados=RESULTADOS, pasajes=(), cfg=None):
    return verificar_respuesta(obj, resultados, list(pasajes), cfg)


def test_respuesta_con_cifras_de_los_resultados_pasa(cfg):
    assert ok({"respuesta": BUENA, "citas": []}, cfg=cfg) == (True, [])


def test_cifra_inventada(cfg):
    good, motivos = ok({"respuesta": BUENA + " Ademas ganaras S/999.", "citas": []}, cfg=cfg)
    assert good is False and motivos == ["cifra_inventada"]


def test_etiquetas_de_cuantil_no_son_cifras(cfg):
    assert ok({"respuesta": BUENA + " Es un escenario P20 y P5.", "citas": []}, cfg=cfg)[0] is True


def test_cifras_de_los_pasajes_estan_permitidas_si_se_citan(cfg):
    texto = BUENA + " El horizonte llega a 14 dias [kb:glosario#2]."
    assert ok({"respuesta": texto, "citas": ["kb:glosario#2"]}, pasajes=PASAJES, cfg=cfg) == (True, [])


def test_cita_inexistente(cfg):
    good, motivos = ok({"respuesta": BUENA, "citas": ["kb:otro#1"]}, pasajes=PASAJES, cfg=cfg)
    assert good is False and "cita_inexistente" in motivos


def test_falta_cita_si_hay_pasajes_y_no_se_cita(cfg):
    good, motivos = ok({"respuesta": BUENA, "citas": []}, pasajes=PASAJES, cfg=cfg)
    assert good is False and motivos == ["falta_cita"]


def test_largo_por_max_palabras_de_la_config(cfg):
    corto = cfg.con(asistente={**cfg["asistente"], "max_palabras": 5})
    good, motivos = ok({"respuesta": BUENA, "citas": []}, cfg=corto)
    assert good is False and "largo" in motivos


@pytest.mark.parametrize("texto", [
    "Datos: S/370. Mira numero_hoy en el desglose.",
    "Datos: S/370. Revisa src/motor/decidir.py.",
    "Datos: S/370. Llama a servicio.consultar.",
])
def test_nombre_interno(cfg, texto):
    good, motivos = ok({"respuesta": texto, "citas": []}, cfg=cfg)
    assert good is False and "nombre_interno" in motivos


def test_la_cita_entre_corchetes_no_cuenta_como_nombre_interno(cfg):
    p = [{"id": "kb:calculo_numero_hoy#2", "texto": "formula"}]
    assert ok({"respuesta": BUENA + " [kb:calculo_numero_hoy#2]", "citas": ["kb:calculo_numero_hoy#2"]},
              pasajes=p, cfg=cfg) == (True, [])


@pytest.mark.parametrize("texto", [
    "Datos: S/370. Mas en https://x.example",
    "Datos: S/370. Escribe a ana@ejemplo.com",
    "Datos: S/370. Es un rendimiento garantizado.",
    "Datos: S/370. Pide un prestamo.",
])
def test_prohibida_o_pii(cfg, texto):
    good, motivos = ok({"respuesta": texto, "citas": []}, cfg=cfg)
    assert good is False and "prohibida_o_pii" in motivos


@pytest.mark.parametrize("intencion", ["explicar_numero", "que_pasa_si"])
def test_falta_cifra_clave(cfg, intencion):
    res = {**RESULTADOS, "intencion": intencion}
    good, motivos = ok({"respuesta": "Datos: el pago de S/220 del dia 7 queda cubierto.", "citas": []}, res, cfg=cfg)
    assert good is False and motivos == ["falta_cifra_clave"]


def test_cifra_clave_explicita_manda_sobre_el_numero_de_hoy(cfg):
    res = {**RESULTADOS, "intencion": "estado_pago", "cifra_clave": 220.0}
    assert ok({"respuesta": "El pago de S/220 del dia 7 esta cubierto.", "citas": []}, res, cfg=cfg) == (True, [])
    good, motivos = ok({"respuesta": "El pago del dia 7 esta cubierto.", "citas": []}, res, cfg=cfg)
    assert good is False and motivos == ["falta_cifra_clave"]


def test_estado_pago_sin_pago_que_nombrar_no_exige_cifra(cfg):
    res = {**RESULTADOS, "intencion": "estado_pago", "cifra_clave": None}
    assert ok({"respuesta": "No hay pagos con fecha por ahora.", "citas": []}, res, cfg=cfg) == (True, [])


def test_concepto_no_exige_cifra_clave(cfg):
    res = {**RESULTADOS, "intencion": "concepto"}
    assert ok({"respuesta": "El P20 es una semana mala moderada.", "citas": []}, res, cfg=cfg) == (True, [])


def test_varios_motivos_juntos(cfg):
    good, motivos = ok({"respuesta": "S/777 en https://x.example", "citas": []}, cfg=cfg)
    assert good is False
    assert {"cifra_inventada", "prohibida_o_pii", "falta_cifra_clave"} <= set(motivos)


def test_obj_mal_formado_no_lanza(cfg):
    assert ok({"citas": []}, cfg=cfg)[0] is False
    assert ok({"respuesta": 5, "citas": None}, cfg=cfg)[0] is False

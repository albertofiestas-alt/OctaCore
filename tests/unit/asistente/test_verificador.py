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


# --- sección 8 del plan: citas reales, cita obligatoria, nombres internos, cada motivo por separado ------------------

OTRO = {"id": "kb:semaforo#1", "texto": "El ambar aparece con 45 de margen."}


def test_cita_en_el_texto_que_no_fue_recuperada(cfg):
    texto = BUENA + " [kb:inventado#9]"
    good, motivos = ok({"respuesta": texto, "citas": ["kb:glosario#2"]}, pasajes=PASAJES, cfg=cfg)
    assert good is False and motivos == ["cita_inexistente"]


def test_corchetes_que_no_son_cita_se_revisan(cfg):
    good, motivos = ok({"respuesta": BUENA + " [S/999]", "citas": []}, cfg=cfg)
    assert good is False and motivos == ["cifra_inventada"]


def test_cifra_de_un_pasaje_no_citado_exige_su_cita(cfg):
    texto = BUENA + " Hay 45 de margen [kb:glosario#2]."
    good, motivos = ok({"respuesta": texto, "citas": ["kb:glosario#2"]}, pasajes=[*PASAJES, OTRO], cfg=cfg)
    assert good is False and motivos == ["falta_cita"]
    texto = BUENA + " Hay 45 de margen [kb:semaforo#1]."
    assert ok({"respuesta": texto, "citas": ["kb:semaforo#1"]}, pasajes=[*PASAJES, OTRO], cfg=cfg) == (True, [])


def test_la_cita_en_el_texto_cuenta_como_cita(cfg):
    texto = BUENA + " El horizonte llega a 14 dias [kb:glosario#2]."
    assert ok({"respuesta": texto, "citas": []}, pasajes=PASAJES, cfg=cfg) == (True, [])


@pytest.mark.parametrize("texto", [
    "Datos: S/370. Lo calcula decidir().",
    "Datos: S/370. Viene de motor.simular(estado, pron, escenario).",
    "Datos: S/370. Es un EstadoPersona.",
    "Datos: S/370. Mira desglose['saldo'].",
    "Datos: S/370. Esta en data/chat/preguntas.",
    r"Datos: S/370. Esta en src\motor.",
    "Datos: S/370. Ver decision#7 del desglose.",
    "Datos: S/370. Lo dice config/base.yaml.",
])
def test_mas_nombres_internos(cfg, texto):
    good, motivos = ok({"respuesta": texto, "citas": []}, cfg=cfg)
    assert good is False and "nombre_interno" in motivos


@pytest.mark.parametrize("texto", [
    "Datos: puedes gastar S/370 hoy. Qué puedes hacer: Simular un ingreso extra; revisar tu(s) pago(s).",
    "Datos: puedes gastar S/370 hoy (confianza media). Por tu seguridad no compartas tu clave.",
])
def test_texto_natural_no_es_nombre_interno_ni_prohibido(cfg, texto):
    assert ok({"respuesta": texto, "citas": []}, cfg=cfg) == (True, [])


@pytest.mark.parametrize("texto, propio", [
    ("Datos: S/370. Mas en https://x.example", "url"),
    ("Datos: S/370. Mas en www.ejemplo.pe", "url"),
    ("Datos: S/370. Escribe a ana@ejemplo.com", "pii"),
    ("Datos: S/370. Es un rendimiento garantizado.", "prohibida"),
    ("Datos: S/370. Tienes una garantia total.", "prohibida"),
    ("Datos: S/370. Te aseguro que llega.", "prohibida"),
])
def test_url_pii_y_prohibida_tienen_su_propio_motivo(cfg, texto, propio):
    good, motivos = ok({"respuesta": texto, "citas": []}, cfg=cfg)
    assert good is False and propio in motivos and "prohibida_o_pii" in motivos
    assert not {"url", "pii", "prohibida"} - {propio} & set(motivos)


def test_cifra_clave_se_compara_completa(cfg):
    res = {**RESULTADOS, "intencion": "estado_pago", "cifra_clave": 1, "pagos": [{"dia": 1, "monto": 150}]}
    good, motivos = ok({"respuesta": "El pago del dia 1 por S/150 esta cubierto.", "citas": []}, res, cfg=cfg)
    assert good is False and motivos == ["falta_cifra_clave"]


def test_cifra_clave_con_separador_de_miles(cfg):
    res = {"intencion": "explicar_numero", "numero_hoy": 1200}
    assert ok({"respuesta": "Hoy puedes gastar S/1,200.", "citas": []}, res, cfg=cfg) == (True, [])


def test_citas_mal_formadas_no_lanzan(cfg):
    assert ok({"respuesta": BUENA, "citas": "kb:glosario#2"}, pasajes=PASAJES, cfg=cfg) == (True, [])
    assert ok({"respuesta": BUENA, "citas": 7}, cfg=cfg) == (True, [])


# --- con una Decision simulada de motor.simular (que_pasa_si) --------------------------------------------------------

def _que_pasa_si(cfg, estado, pron, esc):
    from asistente import plantillas, rag
    from motor import decidir
    from motor.simular import simular

    antes = decidir(estado, pron, cfg)
    despues = simular(estado, pron, esc, cfg)
    res = plantillas.resultados_de(antes, escenario=esc, simulada=despues)
    texto, _ = plantillas.plantilla("que_pasa_si", res)
    resultados = {**res, "intencion": "que_pasa_si", "cifra_clave": int(despues.numero_hoy)}
    return texto, resultados, rag.kb_dinamica(antes), despues


@pytest.mark.parametrize("esc", [
    {"ingresos_extra": [{"dia": 2, "monto": 250}]},
    {"ingresos_extra": [{"dia": 2, "monto": 250.5}, {"dia": 9, "monto": 37}], "gasto_hoy": 12.25},
    {"gasto_hoy": 80},
])
def test_las_cifras_del_escenario_cuentan_como_permitidas(cfg, estado_caso_orden_pagos, pronostico_caso_orden_pagos, esc):
    from contratos import Escenario

    e = Escenario.model_validate(esc)
    texto, res, pasajes, despues = _que_pasa_si(cfg, estado_caso_orden_pagos, pronostico_caso_orden_pagos, e)
    assert ok({"respuesta": texto, "citas": ["decision#1"]}, res, pasajes, cfg) == (True, []), texto
    for i in e.ingresos_extra:
        assert f"día {i.dia}" in texto
    # la misma respuesta con una cifra que el escenario no tiene se rechaza
    good, motivos = ok({"respuesta": texto + " Te sobran S/9876.", "citas": ["decision#1"]}, res, pasajes, cfg)
    assert good is False and motivos == ["cifra_inventada"]


def test_que_pasa_si_exige_el_numero_despues(cfg, estado_caso_orden_pagos, pronostico_caso_orden_pagos):
    from contratos import Escenario

    e = Escenario(ingresos_extra=[{"dia": 2, "monto": 250}])
    texto, res, pasajes, despues = _que_pasa_si(cfg, estado_caso_orden_pagos, pronostico_caso_orden_pagos, e)
    assert despues.numero_hoy > 0
    sin_despues = texto.replace(f"a S/{int(despues.numero_hoy)}.", "a otro valor.")
    good, motivos = ok({"respuesta": sin_despues, "citas": ["decision#1"]}, res, pasajes, cfg)
    assert good is False and "falta_cifra_clave" in motivos

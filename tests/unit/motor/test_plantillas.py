"""Pruebas de src/motor/plantillas.py (supuestos, límites, explicación y propuestas).

Se prueba plantillas.py directamente, sin pasar por decidir. Si `motor` todavía no
se puede importar (decidir.py en construcción), se carga el archivo con importlib.
"""

from __future__ import annotations

import importlib.util
import math
import re
from pathlib import Path
from typing import Any

import pytest

from contratos import DecisionPago, EstadoPersona, PagoConFecha

try:
    from motor import plantillas
except Exception:  # pragma: no cover - solo mientras decidir.py no existe
    _ruta = Path(__file__).resolve().parents[3] / "src" / "motor" / "plantillas.py"
    _spec = importlib.util.spec_from_file_location("motor_plantillas_aislado", _ruta)
    plantillas = importlib.util.module_from_spec(_spec)
    assert _spec.loader is not None
    _spec.loader.exec_module(plantillas)


# --------------------------------------------------------------------------- #
# Ayudas: extractor de cifras y cifras permitidas
# --------------------------------------------------------------------------- #

# Números del texto; se ignoran las etiquetas de cuantil (P5, P20, ...).
_NUMERO = re.compile(r"(?<![A-Za-z\d.,])(?<!P)\d+(?:,\d{3})*(?:\.\d+)?")


def cifras(texto: str) -> list[float]:
    return [float(m.group().replace(",", "")) for m in _NUMERO.finditer(texto)]


def _numeros(obj: Any) -> set[float]:
    if isinstance(obj, bool):
        return set()
    if isinstance(obj, (int, float)):
        x = float(obj)
        return {x, float(math.floor(x)), float(math.ceil(x)), round(x, 2)}
    if isinstance(obj, dict):
        return set().union(*(_numeros(v) for v in obj.values())) if obj else set()
    if isinstance(obj, (list, tuple)):
        return set().union(*(_numeros(v) for v in obj)) if obj else set()
    if hasattr(obj, "model_dump"):
        return _numeros(obj.model_dump(mode="python"))
    return set()


def permitidas(*fuentes: Any) -> set[float]:
    total: set[float] = set()
    for f in fuentes:
        total |= _numeros(f)
    if fuentes and isinstance(fuentes[0], EstadoPersona):
        total.add(float(len(fuentes[0].pagos)))
    return total


def assert_cifras_con_origen(texto: str, *fuentes: Any) -> None:
    ok = permitidas(*fuentes)
    sin_origen = [c for c in cifras(texto) if round(c, 2) not in {round(x, 2) for x in ok}]
    assert not sin_origen, f"cifras sin origen {sin_origen} en: {texto!r}"


def assert_sin_tasas(texto: str) -> None:
    assert "%" not in texto
    assert "tasa" not in texto.lower()
    assert "porcentaje" not in texto.lower()


def test_extractor_de_cifras_ignora_etiquetas_de_cuantil():
    assert cifras("El escenario P20 es malo y el P5 peor") == []
    assert cifras("S/1,234.50 en 3 días y S/45.56") == [1234.5, 3.0, 45.56]


# --------------------------------------------------------------------------- #
# Datos de prueba
# --------------------------------------------------------------------------- #


def _punto(dia, ingreso, pagos, numerador, permitido):
    return {
        "dia": dia,
        "ingreso_conservador": ingreso,
        "pagos_acumulados": pagos,
        "numerador": numerador,
        "permitido": permitido,
    }


@pytest.fixture
def estado_t(estado_tipico) -> EstadoPersona:
    return estado_tipico


@pytest.fixture
def desglose_tipico() -> dict:
    # Caso típico de la especificación: permitidos 66, 45.56, 20 -> número 20, día 14.
    return {
        "saldo": 400.0,
        "colchon": 50.0,
        "cuantil": "p20",
        "numero_hoy": 20,
        "puntos_de_control": [
            _punto(5, 60.0, 80.0, 330.0, 66.0),
            _punto(9, 200.0, 140.0, 410.0, 45.56),
            _punto(14, 420.0, 490.0, 280.0, 20.0),
        ],
        "dia_limitante": 14,
        "faltante": None,
        "registro_id": "",
    }


@pytest.fixture
def por_pago_tipico() -> list[DecisionPago]:
    return [
        DecisionPago(pago_id="P0002:Luz Ficticia:2025-11-19", dia=5, monto=80, permitido=66.0, semaforo="verde"),
        DecisionPago(pago_id="P0002:Internet Ficticio:2025-11-23", dia=9, monto=60, permitido=45.56, semaforo="verde"),
        DecisionPago(pago_id="P0002:Financiera Ficticia:2025-11-28", dia=14, monto=350, permitido=20.0, semaforo="verde"),
    ]


@pytest.fixture
def desglose_orden() -> dict:
    # Caso del orden de pagos: saldo 100, pago 300 el día 3, sin ingreso hasta el día 10.
    return {
        "saldo": 100.0,
        "colchon": 0.0,
        "cuantil": "p20",
        "numero_hoy": 0,
        "puntos_de_control": [
            _punto(3, 0.0, 300.0, -200.0, -66.67),
            _punto(14, 500.0, 300.0, 300.0, 21.43),
        ],
        "dia_limitante": 3,
        "faltante": 200,
        "registro_id": "registro-secreto-123",
    }


@pytest.fixture
def estado_sin_pagos() -> EstadoPersona:
    return EstadoPersona(customer_id="P0009", fecha_corte="2025-11-14", saldo=250.5, colchon=10, semanas_historia=8)


@pytest.fixture
def desglose_sin_pagos() -> dict:
    return {
        "saldo": 250.5,
        "colchon": 10.0,
        "cuantil": "p20",
        "numero_hoy": 33,
        "puntos_de_control": [_punto(14, 230.0, 0.0, 470.5, 33.61)],
        "dia_limitante": 14,
        "faltante": None,
        "registro_id": "",
    }


# --------------------------------------------------------------------------- #
# _soles
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("x", "esperado"),
    [(300, "300"), (300.0, "300"), (45.56, "45.56"), (7.5, "7.50"), (0, "0"), (1234.0, "1234")],
)
def test_soles_entero_si_es_entero_si_no_dos_decimales(x, esperado):
    assert plantillas._soles(x) == esperado


# --------------------------------------------------------------------------- #
# supuestos
# --------------------------------------------------------------------------- #


def test_supuestos_cinco_frases_con_cifras_del_estado(estado_t):
    evidencia = {"semanas_historia": 20, "pagos_detectados": 3}
    s = plantillas.supuestos(estado_t, evidencia)
    assert s == [
        "Gastas cada día lo que indica el número de hoy.",
        "Los pagos con fecha son los 3 detectados en tu historial.",
        "El ingreso futuro se parece al de las últimas 20 semanas.",
        "No se consideran gastos imprevistos.",
        "El escenario P20 es una semana mala y el P5 una semana muy mala.",
    ]
    for frase in s:
        assert_sin_tasas(frase)
        assert_cifras_con_origen(frase, estado_t, evidencia)


def test_supuestos_nunca_vacia_aun_con_evidencia_vacia(estado_sin_pagos):
    s = plantillas.supuestos(estado_sin_pagos, {})
    assert len(s) == 5 and all(s)
    assert "Los pagos con fecha son los 0 detectados en tu historial." in s
    assert "El ingreso futuro se parece al de las últimas 8 semanas." in s
    for frase in s:
        assert_cifras_con_origen(frase, estado_sin_pagos)


# --------------------------------------------------------------------------- #
# limites
# --------------------------------------------------------------------------- #


def test_limites_fijos_primero_y_contexto_despues(cfg):
    lim = plantillas.limites({"semanas_historia": 20}, cfg)
    assert lim[: len(plantillas.LIMITES_FIJOS)] == list(plantillas.LIMITES_FIJOS)
    assert lim[len(plantillas.LIMITES_FIJOS) :] == [
        "El ingreso futuro es un rango, no una cifra exacta.",
        "Los datos son ficticios.",
    ]
    for frase in lim:
        assert_sin_tasas(frase)
        assert cifras(frase) == []


def test_limites_con_poca_historia_agrega_confianza_baja(cfg):
    umbral = cfg["umbral_historia_semanas"]
    lim = plantillas.limites({"semanas_historia": umbral - 1}, cfg)
    assert lim[: len(plantillas.LIMITES_FIJOS)] == list(plantillas.LIMITES_FIJOS)
    assert lim[-1] == "Con pocas semanas de historia la confianza es baja."
    en_umbral = plantillas.limites({"semanas_historia": umbral}, cfg)
    assert "Con pocas semanas de historia la confianza es baja." not in en_umbral


def test_limites_devuelve_lista_nueva(cfg):
    a = plantillas.limites({"semanas_historia": 20}, cfg)
    a.append("x")
    assert "x" not in plantillas.limites({"semanas_historia": 20}, cfg)
    assert isinstance(plantillas.LIMITES_FIJOS, tuple)


# --------------------------------------------------------------------------- #
# explicar
# --------------------------------------------------------------------------- #


def test_explicar_con_mensaje_falta(estado_caso_orden_pagos, desglose_orden):
    texto = plantillas.explicar(
        estado_caso_orden_pagos,
        0,
        "no alcanza para el pago del dia 3: faltan S/200",
        [DecisionPago(pago_id="alquiler-03", dia=3, monto=300, permitido=-66.67, semaforo="rojo")],
        "media",
        desglose_orden,
    )
    assert texto.startswith("Hoy no conviene gastar")
    assert "alquiler" in texto
    assert "S/300" in texto and "S/300.0" not in texto
    assert "3 días" in texto
    assert "faltan S/200" in texto
    assert "registro-secreto-123" not in texto
    assert "Confianza: media." in texto
    assert_sin_tasas(texto)
    assert_cifras_con_origen(texto, estado_caso_orden_pagos, desglose_orden)


def test_explicar_numero_positivo(estado_t, desglose_tipico, por_pago_tipico):
    texto = plantillas.explicar(estado_t, 20, None, por_pago_tipico, "media", desglose_tipico)
    assert "Puedes gastar hasta S/20 hoy." in texto
    assert "deuda" in texto and "S/350" in texto and "14 días" in texto
    assert texto.endswith("Confianza: media.")
    assert_sin_tasas(texto)
    assert_cifras_con_origen(texto, estado_t, desglose_tipico)


def test_explicar_sin_pagos(estado_sin_pagos, desglose_sin_pagos):
    texto = plantillas.explicar(estado_sin_pagos, 33, None, [], "alta", desglose_sin_pagos)
    assert "Puedes gastar hasta S/33 hoy." in texto
    assert "No hay pagos con fecha" in texto
    assert "Confianza: alta." in texto
    assert_sin_tasas(texto)
    assert_cifras_con_origen(texto, estado_sin_pagos, desglose_sin_pagos)


def test_explicar_numero_cero_sin_falta(estado_t, desglose_tipico, por_pago_tipico):
    desglose = {**desglose_tipico, "numero_hoy": 0}
    desglose["puntos_de_control"] = [
        *desglose_tipico["puntos_de_control"][:2],
        _punto(14, 420.0, 490.0, 7.0, 0.5),
    ]
    texto = plantillas.explicar(estado_t, 0, None, por_pago_tipico, "baja", desglose)
    assert texto.startswith("Hoy no conviene gastar")
    assert "S/350" in texto
    assert "Confianza: baja." in texto
    assert_sin_tasas(texto)
    assert_cifras_con_origen(texto, estado_t, desglose)


def test_explicar_dia_limite_sin_pago_ese_dia(desglose_orden):
    # El día 14 limita pero no hay pago ese día: se nombra el día, sin inventar un pago.
    estado = EstadoPersona(
        customer_id="P0003",
        fecha_corte="2025-11-14",
        saldo=50,
        pagos=[PagoConFecha(pago_id="srv-2", dia=2, monto=40, categoria="servicios")],
    )
    desglose = {
        **desglose_orden,
        "saldo": 50.0,
        "puntos_de_control": [_punto(2, 0.0, 40.0, 10.0, 5.0), _punto(14, 0.0, 40.0, -45.5, -3.25)],
        "dia_limitante": 14,
        "faltante": 46,
    }
    texto = plantillas.explicar(
        estado, 0, "no alcanza para el pago del dia 14: faltan S/46", [], "baja", desglose
    )
    assert "faltan S/46" in texto and "14 días" in texto
    assert_sin_tasas(texto)
    assert_cifras_con_origen(texto, estado, desglose)


def test_explicar_pago_hoy(desglose_orden):
    estado = EstadoPersona(
        customer_id="P0004",
        fecha_corte="2025-11-14",
        saldo=10,
        pagos=[PagoConFecha(pago_id="deuda-0", dia=0, monto=60.5, categoria="deuda")],
    )
    desglose = {
        **desglose_orden,
        "saldo": 10.0,
        "puntos_de_control": [_punto(0, 0.0, 60.5, -50.5, -50.5), _punto(14, 300.0, 60.5, 249.5, 17.82)],
        "dia_limitante": 0,
        "faltante": 51,
    }
    texto = plantillas.explicar(
        estado, 0, "no alcanza para el pago del dia 0: faltan S/51", [], "baja", desglose
    )
    assert "S/60.50" in texto and "vence hoy" in texto and "faltan S/51" in texto
    assert_cifras_con_origen(texto, estado, desglose)


# --------------------------------------------------------------------------- #
# Propuestas: registro por tipo
# --------------------------------------------------------------------------- #


def test_apartar_p5_registrado_y_texto():
    assert "apartar_p5" in plantillas.TIPOS_PROPUESTA
    datos = {
        "g5": 7,
        "numero_hoy": 20,
        "apartar": 13,
        "pago_id": "P0002:Financiera Ficticia:2025-11-28",
        "dia": 14,
        "monto": 350.0,
        "categoria": "deuda",
    }
    texto = plantillas.texto_propuesta("apartar_p5", datos)
    assert texto == (
        "Gasta hasta S/7 por día en vez de S/20 y aparta S/13 por día para deuda de S/350 del día 14."
    )
    assert_sin_tasas(texto)
    assert_cifras_con_origen(texto, datos)


def test_tipo_inexistente_da_keyerror():
    with pytest.raises(KeyError):
        plantillas.texto_propuesta("no_existe", {})


def test_prueba_de_evolucion_tipo_nuevo_solo_con_decorador():
    """Agregar un tipo = definir una función con @registrar_tipo. Nada más."""
    antes = dict(plantillas.TIPOS_PROPUESTA)
    try:

        @plantillas.registrar_tipo("juguete")
        def _juguete(datos: dict) -> str:
            return f"Revisa tu pago de S/{plantillas._soles(datos['monto'])}."

        assert plantillas.TIPOS_PROPUESTA["juguete"] is _juguete
        assert plantillas.texto_propuesta("juguete", {"monto": 45.5}) == "Revisa tu pago de S/45.50."
        # Los tipos existentes siguen intactos.
        assert {k: v for k, v in plantillas.TIPOS_PROPUESTA.items() if k != "juguete"} == antes
    finally:
        plantillas.TIPOS_PROPUESTA.pop("juguete", None)
    assert plantillas.TIPOS_PROPUESTA == antes


def test_registrar_tipo_duplicado_falla():
    with pytest.raises(ValueError):

        @plantillas.registrar_tipo("apartar_p5")
        def _otra(datos: dict) -> str:  # pragma: no cover
            return ""

"""Pruebas que matan mutaciones que sobrevivían (ver tests/unit/motor/mutaciones.py y MUTACIONES.md).

Cada prueba fija una FRONTERA que ninguna otra prueba tocaba exactamente. Los valores están
calculados a mano en el comentario de cada caso; la mutación que mata está en el nombre.
"""

from __future__ import annotations

from contratos import EstadoPersona, Pronostico
from motor import decidir
from motor.decidir import confianza, semaforo


def _estado(saldo, pagos=(), colchon=0.0, semanas=12):
    return EstadoPersona.model_validate(
        {
            "customer_id": "MUT",
            "fecha_corte": "2025-11-14",
            "saldo": saldo,
            "colchon": colchon,
            "semanas_historia": semanas,
            "pagos": [
                {"pago_id": f"p{i}-d{dia}", "dia": dia, "monto": monto, "categoria": "servicios"}
                for i, (dia, monto) in enumerate(pagos)
            ],
        }
    )


def _pron(h3, h7, h14):
    def q(p5, p20, p50, p80):
        return {"p5": p5, "p20": p20, "p50": p50, "p80": p80}

    return Pronostico.model_validate({"por_horizonte": {3: q(*h3), 7: q(*h7), 14: q(*h14)}})


CERO = (0, 0, 0, 0)


def test_m15_ambar_si_cubre_justo_en_p50(cfg):
    # Mata M15 (`cobertura(P50) >= 0` -> `> 0`).
    # Pago de 150 el día 7, saldo 100. P5 a 7 días = 0 -> 100 + 0 - 150 = -50 (no verde).
    # P50 a 7 días = 50 -> 100 + 50 - 150 = 0: cubierto JUSTO -> ámbar (la mutación da rojo).
    estado = _estado(100, [(7, 150)])
    pron = _pron(CERO, (0, 20, 50, 60), (0, 20, 50, 60))
    assert semaforo(estado, pron, 7, cfg) == "ambar"


def test_m17_ancho_igual_al_umbral_bajo_es_media(cfg):
    # Mata M17 (`ancho > ancho_bajo` -> `>=`). Umbral ancho_bajo = 1.2 (config/motor.yaml).
    # Ancho a 14 días = (P80 - P5) / max(P50, 1) = (120 - 0) / 100 = 1.2: NO es mayor -> media.
    estado = _estado(100, semanas=12)
    pron = _pron(CERO, CERO, (0, 50, 100, 120))
    assert confianza(estado, pron, cfg) == "media"


def test_m18_ancho_igual_al_umbral_alto_es_media(cfg):
    # Mata M18 (`ancho < ancho_alto` -> `<=`). Umbral ancho_alto = 0.5.
    # Ancho = (100 - 50) / 100 = 0.5: NO es menor -> media (la mutación da alta).
    estado = _estado(100, semanas=12)
    pron = _pron(CERO, CERO, (50, 60, 100, 100))
    assert confianza(estado, pron, cfg) == "media"


def test_m19_cuatro_semanas_exactas_es_historia_suficiente(cfg, estado_tipico, pronostico_tipico):
    # Mata M19 (`semanas >= umbral` -> `>`). umbral_historia_semanas = 4.
    # Con 4 semanas hay historia suficiente: confianza alta con ancho (700 - 500) / 600 = 0.33 < 0.5,
    # y el caso típico sigue proponiendo (apartar 13: número 20, g5 = floor(110 / 14) = 7).
    cuatro = _estado(100, semanas=4)
    pron_alta = _pron(CERO, CERO, (500, 550, 600, 700))
    assert confianza(cuatro, pron_alta, cfg) == "alta"
    tipico_4 = estado_tipico.model_copy(update={"semanas_historia": 4})
    d = decidir(tipico_4, pronostico_tipico, cfg)
    assert [p.monto for p in d.propuestas] == [13]

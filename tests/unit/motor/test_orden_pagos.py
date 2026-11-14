"""Caso del orden de pagos (plan de Sebastián, paso 1): la fórmula de la v3 lo hacía mal.

Saldo 100, pago de 300 el día 3 y el ingreso de 400 llega recién el día 10.
Como el ingreso conservador a 3 días es 0, el pago del día 3 no se cubre: faltan S/200.
"""

from __future__ import annotations

from motor import decidir


def test_orden_de_pagos(estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg):
    d = decidir(estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg)

    assert d.numero_hoy == 0
    assert d.mensaje_falta == "no alcanza para el pago del dia 3: faltan S/200"

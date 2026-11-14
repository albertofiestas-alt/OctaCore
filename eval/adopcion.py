"""Regla de adopción pre-registrada. Dueño: Gino. El umbral se fija ANTES de la primera evaluación completa."""

from __future__ import annotations

import json
from pathlib import Path

RUTA_SALIDA = Path(__file__).resolve().parent / "resultados" / "adopcion.json"
_PENDIENTE = "pre-registro pendiente: {campo} es null en config/preregistro.yaml (lo fija Gino antes de evaluar)"


def _punto_regla2(frontera, cuantil):
    candidatos = [p for p in frontera if p["metodo"] == "regla2" and abs(float(p["cuantil"]) - cuantil) < 1e-9]
    if not candidatos:
        raise ValueError(f"la frontera no tiene un punto de regla2 en el cuantil pre-registrado {cuantil}")
    return candidatos[0]


def _gasto_modelo_en(frontera, pct):
    """Gasto del modelo al pct de descubiertos dado: interpolación lineal entre sus puntos. None si pct queda fuera de su rango."""
    pts = sorted((float(p["pct_descubiertos"]), float(p["gasto_permitido"])) for p in frontera if p["metodo"] == "modelo")
    if not pts:
        raise ValueError("la frontera no tiene puntos del método 'modelo'")
    if not pts[0][0] <= pct <= pts[-1][0]:
        return None
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= pct <= x1:
            return y0 if x1 == x0 else y0 + (y1 - y0) * (pct - x0) / (x1 - x0)
    return pts[-1][1]  # un solo punto, igual a pct


def _mejora(frontera, cuantil):
    """(mejora de gasto del modelo sobre regla2 a igual % descubiertos, o None si no hay punto comparable)."""
    ref = _punto_regla2(frontera, cuantil)
    g = _gasto_modelo_en(frontera, float(ref["pct_descubiertos"]))
    return None if g is None else g - float(ref["gasto_permitido"])


def decidir_adopcion(frontera_prueba, frontera_perturbado, pares, prereg) -> dict:
    """Adopta el modelo solo si, con el mismo % de pagos descubiertos que regla2, permite al menos
    prereg["umbral_adopcion_mejora"] más gasto, en la prueba Y en el perturbado.
    Escribe eval/resultados/adopcion.json -> {"adopta": bool, "razon": str}. Si no adopta, el servicio usa regla2.

    Formato de cada frontera (el de eval/resultados/frontera.csv de Rafael): lista de dicts
    {metodo, cuantil, pct_descubiertos, gasto_permitido}. pct_descubiertos en la misma escala en ambas
    fronteras; gasto_permitido en soles por día (el umbral va en esas mismas unidades, absoluto, no relativo).

    Comparación: se toma el punto de regla2 en prereg["cuantil_conservador"]; el gasto del modelo a ese
    mismo pct_descubiertos se interpola linealmente entre sus puntos. Si el modelo no cubre ese pct
    (sin punto comparable) no se extrapola y no se adopta.
    `pares` (pares de semillas, con intervalo) no entra en la decisión: el plan la define solo con las
    fronteras. Queda en la firma por contrato.
    Lanza ValueError("pre-registro pendiente ...") si umbral_adopcion_mejora o cuantil_conservador son null:
    no se inventa ningún valor y no se escribe el JSON."""
    for campo in ("umbral_adopcion_mejora", "cuantil_conservador"):
        if prereg.get(campo) is None:
            raise ValueError(_PENDIENTE.format(campo=campo))
    umbral, cuantil = float(prereg["umbral_adopcion_mejora"]), float(prereg["cuantil_conservador"])

    resultados = {"prueba": _mejora(frontera_prueba, cuantil), "perturbado": _mejora(frontera_perturbado, cuantil)}
    partes, adopta = [], True
    for nombre, mejora in resultados.items():
        if mejora is None:
            adopta = False
            partes.append(f"{nombre}: sin punto comparable con regla2")
        elif mejora < umbral:
            adopta = False
            partes.append(f"{nombre}: mejora {mejora:.4g} < umbral {umbral:g}")
        else:
            partes.append(f"{nombre}: mejora {mejora:.4g} >= umbral {umbral:g}")
    razon = ("Adopta el modelo. " if adopta else "No adopta: se usa regla2. ") + "; ".join(partes)

    veredicto = {"adopta": adopta, "razon": razon}
    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    RUTA_SALIDA.write_text(json.dumps(veredicto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return veredicto

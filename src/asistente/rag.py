"""RAG local: TF-IDF de scikit-learn sobre kb/, sin vectores externos. Dueño: Rafael."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from contratos import Decision


class BaseConocimiento:
    """Pasajes por párrafo con identificador kb:archivo#n. 12 documentos propios en kb/ (ninguno copiado)."""

    def __init__(self, carpeta: str = "kb") -> None:
        raise NotImplementedError("asistente.BaseConocimiento: corte A (Rafael)")

    def buscar(self, consulta: str, k: int = 3, minimo: float = 0.15) -> list[dict[str, Any]]:
        """Hasta k pasajes {id, texto, score} con score >= minimo [por fijar]; lista vacía si no hay evidencia."""
        raise NotImplementedError("asistente.BaseConocimiento.buscar (Rafael)")


def kb_dinamica(decision: Decision) -> list[dict[str, Any]]:
    """El desglose de la decisión actual como pasajes citables: decision#1, decision#2..."""
    raise NotImplementedError("asistente.kb_dinamica (Rafael)")


__all__ = ["BaseConocimiento", "kb_dinamica"]
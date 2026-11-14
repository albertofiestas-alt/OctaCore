"""RAG local: TF-IDF de scikit-learn sobre kb/, sin vectores externos. Dueño: Rafael.

Hecho por delegación de Gino (DECISIONES #34). Un pasaje por párrafo; id = kb:<archivo sin .md>#<n> (n desde 1).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from contratos.config import RAIZ

if TYPE_CHECKING:
    from contratos import Decision

# Palabras vacías mínimas (sin tildes): sin ellas "qué es" o "de" harían coincidir cualquier pregunta con cualquier pasaje.
_VACIAS = frozenset(
    "a al algo como con cual cuales cuando cuanto de del donde el ella ellas ellos en es esa ese eso esta este esto "
    "hay la las lo los me mi mis muy no o para pero por porque que quien se si significa sin sobre su sus te tu tus "
    "un una uno unos unas y ya".split()
)


class BaseConocimiento:
    """Pasajes por párrafo con identificador kb:archivo#n. Documentos propios en kb/ (ninguno copiado)."""

    def __init__(self, carpeta: str = "kb") -> None:
        ruta = Path(carpeta)
        if not ruta.is_absolute():
            ruta = RAIZ / ruta
        self._pasajes: list[dict[str, str]] = []
        for archivo in sorted(ruta.glob("*.md")) if ruta.is_dir() else []:
            lineas = archivo.read_text(encoding="utf-8").strip().split("\n\n")
            titulo = lineas[0].lstrip("# ").strip()
            for n, parrafo in enumerate((p.strip() for p in lineas[1:] if p.strip()), start=1):
                self._pasajes.append({"id": f"kb:{archivo.stem}#{n}", "texto": parrafo, "indice": f"{titulo}. {parrafo}"})
        self._vec = TfidfVectorizer(strip_accents="unicode", lowercase=True, stop_words=sorted(_VACIAS), sublinear_tf=True)
        try:
            self._matriz = self._vec.fit_transform(p["indice"] for p in self._pasajes)
        except ValueError:  # carpeta vacía o solo palabras vacías: no hay vocabulario
            self._matriz = None

    def buscar(self, consulta: str, k: int = 3, minimo: float = 0.15) -> list[dict[str, Any]]:
        """Hasta k pasajes {id, texto, score} con score >= minimo; lista vacía si no hay evidencia."""
        if self._matriz is None or not consulta.strip():
            return []
        puntajes = linear_kernel(self._vec.transform([consulta]), self._matriz)[0]
        orden = sorted(range(len(puntajes)), key=lambda i: (-puntajes[i], i))
        return [
            {"id": self._pasajes[i]["id"], "texto": self._pasajes[i]["texto"], "score": float(puntajes[i])}
            for i in orden[:k]
            if puntajes[i] >= minimo
        ]


def _soles(x: float) -> str:
    return f"S/{x:.0f}" if float(x).is_integer() else f"S/{x:.2f}"


def kb_dinamica(decision: Decision) -> list[dict[str, Any]]:
    """El desglose de la decisión actual como pasajes citables: decision#1, decision#2..."""
    d = decision
    textos = [f"Hoy puedes gastar hasta {_soles(d.numero_hoy)} con confianza {d.confianza}."]
    ds = d.desglose
    if "saldo" in ds:
        textos.append(f"El saldo es {_soles(ds['saldo'])} y el colchón es {_soles(ds.get('colchon', 0))}.")
    if ds.get("dia_limitante") is not None:
        textos.append(f"El pago que limita el número de hoy es el del día {ds['dia_limitante']}.")
    textos += [
        f"Pago del día {p.dia} por {_soles(p.monto)}: monto permitido {_soles(p.permitido)}, estado {p.semaforo}."
        for p in d.por_pago
    ]
    return [{"id": f"decision#{i}", "texto": t, "score": 1.0} for i, t in enumerate(textos, start=1)]


__all__ = ["BaseConocimiento", "kb_dinamica"]

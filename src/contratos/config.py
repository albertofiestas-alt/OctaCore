"""Configuración (Anexo B). Todos los parámetros viven en config/config.yaml.

Ningún valor mágico en el código: si un módulo necesita un número, lo lee de aquí.
Los valores en null están [por fijar antes de ver resultados].
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

RAIZ = Path(__file__).resolve().parents[2]
RUTA_CONFIG = RAIZ / "config" / "config.yaml"


class UmbralesConfianza(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    # Ancho relativo a 14 días: (P80 - P5) / max(P50, 1)
    ancho_alta: float = Field(gt=0, description="ancho <= esto -> alta")
    ancho_media: float = Field(gt=0, description="ancho <= esto -> media; si no, baja")


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    horizontes_dias: tuple[int, ...]
    cuantiles: tuple[float, ...]
    cuantil_conservador: float = Field(gt=0, lt=1)
    colchon: float | None = Field(default=None, ge=0)
    umbral_historia_semanas: int = Field(ge=1)
    umbrales_confianza: UmbralesConfianza | None = None
    ventana_regla_robusta_semanas: int = Field(ge=1)
    ventana_dias: int = Field(ge=1)
    semilla_generador: int
    semillas_evaluacion: tuple[int, ...]
    version_generador: str
    version_modelo: str
    ruta_registro: str

    @model_validator(mode="after")
    def _coherencia(self) -> Config:
        if self.horizontes_dias != (3, 7, 14):
            raise ValueError("horizontes_dias es fijo: 3, 7, 14 (Anexo B)")
        if self.cuantiles != (0.05, 0.20, 0.50, 0.80):
            raise ValueError("cuantiles es fijo: 0.05, 0.20, 0.50, 0.80 (Anexo B)")
        if self.cuantil_conservador not in self.cuantiles:
            raise ValueError("cuantil_conservador debe ser uno de los cuantiles")
        if len(self.semillas_evaluacion) < 20:
            raise ValueError("semillas_evaluacion necesita 20 o más semillas")
        return self


def cargar_config(ruta: str | Path = RUTA_CONFIG) -> Config:
    with open(ruta, encoding="utf-8") as f:
        datos = yaml.safe_load(f)
    return Config.model_validate(datos)


def hash_config(cfg: Config) -> str:
    """Hash estable de la configuración (no depende de PYTHONHASHSEED)."""
    canonico = json.dumps(cfg.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()[:16]

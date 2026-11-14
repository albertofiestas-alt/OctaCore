"""Configuración (Anexo B y Anexo E de la v7). Ningún valor mágico en el código.

Archivos:
    config/base.yaml        parámetros comunes del Anexo B (dueño: Anderson). Se valida aquí.
    config/<modulo>.yaml    parámetros de cada dueño (ingesta, motor, modelo, datos,
                            preregistro...). Se cargan tal cual en cfg["<modulo>"].

Uso (las dos formas valen):
    cfg = cargar_config()
    cfg["cuantil_conservador"]          # 0.2   (forma de los planes)
    cfg["ingesta"]["max_mb"]            # lee config/ingesta.yaml
    cfg.cuantil_conservador             # 0.2
    otro = cfg.con(cuantil_conservador=0.05)   # copia con cambios (p. ej. la frontera)

La configuración es de solo lectura: así nadie la cambia a mitad de una corrida.
Los valores en null están [por fijar antes de ver resultados].
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

RAIZ = Path(__file__).resolve().parents[2]
DIR_CONFIG = RAIZ / "config"
RUTA_CONFIG = DIR_CONFIG / "base.yaml"


# --------------------------------------------------------------------------- #
# Validación de config/base.yaml
# --------------------------------------------------------------------------- #


class _Estricto(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class UmbralesConfianza(_Estricto):
    # Ancho relativo a 14 días: (P80 - P5) / max(P50, 1). Nombres del plan del motor.
    ancho_alto: float = Field(gt=0, description="ancho < esto (y historia suficiente) -> alta")
    ancho_bajo: float = Field(gt=0, description="ancho > esto -> baja")


class Generativa(_Estricto):
    activada: bool = False
    proveedor: str = "ninguno"
    timeout_s: float = Field(gt=0)
    reintentos: int = Field(ge=0)
    temperatura: float = Field(ge=0)
    max_tokens: int = Field(gt=0)
    max_palabras: int = Field(gt=0)


class ConfigBase(_Estricto):
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
    variables_sensibles: tuple[str, ...]
    patrones_pii: dict[str, str]
    umbral_alerta_sesgo: float | None = None
    generativa: Generativa
    rutas_datos: tuple[str, ...] = Field(min_length=1)
    ruta_modelo: str
    ruta_adopcion: str
    ruta_registro: str
    ruta_respuestas: str
    ruta_salud: str

    @model_validator(mode="after")
    def _coherencia(self) -> ConfigBase:
        if self.horizontes_dias != (3, 7, 14):
            raise ValueError("horizontes_dias es fijo: 3, 7, 14 (Anexo B)")
        if self.cuantiles != (0.05, 0.20, 0.50, 0.80):
            raise ValueError("cuantiles es fijo: 0.05, 0.20, 0.50, 0.80 (Anexo B)")
        if self.cuantil_conservador not in self.cuantiles:
            raise ValueError("cuantil_conservador debe ser uno de los cuantiles")
        if len(self.semillas_evaluacion) < 20:
            raise ValueError("semillas_evaluacion necesita 20 o más semillas")
        if self.generativa.activada:
            raise ValueError(
                "generativa.activada solo se enciende con las cinco condiciones de la opción B "
                "y una entrada en DECISIONES.md"
            )
        return self


# --------------------------------------------------------------------------- #
# Config: dict de solo lectura con acceso por atributo
# --------------------------------------------------------------------------- #


class Config(dict):
    """Configuración unida. Es un dict (cfg["x"]) con acceso por atributo (cfg.x)."""

    def __getattr__(self, nombre: str) -> Any:
        try:
            return self[nombre]
        except KeyError:
            raise AttributeError(f"la configuración no tiene '{nombre}'") from None

    def _solo_lectura(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("la configuración es de solo lectura; usa cfg.con(clave=valor) para una copia")

    __setitem__ = __delitem__ = __setattr__ = __delattr__ = _solo_lectura  # type: ignore[assignment]
    clear = pop = popitem = setdefault = update = __ior__ = _solo_lectura  # type: ignore[assignment]

    def __reduce__(self) -> tuple[Any, ...]:
        # pickle/joblib/deepcopy (el modelo guarda su cfg con joblib).
        return (Config, (dict(self),))

    def con(self, **cambios: Any) -> Config:
        """Copia con algunos valores cambiados. No vuelve a validar base.yaml."""
        return _congelar({**_descongelar(self), **cambios})


def _congelar(valor: Any) -> Any:
    if isinstance(valor, dict):
        return Config({k: _congelar(v) for k, v in valor.items()})
    if isinstance(valor, (list, tuple)):
        return tuple(_congelar(v) for v in valor)
    return valor


def _descongelar(valor: Any) -> Any:
    if isinstance(valor, dict):
        return {k: _descongelar(v) for k, v in valor.items()}
    if isinstance(valor, tuple):
        return [_descongelar(v) for v in valor]
    return valor


def _leer_yaml(ruta: Path) -> Any:
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)


def cargar_config(ruta: str | Path = RUTA_CONFIG) -> Config:
    """Valida `ruta` (base.yaml) y le agrega cada otro *.yaml de su carpeta como cfg[<nombre>]."""
    ruta = Path(ruta)
    datos = _leer_yaml(ruta) or {}
    base = ConfigBase.model_validate(datos)
    unida: dict[str, Any] = base.model_dump(mode="json")

    for archivo in sorted(ruta.parent.glob("*.yaml")):
        if archivo.resolve() == ruta.resolve():
            continue
        nombre = archivo.stem
        if nombre in unida:
            raise ValueError(
                f"config/{archivo.name} choca con el parámetro '{nombre}' de {ruta.name}; renómbralo"
            )
        contenido = _leer_yaml(archivo)
        if contenido is None:
            contenido = {}
        if not isinstance(contenido, dict):
            raise ValueError(f"config/{archivo.name} debe ser un diccionario clave: valor")
        unida[nombre] = contenido
    return _congelar(unida)


def hash_config(cfg: dict[str, Any]) -> str:
    """Hash estable de la configuración (no depende de PYTHONHASHSEED ni del orden)."""
    canonico = json.dumps(cfg, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()[:16]


__all__ = ["Config", "ConfigBase", "cargar_config", "hash_config"]

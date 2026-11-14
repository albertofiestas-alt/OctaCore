"""Lectura segura del CSV de entrada (paso 1 de `cargar`).

Garantías:
- Tamaño acotado: se comprueba antes de leer y, en flujos, se lee a lo sumo `max_mb` + 1 byte.
- Solo UTF-8 estricto (acepta BOM); bytes nulos o texto no decodificable se rechazan.
- Todo se lee como texto (`dtype=str`): ninguna celda se interpreta ni se ejecuta.
- Límites de filas y columnas; encabezados vacíos o repetidos se rechazan.
- Nunca se modifica la entrada y ningún error contiene el valor de una celda: los
  mensajes y detalles solo nombran columnas, filas o posiciones. No se reenvía `str(exc)`
  de pandas/codecs porque pueden incluir fragmentos del contenido.
"""

from __future__ import annotations

import io
import os
import stat
from pathlib import Path
from typing import Any, BinaryIO

import pandas as pd

from .errores import ErrorIngesta

_MB = 1024 * 1024
_PORDEFECTO = {"max_mb": 50, "max_filas": 1_000_000, "max_columnas": 100}
_BLOQUE = 1 << 20


def _param(cfg: Any, nombre: str) -> int | float:
    try:
        valor = cfg["ingesta"].get(nombre)
    except (KeyError, TypeError, AttributeError):
        valor = None
    if valor is None:
        valor = _PORDEFECTO[nombre]
    return valor


def _demasiado_grande(max_mb: float) -> ErrorIngesta:
    return ErrorIngesta(
        f"El archivo pesa más de {max_mb:g} MB. Divídelo en partes más pequeñas e inténtalo de nuevo.",
        f"tamaño máximo permitido: {max_mb:g} MB",
    )


def _bytes_de_ruta(ruta: Path, limite: int, max_mb: float) -> bytes:
    try:
        # O_NOFOLLOW evita seguir un enlace simbólico final; O_NONBLOCK evita colgarse en una FIFO.
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        fd = os.open(ruta, flags)
    except FileNotFoundError:
        raise ErrorIngesta("No se encontró el archivo. Revisa la ruta y vuelve a subirlo.", "archivo inexistente") from None
    except OSError:
        raise ErrorIngesta("No se pudo abrir el archivo. Revisa que exista, no sea un acceso directo y tengas permiso.", "error al abrir") from None
    with os.fdopen(fd, "rb") as f:
        modo = os.fstat(f.fileno()).st_mode
        if not stat.S_ISREG(modo):
            raise ErrorIngesta("La ruta no es un archivo CSV.", "no es un archivo regular")
        if os.fstat(f.fileno()).st_size > limite:
            raise _demasiado_grande(max_mb)
        return _leer_acotado(f, limite, max_mb)


def _leer_acotado(flujo: BinaryIO, limite: int, max_mb: float) -> bytes:
    partes: list[bytes] = []
    total = 0
    try:
        while True:
            trozo = flujo.read(_BLOQUE)
            if not trozo:
                break
            if isinstance(trozo, str):
                raise ErrorIngesta("El archivo debe abrirse en modo binario.", "flujo de texto")
            total += len(trozo)
            if total > limite:
                raise _demasiado_grande(max_mb)
            partes.append(trozo)
    except ErrorIngesta:
        raise
    except Exception:
        raise ErrorIngesta("No se pudo leer el archivo. Vuelve a subirlo.", "error de lectura") from None
    return b"".join(partes)


def _decodificar(datos: bytes) -> str:
    pos_nulo = datos.find(b"\x00")
    if pos_nulo >= 0:
        raise ErrorIngesta(
            "El archivo no parece un CSV de texto. Expórtalo de nuevo como CSV UTF-8.",
            f"byte nulo en la posición {pos_nulo}",
        )
    try:
        return datos.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ErrorIngesta(
            "El archivo no está en UTF-8. Guárdalo como «CSV UTF-8» e inténtalo de nuevo.",
            f"byte no UTF-8 en la posición {exc.start}",
        ) from None


def _validar_forma(df: pd.DataFrame, cfg: Any) -> pd.DataFrame:
    max_cols, max_filas = int(_param(cfg, "max_columnas")), int(_param(cfg, "max_filas"))
    if df.shape[1] == 0 or df.shape[0] == 0:
        raise ErrorIngesta("El archivo está vacío o no tiene filas de datos.", "sin columnas o sin filas")
    if df.shape[1] > max_cols:
        raise ErrorIngesta(
            f"El archivo tiene demasiadas columnas (máximo {max_cols}).", f"{df.shape[1]} columnas"
        )
    if df.shape[0] > max_filas:
        raise ErrorIngesta(
            f"El archivo tiene demasiadas filas (máximo {max_filas}). Divídelo en partes.", f"{df.shape[0]} filas"
        )
    return df


def _normalizar_encabezados(df: pd.DataFrame) -> pd.DataFrame:
    nombres = [str(c).strip() for c in df.columns]
    vacias = [i + 1 for i, n in enumerate(nombres) if not n or n.startswith("Unnamed:")]
    if vacias:
        raise ErrorIngesta(
            "Hay columnas sin nombre en el encabezado. Ponles nombre o elimínalas.",
            f"columnas sin nombre en las posiciones {vacias}",
        )
    vistos: set[str] = set()
    repetidas: list[str] = []
    for n in nombres:
        if n.lower() in vistos and n not in repetidas:
            repetidas.append(n)
        vistos.add(n.lower())
    if repetidas:
        raise ErrorIngesta(
            f"Hay columnas repetidas: {', '.join(repetidas)}. Deja una sola de cada una.",
            f"columnas repetidas: {repetidas}",
        )
    df = df.copy()
    df.columns = nombres
    return df


def _parsear(texto: str) -> pd.DataFrame:
    if not texto.strip():
        raise ErrorIngesta("El archivo está vacío.", "sin contenido")
    try:
        return pd.read_csv(
            io.StringIO(texto),
            dtype=str,
            keep_default_na=False,
            na_values=[""],
            skip_blank_lines=True,
            on_bad_lines="error",
            engine="c",
        )
    except pd.errors.EmptyDataError:
        raise ErrorIngesta("El archivo está vacío.", "sin contenido") from None
    except pd.errors.ParserError as exc:
        # El texto de pandas puede traer fragmentos de la fila: solo se extrae el número de línea.
        import re

        m = re.search(r"line (\d+)", str(exc))
        donde = f"fila {m.group(1)}" if m else "una fila"
        raise ErrorIngesta(
            "El archivo no tiene formato CSV válido: hay filas con distinto número de columnas.",
            f"formato inválido en {donde}",
        ) from None
    except (ValueError, MemoryError):
        raise ErrorIngesta("No se pudo leer el archivo como CSV.", "error de lectura") from None


def leer(origen: str | Path | BinaryIO | pd.DataFrame, cfg: Any) -> pd.DataFrame:
    """Lee `origen` (ruta, flujo binario o DataFrame) y devuelve un DataFrame nuevo de texto.

    Lanza `ErrorIngesta` (nunca otra excepción) si el archivo está vacío, es ilegible,
    pesa más de `cfg["ingesta"]["max_mb"]` o su forma no es válida.
    """
    max_mb = float(_param(cfg, "max_mb"))
    limite = int(max_mb * _MB)
    try:
        if isinstance(origen, pd.DataFrame):
            df = origen.copy(deep=True)
            if int(df.memory_usage(deep=True).sum()) > limite:
                raise _demasiado_grande(max_mb)
        else:
            if isinstance(origen, (str, os.PathLike)):
                datos = _bytes_de_ruta(Path(origen), limite, max_mb)
            elif hasattr(origen, "read"):
                datos = _leer_acotado(origen, limite, max_mb)
            else:
                raise ErrorIngesta("Origen no soportado: sube un archivo CSV.", "tipo de origen no soportado")
            df = _parsear(_decodificar(datos))
        return _normalizar_encabezados(_validar_forma(df, cfg))
    except ErrorIngesta:
        raise
    except Exception:
        raise ErrorIngesta("No se pudo leer el archivo. Revisa que sea un CSV UTF-8 válido.", "error inesperado de lectura") from None

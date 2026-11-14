"""Pruebas de mutación del motor (plan de Sebastián, secciones 9 a 11). Dueño: Sebastián.

Uso (desde la raíz del repo):

    .venv/Scripts/python.exe tests/unit/motor/mutaciones.py              # todas
    .venv/Scripts/python.exe tests/unit/motor/mutaciones.py M03 M12      # solo esas
    .venv/Scripts/python.exe tests/unit/motor/mutaciones.py --lista      # ver el catálogo
    .venv/Scripts/python.exe tests/unit/motor/mutaciones.py --workers 4 --timeout 900

Una mutación es un error pequeño metido a propósito en el motor. Para cada una:
1. se copia lo necesario del repo (src/, config/, pyproject.toml y las pruebas del motor) a un
   directorio TEMPORAL; los archivos reales de src/motor NUNCA se tocan;
2. se aplica UNA sustitución de texto exacta en la copia (falla si el texto original no aparece
   exactamente una vez);
3. se corre `python -m pytest tests/unit/motor tests/property -x -q -p no:cacheprovider` en la copia;
4. si alguna prueba falla la mutación queda DETECTADA; si todas pasan, SOBREVIVE (hueco en las
   pruebas o mutación equivalente); un timeout o un error de pytest (colección, uso) es ERROR.

Antes de mutar se corre la copia SIN mutación: si ya falla, el resultado no valdría nada y se aborta.
Sale con código 0 si se detectan al menos 6 mutaciones (criterio del plan: 6 de 8).
Este archivo no empieza con test_, así pytest no lo recoge.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
MINIMO_DETECTADAS = 6
COMANDO_PYTEST = ["-m", "pytest", "tests/unit/motor", "tests/property", "-x", "-q", "-p", "no:cacheprovider"]

# Lo que se copia al directorio temporal (relativo a la raíz).
COPIAR_DIRS = ("src", "config", "tests/fixtures", "tests/unit/motor", "tests/property")
COPIAR_ARCHIVOS = ("pyproject.toml", "tests/conftest.py")
IGNORAR = shutil.ignore_patterns("__pycache__", ".hypothesis", ".pytest_cache", "*.pyc")


@dataclass(frozen=True)
class Mutacion:
    id: str
    categoria: str
    archivo: str
    descripcion: str
    original: str
    mutado: str
    equivalente: bool = False  # True si no cambia el comportamiento observable (se espera que sobreviva)


DECIDIR = "src/motor/decidir.py"
SIMULAR = "src/motor/simular.py"

MUTACIONES: tuple[Mutacion, ...] = (
    # --- Fórmula ---------------------------------------------------------------------------------
    Mutacion(
        "M01", "fórmula", DECIDIR,
        "pagos acumulados: `p.dia <= d` -> `p.dia < d` (el pago del mismo día no cuenta)",
        "return float(sum(p.monto for p in estado.pagos if p.dia <= d))",
        "return float(sum(p.monto for p in estado.pagos if p.dia < d))",
    ),
    Mutacion(
        "M02", "fórmula", DECIDIR,
        "se olvida el colchón en el numerador",
        "colchon = estado.colchon if con_colchon else 0.0",
        "colchon = 0.0",
    ),
    Mutacion(
        "M03", "fórmula", DECIDIR,
        "divisor del permitido `max(d, 1)` -> `max(d, 2)`",
        "ingresos_extra=ingresos_extra) / max(d, 1)\n",
        "ingresos_extra=ingresos_extra) / max(d, 2)\n",
    ),
    Mutacion(
        "M04", "fórmula", DECIDIR,
        "puntos de control sin el día 14",
        "return sorted({p.dia for p in estado.pagos} | {HORIZONTE_MAXIMO})",
        "return sorted({p.dia for p in estado.pagos})",
    ),
    Mutacion(
        "M05", "fórmula", DECIDIR,
        "punto que limita: `min(...)` -> `max(...)`",
        "d_lim = min(perm, key=lambda d: (perm[d], d))",
        "d_lim = max(perm, key=lambda d: (perm[d], d))",
    ),
    Mutacion(
        "M06", "fórmula", DECIDIR,
        "horizonte: `h <= min(d, 14)` -> `h < min(d, 14)` en _h_para_dia",
        "candidatos = [h for h in horizontes if h <= min(d, HORIZONTE_MAXIMO)]",
        "candidatos = [h for h in horizontes if h < min(d, HORIZONTE_MAXIMO)]",
    ),
    Mutacion(
        "M07", "fórmula", DECIDIR,
        "empate entre días: elige el día MAYOR en vez del menor",
        "d_lim = min(perm, key=lambda d: (perm[d], d))",
        "d_lim = min(perm, key=lambda d: (perm[d], -d))",
    ),
    # --- Redondeo --------------------------------------------------------------------------------
    Mutacion(
        "M08", "redondeo", DECIDIR,
        "número de hoy: floor -> ceil (redondea a favor del gasto)",
        "numero = int(math.floor(max(0.0, minimo)))",
        "numero = int(math.ceil(max(0.0, minimo)))",
    ),
    Mutacion(
        "M09", "redondeo", DECIDIR,
        "número de hoy: floor -> round",
        "numero = int(math.floor(max(0.0, minimo)))",
        "numero = int(round(max(0.0, minimo)))",
    ),
    Mutacion(
        "M10", "redondeo", DECIDIR,
        "faltante: ceil -> floor (dice que falta menos de lo que falta)",
        "faltante = int(math.ceil(-numerador(",
        "faltante = int(math.floor(-numerador(",
    ),
    Mutacion(
        "M11", "redondeo", DECIDIR,
        "faltante solo si el mínimo es `<= 0` en vez de `< 0` (\"faltan S/0\" con el pago justo cubierto)",
        "    if minimo < 0:\n        faltante",
        "    if minimo <= 0:\n        faltante",
    ),
    Mutacion(
        "M12", "redondeo", DECIDIR,
        "refactor: `floor(max(0, m))` -> `max(0, floor(m))` (mismo resultado para todo m)",
        "numero = int(math.floor(max(0.0, minimo)))",
        "numero = max(0, int(math.floor(minimo)))",
        equivalente=True,
    ),
    # --- Semáforo --------------------------------------------------------------------------------
    Mutacion(
        "M13", "semáforo", DECIDIR,
        "verde con P20 en vez de P5",
        "if cobertura(P5) >= 0:",
        "if cobertura(0.2) >= 0:",
    ),
    Mutacion(
        "M14", "semáforo", DECIDIR,
        "verde: `>= 0` -> `> 0` (el pago justo cubierto deja de ser verde)",
        "if cobertura(P5) >= 0:",
        "if cobertura(P5) > 0:",
    ),
    Mutacion(
        "M15", "semáforo", DECIDIR,
        "ámbar: `>= 0` -> `> 0` (cubierto justo en P50 pasa a rojo)",
        "if cobertura(P50) >= 0:",
        "if cobertura(P50) > 0:",
    ),
    Mutacion(
        "M16", "semáforo", DECIDIR,
        "el semáforo descuenta el colchón",
        "n = numerador(estado, pronostico, d, q, cfg, con_colchon=False, ingresos_extra=ingresos_extra)",
        "n = numerador(estado, pronostico, d, q, cfg, con_colchon=True, ingresos_extra=ingresos_extra)",
    ),
    # --- Confianza -------------------------------------------------------------------------------
    Mutacion(
        "M17", "confianza", DECIDIR,
        "baja: `ancho > ancho_bajo` -> `>=` (frontera 1.2)",
        'ancho > umbrales["ancho_bajo"]',
        'ancho >= umbrales["ancho_bajo"]',
    ),
    Mutacion(
        "M18", "confianza", DECIDIR,
        "alta: `ancho < ancho_alto` -> `<=` (frontera 0.5)",
        'if ancho < umbrales["ancho_alto"]:',
        'if ancho <= umbrales["ancho_alto"]:',
    ),
    Mutacion(
        "M19", "confianza", DECIDIR,
        "historia suficiente: `>= umbral` -> `> umbral` (4 semanas exactas pasa a poca historia)",
        'return estado.semanas_historia >= cfg["umbral_historia_semanas"]',
        'return estado.semanas_historia > cfg["umbral_historia_semanas"]',
    ),
    # --- Propuesta -------------------------------------------------------------------------------
    Mutacion(
        "M20", "propuesta", DECIDIR,
        "propone aunque no haya historia suficiente",
        "    if not _historia_suficiente(estado, cfg):\n        return []\n",
        "",
    ),
    Mutacion(
        "M21", "propuesta", DECIDIR,
        "la propuesta usa el cuantil conservador (P20) en vez del de propuesta (P5)",
        'q5 = cfg["motor"]["cuantil_propuesta"]',
        'q5 = cfg["cuantil_conservador"]',
    ),
    Mutacion(
        "M22", "propuesta", DECIDIR,
        "g5: floor -> round (la propuesta deja de cubrir en P5)",
        "g5_entero = int(math.floor(g5))",
        "g5_entero = int(round(g5))",
    ),
    Mutacion(
        "M23", "propuesta", DECIDIR,
        "condición `g5 < numero_hoy` -> `<=` (propone apartar S/0)",
        "if not (0 <= g5 < g20):",
        "if not (0 <= g5 <= g20):",
    ),
    # --- Simulación ------------------------------------------------------------------------------
    Mutacion(
        "M24", "simulación", DECIDIR,
        "ingresos extra sumados en todos los días sin mirar su día",
        "return float(sum(m for (dia0, m) in ingresos_extra if dia0 <= d))",
        "return float(sum(m for (dia0, m) in ingresos_extra))",
    ),
    Mutacion(
        "M25", "simulación", SIMULAR,
        "gasto_hoy se suma al saldo en vez de restarse",
        'estado.model_copy(update={"saldo": estado.saldo - escenario.gasto_hoy})',
        'estado.model_copy(update={"saldo": estado.saldo + escenario.gasto_hoy})',
    ),
    Mutacion(
        "M26", "simulación", SIMULAR,
        "un escenario con solo gasto_hoy se trata como vacío (`and` -> `or`)",
        "if not escenario.ingresos_extra and not escenario.gasto_hoy:",
        "if not escenario.ingresos_extra or not escenario.gasto_hoy:",
    ),
)


@dataclass
class Resultado:
    mutacion: Mutacion
    estado: str  # detectada / sobrevive / error
    detalle: str
    segundos: float


# --------------------------------------------------------------------------- #
# Copia, mutación y corrida
# --------------------------------------------------------------------------- #


def _copiar_repo(destino: Path) -> None:
    for d in COPIAR_DIRS:
        shutil.copytree(RAIZ / d, destino / d, ignore=IGNORAR)
    for a in COPIAR_ARCHIVOS:
        (destino / a).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(RAIZ / a, destino / a)


def aplicar(copia: Path, m: Mutacion) -> None:
    """Sustituye m.original por m.mutado en la copia. ValueError si no aparece exactamente una vez."""
    ruta = copia / m.archivo
    texto = ruta.read_text(encoding="utf-8")
    veces = texto.count(m.original)
    if veces != 1:
        raise ValueError(f"{m.id}: el texto original aparece {veces} veces en {m.archivo} (debe ser 1): {m.original!r}")
    ruta.write_text(texto.replace(m.original, m.mutado, 1), encoding="utf-8", newline="")


def _entorno(copia: Path) -> dict[str, str]:
    env = dict(os.environ)
    # La copia primero: el venv tiene un .pth editable que apunta al src real.
    env["PYTHONPATH"] = str(copia / "src")
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("COVERAGE_PROCESS_START", None)
    return env


def _verificar_import(copia: Path) -> None:
    """Asegura que `import motor` resuelve a la copia y no al src real."""
    salida = subprocess.run(
        [sys.executable, "-c", "import motor; print(motor.__file__)"],
        cwd=copia, env=_entorno(copia), capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    ruta = Path(salida.stdout.strip()).resolve()
    if copia.resolve() not in ruta.parents:
        raise RuntimeError(f"motor se importa desde {ruta}, no desde la copia {copia}")


_FALLO = re.compile(r"^(?:FAILED|ERROR) (\S+?)(?: - (.*))?$", re.MULTILINE)


def _primer_fallo(salida: str) -> str:
    m = _FALLO.search(salida)
    if not m:
        return "(sin resumen de pytest)"
    prueba = m.group(1).replace("\\", "/")
    motivo = (m.group(2) or "").strip()
    return f"{prueba} ({motivo[:90]})" if motivo else prueba


def correr(m: Mutacion | None, timeout: int) -> Resultado:
    """Corre una mutación (o la línea base si m es None) en un directorio temporal propio."""
    inicio = time.perf_counter()
    base = Mutacion("BASE", "-", "-", "sin mutación", "", "") if m is None else m
    with tempfile.TemporaryDirectory(prefix=f"mut_{base.id}_") as tmp:
        copia = Path(tmp)
        try:
            _copiar_repo(copia)
            if m is not None:
                aplicar(copia, m)
            _verificar_import(copia)
        except Exception as exc:  # noqa: BLE001 - se reporta como error de la mutación
            return Resultado(base, "error", f"preparación: {exc}", time.perf_counter() - inicio)
        try:
            proc = subprocess.run(
                [sys.executable, *COMANDO_PYTEST],
                cwd=copia, env=_entorno(copia), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return Resultado(base, "error", f"timeout de {timeout} s", time.perf_counter() - inicio)
    seg = time.perf_counter() - inicio
    salida = proc.stdout + proc.stderr
    if proc.returncode == 0:
        return Resultado(base, "sobrevive", "todas las pruebas pasan", seg)
    if proc.returncode == 1:
        return Resultado(base, "detectada", _primer_fallo(salida), seg)
    cola = " | ".join(salida.strip().splitlines()[-3:])
    return Resultado(base, "error", f"pytest salió con {proc.returncode}: {cola[:200]}", seg)


# --------------------------------------------------------------------------- #
# Reporte
# --------------------------------------------------------------------------- #


def _celda(x: str) -> str:
    return x.replace("|", "\\|").replace("\n", " ")


def tabla(resultados: list[Resultado]) -> str:
    filas = [
        "| Id | Categoría | Archivo | Mutación | Resultado | Detectada por / detalle | s |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in resultados:
        m = r.mutacion
        estado = r.estado + (" (equivalente)" if m.equivalente else "")
        filas.append(
            f"| {m.id} | {m.categoria} | {Path(m.archivo).name} | {_celda(m.descripcion)} | {estado} "
            f"| {_celda(r.detalle)} | {r.segundos:.0f} |"
        )
    return "\n".join(filas)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pruebas de mutación del motor")
    p.add_argument("ids", nargs="*", help="ids de mutación a correr (por defecto todas)")
    p.add_argument("--workers", type=int, default=max(1, min(6, (os.cpu_count() or 2) // 2)))
    p.add_argument("--timeout", type=int, default=900, help="segundos por corrida de pytest")
    p.add_argument("--lista", action="store_true", help="solo lista el catálogo")
    p.add_argument("--sin-base", action="store_true", help="omite la corrida sin mutación")
    args = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # la consola de Windows usa cp1252 por defecto

    elegidas = [m for m in MUTACIONES if not args.ids or m.id in args.ids]
    if args.ids and len(elegidas) != len(set(args.ids)):
        print(f"ids desconocidos: {sorted(set(args.ids) - {m.id for m in MUTACIONES})}", file=sys.stderr)
        return 2
    if args.lista:
        for m in elegidas:
            print(f"{m.id} [{m.categoria}] {m.archivo}: {m.descripcion}" + (" (equivalente)" if m.equivalente else ""))
        return 0

    inicio = time.perf_counter()
    if not args.sin_base:
        print("Línea base (sin mutación)...", flush=True)
        base = correr(None, args.timeout)
        if base.estado != "sobrevive":
            print(f"La copia SIN mutación no pasa ({base.estado}: {base.detalle}). Abortado.", file=sys.stderr)
            return 2
        print(f"  verde en {base.segundos:.0f} s", flush=True)

    print(f"Corriendo {len(elegidas)} mutaciones con {args.workers} procesos en paralelo...", flush=True)

    def _una(m: Mutacion) -> Resultado:
        r = correr(m, args.timeout)
        print(f"  {m.id}: {r.estado} ({r.segundos:.0f} s)", flush=True)
        return r

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        resultados = list(ex.map(_una, elegidas))

    total = time.perf_counter() - inicio
    detectadas = sum(r.estado == "detectada" for r in resultados)
    no_equiv = [r for r in resultados if not r.mutacion.equivalente]
    detectadas_ne = sum(r.estado == "detectada" for r in no_equiv)
    sobreviven = [r.mutacion.id for r in no_equiv if r.estado == "sobrevive"]
    errores = [r.mutacion.id for r in resultados if r.estado == "error"]

    print()
    print(tabla(resultados))
    print()
    print(f"**{detectadas} de {len(resultados)} detectadas** "
          f"({detectadas_ne} de {len(no_equiv)} no equivalentes; "
          f"{len(resultados) - len(no_equiv)} equivalentes documentadas).")
    if sobreviven:
        print(f"Sobreviven (no equivalentes): {', '.join(sobreviven)}")
    if errores:
        print(f"Con error: {', '.join(errores)}")
    print(f"Tiempo total: {total:.0f} s")
    return 0 if detectadas >= MINIMO_DETECTADAS else 1


if __name__ == "__main__":
    sys.exit(main())

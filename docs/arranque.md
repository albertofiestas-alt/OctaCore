# Arranque (sábado 10:15 a 11:00)

Meta de las 11:00: `python tareas.py test` en verde en las 7 laptops y contratos fusionados en `main`.

## 1. Entorno (todos)

```bash
git clone <url-del-repo> octocore && cd octocore
py -3.11 tareas.py setup          # macOS/Linux: python3.11 tareas.py setup
python tareas.py test             # debe terminar en "passed" sin "failed"
```

Si `test_version_de_python` falla, instala Python 3.11. No cambies la versión exigida.

## 2. Rama (todos)

```bash
git switch -c feat/<persona>-<tema>
```

Reglas: `main` siempre ejecutable; se entra por pull request revisado por alguien de otro módulo y solo con `python tareas.py test` en verde. Commits pequeños con prefijo `feat`, `fix`, `test`, `docs`, `data` o `eval`. Nadie edita la carpeta de otra persona sin avisarle.

## 3. Contratos (leer antes de escribir código)

- Modelos: [src/contratos/modelos.py](../src/contratos/modelos.py). Firmas: [src/contratos/firmas.py](../src/contratos/firmas.py).
- Fixtures listas para usar en pruebas, por nombre: `estado_orden_pagos`, `pronostico_orden_pagos`, `decision_orden_pagos`, `estado_tipico`, `pronostico_tipico`, `decision_tipica`, `decision_sin_historia`, `reporte_calidad`, `registro`, `ruta_movimientos_minimo`, `historia_minima`, `cfg`. Ver [tests/conftest.py](../tests/conftest.py).
- En cuanto tu módulo expone su función, `tests/contract/test_firmas.py` exige la firma del Anexo A.
- Cambiar un contrato: pull request aprobado por Anderson y Gino + entrada en DECISIONES.md.

## 4. Esqueleto con una prueba que pasa (cada uno en su rama)

Patrón: la función con su firma exacta y una prueba de la meta marcada `xfail(strict=True)`. Pasa hoy; cuando la implementes, la prueba empieza a pasar de verdad, `strict` la marca como fallo y quitas la marca.

| Persona | Rama | Archivo | Primera prueba |
|---|---|---|---|
| Mathias | `feat/mathias-ingesta` | `src/ingesta/__init__.py` → `def cargar(origen)` | `tests/unit/test_ingesta.py` |
| Sebastián | `feat/sebastian-motor` | `src/motor/__init__.py` → `def decidir(estado, pronostico, cfg)` | `tests/unit/test_motor.py` |
| Rafael | `feat/rafael-muestra` | `data/muestra/movimientos.csv` (20 personas, 24 meses) | ya existe: `tests/contract/test_muestra.py` |
| Rafael | `feat/rafael-reglas` | `src/reglas/__init__.py` → `def regla1(historia, fecha)`, `def regla2(historia, fecha)` | `tests/unit/test_reglas.py` |
| Gino | `feat/gino-modelo` | `src/modelo/__init__.py` → `def predecir(historia, fecha)` | `tests/unit/test_modelo.py` |
| Jesús | `feat/jesus-pantallas` | `src/app/main.py` (Hoy) y `src/app/pages/3_Plan.py` | `tests/e2e/test_app.py` |
| Alberto | `feat/alberto-porque` | `src/app/pages/2_Por_que.py`, `4_Carga.py`, `5_Evaluacion.py` | `tests/e2e/test_por_que.py` |
| Anderson | `feat/anderson-servicio` | `src/servicio/` | `tests/unit/test_servicio.py` |

### Mathias

```python
# src/ingesta/__init__.py
def cargar(origen):
    raise NotImplementedError("ingesta v0: 12:00")

# tests/unit/test_ingesta.py
import pytest
from ingesta import cargar

@pytest.mark.xfail(strict=True, reason="ingesta v0 a las 12:00")
def test_elimina_duplicado_exacto(ruta_movimientos_minimo):
    limpios, reporte, pagos = cargar(ruta_movimientos_minimo)
    assert reporte.duplicados_eliminados == 1
    assert reporte.filas_salida == 13
```

### Sebastián

```python
# src/motor/__init__.py
def decidir(estado, pronostico, cfg):
    raise NotImplementedError("motor: 12:30")

# tests/unit/test_motor.py
import pytest
from motor import decidir

@pytest.mark.xfail(strict=True, reason="caso del orden de pagos a las 12:30")
def test_orden_de_pagos(estado_orden_pagos, pronostico_orden_pagos, cfg):
    d = decidir(estado_orden_pagos, pronostico_orden_pagos, cfg)
    assert d.numero_hoy == 0
    assert any("faltan S/200" in l for l in d.limites)
```

### Rafael (reglas) y Gino (modelo)

```python
# tests/unit/test_reglas.py   (Gino: igual con `from modelo import predecir`)
import pytest
from datetime import date
from contratos import Pronostico
from reglas import regla2

@pytest.mark.xfail(strict=True, reason="regla 2 a las 12:30")
def test_regla2_devuelve_pronostico(historia_minima):
    p = regla2(historia_minima, date(2025, 10, 31))
    assert isinstance(p, Pronostico)
```

### Jesús y Alberto

La app solo importa `servicio` y `contratos`. Hasta las 13:00 usen las fixtures como Decisiones falsas:

```python
# src/app/main.py
import json
from pathlib import Path
import streamlit as st
from contratos import Decision

AVISO = "Orientación educativa basada en una simulación con datos ficticios. No es asesoría financiera ni ejecuta operaciones."
RAIZ = Path(__file__).resolve().parents[2]
d = Decision.model_validate_json((RAIZ / "tests/fixtures/contratos/decision_tipica.json").read_text(encoding="utf-8"))

st.title("Hoy")
st.metric("Hoy puedes gastar hasta", f"S/{d.numero_hoy:,.0f}")
st.caption(AVISO)

# tests/e2e/test_app.py
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[2] / "src/app/main.py"

def test_pantalla_hoy_abre_y_muestra_numero():
    at = AppTest.from_file(str(APP)).run()
    assert not at.exception
    assert at.metric[0].value.startswith("S/")
```

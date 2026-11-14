# Arranque (sábado 10:15 a 11:00)

Meta de V0 (11:00): `python tareas.py test` en verde en las 7 laptops y contratos fusionados en `main`.
Antes de esto, lee la sección **Lectura de asignaciones** del [README](../README.md): ahí está tu plan, tus carpetas y tu revisor.

## 1. Entorno (todos)

```bash
git clone https://github.com/Hackathon-BBVA-Grupo-8/OctaCore.git && cd OctaCore
py -3.11 tareas.py setup          # macOS/Linux: python3.11 tareas.py setup
python tareas.py test             # debe terminar en "passed" sin "failed"
```

Si `test_version_de_python` falla, instala Python 3.11. No cambies la versión exigida.
Si renombras o mueves la carpeta del repositorio, borra `.venv` y vuelve a correr `setup`: el entorno guarda la ruta absoluta.

## 2. Rama (todos)

```bash
git switch main && git pull origin main
git switch -c feat/<persona>-<tema>
```

Reglas: `main` siempre ejecutable; se entra por pull request revisado por tu revisor cruzado y solo con `python tareas.py test` en verde. Commits pequeños con prefijo `feat`, `fix`, `test`, `docs`, `data` o `eval`. `git add <tu carpeta>`, nunca `git add .` ni `git add -A`. Nadie edita la carpeta de otra persona sin avisarle.

## 3. Contratos, firmas y configuración (leer antes de escribir código)

- **Modelos**: [src/contratos/modelos.py](../src/contratos/modelos.py) (Anexo A de la v7 y Anexo 4 de tu plan). `PagoDecision` y `DecisionPago` son la misma clase.
- **Firmas**: [src/contratos/firmas.py](../src/contratos/firmas.py). **Tu paquete ya tiene sus funciones con la firma exacta y `raise NotImplementedError`**: reemplaza el cuerpo, nunca el nombre ni los parámetros. `tests/contract/test_firmas.py` falla si cambias una firma.
  - `ingesta.cargar(origen, cfg)`, `proximos_pagos(pagos_inferidos, customer_id, fecha_corte, ventana=14)`, `semanas_historia(movimientos, customer_id, fecha_corte)`, `cargar_etiquetas(origen)`, `detectar_pii(texto, cfg)`, `enmascarar_pii(df, cfg)`, `ErrorIngesta`
  - `reglas.regla1(historia, fecha, cfg)`, `reglas.regla2(historia, fecha, cfg)`
  - `modelo.construir_features(historia, fecha, cfg)`, `entrenar(movimientos_train, cfg, semilla)`, `Modelo.predecir(historia, fecha)`, `Modelo.guardar(ruta)`, `Modelo.cargar(ruta)` (classmethod), `HistoriaInsuficiente`, `FEATURES`
  - `motor.decidir(estado, pronostico, cfg)`
  - `datos.generar(n_personas, meses, semilla, perturbado, parametros)`, `datos.particion(df, semilla)`
  - `servicio.cargar_archivo(origen)`, `consultar(customer_id, fecha, metodo="modelo")`, `responder(propuesta_id, accion)`, `salud()`, `auditar(registro_id)`
- **Configuración**: `cfg = contratos.cargar_config()`. Se lee como en los planes: `cfg["cuantil_conservador"]`. Es de solo lectura; para una variante usa `cfg.con(cuantil_conservador=0.05)`.
  - `config/base.yaml`: parámetros comunes del Anexo B (dueño: Anderson).
  - `config/<modulo>.yaml`: los tuyos. Se leen como `cfg["<modulo>"]`: `config/ingesta.yaml` → `cfg["ingesta"]["max_mb"]`, `config/motor.yaml` → `cfg["motor"]["ancho_alto"]`, `config/preregistro.yaml` → `cfg["preregistro"]`. Créalo tú en tu rama; nadie edita el de otro.
- **Cambiar un contrato o una firma**: pull request aprobado por Anderson y Gino + entrada en [DECISIONES.md](../DECISIONES.md).

## 4. Fixtures para probar sin esperar a nadie

Archivos en `tests/fixtures/` (se leen directo o se piden por nombre en una prueba; ver [tests/conftest.py](../tests/conftest.py)):

| Archivo / fixture | Qué es |
|---|---|
| `estado_caso_orden_pagos.json`, `pronostico_caso_orden_pagos.json` | Caso del orden de pagos: saldo 100, pago de 300 el día 3. El motor debe dar `numero_hoy == 0` y `mensaje_falta` con "faltan S/200" |
| `decision_sin_alcance.json` | La Decision esperada para ese caso |
| `estado_tipico.json`, `pronostico_tipico.json` | Caso típico (P0002) |
| `decision_verde.json` | Número 20, pagos en verde y una propuesta (para Hoy y Plan) |
| `decision_rojo.json` | Un pago en rojo, número 0 |
| `decision_confianza_baja.json` | 2 semanas de historia, confianza baja, sin propuestas, `respaldo: true` |
| `reporte_calidad_ejemplo.json` | ReporteCalidad con PII enmascarada y una columna sensible descartada |
| `registro.json` | Una línea del registro de recomendaciones |
| `movimientos_minimo.csv` (`ruta_movimientos_minimo`, `historia_minima`) | 14 movimientos crudos con un duplicado, un atípico, una suscripción doble y pagos con fecha |
| `cfg` | La configuración real |

Los nombres de la guía anterior (`estado_orden_pagos`, `decision_tipica`, `decision_sin_historia`, `reporte_calidad`...) siguen funcionando como alias.

## 5. Dónde van tus pruebas

`tests/unit/<tu_modulo>/test_*.py` (por ejemplo `tests/unit/motor/test_orden_pagos.py`). Puedes repetir nombres de archivo entre carpetas. Propiedades en `tests/property/` (Sebastián), accesibilidad en `tests/a11y/` (Alberto), integración y e2e en `tests/integracion/` y `tests/e2e/` (Anderson).

Patrón para la meta de una hora: la prueba con `xfail(strict=True)`. Pasa hoy; cuando implementas, empieza a pasar de verdad, `strict` la marca como fallo y quitas la marca.

```python
# tests/unit/motor/test_orden_pagos.py
import pytest
from motor import decidir

@pytest.mark.xfail(strict=True, raises=NotImplementedError, reason="caso del orden de pagos a las 12:30")
def test_orden_de_pagos(estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg):
    d = decidir(estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg)
    assert d.numero_hoy == 0
    assert "faltan S/200" in d.mensaje_falta
```

## 6. La app (Jesús y Alberto)

Páginas (v7): `src/app/main.py`, `pages/1_Hoy.py`, `pages/2_Plan.py` (Jesús) y `tema.py`, `pages/3_Por_que.py`, `pages/4_Datos.py`, `pages/5_Evaluacion.py` (Alberto).

La app solo importa `servicio` y `contratos`. Con el entorno instalado (`tareas.py setup`) **no hace falta tocar `sys.path`**:

```python
import servicio                    # forma recomendada
from contratos import Decision
```

`from src import servicio` también funciona y devuelve el mismo módulo, pero no mezcles las dos formas en un mismo archivo. Hasta que el servicio real responda (13:00), usa `servicio_falso.py` con las fixtures `decision_verde`, `decision_rojo`, `decision_confianza_baja`, `decision_sin_alcance` y `reporte_calidad_ejemplo`.

Lo que devuelve el servicio real:

- `consultar(...)` → `Decision` con `registro_id` (para auditar) y `respaldo=True` si se usó la regla sencilla porque el modelo no estaba disponible o no se adoptó. Errores: `servicio.ErrorServicio` con `.mensaje_usuario` listo para mostrar.
- `responder(propuesta_id, accion)` → `{"ok", "propuesta_id", "accion", "registro_id", "mensaje"}`; el mensaje dice "Simulación: no se movió ningún dinero." Una segunda respuesta a la misma propuesta devuelve `ok: False`.
- `salud()` → `{"consultas", "p50", "p95", "tasa_error", "tasa_respaldo", "unidad": "ms"}` (`p50`/`p95` son `None` sin consultas).
- `auditar(registro_id)` → `{"encontrado", "entradas", "decision", "version_modelo", "hash_config", "misma_config", "mismos_datos", "diferencias", "se_reproduce", ...}`.

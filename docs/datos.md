# Datos

Dueños: Rafael (generador, partición y ground truth) y Mathias (tratamiento en la ingesta). El detalle de cada
columna, los parámetros por arquetipo y la plausibilidad están en [diccionario_datos.md](diccionario_datos.md).

Todos los datos son **sintéticos**: no hay datos reales de nadie (tampoco del equipo), ni nombres, DNI, teléfonos,
cuentas o marcas reales.

## 1. Cómo se generan

| Tema | Valor | Dónde |
|---|---|---|
| Generador | `src/datos/generador.py`, versión 1.0 | `datos.generar(n_personas, meses, semilla, perturbado, parametros)` |
| Semilla | `20261114`, la única fuente de azar (`numpy.random.default_rng`) | `config/base.yaml` → `semilla_generador`. Si no se puede leer, el generador falla con un mensaje claro: no hay semilla por defecto |
| Tamaño | 400 personas, 24 meses (2025-01-01 a 2026-12-31) y 464 948 filas | Diciembre cae en los meses 12 y 24 |
| Arquetipos | conductor, vendedora, técnico, comisionista y asalariado (control) | Mezcla 25 / 25 / 20 / 20 / 10 % |
| Perturbado | Volatilidad ×1,5, ingreso ×0,8, mezcla 15 / 15 / 30 / 35 / 5 % y semilla 20262114 | Solo para la tabla de robustez, nunca para elegir un modelo |
| Partición | 20 % de las personas en prueba, elegidas con la semilla; nunca entran al entrenamiento. Meses: entrenamiento 1–16, validación 17–20 y prueba 21–24 | `datos.particion(df, semilla)`, que se guarda en `data/generado/particion.json` |
| Muestra | 20 personas (4 por arquetipo, sin cambio de patrón), subconjunto exacto del completo | `data/muestra/movimientos.csv` y `meta.json` |

**Para reproducir:**

```
python tareas.py datos
```

Esto escribe `data/generado/` (ignorado por git), `data/muestra/`, `data/REPORTE_DATOS.md` y `data/chat/`
(preguntas del asistente, de Gino). Los archivos se escriben con fin de línea LF en cualquier sistema.

| Conjunto | Archivo | Hash (`meta.json`) | Filas |
|---|---|---|---|
| Completo | `data/generado/movimientos.csv` | `30d573b1523a4d24` | 464 948 |
| Perturbado | `data/generado/movimientos_perturbado.csv` | `73dac1a4d8819f2e` | 412 843 |
| Muestra | `data/muestra/movimientos.csv` | `hash_completo` = `30d573b1523a4d24` | 22 273 |

**Advertencia sobre el hash.** `meta.json["hash"]` es el sha256 del CSV que pandas arma en memoria, y pandas usa el
fin de línea del sistema operativo. El valor `30d573b1523a4d24` corresponde a Windows (CRLF); en Linux o macOS el
mismo generador con la misma semilla da `1d358d0e43e25b89` (LF). Los datos son idénticos y solo cambia el byte de
fin de línea. Se dejó así para no cambiar el hash que el equipo ya usa. Arreglarlo (calcular siempre con LF) es una
decisión pendiente para DECISIONES.md.

## 2. Ground truth (verdad conocida)

El generador sabe qué inyectó y lo escribe en cuatro etiquetas de referencia, más dos listas en `meta.json`:

| Etiqueta | Cómo se inyecta | Qué se mide con ella |
|---|---|---|
| `es_duplicado` | Copia exacta de una fila (misma fecha, monto, comercio, tipo y saldo) con otro `transaction_id`; 1,5 % de las filas | Precisión y recall de la deduplicación de la ingesta (`ReporteCalidad.duplicados_eliminados`) |
| `es_atipico` | 0,5 % de las filas que no son pagos con fecha; el monto se multiplica por un valor uniforme entre 5 y 10 | Precisión y recall de `atipico_detectado` de la ingesta |
| `pago_con_fecha` | `True` en alquiler, servicios, deuda y suscripción | Precisión y recall de los pagos inferidos (`ReporteCalidad.pagos_inferidos`), por persona y comercio |
| `arquetipo` | Arquetipo vigente en cada fila; cambia en el año 2 para las personas con cambio de patrón | Solo para agrupar la evaluación (`eval/sesgos.py`) |
| `meta.json["suscripciones_duplicadas"]` | `transaction_id` de la segunda cobranza de una suscripción | Recall de `ReporteCalidad.suscripciones_duplicadas` |
| `meta.json["cambio_patron"]` | Personas que cambian de arquetipo | Grupo "cambio de patrón" en los sesgos |

**Cómo se mide:**
- precisión = marcados por el sistema que también lo están en la etiqueta / todos los que marcó el sistema;
- recall = marcados por el sistema que también lo están en la etiqueta / todos los que tiene la etiqueta.

Las etiquetas se leen con `ingesta.cargar_etiquetas` (Mathias) **solo en evaluación**. Resultados: **[por medir]**.

**Las etiquetas nunca entran al modelo, al motor ni a la interfaz.** Lo verifican estas piezas:

| Qué se verifica | Dónde |
|---|---|
| `datos.separar_etiquetas` quita las cuatro etiquetas | `tests/unit/datos/test_privacidad_y_fuga.py::test_separar_etiquetas_quita_las_cuatro` |
| Una historia con etiquetas se rechaza (`HistoriaInvalida`) y sin ellas pasa; el servicio llama a `validar_historia` antes de pronosticar | `tests/unit/datos/test_privacidad_y_fuga.py::test_historia_con_etiquetas_se_rechaza_y_sin_ellas_pasa`, `src/contratos/historia.py` |
| `EstadoPersona` y `PagoConFecha`, que es lo que ve el motor, no tienen campos de etiqueta | `tests/unit/datos/test_privacidad_y_fuga.py::test_estado_del_motor_sin_etiquetas` |
| `modelo.FEATURES` no contiene etiquetas | `tests/unit/datos/test_privacidad_y_fuga.py::test_features_del_modelo_sin_etiquetas` |
| Sin PII (8 y 9 dígitos, correo, tarjeta) ni columnas sensibles | `tests/unit/datos/test_privacidad_y_fuga.py` |

## 3. Escenarios difíciles inyectados (conteos del completo)

| Escenario | Esperado | Observado | Prueba |
|---|---|---|---|
| Duplicados exactos | 1,5 % de las filas | 6 871 (1,48 %) | `test_invariantes.py::test_duplicados_coinciden_con_la_tasa` |
| Atípicos | 0,5 % | 2 290 (0,49 %) | `test_atipicos_coinciden_con_la_tasa` |
| Categoría o comercio vacíos | 2 % | 4 649 + 4 649 (2,0 %) | `test_faltantes_coinciden_con_la_tasa` |
| Suscripción cobrada dos veces | 20 % de las personas con suscripción | 17 personas (4,25 %) | `test_suscripcion_doble_listada_en_meta_existe` |
| Cambio de patrón | 10 % de las personas | 45 (11,25 %) | `test_cambio_de_patron_coincide_con_meta` |

## 4. Desviaciones respecto de la v9

El generador lo escribió Gino (commit `ed86f67`, 11:25), antes de que se publicaran los planes v9, y Rafael lo
adoptó. Al compararlo con la v9 aparecieron estas diferencias. **Se mantienen todas**: corregirlas cambiaría el hash
`30d573b1523a4d24`, sobre el que el equipo ya midió (por ejemplo, la calibración del modelo de Gino), y obligaría a
repetir esas mediciones antes del congelamiento. Ninguna invalida la comparación entre métodos, porque todos se evalúan sobre los
mismos datos. Cada una se declara como límite.

| # | Tema | Qué dice la v9 | Qué hace el generador | Efecto |
|---|---|---|---|---|
| 1 | Vendedora | Entre 10 y 20 depósitos pequeños por día, de S/5 a S/30 | Un depósito diario agregado, lognormal con media S/55 | Menos filas; mismo ingreso diario. La ingesta no prueba con muchos depósitos pequeños |
| 2 | Asalariado | S/1 500 con 3 % de ruido los días 15 y último del mes | Sueldo uniforme entre S/1 100 y S/2 200, en dos mitades, más gratificación en julio y diciembre | Más realista para Perú; el control sigue siendo estable |
| 3 | Otros arquetipos | Conductor de S/60 a S/160; técnico con tiempos entre pagos exponenciales; comisionista con S/200 por semana y comisión con probabilidad de 30 % | Conductor normal de media 75; técnico con 2 a 4 pagos en días al azar; comisionista con S/250 por semana y comisión con probabilidad de 50 % | Mismo comportamiento cualitativo; cambia la escala |
| 4 | `transaction_id` | `T000001` (6 dígitos) | `T0000001` (7 dígitos) | Ninguno en la lógica; el contrato no fija el ancho. Con 7 dígitos caben más de un millón de filas |
| 5 | Cambio de patrón | A mitad de año | Al iniciar el año 2 (día 365) | El cambio cae en el mes 13, dentro del entrenamiento (meses 1–16); la prueba ve personas que ya cambiaron, no el momento del cambio |
| 6 | Suscripción cobrada dos veces | 3 % de las personas, con etiqueta `es_duplicado` y categoría suscripción | 20 % de quienes tienen suscripción (4,25 % de las personas); **sin** `es_duplicado`: los ids van en `meta.json` | Para medirla hay que leer `meta.json`, no la etiqueta |
| 7 | Días sin registro | 3 % de los días sin registro | **No se inyectan** explícitamente; solo faltan los días sin gasto discrecional (12 %) y sin ingreso | La ingesta no prueba huecos completos de días |
| 8 | Categoría de los ingresos | `contratos.CATEGORIAS` no incluye `ingreso` | Los ingresos llevan `categoria = "ingreso"` | Pendiente con Anderson: agregar `ingreso` a `CATEGORIAS` |

## 5. Alcance honesto

Los datos sintéticos demuestran que el método **recupera una estructura que nosotros mismos pusimos** (arquetipos,
estacionalidad, pagos con fecha). **No** demuestran su precisión en el mundo real. Una persona real tiene patrones
que este generador no modela (ver "Qué NO se modela" en el diccionario). Por eso:
- todo resultado se presenta junto al del generador perturbado;
- la partición es por personas y por fecha;
- los parámetros del generador están marcados [SUPUESTO];
- cualquier cifra del pitch sobre precisión dice "en datos sintéticos".

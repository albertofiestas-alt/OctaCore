# Datos

Dueños: Rafael (generador, partición y ground truth) y Mathias (tratamiento en la ingesta). El detalle de cada
columna, los parámetros por arquetipo y la plausibilidad están en [diccionario_datos.md](diccionario_datos.md).

Todos los datos son **sintéticos**: no hay datos reales de nadie (tampoco del equipo), ni nombres, DNI, teléfonos,
cuentas o marcas reales. La PII que aparece en `comercio` es inventada a propósito, para probar el enmascaramiento.

## 1. Cómo se generan

| Tema | Valor | Dónde |
|---|---|---|
| Generador | `src/datos/generador.py`, **versión 1.1** (Anderson, `a67350b`, sobre la 1.0 de Gino) | `datos.generar(...)` y `datos.generador.generar_con_verdad(...)` |
| Parámetros | Los del generador más los de la v1.1 en `config/datos.yaml` (gasto, horas de ingreso, PII), todos [SUPUESTO] | `config/datos.yaml` |
| Semilla | `20261114`, la única fuente de azar (dos `numpy` rng derivados de ella; el segundo es de la v1.1 y no mueve los números de la v1.0) | `config/base.yaml` → `semilla_generador`. Sin configuración legible, el generador falla: no hay semilla por defecto |
| Tamaño | 400 personas, 24 meses (2025-01-01 a 2026-12-31) y 464 948 filas | Diciembre cae en los meses 12 y 24 |
| Arquetipos | conductor, vendedora, técnico, comisionista y asalariado (control) | Mezcla 25 / 25 / 20 / 20 / 10 % |
| Perturbado | Volatilidad ×1,5, ingreso ×0,8, mezcla 15 / 15 / 30 / 35 / 5 % y semilla 20262114 | Solo para la tabla de robustez, nunca para elegir un modelo |
| Partición | 20 % de las personas en prueba, elegidas con la semilla; nunca entran al entrenamiento. Meses: entrenamiento 1–16, validación 17–20 y prueba 21–24 | `datos.particion(df, semilla)`, que se guarda en `data/generado/particion.json` |
| Muestra | 20 personas (4 por arquetipo, sin cambio de patrón), subconjunto exacto del completo | `data/muestra/movimientos.csv`, `verdad_eventos.csv` y `meta.json` |

**Qué cambió de la v1.0 a la v1.1.** Las personas, los arquetipos, los ingresos y los escenarios son los mismos.
Cambian tres cosas:
1. **Gasto endógeno:** el gasto discrecional depende del saldo (base + propensión × exceso sobre una reserva; ver el
   diccionario). Los pagos con fecha no se recortan.
2. **Horas de ingreso por arquetipo:** en la v1.0 el 100 % llegaba a las 20:00.
3. **PII ficticia** en el 0,5 % del texto de `comercio`, con su verdad en `verdad_eventos.csv`.

**Para reproducir:**

```
python tareas.py datos
```

Esto escribe `data/generado/` (ignorado por git), `data/muestra/` y `data/REPORTE_DATOS.md`, con fin de línea LF en
cualquier sistema. **Advertencia:** hoy también reescribe `data/chat/preguntas.csv` de Gino con la versión generada
(225 líneas en vez de las 319 editadas). Hasta que se corrija, genera con `python -m datos --salida <carpeta temporal>`.

| Conjunto | Archivo | Hash de datos | Hash de la verdad de eventos | Filas |
|---|---|---|---|---|
| Completo | `data/generado/movimientos.csv` | `736316b2c4ad9b5c` | `04a07cae737c1505` | 464 948 |
| Perturbado | `data/generado/movimientos_perturbado.csv` | `12bab9fb3feb1a2c` | `8705f500b918db4d` | 412 843 |
| Muestra | `data/muestra/movimientos.csv` | `hash_completo` = `736316b2c4ad9b5c` (en `meta.json`) | — | 22 273 |

Los hashes de la v1.0 (`30d573b1523a4d24` y `73dac1a4d8819f2e`) ya no aplican.

**Advertencia sobre el hash.** `meta.json["hash"]` y `["hash_verdad"]` son el sha256 del CSV que pandas arma en
memoria, y pandas usa el fin de línea del sistema operativo. Los valores de arriba corresponden a Windows (CRLF); en
Linux o macOS el mismo generador da otro valor con datos idénticos. Arreglarlo (calcular siempre con LF) cambia el
hash una vez y es una decisión pendiente para DECISIONES.md.

## 2. Ground truth (verdad conocida)

El generador sabe qué inyectó y lo escribe en cuatro etiquetas de referencia, un archivo de eventos y dos listas en
`meta.json`. **Todo es SOLO para evaluación.**

| Fuente | Cómo se genera | Qué se mide con ella |
|---|---|---|
| `es_duplicado` | Copia exacta de una fila con otro `transaction_id`; 1,5 % de las filas | Precisión y recall de la deduplicación de la ingesta |
| `es_atipico` | 0,5 % de las filas que no son pagos con fecha; monto ×5 a ×10 | Precisión y recall de `atipico_detectado` |
| `pago_con_fecha` | `True` en alquiler, servicios, deuda y suscripción | Precisión y recall de los pagos inferidos, por persona y comercio |
| `arquetipo` | Arquetipo vigente en cada fila; cambia en el año 2 para quien cambia de patrón | Solo para agrupar la evaluación (`eval/sesgos.py`) |
| `verdad_eventos.csv` → `pago_con_saldo_negativo` | Cada pago con fecha que, **con el gasto observado** (el del generador), dejó el saldo en negativo; `valor` es el saldo resultante. 7 575 en el completo y 297 en la muestra | Verdad de los "pagos descubiertos" sin la herramienta. Sirve para validar el simulador: con el gasto observado, la simulación debe reproducir estos eventos |
| `verdad_eventos.csv` → `pii_dni`, `pii_telefono`, `pii_correo` | Filas donde se inyectó PII ficticia en `comercio`; `valor` es el texto inyectado. 945 + 915 + 464 = 2 324 en el completo | Recall de `ingesta.detectar_pii` / `enmascarar_pii` (`ReporteCalidad.pii_enmascarado`) |
| `meta.json["suscripciones_duplicadas"]` | `transaction_id` de la segunda cobranza de una suscripción (17) | Recall de `ReporteCalidad.suscripciones_duplicadas` |
| `meta.json["cambio_patron"]` | Personas que cambian de arquetipo (45) | Grupo "cambio de patrón" en los sesgos |

**Cómo se mide:**
- precisión = marcados por el sistema que también lo están en la verdad / todos los que marcó el sistema;
- recall = marcados por el sistema que también lo están en la verdad / todos los que tiene la verdad.

Las etiquetas se leen con `ingesta.cargar_etiquetas` **solo en evaluación**. Resultados de precisión y recall:
**[por medir]**.

**Nada de esto entra al modelo, al motor ni a la interfaz.** Lo verifican estas piezas:

| Qué se verifica | Dónde |
|---|---|
| `datos.separar_etiquetas` quita las cuatro etiquetas | `tests/unit/datos/test_privacidad_y_fuga.py::test_separar_etiquetas_quita_las_cuatro` |
| Una historia con etiquetas se rechaza (`HistoriaInvalida`) y sin ellas pasa; el servicio llama a `validar_historia` antes de pronosticar | `tests/unit/datos/test_privacidad_y_fuga.py::test_historia_con_etiquetas_se_rechaza_y_sin_ellas_pasa`, `src/contratos/historia.py` |
| `EstadoPersona` y `PagoConFecha`, que es lo que ve el motor, no tienen campos de etiqueta | `tests/unit/datos/test_privacidad_y_fuga.py::test_estado_del_motor_sin_etiquetas` |
| `modelo.FEATURES` no contiene etiquetas | `tests/unit/datos/test_privacidad_y_fuga.py::test_features_del_modelo_sin_etiquetas` |
| La única PII del CSV es la declarada en `verdad_eventos.csv`; no hay columnas sensibles | `tests/unit/datos/test_privacidad_y_fuga.py`, `tests/unit/datos/test_realismo.py` |

## 3. Escenarios difíciles inyectados (conteos del completo, v1.1)

| Escenario | Esperado | Observado | Prueba |
|---|---|---|---|
| Duplicados exactos | 1,5 % de las filas | 6 871 (1,48 %) | `test_invariantes.py::test_duplicados_coinciden_con_la_tasa` |
| Atípicos | 0,5 % | 2 290 (0,49 %) | `test_atipicos_coinciden_con_la_tasa` |
| Categoría o comercio vacíos | 2 % | 4 649 + 4 649 (2,0 %) | `test_faltantes_coinciden_con_la_tasa` |
| Suscripción cobrada dos veces | 20 % de quienes tienen suscripción | 17 personas (4,25 %) | `test_suscripcion_doble_listada_en_meta_existe` |
| Cambio de patrón | 10 % de las personas | 45 (11,25 %) | `test_cambio_de_patron_coincide_con_meta` |
| PII ficticia en `comercio` | 0,5 % de las filas | 2 324 (0,50 %) | `test_privacidad_y_fuga.py`, `test_realismo.py` |
| Pagos que dejan el saldo negativo (resultado, no inyección) | Mayor que 0 | 7 575 pagos; 83 % de las personas | `data/REPORTE_DATOS.md` |

## 4. Plausibilidad (declarada)

| Medida | v1.1 | Referencia | Lectura |
|---|---|---|---|
| Ingreso mensual medio | S/1 944,1 | INEI S/1 887 [por verificar en su fuente] | Razón **1,03** |
| Personas con algún mes en déficit en el año 2 | **100 %** (v1.0: 81 %) | SBS 85 % [por verificar en su fuente] | **Más duro que la referencia** |
| Personas con saldo negativo tras algún pago | **83 %** (v1.0: 43,8 %) | — | Es el evento que el producto intenta evitar |

Los datos v1.1 son más duros que la referencia de la SBS. **Se declara y no se recalibra** [propuesto, pendiente de
Gino], por tres razones:
- recalibrar cambiaría el hash `736316b2c4ad9b5c` y obligaría a repetir las mediciones de frontera, pares y adopción
  ya hechas sobre él;
- la población con déficit frecuente es justo el usuario objetivo;
- la referencia describe a otra población real.

Detalle por arquetipo y perturbado en el diccionario.

## 5. Desviaciones respecto de la v9

El generador 1.0 lo escribió Gino (commit `ed86f67`, 11:25), antes de que se publicaran los planes v9; Rafael lo
adoptó y Anderson lo llevó a la 1.1. Al compararlo con la v9 aparecen estas diferencias. **Se mantienen**: corregirlas
cambiaría el hash sobre el que el equipo ya midió. Ninguna invalida la comparación entre métodos, porque todos se
evalúan sobre los mismos datos. Cada una se declara como límite.

| # | Tema | Qué dice la v9 | Qué hace el generador | Efecto |
|---|---|---|---|---|
| 1 | Vendedora | Entre 10 y 20 depósitos pequeños por día, de S/5 a S/30 | Un depósito diario agregado, lognormal con media S/55 | Menos filas; mismo ingreso diario. La ingesta no prueba con muchos depósitos pequeños |
| 2 | Asalariado | S/1 500 con 3 % de ruido los días 15 y último del mes | Sueldo uniforme entre S/1 100 y S/2 200, en dos mitades, más gratificación en julio y diciembre | Más realista para Perú; el control sigue siendo estable |
| 3 | Otros arquetipos | Conductor de S/60 a S/160; técnico con tiempos entre pagos exponenciales; comisionista con S/200 por semana y comisión con probabilidad de 30 % | Conductor normal de media 75; técnico con 2 a 4 pagos en días al azar; comisionista con S/250 por semana y comisión con probabilidad de 50 % | Mismo comportamiento cualitativo; cambia la escala |
| 4 | `transaction_id` | `T000001` (6 dígitos) | `T0000001` (7 dígitos) | Ninguno en la lógica; el contrato no fija el ancho |
| 5 | Cambio de patrón | A mitad de año | Al iniciar el año 2 (día 365) | El cambio cae en el mes 13, dentro del entrenamiento; la prueba ve personas que ya cambiaron |
| 6 | Suscripción cobrada dos veces | 3 % de las personas, con etiqueta `es_duplicado` | 20 % de quienes tienen suscripción (4,25 % de las personas); **sin** `es_duplicado`: los ids van en `meta.json` | Para medirla hay que leer `meta.json` |
| 7 | Días sin registro | 3 % de los días sin registro | **No se inyectan**; solo faltan los días sin gasto discrecional (12 %) y sin ingreso | La ingesta no prueba huecos completos de días |
| 8 | Categoría de los ingresos | `contratos.CATEGORIAS` no incluye `ingreso` | Los ingresos llevan `categoria = "ingreso"` | Pendiente con Anderson |
| 9 | Gasto discrecional (v1.1) | Sigue el ingreso reciente con ruido | Depende del **saldo** (gasto endógeno) | Más realista (vive al día); el simulador debe reemplazar este gasto por el permitido |
| 10 | Déficit (v1.1) | Plausibilidad contra el 85 % de la SBS | 100 % de las personas con algún mes en déficit | Declarado en la sección 4 |

## 6. Alcance honesto

Los datos sintéticos demuestran que el método **recupera una estructura que nosotros mismos pusimos** (arquetipos,
estacionalidad, pagos con fecha, gasto que reacciona al saldo). **No** demuestran su precisión en el mundo real. Una
persona real tiene patrones que este generador no modela (ver "Qué NO se modela" en el diccionario). Por eso:
- todo resultado se presenta junto al del generador perturbado;
- la partición es por personas y por fecha;
- los parámetros del generador están marcados [SUPUESTO];
- cualquier cifra del pitch sobre precisión dice "en datos sintéticos".

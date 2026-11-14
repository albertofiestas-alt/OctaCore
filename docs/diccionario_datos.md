# Diccionario de datos

Dueño: Rafael. Describe cada columna de `data/muestra/movimientos.csv` y de `data/generado/movimientos.csv`, que salen de
`src/datos/generador.py` en su **versión 1.1** (semilla 20261114 de `config/base.yaml`, hash `736316b2c4ad9b5c`).
La versión 1.1 es de Anderson (commit `a67350b`) y sus parámetros nuevos viven en `config/datos.yaml`.

Todos los parámetros del generador son **[SUPUESTO]**: se eligieron para que la plausibilidad (al final) sea razonable,
no se estimaron con datos reales. Los rangos "observados" se midieron con `pandas` el 14-nov sobre los archivos de la
v1.1 (muestra: 20 personas y 22 273 filas; completo: 400 personas y 464 948 filas). La prueba
`tests/unit/datos/test_diccionario.py` falla si aparece una columna que no está en este documento.

## Columnas del contrato (entran a la ingesta)

| Columna | Tipo | Observado en la muestra | Observado en el completo | Cómo la genera `generador.py` | Supuesto |
|---|---|---|---|---|---|
| `customer_id` | texto | `P0001` a `P0045` (20 personas, 4 por arquetipo, sin cambio de patrón) | `P0001` a `P0400` | `P` más 4 dígitos según el orden de creación | Identificador ficticio |
| `transaction_id` | texto, único | `T0000001` a `T0052002` (no son correlativos, porque la muestra es un subconjunto) | `T0000001` a `T0464948`, todos únicos | `T` más **7 dígitos**, asignados después de ordenar por persona y fecha | Ficticio. La v9 decía 6 dígitos (ver `docs/datos.md`, desviaciones) |
| `fecha_hora` | fecha y hora `AAAA-MM-DD HH:MM:SS` | 2025-01-01 07:07 a 2026-12-31 21:44 | 2025-01-01 06:06 a 2026-12-31 22:55; horas de 6 a 22 | Día del calendario más una hora. **Ingresos según el arquetipo** (`config/datos.yaml: horas_ingreso`): conductor de 6 a 22 h, vendedora de 7 a 20 h, técnico y comisionista de 9 a 17 h, asalariado de 6 a 9 h. Pagos fijos de 9 a 13 h; gasto diario de 8 a 21 h; minutos al azar | 24 meses desde el 2025-01-01; diciembre cae en los meses 12 y 24 |
| `monto` | decimal, 2 decimales | Ingresos de 5,27 a 7 434,43 (mediana 76,54); gastos de −1 631,39 a −0,79 (mediana −21,01) | Ingresos de 3,84 a 13 578,29 (mediana 70,47); gastos de −5 543,50 a −0,50 (mediana −24,52) | Positivo en ingresos y negativo en gastos. El gasto discrecional depende del saldo (ver "Gasto endógeno") y nunca baja de S/0,50. Los extremos son atípicos inyectados (×5 a ×10) | Soles |
| `moneda` | texto | Solo `PEN` | Solo `PEN` | Constante | Una sola moneda |
| `tipo` | `ingreso` / `gasto` | 6 321 ingresos y 15 952 gastos | 147 728 ingresos y 317 220 gastos | Según el origen del movimiento | — |
| `categoria` | texto, puede venir vacío | `alimentacion`, `ingreso`, `transporte`, `otros`, `servicios`, `alquiler`, `deuda`, `suscripcion` y vacíos | Las mismas 8; 4 649 vacíos (1,0 %) | `ingreso` para todo ingreso; categoría fija para los pagos con fecha; `alimentacion` (55 %), `transporte` (30 %) u `otros` (15 %) para el gasto diario. El 1 % de las filas se vacía a propósito | `ingreso` no está en `contratos.CATEGORIAS`; pendiente con Anderson |
| `comercio` | texto, puede venir vacío o **con PII ficticia** | 26 comercios ficticios, vacíos y 110 filas con PII | 26 comercios ficticios más 2 324 textos con PII (2 346 valores distintos) y 4 649 vacíos | Pagador según el arquetipo (`AppViajes`, `VentasDelDia`, `ClienteProyecto`, `ComisionesSur`, `EmpleadorSA`) o comercio según la categoría (`Luzandina`, `AguaClara`, `NetHogar`…). En el 0,5 % de las filas se agrega al texto un DNI, un teléfono o un correo **ficticios** (por ejemplo `TiendaUtil Yape 9xxxxxxxx`) | Nombres inventados. La PII es al azar y el correo usa el dominio reservado `correo-ficticio.example`. Nunca cae en pagos con fecha |
| `saldo` | decimal | −2 232,52 a 7 759,17; sin vacíos | −4 852,00 a 14 474,78; sin vacíos | Saldo inicial (1,0 a 1,5 veces la reserva del día 1) más la suma acumulada de los montos, antes de inyectar duplicados (una copia duplicada repite el saldo de su original) | **Puede ser negativo**: no se modela un límite de sobregiro |
| `ingreso_recurrente` | booleano (columna opcional del contrato) | `True` en 214 filas | `True` en 2 222 filas | `True` solo en los ingresos del asalariado (sueldo quincenal y gratificación); `False` en el resto, gastos incluidos | Marca de sueldo fijo |

## Etiquetas de referencia (SOLO para evaluación)

Son la verdad conocida por el generador. **Nunca entran al modelo, al motor ni a la interfaz.** La ingesta y
`datos.separar_etiquetas` las separan, y `contratos.validar_historia` rechaza una historia que las traiga (ver
`docs/datos.md`, ground truth).

| Columna | Tipo | Observado en la muestra | Observado en el completo | Cómo se genera | Uso |
|---|---|---|---|---|---|
| `es_duplicado` | booleano | 354 `True` | 6 871 `True` (1,48 %) | Copia exacta de una fila con otro `transaction_id`; tasa de 1,5 % de las filas | Precisión y recall de la deduplicación de la ingesta |
| `es_atipico` | booleano | 120 `True` | 2 290 `True` (0,49 %) | 0,5 % de las filas que no son pagos con fecha; el monto se multiplica por un valor uniforme entre 5 y 10 | Precisión y recall de `atipico_detectado` |
| `pago_con_fecha` | booleano | 2 890 `True` | 55 760 `True` | `True` en alquiler, servicios (luz, agua, internet, celular), deuda y suscripción; `False` en la segunda cobranza de una suscripción doble | Precisión y recall de los pagos inferidos |
| `arquetipo` | texto | `conductor`, `vendedora`, `tecnico`, `comisionista`, `asalariado` | Igual; personas por arquetipo inicial: 111, 86, 83, 79 y 41 | Arquetipo vigente en esa fila; cambia a partir del día 365 en las personas con cambio de patrón | Solo para agrupar la evaluación (`eval/sesgos.py`) |

## Archivo aparte: `verdad_eventos.csv` (SOLO para evaluación)

`data/generado/verdad_eventos.csv` (9 899 filas) y `data/muestra/verdad_eventos.csv` (407 filas). No forma parte del
CSV de movimientos.

| Columna | Tipo | Contenido |
|---|---|---|
| `transaction_id` | texto | Fila de movimientos a la que se refiere el evento |
| `customer_id` | texto | Persona |
| `evento` | texto | `pago_con_saldo_negativo` (7 575 en el completo, 297 en la muestra), `pii_dni` (945 / 44), `pii_telefono` (915 / 42) o `pii_correo` (464 / 24) |
| `valor` | texto | Saldo tras el pago (por ejemplo `-10.69`), o el texto de PII inyectado |

Hash de este archivo en el completo: `04a07cae737c1505` (`meta.json["hash_verdad"]`). La suscripción cobrada dos
veces sigue **sin** etiqueta propia: sus `transaction_id` están en `meta.json["suscripciones_duplicadas"]` (17 en el
completo). Las personas con cambio de patrón están en `meta.json["cambio_patron"]` (45).

## Parámetros por arquetipo [SUPUESTO]

`f` = factor de ingreso (1,0, o 0,8 en el perturbado) × nivel de la persona (lognormal de media 1 y sigma 0,25,
recortado entre 0,6 y 1,6). `vol` = 1,0 (1,5 en el perturbado). `est` = factor estacional del mes. **Los ingresos son
los mismos que en la v1.0**; la v1.1 solo cambió su hora.

| Arquetipo | Mezcla base | Ingreso | Estacionalidad del ingreso | Propensión a gastar el exceso de saldo |
|---|---|---|---|---|
| conductor | 25 % | Un depósito diario normal con media 75·f·est (×0,7 en feriados) y desvío 25·vol. No trabaja los domingos y descansa el 5 % de los días; se descartan montos menores a S/5 | Julio ×1,10, diciembre ×1,25 | 0,30 a 0,60 |
| vendedora | 25 % | Un depósito diario lognormal con media 55·f·est (×1,4 sábado y domingo) y sigma 0,5·vol | Marzo ×1,30, julio ×1,15, diciembre ×1,35 | 0,30 a 0,60 |
| tecnico | 20 % | Cada mes: ningún pago con probabilidad 0,15·vol; si no, 2, 3 o 4 pagos uniformes entre S/300 y S/1 200 (×f) | Ninguna | 0,06 a 0,15 |
| comisionista | 20 % | Base cada viernes de 250·f·(1 + normal(0; 0,1·vol)); el último día del mes, con probabilidad 0,5, una comisión uniforme entre S/200 y S/1 800 (×f·est) | Diciembre ×1,30 | 0,12 a 0,30 |
| asalariado (control) | 10 % | Sueldo uniforme entre S/1 100 y S/2 200, en dos mitades los días 15 y último del mes con ruido de 3 %; gratificación de un sueldo el 15 de julio y el 15 de diciembre | Solo la gratificación | 0,06 a 0,15 |

**Gastos fijos (pagos con fecha), sin cambios respecto de la v1.0:**
- Alquiler entre el día 1 y el 5: una fracción de 18 % a 38 % del ingreso mensual medio, recortada entre S/350 y S/900.
- Luz entre el día 8 y el 12: de S/60 a S/150, con 15 % de variación.
- Agua entre el día 10 y el 15: de S/30 a S/60, con 5 % de variación.
- Internet entre el día 15 y el 20: de S/70 a S/120.
- Celular entre el día 20 y el 25: de S/30 a S/60.
- Deuda para el 40 % de las personas: de S/100 a S/400.
- Suscripción para el 30 %: de S/15 a S/40.

Los pagos con fecha **no se recortan**: si no alcanza, el saldo queda negativo.

**Gasto endógeno (v1.1).** El gasto discrecional diario (88 % de los días; alimentación, transporte u otros)
depende del saldo del momento:

    gasto = (base × estacional × [0,6 si saldo ≤ 0] + propensión × max(0, saldo − reserva)) × ruido
    reserva = colchón + previsión × (pagos con fecha + gasto mínimo de los próximos 14 días)

Todos los parámetros son por persona y [SUPUESTO] (`config/datos.yaml: gasto`):
- base: entre 30 % y 60 % del disponible diario, con un piso de S/4;
- colchón: de S/50 a S/300;
- previsión: de 0,3 a 1,0;
- ruido: lognormal con sigma 0,5;
- estacionalidad del gasto: julio ×1,10, diciembre ×1,30.

Quien tiene saldo gasta más, y quien no, recorta. Por eso el saldo no crece sin límite y la correlación semanal
ingreso-gasto es positiva. Además, hay útiles escolares en marzo para el 40 % de las personas, de S/100 a S/250.

**Escenarios inyectados (sin cambios):**
- Cambio de patrón en el 10 % de las personas, al iniciar el año 2.
- Suscripción cobrada dos veces en el 20 % de quienes tienen suscripción.
- Atípicos en el 0,5 % de las filas.
- Duplicados en el 1,5 %.
- Categoría o comercio vacíos en el 2 %.
- **Nuevo:** PII ficticia en el 0,5 % del texto de `comercio` (40 % DNI, 40 % teléfono, 20 % correo).

**Generador perturbado:** volatilidad ×1,5, ingreso ×0,8, mezcla 15 / 15 / 30 / 35 / 5 % y semilla 20262114.

## Realismo

Cifras de `datos.verificar()` y `datos.generador.medir_realismo()` sobre las 400 personas de la v1.1 (también en
`data/REPORTE_DATOS.md`), medidas el 14-nov. Se excluyen los duplicados inyectados.

| Medida | v1.1 | v1.0 (antes) | Referencia | Lectura |
|---|---|---|---|---|
| Ingreso mensual medio por persona | S/1 944,1 (mediana S/1 882,5) | Igual | INEI: S/1 887 **[por verificar en su fuente]** | Razón 1,03 |
| Personas con al menos un mes en déficit en el año 2 | **100 %** | 81 % | SBS: 85 % **[por verificar en su fuente]** | **15 puntos por encima**: más duro que la referencia |
| Personas con saldo negativo tras algún pago con fecha | **83 %** | 43,8 % | — | Es el evento que el producto quiere evitar |
| Pagos con fecha que dejan el saldo negativo (media por persona) | 13,5 % | 5,5 % | — | — |
| Saldo mediano a fin de mes (meses 1 / 6 / 12 / 18 / 24) | S/801 / 782 / 860 / 796 / 916 | S/1 118 a S/7 804 (creciente) | El usuario vive al día | Sin tendencia creciente |
| Saldo mediano en días de ingreso típico | 7,7 días | 65,2 | "Pocos días" | Vive al día |
| Correlación semanal ingreso-gasto discrecional (mediana) | 0,45 | 0,02 | Claramente positiva | Gasta cuando cobra |
| Ingresos a las 20:00 | 3,3 % | 100 % | Sin reloj fijo | — |
| Perturbado: ingreso / déficit en el año 2 / saldo negativo tras un pago | S/1 479,9 (razón 0,78) / 99,8 % / 89,2 % | S/1 479,9 / 95,8 % / — | — | Escenario más duro a propósito |

**Declaración [propuesto, pendiente de Gino].** Los datos v1.1 son **más duros que la referencia de la SBS**: todas
las personas tienen algún mes en déficit y el 83 % se queda en negativo tras algún pago. **Se declara y no se
recalibra.** Recalibrar cambiaría el hash `736316b2c4ad9b5c` y obligaría a repetir las mediciones ya hechas sobre
él. Además, un usuario con déficit frecuente es justo la población objetivo del producto. Las referencias del INEI y
la SBS describen poblaciones reales distintas, así que sirven para comprobar el orden de magnitud y no son un
objetivo a calzar.

**Por arquetipo (v1.1; entre paréntesis la v1.0):**

| Arquetipo | Personas | Ingreso mensual medio | % con algún mes en déficit (año 2) | % con saldo negativo tras un pago | Hora mediana del ingreso |
|---|---|---|---|---|---|
| conductor | 86 | S/1 988 | 100 % (72,1 %) | 70,9 % (27,9 %) | 14 h (20 h) |
| vendedora | 111 | S/2 083 | 100 % (80,2 %) | 72,1 % (21,6 %) | 13 h (20 h) |
| tecnico | 83 | S/1 986 | 100 % (100 %) | 98,8 % (73,5 %) | 13 h (20 h) |
| comisionista | 79 | S/1 653 | 100 % (91,1 %) | 97,5 % (59,5 %) | 13 h (20 h) |
| asalariado | 41 | S/1 954 | 100 % (43,9 %) | 78 % (46,3 %) | 8 h (20 h) |

### Qué NO se modela

- Sobregiro, líneas de crédito, préstamos nuevos ni intereses: el saldo puede quedar negativo sin consecuencias.
- Transferencias entre cuentas propias, efectivo fuera de la cuenta, reembolsos o devoluciones.
- Impuestos, inflación, cambios de precio de los servicios y otras monedas.
- Feriados móviles, choques macroeconómicos y correlación entre personas: cada persona es independiente.
- Hogares, dependientes y cualquier variable demográfica (edad, género, ubicación). No existen en los datos; la PII
  ficticia de `comercio` es texto al azar para probar el enmascaramiento.
- Que la persona recorte un pago con fecha: los pagos se cobran siempre completos.
- Días sin ningún registro como escenario explícito (ver `docs/datos.md`, desviaciones).

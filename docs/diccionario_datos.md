# Diccionario de datos

Dueño: Rafael. Describe cada columna de `data/muestra/movimientos.csv` y de `data/generado/movimientos.csv`, que salen de
`src/datos/generador.py` (versión 1.0, semilla 20261114 de `config/base.yaml`, hash `30d573b1523a4d24`).

Todos los parámetros del generador son **[SUPUESTO]**: se eligieron para que la plausibilidad (al final) sea razonable,
no se estimaron con datos reales. Los rangos "observados" se midieron con `pandas` sobre los archivos generados el
14-nov (muestra: 20 personas y 22 273 filas; completo: 400 personas y 464 948 filas). La prueba
`tests/unit/datos/test_diccionario.py` falla si aparece una columna que no está en este documento.

## Columnas del contrato (entran a la ingesta)

| Columna | Tipo | Observado en la muestra | Observado en el completo | Cómo la genera `generador.py` | Supuesto |
|---|---|---|---|---|---|
| `customer_id` | texto | `P0001` a `P0045` (20 personas, 4 por arquetipo y sin cambio de patrón) | `P0001` a `P0400` | `P` más 4 dígitos según el orden de creación | Identificador ficticio, sin relación con personas reales |
| `transaction_id` | texto, único | `T0000001` a `T0052002` (no son correlativos, porque la muestra es un subconjunto) | `T0000001` a `T0464948`, todos únicos | `T` más **7 dígitos**, asignados después de ordenar por persona y fecha | Ficticio. La v9 decía 6 dígitos (ver `docs/datos.md`, desviaciones) |
| `fecha_hora` | fecha y hora `AAAA-MM-DD HH:MM:SS` | 2025-01-01 08:32 a 2026-12-31 21:44 | 2025-01-01 08:00 a 2026-12-31 21:57; horas de 8 a 21 | Día del calendario más una hora fija por tipo (ingresos 20 h, pagos fijos de 9 a 13 h, gasto diario de 8 a 21 h) y minutos al azar | 24 meses desde el 2025-01-01; diciembre cae en los meses 12 y 24 |
| `monto` | decimal, 2 decimales | Ingresos de 5,27 a 7 434,43 (mediana 76,57); gastos de −1 431,78 a −0,58 (mediana −17,14) | Ingresos de 3,84 a 13 578,29 (mediana 70,50); gastos de −2 474,99 a −0,34 (mediana −22,93) | Positivo en ingresos y negativo en gastos. Los extremos son atípicos inyectados (×5 a ×10) | Soles. Ver los parámetros por arquetipo |
| `moneda` | texto | Solo `PEN` | Solo `PEN` | Constante | Una sola moneda |
| `tipo` | `ingreso` / `gasto` | 6 327 ingresos y 15 946 gastos | 147 729 ingresos y 317 219 gastos | Según el origen del movimiento | — |
| `categoria` | texto, puede venir vacío | `alimentacion`, `ingreso`, `transporte`, `otros`, `servicios`, `alquiler`, `deuda`, `suscripcion` y 212 vacíos | Las mismas 8; 4 649 vacíos (1,0 %) | `ingreso` para todo ingreso; categoría fija para los pagos con fecha; `alimentacion` (55 %), `transporte` (30 %) u `otros` (15 %) para el gasto diario. El 1 % de las filas se vacía a propósito | `ingreso` no está en `contratos.CATEGORIAS`; pendiente con Anderson |
| `comercio` | texto, puede venir vacío | 26 comercios ficticios y 197 vacíos | Los mismos 26 y 4 649 vacíos (1,0 %) | Pagador según arquetipo (`AppViajes`, `VentasDelDia`, `ClienteProyecto`, `ComisionesSur`, `EmpleadorSA`) o comercio ficticio según categoría (`Luzandina`, `AguaClara`, `NetHogar`, `MovilFacil`, `ArrendadorSur`…) | Nombres inventados; ninguna marca real |
| `saldo` | decimal | −1 525,53 a 17 864,81; sin vacíos | −9 256,00 a 26 315,05; sin vacíos | Saldo inicial uniforme entre S/300 y S/1 500 más la suma acumulada de los montos, antes de inyectar duplicados (una copia duplicada repite el saldo de su original) | **Puede ser negativo**: no se modela un límite de sobregiro |
| `ingreso_recurrente` | booleano (columna opcional del contrato) | `True` en 217 filas | `True` en 2 221 filas | `True` solo en los ingresos del asalariado (sueldo quincenal y gratificación); `False` en el resto, gastos incluidos | Marca de sueldo fijo |

## Etiquetas de referencia (SOLO para evaluación)

Son la verdad conocida por el generador. **Nunca entran al modelo, al motor ni a la interfaz.** La ingesta y
`datos.separar_etiquetas` las separan, y `contratos.validar_historia` rechaza una historia que las traiga (ver
`docs/datos.md`, ground truth).

| Columna | Tipo | Observado en la muestra | Observado en el completo | Cómo se genera | Uso |
|---|---|---|---|---|---|
| `es_duplicado` | booleano | 354 `True` | 6 871 `True` (1,48 %) | Copia exacta de una fila con otro `transaction_id`; tasa de 1,5 % de las filas | Precisión y recall de la deduplicación de la ingesta |
| `es_atipico` | booleano | 120 `True` | 2 290 `True` (0,49 %) | 0,5 % de las filas que no son pagos con fecha; el monto se multiplica por un valor uniforme entre 5 y 10 | Precisión y recall de `atipico_detectado` |
| `pago_con_fecha` | booleano | 2 885 `True` | 55 771 `True` | `True` en alquiler, servicios (luz, agua, internet, celular), deuda y suscripción; `False` en la segunda cobranza de una suscripción doble | Precisión y recall de los pagos inferidos |
| `arquetipo` | texto | `conductor`, `vendedora`, `tecnico`, `comisionista`, `asalariado` | Igual; personas por arquetipo inicial: 111, 86, 83, 79 y 41 | Arquetipo vigente en esa fila; cambia a partir del día 365 en las personas con cambio de patrón | Solo para agrupar la evaluación (`eval/sesgos.py`) |

La suscripción cobrada dos veces **no** tiene etiqueta propia en el CSV: sus `transaction_id` están en
`meta.json["suscripciones_duplicadas"]` (17 en el completo). Las personas con cambio de patrón están en
`meta.json["cambio_patron"]` (45 en el completo).

## Parámetros por arquetipo [SUPUESTO]

`f` = factor de ingreso (1,0, o 0,8 en el perturbado) × nivel de la persona (lognormal de media 1 y sigma 0,25,
recortado entre 0,6 y 1,6). `vol` = 1,0 (1,5 en el perturbado). `est` = factor estacional del mes.

| Arquetipo | Mezcla base | Ingreso | Estacionalidad del ingreso |
|---|---|---|---|
| conductor | 25 % | Un depósito diario normal con media 75·f·est (×0,7 en feriados) y desvío 25·vol. No trabaja los domingos y descansa el 5 % de los días; se descartan montos menores a S/5 | Julio ×1,10, diciembre ×1,25 |
| vendedora | 25 % | Un depósito diario lognormal con media 55·f·est (×1,4 sábado y domingo) y sigma 0,5·vol | Marzo ×1,30 (campaña escolar), julio ×1,15, diciembre ×1,35 |
| tecnico | 20 % | Cada mes: ningún pago con probabilidad 0,15·vol; si no, 2, 3 o 4 pagos uniformes entre S/300 y S/1 200 (×f) en días al azar | Ninguna |
| comisionista | 20 % | Base cada viernes de 250·f·(1 + normal(0; 0,1·vol)); el último día del mes, con probabilidad 0,5, una comisión uniforme entre S/200 y S/1 800 (×f·est) | Diciembre ×1,30 |
| asalariado (control) | 10 % | Sueldo uniforme entre S/1 100 y S/2 200, pagado en dos mitades los días 15 y último del mes con ruido de 3 %; gratificación de un sueldo el 15 de julio y el 15 de diciembre | Solo la gratificación |

**Gastos fijos (pagos con fecha), para todos:**
- Alquiler entre el día 1 y el 5: una fracción uniforme de 18 % a 38 % del ingreso mensual medio, redondeada y recortada entre S/350 y S/900.
- Luz entre el día 8 y el 12: de S/60 a S/150, con 15 % de variación mensual.
- Agua entre el día 10 y el 15: de S/30 a S/60, con 5 % de variación.
- Internet entre el día 15 y el 20: de S/70 a S/120.
- Celular entre el día 20 y el 25: de S/30 a S/60.
- Cuota de deuda para el 40 % de las personas: de S/100 a S/400, en un día fijo.
- Suscripción para el 30 %: de S/15 a S/40, en un día fijo.

**Gastos discrecionales:**
- Útiles escolares en marzo para el 40 % de las personas, de S/100 a S/250.
- Gasto diario en el 88 % de los días, lognormal con sigma 0,6. La media diaria es max(150, 0,84·ingreso mensual medio − fijos) / 30, multiplicada por un factor personal uniforme entre 0,8 y 1,2.
- Estacionalidad del gasto: julio ×1,10, diciembre ×1,30.

**Escenarios inyectados:**
- Cambio de patrón en el 10 % de las personas, que pasan a otro arquetipo al iniciar el año 2.
- Suscripción cobrada dos veces en el 20 % de las personas con suscripción, un mes del año 2, entre 3 y 10 días después del cobro normal.
- Atípicos en el 0,5 % de las filas.
- Duplicados en el 1,5 % de las filas.
- Categoría o comercio vacíos en el 2 % de las filas (mitad cada uno).

**Feriados:** 1-ene, 1-may, 28 y 29-jul, 30-ago, 8-oct, 1-nov, 8-dic y 25-dic. Las fechas móviles, como Semana Santa, no están.

**Generador perturbado:** volatilidad ×1,5, ingreso ×0,8, mezcla 15 / 15 / 30 / 35 / 5 % y semilla + 1 000 (20262114).

## Realismo

Cifras de `datos.verificar()`, ejecutado el 14-nov sobre las 400 personas con la semilla 20261114 (también en
`data/REPORTE_DATOS.md`). Se excluyen los duplicados inyectados.

| Medida | Sintético | Referencia | Lectura |
|---|---|---|---|
| Ingreso mensual medio por persona | S/1 944,1 (mediana S/1 882,5) | INEI: S/1 887 **[por verificar en su fuente]** (`docs/fuentes_verificadas.md`, Alberto) | Razón 1,03 |
| Personas con al menos un mes en déficit (gasto > ingreso) en el año 2 | 81,0 % | SBS: 85 % **[por verificar en su fuente]** | 4 puntos por debajo |
| Lo mismo en el generador perturbado | S/1 479,9 (razón 0,78) y 95,8 % | — | Escenario más duro, a propósito |

**Por arquetipo, según el arquetipo de la primera fila:**

| Arquetipo | Personas | Ingreso mensual medio | % con algún mes en déficit |
|---|---|---|---|
| conductor | 86 | S/1 987,6 | 72,1 % |
| vendedora | 111 | S/2 082,5 | 80,2 % |
| tecnico | 83 | S/1 985,9 | 100,0 % |
| comisionista | 79 | S/1 653,0 | 91,1 % |
| asalariado | 41 | S/1 953,9 | 43,9 % |

El asalariado tiene menos déficit, como corresponde a un grupo de control. El técnico, con meses sin cobro, llega
al 100 %. Las referencias del INEI y la SBS describen poblaciones reales distintas de la nuestra, así que sirven
para comprobar el orden de magnitud y no son un objetivo a calzar.

### Qué NO se modela

- Sobregiro, líneas de crédito, préstamos nuevos ni intereses: el saldo puede quedar negativo sin consecuencias.
- Transferencias entre cuentas propias, efectivo fuera de la cuenta, reembolsos o devoluciones.
- Impuestos, inflación, cambios de precio de los servicios y otras monedas.
- Feriados móviles, choques macroeconómicos y correlación entre personas: cada persona es independiente.
- Hogares, dependientes y cualquier variable demográfica (edad, género, ubicación). No existen en los datos.
- Días sin ningún registro como escenario explícito: hoy solo faltan los días sin gasto discrecional (12 %) o sin
  ingreso (ver `docs/datos.md`, desviaciones).

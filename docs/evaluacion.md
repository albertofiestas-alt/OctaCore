# Evaluación

Dueños: Rafael (sesgos, datos y este documento) y Gino (simulación, métricas, frontera, pares de semillas, regla de
adopción). `python tareas.py eval` → `eval/correr.py` produce la tabla de resultados y su hash.

**Estado:** esqueleto. Toda tabla dice **[por medir]** hasta que `eval/correr.py` la produzca con la semilla
20261114. Este documento no contiene ninguna cifra de resultados.

## 1. Escalera de comparación

| Escalón | Método | Dónde |
|---|---|---|
| 1 | Regla ingenua: ingreso de los últimos 90 días / 3 / 30 × h, con factores 0,5 / 0,75 / 1 / 1 para P5 / P20 / P50 / P80 | `src/reglas` (`regla1`) |
| 2 | Regla robusta: percentiles 5, 20, 50 y 80 de las sumas móviles de h días en las últimas 8 semanas; con menos de 63 días de historia usa la regla 1 | `src/reglas` (`regla2`) |
| 3 | Modelo de cuantiles (LightGBM) | `src/modelo` (Gino) |

Nos quedamos con el escalón más simple que cumpla el criterio de éxito.

## 2. Método: simulación de la decisión

La simulación es de Gino (`eval/simular.py`); aquí solo se describe según el plan v9. Para cada persona de **prueba**
(20 %, nunca vista en el entrenamiento) y cada día de los meses 21 a 24:

1. Se arma el estado con lo que se sabía ese día, **sin mirar el futuro**.
2. El método da el pronóstico y el motor, el número de hoy.
3. La persona gasta exactamente ese número **[SUPUESTO]**: el gasto discrecional observado se reemplaza por el permitido.
4. El saldo avanza con los ingresos y pagos reales.
5. Un pago con fecha queda **descubierto** si el saldo es menor que cero el día del pago.

Los pagos con fecha de la simulación son los que **infiere la ingesta** con el historial anterior, no la etiqueta
`pago_con_fecha` (ver `docs/datos.md`). El modelo se entrena solo con personas de entrenamiento y meses 1–16, y se
calibra con los meses 17–20.

### Supuestos

- [SUPUESTO] La persona gasta exactamente el número de hoy.
- [SUPUESTO] Los pagos inferidos se re-infieren cada mes.
- Del pre-registro (`config/preregistro.yaml`, fijado antes de medir): cuantil conservador P20, colchón S/0 y 4
  semanas mínimas de historia.
- Los datos son sintéticos: ver "Alcance honesto" en `docs/datos.md`.

## 3. Métricas

| Métrica | Definición | Dónde |
|---|---|---|
| Pagos descubiertos | descubiertos / pagos con fecha totales | `eval/frontera.py` |
| Gasto permitido | Promedio por persona del gasto permitido por día | `eval/frontera.py` |
| MAE de la mediana | media de \|y − P50\| del ingreso acumulado | `eval/metricas.py` |
| Pinball por cuantil | media de max(τ(y − q), (τ − 1)(y − q)) | `eval/metricas.py` |
| Calibración del P20 | Fracción de casos con y ≥ P20; debería rondar 0,80 | `eval/metricas.py` |

No se usa MAPE, porque se rompe con semanas de ingreso cero.

## 4. Regla de adopción (fijada antes de medir)

El modelo se adopta **solo si gana a la regla robusta en la prueba Y en el generador perturbado**:
- a igual porcentaje de pagos descubiertos que la regla 2 en P20, permite al menos `umbral_adopcion_mejora` = S/2,0
  por día más de gasto (`config/preregistro.yaml`);
- o, a igual gasto, deja menos pagos descubiertos.

Si no gana en los dos conjuntos, se presenta la regla robusta y se dice. Implementación: `eval/adopcion.py` (Gino).

## 5. Resultados

### Frontera de seguridad (prueba | perturbado)

| Método | Cuantil | % descubiertos (prueba) | Gasto/día (prueba) | % descubiertos (perturbado) | Gasto/día (perturbado) |
|---|---|---|---|---|---|
| regla1 | P5 / P20 / P50 / P80 | [por medir] | [por medir] | [por medir] | [por medir] |
| regla2 | P5 / P20 / P50 / P80 | [por medir] | [por medir] | [por medir] | [por medir] |
| modelo | P5 / P20 / P50 / P80 | [por medir] | [por medir] | [por medir] | [por medir] |
| gasto cero | — | [por medir] | [por medir] | [por medir] | [por medir] |
| gasto fijo promedio | — | [por medir] | [por medir] | [por medir] | [por medir] |

### Pares de semillas (modelo − regla 2, 20 semillas, bootstrap con 2 000 remuestreos, IC 95 %)

| Métrica | Diferencia media | IC 95 % |
|---|---|---|
| % descubiertos | [por medir] | [por medir] |
| Gasto permitido por día | [por medir] | [por medir] |

### Métricas del pronóstico (prueba)

| Método | MAE P50 (h = 3 / 7 / 14) | Pinball medio | Calibración P20 |
|---|---|---|---|
| regla1 | [por medir] | [por medir] | [por medir] |
| regla2 | [por medir] | [por medir] | [por medir] |
| modelo | [por medir] | [por medir] | [por medir] |

**Hash de la tabla de resultados:** [por medir]. Con la misma semilla debe salir el mismo hash.

## 6. Sesgos por grupo

Implementación: `eval/sesgos.py` (Rafael). Salida: `eval/resultados/sesgos.csv`.

- **Grupos.** Se calculan solo con los datos y sus etiquetas (es evaluación):
  - arquetipo inicial;
  - tercil de ingreso mensual;
  - tercil de volatilidad (coeficiente de variación del ingreso semanal, solo con semanas completas);
  - cambio de patrón (sí o no).

  Ingreso y volatilidad se miden en los meses 1–20, antes de la prueba, para que el grupo no dependa del resultado
  que se evalúa [SUPUESTO]. Los duplicados y atípicos inyectados no cuentan.
- **Por método, cuantil y grupo:**
  - n de personas;
  - % de pagos descubiertos (suma de descubiertos / suma de totales);
  - gasto permitido medio;
  - calibración del P20, si la simulación la entrega.
- **Brecha:** máximo − mínimo entre los grupos con n > 0 de cada dimensión. Un grupo vacío no cuenta.
- **Alerta:** se dispara si la brecha de una métrica en fracción (% descubiertos o calibración) supera
  `umbral_alerta_sesgo` = 0,05 (`config/preregistro.yaml`). La brecha de gasto, en soles por día, se reporta sin
  alerta [SUPUESTO].
- `resumen_sesgos()` devuelve el peor grupo por dimensión: el de mayor % de descubiertos, y en caso de empate, el de
  menor gasto.

**Límite conocido del indicador de volatilidad.** En los datos de evaluación, 40 de los 41 asalariados caen en el
tercil "alto" de volatilidad (medido el 14-nov). El sueldo quincenal produce semanas con pago y semanas en cero, y el
coeficiente de variación semanal lo cuenta como volatilidad aunque el ingreso sea predecible. La lectura correcta es
"irregularidad semanal", no "riesgo".

| Dimensión | Peor grupo | % descubiertos | Brecha | Alerta |
|---|---|---|---|---|
| Arquetipo | [por medir] | [por medir] | [por medir] | [por medir] |
| Tercil de ingreso | [por medir] | [por medir] | [por medir] | [por medir] |
| Tercil de volatilidad | [por medir] | [por medir] | [por medir] | [por medir] |
| Cambio de patrón | [por medir] | [por medir] | [por medir] | [por medir] |

`eval/resultados/sesgos_demo.csv` tiene resultados **FALSOS** (columna `origen` = `[DEMO]`) y solo sirve para
maquetar la pantalla. No es evidencia.

## 7. Ejemplos de error (al menos tres)

Formato de cada caso, tomado de la prueba con su desglose:

| Campo | Contenido |
|---|---|
| Persona y fecha | `P0xxx`, AAAA-MM-DD [por medir] |
| Qué predijo | Pronóstico (P20 a h días) y número de hoy [por medir] |
| Qué pasó | Ingreso y pagos reales; si quedó un pago descubierto [por medir] |
| Por qué | Causa (por ejemplo, un cambio de patrón o un mes sin cobro del técnico) [por medir] |
| Qué límite revela | Qué no ve el método y qué haríamos [por medir] |

1. [por medir]
2. [por medir]
3. [por medir]

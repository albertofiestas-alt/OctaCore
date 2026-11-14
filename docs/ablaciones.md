# Ablaciones del modelo de cuantiles: qué variable aporta y cuál no

Autor: Gino (por delegación; `eval/ablaciones.py`, Rafael puede reemplazarlo). **1 semilla** (la del pre-registro, 1), generador 1.1 (hash 736316b2c4ad9b5c), simulador de **RESPALDO**. Protocolo igual al de la frontera: se entrena sin la variable con personas de entrenamiento, meses 1-16, calibrado con los meses 17-20, y se mide en la prueba (meses 21-24). Pre-registro y regla de adopción sin tocar.

## Resultado (variante menos modelo completo)
Modelo completo: pinball a 14 días en P20 = 110,08; 9,51 % de pagos descubiertos; gasto S/ 34,37 por día.

| Se quita | Δ pinball (+ = la variable ayuda) | Δ descubiertos (pp) | Δ gasto (S/día) |
|---|---|---|---|
| n_ingresos_28d | **+3,12** | +0,33 | -0,15 |
| ingreso_28d | **+2,92** | +0,05 | -0,05 |
| dias_desde_ultimo_ingreso | **+2,92** | -0,22 | -0,11 |
| ingreso_56d | +1,28 | 0,00 | +0,01 |
| dia_mes | +0,92 | +0,16 | -0,03 |
| mes_cos / mes_sin | +0,12 / +0,07 | -0,05 / 0,00 | -0,05 / -0,01 |
| dia_semana | -0,19 | 0,00 | -0,01 |
| mediana_ingreso_dia_28d | **-1,07** | 0,00 | -0,02 |
| las 5 de historia (queda el calendario) | **+33,21** | +0,55 | -0,62 |
| regla2 (sin modelo), referencia | -0,62 | -0,82 | -0,24 |

## Qué se ve
- **Ayudan** las variables de ingreso reciente: número de ingresos en 28 días, ingreso de 28 días y días desde el último ingreso (cada una ~3 puntos de pinball, ~3 %), luego el ingreso de 56 días y el día del mes. Todas juntas pesan mucho: sin las 5 de historia el pinball empeora 33 (+30 %).
- **Estorban**: `mediana_ingreso_dia_28d` (sin ella el pinball mejora 1,07) y, apenas, `dia_semana`. Mes (seno y coseno) es neutro. En estos datos el calendario no aporta.
- **Descubiertos y gasto**: los cambios son de ±0,3 pp y ±0,15 S/día. Un solo pago descubierto pesa 0,055 pp (1 de 1 820 pagos), así que con una semilla y 80 personas **no se distinguen del ruido**; el pinball es la medida útil aquí.

## Por qué el modelo no supera a regla2 (honestamente)
Con 1 semilla el modelo completo no mejora a regla2: pinball 110,08 contra 109,46, 9,51 % contra 8,68 % de descubiertos y S/ 34,37 contra S/ 34,12 de gasto. Las ablaciones explican la causa probable: casi toda la señal está en el ingreso reciente, y esa información regla2 ya la usa directamente (percentiles empíricos de las ventanas de 8 semanas); lo que el modelo agrega (día de la semana, mes, mediana diaria) no aporta o estorba en estos datos. Con menos señal nueva y más variables que añaden ruido, el modelo no tiene de dónde ganarle. No se cambió el modelo ni el pre-registro tras ver esto.

**Límites:** una sola semilla (falta intervalo); el entrenamiento y la medición usan ventanas con las copias duplicadas sin quitar; todo con el simulador de respaldo y el generador 1.1; las diferencias de ~1 punto de pinball pueden ser ruido.

## Cómo reproducirlo
```
python -m datos --salida data/generado/v11
PYTHONPATH=src python eval/ablaciones.py data/generado/v11 8     # ~12 min; escribe eval/resultados/ablaciones.csv y ablaciones_absolutos.csv
```

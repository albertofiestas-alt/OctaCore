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

## Qué se midió (y nada más)
- **El ingreso reciente ayuda.** Quitar el número de ingresos en 28 días, el ingreso de 28 días o los días desde el último ingreso empeora el pinball en ~3 puntos (~3 %); quitar el ingreso de 56 días, 1,3; el día del mes, 0,9. Quitar las 5 variables de historia a la vez lo empeora 33 (+30 %).
- **Estorban o son neutras:** quitar `mediana_ingreso_dia_28d` mejora el pinball en 1,07 y quitar `dia_semana`, en 0,19 (estorban); mes (seno y coseno) cambia ≤ 0,12 (neutro).
- **Descubiertos y gasto no se distinguen del ruido con 1 semilla:** los cambios son de ±0,3 pp y ±0,15 S/día, y un solo pago descubierto pesa 0,055 pp (1 de 1 820 pagos). **El pinball es la medida útil aquí**, y aun así una diferencia de ~1 punto con 1 semilla no es concluyente.
- **regla2 no es peor que el modelo completo** en estas medidas: pinball 109,46 contra 110,08, 8,68 % contra 9,51 % de descubiertos y S/ 34,12 contra S/ 34,37 de gasto.

No se midió **por qué** el modelo no supera a regla2: las ablaciones no lo prueban. Esto es coherente con los pares de semillas (fila 32 de `DECISIONES.md`), no una explicación de ellos.

No se cambió el modelo tras verlo; quitar `mediana_ingreso_dia_28d` sería un cambio posterior al pre-registro.

**Límites:** una sola semilla (falta intervalo); el entrenamiento y la medición usan ventanas con las copias duplicadas sin quitar; todo con el simulador de respaldo y el generador 1.1.

## Cómo reproducirlo
```
python -m datos --salida data/generado/v11
PYTHONPATH=src python eval/ablaciones.py data/generado/v11 8     # ~12 min; escribe eval/resultados/ablaciones.csv y ablaciones_absolutos.csv
```

# Diagnóstico: por qué los asalariados caen en rojo en la serie diaria

Autor: Gino (sesión de modelo). Solo lectura: no cambia series, pre-registro ni código del motor.
Origen de las cifras: simulador de **RESPALDO** (`eval/_simulador_respaldo.py`), solo regla2 al P20, 46 asalariados, 2026-01-01 a 2026-12-31 (meses 13 a 24), dataset del **generador 1.0** (`hash_completo` 30d573b1523a4d24; en `main` ya hay generador 1.1 y estas cifras hay que repetirlas con él).

## Qué se vio
- Los asalariados pasan una **mediana de 63,5 días al año en rojo** (mín 3, máx 251); 3 402 de 16 790 persona-días = 20,3 %.
- **Sin gastar el número de hoy** (misma regla2, mismos pagos) la mediana de rojo es **0 y el verde es 365 de 365 días**. Gastándolo, el saldo mediano baja de unos 6 400 (enero) a unos 500 desde marzo; sin gastar sube a 17 600 en diciembre.
- El saldo inicial **no** es bajo: al 1-ene-2026 media 7 014, mediana 6 745, mínimo -576.
- Pago que limita en los días rojo: servicios 65 %, alquiler 18 %, deuda 13 %, suscripción 3 %; mediana S/ 90, a 11 días (p25-p75: 9-13). Pagos acumulados hasta ese día: S/ 531 (mediana) contra un saldo mediano de S/ 340; falta con P50 una mediana de S/ 133 (p25 56, p75 272). El 95 % de los rojos tiene saldo positivo.
- El sueldo es quincenal (días 15 y fin de mes, ~S/ 650): las ventanas de 3 y 7 días lo contienen en ~20 % y ~47 %. En los días rojo **p50 a 3 días = 0 en 96 %** y **p50 a 7 días = 0 en 90 %**; el 99,8 % de los rojos tiene el pago limitante a menos de 14 días, o sea sin ningún ingreso contado, ni con P50.
- El 96,3 % de los rojos tiene un sueldo real que llega antes del pago limitante y en el 93,4 % ese sueldo cubre la falta (cota superior: usa lo que de hecho llegó).

## Cinco casos (día en rojo, gastando el número; entre paréntesis, ese mismo día sin gastar)
| Persona | Fecha | Saldo | Limita | Falta P50 | p5/p50 h3 · h7 · h14 | Sueldo antes del pago |
|---|---|---|---|---|---|---|
| P0140 (10 días rojo) | 2026-08-31 | 479 (18 813, verde) | servicios 63 a 12 d | 14 | 0/0 · 0/0 · 0/927 | 941 |
| P0156 (38) | 2026-06-30 | 653 (11 162, verde) | servicios 78 a 12 d | 134 | 0/0 · 0/0 · 0/952 | 983 |
| P0001 (64) | 2026-08-24 | 351 (12 089, verde) | alquiler 420 a 10 d | 69 | 0/0 · 0/0 · 0/656 | 673 |
| P0356 (137) | 2026-08-25 | 195 (6 879, verde) | alquiler 350 a 11 d | 155 | 0/0 · 0/0 · 0/626 | 602 |
| P0384 (251) | 2026-07-03 | 810 (4 584, verde) | servicios 40 a 8 d (acumulado 1 077) | 267 | 0/0 · 0/0 · 0/686 | 0 |

## Hipótesis
No es el generador (saldo alto, sueldo regular), no es un error del simulador de respaldo (aplica la fórmula del plan; con gasto 0 da verde todo el año; contra `motor.decidir` oficial coincide al 100 % con el mismo estado) y la regla2 hace lo que debe: dice que no sabe cuándo cae el cobro. Es el **diseño**, en dos partes: (a) el número de hoy y el semáforo solo cuentan ingreso por cuantiles de ventanas de 3, 7 y 14 días, sin calendario de sueldo ni ingreso fijo inferido, así que para pagos a menos de 14 días el ingreso contado es ~0; (b) quien gasta todo lo permitido (calculado con P20) queda por construcción al borde, y "verde" exige cubrir con P5, más exigente que el P20 del gasto. Por eso "verde sostenido" es casi imposible para quien sigue el número, aunque tenga sueldo fijo y colchón alto. Cambiar el diseño (por ejemplo contar ingresos recurrentes inferidos) lo decide Gino/Sebastián; aquí no se tocó ningún umbral.

## Cómo reproducirlo
```
python -m datos --salida data/generado          # dataset (generador de la rama)
PYTHONPATH=src python eval/_diagnostico_asalariados.py data/generado/generado/movimientos.csv 8
```
Imprime el resumen y los 5 casos de arriba (≈ 5 min con 8 procesos); no escribe archivos.

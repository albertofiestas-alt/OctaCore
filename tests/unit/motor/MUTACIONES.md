# Pruebas de mutación del motor

Una **mutación** es un error pequeño metido a propósito en el motor (el tipo de error que comete un
programador: `<=` por `<`, `floor` por `round`, olvidar un término). Si alguna prueba falla, la mutación
queda **detectada**. Si todas pasan, **sobrevive**: o hay un hueco en las pruebas o la mutación es
**equivalente** (no cambia nada observable).

Criterio del plan de Sebastián (secciones 9 a 11): al menos 6 de 8 mutaciones detectadas y las demás explicadas.

## Resultado

**25 de 26 detectadas.** Las 25 no equivalentes quedan detectadas; la que sobrevive (M12) es equivalente.
En la primera corrida sobrevivían 3 (M15, M17 y M18). Las 3 eran fronteras exactas que ninguna prueba
tocaba, y ahora las cubren las pruebas nuevas de `test_mutaciones_detectadas.py`.

Tiempo: unos 3 minutos con 6 procesos en paralelo (línea base de 85 s + mutaciones; una mutación detectada
tarda entre 5 y 8 s gracias a `-x`, y una que sobrevive tarda unos 90 s porque corre las propiedades completas).

| Id | Categoría | Mutación (qué cambia) | Resultado | Detectada por |
|---|---|---|---|---|
| M01 | fórmula | pagos acumulados `p.dia <= d` -> `p.dia < d` (el pago del mismo día no cuenta) | detectada | test_decidir.py::test_numerador_y_permitido_caso_tipico |
| M02 | fórmula | se olvida el colchón en el numerador | detectada | test_decidir.py::test_numerador_y_permitido_caso_tipico |
| M03 | fórmula | divisor `max(d, 1)` -> `max(d, 2)` | detectada | test_decidir.py::test_pago_dia_cero_y_dos_pagos_mismo_dia |
| M04 | fórmula | puntos de control sin el día 14 | detectada | test_decidir.py::test_puntos_de_control_agrupa_dias_y_agrega_el_14 |
| M05 | fórmula | punto que limita `min(...)` -> `max(...)` | detectada | test_decidir.py::test_proponer_caso_tipico |
| M06 | fórmula | `h <= min(d, 14)` -> `h < min(d, 14)` en `_h_para_dia` | detectada | test_decidir.py::test_ingreso_conservador_usa_el_mayor_horizonte_menor_o_igual |
| M07 | fórmula | empate entre días elige el día mayor | detectada | test_decidir.py::test_empate_elige_el_dia_menor |
| M08 | redondeo | número de hoy `floor` -> `ceil` | detectada | test_decidir.py::test_pago_dia_cero_y_dos_pagos_mismo_dia |
| M09 | redondeo | número de hoy `floor` -> `round` | detectada | test_decidir.py::test_redondeo_hacia_abajo_45_9 |
| M10 | redondeo | faltante `ceil` -> `floor` | detectada | test_decidir.py::test_faltante_hacia_arriba |
| M11 | redondeo | faltante si `minimo <= 0` en vez de `< 0` ("faltan S/0") | detectada | test_decidir.py::test_pago_justo_cubierto_verde |
| M12 | redondeo | `floor(max(0, m))` -> `max(0, floor(m))` | **sobrevive (equivalente)** | ver explicación |
| M13 | semáforo | verde con P20 en vez de P5 | detectada | test_decidir.py::test_semaforo_verde_ambar_rojo |
| M14 | semáforo | verde `>= 0` -> `> 0` | detectada | test_decidir.py::test_semaforo_no_descuenta_colchon |
| M15 | semáforo | ámbar `>= 0` -> `> 0` | detectada (prueba nueva) | test_mutaciones_detectadas.py::test_m15_ambar_si_cubre_justo_en_p50 |
| M16 | semáforo | el semáforo descuenta el colchón | detectada | test_decidir.py::test_semaforo_no_descuenta_colchon |
| M17 | confianza | `ancho > ancho_bajo` -> `>=` (frontera 1.2) | detectada (prueba nueva) | test_mutaciones_detectadas.py::test_m17_ancho_igual_al_umbral_bajo_es_media |
| M18 | confianza | `ancho < ancho_alto` -> `<=` (frontera 0.5) | detectada (prueba nueva) | test_mutaciones_detectadas.py::test_m18_ancho_igual_al_umbral_alto_es_media |
| M19 | confianza | historia `>= umbral` -> `> umbral` (4 semanas exactas) | detectada | test_estres.py::test_historia_corta_confianza_baja_sin_propuesta[4-alta-1]; también test_mutaciones_detectadas.py::test_m19_... |
| M20 | propuesta | propone aunque no haya historia suficiente | detectada | test_decidir.py::test_poca_historia_confianza_baja_sin_propuestas |
| M21 | propuesta | la propuesta usa P20 en vez de P5 | detectada | test_decidir.py::test_proponer_caso_tipico |
| M22 | propuesta | g5 `floor` -> `round` (deja de cubrir en P5; salta el assert del verificador) | detectada | test_decidir.py::test_proponer_caso_tipico |
| M23 | propuesta | `g5 < numero_hoy` -> `<=` (propone apartar S/0) | detectada | test_decidir.py::test_proponer_g5_negativo_o_suficiente_no_propone |
| M24 | simulación | ingresos extra sumados todos los días sin mirar su día | detectada | test_estres.py::test_simular_ingreso_extra_dia_cero_y_catorce (y test_simular.py::test_ingreso_extra_solo_cuenta_desde_su_dia) |
| M25 | simulación | `gasto_hoy` se suma al saldo en vez de restarse | detectada | test_estres.py::test_simular_gasto_hoy_enorme (y test_simular.py::test_gasto_hoy_baja_el_numero) |
| M26 | simulación | escenario con solo `gasto_hoy` tratado como vacío (`and` -> `or`) | detectada | test_estres.py::test_simular_gasto_hoy_enorme (y test_simular.py::test_gasto_hoy_baja_el_numero) |

"Detectada por" es la **primera** prueba que falla (se corre con `-x`). Otras pruebas pueden matar la misma
mutación; entre paréntesis van las que también la matan según el cálculo a mano.

## Mutaciones que sobrevivían y cómo se cerraron

- **M15 (ámbar `>=` -> `>`).** Ninguna prueba tenía un pago cubierto *justo* en P50. Caso nuevo: saldo 100,
  pago de 150 el día 7, P50 a 7 días = 50 -> 100 + 50 - 150 = 0, así que es ámbar. La mutación lo pone rojo.
- **M17 (`ancho > 1.2` -> `>=`).** Ninguna prueba tenía un ancho de exactamente 1.2. Caso nuevo: P5 0, P50 100,
  P80 120 -> (120 - 0) / 100 = 1.2, así que la confianza es media. La mutación da baja.
- **M18 (`ancho < 0.5` -> `<=`).** Caso nuevo: P5 50, P50 100, P80 100 -> 0.5, así que es media. La mutación da alta.
- **M19** ya la mataba `test_estres.py` (4 semanas). Como esa prueba es de otro frente, se agregó
  `test_m19_cuatro_semanas_exactas_es_historia_suficiente` para que la detección no dependa de ella.

## Mutación equivalente

- **M12** cambia `int(floor(max(0.0, m)))` por `max(0, int(floor(m)))`. Si m >= 0, las dos dan floor(m). Si
  m < 0, la primera da floor(0) = 0 y la segunda da max(0, negativo) = 0. El resultado es el mismo para todo m
  finito, así que ninguna prueba puede distinguirlas. Está en el catálogo para mostrar que el ejecutor no
  marca como detectada cualquier mutación: este refactor sobrevive, como debe.

## Cómo repetirlo

```bash
.venv/Scripts/python.exe tests/unit/motor/mutaciones.py              # todas (sale 0 si >= 6 detectadas)
.venv/Scripts/python.exe tests/unit/motor/mutaciones.py M15 M17      # solo algunas
.venv/Scripts/python.exe tests/unit/motor/mutaciones.py --lista      # catálogo
```

El ejecutor copia `src/`, `config/`, `pyproject.toml`, `tests/conftest.py`, `tests/fixtures`, `tests/unit/motor`
y `tests/property` a un directorio temporal. Ahí aplica una sustitución exacta (falla si el texto no aparece
exactamente una vez), comprueba que `import motor` resuelve a la copia (el venv tiene un `.pth` editable al src
real) y corre `python -m pytest tests/unit/motor tests/property -x -q -p no:cacheprovider`. Antes corre la copia
sin mutación: si esa copia ya falla, aborta. Los archivos reales de `src/motor` nunca se modifican.

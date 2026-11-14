# DECISIONES

Cada decisión importante: qué se decidió, el dato que la respalda, qué decidimos y qué haríamos distinto.
Las alternativas rechazadas con datos también se anotan. Los cambios a la v5 los aprueba Gino.

| # | Fecha y hora | Decisión | Dato que la respalda | Qué decidimos | Qué haríamos distinto | Aprobó |
|---|---|---|---|---|---|---|
| 1 | 14-nov 10:30 | Python 3.11 para todo el equipo | Versión instalada en la laptop de Anderson; sección 10: "la que ya tenga la mayoría" **[confirmar con el equipo]** | `requires-python` 3.11 y prueba de entorno que lo verifica | — | Anderson |
| 2 | 14-nov 10:30 | pandas 2.3.3 en vez de 3.x | pandas 3 cambia el tipo de texto por defecto y copy-on-write; riesgo de romper código a mitad del evento | Versiones fijadas en requirements.txt | Migrar a pandas 3 después del evento | Anderson |
| 3 | 14-nov 10:30 | Comandos en `tareas.py` además del Makefile | `make` no viene instalado en Windows | `python tareas.py <setup\|datos\|test\|eval\|demo>`; el Makefile delega | — | Anderson |
| 4 | 14-nov 10:30 | Contrato `PagoInferido` (customer_id, comercio, categoria, monto, dia_mes) para `ReporteCalidad.pagos_inferidos` | El Anexo A solo decía `list`; `PagoConFecha.dia` depende de una fecha de corte que la ingesta no conoce | La ingesta devuelve `PagoInferido`; el servicio lo convierte a `PagoConFecha` | — | Anderson **[falta Gino]** |
| 5 | 14-nov 10:30 | `historia` y `movimientos_limpios` son un `pandas.DataFrame` con las columnas del contrato, sin etiquetas de referencia | El Anexo A no fijaba el tipo; con 400 personas y 24 meses, validar fila a fila con pydantic es lento | `contratos.validar_historia(df)` comprueba columnas, tipos y la regla anti fuga | — | Anderson **[falta Gino]** |
| 6 | 14-nov 10:30 | `Propuesta.confianza` usa los mismos valores que `Decision.confianza` (alta, media, baja) | El Anexo A decía `str` | Literal cerrado | — | Anderson **[falta Gino]** |
| 7 | 14-nov 10:30 | Parámetro `ventana_dias: 14` en config.yaml | La ventana de 14 días del número de hoy no estaba en el Anexo B | Se lee de la config, no del código | — | Anderson **[falta Gino]** |
| 8 | 14-nov 10:30 | El contrato rechaza ingresos con monto negativo, gastos con monto positivo y valores NaN o infinitos | Sección 6: positivo para ingresos, negativo para gastos | Validación en `Movimiento` y en todos los contratos | — | Anderson |

## Por fijar antes de ver resultados

- `colchon` (config.yaml)
- `umbrales_confianza` (config.yaml)
- Umbral numérico de la regla de adopción (README)

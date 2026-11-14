# Arquitectura

Dueño: Anderson. Se completa con el diagrama final, tiempos medidos y salvaguardas antes del domingo.

## Capas y contratos

```
generador (datos)                 -> data/*.csv                          contrato de datos, sección 6
ingesta.cargar(origen, cfg)       -> (DataFrame limpio, ReporteCalidad, pagos_inferidos)
ingesta.proximos_pagos(...)       -> list[PagoConFecha]       ingesta.semanas_historia(...) -> int
reglas.regla1/regla2(historia, fecha, cfg)      -> Pronostico
Modelo.predecir(historia, fecha)                -> Pronostico   {3|7|14: {p5, p20, p50, p80}}, ordenado, >= 0
motor.decidir(estado, pronostico, cfg)          -> Decision
servicio.cargar_archivo(origen)                 -> ReporteCalidad
servicio.consultar(customer_id, fecha, metodo)  -> Decision + línea en registros/recomendaciones.jsonl
servicio.responder(propuesta_id, accion)        -> dict + línea en registros/respuestas.jsonl
servicio.salud()                                -> p50, p95, tasa_error, tasa_respaldo (logs/salud.jsonl)
servicio.auditar(registro_id)                   -> entradas, decisión, hashes y si se reproduce
app -> solo servicio (y contratos); nunca modelo, motor, ingesta, reglas ni datos
```

Modelos pydantic: [src/contratos/modelos.py](../src/contratos/modelos.py). Firmas: [src/contratos/firmas.py](../src/contratos/firmas.py). Configuración: [src/contratos/config.py](../src/contratos/config.py).

## Flujo de una consulta

1. **Datos activos**: el último archivo cargado con `cargar_archivo`; si no hay, el primero que exista de `rutas_datos` (`data/generado/movimientos.csv`, luego `data/muestra/movimientos.csv`).
2. **Historia**: movimientos limpios de la persona **anteriores** a la fecha de corte (nunca del mismo día ni posteriores), ordenados, validados con `validar_historia` (regla anti fuga).
3. **Estado**: saldo (último informado o suma de montos), pagos con fecha de los próximos `ventana_dias`, colchón y semanas de historia.
4. **Pronóstico con escalera de respaldo**: `modelo → regla2 → regla1`. Se baja un escalón si el método falla por cualquier motivo (no implementado, `HistoriaInsuficiente`, sin modelo entrenado en `ruta_modelo`, o `eval/resultados/adopcion.json` dice `adopta: false`). Sin `adopcion.json` todavía no hay veredicto y se intenta el modelo.
5. **Decisión**: `motor.decidir`. El servicio agrega `respaldo` (método usado distinto del pedido) y `registro_id`.
6. **Registro**: una línea JSON con `registro_id`, entradas (persona, fecha, método pedido y usado, motivos del respaldo, origen de datos, hash de la historia), versiones, semilla, hash de la configuración y la decisión completa.
7. **Salud**: una línea en `logs/salud.jsonl` con operación, latencia, método, respaldo y error, también cuando la consulta falla.

`auditar` repite los pasos 2 a 5 con las entradas guardadas y compara: misma configuración, mismos datos (hash de la historia), mismo método y misma decisión campo por campo.

## Configuración

`config/base.yaml` (Anexo B, validado con pydantic) más un archivo por dueño (`config/ingesta.yaml` → `cfg["ingesta"]`, etc.). El resultado es un dict de solo lectura que también admite `cfg.clave`; `cfg.con(...)` devuelve una copia con cambios. `hash_config(cfg)` es estable y va en cada registro. La capa generativa nace apagada y la configuración se niega a cargar si alguien la enciende sin pasar por DECISIONES.md.

## Salvaguardas ya aplicadas

- Contratos inmutables, sin campos extra, sin NaN ni infinito; cuantiles ordenados y no negativos.
- Regla anti fuga: `validar_historia` rechaza cualquier etiqueta de referencia; la historia nunca incluye la fecha de corte ni el futuro.
- La app no puede importar capas internas (prueba de contrato, también con el prefijo `src.`).
- Firmas fijas desde V0: `tests/contract/test_firmas.py` falla si cambian.
- Configuración fuera del código y de solo lectura, con hash estable para el registro.
- Modo de respaldo visible (`Decision.respaldo`) y errores con mensaje para la persona (`ErrorServicio.mensaje_usuario`).
- Nada se ejecuta: `responder` solo anota la decisión de la persona.
- Trazabilidad: `scripts/auditar_recomendacion.py <registro_id>`.
- `.env`, `registros/`, `logs/` y `data/generado/` fuera del repositorio; el MVP no necesita claves ni red.
- Pruebas automáticas en cada pull request (`.github/workflows/test.yml`).

## Pendiente (Anderson)

- Diagrama alineado con la arquitectura de referencia del Challenge pack.
- e2e con Streamlit AppTest cuando existan las pantallas.
- Determinismo con distintos `PYTHONHASHSEED`, mutaciones del motor, escala y tiempos (p50/p95 medidos).
- Búsqueda de secretos en el historial y revisión de dependencias y licencias.

# Arquitectura

Dueño: Anderson. Se completa con el diagrama, tiempos medidos y salvaguardas antes del domingo.

## Capas y contratos

```
generador (datos)      -> data/*.csv                       contrato de datos, sección 6
ingesta.cargar(origen) -> (DataFrame limpio, ReporteCalidad, list[PagoInferido])
reglas.regla1/regla2(historia, fecha) -> Pronostico
modelo.predecir(historia, fecha)      -> Pronostico   {3|7|14: {p5, p20, p50, p80}}, ordenado
motor.decidir(estado, pronostico, cfg) -> Decision
servicio.consultar(id, fecha, metodo)  -> Decision + línea en registros/recomendaciones.jsonl
servicio.responder(propuesta_id, accion)
app -> solo servicio (y contratos); nunca modelo, motor ni ingesta
```

Los modelos pydantic están en [src/contratos/modelos.py](../src/contratos/modelos.py); las firmas, en [src/contratos/firmas.py](../src/contratos/firmas.py).

## Salvaguardas ya aplicadas

- Contratos inmutables, sin campos extra, sin NaN ni infinito; cuantiles ordenados obligatorios.
- Regla anti fuga: `validar_historia` rechaza cualquier etiqueta de referencia.
- La app no puede importar capas internas (prueba de contrato).
- Configuración en `config/config.yaml`, con hash estable para el registro.
- `.env` fuera del repositorio; el MVP no necesita claves ni red.

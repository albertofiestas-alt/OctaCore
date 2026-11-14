# OctaCore · ¿Cuánto puedo gastar hoy sin fallar a un pago con fecha?

> Orientación educativa basada en una simulación con datos ficticios. No es asesoría financiera ni ejecuta operaciones.

Hackathon de Ingeniería BBVA · AI Financial Life · 14 y 15 de noviembre de 2026.
El documento fuente es la propuesta v5. Los cambios a la v5 se anotan en [DECISIONES.md](DECISIONES.md).

## Problema, usuario y decisión

| | |
|---|---|
| Usuario | Adulto con ingresos que varían de una semana a otra, con pagos de fecha fija y sin colchón. |
| Decisión que mejoramos | ¿Cuánto puedo gastar hoy sin fallar a un pago con fecha? |
| Criterio de éxito | A igual porcentaje de pagos con fecha descubiertos, el modelo permite más gasto diario que la regla robusta; o a igual gasto, deja menos pagos descubiertos. Debe cumplirse en la prueba y en el generador perturbado. Si no se cumple, se presenta la regla robusta y se dice. |
| Regla de adopción | La misma, con un umbral numérico de mejora **[por fijar antes de correr nada: Gino]**. |

Los datos son sintéticos: lo que se demuestra es que el método recupera estructura conocida, no precisión en el mundo real.

## Ejecutar

Requisito: **Python 3.11** (todo el equipo y el jurado usan la misma versión). No necesita internet después de instalar.

```bash
python tareas.py setup   # crea .venv e instala requirements.txt (en Windows: py -3.11 tareas.py setup)
python tareas.py datos   # genera los datos con la semilla de config/config.yaml
python tareas.py test    # corre todas las pruebas
python tareas.py eval    # tabla de resultados y su hash
python tareas.py demo    # levanta la interfaz en el navegador
```

Con `make` instalado funcionan igual `make setup`, `make datos`, `make test`, `make eval` y `make demo`.

Semilla del generador: `20261114` (en `config/config.yaml`).

## Arquitectura en una línea

`datos → ingesta → (reglas | modelo) → motor → servicio → app`. La app solo llama a `servicio`. Los contratos entre capas están en [src/contratos](src/contratos) y se describen en [docs/arquitectura.md](docs/arquitectura.md).

## Estructura

```
config/config.yaml     parámetros (Anexo B); ningún valor mágico en el código
src/contratos          contratos pydantic (Anexo A)            Anderson
src/datos              generador sintético y muestra           Rafael
src/ingesta            validación, duplicados, pagos inferidos Mathias
src/reglas             regla ingenua y regla robusta           Rafael
src/modelo             cuantiles por horizonte                 Gino
src/motor              número de hoy, semáforo, propuestas     Sebastián
src/servicio           fachada, config, registro, respaldo     Anderson
src/app                pantallas Streamlit                     Jesús, Alberto
eval/                  simulación de la decisión y frontera    Rafael, Gino
tests/                 unit, property, contract, integracion, e2e, fixtures
data/muestra           20 personas, 24 meses (en el repo)      Rafael
data/generado          datos completos (se regeneran, no se suben)
docs/                  datos, evaluación, arquitectura, conversaciones, arranque
```

Para empezar a trabajar: [docs/arranque.md](docs/arranque.md).

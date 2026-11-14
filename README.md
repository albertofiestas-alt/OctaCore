# Ukku (equipo OctaCore) · ¿Cuánto puedo gastar hoy sin fallar a un pago con fecha?

> Orientación educativa basada en una simulación con datos ficticios. No es asesoría financiera ni ejecuta operaciones.

Hackathon de Ingeniería BBVA · AI Financial Life · 14 y 15 de noviembre de 2026.
El documento fuente es la propuesta **v9** ([asignaciones/Resumen_propuesta_hackathon_BBVA_v9.docx](asignaciones/Resumen_propuesta_hackathon_BBVA_v9.docx)). Si algo contradice a la v9, manda la v9. Los cambios los aprueba Gino y se anotan en [DECISIONES.md](DECISIONES.md).

## Lectura de asignaciones

**Paso 0: ¿quién eres?** Antes de tocar código (tú o una herramienta de IA que trabaje contigo), identifica tu persona en la tabla de abajo. Con eso sabes qué plan leer, qué carpetas son tuyas, qué entregas, a qué hora y quién revisa tu pull request. Si trabajas con un asistente de IA, dile primero quién eres.

Orden de lectura:

1. La v7, secciones 1 (propuesta), 8 (arquitectura y contratos), 9 (pruebas), 11 (equipo) y los Anexos A (firmas) y E (trabajo en paralelo con GitHub).
2. Tu plan individual en [asignaciones/](asignaciones/): secciones 3 (primeros pasos), 4 (tareas del Challenge pack), 6 (archivos y código), 8 (horas) y 10 (definición de hecho).
3. [docs/arranque.md](docs/arranque.md) para el entorno y la rama.

| Persona | Rol | Plan individual | Carpetas y archivos propios (Anexo E) | Entregas clave (hora Lima, sábado) | Revisa sus PR |
|---|---|---|---|---|---|
| Anderson | Backend: servicio, integración y calidad | No hay plan individual: v7 §8, §9, §11, Anexos A, B y E | `src/contratos/`, `src/servicio/`, `tests/contract`, `tests/integracion`, `tests/e2e`, `tests/fixtures`, `config/base.yaml`, `requirements.txt`, `Makefile`, `tareas.py`, `pyproject.toml`, `.github/`, `scripts/`, `README.md`, `docs/arquitectura.md` | 10:45 contratos y fixtures · 13:00 `servicio.consultar` con regla 2 (v0-control1) · 16:00–18:00 `logs/salud.jsonl`, `servicio.salud()`, `scripts/auditar_recomendacion.py`, e2e, determinismo, mutaciones, seguridad · cierra las ventanas V0–V4 y pone las etiquetas | Gino (contratos), Sebastián (resto) |
| Rafael | Data science | [Plan_02](asignaciones/Plan_02_Rafael_data_science.docx) | `src/datos/`, `src/reglas/`, `eval/` (menos `adopcion.py`), `data/`, `config/datos.yaml`, `docs/datos.md`, `docs/evaluacion.md`, `docs/diccionario_datos.md` | 11:00 `data/muestra/` (20 personas) · 12:30 datos de 400 personas y regla 2 · 18:30 simulación y frontera · 18:00–19:30 sesgos y diccionario | Gino |
| Mathias | Backend: ingesta y calidad | [Plan_03](asignaciones/Plan_03_Mathias_backend_ingesta_calidad.docx) | `src/ingesta/`, `config/ingesta.yaml`, `tests/unit/ingesta/` | 12:00 ingesta v0 con pagos inferidos · 13:00–16:00 PII y columnas sensibles · fuzz (P1) | Sebastián |
| Sebastián | Backend: motor de decisión | [Plan_04](asignaciones/Plan_04_Sebastian_backend_motor_decision.docx) | `src/motor/`, `config/motor.yaml`, `tests/unit/motor/`, `tests/property/` | 12:30 motor con el caso del orden de pagos · 13:00–16:00 supuestos, evidencia y límites en cada `Decision` · propuesta | Mathias |
| Gino Vieyra | Machine learning y líder | [Plan_05](asignaciones/Plan_05_Gino_machine_learning_y_liderazgo.docx) | `src/modelo/`, `config/modelo.yaml`, `config/preregistro.yaml`, `tests/unit/modelo/`, `eval/adopcion.py`, `docs/responsible_ai.md`, `docs/roadmap.md`, `DECISIONES.md`, `TRANSPARENCIA.md` | 12:00 pre-registro y enfoque cerrado · 15:30 modelo v1 · decisiones en los controles · pitch | Rafael |
| Jesús | Frontend 1: Hoy y Plan | [Plan_06](asignaciones/Plan_06_Jesus_frontend_hoy_y_plan.docx) | `src/app/main.py`, `componentes.py`, `estado.py`, `servicio_falso.py`, `pages/1_Hoy.py`, `pages/2_Plan.py`, `tests/unit/app_hoy_plan/`, `docs/guion_demo.md` | 12:00 maqueta con fixtures · 13:00 Hoy conectada al servicio · 13:00–18:30 supuestos y límites en Hoy, guion de demo | Alberto |
| Alberto | Frontend 2: Por qué y Evaluación | [Plan_07](asignaciones/Plan_07_Alberto_frontend_porque_datos_evidencia.docx) | `src/app/tema.py`, `pages/3_Por_que.py`, `pages/5_Evaluacion.py`, `tests/unit/app_evidencia/`, `tests/a11y/`, `pitch/`, `docs/conversaciones.md`, `docs/fuentes_verificadas.md` | 11:15 `tema.py` · 16:00 Por qué · 16:00–19:30 paneles de sesgos, salud, auditoría y calidad de datos (solo lectura) · deck y video | Jesús |

Ventanas de integración a `main` (Anexo E): **V0 11:00** estructura, contratos, stubs y muestra · **V1 12:00** ingesta, motor, reglas y esqueletos · **V2 13:00** servicio + Hoy (`v0-control1`) · **V3 16:00** modelo v1, propuesta, Por qué y Plan, P0 (`v1-control2`) · **V4 17:45** todo lo que se muestra; 18:00 `v2-congelado` · **Domingo** solo correcciones; 11:00 `v3-final`.

Reglas que aplican a todos: una carpeta, un dueño; nunca `git add .` ni `git add -A`; nunca `push --force` ni subir `.env` o `data/generado`; `requirements.txt` y los contratos solo los cambia Anderson (contratos además con Gino); un PR solo se fusiona con `python tareas.py test` en verde.

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
python tareas.py datos   # genera los datos con la semilla de config/base.yaml
python tareas.py test    # corre todas las pruebas
python tareas.py eval    # tabla de resultados y su hash
python tareas.py demo    # levanta la interfaz en el navegador
python scripts/auditar_recomendacion.py <registro_id>   # reconstruye una recomendación
```

Con `make` instalado funcionan igual `make setup`, `make datos`, `make test`, `make eval` y `make demo`.

Semilla del generador: `20261114` (en `config/base.yaml`).

## Arquitectura en una línea

`datos → ingesta → (modelo | regla 2 | regla 1) → motor → servicio → app`. La app solo llama a `servicio`. Si el modelo no está disponible o no se adoptó, el servicio baja a la regla 2 y lo marca (`Decision.respaldo`). Cada recomendación queda en `registros/recomendaciones.jsonl` con su `registro_id` y cada consulta en `logs/salud.jsonl`. Los contratos entre capas están en [src/contratos](src/contratos) y se describen en [docs/arquitectura.md](docs/arquitectura.md).

## Estructura

```
config/base.yaml       parámetros comunes (Anexo B)                          Anderson
config/<modulo>.yaml   parámetros de cada dueño; se leen como cfg["<modulo>"]  cada dueño
src/contratos          contratos pydantic (Anexo A) y firmas                 Anderson
src/datos              generador sintético y muestra                         Rafael
src/ingesta            validación, duplicados, PII, pagos inferidos          Mathias
src/reglas             regla ingenua y regla robusta                         Rafael
src/modelo             cuantiles por horizonte                               Gino
src/motor              número de hoy, semáforo, propuestas                   Sebastián
src/servicio           fachada, registro, respaldo, salud, auditoría         Anderson
src/app                pantallas Streamlit (1_Hoy, 2_Plan, 3_Por_que,         Jesús, Alberto
                       5_Evaluacion; sin pantalla de carga)
eval/                  simulación de la decisión, frontera, sesgos, adopción Rafael, Gino
scripts/               auditar_recomendacion.py                              Anderson
tests/                 unit/<modulo>, property, contract, integracion, e2e, a11y, fixtures
data/muestra           20 personas, 24 meses (en el repo)                    Rafael
data/generado          datos completos y modelo (se regeneran, no se suben)
registros/, logs/      recomendaciones, respuestas y salud (no se suben)
docs/                  datos, evaluación, arquitectura, conversaciones, arranque
.github/               pruebas automáticas, plantilla de PR, CODEOWNERS      Anderson
```

Para empezar a trabajar: [docs/arranque.md](docs/arranque.md).

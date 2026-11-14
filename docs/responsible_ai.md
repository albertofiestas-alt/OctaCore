# Responsible AI (BORRADOR)

Coordina: Gino. Borrador: cada afirmación cita su evidencia (archivo del repo). Estado: **hecho** = existe hoy en el repo; **pendiente** = lo escribe su dueño, la cifra o la prueba aún no existe. Donde falta un dato va `[por medir]`; no hay cifras inventadas. Datos 100 % sintéticos.

## 1. Explicabilidad

| Afirmación | Evidencia | Estado |
|---|---|---|
| Cada `Decision` trae fundamento, evidencia, supuestos, límites y confianza | `src/contratos/modelos.py`; `tests/contract/test_contratos.py::test_fixtures_de_decision_traen_supuestos_evidencia_y_limites` | hecho (contrato) |
| El número de hoy sale de una fórmula por fecha de pago, no de una caja negra | `docs/arquitectura.md` (flujo de una consulta); `src/motor/` | pendiente: motor (Sebastián) |
| La pantalla "Por qué" muestra esa evidencia | `src/app/` | pendiente (Alberto) |
| Si se usa IA generativa, solo reescribe lo ya calculado y un verificador sin IA exige que cada cifra exista en la entrada | `src/generativa/verificador.py`; `config/base.yaml` (`generativa.activada: false`) | capa apagada; cifras inventadas tras el verificador: [por medir] |

## 2. Privacidad

| Afirmación | Evidencia | Estado |
|---|---|---|
| Los datos son sintéticos: no hay personas reales | `src/datos/generador.py`; `docs/datos.md` | hecho |
| El contrato no tiene edad, género, ubicación ni nombre; `validar_historia` rechaza etiquetas de referencia | `src/contratos/historia.py`; `tests/contract/test_contratos.py::test_csv_crudo_con_etiquetas_es_fuga` | hecho |
| La ingesta descarta `variables_sensibles` y enmascara patrones de tarjeta, teléfono, DNI y correo, y lo cuenta en el reporte | `config/base.yaml` (`variables_sensibles`, `patrones_pii`); `src/ingesta/` | patrones definidos; implementación y prueba pendientes (Mathias) |
| Los registros no guardan el archivo original | `src/servicio/registro.py`; `tests/unit/servicio/test_registro.py` | hecho: guarda el hash de la historia, no los datos |
| Ninguna variable del modelo está en `variables_sensibles` | prueba prevista en `tests/unit/modelo/` | pendiente (Gino) |

## 3. Límites de la herramienta

- Orienta, no sustituye asesoría financiera, no promete resultados y nada se ejecuta: `responder` solo anota la decisión de la persona (`docs/arquitectura.md`, "Salvaguardas ya aplicadas"). Hecho en el servicio.
- Aviso de orientación educativa en cada pantalla: pendiente (`src/app/`, Jesús y Alberto).
- Con menos de `umbral_historia_semanas` de historia: confianza baja y sin propuestas (`config/base.yaml`). Valor del umbral en el pre-registro: [por fijar] (`config/preregistro.yaml`).
- El modelo se adopta solo si supera a la regla robusta con un umbral pre-registrado, en la prueba y en el perturbado; si no, se usa la regla robusta y se dice (`eval/adopcion.py`, `tests/unit/eval/test_adopcion.py`). Resultado: [por medir].
- Los pronósticos son cuantiles de ingreso acumulado, no una garantía; calibración del P20: [por medir].
- Los datos sintéticos no prueban desempeño con personas reales: no hay evidencia externa [por medir].

## 4. Sesgos

La herramienta no usa variables sensibles. Aun así puede rendir distinto por grupo de comportamiento.

- Se medirán por arquetipo, tercil de ingreso y tercil de volatilidad: pagos descubiertos, gasto permitido y calibración del P20 (`eval/sesgos.py`, Rafael).
- Se reporta la brecha entre el mejor y el peor grupo; hay alerta si supera `umbral_alerta_sesgo` (`config/preregistro.yaml`, [por fijar]).
- Tabla de resultados: [por medir]. Si un grupo queda peor, se dice y se muestra.
- Alcance: los grupos salen del generador sintético (`docs/datos.md`); no se miden sesgos demográficos, porque esas variables no existen en los datos.

## 5. Seguridad técnica

| Afirmación | Evidencia | Estado |
|---|---|---|
| Sin claves en el repositorio; `.env` ignorado; el núcleo no usa APIs externas | `.gitignore`; `requirements.txt`; `docs/arquitectura.md` | hecho; búsqueda de secretos en el historial: pendiente (Anderson) |
| Dependencias fijadas con versión y licencia | `requirements.txt`; `ATRIBUCIONES.md` | hecho; revisión de vulnerabilidades: pendiente |
| Contratos estrictos: sin campos extra, sin NaN, cuantiles ordenados y no negativos | `tests/contract/test_contratos.py` | hecho |
| La app solo habla con el servicio | `tests/contract/` (prueba de importaciones), `docs/arquitectura.md` | hecho |
| El texto libre es dato, no instrucción; ataques de inyección al asistente | `src/asistente/guardia.py`; `eval/chat.py` | pendiente; resultados: [por medir] |
| La capa generativa nace apagada y la configuración se niega a cargar si se enciende sin decisión | `config/base.yaml`; `src/contratos/config.py`; `DECISIONES.md` #13 | hecho |

## 6. Trazabilidad

- Cada recomendación deja una línea con `registro_id`, entradas, versiones, semilla, hash de configuración y decisión (`src/servicio/registro.py`, `tests/unit/servicio/test_registro.py`).
- `scripts/auditar_recomendacion.py <registro_id>` reconstruye la recomendación y compara con lo guardado (`docs/arquitectura.md`). Tasa de reproducción: [por medir].
- Pre-registro: umbrales fijados en un solo commit anterior a la primera evaluación; la hora está en `git log` (`config/preregistro.yaml`).
- Decisiones con su dato y alternativas rechazadas: `DECISIONES.md`. Qué hizo una persona y qué una herramienta de IA: `TRANSPARENCIA.md`.
- Salud: `logs/salud.jsonl` y `servicio.salud()` (p50, p95, tasa de error y de respaldo) en `src/servicio/observabilidad.py`; valores [por medir].

## 7. Quién responde

| Área | Dueño | Evidencia del reparto |
|---|---|---|
| Explicabilidad (motor) / pantalla "Por qué" | Sebastián / Alberto | `README.md` (tabla de asignaciones) |
| Privacidad e ingesta | Mathias | `README.md` |
| Sesgos | Rafael | `README.md` |
| Seguridad y trazabilidad | Anderson | `README.md` |
| Límites y avisos | Jesús y Alberto | `README.md` |
| Modelo, regla de adopción, este documento | Gino | `README.md` |

Las personas deciden siempre; la herramienta no ejecuta nada.

# Resultados del asistente en los dos conjuntos ciegos

Solo mide la **capa de intención en modo 1** (sin LLM): clasificador ML con palabras clave de respaldo y validación de parámetros. **No** mide cifras verificadas, citas ni plantillas (necesitan el flujo completo). La **guardia de entrada** (Mathias) no estaba implementada: ningún rechazo de abajo es de la guardia. Datos sintéticos; las preguntas las escribió Bartolome sin ver el código (`DECISIONES.md` #22 y #26).

Detalle por pregunta (texto, esperada, predicha, confianza, capa que rechazó): `eval/resultados/chat_ciego1.csv` y `eval/resultados/chat_ciego2.csv` (42 preguntas de conjunto ciego más las 12 de ataques; el texto se guarda recortado a 80 caracteres).

| | Ciego 1 | Ciego 2 |
|---|---|---|
| Archivo de preguntas | `data/chat/ciego_preguntas.csv` | `data/chat/ciego2_preguntas.csv` |
| Estado del asistente | **antes** de las mejoras (commit `41e61a7`; datos de entrenamiento: 224 preguntas) | **después** de las mejoras (commit `7f978c4`; entrenado con 318 preguntas, incluidas las del ciego 1) |
| Exactitud de intención | 31/42 = **0,738** | 34/42 = **0,810** |
| IC 95 % de Wilson | [0,589; 0,847] | [0,667; 0,900] |
| Cobertura a umbral 0,30 (confianza >= 0,30) | 29/42 = 0,690 | 35/42 = 0,833 |
| Exactitud entre las aceptadas | 26/29 = 0,897 | 32/35 = 0,914 |
| Exactitud bajo el umbral (se pediría reformular) | 5/13 | 2/7 |
| Fuera de alcance rechazadas | 5/7 | 7/7 |
| Falso rechazo de preguntas válidas | 3/35 | 4/35 (2 por intención y 2 por día fuera de 0 a 14) |
| Ataques rechazados (12) | 11/12: intención 9, parámetros 2, ninguna 1 | 11/12: intención 9, parámetros 2, ninguna 1 |

## Cómo leerlo
- **El ciego 1 ya no es ciego:** se vio, y pasó a conjunto de **desarrollo** (`DECISIONES.md` #27). Su cifra sirve como punto de partida, no como medida de generalización.
- **El ciego 2 se midió después de mejorar** el asistente con el vocabulario del ciego 1. Los dos intervalos se solapan mucho: **no se puede afirmar que mejoró**. Falta un tercer conjunto ciego para medir de nuevo.
- Los 2 ataques "rechazados por parámetros" (DNI y teléfono leídos como monto fuera de rango) son casualidad, no defensa; la URL pasó. Eso le corresponde a la guardia.
- El umbral 0,30 se fijó antes de evaluar (`DECISIONES.md` #24).

## Reproducibilidad
- **Ambos CSV se regeneraron y coinciden** con las corridas originales (mismas exactitudes, rechazos y capas; la latencia cambia en cada corrida y no se debe citar). Se hizo en un árbol de trabajo limpio de cada commit, con `python eval/chat.py` y `PYTHONPATH=src`.
- Ciego 1: commit `41e61a7` (el clasificador de `547c9a0` y las 224 preguntas originales, más el umbral 0,30 de `6caff1b`). Ciego 2: commit `7f978c4`, que es el estado actual de `feat/gino-asistente-v2`.
- Para el ciego 2 en la rama actual basta `python eval/chat.py` (la configuración busca `data/chat/ciego2_*.csv`). Para el ciego 1 hay que posicionarse en `41e61a7`: en la rama actual el ciego 1 es de entrenamiento y mediría memoria.

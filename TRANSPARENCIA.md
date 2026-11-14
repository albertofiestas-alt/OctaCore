# TRANSPARENCIA

Qué decidió cada persona, qué hizo una herramienta de IA y cómo se verificó cada resultado.

| Fecha y hora | Quién | Qué | Herramienta de IA | Cómo se verificó |
|---|---|---|---|---|
| 14-nov 10:30 | Anderson | Estructura del repositorio, contratos del Anexo A, config, fixtures, `tareas.py`, pruebas de contrato | Claude Code generó el código a partir de la propuesta v5 con instrucciones de Anderson | `python tareas.py test` en verde; Anderson revisó los contratos contra el Anexo A |
| 14-nov 11:20 | Anderson | Revisión del repositorio contra la v7 y los planes individuales; contratos, firmas y configuración v7; esqueletos de cada paquete; servicio (consultar con respaldo, responder, salud, auditar), `scripts/auditar_recomendacion.py`; `.github/`; lectura de asignaciones en el README; guía de arranque | Claude Code comparó la v7 y los planes con el repositorio y escribió el código y las pruebas con instrucciones de Anderson | `python tareas.py test`: 134 pruebas pasan; el flujo con capas reales queda como xfail hasta el control 1. Anderson revisa las decisiones 9 a 17 con Gino |
| 14-nov 11:51 | Gino (encargo; lo ejecutó una sesión de Claude Code) | `eval/adopcion.py` (regla de adopción), `tests/unit/eval/`, `config/preregistro.yaml` solo con estructura y null, borradores de `docs/responsible_ai.md` y `docs/roadmap.md`, decisiones 18 y 19 | Claude Code escribió código, pruebas y borradores desde el plan de Gino; Gino aún no revisa los borradores | Pruebas con fronteras de juguete en verde (adopta, no adopta, gana solo en la prueba, umbral null); `tests/contract/test_firmas.py` sigue en verde; ninguna cifra de los documentos se midió todavía (`[por medir]`) |

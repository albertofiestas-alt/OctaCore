# Roadmap (BORRADOR)

Tres horizontes. Sin cifras prometidas: cualquier número que aparezca aquí sale de una medición propia `[por medir]`.

## Horizonte 1 — Después del hackathon: validar lo que hay

- Medir con los datos sintéticos lo que hoy está [por medir]: frontera, calibración del P20, ablaciones, sesgos (`docs/evaluacion.md`, `eval/`).
- Publicar la decisión de adopción tal como salga (`eval/adopcion.py`): si gana la regla robusta, se presenta la regla robusta.
- Cerrar lo pendiente de `docs/responsible_ai.md` (variables sensibles, PII y seguridad).
- Probar con personas usuarias reales solo con consentimiento y datos controlados: aún no se hizo.

## Horizonte 2 — Producto con datos reales

- Conectar fuentes de movimientos reales con consentimiento, minimización y control de acceso (hoy `data/` es sintético).
- Recalibrar y reevaluar el modelo con datos reales antes de decidir de nuevo su adopción, con un pre-registro nuevo (`config/preregistro.yaml`).
- Revisión de sesgos con variables que hoy no existen y que requerirían base legal; decidir si se miden.
- Observabilidad y auditoría (`logs/salud.jsonl`, `scripts/auditar_recomendacion.py`) como base del monitoreo.

## Horizonte 3 — Alcance ampliado, sujeto a evidencia

- Más tipos de ingreso irregular y de pagos; propuestas simuladas más ricas. Solo si el Horizonte 2 muestra que el número de hoy es útil.
- Capa generativa para el porqué (`src/generativa/`), solo con autorización, verificador sin IA y apagada por defecto.
- La ejecución real de movimientos queda fuera: la persona decide siempre.

## Anexo (14-nov, Gino): metas de ahorro y señal de elegibilidad

Líneas añadidas sin tocar lo anterior. Todo lo que no tiene medición propia está marcado **[por medir]** o **[propuesto]**; no se prometen cifras ni se nombran productos de BBVA.

- **Metas de ahorro** (ejemplo: apartar para un departamento) usando el mismo motor de ingresos: la meta se modela como un pago futuro con fecha y monto, y el número de hoy y el semáforo dicen si se alcanza sin fallar los pagos con fecha **[propuesto, por medir]**. Hay que decidir cómo convive con el colchón y con la propuesta de apartar.
- **Señal de elegibilidad por "verde sostenido"**, solo como señal indicativa que un analista de BBVA revisa; nunca aprobación automática, voluntaria y revocable (`docs/criterios_elegibilidad_semaforo.md`). Antes de mostrarla hay que resolver lo que el experimento dejó abierto: una reducción del 25 % del gasto sube la tasa de calificación de 5,0 % a 19,8 % [respaldo] (premia austeridad), y los técnicos y casi todos los asalariados quedan en 0 % con el semáforo de respaldo; la métrica de brecha absoluta no lo detecta cuando casi nadie califica (`eval/resultados/elegibilidad_*.csv`, rama `feat/gino-criterios-elegibilidad`, `6f12d6d`). Requiere datos y políticas reales de BBVA y revisión legal **[BBVA]**.
- **Ingreso recurrente inferido** (sueldos, depósitos periódicos) para dar al motor el calendario del ingreso y no solo el de los pagos: hoy el semáforo sin calendario del sueldo puede marcar rojo a quien gasta todo lo permitido (diagnóstico de Pedro, origen por citar). Validar contra datos reales con consentimiento **[por medir]**.

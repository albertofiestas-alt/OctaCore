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

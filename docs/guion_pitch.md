# Guion del pitch de 5 minutos: "¿cuánto puedo gastar hoy sin fallar un pago con fecha?"

**Formato:** 5 minutos (el formato oficial no está confirmado; si son 10, se alarga la evidencia y la demo, no se añade nada). **Regla de oro:** ningún número sin origen. **[respaldo]** = sale del simulador de respaldo de Pedro (`eval/_simulador_respaldo.py`: pagos inferidos sin validar, solo regla2 al P20; no del motor oficial). Datos 100 % sintéticos, parámetros `[SUPUESTO]` (`data/REPORTE_DATOS.md`).

| Min | Bloque | Mensaje en una frase |
|---|---|---|
| 0:00 a 0:40 | 1. Problema | Quien no cobra sueldo fijo no tiene un problema de montos sino de fechas |
| 0:40 a 1:40 | 2. Solución | Un número de hoy, un semáforo y un porqué |
| 1:40 a 3:00 | 3. Evidencia | Pre-registramos, medimos y el modelo no ganó: usamos regla2 y lo decimos |
| 3:00 a 3:30 | 4. Responsabilidad | Sin IA generativa en el núcleo, cifras verificables, datos sintéticos |
| 3:30 a 4:20 | 5. Lo que aprendimos | Dos hallazgos incómodos, dichos antes de que pregunten |
| 4:20 a 5:00 | 6. Roadmap y cierre | Metas de ahorro y señal de elegibilidad revisada por una persona |

## 1. Problema (0:40)
- "El alquiler o la cuota vencen antes de que entre el dinero." Las herramientas de presupuesto suponen un ingreso mensual estable (`asignaciones/Resumen_propuesta_hackathon_BBVA_v9.md`).
- La pregunta del usuario: **¿cuánto puedo gastar hoy sin fallar un pago con fecha?**
- Contexto en los datos sintéticos: 81,0 % de las personas tiene al menos un mes en déficit en el año 2 (`data/REPORTE_DATOS.md`, referencia, no objetivo).

## 2. Solución (1:00)
- **Número de hoy:** mínimo, sobre cada fecha de pago y el día 14, de (saldo + ingreso conservador − pagos hasta esa fecha − colchón) ÷ días (`asignaciones/Plan_04`). Redondeo hacia abajo, nunca hacia arriba.
- **Semáforo por pago:** verde si se cubre con el escenario P5 de ingreso, ámbar si con P50, rojo si no.
- **Porqué:** desglose con evidencia, supuestos, límites y confianza; cada cifra sale del motor, no de un texto libre.
- **Ingreso como rango (cuantiles), no como promedio.** Escalera de métodos: **regla1** (promedio ingenuo) → **regla2** (regla robusta) → **modelo** de cuantiles.

## 3. Evidencia (1:20): la parte que nos da credibilidad
- **Pre-registramos antes de evaluar:** regla de adopción (mejora mínima 2,0 S/día a igual % de pagos descubiertos), cuantil 0,20, 20 semillas. Commit `005fb50`, 14-nov 11:58:29.
- **La escalera sí sirvió:** regla2 baja los pagos descubiertos de 6,87 % (regla1) a 2,69 % con casi el mismo gasto (84,91 → 83,75 S/día) [respaldo] (`DECISIONES.md` #23, rama `feat/gino-eval-frontera`, `b4dc7d7`).
- **El modelo NO superó a regla2.** Al mismo cuantil, con 20 pares de semillas: **+0,43 pp de descubiertos [IC95 0,31; 0,56]** y **+0,31 S/día [0,27; 0,36]** [respaldo] (`eval/resultados/pares.csv`, `63d75db`). Se mueve a lo largo de la frontera, no la supera; la mejora a igual % de descubiertos fue −0,68 (prueba) y +0,06 (perturbado) frente al umbral de 2,0 [respaldo] (#23). **No se adopta: usamos regla2 y lo decimos.**
- **Asistente, dos conjuntos ciegos de 42 preguntas, solo intención, modo 1:** 31/42 = **74 % [IC 59 a 85]** (el primero, que después pasó a desarrollo: `DECISIONES.md` #27) y 34/42 = **81 % [67 a 90]** (el segundo; `data/chat/ciego2_preguntas.csv`, `7f978c4`, rama `feat/gino-asistente-v2`). Los intervalos se solapan: no probamos que mejoró. Umbral de confianza 0,30 fijado antes (#24).

## 4. Responsabilidad (0:30)
- **Sin IA generativa en el núcleo** (`DECISIONES.md` #20): el porqué lo redactan plantillas con las cifras del motor; la capa generativa está apagada.
- **Números verificables:** el verificador exige que cada cifra del texto salga del desglose.
- **Datos sintéticos, sin variables sensibles en el modelo, sin ejecutar movimientos:** la persona decide siempre.
- **Límites que decimos nosotros:** no hay datos reales de BBVA; la guardia de entrada del asistente aún no está implementada; el semáforo de las evaluaciones sale del respaldo [respaldo].

## 5. Lo que aprendimos (0:50)
1. **El semáforo sin el calendario del sueldo marca rojo a quien gasta todo lo permitido** (diagnóstico de Pedro; **[origen por citar: no encontré el archivo en el repositorio]**). Coherente con lo que vimos: ningún asalariado calificó a "verde 6 meses" [respaldo] (`elegibilidad_tasas.csv`).
2. **Una señal de elegibilidad por "verde sostenido" premia la austeridad.** Con 25 % menos de gasto, quienes califican suben de 5,0 % a 19,8 % (20 → 79 de 400) [respaldo] (`eval/resultados/elegibilidad_incentivo.csv`, rama `feat/gino-criterios-elegibilidad`, `6f12d6d`). Los técnicos quedan en 0 % antes y después. La métrica de brecha (0,145, bajo el umbral 0,20) no lo captura porque casi nadie califica; lo declaramos.

## 6. Roadmap y cierre (0:40)
- **Metas de ahorro** (ejemplo: un departamento) con el mismo motor de ingresos: la meta como un pago futuro con fecha **[propuesto, por medir]**.
- **Señal de elegibilidad solo como señal indicativa que un analista revisa**, nunca aprobación automática, voluntaria y con sus criterios visibles (`docs/criterios_elegibilidad_semaforo.md`).
- **Ingreso recurrente inferido** (hoy el respaldo infiere pagos; falta validarlo con datos reales y consentimiento).
- **Cierre:** "Pre-registramos, medimos y publicamos lo que no funcionó. Preferimos un número honesto a un modelo que impresiona."

## Si preguntan
- *¿Por qué no usaron el modelo?* No superó a regla2 con la regla pre-registrada; un resultado negativo medido vale más que uno no medido.
- *¿Funciona con datos reales?* No lo sabemos. Todo es sintético.
- *¿Es un puntaje de crédito?* No: mide cuánto puedo gastar hoy, no solvencia.

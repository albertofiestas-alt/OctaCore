# Guion del pitch de 5 minutos: "¿cuánto puedo gastar hoy sin fallar un pago con fecha?"

**Formato:** 5 minutos (el formato oficial no está confirmado). **Regla de oro:** ningún número sin origen (apéndice al final). **[respaldo]** = sale del simulador de respaldo de Pedro (pagos inferidos sin validar, solo regla2 al P20), no del motor oficial. Datos 100 % sintéticos.

| Min | Bloque | Mensaje en una frase |
|---|---|---|
| 0:00 a 0:40 | 1. Problema | Sin sueldo fijo, el problema son las fechas, no los montos |
| 0:40 a 1:40 | 2. Solución | Un número de hoy, un semáforo y un porqué |
| 1:40 a 3:00 | 3. Evidencia | Pre-registramos, medimos y el modelo no ganó: usamos regla2 |
| 3:00 a 3:30 | 4. Responsabilidad | Sin IA generativa en el núcleo, cifras verificables |
| 3:30 a 4:20 | 5. Lo que aprendimos | Tres hallazgos incómodos, dichos antes de que pregunten |
| 4:20 a 5:00 | 6. Roadmap y cierre | Metas de ahorro y una señal revisada por una persona |

## 1. Problema
"El alquiler o la cuota vencen antes de que entre el dinero." La pregunta: **¿cuánto puedo gastar hoy sin fallar un pago con fecha?**

## 2. Solución
- **Número de hoy:** el mínimo, sobre cada fecha de pago y el día 14, de (saldo + ingreso conservador − pagos hasta esa fecha − colchón) ÷ días. Siempre se redondea hacia abajo.
- **Semáforo por pago:** verde si se cubre con el escenario P5 de ingreso, ámbar con P50, rojo si no.
- **Porqué:** desglose con evidencia, supuestos, límites y confianza.
- **Ingreso como rango (cuantiles), no promedio.** Escalera: **regla1** (promedio) → **regla2** (regla robusta) → **modelo**.

## 3. Evidencia
- **Pre-registramos antes de evaluar:** mejora mínima de 2,0 S/día a igual % de descubiertos, cuantil 0,20, 20 semillas (commit `005fb50`, 11:58).
- **La escalera sí sirvió:** regla2 baja los pagos descubiertos de 6,87 % a 2,69 % con casi el mismo gasto [respaldo].
- **El modelo NO superó a regla2.** Modelo menos regla2 al P20, 20 semillas, IC95: generador 1.0, **+0,43 pp de descubiertos [0,31; 0,56]** y **+0,31 S/día [0,27; 0,36]**; generador 1.1, **+0,63 pp [0,51; 0,76]** y **+0,29 S/día [0,26; 0,34]** [respaldo]. Gasta algo más, descubre algo más: se mueve por la frontera sin superarla, y la ganancia está unas 7 veces por debajo del umbral. **No se adopta: usamos regla2 y lo decimos.**
- **Asistente, dos conjuntos ciegos de 42 preguntas (solo intención):** **74 % [59 a 85]** y **81 % [67 a 90]**. El segundo se midió después de mejorar con el primero y los intervalos se solapan: no probamos que mejoró.

## 4. Responsabilidad
Sin IA generativa en el núcleo: el porqué lo redactan plantillas con las cifras del motor, y un verificador exige que cada cifra salga del desglose. Datos sintéticos, sin variables sensibles, la persona decide siempre. Lo que decimos nosotros: no hay datos reales de BBVA y la guardia de entrada del asistente aún no está implementada.

## 5. Lo que aprendimos
1. **Sin el calendario del sueldo, el semáforo marca rojo a quien gasta todo lo permitido.** Los asalariados pasan una mediana de 63,5 días al año en rojo; sin gastar el número, ninguno [respaldo, generador 1.0].
2. **Una señal de "verde sostenido" premia la austeridad.** Con 25 % menos de gasto, quienes califican suben de 5 % a casi 20 % [respaldo]. Solo conductores y vendedoras califican; 3 de 5 arquetipos quedan en 0 %. La brecha absoluta (0,145) no lo marca; la razón de tasas (0,0) sí. **La repetición con el generador 1.1 NO es un contraste independiente:** el simulador reemplaza el gasto por el número de hoy, así que casi no ve el cambio de generador.
3. **Medir encontró un error nuestro:** la ingesta marcaba atípico todo el alquiler y la deuda, y el producto no veía el alquiler. Con el parche, el recall de pagos inferidos pasa de 42,2 % a 96,2 % (precisión 97,6 % → 97,8 %). Visto de Mathias pendiente.

## 6. Roadmap y cierre
- **Metas de ahorro** (ejemplo: un departamento) con el mismo motor de ingresos [propuesto, por medir].
- **Señal de elegibilidad solo como señal que un analista revisa**, nunca aprobación automática ni puntaje de crédito.
- **Ingreso recurrente inferido,** para dar al motor el calendario del sueldo.
- **Cierre:** "Pre-registramos, medimos y publicamos lo que no funcionó."

## Preguntas difíciles
- *¿Por qué no usaron el modelo?* No superó a regla2 con la regla pre-registrada; un resultado negativo medido vale más que uno no medido.
- *¿Funciona con datos reales?* No lo sabemos: todo es sintético.
- *¿Es un puntaje de crédito?* No: mide cuánto puedo gastar hoy, no solvencia.

---

## Apéndice: origen de cada cifra (fuera del conteo de la presentación)
| Cifra | Origen |
|---|---|
| Pre-registro | commit `005fb50` (14-nov 11:58:29); `config/preregistro.yaml` |
| Regla1 6,87 % / S/ 84,91 y regla2 2,69 % / S/ 83,75 [respaldo] | `DECISIONES.md` #23, rama `feat/gino-eval-frontera` (`b4dc7d7`) |
| Pares 1.0: +0,433 pp [0,311; 0,563], +0,309 S/día [0,269; 0,356] [respaldo] | `eval/resultados/pares.csv`, rama `feat/gino-eval-frontera` |
| Pares 1.1: +0,631 pp [0,505; 0,764], +0,294 S/día [0,255; 0,337] [respaldo] | `eval/resultados/pares_v11.csv`, rama `feat/gino-eval-frontera` (`58aae08`) |
| Frontera 1.1: regla2 8,68 % / S/ 34,12, modelo 9,51 % / S/ 34,37, gasto fijo 36,15 %; mejora −0,79 (prueba) y −0,16 (perturbado) frente a 2,0 [respaldo] | `eval/resultados/frontera_v11.csv`, `adopcion_v11.json` (`536eca8`) |
| Ingesta oficial sobre 1.0 sin el parche: mejora −0,10 y −0,13, no adopta [respaldo] | `adopcion_v10_ingesta.json` (`536eca8`, 13:50, anterior al parche en main, 13:54) |
| Asistente 31/42 (74 %) y 34/42 (81 %), IC de Wilson, cobertura, ataques | `docs/resultados_chat.md`, `eval/resultados/chat_ciego1.csv` y `chat_ciego2.csv` (en main); `DECISIONES.md` #24 y #27 |
| Asalariados en rojo: mediana 63,5 días; sin gastar el número, 0 rojo y 365 verde [respaldo, generador 1.0; repetir con el 1.1] | `docs/diagnostico_asalariados_rojo.md` (`a3d4e05`, rama `feat/gino-eval-frontera`) |
| Elegibilidad: 20/400 → 79/400 con −25 % de gasto (1.0) y 19/400 → 79/400 (1.1); brecha 0,145; razón de tasas 0,0; 3 arquetipos en 0 % [respaldo] | `eval/resultados/elegibilidad_*.csv`, `elegibilidad_*_v11.csv`, `elegibilidad_1_0_vs_1_1.csv`; `DECISIONES.md` #29 y #35 |
| Ingesta: recall 42,2 % → 96,2 %, precisión 97,6 % → 97,8 % (100 personas, meses 13-24, causal) | `DECISIONES.md` #31, commit `2647fd7` (en main `89d9833`), `eval/_medir_pagos_inferidos.py` |
| Criterios y riesgos de la señal de elegibilidad | `docs/criterios_elegibilidad_semaforo.md` |

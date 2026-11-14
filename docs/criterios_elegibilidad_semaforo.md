# Criterios para que "semáforo verde sostenido" sea una señal defendible

**Estado:** diseño para el roadmap y la lámina de valor. No hay código nuevo ni cambios en `src/`. Todo lo que no se ha medido está marcado **[por medir]**; todo lo que no depende de nosotros, **[BBVA]**. No conocemos políticas de riesgo, productos ni tasas de BBVA, y este documento no las inventa.

**Idea de Gino:** si el semáforo de una persona se mantiene verde N meses (ejemplo: 6), esa constancia podría servir de señal para que un analista de BBVA considere un préstamo o una tarjeta. Pregunta: ¿qué criterios la hacen defendible?

**Respuesta corta:** solo como señal de estabilidad de liquidez, con criterios múltiples, explicable y revisada por una persona. Nunca como puntaje de crédito ni como aprobación.

## 1. Qué significa "verde sostenido" con las definiciones del motor

Del plan del motor (`asignaciones/Plan_04`) y del pre-registro (`config/preregistro.yaml`):

- **Semáforo por pago con fecha** (día d): *verde* si el pago se cubre con el escenario P5 de ingreso (cobertura = saldo + ingreso(d, P5) − pagos hasta d ≥ 0); *ámbar* si se cubre con P50 pero no con P5; *rojo* si ni con P50. El motor entrega un semáforo **por pago**, no uno por persona.
- **Confianza:** `baja` si `semanas_historia` < 4 o el ancho relativo (P80−P5 a 14 días, entre max(P50, 1)) > 1,2; `alta` si ancho < 0,5 y hay historia; `media` en lo demás.
- **Propuesta de definición de día verde (hay que fijarla):** todos los pagos con fecha de la ventana de 14 días en verde, es decir, el *peor* semáforo de `por_pago`. Un día **sin ningún pago con fecha** no tiene semáforo informativo: no debe contar como verde.
- **Mes verde:** todos sus días verdes, salvo la tolerancia del criterio 6.

Lo que esto implica: P5 es un escenario muy pesimista, así que el verde exige tener *saldo* para aguantar una semana mala. Mide liquidez, no ingreso ni hábito de pago.

## 2. Criterios candidatos

| # | Criterio | Razón | Riesgo |
|---|---|---|---|
| 1 | **Meses consecutivos en verde** (N). Gino propone 6; N **[por medir]** | La persistencia distingue un buen momento de un patrón | Se puede lograr gastando poco; un N largo deja fuera a los ingresos irregulares |
| 2 | **Cero pagos con fecha descubiertos** (resultado observado, no pronosticado) | El pronóstico puede equivocarse; el hecho no | Solo lo ve quien ve la cuenta que paga **[BBVA]**; en nuestros datos "descubierto" lo define el simulador, no un banco |
| 3 | **Confianza no baja** durante el periodo | Un verde con confianza baja es evidencia débil | Confianza baja correlaciona con ingreso irregular: castiga a técnicos y comisionistas por su forma de cobrar **[por medir]** |
| 4 | **Historia mínima:** `semanas_historia` ≥ M y al menos k pagos con fecha observados (M y k **[por fijar]**; para N=6 meses, M ≥ ~26 semanas) | Evita verdes triviales (sin pagos, sin datos) | Excluye a clientes nuevos o con poco historial |
| 5 | **Estabilidad del colchón/ahorro:** el saldo mínimo mensual no cae mes a mes | Un verde que se sostiene vaciando ahorros no es sostenible | El colchón del pre-registro es 0; el ahorro está fuera del alcance del motor; puede premiar acumular en vez de pagar deuda |
| 6 | **Tolerancia a ámbar:** hasta *a* semanas ámbar en el periodo (*a* **[por fijar]**), nunca rojo, y el último mes completo en verde | Una semana mala no debería reiniciar el contador | Más reglas = más difícil de explicar y de auditar; abre huecos para ajustar el comportamiento |

Recomendación de diseño: exigir **1 + 2 + 4** como base (constancia, hechos y datos suficientes) y mostrar 3, 5 y 6 como información al analista antes que como filtros duros. Es una hipótesis para probar en el experimento de la sección 5, no una conclusión.

## 3. Riesgos que hay que decir en voz alta

1. **El semáforo mide "cuánto puedo gastar hoy sin fallar un pago con fecha", no solvencia ni capacidad de pagar una deuda nueva.** Una cuota adicional cambiaría los pagos futuros, y el semáforo no sabe cuánto soportaría esa persona.
2. **Incentivo perverso.** Gastar menos de lo necesario, pagar tarde fuera de la vista del banco o mover ingresos a otra cuenta mejoran el semáforo sin mejorar la situación. Cuanto más valioso sea el premio, más fuerte el incentivo.
3. **Sesgo contra ingresos irregulares.** Los datos sintéticos ya lo anticipan (**datos ficticios, todos [SUPUESTO]**, `data/REPORTE_DATOS.md`): el porcentaje de personas con algún mes en déficit en el año 2 va de 43,9 % en asalariados (grupo de control) a 72,1 % en conductores, 80,2 % en vendedoras, 91,1 % en comisionistas y 100 % en técnicos. Con esos números, cualquier criterio de "sin meses malos" deja fuera casi a todos los técnicos; no sabemos aún cuánto de esa brecha es real y cuánto es del generador.
4. **Regulación del scoring de crédito.** Si la señal influye en una decisión de crédito, probablemente exija explicabilidad, no discriminación, consentimiento informado y revisión humana **[BBVA / área legal; no citamos normas]**. Nuestras variables sensibles ya están excluidas del modelo; eso no basta si un criterio las reproduce por otra vía (el arquetipo de ingreso funciona como indicador de ocupación).
5. **No tenemos datos reales de BBVA ni sus políticas de riesgo.** Todo lo medido aquí es sintético y demuestra el método, no la precisión en el mundo real.

## 4. Cómo se presentaría

- Una **señal indicativa de estabilidad de liquidez** ("N meses sin pagos descubiertos"), no un puntaje, con sus criterios visibles en la pantalla Por qué: qué meses cuentan, qué evidencia, qué confianza y qué se ignoró.
- **Voluntaria y revocable:** la persona decide si se comparte y puede retirarla.
- **Un analista de BBVA la revisa** junto con lo que BBVA ya sabe de la persona; **nunca una aprobación automática** ni una oferta preaprobada generada por el semáforo.
- Trazable con el `registro_id` ya existente, y con su límite escrito: "mide liquidez a 14 días, no capacidad de endeudamiento".

## 5. Experimento barato con datos sintéticos (descrito, **no ejecutado**)

**Pregunta:** ¿qué porcentaje de personas de cada arquetipo alcanzaría "N meses verde" bajo cada combinación de criterios? Si la brecha entre arquetipos es grande, es un hallazgo de sesgo y se declara, igual que en `eval/sesgos.py`.

**Cómo se haría:**
1. Generar las 400 personas con la semilla del proyecto (`make datos`, ~26 s) y simular día a día el semáforo con `regla2` (no entrena, así que puede usar los 24 meses sin fuga).
2. Por persona, guardar la serie diaria: peor semáforo, confianza, saldo y pagos descubiertos observados.
3. Calcular por arquetipo la tasa de "N meses verde" para N = 3, 4, 6 y para los conjuntos de criterios {1}, {1+2}, {1+2+4}, {1+2+3+4}, {1+2+4+6}.
4. Reportar la brecha máxima entre arquetipos y compararla con un umbral **[por fijar antes de ver resultados]**. No se reutiliza el 0,05 de `umbral_alerta_sesgo`, que es del modelo.
5. Prueba de incentivo: repetir con la misma persona gastando 20–30 % menos que lo observado; si la tasa sube mucho, la señal premia austeridad, no estabilidad **[por medir]**.

**Por qué no lo ejecuté:** el simulador de respaldo de Pedro (`eval/_simulador_respaldo.py`, rama `feat/gino-eval-frontera`) no puede modificarse y solo devuelve totales por persona (pagos descubiertos, pagos totales, gasto permitido) sobre los meses 21 a 24: **cuatro meses**, menos que los seis de la idea, y sin la serie diaria de semáforo que hace falta. Hacerlo exige que `eval/simular.py` (Rafael) devuelva esa serie y que se simule una ventana de al menos 12 meses. Con el simulador actual solo se podría medir N ≤ 4 y el criterio 2.

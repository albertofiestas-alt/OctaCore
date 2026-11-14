**Hackathon de Ingeniería BBVA · AI Financial Life**

**Propuesta y plan de trabajo · versión 8 (definitiva)**

Sábado 14-nov-2026 · Equipo de 7 · Líder: Gino Vieyra · Basada en la guía oficial del desafío y en el Challenge pack de BBVA, entregados el 14-nov

| **Versión** | **Qué es** | **Estado** |
|---|---|---|
| v3 | Propuesta completa de 12 páginas, para 6 personas | Se integra aquí |
| v4 | Parche de 3 páginas con los huecos de la v3 (criterio de éxito, fórmula por fecha de pago, datos de 24 meses, calendario) | Se integra aquí |
| v5 | Documento único: propuesta, diseño, contratos entre módulos, repositorio, pruebas al límite, pitch y plan de 7 personas | Reemplazada |
| v6 | La v5 más lo que pide el Challenge pack: Responsible AI con análisis de sesgos, pesos y formato de pitch por confirmar, diccionario de datos, observabilidad, trazabilidad auditable, roadmap y tareas nuevas por persona | Reemplazada |
| v7 | La v6 más el diseño de la opción B (capa generativa con OpenAI y verificador), la guía de trabajo en paralelo con GitHub, las firmas exactas de cada módulo y las instrucciones paso a paso por persona | Reemplazada |
| v8 | La v7 más la opción C (asistente conversacional del semáforo con LLM, RAG y ML, inspirado en el copiloto del bot_diagnosis) y las aclaraciones de la fórmula del número de hoy | Fuente de verdad |

Cómo leer las marcas. [SUPUESTO]: no verificado. [propuesto]: lo decide o confirma Gino. [por medir]: se llena con una medición hecha en este trabajo. Regla de oro: cada cifra que digamos sale de una medición nuestra o de una fuente abierta y verificada. Si no, no se dice.

Si algo de este documento contradice a otro, manda la v8. Cada persona tiene un documento individual derivado de esta versión, con sus entregables, interfaces, pruebas, horas y, desde la v8, una sección de tareas nuevas. Los cambios a la v8 los aprueba Gino y se anotan en DECISIONES.md del repositorio.

Dos fuentes oficiales y tres puntos en conflicto. BBVA entregó una guía impresa de 7 páginas y un Challenge pack de 12 láminas. Los pesos de evaluación, el formato del pitch (10 más 3 contra 5 más 5 más 5) y el papel de la IA generativa no coinciden. Hasta que la organización confirme cuál manda, el plan cubre las dos: se prepara el pitch corto y se puede ampliar, y la generativa queda como capa opcional. Las preguntas están en la sección 18.

## 1. La propuesta en una página

Qué construimos. Una herramienta para personas con ingresos irregulares que predice, con incertidumbre medida, si alcanzará para cada pago con fecha, y propone en simulación cuánto se puede gastar hoy y qué conviene apartar. La persona decide siempre.

| **Elemento** | **Definición** |
|---|---|
| Usuario | Adulto con ingresos que varían de una semana a otra (independiente, comisionista, quien cobra por billetera digital), con pagos de fecha fija y sin colchón. |
| Problema | No puede usar un presupuesto mensual: no sabe cuánto entrará ni cuándo, y los pagos vencen antes de que llegue la plata. |
| Decisión que mejoramos | ¿Cuánto puedo gastar hoy sin fallar a un pago con fecha? |
| Criterio de éxito (escrito antes de medir) | A igual porcentaje de pagos con fecha descubiertos, el modelo permite más gasto diario que la regla robusta; o a igual gasto, deja menos pagos descubiertos. Debe cumplirse en la prueba y en el generador perturbado. Si no se cumple, se presenta la regla robusta y se dice. |
| Función de la IA | Pronóstico por cuantiles del ingreso acumulado a 3, 7 y 14 días, comparado contra dos reglas sencillas. Sin modelo de lenguaje en el MVP [propuesto]. |
| Lo que la distingue | No es el pronóstico (BBVA AI Factory ya publicó uno con bandas). Es la decisión por fecha de pago, la frontera entre seguridad y gasto medida contra reglas, propuestas que aguantan el escenario pesimista y decir con datos cuándo el modelo no gana. |
| Lo que no hace | No ejecuta operaciones, no promete rentabilidades, no da asesoría regulada, no usa datos reales, no usa marcas ni interfaces de BBVA. Todo es orientación educativa y simulación. |
| Nombre | Debe hablar de fechas y no parecer de BBVA. Candidatos de trabajo: Fecha Clara, Plata con Fecha, Pago a Tiempo [propuesto]. |

Principio de la guía que nos orienta: la mejor solución no es la más compleja, sino la que convierte datos e IA en una decisión financiera más clara, segura y demostrablemente útil.

### Qué no hacemos (alcance cerrado)

- **Fuera:** modelo de lenguaje en el MVP, React, un servicio FastAPI aparte, app móvil, conexión a cuentas, créditos, inversión, seguros, voz [propuesto].
- **Modelo de lenguaje, si se autoriza:** se agrega solo después del congelamiento y solo si la organización lo autoriza; únicamente para redactar, nunca para calcular ni decidir.

## 2. Reglas del reto que condicionan el diseño

| **Regla de la guía** | **Qué significa para nosotros** |
|---|---|
| IA o ML con función demostrable y evaluable; analítica reproducible; interfaz o API utilizable; demostración ejecutable (p. 2) | Modelo por cuantiles con tabla de resultados reproducible con un comando y una pantalla que corre en local. |
| Explicar supuestos, limitaciones, incertidumbre y métricas; no prometer rentabilidades ni operar (p. 2) | Cada pantalla lleva el aviso de orientación educativa; cada recomendación trae fundamento, límites y confianza. |
| Prohibido datos reales, credenciales, sistemas o material de BBVA, y marcas o interfaces bancarias como producto oficial (p. 2) | Datos sintéticos propios; sin logo ni estilo de BBVA; sin identificadores reales, tampoco del equipo. |
| Justificar cada técnica y compararla con una alternativa sencilla (p. 2) | Escalera de tres escalones: regla ingenua, regla robusta, modelo. Nos quedamos con el más simple que cumpla. |
| BBVA no da claves de API, créditos ni GPU; un modelo de lenguaje externo solo si las reglas finales lo autorizan y sin datos personales (p. 2, p. 6) | Todo corre en local sin internet. El MVP no depende de ningún servicio externo. |
| Contrato de datos recomendado; calidad y trazabilidad; escenarios difíciles; sin fuga entre entrenamiento y evaluación (p. 3) | Sección 6: 24 meses, partición por fecha y por personas, generador perturbado, semilla y reporte de calidad. |
| Tres capas separadas; secretos fuera del código; versiones, prompts y respaldo documentados; validaciones, errores, tiempos y pruebas reproducibles (p. 3) | Secciones 8, 9 y 10. Cada capa se prueba por separado y se comunica por un contrato escrito. |
| El usuario conserva la decisión final (p. 3) | Nada se ejecuta. La persona aprueba o rechaza cada propuesta. |
| Reutilizar código con atribución; el trabajo del evento debe distinguirse (p. 6) | Un solo repositorio, commits desde el sábado, archivo de atribuciones y de transparencia. |
| Diez equipos; el jurado valora evidencia observable, no promesas; demo en vivo principal y grabada de respaldo (p. 4) | Demo local en vivo; video de respaldo; datos de demo precargados. |
| No hay puntos extra por más agentes, modelos o servicios; se penalizan afirmaciones no verificadas, resultados fabricados y riesgos de privacidad o seguridad (p. 5) | Pocas piezas bien medidas. Ningún número sin origen. |
| Challenge pack: toda recomendación explica el porqué con evidencia, supuestos y nivel de confianza; identificar sesgos y evitar decisiones discriminatorias por variables sensibles (p. 11) | Cada Decision trae fundamento, evidencia, supuestos, límites y confianza. Ninguna variable sensible entra al modelo ni al motor, y se mide el resultado por grupos. |
| Challenge pack: privacidad, seguridad y uso responsable; cuidado con secretos, APIs externas, claves, inyección de prompts y dependencias inseguras (p. 11) | Sin PII, secretos fuera del código, dependencias fijadas y revisadas, sin APIs externas en el núcleo, y sin prompts porque no hay modelo de lenguaje en el núcleo. |
| Challenge pack: trazabilidad; debe ser posible auditar qué datos, variables, modelos o prompts produjeron cada recomendación (p. 11) | Registro por recomendación y un script que reconstruye cualquiera a partir de su identificador. |
| Challenge pack: no basta una demo cosmética ni un chatbot genérico; el jurado debe distinguir quién solo habla de IA de quién razona, mide, explica y funciona (p. 4 y 7) | Toda la evidencia es medida: frontera, pares de semillas, ablaciones, sesgos y pruebas. |
| Challenge pack: arquitectura, modularidad, APIs, testing, seguridad, despliegue y observabilidad (p. 7) | Tres capas con contratos, pruebas de varias familias y un registro de salud con latencias y errores. |

## 3. Cómo se evalúa y cómo ganamos cada punto

Hay DOS tablas de pesos oficiales y no coinciden. La de la guía impresa se muestra primero y la del Challenge pack (p. 10) después. Por confirmar con la organización cuál aplica. En las dos, IA y analítica pesa 25, así que ahí va el mayor esfuerzo.

### Pesos del Challenge pack (p. 10)

| **Criterio del pack** | **Peso** | **Qué entregamos** | **Dueños** |
|---|---|---|---|
| IA / ML / analítica | 25 | Escalera de tres escalones, métricas en datos no vistos, frontera, calibración, ablaciones, pares de semillas, ejemplos de error | Gino, Rafael |
| Valor de producto y UX | 20 | Un número, su porqué en soles y fechas, límites, aprobar o rechazar, accesibilidad; problema y usuario claros | Jesús, Alberto, Gino |
| Ingeniería y arquitectura | 20 | Tres capas, contratos, pruebas de varias familias, mutaciones, fuzz, determinismo, seguridad, observabilidad | Anderson, Mathias, Sebastián |
| Datos sintéticos y evidencia | 15 | Generador con semilla, ground truth, diccionario de datos, justificación de realismo, trazabilidad y métricas | Rafael, Mathias |
| Responsible AI | 10 | Explicabilidad, privacidad, límites, análisis de sesgos y uso responsable; docs/responsible_ai.md | Gino, Rafael, Anderson |
| Presentación y storytelling | 10 | Pitch claro, demo en vivo, impacto y respuesta a preguntas, roadmap | Gino, Jesús, Alberto |

### Pesos de la guía impresa

La mitad de la nota está en rigor analítico y calidad técnica. La innovación pesa 10. El esfuerzo se reparte en esa proporción.

| **Criterio** | **Peso** | **Qué entregamos** | **Dueños** |
|---|---|---|---|
| IA y analítica | 25 | Escalera de tres escalones, métricas en datos no vistos, frontera seguridad-gasto, calibración, ablaciones, ejemplos de error, confianza por recomendación | Gino, Rafael |
| Calidad técnica | 25 | Tres capas, contratos, pruebas de varias familias, estrés, mutaciones, fuzz, determinismo, secretos fuera, funcionamiento sin red | Anderson, Mathias, Sebastián |
| Valor y definición del problema | 15 | Usuario, decisión y criterio de éxito escritos; datos oficiales verificados; 2 o 3 conversaciones | Gino |
| Producto y UX | 15 | Un número, su porqué en soles y fechas, sus límites; aprobar o rechazar; accesibilidad mínima | Jesús, Alberto |
| Innovación y diferenciación | 10 | Decisión por calendario de pagos con incertidumbre calibrada; técnica elegida por evidencia; abstención honesta | Gino |
| Demo y evidencia | 10 | Demo en vivo en local, video de respaldo, resultados reproducibles con una semilla | Todos |

## 4. Problema y usuario

Quien no cobra un sueldo fijo vive un problema de fechas más que de montos: el alquiler o la cuota vencen antes de que entre el dinero. Las herramientas de presupuesto asumen un ingreso mensual estable y no le sirven.

### Evidencia (abrir cada fuente antes de llevar un número al pitch)

| **Dato** | **Fuente** | **Estado** |
|---|---|---|
| 90.8 % de los trabajadores independientes es informal (ENAHO 2022) | BCRP, revista Moneda | Sin verificar en origen |
| Unos 4.4 millones de independientes trabajan en zonas urbanas | Diario Correo | Sin verificar en origen |
| Ingreso promedio mensual por trabajo: S/1,887 en 2025 | INEI, vía La República | Sin verificar en origen |
| 85 % dijo que sus ingresos no alcanzaron para sus gastos al menos una vez en el año; solo 21 % pudo calcular un interés simple | Encuesta de capacidades financieras SBS 2022, vía Andina | Sin verificar en origen |
| Bienestar financiero 59.8 de 100; lo más bajo: score crediticio, cumplir metas y estrés financiero | Índice Experian 2026, vía El Peruano | Sin verificar en origen |

Regla: al pitch van solo las cifras que alguien del equipo abrió en su fuente (Alberto o Rafael las verifican hoy). Consecuencia de diseño: si solo 21 % calcula un interés simple, las explicaciones van en soles y fechas, nunca en tasas.

### Antecedentes y lección aplicada

| **Antecedente** | **Qué pasó** | **Lección** |
|---|---|---|
| BBVA AI Factory | Publicó un modelo que predice el saldo a 30 días con bandas de incertidumbre. No trata ingresos irregulares. | El pronóstico no es lo novedoso; lo es aplicarlo a ingresos irregulares y convertirlo en una decisión diaria. Lo decimos nosotros antes que el jurado. |
| Even | Convirtió ingresos irregulares en un sueldo promedio y lo retiró: el problema real era de fechas. | El centro es el calendario de pagos, no el promedio. |
| Hello Digit | Ahorro automático que prometía no sobregirar y sobregiró cuentas; hubo acción del CFPB. | Nada se ejecuta; toda propuesta se verifica en el escenario pesimista y la persona decide. |

### Validación con personas (2 o 3 conversaciones de 15 minutos) [propuesto]

Se presentan como prueba de comprensión con N personas, no como validación estadística. No se registra ningún dato personal ni financiero: solo frases y reacciones.

- **1.** Cuéntame la última vez que te faltó plata para algo con fecha fija. ¿Qué hiciste?
- **2.** ¿Cómo decides hoy cuánto puedes gastar en un día?
- **3.** Mostrar la pantalla principal sin explicar nada: ¿qué entiendes de este número?
- **4.** ¿Qué tendría que pasar para que le creas?
- **5.** Si la herramienta te propone apartar S/20 hoy, ¿lo aceptarías? ¿Qué necesitarías ver?

Dueña de las conversaciones: Alberto, con Jesús como segundo. Se anotan en docs/conversaciones.md con N y fecha.

## 5. Solución y experiencia

El flujo transforma un hallazgo del modelo en una decisión clara y accionable, en tres pantallas.

| **Pantalla** | **Qué muestra** | **Qué decide la persona** |
|---|---|---|
| Hoy | "Hoy puedes gastar hasta S/45." Semáforo de los próximos 14 días. Próximos pagos con fecha y si están cubiertos. | Cuánto gastar hoy. |
| Por qué | Fundamento: cuánto se espera que entre (rango), qué está reservado y para qué. Límites: qué no sabe el modelo. Nivel de confianza: alto, medio o bajo. | Si confía en el número. |
| Plan propuesto | Una propuesta en simulación: apartar S/30 para la cuota del 28, con el efecto antes y después. | Aprobar o rechazar. |

### Cómo se calcula el número de hoy (corrige la fórmula de la v3)

La v3 repartía el total de 14 días y no veía el orden de los pagos. Ahora se calcula por fecha de pago y se toma el mínimo. Para cada pago con fecha d dentro de la ventana de 14 días:

permitido(d) = (saldo + ingreso_conservador(d) - pagos_con_fecha_hasta(d) - colchon) / dias_hasta(d)

numero_de_hoy = max(0, min(permitido(d) para cada pago con fecha y para el dia 14))

- **ingreso_conservador(d):** el de un pago a d días es el cuantil elegido del ingreso acumulado al mayor horizonte h de {3, 7, 14} con h menor o igual a d. Si d es menor que 3, es cero. Subestima a propósito.
- **Parámetros:** el cuantil conservador es el P20 y el colchón es un parámetro de config.yaml [por fijar antes de ver resultados].
- **Ejemplo de prueba:** saldo 100, pago de 300 el día 3, ingreso de 400 el día 10, colchón 0. permitido(3) = (100 - 300) / 3, que es menor que 0. El número es 0 y el mensaje dice "no alcanza para el pago del día 3: faltan S/200". Con la fórmula de la v3 daba un número positivo. Es la primera prueba del motor.

### Aclaraciones de implementación (resueltas al comparar con los documentos del equipo)

Los documentos Formula_Gasto_Diario_Permitido.docx y Determinacion_Limite_Final.docx, escritos por el equipo, coinciden con esta fórmula. Para que nadie programe una versión distinta, quedan fijadas estas precisiones:

- **Nombre:** en el código y en los contratos la cifra se llama numero_hoy (entero en soles), no numero_de_hoy.
- **Ingreso conservador:** el ingreso conservador de un pago a d días NO es una estimación exacta hasta el día d: es el cuantil del mayor horizonte h de {3, 7, 14} con h menor o igual a d, y 0 si d es menor que 3. Subestima a propósito, nunca sobrestima.
- **Pago de hoy:** si un pago vence hoy (d igual a 0), el divisor es max(d, 1) para no dividir entre cero.
- **Redondeo:** el número de hoy se redondea siempre hacia ABAJO a soles enteros y el faltante hacia arriba. Nunca se redondea a favor del gasto.
- **Qué pago se nombra:** el mensaje de falta nombra el pago que LIMITA (el punto de control donde se alcanza el mínimo), que no siempre es la obligación más próxima.
- **Qué cuenta como pago con fecha:** alquiler, servicios, deuda (cuotas y préstamos ya existentes) y suscripción. No son compromisos los gastos discrecionales.
- **Reutilización:** esos dos documentos se convierten en kb/calculo_numero_hoy.md y kb/glosario.md para el asistente de la opción C y se usan como texto base de la pantalla Por qué.

### Semáforo, confianza y propuestas

- **Semáforo por pago:** Verde: el pago queda cubierto con el cuantil P5. Ámbar: cubierto con P50 pero no con P5. Rojo: no cubierto ni con P50. No se llama probabilidad: cuatro cuantiles no la dan sin simulación. La calibración se reporta aparte.
- **Confianza (alta, media, baja):** depende del ancho relativo del rango a 14 días, (P80 - P5) / max(P50, 1), y de las semanas de historia. Con menos de 4 semanas de historia la confianza es baja y no se propone nada más allá del número de hoy. Los umbrales se fijan antes de ver resultados [por fijar].
- **Propuestas:** una sola en el MVP: apartar S/X hoy para el pago Y. Solo se muestra si, aplicada, todos los pagos con fecha siguen cubiertos en el escenario P5. Lleva fundamento, límites, confianza y el efecto antes y después [propuesto].
- **Control humano:** la persona aprueba o rechaza; se registra la decisión y no se ejecuta nada.

### Accesibilidad mínima (suma en Producto y UX)

- **Legible:** texto de al menos 16 px y contraste suficiente; lectura en celular sin desplazarse de lado.
- **No solo color:** el semáforo usa texto y símbolo además del color; el número y el porqué se entienden sin color.
- **Lenguaje:** soles y fechas, nunca tasas; una idea por pantalla.
- **Verificación:** Alberto lo comprueba con la prueba de comprensión del punto 4 y con navegación por teclado.

Texto obligatorio en cada pantalla: "Orientación educativa basada en una simulación con datos ficticios. No es asesoría financiera ni ejecuta operaciones."

## 6. Datos

### Contrato de datos (el recomendado por la guía)

| **Campo** | **Descripción** |
|---|---|
| customer_id | Identificador ficticio de la persona |
| transaction_id | Identificador único del movimiento |
| fecha_hora | Fecha y hora del movimiento |
| monto | Importe, positivo para ingresos y negativo para gastos |
| moneda | PEN |
| tipo | Ingreso o gasto |
| categoria | Alquiler, servicios, alimentación, transporte, deuda, suscripción, otros |
| comercio | Nombre ficticio |
| saldo | Saldo después del movimiento (opcional) |
| ingreso_recurrente | Marca opcional de ingreso recurrente |
| etiquetas de referencia | es_duplicado, es_atipico, pago_con_fecha, arquetipo. Verdad conocida por el generador, usada SOLO para evaluar |

Regla anti fuga: las etiquetas de referencia nunca entran al modelo, al motor ni a la interfaz. La ingesta INFIERE los pagos con fecha (mismo comercio, monto parecido y día del mes repetido) y la evaluación compara esa inferencia con la etiqueta. Rafael escribe una prueba que falla si una columna de etiqueta aparece en las variables del modelo.

### Generador sintético (dueño: Rafael)

- **Tamaño:** 400 personas ficticias, 24 meses de movimientos, de enero del año 1 a diciembre del año 2, generados por reglas con ruido y semilla fija.
- **Cinco arquetipos:** conductor por aplicativo, vendedora con cobros pequeños y frecuentes, técnico freelance con pagos grandes y espaciados, comisionista, y asalariado quincenal como grupo de control. Si el generador se atrasa, se corta a 3 arquetipos.
- **Realismo peruano:** campaña escolar en marzo, Fiestas Patrias en julio, Navidad en diciembre; recibos de alquiler, luz, agua, internet y celular; montos en soles.
- **Privacidad:** sin nombres, DNI, teléfonos, cuentas ni identificadores reales, tampoco del equipo.
- **Muestra para el equipo:** una carpeta data/muestra/ con 20 personas y 24 meses, publicada en el repositorio antes de las 11:00, para que nadie espere al generador completo.

### Escenarios difíciles que el generador inyecta

| **Escenario de la guía** | **Cómo se inyecta** | **Cómo lo trata el sistema** |
|---|---|---|
| Ingresos irregulares | Caso base de cuatro arquetipos | Pronóstico por cuantiles |
| Suscripciones duplicadas | Dos cobros iguales del mismo comercio en el mismo periodo | Se mantiene la detección y el aviso |
| Movimientos duplicados | Copia exacta con otro transaction_id | La ingesta los elimina y lo reporta |
| Cambios de patrón | Una persona cambia de arquetipo a mitad de año | El rango se ensancha y la confianza baja |
| Datos incompletos | Campos vacíos en categoría o comercio; días sin registro | Validación de entrada y valores por defecto documentados |
| Transacciones atípicas | Gasto o ingreso muy fuera de lo habitual | Se marcan y no entran al cálculo de lo recurrente |

### Partición, robustez y calidad

| **Tema** | **Definición** |
|---|---|
| Partición | Por fecha y por personas, nunca aleatoria. Entrenamiento: meses 1 a 16. Validación: 17 a 20. Prueba: 21 a 24, con el 20 % de las personas (80) que nunca entran al entrenamiento. Hay un diciembre en entrenamiento (mes 12) y otro en prueba (mes 24). Hiperparámetros solo con validación. |
| Generador perturbado | Otra semilla y otros parámetros: volatilidad por 1.5, nivel de ingreso 20 % menor, otra mezcla de arquetipos. Se usa solo para la tabla de robustez, nunca para elegir modelo. |
| Calidad y trazabilidad | Volumen, cobertura temporal y distribución de montos por arquetipo; valores faltantes, duplicados y casos extremos antes y después de la limpieza; semilla y versión del generador. |
| Sesgos | Resultados por arquetipo, para verificar que el modelo no funciona solo para el asalariado. |
| Plausibilidad | Ingreso mensual sintético comparado con el promedio del INEI; proporción de personas con al menos un mes en déficit comparada con el 85 % de la encuesta de la SBS. |
| Honestidad del alcance | Los datos son sintéticos: lo que se demuestra es que el método recupera estructura conocida, no precisión en el mundo real. Se dice en el README y en el pitch. |
| Diccionario y realismo | docs/diccionario_datos.md: cada campo con tipo, rango, origen en el generador y supuesto; justificación de realismo con la comparación contra INEI y SBS. Dueño: Rafael. |
| Ground truth | Las etiquetas del generador miden la detección: precisión y recall de duplicados, atípicos y pagos con fecha inferidos. Nunca entran al modelo ni al motor. |
| Datos sensibles | El contrato no incluye edad, género, ubicación ni nombre. Si un archivo los trae, la ingesta los descarta y lo avisa (lista variables_sensibles en config). |

## 7. Inteligencia: modelo, comparación y evaluación

### Objetivo del pronóstico

Ingreso acumulado a 3, 7 y 14 días, cuantiles 5, 20, 50 y 80. Se entrena un modelo por horizonte y por cuantil y se ORDENAN los cuantiles después de predecir para que no se crucen. Las tres técnicas estiman el mismo acumulado, para que la comparación sea justa.

### Escalera de comparación (dueños: Rafael las reglas, Gino el modelo)

| **Escalón** | **Técnica** | **Para qué sirve** |
|---|---|---|
| 1. Regla ingenua | Ingreso promedio mensual dividido entre 30 y multiplicado por h | Piso de comparación: lo que haría cualquiera |
| 2. Regla robusta | Percentiles empíricos del ingreso acumulado en ventanas de h días de las últimas 8 semanas | Alternativa sencilla sin aprendizaje automático |
| 3. Modelo | LightGBM con regresión por cuantiles; variables: día de la semana, época del año, ingreso de las últimas 4 y 8 semanas, días desde el último ingreso, número de ingresos en 28 días. Plan B si falla la instalación: GradientBoostingRegressor de scikit-learn con pérdida de cuantil | Solo se adopta si mejora al escalón 2 |

El arquetipo es una etiqueta de evaluación y NO es una variable del modelo. Si el modelo no supera a la regla robusta, se presenta la regla robusta y se dice. Elegir con evidencia puntúa; inflar la técnica penaliza.

### Métricas

| **Tipo** | **Métrica** | **Cómo se mide** |
|---|---|---|
| Analítica | MAE de la mediana y pérdida pinball por cuantil | En la prueba, por arquetipo y total. Sin MAPE: se rompe en semanas con ingreso cero |
| Analítica | Calibración | Fracción de casos en que el ingreso real superó el P20 pronosticado; debe rondar 80 % |
| Decisión | Pagos con fecha descubiertos | Simulación día a día de los meses de prueba; la persona gasta cada día lo que la herramienta permite [SUPUESTO]; descubierto es saldo menor que cero el día del pago |
| Decisión | Gasto diario permitido promedio | Promedio de soles por día que cada método permite gastar |
| Decisión | Frontera de seguridad | El mismo método con el cuantil conservador en P5, P20, P50 y P80: cuatro pares (descubiertos, gasto permitido) por método. La regla ingenua se dibuja con factores 0.5, 0.75 y 1.0 |
| Analítica | Precisión y recall de alertas y de duplicados | Contra las etiquetas de referencia; tasa de falsos positivos |
| Producto | Tiempo hasta el insight y claridad | Segundos hasta entender el número y personas que lo explican con sus palabras (N pequeño, se dice) |
| Ingeniería | Pruebas, reproducibilidad, latencia | Suite de pruebas; misma semilla, misma tabla; tiempo por pantalla |

Puntos de referencia en la frontera: "gastar S/0" (cero descubiertos y cero gasto) y "gastar el promedio fijo" (más gasto y más descubiertos). Con ellos se ve que el modelo aporta algo más que un truco.

### Regla de adopción (se escribe en el README antes de correr nada)

El modelo se adopta si, con el mismo porcentaje de pagos descubiertos que la regla robusta, permite más gasto; o con el mismo gasto, deja menos pagos descubiertos. Debe cumplirlo en la prueba y también en el generador perturbado. El umbral numérico de mejora se fija antes de ver resultados [por fijar].

### Cómo llevamos la evaluación al límite

- **Pares de semillas:** cada cambio se mide por pares sobre al menos 20 semillas del generador, con la diferencia media y un intervalo bootstrap de 95 %. Lo que no mejora se rechaza y se anota en DECISIONES.md.
- **Ablaciones:** quitar la época del año, quitar la historia reciente, LightGBM contra scikit-learn, 3 contra 5 arquetipos. Se informa qué variable aporta y cuál no.
- **Robustez:** tabla en la prueba y tabla en el generador perturbado, lado a lado, con la diferencia.
- **Ejemplos de error:** al menos tres casos reales donde el modelo falló: qué predijo, qué pasó, por qué y qué límite revela.
- **Honestidad:** si el modelo gana en el generador de entrenamiento y pierde en el perturbado, se dice y se presenta la regla robusta.

### Modelo de lenguaje y capa generativa opcional

El Challenge pack lista la IA generativa útil entre las capacidades que se observan (asistente, explicaciones en lenguaje claro) y advierte que no basta un chatbot genérico. La guía impresa dice que un modelo externo solo se usa si las reglas finales lo autorizan y que BBVA no da claves. Por eso el núcleo no depende de un modelo de lenguaje y la capa generativa es opcional: Gino decide con la respuesta de la organización [propuesto]. El diseño completo está en Diseno_Opcion_B_capa_generativa.docx: proveedor OpenAI con la cuenta propia del equipo, entrada minimizada sin identificadores, prompts, verificador determinista de cifras, respaldo a plantilla y criterio de apagado. Se activa solo si la organización lo autoriza por escrito, el control 1 salió bien y es antes de las 17:00.

Opción C, asistente conversacional del semáforo: una pantalla de chat donde la persona pregunta por su número, sus pagos y escenarios ("y si cobro 200 el día 5"). Usa el motor y el modelo como herramientas de ML, una base de conocimiento propia con búsqueda local (RAG) y, si se activa, un LLM para entender y redactar con cada cifra verificada. Funciona completo sin LLM, por lo que no depende de la autorización. Se inspira en las lecciones del copiloto del bot_diagnosis, sin reutilizar código, datos ni playbooks. Diseño completo en Diseno_Opcion_C_asistente_del_semaforo.docx; nivel P2, con puntos de corte a las 13:00, 16:00 y 17:30.

Fuera del MVP [propuesto]. Las explicaciones se redactan con plantillas a partir del desglose calculado, con cifras que salen del motor. Si la organización autoriza uno externo, entra después del congelamiento: solo recibe datos ficticios, toda cifra de su respuesta se contrasta con el desglose y, si no coincide, se muestra la plantilla.

## 8. Arquitectura, contratos y seguridad

Tres capas separadas, como pide la guía. Cada capa se prueba por separado y se comunica con la siguiente por un contrato escrito. Streamlit llama a un solo módulo (servicio); no hay un servidor aparte [propuesto].

| **Capa y módulo** | **Responsabilidad** | **Carpeta** | **Dueño** |
|---|---|---|---|
| Datos: generador | Personas, arquetipos, escenarios difíciles, generador perturbado, semilla, muestra | src/datos | Rafael |
| 1. Ingesta | Validar el esquema, eliminar duplicados, tratar faltantes, marcar atípicos, inferir pagos con fecha y recurrentes, avisar de suscripciones duplicadas, reporte de calidad | src/ingesta | Mathias |
| Reglas | Regla ingenua y regla robusta con la misma firma que el modelo | src/reglas | Rafael |
| 2. Modelo | Variables, entrenamiento por horizonte y cuantil, orden de cuantiles, calibración, predicción | src/modelo | Gino |
| 2. Motor | Número de hoy por fecha de pago, semáforo, confianza, verificador del escenario P5, propuestas, desglose trazable | src/motor | Sebastián |
| Servicio | Contratos, fachada única, configuración, registro de cada recomendación, orquestación, modo de respaldo | src/servicio, src/contratos | Anderson |
| 3. Interacción | Pantallas Hoy, Plan propuesto, Por qué, carga y calidad, evaluación | src/app | Jesús, Alberto |
| Evaluación | Simulación de la decisión, frontera, tablas, ablaciones, ejemplos de error | eval/ | Rafael, Gino |
| Generativa (opcional, opción B) | minimizar, prompts, verificador, proveedor de OpenAI y redactar; nace apagada y solo se enciende por configuración si se cumplen las condiciones del diseño | src/generativa | Sebastián, Gino, Anderson |
| Asistente (opcional, opción C) | Guardia de entrada, intención (ML y LLM), herramientas (consultar y simular), RAG sobre kb/, plantillas, verificador y flujo; funciona sin LLM | src/asistente, kb/, data/chat | Anderson, Gino, Sebastián, Rafael, Mathias |

### Contratos entre módulos (el Anexo A tiene las firmas)

generador  -> data/*.csv                      (contrato de datos de la sección 6)

ingesta.cargar(origen)            -> (movimientos_limpios, ReporteCalidad, pagos_inferidos)

modelo.predecir(historia, fecha)  -> Pronostico   {h: {p5, p20, p50, p80}} h en 3, 7, 14

reglas.regla1 / regla2            -> Pronostico   (misma forma que el modelo)

motor.decidir(estado, pron, cfg)  -> Decision     (numero_hoy, por_pago, confianza, desglose, propuestas)

servicio.consultar(id, fecha, metodo) -> Decision + registro;  servicio.responder(propuesta_id, aprobar_o_rechazar)

app: solo llama a servicio.*; nunca importa modelo, motor ni ingesta

### Configuración, registro y seguridad

- **Parámetros fuera del código:** config/config.yaml guarda cuantiles, horizontes, colchón, umbrales de confianza, ventana y semillas. Ningún valor mágico en el código.
- **Registro:** cada recomendación se guarda en un archivo JSON por línea con sus entradas, versión del generador y del modelo, semilla y hash de la configuración, para poder reproducirla.
- **Secretos:** variables de entorno; .env.example sin valores; .env en .gitignore; nada de claves en el repositorio ni en la demo.
- **Validación y errores:** tipos, rangos, fechas y tamaño de archivo; los mensajes de error dicen qué corregir; ninguna pantalla queda en blanco.
- **Texto libre:** el texto libre y las descripciones de movimientos son datos, nunca instrucciones.
- **Dependencias:** versiones fijadas en requirements.txt, licencias revisadas y atribución en ATRIBUCIONES.md.

### Responsible AI, sesgos, seguridad y observabilidad (Challenge pack)

- **Explicabilidad:** cada Decision trae fundamento, evidencia (semanas de historia, número de ingresos observados, rango), supuestos, límites y confianza. Dueño: Sebastián; la pantalla Por qué la muestra: Alberto.
- **Variables sensibles:** el contrato no tiene edad, género, ubicación ni nombre. La ingesta descarta esas columnas si llegan y lo avisa. Una prueba falla si una variable del modelo aparece en variables_sensibles. Dueños: Mathias y Gino.
- **Control de sesgos:** resultados por arquetipo, por tercil de ingreso y por tercil de volatilidad (pagos descubiertos, gasto permitido y calibración del P20). Se informa la brecha entre el mejor y el peor grupo; el umbral de alerta se pre-registra [por fijar]. Si un grupo queda peor, se dice y se muestra. Dueño: Rafael.
- **Límites de recomendación:** la herramienta orienta y no sustituye asesoría; no promete resultados; el aviso va en cada pantalla. Dueños: Jesús y Alberto.
- **Privacidad por diseño:** datos sintéticos sin PII. La ingesta enmascara patrones de DNI, teléfono, correo o tarjeta y los cuenta en el reporte; los registros no guardan el archivo original. Dueño: Mathias.
- **Seguridad técnica:** secretos fuera del código; dependencias fijadas con versiones y licencias, y revisión de vulnerabilidades si hay red [propuesto]; validación de entradas; sin APIs externas en el núcleo; sin prompts en el núcleo, así que no hay inyección de prompts. Si se agrega la capa generativa, el texto libre se trata como datos. Dueño: Anderson.
- **Trazabilidad auditable:** scripts/auditar_recomendacion.py reconstruye datos, variables, modelo y configuración de cualquier recomendación desde su identificador. Dueño: Anderson.
- **Observabilidad:** logs/salud.jsonl guarda latencia, método, respaldo y error por consulta; servicio.salud() resume p50, p95 y tasas de error y de respaldo; la pantalla Evaluación lo muestra. Dueños: Anderson y Alberto.
- **Documento:** docs/responsible_ai.md reúne estas áreas con su evidencia. Coordina Gino.

## 9. Pruebas al límite

Se hacen en capas. P0 es obligatorio y entra antes del congelamiento. P1 entra si el control 2 salió bien. P2 es el límite: se hace solo con el equipo holgado y se corta primero.

| **Familia** | **Qué comprueba** | **Criterio de éxito** | **Dueño** | **Nivel** |
|---|---|---|---|---|
| Unitarias | Cada función de ingesta, reglas, modelo, motor y servicio | Pasan todas; cobertura de motor, ingesta y servicio de al menos 80 % [SUPUESTO] | Cada dueño | P0 |
| Caso del orden de pagos | Saldo 100, pago 300 el día 3, ingreso el día 10 | Número 0 y mensaje con "faltan S/200" | Sebastián | P0 |
| De propiedades | Con hypothesis: el número nunca es negativo; más saldo no lo baja; más pagos no lo suben; los cuantiles salen ordenados; con el número de hoy gastado, el escenario P5 no descubre pagos | Cero contraejemplos en 1,000 casos por propiedad | Sebastián, Gino | P0 |
| De contrato | Cada módulo cumple la forma de entrada y salida del Anexo A | Falla si cambia un campo sin aprobación | Anderson | P0 |
| Anti fuga | Ninguna etiqueta de referencia entra al modelo ni al motor | La prueba falla si aparece una | Rafael | P0 |
| Datos difíciles | Duplicados, suscripción repetida, cambio de patrón, datos incompletos, atípicos | Reporte con conteos esperados | Mathias | P0 |
| Integración y e2e | Del archivo a la pantalla con Streamlit AppTest | Las tres pantallas abren y muestran un número | Anderson, Jesús | P0 |
| Determinismo | Misma semilla produce el mismo hash de la tabla de resultados, con distintos PYTHONHASHSEED | Hash idéntico en las laptops del equipo | Anderson | P0 |
| Fuzz de la ingesta | Nulos, textos de 5,000 caracteres, unicode, fechas inválidas, montos NaN e infinito, archivo vacío, columnas extra | 0 excepciones no controladas; mensaje claro | Mathias | P1 |
| Escenarios de estrés | Lista del Anexo C: 20 o más casos extremos del motor y la ingesta | Sin errores; los casos inviables se declaran, no se ocultan | Sebastián, Mathias | P1 |
| Mutaciones | Cambios deliberados en el motor (por ejemplo menor en vez de menor o igual, quitar el colchón, cambiar P5 por P50, invertir un signo) y se verifica que alguna prueba falle | Al menos 80 % detectadas; las equivalentes se explican | Anderson | P1 |
| Escala y tiempos | 400 y 4,000 personas: tiempo de generar, evaluar y responder una consulta (p50 y p95) | Línea base medida; pantalla en menos de 2 s [SUPUESTO] | Anderson | P1 |
| Pares de semillas | Cada cambio de modelo contra la regla robusta, 20 o más semillas, con intervalo bootstrap | Tabla con diferencia media e intervalo | Gino, Rafael | P1 |
| Accesibilidad y UX | Teclado, contraste, texto con símbolo en el semáforo, celular | Lista de comprobación firmada por Alberto | Alberto | P1 |
| Seguridad | Búsqueda de secretos en el historial, .env ignorado, validación de entradas | Cero secretos; cero rutas sin validar | Anderson | P1 |
| Versiones de Python | Resultados idénticos en dos versiones de Python | Mismo hash | Anderson | P2 |
| Adversas a la narrativa | 10 preguntas del jurado ensayadas con la evidencia a mano | Respuesta con cifra y fuente | Gino | P1 |
| Variables sensibles | Ninguna variable del modelo ni del estado aparece en variables_sensibles; la ingesta descarta columnas sensibles | La prueba falla si aparece una | Gino, Mathias | P0 |
| PII | Patrones de DNI, teléfono, correo y tarjeta se enmascaran y se cuentan | Cero PII en los movimientos limpios | Mathias | P0 |
| Supuestos y evidencia | Toda Decision trae supuestos, evidencia, límites y confianza no vacíos | Presentes en el 100 % de los casos | Sebastián | P0 |
| Sesgos | Métricas por arquetipo, tercil de ingreso y tercil de volatilidad | Tabla con la brecha y su alerta | Rafael | P1 |
| Trazabilidad | Reconstruir una recomendación desde su identificador | Mismas entradas y misma decisión | Anderson | P1 |
| Salud y observabilidad | logs/salud.jsonl y servicio.salud() | p50, p95 y tasa de error visibles | Anderson, Alberto | P1 |

Orden de recorte: P2, luego Escala y tiempos, luego Mutaciones, luego Fuzz. Nunca se recortan las P0 ni la tabla de resultados, que valen la mitad de la nota.

## 10. Repositorio y flujo de trabajo del equipo

Un solo repositorio por equipo. Si la organización no confirma el mecanismo de entrega (carpeta o repositorio y quién accede), se entrega una carpeta con el mismo contenido [por confirmar].

repo/

README.md  DECISIONES.md  TRANSPARENCIA.md  ATRIBUCIONES.md  Makefile  requirements.txt

.env.example  .gitignore  config/config.yaml

src/ contratos  datos  ingesta  reglas  modelo  motor  servicio  app

eval/   tests/ unit property contract integracion e2e fixtures

data/ muestra  generado/   docs/ datos.md evaluacion.md arquitectura.md conversaciones.md   pitch/

### Reglas del repositorio

- **Ramas:** main siempre ejecutable. Se trabaja en ramas feat/<persona>-<tema>. Los cambios entran por pull request revisado por una persona de otro módulo.
- **Commits:** prefijos feat, fix, test, docs, data y eval; commits pequeños y frecuentes. El historial es la evidencia de que el trabajo se hizo durante el evento.
- **Contratos:** cualquier cambio en src/contratos o en el Anexo A necesita la aprobación de Anderson y de Gino, y se anota en DECISIONES.md.
- **Antes de fusionar:** un pull request solo se fusiona si make test está verde.
- **Etiquetas de versión:** v0-control1 (13:00), v1-control2 (16:00), v2-congelado (18:00), v3-final (domingo).
- **Comandos:** make setup (instalar), make datos (generar con la semilla), make test, make eval (tabla de resultados) y make demo (levantar la interfaz). El README permite que el jurado ejecute todo con esos comandos.
- **Dueños de carpeta:** cada persona es dueña de su carpeta. Nadie edita una carpeta ajena sin avisar a su dueño.
- **Entorno común:** todos instalan la misma versión de Python, la que ya tenga la mayoría, y las dependencias con requirements.txt antes de las 11:00.
- **Trabajo en paralelo:** el Anexo E explica cómo se trabaja en ramas separadas sin pisarse: una carpeta por dueño, cuatro ventanas de integración, comandos paso a paso, revisión cruzada y protección de main.

### DECISIONES.md (el formato de nuestro guion técnico)

Cada decisión importante se anota con cuatro columnas: decisión, dato que la respalda, qué decidimos y qué haríamos distinto. Es la fuente del pitch y de las preguntas del jurado. Las alternativas rechazadas con datos se anotan igual.

## 11. Equipo y responsabilidades (7 personas)

| **Persona** | **Rol** | **Construye** | **Entrega a** | **Responde de** |
|---|---|---|---|---|
| Mathias | Backend: ingesta y calidad | Validación, duplicados, suscripciones, atípicos, pagos inferidos, reporte de calidad, carga de archivo nuevo sin tocar código | Servicio, Rafael, Gino | Capa 1 y datos difíciles |
| Sebastián | Backend: motor de decisión | Número por fecha de pago, semáforo, confianza, verificador P5, propuesta, desglose trazable | Servicio, interfaz | Motor y propiedades |
| Anderson | Backend: servicio, integración y calidad | Contratos, fachada, config, registro, Makefile, e2e, determinismo, escala, mutaciones, seguridad, README de ejecución | Todos | Calidad técnica y entrega |
| Rafael | Data science | Generador, escenarios, perturbado, muestra, reglas 1 y 2, simulación de la decisión, frontera, docs de datos y evaluación | Gino, Mathias, interfaz | Datos, evaluación y ejemplos de error |
| Gino Vieyra | Machine learning y líder | Variables, cuantiles por horizonte, orden, calibración, ablaciones, regla de adopción, pares de semillas; decisiones en los controles; pitch | Sebastián, Rafael | IA y analítica y pitch |
| Jesús | Frontend 1 | Pantallas Hoy y Plan propuesto, estados vacíos y de error, modo de respaldo con datos precargados | Jurado y demo | Producto y demo |
| Alberto | Frontend 2 | Pantalla Por qué, carga de archivo y reporte de calidad, vista de evaluación y frontera, accesibilidad, conversaciones, video | Jurado y demo | UX y evidencia visual |

### Quién necesita qué de quién (lo que hace correlativo al plan)

| **Necesita** | **De** | **Hora** | **Para qué** |
|---|---|---|---|
| Esquemas y fixtures de contratos | Anderson | 10:45 | Que todos escriban contra la misma forma desde el inicio |
| Muestra de 20 personas | Rafael | 11:00 | Que ingesta, modelo y motor trabajen sin esperar el generador completo |
| Datos completos de 400 personas | Rafael | 12:30 | Entrenar y medir |
| Ingesta v0 con pagos inferidos | Mathias | 12:00 | Motor y servicio |
| Regla 2 con la forma de Pronostico | Rafael | 12:30 | Flujo de punta a punta del control 1 |
| Motor con el caso del orden de pagos | Sebastián | 12:30 | Número de hoy en pantalla |
| Servicio.consultar funcionando con la regla 2 | Anderson | 13:00 | Pantalla Hoy real y control 1 |
| Modelo v1 con la forma de Pronostico | Gino | 15:30 | Control 2 y frontera |
| Simulación de decisión y primera frontera | Rafael, Gino | 18:30 | Tabla de resultados y pitch |

### Tareas nuevas por el Challenge pack (qué hace cada uno)

Cada plan individual detalla estas tareas con su forma, su hora y su prueba.

| **Persona** | **Qué hace de nuevo** | **Entregable** | **Hora** |
|---|---|---|---|
| Anderson | Registro de salud (latencia, errores y respaldo) y servicio.salud(); script que audita una recomendación desde su identificador; revisión y fijado de dependencias con licencias; diagrama alineado con la arquitectura de referencia del pack; campos nuevos en los contratos | logs/salud.jsonl, scripts/auditar_recomendacion.py, docs/arquitectura.md | 16:00 a 18:00; domingo |
| Rafael | Diccionario de datos con justificación de realismo; análisis de sesgos por arquetipo, ingreso y volatilidad con alerta pre-registrada; ground truth documentado; sección de sesgos de Responsible AI | docs/diccionario_datos.md, eval/resultados/sesgos.csv | 18:00 a 19:30; domingo |
| Mathias | Detector y enmascarado de PII; descarte de columnas sensibles con aviso; campos nuevos en ReporteCalidad | ingesta con PII y sensibles, pruebas | 13:00 a 16:00 |
| Sebastián | Supuestos y evidencia en cada Decision; límites de recomendación fijos; id de registro en el desglose | Decision.supuestos y evidencia | 13:00 a 16:00 |
| Gino | Coordinar Responsible AI y escribir docs/responsible_ai.md; prueba de variables sensibles; decidir la capa generativa con la respuesta de la organización; guion de pitch corto, roadmap y preguntas nuevas | docs/responsible_ai.md, docs/roadmap.md, pitch | Todo el día |
| Jesús | Mostrar supuestos y límites en Hoy; guion cronometrado de la demo de 5 minutos con datos precargados | Pantallas Hoy y Plan, guion de demo | 13:00 a 18:30 |
| Alberto | Paneles de sesgos, salud y auditoría en Evaluación; sección de supuestos y evidencia en Por qué; deck corto y video de 5 minutos | pages/3 y pages/5, deck, video | 16:00 a 19:30; domingo |

### Si se activa la opción B (capa generativa): tareas por persona

Detalle en Diseno_Opcion_B_capa_generativa.docx. T0 es la hora de la autorización. Con T0 después de las 14:30 no se activa.

| **Persona** | **Tarea** | **Hora** |
|---|---|---|
| Gino | Decide activar con las cinco condiciones; fija el umbral antes de evaluar; redacta los prompts; coordina la evaluación de 30 decisiones; decide seguir o apagar a las 17:00 | T0 a T0+90 |
| Anderson | Proveedor de OpenAI con la clave en .env, timeout, reintento y cortacircuitos; salud de la capa; llamada de prueba en las dos laptops | T0 a T0+60 |
| Sebastián | minimizar con lista blanca, verificador de cifras y redactar; pruebas con textos buenos y malos | T0 a T0+90 |
| Rafael | Entrega las 20 decisiones del conjunto de evaluación | T0+30 |
| Mathias | Exporta los patrones de PII de la ingesta para que los reutilice el verificador; revisa la lista blanca | T0 a T0+45 |
| Jesús | Muestra Decision.explicacion en Hoy y en Por qué y la integra en el guion de la demo | T0+90 a T0+150 |
| Alberto | Etiqueta de fuente en pantalla, panel de respaldo en Evaluación y comparación de comprensión | T0+90 a T0+150 |

### Si se llega al corte de la opción C (asistente del semáforo): tareas por persona

Detalle en Diseno_Opcion_C_asistente_del_semaforo.docx. Puntos de corte: A a las 13:00 (si el control 1 salió bien, empieza la fase 1 quien tenga holgura), B a las 16:00 (se integra el flujo si el control 2 salió bien), C a las 17:30 (lo que no pase la evaluación no entra a la demo) y D a las 17:45 (fusión final). El asistente nunca desplaza una prueba P0.

| **Persona** | **Tarea** | **Desde** |
|---|---|---|
| Gino | Intenciones, clasificador ML de TF-IDF y regresión logística, prompts, evaluación del asistente y decisión en cada punto de corte; pre-registro de umbrales | Corte A |
| Sebastián | motor.simular con el parámetro opcional ingresos_extra, plantillas por intención y verificador de salida | Corte A |
| Anderson | Flujo de orquestación, servicio.preguntar y servicio.simular, registro, salud, reutiliza el proveedor de la opción B, prueba de humo chat-humo | Corte A |
| Rafael | Base de conocimiento de 12 documentos (parte de la fórmula escrita por el equipo), RAG con TF-IDF y conjunto de preguntas de entrenamiento | Corte A |
| Mathias | Guardia de entrada y enmascarado de la pregunta antes de registrar | Corte A |
| Jesús | Pantalla de chat con preguntas sugeridas e integración en el guion de la demo; escribe 15 preguntas del conjunto ciego | Corte A |
| Alberto | Accesibilidad y etiquetas de fuente del chat, panel de evaluación del chat y video; escribe 15 preguntas del conjunto ciego | Corte A |

### Reglas de coordinación

- **Canal:** un canal único del equipo; cada hito se avisa con la etiqueta del repositorio.
- **Retrasos:** si una entrega se retrasa más de 30 minutos, el dueño avisa a Gino y se activa la versión simple (datos de la muestra, regla 2, número fijo).
- **Riesgo de carga del líder:** Gino es líder y ML a la vez, y el modelo está en la ruta crítica. Rafael es su respaldo en el modelo y Anderson en la integración. Gino decide en los controles y delega la redacción del pitch en Rafael y Alberto, que él revisa [propuesto].

## 12. Hoja de ruta [SUPUESTO hasta que la organización comunique sus horarios]

| **Hora (Lima)** | **Qué se hace** | **Debe quedar verificable** |
|---|---|---|
| Sábado 10:15 a 11:00 | Todos instalan el entorno. Anderson crea el repositorio, la estructura, los contratos y las fixtures. Rafael publica la muestra. Cada uno crea su rama y su esqueleto con una prueba que pasa. | make test corre en las 7 laptops; contratos fusionados en main |
| Sábado 11:00 a 12:00 | Mathias: ingesta v0. Sebastián: motor con el caso del orden de pagos. Rafael: generador completo y regla 2. Gino: variables y entrenamiento sobre la muestra. Jesús y Alberto: maquetas con Decisiones falsas de las fixtures. | Usuario, decisión, criterio de éxito y regla de adopción escritos en el README. Preguntas a la organización y al mentor enviadas |
| Sábado 12:00 | Enfoque cerrado. Después no se pivota salvo bloqueo técnico grave. | Gino confirma o ajusta la v5 con la respuesta del mentor y la organización |
| Sábado 13:00, control 1 | Flujo de punta a punta con la regla 2: generador, ingesta, regla, motor, servicio y pantalla Hoy. | Etiqueta v0-control1. Si falla, todos vuelven al flujo básico |
| Sábado 13:00 a 16:00 | Modelo por cuantiles, motor completo con semáforo y confianza, plan propuesto, pantalla Por qué, pruebas P0, simulación de la decisión. | Número de hoy calculado desde los datos, con fundamento, límites y confianza |
| Sábado 16:00, control 2 | Una propuesta se explica y la persona puede aprobarla o rechazarla. | Etiqueta v1-control2. Si falla, se presenta solo el número de hoy con su explicación |
| Sábado 16:00 a 18:00 | Integración del modelo, e2e, determinismo, fuzz, estrés, mutaciones, accesibilidad, datos de demo precargados, análisis de sesgos, registro de salud y auditoría de una recomendación. | Todas las P0 en verde |
| Sábado 18:00 | Congelamiento de funciones. Desde aquí solo se corrigen fallas y se miden resultados. | Etiqueta v2-congelado |
| Sábado 18:00 a 19:30 | Primera tabla de resultados y frontera, reproducible con un comando. Tres ejemplos de error. Tabla de sesgos. Borrador del video de respaldo. | make eval produce la tabla, los sesgos y su hash |
| Domingo 8:30 a 11:00 | Se corrigen fallas, se repite la tabla con la misma semilla, README, arquitectura, ATRIBUCIONES y TRANSPARENCIA, docs/responsible_ai.md, docs/diccionario_datos.md, roadmap, video de respaldo. No se construye nada nuevo. | Carpeta de entregables completa |
| Domingo 11:00 a 13:30 | Tres ensayos con cronómetro, respuestas a las preguntas difíciles, demo que corre tres veces seguidas, pitch. | Checklist de salida completo |

Orden de recorte si falta tiempo: pruebas P2, escala, mutaciones; luego el plan propuesto; luego el modelo del escalón 3. Nunca se recortan la evaluación, las pruebas P0 ni el README.

## 13. Entregables obligatorios

| **Entregable** | **Contenido esperado por la guía** | **Archivo o carpeta** | **Responde** |
|---|---|---|---|
| README | Problema, usuario, solución, instrucciones de ejecución y requisitos de entorno; make setup, make datos, make demo y make eval | README.md | Gino, Anderson |
| Código y demo | MVP funcional; ejecución local; credenciales ficticias si aplica | src/ | Todos |
| Datos y metodología | Dataset sintético, generador, diccionario y tratamiento aplicado | data/, docs/datos.md | Rafael, Mathias |
| Evaluación | Casos de prueba, baseline, métricas, resultados y ejemplos de errores | eval/, tests/, docs/evaluacion.md | Rafael, Gino |
| Arquitectura y seguridad | Diagrama simple, componentes, modelos, dependencias y salvaguardas | docs/arquitectura.md | Anderson |
| Pitch | Máximo 10 minutos de presentación y 3 de preguntas (sujeto a confirmación) | pitch/ | Gino |
| Transparencia | Qué hizo el equipo, qué hizo la IA, atribuciones y licencias | TRANSPARENCIA.md, ATRIBUCIONES.md | Gino |
| Responsible AI (pack) | Explicabilidad, privacidad, límites, sesgos medidos, seguridad y trazabilidad | docs/responsible_ai.md | Gino, Rafael, Anderson |
| Diccionario de datos (pack) | Campos, supuestos y justificación de realismo | docs/diccionario_datos.md | Rafael |
| Roadmap (pack) | Próximos pasos sin prometer resultados | docs/roadmap.md y una lámina | Gino |
| Diseño de la opción B | Capa generativa opcional con OpenAI, verificador de cifras, respaldo y criterio de apagado | Diseno_Opcion_B_capa_generativa.docx y src/generativa si se activa | Gino, Sebastián, Anderson |
| Diseño de la opción C | Asistente conversacional del semáforo (LLM, RAG y ML) con modo sin LLM, evaluación ciega y puntos de corte | Diseno_Opcion_C_asistente_del_semaforo.docx, src/asistente, kb/, data/chat | Gino, Sebastián, Anderson, Rafael, Mathias, Jesús, Alberto |

## 14. Prueba de evolución

La organización puede entregar a todos los equipos el mismo cambio sorpresa. Los ejemplos que da la guía ya están previstos.

| **Cambio posible** | **Por qué estamos preparados** | **Qué tener listo** |
|---|---|---|
| Ingresos variables | Es nuestro caso base | Cargar un archivo nuevo con el mismo contrato y obtener resultados sin tocar código (Mathias) |
| Movimientos duplicados | La ingesta ya los elimina | Prueba automática y contador visible en el reporte (Mathias) |
| Recomendación explicable | Cada propuesta trae fundamento, límites y confianza | Plantillas que aceptan un tipo de propuesta nuevo (Sebastián) |

Regla general: parámetros en config.yaml y no en el código, y una prueba automática por cada caso difícil. Así un cambio se adapta y se demuestra en minutos.

## 15. Pitch y demo (dos formatos posibles)

La guía impresa dice 10 minutos de presentación más 3 de preguntas. El Challenge pack sugiere 5 de pitch, 5 de demo y 5 de preguntas. Ninguno está confirmado. Se prepara el formato corto como base (formato A) y se amplía al formato B si la organización lo confirma.

### Formato A: 5 de pitch, 5 de demo y 5 de preguntas (base)

| **Minutos** | **Bloque** | **Contenido** | **Quién** |
|---|---|---|---|
| Pitch 0 a 1 | Problema y usuario | Persona ficticia con ingresos de S/900 y S/300 en semanas seguidas y una cuota que vence antes de cobrar; la decisión que mejoramos | Gino |
| Pitch 1 a 3 | IA y evidencia | Escalera de tres escalones, frontera en la prueba y en el perturbado, pares de semillas, una decisión rechazada con datos y un ejemplo de error | Gino con Rafael |
| Pitch 3 a 4 | Responsible AI | Sesgos medidos por grupo, límites de la recomendación, privacidad y trazabilidad auditable | Rafael |
| Pitch 4 a 5 | Roadmap y cierre | Próximos pasos sin prometer resultados; autocrítica; volver a la persona del inicio | Gino |
| Demo 5 min | Demo en vivo | Número de hoy, porqué con supuestos y límites, propuesta aprobada, archivo con duplicados y PII enmascarada, panel de salud y auditoría de una recomendación | Jesús y Alberto |
| Preguntas 5 min | Respuestas | Cada persona responde su área con cifra y fuente | Todos |

- **Opción C en la demo:** si el asistente de la opción C llega al corte, el minuto de demo incluye tres preguntas al asistente (por qué este número, y si cobro tal día, y una fuera de alcance que rechaza). Si no llega, se dice y no se muestra.

### Formato B: 10 de presentación y 3 de preguntas (si lo confirman)

Es la tabla de minutos que sigue, con el bloque de Responsible AI dentro de Límites y cierre y el roadmap en el cierre.

### Apertura de 30 segundos (plantilla)

"Nuestra herramienta responde una pregunta: ¿cuánto puedo gastar hoy sin fallar a un pago con fecha? Predice el ingreso con un rango, decide por fecha de pago y solo propone lo que aguanta el escenario pesimista. Todo lo que cambiamos lo medimos por pares de semillas, en la prueba y en un generador perturbado, y rechazamos lo que no mejoraba. Sabemos dónde está nuestro punto débil: [completar con el resultado del domingo]."

| **Minutos** | **Bloque** | **Contenido** |
|---|---|---|
| 0 a 1 | Problema | Una persona ficticia con ingresos de S/900 una semana y S/300 la siguiente, y una cuota que vence antes de cobrar |
| 1 a 2 | Usuario y decisión | A quién servimos, qué decisión mejoramos y cómo medimos el éxito. Un dato oficial verificado y una frase de conversación |
| 2 a 5 | Demo en vivo | Cargar datos, ver el número de hoy, abrir el porqué con límites y confianza, aprobar una propuesta. Cargar un archivo con duplicados y mostrar que se limpian |
| 5 a 7 | IA y evidencia | Los tres escalones, la frontera en la prueba y en el perturbado, la calibración, una decisión rechazada con datos y un ejemplo de error |
| 7 a 8:30 | Ingeniería | Diagrama de tres capas, familias de pruebas, estrés y mutaciones, determinismo, funcionamiento sin red, transparencia |
| 8:30 a 10 | Límites y cierre | Qué no hace, supuestos, autocrítica, qué faltaría para datos reales. Volver a la persona del inicio |

### Las decisiones medidas que vamos a poder contar (se llenan con datos)

Formato de DECISIONES.md: decisión, dato, qué decidimos y qué haríamos distinto. Se esperan al menos estas, y cada una solo se cuenta si tiene su medición:

- **1.** orden de pagos en el número de hoy contra el reparto de 14 días: [por medir].
- **2.** modelo contra regla robusta, por pares de semillas y con intervalo: [por medir].
- **3.** qué variable aporta y cuál no, con las ablaciones: [por medir].
- **4.** prueba contra generador perturbado: [por medir].
- **5.** cuantil conservador elegido a partir de la frontera: [por medir].
- **6.** alternativas rechazadas con su dato (por ejemplo, más variables o más arquetipos que no mejoran): [por medir].
- **7.** robustez: fuzz sin excepciones, mutaciones detectadas, hash idéntico: [por medir].
- **8.** escala y tiempos de respuesta: [por medir].

### Autocrítica prevista (decirla antes de que pregunten)

- **Alcance:** los datos son sintéticos; el resultado muestra que el método recupera estructura conocida, no precisión real.
- **Innovación:** el pronóstico ya existe en el mercado; lo nuevo es aplicarlo a ingresos irregulares con decisión por fecha de pago.
- **Validación:** pocas conversaciones y sin estadística; se presentan como prueba de comprensión.
- **Dónde falla:** [completar el domingo con el peor resultado medido: arquetipo, escenario o horizonte donde el modelo no gana].

### Preguntas difíciles y respuesta preparada

| **Pregunta** | **Respuesta** |
|---|---|
| ¿Por qué un modelo y no una regla? | Con la frontera: a igual pagos descubiertos, cuánto más gasto permite. Si no mejora, usamos la regla y lo decimos. |
| ¿Qué pasa si el pronóstico se equivoca? | Por eso se usa un cuantil conservador, se muestra la confianza y solo se propone lo que aguanta el escenario P5. |
| ¿Los datos sintéticos no favorecen a su modelo? | Partición por fecha y por personas, resultados por arquetipo, el generador perturbado y la comparación con cifras oficiales. |
| ¿Esto es asesoría financiera? | No: es orientación educativa en simulación y la persona decide. |
| ¿Qué hace si falla el modelo de lenguaje? | No lo usamos. Las explicaciones salen de plantillas con cifras del motor. |
| ¿En qué se diferencia de lo que ya existe? | Decide por fecha de pago, mide la frontera contra reglas sencillas y dice cuándo no gana. |
| ¿Qué hizo el equipo y qué hizo la IA? | Completar el domingo con TRANSPARENCIA.md: quién fijó el objetivo, quién decidió cada elección y qué herramientas de IA se usaron y para qué. |
| ¿Qué no verificaron? | Completar con lo que quede sin medir: otros usuarios reales, otros países, datos reales. |

### Números para tener de memoria (se completan el domingo)

Frontera: pagos descubiertos y gasto permitido por método y cuantil, en la prueba y en el perturbado. Pares de semillas: diferencia media e intervalo del modelo contra la regla robusta. Calibración del P20. Mutaciones detectadas sobre las hechas. Latencia p50 y p95 por pantalla. Hash de la tabla de resultados. Todos [por medir].

## 16. Riesgos y plan B

| **Riesgo** | **Señal temprana** | **Plan B** |
|---|---|---|
| La demo falla en vivo | Errores intermitentes en los ensayos | Video grabado y datos de demo precargados |
| El generador se atrasa | Sin datos completos a las 12:30 | Seguir con la muestra de 20 personas y 3 arquetipos; completar después |
| Un contrato cambia a mitad de camino | Pruebas de contrato en rojo | Solo se cambia por pull request aprobado por Anderson y Gino |
| El modelo no supera a la regla robusta | Frontera del sábado por la noche | Se presenta la regla robusta y se explica la decisión |
| El modelo gana en entrenamiento y pierde en el perturbado | Tabla de robustez | Se dice y se presenta la regla robusta |
| No se autoriza un modelo de lenguaje o no hay internet | Respuesta de la organización | Ya no lo usamos |
| El alcance crece | Propuestas de funciones nuevas después del control 2 | Van a una lista de pendientes, no al código |
| El líder se satura | Decisiones que esperan a Gino más de 30 minutos | Rafael decide en el modelo y Anderson en la integración |
| Entregables incompletos | Domingo temprano sin README ni evaluación | Cada entregable tiene responsable desde el sábado |
| Afirmaciones sin respaldo en el pitch | Cifras en láminas que no salen de la evaluación | Regla: ningún número sin su origen |
| Conflictos de git | Fusiones que rompen make test | Dueños de carpeta; ramas cortas; etiquetas de versión para volver atrás |
| Cambio sorpresa de la organización | Anuncio de la prueba de evolución | Configuración fuera del código y pruebas por caso |
| Los pesos o el formato del pitch no son los que suponemos | Respuesta de la organización | El plan cubre las dos fuentes: pitch corto como base y ampliable; el mayor esfuerzo va a IA y analítica, que pesa 25 en ambas |
| El jurado espera IA generativa | Respuesta de la organización o comentario del mentor | Capa generativa opcional, local o autorizada, con verificador de cifras y fuera del núcleo; si no hay tiempo, se explica por qué las plantillas son más verificables |
| Responsible AI sin evidencia | docs/responsible_ai.md vacío el sábado a las 18:00 | Gino y Rafael lo cierran el domingo temprano con las tablas de sesgos ya medidas |
| La capa generativa falla o se retrasa | Verificador con baja aprobación, latencia mayor que 6 segundos o autorización tardía | Se apaga a las 17:00 con el criterio escrito y se presenta la opción A; el núcleo no depende de ella |
| El asistente (opción C) llega a medias o responde mal | Evaluación del modo 1 bajo los umbrales a las 17:30 | No se muestra en la demo; se dice en el pitch con su dato; el semáforo y las pantallas ya están completos sin él |
| Inyección de prompts por el texto libre del chat | Pruebas de ataque que producen respuestas fuera de las reglas | Guardia de entrada, esquema cerrado, aislamiento de la pregunta y verificador de salida; si algo falla, plantilla o rechazo |
| Reutilizar material del bot_diagnosis por error | Archivos, datos o textos del NOC en el repositorio del hackathon | No se copia nada; solo el patrón de diseño, declarado en TRANSPARENCIA.md; el buscador de secretos y de datos revisa el repositorio |
| Fuga de la clave de OpenAI | La clave aparece en el historial o en una pantalla | Está solo en .env; el buscador de secretos la revisa; se regenera en el panel de la cuenta y se fija un tope de gasto |
| Conflictos entre ramas de GitHub | Un pull request toca carpetas de otra persona | Una carpeta, un dueño; contratos y configuración compartida solo por Anderson; ventanas de integración con etiqueta |

## 17. Transparencia y uso de herramientas de IA

- **TRANSPARENCIA.md:** qué decidió cada persona, qué hizo una herramienta de IA (código, pruebas, scripts) y cómo se verificó cada resultado contra una medición.
- **ATRIBUCIONES.md:** bibliotecas, versiones y licencias; todo código reutilizado con su origen.
- **Honestidad:** las omisiones, los supuestos y lo que no se pudo verificar se declaran con su número; no se esconden.
- **Privacidad:** ningún dato real, ni siquiera del equipo; ninguna clave en el repositorio ni en la demo.

## 18. Checklist de salida y pendientes

| **Checklist de la guía** | **Estado** |
|---|---|
| Problema y usuario definidos | Sección 1 y 4 [escritos en el README] |
| Datos legales y reproducibles | Sección 6 [semilla y generador] |
| MVP ejecutable | Control 1 y control 2 |
| IA o ML aporta valor medido | Frontera y regla de adopción |
| Baseline y casos adversos | Escalera y pruebas de la sección 9 |
| Seguridad y explicabilidad | Sección 8 y pantalla Por qué |
| Responsible AI (pack) | docs/responsible_ai.md con sesgos medidos |
| Diccionario de datos (pack) | docs/diccionario_datos.md |
| Roadmap en el pitch (pack) | Una lámina y docs/roadmap.md |
| README y arquitectura | Anderson y Gino |
| Demo ensayada | Tres ensayos el domingo |
| Entrega completa | Carpeta con los entregables de la sección 13 |

### Preguntar a la organización (antes de las 12:00)

- ¿Se autoriza un modelo de lenguaje externo, y con qué condiciones?
- ¿Se activa la prueba de evolución, cuándo y cuánto puntúa?
- Horarios de controles, mentorías, cierre de entregas y presentaciones.
- ¿Se confirma el pitch de 10 minutos más 3 de preguntas?
- Mecanismo de entrega: carpeta o repositorio, y quién debe tener acceso.
- Lenguajes y frameworks autorizados.
- ¿Qué pesos aplican: los de la guía impresa o los del Challenge pack?
- ¿El pitch es de 5 más 5 más 5 o de 10 más 3?
- ¿Se espera IA generativa o es opcional?
- Autorización por escrito para usar un modelo de lenguaje externo (API de OpenAI con cuenta propia, solo datos ficticios) en la opción B.

### Decisiones del equipo

- Nombre del producto.
- Quién presenta y quién maneja la demo.
- Qué laptop corre la demo y cuál es la de respaldo.
- Umbrales de confianza, cuantil conservador y colchón: se fijan antes de ver resultados.
- Confirmar las decisiones marcadas [propuesto]: sin modelo de lenguaje, Streamlit sin servidor aparte, 2 o 3 conversaciones, el reparto de roles y el respaldo del líder.

## 19. Fuentes

- BBVA AI Factory: saldo con incertidumbre y detección de anomalías.
- Capital & Main: lo que aprendió Even sobre ingresos irregulares.
- CFPB: acción contra Hello Digit por su algoritmo de ahorro automático.
- BCRP, revista Moneda: informalidad según tipo de trabajador (ENAHO).
- Andina: encuesta de capacidades financieras de la SBS 2022.
- La República: ingreso promedio mensual 2025 según el INEI.
- El Peruano: Índice de Bienestar Financiero de Experian 2026.
- INEI: Encuesta Nacional de Hogares.

Según la v3, las tres primeras fuentes se leyeron completas. Las demás cifras vienen de resúmenes de prensa y deben abrirse en su origen antes del pitch. Las reglas y los pesos provienen de la guía oficial del desafío entregada el 14-nov.

## Anexo A. Firmas de los contratos entre módulos

Se implementan con pydantic en src/contratos. Cambiarlas exige la aprobación de Anderson y Gino.

Movimiento      : customer_id str, transaction_id str, fecha_hora datetime, monto float, moneda "PEN",

tipo "ingreso"|"gasto", categoria str, comercio str, saldo float|None

ReporteCalidad   : filas_entrada int, filas_salida int, duplicados_eliminados int, faltantes dict,

atipicos int, suscripciones_duplicadas list, pagos_inferidos list,

pii_enmascarado int, columnas_sensibles_descartadas list

PagoConFecha     : pago_id str, dia int (dias hasta el pago), monto float, categoria str

EstadoPersona    : customer_id str, fecha_corte date, saldo float, pagos list[PagoConFecha], colchon float,

semanas_historia int

Pronostico       : por_horizonte {3|7|14: {"p5","p20","p50","p80": float}}  (ordenado: p5<=p20<=p50<=p80)

Decision         : numero_hoy float, por_pago list[{pago_id, permitido, semaforo "verde"|"ambar"|"rojo"}],

confianza "alta"|"media"|"baja", desglose dict, limites list[str], supuestos list[str],

evidencia dict, propuestas list[Propuesta], respaldo bool, registro_id str,

mensaje_falta str|None, explicacion str, explicacion_fuente "plantilla"|"generativa"

IngresoExtra     : dia int (0 a 14), monto float (0 a 10000)            [opcion C]

Escenario        : ingresos_extra list[IngresoExtra] (maximo 3), gasto_hoy float (0 a 10000)

Respuesta        : texto str, intencion str, fuente "motor"|"kb"|"generativa"|"plantilla"|"rechazo",

citas list[str], datos dict, acciones list[str], registro_id str

Opcion C         : servicio.preguntar(customer_id, fecha, texto, contexto=None) -> Respuesta | servicio.simular(customer_id, fecha, escenario) -> Decision

motor.decidir(estado, pronostico, cfg, ingresos_extra=())   # parametro OPCIONAL, compatible

Propuesta        : propuesta_id str, texto str, monto float, pago_id str, antes dict, despues dict, confianza str

Registro         : una linea JSON por recomendacion: entradas, version_generador, version_modelo, semilla, hash_config

Funciones        : ingesta.cargar(origen) | modelo.predecir(historia, fecha) | reglas.regla1/regla2(historia, fecha)

motor.decidir(estado, pronostico, cfg) | servicio.consultar(id, fecha, metodo) | servicio.responder(propuesta_id, accion)

Adiciones v8     : ingesta.cargar_etiquetas(origen) (solo evaluacion) | modelo.entrenar(movimientos_train, cfg, semilla) -> Modelo,

Modelo.predecir/guardar/cargar, excepcion HistoriaInsuficiente | servicio.cargar_archivo(origen) -> ReporteCalidad

servicio.salud() -> {p50, p95, tasa_error, tasa_respaldo, consultas} | servicio.auditar(registro_id) -> registro y si se reproduce

scripts/auditar_recomendacion.py <registro_id>

## Anexo B. Parámetros de config.yaml

| **Parámetro** | **Valor inicial** | **Estado** |
|---|---|---|
| horizontes_dias | 3, 7, 14 | Fijo |
| cuantiles | 0.05, 0.20, 0.50, 0.80 | Fijo |
| cuantil_conservador | 0.20 | Se confirma con la frontera [por medir] |
| colchon | Por fijar | Antes de ver resultados |
| umbral_historia_semanas | 4 | Antes de ver resultados |
| umbrales_confianza | Por fijar | Antes de ver resultados |
| ventana_regla_robusta_semanas | 8 | Fijo |
| semillas_evaluacion | 20 o más | Fijo |
| semilla_generador | Una fija, anotada en el README | Fijo |
| variables_sensibles | edad, genero, ubicacion, distrito, nombre, dni, telefono | Fijo; la ingesta descarta y la prueba verifica |
| umbral_alerta_sesgo | Por fijar | Antes de ver resultados |
| patrones_pii | DNI de 8 digitos, telefono de 9 digitos, correo, tarjeta de 13 a 19 digitos | Fijo |
| asistente.activado, asistente.modo | falso, modo 1 (sin LLM) | El modo 2 exige además generativa.activada |
| asistente.max_caracteres, max_palabras, umbral_intencion, minimo_rag, max_preguntas_por_minuto | 200, 120, por fijar, por fijar, 10 | Por fijar antes de ver resultados |
| generativa.activada | falso | Solo con las cinco condiciones del diseño de la opción B |
| generativa.proveedor | ninguno (openai al activar) | Variable LLM_PROVEEDOR; clave en LLM_API_KEY dentro de .env |
| generativa.timeout_s, reintentos, temperatura, max_tokens, max_palabras | 6, 1, 0, 250, 90 | Por fijar |

## Anexo C. Escenarios de estrés para el motor y la ingesta

Se prueban en tests/unit y tests/property. Los casos inviables se declaran, no se ocultan.

- **Ingresos:** ocho semanas sin ingreso; un solo ingreso grande al final de la ventana; ingreso muy grande el mismo día del pago.
- **Pagos:** pago diez veces mayor que el saldo; dos pagos el mismo día; pago el día 0 y el día 14; sin ningún pago con fecha; pagos con monto cero.
- **Saldo:** saldo negativo inicial; saldo cero; saldo enorme.
- **Historia y calendario:** un solo día de historia; menos de 4 semanas; historia con huecos de un mes; mes de 28 y de 31 días; año bisiesto.
- **Archivos:** archivo vacío; columnas faltantes; columnas extra; tipos erróneos; fechas inválidas; montos NaN, infinito y negativos donde no corresponde; textos de 5,000 caracteres; unicode; identificadores vacíos.
- **Modelo:** cuantiles cruzados antes de ordenar; cuantiles iguales; pronóstico con valores negativos.

## Anexo D. Ejemplo de entrada de DECISIONES.md

Decision        : Mantener el cuantil conservador en P20

Dato            : frontera en la prueba y en el perturbado: [por medir]

Que decidimos   : [completar]

Que haríamos distinto: [completar]

## Anexo E. Trabajo en paralelo con GitHub: ramas separadas que luego se unen

Idea central: cada persona trabaja en su propia rama y en sus propias carpetas, así nadie pisa el trabajo de otro. Las ramas se unen a main en cuatro ventanas de integración. Lo que hace posible este orden es que todos programan contra los mismos contratos y firmas desde el primer minuto.

### 1. Una carpeta, un dueño

| **Ruta** | **Dueño** | **Cómo se cambia** |
|---|---|---|
| src/contratos/, src/servicio/, tests/contract, tests/integracion, tests/e2e, tests/fixtures | Anderson | Solo Anderson; los demás piden el cambio con un pull request pequeño. Un campo de contrato exige además la aprobación de Gino |
| config/base.yaml, requirements.txt, Makefile, tareas.py, pyproject.toml, .github/, scripts/, README.md, docs/arquitectura.md | Anderson | Solo Anderson. Si necesitas una librería, avísale con nombre y versión |
| src/datos/, src/reglas/, eval/ (menos adopcion.py), data/, config/datos.yaml, docs/datos.md, docs/evaluacion.md, docs/diccionario_datos.md | Rafael | Solo Rafael |
| src/ingesta/, config/ingesta.yaml, tests/unit/ingesta/ | Mathias | Solo Mathias |
| src/motor/, config/motor.yaml, tests/unit/motor/, tests/property/ | Sebastián | Solo Sebastián |
| src/modelo/, config/modelo.yaml, config/preregistro.yaml, tests/unit/modelo/, eval/adopcion.py, docs/responsible_ai.md, docs/roadmap.md, DECISIONES.md, TRANSPARENCIA.md | Gino | Solo Gino |
| src/app/main.py, componentes.py, estado.py, servicio_falso.py, pages/1_Hoy.py, pages/2_Plan.py, tests/unit/app_hoy_plan/, docs/guion_demo.md | Jesús | Solo Jesús |
| src/app/tema.py, pages/3_Por_que.py, 4_Datos.py, 5_Evaluacion.py, tests/unit/app_evidencia/, tests/a11y/, pitch/, docs/conversaciones.md, docs/fuentes_verificadas.md | Alberto | Solo Alberto |
| src/generativa/ (si se activa la opción B): minimizar, verificador, redactar \| prompts \| proveedores | Sebastián \| Gino \| Anderson | Cada archivo tiene un solo dueño |
| src/asistente/ (opción C): flujo.py \| intenciones.py, prompts.py \| plantillas.py, verificador.py \| rag.py y kb/ y data/chat \| guardia.py | Anderson \| Gino \| Sebastián \| Rafael \| Mathias | Cada archivo tiene un solo dueño |
| src/motor/simular.py (opción C), src/app/pages/6_Asistente.py, eval/chat.py | Sebastián \| Jesús \| Gino | Solo el dueño |

### 2. Reglas para no malograr a los demás

- **Una carpeta, un dueño:** solo tocas los archivos de tu carpeta. Si necesitas un cambio en otra, escribes al dueño o abres un pull request pequeño para él.
- **Firmas desde el inicio:** src/__init__.py y cada __init__.py de paquete ya existen desde V0 con las firmas y NotImplementedError. Tú reemplazas el cuerpo, no la firma. Así los demás pueden importar tu función desde el minuto 1.
- **Configuración por dueño:** cada módulo lee su propio archivo config/<modulo>.yaml y Anderson los une con config/base.yaml. Nadie edita el archivo de otro.
- **Librerías nuevas:** requirements.txt lo edita solo Anderson. Instálala en tu laptop y pásale el nombre y la versión.
- **Formato:** no corras formateadores sobre todo el repositorio, solo sobre tu carpeta. No renombres ni muevas archivos ajenos.
- **Nada compartido:** lo único que se comparte entre módulos son los modelos de src/contratos. Una pequeña duplicación de código es mejor que un archivo compartido.
- **Pruebas junto al dueño:** las pruebas de tu módulo viven en tu carpeta de tests, nunca en la de otro.

### 3. Cuatro ventanas de integración

| **Hora** | **Ventana** | **Qué debe estar fusionado en main antes de la hora** | **Quién la cierra** |
|---|---|---|---|
| 11:00 | V0 | Estructura, contratos, stubs con firmas, fixtures, tareas.py y muestra de 20 personas | Anderson y Rafael |
| 12:00 | V1 | Ingesta v0, motor v0, reglas, esqueleto del modelo, esqueleto de la app y generador v1 | Cada dueño; Anderson verifica |
| 13:00 | V2 (control 1) | Servicio con regla 2 funcionando y pantalla Hoy conectada. Etiqueta v0-control1 | Anderson |
| 16:00 | V3 (control 2) | Modelo v1, motor completo con propuesta, pantallas Por qué y Plan, pruebas P0. Etiqueta v1-control2 | Anderson |
| 17:45 | V4 | Todo lo que se va a mostrar, con make test verde. A las 18:00 etiqueta v2-congelado | Anderson y Gino |
| Domingo | Solo correcciones | Pull requests pequeños con fallas corregidas. Etiqueta v3-final a las 11:00 | Anderson |

Un cuarto de hora antes de cada ventana, avisa en el canal: voy a fusionar tal rama. Después de cada fusión Anderson corre las pruebas sobre main y, si salen bien, pone la etiqueta de versión.

### 4. Comandos paso a paso

UNA SOLA VEZ (en tu laptop)

git clone <URL-del-repositorio>

cd <carpeta-del-repositorio>

git config user.name "Tu Nombre"

git config user.email "tu-correo@ejemplo.com"

python -m venv .venv

.venv\Scripts\activate            (en PowerShell; en Git Bash: source .venv/Scripts/activate)

pip install -r requirements.txt

CADA TAREA NUEVA

git switch main

git pull origin main

git switch -c feat/<tu-nombre>-<tema>

... programas y pruebas ...

python tareas.py test              (o: pytest -q tests/unit/<tu_modulo>)

git status

git add src/<tu_carpeta> tests/<tu_carpeta>       (NUNCA git add . ni git add -A)

git commit -m "feat: descripcion corta"

git push -u origin feat/<tu-nombre>-<tema>

(en GitHub: Compare and pull request, base main, pide revision a tu revisor)

TRAER LO NUEVO DE MAIN A TU RAMA (cada hora y antes de cada ventana)

git fetch origin

git merge origin/main

python tareas.py test

git push

SI ALGO SALE MAL

git status                         (mira primero que paso)

git restore <archivo>              (descarta cambios SIN guardar de un archivo)

git revert <commit>                (deshace un commit ya subido sin borrar la historia)

NUNCA: git push --force, git reset --hard sobre una rama compartida, ni subir .env o data/generado

### 5. Revisión cruzada de pull requests

| **Autor** | **Revisor** |
|---|---|
| Mathias | Sebastián |
| Sebastián | Mathias |
| Rafael | Gino |
| Gino | Rafael |
| Jesús | Alberto |
| Alberto | Jesús |
| Anderson | Gino para los contratos; Sebastián para lo demás |

El revisor comprueba tres cosas: que solo se tocaron carpetas del autor, que python tareas.py test pasa y que no hay claves, datos generados ni archivos .env. Si todo está bien, aprueba y el autor fusiona.

### 6. Protección de main y pruebas automáticas

- **Regla sugerida:** en GitHub, Settings, Branches, regla para main: exigir pull request, una aprobación y la comprobación tests; sin push forzado. Si estorba, basta con pull request y pruebas locales.
- **Pruebas automáticas:** .github/workflows/test.yml ejecuta pytest en cada pull request. Lo escribe Anderson.
- **Dueños en GitHub:** .github/CODEOWNERS asigna cada carpeta a su dueño para que GitHub pida su revisión.
- **Windows:** en las laptops con Windows puede no existir make. Por eso Anderson entrega tareas.py con los mismos comandos (python tareas.py setup, datos, test, eval, demo) y el Makefile queda como alias.

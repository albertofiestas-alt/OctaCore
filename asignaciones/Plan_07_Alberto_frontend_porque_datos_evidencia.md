**Hackathon de Ingeniería BBVA · AI Financial Life · Plan individual**

**Alberto · Frontend 2: Por qué, evaluación y evidencia visual**

Versión 9: incluye el Challenge pack de BBVA, la opción B (capa generativa con OpenAI), las firmas exactas de cada módulo y la guía de GitHub. Derivado de la propuesta v9; si algo de este plan contradice a la v9, manda la v9. Generado el sábado 14-nov a las 11:34 a. m. (Lima). Si la hora de una fila ya pasó, haz esa tarea de inmediato y avisa a Gino.

Marcas: [SUPUESTO] no verificado; [propuesto] lo confirma Gino; [por medir] se llena con una medición nuestra; [por fijar] se fija antes de ver resultados. Ningún número va al pitch sin su origen.

## 1. El proyecto en una página

Qué es: una herramienta para personas con ingresos irregulares que dice cuánto pueden gastar hoy sin fallar a un pago con fecha, con un rango de incertidumbre y propuestas simuladas. La persona decide siempre y nada se ejecuta.

| **Tema** | **Definición (resumen de la v9)** |
|---|---|
| Criterio de éxito | A igual porcentaje de pagos con fecha descubiertos, el modelo permite más gasto diario que la regla robusta; o a igual gasto, deja menos pagos descubiertos. Debe cumplirse en la prueba y en el generador perturbado. Si no, se presenta la regla robusta y se dice. |
| Cómo se calcula el número de hoy | Por fecha de pago, tomando el mínimo: permitido(d) = (saldo + ingreso conservador(d) - pagos con fecha hasta d - colchón) / días hasta d. El número de hoy es max(0, mínimo de permitido(d) sobre cada pago y el día 14). |
| Pronóstico | Cuantiles 5, 20, 50 y 80 del ingreso ACUMULADO a 3, 7 y 14 días. Tres técnicas con la misma forma de salida: regla ingenua, regla robusta y modelo. |
| Datos | 400 personas ficticias, 24 meses, cinco arquetipos, semilla fija. Partición por fecha y por personas. Existe un generador perturbado solo para robustez. |
| Pantallas | Hoy, Por qué y Plan propuesto, más carga de datos y evaluación. Cada pantalla lleva el aviso de orientación educativa. |
| Evaluación | Dos números por método (pagos descubiertos y gasto permitido) y una frontera con los cuantiles P5, P20, P50 y P80, más referencias de gasto cero y gasto fijo. |

### Lo que agrega el Challenge pack de BBVA (v9)

| **Tema** | **Qué dice y qué hacemos** |
|---|---|
| Pesos del pack | IA/ML/analítica 25, valor de producto y UX 20, ingeniería y arquitectura 20, datos sintéticos y evidencia 15, Responsible AI 10, presentación y storytelling 10. La guía impresa trae otros pesos; la organización debe confirmar cuál manda. IA y analítica pesa 25 en las dos. |
| Formato del pitch | Pack: 5 de pitch, 5 de demo y 5 de preguntas. Guía impresa: 10 más 3. Se prepara el corto como base y se amplía si lo confirman. |
| Responsible AI (10) | Explicabilidad con evidencia, supuestos y confianza; privacidad; límites; sesgos medidos por grupo y sin variables sensibles; seguridad técnica; trazabilidad auditable. Todo en docs/responsible_ai.md, coordinado por Gino. |
| Datos y evidencia (15) | Ground truth, diccionario de datos con justificación de realismo, trazabilidad y métricas. |
| IA generativa | El pack la lista como capacidad observada y pide que no sea un chatbot genérico. El núcleo no la usa; es una capa opcional que decide Gino con la respuesta de la organización. |
| Roadmap | El pitch final incluye una lámina de próximos pasos sin prometer resultados. |

### Reglas duras para todos

- **Datos:** sin datos reales, ni siquiera del equipo; sin marcas ni interfaces de BBVA; sin claves en el repositorio.
- **Alcance:** sin modelo de lenguaje, sin servidor aparte, todo corre en local y sin internet.
- **Anti fuga:** las etiquetas es_duplicado, es_atipico, pago_con_fecha y arquetipo nunca entran al modelo, al motor ni a la interfaz.
- **Honestidad:** ningún número en el pitch sin su origen; las marcas son [SUPUESTO], [propuesto], [por medir] y [por fijar].
- **Calendario:** congelamiento el sábado 18:00; el domingo no se construye nada nuevo.
- **Contratos:** cambiar un campo de src/contratos exige la aprobación de Anderson y de Gino.
- **Responsible AI:** ninguna variable sensible (edad, género, ubicación, nombre) entra al modelo ni al motor; toda recomendación trae supuestos, evidencia, límites y confianza; todo se puede auditar desde su identificador.
- **Pitch:** prepara tu parte para el formato corto de 5 minutos; si confirman el de 10, se amplía.

## 2. Tu misión

Eres la explicación y la evidencia: que la persona entienda por qué confía en el número, que el jurado vea la calidad de los datos y los resultados, y que todo sea accesible. No cargas datos: son sintéticos y vienen precargados; tú los muestras. Además verificas las cifras que irán al pitch, haces las conversaciones y grabas el video de respaldo.

### Qué recibes y de quién

| **Qué** | **De** | **Hora** |
|---|---|---|
| Contratos y fixtures de Decision | Anderson | 10:45 |
| Desglose en la Decision | Sebastián | 12:30 |
| Reporte de calidad del dataset sintético (eval/resultados/calidad_datos.json) | Mathias | 16:00 |
| Archivos de eval/resultados | Rafael | 16:00 y 18:30 |

### Qué entregas y a quién

| **Qué** | **A** | **Hora** |
|---|---|---|
| tema.py (paleta, contraste, tamaños) | Jesús | 11:15 |
| Pantalla Por qué | Todos | 14:00 |
| Pantalla Evaluación con la frontera | Pitch | 18:30 |
| Lista de accesibilidad y conversaciones | Gino, Rafael | 18:00 |
| Cifras verificadas y video de respaldo | Pitch | 12:30 y domingo |

## 3. Tus primeros pasos exactos (empieza por aquí)

Hazlos en este orden. No esperes a nadie: todo lo que necesitas para empezar está en los anexos de este plan.

- **1.** Clona el repositorio y crea la rama feat/alberto-tema.
- **2.** Escribe src/app/tema.py y la prueba de contraste. Sube el pull request antes de las 11:15: Jesús lo importa.
- **3.** Crea la rama feat/alberto-evidencia y construye 3_Por_que.py con las fixtures de confianza alta, media y baja.
- **4.** Mientras tanto, con Rafael, abre las fuentes de las cifras de prensa y anótalas en docs/fuentes_verificadas.md.
- **5.** Sigue con 5_Evaluacion.py leyendo archivos de ejemplo (incluido el reporte de calidad de datos).

## 4. Qué haces tú con el Challenge pack (tareas nuevas)

Seis tareas nuevas. La pantalla Evaluación pasa a mostrar sesgos, salud y auditoría, que es lo que el pack llama evidencia.

| **#** | **Qué haces** | **Cómo y dónde** | **Hora** | **Cómo sabes que está bien** |
|---|---|---|---|---|
| 1 | Supuestos y evidencia en Por qué | Tabla de evidencia (semanas de historia, pagos detectados, rango) y la lista de supuestos de Decision, en lenguaje simple. | 14:30 | AppTest con las tres fixtures de confianza |
| 2 | Panel de salud en Evaluación | Llama a servicio.salud() y muestra p50, p95, tasa de error, tasa de respaldo y número de consultas. | 17:30 | Muestra valores reales tras 20 consultas |
| 3 | Panel de sesgos en Evaluación | Lee eval/resultados/sesgos.csv: gráfico de barras por grupo con la brecha anotada y el aviso si hay alerta. Si falta el archivo, mensaje con make eval. | 18:30 | Con el archivo de ejemplo se ve la brecha; sin archivo, el mensaje |
| 4 | Panel de auditoría en Evaluación | Campo para registro_id (se copia de la pantalla Hoy) que llama a servicio.auditar y muestra entradas, decisión, versión del modelo, hash de configuración y si se reproduce. | 18:00 | Auditar un id real muestra coincidencia |
| 5 | Deck de 5 minutos | No más de 6 láminas: problema y usuario, IA y evidencia (frontera), Responsible AI (sesgos), arquitectura en una imagen, demo y roadmap. Cada cifra lleva su fuente al pie. | Borrador sábado 19:30; final domingo 9:00 | Todas las cifras con fuente; Gino lo revisa |
| 6 | Video de la demo de 5 minutos | Grabación del guion de Jesús, con narración, como respaldo. | Borrador sábado 19:30; final domingo | Se reproduce en otra laptop y dura 5:00 o menos |

## 5. Tu especificación técnica

### 1. Tema compartido (src/app/tema.py), antes de las 11:15

- **Contenido:** colores del semáforo con relación de contraste de al menos 4.5 a 1 sobre el fondo, tamaños de texto de al menos 16 px, símbolos para cada estado, y una paleta segura para daltonismo. Jesús lo importa.
- **Prueba:** tests/a11y/contraste.py calcula la relación de contraste de cada par de colores y falla por debajo de 4.5.

### 2. Pantalla Por qué (pages/3_Por_que.py)

- **Fundamento:** cuánto se espera que entre en 14 días (rango con P5, P20, P50 y P80 como un gráfico simple con marcadores), qué pagos están reservados y para qué.
- **Cómo se calculó:** un desplegable con la tabla de puntos de control del desglose: día, ingreso conservador, pagos acumulados y permitido. Resalta el punto que limita.
- **Límites:** las frases del motor, visibles sin desplegar.
- **Confianza:** alta, media o baja en palabras y con su razón (ancho del rango y semanas de historia). No solo color.
- **Lenguaje:** soles y fechas, nunca tasas; una idea por bloque.

### 3. Calidad de los datos (panel de solo lectura dentro de 5_Evaluacion.py)

- **Qué muestra:** lee eval/resultados/calidad_datos.json (el ReporteCalidad de aplicar la ingesta al dataset sintético completo; lo genera Mathias): filas de entrada y de salida, duplicados eliminados, suscripciones duplicadas, faltantes, atípicos, PII enmascarada y columnas sensibles descartadas. No hay selector de archivos: los datos son sintéticos y vienen precargados.
- **Si falta el archivo:** mensaje con el comando que lo genera. Nunca un traceback.

### 4. Pantalla Evaluación (pages/5_Evaluacion.py)

- **Contenido:** solo lectura de eval/resultados: tabla de métricas, gráfico de la frontera con un marcador distinto por método y los cuatro puntos de cuantil, tabla de robustez en el generador perturbado y los ejemplos de error.
- **Archivos ausentes:** mensaje que dice qué comando los genera (make eval).
- **Honestidad:** se muestra la nota de que los datos son sintéticos y que se demuestra el método, no la precisión real.

### 5. Accesibilidad, conversaciones, cifras y video

- **Lista de accesibilidad:** teclado, contraste, texto de 16 px, símbolo además del color, celular de 360 px de ancho, y la prueba de comprensión. La firmas tú antes del congelamiento.
- **Conversaciones (2 o 3) [propuesto]:** con las preguntas de la v5. Sin datos personales ni financieros; solo frases y reacciones, con N y fecha en docs/conversaciones.md. Se presentan como prueba de comprensión, no como estadística.
- **Cifras de prensa:** con Rafael, abre la fuente original de las 2 o 3 cifras que irán al pitch y anótalas en docs/fuentes_verificadas.md con el enlace y el texto exacto. Las que no puedas abrir, no se usan.
- **Video de respaldo:** grabación de pantalla (en Windows, la barra de juegos con Win y G, u OBS) de la demo completa, con guion y narración. Borrador el sábado a las 19:00 y versión final el domingo. Verifica que el archivo se reproduce en otra laptop.
- **Pitch visual:** con Rafael, un deck de no más de 8 láminas; cada número lleva su fuente al pie.

## 6. Archivos y funciones que escribes (con código)

Tu primera entrega es tema.py (antes de las 11:15) porque Jesús lo importa. Después construyes las otras páginas con el servicio falso de Jesús (src/app/servicio_falso.py), igual que él.

### src/app/tema.py

COLOR = {                       # relacion de contraste >= 4.5 sobre FONDO (se comprueba con la prueba)

"fondo": "#FFFFFF", "texto": "#1A1A1A",

"verde": "#1B7F3B", "ambar": "#8A5A00", "rojo": "#B3261E", "acento": "#0B2A6F"}

TAMANO_TEXTO_PX = 16

def contraste(hex1, hex2) -> float:

def lum(h):

r, g, b = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]

f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

a, b = sorted([lum(hex1), lum(hex2)], reverse=True)

return (a + 0.05) / (b + 0.05)

# tests/a11y/test_contraste.py: para cada color de COLOR distinto del fondo, contraste(color, fondo) >= 4.5

### 3_Por_que.py

d = s.consultar(persona, fecha)

st.header("Por qué este número")

# 1) rango de ingreso a 14 dias: p5, p20, p50, p80 (desde d.evidencia["rango_14d"]) como grafico simple con marcadores

# 2) pagos reservados y para que (d.por_pago)

# 3) expander "Como se calculo": tabla de puntos de control desde d.desglose (dia, ingreso conservador, pagos acumulados, permitido) y el punto que limita

# 4) confianza en PALABRAS con su razon: ancho del rango y semanas de historia

# 5) "Supuestos y evidencia": d.supuestos y d.evidencia en lenguaje simple

# 6) d.limites visibles sin desplegar; aviso()

### Calidad de datos (dentro de 5_Evaluacion.py, solo lectura)

# Los datos son sinteticos y vienen precargados: NO hay selector de archivos.

import json

ruta = RAIZ / "eval/resultados/calidad_datos.json"      # lo genera Mathias con python tareas.py eval

if not ruta.exists():

st.info("Genera el reporte con: python tareas.py eval")

else:

r = json.loads(ruta.read_text(encoding="utf-8"))

st.metric("Filas de entrada", r["filas_entrada"]); st.metric("Filas limpias", r["filas_salida"])

st.metric("Duplicados eliminados", r["duplicados_eliminados"])

# suscripciones duplicadas, faltantes, atipicos, pii_enmascarado y columnas_sensibles_descartadas

### 5_Evaluacion.py

# Solo lectura de eval/resultados/. Si falta un archivo: st.info("Genera los resultados con: python tareas.py eval")

# - tabla de metricas (resultados.csv) y calidad de los datos (calidad_datos.json), ver el bloque anterior

# - grafico de la frontera: x = % de pagos descubiertos, y = gasto permitido por dia; un marcador DISTINTO por metodo

#   y puntos para P5, P20, P50 y P80 (frontera.csv)

# - robustez: misma tabla en el generador perturbado, al lado

# - sesgos por grupo (sesgos.csv): barras por grupo con la brecha anotada y el aviso si hay alerta

# - salud del sistema: s.salud() -> p50, p95, tasa de error, tasa de respaldo

# - auditar: campo registro_id -> s.auditar(id) -> muestra entradas, decision, modelo, hash y si se reproduce

# - nota fija: los datos son sinteticos; se demuestra el metodo, no la precision real

Conversaciones, cifras verificadas, deck y video: están descritos en las secciones 3 y 4 de este plan, con sus horas y su criterio.

## 7. Opción B (capa generativa): tu parte si se activa

Esta sección solo se ejecuta si se cumplen las cinco condiciones del diseño de la opción B: autorización por escrito de la organización, control 1 aprobado, antes de las 17:00, clave de OpenAI funcionando en las dos laptops y pruebas P0 en verde. Si falta una, no hagas nada de esto. T0 es la hora de la autorización; con T0 después de las 14:30 no se activa.

Resumen del diseño: el modelo solo reescribe el porqué que el motor ya calculó. Ve una entrada mínima sin identificadores. Un verificador sin IA exige que cada cifra del texto exista en esa entrada; si algo falla, se muestra la plantilla. La clave de OpenAI vive solo en .env.

### Tu tarea (T0+90 a T0+150)

- **Etiqueta de fuente:** junto a cada explicación muestra Redactado con IA y verificado si Decision.explicacion_fuente es generativa, o Plantilla del motor si es plantilla. Nunca ocultes cuál es cuál. Texto y símbolo, no solo color.
- **Panel en Evaluación:** tasa de fallback de la capa y latencias, desde servicio.salud().
- **Comprensión:** con 2 o 3 personas compara la plantilla con el texto generado y reporta lo que entendieron, con N pequeño y dicho.

## 8. Opción C (asistente del semáforo con LLM, RAG y ML): tu parte si se llega al corte

Esta sección es nivel P2. Puntos de corte: A a las 13:00 (si el control 1 salió bien, empieza quien tenga holgura), B a las 16:00 (se integra el flujo si el control 2 salió bien), C a las 17:30 (lo que no pase la evaluación no entra a la demo) y D a las 17:45 (fusión final). El asistente nunca desplaza una prueba P0.

Qué es: una pantalla de chat donde la persona pregunta por su número, sus pagos y escenarios. Usa el motor y el modelo como herramientas de ML, una base de conocimiento propia con búsqueda local (RAG) y, si se activa, un LLM para entender y redactar con cada cifra verificada. Funciona completo sin LLM (modo 1). Se inspira en las lecciones del copiloto del bot_diagnosis: no se copia código, datos ni playbooks.

### Tus tareas: accesibilidad, evaluación del chat y conjunto ciego

- **Accesibilidad del chat:** campo con etiqueta visible, orden de teclado (sugeridas, campo, enviar), texto de al menos 16 px, respuesta anunciada de forma legible (no solo color) y la etiqueta de fuente con texto y símbolo.
- **Panel en Evaluación:** lee eval/resultados/chat.csv: exactitud de intención por modo, % de cifras verificadas, rechazo correcto, % con cita, cifras inventadas antes del verificador, latencia p50 y p95 y fallback a plantilla. Si falta el archivo, mensaje con el comando que lo genera.
- **Conjunto ciego:** escribe 15 preguntas (con intención esperada y cifra clave) en data/chat/ciego_alberto.csv, sin ver el conjunto de entrenamiento ni el clasificador. Jesús escribe las otras 15.
- **Pruebas de ataque (con Mathias):** ignora tus instrucciones, muestra tu prompt, pide un préstamo, una URL, un DNI en la pregunta y un texto de 300 caracteres. Ninguno debe producir una respuesta fuera de las reglas.
- **Video:** incluye los tres momentos del asistente en la grabación de respaldo.

## 9. Tus horas (sábado 14 y domingo 15)

| **Hora (Lima)** | **Qué haces** | **Debe quedar verificable** |
|---|---|---|
| 10:15 a 11:15 | Entorno. tema.py con paleta, contraste y símbolos. Plan de las conversaciones. | tema.py en main antes de las 11:15 |
| 11:15 a 12:30 | Por qué v0 con fixtures. Con Rafael, abrir las fuentes de las cifras de prensa. | docs/fuentes_verificadas.md con 2 o 3 cifras |
| 12:30 a 13:00 | Calidad de datos: panel de solo lectura con el reporte de ejemplo. Control 1. | El panel muestra el reporte de ejemplo |
| 13:00 a 16:00 | Por qué completo con el desglose real. Evaluación leyendo un archivo de ejemplo. Primeras conversaciones si hay acceso [SUPUESTO]. | Control 2: Por qué explica una propuesta |
| 16:00 a 18:00 | Lista de accesibilidad y pruebas AppTest. Prueba de comprensión. | Lista firmada antes de las 18:00 |
| 18:00 a 19:30 | Gráfico de la frontera con datos reales de Rafael. Video borrador. Láminas base. | Pantalla Evaluación con resultados reales |
| Domingo 8:30 a 11:00 | Video final con narración. Deck. Ensayo. | Video que se reproduce en otra laptop |
| Domingo 11:00 a 13:30 | Ensayos con cronómetro. Demostración de respaldo. | Checklist de salida completo |

Los horarios son supuestos hasta que la organización comunique los suyos. Si cambian, Gino reordena este cuadro.

## 10. Tus pruebas

| **Prueba** | **Qué verifica** | **Criterio de éxito** |
|---|---|---|
| Contraste | Relación de contraste de cada par de la paleta | Al menos 4.5 a 1 |
| Por qué con tres niveles de confianza | AppTest con las fixtures alta, media y baja | El texto y la razón de cada nivel |
| Desplegable de cálculo | La tabla de puntos de control aparece con el punto que limita | Presente |
| Calidad de datos | Con y sin calidad_datos.json | Muestra los conteos o el mensaje con el comando que lo genera |
| Evaluación con archivo ausente | Sin eval/resultados | Mensaje con make eval |
| Aviso obligatorio | Las páginas 3 y 5 contienen el aviso | Presente |
| Celular | Ancho de 360 px | Sin desplazamiento lateral [revisión manual] |
| Teclado | Recorrer las pantallas solo con teclado | Todo es alcanzable [revisión manual] |
| Por qué con evidencia | AppTest con confianza alta, media y baja | Supuestos y evidencia presentes |
| Panel de salud | Tras 20 consultas | Valores coinciden con servicio.salud() |
| Panel de sesgos | Con y sin sesgos.csv | Gráfico o mensaje claro |
| Panel de auditoría | Un registro_id real y uno inventado | Coincidencia y mensaje de no encontrado |

Escribe cada prueba antes que el código cuando puedas (primero rojo, después verde). Cobertura objetivo de tu módulo: al menos 80 % [SUPUESTO].

## 11. Cuándo estás listo (definición de hecho)

- **[ ]** tema.py y la prueba de contraste en main
- **[ ]** Por qué y Evaluación (con calidad de datos, sesgos, salud y auditoría) funcionan con servicio real y con fixtures
- **[ ]** Lista de accesibilidad firmada antes de las 18:00
- **[ ]** 2 o 3 conversaciones anotadas con N y fecha, sin datos personales
- **[ ]** Cifras del pitch verificadas en su fuente con enlace
- **[ ]** Video de respaldo que se reproduce en otra laptop
- **[ ]** Por qué muestra supuestos y evidencia
- **[ ]** Evaluación muestra sesgos, salud y auditoría
- **[ ]** Deck de 5 minutos con cifras y fuentes
- **[ ]** Video de 5 minutos que se reproduce en otra laptop

## 12. Riesgos y qué hacer

| **Riesgo** | **Plan B** |
|---|---|
| No hay acceso a personas para las conversaciones | Presentarlo como prueba de comprensión con el propio equipo y decirlo; no inflar la validación |
| Las fuentes de prensa no se pueden abrir | No usar esas cifras; usar solo las verificadas |
| El video no se reproduce | Exportar en un formato común, probarlo en otra laptop y tener la demo en vivo como principal |

## 13. Tu parte del pitch

| **Tema** | **Contenido** |
|---|---|
| Qué cuentas | Por qué la persona puede confiar: fundamento, límites y confianza; la calidad de los datos; la frontera en pantalla. |
| Cifras que debes tener | Una cifra oficial verificada con su fuente; una frase de las conversaciones; resultado de la prueba de comprensión [por medir]; lista de accesibilidad cumplida. |
| Pregunta que te toca | Qué entienden las personas al ver el número: lo que mostró la prueba de comprensión, con N pequeño y dicho. |
| En el formato de 5 minutos | Apoyas a Jesús en la demo (el porqué) y entregas el deck y el video de respaldo. |

El formato no está confirmado: la guía impresa dice 10 minutos más 3 de preguntas y el Challenge pack sugiere 5 de pitch, 5 de demo y 5 de preguntas. Prepara primero el corto. La regla de oro: ningún número sin su origen. La autocrítica se dice antes de que pregunten.

## 14. Git y trabajo en paralelo: cómo subir tu parte sin malograr la de los demás

Tu trabajo vive en tus ramas y en tus carpetas. Así puedes programar al mismo tiempo que los otros seis sin pisar nada. Tus ramas sugeridas: feat/alberto-tema, feat/alberto-evidencia.

### Qué es tuyo y qué no

- **Tus carpetas:** src/app/tema.py, pages/3_Por_que.py, 5_Evaluacion.py, tests/unit/app_evidencia, tests/a11y, pitch, docs/conversaciones.md, docs/fuentes_verificadas.md.
- **Todo lo demás:** no lo edites. Si necesitas un cambio en una carpeta ajena, escribe al dueño o abre un pull request pequeño para él. Tabla completa de dueños en el Anexo E de la v9.
- **Tu revisor:** Jesús. Tú revisas a quien te toque en el cuadro de revisión cruzada.

| **Ruta** | **Dueño** | **Cómo se cambia** |
|---|---|---|
| src/contratos/, src/servicio/, tests/contract, tests/integracion, tests/e2e, tests/fixtures | Anderson | Solo Anderson; los demás piden el cambio con un pull request pequeño. Un campo de contrato exige además la aprobación de Gino |
| config/base.yaml, requirements.txt, Makefile, tareas.py, pyproject.toml, .github/, scripts/, README.md, docs/arquitectura.md | Anderson | Solo Anderson. Si necesitas una librería, avísale con nombre y versión |
| src/datos/, src/reglas/, eval/ (menos adopcion.py), data/, config/datos.yaml, docs/datos.md, docs/evaluacion.md, docs/diccionario_datos.md | Rafael | Solo Rafael |
| src/ingesta/, config/ingesta.yaml, tests/unit/ingesta/ | Mathias | Solo Mathias |
| src/motor/, config/motor.yaml, tests/unit/motor/, tests/property/ | Sebastián | Solo Sebastián |
| src/modelo/, config/modelo.yaml, config/preregistro.yaml, tests/unit/modelo/, eval/adopcion.py, docs/responsible_ai.md, docs/roadmap.md, DECISIONES.md, TRANSPARENCIA.md | Gino | Solo Gino |
| src/app/main.py, componentes.py, estado.py, servicio_falso.py, pages/1_Hoy.py, pages/2_Plan.py, tests/unit/app_hoy_plan/, docs/guion_demo.md | Jesús | Solo Jesús |
| src/app/tema.py, pages/3_Por_que.py, 5_Evaluacion.py, tests/unit/app_evidencia/, tests/a11y/, pitch/, docs/conversaciones.md, docs/fuentes_verificadas.md | Alberto | Solo Alberto |
| src/generativa/ (si se activa la opción B): minimizar, verificador, redactar \| prompts \| proveedores | Sebastián \| Gino \| Anderson | Cada archivo tiene un solo dueño |
| src/asistente/ (opción C): flujo.py \| intenciones.py, prompts.py \| plantillas.py, verificador.py \| rag.py y kb/ y data/chat \| guardia.py | Anderson \| Gino \| Sebastián \| Rafael \| Mathias | Cada archivo tiene un solo dueño |
| src/motor/simular.py (opción C), src/app/pages/6_Asistente.py, eval/chat.py | Sebastián \| Jesús \| Gino | Solo el dueño |

### Reglas para no malograr a los demás

- **Firmas fijas:** tu módulo ya tiene su __init__.py con la firma de cada función (Anexo 5). Reemplazas el cuerpo, nunca la firma. Si crees que la firma está mal, avisa a Anderson y a Gino antes de cambiarla.
- **Nunca git add . ni git add -A:** agrega solo tus carpetas con git add <ruta>. Así no subes por accidente archivos de otro, datos generados ni .env.
- **Nada compartido:** no importes de las carpetas de otros, salvo src/contratos. Excepciones: la app solo importa src/servicio.
- **Una pequeña duplicación es mejor que un archivo compartido:** si necesitas una utilidad que ya existe en otra carpeta, cópiala a la tuya.
- **Configuración:** tus parámetros viven en tu config/<modulo>.yaml. No edites config/base.yaml.
- **Librerías nuevas:** instálala en tu laptop y pásale a Anderson el nombre y la versión. No edites requirements.txt.
- **Formato:** si formateas con ruff, solo sobre tu carpeta (ruff format src/<tu_carpeta>).
- **Probar sin esperar:** cada módulo se prueba con las fixtures de tests/fixtures y con data/muestra, sin depender del código de los demás.

### Comandos paso a paso

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

### Ventanas de integración

| **Hora** | **Ventana** | **Qué debe estar fusionado en main antes de la hora** | **Quién la cierra** |
|---|---|---|---|
| 11:00 | V0 | Estructura, contratos, stubs con firmas, fixtures, tareas.py y muestra de 20 personas | Anderson y Rafael |
| 12:00 | V1 | Ingesta v0, motor v0, reglas, esqueleto del modelo, esqueleto de la app y generador v1 | Cada dueño; Anderson verifica |
| 13:00 | V2 (control 1) | Servicio con regla 2 funcionando y pantalla Hoy conectada. Etiqueta v0-control1 | Anderson |
| 16:00 | V3 (control 2) | Modelo v1, motor completo con propuesta, pantallas Por qué y Plan, pruebas P0. Etiqueta v1-control2 | Anderson |
| 17:45 | V4 | Todo lo que se va a mostrar, con make test verde. A las 18:00 etiqueta v2-congelado | Anderson y Gino |
| Domingo | Solo correcciones | Pull requests pequeños con fallas corregidas. Etiqueta v3-final a las 11:00 | Anderson |

Antes de cada ventana: trae main a tu rama (git merge origin/main), corre python tareas.py test, sube tu rama, abre el pull request y avisa en el canal. Si tus pruebas fallan por algo que no es tuyo, avisa a Anderson; no lo arregles en carpeta ajena.

### Plantilla del pull request (.github/pull_request_template.md)

## Qué hace este cambio

(una o dos frases)

## Carpetas que toca

- [ ] Solo carpetas del autor

## Antes de pedir revisión

- [ ] python tareas.py test pasa
- [ ] No hay claves, .env ni datos generados
- [ ] No cambié ninguna firma ni ningún contrato
- [ ] Probé con las fixtures de tests/fixtures

## Cómo probarlo

(comando y resultado esperado)

## Anexo 1. Contratos entre módulos (resumen)

Movimiento      : customer_id str, transaction_id str, fecha_hora datetime, monto float, moneda "PEN",

tipo "ingreso"|"gasto", categoria str, comercio str, saldo float|None

ReporteCalidad   : filas_entrada int, filas_salida int, duplicados_eliminados int, faltantes dict,

atipicos int, suscripciones_duplicadas list, pagos_inferidos list,

pii_enmascarado int*, columnas_sensibles_descartadas list*

PagoConFecha     : pago_id str, dia int (dias hasta el pago), monto float, categoria str

EstadoPersona    : customer_id str, fecha_corte date, saldo float, pagos list[PagoConFecha], colchon float, semanas_historia int*

Pronostico       : por_horizonte {3|7|14: {"p5","p20","p50","p80": float}}  (ordenado: p5<=p20<=p50<=p80)

Decision         : numero_hoy int, por_pago list[{pago_id, permitido, semaforo "verde"|"ambar"|"rojo"}],

confianza "alta"|"media"|"baja", desglose dict, limites list[str], supuestos list[str]*, evidencia dict*,

propuestas list[Propuesta], respaldo bool*, registro_id str*

Propuesta        : propuesta_id str, texto str, monto float, pago_id str, antes dict, despues dict, confianza str

Registro         : una linea JSON por recomendacion: entradas, version_generador, version_modelo, semilla, hash_config

Funciones        : ingesta.cargar(origen) | modelo.predecir(historia, fecha) | reglas.regla1/regla2(historia, fecha)

motor.decidir(estado, pronostico, cfg) | servicio.consultar(id, fecha, metodo) | servicio.responder(propuesta_id, accion)

Opcion C        : IngresoExtra(dia, monto) | Escenario(ingresos_extra, gasto_hoy) | Respuesta(texto, intencion, fuente, citas, datos, acciones, registro_id)*

(* = adicion propuesta, ver la tabla anterior)

### Adiciones al Anexo A incluidas en la v9 (Anderson y Gino las aprueban en el cierre de las 11:00)

Al escribir los planes y leer el Challenge pack aparecieron huecos en los contratos de la v5. Ya están en el Anexo A de la v9. Hasta que Anderson y Gino las aprueben, trabaja asumiendo que existen.

| **Adición** | **Por qué** | **Quién la implementa** |
|---|---|---|
| EstadoPersona.semanas_historia (entero) | La confianza depende de las semanas de historia y el contrato no la traía | Anderson el campo, Mathias lo calcula, Sebastián lo usa |
| ingesta.cargar_etiquetas(origen) | La evaluación necesita las etiquetas sin que pasen por la ingesta normal | Mathias; solo la usa la evaluación |
| modelo.entrenar(movimientos_train, cfg, semilla) devuelve Modelo; Modelo.predecir, guardar y cargar; excepción HistoriaInsuficiente | El arnés de pares de semillas reentrena muchas veces | Gino |
| servicio.cargar_archivo(origen) devuelve ReporteCalidad; Decision.respaldo (booleano) | La app no importa la ingesta; hace falta un aviso visible del modo de respaldo | Anderson |
| Decision.supuestos (lista), Decision.evidencia (diccionario) y Decision.registro_id | El pack exige porqué con evidencia, supuestos y nivel de confianza, y trazabilidad por recomendación | Anderson el campo, Sebastián lo llena |
| ReporteCalidad.pii_enmascarado y columnas_sensibles_descartadas | Privacidad por diseño y control de variables sensibles | Anderson el campo, Mathias lo llena |
| servicio.salud(), servicio.auditar(registro_id) y scripts/auditar_recomendacion.py | Observabilidad y trazabilidad auditable; la pantalla Evaluación los muestra | Anderson |
| Opción C: Escenario, IngresoExtra y Respuesta; servicio.preguntar y servicio.simular; parámetro opcional ingresos_extra en motor.decidir | El asistente del semáforo consulta el motor con escenarios hipotéticos y responde con fuente y citas | Anderson los modelos, Sebastián el parámetro del motor |

## Anexo 2. Parámetros de configuración

| **Parámetro (config/config.yaml)** | **Valor inicial** | **Estado** |
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
| variables_sensibles | edad, genero, ubicacion, distrito, nombre, dni, telefono | Fijo; la ingesta descarta y una prueba verifica |
| umbral_alerta_sesgo | Por fijar | Antes de ver resultados |
| patrones_pii | DNI de 8 digitos, telefono de 9 digitos, correo, tarjeta de 13 a 19 digitos | Fijo |

## Anexo 3. Mapa del equipo

| **Persona** | **Rol** | **Carpeta** | **Le pides** |
|---|---|---|---|
| Anderson | Servicio, integración y calidad | src/contratos, src/servicio, tests/integracion, Makefile | Contratos, fixtures, servicio, entorno |
| Rafael | Data science | src/datos, src/reglas, eval/ | Datos, reglas, evaluación |
| Mathias | Ingesta y calidad | src/ingesta | Movimientos limpios, pagos inferidos, reporte |
| Sebastián | Motor de decisión | src/motor | Decision, semáforo, propuesta, desglose |
| Gino | Machine learning y líder | src/modelo | Modelo, decisiones, aprobación de contratos |
| Jesús | Frontend 1 | src/app (Hoy, Plan, componentes) | Pantallas Hoy y Plan, demo |
| Alberto | Frontend 2 | src/app (Por qué, Datos, Evaluación, tema) | Tema, pantallas, accesibilidad, video |

## Anexo 4. src/contratos/modelos.py completo (cópialo tal cual)

# src/contratos/modelos.py  (lo escribe Anderson; todos programan contra este archivo)

from __future__ import annotations

from datetime import date, datetime

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, model_validator

class _Base(BaseModel):

model_config = ConfigDict(frozen=True, extra="forbid")

class Movimiento(_Base):

customer_id: str

transaction_id: str

fecha_hora: datetime

monto: float                      # ingreso positivo, gasto negativo

moneda: Literal["PEN"] = "PEN"

tipo: Literal["ingreso", "gasto"]

categoria: str

comercio: str

saldo: Optional[float] = None

class PagoConFecha(_Base):

pago_id: str

dia: int                          # dias hasta el pago (0 a 14)

monto: float                      # siempre positivo

categoria: str

class EstadoPersona(_Base):

customer_id: str

fecha_corte: date

saldo: float

pagos: list[PagoConFecha]

colchon: float = 0.0

semanas_historia: int = 0

class Cuantiles(_Base):

p5: float

p20: float

p50: float

p80: float

@model_validator(mode="after")

def _ordenado(self):

if not (0 <= self.p5 <= self.p20 <= self.p50 <= self.p80):

raise ValueError("cuantiles desordenados o negativos")

return self

class Pronostico(_Base):

por_horizonte: dict[int, Cuantiles]      # claves exactas: 3, 7 y 14

@model_validator(mode="after")

def _horizontes(self):

if set(self.por_horizonte) != {3, 7, 14}:

raise ValueError("deben existir los horizontes 3, 7 y 14")

return self

Semaforo = Literal["verde", "ambar", "rojo"]

Confianza = Literal["alta", "media", "baja"]

class PagoDecision(_Base):

pago_id: str

dia: int

monto: float

permitido: float

semaforo: Semaforo

class Propuesta(_Base):

propuesta_id: str

texto: str

monto: float

pago_id: str

antes: dict

despues: dict

confianza: Confianza

class Decision(_Base):

numero_hoy: int                          # soles enteros, nunca negativo

por_pago: list[PagoDecision]

confianza: Confianza

desglose: dict

limites: list[str]

supuestos: list[str]

evidencia: dict

propuestas: list[Propuesta] = []

respaldo: bool = False

registro_id: str = ""

mensaje_falta: Optional[str] = None      # "no alcanza para el pago del dia 3: faltan S/200"

explicacion: str = ""                    # texto en lenguaje simple (plantilla o generativa)

explicacion_fuente: Literal["plantilla", "generativa"] = "plantilla"

class ReporteCalidad(_Base):

filas_entrada: int

filas_salida: int

duplicados_eliminados: int

faltantes: dict[str, int]

atipicos: int

suscripciones_duplicadas: list[dict]

pagos_inferidos: list[dict]

pii_enmascarado: int = 0

columnas_sensibles_descartadas: list[str] = []

rechazos: dict[str, int] = {}

## Anexo 5. Firmas de todos los módulos (stubs que existen desde V0)

# Cada paquete tiene un __init__.py con estas firmas desde V0 (cuerpo: raise NotImplementedError).

# 'historia' es un DataFrame con los movimientos LIMPIOS de UNA persona hasta la fecha de corte,

# con las columnas de Movimiento y la columna extra 'atipico_detectado' (bool).

# src/ingesta/__init__.py                                  (Mathias)

class ErrorIngesta(Exception): ...          # atributos: mensaje_usuario, detalle

def cargar(origen, cfg) -> tuple[pd.DataFrame, ReporteCalidad, list[dict]]

def proximos_pagos(pagos_inferidos, customer_id, fecha_corte, ventana=14) -> list[PagoConFecha]

def semanas_historia(movimientos, customer_id, fecha_corte) -> int

def cargar_etiquetas(origen) -> pd.DataFrame          # indexado por transaction_id; solo evaluacion

def detectar_pii(texto, cfg) -> list[str]

def enmascarar_pii(df, cfg) -> tuple[pd.DataFrame, int]

# src/reglas/__init__.py                                   (Rafael)

def regla1(historia, fecha, cfg) -> Pronostico

def regla2(historia, fecha, cfg) -> Pronostico

# src/modelo/__init__.py                                   (Gino)

class HistoriaInsuficiente(Exception): ...

FEATURES: list[str]

def construir_features(historia, fecha, cfg) -> dict[str, float]

def entrenar(movimientos_train, cfg, semilla) -> "Modelo"

class Modelo:  predecir(historia, fecha) -> Pronostico | guardar(ruta) | cargar(ruta) [classmethod]

# src/motor/__init__.py                                    (Sebastian)

def decidir(estado, pronostico, cfg) -> Decision

# src/datos/__init__.py                                    (Rafael)

def generar(n_personas=400, meses=24, semilla=12345, perturbado=False, parametros=None) -> tuple[pd.DataFrame, dict]

def particion(df, semilla=12345) -> dict

# src/servicio/__init__.py                                 (Anderson)  la app SOLO importa esto

def cargar_archivo(origen) -> ReporteCalidad

def consultar(customer_id, fecha, metodo="modelo") -> Decision

def responder(propuesta_id, accion) -> dict           # accion: "aprobar" | "rechazar"

def salud() -> dict                                   # p50, p95, tasa_error, tasa_respaldo, consultas

def auditar(registro_id) -> dict

def simular(customer_id, fecha, escenario) -> Decision                      # opcion C

def preguntar(customer_id, fecha, texto, contexto=None) -> Respuesta        # opcion C

# opcion C: src/motor/__init__.py  ->  decidir(estado, pronostico, cfg, ingresos_extra=())   (parametro OPCIONAL)

#           src/asistente/__init__.py (Anderson): preguntar(...) ; guardia.revisar(texto, cfg) -> (bool, motivo) (Mathias)

#           intenciones.clasificar(texto, cfg, proveedor=None) (Gino) ; rag.BaseConocimiento.buscar(consulta, k=3) (Rafael)

## Anexo 6. Datos de ejemplo para probar sin esperar

# tests/fixtures/estado_caso_orden_pagos.json

{"customer_id": "P0001", "fecha_corte": "2025-03-01", "saldo": 100, "colchon": 0, "semanas_historia": 12,

"pagos": [{"pago_id": "alquiler-03", "dia": 3, "monto": 300, "categoria": "alquiler"}]}

# tests/fixtures/pronostico_caso_orden_pagos.json   (el ingreso de 400 llega el dia 10)

{"por_horizonte": {"3":  {"p5": 0,   "p20": 0,   "p50": 0,   "p80": 0},

"7":  {"p5": 0,   "p20": 0,   "p50": 0,   "p80": 0},

"14": {"p5": 300, "p20": 400, "p50": 500, "p80": 600}}}

# resultado esperado de motor.decidir con estos dos archivos

numero_hoy = 0      mensaje_falta = "no alcanza para el pago del dia 3: faltan S/200"

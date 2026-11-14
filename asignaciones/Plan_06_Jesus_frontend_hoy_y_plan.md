**Hackathon de Ingeniería BBVA · AI Financial Life · Plan individual**

**Jesús · Frontend 1: pantallas Hoy y Plan propuesto**

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

Eres la cara de la demo: la persona ve un número, entiende si sus pagos están cubiertos y aprueba o rechaza una propuesta. Empiezas con decisiones de ejemplo (fixtures) y conectas el servicio real cuando esté listo, de modo que nunca esperas a los demás.

### Qué recibes y de quién

| **Qué** | **De** | **Hora** |
|---|---|---|
| Contratos y fixtures de Decision | Anderson | 10:45 |
| tema.py (paleta, contraste, tamaños) | Alberto | 11:15 |
| servicio.consultar real | Anderson | 13:00 |

### Qué entregas y a quién

| **Qué** | **A** | **Hora** |
|---|---|---|
| Navegación y aviso en todas las páginas | Alberto, Anderson | 11:00 |
| Pantalla Hoy con fixtures | Todos | 12:00 |
| Pantalla Hoy conectada al servicio | Todos | 13:00 |
| Pantalla Plan propuesto con aprobar y rechazar | Todos | 16:00 |
| Demo ensayada y modo de respaldo | Pitch | 18:30 y domingo |

## 3. Tus primeros pasos exactos (empieza por aquí)

Hazlos en este orden. No esperes a nadie: todo lo que necesitas para empezar está en los anexos de este plan.

- **1.** Clona el repositorio y crea la rama feat/jesus-hoy.
- **2.** Pon el bloque de sys.path al inicio de main.py y de cada página.
- **3.** Escribe servicio_falso.py y estado.py; corre APP_FAKE=1 y streamlit run src/app/main.py: debe abrir con el aviso.
- **4.** Construye 1_Hoy.py con las fixtures verde y roja y su prueba AppTest.
- **5.** Sube el primer pull request antes de las 12:00. Cuando Anderson publique el servicio, cambia a la versión real.

## 4. Qué haces tú con el Challenge pack (tareas nuevas)

Tres tareas nuevas. El pack dice que no basta una demo cosmética; tu guion cronometrado es lo que lo demuestra.

| **#** | **Qué haces** | **Cómo y dónde** | **Hora** | **Cómo sabes que está bien** |
|---|---|---|---|---|
| 1 | Supuestos y límites en Hoy | Bajo el número, un bloque Supuestos y límites que lista Decision.supuestos y Decision.limites en lenguaje simple. Abierto por defecto. | 14:00 | AppTest: aparece cada supuesto y cada límite de la fixture |
| 2 | Evidencia en Plan propuesto | Junto a la propuesta, mostrar Decision.evidencia: semanas de historia, pagos detectados y rango a 14 días. | 15:00 | AppTest: la evidencia de la fixture está en pantalla |
| 3 | Guion de la demo de 5 minutos | docs/guion_demo.md con segundos: 0:00 persona y número de hoy (30 s); 0:30 semáforo y pago límite (40 s); 1:10 el porqué con supuestos y límites, con Alberto (50 s); 2:00 aprobar la propuesta (40 s); 2:40 calidad de los datos en Evaluación: duplicados eliminados y PII enmascarada (60 s); 3:40 panel de salud y auditar una recomendación (40 s); 4:20 volver a la persona y cierre (40 s). Para cada paso, qué hacer si falla. | Sábado 18:30 | Tres ensayos seguidos de 5:00 o menos |

## 5. Tu especificación técnica

### 1. Estructura de la app (src/app)

- **Archivos:** main.py (navegación), pages/1_Hoy.py y pages/2_Plan.py (tuyas), pages/3_Por_que.py y 5_Evaluacion.py (de Alberto), componentes.py (semáforo, tarjeta de número, aviso: tuyo, lo usa Alberto), estado.py (persona, fecha y método en el estado de la sesión), tema.py (de Alberto), servicio_falso.py (tuyo).
- **Regla de oro:** la app solo llama a servicio.consultar, servicio.responder, servicio.salud y servicio.auditar (y servicio.preguntar si se llega a la opción C). Nunca importa modelo, motor ni ingesta, y no carga archivos: los datos son sintéticos y vienen precargados.
- **servicio_falso:** misma firma que el servicio real, pero devuelve las fixtures de tests/fixtures. Se activa con la variable APP_FAKE igual a 1. Con él trabajas desde las 10:45 y, además, sirve de respaldo de la demo.

### 2. Pantalla Hoy

- **Selector:** persona de demo (5 personas precargadas) y fecha de corte. Cambiarlos vuelve a llamar a consultar.
- **Número:** una línea grande: Hoy puedes gastar hasta S/45. Si el número es 0, el texto cambia a No alcanza para el pago del día d: faltan S/X, con el desglose de Sebastián.
- **Semáforo de 14 días:** lista de los próximos pagos con su fecha y su estado. Cada estado usa texto y símbolo además del color (por ejemplo el símbolo y la palabra Cubierto, Con riesgo o No cubierto). No dependas solo del color.
- **Banner de respaldo:** si Decision.respaldo es verdadero, un aviso claro: se está usando la regla sencilla.
- **Aviso obligatorio:** Orientación educativa basada en una simulación con datos ficticios. No es asesoría financiera ni ejecuta operaciones. Va en cada página, desde componentes.aviso().

### 3. Pantalla Plan propuesto

- **Contenido:** la propuesta de Sebastián con su texto, el efecto antes y después en una tabla, la confianza y los límites.
- **Botones:** Aprobar y Rechazar. Cada uno llama a servicio.responder una sola vez y muestra: Simulación: no se movió ningún dinero. Se deshabilitan después del clic.
- **Sin propuesta:** mensaje explicando por qué (ya estás cubierto en una semana mala, o no alcanza ni gastando cero).

### 4. Estados, errores y rendimiento

- **Sin datos:** mensaje que guía: carga un archivo en Datos o usa una persona de demo.
- **Errores:** ningún traceback ni pantalla en blanco. El servicio devuelve mensajes; la app solo los muestra.
- **Espera:** indicador de carga mientras llega la Decision.
- **Accesibilidad:** texto de al menos 16 px y contraste desde tema.py, diseño centrado que se lea en celular, orden lógico para teclado.
- **Rendimiento:** mide cuánto tarda cada pantalla en responder y pásale los números a Anderson. Objetivo: menos de 2 segundos [SUPUESTO].
- **Demo:** datos precargados en data/demo para que la demo funcione sin modelo ni red. Tú manejas la demo en vivo [propuesto], con una laptop de respaldo.

## 6. Archivos y funciones que escribes (con código)

Tu app solo habla con src/servicio. Mientras Anderson no lo publique, usas servicio_falso con las fixtures, que tiene la misma firma. Así empiezas a las 10:45 sin esperar a nadie.

### Streamlit no encuentra src: primera línea de cada archivo

# Se pone al INICIO de main.py y de cada pagina (Streamlit solo agrega la carpeta del script al path)

import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # raiz del repositorio

En las páginas, que están en src/app/pages, el índice cambia a parents[3]. Compruébalo con un print la primera vez.

### src/app/servicio_falso.py y src/app/estado.py

# servicio_falso.py: misma firma que src/servicio

def consultar(customer_id, fecha, metodo="modelo"):

nombre = {"P0001": "decision_verde", "P0002": "decision_rojo", "P0003": "decision_confianza_baja",

"P0004": "decision_sin_alcance"}.get(customer_id, "decision_verde")

return Decision.model_validate_json(Path(f"tests/fixtures/{nombre}.json").read_text(encoding="utf-8"))

def responder(propuesta_id, accion): return {"ok": True, "accion": accion}

# (no hay carga de archivos: los datos son sinteticos y precargados)

def salud(): return {"p50": 120, "p95": 300, "tasa_error": 0.0, "tasa_respaldo": 0.0, "consultas": 10}

# estado.py

def servicio():       # APP_FAKE=1 usa el falso; si no, el real

if os.environ.get("APP_FAKE") == "1":

from src.app import servicio_falso as s

else:

from src import servicio as s

return s

### src/app/componentes.py

AVISO = ("Orientación educativa basada en una simulación con datos ficticios. "

"No es asesoría financiera ni ejecuta operaciones.")

def aviso():                              # va en TODAS las paginas, incluidas las de Alberto

st.caption(AVISO)

def numero_hoy(decision):                 # linea grande

if decision.numero_hoy == 0 and decision.mensaje_falta:

st.error(decision.mensaje_falta)

else:

st.markdown(f"## Hoy puedes gastar hasta S/{decision.numero_hoy}")

def semaforo(pago):                       # texto + simbolo + color (nunca solo color)

texto = {"verde": "✔ Cubierto", "ambar": "▲ Con riesgo", "rojo": "✖ No cubierto"}[pago.semaforo]

st.markdown(f"**Dia {pago.dia}** · S/{pago.monto:.0f} · {texto}")

def banner_respaldo(decision):

if decision.respaldo:

st.warning("Se está usando la regla sencilla porque el modelo no está disponible.")

### Páginas 1_Hoy.py y 2_Plan.py

# 1_Hoy.py

s = servicio()

persona = st.selectbox("Persona de demo", ["P0001", "P0002", "P0003", "P0004"])

fecha = st.date_input("Fecha de corte")

try:

d = s.consultar(persona, fecha)

except Exception as e:

st.error("No pudimos calcular tu número. Intenta con otra persona o fecha."); st.stop()

banner_respaldo(d); numero_hoy(d)

for p in d.por_pago: semaforo(p)

with st.expander("Supuestos y límites", expanded=True):

for t in d.supuestos + d.limites: st.write("- " + t)

st.caption(d.explicacion)                  # plantilla (o texto de IA si se activa la opcion B)

aviso()

# 2_Plan.py: muestra d.propuestas[0] (texto, tabla antes y despues, d.evidencia, d.confianza) con dos botones.

# Cada boton llama a s.responder(propuesta_id, "aprobar" | "rechazar") UNA vez y se deshabilita.

# Mensaje al responder: "Simulación: no se movió ningún dinero."

### Prueba con AppTest

from streamlit.testing.v1 import AppTest

def test_hoy_muestra_numero():

os.environ["APP_FAKE"] = "1"

at = AppTest.from_file("src/app/pages/1_Hoy.py").run()

assert any("Hoy puedes gastar" in m.value for m in at.markdown)

## 7. Opción B (capa generativa): tu parte si se activa

Esta sección solo se ejecuta si se cumplen las cinco condiciones del diseño de la opción B: autorización por escrito de la organización, control 1 aprobado, antes de las 17:00, clave de OpenAI funcionando en las dos laptops y pruebas P0 en verde. Si falta una, no hagas nada de esto. T0 es la hora de la autorización; con T0 después de las 14:30 no se activa.

Resumen del diseño: el modelo solo reescribe el porqué que el motor ya calculó. Ve una entrada mínima sin identificadores. Un verificador sin IA exige que cada cifra del texto exista en esa entrada; si algo falla, se muestra la plantilla. La clave de OpenAI vive solo en .env.

### Tu tarea (T0+90 a T0+150)

- **Hoy y Por qué:** ya muestras Decision.explicacion. Con la capa activa será texto redactado por IA; si no, es la plantilla. No cambies nada de la lógica: solo asegúrate de mostrarla bajo el número.
- **Guion de demo:** agrega un paso de 20 segundos: se enciende la capa y se muestra una explicación; luego se apaga el proveedor (quitando la clave) y se muestra que la pantalla sigue funcionando con la plantilla. Pon cada paso con su plan B.

## 8. Opción C (asistente del semáforo con LLM, RAG y ML): tu parte si se llega al corte

Esta sección es nivel P2. Puntos de corte: A a las 13:00 (si el control 1 salió bien, empieza quien tenga holgura), B a las 16:00 (se integra el flujo si el control 2 salió bien), C a las 17:30 (lo que no pase la evaluación no entra a la demo) y D a las 17:45 (fusión final). El asistente nunca desplaza una prueba P0.

Qué es: una pantalla de chat donde la persona pregunta por su número, sus pagos y escenarios. Usa el motor y el modelo como herramientas de ML, una base de conocimiento propia con búsqueda local (RAG) y, si se activa, un LLM para entender y redactar con cada cifra verificada. Funciona completo sin LLM (modo 1). Se inspira en las lecciones del copiloto del bot_diagnosis: no se copia código, datos ni playbooks.

### Tu archivo: src/app/pages/6_Asistente.py

s = servicio()

persona = st.session_state.get("persona", "P0001")

if "chat" not in st.session_state: st.session_state.chat = []

st.header("Pregúntale a tu semáforo")

for m in st.session_state.chat:

with st.chat_message(m["rol"]): st.write(m["texto"])

SUGERIDAS = ["¿Por qué solo puedo gastar este monto hoy?", "¿Me alcanza para mi pago del día 3?", "¿Y si cobro S/200 el día 5?"]

cols = st.columns(3)

for c, q in zip(cols, SUGERIDAS):

if c.button(q): st.session_state.pendiente = q

pregunta = st.chat_input("Escribe tu pregunta (máximo 200 caracteres)", max_chars=200) or st.session_state.pop("pendiente", None)

if pregunta:

r = s.preguntar(persona, fecha, pregunta)                 # Respuesta

# muestra: Datos (tabla corta desde r.datos) | Qué significa (r.texto) | Qué puedes hacer (r.acciones)

# etiqueta de fuente: "Calculado por el motor" | "Base de conocimiento" | "Redactado con IA y verificado" | "Plantilla" | "No puedo ayudar con eso"

# citas en un expander: r.citas

aviso()

- **Servicio falso:** agrega preguntar y simular a servicio_falso.py con tres respuestas de las fixtures para trabajar desde el corte A sin esperar a nadie.
- **Conjunto ciego:** escribe 15 preguntas (con la intención esperada y la cifra clave) en data/chat/ciego_jesus.csv. No miras el conjunto de entrenamiento ni el clasificador. Alberto escribe las otras 15.
- **Demo:** agrega al guion los tres momentos del asistente: por qué este número, y si cobro tal día, y una pregunta fuera de alcance que se rechaza. Con su plan B: si falla el asistente, se muestra Por qué.
- **Prueba AppTest:** una pregunta sugerida produce una respuesta con etiqueta de fuente; una pregunta vacía no llama al servicio; el aviso está presente.

## 9. Tus horas (sábado 14 y domingo 15)

| **Hora (Lima)** | **Qué haces** | **Debe quedar verificable** |
|---|---|---|
| 10:15 a 11:00 | Entorno. main.py con navegación, componentes.aviso y servicio_falso con las fixtures de Anderson. | make demo abre con las páginas vacías y el aviso |
| 11:00 a 12:00 | Hoy v0 con las fixtures verde, rojo y confianza baja. Primera prueba con AppTest. | AppTest de Hoy pasa con el servicio falso |
| 12:00 a 13:00 | Hoy conectada a servicio.consultar con respaldo al falso. Control 1. | Etiqueta v0-control1 con Hoy real |
| 13:00 a 16:00 | Plan propuesto: antes y después, aprobar y rechazar, estados vacíos y de error. Control 2. | AppTest de aprobar llama a responder una vez |
| 16:00 a 18:00 | Modo de respaldo, banner, datos de demo precargados. Medir latencia. Pulir con Alberto. | La demo corre sin modelo |
| 18:00 a 19:30 | Ensayo completo de la demo. Lista de fallos y arreglos. | Tres corridas seguidas |
| Domingo 8:30 a 11:00 | Correcciones. Laptop de respaldo con el repositorio. Ensayo con cronómetro. | Demo de 3 minutos sin tropiezos |
| Domingo 11:00 a 13:30 | Ensayos con el equipo. Demo en vivo. | Demo corre tres veces seguidas |

Los horarios son supuestos hasta que la organización comunique los suyos. Si cambian, Gino reordena este cuadro.

## 10. Tus pruebas

| **Prueba** | **Qué verifica** | **Criterio de éxito** |
|---|---|---|
| Hoy con fixture verde | AppTest muestra el número y los pagos en estado Cubierto | Texto esperado presente |
| Hoy con fixture sin alcance | Número 0 y mensaje de falta | El mensaje nombra el pago y el monto |
| Aviso obligatorio | Todas las páginas contienen el aviso | Presente en las cinco |
| Semáforo sin color | El estado aparece como texto y símbolo | Texto presente |
| Aprobar y rechazar | Un clic llama a responder una vez y deshabilita los botones | Una llamada por clic |
| Error del servicio | El servicio lanza un error simulado | Mensaje claro, sin traceback |
| Sin datos | Sin persona seleccionada o sin archivo | Mensaje que guía |
| Banner de respaldo | Decision con respaldo verdadero | Banner visible |
| Latencia | Tiempo de cada pantalla | Medido y anotado |
| Supuestos y límites en Hoy | AppTest con la fixture | Cada texto presente |
| Evidencia en Plan | AppTest con la fixture | Evidencia visible |
| Demo cronometrada | Ensayo completo del guion | 5:00 o menos, tres veces |

Escribe cada prueba antes que el código cuando puedas (primero rojo, después verde). Cobertura objetivo de tu módulo: al menos 80 % [SUPUESTO].

## 11. Cuándo estás listo (definición de hecho)

- **[ ]** Hoy y Plan propuesto funcionan con el servicio real y con el falso
- **[ ]** Aviso obligatorio y banner de respaldo presentes
- **[ ]** Estados vacíos y de error sin traceback
- **[ ]** Datos de demo precargados; la demo corre sin modelo ni red
- **[ ]** Pruebas AppTest en verde y latencia medida
- **[ ]** Demo ensayada tres veces seguidas
- **[ ]** Supuestos y límites visibles en Hoy
- **[ ]** Evidencia visible en Plan propuesto
- **[ ]** docs/guion_demo.md con tiempos y plan B por paso
- **[ ]** Demo de 5 minutos ensayada tres veces seguidas

## 12. Riesgos y qué hacer

| **Riesgo** | **Plan B** |
|---|---|
| El servicio real se retrasa | Seguir con servicio_falso: la demo se puede mostrar igual con la fixture |
| Streamlit se comporta distinto en la laptop de la demo | Probar en la laptop de la demo el sábado por la noche y tener el video de Alberto |
| Falla la red en la sala | La app no usa red; confirmar que no haya fuentes ni imágenes externas |

## 13. Tu parte del pitch

| **Tema** | **Contenido** |
|---|---|
| Qué cuentas | La demo en vivo de los minutos 2 a 5: el número de hoy, aprobar una propuesta y la calidad de los datos en Evaluación. |
| Cifras que debes tener | Latencia de las pantallas [por medir]; tiempo hasta entender el número en la prueba de comprensión [por medir]. |
| Pregunta que te toca | Qué hace si falla el modelo o no hay internet: la demo corre con los datos precargados y el respaldo. |
| En el formato de 5 minutos | Conduces los 5 minutos de demo con el guion cronometrado, apoyado por Alberto en el porqué. |

El formato no está confirmado: la guía impresa dice 10 minutos más 3 de preguntas y el Challenge pack sugiere 5 de pitch, 5 de demo y 5 de preguntas. Prepara primero el corto. La regla de oro: ningún número sin su origen. La autocrítica se dice antes de que pregunten.

## 14. Git y trabajo en paralelo: cómo subir tu parte sin malograr la de los demás

Tu trabajo vive en tus ramas y en tus carpetas. Así puedes programar al mismo tiempo que los otros seis sin pisar nada. Tus ramas sugeridas: feat/jesus-hoy, feat/jesus-plan.

### Qué es tuyo y qué no

- **Tus carpetas:** src/app/main.py, componentes.py, estado.py, servicio_falso.py, pages/1_Hoy.py, pages/2_Plan.py, tests/unit/app_hoy_plan, docs/guion_demo.md.
- **Todo lo demás:** no lo edites. Si necesitas un cambio en una carpeta ajena, escribe al dueño o abre un pull request pequeño para él. Tabla completa de dueños en el Anexo E de la v9.
- **Tu revisor:** Alberto. Tú revisas a quien te toque en el cuadro de revisión cruzada.

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

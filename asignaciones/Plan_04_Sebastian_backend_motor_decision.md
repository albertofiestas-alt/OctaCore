**Hackathon de Ingeniería BBVA · AI Financial Life · Plan individual**

**Sebastián · Backend: motor de decisión**

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

Eres el corazón de la propuesta: conviertes el pronóstico en una decisión por fecha de pago, con semáforo, confianza, propuesta y explicación trazable. Tu primera línea de código es la prueba del caso del orden de pagos, que la fórmula de la v3 hacía mal.

### Qué recibes y de quién

| **Qué** | **De** | **Hora** |
|---|---|---|
| Contratos, fixtures y estado de ejemplo | Anderson | 10:45 |
| Pagos próximos y semanas de historia en el estado | Mathias, Anderson | 12:00 |
| Pronostico de la regla 2 y luego del modelo | Rafael, Gino | 12:30 y 15:30 |

### Qué entregas y a quién

| **Qué** | **A** | **Hora** |
|---|---|---|
| motor.decidir con número, semáforo y desglose | Anderson, Jesús, Alberto | 12:30 |
| confianza, propuesta y plantillas | Todos | 16:00 |
| Pruebas de propiedades y casos de estrés del motor | Anderson (mutaciones) | 18:00 |
| Casos donde el motor propone poco o nada | Rafael, pitch | 19:00 |

## 3. Tus primeros pasos exactos (empieza por aquí)

Hazlos en este orden. No esperes a nadie: todo lo que necesitas para empezar está en los anexos de este plan.

- **1.** Clona el repositorio y crea la rama feat/sebastian-motor.
- **2.** Escribe la prueba del caso del orden de pagos (está completa en este plan) y confirma que falla.
- **3.** Implementa ingreso_conservador, numerador, puntos_de_control y permitido; luego decidir con número de hoy y mensaje de falta, hasta que la prueba pase.
- **4.** Agrega el semáforo y el desglose. Sube el primer pull request antes de las 12:30.
- **5.** Luego confianza, propuesta, supuestos, evidencia y plantillas.

## 4. Qué haces tú con el Challenge pack (tareas nuevas)

Cinco tareas nuevas. El pack exige que toda recomendación explique el porqué con evidencia, supuestos y nivel de confianza; eso sale de tu módulo.

| **#** | **Qué haces** | **Cómo y dónde** | **Hora** | **Cómo sabes que está bien** |
|---|---|---|---|---|
| 1 | Decision.supuestos | Lista construida con plantillas y las cifras del estado: la persona gasta cada día lo que indica el número de hoy; los pagos con fecha son los N detectados en su historial; el ingreso futuro se parece al de las últimas S semanas; no se consideran gastos imprevistos; P20 y P5 representan una semana mala y una muy mala. | 14:00 | Nunca vacía; cada cifra del texto sale del estado o del desglose |
| 2 | Decision.evidencia | Diccionario con semanas_historia, número de pagos detectados, rango a 14 días (p5, p50, p80), cuantil usado y el punto de control que limita. | 14:30 | Presente en todos los casos |
| 3 | Límites de recomendación | Frases fijas: es una orientación educativa y no sustituye asesoría financiera; no promete resultados; el futuro puede diferir del pronóstico. | 14:30 | Siempre presentes |
| 4 | registro_id en el desglose | El servicio genera el identificador y te lo pasa; lo copias al desglose. No lo inventas tú. | 15:00 | El desglose trae el id que el servicio escribió en el Registro |
| 5 | Verificador de textos | Propiedad con hypothesis: toda cifra que aparece en supuestos, límites o plantillas existe en el estado, el desglose o la evidencia. | 15:00 a 16:00 | Cero contraejemplos |

## 5. Tu especificación técnica

### 1. motor.decidir(estado, pronostico, cfg) devuelve Decision

La función es pura: no lee archivos ni la hora, no cambia sus entradas y devuelve objetos nuevos. Todo parámetro sale de cfg.

- **Ingreso conservador de un pago a d días:** h* es el mayor h de {3, 7, 14} con h menor o igual a d; el ingreso es pronostico[h*][cuantil] y 0 si d es menor que 3. Para d mayor que 14 se usa h igual a 14. Subestima a propósito.
- **permitido(d, q):** (saldo + ingreso(d, q) - suma de los pagos con día menor o igual a d - colchón) dividido entre max(d, 1).
- **Puntos de control:** cada día distinto en el que vence un pago, más el día 14. Si no hay pagos, solo el día 14.
- **Número de hoy:** max(0, mínimo de permitido(d, P20) sobre los puntos de control), redondeado hacia ABAJO a soles enteros. Nunca se redondea hacia arriba.
- **Mensaje de falta:** si el mínimo es negativo, el punto de control que lo produce da el mensaje: no alcanza para el pago del día d: faltan S/X, con X igual a la parte entera hacia arriba de menos el numerador (saldo + ingreso - pagos - colchón).
- **Semáforo por pago (día d_k):** cobertura(q) es saldo + ingreso(d_k, q) - suma de pagos con día menor o igual a d_k, mayor o igual a 0 (sin colchón). Verde si se cubre con P5; ámbar si se cubre con P50 pero no con P5; rojo si no.
- **Confianza:** ancho relativo igual a (p80 - p5) a 14 días dividido entre max(p50 a 14 días, 1). Baja si semanas_historia es menor que el umbral (4) o el ancho supera el umbral bajo; alta si el ancho es menor que el umbral alto y hay historia suficiente; media en los demás casos. Umbrales [por fijar antes de ver resultados].

### 2. Propuesta (una sola en el MVP) [propuesto, confirmar con Gino]

Definición pensada para que sea simple y verificable. Sea g20 el número de hoy y g5 el mismo cálculo con el cuantil P5.

- **Cuándo se propone:** si g5 es mayor o igual que 0 y menor que g20, hay una propuesta: gastar hasta S/g5 por día en vez de S/g20 y apartar S/(g20 - g5) por día para el pago que limita (el punto de control donde se alcanza el mínimo en P5).
- **Cuándo no:** si g5 es mayor o igual que g20, no hace falta proponer (se cubre incluso en una semana mala). Si g5 es negativo, no hay propuesta posible: se muestra el mensaje de falta y nada más.
- **Verificación:** el verificador recalcula la cobertura en P5 en todos los puntos de control gastando g5 por día y falla con una aserción si algún pago queda descubierto. Es la prueba de que solo se muestra lo que aguanta el escenario pesimista.
- **Contenido:** texto, monto, pago, antes y después (número de hoy, semáforo del pago límite), confianza y límites.

### 3. Desglose y plantillas

- **Desglose:** saldo, colchón, para cada punto de control el ingreso conservador, los pagos acumulados y el permitido, el punto que limita y el cuantil usado. Alberto lo dibuja en la pantalla Por qué.
- **Plantillas (src/motor/plantillas.py):** texto en soles y fechas, sin tasas. Toda cifra del texto sale del desglose. Un registro por tipo de propuesta permite agregar uno nuevo en la prueba de evolución sin tocar el resto.
- **Límites:** lista de frases fijas: el ingreso futuro es un rango; el P20 asume una semana mala moderada; datos ficticios; con pocas semanas de historia la confianza baja.

## 6. Archivos y funciones que escribes (con código)

Tu módulo es una función pura: decidir(estado, pronostico, cfg). No lee archivos, no lee la hora y no cambia sus entradas. Lo pruebas solo con los JSON del Anexo 6 de este plan, sin esperar a nadie.

### Aclaraciones fijadas (del cotejo con Formula_Gasto_Diario_Permitido.docx y Determinacion_Limite_Final.docx)

- **Nombre:** la cifra se llama numero_hoy en el código y en los contratos (entero en soles), no numero_de_hoy.
- **Ingreso conservador:** no es una estimación exacta hasta el día d: es el cuantil del mayor horizonte h de {3, 7, 14} con h menor o igual a d, y 0 si d es menor que 3.
- **Pago de hoy:** si d es 0, el divisor es max(d, 1).
- **Redondeo:** número de hoy hacia abajo y faltante hacia arriba.
- **Qué pago se nombra:** el que LIMITA (el punto donde se alcanza el mínimo), no necesariamente el más próximo.

### Paso 1 (10:15): escribe la prueba primero

# tests/unit/motor/test_orden_pagos.py

def test_orden_de_pagos():

estado = EstadoPersona.model_validate_json(open("tests/fixtures/estado_caso_orden_pagos.json").read())

pron = Pronostico.model_validate({"por_horizonte": {

3:  {"p5": 0, "p20": 0, "p50": 0, "p80": 0},

7:  {"p5": 0, "p20": 0, "p50": 0, "p80": 0},

14: {"p5": 300, "p20": 400, "p50": 500, "p80": 600}}})

d = decidir(estado, pron, CFG_PRUEBA)

assert d.numero_hoy == 0

assert "faltan S/200" in d.mensaje_falta

### Paso 2 (11:00): src/motor/decidir.py

ATRIBUTO = {0.05: "p5", 0.20: "p20", 0.50: "p50", 0.80: "p80"}

def _h_para_dia(d, horizontes):

# mayor horizonte h con h <= d; 0 si ninguno (entonces el ingreso conservador es 0)

candidatos = [h for h in horizontes if h <= min(d, 14)]

return max(candidatos) if candidatos else 0

def ingreso_conservador(pron, d, cuantil, horizontes):

h = _h_para_dia(d, horizontes)

return 0.0 if h == 0 else getattr(pron.por_horizonte[h], ATRIBUTO[cuantil])

def numerador(estado, pron, d, cuantil, cfg, con_colchon=True):

pagos = sum(p.monto for p in estado.pagos if p.dia <= d)

colchon = estado.colchon if con_colchon else 0.0

return estado.saldo + ingreso_conservador(pron, d, cuantil, cfg["horizontes_dias"]) - pagos - colchon

def puntos_de_control(estado):

return sorted({p.dia for p in estado.pagos} | {14})

def permitido(estado, pron, d, cuantil, cfg):

return numerador(estado, pron, d, cuantil, cfg) / max(d, 1)

def decidir(estado, pron, cfg) -> Decision:

q = cfg["cuantil_conservador"]                                   # 0.20

pts = puntos_de_control(estado)

perm = {d: permitido(estado, pron, d, q, cfg) for d in pts}

d_lim = min(perm, key=perm.get)                                  # punto que limita

numero = int(math.floor(max(0.0, perm[d_lim])))                  # SIEMPRE hacia abajo

falta = None

if perm[d_lim] < 0:

faltante = math.ceil(-numerador(estado, pron, d_lim, q, cfg))

falta = f"no alcanza para el pago del dia {d_lim}: faltan S/{faltante}"

por_pago = [PagoDecision(pago_id=p.pago_id, dia=p.dia, monto=p.monto,

permitido=perm[p.dia], semaforo=_semaforo(estado, pron, p, cfg)) for p in estado.pagos]

confianza = _confianza(estado, pron, cfg)

propuestas = _proponer(estado, pron, cfg, numero, d_lim)

# desglose, evidencia, supuestos y limites: ver plantillas.py

return Decision(numero_hoy=numero, por_pago=por_pago, confianza=confianza, ...)

| **Función** | **Regla exacta** |
|---|---|
| _semaforo | cobertura(q) = saldo + ingreso(d, q) - suma de pagos con día menor o igual a d, sin colchón. Verde si cobertura con p5 mayor o igual a 0; ámbar si no con p5 pero sí con p50; rojo en otro caso. |
| _confianza | ancho = (p80 - p5) a 14 días dividido entre max(p50 a 14 días, 1). Baja si semanas_historia es menor que umbral_historia_semanas o ancho mayor que ancho_bajo; alta si ancho menor que ancho_alto y hay historia suficiente; media en los demás casos. Umbrales en config/motor.yaml [por fijar]. |
| _proponer | g5 = mínimo de permitido con p5 en todos los puntos. Si g5 mayor o igual a 0 y menor que el número de hoy, una propuesta: gastar hasta S/g5 por día y apartar S/(número - g5) por día para el pago límite. Verifica con una aserción que, gastando g5, la cobertura en p5 de todos los puntos es mayor o igual a 0. Si g5 es negativo, no hay propuesta; si g5 mayor o igual que el número, no hace falta. |
| Redondeo | Siempre hacia abajo (floor) en el número de hoy y hacia arriba (ceil) en el faltante. Nunca se redondea a favor del gasto. |

### Paso 3 (13:00): src/motor/plantillas.py

def supuestos(estado, evidencia) -> list[str]:

return [

"Gastas cada dia lo que indica el numero de hoy.",

f"Los pagos con fecha son los {len(estado.pagos)} detectados en tu historial.",

f"El ingreso futuro se parece al de las ultimas {estado.semanas_historia} semanas.",

"No se consideran gastos imprevistos.",

"El escenario P20 es una semana mala y el P5 una semana muy mala."]

LIMITES = ["Es una orientacion educativa y no sustituye asesoria financiera.",

"No promete resultados.", "El futuro puede diferir del pronostico."]

def explicar(numero, mensaje_falta, por_pago, confianza) -> str:

# texto en soles y fechas; toda cifra sale del estado o del desglose; nada de tasas

...

config/motor.yaml: ancho_alto 0.5, ancho_bajo 1.2 (ambos [por fijar] y los fija Gino en el pre-registro). El registro_id lo genera el servicio y tú solo lo copias al desglose.

## 7. Opción B (capa generativa): tu parte si se activa

Esta sección solo se ejecuta si se cumplen las cinco condiciones del diseño de la opción B: autorización por escrito de la organización, control 1 aprobado, antes de las 17:00, clave de OpenAI funcionando en las dos laptops y pruebas P0 en verde. Si falta una, no hagas nada de esto. T0 es la hora de la autorización; con T0 después de las 14:30 no se activa.

Resumen del diseño: el modelo solo reescribe el porqué que el motor ya calculó. Ve una entrada mínima sin identificadores. Un verificador sin IA exige que cada cifra del texto exista en esa entrada; si algo falla, se muestra la plantilla. La clave de OpenAI vive solo en .env.

### Tus archivos: src/generativa/minimizar.py, verificador.py y redactar.py (T0 a T0+90)

# minimizar.py: lista blanca. NADA fuera de estas claves sale de la laptop.

CLAVES = {"numero_hoy", "ventana_dias", "pagos", "punto_limite", "confianza", "evidencia", "supuestos", "limites", "propuesta"}

def minimizar(decision) -> dict:

# numeros, dias ("dia 3") y frases fijas del motor. Sin customer_id, comercios, fechas absolutas ni texto libre.

...

# verificador.py: determinista, sin modelo de lenguaje

def cifras_de(entrada) -> set[float]: ...              # numero_hoy, dias, montos, semanas, rango, faltante, ventana_dias

def verificar(texto_json, entrada, cfg):

obj = _parsear(texto_json)                          # 1 JSON valido con la clave "texto"

if obj is None: return False, ["json_invalido"]

t = obj["texto"]

if len(t.split()) > cfg["generativa"]["max_palabras"]: return False, ["largo"]          # 2

usadas = _numeros_en(t) + _palabras_numericas_en(t)                                      # 3: S/45, 45, "tres", "cien"

extra = [x for x in usadas if x not in cifras_de(entrada)]

if extra: return False, [f"cifra_inventada:{extra}"]

if f"S/{entrada['numero_hoy']}" not in t: return False, ["falta_numero_hoy"]              # 4

if entrada["pagos"] and any(p["semaforo"] != "verde" for p in entrada["pagos"]) \

and f"dia {entrada['punto_limite']['dia']}" not in _sin_tildes(t): return False, ["falta_dia_limite"]

if entrada["confianza"] not in t: return False, ["falta_confianza"]

if _contiene_prohibidas(t, cfg): return False, ["prohibida"]                              # 5

if _contradice(t, entrada): return False, ["contradiccion"]                               # 6

if _tiene_pii_o_url(t): return False, ["pii_o_url"]                                       # 7

return True, []

# redactar.py

def redactar(decision, cfg, proveedor):

entrada = minimizar(decision)

try:

crudo = proveedor.generar(SISTEMA, USUARIO.format(json=json.dumps(entrada, ensure_ascii=False)))

except Exception as e:

return None, ["proveedor:" + type(e).__name__]

ok, motivos = verificar(crudo, entrada, cfg)

return (json.loads(crudo)["texto"], []) if ok else (None, motivos)

- **Reglas del verificador:** los artículos un y una no cuentan como número; las palabras numéricas se convierten (uno a veinte, treinta, cien, mil) y se verifican igual que los dígitos; la lista de palabras prohibidas y de frases de contradicción vive en config.
- **PII:** copia los patrones que publique Mathias en docs/patrones_pii.md (no importes de su carpeta).
- **Pruebas:** textos buenos pasan; cifra inventada, cifra faltante, palabra prohibida, contradicción, JSON inválido, texto largo, URL y número de 9 dígitos fallan cada uno con su motivo; propiedad: lo que pasa solo contiene cifras de la entrada.

## 8. Opción C (asistente del semáforo con LLM, RAG y ML): tu parte si se llega al corte

Esta sección es nivel P2. Puntos de corte: A a las 13:00 (si el control 1 salió bien, empieza quien tenga holgura), B a las 16:00 (se integra el flujo si el control 2 salió bien), C a las 17:30 (lo que no pase la evaluación no entra a la demo) y D a las 17:45 (fusión final). El asistente nunca desplaza una prueba P0.

Qué es: una pantalla de chat donde la persona pregunta por su número, sus pagos y escenarios. Usa el motor y el modelo como herramientas de ML, una base de conocimiento propia con búsqueda local (RAG) y, si se activa, un LLM para entender y redactar con cada cifra verificada. Funciona completo sin LLM (modo 1). Se inspira en las lecciones del copiloto del bot_diagnosis: no se copia código, datos ni playbooks.

### Tus archivos: src/motor/simular.py, src/asistente/plantillas.py y verificador.py

# decidir.py: agrega un parametro OPCIONAL (compatible con todo lo escrito hasta ahora)

def decidir(estado, pron, cfg, ingresos_extra=()) -> Decision: ...

def numerador(estado, pron, d, cuantil, cfg, ingresos_extra=(), con_colchon=True):

pagos = sum(p.monto for p in estado.pagos if p.dia <= d)

extra = sum(m for (dia0, m) in ingresos_extra if dia0 <= d)          # ingreso hipotetico CONOCIDO

colchon = estado.colchon if con_colchon else 0.0

return estado.saldo + ingreso_conservador(pron, d, cuantil, cfg["horizontes_dias"]) + extra - pagos - colchon

# simular.py

def simular(estado, pron, escenario, cfg) -> Decision:

estado_sim = estado.model_copy(update={"saldo": estado.saldo - escenario.gasto_hoy})

extras = tuple((i.dia, i.monto) for i in escenario.ingresos_extra)

return decidir(estado_sim, pron, cfg, ingresos_extra=extras)          # una Decision completa

# plantillas.py: una funcion por intencion, deterministas, con cifras del resultado y tres bloques

def plantilla(intencion, resultados) -> tuple[str, list[str]]:            # (texto, acciones)

# "Datos: ...  Que significa: ...  Que puedes hacer: ..."  (acciones simuladas, nunca operaciones)

...

- **Validación:** dia entre 0 y 14, monto entre 0 y 10000, máximo 3 ingresos extra. Fuera de rango se rechaza antes de llamar al motor.
- **Prueba clave:** con el caso de 100 y 300, simular un ingreso extra de 250 el día 2 cambia el número de hoy de 0 a un valor positivo y el semáforo del pago del día 3 mejora; sin ingreso extra el resultado es idéntico a decidir.
- **verificador.py:** copia el de la opción B (src/generativa) y agrega: citas reales (todas están entre los ids recuperados), cita obligatoria si usa pasajes, y cero nombres internos (funciones, campos, rutas, nombres de herramientas). Cada comprobación devuelve su motivo.
- **Pruebas:** textos buenos pasan; cifra inventada, cita inexistente, nombre interno, URL, palabra prohibida y texto largo fallan cada uno con su motivo.

## 9. Tus horas (sábado 14 y domingo 15)

| **Hora (Lima)** | **Qué haces** | **Debe quedar verificable** |
|---|---|---|
| 10:15 a 11:00 | Entorno. Leer el Anexo A. Escribir primero la prueba del caso del orden de pagos (saldo 100, pago de 300 el día 3, ingreso de 400 el día 10), que debe fallar. | Commit con la prueba en rojo |
| 11:00 a 12:00 | motor v0: puntos de control, permitido, número de hoy con redondeo hacia abajo, mensaje de falta. | El caso del orden de pagos pasa a verde |
| 12:00 a 12:30 | Semáforo y desglose. Actualizar las fixtures con Anderson. | PR con decidir completo salvo confianza y propuestas |
| 12:30 a 13:00 | Control 1: el motor responde con la regla 2 a través del servicio. | Etiqueta v0-control1 |
| 13:00 a 16:00 | Confianza, propuesta con verificador P5, plantillas y límites. Pruebas de propiedades con hypothesis. | Control 2: una propuesta se explica y se aprueba o rechaza |
| 16:00 a 18:00 | Estrés del motor (Anexo C), mutaciones con Anderson, plantillas sin cifras inventadas. | Al menos 6 de 8 mutaciones detectadas |
| 18:00 a 19:30 | Casos donde el motor propone poco o nada y por qué; ejemplos para el pitch. | Lista de casos con su desglose |
| Domingo 8:30 a 11:00 | Correcciones. Prueba de evolución: agregar un tipo de propuesta nuevo con una plantilla. | Nuevo tipo en menos de 15 minutos |
| Domingo 11:00 a 13:30 | Ensayos. Explicar la fórmula con el ejemplo de 100 y 300. | Explicación en menos de un minuto |

Los horarios son supuestos hasta que la organización comunique los suyos. Si cambian, Gino reordena este cuadro.

## 10. Tus pruebas

| **Prueba** | **Qué verifica** | **Criterio de éxito** |
|---|---|---|
| Orden de pagos | Saldo 100, pago de 300 el día 3, ingreso de 400 el día 10 | Número 0 y mensaje con faltan S/200 |
| Pago justo cubierto | Saldo igual al pago | Cubierto; verde o ámbar según el cuantil |
| Sin pagos | Solo el punto de control del día 14 | Número calculado con h igual a 14 |
| Pago el día 0 y dos pagos el mismo día | Se agrupan y no divide entre cero | Sin excepción |
| Propiedad: no negativo | Con hypothesis sobre saldo, pagos y pronóstico válidos | Número siempre mayor o igual que 0 |
| Propiedad: monotonía | Más saldo no baja el número; más pagos no lo suben | Cero contraejemplos en 1,000 casos |
| Propiedad: cobertura en P5 | Si hay propuesta, gastando g5 por día ningún pago queda descubierto en P5 | Cero contraejemplos |
| Semáforo | Un caso verde, uno ámbar y uno rojo | Colores esperados |
| Redondeo conservador | Numerador que da 45.9 | Número 45 |
| Cuantiles iguales o saldo negativo | Pronóstico con p5 igual a p80; saldo inicial negativo | Sin excepción; mensaje correcto |
| Plantillas | Toda cifra del texto existe en el desglose | Propiedad verificada |
| Pureza | Las entradas no cambian después de decidir | Iguales |
| Supuestos y evidencia presentes | Toda Decision del conjunto de pruebas | Supuestos, evidencia, límites y confianza no vacíos |
| Cifras de los textos | Hypothesis sobre estados válidos | Toda cifra tiene origen |
| registro_id | consultar y auditar un caso | El id del desglose coincide con el del Registro |

Escribe cada prueba antes que el código cuando puedas (primero rojo, después verde). Cobertura objetivo de tu módulo: al menos 80 % [SUPUESTO].

## 11. Cuándo estás listo (definición de hecho)

- **[ ]** El caso del orden de pagos pasa y está en main desde las 12:30
- **[ ]** Semáforo, confianza, propuesta con verificador P5, desglose y plantillas
- **[ ]** Propiedades con hypothesis en verde sin contraejemplos
- **[ ]** Casos de estrés del motor del Anexo C cubiertos
- **[ ]** Al menos 6 de las 8 mutaciones detectadas y las demás explicadas
- **[ ]** Nuevo tipo de propuesta agregable en menos de 15 minutos
- **[ ]** Decision con supuestos, evidencia y límites en todos los casos
- **[ ]** Verificador de cifras de los textos sin contraejemplos
- **[ ]** registro_id en el desglose

## 12. Riesgos y qué hacer

| **Riesgo** | **Plan B** |
|---|---|
| La propuesta g5 resulta confusa para la persona | Mostrar solo el número de hoy con su explicación y dejar la propuesta como opcional |
| El ingreso conservador subestima demasiado y el número sale siempre 0 | La frontera de Rafael muestra el efecto; se sube el cuantil conservador con evidencia y se anota en DECISIONES.md |
| Cambia el contrato de Pronostico | Solo por pull request aprobado; tus fixtures se actualizan el mismo día |

## 13. Tu parte del pitch

| **Tema** | **Contenido** |
|---|---|
| Qué cuentas | La fórmula por fecha de pago con el ejemplo de 100 y 300, y por qué la fórmula de la v3 fallaba. Eso es una decisión medida y corregida. |
| Cifras que debes tener | Casos de propiedades y contraejemplos encontrados [por medir]; mutaciones detectadas [por medir]; en cuántos casos de la prueba el motor propone, no propone o dice que no alcanza [por medir]. |
| Pregunta que te toca | Qué pasa si el pronóstico se equivoca: cuantil conservador, confianza visible y solo se propone lo que aguanta el escenario P5. |
| En el formato de 5 minutos | En la demo explicas el porqué con los supuestos y los límites. Respondes por qué se confía en el número y por qué no se propone más. |

El formato no está confirmado: la guía impresa dice 10 minutos más 3 de preguntas y el Challenge pack sugiere 5 de pitch, 5 de demo y 5 de preguntas. Prepara primero el corto. La regla de oro: ningún número sin su origen. La autocrítica se dice antes de que pregunten.

## 14. Git y trabajo en paralelo: cómo subir tu parte sin malograr la de los demás

Tu trabajo vive en tus ramas y en tus carpetas. Así puedes programar al mismo tiempo que los otros seis sin pisar nada. Tus ramas sugeridas: feat/sebastian-motor, feat/sebastian-propuesta.

### Qué es tuyo y qué no

- **Tus carpetas:** src/motor, config/motor.yaml, tests/unit/motor, tests/property.
- **Todo lo demás:** no lo edites. Si necesitas un cambio en una carpeta ajena, escribe al dueño o abre un pull request pequeño para él. Tabla completa de dueños en el Anexo E de la v9.
- **Tu revisor:** Mathias. Tú revisas a quien te toque en el cuadro de revisión cruzada.

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

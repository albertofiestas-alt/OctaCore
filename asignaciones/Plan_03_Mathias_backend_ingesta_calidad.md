**Hackathon de Ingeniería BBVA · AI Financial Life · Plan individual**

**Mathias · Backend: ingesta y calidad de datos**

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

Eres la puerta de entrada de los datos. Cualquier archivo que llegue debe validarse, limpiarse y convertirse en movimientos confiables, con un reporte de calidad y los pagos con fecha inferidos. Si llega un archivo nuevo en la prueba de evolución, tu módulo debe procesarlo sin tocar código.

### Qué recibes y de quién

| **Qué** | **De** | **Hora** |
|---|---|---|
| Esquema pydantic, fixtures y estructura | Anderson | 10:45 |
| Muestra de 20 personas | Rafael | 11:00 |
| Aprobación de ingesta.cargar_etiquetas y semanas_historia | Gino y Anderson | 11:00 |

### Qué entregas y a quién

| **Qué** | **A** | **Hora** |
|---|---|---|
| ingesta v0: cargar, ReporteCalidad, duplicados | Anderson, Sebastián | 12:00 |
| pagos inferidos, atípicos, suscripciones, proximos_pagos | Sebastián, Anderson | 13:00 |
| cargar_etiquetas para la evaluación | Rafael | 13:00 |
| Métricas de la ingesta (precisión y recall) | Rafael, pitch | 19:00 |
| Sección de tratamiento de docs/datos.md | Rafael | Domingo 10:00 |

## 3. Tus primeros pasos exactos (empieza por aquí)

Hazlos en este orden. No esperes a nadie: todo lo que necesitas para empezar está en los anexos de este plan.

- **1.** Clona el repositorio y crea la rama feat/mathias-ingesta.
- **2.** Abre src/ingesta/__init__.py: ya tiene las firmas con NotImplementedError. No cambies las firmas.
- **3.** Escribe un CSV de 10 filas en tests/fixtures con un duplicado exacto, un monto atípico y una columna extra (edad).
- **4.** Escribe primero la prueba de duplicados y de columnas sensibles; verás que fallan.
- **5.** Implementa _leer, _descartar_sensibles, _validar_tipos, _defaults y _quitar_duplicados hasta que pasen.
- **6.** Primer pull request (ingesta v0) antes de las 12:00. Luego pagos inferidos, atípicos, suscripciones y PII.

## 4. Qué haces tú con el Challenge pack (tareas nuevas)

Tres tareas nuevas, todas de privacidad por diseño. Entran antes del congelamiento porque son pruebas P0.

| **#** | **Qué haces** | **Cómo y dónde** | **Hora** | **Cómo sabes que está bien** |
|---|---|---|---|---|
| 1 | Descartar columnas sensibles | Antes de cualquier otro paso de cargar, si el archivo trae columnas de la lista variables_sensibles de config (edad, genero, ubicacion, distrito, nombre, dni, telefono) se eliminan y se anotan en ReporteCalidad.columnas_sensibles_descartadas con un aviso. | 13:00 a 14:00 | Archivo con edad, genero y distrito: las tres se descartan y se reportan; los movimientos limpios no las traen |
| 2 | Detectar y enmascarar PII | ingesta.detectar_pii(texto) y enmascarar_pii(df), aplicados a customer_id, comercio y categoria: DNI de 8 dígitos aislados, teléfono de 9 dígitos que empieza en 9, correo electrónico y tarjeta de 13 a 19 dígitos con o sin separadores. Se reemplazan por *** y se cuentan en ReporteCalidad.pii_enmascarado. No toca montos, fechas ni identificadores como P0001. | 14:00 a 15:00 | tests/fixtures/pii_ejemplo.csv con patrones falsos: todos enmascarados; un monto de 12345678 en la columna monto no se toca |
| 3 | Privacidad en errores y registros | ErrorIngesta.detalle solo incluye nombres de columna y números de fila, nunca el valor de una celda. El Registro no guarda el archivo original. | 15:00 a 15:30 | Prueba que fuerza un error con un valor PII y confirma que no aparece en el mensaje ni en el registro |
| 4 | Reporte de calidad del dataset sintético (para la pantalla Evaluación de Alberto) | Un script que aplica ingesta.cargar al dataset completo (data/generado/movimientos.csv; si no existe, la muestra) y escribe eval/resultados/calidad_datos.json con el ReporteCalidad. Lo corre python tareas.py eval. Alberto solo lo lee. | 16:00 | El JSON existe, trae los conteos del reporte y se genera con un comando |

## 5. Tu especificación técnica

### 1. ingesta.cargar(origen) devuelve (movimientos_limpios, ReporteCalidad, pagos_inferidos)

origen es una ruta a un CSV o un DataFrame. La función no modifica su entrada: trabaja sobre copias y devuelve objetos nuevos. Todos los umbrales salen de config/config.yaml (sección ingesta), para que un archivo nuevo se procese sin tocar código.

| **#** | **Paso** | **Regla** |
|---|---|---|
| 1 | Lectura | CSV en UTF-8; tamaño máximo [por fijar, por ejemplo 50 MB]; archivo vacío o ilegible lanza ErrorIngesta con un mensaje para la persona. |
| 2 | Esquema | Obligatorias: customer_id, transaction_id, fecha_hora, monto, moneda, tipo, categoria, comercio. Opcionales: saldo, ingreso_recurrente. Si faltan columnas, el mensaje las nombra. Las columnas extra se ignoran y se avisa. |
| 3 | Etiquetas | es_duplicado, es_atipico, pago_con_fecha y arquetipo se separan de inmediato y NO viajan en los movimientos limpios. Solo cargar_etiquetas las devuelve y solo la evaluación la usa. |
| 4 | Tipos y dominios | fecha_hora a fecha válida (las inválidas se rechazan con motivo); monto finito (NaN e infinito se rechazan); moneda distinta de PEN se rechaza; tipo debe ser ingreso o gasto y coherente con el signo del monto (ingreso positivo, gasto negativo), si no se corrige el signo y se cuenta. |
| 5 | Valores por defecto | categoria vacía o desconocida pasa a otros; comercio vacío pasa a SIN_COMERCIO; ambos conteos van al reporte. Los defaults se documentan en docs/datos.md. |
| 6 | Duplicados | transaction_id repetido: se conserva la primera. Misma persona, fecha_hora, monto, comercio y tipo con otro transaction_id: duplicado exacto, se conserva el primero y se cuenta. |
| 7 | Atípicos | Por persona y tipo, un monto absoluto mayor que la mediana más k veces la desviación absoluta mediana (k en config, inicial 5) se marca y no entra al cálculo de recurrentes. |
| 8 | Pagos con fecha | Se agrupa por persona, comercio y categoría (alquiler, servicios, deuda y suscripción). Es un pago con fecha si hay al menos 3 ocurrencias, el monto está dentro de 10 % de la mediana y el día del mes varía a lo sumo 3 días [valores iniciales en config]. Salen el día del mes y el monto esperado. |
| 9 | Suscripciones duplicadas | Mismo comercio, categoría suscripción y monto dos veces dentro de 30 días: aviso con comercio, monto y fechas. No se elimina; se avisa. |
| 10 | Reporte | Filas de entrada y de salida, duplicados eliminados, faltantes por columna, rechazos con motivo, atípicos, suscripciones duplicadas, pagos inferidos, cobertura temporal y percentiles de monto. |

### 2. Funciones auxiliares

- **proximos_pagos(pagos_inferidos, fecha_corte, ventana=14):** devuelve la lista de PagoConFecha con el día que falta para cada uno. La usa el servicio para armar el estado.
- **semanas_historia(movimientos, customer_id, fecha_corte):** semanas completas con datos hasta la fecha. Es la adición 1 al contrato.
- **cargar_etiquetas(origen):** devuelve las etiquetas por transaction_id. Es la adición 2. Solo para evaluación.
- **ErrorIngesta:** excepción con mensaje_usuario y detalle. La interfaz muestra solo el mensaje.

### 3. Pruebas de la prueba de evolución

La organización puede entregar un archivo nuevo con el mismo contrato, con ingresos variables o movimientos duplicados. Prepara un archivo de 5 personas que no vio nadie, cárgalo desde la línea de comandos con servicio.cargar_archivo(ruta) y comprueba que el reporte sale sin cambiar código (no hay pantalla de carga: los datos son sintéticos y precargados).

## 6. Archivos y funciones que escribes (con código)

Tus archivos, en orden. Con data/muestra de Rafael (11:00) pruebas todo; mientras tanto usa un CSV pequeño que escribas tú con 10 filas en tests/fixtures.

### src/ingesta/__init__.py: cargar

def cargar(origen, cfg):

df = _leer(origen, cfg)                    # ErrorIngesta si esta vacio, ilegible o pesa mas de cfg["ingesta"]["max_mb"]

df, sensibles = _descartar_sensibles(df, cfg)   # columnas de cfg["variables_sensibles"] se eliminan y se anotan

df = _separar_etiquetas(df)                # es_duplicado, es_atipico, pago_con_fecha, arquetipo: fuera de los movimientos

df, rechazos = _validar_tipos(df)          # fechas invalidas, NaN/inf, moneda != PEN: se rechazan con motivo; signo se corrige

df, faltantes = _defaults(df)              # categoria vacia -> "otros"; comercio vacio -> "SIN_COMERCIO"

df, n_pii = enmascarar_pii(df, cfg)        # DNI, telefono, correo, tarjeta -> "***"

df, n_dup = _quitar_duplicados(df)         # transaction_id repetido; misma persona+fecha+monto+comercio+tipo

df, n_atip = _marcar_atipicos(df, cfg)     # columna nueva atipico_detectado (bool)

avisos = _suscripciones_duplicadas(df, cfg)

pagos = _pagos_inferidos(df, cfg)

reporte = ReporteCalidad(filas_entrada=..., filas_salida=len(df), duplicados_eliminados=n_dup,

faltantes=faltantes, atipicos=n_atip, suscripciones_duplicadas=avisos, pagos_inferidos=pagos,

pii_enmascarado=n_pii, columnas_sensibles_descartadas=sensibles, rechazos=rechazos)

return df, reporte, pagos

| **Función** | **Regla exacta** |
|---|---|
| _marcar_atipicos | Por persona y tipo: mediana m y desviación absoluta mediana mad = mediana(\|x - m\|). Atípico si \|monto\| mayor que m + k por mad, con k en config (inicial 5). Si mad es 0, el umbral es 5 por m. |
| _pagos_inferidos | Solo categorías alquiler, servicios, deuda y suscripción. Agrupa por persona, comercio y categoría. Toma la mediana del monto; conserva las ocurrencias cuyo monto esté dentro de tol_monto (0.10) de la mediana. Es pago con fecha si hay al menos min_ocurrencias (3) y el día del mes varía a lo sumo 2 por tol_dia (3). Devuelve dicts con customer_id, comercio, categoria, dia_mes, monto y ocurrencias. |
| _suscripciones_duplicadas | Categoría suscripción, mismo comercio y monto dos veces dentro de ventana_suscripcion_dias (30): un aviso con comercio, monto y las dos fechas. No se elimina. |
| _quitar_duplicados | Primero transaction_id repetido (se conserva el primero); después misma persona, fecha_hora, monto, comercio y tipo con otro id (se conserva el primero). Cuenta ambos. |

### proximos_pagos, semanas_historia y cargar_etiquetas

def proximos_pagos(pagos_inferidos, customer_id, fecha_corte, ventana=14):

salida = []

for p in pagos_inferidos:

if p["customer_id"] != customer_id: continue

fecha = _proxima_fecha(p["dia_mes"], fecha_corte)      # si el dia no existe en el mes (31 en febrero), usa el ultimo dia

dias = (fecha - fecha_corte).days

if 0 <= dias <= ventana:

salida.append(PagoConFecha(pago_id=f'{customer_id}:{p["comercio"]}:{fecha}',

dia=dias, monto=abs(p["monto"]), categoria=p["categoria"]))

return sorted(salida, key=lambda x: x.dia)

def semanas_historia(movimientos, customer_id, fecha_corte):

m = movimientos[movimientos.customer_id == customer_id]

return 0 if m.empty else (fecha_corte - m.fecha_hora.min().date()).days // 7

def cargar_etiquetas(origen):         # relee el archivo y devuelve SOLO las etiquetas, indexadas por transaction_id

### PII y columnas sensibles

PATRONES_PII = {                 # en este orden, para que la tarjeta no se parta en pedazos

"tarjeta":  r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)",

"telefono": r"(?<!\d)9\d{8}(?!\d)",

"dni":      r"(?<!\d)\d{8}(?!\d)",

"correo":   r"[\w.+-]+@[\w-]+\.[\w.-]+",

}

# enmascarar_pii aplica los patrones SOLO a las columnas de texto customer_id, comercio y categoria,

# reemplaza cada coincidencia por "***" y cuenta cuantas. No toca monto, fecha ni ids como "P0001".

# detectar_pii(texto, cfg) devuelve la lista de tipos encontrados (lo reutiliza el verificador de la opcion B).

# Columnas sensibles: se comparan en minusculas contra cfg["variables_sensibles"]; se eliminan y se listan.

config/ingesta.yaml: max_mb 50, mad_k 5, tol_monto 0.10, tol_dia 3, min_ocurrencias 3, ventana_suscripcion_dias 30. Todos los valores se pueden cambiar sin tocar código.

## 7. Opción B (capa generativa): tu parte si se activa

Esta sección solo se ejecuta si se cumplen las cinco condiciones del diseño de la opción B: autorización por escrito de la organización, control 1 aprobado, antes de las 17:00, clave de OpenAI funcionando en las dos laptops y pruebas P0 en verde. Si falta una, no hagas nada de esto. T0 es la hora de la autorización; con T0 después de las 14:30 no se activa.

Resumen del diseño: el modelo solo reescribe el porqué que el motor ya calculó. Ve una entrada mínima sin identificadores. Un verificador sin IA exige que cada cifra del texto exista en esa entrada; si algo falla, se muestra la plantilla. La clave de OpenAI vive solo en .env.

### Tu tarea (T0 a T0+45)

- **docs/patrones_pii.md:** publica los patrones de PII de tu ingesta (tarjeta, teléfono, DNI y correo) como texto, para que Sebastián los copie al verificador. Nadie importa de tu carpeta.
- **Revisión de la lista blanca:** lee src/generativa/minimizar.py de Sebastián y confirma que ninguna clave ni valor pueda contener un identificador o texto libre. Si dudas, díselo antes de las 17:00.

## 8. Opción C (asistente del semáforo con LLM, RAG y ML): tu parte si se llega al corte

Esta sección es nivel P2. Puntos de corte: A a las 13:00 (si el control 1 salió bien, empieza quien tenga holgura), B a las 16:00 (se integra el flujo si el control 2 salió bien), C a las 17:30 (lo que no pase la evaluación no entra a la demo) y D a las 17:45 (fusión final). El asistente nunca desplaza una prueba P0.

Qué es: una pantalla de chat donde la persona pregunta por su número, sus pagos y escenarios. Usa el motor y el modelo como herramientas de ML, una base de conocimiento propia con búsqueda local (RAG) y, si se activa, un LLM para entender y redactar con cada cifra verificada. Funciona completo sin LLM (modo 1). Se inspira en las lecciones del copiloto del bot_diagnosis: no se copia código, datos ni playbooks.

### Tu archivo: src/asistente/guardia.py

INYECCION = ["ignora", "olvida", "instrucciones", "system prompt", "prompt", "eres ahora", "actua como",

"api key", "clave", "token", "muestra tu", "revela"]        # red de seguridad; la defensa real es la estructura

def revisar(texto, cfg) -> tuple[bool, str]:

if not texto or not texto.strip():                       return False, "vacio"

if len(texto) > cfg["asistente"]["max_caracteres"]:      return False, "largo"        # 200

if any(ord(c) < 32 for c in texto if c not in "\n\t"):    return False, "control"

if re.search(r"https?://|www\.", texto, re.I):           return False, "url"

if detectar_pii(texto, cfg):                             return False, "pii"          # tus mismos patrones

if any(m in _sin_tildes(texto).lower() for m in INYECCION):

return False, "inyeccion"

return True, ""

def enmascarar_para_registro(texto, cfg) -> str:              # ***  en lugar de PII antes de guardar la pregunta

- **Qué se hace con cada rechazo:** el flujo responde con un mensaje fijo y amable según el motivo (por ejemplo "tu pregunta es muy larga, resúmela en una frase") y registra solo el motivo y la pregunta enmascarada.
- **Pruebas:** una pregunta normal pasa; texto vacío, 201 caracteres, un enlace, un DNI, un teléfono y cada frase de INYECCION fallan con su motivo; el registro nunca guarda la pregunta con PII.

## 9. Tus horas (sábado 14 y domingo 15)

| **Hora (Lima)** | **Qué haces** | **Debe quedar verificable** |
|---|---|---|
| 10:15 a 11:00 | Entorno. Esqueleto de src/ingesta con las firmas y una prueba que pasa. Leer el contrato de datos. | Rama feat/mathias-ingesta; make test verde |
| 11:00 a 12:00 | ingesta v0: lectura, esquema, tipos, defaults, duplicados exactos, ReporteCalidad, proximos_pagos. | cargar(data/muestra) devuelve la tupla; pruebas de duplicados |
| 12:00 | Entregar v0 a Anderson y Sebastián por pull request. | PR fusionado |
| 12:00 a 13:00 | Pagos con fecha inferidos, atípicos, suscripciones duplicadas, cargar_etiquetas, semanas_historia. | Precisión y recall de pagos contra la etiqueta [por medir] |
| 13:00 a 16:00 | Fuzz y casos difíciles. Archivo nuevo sin tocar código. Mensajes de error claros. | Más de 20 pruebas; cero excepciones crudas |
| 16:00 a 18:00 | Estrés de archivos (Anexo C de la v5). Pruebas de propiedades. Texto de tratamiento para docs/datos.md. | Pruebas P0 y P1 en verde |
| 18:00 a 19:30 | Métricas de ingesta: duplicados eliminados contra inyectados; pagos inferidos y atípicos con precisión y recall. | eval/resultados/ingesta.csv |
| Domingo 8:30 a 11:00 | Correcciones. docs/datos.md con el tratamiento. Dejar listo el reporte de calidad del dataset sintético (eval/resultados/calidad_datos.json) que muestra Alberto en Evaluación. | El JSON se genera con un comando |
| Domingo 11:00 a 13:30 | Ensayos. | Demo del archivo corre tres veces |

Los horarios son supuestos hasta que la organización comunique los suyos. Si cambian, Gino reordena este cuadro.

## 10. Tus pruebas

| **Prueba** | **Qué verifica** | **Criterio de éxito** |
|---|---|---|
| Archivo vacío | cargar de un CSV vacío | ErrorIngesta con mensaje claro |
| Columnas faltantes | CSV sin la columna monto | El mensaje nombra monto |
| Duplicados | Archivo con N duplicados inyectados | duplicados_eliminados igual a N |
| Suscripción repetida | Dos cobros iguales del mismo comercio en 30 días | Aviso con comercio, monto y fechas |
| Atípico | Un monto 8 veces la mediana | Marcado y fuera de los recurrentes |
| Pagos con fecha | Cuatro meses de alquiler con ruido de un día | Un pago inferido con el día y monto esperados |
| Tipos inválidos | Fechas imposibles, NaN, infinito, moneda USD | Filas rechazadas con motivo; cero excepciones |
| Signo y tipo | Gasto con monto positivo | Se corrige y se cuenta |
| Unicode y longitud | Comercio con tildes y un texto de 5,000 caracteres | Sin excepción; se recorta o se acepta según config |
| Idempotencia | cargar aplicado dos veces | Mismo resultado |
| Inmutabilidad | La entrada después de cargar | No cambió |
| Anti fuga | Columnas de movimientos limpios | Ninguna etiqueta presente |
| Fuzz con hypothesis | Filas con nulos, textos largos y números extremos | Cero excepciones no controladas |
| Columnas sensibles | Archivo con edad, genero y distrito | Descartadas y reportadas |
| PII por patrón | DNI, teléfono, correo y tarjeta en comercio y customer_id | Todos enmascarados y contados |
| Falsos positivos | Monto 12345678 y customer_id P0001 | No se modifican |
| Errores sin PII | Error con un valor PII en una celda | El mensaje no contiene el valor |

Escribe cada prueba antes que el código cuando puedas (primero rojo, después verde). Cobertura objetivo de tu módulo: al menos 80 % [SUPUESTO].

## 11. Cuándo estás listo (definición de hecho)

- **[ ]** cargar devuelve movimientos limpios, ReporteCalidad y pagos inferidos para la muestra y para los 400
- **[ ]** Cero excepciones crudas hacia la interfaz; solo ErrorIngesta con mensaje para la persona
- **[ ]** Etiquetas separadas y no presentes en los movimientos limpios
- **[ ]** Un archivo nuevo con el mismo contrato se procesa sin cambios de código
- **[ ]** Precisión y recall de duplicados, atípicos y pagos medidos
- **[ ]** Sección de tratamiento en docs/datos.md
- **[ ]** Columnas sensibles descartadas con aviso
- **[ ]** PII enmascarada y contada en el reporte
- **[ ]** Errores y registros sin valores de celdas
- **[ ]** Pruebas de privacidad P0 en verde antes de las 18:00
- **[ ]** eval/resultados/calidad_datos.json se genera con un comando y Alberto lo muestra en Evaluación

## 12. Riesgos y qué hacer

| **Riesgo** | **Plan B** |
|---|---|
| La inferencia de pagos falla con datos ruidosos | Usar las categorías alquiler, servicios y deuda con el último monto y el día más frecuente |
| Muchas filas rechazadas con datos reales de la organización | Informar el motivo y no detenerse; el reporte dice cuántas y por qué |
| El archivo de la organización trae otro formato de fecha | Parsers tolerantes y mensaje claro; el formato aceptado va al README |

## 13. Tu parte del pitch

| **Tema** | **Contenido** |
|---|---|
| Qué cuentas | El reporte de calidad del dataset sintético en la pantalla Evaluación: duplicados eliminados, atípicos, suscripciones duplicadas y PII enmascarada. |
| Cifras que debes tener | Duplicados eliminados contra inyectados [por medir]; precisión y recall de pagos inferidos [por medir]; filas rechazadas con motivo [por medir]. |
| Pregunta que te toca | Qué pasa si el archivo viene mal: mensaje claro, sin pantalla en blanco y sin tocar código. |
| En el formato de 5 minutos | En la pantalla Evaluación: el reporte de calidad del dataset sintético (duplicados eliminados y PII enmascarada). Respondes sobre privacidad y calidad de datos. |

El formato no está confirmado: la guía impresa dice 10 minutos más 3 de preguntas y el Challenge pack sugiere 5 de pitch, 5 de demo y 5 de preguntas. Prepara primero el corto. La regla de oro: ningún número sin su origen. La autocrítica se dice antes de que pregunten.

## 14. Git y trabajo en paralelo: cómo subir tu parte sin malograr la de los demás

Tu trabajo vive en tus ramas y en tus carpetas. Así puedes programar al mismo tiempo que los otros seis sin pisar nada. Tus ramas sugeridas: feat/mathias-ingesta, feat/mathias-pii.

### Qué es tuyo y qué no

- **Tus carpetas:** src/ingesta, config/ingesta.yaml, tests/unit/ingesta.
- **Todo lo demás:** no lo edites. Si necesitas un cambio en una carpeta ajena, escribe al dueño o abre un pull request pequeño para él. Tabla completa de dueños en el Anexo E de la v9.
- **Tu revisor:** Sebastián. Tú revisas a quien te toque en el cuadro de revisión cruzada.

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

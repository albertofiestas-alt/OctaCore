**Hackathon de Ingeniería BBVA · AI Financial Life · Plan individual**

**Rafael · Data science: datos, reglas y evaluación**

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

Eres dueño de la verdad del experimento: el generador de datos, las dos reglas de comparación y el arnés que mide todo. Si tus datos o tu medición están mal, nada de lo demás vale. Entregas la muestra de 20 personas antes de las 11:00 para que nadie espere.

### Qué recibes y de quién

| **Qué** | **De** | **Hora** |
|---|---|---|
| Esquemas, fixtures y estructura del repositorio | Anderson | 10:45 |
| ingesta.cargar_etiquetas y pagos inferidos | Mathias | 12:00 |
| modelo.entrenar y Modelo.predecir | Gino | 15:30 |
| servicio y motor para simular la decisión | Anderson y Sebastián | 13:00 |

### Qué entregas y a quién

| **Qué** | **A** | **Hora** |
|---|---|---|
| data/muestra con 20 personas | Todos | 11:00 |
| Datos completos de 400 personas y partición | Gino, Mathias | 12:30 |
| regla1 y regla2 con la forma Pronostico | Anderson, Gino | 12:30 |
| Arnés de simulación y frontera con las reglas | Gino, Alberto | 16:00 |
| Tabla definitiva, pares de semillas y ejemplos de error | Todos, pitch | 19:00 |
| docs/datos.md y docs/evaluacion.md | Jurado | Domingo 10:00 |

## 3. Tus primeros pasos exactos (empieza por aquí)

Hazlos en este orden. No esperes a nadie: todo lo que necesitas para empezar está en los anexos de este plan.

- **1.** Clona el repositorio cuando Anderson lo publique y crea la rama feat/rafael-generador.
- **2.** Escribe un generador mínimo con semilla que produzca el CSV con las columnas del contrato para 20 personas (4 por arquetipo), aunque los parámetros sean toscos.
- **3.** Guarda data/muestra/movimientos.csv y meta.json. Sube la rama y abre el pull request antes de las 11:00: es lo que desbloquea a los demás.
- **4.** Después mejora el generador por partes (gastos fijos, estacionalidad, escenarios inyectados) sin cambiar el formato.
- **5.** Empieza src/reglas con regla1 y regla2 y sus pruebas con valores calculados a mano.

## 4. Qué haces tú con el Challenge pack (tareas nuevas)

Cuatro tareas nuevas. Responsible AI y Datos y evidencia pesan 25 puntos entre las dos y se apoyan en lo que mides tú.

| **#** | **Qué haces** | **Cómo y dónde** | **Hora** | **Cómo sabes que está bien** |
|---|---|---|---|---|
| 1 | Diccionario de datos con justificación de realismo | docs/diccionario_datos.md: tabla con cada campo (nombre, tipo, rango, cómo lo genera el generador, supuesto). Sección de realismo: ingreso mensual sintético contra el promedio del INEI y proporción con déficit contra el 85 % de la SBS, usando solo las cifras que Alberto verificó en su fuente. | Borrador sábado 19:00; final domingo 9:30 | Todos los campos del CSV están descritos; el realismo cita cifra y fuente |
| 2 | Documentar el ground truth | Sección en docs/datos.md: etiquetas es_duplicado, es_atipico, pago_con_fecha y arquetipo; cómo se generan; cómo se usan para medir precisión y recall; y que nunca entran al modelo ni al motor. | Sábado 18:30 | Una persona ajena al módulo entiende qué es verdad y qué se mide |
| 3 | Análisis de sesgos por grupo | eval/sesgos.py: grupos por arquetipo, tercil de ingreso mensual, tercil de volatilidad (coeficiente de variación del ingreso semanal) y cambio de patrón. Para cada método y grupo: porcentaje de pagos descubiertos, gasto permitido promedio y calibración del P20. Salida en eval/resultados/sesgos.csv con la brecha (diferencia máxima entre grupos) y una columna de alerta contra el umbral pre-registrado. | 17:30 a 18:30 | Caso de juguete con dos grupos y una brecha conocida da el resultado calculado a mano |
| 4 | Sección de sesgos de docs/responsible_ai.md (con Gino) | Qué se midió, qué grupo queda peor, de cuánto es la brecha y qué decide el equipo: se dice y se muestra, no se esconde. | Domingo 9:00 a 10:00 | Cada afirmación del documento cita una fila de sesgos.csv |

## 5. Tu especificación técnica

### 1. Generador sintético (src/datos/generador.py)

- **Firma:** generar(n_personas=400, meses=24, semilla, perturbado=False, parametros=None) devuelve el DataFrame de movimientos con el contrato de datos más las columnas de etiqueta, y un diccionario de metadatos (semilla, versión del generador, parámetros, hash). Escribe data/generado/movimientos.csv y meta.json.
- **Calendario:** de enero del año 1 a diciembre del año 2. Hay un diciembre en entrenamiento (mes 12) y otro en prueba (mes 24).
- **Determinismo:** un generador numpy con la semilla; ninguna fuente de azar fuera de él; mismo resultado en cualquier laptop.
- **Privacidad:** identificadores como P0001 y T000001; comercios inventados; ningún nombre, DNI ni teléfono. Una prueba busca patrones de 8 y 9 dígitos y falla si los encuentra.

Parámetros iniciales de los arquetipos. Todos son [SUPUESTO]: se ajustan hasta que la plausibilidad (más abajo) salga razonable.

| **Arquetipo** | **Ingresos** | **Particularidades** |
|---|---|---|
| Conductor por aplicativo | Un depósito diario de S/60 a S/160, seis días por semana | Caída de 30 % en feriados; combustible como gasto discrecional |
| Vendedora | Entre 10 y 20 depósitos pequeños por día de S/5 a S/30 | Fin de semana con 40 % más; marzo con 30 % más por la campaña escolar |
| Técnico freelance | De 2 a 4 pagos al mes de S/300 a S/1,200 | Tiempos entre pagos exponenciales; meses sin ingreso |
| Comisionista | Base de S/200 por semana más comisión de S/0 a S/1,500 | Comisión con 30 % de probabilidad al cierre de mes |
| Asalariado quincenal (control) | S/1,500 con 3 % de ruido los días 15 y último del mes | Grupo de control para verificar que el modelo no funciona solo aquí |

Gastos fijos y discrecionales (todos [SUPUESTO]): alquiler el día 1 a 5 de S/350 a S/900; luz entre el 8 y 12 de S/60 a S/150 con 15 % de variación; agua de S/30 a S/60; internet de S/70 a S/120; celular de S/30 a S/60; cuota de deuda en una fecha fija de S/100 a S/400 para el 40 % de las personas; suscripción de S/15 a S/40 para el 30 %. Los gastos discrecionales (alimentación, transporte, otros) siguen el ingreso reciente con ruido.

| **Escenario inyectado** | **Tasa inicial [SUPUESTO]** | **Etiqueta que se escribe** |
|---|---|---|
| Movimientos duplicados exactos | 1 % a 2 % de las filas | es_duplicado |
| Suscripción cobrada dos veces | 3 % de las personas | es_duplicado y categoría suscripción |
| Transacciones atípicas | 0.5 % de las filas, entre 5 y 10 veces el monto habitual | es_atipico |
| Datos incompletos | 2 % de categoría o comercio vacíos; 3 % de días sin registro | Ninguna (son huecos) |
| Cambio de patrón | 10 % de las personas cambian de arquetipo a mitad de año | arquetipo inicial y final |
| Pagos con fecha | Alquiler, servicios, deuda y suscripción | pago_con_fecha |

- **Partición:** función particion(df) que devuelve las personas de prueba (20 %, elegidas con la semilla) y las ventanas de meses: entrenamiento 1 a 16, validación 17 a 20, prueba 21 a 24. Las personas de prueba nunca están en el entrenamiento.
- **Generador perturbado:** misma función con perturbado=True: otra semilla, volatilidad por 1.5, nivel de ingreso 20 % menor y otra mezcla de arquetipos. Solo para la tabla de robustez.
- **Muestra:** data/muestra con 20 personas (cuatro por arquetipo) y los 24 meses, lista antes de las 11:00 aunque sea una primera versión. Después se mejora el generador sin cambiar el formato.

### 2. Reglas de comparación (src/reglas/reglas.py)

- **regla1 (ingenua):** promedio mensual de ingresos dividido entre 30 y multiplicado por h. Para dar la forma Pronostico usa factores por cuantil: P5 por 0.5, P20 por 0.75, P50 por 1.0 y P80 por 1.0 [propuesto].
- **regla2 (robusta):** para cada h en 3, 7 y 14, se toman las sumas de ingresos en ventanas móviles de h días dentro de las últimas 8 semanas y se calculan los percentiles empíricos 5, 20, 50 y 80. Con menos de h más 7 días de historia, vuelve a regla1 y lo anota.
- **Misma firma que el modelo:** regla(historia, fecha) devuelve un Pronostico ordenado y no negativo.

### 3. Arnés de evaluación (eval/)

- **Simulación de la decisión (eval/simular.py):** para cada persona de prueba y cada día de los meses 21 a 24: se arma el estado con lo que se sabía ese día (sin mirar el futuro), el método da el número de hoy, la persona gasta exactamente ese número [SUPUESTO] y se avanza el saldo con los ingresos y pagos reales. Los gastos discrecionales observados se reemplazan por el gasto permitido. Un pago queda descubierto si el saldo es menor que cero el día del pago.
- **Pagos con fecha en la simulación:** los que infiere la ingesta con el historial anterior a la prueba, no la etiqueta. Se anota el compromiso: se re-infieren cada mes.
- **Métricas (eval/metricas.py):** MAE de la mediana, pérdida pinball por cuantil, calibración del P20, porcentaje de pagos descubiertos y gasto permitido promedio por día. Nada de MAPE. Pruebas con valores calculados a mano y con semanas de ingreso cero.
- **Frontera (eval/frontera.py):** para cada método y cada cuantil conservador (P5, P20, P50, P80) un par (descubiertos, gasto permitido); la regla ingenua se dibuja con los factores 0.5, 0.75 y 1.0; más las referencias de gasto cero y gasto fijo promedio. Salida en eval/resultados/frontera.csv.
- **Pares de semillas (eval/pares.py):** al menos 20 semillas del generador (con menos personas para que sea rápido), la diferencia modelo menos regla robusta en cada semilla y un intervalo bootstrap de 95 % con 2,000 remuestreos. Gino aporta el entrenamiento; tú el bucle y la estadística.
- **Perturbado:** toda tabla se repite en el generador perturbado y se muestra al lado.
- **Ejemplos de error:** al menos tres casos de la prueba donde el método falla: qué predijo, qué pasó, por qué y qué límite revela. Se guardan con su persona, su fecha y el desglose.
- **Plausibilidad:** ingreso mensual sintético contra el promedio del INEI y proporción de personas con al menos un mes en déficit contra el 85 % de la encuesta de la SBS. Si no se parecen, se ajustan los parámetros o se dice.
- **Tabla final:** make eval produce eval/resultados con la tabla, la frontera, la robustez y su sha256. Con la misma semilla, el mismo hash.

## 6. Archivos y funciones que escribes (con código)

Tus archivos, en orden. Lo primero que se necesita es la muestra de 20 personas antes de las 11:00, aunque sea una primera versión; después mejoras el generador sin cambiar el formato.

### src/datos/generador.py

ARQUETIPOS = ["conductor", "vendedora", "tecnico", "comisionista", "asalariado"]

INICIO = date(2025, 1, 1)           # ano 1; diciembre = mes 12 y mes 24

def generar(n_personas=400, meses=24, semilla=12345, perturbado=False, parametros=None):

rng = np.random.default_rng(semilla)               # unica fuente de azar

p = _parametros(perturbado, parametros)            # volatilidad, factor_ingreso, mezcla de arquetipos

filas = []

for i in range(n_personas):

arq = rng.choice(ARQUETIPOS, p=p["mezcla"])

persona = _crear_persona(i, arq, rng, p)       # id P0001.., alquiler y su dia, deuda?, suscripcion?

filas += _simular_persona(persona, INICIO, meses, rng, p)

df = pd.DataFrame(filas)

df = _inyectar_escenarios(df, rng, p)   # duplicados, suscripcion doble, atipicos, faltantes, cambio de patron

df = _calcular_saldo(df)

meta = {"semilla": semilla, "version_generador": "1.0", "perturbado": perturbado,

"n_personas": n_personas, "hash": _hash(df)}

return df, meta

# Columnas del CSV: customer_id, transaction_id, fecha_hora, monto, moneda, tipo, categoria, comercio,

# saldo, ingreso_recurrente, es_duplicado, es_atipico, pago_con_fecha, arquetipo

| **Arquetipo** | **Cómo se simula el ingreso (todo [SUPUESTO])** | **Gastos propios** |
|---|---|---|
| conductor | Un depósito diario de S/60 a S/160 seis días por semana; 30 % menos en feriados | Combustible discrecional |
| vendedora | 10 a 20 depósitos por día de S/5 a S/30; fin de semana 40 % más; marzo 30 % más | Mercadería discrecional |
| tecnico | 2 a 4 pagos al mes de S/300 a S/1,200; tiempo entre pagos exponencial | Herramientas discrecionales |
| comisionista | S/200 por semana más una comisión de S/0 a S/1,500 con 30 % de probabilidad al cierre de mes | Transporte discrecional |
| asalariado | S/1,500 con 3 % de ruido los días 15 y último del mes | Control: pocos gastos discrecionales |

Gastos fijos de todos: alquiler el día 1 a 5 (S/350 a S/900), luz entre el 8 y 12 (S/60 a S/150 con 15 % de variación), agua, internet y celular; deuda para el 40 % y suscripción para el 30 %. Con volatilidad por 1.5, ingreso por 0.8 y otra mezcla cuando perturbado es verdadero.

### src/datos/particion.py y data/muestra

def particion(df, semilla=12345):

personas = sorted(df.customer_id.unique())

rng = np.random.default_rng(semilla); rng.shuffle(personas)

n_test = int(0.2 * len(personas))

return {"test_personas": personas[:n_test], "train_personas": personas[n_test:],

"meses_train": (1, 16), "meses_val": (17, 20), "meses_test": (21, 24)}

def mes_indice(fecha):                 # mes 1 = enero del ano 1

return (fecha.year - 2025) * 12 + fecha.month

# data/muestra: generar(n_personas=20, ...) con 4 personas por arquetipo; guardar movimientos.csv y meta.json

### src/reglas/reglas.py

def _ingresos_diarios(historia, fecha):

# Serie diaria de ingresos hasta fecha-1, con ceros donde no hubo ingreso. Usa tipo == "ingreso".

...

def regla1(historia, fecha, cfg) -> Pronostico:

serie = _ingresos_diarios(historia, fecha)

mensual = serie[-90:].sum() / 3                     # promedio mensual de los ultimos 90 dias

base = mensual / 30

return Pronostico(por_horizonte={

h: Cuantiles(p5=base*h*0.5, p20=base*h*0.75, p50=base*h, p80=base*h) for h in (3, 7, 14)})

def regla2(historia, fecha, cfg) -> Pronostico:

serie = _ingresos_diarios(historia, fecha)

if len(serie) < 63:                                 # menos de 56 dias mas 7 de margen

return regla1(historia, fecha, cfg)

ultimas = serie[-56:]

por_h = {}

for h in (3, 7, 14):

sumas = ultimas.rolling(h).sum().dropna()       # ingreso acumulado en ventanas de h dias

q = np.percentile(sumas, [5, 20, 50, 80])

q = np.sort(q)                                  # garantiza el orden

por_h[h] = Cuantiles(p5=q[0], p20=q[1], p50=q[2], p80=q[3])

return Pronostico(por_horizonte=por_h)

### eval/: métricas, simulación, frontera, pares y sesgos

# eval/metricas.py

def pinball(y, q, tau):    return np.mean(np.maximum(tau * (y - q), (tau - 1) * (y - q)))

def mae(y, pred):          return np.mean(np.abs(y - pred))

def calibracion(y, q20):   return np.mean(y >= q20)                 # debe rondar 0.80

# eval/simular.py

def simular_persona(historia_completa, etiquetas, cfg, metodo, cuantil, modelo=None):

# Para cada dia t de los meses de prueba:

#   1) hist = movimientos hasta t (SIN mirar el futuro); estado con saldo simulado y pagos proximos

#   2) pron = metodo(hist, t); decision = motor.decidir(estado, pron, cfg_con_cuantil)

#   3) la persona gasta decision.numero_hoy (gasto discrecional observado se reemplaza por ese gasto)

#   4) saldo += ingresos reales de t - pagos reales de t - gasto

#   5) si hay pago real en t y saldo < 0 despues de pagar -> pago descubierto

# devuelve {"pagos_descubiertos": n, "pagos_totales": m, "gasto_permitido_dia": promedio}

# eval/frontera.py

def frontera(df, cfg, metodos=("regla1", "regla2", "modelo")):

# para cada metodo y cuantil en (0.05, 0.20, 0.50, 0.80): (pct_descubiertos, gasto_permitido)

# + referencias: gasto 0 y gasto fijo promedio; guarda eval/resultados/frontera.csv

# eval/pares.py

def pares(n_semillas=20):

# por semilla: diferencia modelo - regla2 en (descubiertos, gasto); bootstrap 2000 remuestreos -> IC 95 %

# eval/sesgos.py

def sesgos(df, resultados_por_persona, cfg):

# grupos: arquetipo, tercil de ingreso mensual, tercil de volatilidad (coef. de variacion del ingreso semanal),

# cambio de patron. Por grupo y metodo: pct descubiertos, gasto permitido, calibracion del P20.

# brecha = maximo - minimo entre grupos; alerta si supera config/preregistro.yaml:umbral_alerta_sesgo

Todo lo que escribas en eval/resultados/ debe poder regenerarse con python tareas.py eval y producir el mismo hash con la misma semilla. Las pruebas con valores calculados a mano están en la tabla de pruebas de este plan.

## 7. Opción B (capa generativa): tu parte si se activa

Esta sección solo se ejecuta si se cumplen las cinco condiciones del diseño de la opción B: autorización por escrito de la organización, control 1 aprobado, antes de las 17:00, clave de OpenAI funcionando en las dos laptops y pruebas P0 en verde. Si falta una, no hagas nada de esto. T0 es la hora de la autorización; con T0 después de las 14:30 no se activa.

Resumen del diseño: el modelo solo reescribe el porqué que el motor ya calculó. Ve una entrada mínima sin identificadores. Un verificador sin IA exige que cada cifra del texto exista en esa entrada; si algo falla, se muestra la plantilla. La clave de OpenAI vive solo en .env.

### Tu tarea (T0+30)

- **eval/generativa_conjunto.json:** entrega 20 decisiones tomadas de la evaluación: variadas en semáforo (verde, ámbar, rojo), con y sin propuesta, confianza alta, media y baja, y casos con número de hoy igual a 0. Formato: la Decision completa en JSON, la misma que usan las fixtures.
- **Qué no incluyas:** ningún texto libre ni identificadores reales; solo datos del generador sintético.

## 8. Opción C (asistente del semáforo con LLM, RAG y ML): tu parte si se llega al corte

Esta sección es nivel P2. Puntos de corte: A a las 13:00 (si el control 1 salió bien, empieza quien tenga holgura), B a las 16:00 (se integra el flujo si el control 2 salió bien), C a las 17:30 (lo que no pase la evaluación no entra a la demo) y D a las 17:45 (fusión final). El asistente nunca desplaza una prueba P0.

Qué es: una pantalla de chat donde la persona pregunta por su número, sus pagos y escenarios. Usa el motor y el modelo como herramientas de ML, una base de conocimiento propia con búsqueda local (RAG) y, si se activa, un LLM para entender y redactar con cada cifra verificada. Funciona completo sin LLM (modo 1). Se inspira en las lecciones del copiloto del bot_diagnosis: no se copia código, datos ni playbooks.

### Tus archivos: kb/, src/asistente/rag.py y data/chat/

- **kb/ (12 documentos cortos, escritos por el equipo):** glosario, calculo_numero_hoy, semaforo, confianza, supuestos_y_limites, propuestas, ingresos_irregulares, simulacion_que_pasa_si, datos_sinteticos_y_privacidad, que_no_hacemos, como_leer_la_pantalla y preguntas_frecuentes. Cada uno de 1 a 3 párrafos.
- **Insumos que ya existen:** convierte Formula_Gasto_Diario_Permitido.docx y Determinacion_Limite_Final.docx (escritos por el equipo) en kb/calculo_numero_hoy.md y kb/glosario.md, con las aclaraciones fijadas en la sección 5 de la v9: nombre numero_hoy, ingreso conservador por horizontes, divisor max(d, 1), redondeo hacia abajo y el pago que limita.

# src/asistente/rag.py   (TF-IDF de scikit-learn, sin dependencias nuevas ni vectores externos)

class BaseConocimiento:

def __init__(self, carpeta="kb"):

self.pasajes = _partir(carpeta)       # [{"id": "kb:glosario#2", "texto": "..."}]  (un pasaje por parrafo)

self.vec = TfidfVectorizer(strip_accents="unicode", lowercase=True, ngram_range=(1, 2))

self.matriz = self.vec.fit_transform([p["texto"] for p in self.pasajes])

def buscar(self, consulta, k=3, minimo=0.15):                          # minimo [por fijar]

s = cosine_similarity(self.vec.transform([consulta]), self.matriz)[0]

orden = s.argsort()[::-1][:k]

return [self.pasajes[i] | {"score": float(s[i])} for i in orden if s[i] >= minimo]

def kb_dinamica(decision) -> list[dict]:    # el desglose de la decision actual como pasajes citables: decision#1, decision#2...

- **Preguntas de entrenamiento:** data/chat/preguntas.csv con 120 a 150 preguntas (columnas texto, intencion), al menos 20 por intención, escritas con Gino. Incluye variaciones de monto y día, faltas de ortografía y mayúsculas. Sin datos reales de nadie.
- **Pruebas:** para 20 pares pregunta y documento esperado, el documento correcto está entre los 3 primeros; una consulta sin relación devuelve lista vacía; todos los ids de pasaje son únicos.

## 9. Tus horas (sábado 14 y domingo 15)

| **Hora (Lima)** | **Qué haces** | **Debe quedar verificable** |
|---|---|---|
| 10:15 a 11:00 | Entorno. Generador mínimo con semilla. Publicar data/muestra con 20 personas. | data/muestra/movimientos.csv y meta.json en main antes de las 11:00 |
| 11:00 a 12:00 | Generador v1: cinco arquetipos, gastos fijos, estacionalidad y escenarios inyectados. Etiquetas. regla1 y regla2. | make datos genera 400 personas; pruebas de invariantes en verde |
| 12:00 a 12:30 | Datos completos, particion(), generador perturbado. regla2 con la forma Pronostico. | data/generado listo; regla2 pasa sus pruebas |
| 12:30 a 13:00 | Control 1. Con Alberto, abrir las fuentes de las cifras de prensa. | docs/fuentes_verificadas.md con 2 o 3 cifras abiertas |
| 13:00 a 16:00 | Arnés de simulación con las reglas: descubiertos, gasto permitido, frontera, perturbado. Métricas con pruebas. | eval/resultados/frontera.csv reproducible con regla1 y regla2 |
| 16:00 a 18:00 | Integrar el modelo de Gino. Pares de semillas. Ablaciones con Gino. Prueba anti fuga. | Tabla de pares con intervalo; la prueba anti fuga pasa |
| 18:00 a 19:30 | Tabla definitiva en prueba y perturbado. Tres ejemplos de error. Plausibilidad. Borrador de docs/evaluacion.md. | make eval y su hash anotado |
| Domingo 8:30 a 11:00 | Repetir con la misma semilla. docs/datos.md y docs/evaluacion.md finales. Apoyar el pitch. | Hash idéntico al del sábado |
| Domingo 11:00 a 13:30 | Ensayos. Respuestas sobre datos y evaluación. | Preguntas difíciles respondidas con cifra y fuente |

Los horarios son supuestos hasta que la organización comunique los suyos. Si cambian, Gino reordena este cuadro.

## 10. Tus pruebas

| **Prueba** | **Qué verifica** | **Criterio de éxito** |
|---|---|---|
| Invariantes del generador | Cobertura de 24 meses; diciembre en el mes 12 y el 24; ids únicos; sumas de etiquetas coinciden con lo inyectado | Todas en verde |
| Sin datos personales | Patrones de 8 y 9 dígitos y de correos en todo el CSV | Cero coincidencias |
| Determinismo del generador | Misma semilla produce el mismo hash; otra semilla, otro | Hash coincide y difiere |
| Partición | Personas de prueba y de entrenamiento no se solapan; ventanas sin mezcla | Intersección vacía |
| Anti fuga | Ninguna columna de etiqueta aparece en las variables del modelo ni en el estado del motor | La prueba falla si aparece una |
| Reglas | Salida ordenada, no negativa y con la forma Pronostico; fallback a regla1 | Casos de historia corta y de ingreso cero |
| Métricas | MAE y pinball contra valores calculados a mano; semana de ingreso cero | Coinciden y no se rompen |
| Simulación | Caso de juguete de tres días con resultado calculado a mano | Descubiertos y gasto coinciden |
| Pares de semillas | Intervalo bootstrap con una diferencia conocida | El intervalo contiene la diferencia |
| Sesgos con caso de juguete | Dos grupos con brecha conocida | La brecha y la alerta coinciden con lo calculado a mano |
| Sin variables sensibles | El generador no escribe edad, género ni ubicación | Ninguna de esas columnas en el CSV |
| Diccionario completo | Cada columna del CSV está en el diccionario | Cero columnas sin describir |

Escribe cada prueba antes que el código cuando puedas (primero rojo, después verde). Cobertura objetivo de tu módulo: al menos 80 % [SUPUESTO].

## 11. Cuándo estás listo (definición de hecho)

- **[ ]** Muestra de 20 personas en main antes de las 11:00
- **[ ]** make datos genera 400 personas con semilla, etiquetas y meta.json
- **[ ]** regla1 y regla2 con la forma Pronostico y sus pruebas
- **[ ]** make eval produce tabla, frontera, robustez y hash reproducibles
- **[ ]** Pares de semillas con intervalo, ablaciones y tres ejemplos de error
- **[ ]** Plausibilidad medida contra INEI y SBS, y declarada
- **[ ]** docs/datos.md y docs/evaluacion.md completos
- **[ ]** docs/diccionario_datos.md con realismo justificado
- **[ ]** Ground truth documentado
- **[ ]** eval/resultados/sesgos.csv con brecha y alerta
- **[ ]** Sección de sesgos de docs/responsible_ai.md terminada

## 12. Riesgos y qué hacer

| **Riesgo** | **Plan B** |
|---|---|
| El generador se atrasa | Seguir con la muestra de 20 personas y 3 arquetipos; completar después |
| La simulación es lenta | Reducir personas por semilla en los pares; paralelizar por persona; medir antes |
| El modelo gana en entrenamiento y pierde en el perturbado | Se dice y se presenta la regla robusta |
| Plausibilidad no cuadra | Ajustar parámetros con una sola regla y anotar el ajuste; no mover la prueba |

## 13. Tu parte del pitch

| **Tema** | **Contenido** |
|---|---|
| Qué cuentas | Cómo se hicieron los datos, por qué no favorecen al modelo (partición, perturbado, resultados por arquetipo) y la frontera con sus puntos de referencia. |
| Cifras que debes tener | Frontera de cada método en la prueba y en el perturbado [por medir]; diferencia de pares con su intervalo [por medir]; plausibilidad [por medir]; los tres ejemplos de error. |
| Pregunta que te toca | Los datos sintéticos no favorecen a su modelo? Partición por fecha y personas, perturbado, y la advertencia de que solo se demuestra que el método recupera estructura conocida. |
| En el formato de 5 minutos | Minuto 3 a 4 del pitch: Responsible AI. Presentas la tabla de sesgos por grupo, la brecha, qué grupo queda peor y qué se hace. También respondes sobre datos y evaluación. |

El formato no está confirmado: la guía impresa dice 10 minutos más 3 de preguntas y el Challenge pack sugiere 5 de pitch, 5 de demo y 5 de preguntas. Prepara primero el corto. La regla de oro: ningún número sin su origen. La autocrítica se dice antes de que pregunten.

## 14. Git y trabajo en paralelo: cómo subir tu parte sin malograr la de los demás

Tu trabajo vive en tus ramas y en tus carpetas. Así puedes programar al mismo tiempo que los otros seis sin pisar nada. Tus ramas sugeridas: feat/rafael-generador, feat/rafael-reglas, feat/rafael-evaluacion.

### Qué es tuyo y qué no

- **Tus carpetas:** src/datos, src/reglas, eval (menos adopcion.py), data, config/datos.yaml, docs/datos.md, docs/evaluacion.md, docs/diccionario_datos.md.
- **Todo lo demás:** no lo edites. Si necesitas un cambio en una carpeta ajena, escribe al dueño o abre un pull request pequeño para él. Tabla completa de dueños en el Anexo E de la v9.
- **Tu revisor:** Gino. Tú revisas a quien te toque en el cuadro de revisión cruzada.

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

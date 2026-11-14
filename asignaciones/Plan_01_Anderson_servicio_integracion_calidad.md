**Hackathon de Ingeniería BBVA · AI Financial Life · Plan individual**

**Anderson · Backend: servicio, integración y calidad**

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

Eres el que hace que las piezas de los otros seis encajen y se puedan demostrar. Entregas el esqueleto del repositorio y los contratos antes de las 10:45, la fachada servicio que consume la interfaz, y las pruebas que valen la mitad de la nota: integración, determinismo, mutaciones, escala y seguridad.

### Qué recibes y de quién

| **Qué** | **De** | **Hora** |
|---|---|---|
| Aprobación de las adiciones al Anexo A | Gino | 11:00 |
| ingesta v0 con pagos inferidos | Mathias | 12:00 |
| motor.decidir con el caso del orden de pagos | Sebastián | 12:30 |
| regla2 con la forma Pronostico | Rafael | 12:30 |
| modelo.predecir v1 | Gino | 15:30 |

### Qué entregas y a quién

| **Qué** | **A** | **Hora** |
|---|---|---|
| Repositorio, estructura, Makefile, requirements, contratos y fixtures | Todos | 10:45 |
| servicio.consultar funcionando con la regla 2 | Jesús y Alberto | 13:00 |
| servicio con modelo y modo de respaldo | Todos | 16:00 |
| Resultados de determinismo, mutaciones, escala y seguridad | Gino y pitch | 18:00 y domingo |
| README de ejecución y docs/arquitectura.md | Jurado | Domingo 10:00 |

## 3. Tus primeros pasos exactos (empieza por aquí)

Hazlos en este orden. No esperes a nadie: todo lo que necesitas para empezar está en los anexos de este plan.

- **1.** Crea el repositorio en GitHub (privado) e invita a las otras seis personas con permiso de escritura.
- **2.** Clona, crea la rama feat/anderson-estructura y construye la estructura, los __init__.py con las firmas del Anexo 5 y el archivo de contratos del Anexo 4.
- **3.** Escribe tareas.py, pyproject.toml, config/base.yaml, .gitignore, .env.example y las fixtures del Anexo 6.
- **4.** Corre python tareas.py test: debe pasar (aunque solo haya una prueba de contratos).
- **5.** Sube la rama, abre el pull request a main y fusiónalo tú mismo en esta primera vez (V0, 11:00).
- **6.** Avisa al canal con la URL del repositorio y el comando de arranque: git clone, python -m venv .venv, activar, python tareas.py setup.
- **7.** Después: .github/workflows/test.yml, CODEOWNERS, plantilla de pull request y la regla de protección de main.

## 4. Qué haces tú con el Challenge pack (tareas nuevas)

Cinco tareas nuevas. Las dos primeras son contratos y observabilidad: sin ellas los demás no pueden mostrar supuestos, salud ni auditoría.

| **#** | **Qué haces** | **Cómo y dónde** | **Hora** | **Cómo sabes que está bien** |
|---|---|---|---|---|
| 1 | Agregar los campos nuevos a los contratos y actualizar las fixtures | En src/contratos/modelos.py: Decision.supuestos, evidencia, registro_id y respaldo; EstadoPersona.semanas_historia; ReporteCalidad.pii_enmascarado y columnas_sensibles_descartadas. Actualiza las 7 fixtures con valores de ejemplo. | 10:45 | Pruebas de contrato en verde; Sebastián, Mathias y las pantallas ya usan los campos |
| 2 | Registro de salud y servicio.salud() | Cada llamada a consultar escribe una línea en logs/salud.jsonl con marca de tiempo, método, latencia en milisegundos, si hubo respaldo y el código de error. servicio.salud() devuelve p50, p95, tasa de error, tasa de respaldo y número de consultas. | 16:00 a 17:00 | Con 100 consultas simuladas, p50 menor que p95 y las tasas coinciden con lo simulado |
| 3 | Auditoría de una recomendación | servicio.auditar(registro_id) lee el Registro, vuelve a correr el motor con las mismas entradas y devuelve el registro y si la decisión coincide. scripts/auditar_recomendacion.py lo llama e imprime datos, variables, modelo, versión y hash de configuración. Alberto lo muestra en la pantalla Evaluación. | 17:00 a 17:30 | La decisión se reproduce; si cambias un parámetro de config, el hash cambia y el script lo dice |
| 4 | Dependencias seguras y licencias | requirements.txt con versiones fijadas. scripts/auditar_dependencias.py lista paquete, versión y licencia (importlib.metadata) y, si hay red, ejecuta pip-audit. Vuelca el resultado a ATRIBUCIONES.md. | 17:30 a 18:00 | ATRIBUCIONES.md completo; vulnerabilidades conocidas en cero o declaradas |
| 5 | Arquitectura de referencia y decisiones técnicas clave | docs/arquitectura.md con un diagrama alineado con el del pack: datos sintéticos, motor analítico (ingesta y reglas), IA y ML, orquestación (servicio, evaluación, trazabilidad) y interfaz. Agrega cinco decisiones técnicas clave con su razón. | Domingo 9:00 a 10:00 | Diagrama y cinco decisiones en el documento; coincide con el código |

## 5. Tu especificación técnica

### 1. Repositorio, entorno y Makefile (antes de las 10:45)

- **Estructura:** la de la sección 10 de la v5: src/ con contratos, datos, ingesta, reglas, modelo, motor, servicio y app; eval/; tests/ con unit, property, contract, integracion, e2e y fixtures; data/; docs/; pitch/; config/config.yaml.
- **Archivos de arranque:** README.md esqueleto, DECISIONES.md, TRANSPARENCIA.md, ATRIBUCIONES.md, .gitignore (con .env, data/generado/, .venv, __pycache__, modelos guardados), .env.example sin valores.
- **requirements.txt:** pandas, numpy, scikit-learn, lightgbm, pydantic versión 2, streamlit, pytest, pytest-cov, hypothesis, pyyaml y ruff. Instala en tu laptop, prueba, y fija las versiones con pip freeze. Anota en el README la versión de Python [SUPUESTO: la que tenga la mayoría].
- **Makefile:** setup (entorno virtual e instalación), datos (generador con la semilla), test (pytest con cobertura), eval (tabla de resultados), demo (streamlit run src/app/main.py), mutacion, estres y seguridad.

### 2. Contratos y fixtures (antes de las 10:45)

- **src/contratos/modelos.py:** modelos pydantic con las firmas del Anexo A y las adiciones. Validadores: Pronostico ordenado (p5 menor o igual a p20, a p50 y a p80) y no negativo; Decision.numero_hoy entero y no negativo; semáforo y confianza como valores cerrados; Movimiento.moneda igual a PEN.
- **tests/fixtures:** decision_verde.json, decision_rojo.json, decision_confianza_baja.json, decision_sin_alcance.json (número 0 con el mensaje de lo que falta), pronostico_ejemplo.json, estado_caso_orden_pagos.json (saldo 100, pago de 300 el día 3, ingreso de 400 el día 10), reporte_calidad_ejemplo.json. Con estos archivos Jesús y Alberto avanzan sin esperar al motor.

### 3. Servicio (regla 2 a las 13:00, completo a las 16:00)

- **config:** cargar(ruta) devuelve una configuración inmutable. Falla con un mensaje que nombra la clave que falta. hash_config es el sha256 del JSON ordenado.
- **consultar(customer_id, fecha, metodo):** metodo es modelo, regla1 o regla2. Pasos: 1) tomar el historial limpio de la persona (la ingesta se ejecuta una vez al cargar y se guarda en memoria); 2) armar EstadoPersona con el saldo del último movimiento, los pagos de los próximos 14 días y las semanas de historia; 3) obtener el Pronostico del método elegido; 4) llamar motor.decidir; 5) escribir el Registro; 6) devolver la Decision.
- **Modo de respaldo:** si el modelo falla, falta o lanza HistoriaInsuficiente, se usa la regla 2 y Decision.respaldo queda en verdadero con un mensaje claro. Si faltan datos, se cargan los de data/muestra. La interfaz nunca ve una excepción cruda.
- **responder(propuesta_id, accion):** accion es aprobar o rechazar. Solo registra la decisión. No mueve nada.
- **cargar_archivo(origen):** llama a ingesta.cargar y devuelve el ReporteCalidad. La usan el arranque del servicio y la prueba de evolución desde la línea de comandos; la app NO la llama: no hay pantalla de carga porque los datos son sintéticos y vienen precargados.
- **Registro:** una línea JSON por recomendación, escrita con append y vaciado a disco. Campos: marca de tiempo, customer_id, fecha_corte, método, entradas (saldo, pagos, pronóstico), decisión completa, versión del generador, versión del modelo, semilla y hash_config.

### 4. Calidad transversal (16:00 a 18:00 y el domingo)

- **Integración y e2e:** prueba del flujo completo con AppTest de Streamlit: del archivo a las tres pantallas, con la muestra y con la regla 2, y después con el modelo.
- **Determinismo:** correr make eval tres veces con PYTHONHASHSEED distintos (0, 1 y 42) y comparar el sha256 del archivo de resultados. Debe ser idéntico. En las demás laptops, lo mismo.
- **Escala y tiempos:** script que genera 400 y 4,000 personas, mide el tiempo de generar, de evaluar y el p50 y p95 de 100 consultas al servicio. Lo medido va a docs/evaluacion.md. Objetivo: pantalla en menos de 2 segundos [SUPUESTO].
- **Seguridad:** scripts/buscar_secretos.py: expresiones regulares sobre git log -p y sobre el árbol de trabajo (claves, tokens, contraseñas, correos, teléfonos de 9 dígitos, DNI de 8 dígitos). Debe dar cero hallazgos. Revisa que .env no esté en el historial.
- **Versiones de Python:** si hay dos versiones instaladas en el equipo, correr los resultados en ambas (nivel P2).
- **Documentos:** README con tres comandos para el jurado (make setup, make datos, make demo y make eval) y docs/arquitectura.md con el diagrama de tres capas, los contratos, las dependencias y las salvaguardas.

### Mutaciones del motor (script scripts/mutar_motor.py)

El script copia src/motor a una carpeta temporal, aplica una mutación por vez, corre las pruebas del motor y cuenta si alguna falla. Una mutación que ninguna prueba detecta se explica o se cubre con una prueba nueva.

| **#** | **Mutación** | **Prueba que debería fallar** |
|---|---|---|
| 1 | Cambiar menor o igual por menor en la cobertura del pago | Caso borde del pago justo cubierto |
| 2 | Quitar el colchón de la resta | Caso con colchón distinto de cero |
| 3 | Cambiar P5 por P50 en el verificador de la propuesta | Propiedad de cobertura en P5 |
| 4 | Invertir el signo de los pagos | Caso del orden de pagos |
| 5 | Cambiar el mínimo por el máximo en el número de hoy | Caso del orden de pagos |
| 6 | Quitar el max con cero | Propiedad de número no negativo |
| 7 | Intercambiar los umbrales del semáforo | Casos de semáforo verde, ámbar y rojo |
| 8 | Redondear hacia arriba en vez de hacia abajo | Prueba de redondeo conservador |

## 6. Archivos y funciones que escribes (con código)

Estos son tus archivos, en el orden en que debes escribirlos. Los marcados V0 deben estar en main antes de las 11:00 para que nadie espere.

### V0 (antes de las 11:00): estructura, contratos, stubs y herramientas

- **Estructura:** carpetas de la sección 10 de la v9, más src/__init__.py y un __init__.py en cada paquete de src, tests y eval (para que Python los reconozca).
- **src/contratos/modelos.py:** copia tal cual el archivo del Anexo 4 de este plan. Es el contrato de todos.
- **Stubs:** en el __init__.py de cada módulo escribe las firmas del Anexo 5 con raise NotImplementedError en el cuerpo. Con eso Mathias, Sebastián, Gino y Rafael pueden importar las funciones de los demás desde el minuto 1.
- **tests/fixtures:** los archivos JSON del Anexo 6 más una decisión verde, una roja, una de confianza baja, una sin alcance y un reporte de calidad de ejemplo.
- **.gitignore:** incluye .env, .venv, __pycache__, data/generado, logs, *.pkl y *.joblib. .env.example sin valores.

# pyproject.toml

[tool.pytest.ini_options]

pythonpath = ["."]

testpaths = ["tests"]

# tareas.py  (reemplaza a make en Windows; el Makefile queda como alias)

import subprocess, sys

COMANDOS = {

"setup": [[sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]],

"datos": [[sys.executable, "-m", "src.datos.generador"]],

"test":  [[sys.executable, "-m", "pytest", "-q"]],

"eval":  [[sys.executable, "-m", "eval.tabla"]],

"demo":  [["streamlit", "run", "src/app/main.py"]],

}

if __name__ == "__main__":

if len(sys.argv) != 2 or sys.argv[1] not in COMANDOS:

sys.exit("Comandos: " + ", ".join(COMANDOS))

for cmd in COMANDOS[sys.argv[1]]:

codigo = subprocess.call(cmd)

if codigo:

sys.exit(codigo)

### config/base.yaml y src/servicio/config.py

# config/base.yaml   (cada modulo tiene su propio config/<modulo>.yaml; Anderson solo el base)

horizontes_dias: [3, 7, 14]

cuantiles: [0.05, 0.20, 0.50, 0.80]

cuantil_conservador: 0.20

colchon: 0

umbral_historia_semanas: 4

ventana_regla_robusta_semanas: 8

semillas_evaluacion: 20

semilla_generador: 12345

variables_sensibles: [edad, genero, ubicacion, distrito, nombre, dni, telefono]

generativa: {activada: false, proveedor: ninguno, timeout_s: 6, reintentos: 1, temperatura: 0, max_tokens: 250, max_palabras: 90}

# src/servicio/config.py

import hashlib, json

from pathlib import Path

import yaml

OBLIGATORIAS = ["horizontes_dias", "cuantiles", "cuantil_conservador", "colchon",

"umbral_historia_semanas", "variables_sensibles"]

def cargar(carpeta: str = "config") -> dict:

cfg: dict = {}

for archivo in sorted(Path(carpeta).glob("*.yaml")):

datos = yaml.safe_load(archivo.read_text(encoding="utf-8")) or {}

if archivo.stem == "base":

cfg.update(datos)

else:

cfg[archivo.stem] = datos       # cfg["ingesta"], cfg["motor"], cfg["modelo"], cfg["datos"]

faltan = [k for k in OBLIGATORIAS if k not in cfg]

if faltan:

raise ValueError(f"Faltan claves en config: {faltan}")

return cfg

def hash_config(cfg: dict) -> str:

return hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:16]

### V2 (13:00): src/servicio/servicio.py

La app solo importa funciones de src/servicio/__init__.py, que delegan en una instancia de la clase Servicio.

class Servicio:

def __init__(self, cfg, modelo=None, dir_logs="logs"):

self.cfg, self.modelo, self.dir_logs = cfg, modelo, dir_logs

self._df = None            # movimientos limpios de todas las personas

self._pagos = []           # pagos inferidos por la ingesta

def cargar_archivo(self, origen) -> ReporteCalidad:

df, reporte, pagos = ingesta.cargar(origen, self.cfg)   # puede lanzar ErrorIngesta: se deja subir

self._df, self._pagos = df, pagos

return reporte

def consultar(self, customer_id, fecha, metodo="modelo") -> Decision:

t0 = time.perf_counter(); respaldo = False; codigo_error = None

hist = self._df[(self._df.customer_id == customer_id) & (self._df.fecha_hora.dt.date <= fecha)]

estado = EstadoPersona(

customer_id=customer_id, fecha_corte=fecha, saldo=_saldo(hist),

pagos=ingesta.proximos_pagos(self._pagos, customer_id, fecha),

colchon=self.cfg["colchon"],

semanas_historia=ingesta.semanas_historia(hist, customer_id, fecha))

try:

if metodo == "modelo" and self.modelo is not None:

pron = self.modelo.predecir(hist, fecha)

elif metodo == "regla1":

pron = reglas.regla1(hist, fecha, self.cfg)

else:

pron = reglas.regla2(hist, fecha, self.cfg)

except Exception as e:                       # incluye HistoriaInsuficiente y modelo ausente

respaldo, codigo_error = True, type(e).__name__

pron = reglas.regla2(hist, fecha, self.cfg)

decision = motor.decidir(estado, pron, self.cfg)

registro_id = self._registrar(estado, pron, decision, metodo)   # una linea en logs/registro.jsonl

decision = decision.model_copy(update={"registro_id": registro_id, "respaldo": respaldo})

self._salud(metodo, (time.perf_counter() - t0) * 1000, respaldo, codigo_error)

return decision

def responder(self, propuesta_id, accion) -> dict:

# accion en {"aprobar", "rechazar"}; solo registra, no mueve nada

...

def salud(self) -> dict:

# lee logs/salud.jsonl y devuelve p50, p95, tasa_error, tasa_respaldo, consultas

...

def auditar(self, registro_id) -> dict:

# lee el registro, vuelve a correr motor.decidir con las MISMAS entradas guardadas

# y devuelve {"registro": ..., "reproduce": True/False, "hash_config": ...}

...

Detalles: saldo = el campo saldo del último movimiento de la persona; si no existe, la suma acumulada de montos. Registro y salud se escriben con append y vaciado a disco; ninguno guarda el archivo original ni texto libre. La Decision es inmutable, por eso se usa model_copy(update=...).

### Pruebas automáticas y repositorio (.github)

# .github/workflows/test.yml     (comprobar las versiones de las acciones en la documentacion de GitHub)

name: tests

on: [pull_request, push]

jobs:

tests:

runs-on: ubuntu-latest

steps:

- uses: actions/checkout@v4
- uses: actions/setup-python@v5

with: {python-version: "3.12"}

- run: pip install -r requirements.txt
- run: pytest -q

# .github/CODEOWNERS      (cambia los nombres por los usuarios de GitHub de cada persona)

/src/contratos/   @usuario-anderson @usuario-gino

/src/servicio/    @usuario-anderson

/src/datos/ /src/reglas/ /eval/    @usuario-rafael

/src/ingesta/     @usuario-mathias

/src/motor/       @usuario-sebastian

/src/modelo/      @usuario-gino

/src/app/         @usuario-jesus @usuario-alberto

### V3 a V4: scripts de calidad

- **scripts/mutar_motor.py:** copia src/motor a una carpeta temporal, aplica una mutación de la tabla, corre pytest tests/unit/motor tests/property y cuenta si alguna prueba falla.

MUTACIONES = [  # (archivo, texto a buscar, texto de reemplazo)

("decidir.py", "<= d", "< d"),                 # 1 pago justo cubierto

("decidir.py", "- cfg[\"colchon\"]", ""),         # 2 quitar el colchon

("decidir.py", "\"p5\"", "\"p50\""),            # 3 verificador en P50

("decidir.py", "min(", "max("),               # 4 minimo por maximo

("decidir.py", "max(0,", "(")]                # 5 quitar el max con cero

# bucle: copiar -> reemplazar una vez -> pytest -> "detectada" si pytest falla, "sobrevive" si pasa

- **scripts/buscar_secretos.py:** expresiones regulares sobre git log -p y el árbol de trabajo: claves (sk-, api_key, token), correos, teléfonos de 9 dígitos, DNI de 8 dígitos. Debe dar cero hallazgos.
- **scripts/auditar_dependencias.py:** importlib.metadata para listar paquete, versión y licencia; escribe ATRIBUCIONES.md; si hay red, ejecuta pip-audit.
- **scripts/auditar_recomendacion.py <registro_id>:** llama a servicio.auditar e imprime datos, versión, hash de configuración y si se reproduce.
- **scripts/escala.py:** genera 400 y 4,000 personas, mide tiempos y p50 y p95 de 100 consultas.

## 7. Opción B (capa generativa): tu parte si se activa

Esta sección solo se ejecuta si se cumplen las cinco condiciones del diseño de la opción B: autorización por escrito de la organización, control 1 aprobado, antes de las 17:00, clave de OpenAI funcionando en las dos laptops y pruebas P0 en verde. Si falta una, no hagas nada de esto. T0 es la hora de la autorización; con T0 después de las 14:30 no se activa.

Resumen del diseño: el modelo solo reescribe el porqué que el motor ya calculó. Ve una entrada mínima sin identificadores. Un verificador sin IA exige que cada cifra del texto exista en esa entrada; si algo falla, se muestra la plantilla. La clave de OpenAI vive solo en .env.

### Tu archivo: src/generativa/proveedores.py (T0 a T0+60)

class ProveedorNoDisponible(Exception): ...

class ProveedorOpenAI:

def __init__(self, cfg):

self.modelo = os.environ.get("LLM_MODEL")          # se elige probando con las fixtures [por elegir]

clave = os.environ.get("LLM_API_KEY")

if not clave or not self.modelo:

raise ProveedorNoDisponible("falta LLM_API_KEY o LLM_MODEL")

from openai import OpenAI

self.cfg = cfg["generativa"]

self.cliente = OpenAI(api_key=clave, timeout=self.cfg["timeout_s"])

def generar(self, sistema: str, usuario: str) -> str:

mensajes = [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}]

params = dict(model=self.modelo, messages=mensajes, response_format={"type": "json_object"})

try:

r = self.cliente.chat.completions.create(max_tokens=self.cfg["max_tokens"], temperature=0, **params)

except Exception:

# algunos modelos piden max_completion_tokens y no aceptan temperature [verificar en la documentacion de OpenAI]

r = self.cliente.chat.completions.create(max_completion_tokens=self.cfg["max_tokens"], **params)

return r.choices[0].message.content

class Cortacircuitos:                 # 3 fallos seguidos apagan la capa 60 segundos

def __init__(self, fallos=3, pausa_s=60): ...

def permite(self) -> bool: ...

def registrar(self, ok: bool): ...

- **.env.example:** LLM_PROVEEDOR=ninguno, LLM_API_KEY=, LLM_MODEL=, LLM_BASE_URL= (sin valores). El .env real no se sube nunca.
- **Llamada de prueba:** con tests/fixtures/decision_rojo.json debe devolver texto que pase el verificador en menos de 6 segundos. Hazla en las dos laptops.
- **Servicio y salud:** después de motor.decidir, si cfg["generativa"]["activada"] es verdadero, llama a redactar(decision); registra fuente, motivo y latencia en logs/salud.jsonl y suma tasa_fallback_generativa a servicio.salud(). El servicio nunca deja pasar una excepción de esta capa.
- **Tope de gasto:** fija un límite de gasto en el panel de la cuenta de OpenAI antes de la demo y revisa los términos de uso y la política de datos [verificar].

## 8. Opción C (asistente del semáforo con LLM, RAG y ML): tu parte si se llega al corte

Esta sección es nivel P2. Puntos de corte: A a las 13:00 (si el control 1 salió bien, empieza quien tenga holgura), B a las 16:00 (se integra el flujo si el control 2 salió bien), C a las 17:30 (lo que no pase la evaluación no entra a la demo) y D a las 17:45 (fusión final). El asistente nunca desplaza una prueba P0.

Qué es: una pantalla de chat donde la persona pregunta por su número, sus pagos y escenarios. Usa el motor y el modelo como herramientas de ML, una base de conocimiento propia con búsqueda local (RAG) y, si se activa, un LLM para entender y redactar con cada cifra verificada. Funciona completo sin LLM (modo 1). Se inspira en las lecciones del copiloto del bot_diagnosis: no se copia código, datos ni playbooks.

### Tu archivo: src/asistente/flujo.py y servicio.preguntar / servicio.simular

def preguntar(servicio, customer_id, fecha, texto, contexto=None) -> Respuesta:

t0 = time.perf_counter()

ok, motivo = guardia.revisar(texto, servicio.cfg)                  # Mathias

if not ok:

return _rechazo(motivo)

intent = intenciones.clasificar(texto, servicio.cfg, servicio.proveedor)   # Gino: modo 2 (LLM) o ML + reglas

if intent.nombre == "fuera_de_alcance":

return _rechazo("fuera_de_alcance")

if intent.confianza < servicio.cfg["asistente"]["umbral_intencion"]:

return _pedir_reformular()                                     # ofrece 3 preguntas sugeridas

params = intenciones.parametros(texto, intent, servicio.cfg)       # monto y dia ya validados

decision = servicio.consultar(customer_id, fecha)                  # herramienta: motor y modelo

resultados = {"intencion": intent.nombre, "numero_hoy": decision.numero_hoy}

if intent.nombre == "que_pasa_si":

sim = servicio.simular(customer_id, fecha, Escenario(**params))

resultados |= _comparar(decision, sim)                         # antes y despues

pasajes = servicio.rag.buscar(_consulta(intent, texto), k=3) + kb_dinamica(decision)   # Rafael

respuesta = _redactar(intent, resultados, pasajes)                 # modo 2 con LLM y verificador; si falla, plantilla

_registrar(...); _salud(...)                                       # sin guardar la pregunta sin enmascarar

return respuesta

# servicio.simular(customer_id, fecha, escenario): arma el estado y el pronostico como en consultar y llama a

# motor.simular(estado, pron, escenario, cfg).  Mismo respaldo: si el modelo falla, usa regla2.

- **Límite de tasa:** máximo asistente.max_preguntas_por_minuto (10) por sesión; la pregunta 11 recibe un mensaje de espera, no un error.
- **Prueba de humo (desde el corte A):** agrega a tareas.py el comando chat-humo: hace una pregunta por cada intención con el servicio falso y comprueba que cada una devuelve una Respuesta válida. Es la lección del bot_diagnosis: el copiloto estuvo roto por cuatro errores apilados porque nadie lo probó de punta a punta; aquí se prueba el primer día.
- **Salud y registro:** suma a servicio.salud() la tasa de fallback del chat y la latencia por modo; el Registro guarda intención, herramientas, ids de pasajes, fuente y verificación.
- **Proveedor:** reutiliza el ProveedorOpenAI de la opción B sin cambios; en modo 1 el servicio nunca lo instancia.

## 9. Tus horas (sábado 14 y domingo 15)

| **Hora (Lima)** | **Qué haces** | **Debe quedar verificable** |
|---|---|---|
| 10:15 a 10:45 | Repositorio, estructura, Makefile, requirements, contratos pydantic y fixtures. Publicar en main. | make test corre en tu laptop; los demás clonan y hacen make setup |
| 10:45 a 11:00 | Avisar al equipo. Apoyar instalaciones. Llevar a Gino las cuatro adiciones del Anexo A. | Aprobación anotada en DECISIONES.md |
| 11:00 a 12:00 | config.py, hash_config, servicio.consultar con regla 2 falsa sobre la muestra, Registro. | consultar devuelve una Decision de la fixture |
| 12:00 a 13:00 | Conectar ingesta v0, motor y regla 2 reales. Control 1. | Etiqueta v0-control1 con el flujo de punta a punta |
| 13:00 a 16:00 | Modo de respaldo, cargar_archivo, responder. Pruebas de contrato y e2e. Empezar mutaciones y escala. | Pruebas P0 en verde; control 2 con la etiqueta v1-control2 |
| 16:00 a 18:00 | Determinismo, seguridad, mutaciones, escala. Integrar el modelo de Gino en el servicio. | Informe de mutaciones y de tiempos |
| 18:00 a 19:30 | Etiqueta v2-congelado. make eval reproducible y su hash. docs/arquitectura.md borrador. | Hash de la tabla anotado |
| Domingo 8:30 a 11:00 | Repetir determinismo y seguridad. README final. Entregables completos. | Carpeta lista; make setup y make demo desde un clon limpio |
| Domingo 11:00 a 13:30 | Ensayos. Etiqueta v3-final. Laptop de respaldo con el repositorio clonado. | Demo corre tres veces seguidas |

Los horarios son supuestos hasta que la organización comunique los suyos. Si cambian, Gino reordena este cuadro.

## 10. Tus pruebas

| **Prueba** | **Qué verifica** | **Criterio de éxito** |
|---|---|---|
| De contrato | Cada modelo pydantic rechaza campos faltantes y valores fuera de rango; cada función cumple la forma del Anexo A | Falla si alguien cambia un campo sin aprobación |
| Servicio con la regla 2 | consultar devuelve una Decision válida para cinco personas de la muestra | Sin excepciones; Registro con una línea por consulta |
| Respaldo | Con el modelo ausente, consultar usa la regla 2 y marca respaldo | respaldo verdadero y mensaje presente |
| Integración y e2e | AppTest del archivo a las tres pantallas | Las pantallas muestran un número |
| Determinismo | sha256 de la tabla con tres PYTHONHASHSEED | Hash idéntico |
| Mutaciones | Las 8 del cuadro | Al menos 6 detectadas; las otras se explican |
| Escala | 400 y 4,000 personas; p50 y p95 de consulta | Línea base medida y anotada |
| Seguridad | Búsqueda de secretos en el historial y el árbol | Cero hallazgos |
| Salud | 100 consultas simuladas | p50 menor que p95; tasas correctas |
| Auditoría | servicio.auditar de un registro_id real | La decisión se reproduce igual |
| Sin PII en logs | Revisar Registro y salud.jsonl | No guardan el archivo original ni texto libre |
| Contratos nuevos | Campos supuestos, evidencia, registro_id, pii_enmascarado | Validación pydantic rechaza ausencias |

Escribe cada prueba antes que el código cuando puedas (primero rojo, después verde). Cobertura objetivo de tu módulo: al menos 80 % [SUPUESTO].

## 11. Cuándo estás listo (definición de hecho)

- **[ ]** make setup, make datos, make test, make eval y make demo funcionan desde un clon limpio
- **[ ]** Contratos y fixtures en main antes de las 10:45 y las adiciones aprobadas
- **[ ]** servicio.consultar funciona con regla 2 a las 13:00 y con el modelo y el respaldo a las 16:00
- **[ ]** Pruebas P0 en verde antes del congelamiento
- **[ ]** Informe de mutaciones, escala, determinismo y seguridad en docs/evaluacion.md
- **[ ]** README y docs/arquitectura.md completos
- **[ ]** Campos nuevos en contratos y fixtures antes de las 11:00
- **[ ]** logs/salud.jsonl y servicio.salud() funcionando
- **[ ]** servicio.auditar y el script reproducen una recomendación
- **[ ]** ATRIBUCIONES.md con versiones y licencias
- **[ ]** docs/arquitectura.md con el diagrama de referencia y cinco decisiones

## 12. Riesgos y qué hacer

| **Riesgo** | **Plan B** |
|---|---|
| Alguien no puede instalar LightGBM | Usar GradientBoostingRegressor de scikit-learn (plan B de Gino) y anotarlo |
| Una laptop falla con la versión de Python | Todos usan la versión fijada en el README; ten una laptop de respaldo con el repositorio clonado |
| Un contrato cambia a mitad de camino | Solo por pull request aprobado por ti y Gino; actualizas fixtures el mismo día |
| La mutación revela un hueco de pruebas | Se agrega la prueba o se explica por qué la mutación es equivalente |

## 13. Tu parte del pitch

| **Tema** | **Contenido** |
|---|---|
| Qué cuentas | La arquitectura de tres capas, los contratos, el funcionamiento sin red, el respaldo, y los números de pruebas, mutaciones y determinismo. |
| Cifras que debes tener | Mutaciones detectadas sobre las hechas [por medir]; pruebas totales y cobertura [por medir]; hash idéntico en las laptops [por medir]; latencia p50 y p95 [por medir]. |
| Pregunta que te toca | Qué pasa si falla el modelo o no hay internet: respaldo con regla 2 y cero dependencias externas. |
| En el formato de 5 minutos | Aportas 30 segundos dentro de la demo (panel de salud y auditar una recomendación) y respondes preguntas de arquitectura, seguridad y trazabilidad. |

El formato no está confirmado: la guía impresa dice 10 minutos más 3 de preguntas y el Challenge pack sugiere 5 de pitch, 5 de demo y 5 de preguntas. Prepara primero el corto. La regla de oro: ningún número sin su origen. La autocrítica se dice antes de que pregunten.

## 14. Git y trabajo en paralelo: cómo subir tu parte sin malograr la de los demás

Tu trabajo vive en tus ramas y en tus carpetas. Así puedes programar al mismo tiempo que los otros seis sin pisar nada. Tus ramas sugeridas: feat/anderson-estructura, feat/anderson-servicio, feat/anderson-calidad.

### Qué es tuyo y qué no

- **Tus carpetas:** src/contratos, src/servicio, config/base.yaml, requirements.txt, tareas.py, Makefile, pyproject.toml, .github, scripts, tests/contract, tests/integracion, tests/e2e, tests/fixtures, README.md, docs/arquitectura.md.
- **Todo lo demás:** no lo edites. Si necesitas un cambio en una carpeta ajena, escribe al dueño o abre un pull request pequeño para él. Tabla completa de dueños en el Anexo E de la v9.
- **Tu revisor:** Gino (contratos) y Sebastián (lo demás). Tú revisas a quien te toque en el cuadro de revisión cruzada.

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

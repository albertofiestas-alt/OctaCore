# Ukku para iOS

«Tu plata, con un plan». App nativa SwiftUI de cuatro pestañas (Inicio, Tu plan, Actividad, Ajustes) para el hackathon. Prototipo con datos sintéticos: orientación educativa, sin operaciones bancarias y sin vínculo oficial con ningún banco.

Bundle ID: `com.hackathon.ukku`. No toca MisCuentas ni el backend OctaCore.

## Arrancar

En otra Mac: instala Xcode con un simulador iOS y XcodeGen. Desde esta carpeta ejecuta `xcodegen generate`, abre `Ukku.xcodeproj`, selecciona un simulador disponible y ejecuta el esquema `Ukku`. El proyecto requiere iOS 18 o posterior. Las pruebas de esta entrega se hicieron en iPhone 17 Pro con iOS 26.5.

Los scripts siguientes conservan el identificador del simulador de la Mac de desarrollo. Para otro dispositivo, utiliza Xcode o adapta ese identificador.

```sh
herramientas/compilar_y_lanzar.sh            # compila, instala y abre en el iPhone 17 Pro del simulador
herramientas/compilar_y_lanzar.sh --escenario base --pestana 0   # reinicia los datos demo y abre en Inicio
```

Argumentos de desarrollo de la app: `--pestana 0..3`, `--escenario base|depende|revisar|vacio` (reinicia los datos con ese escenario).

Si agregas archivos Swift, el script ya corre `xcodegen generate`.

## IA (pendiente de credencial)

La app nunca guarda secretos. Habla con un backend local en `http://127.0.0.1:8787`:

```sh
python3 backend/servidor.py                               # sin IA: la app muestra «Conecta un proveedor de IA»
ANTHROPIC_API_KEY=... python3 backend/servidor.py         # con IA real (API oficial de Anthropic)
UKKU_MODEL=<id> ANTHROPIC_API_KEY=... python3 backend/servidor.py   # fijar el modelo; si no, usa el primero que devuelve /v1/models
```

La suscripción de Claude con la que se construyó la app no se usa para el chat: hace falta una clave de API propia. Sin ella funcionan todas las acciones manuales y las tres acciones guiadas (ejemplos calculados sin IA, etiquetados como tales).

Flujo con IA: el modelo interpreta y propone con herramientas -> el backend valida (lista permitida + esquema estricto) -> la app valida otra vez y muestra la vista previa calculada por ella -> el usuario confirma -> ejecución local idempotente -> el chat informa el resultado guardado.

## Estructura

```
Sources/
  App/UkkuApp.swift            entrada, TabView de 4 pestañas
  Models/Modelos.swift         Cuenta, Movimiento, PagoConFecha, Presupuesto, Meta, Plan, Ejecucion, PropuestaAccion
  Models/Seed.swift            datos demo y escenarios
  Services/Calculo.swift       disponible, semáforo por fecha, sugerencia de hoy, insights, logros (determinista)
  Services/Simulacion.swift    impacto local de un gasto hipotético sin modificar el estado
  Services/Acciones.swift      capa única de acciones del contrato: validar, previsualizar, aplicar
  Services/Store.swift         estado observable, persistencia, runner idempotente, chat
  Services/Servicios.swift     JSON local, notificaciones locales, LLMProvider (backend local)
  Design/                      tokens, iconos y UkkuPersonaje (reproducción de PNG del oso aprobado)
  Views/                       Inicio, PlanUkku, Actividad, Ajustes y hoja Simulador
backend/servidor.py            LLMProvider real (solo biblioteca estándar)
herramientas/                  compilar_y_lanzar.sh, captura.sh, preparar_creativos.py
Personaje/                     siete clips PNG transparentes y sus manifest.json
evidencias-premium/            capturas, video real del simulador e INFORME.md
```

Recursos editables y catálogo: [original-character](../ukku-app-handoff/original-character/). Identidad: [guía de marca](../branding/ukku-equipo-v1/GUIA-DE-MARCA.html). Ver [INFORME.md](evidencias-premium/INFORME.md) para las pruebas realizadas y las limitaciones.

## Cálculos

- Importes en céntimos enteros.
- Disponible del mes = saldo actual + ingresos confirmados del ciclo − pagos fijos pendientes − reservas (sin duplicar) − colchón. El saldo ya incluye los movimientos pasados. Si es negativo se muestra 0 y el faltante aparte.
- Semáforo: se evalúa pago por pago según su fecha. Verde si alcanza con dinero confirmado; ámbar si solo alcanza contando ingresos sin confirmar; rojo si no alcanza.
- «Para hoy»: adaptador demo determinista con la forma de la regla de OctaCore (mínimo por fecha de pago a 14 días) usando ingresos confirmados. No es un modelo entrenado; se reemplaza por el motor de OctaCore cuando exista una forma de consultarlo.
- Semilla: saldo S/ 2,400, alquiler pendiente S/ 700, reservas S/ 240, colchón S/ 200 => disponible S/ 1,260.

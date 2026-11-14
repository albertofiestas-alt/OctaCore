# Ukku · Edición Codex

App nativa SwiftUI para iPhone, diseñada como una versión independiente de Ukku. Identificador `com.hackathon.ukku.codex`: convive con la app anterior y conserva sus propios datos.

## Abrir y ejecutar

Abre `UkkuCodex.xcodeproj`, selecciona el esquema **UkkuCodex** y un iPhone Simulator; pulsa Run. Requiere Xcode con iOS 18 o posterior. Swift Package Manager resuelve Rive 6.30.1 al compilar por primera vez.

También puedes usar:

```sh
./herramientas/ejecutar.sh
```

El script utiliza XcodeGen para regenerar el proyecto y el simulador «Ukku Codex» si existe, o el primer iPhone disponible. `UKKU_SIMULATOR_UDID` permite elegir otro dispositivo; `UKKU_DERIVED_DATA`, la carpeta de compilación. Con Xcode 27 abre Device Hub, donde se muestra el simulador.

Para cargar un ejemplo desde cero:

```sh
./herramientas/ejecutar.sh --escenario base
# Otros ejemplos: depende, revisar, vacio.
# --sin-saludo omite la bienvenida; --pestana 0..3 abre una sección.
```

## Experiencia

- **Inicio:** margen para hoy, disponible mensual, desglose de cálculo, calendario, meta y movimientos recientes.
- **Simulador:** gasto, ingreso hipotético o ambos; día del ingreso; comparación de importes y gráfico a 14 días. Nunca modifica el estado guardado.
- **Tu plan:** reserva para un pago, meta de ahorro o presupuesto; vista previa y confirmación; aportes, pausa, reanudación y eliminación.
- **Actividad:** registros de ingresos y gastos, búsqueda, filtros, detalle y eliminación reversible en el saldo. Registrar un pago previsto no lo descuenta dos veces; eliminar ese movimiento vuelve a dejarlo pendiente.
- **Ajustes:** nombre, colchón, ciclo, privacidad, movimiento reducido, recordatorios locales, exportación y ejemplos.

La creación de planes y movimientos se confirma tras una vista previa. Cada propuesta conserva un ID y una versión del contexto para evitar duplicados y confirmar sobre información desactualizada.

## Identidad y animación

Conserva el oso y la paleta aprobados. El archivo Rive local incluye los artboards Reposo, Atento, Revisar, SinDatos, Saludo y Celebra. La reproducción se pausa fuera de primer plano. Movimiento reducido usa una imagen quieta; los clips PNG originales están disponibles como respaldo si el recurso Rive no puede abrirse.

La interfaz y los recorridos de esta edición se implementaron en este proyecto. El dominio de datos, cálculos iniciales y recursos del personaje provienen de la base local `UkkuApp`. Esta edición amplía la simulación por fechas y corrige la cobertura al cruzar el cierre mensual y el registro reversible de pagos. La animación conserva el archivo original del proyecto, sin rediseñar al personaje.

## Datos y límites

Funciona con datos ficticios, persistidos dentro del contenedor de la app. No requiere credenciales, no llama a IA ni ejecuta operaciones bancarias. El gráfico y el margen se calculan con ingresos confirmados e hipótesis explícitas, sin predicciones del modelo del equipo.

Los importes se calculan en céntimos enteros. La vista de simulación permite un gasto y un ingreso hipotético; el servicio acepta hasta tres ingresos, con montos de hasta S/ 10,000 y días 0 a 14, siguiendo los límites del contrato del equipo.

El proyecto está preparado para iPhone en vertical y modo claro. La firma para instalarlo en un iPhone físico requiere elegir tu equipo de Apple en Xcode; la entrega está compilada para simulador.

## Verificación

```sh
./herramientas/probar_dominio.sh
xcodebuild -project UkkuCodex.xcodeproj -scheme UkkuCodex \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' \
  -parallel-testing-enabled NO CODE_SIGNING_ALLOWED=NO test
```

Las pruebas de dominio cubren importes, límites, ingresos antes y después de un pago, inmutabilidad de la simulación, cambio de mes, colchón y registro de pagos. Las cinco pruebas de interfaz recorren simulación, creación y persistencia de metas, movimientos, búsqueda, estado vacío, privacidad y registro y eliminación de pagos. La compilación y estas pruebas se verificaron en el simulador iOS. Los resultados y capturas de la entrega se conservan localmente en `evidencias`; no se incluyen en el repositorio.

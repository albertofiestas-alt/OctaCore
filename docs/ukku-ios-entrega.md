# Entrega de Ukku: app iOS, identidad y personaje

Entrega de Alberto/Afi preparada el 14 de noviembre de 2026. La app nativa es un prototipo independiente de la interfaz Python y del servicio OctaCore. No cambia contratos, modelos ni cálculos del backend del equipo.

## Dónde está cada cosa

| Carpeta | Contenido |
|---|---|
| [UkkuApp](../UkkuApp/) | Proyecto SwiftUI, cuatro pestañas, datos sintéticos, persistencia local y backend adaptador para una API de IA |
| [Personaje](../UkkuApp/Personaje/) | Clips que se incluyen en el bundle iOS; no se descargan al abrir la app |
| [Personaje original y catálogo](../ukku-app-handoff/original-character/) | Logo maestro, capas, expresiones, escenas, renders PNG RGBA, previews MP4/GIF, prompts e inventario |
| [Identidad aprobada](../branding/ukku-bbva-v2/) | Logo, colores, tokens y lámina de identidad |
| [Guía del equipo](../branding/ukku-equipo-v1/GUIA-DE-MARCA.html) | Identidad, voz y aplicaciones de marca |
| [Contrato de acciones](../ukku-app-handoff/CONTRATO-ACCIONES.json) | Acciones locales que puede proponer el asistente y sus parámetros |
| [Pruebas y limitaciones](../UkkuApp/evidencias-premium/INFORME.md) | Evidencia de la compilación, flujos y movimiento en el simulador |

Los catálogos HTML se abren después de clonar o descargar el repositorio; GitHub muestra su código fuente. Las previews son para revisión. Los PNG transparentes son los recursos de integración.

## Ejecutar en otra Mac

Requisitos: Xcode con un simulador iOS 18 o posterior y XcodeGen instalado. Para generar el proyecto y abrirlo:

```sh
cd UkkuApp
xcodegen generate
open Ukku.xcodeproj
```

En Xcode, selecciona el esquema `Ukku` y un simulador instalado, y ejecuta la app. Los scripts de la Mac de desarrollo contienen un UDID concreto; utiliza Xcode si ese dispositivo no existe en tu Mac. El backend Python es opcional para la demo guiada. Consulta [UkkuApp/README.md](../UkkuApp/README.md) para la configuración de la API y los escenarios de prueba.

## Animación y creativos

El maestro aprobado es [logo-maestro.png](../ukku-app-handoff/original-character/referencia/logo-maestro.png). Se entrega el oso de anteojos con sombrero azul y cinta celeste. El rig vectorial anterior y las propuestas descartadas no forman parte de esta entrega.

- `saludo`: tres segundos; mano y sombrero independientes, retirada, saludo y recolocación.
- `reposo`, `reposo-bien`, `reposo-sin-datos`: parpadeo interno del maestro.
- `reposo-atento`, `reposo-revisar`: expresiones estáticas entregadas en el formato de secuencia del reproductor.
- `celebra`: un segundo; visto y destellos independientes junto al personaje.

Los siete clips son PNG RGBA de 480 × 480 a 24 fps. El render reproducible está en [RenderOriginal.swift](../ukku-app-handoff/original-character/animacion/RenderOriginal.swift); sus instrucciones están en [LEEME-ANIMACION.txt](../ukku-app-handoff/original-character/animacion/LEEME-ANIMACION.txt). Ejecuta el renderer desde la raíz del repositorio, conservando esta estructura de carpetas. Para regenerar el catálogo se necesita Python con Pillow; para las previews también FFmpeg.

Se conservan tanto los renders editables como su copia dentro de la app para poder compilar sin ejecutar herramientas de diseño. No se suben ZIP duplicados, entornos virtuales, claves ni archivos de estado local de Xcode.

## Estado real de la demo

La entrega de GitHub incluye una instantánea posterior a la grabación: añade `SimuladorLocal`/`SimuladorView`, ajustes de Inicio y del chat, y el reproductor con UIKit y reutilización de imágenes idénticas. Los hashes de los archivos activos están en [ukku-ios-snapshot.json](ukku-ios-snapshot.json). El informe y el video anteriores documentan los flujos de la versión grabada, sin afirmar que estas incorporaciones posteriores estén probadas de extremo a extremo.

La instantánea incluida volvió a compilar correctamente desde esta copia con `xcodebuild`, destino genérico iOS Simulator y firma desactivada (`BUILD SUCCEEDED`). Se validaron también los siete clips y enlaces del catálogo, los hashes de la instantánea, la sintaxis de los scripts y la ausencia de claves reconocibles o archivos mayores de 100 MiB en la entrega.

Verificado en iPhone 17 Pro/iOS 26.5: compilación, saludo y transición a Inicio, parpadeo, cuatro pestañas, propuesta guiada, creación local de un plan, celebración y ajuste de movimiento reducido de la app. La [grabación real](../UkkuApp/evidencias-premium/video-ukku-premium.mp4) dura unos 27 segundos.

La IA real requiere una credencial de API en el backend; la suscripción de Claude utilizada para desarrollar la app no conecta el chat embebido. El cálculo de la app es una demo local y todavía no consulta el servicio del equipo. Ninguna acción mueve dinero real. Las pruebas no realizadas se detallan en el informe, sin presentarlas como verificadas.

## Autoría asistida

Alberto/Afi definió el producto, aprobó el personaje y dirigió los cambios. Codex generó los recursos raster con ImageGen, compuso las animaciones por capas y preparó los entregables. Claude, usando Fable 5.2 en la sesión de desarrollo, implementó e integró la app y ejecutó las pruebas del simulador. La paleta se basó en la [referencia creativa de BBVA](https://www.bbvacreative.com/new-brand/), sin afirmar vínculo oficial con el banco.

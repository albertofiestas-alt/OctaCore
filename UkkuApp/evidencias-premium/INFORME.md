# Ukku premium: informe final

Sábado 14 de noviembre de 2026, 14:40. iPhone 17 Pro, iOS 26.5 (simulador). Compilación Debug: BUILD SUCCEEDED.

Video: `video-ukku-premium.mp4` (27 s, grabación real del simulador). Hojas de fotogramas: `video-hoja-general.png`, `video-hoja-saludo.png`, `video-hoja-celebracion.png`.

Arranque: `herramientas/compilar_y_lanzar.sh --escenario base --pestana 0`

## Qué es

- UI «Claridad azul» en las cuatro pestañas, con la lógica, los datos y las acciones anteriores intactos.
- Personaje: solo creativos de Codex. El oso quieto es el recorte de `logo-maestro.png`; los siete clips de `UkkuApp/Personaje` (saludo, reposo, reposo-bien, reposo-atento, reposo-revisar, reposo-sin-datos, celebra) se reproducen tal cual. El rig vectorial y las caras derivadas anteriores están retirados. La app no dibuja ni deforma al personaje.
- Cuatro escenas originales: planificando (chat y planes vacíos), meta-lograda (resultado sin clip o con movimiento reducido), privacidad (Ajustes), sin-movimientos (lista completa vacía).

## Verificado con los clips reales

| Prueba | Resultado | Evidencia |
|---|---|---|
| Arranque en frío -> saludo -> Inicio | Ukku levanta el sombrero, saluda, se lo vuelve a poner y funde a Inicio. Sin destello blanco al terminar | video, `video-hoja-saludo.png` |
| Parpadeo en el hero (estado «bien») | En el video, a 15 fps, hay un parpadeo de unos 0,2 s | video |
| Cuatro estados | Cada escenario carga su clip y su expresión; el estado va además en texto y símbolo | `16-estados-del-oso.png` |
| Crear plan -> celebración | Propuesta -> «Crear plan» -> la tarjeta pasa a resultado y se reproduce «celebra» una vez (visto y destellos junto al sombrero). 1 plan guardado, 1 propuesta aplicada | video, `video-hoja-celebracion.png`, 06 |
| El plan creado aparece en Actividad | Bajo «Esta semana», «4 planes al día» | video |
| Cuatro pestañas | Inicio, Plan + Ukku, Actividad, Ajustes y vuelta a Inicio | video |
| Reducir movimiento (ajuste de la app) | Inicio aparece directo, sin saludo; el oso queda quieto (6 capturas idénticas) | comparación de píxeles |
| Texto muy grande | Pie del hero y banda de IA apilados, sin recortes | 12, 13 |
| Sin datos | Una sola mascota, sin cifras | 10 |
| Importe de nueve cifras | El hero pasa a una columna | 11 |
| Colchón de S/ 200 a S/ 500 | Disponible de S/ 1,260 a S/ 960 | 15 |

## Observaciones sobre los clips (para Codex; no modifiqué ningún creativo)

- `reposo-atento` y `reposo-revisar` tienen 72 fotogramas idénticos: en esos dos estados Ukku no parpadea. `reposo`, `reposo-bien` y `reposo-sin-datos` sí (fotogramas 45 a 51) y cierran el bucle sin salto.
- `reposo-atento` y `reposo-revisar` muestran al oso de frente; el maestro y los otros reposos lo muestran de tres cuartos. Al cambiar de estado la pose cambia. Es una decisión de los creativos; la dejo anotada.
- `celebra` se ve a 56 pt en el chat: el visto y los destellos quedan pequeños. Si se quiere más presencia, puedo mostrarlo más grande.
- `saludo` viene con escala 0,65: el oso ocupa unos 312 px y la app lo amplía para igualar el tamaño del maestro, así que en la bienvenida se ve algo menos nítido que el PNG quieto.
- Los clips pesan 90 MB en total dentro del bundle.

## No probado

- IA real: sigue sin credencial. No se afirma conexión.
- Reducir movimiento del sistema (iOS) con la UI nueva; se probó el ajuste de la app. Con movimiento reducido no se probó crear un plan.
- Que la bienvenida no se repita al volver de segundo plano: está implementado (una vez por proceso), no lo comprobé en pantalla. Al cambiar de pestaña no reapareció en el video.
- Hojas «Ver cálculo», «Ver más», «Cómo funciona», Presupuestos y Opciones de demostración; lista completa de movimientos vacía.
- Editar, reanudar, reprogramar y eliminar planes; aportes; vencimientos; notificaciones; Ocultar importes con la UI nueva; VoiceOver.
- El video de YouTube de referencia no se vio.

## Notas

- Capturas 01 a 15: UI premium. 08, 09 y 10 muestran el estado correcto; las expresiones de cada estado con clip están en la 16. La 07 es de las 14:25.
- Estado final: app abierta en Inicio con el escenario base.

# Reporte de calidad de los datos sinteticos

Generado con semilla 20261114, version 1.1, hash 736316b2c4ad9b5c (verdad de eventos: hash 04a07cae737c1505).

## Resultado de las comprobaciones

- Todas las comprobaciones pasan (contrato, ids unicos, signos, diciembre en los meses 12 y 24, duplicados con original, PII solo en las filas declaradas en verdad_eventos.csv).

## Antes (v1.0) y despues (v1.1): las 400 personas

El usuario objetivo vive al dia y sin colchon: el saldo debe rondar valores bajos, subir al cobrar y bajar antes del siguiente ingreso, sin tendencia creciente. Las referencias externas son orientativas, no objetivos.

| Medida | v1.0 | v1.1 | Que se espera |
|---|---|---|---|
| Saldo mediano a fin del mes 1 | S/1,118 | S/801 |  |
| Saldo mediano a fin del mes 6 | S/2,389 | S/782 |  |
| Saldo mediano a fin del mes 12 | S/4,200 | S/860 |  |
| Saldo mediano a fin del mes 18 | S/5,988 | S/796 |  |
| Saldo mediano a fin del mes 24 | S/7,804 | S/916 | sin tendencia creciente |
| Saldo mediano en dias de ingreso tipico | 65.2 | 7.7 | bajo (pocos dias) |
| Correlacion semanal ingreso vs gasto discrecional (mediana por persona) | 0.02 | 0.45 | claramente positiva |
| % de personas con saldo negativo al menos una vez tras un pago con fecha | 43.8 % | 83 % | mayor que 0: es el evento que el producto intenta evitar |
| % de pagos con fecha que dejan el saldo negativo (media por persona) | 5.5 % | 13.5 % |  |
| % de filas con saldo negativo (media por persona) | 4.9 % | 10.1 % |  |
| Ingreso mensual medio | S/1,944 | S/1,944 | referencia INEI S/1,887 [por verificar en su fuente] |
| % de personas con algun mes en deficit (ano 2) | 81 % | 100 % | referencia SBS 85 % [por verificar en su fuente] |
| % de ingresos a las 20:00 | 100 % | 3.3 % | bajo: horas repartidas segun el arquetipo |
| Filas con PII en comercio | 0 | 2324 | ~0.5 % de las filas, todas ficticias |

Muestra publicada (las mismas 20 personas): saldo mediano a fin de mes, v1.0 -> v1.1: mes 1: S/1,374 -> S/817; mes 6: S/2,646 -> S/901; mes 12: S/4,919 -> S/1,053; mes 18: S/6,959 -> S/831; mes 24: S/8,794 -> S/928.

## Por arquetipo (v1.1; entre parentesis la v1.0)

| Arquetipo | Personas | Saldo mediano fin de mes 1 / 6 / 12 / 18 / 24 | Dias de ingreso | Corr. ingreso-gasto | % personas con saldo negativo tras un pago | Ingreso mensual medio | % con mes en deficit (ano 2) | Hora mediana del ingreso |
|---|---|---|---|---|---|---|---|---|
| conductor | 86 | S/770 / S/748 / S/857 / S/784 / S/901 (S/1,055 / S/2,043 / S/4,103 / S/5,369 / S/7,492) | 8.3 (63.1) | 0.46 (0.05) |70.9 % (27.9 %) | S/1,988 (S/1,988) | 100 % (72.1 %) | 14 h (20 h) |
| vendedora | 111 | S/767 / S/757 / S/874 / S/766 / S/883 (S/1,133 / S/2,648 / S/4,703 / S/6,536 / S/8,517) | 7.6 (65.5) | 0.52 (0.04) |72.1 % (21.6 %) | S/2,083 (S/2,083) | 100 % (80.2 %) | 13 h (20 h) |
| tecnico | 83 | S/793 / S/740 / S/693 / S/683 / S/649 (S/1,083 / S/2,677 / S/3,538 / S/5,931 / S/6,808) | 6.9 (60.8) | 0.36 (-0.03) |98.8 % (73.5 %) | S/1,986 (S/1,986) | 100 % (100 %) | 13 h (20 h) |
| comisionista | 79 | S/755 / S/647 / S/609 / S/741 / S/758 (S/1,121 / S/2,286 / S/3,214 / S/4,352 / S/6,244) | 6.6 (56) | 0.57 (-0.04) |97.5 % (59.5 %) | S/1,653 (S/1,653) | 100 % (91.1 %) | 13 h (20 h) |
| asalariado | 41 | S/929 / S/1,115 / S/1,430 / S/1,082 / S/1,402 (S/1,217 / S/2,216 / S/7,170 / S/8,211 / S/13,238) | 8.7 (102.8) | 0.29 (0.03) |78 % (46.3 %) | S/1,954 (S/1,954) | 100 % (43.9 %) | 8 h (20 h) |

## Hora de los ingresos (% de los ingresos)

| Franja | v1.0 | v1.1 |
|---|---|---|
| 0-5 h | 0 % | 0 % |
| 6-9 h | 0 % | 22.3 % |
| 10-13 h | 0 % | 28.1 % |
| 14-17 h | 0 % | 28 % |
| 18-21 h | 100 % | 19.6 % |
| 22-23 h | 0 % | 2 % |

Ventas y viajes repartidos en el dia; sueldos en la manana; comisiones y honorarios en horario de oficina (config/datos.yaml: horas_ingreso).

## PII ficticia inyectada

- 2324 filas (0.50 %): dni 945, telefono 915, correo 464.
- Va dentro del texto de comercio, nunca en pagos con fecha ni en pares original-duplicado. DNI y telefono son numeros al azar sin vinculo con nadie; los correos usan un dominio reservado que no existe.
- La verdad (que fila y que patron) esta en data/generado/verdad_eventos.csv, junto con los pagos con fecha que dejan el saldo negativo. Ese archivo solo lo usa la evaluacion.

## Escenarios dificiles y medidas generales

- Personas: 400; filas: 464948; periodo: 2025-01-01 a 2026-12-31
- Ingreso mensual medio por persona: S/1944.1 (mediana S/1882.5); razon contra la cifra de referencia del INEI (S/1887, por verificar en su fuente): 1.03
- Duplicados exactos: 6871; atipicos: 2290; suscripciones cobradas dos veces: 17; sin categoria: 4649; sin comercio: 4649
- Personas que cambian de arquetipo al iniciar el ano 2: 45

Generador perturbado (volatilidad x1.5, ingreso x0.8, otra mezcla): semilla 20262114, hash 12bab9fb3feb1a2c, filas 412843.

## Como se calibro

Todos los parametros nuevos estan en config/datos.yaml y son [SUPUESTO]. Se ajustaron solo con las medidas de este reporte (saldo, dias de ingreso, correlacion, horas, referencias INEI y SBS); nunca mirando resultados del modelo ni de las reglas, porque eso seria fabricar evidencia a favor del modelo.

Los datos son ficticios y demuestran el metodo, no la precision en el mundo real.

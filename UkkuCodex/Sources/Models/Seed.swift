import Foundation

/// Datos sintéticos de demostración. Ningún dato real.
enum Seed {
    static let categorias: [Categoria] = [
        .init(id: "housing", nombre: "Vivienda", icono: "house"),
        .init(id: "utilities", nombre: "Servicios", icono: "bolt"),
        .init(id: "groceries", nombre: "Mercado", icono: "cart"),
        .init(id: "restaurants", nombre: "Restaurantes", icono: "fork.knife"),
        .init(id: "transport", nombre: "Transporte", icono: "bus"),
        .init(id: "subscriptions", nombre: "Suscripciones", icono: "repeat.circle"),
        .init(id: "health", nombre: "Salud", icono: "cross.case"),
        .init(id: "shopping", nombre: "Compras", icono: "bag"),
        .init(id: "savings", nombre: "Ahorro", icono: "banknote"),
        .init(id: "income", nombre: "Ingresos", icono: "arrow.down.circle"),
        .init(id: "other", nombre: "Otros", icono: "circle.grid.2x2"),
    ]

    static func estado(_ escenario: Escenario, hoy: Date, ajustes: Ajustes = Ajustes()) -> Estado {
        var e = Estado()
        e.escenario = escenario
        e.ajustes = ajustes
        e.categorias = categorias
        guard escenario != .vacio else { return e }

        func dia(_ d: Int) -> Date { Fechas.cal.date(byAdding: .day, value: d, to: Fechas.inicioDia(hoy))! }
        let ciclo = Calculo.ciclo(hoy: hoy, dia: e.ajustes.cicloDia)

        // El saldo ya incluye todos los movimientos pasados de la lista.
        let saldo: Centimos = switch escenario {
        case .depende: 60_000
        case .revisar: 50_000
        default: 240_000
        }
        e.cuentas = [Cuenta(id: "demo-principal", nombre: "Cuenta demo", saldoMinor: saldo)]

        let movs: [(Int, Centimos, String, String)] = [
            (-12, 320_000, "income", "Pago de cliente"),
            (-9, -9_500, "utilities", "Recibo de luz"),
            (-8, -8_900, "utilities", "Internet del hogar"),
            (-7, -4_500, "utilities", "Plan de celular"),
            (-6, -18_050, "groceries", "Mercado de la semana"),
            (-5, -3_490, "subscriptions", "Streaming de series"),
            (-4, -2_290, "subscriptions", "Música en línea"),
            (-3, -2_990, "subscriptions", "Almacenamiento en la nube"),
            (-2, -6_400, "restaurants", "Almuerzo con amigos"),
            (-1, -1_800, "transport", "Pasajes"),
            (-1, -4_200, "restaurants", "Cena"),
        ]
        e.movimientos = movs.map { Movimiento(cuentaId: "demo-principal", montoMinor: $0.1, categoriaId: $0.2, fecha: dia($0.0), comercio: $0.3) }

        e.pagos = [
            PagoConFecha(nombre: "Luz", montoMinor: 9_500, fecha: dia(-9), categoriaId: "utilities", pagado: true),
            PagoConFecha(nombre: "Internet", montoMinor: 8_900, fecha: dia(-8), categoriaId: "utilities", pagado: true),
            PagoConFecha(nombre: "Celular", montoMinor: 4_500, fecha: dia(-7), categoriaId: "utilities", pagado: true),
            PagoConFecha(nombre: "Alquiler", montoMinor: 70_000, fecha: dia(escenario == .revisar ? 2 : 6), categoriaId: "housing"),
        ]
        if escenario == .depende {
            e.ingresos = [IngresoEsperado(nombre: "Pago de cliente por confirmar", montoMinor: 90_000, fecha: dia(3), confirmado: false)]
        }

        let meta = Meta(titulo: "Fondo de emergencia", objetivoMinor: 100_000, ahorradoMinor: 24_000, fechaObjetivo: dia(90))
        e.metas = [meta]
        let pres = [
            Presupuesto(categoriaId: "restaurants", limiteMinor: 25_000, cicloId: ciclo.id),
            Presupuesto(categoriaId: "subscriptions", limiteMinor: 10_000, cicloId: ciclo.id),
        ]
        e.presupuestos = pres
        e.planes = [
            Plan(tipo: .meta, titulo: meta.titulo, importeMinor: meta.objetivoMinor, fecha: meta.fechaObjetivo, categoriaId: "savings",
                 origen: .usuario, estado: .enCurso, refId: meta.id, creado: dia(-12), esDemo: true),
            Plan(tipo: .presupuesto, titulo: "Presupuesto de Restaurantes", importeMinor: 25_000, fecha: ciclo.fin, periodicidad: .monthly,
                 categoriaId: "restaurants", origen: .usuario, estado: .enCurso, refId: pres[0].id, creado: dia(-12), esDemo: true),
            Plan(tipo: .presupuesto, titulo: "Presupuesto de Suscripciones", importeMinor: 10_000, fecha: ciclo.fin, periodicidad: .monthly,
                 categoriaId: "subscriptions", origen: .usuario, estado: .enCurso, refId: pres[1].id, creado: dia(-12), esDemo: true),
        ]
        return e
    }
}

import Foundation

enum UkkuMood: String { case bien, atento, revisar, sinDatos }

@main struct DominioTests {
    static func main() throws {
        let hoy = Fechas.deIso("2026-11-14")!
        let base = Seed.estado(.base, hoy: hoy)
        let encoder = JSONEncoder(); encoder.outputFormatting = .sortedKeys
        let original = try encoder.encode(base)
        let normal = SimuladorLocal.evaluar(.init(gasto: 10_000), estado: base, hoy: hoy)!
        precondition(normal.antes.disponible == 126_000 && normal.despues.disponible == 116_000)
        precondition(normal.antes.sugerenciaHoy == 9_000 && normal.despues.sugerenciaHoy == 8_200)
        precondition(normal.despues.reservas == 24_000 && normal.despues.colchon == 20_000)
        let alto = SimuladorLocal.evaluar(.init(gasto: 150_000), estado: base, hoy: hoy)!
        precondition(alto.despues.faltante == 24_000 && alto.despues.mood == .revisar)
        let vacio = SimuladorLocal.evaluar(.init(), estado: base, hoy: hoy)!
        precondition(vacio.antes.disponible == vacio.despues.disponible)
        precondition(vacio.dias.allSatisfy { $0.antes == $0.despues })
        precondition(SimuladorLocal.evaluar(.init(gasto: -1), estado: base, hoy: hoy) == nil)
        precondition(SimuladorLocal.evaluar(.init(gasto: 1_000_001), estado: base, hoy: hoy) == nil)
        for dia in [-1, 15] {
            precondition(SimuladorLocal.evaluar(.init(ingresos: [.init(monto: 100, dia: dia)]), estado: base, hoy: hoy) == nil)
        }
        precondition(SimuladorLocal.evaluar(.init(ingresos: Array(repeating: .init(monto: 100, dia: 1), count: 4)), estado: base, hoy: hoy) == nil)
        precondition(SimuladorLocal.evaluar(.init(), estado: Seed.estado(.vacio, hoy: hoy), hoy: hoy) == nil)
        let revisar = Seed.estado(.revisar, hoy: hoy)
        let temprano = SimuladorLocal.evaluar(.init(ingresos: [.init(monto: 100_000, dia: 1)]), estado: revisar, hoy: hoy)!
        let tarde = SimuladorLocal.evaluar(.init(ingresos: [.init(monto: 100_000, dia: 10)]), estado: revisar, hoy: hoy)!
        precondition(temprano.despues.mood == .bien)
        precondition(tarde.despues.mood == .revisar && tarde.despues.disponible > 0)
        precondition(tarde.dias[2].despues < 0 && tarde.dias[10].despues > 0)
        let cierre = Fechas.deIso("2026-11-28")!
        let finMes = Seed.estado(.base, hoy: cierre)
        let cruce = SimuladorLocal.evaluar(.init(gasto: 150_000), estado: finMes, hoy: cierre)!
        precondition(cruce.despues.mood == .revisar, "Los pagos de diciembre cuentan en los próximos 14 días")
        precondition(cruce.despues.sugerenciaHoy == 0)
        let originalDespues = try encoder.encode(base)
        precondition(originalDespues == original, "Simular no escribe en el estado original")

        let pago = base.pagos.first { !$0.pagado }!
        let proposal = PropuestaAccion(tool: "record_demo_transaction", arguments: [
            "account_id": .s(base.cuentas[0].id), "amount_minor_signed": .i(-pago.montoMinor), "currency": .s("PEN"),
            "category_id": .s(pago.categoriaId), "date": .s(Fechas.iso(hoy)), "merchant": .s("Alquiler")
        ], source: .manual, contextVersion: base.contextVersion)
        let preview = try Acciones.previsualizar(proposal, base, hoy: hoy, pagoID: pago.id)
        precondition(preview.lineas.first { $0.etiqueta == "Disponible del mes" }?.antes == preview.lineas.first { $0.etiqueta == "Disponible del mes" }?.despues,
                     "Registrar un pago previsto no debe descontarlo dos veces")
        var copia = base
        let result = try Acciones.aplicar(proposal, en: &copia, hoy: hoy)
        try RegistroPago.vincular(resultado: result, pagoID: pago.id, en: &copia)
        precondition(copia.pagos.first { $0.id == pago.id }!.pagado)
        precondition(copia.movimientos.last!.pagoId == pago.id)
        precondition(Calculo.resumen(copia, hoy: hoy).disponible == 126_000)
        var conReserva = base
        conReserva.planes.append(Plan(tipo: .reserva, titulo: "Reserva ampliada", importeMinor: 100_000, fecha: pago.fecha,
            categoriaId: pago.categoriaId, origen: .usuario, estado: .programado, pagoId: pago.id, reservadoMinor: 100_000, creado: hoy))
        precondition(Calculo.reservas(conReserva) == 54_000, "El excedente sobre un pago también debe reservarse")
        do {
            try RegistroPago.vincular(resultado: result, pagoID: pago.id, en: &copia)
            preconditionFailure("Un pago realizado no se puede registrar dos veces")
        } catch is ErrorAccion {}
        var invalida = proposal; invalida.arguments["amount_minor_signed"] = .i(Int.min)
        do { try Acciones.validar(invalida, base, hoy: hoy); preconditionFailure("Debe rechazar el desbordamiento") } catch is ErrorAccion {}
        precondition(Dinero.parse("25,50") == 2550 && Dinero.parse("25.500") == nil)
        var ajustes = Ajustes(); ajustes.colchonMinor = 45_000
        precondition(Seed.estado(.base, hoy: hoy, ajustes: ajustes).ajustes.colchonMinor == 45_000)
        print("OK: gastos, ingresos por fecha, límites, inmutabilidad, cruce de mes, reservas y excedentes, registro de pagos y validación.")
    }
}

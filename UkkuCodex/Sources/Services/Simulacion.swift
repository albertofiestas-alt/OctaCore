import Foundation

struct IngresoHipotetico: Identifiable, Equatable {
    var id = UUID()
    var monto: Centimos
    var dia: Int
}

struct EscenarioHipotetico {
    var gasto: Centimos = 0
    var ingresos: [IngresoHipotetico] = []
}

struct DiaSimulado: Identifiable {
    var dia: Int
    var antes: Centimos
    var despues: Centimos
    var id: Int { dia }
}

struct ResultadoSimulacion {
    var antes: Resumen
    var despues: Resumen
    var dias: [DiaSimulado]
    var escenario: EscenarioHipotetico
    var cambiaCobertura: Bool { !despues.pagosSinCubrir.isEmpty }
}

enum SimuladorLocal {
    /// Límites del contrato del equipo: gasto <= S/ 10 000, hasta tres ingresos y días 0...14.
    static func evaluar(_ escenario: EscenarioHipotetico, estado: Estado, hoy: Date) -> ResultadoSimulacion? {
        guard (0...1_000_000).contains(escenario.gasto), escenario.ingresos.count <= 3,
              escenario.ingresos.allSatisfy({ (1...1_000_000).contains($0.monto) && (0...14).contains($0.dia) }),
              !estado.cuentas.isEmpty else { return nil }
        let antes = Calculo.resumen(estado, hoy: hoy)
        guard antes.hayDatos else { return nil }
        var copia = estado
        copia.cuentas[0].saldoMinor -= escenario.gasto
        for ingreso in escenario.ingresos {
            copia.ingresos.append(IngresoEsperado(nombre: "Ingreso hipotético", montoMinor: ingreso.monto,
                fecha: Fechas.cal.date(byAdding: .day, value: ingreso.dia, to: Fechas.inicioDia(hoy))!, confirmado: true))
        }
        let dias = (0...14).map { dia in
            DiaSimulado(dia: dia, antes: margen(estado, dia: dia, hoy: hoy), despues: margen(copia, dia: dia, hoy: hoy))
        }
        return ResultadoSimulacion(antes: antes, despues: Calculo.resumen(copia, hoy: hoy), dias: dias, escenario: escenario)
    }

    private static func margen(_ estado: Estado, dia: Int, hoy: Date) -> Centimos {
        let inicio = Fechas.inicioDia(hoy)
        let fecha = Fechas.cal.date(byAdding: .day, value: dia, to: inicio)!
        let saldo = estado.cuentas.reduce(0) { $0 + $1.saldoMinor }
        let ingresos = estado.ingresos.filter { $0.confirmado && $0.fecha >= inicio && $0.fecha <= fecha }.reduce(0) { $0 + $1.montoMinor }
        let pagos = estado.pagos.filter { !$0.pagado && $0.fecha <= fecha }.reduce(0) { $0 + $1.montoMinor }
        return saldo + ingresos - pagos - Calculo.reservas(estado) - estado.ajustes.colchonMinor
    }
}

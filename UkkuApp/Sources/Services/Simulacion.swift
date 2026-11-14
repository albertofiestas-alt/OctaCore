import Foundation

/// Punto de sustitución del motor: una simulación nunca escribe sobre el estado original.
struct ImpactoSimulado {
    let antes: Resumen
    let despues: Resumen
    let gasto: Centimos
    var superaDisponible: Bool { gasto > antes.disponible }
    var afectaPagos: Bool { despues.pagosSinCubrir.count > antes.pagosSinCubrir.count }
}

enum SimuladorLocal {
    static func gasto(_ monto: Centimos, estado: Estado, hoy: Date) -> ImpactoSimulado? {
        guard monto > 0, monto < 10_000_000_000, !estado.cuentas.isEmpty else { return nil }
        let antes = Calculo.resumen(estado, hoy: hoy)
        guard antes.hayDatos else { return nil }
        var copia = estado
        copia.cuentas[0].saldoMinor -= monto
        return ImpactoSimulado(antes: antes, despues: Calculo.resumen(copia, hoy: hoy), gasto: monto)
    }
}

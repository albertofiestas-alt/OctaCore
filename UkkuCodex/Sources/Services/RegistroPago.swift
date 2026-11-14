import Foundation

/// Se ejecuta sobre la misma copia que el movimiento, antes de persistir una sola vez.
enum RegistroPago {
    static func vincular(resultado: ResultadoAccion, pagoID: UUID, en estado: inout Estado) throws {
        guard let p = estado.pagos.firstIndex(where: { $0.id == pagoID }), !estado.pagos[p].pagado,
              let m = estado.movimientos.firstIndex(where: { $0.id.uuidString == resultado.entityId }),
              estado.movimientos[m].montoMinor == -estado.pagos[p].montoMinor,
              estado.movimientos[m].categoriaId == estado.pagos[p].categoriaId else {
            throw ErrorAccion(mensaje: "El pago cambió. Revisa el importe y vuelve a intentarlo.")
        }
        estado.movimientos[m].pagoId = pagoID
        estado.pagos[p].pagado = true
    }
}

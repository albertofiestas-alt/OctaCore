import SwiftUI

/// Un solo lenguaje de iconos nativos para mantener nitidez y consistencia.
enum UkkuIcon: String {
    case inicio = "house.fill"
    case plan = "sparkles"
    case actividad = "checklist"
    case ajustes = "person.crop.circle"
    case transacciones = "arrow.left.arrow.right"
    case suscripciones = "repeat.circle"
    case meta = "target"
    case ahorro = "banknote"
    case calendario = "calendar"
    case logro = "rosette"
    case agregar = "plus"
    case enviar = "arrow.up"
    case pausar = "pause.circle"
    case reanudar = "play.circle"
    case detalle = "chevron.right"
    case cubierto = "checkmark.circle.fill"
    case condicionado = "exclamationmark.circle.fill"
    case revisar = "exclamationmark.triangle.fill"
    case privacidad = "lock.shield"
    case notificaciones = "bell"
    case comida = "fork.knife"
    case transporte = "bus"
    case servicios = "bolt"
    case compras = "bag"
    case salud = "cross.case"
}

struct UkkuIconView: View {
    let icon: UkkuIcon
    var body: some View {
        Image(systemName: icon.rawValue)
            .font(.body.weight(.medium))
            .symbolRenderingMode(.hierarchical)
            .accessibilityHidden(true)
    }
}

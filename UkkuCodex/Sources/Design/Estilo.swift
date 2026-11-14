import SwiftUI

extension Color {
    static let ukkuAzul = Color(red: 0, green: 19 / 255, blue: 145 / 255)
    static let ukkuCeleste = Color(red: 133 / 255, green: 200 / 255, blue: 1)
    static let tinta = Color(red: 11 / 255, green: 25 / 255, blue: 52 / 255)
    static let secundaria = Color(red: 93 / 255, green: 109 / 255, blue: 133 / 255)
    static let fondo = Color(red: 245 / 255, green: 247 / 255, blue: 252 / 255)
    static let borde = Color(red: 229 / 255, green: 235 / 255, blue: 245 / 255)
    static let verde = Color(red: 23 / 255, green: 114 / 255, blue: 75 / 255)
    static let ambar = Color(red: 143 / 255, green: 83 / 255, blue: 0)
    static let rojo = Color(red: 178 / 255, green: 44 / 255, blue: 53 / 255)
}

extension EnvironmentValues { @Entry var ukkuQuieto = false }

extension UkkuMood {
    var color: Color {
        switch self { case .bien: .verde; case .atento: .ambar; case .revisar: .rojo; case .sinDatos: .secundaria }
    }
    var icono: String {
        switch self { case .bien: "checkmark.shield.fill"; case .atento: "clock.badge.exclamationmark"; case .revisar: "exclamationmark.triangle.fill"; case .sinDatos: "tray" }
    }
    var corto: String {
        switch self { case .bien: "Pagos cubiertos"; case .atento: "Un ingreso por confirmar"; case .revisar: "Hay pagos por revisar"; case .sinDatos: "Empecemos con un ejemplo" }
    }
}

struct PressStyle: ButtonStyle {
    @Environment(\.ukkuQuieto) private var quieto
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .contentShape(Rectangle())
            .opacity(configuration.isPressed ? 0.75 : 1)
            .scaleEffect(configuration.isPressed && !quieto ? 0.98 : 1)
            .animation(quieto ? nil : .easeOut(duration: 0.16), value: configuration.isPressed)
    }
}

struct BotonEnlace: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(.headline).foregroundStyle(Color.ukkuAzul)
            .frame(minHeight: 44).opacity(configuration.isPressed ? 0.6 : 1)
    }
}

struct PrimaryButton: View {
    let title: String
    var icon = "arrow.right"
    var inverse = false
    var action: () -> Void
    var body: some View {
        Button(action: action) {
            HStack {
                Text(title).fixedSize(horizontal: false, vertical: true)
                Spacer(minLength: 8)
                Image(systemName: icon).accessibilityHidden(true)
            }
            .font(.headline)
            .padding(.horizontal, 20).padding(.vertical, 17)
            .frame(maxWidth: .infinity, minHeight: 54)
            .foregroundStyle(inverse ? Color.ukkuAzul : .white)
            .background(inverse ? .white : Color.ukkuAzul, in: .rect(cornerRadius: 18))
            .contentShape(.rect)
        }.buttonStyle(PressStyle())
    }
}

struct Paper<Content: View>: View {
    var color: Color = .white
    var padding: CGFloat = 20
    @ViewBuilder var content: Content
    var body: some View {
        content.padding(padding).frame(maxWidth: .infinity, alignment: .leading)
            .background(color, in: .rect(cornerRadius: 24))
    }
}

struct Eyebrow: View {
    let text: String
    var color: Color = .secundaria
    var body: some View {
        Text(text.uppercased()).font(.caption.weight(.bold)).tracking(1.4).foregroundStyle(color)
    }
}

struct PageTitle: View {
    let title: String
    let subtitle: String
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title).font(.largeTitle.weight(.bold)).tracking(-0.8).foregroundStyle(Color.tinta).accessibilityAddTraits(.isHeader)
            Text(subtitle).font(.subheadline).foregroundStyle(Color.secundaria).fixedSize(horizontal: false, vertical: true)
        }
    }
}

struct SectionHeading: View {
    let title: String
    var action: String?
    var onAction: (() -> Void)?
    var body: some View {
        HStack {
            Text(title).font(.title3.bold()).foregroundStyle(Color.tinta).accessibilityAddTraits(.isHeader)
            Spacer(minLength: 8)
            if let action, let onAction { Button(action, action: onAction).font(.subheadline.weight(.semibold)).frame(minHeight: 44) }
        }
    }
}

struct Glyph: View {
    let name: String
    var color: Color = .ukkuAzul
    var body: some View {
        Image(systemName: name).font(.system(size: 20, weight: .semibold))
            .foregroundStyle(color).frame(width: 46, height: 46)
            .background(color.opacity(0.07), in: .rect(cornerRadius: 15)).accessibilityHidden(true)
    }
}

struct StatusPill: View {
    let mood: UkkuMood
    var body: some View {
        Label(mood.corto, systemImage: mood.icono).font(.caption.weight(.semibold))
            .foregroundStyle(mood.color).padding(.horizontal, 12).padding(.vertical, 8)
            .background(mood.color.opacity(0.08), in: .capsule)
    }
}

struct DemoFootnote: View {
    var body: some View {
        Label("Datos ficticios · Tú decides cada paso", systemImage: "lock.shield")
            .font(.caption).foregroundStyle(Color.secundaria)
            .frame(maxWidth: .infinity).padding(.vertical, 8)
    }
}

struct MoneyText: View {
    @Environment(AppStore.self) private var store
    let value: Centimos
    var body: some View {
        Text(store.importe(value, decimales: false)).monospacedDigit().contentTransition(.numericText())
    }
}

struct EmptyState: View {
    let title: String
    let detail: String
    var scene: EscenaUkku.Escena = .sinMovimientos
    var body: some View {
        VStack(spacing: 12) {
            EscenaUkku(escena: scene, size: 160)
            Text(title).font(.title3.bold()).foregroundStyle(Color.tinta)
            Text(detail).font(.subheadline).foregroundStyle(Color.secundaria).multilineTextAlignment(.center)
        }.frame(maxWidth: .infinity).padding(.vertical, 20)
    }
}

struct ErrorNotice: View {
    let text: String
    var body: some View {
        Label(text, systemImage: "exclamationmark.circle.fill").font(.subheadline)
            .foregroundStyle(Color.rojo).fixedSize(horizontal: false, vertical: true)
    }
}

import SwiftUI

// Sistema visual «Claridad azul»: una escena con Ukku, el resto en silencio.

extension Color {
    static let ukkuAzul = Color(red: 0, green: 0x13 / 255, blue: 0x91 / 255)
    static let ukkuCeleste = Color(red: 0x85 / 255, green: 0xC8 / 255, blue: 1)
    static let ukkuTinta = Color(red: 0, green: 0x05 / 255, blue: 0x19 / 255)
    static let ukkuSuperficie = Color(red: 0xF5 / 255, green: 0xF7 / 255, blue: 0xFB / 255)
    static let ukkuDivisor = Color(red: 0xE7 / 255, green: 0xEC / 255, blue: 0xF4 / 255)
    static let ukkuSecundario = Color(red: 0x66 / 255, green: 0x70 / 255, blue: 0x85 / 255)
    // Semáforo: solo en la etiqueta de estado, con contraste >= 4.5:1.
    static let ukkuVerde = Color(red: 0x1B / 255, green: 0x7F / 255, blue: 0x3B / 255)
    static let ukkuAmbar = Color(red: 0x8A / 255, green: 0x5A / 255, blue: 0)
    static let ukkuRojo = Color(red: 0xB3 / 255, green: 0x26 / 255, blue: 0x1E / 255)
}

/// Escala tipográfica con Dynamic Type: título 28, sección 17, cuerpo 16, metadato 13.
extension Font {
    static let ukTitulo = Font.title.weight(.semibold)
    static let ukSeccion = Font.headline
    static let ukCuerpo = Font.callout
    static let ukCuerpoFuerte = Font.callout.weight(.semibold)
    static let ukMeta = Font.footnote
}

extension EnvironmentValues {
    /// Reducir movimiento del sistema o de la app. Todas las animaciones lo consultan.
    @Entry var ukkuQuieto = false
}

enum Movimiento_ {
    static let toque = Animation.easeOut(duration: 0.16)
    static let cifra = Animation.easeInOut(duration: 0.25)
    static let contenido = Animation.easeInOut(duration: 0.22)
}

extension UkkuMood {
    var estadoCorto: String {
        switch self {
        case .bien: "Pagos cubiertos"
        case .atento: "Depende de próximos ingresos"
        case .revisar: "Revisa estos pagos"
        case .sinDatos: "Faltan datos para evaluar"
        }
    }
    var simbolo: String {
        switch self {
        case .bien: UkkuIcon.cubierto.rawValue
        case .atento: UkkuIcon.condicionado.rawValue
        case .revisar: UkkuIcon.revisar.rawValue
        case .sinDatos: "questionmark.circle.fill"
        }
    }
    var colorTexto: Color {
        switch self {
        case .bien: .ukkuVerde
        case .atento: .ukkuAmbar
        case .revisar: .ukkuRojo
        case .sinDatos: .ukkuSecundario
        }
    }
}

extension EstadoPlan {
    var color: Color {
        switch self {
        case .completado: .ukkuVerde
        case .necesitaConfirmacion: .ukkuAmbar
        case .error: .ukkuRojo
        default: .ukkuSecundario
        }
    }
}

/// Compresión breve al tocar (0.98, ~160 ms). Sin rebote.
private struct Presion: ViewModifier {
    @Environment(\.ukkuQuieto) private var quieto
    let presionado: Bool
    func body(content: Content) -> some View {
        content
            .scaleEffect(presionado && !quieto ? 0.98 : 1)
            .opacity(presionado ? 0.85 : 1)
            .animation(quieto ? nil : Movimiento_.toque, value: presionado)
    }
}

/// El único botón relleno de cada pantalla.
struct BotonPrincipal: ButtonStyle {
    @Environment(\.isEnabled) private var activo
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.ukCuerpoFuerte)
            .frame(maxWidth: .infinity, minHeight: 48)
            .padding(.horizontal, 16)
            .background(Color.ukkuAzul.opacity(activo ? 1 : 0.3), in: .rect(cornerRadius: 14))
            .foregroundStyle(.white)
            .modifier(Presion(presionado: configuration.isPressed))
    }
}

/// Acción secundaria: enlace discreto con área táctil de 44 pt.
struct BotonEnlace: ButtonStyle {
    @Environment(\.isEnabled) private var activo
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.ukCuerpoFuerte)
            .foregroundStyle(Color.ukkuAzul.opacity(activo ? 1 : 0.35))
            .frame(minHeight: 44)
            .contentShape(.rect)
            .modifier(Presion(presionado: configuration.isPressed))
    }
}

/// Se conserva para hojas secundarias: borde fino, sin relleno.
struct BotonSecundario: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.ukCuerpoFuerte)
            .frame(maxWidth: .infinity, minHeight: 48)
            .padding(.horizontal, 16)
            .foregroundStyle(Color.ukkuAzul)
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(Color.ukkuDivisor, lineWidth: 1))
            .contentShape(.rect)
            .modifier(Presion(presionado: configuration.isPressed))
    }
}

struct FilaPresionable: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.contentShape(.rect).modifier(Presion(presionado: configuration.isPressed))
    }
}

struct Separador: View {
    var body: some View { Rectangle().fill(Color.ukkuDivisor).frame(height: 1) }
}

/// Cabecera de pantalla: título 28 semibold, subtítulo opcional y una acción a la derecha.
struct Cabecera<Accion: View>: View {
    let titulo: String
    var subtitulo: String?
    @ViewBuilder var accion: Accion
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(alignment: .leading, spacing: 2) {
                Text(titulo).font(.ukTitulo).foregroundStyle(Color.ukkuTinta).accessibilityAddTraits(.isHeader)
                if let subtitulo { Text(subtitulo).font(.ukCuerpo).foregroundStyle(Color.ukkuSecundario) }
            }
            Spacer(minLength: 8)
            accion
        }
        .padding(.top, 8)
    }
}

struct TituloSeccion<Accion: View>: View {
    let texto: String
    @ViewBuilder var accion: Accion
    var body: some View {
        HStack(alignment: .firstTextBaseline) {
            Text(texto).font(.ukSeccion).foregroundStyle(Color.ukkuTinta).accessibilityAddTraits(.isHeader)
            Spacer(minLength: 8)
            accion
        }
    }
}

extension TituloSeccion where Accion == EmptyView {
    init(texto: String) { self.init(texto: texto) { EmptyView() } }
}

struct IconoFila: View {
    let simbolo: String
    var color: Color = .ukkuAzul
    var body: some View {
        Image(systemName: simbolo)
            .font(.system(size: 19, weight: .medium))
            .foregroundStyle(color)
            .frame(width: 28)
            .accessibilityHidden(true)
    }
}

struct EtiquetaEstado: View {
    let estado: EstadoPlan
    var body: some View {
        Label(estado.nombre, systemImage: estado.icono)
            .font(.ukMeta.weight(.medium))
            .foregroundStyle(estado.color)
    }
}

struct AvisoDemo: View {
    var texto = "Datos de demostración. Ukku orienta; no ejecuta pagos ni operaciones bancarias."
    var body: some View {
        Text(texto).font(.ukMeta).foregroundStyle(Color.ukkuSecundario).frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct FilaMovimiento: View {
    @Environment(AppStore.self) private var store
    let mov: Movimiento
    var body: some View {
        let cat = store.categoria(mov.categoriaId)
        HStack(spacing: 12) {
            IconoFila(simbolo: cat.icono)
            VStack(alignment: .leading, spacing: 2) {
                Text(mov.comercio).font(.ukCuerpo).foregroundStyle(Color.ukkuTinta).lineLimit(1)
                Text("\(cat.nombre) · \(Fechas.corta(mov.fecha))").font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
            }
            Spacer(minLength: 8)
            Text(store.importe(mov.montoMinor, signo: true))
                .font(.ukCuerpo.weight(.medium).monospacedDigit())
                .foregroundStyle(mov.montoMinor > 0 ? Color.ukkuVerde : Color.ukkuTinta)
        }
        .frame(minHeight: 60)
        .accessibilityElement(children: .combine)
    }
}

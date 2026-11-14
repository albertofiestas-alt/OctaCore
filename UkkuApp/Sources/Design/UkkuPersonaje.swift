import SwiftUI
import UIKit
import CryptoKit

/// Estado del personaje. Sale del cálculo determinista; nunca del texto del chat.
enum UkkuMood: String, CaseIterable, Identifiable {
    case bien, atento, revisar, sinDatos
    var id: String { rawValue }
    var label: String {
        switch self {
        case .bien: "Pagos cubiertos"
        case .atento: "Algunos pagos dependen de próximos ingresos"
        case .revisar: "Hay pagos por revisar"
        case .sinDatos: "Faltan datos para evaluar tus pagos"
        }
    }
    var glow: Color {
        switch self {
        case .bien: Color(red: 0.15, green: 0.78, blue: 0.51)
        case .atento: Color(red: 1.0, green: 0.69, blue: 0.22)
        case .revisar: Color(red: 1.0, green: 0.31, blue: 0.36)
        case .sinDatos: Color(red: 0.52, green: 0.78, blue: 1.0)
        }
    }
    /// Clip de reposo que se busca para este estado (ver NECESIDADES-CLAUDE.txt).
    var clip: String {
        switch self {
        case .bien: "reposo-bien"
        case .atento: "reposo-atento"
        case .revisar: "reposo-revisar"
        case .sinDatos: "reposo-sin-datos"
        }
    }
}

/// Clip raster entregado por Codex: Personaje/<nombre>/manifest.json + fotogramas PNG numerados.
/// La app no dibuja ni deforma al personaje: solo reproduce estos fotogramas.
struct ClipUkku {
    let frames: [UIImage]
    let fps: Double
    let loop: Bool
    /// Escala del oso dentro del lienzo (manifest «escala»). Se compensa para igualar al PNG maestro.
    var escala: Double = 1
    var duracion: Double { Double(frames.count) / fps }

    func frame(en t: Double) -> UIImage {
        let i = Int(max(0, t) * fps)
        return frames[loop ? i % frames.count : min(i, frames.count - 1)]
    }
}

@MainActor
enum ClipsUkku {
    private static var cache: [String: ClipUkku?] = [:]

    static func cargar(_ nombre: String) -> ClipUkku? {
        if let c = cache[nombre] { return c }
        var clip: ClipUkku?
        if let dir = Bundle.main.resourceURL?.appendingPathComponent("Personaje/\(nombre)"),
           let archivos = try? FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil) {
            var unicos: [SHA256.Digest: UIImage] = [:]
            let frames = archivos.filter { $0.pathExtension.lowercased() == "png" }
                .sorted { $0.lastPathComponent < $1.lastPathComponent }
                .compactMap { url -> UIImage? in
                    guard let data = try? Data(contentsOf: url) else { return nil }
                    let hash = SHA256.hash(data: data)
                    if let imagen = unicos[hash] { return imagen }
                    guard let imagen = UIImage(data: data) else { return nil }
                    unicos[hash] = imagen
                    return imagen
                }
            let manifiesto = (try? Data(contentsOf: dir.appendingPathComponent("manifest.json")))
                .flatMap { try? JSONSerialization.jsonObject(with: $0) as? [String: Any] }
            let fps = min(max((manifiesto?["fps"] as? Double) ?? 24, 1), 60)
            let escala = min(max((manifiesto?["escala"] as? Double) ?? 1, 0.4), 1)
            if !frames.isEmpty { clip = ClipUkku(frames: frames, fps: fps, loop: (manifiesto?["loop"] as? Bool) ?? true, escala: escala) }
        }
        cache[nombre] = clip
        return clip
    }

    /// Primer clip disponible de la lista, en orden de preferencia.
    static func primero(_ nombres: [String]) -> ClipUkku? {
        for n in nombres { if let c = cargar(n) { return c } }
        return nil
    }
}

/// UIKit mantiene el reloj de reproducción fuera del árbol SwiftUI.
/// Los fotogramas repetidos comparten imagen; el último frame permanece al finalizar.
private struct LienzoClip: UIViewRepresentable {
    let clip: ClipUkku
    let activo: Bool
    func makeUIView(context: Context) -> UIImageView {
        let vista = UIImageView()
        vista.contentMode = .scaleAspectFit
        vista.isAccessibilityElement = false
        vista.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)
        vista.setContentCompressionResistancePriority(.defaultLow, for: .vertical)
        return vista
    }
    func updateUIView(_ vista: UIImageView, context: Context) {
        if vista.animationImages?.first !== clip.frames.first {
            vista.animationImages = clip.frames
            vista.animationDuration = clip.duracion
            vista.animationRepeatCount = clip.loop ? 0 : 1
            vista.image = clip.loop ? clip.frames.first : clip.frames.last
            if activo { vista.startAnimating() }
        } else if !activo {
            vista.stopAnimating()
        } else if clip.loop && !vista.isAnimating {
            vista.startAnimating()
        }
    }
    static func dismantleUIView(_ vista: UIImageView, coordinator: ()) {
        vista.stopAnimating()
        vista.animationImages = nil
    }
}

struct ReproductorClip: View {
    let clip: ClipUkku
    @Environment(\.scenePhase) private var fase
    var body: some View {
        LienzoClip(clip: clip, activo: fase == .active)
            .scaleEffect(1 / clip.escala, anchor: .bottom)
    }
}

/// Ukku en la interfaz: el PNG maestro aprobado, o el clip de reposo del estado si Codex ya lo entregó.
/// Con movimiento reducido siempre se muestra el PNG maestro quieto.
struct UkkuPersonajeView: View {
    let mood: UkkuMood
    var size: CGFloat = 108
    @Environment(\.ukkuQuieto) private var quieto
    @Environment(\.scenePhase) private var fase

    var body: some View {
        ZStack {
            Ellipse()
                .fill(RadialGradient(colors: [mood.glow.opacity(0.30), mood.glow.opacity(0.08), .clear],
                                     center: .center, startRadius: 0, endRadius: size * 0.6))
                .frame(width: size * 1.2, height: size * 1.0)
                .blur(radius: 10)
                .offset(y: size * 0.08)
                .accessibilityHidden(true)
            Circle().stroke(mood.glow.opacity(0.14), lineWidth: 1)
                .frame(width: size * 0.95, height: size * 0.95)
                .overlay(alignment: .topTrailing) {
                    Circle().fill(mood.glow.opacity(0.65)).frame(width: 5, height: 5).offset(x: -10, y: 10)
                }
                .phaseAnimator([false, true]) { halo, abierto in
                    halo.scaleEffect(quieto || fase != .active ? 1 : (abierto ? 1.06 : 0.96))
                        .opacity(abierto && !quieto ? 0.55 : 1)
                } animation: { _ in .easeInOut(duration: 2.8) }
                .accessibilityHidden(true)
            if !quieto, let clip = ClipsUkku.primero([mood.clip, "reposo"]) {
                ReproductorClip(clip: clip).frame(width: size, height: size)
            } else {
                Image("ukku-maestro").resizable().scaledToFit().frame(width: size, height: size)
            }
        }
        .frame(width: size * 1.1, height: size * 1.05)
        .animation(quieto ? nil : .easeInOut(duration: 0.28), value: mood)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Ukku: \(mood.label)")
    }
}

/// Ilustración original de Ukku para un momento concreto (vacíos, resultado, privacidad). Decorativa.
struct EscenaUkku: View {
    enum Escena: String { case metaLograda = "escena-meta-lograda", planificando = "escena-planificando", sinMovimientos = "escena-sin-movimientos", privacidad = "escena-privacidad" }
    let escena: Escena
    var size: CGFloat = 120
    var body: some View {
        Image(escena.rawValue).resizable().scaledToFit().frame(width: size, height: size).accessibilityHidden(true)
    }
}

/// Bienvenida: reproduce una vez el clip «saludo» (quitarse el sombrero, saludar, volver a ponérselo)
/// y da paso a Inicio. Si el clip no existe o hay movimiento reducido, no aparece.
struct BienvenidaView: View {
    let clip: ClipUkku
    let terminar: () -> Void

    var body: some View {
        ZStack {
            // Mismo blanco que Inicio y que la pantalla de arranque: al terminar no hay destello.
            Color.white.ignoresSafeArea()
            VStack(spacing: 16) {
                ReproductorClip(clip: clip).frame(width: 220, height: 220)
                Text("Tu plata, con un plan").font(.title3).fontDesign(.serif).foregroundStyle(Color.ukkuAzul)
            }
        }
        .overlay(alignment: .bottom) {
            Button("Empezar", action: terminar)
                .buttonStyle(BotonEnlace()).padding(.bottom, 36)
        }
        .accessibilityLabel("Ukku te saluda. Toca para continuar.")
        .task {
            do { try await Task.sleep(for: .seconds(clip.duracion + 0.2)) }
            catch { return }
            terminar()
        }
    }
}

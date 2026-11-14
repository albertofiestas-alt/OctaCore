import SwiftUI
import RiveRuntime

@MainActor private enum RiveLibrary {
    private static var loading: Task<RiveRuntime.File, Error>?
    static func file() async throws -> RiveRuntime.File {
        if let loading { return try await loading.value }
        let task = Task {
            let worker = try await Worker()
            return try await RiveRuntime.File(source: .local("ukku-original", .main), worker: worker)
        }
        loading = task
        return try await task.value
    }
}

/// Render nativo Rive con el archivo local del personaje aprobado y respaldo PNG.
struct RiveScene: View {
    let artboard: String
    let fallback: ClipUkku
    @Environment(\.scenePhase) private var phase
    @Environment(\.ukkuQuieto) private var quieto
    @State private var rive: Rive?

    var body: some View {
        Group {
            if quieto {
                Image("ukku-maestro").resizable().scaledToFit()
            } else if let rive {
                RiveUIViewRepresentable(rive: rive).paused(phase != .active)
                    .accessibilityIdentifier("rive-\(artboard)")
            } else {
                ReproductorClip(clip: fallback)
            }
        }
        .task(id: artboard) {
            do {
                let file = try await RiveLibrary.file()
                let board = try await file.createArtboard(artboard)
                let renderer = try await Rive(file: file, artboard: board)
                try Task.checkCancellation()
                rive = renderer
            } catch {
                // Un error de render no bloquea el recorrido: continúa el clip incluido.
                rive = nil
            }
        }
    }
}

extension UkkuMood {
    var riveArtboard: String {
        switch self { case .bien: "Reposo"; case .atento: "Atento"; case .revisar: "Revisar"; case .sinDatos: "SinDatos" }
    }
}

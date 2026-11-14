import SwiftUI

@main
struct UkkuApp: App {
    @State private var store = AppStore()
    @Environment(\.scenePhase) private var fase

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(store)
                .preferredColorScheme(.light)
                .environment(\.locale, Locale(identifier: "es_PE"))
                .environment(\.calendar, Fechas.cal)
                .tint(.ukkuAzul)
                .onChange(of: fase) { _, nueva in
                    // iOS no garantiza ejecución en segundo plano: se reconcilia al volver.
                    if nueva == .active {
                        store.reconciliar()
                        Task { await store.comprobarIA() }
                    }
                }
        }
    }
}

struct RootView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.accessibilityReduceMotion) private var reducirSistema
    @State private var saludo: ClipUkku?
    /// Una vez por proceso: no depende de que la vista reaparezca.
    private static var saludoVisto = false

    var body: some View {
        @Bindable var store = store
        TabView(selection: $store.tab) {
            Tab("Inicio", systemImage: UkkuIcon.inicio.rawValue, value: Pestana.inicio) {
                NavigationStack { InicioView() }
            }
            Tab("Tu plan", systemImage: UkkuIcon.plan.rawValue, value: Pestana.plan) {
                NavigationStack { PlanUkkuView() }
            }
            Tab("Actividad", systemImage: UkkuIcon.actividad.rawValue, value: Pestana.actividad) {
                ActividadView()
            }
            Tab("Ajustes", systemImage: UkkuIcon.ajustes.rawValue, value: Pestana.ajustes) {
                NavigationStack { AjustesView() }
            }
        }
        .environment(\.ukkuQuieto, reducirSistema || store.estado.ajustes.reducirMovimiento)
        // Respuesta háptica solo al aplicar una acción confirmada.
        .sensoryFeedback(.success, trigger: store.estado.aplicadas.count)
        .overlay {
            if let saludo {
                BienvenidaView(clip: saludo) { withAnimation(.easeOut(duration: 0.3)) { self.saludo = nil } }
                    .transition(.opacity)
            }
        }
        .onAppear {
            // Saludo de entrada, una vez por arranque. Lo entrega Codex como clip «saludo».
            guard !Self.saludoVisto else { return }
            Self.saludoVisto = true
            let quieto = reducirSistema || store.estado.ajustes.reducirMovimiento
            if !quieto, !ProcessInfo.processInfo.arguments.contains("--sin-saludo") { saludo = ClipsUkku.cargar("saludo") }
        }
        .task { await store.comprobarIA() }
    }
}

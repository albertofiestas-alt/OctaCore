import SwiftUI

@main
struct UkkuCodexApp: App {
    @State private var store = AppStore()
    @Environment(\.scenePhase) private var phase
    var body: some Scene {
        WindowGroup {
            MainView().environment(store)
                .environment(\.locale, Locale(identifier: "es_PE"))
                .environment(\.calendar, Fechas.cal)
                .environment(\.timeZone, Fechas.zona)
                .preferredColorScheme(.light).tint(.ukkuAzul)
                .onChange(of: phase) { _, value in if value == .active { store.reconciliar() } }
        }
    }
}

struct MainView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var greeted = false
    @State private var greeting: ClipUkku?

    var body: some View {
        @Bindable var store = store
        TabView(selection: $store.tab) {
            Tab("Inicio", systemImage: "house.fill", value: .inicio) { NavigationStack { HomeScreen() } }
            Tab("Tu plan", systemImage: "square.stack.3d.up.fill", value: .plan) { NavigationStack { PlanScreen() } }
            Tab("Actividad", systemImage: "arrow.left.arrow.right", value: .actividad) { NavigationStack { ActivityScreen() } }
            Tab("Ajustes", systemImage: "slider.horizontal.3", value: .ajustes) { NavigationStack { SettingsScreen() } }
        }
        .environment(\.ukkuQuieto, reduceMotion || store.estado.ajustes.reducirMovimiento)
        .sensoryFeedback(.success, trigger: store.estado.aplicadas.count)
        .overlay {
            if let greeting {
                BienvenidaView(clip: greeting) {
                    withAnimation(reduceMotion ? nil : .easeOut(duration: 0.3)) { self.greeting = nil }
                }.transition(.opacity)
            }
        }
        .onAppear {
            guard !greeted else { return }
            greeted = true
            if !reduceMotion && !store.estado.ajustes.reducirMovimiento && !ProcessInfo.processInfo.arguments.contains("--sin-saludo") {
                greeting = ClipsUkku.cargar("saludo")
            }
        }
    }
}

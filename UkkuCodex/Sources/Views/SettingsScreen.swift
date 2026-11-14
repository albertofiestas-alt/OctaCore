import SwiftUI

struct SettingsScreen: View {
    @Environment(AppStore.self) private var store
    @State private var name = ""
    @State private var cushion = ""
    @State private var startDay = 1
    @State private var scenario: Escenario = .base
    @State private var reset = false
    @State private var error: String?
    @State private var saved = false
    @State private var permissionNote: String?

    var body: some View {
        Form {
            Section {
                HStack(spacing: 16) {
                    EscenaUkku(escena: .privacidad, size: 76)
                    VStack(alignment: .leading, spacing: 6) {
                        Text("A tu manera").font(.title2.bold()).foregroundStyle(Color.tinta)
                        Text("Tu dinero y tus datos, bajo tu control.").font(.subheadline).foregroundStyle(Color.secundaria)
                    }
                }.padding(.vertical, 8)
            }.listRowBackground(Color.clear)
            Section("Tu perfil") {
                TextField("Tu nombre", text: $name).accessibilityIdentifier("nombre-perfil")
                LabeledContent("Moneda", value: "Soles · PEN")
            }
            Section {
                LabeledContent("Colchón mínimo") {
                    TextField("Monto en soles", text: $cushion).keyboardType(.decimalPad).multilineTextAlignment(.trailing)
                        .accessibilityIdentifier("colchon-ajustes")
                }
                Stepper("Tu ciclo empieza el día \(startDay)", value: $startDay, in: 1...28)
                Button("Guardar mis preferencias") { save() }.frame(minHeight: 44)
                if saved { Label("Preferencias guardadas", systemImage: "checkmark.circle.fill").foregroundStyle(Color.verde) }
                if let error { ErrorNotice(text: error) }
            } header: { Text("Tu forma de organizarte") } footer: {
                Text("Tu colchón queda fuera del disponible: es el dinero que prefieres cuidar.")
            }
            Section("Privacidad y accesibilidad") {
                Toggle("Ocultar importes", isOn: Binding(get: { store.estado.ajustes.ocultarImportes }, set: { v in store.ajustar { $0.ocultarImportes = v } }))
                    .accessibilityIdentifier("ocultar-importes")
                Toggle("Reducir movimiento", isOn: Binding(get: { store.estado.ajustes.reducirMovimiento }, set: { v in store.ajustar { $0.reducirMovimiento = v } }))
                    .accessibilityIdentifier("reducir-movimiento")
                Toggle("Recordatorios de mis planes", isOn: Binding(get: { store.estado.ajustes.notificaciones }, set: notifications))
                if let permissionNote { Text(permissionNote).font(.caption).foregroundStyle(Color.secundaria) }
            }
            Section {
                Picker("Ejemplo", selection: $scenario) { ForEach(Escenario.allCases) { Text($0.nombre).tag($0) } }
                Button("Cargar este ejemplo", role: .destructive) { reset = true }
                ShareLink(item: Persistencia.exportar(store.estado), preview: SharePreview("Datos de Ukku Codex")) {
                    Label("Exportar mis datos demo", systemImage: "square.and.arrow.up")
                }
            } header: { Text("Explora la demostración") } footer: {
                Text("Cargar un ejemplo reemplaza los movimientos y planes de esta versión. Tus preferencias se conservan.")
            }
            Section {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Ukku · Edición Codex").font(.headline).foregroundStyle(Color.tinta)
                    Text("Una experiencia nativa para pensar antes de gastar. Prototipo local con datos ficticios; no ejecuta pagos ni está conectado a cuentas bancarias o IA.")
                        .font(.caption).foregroundStyle(Color.secundaria)
                }.padding(.vertical, 6)
            }
        }
        .scrollContentBackground(.hidden).background(Color.fondo)
        .scrollDismissesKeyboard(.interactively)
        .navigationTitle("Ajustes").navigationBarTitleDisplayMode(.inline)
        .onAppear {
            name = store.estado.ajustes.nombre
            cushion = String(format: "%.2f", Double(store.estado.ajustes.colchonMinor) / 100)
            startDay = store.estado.ajustes.cicloDia; scenario = store.estado.escenario
        }
        .confirmationDialog("¿Reemplazar los datos por «\(scenario.nombre)»?", isPresented: $reset, titleVisibility: .visible) {
            Button("Cargar ejemplo", role: .destructive) { store.reiniciar(scenario); store.tab = .inicio }
        }
    }

    private func save() {
        let clean = name.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !clean.isEmpty && clean.count <= 40 else { error = "Usa un nombre de entre 1 y 40 caracteres."; saved = false; return }
        guard let value = Dinero.parse(cushion) else { error = "Revisa el monto del colchón."; saved = false; return }
        store.ajustar { $0.nombre = clean; $0.colchonMinor = value; $0.cicloDia = startDay }
        error = nil; saved = true
    }

    private func notifications(_ enabled: Bool) {
        guard enabled else { store.ajustar { $0.notificaciones = false }; return }
        Task {
            let allowed = await Notificaciones.pedirPermiso()
            store.ajustar { $0.notificaciones = allowed }
            permissionNote = allowed ? nil : "Puedes permitir los avisos desde Configuración de iOS."
        }
    }
}

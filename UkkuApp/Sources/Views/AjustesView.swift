import SwiftUI

struct AjustesView: View {
    @Environment(AppStore.self) private var store
    @State private var nombre = ""
    @State private var colchon = ""
    @State private var avisoPermiso: String?

    var body: some View {
        let a = store.estado.ajustes
        Form {
            Section {
                Cabecera(titulo: "Ajustes") { EmptyView() }
                    .listRowInsets(EdgeInsets(top: 0, leading: 4, bottom: 0, trailing: 4))
                    .listRowBackground(Color.clear)
            }
            .listSectionSpacing(.compact)

            Section("Perfil") {
                LabeledContent("Nombre") {
                    TextField("Tu nombre", text: $nombre).multilineTextAlignment(.trailing)
                        .onSubmit(guardarNombre)
                        .onChange(of: nombre) { guardarNombre() }
                }
                LabeledContent("Moneda", value: "Soles (PEN)")
            }

            Section {
                Stepper("Tu mes empieza el día \(a.cicloDia)", value: Binding(get: { a.cicloDia }, set: { v in store.ajustar { $0.cicloDia = v } }), in: 1...28)
                LabeledContent("Colchón mínimo") {
                    TextField("0", text: $colchon).keyboardType(.decimalPad).multilineTextAlignment(.trailing)
                        .accessibilityIdentifier("colchon")
                        .onChange(of: colchon) {
                            if let c = Dinero.parse(colchon), c != a.colchonMinor { store.ajustar { $0.colchonMinor = c } }
                        }
                }
                NavigationLink("Presupuestos por categoría") { PresupuestosView() }
                Toggle("Recordatorios de mis planes", isOn: Binding(get: { a.notificaciones }, set: cambiarNotificaciones))
                if let avisoPermiso { Text(avisoPermiso).font(.ukMeta).foregroundStyle(Color.ukkuAmbar) }
            } header: { Text("Dinero y planes") } footer: {
                Text("El colchón es dinero que no quieres tocar. Con él, tu disponible del mes es \(store.importe(store.resumen.disponible)).")
            }

            Section("Privacidad y accesibilidad") {
                HStack(spacing: 12) {
                    EscenaUkku(escena: .privacidad, size: 52)
                    Text("Los datos de esta demo se guardan en este teléfono.").font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
                }
                Toggle("Ocultar importes", isOn: Binding(get: { a.ocultarImportes }, set: { v in store.ajustar { $0.ocultarImportes = v } }))
                Toggle("Reducir movimiento", isOn: Binding(get: { a.reducirMovimiento }, set: { v in store.ajustar { $0.reducirMovimiento = v } }))
            }

            Section {
                Label("Simulación local", systemImage: "checkmark.circle.fill")
                    .foregroundStyle(Color.ukkuVerde)
                NavigationLink("Opciones de demostración") { OpcionesDemoView() }
            } header: { Text("Demostración") } footer: {
                Text("Datos ficticios. Explora escenarios y crea planes sin conexión.")
            }

            Section {
                VStack(spacing: 4) {
                    Image("ukku-logo").resizable().scaledToFit().frame(height: 28).accessibilityLabel("Ukku")
                    Text("Tu plata, con un plan").font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
                }
                .frame(maxWidth: .infinity)
                .listRowBackground(Color.clear)
            }
        }
        .contentMargins(.top, 0, for: .scrollContent)
        .scrollContentBackground(.hidden)
        .background(Color.ukkuSuperficie)
        .safeAreaInset(edge: .top, spacing: 0) {
            // Evita que el contenido pase por debajo de la hora al desplazar.
            Color.clear.frame(height: 0).background(Color.ukkuSuperficie.ignoresSafeArea(edges: .top))
        }
        .toolbar(.hidden, for: .navigationBar)
        .onAppear {
            nombre = a.nombre
            colchon = String(format: "%d.%02d", a.colchonMinor / 100, a.colchonMinor % 100)
        }
    }

    private func guardarNombre() {
        let n = nombre.trimmingCharacters(in: .whitespaces)
        if !n.isEmpty, n != store.estado.ajustes.nombre { store.ajustar { $0.nombre = n } }
    }
    private func cambiarNotificaciones(_ activar: Bool) {
        guard activar else { store.ajustar { $0.notificaciones = false }; avisoPermiso = nil; return }
        Task {
            if await Notificaciones.pedirPermiso() { store.ajustar { $0.notificaciones = true }; avisoPermiso = nil }
            else { avisoPermiso = "iOS no dio permiso. Puedes activarlo en Configuración del teléfono." }
        }
    }
}

struct PresupuestosView: View {
    @Environment(AppStore.self) private var store
    @State private var limite: Categoria?
    var body: some View {
        Form {
            Section {
                ForEach(store.estado.categorias.filter { $0.id != "income" && $0.id != "savings" }) { c in
                    Button { limite = c } label: {
                        HStack {
                            Label(c.nombre, systemImage: c.icono).foregroundStyle(Color.ukkuTinta)
                            Spacer()
                            Text(store.estado.presupuestos.first { $0.categoriaId == c.id }.map { store.importe($0.limiteMinor, decimales: false) } ?? "Sin límite")
                                .foregroundStyle(Color.ukkuSecundario).monospacedDigit()
                        }
                    }
                }
            } footer: { Text("Toca una categoría para fijar su límite mensual.") }
        }
        .navigationTitle("Presupuestos")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(item: $limite) { LimiteView(categoria: $0) }
    }
}

/// Opciones secundarias de la demo: endpoint local, escenarios, exportar y reiniciar.
struct OpcionesDemoView: View {
    @Environment(AppStore.self) private var store
    @State private var endpoint = ""
    @State private var escenario = Escenario.base
    @State private var reiniciar = false

    var body: some View {
        Form {
            if !store.modoSimulacion {
            Section {
                TextField("Dirección local", text: $endpoint)
                    .keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled()
                    .onSubmit(guardarEndpoint)
                Button("Probar conexión") {
                    guardarEndpoint()
                    Task { store.ia = .comprobando; await store.comprobarIA() }
                }
            } header: { Text("Servicio de IA") } footer: {
                Text("\(store.ia.texto). La IA se conecta a través de un servicio en tu computadora; la credencial se queda ahí, nunca en el teléfono.")
            }
            }
            Section {
                Picker("Escenario", selection: $escenario) { ForEach(Escenario.allCases) { Text($0.nombre).tag($0) } }
                Button("Reiniciar datos con este escenario", role: .destructive) { reiniciar = true }
            } header: { Text("Datos de demostración") } footer: { Text("Cargado ahora: \(store.estado.escenario.nombre).") }
            Section {
                ShareLink(item: Persistencia.exportar(store.estado), preview: SharePreview("Datos demo de Ukku (JSON)")) {
                    Label("Exportar datos de la demo", systemImage: "square.and.arrow.up")
                }
            }
            Section("Sobre esta demo") {
                Text("Ukku es un prototipo de hackathon con datos sintéticos. Ofrece orientación educativa, no asesoría financiera. No se conecta a cuentas reales, no ejecuta pagos ni cancela servicios, y no es un producto oficial de ningún banco.")
                    .font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
            }
        }
        .navigationTitle("Demostración")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            endpoint = store.estado.ajustes.endpointIA
            escenario = store.estado.escenario
        }
        .confirmationDialog("Se borrarán tus movimientos, planes y conversación, y se cargará «\(escenario.nombre)». Tus ajustes se conservan.", isPresented: $reiniciar, titleVisibility: .visible) {
            Button("Reiniciar datos", role: .destructive) { store.reiniciar(escenario) }
        }
    }

    private func guardarEndpoint() {
        let e = endpoint.trimmingCharacters(in: .whitespaces)
        if e != store.estado.ajustes.endpointIA { store.ajustar { $0.endpointIA = e } }
    }
}

struct LimiteView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var cerrar
    let categoria: Categoria
    @State private var monto = ""
    @State private var error: String?
    var body: some View {
        let r = store.resumen
        NavigationStack {
            Form {
                Section {
                    TextField("Límite mensual en soles", text: $monto).keyboardType(.decimalPad)
                } footer: {
                    Text("Este mes llevas \(store.importe(Calculo.gastado(store.estado, categoria: categoria.id, ciclo: r.ciclo))) en \(categoria.nombre).")
                }
                if let error { Label(error, systemImage: "exclamationmark.circle").foregroundStyle(Color.ukkuRojo) }
            }
            .navigationTitle(categoria.nombre)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancelar") { cerrar() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Guardar límite") {
                        guard let c = Dinero.parse(monto), c > 0 else { error = "Escribe un límite mayor que cero."; return }
                        let p = store.propuesta("set_category_budget", ["category_id": .s(categoria.id), "amount_minor": .i(c), "currency": .s("PEN"), "cycle_id": .s(r.ciclo.id)], fuente: .manual)
                        if case .failure(let e) = store.aplicar(p) { error = e.mensaje } else { cerrar() }
                    }
                }
            }
            .onAppear {
                if let l = store.estado.presupuestos.first(where: { $0.categoriaId == categoria.id })?.limiteMinor { monto = String(format: "%d.%02d", l / 100, l % 100) }
            }
        }
        .presentationDetents([.medium])
    }
}

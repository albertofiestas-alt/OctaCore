import SwiftUI

private enum MovementFilter: String, CaseIterable, Identifiable {
    case all = "Todos", expenses = "Gastos", income = "Ingresos"
    var id: String { rawValue }
    func includes(_ movement: Movimiento) -> Bool {
        switch self { case .all: true; case .expenses: movement.montoMinor < 0; case .income: movement.montoMinor > 0 }
    }
}

struct ActivityScreen: View {
    @Environment(AppStore.self) private var store
    @State private var filter: MovementFilter = .all
    @State private var query = ""
    @State private var newMovement = false
    @State private var selected: Movimiento?
    @FocusState private var searching: Bool

    private var movements: [Movimiento] {
        store.estado.movimientos.filter {
            filter.includes($0) && (query.isEmpty || $0.comercio.localizedCaseInsensitiveContains(query) || store.categoria($0.categoriaId).nombre.localizedCaseInsensitiveContains(query))
        }.sorted { $0.fecha > $1.fecha }
    }
    private var days: [Date] { Array(Set(movements.map { Fechas.inicioDia($0.fecha) })).sorted(by: >) }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                HStack(alignment: .top) {
                    PageTitle(title: "Actividad", subtitle: "Lo que entra. Lo que sale. Todo claro.")
                    Spacer(minLength: 4)
                    Button { newMovement = true } label: {
                        Image(systemName: "plus").font(.title3.bold()).foregroundStyle(.white).frame(width: 48, height: 48)
                            .background(Color.ukkuAzul, in: .circle)
                    }.accessibilityLabel("Registrar movimiento").accessibilityIdentifier("agregar-movimiento")
                        .disabled(store.estado.cuentas.isEmpty)
                }
                summary
                HStack {
                    Image(systemName: "magnifyingglass").foregroundStyle(Color.secundaria)
                    TextField("Buscar un movimiento", text: $query).font(.subheadline).autocorrectionDisabled()
                        .focused($searching).submitLabel(.search).onSubmit { searching = false }
                        .accessibilityIdentifier("buscar-movimientos")
                    if !query.isEmpty { Button { query = "" } label: { Image(systemName: "xmark.circle.fill") }.accessibilityLabel("Limpiar búsqueda") }
                }.padding(16).background(.white, in: .rect(cornerRadius: 16))
                Picker("Filtrar movimientos", selection: $filter) {
                    ForEach(MovementFilter.allCases) { Text($0.rawValue).tag($0) }
                }.pickerStyle(.segmented)
                if movements.isEmpty {
                    EmptyState(title: query.isEmpty ? "Todavía no hay movimientos" : "Sin coincidencias", detail: query.isEmpty ? "Los movimientos que registres aparecerán aquí." : "Prueba con otro comercio o categoría.")
                }
                ForEach(days, id: \.self) { day in
                    VStack(alignment: .leading, spacing: 12) {
                        Eyebrow(text: Fechas.corta(day))
                        Paper {
                            VStack(spacing: 20) {
                                ForEach(movements.filter { Fechas.inicioDia($0.fecha) == day }) { movement in
                                    Button { selected = movement } label: { MovementRow(movement: movement) }.buttonStyle(PressStyle())
                                }
                            }
                        }
                    }
                }
                DemoFootnote()
            }.padding(22)
        }
        .background(Color.fondo).toolbar(.hidden, for: .navigationBar)
        .scrollDismissesKeyboard(.interactively)
        .toolbar { ToolbarItemGroup(placement: .keyboard) { Spacer(); Button("Terminar búsqueda") { searching = false } } }
        .sheet(isPresented: $newMovement) { MovementEditor() }
        .sheet(item: $selected) { MovementDetail(movement: $0, selection: $selected) }
    }

    private var summary: some View {
        let cycle = store.resumen.ciclo
        let current = store.estado.movimientos.filter { $0.fecha >= cycle.inicio && $0.fecha < cycle.fin }
        let income = current.filter { $0.montoMinor > 0 }.reduce(0) { $0 + $1.montoMinor }
        let expenses = -current.filter { $0.montoMinor < 0 }.reduce(0) { $0 + $1.montoMinor }
        return Paper {
            VStack(alignment: .leading, spacing: 16) {
                Eyebrow(text: "Este ciclo · \(Fechas.corta(cycle.inicio))")
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 8) {
                        Label("Entró", systemImage: "arrow.down.left").font(.subheadline).foregroundStyle(Color.verde)
                        MoneyText(value: income).font(.title2.bold()).foregroundStyle(Color.tinta)
                    }.frame(maxWidth: .infinity, alignment: .leading)
                    VStack(alignment: .leading, spacing: 8) {
                        Label("Salió", systemImage: "arrow.up.right").font(.subheadline).foregroundStyle(Color.secundaria)
                        MoneyText(value: expenses).font(.title2.bold()).foregroundStyle(Color.tinta)
                    }.frame(maxWidth: .infinity, alignment: .leading)
                }.minimumScaleFactor(0.65)
            }
        }
    }
}

struct MovementRow: View {
    @Environment(AppStore.self) private var store
    let movement: Movimiento
    var body: some View {
        HStack(spacing: 12) {
            Glyph(name: store.categoria(movement.categoriaId).icono, color: movement.montoMinor > 0 ? .verde : .ukkuAzul)
            VStack(alignment: .leading, spacing: 5) {
                Text(movement.comercio).font(.subheadline.weight(.semibold)).foregroundStyle(Color.tinta).lineLimit(2)
                Text(store.categoria(movement.categoriaId).nombre).font(.caption).foregroundStyle(Color.secundaria)
            }
            Spacer(minLength: 6)
            Text(store.importe(movement.montoMinor, signo: true, decimales: false)).font(.subheadline.weight(.semibold).monospacedDigit())
                .foregroundStyle(movement.montoMinor > 0 ? Color.verde : Color.tinta).lineLimit(1).minimumScaleFactor(0.65)
        }.accessibilityElement(children: .combine)
    }
}

struct MovementEditor: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    var payment: PagoConFecha?
    @State private var expense = true
    @State private var amount = ""
    @State private var merchant = ""
    @State private var category = "groceries"
    @State private var date = Date()
    @State private var proposal: PropuestaAccion?
    @State private var error: String?
    @State private var seeded = false

    var body: some View {
        NavigationStack {
            Group {
                if let proposal {
                    ReviewContent(initialProposal: proposal, paymentID: payment?.id) { self.proposal = nil }
                } else {
                    Form {
                        Section {
                            if payment == nil {
                                Picker("Tipo", selection: $expense) { Text("Gasto").tag(true); Text("Ingreso").tag(false) }.pickerStyle(.segmented)
                            }
                            TextField("Monto en soles", text: $amount).keyboardType(.decimalPad)
                                .disabled(payment != nil).accessibilityIdentifier("monto-movimiento")
                            TextField("Comercio o descripción", text: $merchant).accessibilityIdentifier("comercio-movimiento")
                            Picker("Categoría", selection: $category) {
                                ForEach(store.estado.categorias) { Text($0.nombre).tag($0.id) }
                            }.disabled(payment != nil)
                            DatePicker("Fecha", selection: $date, in: ...store.hoy, displayedComponents: .date)
                        } header: { Text(payment == nil ? "Un movimiento en tu demo" : "Registrar \(payment!.nombre)") } footer: {
                            Text(payment == nil ? "Revisarás el saldo antes de guardar. Ninguna operación mueve dinero real." : "Confirma solo si ya realizaste este pago. Dejará de contarse como pendiente.")
                        }
                        if let error { Section { ErrorNotice(text: error) } }
                        Section { PrimaryButton(title: "Revisar movimiento") { prepare() }.accessibilityIdentifier("revisar-movimiento") }
                            .listRowInsets(EdgeInsets()).listRowBackground(Color.clear)
                    }
                    .scrollDismissesKeyboard(.interactively)
                }
            }
            .navigationTitle(proposal == nil ? "Registrar movimiento" : "Revisa y decide")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Cerrar") { dismiss() } } }
            .onChange(of: expense) { _, value in category = value ? "groceries" : "income" }
            .onAppear {
                guard !seeded else { return }; seeded = true
                if let payment {
                    merchant = payment.nombre; amount = String(format: "%.2f", Double(payment.montoMinor) / 100)
                    category = payment.categoriaId
                }
            }
        }
    }

    private func prepare() {
        guard let amount = Dinero.parse(amount), amount > 0 else { error = "Escribe un monto mayor que cero, con hasta dos decimales."; return }
        let name = merchant.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty else { error = "Agrega una descripción para reconocer el movimiento."; return }
        guard let account = store.estado.cuentas.first else { error = "Carga un ejemplo para empezar."; return }
        let p = store.propuesta("record_demo_transaction", ["account_id": .s(account.id), "amount_minor_signed": .i(expense ? -amount : amount),
            "currency": .s("PEN"), "category_id": .s(category), "date": .s(Fechas.iso(date)), "merchant": .s(name)], fuente: .manual)
        switch store.previsualizar(p, pagoID: payment?.id) {
        case .success: error = nil; proposal = p
        case .failure(let failure): error = failure.mensaje
        }
    }
}

struct MovementDetail: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    let movement: Movimiento
    @Binding var selection: Movimiento?
    @State private var confirmDelete = false
    var body: some View {
        NavigationStack {
            List {
                Section {
                    LabeledContent("Descripción", value: movement.comercio)
                    LabeledContent("Monto", value: store.importe(movement.montoMinor, signo: true))
                    LabeledContent("Categoría", value: store.categoria(movement.categoriaId).nombre)
                    LabeledContent("Fecha", value: Fechas.corta(movement.fecha))
                    LabeledContent("Cuenta", value: "Cuenta demo")
                }
                if movement.pagoId != nil { Section { Text("Este movimiento registra un pago pendiente. Si lo eliminas, el pago volverá a estar pendiente.").font(.footnote) } }
                Section { Button("Eliminar movimiento", role: .destructive) { confirmDelete = true } }
            }
            .navigationTitle("Detalle").navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Listo") { dismiss() } } }
            .confirmationDialog("El saldo de tu cuenta demo se ajustará al eliminar este movimiento.", isPresented: $confirmDelete, titleVisibility: .visible) {
                Button("Eliminar movimiento", role: .destructive) {
                    store.eliminarMovimiento(movement.id)
                    selection = nil
                }.accessibilityIdentifier("confirmar-eliminar-movimiento")
            }
        }
    }
}

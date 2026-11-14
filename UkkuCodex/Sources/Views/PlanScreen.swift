import SwiftUI

struct PlanScreen: View {
    @Environment(AppStore.self) private var store
    @State private var newKind: TipoPlan?
    @State private var selected: Plan?
    @State private var includeFinished = false

    private var plans: [Plan] {
        store.estado.planes.filter { includeFinished || $0.estado != .completado }.sorted { $0.creado > $1.creado }
    }
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                PageTitle(title: "Tu plan", subtitle: "Pequeños pasos. Más tranquilidad.")
                Paper(color: Color.ukkuCeleste.opacity(0.16)) {
                    HStack(spacing: 12) {
                        VStack(alignment: .leading, spacing: 8) {
                            Eyebrow(text: "Vamos juntos", color: .ukkuAzul)
                            Text("Dale un propósito\na tu plata.").font(.title2.bold()).foregroundStyle(Color.tinta)
                            Text("Elige un paso y revisa el impacto antes de guardarlo.").font(.subheadline).foregroundStyle(Color.secundaria)
                        }
                        Spacer(minLength: 0)
                        EscenaUkku(escena: .planificando, size: 110)
                    }
                }
                VStack(spacing: 12) {
                    action("Separar para un pago", detail: "Reserva su lugar en tu calendario", icon: "calendar.badge.clock", kind: .reserva)
                    action("Crear una meta", detail: "Empieza por algo que te importe", icon: "target", kind: .meta)
                    action("Poner un límite", detail: "Decide cuánto gastar por categoría", icon: "chart.bar.xaxis", kind: .presupuesto)
                }
                VStack(alignment: .leading, spacing: 14) {
                    SectionHeading(title: "Lo que estás construyendo")
                    if plans.isEmpty {
                        EmptyState(title: "Tu primer plan te espera", detail: "Elige una de las opciones de arriba.", scene: .planificando)
                    }
                    ForEach(plans) { plan in
                        Button { selected = plan } label: { PlanCard(plan: plan) }.buttonStyle(PressStyle())
                    }
                    Toggle("Incluir completados", isOn: $includeFinished).font(.subheadline).tint(.ukkuAzul)
                }
                DemoFootnote()
            }.padding(22)
        }.background(Color.fondo).toolbar(.hidden, for: .navigationBar)
            .sheet(item: $newKind) { PlanEditor(kind: $0) }
            .sheet(item: $selected) { PlanDetailScreen(planID: $0.id) }
    }

    private func action(_ title: String, detail: String, icon: String, kind: TipoPlan) -> some View {
        Button { newKind = kind } label: {
            Paper {
                HStack(spacing: 14) {
                    Glyph(name: icon)
                    VStack(alignment: .leading, spacing: 4) {
                        Text(title).font(.headline).foregroundStyle(Color.tinta)
                        Text(detail).font(.caption).foregroundStyle(Color.secundaria)
                    }
                    Spacer(minLength: 4)
                    Image(systemName: "chevron.right").font(.caption.bold()).foregroundStyle(Color.secundaria)
                }
            }
        }.buttonStyle(PressStyle()).accessibilityIdentifier("crear-\(kind.rawValue)")
    }
}

struct PlanCard: View {
    @Environment(AppStore.self) private var store
    let plan: Plan
    var body: some View {
        let progress = Calculo.progreso(plan, store.estado, hoy: store.hoy)
        Paper {
            VStack(alignment: .leading, spacing: 16) {
                HStack(alignment: .top, spacing: 12) {
                    Glyph(name: plan.tipo.icono)
                    VStack(alignment: .leading, spacing: 4) {
                        Text(plan.titulo).font(.headline).foregroundStyle(Color.tinta)
                        Text("\(plan.estado.nombre) · \(Fechas.corta(plan.fecha))").font(.caption).foregroundStyle(Color.secundaria)
                    }
                    Spacer(minLength: 0)
                    Image(systemName: "chevron.right").font(.caption.bold()).foregroundStyle(Color.secundaria)
                }
                if plan.tipo != .recordatorio {
                    ProgressView(value: progress.valor).tint(plan.estado == .pausado ? Color.secundaria : Color.ukkuAzul)
                    Text(store.estado.ajustes.ocultarImportes ? "Importes ocultos" : progress.texto)
                        .font(.caption).foregroundStyle(Color.secundaria)
                }
            }
        }
    }
}

struct PlanEditor: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    let kind: TipoPlan
    @State private var title = ""
    @State private var amount = ""
    @State private var date = Date()
    @State private var category = "savings"
    @State private var recurrence: Periodicidad = .none
    @State private var proposal: PropuestaAccion?
    @State private var error: String?
    @State private var seeded = false

    var body: some View {
        NavigationStack {
            Group {
                if let proposal {
                    ReviewContent(initialProposal: proposal) { self.proposal = nil }
                } else {
                    Form {
                        Section {
                            if kind != .presupuesto {
                                TextField(kind == .meta ? "¿Para qué quieres ahorrar?" : "Nombre del plan", text: $title)
                                    .accessibilityIdentifier("nombre-plan")
                            }
                            if kind != .recordatorio {
                                TextField("Monto en soles", text: $amount).keyboardType(.decimalPad).accessibilityIdentifier("monto-plan")
                            }
                            if kind != .meta && kind != .recordatorio {
                                Picker("Categoría", selection: $category) {
                                    ForEach(store.estado.categorias.filter { $0.id != "income" }) { Text($0.nombre).tag($0.id) }
                                }
                            }
                            if kind != .presupuesto {
                                DatePicker("Fecha", selection: $date, in: Fechas.inicioDia(store.hoy)...,
                                           displayedComponents: kind == .recordatorio ? [.date, .hourAndMinute] : [.date])
                            }
                            if kind == .reserva {
                                Picker("Repetir", selection: $recurrence) { ForEach(Periodicidad.allCases) { Text($0.nombre).tag($0) } }
                            }
                        } header: { Text(kind.nombre) } footer: {
                            Text(kind == .meta ? "Crear una meta no separa dinero todavía. Tú decides cada aporte." : "Revisarás el efecto en tus números antes de confirmar.")
                        }
                        if let error { Section { ErrorNotice(text: error) } }
                        Section { PrimaryButton(title: "Revisar mi plan") { prepare() }.accessibilityIdentifier("revisar-plan") }
                            .listRowBackground(Color.clear).listRowInsets(EdgeInsets())
                    }.scrollDismissesKeyboard(.interactively)
                }
            }
            .navigationTitle(proposal == nil ? "Un nuevo paso" : "Revisa y decide")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Cerrar") { dismiss() } } }
            .onAppear {
                guard !seeded else { return }; seeded = true
                date = Fechas.cal.date(byAdding: .day, value: kind == .meta ? 30 : 7, to: store.hoy)!
                if kind == .reserva, let p = store.resumen.proximoPago {
                    title = "Reservar para \(p.nombre)"; amount = String(format: "%.2f", Double(p.montoMinor) / 100)
                    date = max(p.fecha, store.hoy); category = p.categoriaId
                } else if kind == .presupuesto { category = "restaurants" }
            }
        }
    }

    private func prepare() {
        let name = title.trimmingCharacters(in: .whitespacesAndNewlines)
        guard kind == .presupuesto || !name.isEmpty else { error = "Dale un nombre a tu plan."; return }
        guard let value = kind == .recordatorio ? 0 : Dinero.parse(amount), kind == .recordatorio || value > 0 else {
            error = "Escribe un monto mayor que cero, con hasta dos decimales."; return
        }
        let p: PropuestaAccion
        switch kind {
        case .meta:
            p = store.propuesta("create_savings_goal", ["title": .s(name), "target_minor": .i(value), "currency": .s("PEN"), "target_date": .s(Fechas.iso(date))], fuente: .manual)
        case .reserva:
            p = store.propuesta("create_plan", ["title": .s(name), "amount_minor": .i(value), "currency": .s("PEN"), "due_date": .s(Fechas.iso(date)), "category_id": .s(category), "recurrence": .s(recurrence.rawValue)], fuente: .manual)
        case .presupuesto:
            p = store.propuesta("set_category_budget", ["category_id": .s(category), "amount_minor": .i(value), "currency": .s("PEN"), "cycle_id": .s(store.resumen.ciclo.id)], fuente: .manual)
        case .recordatorio:
            p = store.propuesta("create_reminder", ["title": .s(name), "local_datetime": .s(Fechas.isoHora(date)), "timezone": .s("America/Lima")], fuente: .manual)
        }
        switch store.previsualizar(p) {
        case .success: error = nil; proposal = p
        case .failure(let failure): error = failure.mensaje
        }
    }
}

/// La propuesta mantiene el mismo ID al confirmar: un doble toque no duplica la escritura.
struct ReviewContent: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @Environment(\.ukkuQuieto) private var quieto
    @State private var proposal: PropuestaAccion
    @State private var result: ResultadoAccion?
    @State private var error: String?
    let paymentID: UUID?
    let back: () -> Void

    init(initialProposal: PropuestaAccion, paymentID: UUID? = nil, back: @escaping () -> Void) {
        _proposal = State(initialValue: initialProposal)
        self.paymentID = paymentID; self.back = back
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                if let result {
                    VStack(spacing: 16) {
                        if !quieto, let clip = ClipsUkku.cargar("celebra") {
                            RiveScene(artboard: "Celebra", fallback: clip).frame(width: 170, height: 170).accessibilityHidden(true)
                        } else { EscenaUkku(escena: .metaLograda, size: 170) }
                        Text("Un paso más, contigo.").font(.title.bold()).foregroundStyle(Color.tinta).multilineTextAlignment(.center)
                        Text(store.estado.ajustes.ocultarImportes ? "Tu cambio quedó guardado." : result.summary)
                            .font(.subheadline).foregroundStyle(Color.secundaria).multilineTextAlignment(.center)
                        Label("Guardado en esta demo", systemImage: "checkmark.circle.fill").font(.subheadline.bold()).foregroundStyle(Color.verde)
                            .accessibilityIdentifier("accion-guardada")
                    }.padding(.vertical, 20)
                    PrimaryButton(title: "Listo", icon: "checkmark") { dismiss() }.accessibilityIdentifier("finalizar-accion")
                } else if case .success(let preview) = store.previsualizar(proposal, pagoID: paymentID) {
                    VStack(spacing: 8) {
                        Glyph(name: "checklist")
                        Text(preview.titulo).font(.title2.bold()).foregroundStyle(Color.tinta).multilineTextAlignment(.center)
                        if let value = preview.importe { MoneyText(value: value).font(.largeTitle.bold()).foregroundStyle(Color.ukkuAzul) }
                        if let date = preview.fecha { Text(Fechas.corta(date)).font(.subheadline).foregroundStyle(Color.secundaria) }
                    }.padding(.top, 12)
                    Paper {
                        VStack(alignment: .leading, spacing: 18) {
                            Eyebrow(text: "Esto es lo que cambia")
                            ForEach(preview.lineas) { line in
                                VStack(alignment: .leading, spacing: 6) {
                                    Text(line.etiqueta).font(.subheadline).foregroundStyle(Color.secundaria)
                                    HStack {
                                        Text(store.estado.ajustes.ocultarImportes ? "•••" : line.antes).foregroundStyle(Color.secundaria)
                                        Image(systemName: "arrow.right").font(.caption).accessibilityHidden(true)
                                        Text(store.estado.ajustes.ocultarImportes ? "•••" : line.despues).foregroundStyle(Color.ukkuAzul)
                                    }.font(.headline).minimumScaleFactor(0.65)
                                }
                            }
                            if let note = preview.nota { Text(note).font(.footnote).foregroundStyle(Color.secundaria) }
                        }
                    }
                    if let error { ErrorNotice(text: error) }
                    PrimaryButton(title: "Confirmar y guardar", icon: "checkmark") { confirm() }.accessibilityIdentifier("confirmar-accion")
                    Button("Volver a editar", action: back).font(.subheadline.bold()).frame(minHeight: 44)
                    DemoFootnote()
                } else {
                    ErrorNotice(text: "La propuesta ya no se puede aplicar. Vuelve a editarla con tus datos actuales.")
                    Button("Volver a editar", action: back).frame(minHeight: 44)
                }
            }.padding(22)
        }.background(Color.fondo)
    }

    private func confirm() {
        guard result == nil else { return }
        switch store.aplicar(proposal, pagoID: paymentID) {
        case .success(let saved): result = saved
        case .failure(let failure):
            error = failure.mensaje
            if failure.contextoCambio { proposal.contextVersion = store.estado.contextVersion }
        }
    }
}

struct PlanDetailScreen: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    let planID: UUID
    @State private var contribution = "50"
    @State private var confirmContribution = false
    @State private var confirmDelete = false
    @State private var error: String?
    @State private var saved = false

    private var plan: Plan? { store.estado.planes.first { $0.id == planID } }
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    if let plan {
                        PlanCard(plan: plan)
                        if plan.tipo == .meta, plan.estado.activo {
                            Paper {
                                VStack(alignment: .leading, spacing: 14) {
                                    Text("Acércate un poco más").font(.headline)
                                    TextField("Aporte en soles", text: $contribution).keyboardType(.decimalPad)
                                        .font(.title.bold()).accessibilityIdentifier("aporte-meta")
                                    if let value = Dinero.parse(contribution) {
                                        Text("Tu disponible pasaría de \(store.importe(store.resumen.disponible)) a \(store.importe(max(0, store.resumen.disponible - value))).")
                                            .font(.caption).foregroundStyle(Color.secundaria)
                                    }
                                    PrimaryButton(title: "Separar para mi meta", icon: "plus") { confirmContribution = true }
                                    if saved { Label("Aporte guardado", systemImage: "checkmark.circle.fill").foregroundStyle(Color.verde) }
                                    if let error { ErrorNotice(text: error) }
                                }
                            }
                        }
                        Paper {
                            VStack(alignment: .leading, spacing: 16) {
                                Label("\(plan.estado.nombre) · \(Fechas.corta(plan.fecha))", systemImage: plan.estado.icono)
                                Text("\(plan.tipo.nombre). \(plan.periodicidad.nombre).").font(.subheadline).foregroundStyle(Color.secundaria)
                                if plan.estado == .pausado {
                                    Button("Reanudar plan") { store.reanudar(plan.id) }.frame(minHeight: 44)
                                } else if plan.estado.activo {
                                    Button("Pausar plan") {
                                        let p = store.propuesta("pause_plan", ["plan_id": .s(plan.id.uuidString)], fuente: .manual)
                                        if case .failure(let e) = store.aplicar(p) { error = e.mensaje }
                                    }.frame(minHeight: 44)
                                }
                                Text(plan.tipo == .meta ? "Pausar conserva el dinero que ya separaste para la meta." : "Ukku guarda tu plan; los pagos los realizas tú.")
                                    .font(.caption).foregroundStyle(Color.secundaria)
                            }
                        }
                        Button("Eliminar plan", role: .destructive) { confirmDelete = true }.frame(maxWidth: .infinity, minHeight: 44)
                        DemoFootnote()
                    }
                }.padding(22)
            }.background(Color.fondo)
                .navigationTitle("Tu siguiente paso").navigationBarTitleDisplayMode(.inline)
                .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Listo") { dismiss() } } }
                .confirmationDialog("¿Separar este aporte para la meta?", isPresented: $confirmContribution, titleVisibility: .visible) {
                    Button("Confirmar aporte") {
                        guard let value = Dinero.parse(contribution) else { error = "Revisa el monto del aporte."; return }
                        error = store.aportar(planID, monto: value); saved = error == nil
                    }
                }
                .confirmationDialog("Se eliminará este plan y se liberará su reserva dentro de la demo.", isPresented: $confirmDelete, titleVisibility: .visible) {
                    Button("Eliminar plan", role: .destructive) { store.eliminarPlan(planID); dismiss() }
                }
        }
    }
}

import SwiftUI

private enum HomeSheet: String, Identifiable {
    case simulator, breakdown, payment, movement
    var id: String { rawValue }
}

struct HomeScreen: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dynamicTypeSize) private var typeSize
    @State private var sheet: HomeSheet?
    @State private var goal: Plan?
    @ScaledMetric(relativeTo: .largeTitle) private var amountSize: CGFloat = 55

    var body: some View {
        let r = store.resumen
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                header
                if r.hayDatos {
                    hero(r)
                    balances(r)
                    nextPayment(r)
                    savings
                    recentActivity
                } else {
                    Paper {
                        EmptyState(title: "Tu próximo paso empieza aquí", detail: "Conoce a Ukku con un ejemplo. Podrás probar gastos, organizar pagos y crear tu primera meta.", scene: .planificando)
                        PrimaryButton(title: "Explorar con datos de ejemplo") { store.reiniciar(.base) }
                            .accessibilityIdentifier("cargar-demo")
                    }
                }
                DemoFootnote()
            }.padding(.horizontal, 22).padding(.top, 12).padding(.bottom, 24)
        }
        .background(Color.fondo).toolbar(.hidden, for: .navigationBar)
        .sheet(item: $sheet) { route in
            switch route {
            case .simulator: ScenarioScreen()
            case .breakdown: BreakdownScreen()
            case .payment: PaymentsScreen()
            case .movement: MovementEditor()
            }
        }
        .sheet(item: $goal) { PlanDetailScreen(planID: $0.id) }
        .onAppear {
            if ProcessInfo.processInfo.arguments.contains("--simular") { sheet = .simulator }
        }
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 5) {
                Image("ukku-logo").resizable().scaledToFit().frame(width: 76, height: 29).accessibilityLabel("Ukku")
                Text("Hola, \(store.estado.ajustes.nombre)").font(.subheadline).foregroundStyle(Color.secundaria)
            }
            Spacer()
            Text("DEMO").font(.caption2.bold()).tracking(1).foregroundStyle(Color.secundaria)
                .padding(.horizontal, 9).padding(.vertical, 6).background(.white, in: .capsule)
            Button { store.ajustar { $0.ocultarImportes.toggle() } } label: {
                Image(systemName: store.estado.ajustes.ocultarImportes ? "eye.slash" : "eye")
                    .font(.body).foregroundStyle(Color.tinta).frame(width: 44, height: 44)
                    .background(.white, in: .circle)
            }.accessibilityLabel(store.estado.ajustes.ocultarImportes ? "Mostrar importes" : "Ocultar importes")
                .accessibilityIdentifier("privacidad-inicio")
        }
    }

    private func hero(_ r: Resumen) -> some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                Eyebrow(text: "Tu día, con margen", color: .ukkuCeleste)
                Spacer()
                Image(systemName: "sun.max").foregroundStyle(Color.ukkuCeleste).accessibilityHidden(true)
            }
            HStack(alignment: .center, spacing: 0) {
                VStack(alignment: .leading, spacing: 5) {
                    Text("Para usar hoy").font(.subheadline).foregroundStyle(.white.opacity(0.8))
                    MoneyText(value: r.sugerenciaHoy ?? 0)
                        .font(.system(size: amountSize, weight: .semibold, design: .rounded))
                        .tracking(-2).lineLimit(1).minimumScaleFactor(0.55)
                        .accessibilityIdentifier("margen-hoy")
                    Text("Cuidando tus próximos pagos.")
                        .font(.caption).foregroundStyle(.white.opacity(0.8)).fixedSize(horizontal: false, vertical: true)
                }.frame(maxWidth: .infinity, alignment: .leading)
                if !typeSize.isAccessibilitySize {
                    UkkuPersonajeView(mood: r.mood, size: 115).padding(.trailing, -8)
                }
            }.foregroundStyle(.white)
            PrimaryButton(title: "Probar un escenario", icon: "slider.horizontal.3", inverse: true) { sheet = .simulator }
                .accessibilityIdentifier("abrir-simulador")
            HStack(spacing: 6) {
                Image(systemName: "sparkle")
                Text("Un vistazo a los próximos 14 días")
            }.font(.caption).foregroundStyle(.white.opacity(0.8)).frame(maxWidth: .infinity)
        }
        .padding(24)
        .background {
            RoundedRectangle(cornerRadius: 30).fill(LinearGradient(colors: [.ukkuAzul, Color(red: 0.02, green: 0.19, blue: 0.65)], startPoint: .topLeading, endPoint: .bottomTrailing))
        }
    }

    private func balances(_ r: Resumen) -> some View {
        Paper {
            VStack(alignment: .leading, spacing: 18) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Disponible este mes").font(.subheadline).foregroundStyle(Color.secundaria)
                        MoneyText(value: r.disponible).font(.title.bold()).foregroundStyle(Color.tinta)
                            .accessibilityIdentifier("disponible-mes")
                    }
                    Spacer(minLength: 8)
                    Button { sheet = .breakdown } label: {
                        Image(systemName: "arrow.up.right").font(.body.weight(.semibold)).frame(width: 44, height: 44)
                            .background(Color.fondo, in: .circle)
                    }.accessibilityLabel("Ver cómo se calcula tu disponible")
                }
                HStack(spacing: 4) {
                    Capsule().fill(Color.ukkuAzul).frame(maxWidth: .infinity)
                    Capsule().fill(Color.ukkuCeleste).frame(maxWidth: .infinity)
                    Capsule().fill(Color.borde).frame(maxWidth: .infinity)
                }.frame(height: 5).accessibilityHidden(true)
                // Los tres trazos son un separador visual, no una gráfica proporcional.
                ViewThatFits(in: .horizontal) {
                    HStack { protected(r); Spacer(); StatusPill(mood: r.mood) }
                    VStack(alignment: .leading, spacing: 12) { protected(r); StatusPill(mood: r.mood) }
                }
                if r.faltante > 0 { ErrorNotice(text: "Faltan \(store.importe(r.faltante)) para cubrir pagos y reservas.") }
            }
        }
    }

    private func protected(_ r: Resumen) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text("Reservas + colchón").font(.caption).foregroundStyle(Color.secundaria)
            MoneyText(value: r.reservas + r.colchon).font(.subheadline.bold()).foregroundStyle(Color.tinta)
        }
    }

    @ViewBuilder private func nextPayment(_ r: Resumen) -> some View {
        if let p = r.proximoPago {
            VStack(spacing: 6) {
                SectionHeading(title: "En el calendario", action: "Ver todos") { sheet = .payment }
                Button { sheet = .payment } label: {
                    Paper {
                        HStack(spacing: 14) {
                            VStack(spacing: 2) {
                                Text(p.fecha.formatted(.dateTime.day().locale(Locale(identifier: "es_PE"))))
                                    .font(.title2.bold())
                                Text(p.fecha.formatted(.dateTime.month(.abbreviated).locale(Locale(identifier: "es_PE"))).uppercased())
                                    .font(.caption2.bold())
                            }.foregroundStyle(Color.ukkuAzul).frame(width: 52, height: 60)
                                .background(Color.ukkuCeleste.opacity(0.18), in: .rect(cornerRadius: 16))
                            VStack(alignment: .leading, spacing: 5) {
                                Text(p.nombre).font(.headline).foregroundStyle(Color.tinta)
                                Text(r.pagosSinCubrir.contains(p) ? "Revisemos cómo cubrirlo" : "Ya considerado en tu disponible")
                                    .font(.caption).foregroundStyle(Color.secundaria)
                            }
                            Spacer(minLength: 2)
                            MoneyText(value: p.montoMinor).font(.subheadline.bold()).foregroundStyle(Color.tinta)
                        }
                    }
                }.buttonStyle(PressStyle()).accessibilityIdentifier("proximo-pago")
            }
        }
    }

    @ViewBuilder private var savings: some View {
        if let meta = store.estado.metas.first, let plan = store.estado.planes.first(where: { $0.refId == meta.id }) {
            Button { goal = plan } label: {
                Paper(color: Color.ukkuCeleste.opacity(0.16)) {
                    VStack(alignment: .leading, spacing: 16) {
                        HStack(alignment: .top) {
                            VStack(alignment: .leading, spacing: 5) {
                                Eyebrow(text: "Un paso hacia tu meta", color: .ukkuAzul)
                                Text(meta.titulo).font(.headline).foregroundStyle(Color.tinta)
                            }
                            Spacer()
                            Image(systemName: "arrow.up.right").foregroundStyle(Color.ukkuAzul)
                        }
                        ProgressView(value: Double(meta.ahorradoMinor), total: Double(max(1, meta.objetivoMinor)))
                            .tint(.ukkuAzul).accessibilityLabel("Progreso de \(meta.titulo)")
                        HStack {
                            Text("\(store.importe(meta.ahorradoMinor, decimales: false)) de \(store.importe(meta.objetivoMinor, decimales: false))")
                            Spacer()
                            Text("\(meta.ahorradoMinor * 100 / max(1, meta.objetivoMinor)) %").bold()
                        }.font(.caption).foregroundStyle(Color.ukkuAzul)
                    }
                }
            }.buttonStyle(PressStyle())
        }
    }

    private var recentActivity: some View {
        VStack(spacing: 6) {
            SectionHeading(title: "Últimos movimientos", action: "Ver todos") { store.tab = .actividad }
            Paper {
                VStack(spacing: 14) {
                    ForEach(store.estado.movimientos.sorted { $0.fecha > $1.fecha }.prefix(3)) { movement in
                        MovementRow(movement: movement)
                    }
                    Button { sheet = .movement } label: {
                        Label("Registrar movimiento", systemImage: "plus.circle.fill").font(.subheadline.bold()).frame(maxWidth: .infinity, minHeight: 44)
                    }.accessibilityIdentifier("nuevo-movimiento")
                }
            }
        }
    }
}

struct BreakdownScreen: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        let r = store.resumen
        NavigationStack {
            List {
                Section {
                    line("Saldo de tus cuentas", r.saldo)
                    line("Ingresos confirmados del ciclo", r.ingresosConfirmados, prefix: "+")
                    line("Pagos pendientes", r.pagosPendientes, prefix: "−")
                    line("Reservas de metas y planes", r.reservas, prefix: "−")
                    line("Colchón", r.colchon, prefix: "−")
                    line("Disponible del mes", r.disponible)
                    if r.faltante > 0 { line("Faltante", r.faltante) }
                } header: { Text("Cada sol tiene su lugar") } footer: {
                    Text("El saldo ya incluye los movimientos anteriores. Un pago reservado se descuenta una sola vez.")
                }
                Section("Tu margen diario") {
                    ForEach(r.puntos) { point in
                        VStack(alignment: .leading, spacing: 6) {
                            HStack { Text(point.etiqueta); Spacer(); MoneyText(value: max(0, point.permitido)) }
                            if point.limita { Label("Este punto limita el margen", systemImage: "flag.fill").font(.caption).foregroundStyle(Color.ukkuAzul) }
                        }
                    }
                    Text("Estimación local a 14 días con ingresos confirmados. Se toma el menor margen diario y se redondea hacia abajo a soles enteros.")
                        .font(.footnote).foregroundStyle(Color.secundaria)
                }
            }
            .navigationTitle("Así salen tus números").navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Listo") { dismiss() } } }
        }
    }
    private func line(_ title: String, _ value: Centimos, prefix: String = "") -> some View {
        HStack { Text(title); Spacer(); Text("\(prefix)\(store.importe(value))").monospacedDigit() }.font(.subheadline)
    }
}

struct PaymentsScreen: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @State private var selected: PagoConFecha?
    var body: some View {
        NavigationStack {
            List {
                Section {
                    ForEach(store.estado.pagos.filter { !$0.pagado }.sorted { $0.fecha < $1.fecha }) { payment in
                        Button { selected = payment } label: {
                            HStack(spacing: 12) {
                                Glyph(name: "calendar")
                                VStack(alignment: .leading, spacing: 5) {
                                    Text(payment.nombre).font(.headline).foregroundStyle(Color.tinta)
                                    Text(Fechas.corta(payment.fecha)).font(.caption).foregroundStyle(Color.secundaria)
                                }
                                Spacer()
                                MoneyText(value: payment.montoMinor).foregroundStyle(Color.tinta)
                            }.padding(.vertical, 4)
                        }
                    }
                } header: { Text("Por registrar") } footer: { Text("Toca un pago si ya lo hiciste y quieres registrarlo en la demo. Ukku no realiza pagos.") }
                Section("Registrados") {
                    ForEach(store.estado.pagos.filter(\.pagado)) { payment in
                        Label(payment.nombre, systemImage: "checkmark.circle.fill").foregroundStyle(Color.verde)
                    }
                }
            }
            .navigationTitle("Tus próximos pagos").navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Listo") { dismiss() } } }
            .sheet(item: $selected) { MovementEditor(payment: $0) }
        }
    }
}

import SwiftUI
import Charts

private enum ScenarioKind: String, CaseIterable, Identifiable {
    case expense = "Gasto", income = "Ingreso", both = "Ambos"
    var id: String { rawValue }
}

struct ScenarioScreen: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @Environment(\.ukkuQuieto) private var quieto
    @State private var kind: ScenarioKind = .expense
    @State private var expense = "100"
    @State private var income = "300"
    @State private var day = 3
    @FocusState private var editing: Bool

    private var scenario: EscenarioHipotetico? {
        guard let gasto = kind == .income ? 0 : Dinero.parse(expense),
              let ingreso = kind == .expense ? 0 : Dinero.parse(income),
              kind == .expense || ingreso > 0 else { return nil }
        return EscenarioHipotetico(gasto: gasto, ingresos: kind == .expense ? [] : [IngresoHipotetico(monto: ingreso, dia: day)])
    }
    private var result: ResultadoSimulacion? {
        scenario.flatMap { SimuladorLocal.evaluar($0, estado: store.estado, hoy: store.hoy) }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    PageTitle(title: "Antes de decidir…", subtitle: "Prueba una idea. Mira su impacto. Tus datos siguen igual.")
                    Picker("Qué quieres probar", selection: $kind) {
                        ForEach(ScenarioKind.allCases) { Text($0.rawValue).tag($0) }
                    }.pickerStyle(.segmented).accessibilityIdentifier("tipo-escenario")
                    Paper {
                        VStack(alignment: .leading, spacing: 18) {
                            if kind != .income {
                                amountField("Si gasto hoy", text: $expense, id: "gasto-simulacion")
                                ScrollView(.horizontal) {
                                    HStack(spacing: 8) {
                                        ForEach([50, 100, 300, 1500], id: \.self) { value in
                                            Button("S/ \(value)") { expense = String(value); editing = false }
                                                .font(.subheadline.bold()).padding(.horizontal, 15).frame(minHeight: 44)
                                                .foregroundStyle(expense == String(value) ? .white : Color.ukkuAzul)
                                                .background(expense == String(value) ? Color.ukkuAzul : Color.fondo, in: .capsule)
                                                .accessibilityIdentifier("monto-rapido-\(value)")
                                                .accessibilityAddTraits(expense == String(value) ? .isSelected : [])
                                        }
                                    }
                                }.scrollIndicators(.hidden)
                            }
                            if kind == .both { Divider() }
                            if kind != .expense {
                                amountField("Si recibo", text: $income, id: "ingreso-simulacion")
                                Stepper(value: $day, in: 0...14) {
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(day == 0 ? "Hoy" : "Dentro de \(day) días").font(.headline)
                                        Text(Fechas.corta(Fechas.cal.date(byAdding: .day, value: day, to: store.hoy)!))
                                            .font(.caption).foregroundStyle(Color.secundaria)
                                    }
                                }.accessibilityIdentifier("dia-ingreso")
                                Text("Solo suponemos que llega en esa fecha. No se registra como ingreso real.")
                                    .font(.caption).foregroundStyle(Color.secundaria)
                            }
                        }
                    }
                    if let result {
                        impact(result)
                        projection(result)
                    } else {
                        Paper { ErrorNotice(text: "Usa importes de hasta S/ 10,000, con un máximo de dos decimales. El ingreso debe ser mayor que cero.") }
                    }
                    DemoFootnote()
                }.padding(22)
            }
            .background(Color.fondo).scrollDismissesKeyboard(.interactively)
            .navigationTitle("Tu simulador").navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) { Button("Listo") { dismiss() }.accessibilityIdentifier("cerrar-simulador") }
                ToolbarItemGroup(placement: .keyboard) { Spacer(); Button("Terminar") { editing = false } }
            }
        }
    }

    private func amountField(_ label: String, text: Binding<String>, id: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label).font(.subheadline).foregroundStyle(Color.secundaria)
            HStack(alignment: .firstTextBaseline) {
                Text("S/").foregroundStyle(Color.secundaria)
                TextField("0", text: text).keyboardType(.decimalPad).focused($editing)
                    .accessibilityLabel("\(label), monto en soles").accessibilityIdentifier(id)
            }.font(.largeTitle.bold()).foregroundStyle(Color.ukkuAzul)
        }
    }

    private func impact(_ r: ResultadoSimulacion) -> some View {
        let warning = r.despues.faltante > 0 || r.cambiaCobertura
        return Paper {
            VStack(alignment: .leading, spacing: 20) {
                HStack(spacing: 10) {
                    UkkuPersonajeView(mood: warning ? .revisar : .bien, size: 65)
                    VStack(alignment: .leading, spacing: 4) {
                        Text(warning ? "Revisemos esa idea" : "Así cambia tu margen").font(.headline).foregroundStyle(Color.tinta)
                        Text(warning ? "Hay algo que conviene cuidar." : "Tus reservas siguen protegidas.").font(.caption).foregroundStyle(Color.secundaria)
                    }
                }
                comparison("Para usar hoy", before: r.antes.sugerenciaHoy ?? 0, after: r.despues.sugerenciaHoy ?? 0, id: "resultado-diario")
                Divider()
                comparison("Disponible este mes", before: r.antes.disponible, after: r.despues.disponible, id: "resultado-mensual")
                if r.despues.faltante > 0 {
                    ErrorNotice(text: "Faltarían \(store.importe(r.despues.faltante)) para cubrir tus pagos, reservas y colchón.")
                        .accessibilityIdentifier("alerta-simulacion")
                } else if r.cambiaCobertura {
                    ErrorNotice(text: "El total del mes alcanza, pero hay pagos anteriores al ingreso que necesitan atención.")
                        .accessibilityIdentifier("alerta-simulacion")
                }
                ForEach(r.despues.pagosSinCubrir) { p in
                    Label("\(p.nombre) · \(Fechas.corta(p.fecha))", systemImage: "calendar.badge.exclamationmark")
                        .font(.caption).foregroundStyle(Color.ambar)
                }
                if kind != .expense {
                    Text("El ingreso hipotético solo ayuda a partir del día elegido. No cubre pagos anteriores.")
                        .font(.caption).foregroundStyle(Color.secundaria)
                }
            }
        }
    }

    private func comparison(_ title: String, before: Centimos, after: Centimos, id: String) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title).font(.subheadline).foregroundStyle(Color.secundaria)
            HStack(alignment: .firstTextBaseline, spacing: 12) {
                MoneyText(value: before).foregroundStyle(Color.secundaria)
                Image(systemName: "arrow.right").font(.body).foregroundStyle(Color.secundaria).accessibilityHidden(true)
                MoneyText(value: after).foregroundStyle(Color.ukkuAzul).accessibilityIdentifier(id)
            }.font(.title2.bold()).lineLimit(1).minimumScaleFactor(0.6)
                .animation(quieto ? nil : .easeInOut(duration: 0.2), value: after)
        }
    }

    private func projection(_ r: ResultadoSimulacion) -> some View {
        Paper {
            VStack(alignment: .leading, spacing: 16) {
                Eyebrow(text: "Tu margen durante 14 días")
                if store.estado.ajustes.ocultarImportes {
                    Label("Gráfico oculto por privacidad", systemImage: "eye.slash").font(.subheadline).foregroundStyle(Color.secundaria)
                } else {
                    Chart {
                        RuleMark(y: .value("Sin margen", 0)).foregroundStyle(Color.secundaria.opacity(0.3))
                        ForEach(r.dias) { d in
                            LineMark(x: .value("Día", d.dia), y: .value("Soles", Double(d.antes) / 100), series: .value("Escenario", "Actual"))
                                .foregroundStyle(by: .value("Escenario", "Actual"))
                                .lineStyle(StrokeStyle(lineWidth: 2, dash: [4, 4])).interpolationMethod(.stepEnd)
                            LineMark(x: .value("Día", d.dia), y: .value("Soles", Double(d.despues) / 100), series: .value("Escenario", "Simulado"))
                                .foregroundStyle(by: .value("Escenario", "Simulado"))
                                .lineStyle(StrokeStyle(lineWidth: 3)).interpolationMethod(.stepEnd)
                        }
                    }
                    .chartForegroundStyleScale(["Actual": Color.secundaria.opacity(0.5), "Simulado": Color.ukkuAzul])
                    .chartXAxis { AxisMarks(values: [0, 7, 14]) { value in
                        AxisValueLabel { if let d = value.as(Int.self) { Text(d == 0 ? "Hoy" : "Día \(d)") } }
                    } }
                    .chartYAxis { AxisMarks(position: .leading) }
                    .frame(height: 165)
                    .accessibilityElement(children: .ignore)
                    .accessibilityLabel("Proyección del margen después de reservas y colchón. Al día 14, actual \(store.importe(r.dias.last!.antes)), simulado \(store.importe(r.dias.last!.despues)).")
                }
                Text("Se descuentan pagos, reservas y colchón. Cálculo de demostración, sin predicciones de IA.")
                    .font(.caption).foregroundStyle(Color.secundaria)
            }
        }
    }
}

import SwiftUI

struct SimuladorView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var cerrar
    @Environment(\.ukkuQuieto) private var quieto
    @State private var monto = "100"
    @FocusState private var escribiendo: Bool

    private var impacto: ImpactoSimulado? {
        Dinero.parse(monto).flatMap { SimuladorLocal.gasto($0, estado: store.estado, hoy: store.hoy) }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    VStack(alignment: .leading, spacing: 8) {
                        Label("ANTES DE DECIDIR", systemImage: "slider.horizontal.3")
                            .font(.caption.weight(.semibold)).tracking(1.4).foregroundStyle(Color.ukkuAzul)
                        Text("¿Y si gasto…?").font(.largeTitle.weight(.semibold)).foregroundStyle(Color.ukkuTinta)
                        Text("Prueba un monto y mira cómo cambia tu margen para los próximos pagos.")
                            .font(.ukCuerpo).foregroundStyle(Color.ukkuSecundario)
                    }
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Monto en soles").font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
                        HStack(alignment: .firstTextBaseline, spacing: 8) {
                            Text("S/").foregroundStyle(Color.ukkuSecundario)
                            TextField("100", text: $monto).keyboardType(.decimalPad)
                                .focused($escribiendo).accessibilityLabel("Gasto a simular en soles")
                                .accessibilityIdentifier("monto-simulacion")
                        }
                        .font(.system(size: 40, weight: .semibold).monospacedDigit())
                        .foregroundStyle(Color.ukkuAzul)
                        ViewThatFits {
                            HStack(spacing: 10) { montosRapidos }
                            VStack(alignment: .leading, spacing: 10) { montosRapidos }
                        }
                    }
                    .padding(20).background(Color.ukkuSuperficie, in: .rect(cornerRadius: 22))
                    if let i = impacto {
                        resultado(i)
                    } else {
                        Label("Escribe un monto mayor que cero, con hasta dos decimales.", systemImage: "info.circle")
                            .font(.ukCuerpo).foregroundStyle(Color.ukkuSecundario)
                    }
                    Label("Datos ficticios · Probar un monto no registra un gasto.", systemImage: "lock.shield")
                        .font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
                }
                .padding(24)
            }
            .scrollDismissesKeyboard(.interactively)
            .background(Color.white)
            .navigationTitle("Simular un gasto").navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) { Button("Listo") { cerrar() } }
                ToolbarItemGroup(placement: .keyboard) { Spacer(); Button("Terminar") { escribiendo = false } }
            }
        }
    }

    private var montosRapidos: some View {
        ForEach([50, 100, 300, 1500], id: \.self) { valor in
            Button("S/ \(valor)") { monto = String(valor); escribiendo = false }
                .font(.ukMeta.weight(.semibold)).foregroundStyle(monto == String(valor) ? .white : Color.ukkuAzul)
                .padding(.horizontal, 12).frame(minHeight: 44)
                .background(monto == String(valor) ? Color.ukkuAzul : Color.white, in: .capsule)
                .buttonStyle(FilaPresionable())
                .accessibilityAddTraits(monto == String(valor) ? .isSelected : [])
        }
    }

    private func resultado(_ i: ImpactoSimulado) -> some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack(spacing: 12) {
                UkkuPersonajeView(mood: i.despues.mood, size: 76)
                VStack(alignment: .leading, spacing: 5) {
                    Text(i.superaDisponible || i.afectaPagos ? "Mejor revisemos el monto" : "Así quedaría tu mes")
                        .font(.ukSeccion).foregroundStyle(Color.ukkuTinta)
                    Text(i.despues.mood.estadoCorto).font(.ukMeta).foregroundStyle(i.despues.mood.colorTexto)
                }
            }
            comparacion("Disponible del mes", antes: i.antes.disponible, despues: i.despues.disponible)
            Separador()
            if let antes = i.antes.sugerenciaHoy, let despues = i.despues.sugerenciaHoy {
                comparacion("Sugerencia diaria", antes: antes, despues: despues)
                Separador()
            }
            if i.despues.faltante > 0 {
                Label("Faltarían \(store.importe(i.despues.faltante)) para cubrir pagos, reservas y colchón.", systemImage: "exclamationmark.circle")
                    .foregroundStyle(Color.ukkuRojo).font(.ukCuerpo)
            } else if i.afectaPagos {
                Text("Este gasto deja algún pago sin cubrir en su fecha. Revisa los próximos vencimientos.")
                    .font(.ukCuerpo).foregroundStyle(Color.ukkuAmbar)
            } else {
                Text("El cálculo conserva tus reservas y tu colchón de \(store.importe(i.antes.colchon)).")
                    .font(.ukCuerpo).foregroundStyle(Color.ukkuSecundario)
            }
            Text("Estimación local con ingresos confirmados. No incluye predicciones de un modelo.")
                .font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
        }
        .animation(quieto ? nil : .smooth(duration: 0.3), value: i.gasto)
        .accessibilityElement(children: .contain)
    }

    private func comparacion(_ titulo: String, antes: Centimos, despues: Centimos) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(titulo).font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
            HStack(alignment: .firstTextBaseline, spacing: 12) {
                Text(store.importe(antes, decimales: false)).foregroundStyle(Color.ukkuSecundario)
                Image(systemName: "arrow.right").font(.ukMeta).foregroundStyle(Color.ukkuSecundario).accessibilityHidden(true)
                Text(store.importe(despues, decimales: false)).foregroundStyle(Color.ukkuAzul)
                    .contentTransition(.numericText())
            }
            .font(.title3.weight(.semibold).monospacedDigit())
            .minimumScaleFactor(0.65).lineLimit(1)
            .accessibilityElement(children: .ignore)
            .accessibilityLabel("\(titulo): de \(store.importe(antes)) a \(store.importe(despues))")
        }
    }
}

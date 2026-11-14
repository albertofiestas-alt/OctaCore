import SwiftUI

struct InicioView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.ukkuQuieto) private var quieto
    @State private var verSimulador = false
    @State private var verCalculo = false
    @State private var verVencimientos = false
    @State private var verInsights = false
    @State private var nuevoMovimiento = false
    @State private var detalle: Movimiento?
    @State private var revelado = false
    @ScaledMetric(relativeTo: .largeTitle) private var tamCifra: CGFloat = 44

    var body: some View {
        let r = store.resumen
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                cabecera(r)
                hero(r)
                    .opacity(revelado ? 1 : 0)
                    .offset(y: revelado ? 0 : 10)
                if r.hayDatos {
                    decisionHoy(r)
                    metricas(r)
                    insight(r)
                } else {
                    sinDatos
                }
                if r.hayDatos || !store.estado.movimientos.isEmpty { movimientos }
                AvisoDemo()
            }
            .padding(.horizontal, 24)
            .padding(.bottom, 24)
        }
        .background(Color.white)
        .safeAreaInset(edge: .top, spacing: 0) {
            // Evita que el contenido pase por debajo de la hora al desplazar.
            Color.clear.frame(height: 0).background(Color.white.ignoresSafeArea(edges: .top))
        }
        .toolbar(.hidden, for: .navigationBar)
        .sheet(isPresented: $verSimulador) { SimuladorView() }
        .sheet(isPresented: $verCalculo) { CalculoSheet() }
        .sheet(isPresented: $verVencimientos) { VencimientosSheet() }
        .sheet(isPresented: $verInsights) { InsightsSheet() }
        .sheet(isPresented: $nuevoMovimiento) { MovimientoFormView() }
        .sheet(item: $detalle) { MovimientoDetalleView(mov: $0) }
        .onAppear {
            // Una sola revelación sutil por arranque; con movimiento reducido aparece directo.
            guard !revelado else { return }
            if store.heroRevelado || quieto { revelado = true } else {
                store.heroRevelado = true
                withAnimation(.easeOut(duration: 0.45)) { revelado = true }
            }
        }
    }

    private func cabecera(_ r: Resumen) -> some View {
        let mes = Fechas.mes(r.ciclo.inicio)
        return HStack(spacing: 0) {
            VStack(alignment: .leading, spacing: 0) {
                Text("Hola, \(store.estado.ajustes.nombre)").font(.body.weight(.semibold)).foregroundStyle(Color.ukkuTinta)
                Text(mes.prefix(1).uppercased() + mes.dropFirst()).font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
            }
            Spacer()
            Button { nuevoMovimiento = true } label: {
                Image(systemName: UkkuIcon.agregar.rawValue)
                    .font(.system(size: 20, weight: .medium))
                    .foregroundStyle(Color.ukkuAzul)
                    .frame(width: 44, height: 44)
                    .contentShape(.rect)
            }
            .buttonStyle(FilaPresionable())
            .disabled(store.estado.cuentas.isEmpty)
            .accessibilityLabel("Agregar movimiento")
            Button { verVencimientos = true } label: {
                Image(systemName: UkkuIcon.notificaciones.rawValue)
                    .font(.system(size: 20, weight: .medium))
                    .foregroundStyle(Color.ukkuTinta)
                    .frame(width: 44, height: 44)
                    .contentShape(.rect)
            }
            .buttonStyle(FilaPresionable())
            .accessibilityLabel("Próximos vencimientos")
        }
        .padding(.top, 4)
    }

    // MARK: Hero: la única tarjeta protagonista

    private func hero(_ r: Resumen) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            ViewThatFits(in: .horizontal) {
                HStack(alignment: .center, spacing: 12) { oso(r); cifras(r, ajustar: false) }
                VStack(alignment: .leading, spacing: 4) { oso(r); cifras(r, ajustar: true) }
            }
            Separador()
            pie(r)
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.ukkuSuperficie, in: .rect(cornerRadius: 22))
    }

    private func oso(_ r: Resumen) -> some View {
        UkkuPersonajeView(mood: r.mood, size: 108)
    }

    private func cifras(_ r: Resumen, ajustar: Bool) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text("Disponible este mes").font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
            Text(r.hayDatos ? store.importe(r.disponible, decimales: false) : "Sin datos")
                .font(.system(size: r.hayDatos ? tamCifra : tamCifra * 0.68, weight: .semibold).monospacedDigit())
                .foregroundStyle(Color.ukkuAzul)
                .lineLimit(1)
                .minimumScaleFactor(ajustar ? 0.7 : 1)
                .contentTransition(.numericText())
                .animation(quieto ? nil : Movimiento_.cifra, value: r.disponible)

        }
        .fixedSize(horizontal: !ajustar, vertical: false)
        .accessibilityElement(children: .combine)
    }

    private func pie(_ r: Resumen) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            ViewThatFits(in: .horizontal) {
                HStack(alignment: .center, spacing: 8) {
                    estado(r).fixedSize()
                    Spacer(minLength: 8)
                    if r.hayDatos { enlaceCalculo.fixedSize() }
                }
                VStack(alignment: .leading, spacing: 0) {
                    estado(r)
                    if r.hayDatos { enlaceCalculo }
                }
            }
            if r.faltante > 0 {
                Text("Faltan \(store.importe(r.faltante)) para pagos, reservas y colchón.")
                    .font(.ukMeta).foregroundStyle(Color.ukkuTinta)
            }
            if r.mood == .atento, r.ingresosInciertos > 0 {
                Text("Si entran \(store.importe(r.ingresosInciertos)) aún sin confirmar, tus pagos quedan cubiertos.")
                    .font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
            }
            if r.mood == .revisar, let p = r.pagosSinCubrir.first {
                Text("\(p.nombre), \(Fechas.corta(p.fecha)): \(store.importe(p.montoMinor))")
                    .font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
            }
        }
    }

    private func estado(_ r: Resumen) -> some View {
        Label(r.mood.estadoCorto, systemImage: r.mood.simbolo).font(.ukCuerpoFuerte).foregroundStyle(r.mood.colorTexto)
    }
    private var enlaceCalculo: some View {
        Button("Ver cálculo") { verCalculo = true }.buttonStyle(BotonEnlace())
    }

    private func decisionHoy(_ r: Resumen) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(alignment: .firstTextBaseline) {
                Label("TU MARGEN PARA HOY", systemImage: "sun.max")
                    .font(.caption.weight(.semibold)).tracking(1)
                Spacer(minLength: 0)
                Text("DEMO").font(.caption2.weight(.semibold)).tracking(1)
                    .padding(.horizontal, 8).padding(.vertical, 5)
                    .background(.white.opacity(0.12), in: .capsule)
            }
            .foregroundStyle(.white.opacity(0.8))
            if let hoy = r.sugerenciaHoy {
                Text(store.importe(hoy, decimales: false))
                    .font(.system(.largeTitle, design: .rounded, weight: .semibold).monospacedDigit())
                    .contentTransition(.numericText())
                    .animation(quieto ? nil : Movimiento_.cifra, value: hoy)
            }
            Text("Una referencia diaria para cuidar tus próximos pagos.")
                .font(.ukCuerpo).foregroundStyle(.white.opacity(0.85))
            Button { verSimulador = true } label: {
                HStack {
                    Text("Simular un gasto")
                    Spacer()
                    Image(systemName: "arrow.up.right")
                }
                .font(.ukCuerpoFuerte).padding(14)
                .background(.white.opacity(0.13), in: .rect(cornerRadius: 14))
            }
            .buttonStyle(FilaPresionable()).accessibilityIdentifier("abrir-simulador")
        }
        .foregroundStyle(.white).padding(20)
        .background(LinearGradient(colors: [Color.ukkuAzul, Color(red: 0.05, green: 0.17, blue: 0.43)], startPoint: .topLeading, endPoint: .bottomTrailing), in: .rect(cornerRadius: 24))
    }

    // MARK: Dos métricas

    private func metricas(_ r: Resumen) -> some View {
        HStack(alignment: .top, spacing: 16) {
            metrica("Reservado", store.importe(r.reservas))
            Rectangle().fill(Color.ukkuDivisor).frame(width: 1, height: 40)
            if let p = r.proximoPago {
                metrica("\(p.nombre) · \(Fechas.corta(p.fecha))", store.importe(p.montoMinor))
            } else {
                metrica("Próximo pago", "Ninguno")
            }
        }
    }

    private func metrica(_ etiqueta: String, _ valor: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(etiqueta).font(.ukMeta).foregroundStyle(Color.ukkuSecundario).lineLimit(1)
            Text(valor).font(.ukCuerpoFuerte.monospacedDigit()).foregroundStyle(Color.ukkuTinta).lineLimit(1)
                .contentTransition(.numericText())
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityElement(children: .combine)
    }

    // MARK: Un insight destacado

    @ViewBuilder private func insight(_ r: Resumen) -> some View {
        let todos = Calculo.insights(store.estado, r)
        if let ins = todos.first {
            VStack(alignment: .leading, spacing: 4) {
                TituloSeccion(texto: "Ukku sugiere") {
                    if todos.count > 1 { Button("Ver más") { verInsights = true }.buttonStyle(BotonEnlace()) }
                }
                FilaInsight(insight: ins)
            }
        }
    }

    private var sinDatos: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Todavía no hay movimientos ni pagos").font(.ukSeccion).foregroundStyle(Color.ukkuTinta)
            Text("Ukku no muestra cifras hasta tener datos. Carga el ejemplo desde Ajustes.")
                .font(.ukCuerpo).foregroundStyle(Color.ukkuSecundario)
            Button("Ir a Ajustes") { store.tab = .ajustes }.buttonStyle(BotonEnlace())
        }
    }

    // MARK: Movimientos

    private var movimientos: some View {
        let recientes = store.estado.movimientos.sorted { $0.fecha > $1.fecha }.prefix(3)
        return VStack(alignment: .leading, spacing: 0) {
            TituloSeccion(texto: "Movimientos") {
                if !recientes.isEmpty { NavigationLink("Ver todos") { MovimientosListaView() }.buttonStyle(BotonEnlace()) }
            }
            if recientes.isEmpty {
                Text("Aún no hay movimientos.").font(.ukCuerpo).foregroundStyle(Color.ukkuSecundario).padding(.vertical, 12)
            }
            ForEach(Array(recientes)) { m in
                Button { detalle = m } label: { FilaMovimiento(mov: m) }.buttonStyle(FilaPresionable())
                Separador()
            }
        }
    }
}

struct FilaInsight: View {
    @Environment(AppStore.self) private var store
    let insight: Insight
    var alTocar: () -> Void = {}
    var body: some View {
        Button {
            alTocar()
            store.contextoChat = insight.contexto
            store.tab = .plan
        } label: {
            HStack(alignment: .top, spacing: 12) {
                IconoFila(simbolo: insight.icono)
                VStack(alignment: .leading, spacing: 2) {
                    Text(store.estado.ajustes.ocultarImportes ? insight.accion : insight.titulo)
                        .font(.ukCuerpo).foregroundStyle(Color.ukkuTinta).multilineTextAlignment(.leading)
                    Text(insight.accion).font(.ukMeta.weight(.medium)).foregroundStyle(Color.ukkuAzul)
                }
                Spacer(minLength: 8)
                Image(systemName: UkkuIcon.detalle.rawValue).font(.footnote.weight(.semibold)).foregroundStyle(Color.ukkuSecundario)
            }
            .padding(.vertical, 10)
        }
        .buttonStyle(FilaPresionable())
    }
}

struct InsightsSheet: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var cerrar
    var body: some View {
        let todos = Calculo.insights(store.estado, store.resumen)
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    ForEach(todos) { ins in
                        FilaInsight(insight: ins) { cerrar() }
                        if !store.estado.ajustes.ocultarImportes {
                            Text(ins.fundamento).font(.ukMeta).foregroundStyle(Color.ukkuSecundario).padding(.leading, 40).padding(.bottom, 10)
                        }
                        Separador()
                    }
                    Text("Son resúmenes calculados con tus datos de demostración, no respuestas de IA.")
                        .font(.ukMeta).foregroundStyle(Color.ukkuSecundario).padding(.top, 16)
                }
                .padding(24)
            }
            .navigationTitle("Ukku sugiere")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Listo") { cerrar() } } }
        }
        .presentationDetents([.medium, .large])
    }
}

enum FiltroMov: String, CaseIterable, Identifiable {
    case todos, gastos, ingresos
    var id: String { rawValue }
    var nombre: String { rawValue.capitalized }
    func incluye(_ m: Movimiento) -> Bool {
        switch self {
        case .todos: true
        case .gastos: m.montoMinor < 0
        case .ingresos: m.montoMinor > 0
        }
    }
}

struct CalculoSheet: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var cerrar

    var body: some View {
        let r = store.resumen
        NavigationStack {
            List {
                Section {
                    fila("Saldo actual de tus cuentas", r.saldo)
                    fila("Ingresos confirmados que faltan entrar", r.ingresosConfirmados, signo: "+")
                    fila("Pagos fijos pendientes", r.pagosPendientes, signo: "−")
                    fila("Reservas de metas y planes", r.reservas, signo: "−")
                    fila("Colchón mínimo", r.colchon, signo: "−")
                    HStack {
                        Text("Disponible estimado del mes").font(.headline)
                        Spacer()
                        Text(store.importe(r.disponible)).font(.headline.monospacedDigit()).foregroundStyle(Color.ukkuAzul)
                    }
                    if r.faltante > 0 { fila("Faltante", r.faltante) }
                } header: { Text("Disponible del mes") } footer: {
                    Text("El saldo ya incluye los movimientos pasados, por eso no se restan otra vez. Los ingresos sin confirmar no cuentan como efectivo.")
                }
                if r.ingresosInciertos > 0 {
                    Section("Escenario, no confirmado") { fila("Ingresos por confirmar", r.ingresosInciertos) }
                }
                Section {
                    ForEach(r.puntos) { p in
                        HStack {
                            VStack(alignment: .leading) {
                                Text(p.etiqueta)
                                Text(p.limita ? "Este punto limita tu día" : "En \(p.dia) días").font(.footnote)
                                    .foregroundStyle(p.limita ? Color.ukkuAzul : Color.ukkuSecundario)
                            }
                            Spacer()
                            Text("\(store.importe(p.permitido)) al día").monospacedDigit().fontWeight(p.limita ? .semibold : .regular)
                        }
                    }
                } header: { Text("Sugerencia para hoy: \(r.sugerenciaHoy.map { store.importe($0, decimales: false) } ?? "sin datos")") } footer: {
                    Text("Regla de demostración a 14 días: para cada pago con fecha se divide lo que queda entre los días que faltan y se toma el menor valor. Usa solo ingresos confirmados. No es un modelo entrenado; el motor de OctaCore la reemplaza cuando esté conectado.")
                }
                Section("Estado de tus pagos") {
                    Label(r.mood.label, systemImage: r.mood.simbolo).foregroundStyle(r.mood.colorTexto)
                    Text("Se evalúa pago por pago según su fecha, no solo con la suma del mes.").font(.footnote).foregroundStyle(Color.ukkuSecundario)
                }
            }
            .navigationTitle("Cómo se calcula")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Listo") { cerrar() } } }
        }
    }

    private func fila(_ t: String, _ c: Centimos, signo: String = "") -> some View {
        HStack {
            Text(t)
            Spacer()
            Text("\(signo) \(store.importe(c))").monospacedDigit().foregroundStyle(Color.ukkuSecundario)
        }
        .accessibilityElement(children: .combine)
    }
}

struct VencimientosSheet: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var cerrar
    var body: some View {
        let pagos = store.estado.pagos.filter { !$0.pagado }.sorted { $0.fecha < $1.fecha }
        let planes = store.estado.planes.filter { $0.estado == .necesitaConfirmacion }
        NavigationStack {
            List {
                Section("Pagos pendientes") {
                    if pagos.isEmpty { Text("No tienes pagos pendientes.").foregroundStyle(Color.ukkuSecundario) }
                    ForEach(pagos) { p in
                        LabeledContent("\(p.nombre), \(Fechas.corta(p.fecha))", value: store.importe(p.montoMinor))
                    }
                }
                Section("Planes que esperan tu confirmación") {
                    if planes.isEmpty { Text("Ninguno por ahora.").foregroundStyle(Color.ukkuSecundario) }
                    ForEach(planes) { p in Label(p.titulo, systemImage: p.estado.icono) }
                }
            }
            .navigationTitle("Vencimientos")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Listo") { cerrar() } } }
        }
        .presentationDetents([.medium, .large])
    }
}

struct MovimientosListaView: View {
    @Environment(AppStore.self) private var store
    @State private var filtro = FiltroMov.todos
    @State private var detalle: Movimiento?
    @State private var nuevo = false
    var body: some View {
        let lista = store.estado.movimientos.sorted { $0.fecha > $1.fecha }.filter(filtro.incluye)
        List {
            Picker("Filtro", selection: $filtro) { ForEach(FiltroMov.allCases) { Text($0.nombre).tag($0) } }
                .pickerStyle(.segmented).listRowSeparator(.hidden)
            if lista.isEmpty {
                VStack(spacing: 8) {
                    EscenaUkku(escena: .sinMovimientos, size: 120)
                    Text("No hay movimientos.").foregroundStyle(Color.ukkuSecundario)
                }
                .frame(maxWidth: .infinity).listRowSeparator(.hidden)
            }
            ForEach(lista) { m in
                Button { detalle = m } label: { FilaMovimiento(mov: m).contentShape(.rect) }.buttonStyle(.plain)
            }
        }
        .listStyle(.plain)
        .navigationTitle("Movimientos")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button { nuevo = true } label: { Label("Agregar movimiento", systemImage: UkkuIcon.agregar.rawValue) }
                    .disabled(store.estado.cuentas.isEmpty)
            }
        }
        .sheet(isPresented: $nuevo) { MovimientoFormView() }
        .sheet(item: $detalle) { MovimientoDetalleView(mov: $0) }
    }
}

struct MovimientoDetalleView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var cerrar
    let mov: Movimiento
    @State private var confirmar = false
    var body: some View {
        NavigationStack {
            List {
                LabeledContent("Monto", value: store.importe(mov.montoMinor, signo: true))
                LabeledContent("Comercio", value: mov.comercio)
                LabeledContent("Categoría", value: store.categoria(mov.categoriaId).nombre)
                LabeledContent("Fecha", value: Fechas.corta(mov.fecha))
                LabeledContent("Cuenta", value: store.estado.cuentas.first { $0.id == mov.cuentaId }?.nombre ?? "Cuenta demo")
                LabeledContent("Origen", value: "Dato de demostración")
                Button("Eliminar movimiento", role: .destructive) { confirmar = true }
            }
            .navigationTitle("Detalle")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Listo") { cerrar() } } }
            .confirmationDialog("Se eliminará el movimiento y el saldo de la cuenta demo volverá a su valor anterior.", isPresented: $confirmar, titleVisibility: .visible) {
                Button("Eliminar movimiento", role: .destructive) { store.eliminarMovimiento(mov.id); cerrar() }
            }
        }
        .presentationDetents([.medium])
    }
}

struct MovimientoFormView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var cerrar
    @State private var esGasto = true
    @State private var monto = ""
    @State private var comercio = ""
    @State private var categoria = "groceries"
    @State private var fecha = Date()
    @State private var pago: UUID?
    @State private var error: String?
    @FocusState private var foco: Bool

    var body: some View {
        let pendientes = store.estado.pagos.filter { !$0.pagado }
        NavigationStack {
            Form {
                Section {
                    Picker("Tipo", selection: $esGasto) {
                        Text("Gasto").tag(true)
                        Text("Ingreso").tag(false)
                    }
                    .pickerStyle(.segmented)
                    TextField("Monto en soles", text: $monto).keyboardType(.decimalPad).focused($foco)
                        .accessibilityIdentifier("monto")
                    TextField("Comercio o descripción", text: $comercio)
                    Picker("Categoría", selection: $categoria) {
                        ForEach(store.estado.categorias) { Text($0.nombre).tag($0.id) }
                    }
                    DatePicker("Fecha", selection: $fecha, in: ...Date(), displayedComponents: .date)
                } footer: { Text("Se guarda en la cuenta demo. No mueve dinero real.") }
                if esGasto, !pendientes.isEmpty {
                    Section {
                        Picker("Corresponde a", selection: $pago) {
                            Text("Ningún pago pendiente").tag(UUID?.none)
                            ForEach(pendientes) { Text("\($0.nombre), \(Dinero.texto($0.montoMinor))").tag(UUID?.some($0.id)) }
                        }
                    } footer: { Text("Si eliges un pago, se marca como registrado y deja de descontarse dos veces.") }
                }
                if let error { Section { Label(error, systemImage: "exclamationmark.circle").foregroundStyle(Color.ukkuRojo) } }
            }
            .navigationTitle("Movimiento")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancelar") { cerrar() } }
                ToolbarItem(placement: .confirmationAction) { Button("Guardar") { guardar() } }
            }
            .onChange(of: esGasto) { _, gasto in categoria = gasto ? "groceries" : "income" }
            .onAppear { foco = true }
        }
    }

    private func guardar() {
        guard let c = Dinero.parse(monto), c > 0 else { error = "Escribe un monto mayor que cero, por ejemplo 25.50."; return }
        guard !comercio.trimmingCharacters(in: .whitespaces).isEmpty else { error = "Escribe el comercio o una descripción."; return }
        guard let cuenta = store.estado.cuentas.first else { error = "No hay una cuenta demo."; return }
        let p = store.propuesta("record_demo_transaction", [
            "account_id": .s(cuenta.id), "amount_minor_signed": .i(esGasto ? -c : c), "currency": .s("PEN"),
            "category_id": .s(categoria), "date": .s(Fechas.iso(fecha)), "merchant": .s(comercio.trimmingCharacters(in: .whitespaces)),
        ], fuente: .manual)
        switch store.aplicar(p) {
        case .success:
            if let pago { store.marcarPagoPagado(pago) }
            cerrar()
        case .failure(let e): error = e.mensaje
        }
    }
}

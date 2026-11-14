import SwiftUI

struct ActividadView: View {
    @Environment(AppStore.self) private var store
    @State private var seccion = 0
    @State private var crear = false
    @State private var comoFunciona = false
    @State private var ruta: [UUID] = []

    var body: some View {
        NavigationStack(path: $ruta) {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    Cabecera(titulo: "Tus planes") {
                        HStack(spacing: 0) {
                            Button { comoFunciona = true } label: {
                                Image(systemName: "info.circle").font(.system(size: 20, weight: .medium)).foregroundStyle(Color.ukkuSecundario)
                                    .frame(width: 44, height: 44).contentShape(.rect)
                            }
                            .buttonStyle(FilaPresionable())
                            .accessibilityLabel("Cómo funciona")
                            Button { crear = true } label: {
                                Image(systemName: UkkuIcon.agregar.rawValue).font(.system(size: 17, weight: .semibold)).foregroundStyle(.white)
                                    .frame(width: 36, height: 36).background(Color.ukkuAzul, in: .circle)
                                    .frame(width: 44, height: 44).contentShape(.rect)
                            }
                            .buttonStyle(FilaPresionable())
                            .accessibilityLabel("Crear plan")
                        }
                    }
                    Picker("Sección", selection: $seccion) {
                        Text("Planes").tag(0)
                        Text("Historial").tag(1)
                    }
                    .pickerStyle(.segmented)
                    if seccion == 0 { planes } else { historial }
                }
                .padding(.horizontal, 24).padding(.bottom, 24)
            }
            .background(Color.white)
        .safeAreaInset(edge: .top, spacing: 0) {
            // Evita que el contenido pase por debajo de la hora al desplazar.
            Color.clear.frame(height: 0).background(Color.white.ignoresSafeArea(edges: .top))
        }
            .toolbar(.hidden, for: .navigationBar)
            .navigationDestination(for: UUID.self) { PlanDetalleView(planId: $0) }
            .sheet(isPresented: $crear) { PlanFormView(plan: nil) }
            .sheet(isPresented: $comoFunciona) { ComoFuncionaSheet() }
            .onAppear(perform: abrirDestacado)
            .onChange(of: store.planDestacado) { abrirDestacado() }
        }
    }

    private func abrirDestacado() {
        guard let id = store.planDestacado else { return }
        store.planDestacado = nil
        seccion = 0
        ruta = [id]
    }

    /// Cada plan cae en un solo grupo; los atrasados van a «Por revisar» o «Esta semana», nunca se ocultan.
    private var grupos: [(titulo: String, planes: [Plan])] {
        let hoy0 = Fechas.inicioDia(store.hoy)
        var revisar: [Plan] = [], semana: [Plan] = [], luego: [Plan] = [], otros: [Plan] = []
        for p in store.estado.planes.sorted(by: { $0.fecha < $1.fecha }) {
            switch p.estado {
            case .necesitaConfirmacion, .error: revisar.append(p)
            case .programado, .enCurso:
                if Fechas.dias(de: hoy0, a: p.fecha) <= 7 { semana.append(p) } else { luego.append(p) }
            case .pausado, .completado, .borrador: otros.append(p)
            }
        }
        return [("Por revisar", revisar), ("Esta semana", semana), ("Más adelante", luego), ("Pausados y terminados", otros)]
            .filter { !$0.1.isEmpty }.map { (titulo: $0.0, planes: $0.1) }
    }

    @ViewBuilder private var planes: some View {
        let todos = store.estado.planes
        let activos = todos.filter { $0.estado.activo }
        let porRevisar = todos.filter { $0.estado == .necesitaConfirmacion || $0.estado == .error }.count
        let proximo = activos.filter { $0.tipo != .presupuesto }.min { $0.fecha < $1.fecha }
        VStack(alignment: .leading, spacing: 4) {
            Text(activos.isEmpty ? "Sin planes activos"
                 : porRevisar == 0 ? "\(activos.count) \(activos.count == 1 ? "plan" : "planes") al día"
                 : "\(activos.count - porRevisar) al día · \(porRevisar) por revisar")
                .font(.ukSeccion).foregroundStyle(Color.ukkuTinta)
            if let proximo {
                Text("Próximo: \(proximo.titulo), \(Fechas.corta(proximo.fecha))").font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
            }
            ForEach(Calculo.logros(store.estado, store.resumen)) { l in
                Text(l.texto).font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
            }
        }
        if todos.isEmpty {
            VStack(alignment: .leading, spacing: 4) {
                EscenaUkku(escena: .planificando, size: 112)
                Text("Aún no tienes planes").font(.ukCuerpoFuerte).foregroundStyle(Color.ukkuTinta)
                Text("Crea el primero con el botón + o pídeselo a Ukku.").font(.ukCuerpo).foregroundStyle(Color.ukkuSecundario)
            }
        }
        ForEach(grupos, id: \.titulo) { grupo in
            VStack(alignment: .leading, spacing: 0) {
                Text(grupo.titulo).font(.ukMeta.weight(.semibold)).foregroundStyle(Color.ukkuSecundario)
                    .padding(.bottom, 4).accessibilityAddTraits(.isHeader)
                ForEach(grupo.planes) { p in
                    NavigationLink(value: p.id) { FilaPlan(plan: p) }.buttonStyle(FilaPresionable())
                    Separador()
                }
            }
        }
    }

    private var historial: some View {
        let eventos = store.estado.ejecuciones.sorted { $0.fecha > $1.fecha }
        return VStack(alignment: .leading, spacing: 0) {
            if eventos.isEmpty {
                Text("Aquí aparece cada plan que crees, edites o completes.").font(.ukCuerpo).foregroundStyle(Color.ukkuSecundario)
            }
            ForEach(eventos) { ev in
                HStack(alignment: .top, spacing: 12) {
                    IconoFila(simbolo: icono(ev.tipo), color: .ukkuSecundario)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(store.estado.ajustes.ocultarImportes ? ev.tipo.rawValue.capitalized : ev.resumen).font(.ukCuerpo).foregroundStyle(Color.ukkuTinta)
                        Text(Fechas.larga(ev.fecha)).font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
                    }
                }
                .padding(.vertical, 12)
                Separador()
            }
        }
    }

    private func icono(_ t: Ejecucion.Tipo) -> String {
        switch t {
        case .creado, .presupuesto: "plus.circle"
        case .editado: "pencil.circle"
        case .pausado: UkkuIcon.pausar.rawValue
        case .reanudado: UkkuIcon.reanudar.rawValue
        case .reprogramado: UkkuIcon.calendario.rawValue
        case .vencimiento: "clock.badge.exclamationmark"
        case .completado: "checkmark.circle"
        case .eliminado: "trash"
        case .aporte: UkkuIcon.ahorro.rawValue
        case .movimiento: UkkuIcon.transacciones.rawValue
        }
    }
}

struct ComoFuncionaSheet: View {
    @Environment(\.dismiss) private var cerrar
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    punto("Todo ocurre dentro de Ukku", "Crear, pausar o completar un plan actualiza tus datos en la app. No se paga ni se cancela ningún servicio externo.")
                    punto("Las fechas son recordatorios", "Cuando un plan llega a su fecha, pasa a «Por revisar» para que confirmes si ya lo hiciste. Ukku no cobra de forma automática.")
                    punto("El avance sale de tus datos", "Metas y presupuestos avanzan con los movimientos y aportes que registres. Los planes marcados como demo son de ejemplo.")
                }
                .padding(24)
            }
            .navigationTitle("Cómo funciona")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Listo") { cerrar() } } }
        }
        .presentationDetents([.medium])
    }
    private func punto(_ t: String, _ d: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(t).font(.ukCuerpoFuerte).foregroundStyle(Color.ukkuTinta)
            Text(d).font(.ukCuerpo).foregroundStyle(Color.ukkuSecundario)
        }
    }
}

struct FilaPlan: View {
    @Environment(AppStore.self) private var store
    let plan: Plan
    @Environment(\.ukkuQuieto) private var quieto
    @State private var lleno = false
    var body: some View {
        let prog = Calculo.progreso(plan, store.estado, hoy: store.hoy)
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .firstTextBaseline) {
                Text(plan.titulo).font(.ukCuerpo.weight(.medium)).foregroundStyle(Color.ukkuTinta).lineLimit(2).multilineTextAlignment(.leading)
                Spacer(minLength: 12)
                if plan.importeMinor > 0 {
                    Text(store.importe(plan.importeMinor, decimales: false)).font(.ukCuerpo.monospacedDigit()).foregroundStyle(Color.ukkuTinta)
                }
            }
            HStack(spacing: 6) {
                Text(Fechas.corta(plan.fecha)).font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
                Text("·").font(.ukMeta).foregroundStyle(Color.ukkuSecundario).accessibilityHidden(true)
                EtiquetaEstado(estado: plan.estado)
            }
            // Progreso solo donde representa algo real: metas y presupuestos.
            if plan.tipo == .meta || plan.tipo == .presupuesto {
                ProgressView(value: lleno || quieto ? prog.valor : 0)
                    .tint(plan.tipo == .presupuesto && prog.valor >= 1 ? .ukkuRojo : .ukkuAzul)
                    .scaleEffect(x: 1, y: 0.6, anchor: .center)
                    .animation(quieto ? nil : .easeOut(duration: 0.5), value: lleno)
                    .onAppear { lleno = true }
                Text(store.estado.ajustes.ocultarImportes ? "\(Int(prog.valor * 100)) %" : prog.texto).font(.caption).foregroundStyle(Color.ukkuSecundario)
            }
        }
        .padding(.vertical, 12)
        .frame(minHeight: 60)
        .accessibilityElement(children: .combine)
    }
}

struct PlanDetalleView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var cerrar
    let planId: UUID
    @State private var editar = false
    @State private var eliminar = false
    @State private var reprogramar = false
    @State private var aportar = false
    @State private var nuevaFecha = Date()
    @State private var aporte = ""
    @State private var error: String?

    var body: some View {
        if let plan = store.estado.planes.first(where: { $0.id == planId }) {
            let prog = Calculo.progreso(plan, store.estado, hoy: store.hoy)
            List {
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        EtiquetaEstado(estado: plan.estado)
                        Text(plan.titulo).font(.title2.weight(.bold)).foregroundStyle(Color.ukkuTinta)
                        if plan.tipo != .recordatorio {
                            ProgressView(value: prog.valor).tint(.ukkuAzul)
                            Text(store.estado.ajustes.ocultarImportes ? "\(Int(prog.valor * 100)) %" : prog.texto).font(.subheadline).foregroundStyle(Color.ukkuSecundario)
                        }
                    }
                    .padding(.vertical, 4)
                }
                Section("Detalle") {
                    LabeledContent("Tipo", value: plan.tipo.nombre)
                    if plan.importeMinor > 0 { LabeledContent("Importe", value: store.importe(plan.importeMinor)) }
                    LabeledContent(plan.tipo == .recordatorio ? "Aviso" : "Fecha", value: plan.tipo == .recordatorio ? Fechas.larga(plan.fecha) : Fechas.corta(plan.fecha))
                    LabeledContent("Periodicidad", value: plan.periodicidad.nombre)
                    LabeledContent("Categoría", value: store.categoria(plan.categoriaId).nombre)
                    LabeledContent("Origen", value: plan.origen.nombre + (plan.esDemo ? " (dato demo)" : ""))
                    LabeledContent("ID", value: String(plan.id.uuidString.prefix(8)))
                }
                Section {
                    if plan.estado == .necesitaConfirmacion {
                        Button("Marcar como hecho", systemImage: "checkmark.circle") { store.marcarHecho(plan.id) }
                    }
                    if plan.tipo == .meta, plan.estado.activo {
                        Button("Registrar un aporte", systemImage: UkkuIcon.ahorro.rawValue) { aporte = ""; error = nil; aportar = true }
                    }
                    if plan.estado != .completado {
                        Button("Editar", systemImage: "pencil") { editar = true }
                    }
                    if plan.estado.activo {
                        Button("Pausar", systemImage: UkkuIcon.pausar.rawValue) {
                            _ = store.aplicar(store.propuesta("pause_plan", ["plan_id": .s(plan.id.uuidString)], fuente: .manual))
                        }
                    }
                    if plan.estado == .pausado {
                        Button("Reanudar", systemImage: UkkuIcon.reanudar.rawValue) { store.reanudar(plan.id) }
                    }
                    if plan.estado != .completado, plan.tipo != .presupuesto {
                        Button("Reprogramar", systemImage: UkkuIcon.calendario.rawValue) { nuevaFecha = max(plan.fecha, Date()); reprogramar = true }
                    }
                    Button("Eliminar plan", systemImage: "trash", role: .destructive) { eliminar = true }
                } footer: {
                    Text(plan.tipo == .reserva || plan.tipo == .recordatorio
                         ? "Ukku te recuerda la fecha y lleva la cuenta. No realiza el pago ni cancela servicios por ti."
                         : "El progreso se calcula con los movimientos y aportes registrados en la app.")
                }
                if let error { Section { Label(error, systemImage: "exclamationmark.circle").foregroundStyle(Color.ukkuRojo) } }
            }
            .navigationTitle("Plan")
            .navigationBarTitleDisplayMode(.inline)
            .sheet(isPresented: $editar) { PlanFormView(plan: plan) }
            .confirmationDialog("Se eliminará «\(plan.titulo)» y se liberará lo que tenía reservado. Esta acción no se puede deshacer.", isPresented: $eliminar, titleVisibility: .visible) {
                Button("Eliminar plan", role: .destructive) { store.eliminarPlan(plan.id); cerrar() }
            }
            .sheet(isPresented: $reprogramar) {
                NavigationStack {
                    Form { DatePicker("Nueva fecha", selection: $nuevaFecha, in: Date()..., displayedComponents: .date).datePickerStyle(.graphical) }
                        .navigationTitle("Reprogramar").navigationBarTitleDisplayMode(.inline)
                        .toolbar {
                            ToolbarItem(placement: .cancellationAction) { Button("Cancelar") { reprogramar = false } }
                            ToolbarItem(placement: .confirmationAction) {
                                Button("Guardar fecha") {
                                    let r = store.aplicar(store.propuesta("reschedule_plan", ["plan_id": .s(plan.id.uuidString), "due_date": .s(Fechas.iso(nuevaFecha))], fuente: .manual))
                                    if case .failure(let e) = r { error = e.mensaje }
                                    reprogramar = false
                                }
                            }
                        }
                }
            }
            .alert("Registrar un aporte", isPresented: $aportar) {
                TextField("Monto en soles", text: $aporte).keyboardType(.decimalPad)
                Button("Cancelar", role: .cancel) {}
                Button("Guardar aporte") { error = store.aportar(plan.id, monto: Dinero.parse(aporte) ?? 0) }
            } message: { Text("El monto se separa de tu disponible y pasa a la meta, dentro de Ukku.") }
        } else {
            ContentUnavailableView("Este plan ya no existe", systemImage: "tray")
        }
    }
}

/// Formulario completo sin IA. Crear usa la misma capa de acciones que el chat.
struct PlanFormView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var cerrar
    let plan: Plan?
    @State private var tipo = TipoPlan.reserva
    @State private var titulo = ""
    @State private var monto = ""
    @State private var fecha = Date()
    @State private var periodicidad = Periodicidad.none
    @State private var categoria = "housing"
    @State private var error: String?

    var body: some View {
        NavigationStack {
            Form {
                if plan == nil {
                    Section {
                        Picker("Tipo de plan", selection: $tipo) { ForEach(TipoPlan.allCases) { Text($0.nombre).tag($0) } }
                    } footer: { Text(ayuda) }
                }
                Section {
                    if tipo != .presupuesto { TextField("Nombre del plan", text: $titulo).accessibilityIdentifier("nombre") }
                    if tipo != .recordatorio { TextField(tipo == .presupuesto ? "Límite mensual en soles" : "Importe en soles", text: $monto).keyboardType(.decimalPad).accessibilityIdentifier("importe") }
                    if tipo == .recordatorio {
                        DatePicker("Fecha y hora", selection: $fecha, in: Date()...)
                    } else if tipo != .presupuesto {
                        DatePicker(tipo == .meta ? "Fecha objetivo" : "Fecha", selection: $fecha, in: Date()..., displayedComponents: .date)
                    }
                    if tipo == .reserva {
                        Picker("Periodicidad", selection: $periodicidad) { ForEach(Periodicidad.allCases) { Text($0.nombre).tag($0) } }
                    }
                    if tipo == .reserva || tipo == .presupuesto {
                        Picker("Categoría", selection: $categoria) {
                            ForEach(store.estado.categorias.filter { $0.id != "income" }) { Text($0.nombre).tag($0.id) }
                        }
                    }
                }
                if let error { Section { Label(error, systemImage: "exclamationmark.circle").foregroundStyle(Color.ukkuRojo) } }
            }
            .navigationTitle(plan == nil ? "Crear plan" : "Editar plan")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancelar") { cerrar() } }
                ToolbarItem(placement: .confirmationAction) { Button(plan == nil ? "Crear" : "Guardar") { guardar() } }
            }
            .onAppear {
                guard let plan else { fecha = Fechas.cal.date(byAdding: .day, value: 7, to: Date())!; return }
                tipo = plan.tipo; titulo = plan.titulo; fecha = max(plan.fecha, Date())
                monto = String(format: "%d.%02d", plan.importeMinor / 100, plan.importeMinor % 100)
                periodicidad = plan.periodicidad; categoria = plan.categoriaId
            }
        }
    }

    private var ayuda: String {
        switch tipo {
        case .reserva: "Separa un monto dentro de Ukku para un pago con fecha. Ukku no hace el pago."
        case .presupuesto: "Un límite de gasto mensual para una categoría. El avance sale de tus movimientos."
        case .meta: "Un objetivo de ahorro con fecha. Avanza con los aportes que registres."
        case .recordatorio: "Un aviso en la fecha que elijas. No ejecuta ninguna operación."
        }
    }

    private func guardar() {
        let nombre = titulo.trimmingCharacters(in: .whitespaces)
        let c = Dinero.parse(monto) ?? 0
        if tipo != .presupuesto, nombre.isEmpty { error = "Escribe un nombre para el plan."; return }
        if tipo != .recordatorio, c <= 0 { error = "Escribe un importe mayor que cero, por ejemplo 100."; return }
        if let plan {
            store.editarPlan(plan.id, titulo: tipo == .presupuesto ? "Presupuesto de \(store.categoria(categoria).nombre)" : nombre,
                             importe: c, fecha: tipo == .presupuesto ? plan.fecha : fecha, periodicidad: periodicidad, categoriaId: categoria)
            cerrar()
            return
        }
        let ciclo = store.resumen.ciclo
        let p: PropuestaAccion = switch tipo {
        case .reserva: store.propuesta("create_plan", ["title": .s(nombre), "amount_minor": .i(c), "currency": .s("PEN"), "due_date": .s(Fechas.iso(fecha)),
                                                       "category_id": .s(categoria), "recurrence": .s(periodicidad.rawValue)], fuente: .manual)
        case .presupuesto: store.propuesta("set_category_budget", ["category_id": .s(categoria), "amount_minor": .i(c), "currency": .s("PEN"), "cycle_id": .s(ciclo.id)], fuente: .manual)
        case .meta: store.propuesta("create_savings_goal", ["title": .s(nombre), "target_minor": .i(c), "currency": .s("PEN"), "target_date": .s(Fechas.iso(fecha))], fuente: .manual)
        case .recordatorio: store.propuesta("create_reminder", ["title": .s(nombre), "local_datetime": .s(Fechas.isoHora(fecha)), "timezone": .s("America/Lima")], fuente: .manual)
        }
        switch store.aplicar(p) {
        case .success: cerrar()
        case .failure(let e): error = e.mensaje
        }
    }
}

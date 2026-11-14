import SwiftUI

struct PlanUkkuView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.ukkuQuieto) private var quieto
    @State private var texto = ""
    @State private var editando: MensajeChat?
    @State private var borrar = false
    @FocusState private var foco: Bool

    private let chips = [("organizar", "Organizar pagos"), ("meta", "Ahorrar"), ("suscripciones", "Suscripciones")]

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    cabecera
                    if !store.modoSimulacion && !store.ia.conectada { bandaIA }
                    opciones
                    if store.estado.chat.isEmpty {
                        VStack(spacing: 12) {
                            EscenaUkku(escena: .planificando, size: 132)
                            Text("Elige una opción para empezar. Ukku te muestra una propuesta y tú decides si se crea.")
                                .font(.ukCuerpo).foregroundStyle(Color.ukkuSecundario).multilineTextAlignment(.center)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.top, 32)
                    }
                    ForEach(store.estado.chat) { m in
                        BurbujaChat(mensaje: m, editar: { editando = m }).id(m.id)
                    }
                    if store.pensando {
                        HStack(spacing: 8) { ProgressView(); Text("Ukku está revisando tus datos").font(.ukMeta).foregroundStyle(Color.ukkuSecundario) }
                    }
                }
                .padding(.horizontal, 24)
                .padding(.bottom, 12)
            }
            .scrollDismissesKeyboard(.interactively)
            .onChange(of: store.estado.chat.count) {
                guard let ultimo = store.estado.chat.last else { return }
                // Lleva al último mensaje sin saltar al final absoluto.
                if quieto { proxy.scrollTo(ultimo.id, anchor: .bottom) }
                else { withAnimation(Movimiento_.contenido) { proxy.scrollTo(ultimo.id, anchor: .bottom) } }
            }
        }
        .background(Color.white)
        .safeAreaInset(edge: .top, spacing: 0) {
            // Evita que el contenido pase por debajo de la hora al desplazar.
            Color.clear.frame(height: 0).background(Color.white.ignoresSafeArea(edges: .top))
        }
        .safeAreaInset(edge: .bottom) {
            if store.modoSimulacion { pieSimulacion } else { compositor }
        }
        .toolbar(.hidden, for: .navigationBar)
        .confirmationDialog("Se borrará la conversación. Los planes que ya creaste se conservan.", isPresented: $borrar, titleVisibility: .visible) {
            Button("Borrar conversación", role: .destructive) { store.borrarChat() }
        }
        .sheet(item: $editando) { m in
            if let p = m.propuesta { PropuestaEditarView(propuesta: p) { store.actualizarPropuesta(mensaje: m.id, $0) } }
        }
        .onAppear(perform: usarContexto)
        .onChange(of: store.contextoChat) { usarContexto() }
        .task { await store.comprobarIA() }
    }

    private func usarContexto() {
        guard let c = store.contextoChat else { return }
        store.contextoChat = nil
        store.accionGuiada(c)
    }

    private var cabecera: some View {
        let r = store.resumen
        let semana = store.estado.pagos.filter { !$0.pagado && Fechas.dias(de: store.hoy, a: $0.fecha) <= 7 }.count
        let linea = !r.hayDatos ? "Aún no hay datos para planificar"
            : "Disponible \(store.importe(r.disponible, decimales: false)) · \(semana == 0 ? "sin pagos esta semana" : semana == 1 ? "1 pago esta semana" : "\(semana) pagos esta semana")"
        return VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .top, spacing: 10) {
                Image("ukku-maestro").resizable().scaledToFit().frame(width: 34, height: 34).padding(.top, 10).accessibilityHidden(true)
                Cabecera(titulo: "Tu plan", subtitulo: "Un paso a la vez, con Ukku") {
                if !store.estado.chat.isEmpty {
                    Button { borrar = true } label: {
                        Image(systemName: "trash").font(.system(size: 19, weight: .medium)).foregroundStyle(Color.ukkuSecundario)
                            .frame(width: 44, height: 44).contentShape(.rect)
                    }
                    .buttonStyle(FilaPresionable())
                    .accessibilityLabel("Borrar conversación")
                }
                }
            }
            Text(linea).font(.ukMeta.monospacedDigit()).foregroundStyle(Color.ukkuSecundario)
        }
    }

    private var bandaIA: some View {
        Button { store.tab = .ajustes } label: {
            ViewThatFits(in: .horizontal) {
                HStack(spacing: 10) {
                    sinIA.fixedSize()
                    Spacer(minLength: 8)
                    Text("Conectar IA").font(.ukCuerpoFuerte).foregroundStyle(Color.ukkuAzul).fixedSize()
                }
                VStack(alignment: .leading, spacing: 4) {
                    sinIA
                    Text("Conectar IA").font(.ukCuerpoFuerte).foregroundStyle(Color.ukkuAzul)
                }
                .padding(.vertical, 10)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 16)
            .frame(minHeight: 48)
            .background(Color.ukkuSuperficie, in: .rect(cornerRadius: 14))
        }
        .buttonStyle(FilaPresionable())
        .accessibilityHint("Abre Ajustes")
    }

    private var sinIA: some View {
        HStack(spacing: 10) {
            Image(systemName: "bolt.slash").font(.system(size: 17, weight: .medium)).foregroundStyle(Color.ukkuSecundario).accessibilityHidden(true)
            Text("Sin IA conectada").font(.ukCuerpo).foregroundStyle(Color.ukkuTinta)
        }
    }

    private var opciones: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("¿Qué quieres resolver hoy?").font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(chips, id: \.0) { clave, titulo in
                        Button(titulo) { store.accionGuiada(clave) }
                            .font(.ukCuerpo.weight(.medium))
                            .foregroundStyle(Color.ukkuAzul)
                            .padding(.horizontal, 14)
                            .frame(minHeight: 44)
                            .overlay(Capsule().stroke(Color.ukkuDivisor, lineWidth: 1.5))
                            .contentShape(.capsule)
                            .buttonStyle(FilaPresionable())
                            .disabled(!store.resumen.hayDatos)
                    }
                }
                .padding(.vertical, 1)
            }
            .scrollClipDisabled()
        }
    }

    private var pieSimulacion: some View {
        Label("Demo interactiva · Elige, revisa y confirma", systemImage: "hand.tap")
            .font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
            .frame(maxWidth: .infinity).padding(16)
            .background(Color.white)
    }

    private var compositor: some View {
        let vacio = texto.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        return HStack(alignment: .bottom, spacing: 8) {
            TextField("Escribe a Ukku", text: $texto, axis: .vertical)
                .font(.ukCuerpo)
                .lineLimit(1...4)
                .focused($foco)
                .padding(.horizontal, 16)
                .frame(minHeight: 52)
                .background(Color.ukkuSuperficie, in: .rect(cornerRadius: 26))
            Button {
                let t = texto.trimmingCharacters(in: .whitespacesAndNewlines)
                texto = ""
                Task { await store.enviar(t) }
            } label: {
                Image(systemName: UkkuIcon.enviar.rawValue).font(.system(size: 17, weight: .semibold))
                    .frame(width: 44, height: 44)
                    .background(Color.ukkuAzul.opacity(vacio || store.pensando ? 0.25 : 1), in: .circle)
                    .foregroundStyle(.white)
            }
            .buttonStyle(FilaPresionable())
            .disabled(vacio || store.pensando)
            .padding(.bottom, 4)
            .accessibilityLabel("Enviar mensaje")
        }
        .padding(.horizontal, 16).padding(.vertical, 8)
        .background(Color.white)
    }
}

struct BurbujaChat: View {
    @Environment(AppStore.self) private var store
    let mensaje: MensajeChat
    let editar: () -> Void

    var body: some View {
        VStack(alignment: mensaje.rol == .usuario ? .trailing : .leading, spacing: 8) {
            if !mensaje.texto.isEmpty {
                if mensaje.rol == .usuario {
                    Text(mensaje.texto).font(.ukCuerpo).foregroundStyle(.white)
                        .padding(.horizontal, 14).padding(.vertical, 10)
                        .background(Color.ukkuAzul, in: .rect(cornerRadius: 18))
                } else {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(mensaje.texto).font(.ukCuerpo).foregroundStyle(Color.ukkuTinta)
                        if mensaje.propuesta == nil { Text(etiquetaFuente).font(.caption).foregroundStyle(Color.ukkuSecundario) }
                    }
                    .padding(.horizontal, 14).padding(.vertical, 10)
                    .background(Color.ukkuSuperficie, in: .rect(cornerRadius: 18))
                }
            }
            if let solicitud = mensaje.solicitudFallida, let ultimo = store.estado.chat.last(where: { $0.rol == .usuario }) {
                Button("Reintentar") { Task { await store.enviar(ultimo.texto, reintento: solicitud) } }.buttonStyle(BotonEnlace())
            }
            if let p = mensaje.propuesta { TarjetaPropuesta(mensaje: mensaje, propuesta: p, editar: editar) }
            else if let aviso = mensaje.aviso {
                Label(aviso, systemImage: "exclamationmark.circle").font(.ukMeta).foregroundStyle(Color.ukkuRojo)
            }
        }
        .frame(maxWidth: .infinity, alignment: mensaje.rol == .usuario ? .trailing : .leading)
    }

    private var etiquetaFuente: String {
        switch mensaje.fuente {
        case .ia: "Respuesta de IA"
        case .ejemplo: "Simulación con tus datos demo"
        default: "Aviso de la app"
        }
    }
}

/// Propuesta estructurada. Al confirmar, la misma tarjeta pasa a mostrar el resultado guardado.
struct TarjetaPropuesta: View {
    @Environment(AppStore.self) private var store
    @Environment(\.ukkuQuieto) private var quieto
    let mensaje: MensajeChat
    let propuesta: PropuestaAccion
    let editar: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            switch store.previsualizar(propuesta) {
            case .failure(let e) where mensaje.resultado == nil:
                Label(e.mensaje, systemImage: "exclamationmark.circle").font(.ukMeta).foregroundStyle(Color.ukkuRojo)
                Button("Editar", action: editar).buttonStyle(BotonEnlace())
            case .failure:
                resultado(titulo: nil)
            case .success(let v):
                if mensaje.resultado == nil { vista(v).transition(.opacity) }
                else { resultado(titulo: v.titulo).transition(.opacity) }
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(mensaje.resultado == nil ? Color.ukkuCeleste : Color.ukkuDivisor, lineWidth: 1.5))
        .animation(quieto ? nil : Movimiento_.contenido, value: mensaje.resultado != nil)
    }

    @ViewBuilder private func vista(_ v: VistaPrevia) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(propuesta.source == .llm ? "Propuesta de IA" : "Vista previa · Tú decides").font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
            Text(v.titulo).font(.ukSeccion).foregroundStyle(Color.ukkuTinta)
        }
        if v.importe != nil || v.fecha != nil {
            HStack(spacing: 16) {
                if let i = v.importe { Text(store.importe(i)).font(.title3.weight(.semibold).monospacedDigit()).foregroundStyle(Color.ukkuAzul) }
                if let f = v.fecha { Label(Fechas.corta(f), systemImage: UkkuIcon.calendario.rawValue).font(.ukCuerpo).foregroundStyle(Color.ukkuTinta) }
            }
        }
        if !v.lineas.isEmpty {
            Separador()
            ForEach(v.lineas) { l in
                HStack(alignment: .firstTextBaseline) {
                    Text(l.etiqueta).font(.ukMeta).foregroundStyle(Color.ukkuSecundario)
                    Spacer(minLength: 8)
                    Text(store.estado.ajustes.ocultarImportes ? "•••" : (l.antes == l.despues ? "Sin cambio" : "\(l.antes) → \(l.despues)"))
                        .font(.ukMeta.weight(.medium).monospacedDigit()).foregroundStyle(Color.ukkuTinta)
                        .multilineTextAlignment(.trailing)
                }
                .accessibilityElement(children: .combine)
                .accessibilityLabel(l.antes == l.despues ? "\(l.etiqueta): sin cambio" : "\(l.etiqueta): pasa de \(l.antes) a \(l.despues)")
            }
        }
        if let n = v.nota { Text(n).font(.ukMeta).foregroundStyle(Color.ukkuSecundario) }
        if let a = mensaje.aviso { Label(a, systemImage: "exclamationmark.circle").font(.ukMeta).foregroundStyle(Color.ukkuAmbar) }
        HStack(spacing: 16) {
            Button(Acciones.nombreAccion(propuesta.tool)) { store.confirmar(mensaje: mensaje.id) }.buttonStyle(BotonPrincipal())
            Button("Editar", action: editar).buttonStyle(BotonEnlace())
        }
        .padding(.top, 4)
    }

    private var esUltimoResultado: Bool { store.estado.chat.last { $0.resultado != nil }?.id == mensaje.id }

    @ViewBuilder private func resultado(titulo: String?) -> some View {
        if let r = mensaje.resultado {
            HStack(alignment: .center, spacing: 10) {
                if !esUltimoResultado {
                    Image(systemName: "checkmark.circle.fill").font(.title3).foregroundStyle(Color.ukkuVerde).accessibilityHidden(true)
                } else if !quieto, let celebra = ClipsUkku.cargar("celebra") {
                    ReproductorClip(clip: celebra).frame(width: 88, height: 88).accessibilityHidden(true)
                } else {
                    EscenaUkku(escena: .metaLograda, size: 56)
                }
                Text(r.summary).font(.ukCuerpoFuerte).foregroundStyle(Color.ukkuVerde)
            }
            Text("Listo. Tu plan ya está actualizado.").font(.ukMeta.monospacedDigit()).foregroundStyle(Color.ukkuSecundario)
            if let id = r.planId {
                Button("Ver en Actividad") {
                    store.planDestacado = id
                    store.tab = .actividad
                }
                .buttonStyle(BotonEnlace())
            }
        }
    }
}

/// Edita los argumentos de una propuesta antes de confirmarla. No ejecuta nada.
struct PropuestaEditarView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var cerrar
    let propuesta: PropuestaAccion
    let guardar: (PropuestaAccion) -> Void
    @State private var titulo = ""
    @State private var monto = ""
    @State private var fecha = Date()
    @State private var error: String?

    private var claveTitulo: String? { ["title"].first { propuesta.arguments[$0] != nil } }
    private var claveMonto: String? { ["amount_minor", "target_minor"].first { propuesta.arguments[$0] != nil } }
    private var claveFecha: String? { ["due_date", "target_date"].first { propuesta.arguments[$0] != nil } }

    var body: some View {
        NavigationStack {
            Form {
                if claveTitulo != nil { TextField("Nombre", text: $titulo) }
                if claveMonto != nil { TextField("Monto en soles", text: $monto).keyboardType(.decimalPad) }
                if claveFecha != nil { DatePicker("Fecha", selection: $fecha, in: Date()..., displayedComponents: .date) }
                if let error { Label(error, systemImage: "exclamationmark.circle").foregroundStyle(Color.ukkuRojo) }
            }
            .navigationTitle("Editar propuesta")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancelar") { cerrar() } }
                ToolbarItem(placement: .confirmationAction) { Button("Guardar") { aplicar() } }
            }
            .onAppear {
                titulo = claveTitulo.flatMap { propuesta.arguments[$0]?.texto } ?? ""
                if let c = claveMonto.flatMap({ propuesta.arguments[$0]?.entero }) { monto = String(format: "%d.%02d", c / 100, c % 100) }
                fecha = claveFecha.flatMap { propuesta.arguments[$0]?.texto }.flatMap(Fechas.deIso) ?? Date()
            }
        }
        .presentationDetents([.medium])
    }

    private func aplicar() {
        var p = propuesta
        if let k = claveTitulo { p.arguments[k] = .s(titulo.trimmingCharacters(in: .whitespaces)) }
        if let k = claveMonto {
            guard let c = Dinero.parse(monto), c > 0 else { error = "Escribe un monto mayor que cero."; return }
            p.arguments[k] = .i(c)
        }
        if let k = claveFecha { p.arguments[k] = .s(Fechas.iso(fecha)) }
        p.contextVersion = store.estado.contextVersion
        if case .failure(let e) = store.previsualizar(p) { error = e.mensaje; return }
        guardar(p)
        cerrar()
    }
}

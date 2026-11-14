import Foundation
import Observation

enum Pestana: Int, Hashable { case inicio, plan, actividad, ajustes }

/// Estado observable de toda la app. Única fuente de verdad para Inicio, chat, planes y ajustes.
@MainActor @Observable
final class AppStore {
    private(set) var estado: Estado
    var tab: Pestana = .inicio
    /// Contexto con el que Inicio abre Plan + Ukku ("organizar", "suscripciones", "meta").
    var contextoChat: String?
    var planDestacado: UUID?
    /// La demo no necesita red. Integración real solo con --conectar-ia.
    let modoSimulacion = true
    var ia: EstadoIA = .comprobando
    var pensando = false
    /// La revelación del hero ocurre una sola vez por arranque, no en cada cambio de pestaña.
    var heroRevelado = false

    var hoy: Date { Date() }
    var resumen: Resumen { Calculo.resumen(estado, hoy: hoy) }
    var llm: LLMProvider { BackendLLM(base: estado.ajustes.endpointIA) }

    init() {
        let args = ProcessInfo.processInfo.arguments
        var e = Persistencia.cargar()
        if let i = args.firstIndex(of: "--escenario"), i + 1 < args.count, let esc = Escenario(rawValue: args[i + 1]) {
            e = Seed.estado(esc, hoy: Date())
        }
        estado = e ?? Seed.estado(.base, hoy: Date())
        if let i = args.firstIndex(of: "--pestana"), i + 1 < args.count, let n = Int(args[i + 1]), let p = Pestana(rawValue: n) { tab = p }
        Persistencia.guardar(estado)
        reconciliar()
    }

    // MARK: Lectura

    func importe(_ c: Centimos, signo: Bool = false, decimales: Bool = true) -> String {
        estado.ajustes.ocultarImportes ? "S/ •••" : Dinero.texto(c, signo: signo, decimales: decimales)
    }
    func categoria(_ id: String) -> Categoria {
        estado.categorias.first { $0.id == id } ?? Categoria(id: id, nombre: "Otros", icono: "circle.grid.2x2")
    }

    // MARK: Escritura

    /// `version: false` para escrituras que no cambian datos financieros (mensajes del chat).
    private func mutar(version: Bool = true, _ cambio: (inout Estado) -> Void) {
        var e = estado
        cambio(&e)
        if version { e.contextVersion += 1 }
        estado = e
        Persistencia.guardar(e)
        Notificaciones.sincronizar(planes: e.planes, activas: e.ajustes.notificaciones, ahora: hoy)
    }

    func propuesta(_ tool: String, _ args: [String: Arg], fuente: PropuestaAccion.Fuente) -> PropuestaAccion {
        PropuestaAccion(tool: tool, arguments: args, source: fuente, contextVersion: estado.contextVersion)
    }

    func previsualizar(_ p: PropuestaAccion, pagoID: UUID? = nil) -> Result<VistaPrevia, ErrorAccion> {
        do { return .success(try Acciones.previsualizar(p, estado, hoy: hoy, pagoID: pagoID)) }
        catch let e as ErrorAccion { return .failure(e) }
        catch { return .failure(ErrorAccion(mensaje: "No se pudo calcular la vista previa.")) }
    }

    /// Ejecución idempotente: un ID de propuesta se aplica una sola vez, aunque haya doble toque o reintento.
    func aplicar(_ p: PropuestaAccion, pagoID: UUID? = nil) -> Result<ResultadoAccion, ErrorAccion> {
        if let previo = estado.aplicadas[p.id.uuidString] { return .success(previo) }
        guard p.contextVersion == estado.contextVersion else {
            return .failure(ErrorAccion(mensaje: "Tus datos cambiaron desde esta propuesta. Revisa el impacto actualizado y confirma de nuevo.", contextoCambio: true))
        }
        var copia = estado
        do {
            let r = try Acciones.aplicar(p, en: &copia, hoy: hoy)
            if let pagoID { try RegistroPago.vincular(resultado: r, pagoID: pagoID, en: &copia) }
            copia.aplicadas[p.id.uuidString] = r
            mutar { $0 = copia }
            return .success(r)
        } catch let e as ErrorAccion { return .failure(e) }
        catch { return .failure(ErrorAccion(mensaje: "No se pudo completar la acción.")) }
    }

    private func historial(_ e: inout Estado, _ tipo: Ejecucion.Tipo, _ texto: String, plan: UUID?) {
        e.ejecuciones.append(Ejecucion(id: UUID().uuidString, planId: plan, tipo: tipo, fecha: hoy, resumen: texto))
    }

    func editarPlan(_ id: UUID, titulo: String, importe: Centimos, fecha: Date, periodicidad: Periodicidad, categoriaId: String) {
        mutar { e in
            guard let k = e.planes.firstIndex(where: { $0.id == id }) else { return }
            e.planes[k].titulo = titulo
            e.planes[k].importeMinor = importe
            e.planes[k].fecha = fecha
            e.planes[k].periodicidad = periodicidad
            e.planes[k].categoriaId = categoriaId
            if e.planes[k].tipo == .reserva { e.planes[k].reservadoMinor = importe }
            if e.planes[k].estado == .borrador { e.planes[k].estado = .programado }
            if let j = e.metas.firstIndex(where: { $0.id == e.planes[k].refId }) {
                e.metas[j].titulo = titulo; e.metas[j].objetivoMinor = importe; e.metas[j].fechaObjetivo = fecha
            }
            if let j = e.presupuestos.firstIndex(where: { $0.id == e.planes[k].refId }) {
                e.presupuestos[j].limiteMinor = importe; e.presupuestos[j].categoriaId = categoriaId
            }
            historial(&e, .editado, "Plan editado: \(titulo)", plan: id)
        }
    }

    func reanudar(_ id: UUID) {
        mutar { e in
            guard let k = e.planes.firstIndex(where: { $0.id == id }), e.planes[k].estado == .pausado else { return }
            e.planes[k].estado = e.planes[k].estadoAntesDePausa ?? .programado
            e.planes[k].estadoAntesDePausa = nil
            historial(&e, .reanudado, "Plan reanudado: \(e.planes[k].titulo)", plan: id)
        }
        reconciliar()
    }

    func marcarHecho(_ id: UUID) {
        mutar { e in
            guard let k = e.planes.firstIndex(where: { $0.id == id }) else { return }
            let p = e.planes[k]
            historial(&e, .completado, "Marcaste como hecho: \(p.titulo)", plan: id)
            let paso: Calendar.Component? = p.periodicidad == .weekly ? .weekOfYear : (p.periodicidad == .monthly ? .month : nil)
            if let paso, p.tipo != .meta {
                // Siguiente vencimiento: siempre posterior a hoy, para no repetir al relanzar.
                var f = p.fecha
                repeat { f = Fechas.cal.date(byAdding: paso, value: 1, to: f)! } while f <= hoy
                e.planes[k].fecha = f
                e.planes[k].estado = .programado
            } else {
                e.planes[k].estado = .completado
                e.planes[k].reservadoMinor = 0
            }
        }
    }

    /// Aporte a una meta: mueve dinero del disponible a la reserva, dentro de Ukku.
    func aportar(_ id: UUID, monto: Centimos) -> String? {
        guard let plan = estado.planes.first(where: { $0.id == id }), plan.estado.activo,
              let meta = estado.metas.first(where: { $0.id == plan.refId }) else { return "Esta meta no está activa." }
        guard monto > 0 else { return "El aporte debe ser mayor que cero." }
        guard monto <= meta.objetivoMinor - meta.ahorradoMinor else { return "El aporte supera lo que falta para alcanzar la meta." }
        guard monto <= resumen.disponible else { return "El aporte supera tu disponible del mes (\(Dinero.texto(resumen.disponible)))." }
        mutar { e in
            guard let k = e.planes.firstIndex(where: { $0.id == id }), let j = e.metas.firstIndex(where: { $0.id == e.planes[k].refId }) else { return }
            e.metas[j].ahorradoMinor += monto
            historial(&e, .aporte, "Aporte de \(Dinero.texto(monto)) a \(e.metas[j].titulo)", plan: id)
            if e.metas[j].ahorradoMinor >= e.metas[j].objetivoMinor {
                e.planes[k].estado = .completado
                historial(&e, .completado, "Meta alcanzada: \(e.metas[j].titulo)", plan: id)
            }
        }
        return nil
    }

    func eliminarPlan(_ id: UUID) {
        mutar { e in
            guard let p = e.planes.first(where: { $0.id == id }) else { return }
            e.metas.removeAll { $0.id == p.refId }
            e.presupuestos.removeAll { $0.id == p.refId }
            e.planes.removeAll { $0.id == id }
            historial(&e, .eliminado, "Plan eliminado: \(p.titulo)", plan: nil)
        }
    }

    func eliminarMovimiento(_ id: UUID) {
        mutar { e in
            guard let m = e.movimientos.first(where: { $0.id == id }) else { return }
            if let k = e.cuentas.firstIndex(where: { $0.id == m.cuentaId }) { e.cuentas[k].saldoMinor -= m.montoMinor }
            if let pagoID = m.pagoId, let k = e.pagos.firstIndex(where: { $0.id == pagoID }) { e.pagos[k].pagado = false }
            e.movimientos.removeAll { $0.id == id }
            historial(&e, .movimiento, "Movimiento eliminado: \(m.comercio)", plan: nil)
        }
    }

    func marcarPagoPagado(_ id: UUID) {
        mutar { e in
            if let k = e.pagos.firstIndex(where: { $0.id == id }) { e.pagos[k].pagado = true }
        }
    }

    func ajustar(_ cambio: (inout Ajustes) -> Void) { mutar { cambio(&$0.ajustes) } }

    func reiniciar(_ escenario: Escenario) {
        let ajustes = estado.ajustes
        mutar { e in
            let version = e.contextVersion
            e = Seed.estado(escenario, hoy: hoy, ajustes: ajustes)
            e.contextVersion = version
        }
        reconciliar()
    }

    /// Runner idempotente por plan + vencimiento. Se llama al abrir y al volver a primer plano.
    func reconciliar() {
        let hoy0 = Fechas.inicioDia(hoy)
        let vencidos = estado.planes.filter { p in
            (p.estado == .programado || p.estado == .enCurso) && p.tipo != .presupuesto
                && (p.tipo == .recordatorio ? p.fecha <= hoy : Fechas.inicioDia(p.fecha) <= hoy0)
                && !estado.ejecuciones.contains { $0.id == "\(p.id.uuidString)|\(Fechas.iso(p.fecha))" }
        }
        guard !vencidos.isEmpty else { return }
        mutar { e in
            for p in vencidos {
                guard let k = e.planes.firstIndex(where: { $0.id == p.id }) else { continue }
                e.planes[k].estado = .necesitaConfirmacion
                let texto = p.tipo == .meta ? "Llegó la fecha de la meta «\(p.titulo)». Revisa si la alcanzaste."
                    : "Venció «\(p.titulo)». Ukku no paga por ti: confirma si ya lo hiciste."
                e.ejecuciones.append(Ejecucion(id: "\(p.id.uuidString)|\(Fechas.iso(p.fecha))", planId: p.id, tipo: .vencimiento, fecha: hoy, resumen: texto))
            }
        }
    }

    // MARK: Chat

    private func decir(_ m: MensajeChat) { mutar(version: false) { $0.chat.append(m) } }

    func comprobarIA() async {
        guard !modoSimulacion else { return }
        ia = await llm.estado()
    }

    func borrarChat() { mutar(version: false) { $0.chat = [] } }

    /// Ejemplos guiados: se calculan sin IA y se etiquetan como tales.
    func accionGuiada(_ clave: String) {
        let r = resumen
        let finCiclo = Fechas.cal.date(byAdding: .day, value: -1, to: r.ciclo.fin)!
        var texto = ""
        var prop: PropuestaAccion?
        switch clave {
        case "organizar":
            decir(MensajeChat(rol: .usuario, fuente: .usuario, texto: "Organizar mis pagos", fecha: hoy))
            if let p = r.proximoPago {
                texto = "Tu próximo pago es \(p.nombre): \(Dinero.texto(p.montoMinor)) el \(Fechas.corta(p.fecha)). Puedo separar ese monto para que no lo gastes antes."
                prop = propuesta("create_plan", ["title": .s("Reservar para \(p.nombre)"), "amount_minor": .i(p.montoMinor), "currency": .s("PEN"),
                                                 "due_date": .s(Fechas.iso(max(p.fecha, hoy))), "category_id": .s(p.categoriaId), "recurrence": .s("none")], fuente: .ejemplo)
            } else { texto = "No tienes pagos pendientes registrados este mes. Agrega uno desde Actividad para organizarlo." }
        case "suscripciones":
            decir(MensajeChat(rol: .usuario, fuente: .usuario, texto: "Reducir suscripciones", fecha: hoy))
            let gasto = Calculo.gastado(estado, categoria: "subscriptions", ciclo: r.ciclo)
            if gasto > 0 {
                let limite = max(500, gasto * 8 / 10 / 500 * 500)
                texto = "Este mes llevas \(Dinero.texto(gasto)) en suscripciones. Te propongo un límite un 20 % menor. Cancelar un servicio es algo que haces tú: Ukku solo lleva la cuenta."
                prop = propuesta("set_category_budget", ["category_id": .s("subscriptions"), "amount_minor": .i(limite), "currency": .s("PEN"), "cycle_id": .s(r.ciclo.id)], fuente: .ejemplo)
            } else { texto = "No hay cobros de suscripciones registrados este mes." }
        default:
            decir(MensajeChat(rol: .usuario, fuente: .usuario, texto: "Crear una meta", fecha: hoy))
            texto = "Una meta de ejemplo: ahorrar S/ 300 antes de que termine el mes. Puedes cambiar el nombre, el monto y la fecha antes de crearla."
            prop = propuesta("create_savings_goal", ["title": .s("Ahorro del mes"), "target_minor": .i(30_000), "currency": .s("PEN"),
                                                     "target_date": .s(Fechas.iso(max(finCiclo, hoy)))], fuente: .ejemplo)
        }
        decir(MensajeChat(rol: .ukku, fuente: .ejemplo, texto: texto, fecha: hoy, propuesta: prop))
    }

    func actualizarPropuesta(mensaje id: UUID, _ nueva: PropuestaAccion) {
        mutar(version: false) { e in
            if let k = e.chat.firstIndex(where: { $0.id == id }) { e.chat[k].propuesta = nueva; e.chat[k].aviso = nil }
        }
    }

    func confirmar(mensaje id: UUID) {
        guard let m = estado.chat.first(where: { $0.id == id }), let p = m.propuesta, m.resultado == nil else { return }
        switch aplicar(p) {
        case .success(let r):
            mutar(version: false) { e in
                if let k = e.chat.firstIndex(where: { $0.id == id }) { e.chat[k].resultado = r; e.chat[k].aviso = nil }
            }
        case .failure(let err):
            mutar(version: false) { e in
                guard let k = e.chat.firstIndex(where: { $0.id == id }) else { return }
                e.chat[k].aviso = err.mensaje
                // La propuesta queda alineada con el contexto que el usuario ve ahora; debe confirmar otra vez.
                if err.contextoCambio { e.chat[k].propuesta?.contextVersion = e.contextVersion }
            }
        }
    }

    func contextoFinanciero() -> [String: Any] {
        let r = resumen
        return [
            "today": Fechas.iso(hoy), "timezone": "America/Lima", "currency": "PEN", "cycle_id": r.ciclo.id,
            "context_version": estado.contextVersion, "data_is_synthetic": true,
            "available_month_minor": r.disponible, "shortfall_minor": r.faltante, "balance_minor": r.saldo,
            "reserved_minor": r.reservas, "buffer_minor": r.colchon, "payment_status": r.mood.rawValue,
            "accounts": estado.cuentas.map { ["id": $0.id, "name": $0.nombre] },
            "categories": estado.categorias.map { ["id": $0.id, "name": $0.nombre] },
            "pending_payments": estado.pagos.filter { !$0.pagado }.map { ["name": $0.nombre, "amount_minor": $0.montoMinor, "due_date": Fechas.iso($0.fecha), "category_id": $0.categoriaId] },
            "budgets": estado.presupuestos.map { ["category_id": $0.categoriaId, "limit_minor": $0.limiteMinor, "spent_minor": Calculo.gastado(estado, categoria: $0.categoriaId, ciclo: r.ciclo)] },
            "plans": estado.planes.map { ["plan_id": $0.id.uuidString, "title": $0.titulo, "type": $0.tipo.rawValue, "status": $0.estado.rawValue, "due_date": Fechas.iso($0.fecha)] },
        ]
    }

    func enviar(_ texto: String, reintento: String? = nil) async {
        let solicitud = reintento ?? UUID().uuidString
        if reintento == nil { decir(MensajeChat(rol: .usuario, fuente: .usuario, texto: texto, fecha: hoy)) }
        else { mutar(version: false) { $0.chat.removeAll { $0.solicitudFallida == solicitud } } }
        guard ia.conectada else {
            decir(MensajeChat(rol: .sistema, fuente: .sistema, texto: "La IA no está conectada, así que Ukku no puede responder mensajes libres. Usa las opciones guiadas o conéctala en Ajustes.", fecha: hoy))
            return
        }
        pensando = true
        defer { pensando = false }
        let historia = estado.chat.filter { $0.rol != .sistema }.suffix(12).map { ["role": $0.rol == .usuario ? "user" : "assistant", "content": $0.texto] }
        do {
            let r = try await llm.chat(solicitud: solicitud, mensajes: historia, contexto: contextoFinanciero())
            var primero = true
            if r.proposals.isEmpty { decir(MensajeChat(rol: .ukku, fuente: .ia, texto: r.text, fecha: hoy)) }
            for pr in r.proposals {
                guard !estado.chat.contains(where: { $0.propuesta?.id == pr.id }) else { continue } // reintento sin duplicar
                var p = propuesta(pr.tool, pr.arguments, fuente: .llm)
                p.id = pr.id
                var m = MensajeChat(rol: .ukku, fuente: .ia, texto: primero ? r.text : "", fecha: hoy, propuesta: p)
                if case .failure(let err) = previsualizar(p) { m.propuesta = nil; m.aviso = "La IA propuso una acción que no pasó la validación: \(err.mensaje)" }
                decir(m)
                primero = false
            }
        } catch {
            let msg = (error as? ErrorIA)?.mensaje ?? "No se pudo obtener respuesta."
            decir(MensajeChat(rol: .sistema, fuente: .sistema, texto: "\(msg) No se hizo ningún cambio.", fecha: hoy, solicitudFallida: solicitud))
        }
    }
}

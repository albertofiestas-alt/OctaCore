import Foundation

struct ErrorAccion: Error, Hashable {
    var mensaje: String
    var contextoCambio = false
}

struct VistaPrevia: Hashable {
    struct Linea: Hashable, Identifiable {
        var id: String { etiqueta }
        var etiqueta: String
        var antes: String
        var despues: String
    }
    var titulo: String
    var importe: Centimos?
    var fecha: Date?
    var lineas: [Linea]
    var nota: String?
}

/// Capa única de acciones (CONTRATO-ACCIONES.json). Formularios y chat pasan por aquí.
enum Acciones {
    enum T { case texto, entero }
    static let esquemas: [String: [String: T]] = [
        "create_plan": ["title": .texto, "amount_minor": .entero, "currency": .texto, "due_date": .texto, "category_id": .texto, "recurrence": .texto],
        "set_category_budget": ["category_id": .texto, "amount_minor": .entero, "currency": .texto, "cycle_id": .texto],
        "create_savings_goal": ["title": .texto, "target_minor": .entero, "currency": .texto, "target_date": .texto],
        "create_reminder": ["title": .texto, "local_datetime": .texto, "timezone": .texto],
        "record_demo_transaction": ["account_id": .texto, "amount_minor_signed": .entero, "currency": .texto, "category_id": .texto, "date": .texto, "merchant": .texto],
        "pause_plan": ["plan_id": .texto],
        "reschedule_plan": ["plan_id": .texto, "due_date": .texto],
    ]

    static func nombreAccion(_ tool: String) -> String {
        switch tool {
        case "create_plan": "Crear plan"
        case "set_category_budget": "Crear presupuesto"
        case "create_savings_goal": "Crear meta"
        case "create_reminder": "Crear recordatorio"
        case "record_demo_transaction": "Registrar movimiento"
        case "pause_plan": "Pausar plan"
        case "reschedule_plan": "Reprogramar plan"
        default: "Confirmar"
        }
    }

    // MARK: Validación estricta

    static func validar(_ p: PropuestaAccion, _ e: Estado, hoy: Date) throws {
        guard let esquema = esquemas[p.tool] else { throw ErrorAccion(mensaje: "Acción no permitida: \(p.tool).") }
        guard Set(p.arguments.keys) == Set(esquema.keys) else { throw ErrorAccion(mensaje: "La propuesta tiene datos faltantes o no permitidos.") }
        for (k, t) in esquema {
            switch t {
            case .texto: guard let s = p.arguments[k]?.texto, !s.trimmingCharacters(in: .whitespaces).isEmpty, s.count <= 120 else { throw ErrorAccion(mensaje: "Falta completar: \(k).") }
            case .entero: guard p.arguments[k]?.entero != nil else { throw ErrorAccion(mensaje: "El importe no es válido.") }
            }
        }
        func s(_ k: String) -> String { p.arguments[k]?.texto ?? "" }
        func i(_ k: String) -> Int { p.arguments[k]?.entero ?? 0 }
        let hoy0 = Fechas.inicioDia(hoy)
        if esquema["currency"] != nil, s("currency") != "PEN" { throw ErrorAccion(mensaje: "Esta demo solo trabaja en soles (PEN).") }
        if esquema["category_id"] != nil, !e.categorias.contains(where: { $0.id == s("category_id") }) { throw ErrorAccion(mensaje: "La categoría no existe.") }
        for k in ["amount_minor", "target_minor"] where esquema[k] != nil {
            guard i(k) > 0, i(k) <= 100_000_000_00 else { throw ErrorAccion(mensaje: "El importe debe ser mayor que cero.") }
        }
        for k in ["due_date", "target_date"] where esquema[k] != nil {
            guard let d = Fechas.deIso(s(k)) else { throw ErrorAccion(mensaje: "La fecha no es válida.") }
            guard d >= hoy0 else { throw ErrorAccion(mensaje: "La fecha debe ser hoy o posterior.") }
        }
        switch p.tool {
        case "create_plan":
            guard Periodicidad(rawValue: s("recurrence")) != nil else { throw ErrorAccion(mensaje: "La periodicidad no es válida.") }
        case "create_reminder":
            guard let d = Fechas.deIsoHora(s("local_datetime")), d > hoy.addingTimeInterval(-60) else { throw ErrorAccion(mensaje: "El recordatorio debe tener una fecha y hora futuras.") }
            guard s("timezone") == "America/Lima" else { throw ErrorAccion(mensaje: "La zona horaria debe ser America/Lima.") }
        case "record_demo_transaction":
            guard e.cuentas.contains(where: { $0.id == s("account_id") }) else { throw ErrorAccion(mensaje: "La cuenta no existe.") }
            guard (-9_999_999_999...9_999_999_999).contains(i("amount_minor_signed")), i("amount_minor_signed") != 0 else { throw ErrorAccion(mensaje: "El importe está fuera de rango.") }
            guard let d = Fechas.deIso(s("date")), d <= hoy else { throw ErrorAccion(mensaje: "La fecha del movimiento no puede ser futura.") }
        case "pause_plan", "reschedule_plan":
            guard let plan = e.planes.first(where: { $0.id.uuidString == s("plan_id") }) else { throw ErrorAccion(mensaje: "No encontramos ese plan.") }
            if p.tool == "pause_plan", !plan.estado.activo { throw ErrorAccion(mensaje: "Ese plan no está activo.") }
        default: break
        }
    }

    // MARK: Ejecución (sobre una copia o sobre el estado real)

    static func aplicar(_ p: PropuestaAccion, en e: inout Estado, hoy: Date) throws -> ResultadoAccion {
        try validar(p, e, hoy: hoy)
        func s(_ k: String) -> String { p.arguments[k]?.texto ?? "" }
        func i(_ k: String) -> Int { p.arguments[k]?.entero ?? 0 }
        let origen: OrigenPlan = p.source == .manual ? .usuario : .ukku
        var entidad = ""
        var planId: UUID?
        var resumen = ""
        func registrar(_ tipo: Ejecucion.Tipo, _ texto: String, plan: UUID?) {
            e.ejecuciones.append(Ejecucion(id: UUID().uuidString, planId: plan, tipo: tipo, fecha: hoy, resumen: texto))
        }

        switch p.tool {
        case "create_plan":
            let fecha = Fechas.deIso(s("due_date"))!
            let pago = e.pagos.first { !$0.pagado && $0.categoriaId == s("category_id") && Fechas.inicioDia($0.fecha) == fecha }
            let plan = Plan(tipo: .reserva, titulo: s("title"), importeMinor: i("amount_minor"), fecha: fecha,
                            periodicidad: Periodicidad(rawValue: s("recurrence"))!, categoriaId: s("category_id"), origen: origen,
                            estado: .programado, pagoId: pago?.id, reservadoMinor: i("amount_minor"), creado: hoy)
            e.planes.append(plan)
            (entidad, planId, resumen) = (plan.id.uuidString, plan.id, "Plan creado: \(plan.titulo)")
            registrar(.creado, "\(resumen), \(Dinero.texto(plan.importeMinor)) para el \(Fechas.corta(fecha))", plan: plan.id)

        case "set_category_budget":
            let cat = e.categorias.first { $0.id == s("category_id") }!
            if let k = e.presupuestos.firstIndex(where: { $0.categoriaId == cat.id }) {
                e.presupuestos[k].limiteMinor = i("amount_minor")
                e.presupuestos[k].cicloId = s("cycle_id")
                let ref = e.presupuestos[k].id
                if let j = e.planes.firstIndex(where: { $0.refId == ref }) {
                    e.planes[j].importeMinor = i("amount_minor")
                    planId = e.planes[j].id
                }
                entidad = ref.uuidString
                resumen = "Presupuesto de \(cat.nombre) actualizado a \(Dinero.texto(i("amount_minor")))"
            } else {
                let pres = Presupuesto(categoriaId: cat.id, limiteMinor: i("amount_minor"), cicloId: s("cycle_id"))
                e.presupuestos.append(pres)
                let ciclo = Calculo.ciclo(hoy: hoy, dia: e.ajustes.cicloDia)
                let plan = Plan(tipo: .presupuesto, titulo: "Presupuesto de \(cat.nombre)", importeMinor: pres.limiteMinor, fecha: ciclo.fin,
                                periodicidad: .monthly, categoriaId: cat.id, origen: origen, estado: .enCurso, refId: pres.id, creado: hoy)
                e.planes.append(plan)
                (entidad, planId) = (pres.id.uuidString, plan.id)
                resumen = "Presupuesto creado: \(cat.nombre), \(Dinero.texto(pres.limiteMinor)) al mes"
            }
            registrar(.presupuesto, resumen, plan: planId)

        case "create_savings_goal":
            let meta = Meta(titulo: s("title"), objetivoMinor: i("target_minor"), fechaObjetivo: Fechas.deIso(s("target_date"))!)
            e.metas.append(meta)
            let plan = Plan(tipo: .meta, titulo: meta.titulo, importeMinor: meta.objetivoMinor, fecha: meta.fechaObjetivo,
                            categoriaId: "savings", origen: origen, estado: .enCurso, refId: meta.id, creado: hoy)
            e.planes.append(plan)
            (entidad, planId, resumen) = (meta.id.uuidString, plan.id, "Meta creada: \(meta.titulo)")
            registrar(.creado, "\(resumen), objetivo \(Dinero.texto(meta.objetivoMinor)) al \(Fechas.corta(meta.fechaObjetivo))", plan: plan.id)

        case "create_reminder":
            let fecha = Fechas.deIsoHora(s("local_datetime"))!
            let plan = Plan(tipo: .recordatorio, titulo: s("title"), importeMinor: 0, fecha: fecha, categoriaId: "other",
                            origen: origen, estado: .programado, creado: hoy)
            e.planes.append(plan)
            (entidad, planId, resumen) = (plan.id.uuidString, plan.id, "Recordatorio creado: \(plan.titulo)")
            registrar(.creado, "\(resumen), \(Fechas.larga(fecha))", plan: plan.id)

        case "record_demo_transaction":
            let mov = Movimiento(cuentaId: s("account_id"), montoMinor: i("amount_minor_signed"), categoriaId: s("category_id"),
                                 fecha: Fechas.deIso(s("date"))!.addingTimeInterval(12 * 3600), comercio: s("merchant"))
            e.movimientos.append(mov)
            if let k = e.cuentas.firstIndex(where: { $0.id == mov.cuentaId }) { e.cuentas[k].saldoMinor += mov.montoMinor }
            (entidad, resumen) = (mov.id.uuidString, "Movimiento demo registrado: \(mov.comercio), \(Dinero.texto(mov.montoMinor, signo: true))")
            registrar(.movimiento, resumen, plan: nil)

        case "pause_plan":
            let k = e.planes.firstIndex { $0.id.uuidString == s("plan_id") }!
            e.planes[k].estadoAntesDePausa = e.planes[k].estado
            e.planes[k].estado = .pausado
            (entidad, planId, resumen) = (e.planes[k].id.uuidString, e.planes[k].id, "Plan pausado: \(e.planes[k].titulo)")
            registrar(.pausado, resumen, plan: planId)

        case "reschedule_plan":
            let k = e.planes.firstIndex { $0.id.uuidString == s("plan_id") }!
            let fecha = Fechas.deIso(s("due_date"))!
            e.planes[k].fecha = fecha
            if e.planes[k].estado == .necesitaConfirmacion { e.planes[k].estado = .programado }
            if let j = e.metas.firstIndex(where: { $0.id == e.planes[k].refId }) { e.metas[j].fechaObjetivo = fecha }
            (entidad, planId, resumen) = (e.planes[k].id.uuidString, e.planes[k].id, "Plan reprogramado: \(e.planes[k].titulo), nueva fecha \(Fechas.corta(fecha))")
            registrar(.reprogramado, resumen, plan: planId)

        default: throw ErrorAccion(mensaje: "Acción no permitida.")
        }
        return ResultadoAccion(proposalId: p.id, entityId: entidad, executedAt: hoy, summary: resumen, planId: planId)
    }

    /// Impacto calculado por el servicio determinista aplicando la propuesta a una copia.
    static func previsualizar(_ p: PropuestaAccion, _ e: Estado, hoy: Date, pagoID: UUID? = nil) throws -> VistaPrevia {
        var copia = e
        let resultado = try aplicar(p, en: &copia, hoy: hoy)
        if let pagoID { try RegistroPago.vincular(resultado: resultado, pagoID: pagoID, en: &copia) }
        let (a, d) = (Calculo.resumen(e, hoy: hoy), Calculo.resumen(copia, hoy: hoy))
        func s(_ k: String) -> String { p.arguments[k]?.texto ?? "" }
        func i(_ k: String) -> Int { p.arguments[k]?.entero ?? 0 }
        var lineas = [VistaPrevia.Linea(etiqueta: "Disponible del mes", antes: Dinero.texto(a.disponible), despues: Dinero.texto(d.disponible))]
        var v = VistaPrevia(titulo: "", importe: nil, fecha: nil, lineas: [], nota: nil)
        switch p.tool {
        case "create_plan":
            v.titulo = s("title"); v.importe = i("amount_minor"); v.fecha = Fechas.deIso(s("due_date"))
            lineas.append(.init(etiqueta: "Separado para este plan", antes: Dinero.texto(0), despues: Dinero.texto(i("amount_minor"))))
            if copia.planes.last?.pagoId != nil {
                v.nota = a.disponible == d.disponible ? "Tu disponible no cambia: ese pago ya estaba descontado. No se paga nada." : "El pago ya estaba descontado. Solo se separa además lo que excede su importe. No se paga nada."
            }
        case "set_category_budget":
            let cat = e.categorias.first { $0.id == s("category_id") }?.nombre ?? ""
            v.titulo = "Presupuesto de \(cat)"; v.importe = i("amount_minor")
            let antes = e.presupuestos.first { $0.categoriaId == s("category_id") }?.limiteMinor
            lineas = [.init(etiqueta: "Límite mensual", antes: antes.map { Dinero.texto($0) } ?? "Sin límite", despues: Dinero.texto(i("amount_minor"))),
                      .init(etiqueta: "Gastado este mes", antes: Dinero.texto(Calculo.gastado(e, categoria: s("category_id"), ciclo: a.ciclo)), despues: "Sin cambio")]
            v.nota = "Un presupuesto es un límite que tú te pones. No bloquea compras ni cancela servicios."
        case "create_savings_goal":
            v.titulo = s("title"); v.importe = i("target_minor"); v.fecha = Fechas.deIso(s("target_date"))
            lineas.append(.init(etiqueta: "Ahorrado para la meta", antes: "No existe", despues: Dinero.texto(0)))
            v.nota = "La meta empieza en S/ 0. Cada aporte que registres se separa de tu disponible."
        case "create_reminder":
            v.titulo = s("title"); v.fecha = Fechas.deIsoHora(s("local_datetime"))
            lineas = []
            v.nota = "Es solo un recordatorio dentro de Ukku: no paga ni cancela nada por ti."
        case "record_demo_transaction":
            v.titulo = s("merchant"); v.importe = i("amount_minor_signed"); v.fecha = Fechas.deIso(s("date"))
            lineas.insert(.init(etiqueta: "Saldo de la cuenta demo", antes: Dinero.texto(a.saldo), despues: Dinero.texto(d.saldo)), at: 0)
        case "pause_plan", "reschedule_plan":
            let plan = e.planes.first { $0.id.uuidString == s("plan_id") }
            v.titulo = plan?.titulo ?? ""; v.fecha = Fechas.deIso(s("due_date"))
            lineas.append(.init(etiqueta: "Estado del plan", antes: plan?.estado.nombre ?? "", despues: p.tool == "pause_plan" ? "Pausado" : "Reprogramado"))
        default: break
        }
        v.lineas = lineas
        return v
    }
}

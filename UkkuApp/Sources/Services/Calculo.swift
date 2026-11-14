import Foundation

enum Fechas {
    static let zona = TimeZone(identifier: "America/Lima")!
    static let cal: Calendar = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = zona
        c.locale = Locale(identifier: "es_PE")
        return c
    }()
    private static func formato(_ f: String, posix: Bool = false) -> DateFormatter {
        let d = DateFormatter()
        d.calendar = cal
        d.timeZone = zona
        d.locale = Locale(identifier: posix ? "en_US_POSIX" : "es_PE")
        d.dateFormat = f
        return d
    }
    private static let fIso = formato("yyyy-MM-dd", posix: true)
    private static let fIsoHora = formato("yyyy-MM-dd'T'HH:mm", posix: true)
    private static let fCorta = formato("d MMM")
    private static let fMes = formato("LLLL 'de' yyyy")
    private static let fLarga = formato("d 'de' MMMM, HH:mm")

    static func inicioDia(_ d: Date) -> Date { cal.startOfDay(for: d) }
    static func iso(_ d: Date) -> String { fIso.string(from: d) }
    static func deIso(_ s: String) -> Date? {
        guard s.count == 10, let d = fIso.date(from: s), iso(d) == s else { return nil }
        return d
    }
    static func isoHora(_ d: Date) -> String { fIsoHora.string(from: d) }
    static func deIsoHora(_ s: String) -> Date? { fIsoHora.date(from: String(s.prefix(16))) }
    static func corta(_ d: Date) -> String { fCorta.string(from: d).replacingOccurrences(of: ".", with: "") }
    static func mes(_ d: Date) -> String { fMes.string(from: d) }
    static func larga(_ d: Date) -> String { fLarga.string(from: d) }
    static func dias(de a: Date, a b: Date) -> Int {
        cal.dateComponents([.day], from: inicioDia(a), to: inicioDia(b)).day ?? 0
    }
}

enum Dinero {
    /// "S/ 1,260.00" (formato peruano). Signo explícito opcional.
    static func texto(_ c: Centimos, signo: Bool = false, decimales: Bool = true) -> String {
        let a = abs(c)
        var enteros = String(a / 100)
        var grupos: [String] = []
        while enteros.count > 3 {
            grupos.insert(String(enteros.suffix(3)), at: 0)
            enteros = String(enteros.dropLast(3))
        }
        grupos.insert(enteros, at: 0)
        var s = "S/ " + grupos.joined(separator: ",")
        if decimales || a % 100 != 0 { s += String(format: ".%02d", a % 100) }
        if c < 0 { return "−" + s }
        return signo && c > 0 ? "+" + s : s
    }

    /// "100", "100.5", "100,50" -> céntimos. nil si no es un importe válido.
    static func parse(_ texto: String) -> Centimos? {
        let t = texto.trimmingCharacters(in: .whitespaces).replacingOccurrences(of: ",", with: ".")
        guard !t.isEmpty, t.allSatisfy({ $0.isNumber || $0 == "." }) else { return nil }
        let partes = t.split(separator: ".", omittingEmptySubsequences: false)
        guard partes.count <= 2, let soles = Int(partes[0].isEmpty ? "0" : partes[0]) else { return nil }
        var cent = 0
        if partes.count == 2 {
            let d = String(partes[1].prefix(2)).padding(toLength: 2, withPad: "0", startingAt: 0)
            guard partes[1].count <= 2, let v = Int(d) else { return nil }
            cent = v
        }
        guard soles < 100_000_000 else { return nil }
        return soles * 100 + cent
    }
}

struct Ciclo: Hashable {
    var inicio: Date
    var fin: Date
    var id: String
}

struct PuntoControl: Identifiable, Hashable {
    var id: String
    var etiqueta: String
    var dia: Int
    var permitido: Centimos
    var limita: Bool
}

struct Resumen {
    var ciclo: Ciclo
    var saldo: Centimos = 0
    var ingresosConfirmados: Centimos = 0
    var ingresosInciertos: Centimos = 0
    var pagosPendientes: Centimos = 0
    var reservas: Centimos = 0
    var colchon: Centimos = 0
    var bruto: Centimos = 0
    var disponible: Centimos { max(0, bruto) }
    var faltante: Centimos { max(0, -bruto) }
    var mood: UkkuMood = .sinDatos
    var sugerenciaHoy: Centimos?
    var puntos: [PuntoControl] = []
    var proximoPago: PagoConFecha?
    var pagosSinCubrir: [PagoConFecha] = []
    var hayDatos = false
}

struct Insight: Identifiable, Hashable {
    var id: String
    var icono: String
    var titulo: String
    var fundamento: String
    var accion: String
    var contexto: String
}

struct Logro: Identifiable, Hashable {
    var id: String
    var texto: String
}

/// Servicio determinista: todos los importes salen de aquí. El LLM no calcula saldos.
enum Calculo {
    static func ciclo(hoy: Date, dia: Int) -> Ciclo {
        let cal = Fechas.cal
        let d = min(max(dia, 1), 28)
        var comp = cal.dateComponents([.year, .month], from: hoy)
        comp.day = d
        var inicio = cal.date(from: comp)!
        if inicio > Fechas.inicioDia(hoy) { inicio = cal.date(byAdding: .month, value: -1, to: inicio)! }
        let fin = cal.date(byAdding: .month, value: 1, to: inicio)!
        let c = cal.dateComponents([.year, .month], from: inicio)
        return Ciclo(inicio: inicio, fin: fin, id: String(format: "%04d-%02d", c.year!, c.month!))
    }

    /// Reservas sin duplicar: metas + reservas de planes que no apuntan a un pago ya descontado.
    static func reservas(_ e: Estado) -> Centimos {
        let pendientes = Set(e.pagos.filter { !$0.pagado }.map(\.id))
        let metas = e.metas.reduce(0) { $0 + $1.ahorradoMinor }
        let planes = e.planes.filter { $0.tipo == .reserva && $0.estado.activo && !($0.pagoId.map(pendientes.contains) ?? false) }
            .reduce(0) { $0 + $1.reservadoMinor }
        return metas + planes
    }

    static func resumen(_ e: Estado, hoy: Date) -> Resumen {
        let ciclo = ciclo(hoy: hoy, dia: e.ajustes.cicloDia)
        var r = Resumen(ciclo: ciclo)
        r.hayDatos = !e.cuentas.isEmpty && !(e.movimientos.isEmpty && e.pagos.isEmpty)
        guard r.hayDatos else { return r }
        let hoy0 = Fechas.inicioDia(hoy)

        r.saldo = e.cuentas.reduce(0) { $0 + $1.saldoMinor }
        let pendientes = e.pagos.filter { !$0.pagado && $0.fecha < ciclo.fin }.sorted { $0.fecha < $1.fecha }
        let ingresos = e.ingresos.filter { $0.fecha >= hoy0 && $0.fecha < ciclo.fin }
        r.ingresosConfirmados = ingresos.filter(\.confirmado).reduce(0) { $0 + $1.montoMinor }
        r.ingresosInciertos = ingresos.filter { !$0.confirmado }.reduce(0) { $0 + $1.montoMinor }
        r.pagosPendientes = pendientes.reduce(0) { $0 + $1.montoMinor }
        r.reservas = reservas(e)
        r.colchon = e.ajustes.colchonMinor
        // El saldo ya incorpora los movimientos ocurridos: no se restan otra vez.
        r.bruto = r.saldo + r.ingresosConfirmados - r.pagosPendientes - r.reservas - r.colchon
        r.proximoPago = pendientes.first

        // Semáforo por fecha de pago: una suma mensual positiva puede ocultar falta de liquidez antes de un ingreso.
        func fondos(hasta d: Date, inciertos: Bool) -> Centimos {
            let ing = ingresos.filter { $0.fecha <= d && ($0.confirmado || inciertos) }.reduce(0) { $0 + $1.montoMinor }
            let pag = pendientes.filter { $0.fecha <= d }.reduce(0) { $0 + $1.montoMinor }
            return r.saldo + ing - pag - r.reservas - r.colchon
        }
        let sinConfirmado = pendientes.filter { fondos(hasta: $0.fecha, inciertos: false) < 0 }
        let sinNada = pendientes.filter { fondos(hasta: $0.fecha, inciertos: true) < 0 }
        r.mood = sinConfirmado.isEmpty ? .bien : (sinNada.isEmpty ? .atento : .revisar)
        r.pagosSinCubrir = sinNada.isEmpty ? sinConfirmado : sinNada

        // Sugerencia de hoy: adaptador demo determinista con la forma de la regla de OctaCore
        // (mínimo por fecha de pago en 14 días), usando ingresos confirmados en vez de cuantiles.
        var puntos: [PuntoControl] = []
        for p in pendientes {
            let d = Fechas.dias(de: hoy0, a: p.fecha)
            guard d <= 14 else { continue }
            let f = fondos(hasta: p.fecha, inciertos: false)
            puntos.append(PuntoControl(id: p.id.uuidString, etiqueta: "\(p.nombre), \(Fechas.corta(p.fecha))", dia: max(d, 0),
                                       permitido: f / max(d, 1), limita: false))
        }
        let d14 = Fechas.cal.date(byAdding: .day, value: 14, to: hoy0)!
        puntos.append(PuntoControl(id: "dia14", etiqueta: "Día 14", dia: 14, permitido: fondos(hasta: d14, inciertos: false) / 14, limita: false))
        if let minimo = puntos.map(\.permitido).min(), let i = puntos.firstIndex(where: { $0.permitido == minimo }) {
            puntos[i].limita = true
            r.sugerenciaHoy = max(0, minimo / 100 * 100)
        }
        r.puntos = puntos
        return r
    }

    static func gastado(_ e: Estado, categoria: String, ciclo: Ciclo) -> Centimos {
        -e.movimientos.filter { $0.categoriaId == categoria && $0.montoMinor < 0 && $0.fecha >= ciclo.inicio && $0.fecha < ciclo.fin }
            .reduce(0) { $0 + $1.montoMinor }
    }

    static func progreso(_ p: Plan, _ e: Estado, hoy: Date) -> (valor: Double, texto: String) {
        func razon(_ a: Centimos, _ b: Centimos) -> Double { b > 0 ? min(1, Double(a) / Double(b)) : 0 }
        switch p.tipo {
        case .presupuesto:
            let g = gastado(e, categoria: p.categoriaId, ciclo: ciclo(hoy: hoy, dia: e.ajustes.cicloDia))
            return (razon(g, p.importeMinor), "Gastado \(Dinero.texto(g)) de \(Dinero.texto(p.importeMinor))")
        case .meta:
            let a = e.metas.first { $0.id == p.refId }?.ahorradoMinor ?? 0
            return (razon(a, p.importeMinor), "Ahorrado \(Dinero.texto(a)) de \(Dinero.texto(p.importeMinor))")
        case .reserva:
            return (razon(p.reservadoMinor, p.importeMinor), "Separado \(Dinero.texto(p.reservadoMinor)) de \(Dinero.texto(p.importeMinor))")
        case .recordatorio:
            return (p.estado == .completado ? 1 : 0, p.estado == .completado ? "Hecho" : "Te avisamos el \(Fechas.larga(p.fecha))")
        }
    }

    static func insights(_ e: Estado, _ r: Resumen) -> [Insight] {
        guard r.hayDatos else { return [] }
        var out: [Insight] = []
        if let p = r.proximoPago {
            let cubierto = !r.pagosSinCubrir.contains(p)
            out.append(Insight(id: "pago", icono: "calendar",
                               titulo: "\(p.nombre) vence el \(Fechas.corta(p.fecha)): \(Dinero.texto(p.montoMinor))",
                               fundamento: cubierto ? "Ya está descontado de tu disponible del mes." : "Con tu saldo confirmado todavía no alcanza para esa fecha.",
                               accion: "Organizar mis pagos", contexto: "organizar"))
        }
        let subs = e.movimientos.filter { $0.categoriaId == "subscriptions" && $0.montoMinor < 0 && $0.fecha >= r.ciclo.inicio && $0.fecha < r.ciclo.fin }
        if !subs.isEmpty {
            let total = -subs.reduce(0) { $0 + $1.montoMinor }
            out.append(Insight(id: "subs", icono: "repeat.circle",
                               titulo: "Suscripciones de este mes: \(Dinero.texto(total))",
                               fundamento: "Suma de \(subs.count) cobros registrados desde el \(Fechas.corta(r.ciclo.inicio)).",
                               accion: "Planificar una reducción", contexto: "suscripciones"))
        }
        if let m = e.metas.first, m.objetivoMinor > 0 {
            let pct = m.ahorradoMinor * 100 / m.objetivoMinor
            out.append(Insight(id: "meta", icono: "target",
                               titulo: "\(m.titulo): vas en \(pct) %",
                               fundamento: "\(Dinero.texto(m.ahorradoMinor)) de \(Dinero.texto(m.objetivoMinor)), con fecha \(Fechas.corta(m.fechaObjetivo)).",
                               accion: "Crear otra meta", contexto: "meta"))
        } else {
            out.append(Insight(id: "meta", icono: "target", titulo: "Aún no tienes una meta de ahorro",
                               fundamento: "No hay metas registradas en tus datos.", accion: "Crear una meta", contexto: "meta"))
        }
        return Array(out.prefix(3))
    }

    static func logros(_ e: Estado, _ r: Resumen) -> [Logro] {
        guard r.hayDatos else { return [] }
        var out: [Logro] = []
        let delCiclo = e.pagos.filter { $0.fecha >= r.ciclo.inicio && $0.fecha < r.ciclo.fin }
        if !delCiclo.isEmpty {
            out.append(Logro(id: "pagos", texto: "\(delCiclo.filter(\.pagado).count) de \(delCiclo.count) pagos registrados"))
        }
        let enRegla = e.planes.filter { $0.tipo == .presupuesto && $0.estado.activo }
            .filter { gastado(e, categoria: $0.categoriaId, ciclo: r.ciclo) <= $0.importeMinor }
        let totalPres = e.planes.filter { $0.tipo == .presupuesto && $0.estado.activo }.count
        if totalPres > 0 { out.append(Logro(id: "pres", texto: "\(enRegla.count) de \(totalPres) presupuestos dentro del límite")) }
        return out
    }
}

import Foundation

/// Importes en céntimos enteros (PEN). Nunca Double para dinero.
typealias Centimos = Int

struct Categoria: Codable, Identifiable, Hashable {
    var id: String
    var nombre: String
    var icono: String
}

struct Cuenta: Codable, Identifiable, Hashable {
    var id: String
    var nombre: String
    var saldoMinor: Centimos
    var moneda: String = "PEN"
    var esDemo: Bool = true
}

struct Movimiento: Codable, Identifiable, Hashable {
    var id: UUID = UUID()
    var cuentaId: String
    /// Con signo: ingreso positivo, gasto negativo.
    var montoMinor: Centimos
    var categoriaId: String
    var fecha: Date
    var comercio: String
    var esDemo: Bool = true
    /// Enlace reversible con un pago pendiente.
    var pagoId: UUID?
}

struct PagoConFecha: Codable, Identifiable, Hashable {
    var id: UUID = UUID()
    var nombre: String
    var montoMinor: Centimos
    var fecha: Date
    var categoriaId: String
    var pagado: Bool = false
}

struct IngresoEsperado: Codable, Identifiable, Hashable {
    var id: UUID = UUID()
    var nombre: String
    var montoMinor: Centimos
    var fecha: Date
    var confirmado: Bool
}

struct Presupuesto: Codable, Identifiable, Hashable {
    var id: UUID = UUID()
    var categoriaId: String
    var limiteMinor: Centimos
    var cicloId: String
}

struct Meta: Codable, Identifiable, Hashable {
    var id: UUID = UUID()
    var titulo: String
    var objetivoMinor: Centimos
    var ahorradoMinor: Centimos = 0
    var fechaObjetivo: Date
}

enum TipoPlan: String, Codable, CaseIterable, Identifiable {
    case reserva, presupuesto, meta, recordatorio
    var id: String { rawValue }
    var nombre: String {
        switch self {
        case .reserva: "Reserva para un pago"
        case .presupuesto: "Presupuesto de categoría"
        case .meta: "Meta de ahorro"
        case .recordatorio: "Recordatorio"
        }
    }
    var icono: String {
        switch self {
        case .reserva: "calendar"
        case .presupuesto: "chart.bar"
        case .meta: "target"
        case .recordatorio: "bell"
        }
    }
}

enum EstadoPlan: String, Codable, CaseIterable {
    case borrador, programado, necesitaConfirmacion, enCurso, completado, pausado, error
    var nombre: String {
        switch self {
        case .borrador: "Borrador"
        case .programado: "Programado"
        case .necesitaConfirmacion: "Necesita confirmación"
        case .enCurso: "En curso"
        case .completado: "Completado"
        case .pausado: "Pausado"
        case .error: "Error"
        }
    }
    var icono: String {
        switch self {
        case .borrador: "pencil.circle"
        case .programado: "clock"
        case .necesitaConfirmacion: "questionmark.circle.fill"
        case .enCurso: "arrow.triangle.2.circlepath"
        case .completado: "checkmark.circle.fill"
        case .pausado: "pause.circle"
        case .error: "xmark.octagon.fill"
        }
    }
    var activo: Bool { self == .programado || self == .enCurso || self == .necesitaConfirmacion }
}

enum Periodicidad: String, Codable, CaseIterable, Identifiable {
    case none, weekly, monthly
    var id: String { rawValue }
    var nombre: String {
        switch self {
        case .none: "Una vez"
        case .weekly: "Cada semana"
        case .monthly: "Cada mes"
        }
    }
}

enum OrigenPlan: String, Codable {
    case usuario, ukku
    var nombre: String { self == .usuario ? "Creado contigo" : "Creado con Ukku" }
}

struct Plan: Codable, Identifiable, Hashable {
    var id: UUID = UUID()
    var tipo: TipoPlan
    var titulo: String
    var importeMinor: Centimos
    var fecha: Date
    var periodicidad: Periodicidad = .none
    var categoriaId: String
    var origen: OrigenPlan
    var estado: EstadoPlan
    var estadoAntesDePausa: EstadoPlan?
    /// Meta o Presupuesto asociado.
    var refId: UUID?
    /// Pago pendiente al que se dedica la reserva (ya descontado del disponible).
    var pagoId: UUID?
    var reservadoMinor: Centimos = 0
    var creado: Date
    var esDemo: Bool = false
}

/// Evento de historial. Los vencimientos usan id "plan|fecha" para ser idempotentes.
struct Ejecucion: Codable, Identifiable, Hashable {
    enum Tipo: String, Codable {
        case creado, editado, pausado, reanudado, reprogramado, vencimiento, completado, eliminado, aporte, movimiento, presupuesto
    }
    var id: String
    var planId: UUID?
    var tipo: Tipo
    var fecha: Date
    var resumen: String
}

enum Arg: Codable, Hashable {
    case s(String), i(Int)
    init(from decoder: Decoder) throws {
        let c = try decoder.singleValueContainer()
        if let v = try? c.decode(Int.self) { self = .i(v) } else { self = .s(try c.decode(String.self)) }
    }
    func encode(to encoder: Encoder) throws {
        var c = encoder.singleValueContainer()
        switch self {
        case .s(let v): try c.encode(v)
        case .i(let v): try c.encode(v)
        }
    }
    var texto: String? { if case .s(let v) = self { v } else { nil } }
    var entero: Int? { if case .i(let v) = self { v } else { nil } }
}

/// Propuesta estructurada (CONTRATO-ACCIONES.json). La usan el chat y los formularios.
struct PropuestaAccion: Codable, Identifiable, Hashable {
    enum Fuente: String, Codable { case llm, ejemplo, manual }
    var id: UUID = UUID()
    var tool: String
    var arguments: [String: Arg]
    var source: Fuente
    var requiresConfirmation: Bool = true
    var contextVersion: Int
}

struct ResultadoAccion: Codable, Hashable {
    var proposalId: UUID
    var status: String = "applied"
    var entityId: String
    var executedAt: Date
    var summary: String
    var planId: UUID?
}

struct MensajeChat: Codable, Identifiable, Hashable {
    enum Rol: String, Codable { case usuario, ukku, sistema }
    enum Fuente: String, Codable { case ia, ejemplo, sistema, usuario }
    var id: UUID = UUID()
    var rol: Rol
    var fuente: Fuente
    var texto: String
    var fecha: Date
    var propuesta: PropuestaAccion?
    var resultado: ResultadoAccion?
    var aviso: String?
    /// Para reintentar sin duplicar: el backend responde lo mismo al mismo id.
    var solicitudFallida: String?
}

struct Ajustes: Codable, Hashable {
    var nombre: String = "Camila"
    var cicloDia: Int = 1
    var colchonMinor: Centimos = 20_000
    var notificaciones: Bool = false
    var ocultarImportes: Bool = false
    var reducirMovimiento: Bool = false
    var endpointIA: String = "http://127.0.0.1:8787"
}

enum Escenario: String, Codable, CaseIterable, Identifiable {
    case base, depende, revisar, vacio
    var id: String { rawValue }
    var nombre: String {
        switch self {
        case .base: "Base: pagos cubiertos"
        case .depende: "Depende de un ingreso"
        case .revisar: "Pago sin cubrir"
        case .vacio: "Sin historia"
        }
    }
}

/// Fuente de verdad única, persistida como JSON.
struct Estado: Codable {
    var esquema: Int = 1
    var escenario: Escenario = .base
    var contextVersion: Int = 1
    var ajustes = Ajustes()
    var categorias: [Categoria] = []
    var cuentas: [Cuenta] = []
    var movimientos: [Movimiento] = []
    var pagos: [PagoConFecha] = []
    var ingresos: [IngresoEsperado] = []
    var presupuestos: [Presupuesto] = []
    var metas: [Meta] = []
    var planes: [Plan] = []
    var ejecuciones: [Ejecucion] = []
    var aplicadas: [String: ResultadoAccion] = [:]
    var chat: [MensajeChat] = []
}

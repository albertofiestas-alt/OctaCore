import Foundation
import UserNotifications

enum Persistencia {
    static var url: URL {
        let dir = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir.appendingPathComponent("ukku-estado.json")
    }
    private static var enc: JSONEncoder {
        let e = JSONEncoder()
        e.dateEncodingStrategy = .iso8601
        e.outputFormatting = [.prettyPrinted, .sortedKeys]
        return e
    }
    private static var dec: JSONDecoder {
        let d = JSONDecoder()
        d.dateDecodingStrategy = .iso8601
        return d
    }
    static func cargar() -> Estado? {
        guard let data = try? Data(contentsOf: url) else { return nil }
        return try? dec.decode(Estado.self, from: data)
    }
    static func guardar(_ e: Estado) {
        guard let data = try? enc.encode(e) else { return }
        try? data.write(to: url, options: .atomic)
    }
    static func exportar(_ e: Estado) -> String {
        (try? enc.encode(e)).flatMap { String(data: $0, encoding: .utf8) } ?? "{}"
    }
}

/// Recordatorios locales opt-in. iOS no garantiza hora exacta: se describen como recordatorio.
enum Notificaciones {
    static func pedirPermiso() async -> Bool {
        (try? await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound])) ?? false
    }
    static func sincronizar(planes: [Plan], activas: Bool, ahora: Date) {
        let centro = UNUserNotificationCenter.current()
        centro.removeAllPendingNotificationRequests()
        guard activas else { return }
        for p in planes where (p.tipo == .recordatorio || p.tipo == .reserva) && p.estado == .programado {
            var fecha = p.fecha
            if p.tipo == .reserva { fecha = Fechas.cal.date(bySettingHour: 9, minute: 0, second: 0, of: p.fecha) ?? p.fecha }
            guard fecha > ahora else { continue }
            let c = UNMutableNotificationContent()
            c.title = "Ukku: \(p.titulo)"
            c.body = p.tipo == .reserva ? "Hoy vence este plan. Ukku no paga por ti: revisa si ya lo hiciste." : "Recordatorio que programaste."
            let comp = Fechas.cal.dateComponents([.year, .month, .day, .hour, .minute], from: fecha)
            centro.add(UNNotificationRequest(identifier: p.id.uuidString, content: c,
                                             trigger: UNCalendarNotificationTrigger(dateMatching: comp, repeats: false)))
        }
    }
}

// MARK: - Proveedor de IA (backend local; la app no guarda secretos)

enum EstadoIA: Equatable {
    case comprobando
    case conectada(modelo: String)
    case sinCredencial
    case sinBackend
    var conectada: Bool { if case .conectada = self { true } else { false } }
    var texto: String {
        switch self {
        case .comprobando: "Comprobando la conexión"
        case .conectada(let m): "IA conectada (\(m))"
        case .sinCredencial: "IA sin conectar: falta la credencial en tu computadora"
        case .sinBackend: "IA sin conectar: no se encuentra el servicio local"
        }
    }
}

struct RespuestaIA: Decodable {
    struct Prop: Decodable {
        var id: UUID
        var tool: String
        var arguments: [String: Arg]
    }
    var text: String
    var proposals: [Prop]
}

struct ErrorIA: Error { var mensaje: String }

protocol LLMProvider {
    func estado() async -> EstadoIA
    func chat(solicitud: String, mensajes: [[String: String]], contexto: [String: Any]) async throws -> RespuestaIA
}

struct BackendLLM: LLMProvider {
    var base: String

    private func url(_ ruta: String) -> URL? {
        guard let u = URL(string: base.trimmingCharacters(in: .whitespaces)), let host = u.host,
              ["127.0.0.1", "localhost"].contains(host) else { return nil } // solo acceso local controlado
        return u.appendingPathComponent(ruta)
    }

    func estado() async -> EstadoIA {
        guard let u = url("health") else { return .sinBackend }
        var req = URLRequest(url: u)
        req.timeoutInterval = 3
        guard let (data, resp) = try? await URLSession.shared.data(for: req), (resp as? HTTPURLResponse)?.statusCode == 200,
              let j = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return .sinBackend }
        if j["connected"] as? Bool == true { return .conectada(modelo: j["model"] as? String ?? "modelo configurado") }
        return .sinCredencial
    }

    func chat(solicitud: String, mensajes: [[String: String]], contexto: [String: Any]) async throws -> RespuestaIA {
        guard let u = url("chat") else { throw ErrorIA(mensaje: "El endpoint debe ser local (127.0.0.1).") }
        var req = URLRequest(url: u)
        req.httpMethod = "POST"
        req.timeoutInterval = 45
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: ["request_id": solicitud, "messages": mensajes, "context": contexto])
        let data: Data, resp: URLResponse
        do { (data, resp) = try await URLSession.shared.data(for: req) } catch let e as URLError where e.code == .timedOut {
            throw ErrorIA(mensaje: "La IA tardó demasiado en responder.")
        } catch { throw ErrorIA(mensaje: "No pudimos conectar con el backend local.") }
        guard (resp as? HTTPURLResponse)?.statusCode == 200 else {
            let m = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["error"] as? String
            throw ErrorIA(mensaje: m ?? "El backend respondió con un error.")
        }
        guard let r = try? JSONDecoder().decode(RespuestaIA.self, from: data) else { throw ErrorIA(mensaje: "La respuesta de la IA no tiene el formato esperado.") }
        return r
    }
}

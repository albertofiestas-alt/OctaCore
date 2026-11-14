import XCTest

final class UkkuFlowTests: XCTestCase {
    @MainActor private func app(_ scenario: String = "base") -> XCUIApplication {
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchArguments = ["--escenario", scenario, "--sin-saludo", "-AppleLanguages", "(es)", "-AppleLocale", "es_PE"]
        app.launch()
        XCTAssertTrue(app.tabBars.buttons["Inicio"].waitForExistence(timeout: 15))
        return app
    }

    @MainActor private func capture(_ name: String, _ app: XCUIApplication) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name; attachment.lifetime = .keepAlways; add(attachment)
    }

    @MainActor func testScenarioDoesNotChangeBalance() {
        let app = app()
        XCTAssertEqual(app.staticTexts["disponible-mes"].label, "S/ 1,260")
        capture("01-inicio", app)
        app.buttons["abrir-simulador"].tap()
        XCTAssertTrue(app.staticTexts["resultado-diario"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.staticTexts["resultado-diario"].label, "S/ 82")
        capture("02-simulador", app)
        app.buttons["monto-rapido-1500"].tap()
        app.swipeUp()
        XCTAssertTrue(app.staticTexts["alerta-simulacion"].waitForExistence(timeout: 5))
        capture("03-alerta", app)
        app.buttons["cerrar-simulador"].tap()
        XCTAssertEqual(app.staticTexts["disponible-mes"].label, "S/ 1,260")
        app.buttons["abrir-simulador"].tap()
        app.segmentedControls.buttons["Ingreso"].tap()
        XCTAssertTrue(app.textFields["ingreso-simulacion"].waitForExistence(timeout: 5))
        app.swipeUp()
        XCTAssertEqual(app.staticTexts["resultado-diario"].label, "S/ 111")
        capture("04-ingreso", app)
    }

    @MainActor func testCreateGoalAndPersist() {
        let app = app()
        app.tabBars.buttons["Tu plan"].tap()
        capture("05-tu-plan", app)
        app.buttons["crear-meta"].tap()
        let name = app.textFields["nombre-plan"]
        XCTAssertTrue(name.waitForExistence(timeout: 5)); name.tap(); name.typeText("Mi viaje")
        let amount = app.textFields["monto-plan"]
        amount.tap(); amount.typeText("600")
        app.buttons["revisar-plan"].tap()
        XCTAssertTrue(app.buttons["confirmar-accion"].waitForExistence(timeout: 5))
        capture("06-confirmacion", app)
        app.buttons["confirmar-accion"].tap()
        XCTAssertTrue(app.staticTexts["accion-guardada"].waitForExistence(timeout: 5))
        capture("07-guardado", app)
        app.buttons["finalizar-accion"].tap()
        app.swipeUp()
        XCTAssertTrue(app.staticTexts["Mi viaje"].exists)
        app.terminate()
        app.launchArguments = ["--sin-saludo", "--pestana", "1"]
        app.launch()
        XCTAssertTrue(app.buttons["crear-meta"].waitForExistence(timeout: 10))
        app.swipeUp()
        XCTAssertTrue(app.staticTexts["Mi viaje"].exists)
    }

    @MainActor func testMovementAndSearch() {
        let app = app()
        app.tabBars.buttons["Actividad"].tap()
        capture("08-actividad", app)
        app.buttons["agregar-movimiento"].tap()
        let amount = app.textFields["monto-movimiento"]
        XCTAssertTrue(amount.waitForExistence(timeout: 5)); amount.tap(); amount.typeText("25.50")
        app.textFields["comercio-movimiento"].tap(); app.textFields["comercio-movimiento"].typeText("Cafe Codex")
        app.buttons["revisar-movimiento"].tap()
        app.buttons["confirmar-accion"].tap()
        XCTAssertTrue(app.staticTexts["accion-guardada"].waitForExistence(timeout: 5))
        app.buttons["finalizar-accion"].tap()
        let search = app.textFields["buscar-movimientos"]
        XCTAssertTrue(search.waitForExistence(timeout: 5)); search.tap(); search.typeText("Cafe Codex")
        XCTAssertTrue(app.buttons.containing(.staticText, identifier: "Cafe Codex").firstMatch.exists)
        app.buttons["Terminar búsqueda"].tap()
        app.tabBars.buttons["Inicio"].tap()
        XCTAssertTrue(app.staticTexts["disponible-mes"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.staticTexts["disponible-mes"].label, "S/ 1,234.50")
    }

    @MainActor func testEmptyStateAndPrivacy() {
        let app = app("vacio")
        capture("09-vacio", app)
        app.buttons["cargar-demo"].tap()
        XCTAssertTrue(app.buttons["abrir-simulador"].waitForExistence(timeout: 5))
        app.buttons["privacidad-inicio"].tap()
        XCTAssertEqual(app.staticTexts["disponible-mes"].label, "S/ •••")
        capture("10-privacidad", app)
        app.tabBars.buttons["Ajustes"].tap()
        capture("11-ajustes", app)
    }

    @MainActor func testPaymentRegistrationAndUndo() {
        let app = app()
        app.swipeUp()
        app.buttons["proximo-pago"].tap()
        app.buttons.containing(.staticText, identifier: "Alquiler").firstMatch.tap()
        XCTAssertTrue(app.buttons["revisar-movimiento"].waitForExistence(timeout: 5))
        app.buttons["revisar-movimiento"].tap()
        app.buttons["confirmar-accion"].tap()
        XCTAssertTrue(app.staticTexts["accion-guardada"].waitForExistence(timeout: 5))
        app.buttons["finalizar-accion"].tap()
        app.buttons["Listo"].tap()
        app.tabBars.buttons["Actividad"].tap()
        app.buttons.containing(.staticText, identifier: "Alquiler").firstMatch.tap()
        app.buttons["Eliminar movimiento"].tap()
        let confirmation = app.sheets.buttons.matching(identifier: "confirmar-eliminar-movimiento").firstMatch
        XCTAssertTrue(confirmation.waitForExistence(timeout: 5))
        confirmation.tap()
        let visibleTab = NSPredicate(format: "isHittable == true")
        expectation(for: visibleTab, evaluatedWith: app.tabBars.buttons["Inicio"])
        waitForExpectations(timeout: 5)
        app.tabBars.buttons["Inicio"].tap()
        app.swipeDown()
        XCTAssertTrue(app.staticTexts["disponible-mes"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.staticTexts["disponible-mes"].label, "S/ 1,260")
        XCTAssertTrue(app.buttons["proximo-pago"].exists)
    }
}

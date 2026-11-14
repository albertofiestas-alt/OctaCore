#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
UKKU_TEST_TMP=$(mktemp -d)
trap 'rm -rf "$UKKU_TEST_TMP"' EXIT
swiftc Sources/Models/Modelos.swift Sources/Models/Seed.swift Sources/Services/Calculo.swift Sources/Services/Acciones.swift Sources/Services/RegistroPago.swift Sources/Services/Simulacion.swift Tests/DominioTests.swift -o "$UKKU_TEST_TMP/pruebas"
"$UKKU_TEST_TMP/pruebas"

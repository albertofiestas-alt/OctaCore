#!/bin/sh
# Uso: herramientas/captura.sh nombre [carpeta]   -> <carpeta>/nombre.png (por defecto evidencias-premium)
C="${2:-evidencias-premium}"
xcrun simctl io E2064532-A568-4F32-A8F3-9343A9E431FB screenshot "$(dirname "$0")/../$C/$1.png" >/dev/null 2>&1 && echo "$C/$1.png"

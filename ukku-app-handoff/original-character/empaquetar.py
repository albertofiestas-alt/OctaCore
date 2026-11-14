#!/usr/bin/env python3
"""Regenera, verifica y empaqueta exclusivamente el personaje original."""
from pathlib import Path
import subprocess,zipfile,json
ROOT=Path(__file__).resolve().parent
for script in ('generar_catalogo.py','verificar_catalogo.py'):
 subprocess.run(['python3',str(ROOT/script)],cwd=ROOT,check=True)
out=ROOT/'Ukku-personaje-original.zip'
files=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and p!=out and p.suffix!='.zip' and '__pycache__' not in p.parts and not p.name.startswith('.')]
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,'Ukku-personaje-original/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
print(json.dumps({'zip':str(out),'archivos':len(files),'bytes':out.stat().st_size},ensure_ascii=False))

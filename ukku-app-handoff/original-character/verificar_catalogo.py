#!/usr/bin/env python3
"""Verifica enlaces locales, inventario y secuencias sin editar medios."""
from pathlib import Path
from html.parser import HTMLParser
from PIL import Image
import json,re,subprocess,shutil
ROOT=Path(__file__).resolve().parent
errors=[]
class Links(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for key,value in attrs:
   if key in ('src','href') and value and not value.startswith(('http:','https:','#','data:')) and not (ROOT/value).is_file():errors.append('Enlace ausente: '+value)
Links().feed((ROOT/'CATALOGO.html').read_text())
inv=json.loads((ROOT/'inventario.json').read_text())
for d in inv['archivos']:
 p=ROOT/d['ruta']
 if not p.is_file():errors.append('Archivo ausente: '+d['ruta'])
 if p.stat().st_size!=d['bytes']:errors.append('Inventario desactualizado: '+d['ruta'])
for c in inv['clips']:
 names=[Path(p).name for p in c['frames']]
 if names!=[f'{i:04}.png' for i in range(len(names))]:errors.append('Numeración incompleta: '+c['nombre'])
 sizes=set()
 for frame in c['frames']:
  with Image.open(ROOT/frame) as im:
   sizes.add(im.size)
   if 'A' not in im.getbands():errors.append('Sin canal alfa: '+frame)
 if sizes!={(480,480)}:errors.append('Dimensiones clip: '+c['nombre']+' '+str(sizes))
 if len(names)>96:errors.append('Más de 96 frames: '+c['nombre'])
print(json.dumps({'resultado':'CORRECTO' if not errors else 'REVISAR','medios':len(inv['archivos']),'clips':len(inv['clips']),'errores':errors},ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))

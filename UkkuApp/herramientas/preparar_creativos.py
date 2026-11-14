"""Recorta el oso del logo maestro (sin escalar ni redibujar) y genera el icono.
Uso: python preparar_creativos.py <logo-maestro.png> <Assets.xcassets>"""
import sys
from pathlib import Path
from PIL import Image

maestro, destino = Image.open(sys.argv[1]).convert("RGBA"), Path(sys.argv[2])
alfa = maestro.getchannel("A").point(lambda a: 255 if a > 16 else 0)
# Primera columna vacía después del oso: separa personaje y logotipo.
ancho, alto = maestro.size
ocupada = [alfa.crop((x, 0, x + 1, alto)).getbbox() is not None for x in range(ancho)]
inicio = ocupada.index(True)
fin = next(x for x in range(inicio, ancho) if not ocupada[x])
caja = alfa.crop((inicio, 0, fin, alto)).getbbox()
oso = maestro.crop((inicio + caja[0], caja[1], inicio + caja[2], caja[3]))
lado = max(oso.size)
lienzo = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
lienzo.paste(oso, ((lado - oso.width) // 2, lado - oso.height), oso)   # base apoyada, centrado
lienzo.save(destino / "ukku-maestro.imageset" / "ukku-maestro.png")
maestro.save(destino / "ukku-logo.imageset" / "ukku-logo.png")
fondo = Image.new("RGBA", (1024, 1024), (245, 247, 251, 255))
esc = 800 / lado
chico = oso.resize((round(oso.width * esc), round(oso.height * esc)), Image.LANCZOS)
fondo.paste(chico, ((1024 - chico.width) // 2, 1024 - chico.height - 60), chico)
fondo.convert("RGB").save(destino / "AppIcon.appiconset" / "AppIcon.png")
print("oso:", oso.size, "lienzo:", lado)

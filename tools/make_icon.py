"""
Genera el ícono de la aplicación (assets/app.ico)

Uso: python tools/make_icon.py

El ícono se usa en el ejecutable (PyInstaller), en el instalador (Inno Setup)
y, mediante src.gui.brand, como icono de las ventanas. Requiere Pillow.

La marca es la misma en todo el producto (SDEP): el isotipo del escritorio se
dibuja con el mismo criterio que el de la interfaz, de modo que el icono del
.exe, el del instalador y el del login no se contradigan.
"""

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "assets" / "app.ico"

# Degradado de la marca (mismos tonos que la paleta de la interfaz).
AZUL_SUPERIOR = (59, 130, 246)  # #3b82f6 (acento)
AZUL_INFERIOR = (30, 58, 138)  # #1e3a8a (azul profundo)

TAMANO_BASE = 512
MARGEN = 26
RADIO = 108
TAMANOS_ICO = [16, 20, 24, 32, 40, 48, 64, 128, 256]


def _fuente(tamano: int):
    candidatas = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for ruta in candidatas:
        if os.path.exists(ruta):
            try:
                return ImageFont.truetype(ruta, tamano)
            except OSError:
                continue
    return ImageFont.load_default()


def _degradado_vertical(ancho: int, alto: int) -> Image.Image:
    """Degradado vertical continuo entre los dos azules de la marca."""
    degradado = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(degradado)
    for y in range(alto):
        t = y / max(1, alto - 1)
        color = tuple(
            int(AZUL_SUPERIOR[i] + (AZUL_INFERIOR[i] - AZUL_SUPERIOR[i]) * t) for i in range(3)
        )
        dibujo.line([(0, y), (ancho, y)], fill=color + (255,))
    return degradado


def generar_icono(ruta: Path) -> None:
    """
    Dibuja el isotipo: cuadrado redondeado con degradado azul y una «S» blanca.

    El degradado se recorta con una máscara redondeada. Antes se pintaba con
    líneas horizontales sobre el cuadrado ya dibujado y esas líneas tapaban
    las esquinas, de modo que el icono salía con esquinas rectas.
    """
    degradado = _degradado_vertical(TAMANO_BASE, TAMANO_BASE)

    mascara = Image.new("L", (TAMANO_BASE, TAMANO_BASE), 0)
    ImageDraw.Draw(mascara).rounded_rectangle(
        [MARGEN, MARGEN, TAMANO_BASE - MARGEN, TAMANO_BASE - MARGEN],
        radius=RADIO,
        fill=255,
    )

    img = Image.new("RGBA", (TAMANO_BASE, TAMANO_BASE), (0, 0, 0, 0))
    img.paste(degradado, (0, 0), mascara)

    # Monograma centrado, ajustado por la caja real del glifo para que quede
    # ópticamente centrado y no desplazado por el hueco de la línea base.
    dibujo = ImageDraw.Draw(img)
    fuente = _fuente(300)
    caja = dibujo.textbbox((0, 0), "S", font=fuente)
    x = int((TAMANO_BASE - (caja[2] - caja[0])) / 2 - caja[0])
    y = int((TAMANO_BASE - (caja[3] - caja[1])) / 2 - caja[1])
    dibujo.text((x, y), "S", font=fuente, fill=(255, 255, 255, 255))

    ruta.parent.mkdir(parents=True, exist_ok=True)
    img.save(ruta, format="ICO", sizes=[(s, s) for s in TAMANOS_ICO])
    print(f"Ícono generado: {ruta}")


if __name__ == "__main__":
    generar_icono(SALIDA)

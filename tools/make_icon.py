"""
Genera el ícono de la aplicación (assets/app.ico)

Uso: python tools/make_icon.py

El ícono se usa en el ejecutable (PyInstaller) y en el instalador
(Inno Setup). Requiere Pillow.
"""

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "assets" / "app.ico"


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


def generar_icono(ruta: Path) -> None:
    """Dibuja un cuadrado redondeado azul con las siglas SGP"""
    tamano_base = 512
    img = Image.new("RGBA", (tamano_base, tamano_base), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margen = 24
    radio = 110
    azul = (34, 51, 77, 255)          # #22334d (panel de la marca)
    azul_claro = (58, 88, 130, 255)   # degradado inferior
    blanco = (255, 255, 255, 255)

    # Fondo redondeado con leve degradado vertical
    draw.rounded_rectangle(
        [margen, margen, tamano_base - margen, tamano_base - margen],
        radius=radio, fill=azul,
    )
    for y in range(margen, tamano_base - margen):
        t = (y - margen) / (tamano_base - 2 * margen)
        color = tuple(int(azul[i] + (azul_claro[i] - azul[i]) * t) for i in range(3)) + (255,)
        draw.line([(margen, y), (tamano_base - margen, y)], fill=color)

    # Símbolo central: "SGP"
    texto = "SGP"
    fuente = _fuente(210)
    caja = draw.textbbox((0, 0), texto, font=fuente)
    ancho_texto = caja[2] - caja[0]
    alto_texto = caja[3] - caja[1]
    x = (tamano_base - ancho_texto) // 2 - caja[0]
    y = (tamano_base - alto_texto) // 2 - caja[1]
    draw.text((x, y), texto, font=fuente, fill=blanco)

    # Redimensionar con suavizado a los tamaños que espera Windows
    img_redimensionada = img.resize((256, 256), Image.LANCZOS)

    ruta.parent.mkdir(parents=True, exist_ok=True)
    tamanos = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    img_redimensionada.save(
        ruta, format="ICO", sizes=[(s, s) for s in tamanos],
    )
    print(f"Ícono generado: {ruta}")


if __name__ == "__main__":
    generar_icono(SALIDA)

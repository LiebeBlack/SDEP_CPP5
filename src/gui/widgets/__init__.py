"""
Widgets de interfaz reutilizables

Componentes de dibujo propios (sin dependencias externas de gráficos)
usados por el Dashboard y por los módulos de reportes.
"""

from .graficos import (
    GraficoBarras,
    GraficoDona,
    GraficoLinea,
    TarjetaIndicador,
)

__all__ = [
    "GraficoBarras",
    "GraficoDona",
    "GraficoLinea",
    "TarjetaIndicador",
]

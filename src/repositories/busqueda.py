"""
Búsqueda insensible a mayúsculas y tildes

SQLite LIKE no normaliza los caracteres acentuados: "gomez" debe encontrar
"Gómez". Estas utilidades construyen la comparación en SQL (funciones sobre
la columna) y normalizan el término en Python. Vivían dentro del repositorio
de empleados y ahora las comparten los repositorios que buscan por nombre.
"""

from typing import Any

from sqlalchemy import func

# Pares (acentuada, plana) que se reemplazan en ambos lados de la comparación
_ACENTOS: tuple[tuple[str, str], ...] = (
    ("á", "a"),
    ("é", "e"),
    ("í", "i"),
    ("ó", "o"),
    ("ú", "u"),
    ("ü", "u"),
    ("ñ", "n"),
)


def normalizar_expr(columna: Any) -> Any:
    """Expresión SQL que pasa una columna a minúsculas sin tildes"""
    expr = func.lower(columna)
    for acento, plano in _ACENTOS:
        expr = func.replace(expr, acento, plano)
    return expr


def normalizar_termino(termino: str) -> str:
    """Normaliza un término de búsqueda: minúsculas y sin tildes"""
    texto = termino.lower()
    for acento, plano in _ACENTOS:
        texto = texto.replace(acento, plano)
    return texto

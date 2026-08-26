print("Prueba básica")

import sys
print("Python OK")

import os
print("OS OK")

from pathlib import Path
print("Pathlib OK")

project_root = Path(__file__).resolve().parent
print(f"Ruta: {project_root}")

print("Fin de prueba básica")
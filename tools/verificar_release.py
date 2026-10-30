"""Puerta de calidad previa a un release.

Comprueba, sin compilar ni publicar nada, las condiciones que un release
estable necesita antes de crear la etiqueta:

* la versión es la misma en todos los archivos que la declaran;
* el recurso de versión del actualizador no quedó fijo en una versión vieja;
* todo el código Python compila;
* el portal de documentación está sincronizado con las fuentes;
* no hay credenciales ni bases de datos rastreadas por Git;
* el árbol de trabajo está limpio.

Uso::

    python tools/verificar_release.py            # comprobaciones rápidas
    python tools/verificar_release.py --tests    # además, la suite completa

Devuelve 0 si todo está en orden, 1 si hay alguna falla. Los avisos no
bloquean el release pero deben revisarse antes de etiquetarlo.
"""

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# Rutas cuyo código debe compilar antes de empaquetar.
FUENTES = ("src", "sync_agent", "updater", "tools")
SUELTOS = ("build.py", "iniciar_servidor.py", "verificar_red.py")

# Credenciales: si están rastreadas, el release no puede salir.
BLOQUEANTES = (
    (re.compile(r"(^|/)\.env$"), "archivo de entorno"),
    (re.compile(r"\.(pfx|p12|key|pem)$"), "clave privada"),
    (re.compile(r"(^|/)id_(rsa|ed25519)$"), "clave SSH"),
)

# Datos que no deberían viajar en el repositorio, pero cuya limpieza es una
# decisión del responsable del proyecto (retirarlos cambia el índice de Git).
AVISABLES = (
    (re.compile(r"\.(db|sqlite|sqlite3)$"), "base de datos"),
    (re.compile(r"\.(db\.gz)$"), "respaldo comprimido"),
)

# Archivos históricos que ya no alimentan ningún build.
OBSOLETOS = ("updater/version_info.txt",)


class Resultado:
    """Una comprobación y su veredicto."""

    def __init__(self, nombre: str, estado: str, detalle: str = "") -> None:
        self.nombre = nombre
        self.estado = estado  # ok | aviso | falla
        self.detalle = detalle

    def __str__(self) -> str:
        marca = {"ok": "[OK]   ", "aviso": "[AVISO]", "falla": "[FALLA]"}[self.estado]
        return f"{marca} {self.nombre}" + (f": {self.detalle}" if self.detalle else "")


def _leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8").strip()


def _version() -> str:
    return _leer(RAIZ / "VERSION")


def _buscar_version(archivo: Path, patron: str) -> str | None:
    """Primera captura de ``patron`` en el archivo, o None si no aparece."""
    if not archivo.exists():
        return None
    coincidencia = re.search(patron, archivo.read_text(encoding="utf-8"), re.MULTILINE)
    return coincidencia.group(1).strip() if coincidencia else None


def verificar_versiones() -> list[Resultado]:
    """La versión debe ser una sola en todo el proyecto."""
    resultados: list[Resultado] = []
    version = _version()
    if not re.fullmatch(r"\d+\.\d+(\.\d+)*", version):
        return [Resultado("Versión", "falla", f"VERSION no es válida: {version!r}")]

    declaradas = {
        "pyproject.toml": _buscar_version(RAIZ / "pyproject.toml", r'^version\s*=\s*"([^"]+)"'),
        "src/config/settings.py": _buscar_version(
            RAIZ / "src" / "config" / "settings.py", r'APP_VERSION_DEFAULT\s*=\s*"([^"]+)"'
        ),
        "src/__init__.py": _buscar_version(
            RAIZ / "src" / "__init__.py", r'__version__\s*=\s*"([^"]+)"'
        ),
        "installer/setup.iss": _buscar_version(
            RAIZ / "installer" / "setup.iss", r'#define MyAppVersion "([^"]+)"'
        ),
    }
    distintas = {archivo: valor for archivo, valor in declaradas.items() if valor != version}
    if distintas:
        detalle = ", ".join(f"{archivo}={valor}" for archivo, valor in distintas.items())
        resultados.append(Resultado("Versión coherente", "falla", f"VERSION={version}; {detalle}"))
    else:
        resultados.append(
            Resultado(
                "Versión coherente",
                "ok",
                f"{version} en VERSION, pyproject, settings, __init__ e instalador",
            )
        )

    resultados.extend(_verificar_android(version))
    return resultados


def _verificar_android(version: str) -> list[Resultado]:
    """
    El teléfono declara la misma versión que el producto.

    La forma preferida es derivarla del archivo ``VERSION`` en el propio
    Gradle; si quedó un literal, se compara contra el producto y se avisa,
    porque un literal se olvida y el APK acaba anunciando una versión vieja.
    """
    archivo = RAIZ / "android" / "app" / "build.gradle.kts"
    if not archivo.exists():
        return [Resultado("Versión Android", "aviso", "no hay módulo Android en el proyecto")]
    texto = archivo.read_text(encoding="utf-8")

    literal = _buscar_version(archivo, r'versionName\s*=\s*"([^"]+)"')
    if literal is not None:
        if literal == version:
            return [Resultado("Versión Android", "ok", f"versionName={literal} (literal)")]
        # Un literal vuelve a separar la versión del teléfono de la del
        # producto: es la regresión que ya ocurrió con 1.0.0 frente a 3.0.1.
        return [
            Resultado(
                "Versión Android",
                "falla",
                f"versionName={literal} escrito a mano; debe derivarse de VERSION ({version})",
            )
        ]

    deriva = "VERSION" in texto and "versionName = versionProducto" in texto
    respaldo = _buscar_version(archivo, r'\?:\s*"(\d+\.\d+(?:\.\d+)*)"')
    if not deriva:
        return [Resultado("Versión Android", "falla", "build.gradle.kts no declara versionName")]
    if respaldo != version:
        return [
            Resultado(
                "Versión Android",
                "falla",
                f"se deriva de VERSION pero el respaldo sin archivo es {respaldo!r} y el producto es {version}",
            )
        ]
    if "versionCode = codigoVersion" not in texto:
        return [
            Resultado(
                "Versión Android",
                "falla",
                "versionCode fijo: el APK no subiría de código en cada release",
            )
        ]
    partes = [int(p) for p in version.split(".")]
    codigo = (
        partes[0] * 10_000
        + (partes[1] if len(partes) > 1 else 0) * 100
        + (partes[2] if len(partes) > 2 else 0)
    )
    return [Resultado("Versión Android", "ok", f"{version} derivada de VERSION (código {codigo})")]


def verificar_actualizador() -> list[Resultado]:
    """El actualizador se distribuye con su versión; no debe quedar fija."""
    spec = RAIZ / "updater" / "updater.spec"
    if not spec.exists():
        return [Resultado("Recurso del actualizador", "falla", "falta updater/updater.spec")]
    texto = spec.read_text(encoding="utf-8")
    resultados = []
    # Un comentario que menciona el archivo viejo es historia; lo que importa es
    # que el recurso no se siga tomando de él.
    usa_archivo_fijo = bool(re.search(r"version_resource\s*=\s*str\([^)]*version_info\.txt", texto))
    if usa_archivo_fijo:
        resultados.append(
            Resultado(
                "Recurso del actualizador",
                "falla",
                "updater.spec usa un version_info.txt fijo; debe derivarse de VERSION",
            )
        )
    elif "VERSION" not in texto:
        resultados.append(
            Resultado("Recurso del actualizador", "falla", "updater.spec no lee VERSION")
        )
    else:
        resultados.append(
            Resultado("Recurso del actualizador", "ok", "la versión se deriva de VERSION")
        )
    for obsoleto in OBSOLETOS:
        ruta = RAIZ / obsoleto
        if ruta.exists():
            resultados.append(
                Resultado(
                    "Archivo obsoleto",
                    "aviso",
                    f"{obsoleto} ya no se usa; su contenido puede contradecir la versión",
                )
            )
    return resultados


def verificar_sintaxis() -> list[Resultado]:
    """Compila todo el árbol sin ejecutarlo ni escribir cachés."""
    archivos: list[Path] = []
    for carpeta in FUENTES:
        archivos.extend(sorted((RAIZ / carpeta).rglob("*.py")))
    archivos.extend(RAIZ / nombre for nombre in SUELTOS if (RAIZ / nombre).exists())

    errores = []
    for archivo in archivos:
        if "__pycache__" in archivo.parts:
            continue
        try:
            ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
        except (SyntaxError, UnicodeDecodeError) as error:
            errores.append(f"{archivo.relative_to(RAIZ)}: {error}")

    if errores:
        return [Resultado("Sintaxis Python", "falla", "; ".join(errores[:5]))]
    return [Resultado("Sintaxis Python", "ok", f"{len(archivos)} archivos compilan")]


def verificar_documentacion() -> list[Resultado]:
    """El portal de docs debe corresponder a los .md de las fuentes."""
    generador = RAIZ / "tools" / "verify_docs.py"
    if not generador.exists():
        return [Resultado("Documentación", "aviso", "falta tools/verify_docs.py")]
    proceso = subprocess.run(
        [sys.executable, str(generador)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proceso.returncode == 0:
        salida = (proceso.stdout or "").strip().splitlines()
        return [Resultado("Documentación", "ok", salida[-1] if salida else "sincronizada")]
    detalle = (proceso.stdout or proceso.stderr or "").strip().splitlines()
    return [Resultado("Documentación", "falla", detalle[-1] if detalle else "verify_docs falló")]


def verificar_git() -> list[Resultado]:
    """Sin credenciales rastreadas y con el árbol limpio."""
    try:
        listado = subprocess.run(
            ["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, timeout=60
        )
        estado = subprocess.run(
            ["git", "status", "--porcelain"], cwd=RAIZ, capture_output=True, text=True, timeout=60
        )
    except (OSError, subprocess.SubprocessError) as error:
        return [Resultado("Git", "aviso", f"no se pudo consultar: {error}")]

    resultados = []
    archivos = listado.stdout.splitlines()
    bloqueantes = []
    avisables = []
    for archivo in archivos:
        for patron, etiqueta in BLOQUEANTES:
            if patron.search(archivo):
                bloqueantes.append(f"{archivo} ({etiqueta})")
                break
        else:
            for patron, etiqueta in AVISABLES:
                if patron.search(archivo):
                    avisables.append(f"{archivo} ({etiqueta})")
                    break
    if bloqueantes:
        resultados.append(Resultado("Credenciales rastreadas", "falla", ", ".join(bloqueantes[:5])))
    else:
        resultados.append(Resultado("Credenciales rastreadas", "ok", "ninguna en el índice"))
    if avisables:
        resultados.append(
            Resultado(
                "Datos rastreados",
                "aviso",
                ", ".join(avisables[:4])
                + " — retirar con `git rm --cached` cuando el responsable lo decida",
            )
        )
    else:
        resultados.append(Resultado("Datos rastreados", "ok", "bases y respaldos fuera del índice"))

    sucio = [linea for linea in estado.stdout.splitlines() if linea.strip()]
    if sucio:
        resultados.append(
            Resultado(
                "Árbol de trabajo",
                "aviso",
                f"{len(sucio)} archivo(s) con cambios sin confirmar; la etiqueta debe apuntar al commit ya probado",
            )
        )
    else:
        resultados.append(Resultado("Árbol de trabajo", "ok", "limpio"))
    return resultados


def verificar_pruebas() -> list[Resultado]:
    """Opcional: la suite completa, tal como la ejecuta el CI."""
    proceso = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    resumen = [
        linea
        for linea in (proceso.stdout or "").splitlines()
        if "passed" in linea or "failed" in linea
    ]
    if proceso.returncode == 0:
        return [Resultado("Suite de pruebas", "ok", resumen[-1] if resumen else "sin fallos")]
    return [
        Resultado(
            "Suite de pruebas",
            "falla",
            resumen[-1] if resumen else (proceso.stdout or proceso.stderr or "").strip()[-300:],
        )
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Verificación previa a un release")
    parser.add_argument("--tests", action="store_true", help="Ejecutar además la suite completa")
    argumentos = parser.parse_args()

    resultados: list[Resultado] = []
    for comprobacion in (
        verificar_versiones,
        verificar_actualizador,
        verificar_sintaxis,
        verificar_documentacion,
        verificar_git,
    ):
        resultados.extend(comprobacion())
    if argumentos.tests:
        resultados.extend(verificar_pruebas())

    print(f"Verificación de release · versión {_version()}\n")
    for resultado in resultados:
        print(resultado)

    fallas = [resultado for resultado in resultados if resultado.estado == "falla"]
    avisos = [resultado for resultado in resultados if resultado.estado == "aviso"]
    print()
    if fallas:
        print(
            f"RESULTADO: {len(fallas)} falla(s), {len(avisos)} aviso(s). No etiquetar el release."
        )
        return 1
    print(f"RESULTADO: listo para etiquetar ({len(avisos)} aviso(s) para revisar).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

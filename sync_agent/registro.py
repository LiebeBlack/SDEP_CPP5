"""
Registro de entidades sincronizables

Declara, en un solo lugar, **qué** se replica entre los puestos y **cómo** se
identifica cada fila: sin esta tabla el agente no sabría qué tablas tocar, cuál
es la clave natural que permite reconocer el mismo registro creado en dos
equipos distintos, ni qué columnas son locales y no deben viajar.

Quedan fuera del alcance ``usuarios`` (cada puesto administra sus propias
cuentas) y las propias tablas ``sync_*``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeGuard

from sqlalchemy import Table

from src.models import (
    Configuracion,
    Contrato,
    Documento,
    Empleado,
    Estudiante,
    Grado,
    Incidencia,
    Matricula,
    NotaFinal,
    Pago,
    PeriodoAcademico,
)

# Columnas presentes en varias tablas que apuntan a archivos del equipo y no
# al dato: la ruta "C:\\Users\\...\\documents\\x.pdf" de un puesto no significa
# nada en otro, así que se sincroniza el contenido o el metadato, nunca la ruta.
COLUMNAS_LOCALES = {
    "empleados": ("foto_ruta",),
    "documentos": ("ruta_archivo",),
    "incidencias": ("documento_soporte_ruta",),
    "contratos": ("archivo_ruta",),
}

# Columnas de ``documentos``/``incidencias`` cuyo contenido viaja por el
# endpoint de binarios (identificado por hash) y no dentro del payload JSON.
COLUMNAS_BLOB = {
    "documentos": ("contenido_binario",),
    "incidencias": ("documento_soporte_binario",),
}

# Parámetros de configuración que son preferencias del equipo y no deben
# replicarse (tema visual, respaldos automáticos y el propio agente).
CLAVES_CONFIGURACION_LOCALES = (
    "apariencia_modo",
    "backup_enabled",
    "backup_interval_hours",
    "audit_enabled",
)
PREFIJOS_CONFIGURACION_LOCALES = ("sync_",)


@dataclass(frozen=True)
class Entidad:
    """Descripción de una tabla replicada"""

    tabla: str
    # Clase del modelo. Se declara ``Any`` porque el registro trabaja con los
    # atributos que el ORM expone de forma dinámica (``id``, ``__table__``) y
    # cada modelo los tipa distinto: atarlo a un tipo obligaría a repetir aquí
    # los detalles de las cinco entidades.
    clase: Any
    clave_natural: tuple[str, ...] = ()
    # Clave natural de varias columnas que solo puede evaluarse en el equipo
    # receptor, cuando sus valores ya se tradujeron de UUID a ids locales
    # (``periodo_id``, ``estudiante_id``...). En el equipo emisor esos números
    # son otros, así que no sirven para adoptar identidad: para eso está
    # ``clave_natural``, que exige una columna estable entre equipos.
    clave_natural_compuesta: tuple[str, ...] = ()
    borrado_logico: bool = False
    columna_activo: str = "activo"
    columnas_blob: tuple[str, ...] = ()
    columnas_locales: tuple[str, ...] = ()
    descripcion: str = ""


ENTIDADES: dict[str, Entidad] = {
    "empleados": Entidad(
        tabla="empleados",
        clase=Empleado,
        clave_natural=("cedula",),
        borrado_logico=True,
        columnas_locales=COLUMNAS_LOCALES["empleados"],
        descripcion="Fichas del personal",
    ),
    "documentos": Entidad(
        tabla="documentos",
        clase=Documento,
        borrado_logico=True,
        columnas_blob=COLUMNAS_BLOB["documentos"],
        columnas_locales=COLUMNAS_LOCALES["documentos"],
        descripcion="Documentos del legajo (metadatos y archivos por hash)",
    ),
    "incidencias": Entidad(
        tabla="incidencias",
        clase=Incidencia,
        columnas_blob=COLUMNAS_BLOB["incidencias"],
        columnas_locales=COLUMNAS_LOCALES["incidencias"],
        descripcion="Permisos y ausencias",
    ),
    "contratos": Entidad(
        tabla="contratos",
        clase=Contrato,
        clave_natural=("numero",),
        columnas_locales=COLUMNAS_LOCALES["contratos"],
        descripcion="Contratos laborales",
    ),
    "pagos": Entidad(
        tabla="pagos",
        clase=Pago,
        descripcion="Nómina y deducciones",
    ),
    "configuraciones": Entidad(
        tabla="configuraciones",
        clase=Configuracion,
        clave_natural=("clave",),
        descripcion="Parámetros compartidos por la institución",
    ),
    # --- Subdominio académico ------------------------------------------
    # ``tokens_sesion`` queda FUERA a propósito: un token es una credencial
    # local (solo se guarda su hash, pero describe la vigencia y el alcance de
    # una sesión de este equipo) y no tiene sentido replicarla.
    "estudiantes": Entidad(
        tabla="estudiantes",
        clase=Estudiante,
        clave_natural=("cedula",),
        borrado_logico=True,
        descripcion="Legajo de estudiantes",
    ),
    "periodos_academicos": Entidad(
        tabla="periodos_academicos",
        clase=PeriodoAcademico,
        clave_natural=("nombre",),
        descripcion="Años escolares",
    ),
    "grados": Entidad(
        tabla="grados",
        clase=Grado,
        # La unicidad real es (periodo_id, nombre, seccion); se resuelve en el
        # receptor con la clave compuesta de abajo, porque ``periodo_id`` es
        # un id local distinto en cada equipo.
        clave_natural_compuesta=("periodo_id", "nombre", "seccion"),
        descripcion="Grados y secciones",
    ),
    "matriculas": Entidad(
        tabla="matriculas",
        clase=Matricula,
        borrado_logico=True,
        columna_activo="activa",
        descripcion="Matrículas por año escolar",
    ),
    "notas_finales": Entidad(
        tabla="notas_finales",
        clase=NotaFinal,
        clave_natural_compuesta=("estudiante_id", "grado_id", "materia"),
        descripcion="Calificaciones finales",
    ),
}


def entidad(tabla: str) -> Entidad | None:
    """Devuelve la descripción de una tabla replicada, o None si no lo es"""
    return ENTIDADES.get(tabla)


def es_sincronizable(tabla: str | None) -> TypeGuard[str]:
    """
    Indica si una tabla participa en la sincronización

    Se declara ``TypeGuard`` para que quien pregunte por una tabla de la que
    solo conoce su nombre —a menudo ``str | None``— pueda usarla después sin
    volver a comprobar que no es nula.
    """
    return bool(tabla) and tabla in ENTIDADES


def tabla_orm(nombre: str) -> Table | None:
    """Tabla SQLAlchemy de una entidad del registro"""
    descripcion = ENTIDADES.get(nombre)
    if descripcion is None:
        return None
    tabla = getattr(descripcion.clase, "__table__", None)
    return tabla if isinstance(tabla, Table) else None


def columnas(nombre: str) -> dict[str, Any]:
    """Columnas de una entidad indexadas por nombre"""
    tabla = tabla_orm(nombre)
    if tabla is None:
        return {}
    return {columna.name: columna for columna in tabla.columns}


def columna(nombre: str, columna_nombre: str) -> Any:
    """Columna concreta de una entidad (None si no existe)"""
    return columnas(nombre).get(columna_nombre)


def columnas_transportables(nombre: str) -> list[str]:
    """
    Columnas que viajan en el payload

    Incluye las de contenido binario (que se anuncian por hash) y excluye la
    clave primaria —que es local por definición— y las rutas de archivo.
    """
    descripcion = ENTIDADES.get(nombre)
    tabla = tabla_orm(nombre)
    if descripcion is None or tabla is None:
        return []
    excluidas = set(descripcion.columnas_locales) | {"id"}
    return [
        columna.name
        for columna in tabla.columns
        if columna.name not in excluidas and not columna.primary_key
    ]


def claves_foraneas(nombre: str) -> dict[str, str]:
    """
    Columnas que son clave foránea, con la tabla padre a la que apuntan

    Returns:
        dict: columna local -> tabla padre
    """
    tabla = tabla_orm(nombre)
    if tabla is None:
        return {}
    relacion: dict[str, str] = {}
    for columna_fk in tabla.columns:
        if not columna_fk.foreign_keys:
            continue
        destinos = {fk.column.table.name for fk in columna_fk.foreign_keys if fk.column is not None}
        if len(destinos) == 1:
            relacion[columna_fk.name] = destinos.pop()
    return relacion


def columna_clave_natural(nombre: str) -> str | None:
    """Nombre de la clave natural de una entidad (None si no tiene)"""
    descripcion = ENTIDADES.get(nombre)
    if descripcion is None or not descripcion.clave_natural:
        return None
    return descripcion.clave_natural[0]


def configuracion_es_local(clave: str | None) -> bool:
    """Indica si un parámetro de configuración es preferencia del equipo"""
    if not clave:
        return True
    if clave in CLAVES_CONFIGURACION_LOCALES:
        return True
    return any(clave.startswith(prefijo) for prefijo in PREFIJOS_CONFIGURACION_LOCALES)


def tablas_sincronizadas() -> list[str]:
    """Nombres de todas las tablas replicadas"""
    return list(ENTIDADES)


def tablas_con_blobs() -> list[str]:
    """Tablas que alojan contenido binario"""
    return [nombre for nombre, desc in ENTIDADES.items() if desc.columnas_blob]


def columnas_blob(nombre: str) -> tuple[str, ...]:
    """Columnas binarias declaradas por una entidad"""
    descripcion = ENTIDADES.get(nombre)
    return descripcion.columnas_blob if descripcion else ()

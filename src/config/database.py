"""
Database Configuration
Configuración de base de datos SQLite

La ruta de la base de datos se resuelve siempre a partir de
settings.database_path (absoluta y única), evitando la creación de
archivos .db duplicados según el directorio de trabajo.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

from src.models import Base

logger = logging.getLogger(__name__)


# Columnas opcionales añadidas a la tabla empleados en versiones posteriores
# de la aplicación. SQLite no soporta ALTER TABLE ... ADD COLUMN IF NOT EXISTS,
# por eso se consulta PRAGMA table_info antes de agregar cada columna.
MIGRACIONES_EMPLEADOS = {
    "titulo_secundaria": "VARCHAR(100)",
    "institucion_bancaria": "VARCHAR(100)",
    "numero_cuenta": "VARCHAR(50)",
    "tipo_cuenta": "VARCHAR(30)",
    "carnet_discapacidad": "VARCHAR(30)",
    "enfermedades_preexistentes": "TEXT",
    "alergias_medicamentosas": "TEXT",
    "alergias_alimentarias": "TEXT",
    "tipo_contratacion": "VARCHAR(50)",
    "hijos": "TEXT",
}

# Registro de migraciones por tabla: cada entrada describe las columnas que
# versiones posteriores agregaron a una tabla ya existente. Las tablas nuevas
# no se listan aquí porque las crea Base.metadata.create_all en el arranque.
MIGRACIONES: dict[str, dict[str, str]] = {
    "empleados": MIGRACIONES_EMPLEADOS,
    "usuarios": {
        "fecha_cambio_password": "DATETIME",
        "password_historial": "TEXT",
        "bloqueado_hasta": "DATETIME",
    },
    "pagos": {
        "modalidad_calculo": "VARCHAR(20)",
        "base_gravable": "NUMERIC(10, 2)",
        "horas_extra_diurnas": "NUMERIC(10, 2)",
        "horas_extra_nocturnas": "NUMERIC(10, 2)",
        "horas_extra_feriadas": "NUMERIC(10, 2)",
        "aguinaldo": "NUMERIC(10, 2)",
        "bono_vacacional": "NUMERIC(10, 2)",
        "aporte_seguro_patronal": "NUMERIC(10, 2)",
        "aporte_pension_patronal": "NUMERIC(10, 2)",
        "isr_tramo": "VARCHAR(50)",
        # Prorrateo del período (días efectivos y bandera): permiten que
        # editar un pago prorrateado lo recalcule con los mismos días.
        "dias_laborados": "INTEGER",
        "dias_periodo": "INTEGER",
        "prorrateado": "INTEGER",
    },
}

# Tablas y columnas que quedaron sin modelo al retirar los módulos de
# asistencia, horarios y préstamos. Se purgan en el arranque para que una base
# creada por una versión anterior quede coherente con el esquema vigente.
TABLAS_OBSOLETAS: tuple[str, ...] = ("asistencias", "horarios", "prestamos")

# Columnas de ``pagos`` que dependían del módulo de préstamos. SQLite no
# permite DROP COLUMN sobre una columna que participa en una clave foránea,
# así que la tabla se reconstruye a partir del modelo actual.
COLUMNAS_OBSOLETAS_PAGOS: tuple[str, ...] = ("deduccion_prestamo", "prestamo_id")


def _activar_claves_foraneas(engine) -> None:
    """
    Activa la verificación de claves foráneas en cada conexión de SQLite

    SQLite las ignora de forma predeterminada, así que el esquema declaraba
    relaciones que nadie verificaba: un documento, un pago o un contrato
    podían quedar apuntando a un empleado inexistente sin que ninguna
    operación lo notara (registros huérfanos que después aparecían como
    "Desconocido" en la interfaz).

    El PRAGMA es por conexión y no por base de datos, por eso se registra en
    el evento ``connect`` del pool y se comprueba que haya quedado activo.

    Args:
        engine: Motor SQLAlchemy sobre una base SQLite
    """

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            activo = cursor.execute("PRAGMA foreign_keys").fetchone()
        finally:
            cursor.close()
        if not activo or not activo[0]:
            raise RuntimeError(
                "SQLite no activó la verificación de claves foráneas; "
                "se cancela la conexión para proteger la integridad de los datos"
            )


def _columnas_pendientes(engine) -> dict[str, list[tuple[str, str]]]:
    """
    Columnas nuevas que faltan en cada tabla ya existente

    Solo considera tablas presentes en la base: en una base recién creada
    create_all ya dejó el esquema completo y no hay nada que migrar.

    Returns:
        dict: tabla -> lista de pares (columna, tipo) por agregar
    """
    pendientes: dict[str, list[tuple[str, str]]] = {}
    with engine.connect() as conn:
        for tabla, columnas in MIGRACIONES.items():
            existe = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name = :tabla"),
                {"tabla": tabla},
            ).fetchone()
            if not existe:
                continue
            existentes = {
                fila[1] for fila in conn.execute(text(f"PRAGMA table_info({tabla})"))
            }
            faltantes = [
                (columna, tipo)
                for columna, tipo in columnas.items()
                if columna not in existentes
            ]
            if faltantes:
                pendientes[tabla] = faltantes
    return pendientes


def migrar_columnas(engine) -> int:
    """
    Agrega a las tablas existentes las columnas nuevas que falten.

    Se ejecuta en cada arranque (create_tables) para que las bases de datos
    creadas con versiones anteriores ganen los campos nuevos sin perder datos.

    Seguridad: la sentencia ALTER TABLE se construye con interpolación, así
    que columna y tipo se validan contra listas blancas estrictas antes de
    tocar la base (defensa en profundidad aunque la fuente sea interna).

    Returns:
        int: Cantidad de columnas agregadas
    """
    # Lista blanca: nombre de columna y tipos SQL permitidos en la DDL
    patron_columna = re.compile(r"^[a-z_][a-z0-9_]*$")
    patron_tipo = re.compile(
        r"^(VARCHAR\(\d+\)|TEXT|INTEGER|REAL|BLOB|DATETIME|DATE|TIME|"
        r"NUMERIC\(\d+(,\s*\d+)?\))$",
        re.IGNORECASE,
    )
    for tabla, columnas in MIGRACIONES.items():
        if not patron_columna.fullmatch(tabla):
            raise ValueError(f"MIGRACIONES contiene una tabla no válida: {tabla!r}")
        for columna, tipo in columnas.items():
            if not patron_columna.fullmatch(columna) or not patron_tipo.fullmatch(tipo):
                raise ValueError(
                    f"MIGRACIONES contiene una entrada no válida: "
                    f"{tabla}.{columna!r} -> {tipo!r}"
                )
    pendientes = _columnas_pendientes(engine)
    if not pendientes:
        return 0

    # Respaldo automático ANTES de modificar el esquema: si la
    # migración falla a mitad de camino (disco lleno, corte de
    # energía, archivo bloqueado), la base nunca queda en un
    # estado a medio migrar sin recuperación posible.
    try:
        from src.utils.backup_manager import get_backup_manager

        get_backup_manager().create_backup("pre_migracion", compress=True)
    except Exception as e:
        logger.error("Se cancela la migración porque no se pudo crear su backup", exc_info=True)
        raise RuntimeError("No se pudo respaldar la base antes de migrar el esquema") from e

    agregadas = 0
    try:
        with engine.begin() as conn:
            for tabla, faltantes in pendientes.items():
                for columna, tipo in faltantes:
                    conn.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}"))
                    logger.info(f"Migración: columna {tabla}.{columna} agregada")
                    agregadas += 1
    except SQLAlchemyError as e:
        logger.error("No se pudo migrar el esquema de la base de datos", exc_info=True)
        raise RuntimeError("La migración del esquema falló y se revirtió") from e
    return agregadas


def crear_disparadores_inmutabilidad(engine) -> int:
    """
    Crea los disparadores que bloquean editar notas de periodos cerrados

    Se ejecuta en cada arranque (create_tables) después de create_all: las
    tablas nuevas ya existen y las que ya tenían los disparadores no se
    tocan (CREATE TRIGGER IF NOT EXISTS). Si una protección no puede
    aplicarse, el arranque falla explícitamente en vez de dejarla desactivada.

    Returns:
        int: Cantidad de disparadores creados o verificados
    """
    creados = 0
    try:
        with engine.begin() as conn:
            for nombre, sentencia in DISPARADORES_INMUTABILIDAD:
                try:
                    conn.execute(text(sentencia))
                    creados += 1
                except SQLAlchemyError as e:
                    logger.error("No se pudo crear el disparador %s", nombre, exc_info=True)
                    raise RuntimeError(
                        f"No se pudo instalar la protección de inmutabilidad {nombre}"
                    ) from e
    except SQLAlchemyError as e:
        logger.error("No se pudieron crear los disparadores de inmutabilidad", exc_info=True)
        raise RuntimeError("No se pudieron aplicar las protecciones de inmutabilidad") from e
    return creados


def purgar_esquema_obsoleto(engine) -> int:
    """
    Elimina las tablas y columnas que ya no tienen modelo.

    Al retirar los módulos de asistencia, horarios y préstamos sus tablas
    dejaron de declararse en los modelos, y la tabla ``pagos`` perdió las
    columnas del préstamo. Como SQLite no admite ``DROP COLUMN`` sobre una
    columna usada en una clave foránea, ``pagos`` se reconstruye: se renombra
    la tabla original, se crea la nueva con el esquema del modelo vigente, se
    copian las columnas comunes y se elimina la antigua.

    La operación es idempotente: si no queda nada por purgar no toca la base.

    Returns:
        int: Cantidad de cambios aplicados (tablas y columnas eliminadas)
    """
    try:
        with engine.connect() as conn:
            tablas = {
                fila[0]
                for fila in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
    except SQLAlchemyError as e:
        logger.error("No se pudo inspeccionar el esquema para purgarlo", exc_info=True)
        raise RuntimeError("No se pudo inspeccionar el esquema de la base") from e

    obsoletas = [tabla for tabla in TABLAS_OBSOLETAS if tabla in tablas]
    sobrantes: list[str] = []
    if "pagos" in tablas:
        try:
            with engine.connect() as conn:
                existentes = {
                    fila[1] for fila in conn.execute(text("PRAGMA table_info(pagos)"))
                }
        except SQLAlchemyError as e:
            logger.error("No se pudo leer el esquema de pagos", exc_info=True)
            raise RuntimeError("No se pudo leer el esquema de pagos") from e
        sobrantes = [columna for columna in COLUMNAS_OBSOLETAS_PAGOS if columna in existentes]

    if not obsoletas and not sobrantes:
        return 0

    # Respaldo previo: la purga elimina datos de forma irreversible.
    try:
        from src.utils.backup_manager import get_backup_manager

        get_backup_manager().create_backup("pre_purga_esquema", compress=True)
    except Exception as e:
        logger.error("Se cancela la purga porque no se pudo crear su backup", exc_info=True)
        raise RuntimeError("No se pudo respaldar la base antes de purgar el esquema") from e

    cambios = 0
    try:
        with engine.begin() as conn:
            if sobrantes:
                tabla_pagos = Base.metadata.tables["pagos"]
                # Al renombrar una tabla, SQLite conserva sus índices ligados al
                # nuevo nombre pero con los mismos nombres. Si no se eliminan
                # antes de recrear ``pagos``, el CREATE INDEX del modelo choca
                # con los índices heredados y la purga falla.
                indices_heredados = [
                    fila[0]
                    for fila in conn.execute(
                        text(
                            "SELECT name FROM sqlite_master "
                            "WHERE type='index' AND tbl_name='pagos' AND name NOT LIKE 'sqlite_%'"
                        )
                    )
                ]
                conn.execute(text("ALTER TABLE pagos RENAME TO pagos_obsoleto"))
                for indice in indices_heredados:
                    conn.execute(text(f'DROP INDEX IF EXISTS "{indice}"'))
                tabla_pagos.create(bind=conn)
                antiguas = {
                    fila[1]
                    for fila in conn.execute(text("PRAGMA table_info(pagos_obsoleto)"))
                }
                comunes = [
                    columna.name
                    for columna in tabla_pagos.columns
                    if columna.name in antiguas
                ]
                destino = ", ".join(f'"{columna}"' for columna in comunes)
                conn.execute(
                    text(f"INSERT INTO pagos ({destino}) SELECT {destino} FROM pagos_obsoleto")
                )
                conn.execute(text("DROP TABLE pagos_obsoleto"))
                cambios += len(sobrantes)
                logger.info(
                    "Purga: tabla pagos reconstruida sin %s", ", ".join(sobrantes)
                )

            for tabla in obsoletas:
                conn.execute(text(f"DROP TABLE IF EXISTS {tabla}"))
                cambios += 1
                logger.info(f"Purga: tabla {tabla} eliminada")
    except SQLAlchemyError as e:
        logger.error("No se pudo purgar el esquema obsoleto", exc_info=True)
        raise RuntimeError("La purga del esquema falló y se revirtió") from e
    return cambios


# Parámetros de configuración que llegaron después de la primera versión del
# sistema. Se declaran aquí una sola vez y los consumen dos caminos:
#   * _seed_initial_data()         -> instalación nueva: los siembra junto a los históricos
#   * _sincronizar_configuracion() -> instalación existente: agrega solo los que faltan
# Todos son editables desde el módulo de Configuración de la aplicación.
CONFIGURACION_ADICIONAL: tuple[dict[str, Any], ...] = (
    # --- Nómina: modalidad de cálculo y parámetros legales ---
    {
        "clave": "modo_calculo_nomina",
        "valor": "porcentaje",
        "descripcion": (
            "Modalidad de deducciones: 'porcentaje' (cálculo histórico) o "
            "'tramos' (motor con tabla de ISR, techos y recargos)"
        ),
        "tipo_dato": "string",
        "categoria": "nomina",
    },
    {
        "clave": "techo_seguro",
        "valor": "0.0",
        "descripcion": "Techo mensual del aporte al seguro social (0 = sin techo)",
        "tipo_dato": "float",
        "categoria": "nomina",
    },
    {
        "clave": "techo_pension",
        "valor": "0.0",
        "descripcion": "Techo mensual del aporte a pensión (0 = sin techo)",
        "tipo_dato": "float",
        "categoria": "nomina",
    },
    {
        "clave": "porcentaje_seguro_patronal",
        "valor": "9.0",
        "descripcion": "Aporte patronal al seguro social (no se descuenta al empleado)",
        "tipo_dato": "float",
        "categoria": "nomina",
    },
    {
        "clave": "porcentaje_pension_patronal",
        "valor": "7.5",
        "descripcion": "Aporte patronal a pensión (no se descuenta al empleado)",
        "tipo_dato": "float",
        "categoria": "nomina",
    },
    {
        "clave": "isr_tramos",
        "valor": json.dumps(
            [
                {
                    "limite_inferior": 0.0,
                    "limite_superior": 1000.0,
                    "tasa": 0.0,
                    "cuota_fija": 0.0,
                },
                {
                    "limite_inferior": 1000.0,
                    "limite_superior": 2000.0,
                    "tasa": 15.0,
                    "cuota_fija": 0.0,
                },
                {
                    "limite_inferior": 2000.0,
                    "limite_superior": 3000.0,
                    "tasa": 20.0,
                    "cuota_fija": 150.0,
                },
                {
                    "limite_inferior": 3000.0,
                    "limite_superior": None,
                    "tasa": 30.0,
                    "cuota_fija": 350.0,
                },
            ],
            ensure_ascii=False,
        ),
        "descripcion": "Tabla progresiva de ISR por tramos (editables en Configuración)",
        "tipo_dato": "json",
        "categoria": "nomina",
    },
    {
        "clave": "horas_jornada_diaria",
        "valor": "8",
        "descripcion": "Horas de una jornada diaria ordinaria",
        "tipo_dato": "int",
        "categoria": "nomina",
    },
    {
        "clave": "recargo_hora_extra_diurna",
        "valor": "25.0",
        "descripcion": "Recargo porcentual de la hora extra diurna",
        "tipo_dato": "float",
        "categoria": "nomina",
    },
    {
        "clave": "recargo_hora_extra_nocturna",
        "valor": "50.0",
        "descripcion": "Recargo porcentual de la hora extra nocturna o mixta",
        "tipo_dato": "float",
        "categoria": "nomina",
    },
    {
        "clave": "recargo_hora_extra_feriada",
        "valor": "100.0",
        "descripcion": "Recargo porcentual de la hora extra en día feriado",
        "tipo_dato": "float",
        "categoria": "nomina",
    },
    {
        "clave": "dias_aguinaldo",
        "valor": "15",
        "descripcion": "Días de aguinaldo al año",
        "tipo_dato": "int",
        "categoria": "nomina",
    },
    {
        "clave": "dias_bono_vacacional",
        "valor": "15",
        "descripcion": "Días de bono vacacional al año",
        "tipo_dato": "int",
        "categoria": "nomina",
    },
    {
        "clave": "dias_prestaciones_por_ano",
        "valor": "30",
        "descripcion": "Días de prestaciones acumulados por año de servicio",
        "tipo_dato": "int",
        "categoria": "nomina",
    },
    {
        "clave": "dias_preaviso",
        "valor": "30",
        "descripcion": "Días de preaviso considerados en el finiquito",
        "tipo_dato": "int",
        "categoria": "nomina",
    },
    # --- Recursos humanos: contratos y vencimientos ---
    {
        "clave": "umbral_contrato_por_vencer_dias",
        "valor": "30",
        "descripcion": "Días de anticipación para avisar de contratos por vencer",
        "tipo_dato": "int",
        "categoria": "recursos_humanos",
    },
    # --- Académico: escala de calificaciones ---
    {
        "clave": "nota_minima",
        "valor": "0",
        "descripcion": "Calificación mínima de la escala académica (0 = permite cero)",
        "tipo_dato": "float",
        "categoria": "academico",
    },
    {
        "clave": "nota_maxima",
        "valor": "20",
        "descripcion": "Calificación máxima de la escala académica (20 = escala 0-20)",
        "tipo_dato": "float",
        "categoria": "academico",
    },
    {
        "clave": "nota_aprobatoria",
        "valor": "10",
        "descripcion": "Calificación mínima aprobatoria usada en boletines y actas",
        "tipo_dato": "float",
        "categoria": "academico",
    },
    # --- Seguridad: política de credenciales y respaldos ---
    {
        "clave": "password_dias_caducidad",
        "valor": "90",
        "descripcion": "Días de vigencia de una contraseña (0 = sin caducidad)",
        "tipo_dato": "int",
        "categoria": "seguridad",
    },
    {
        "clave": "password_historial",
        "valor": "3",
        "descripcion": "Contraseñas anteriores que no se pueden repetir",
        "tipo_dato": "int",
        "categoria": "seguridad",
    },
    {
        "clave": "password_min_longitud",
        "valor": "6",
        "descripcion": "Longitud mínima de contraseña exigida por el sistema",
        "tipo_dato": "int",
        "categoria": "seguridad",
    },
    {
        "clave": "max_intentos_fallidos",
        "valor": "5",
        "descripcion": "Intentos fallidos antes de bloquear temporalmente la cuenta",
        "tipo_dato": "int",
        "categoria": "seguridad",
    },
    {
        "clave": "bloqueo_minutos",
        "valor": "15",
        "descripcion": "Minutos que dura el bloqueo temporal por intentos fallidos",
        "tipo_dato": "int",
        "categoria": "seguridad",
    },
    {
        "clave": "backup_max_copias",
        "valor": "30",
        "descripcion": "Máximo de respaldos automáticos conservados",
        "tipo_dato": "int",
        "categoria": "seguridad",
    },
)

# Disparadores que protegen la inmutabilidad de las notas finales.
# ----------------------------------------------------------------------
# El cierre de un periodo debe respetarse incluso por SQL directo (scripts de
# corrección, importaciones masivas, herramientas externas), no solo por el
# servicio: estos disparadores abortan cualquier alta, cambio o borrado de una
# nota cuyo grado pertenezca a un periodo cerrado. Se recrean en cada arranque
# (CREATE TRIGGER IF NOT EXISTS) y viajan dentro del archivo SQLite, así que
# también quedan activos al restaurar un respaldo.
DISPARADORES_INMUTABILIDAD: tuple[tuple[str, str], ...] = (
    (
        "trg_notas_finales_insert_bloqueado",
        """
        CREATE TRIGGER IF NOT EXISTS trg_notas_finales_insert_bloqueado
        BEFORE INSERT ON notas_finales
        FOR EACH ROW
        WHEN (
            SELECT p.estado FROM grados g
            JOIN periodos_academicos p ON p.id = g.periodo_id
            WHERE g.id = NEW.grado_id
        ) = 'cerrado'
        BEGIN
            SELECT RAISE(ABORT, 'El periodo academico esta cerrado: no se pueden registrar notas');
        END
        """,
    ),
    (
        "trg_notas_finales_update_bloqueado",
        """
        CREATE TRIGGER IF NOT EXISTS trg_notas_finales_update_bloqueado
        BEFORE UPDATE ON notas_finales
        FOR EACH ROW
        WHEN (
            SELECT p.estado FROM grados g
            JOIN periodos_academicos p ON p.id = g.periodo_id
            WHERE g.id = OLD.grado_id
        ) = 'cerrado'
        OR (
            SELECT p.estado FROM grados g
            JOIN periodos_academicos p ON p.id = g.periodo_id
            WHERE g.id = NEW.grado_id
        ) = 'cerrado'
        BEGIN
            SELECT RAISE(ABORT, 'El periodo academico esta cerrado: la nota no puede modificarse');
        END
        """,
    ),
    (
        "trg_notas_finales_delete_bloqueado",
        """
        CREATE TRIGGER IF NOT EXISTS trg_notas_finales_delete_bloqueado
        BEFORE DELETE ON notas_finales
        FOR EACH ROW
        WHEN (
            SELECT p.estado FROM grados g
            JOIN periodos_academicos p ON p.id = g.periodo_id
            WHERE g.id = OLD.grado_id
        ) = 'cerrado'
        BEGIN
            SELECT RAISE(ABORT, 'El periodo academico esta cerrado: la nota no puede eliminarse');
        END
        """,
    ),
)


# Claves de configuración que quedaron sin consumidor al retirar los módulos de
# asistencia, horarios y préstamos. Se eliminan de las instalaciones existentes
# en cada arranque (ver _purgar_configuracion_obsoleta).
CONFIGURACION_OBSOLETA: tuple[str, ...] = (
    "max_cuotas_prestamo",
    "max_porcentaje_cuota_prestamo",
    "hora_entrada_default",
    "hora_salida_default",
    "tolerancia_asistencia_minutos",
    "umbral_ausentismo_alerta",
    "dias_alerta_documento",
    "max_horas_extra_semana",
    "dias_alerta_pago_antiguo",
    "dias_descanso",
    "feriados",
)


class DatabaseConfig:
    """Configuración de la base de datos SQLite"""

    def __init__(self):
        from src.config import settings

        # Ruta absoluta y única de la base de datos
        self.database_path = settings.database_path
        self.database_url = settings.database_url
        self.echo = settings.debug

        self._ensure_data_directory()

        self.engine = self._create_engine()
        self.SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.SessionLocal = scoped_session(self.SessionFactory)

        # El esquema del agente de sincronización se crea una sola vez por
        # proceso y la captura de cambios se engancha únicamente si este
        # puesto tiene el agente configurado (ver crear_tables).
        self._sync_esquema_listo = False
        self._sync_captura_activa = False

        logger.info(f"Base de datos configurada: {self.database_path}")

    def _safe_log_error(self, error: Exception, context: dict | None = None):
        try:
            from src.utils.audit_logger import get_audit_logger

            audit = get_audit_logger()
            if audit:
                audit.log_error(error, context=context)
        except Exception:
            logger.warning(
                "%s: operación auxiliar falló (se continúa)", "_safe_log_error", exc_info=True
            )

    def _safe_log_event(self, event_type, details: dict | None = None):
        try:
            from src.utils.audit_logger import get_audit_logger

            audit = get_audit_logger()
            if audit:
                audit.log_system_event(event_type, details=details)
        except Exception:
            logger.warning(
                "%s: operación auxiliar falló (se continúa)", "_safe_log_event", exc_info=True
            )

    def _ensure_data_directory(self):
        db_path = Path(self.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

    def _create_engine(self):
        try:
            # Agrupar las conexiones (pool) evita abrir y cerrar el archivo
            # SQLite en cada operación: al guardar un lote grande de notas a
            # fin de año la diferencia es de decenas de milisegundos por fila
            # a microsegundos. El tamaño se declara explícito para que no
            # dependa del valor por defecto del dialecto. SQLite en memoria no
            # admite el pool: cada conexión abriría una base de datos vacía.
            opciones: dict[str, Any] = {
                "connect_args": {"check_same_thread": False, "timeout": 30},
                "echo": self.echo,
                "pool_pre_ping": True,
            }
            if ":memory:" not in self.database_url:
                opciones.update(
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                )
            engine = create_engine(self.database_url, **opciones)
            _activar_claves_foraneas(engine)
            logger.info("Engine de base de datos creado exitosamente")
            return engine
        except Exception as e:
            logger.error(f"Error creando engine de base de datos: {e}")
            self._safe_log_error(e, context={"operation": "create_engine"})
            raise

    def create_tables(self):
        """Crea todas las tablas que aún no existan y migra columnas nuevas"""
        try:
            Base.metadata.create_all(bind=self.engine)
            migrar_columnas(self.engine)
            crear_disparadores_inmutabilidad(self.engine)
            purgar_esquema_obsoleto(self.engine)
            if self.sincronizacion_configurada():
                if not self.preparar_sincronizacion():
                    raise RuntimeError(
                        "La sincronización está habilitada, pero no se pudo preparar su esquema"
                    )
                if not self.activar_captura_sincronizacion():
                    raise RuntimeError(
                        "La sincronización está habilitada, pero no se pudo activar la captura"
                    )
            logger.info("Tablas de base de datos verificadas exitosamente")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error creando tablas: {e}")
            self._safe_log_error(e, context={"operation": "create_tables"})
            raise

    # ------------------------------------------------------------------
    # Agente de sincronización
    # ------------------------------------------------------------------
    def preparar_sincronizacion(self) -> bool:
        """
        Crea en la base local las tablas del agente de sincronización

        Son tablas propias del agente (identidad global de las filas, journal
        de operaciones, marcas por campo, conflictos, binarios en tránsito),
        independientes del esquema de la aplicación. La operación es idempotente
        y nunca impide el arranque: si el paquete del agente no está disponible,
        el sistema sigue funcionando con normalidad, solo sin replicar datos.
        """
        if self._sync_esquema_listo:
            return True
        try:
            from sync_agent.esquema import asegurar_esquema

            asegurar_esquema(self.engine)
            self._sync_esquema_listo = True
            return True
        except Exception as e:
            logger.warning(f"No se pudo preparar el esquema de sincronización: {e}")
            return False

    def activar_captura_sincronizacion(self) -> bool:
        """
        Engancha la captura de cambios del ORM (una sola vez por proceso)

        A partir de este momento cada alta, edición o borrado de los datos
        replicables deja su operación en el journal del agente **dentro de la
        misma transacción** que el dato: si la operación se deshace, la
        operación tampoco se anuncia al resto de la red. Se engancha solo
        cuando el puesto tiene el agente configurado, para no hacer trabajar
        de más a las instalaciones que no sincronizan.
        """
        if self._sync_captura_activa:
            return True
        try:
            from sync_agent.captura import instalar

            instalar(self.SessionFactory, self.engine)
            self._sync_captura_activa = True
            logger.info("Captura de cambios para sincronización activada")
            return True
        except Exception as e:
            logger.warning(f"No se pudo activar la captura de sincronización: {e}")
            return False

    @staticmethod
    def sincronizacion_configurada() -> bool:
        """Indica si este equipo tiene el agente de sincronización habilitado"""
        try:
            from sync_agent.config import cargar

            return bool(cargar().activo)
        except Exception:
            return False

    def drop_tables(self):
        """Elimina todas las tablas de la base de datos con backup previo"""
        try:
            try:
                from src.utils.backup_manager import get_backup_manager

                backup_mgr = get_backup_manager()
                backup_info = backup_mgr.create_backup("pre_drop_tables", compress=True)
                logger.info(f"Backup creado antes de eliminar tablas: {backup_info.get('name')}")
            except Exception as e:
                logger.warning(f"No se pudo crear backup antes de eliminar tablas: {e}")

            Base.metadata.drop_all(bind=self.engine)
            logger.warning("Tablas de base de datos eliminadas")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error eliminando tablas: {e}")
            self._safe_log_error(e, context={"operation": "drop_tables"})
            raise

    def get_session(self):
        """
        Retorna una sesión de base de datos ligada al registry scoped

        La misma sesión se reutiliza dentro del hilo hasta que se cierra
        con close_session(). Es la opción por defecto para operaciones
        puntuales (auditoría, configuración, etc.).
        """
        try:
            return self.SessionLocal()
        except Exception as e:
            logger.error(f"Error obteniendo sesión de base de datos: {e}")
            self._safe_log_error(e, context={"operation": "get_session"})
            raise

    def new_session(self):
        """
        Retorna una sesión independiente y no gestionada por el registry

        Las sesiones scoped se cierran en cascada (SessionLocal.remove),
        invalidando cualquier objeto que estuvieran cargando. Una ventana
        de larga duración (MainWindow) necesita una sesión propia que
        sobreviva a esas operaciones.
        """
        return self.SessionFactory()

    def _es_sesion_scoped(self, session) -> bool:
        """
        Indica si la sesión es la del registry scoped del hilo actual

        Se consulta el registry sin crear ninguna sesión (``has`` antes de
        pedir la instancia) para distinguir la sesión compartida por hilo
        de ``get_session`` de una sesión independiente creada con
        ``new_session``.
        """
        try:
            registro = self.SessionLocal.registry
            return bool(registro.has() and registro() is session)
        except Exception:
            logger.debug("No se pudo consultar el registry de sesiones", exc_info=True)
            return False

    def close_session(self, session):
        """
        Cierra una sesión de base de datos de forma segura

        El registry scoped solo se libera cuando la sesión cerrada ES la
        sesión scoped del hilo. Al cerrar una sesión independiente
        (``new_session``, como la de la ventana principal) el ``remove()``
        invalidaba la sesión scoped que otro consumidor del mismo hilo
        pudiera estar usando a mitad de una operación, y la aplicación
        fallaba con "session is in 'closed' state".
        """
        if session is not None:
            try:
                session.close()
            except Exception as e:
                logger.warning(f"Error cerrando sesión de base de datos: {e}")
        if self._es_sesion_scoped(session):
            try:
                self.SessionLocal.remove()
            except Exception as e:
                logger.warning(f"Error removiendo sesión: {e}")

    def dispose(self):
        """Libera TODAS las conexiones del pool y el registry de sesiones.

        Se invoca al cerrar la aplicación para no dejar conexiones a la
        base de datos ni sesiones scoped pendientes (anti-fugas).
        """
        try:
            self.SessionLocal.remove()
        except Exception as e:
            logger.warning(f"Error removiendo sesiones al liberar: {e}")
        try:
            self.engine.dispose()
        except Exception as e:
            logger.warning(f"Error liberando el pool de conexiones: {e}")

    def init_db(self):
        """Inicializa la base de datos: tablas, verificación y datos semilla"""
        try:
            logger.info("Inicializando base de datos...")
            db_file = Path(self.database_path)
            base_de_datos_nueva = not db_file.exists() or db_file.stat().st_size == 0
            self._check_integrity()
            self.create_tables()
            self._check_integrity()
            self._seed_initial_data()
            self._sincronizar_configuracion()
            self._purgar_configuracion_obsoleta()
            self._seed_initial_user()

            # Crear el backup inicial después de crear tablas y datos semilla.
            if base_de_datos_nueva:
                try:
                    from src.utils.backup_manager import get_backup_manager

                    get_backup_manager().create_backup("initial_setup", compress=True)
                except Exception as e:
                    logger.warning(f"No se pudo crear backup inicial: {e}")

            logger.info("Base de datos inicializada exitosamente")
            try:
                from src.utils.audit_logger import AuditEventType

                self._safe_log_event(AuditEventType.SYSTEM_START, details={"operation": "init_db"})
            except Exception:
                logger.warning(
                    "%s: operación auxiliar falló (se continúa)", "init_db", exc_info=True
                )
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}")
            self._safe_log_error(e, context={"operation": "init_db"})
            raise

    def _check_integrity(self):
        """Verifica toda la estructura SQLite y bloquea el arranque si está dañada."""
        db_path = Path(self.database_path)
        if not db_path.exists():
            return
        try:
            with self.engine.connect() as conn:
                resultados = [fila[0] for fila in conn.execute(text("PRAGMA quick_check"))]
                claves_huerfanas = conn.execute(text("PRAGMA foreign_key_check")).fetchmany(20)
            if not resultados or any(resultado != "ok" for resultado in resultados):
                detalle = "; ".join(str(resultado) for resultado in resultados) or "sin resultado"
                logger.critical("La base de datos no superó quick_check: %s", detalle)
                raise RuntimeError(
                    "La base de datos presenta daños de integridad. "
                    "No se iniciará la aplicación para evitar modificar datos dañados."
                )
            if claves_huerfanas:
                detalle_fk = "; ".join(
                    f"tabla={fila[0]}, fila={fila[1]}, padre={fila[2]}, fk={fila[3]}"
                    for fila in claves_huerfanas
                )
                logger.critical("La base contiene referencias huérfanas: %s", detalle_fk)
                raise RuntimeError(
                    "La base de datos contiene relaciones huérfanas. "
                    "No se iniciará la aplicación hasta corregir los datos."
                )
            logger.info("Integridad de base de datos verificada (ok)")
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            logger.critical("No se pudo comprobar la integridad de la base de datos", exc_info=True)
            raise RuntimeError("No se pudo verificar la integridad de la base de datos") from e

    def _seed_initial_data(self):
        """Inserta la configuración inicial del sistema si no existe"""
        from src.models.configuracion import Configuracion

        session = self.get_session()
        try:
            if session.query(Configuracion).first() is not None:
                return

            configuraciones = [
                Configuracion(
                    clave="nombre_institucion",
                    valor="Institución Educativa",
                    descripcion="Nombre de la institución educativa",
                    tipo_dato="string",
                    categoria="general",
                ),
                Configuracion(
                    clave="ruc",
                    valor="",
                    descripcion="RUC de la institución",
                    tipo_dato="string",
                    categoria="general",
                ),
                Configuracion(
                    clave="direccion",
                    valor="",
                    descripcion="Dirección de la institución",
                    tipo_dato="string",
                    categoria="general",
                ),
                Configuracion(
                    clave="telefono",
                    valor="",
                    descripcion="Teléfono de la institución",
                    tipo_dato="string",
                    categoria="general",
                ),
                Configuracion(
                    clave="email",
                    valor="",
                    descripcion="Email de la institución",
                    tipo_dato="string",
                    categoria="general",
                ),
                Configuracion(
                    clave="porcentaje_seguro",
                    valor="4.5",
                    descripcion="Porcentaje de deducción por seguro social",
                    tipo_dato="float",
                    categoria="nomina",
                ),
                Configuracion(
                    clave="porcentaje_pension",
                    valor="5.0",
                    descripcion="Porcentaje de deducción por pensión",
                    tipo_dato="float",
                    categoria="nomina",
                ),
                Configuracion(
                    clave="porcentaje_impuesto",
                    valor="0.0",
                    descripcion="Porcentaje de deducción por impuesto",
                    tipo_dato="float",
                    categoria="nomina",
                ),
                Configuracion(
                    clave="salario_minimo",
                    valor="130.0",
                    descripcion="Salario mínimo mensual",
                    tipo_dato="float",
                    categoria="nomina",
                ),
                Configuracion(
                    clave="dias_vacaciones_anual",
                    valor="15",
                    descripcion="Días de vacaciones anuales",
                    tipo_dato="int",
                    categoria="recursos_humanos",
                ),
                Configuracion(
                    clave="horas_laborales_semana",
                    valor="40",
                    descripcion="Horas laborales semanales",
                    tipo_dato="int",
                    categoria="recursos_humanos",
                ),
                Configuracion(
                    clave="backup_enabled",
                    valor="true",
                    descripcion="Habilitar backups automáticos",
                    tipo_dato="bool",
                    categoria="seguridad",
                ),
                Configuracion(
                    clave="backup_interval_hours",
                    valor="24",
                    descripcion="Intervalo de backups en horas",
                    tipo_dato="int",
                    categoria="seguridad",
                ),
                Configuracion(
                    clave="audit_enabled",
                    valor="true",
                    descripcion="Habilitar auditoría de eventos",
                    tipo_dato="bool",
                    categoria="seguridad",
                ),
            ]
            configuraciones.extend(
                Configuracion(**datos) for datos in CONFIGURACION_ADICIONAL
            )
            session.add_all(configuraciones)
            session.commit()
            logger.info(f"Configuraciones iniciales insertadas: {len(configuraciones)}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error insertando configuraciones iniciales: {e}")
            self._safe_log_error(e, context={"operation": "seed_initial_data"})
            raise
        finally:
            self.close_session(session)

    def _sincronizar_configuracion(self) -> int:
        """
        Agrega los parámetros de configuración nuevos que falten

        Nunca modifica ni elimina valores existentes: una instalación ya
        configurada conserva su configuración y solo gana los parámetros que
        las versiones nuevas necesitan para funcionar.

        Returns:
            int: Cantidad de parámetros agregados
        """
        from src.models.configuracion import Configuracion

        session = self.get_session()
        try:
            existentes = {fila.clave for fila in session.query(Configuracion).all()}
            nuevas = [
                Configuracion(**datos)
                for datos in CONFIGURACION_ADICIONAL
                if datos["clave"] not in existentes
            ]
            if not nuevas:
                return 0
            session.add_all(nuevas)
            session.commit()
            logger.info(f"Parámetros de configuración agregados: {len(nuevas)}")
            return len(nuevas)
        except SQLAlchemyError as e:
            session.rollback()
            logger.error("No se pudieron agregar los parámetros de configuración", exc_info=True)
            raise RuntimeError("No se pudo completar la actualización de configuración") from e
        finally:
            self.close_session(session)

    def _purgar_configuracion_obsoleta(self) -> int:
        """
        Elimina los parámetros de configuración que ya no se usan

        Los borra de la base y de la copia local en config.json: si la clave
        quedara en el espejo, ``obtener_valor`` la devolvería como si siguiera
        vigente aunque ya nadie la lea.

        Returns:
            int: Cantidad de parámetros eliminados
        """
        from src.models.configuracion import Configuracion

        session = self.get_session()
        eliminados = 0
        try:
            obsoletas = (
                session.query(Configuracion)
                .filter(Configuracion.clave.in_(CONFIGURACION_OBSOLETA))
                .all()
            )
            for configuracion in obsoletas:
                session.delete(configuracion)
                eliminados += 1
            if eliminados:
                session.commit()
                logger.info(f"Parámetros obsoletos eliminados: {eliminados}")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error("No se pudieron eliminar los parámetros obsoletos", exc_info=True)
            raise RuntimeError("No se pudo completar la limpieza de configuración") from e
        finally:
            self.close_session(session)

        from src.config import settings

        for clave in CONFIGURACION_OBSOLETA:
            try:
                settings.delete_config_value(clave)
            except Exception:
                logger.warning(
                    "%s: operación auxiliar falló (se continúa)",
                    "_purgar_configuracion_obsoleta",
                    exc_info=True,
                )
        return eliminados

    def _seed_initial_user(self):
        """Crea el usuario administrador por defecto en el primer arranque"""
        session = self.get_session()
        try:
            from src.models import Usuario

            if session.query(Usuario).count() > 0:
                return
            from src.services.auth_service import ensure_default_admin

            ensure_default_admin(session)
        except Exception as e:
            session.rollback()
            logger.exception("No se pudo crear el usuario inicial")
            raise RuntimeError("No se pudo inicializar el acceso de administrador") from e
        finally:
            self.close_session(session)

    def create_backup(self, backup_name: str | None = None) -> dict:
        """Crea un backup de la base de datos"""
        try:
            from src.utils.backup_manager import get_backup_manager

            resultado: dict[str, Any] = get_backup_manager().create_backup(backup_name)
            return resultado
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            self._safe_log_error(e, context={"operation": "create_backup"})
            raise

    def restore_backup(self, backup_name: str) -> bool:
        """Restaura un backup de la base de datos"""
        try:
            from src.utils.backup_manager import get_backup_manager

            result = get_backup_manager().restore_backup(backup_name)
            try:
                from src.utils.audit_logger import AuditEventType

                self._safe_log_event(
                    AuditEventType.SYSTEM_RESTORE, details={"backup_name": backup_name}
                )
            except Exception:
                logger.warning(
                    "%s: operación auxiliar falló (se continúa)", "restore_backup", exc_info=True
                )
            return bool(result)
        except Exception as e:
            logger.error(f"Error restaurando backup: {e}")
            self._safe_log_error(
                e, context={"operation": "restore_backup", "backup_name": backup_name}
            )
            raise

    def get_backup_status(self) -> dict:
        """Obtiene el estado del sistema de backups"""
        try:
            from src.utils.backup_manager import get_backup_manager

            backup_mgr = get_backup_manager()
            backups = backup_mgr.list_backups()
            # Leer la preferencia real de configuración; ante cualquier
            # error se conserva el valor por defecto (habilitado).
            try:
                from src.repositories import ConfiguracionRepository

                session = self.get_session()
                try:
                    habilitado = ConfiguracionRepository(session).get_valor("backup_enabled", True)
                finally:
                    self.close_session(session)
            except Exception:
                habilitado = True
            return {
                "total_backups": len(backups),
                "latest_backup": backups[0] if backups else None,
                "backup_enabled": bool(habilitado),
                "database_path": str(Path(self.database_path).absolute()),
                "backup_directory": str(backup_mgr.backup_dir.absolute()),
            }
        except Exception as e:
            logger.error(f"Error obteniendo estado de backups: {e}")
            return {"error": str(e)}


# Instancia global de configuración de base de datos
db_config = DatabaseConfig()


def get_db():
    """Retorna una sesión de base de datos (para dependency injection)"""
    session = db_config.get_session()
    try:
        yield session
    finally:
        db_config.close_session(session)

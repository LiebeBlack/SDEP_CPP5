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

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError

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
        "deduccion_prestamo": "NUMERIC(10, 2)",
        "aguinaldo": "NUMERIC(10, 2)",
        "bono_vacacional": "NUMERIC(10, 2)",
        "aporte_seguro_patronal": "NUMERIC(10, 2)",
        "aporte_pension_patronal": "NUMERIC(10, 2)",
        "isr_tramo": "VARCHAR(50)",
        "prestamo_id": "INTEGER",
    },
}


def _columnas_pendientes(engine) -> dict[str, list[tuple[str, str]]]:
    """
    Columnas nuevas que faltan en cada tabla ya existente

    Solo considera tablas presentes en la base: en una base recién creada
    create_all ya dejó el esquema completo y no hay nada que migrar.

    Returns:
        dict: tabla -> lista de pares (columna, tipo) por agregar
    """
    pendientes: dict[str, list[tuple[str, str]]] = {}
    try:
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
    except SQLAlchemyError as e:
        logger.warning(f"No se pudo leer el esquema actual de la base de datos: {e}")
        return {}
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
        logger.warning(f"No se pudo crear backup antes de migrar el esquema: {e}")

    agregadas = 0
    try:
        with engine.begin() as conn:
            for tabla, faltantes in pendientes.items():
                for columna, tipo in faltantes:
                    conn.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}"))
                    logger.info(f"Migración: columna {tabla}.{columna} agregada")
                    agregadas += 1
    except SQLAlchemyError as e:
        logger.warning(f"No se pudo migrar el esquema de la base de datos: {e}")
        return 0
    return agregadas


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
    {
        "clave": "max_cuotas_prestamo",
        "valor": "24",
        "descripcion": "Máximo de cuotas permitidas en un préstamo",
        "tipo_dato": "int",
        "categoria": "nomina",
    },
    {
        "clave": "max_porcentaje_cuota_prestamo",
        "valor": "30.0",
        "descripcion": "Tope porcentual del neto que puede descontarse por préstamos",
        "tipo_dato": "float",
        "categoria": "nomina",
    },
    # --- Recursos humanos: asistencia, contratos y vencimientos ---
    {
        "clave": "hora_entrada_default",
        "valor": "07:00",
        "descripcion": "Hora de entrada por defecto al crear horarios",
        "tipo_dato": "string",
        "categoria": "recursos_humanos",
    },
    {
        "clave": "hora_salida_default",
        "valor": "15:00",
        "descripcion": "Hora de salida por defecto al crear horarios",
        "tipo_dato": "string",
        "categoria": "recursos_humanos",
    },
    {
        "clave": "tolerancia_asistencia_minutos",
        "valor": "10",
        "descripcion": "Minutos de tolerancia por defecto antes de marcar tardanza",
        "tipo_dato": "int",
        "categoria": "recursos_humanos",
    },
    {
        "clave": "umbral_ausentismo_alerta",
        "valor": "10.0",
        "descripcion": "Porcentaje de ausentismo a partir del cual se genera una alerta",
        "tipo_dato": "float",
        "categoria": "recursos_humanos",
    },
    {
        "clave": "umbral_contrato_por_vencer_dias",
        "valor": "30",
        "descripcion": "Días de anticipación para avisar de contratos por vencer",
        "tipo_dato": "int",
        "categoria": "recursos_humanos",
    },
    {
        "clave": "dias_alerta_documento",
        "valor": "30",
        "descripcion": "Días de anticipación para avisar de documentos por vencer",
        "tipo_dato": "int",
        "categoria": "recursos_humanos",
    },
    {
        "clave": "max_horas_extra_semana",
        "valor": "10",
        "descripcion": "Horas extra semanales a partir de las cuales se genera una alerta",
        "tipo_dato": "int",
        "categoria": "recursos_humanos",
    },
    {
        "clave": "dias_descanso",
        "valor": "[5, 6]",
        "descripcion": "Días de descanso semanal (0 = lunes ... 6 = domingo)",
        "tipo_dato": "json",
        "categoria": "recursos_humanos",
    },
    {
        "clave": "feriados",
        "valor": "[]",
        "descripcion": "Fechas feriadas en formato AAAA-MM-DD usadas al calcular horas extra",
        "tipo_dato": "json",
        "categoria": "recursos_humanos",
    },
    {
        "clave": "dias_alerta_pago_antiguo",
        "valor": "30",
        "descripcion": "Días tras los cuales un pago pendiente genera una alerta",
        "tipo_dato": "int",
        "categoria": "nomina",
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
            engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False, "timeout": 30},
                echo=self.echo,
                pool_pre_ping=True,
            )
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
            logger.info("Tablas de base de datos verificadas exitosamente")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error creando tablas: {e}")
            self._safe_log_error(e, context={"operation": "create_tables"})
            raise

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

    def close_session(self, session):
        """Cierra una sesión de base de datos de forma segura"""
        if session is not None:
            try:
                session.close()
            except Exception as e:
                logger.warning(f"Error cerrando sesión de base de datos: {e}")
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
            self.create_tables()
            self._check_integrity()
            self._seed_initial_data()
            self._sincronizar_configuracion()
            self._seed_initial_user()

            # Crear backup inicial una sola vez (si la BD es nueva)
            from pathlib import Path as _Path

            db_file = _Path(self.database_path)
            if not db_file.exists() or db_file.stat().st_size == 0:
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
        """Ejecuta PRAGMA quick_check y registra advertencias sin abortar"""
        db_path = Path(self.database_path)
        if not db_path.exists():
            return
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("PRAGMA quick_check")).scalar()
            if result and result != "ok":
                logger.warning(f"Integridad de base de datos: {result}")
            else:
                logger.info("Integridad de base de datos verificada (ok)")
        except Exception as e:
            logger.warning(f"No se pudo verificar la integridad de la base de datos: {e}")

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
            logger.warning(f"No se pudieron agregar los parámetros de configuración: {e}")
            return 0
        finally:
            self.close_session(session)

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
            logger.warning(f"No se pudo crear el usuario inicial: {e}")
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

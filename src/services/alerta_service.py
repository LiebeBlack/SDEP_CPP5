"""
Alerta Service
Servicio de alertas accionables del sistema

Reúne en un solo lugar todo lo que requiere la atención del usuario:
documentos vencidos o por vencer, incidencias pendientes de aprobación,
contratos por expirar, jornadas sin registrar, préstamos por vencer,
respaldos atrasados, credenciales caducadas y parámetros de nómina
inconsistentes.

Cada alerta indica su severidad, cuántos casos abarca y a qué módulo
llevar al usuario para resolverla, de modo que la interfaz pueda actuar
en un clic.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import SeveridadAlerta
from src.nomina import validar_parametros
from src.repositories import (
    ConfiguracionRepository,
    ContratoRepository,
    DocumentoRepository,
    IncidenciaRepository,
    PagoRepository,
    PrestamoRepository,
    UsuarioRepository,
)

logger = logging.getLogger(__name__)

DIAS_DOCUMENTO_DEFECTO = 30
DIAS_CONTRATO_DEFECTO = 30
DIAS_PAGO_ANTIGUO_DEFECTO = 30
DIAS_RESPALDO_DEFECTO = 24


@dataclass(frozen=True, slots=True)
class Alerta:
    """Alerta accionable mostrada al usuario"""

    clave: str
    titulo: str
    descripcion: str
    severidad: str = SeveridadAlerta.INFO.value
    categoria: str = "general"
    cantidad: int = 0
    modulo: str | None = None
    detalles: tuple[str, ...] = field(default_factory=tuple)

    @property
    def es_critica(self) -> bool:
        """Indica si la alerta requiere atención inmediata"""
        return self.severidad == SeveridadAlerta.CRITICA.value

    def to_dict(self) -> dict:
        """Representación de la alerta para la interfaz"""
        return {
            "clave": self.clave,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "severidad": self.severidad,
            "categoria": self.categoria,
            "cantidad": self.cantidad,
            "modulo": self.modulo,
            "detalles": list(self.detalles),
            "es_critica": self.es_critica,
        }


class AlertaService:
    """Generador de alertas del sistema"""

    def __init__(self, session: Session):
        self.session = session
        self.config_repository = ConfiguracionRepository(session)
        self.documento_repository = DocumentoRepository(session)
        self.incidencia_repository = IncidenciaRepository(session)
        self.contrato_repository = ContratoRepository(session)
        self.prestamo_repository = PrestamoRepository(session)
        self.pago_repository = PagoRepository(session)
        self.usuario_repository = UsuarioRepository(session)

    # ------------------------------------------------------------------
    # Lectura de parámetros
    # ------------------------------------------------------------------
    def _valor(self, clave: str, por_defecto):
        """Lee un parámetro de configuración sin romperse si falta"""
        try:
            return self.config_repository.get_valor(clave, por_defecto)
        except (SQLAlchemyError, ValueError, TypeError):
            logger.debug("No se pudo leer la configuración %s", clave, exc_info=True)
            return por_defecto

    def _entero(self, clave: str, por_defecto: int) -> int:
        """Lee un parámetro entero de configuración"""
        try:
            return int(self._valor(clave, por_defecto))
        except (TypeError, ValueError):
            return por_defecto

    # ------------------------------------------------------------------
    # Generación de alertas
    # ------------------------------------------------------------------
    def generar_alertas(self, usuario=None) -> list[Alerta]:
        """
        Genera todas las alertas vigentes ordenadas por severidad

        Args:
            usuario: Usuario en sesión, para las alertas de credenciales

        Returns:
            list[Alerta]: Alertas de mayor a menor severidad.
        """
        alertas: list[Alerta] = []
        constructores = (
            self.alertas_documentos,
            self.alertas_contratos,
            self.alertas_incidencias,
            self.alertas_asistencia,
            self.alertas_prestamos,
            self.alertas_nomina,
            self.alertas_respaldo,
            lambda: self.alertas_credenciales(usuario),
        )
        for constructor in constructores:
            try:
                alertas.extend(constructor())
            except (SQLAlchemyError, ValueError, TypeError):
                logger.warning(
                    "No se pudieron generar algunas alertas del sistema", exc_info=True
                )
        return self.ordenar(alertas)

    @staticmethod
    def ordenar(alertas: list[Alerta]) -> list[Alerta]:
        """Ordena las alertas por severidad y luego por cantidad"""
        prioridad = {
            SeveridadAlerta.CRITICA.value: 0,
            SeveridadAlerta.ADVERTENCIA.value: 1,
            SeveridadAlerta.INFO.value: 2,
        }
        return sorted(
            alertas,
            key=lambda alerta: (prioridad.get(alerta.severidad, 3), -alerta.cantidad),
        )

    def alertas_documentos(self) -> list[Alerta]:
        """Documentos vencidos y próximos a vencer"""
        alertas: list[Alerta] = []
        vencidos = self.documento_repository.get_vencidos()
        if vencidos:
            alertas.append(
                Alerta(
                    clave="documentos_vencidos",
                    titulo="Documentos vencidos",
                    descripcion=(
                        f"{len(vencidos)} documento(s) ya pasaron su fecha de vencimiento"
                    ),
                    severidad=SeveridadAlerta.CRITICA.value,
                    categoria="documentos",
                    cantidad=len(vencidos),
                    modulo="documentos",
                    detalles=tuple(
                        f"{getattr(documento, 'nombre', 'Documento')} "
                        f"({getattr(documento, 'fecha_vencimiento', '')})"
                        for documento in vencidos[:5]
                    ),
                )
            )

        dias = self._entero("dias_alerta_documento", DIAS_DOCUMENTO_DEFECTO)
        por_vencer = self.documento_repository.get_por_vencer(dias)
        if por_vencer:
            alertas.append(
                Alerta(
                    clave="documentos_por_vencer",
                    titulo="Documentos por vencer",
                    descripcion=(
                        f"{len(por_vencer)} documento(s) vencen en los próximos {dias} días"
                    ),
                    severidad=SeveridadAlerta.ADVERTENCIA.value,
                    categoria="documentos",
                    cantidad=len(por_vencer),
                    modulo="documentos",
                    detalles=tuple(
                        f"{getattr(documento, 'nombre', 'Documento')} "
                        f"({getattr(documento, 'fecha_vencimiento', '')})"
                        for documento in por_vencer[:5]
                    ),
                )
            )
        return alertas

    def alertas_contratos(self) -> list[Alerta]:
        """Contratos vencidos y próximos a vencer"""
        alertas: list[Alerta] = []
        dias = self._entero("umbral_contrato_por_vencer_dias", DIAS_CONTRATO_DEFECTO)

        vencidos = self.contrato_repository.get_vencidos()
        if vencidos:
            alertas.append(
                Alerta(
                    clave="contratos_vencidos",
                    titulo="Contratos vencidos sin cerrar",
                    descripcion=(
                        f"{len(vencidos)} contrato(s) superaron su fecha de fin y siguen "
                        "sin renovarse ni terminarse"
                    ),
                    severidad=SeveridadAlerta.CRITICA.value,
                    categoria="contratos",
                    cantidad=len(vencidos),
                    modulo="contratos",
                    detalles=tuple(
                        f"{contrato.numero} - vence {contrato.fecha_fin}"
                        for contrato in vencidos[:5]
                    ),
                )
            )

        por_vencer = self.contrato_repository.get_por_vencer(dias)
        if por_vencer:
            alertas.append(
                Alerta(
                    clave="contratos_por_vencer",
                    titulo="Contratos por vencer",
                    descripcion=f"{len(por_vencer)} contrato(s) vencen en los próximos {dias} días",
                    severidad=SeveridadAlerta.ADVERTENCIA.value,
                    categoria="contratos",
                    cantidad=len(por_vencer),
                    modulo="contratos",
                    detalles=tuple(
                        f"{contrato.numero} - {contrato.dias_para_vencer} día(s)"
                        for contrato in por_vencer[:5]
                    ),
                )
            )

        # Un empleado activo sin contrato vigente es un riesgo laboral y de
        # nómina: no hay respaldo documental de su salario ni de su jornada.
        sin_contrato = self.empleados_sin_contrato()
        if sin_contrato:
            alertas.append(
                Alerta(
                    clave="empleados_sin_contrato",
                    titulo="Empleados sin contrato vigente",
                    descripcion=(
                        f"{len(sin_contrato)} empleado(s) activos no tienen un "
                        "contrato vigente registrado"
                    ),
                    severidad=SeveridadAlerta.ADVERTENCIA.value,
                    categoria="contratos",
                    cantidad=len(sin_contrato),
                    modulo="contratos",
                    detalles=tuple(
                        f"{empleado.nombre_completo} ({empleado.cedula})"
                        for empleado in sin_contrato[:5]
                    ),
                )
            )
        return alertas

    def empleados_sin_contrato(self) -> list:
        """Empleados activos sin ningún contrato vigente"""
        from src.services.contrato_service import ContratoService

        return ContratoService(self.session).empleados_sin_contrato()

    def alertas_incidencias(self) -> list[Alerta]:
        """Incidencias pendientes de aprobación"""
        pendientes = self.incidencia_repository.get_pendientes()
        if not pendientes:
            return []
        antiguas = [
            incidencia
            for incidencia in pendientes
            if getattr(incidencia, "fecha_solicitud", None)
            and isinstance(incidencia.fecha_solicitud, date)
            and (date.today() - incidencia.fecha_solicitud).days > 15
        ]
        return [
            Alerta(
                clave="incidencias_pendientes",
                titulo="Incidencias por aprobar",
                descripcion=f"{len(pendientes)} incidencia(s) esperan aprobación",
                severidad=(
                    SeveridadAlerta.CRITICA.value
                    if antiguas
                    else SeveridadAlerta.ADVERTENCIA.value
                ),
                categoria="incidencias",
                cantidad=len(pendientes),
                modulo="incidencias",
                detalles=tuple(
                    f"#{incidencia.id} {getattr(incidencia, 'tipo_incidencia', '')} "
                    f"({incidencia.fecha_inicio} - {incidencia.fecha_fin})"
                    for incidencia in pendientes[:5]
                ),
            )
        ]

    def alertas_asistencia(self, fecha: date | None = None) -> list[Alerta]:
        """Jornadas del día pendientes de registrar y ausentismo elevado"""
        from src.services.asistencia_service import AsistenciaService

        referencia = fecha or date.today()
        servicio = AsistenciaService(self.session)
        sin_registro = servicio.empleados_sin_registro(referencia)

        alertas: list[Alerta] = []
        if sin_registro:
            alertas.append(
                Alerta(
                    clave="asistencia_sin_registrar",
                    titulo="Jornadas sin registrar",
                    descripcion=(
                        f"{len(sin_registro)} empleado(s) no tienen asistencia del "
                        f"{referencia.strftime('%d/%m/%Y')}"
                    ),
                    severidad=SeveridadAlerta.ADVERTENCIA.value,
                    categoria="asistencia",
                    cantidad=len(sin_registro),
                    modulo="asistencia",
                    detalles=tuple(
                        empleado.nombre_completo for empleado in sin_registro[:5]
                    ),
                )
            )

        umbral = float(self._valor("umbral_ausentismo_alerta", 10) or 10)
        inicio_mes = referencia.replace(day=1)
        estadisticas = servicio.obtener_estadisticas(inicio_mes, referencia)
        ausentismo = float(estadisticas.get("ausentismo_porcentaje") or 0)
        if umbral > 0 and ausentismo >= umbral:
            alertas.append(
                Alerta(
                    clave="ausentismo_elevado",
                    titulo="Ausentismo elevado",
                    descripcion=(
                        f"El ausentismo del mes es {ausentismo:.1f}% "
                        f"(umbral configurado: {umbral:.1f}%)"
                    ),
                    severidad=SeveridadAlerta.ADVERTENCIA.value,
                    categoria="asistencia",
                    cantidad=int(estadisticas.get("faltas") or 0),
                    modulo="asistencia",
                )
            )

        excesos = servicio.empleados_con_exceso_horas(inicio_mes, referencia)
        if excesos:
            alertas.append(
                Alerta(
                    clave="horas_extra_excesivas",
                    titulo="Horas extra por encima del límite",
                    descripcion=(
                        f"{len(excesos)} empleado(s) superaron el máximo de horas extra semanal"
                    ),
                    severidad=SeveridadAlerta.ADVERTENCIA.value,
                    categoria="asistencia",
                    cantidad=len(excesos),
                    modulo="asistencia",
                    detalles=tuple(
                        f"{exceso['empleado']}: {exceso['horas_extra']} h "
                        f"(semana {exceso['semana']})"
                        for exceso in excesos[:5]
                    ),
                )
            )
        return alertas

    def alertas_prestamos(self) -> list[Alerta]:
        """Solicitudes de préstamo por aprobar y saldos por cobrar"""
        alertas: list[Alerta] = []
        pendientes = self.prestamo_repository.get_pendientes_aprobacion()
        if pendientes:
            alertas.append(
                Alerta(
                    clave="prestamos_por_aprobar",
                    titulo="Préstamos por aprobar",
                    descripcion=f"{len(pendientes)} solicitud(es) de anticipo o préstamo esperan aprobación",
                    severidad=SeveridadAlerta.ADVERTENCIA.value,
                    categoria="prestamos",
                    cantidad=len(pendientes),
                    modulo="prestamos",
                    detalles=tuple(
                        f"#{prestamo.id} - {float(prestamo.monto or 0):.2f} "
                        f"({prestamo.numero_cuotas} cuota(s))"
                        for prestamo in pendientes[:5]
                    ),
                )
            )

        estadisticas = self.prestamo_repository.get_estadisticas()
        if estadisticas.get("activos"):
            alertas.append(
                Alerta(
                    clave="prestamos_activos",
                    titulo="Préstamos en curso",
                    descripcion=(
                        f"{estadisticas['activos']} préstamo(s) activos con un saldo de "
                        f"{float(estadisticas.get('saldo_pendiente') or 0):.2f}"
                    ),
                    severidad=SeveridadAlerta.INFO.value,
                    categoria="prestamos",
                    cantidad=int(estadisticas["activos"]),
                    modulo="prestamos",
                )
            )
        return alertas

    def alertas_nomina(self) -> list[Alerta]:
        """Pagos pendientes antiguos y parámetros de cálculo inconsistentes"""
        alertas: list[Alerta] = []
        limite = self._entero("dias_alerta_pago_antiguo", DIAS_PAGO_ANTIGUO_DEFECTO)
        fecha_limite = date.today() - timedelta(days=max(1, limite))
        antiguos = [
            pago
            for pago in self.pago_repository.get_pendientes()
            if getattr(pago, "periodo_fin", None)
            and isinstance(pago.periodo_fin, date)
            and pago.periodo_fin < fecha_limite
        ]
        if antiguos:
            alertas.append(
                Alerta(
                    clave="pagos_pendientes_antiguos",
                    titulo="Pagos pendientes antiguos",
                    descripcion=(
                        f"{len(antiguos)} pago(s) llevan más de {limite} días sin marcarse "
                        "como realizados"
                    ),
                    severidad=SeveridadAlerta.ADVERTENCIA.value,
                    categoria="nomina",
                    cantidad=len(antiguos),
                    modulo="nomina",
                    detalles=tuple(
                        f"#{pago.id} - {float(pago.monto_neto or 0):.2f} ({pago.periodo_fin})"
                        for pago in antiguos[:5]
                    ),
                )
            )

        from src.nomina import cargar_parametros_desde

        try:
            parametros = cargar_parametros_desde(self.config_repository.get_valor)
        except (SQLAlchemyError, ValueError, TypeError):
            logger.debug("No se pudieron leer los parámetros de nómina", exc_info=True)
            return alertas

        problemas = validar_parametros(parametros)
        if problemas:
            alertas.append(
                Alerta(
                    clave="parametros_nomina_inconsistentes",
                    titulo="Parámetros de nómina inconsistentes",
                    descripcion="La configuración de nómina tiene valores que deben revisarse",
                    severidad=SeveridadAlerta.CRITICA.value,
                    categoria="nomina",
                    cantidad=len(problemas),
                    modulo="configuracion",
                    detalles=tuple(problemas[:5]),
                )
            )
        return alertas

    def alertas_respaldo(self) -> list[Alerta]:
        """Respaldos atrasados o deshabilitados"""
        try:
            from src.utils.backup_manager import get_backup_manager

            backups = get_backup_manager().list_backups()
        except (OSError, ValueError, SQLAlchemyError):
            logger.debug("No se pudo consultar el estado de los respaldos", exc_info=True)
            return []

        habilitado = bool(self._valor("backup_enabled", True))
        alertas: list[Alerta] = []

        if not habilitado:
            alertas.append(
                Alerta(
                    clave="respaldo_deshabilitado",
                    titulo="Respaldos automáticos deshabilitados",
                    descripcion=(
                        "El sistema no está generando respaldos automáticos; "
                        "active la opción en Configuración"
                    ),
                    severidad=SeveridadAlerta.ADVERTENCIA.value,
                    categoria="respaldo",
                    modulo="configuracion",
                )
            )
            return alertas

        intervalo = self._entero("backup_interval_hours", DIAS_RESPALDO_DEFECTO)
        ultimo = self._fecha_ultimo_respaldo(backups)
        if ultimo is None:
            alertas.append(
                Alerta(
                    clave="respaldo_ausente",
                    titulo="Sin respaldos registrados",
                    descripcion="No hay ningún respaldo disponible para recuperar la información",
                    severidad=SeveridadAlerta.CRITICA.value,
                    categoria="respaldo",
                    modulo="configuracion",
                )
            )
            return alertas

        horas = (datetime.now() - ultimo).total_seconds() / 3600
        if intervalo > 0 and horas > intervalo * 1.5:
            alertas.append(
                Alerta(
                    clave="respaldo_atrasado",
                    titulo="Respaldo atrasado",
                    descripcion=(
                        f"El último respaldo es de hace {horas:.0f} horas "
                        f"(intervalo configurado: {intervalo} h)"
                    ),
                    severidad=SeveridadAlerta.ADVERTENCIA.value,
                    categoria="respaldo",
                    modulo="configuracion",
                )
            )
        return alertas

    def alertas_credenciales(self, usuario=None) -> list[Alerta]:
        """Contraseñas caducadas y cuentas bloqueadas"""
        dias_caducidad = self._entero("password_dias_caducidad", 90)
        alertas: list[Alerta] = []

        bloqueados = [
            cuenta
            for cuenta in self.usuario_repository.get_all(skip=0, limit=None)
            if getattr(cuenta, "bloqueado", 0)
        ]
        if bloqueados:
            alertas.append(
                Alerta(
                    clave="usuarios_bloqueados",
                    titulo="Cuentas bloqueadas",
                    descripcion=f"{len(bloqueados)} usuario(s) tienen su cuenta bloqueada",
                    severidad=SeveridadAlerta.ADVERTENCIA.value,
                    categoria="seguridad",
                    cantidad=len(bloqueados),
                    modulo="configuracion",
                    detalles=tuple(cuenta.username for cuenta in bloqueados[:5]),
                )
            )

        if dias_caducidad > 0:
            vencidas = [
                cuenta
                for cuenta in self.usuario_repository.get_all(skip=0, limit=None)
                if self._password_caducada(cuenta, dias_caducidad)
            ]
            if vencidas:
                alertas.append(
                    Alerta(
                        clave="passwords_caducadas",
                        titulo="Contraseñas caducadas",
                        descripcion=(
                            f"{len(vencidas)} usuario(s) deben cambiar su contraseña "
                            f"(vigencia de {dias_caducidad} días)"
                        ),
                        severidad=SeveridadAlerta.ADVERTENCIA.value,
                        categoria="seguridad",
                        cantidad=len(vencidas),
                        modulo="configuracion",
                        detalles=tuple(cuenta.username for cuenta in vencidas[:5]),
                    )
                )

        if usuario is not None and getattr(usuario, "debe_cambiar_password", False):
            alertas.append(
                Alerta(
                    clave="cambio_password_obligatorio",
                    titulo="Cambio de contraseña pendiente",
                    descripcion="Su cuenta requiere un cambio de contraseña",
                    severidad=SeveridadAlerta.ADVERTENCIA.value,
                    categoria="seguridad",
                    cantidad=1,
                    modulo="configuracion",
                )
            )
        return alertas

    @staticmethod
    def _password_caducada(cuenta, dias_caducidad: int) -> bool:
        """
        Indica si la contraseña de una cuenta superó su vigencia

        Se toma como referencia la fecha del último cambio; si nunca se
        registró, se usa la fecha de creación de la cuenta, y como último
        recurso se considera vigente para no bloquear a nadie por falta
        de datos.
        """
        referencia = getattr(cuenta, "fecha_cambio_password", None)
        if referencia is None:
            referencia = getattr(cuenta, "created_at", None)
        if not isinstance(referencia, (datetime, date)):
            return False
        if isinstance(referencia, date) and not isinstance(referencia, datetime):
            referencia = datetime.combine(referencia, datetime.min.time())
        return (datetime.now() - referencia).days > dias_caducidad

    @staticmethod
    def _fecha_ultimo_respaldo(backups: list) -> datetime | None:
        """
        Fecha del respaldo más reciente

        Los respaldos pueden venir como diccionarios (con 'fecha' o
        'created_at') o como objetos con atributos equivalentes; se
        interpretan ambas formas y, si ninguna es legible, se usa la
        fecha del archivo de cada respaldo.
        """
        candidatos: list[datetime] = []
        atributos_fecha = ("fecha", "created_at", "date", "fecha_creacion", "mtime")
        for respaldo in backups or []:
            fecha = AlertaService._fecha_de_respaldo(respaldo, atributos_fecha)
            if fecha is None:
                fecha = AlertaService._fecha_de_archivo(respaldo)
            if fecha is not None:
                candidatos.append(fecha)
        return max(candidatos) if candidatos else None

    @staticmethod
    def _fecha_de_respaldo(respaldo, atributos: tuple[str, ...]) -> datetime | None:
        """Fecha declarada en los metadatos de un respaldo"""
        # El gestor de respaldos guarda su marca con el formato 20260922_180454
        marca = (
            respaldo.get("timestamp") if isinstance(respaldo, dict) else getattr(respaldo, "timestamp", None)
        )
        if isinstance(marca, str) and marca.strip():
            try:
                return datetime.strptime(marca.strip()[:15], "%Y%m%d_%H%M%S")
            except ValueError:
                pass

        for atributo in atributos:
            valor = (
                respaldo.get(atributo)
                if isinstance(respaldo, dict)
                else getattr(respaldo, atributo, None)
            )
            fecha = AlertaService._como_datetime(valor)
            if fecha is not None:
                return fecha
        return None

    @staticmethod
    def _fecha_de_archivo(respaldo) -> datetime | None:
        """Fecha de modificación del archivo de un respaldo"""
        from pathlib import Path

        if isinstance(respaldo, dict):
            ruta = respaldo.get("path") or respaldo.get("ruta")
        else:
            ruta = getattr(respaldo, "path", None) or getattr(respaldo, "ruta", None)
        if not ruta:
            return None
        try:
            return datetime.fromtimestamp(Path(str(ruta)).stat().st_mtime)
        except (OSError, ValueError):
            return None

    @staticmethod
    def _como_datetime(valor) -> datetime | None:
        """Convierte un valor de fecha de cualquier procedencia a datetime"""
        if isinstance(valor, datetime):
            return valor
        if isinstance(valor, date):
            return datetime.combine(valor, datetime.min.time())
        if isinstance(valor, (int, float)):
            try:
                return datetime.fromtimestamp(float(valor))
            except (OSError, OverflowError, ValueError):
                return None
        if isinstance(valor, str) and valor.strip():
            texto = valor.strip().replace("Z", "")
            for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(texto[:19], formato)
                except ValueError:
                    continue
        return None

    # ------------------------------------------------------------------
    # Resúmenes
    # ------------------------------------------------------------------
    def resumen(self, usuario=None) -> dict:
        """
        Resumen de alertas para la barra lateral y el panel del Dashboard

        Returns:
            dict: totales por severidad, total general y alertas críticas.
        """
        alertas = self.generar_alertas(usuario)
        por_severidad: dict[str, int] = {
            SeveridadAlerta.CRITICA.value: 0,
            SeveridadAlerta.ADVERTENCIA.value: 0,
            SeveridadAlerta.INFO.value: 0,
        }
        for alerta in alertas:
            por_severidad[alerta.severidad] = por_severidad.get(alerta.severidad, 0) + 1
        return {
            "total": len(alertas),
            "criticas": por_severidad[SeveridadAlerta.CRITICA.value],
            "advertencias": por_severidad[SeveridadAlerta.ADVERTENCIA.value],
            "informativas": por_severidad[SeveridadAlerta.INFO.value],
            "por_severidad": por_severidad,
            "alertas": alertas,
        }

    def contar(self, usuario=None) -> int:
        """Cantidad total de alertas vigentes"""
        return len(self.generar_alertas(usuario))

    def criticas(self, usuario=None) -> list[Alerta]:
        """Alertas que requieren atención inmediata"""
        return [alerta for alerta in self.generar_alertas(usuario) if alerta.es_critica]

"""
Acciones y consultas del protocolo 2 del nodo central

El protocolo v1 (ping/push/pull/blob) replicaba **datos**; la aplicación móvil
con paridad total necesita además tres cosas que el escritorio resuelve en su
propio proceso y que aquí deben vivir en el servidor para que exista una sola
fuente de verdad:

1. **Autenticación de usuario**: login contra la tabla ``usuarios`` de la base
   institucional (``sync_agent.sesiones``), con los mismos roles del escritorio.
2. **Acciones de negocio**: generar nómina, terminar contratos con finiquito,
   cerrar periodos académicos… todo se ejecuta con los servicios Python
   existentes; el móvil nunca reimplementa el cálculo.
3. **Documentos**: PDF y Excel se generan aquí con el generador del escritorio y
   se entregan por el canal de binarios (hash + descarga), deduplicados.

Toda acción exige una sesión de usuario y aplica **la misma matriz de permisos
del escritorio** (``PermissionChecker``): módulo visible según rol y permiso de
acción (create/read/update/delete/report/config). La comprobación es
*fail-closed*: un módulo no declarado queda denegado para todos los roles.
"""

from __future__ import annotations

import logging
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from sqlalchemy.exc import SQLAlchemyError

from sync_agent.comun import hash_bytes
from sync_agent.sesiones import ErrorSesion, GestorSesiones, SesionValida

logger = logging.getLogger(__name__)

# Límites razonables para una consulta desde un teléfono
MAX_FILAS_LISTA = 500


class ErrorApi(Exception):
    """Acción rechazada; ``codigo`` es el estado HTTP con el que responder"""

    def __init__(self, mensaje: str, codigo: int = 400):
        super().__init__(mensaje)
        self.codigo = codigo


# ----------------------------------------------------------------------
# Auditoría
# ----------------------------------------------------------------------
def _tipo_evento(nombre: str):
    """Accede a un tipo de evento de auditoría sin importar el módulo arriba"""
    from src.utils.audit_logger import AuditEventType

    return getattr(AuditEventType, nombre)


def _auditar(
    username: str,
    evento,
    entidad: str,
    entidad_id=None,
    detalles: dict | None = None,
    exito: bool = True,
) -> None:
    """Registra una acción del móvil en la auditoría del sistema"""
    try:
        from src.utils.audit_logger import get_audit_logger

        auditoria = get_audit_logger()
        if auditoria:
            auditoria.log_event(
                event_type=evento,
                entity_type=entidad,
                entity_id=entidad_id,
                user=username or "system",
                details={"origen": "movil", **(detalles or {})},
                success=exito,
            )
    except Exception:  # pragma: no cover - la auditoría nunca rompe una acción
        logger.warning("No se pudo registrar el evento de auditoría", exc_info=True)


# ----------------------------------------------------------------------
# Control de permisos (espejo de la política del escritorio)
# ----------------------------------------------------------------------
def exigir_permiso(sesion: SesionValida, permiso: str, modulo: str | None = None) -> None:
    """
    Comprueba el permiso de acción y, si aplica, el acceso al módulo

    Raises:
        ErrorApi: 403 si el rol no tiene ese permiso o no accede al módulo
    """
    from src.utils.security import PermissionChecker

    if modulo is not None and not PermissionChecker.can_access_module(sesion.rol, modulo):
        _auditar(sesion.username, _tipo_evento("SECURITY_PERMISSION_DENIED"), modulo or "sistema",
                 detalles={"permiso": permiso}, exito=False)
        raise ErrorApi(f"Su rol no tiene acceso al módulo «{modulo}»", 403)
    if not PermissionChecker.has_permission(sesion.rol, permiso):
        _auditar(sesion.username, _tipo_evento("SECURITY_PERMISSION_DENIED"), modulo or "sistema",
                 detalles={"permiso": permiso}, exito=False)
        raise ErrorApi(f"Su rol no tiene permiso para «{permiso}»", 403)


def exigir_admin(sesion: SesionValida) -> None:
    """Comprueba que la sesión corresponde a un administrador"""
    if sesion.rol != "admin":
        _auditar(sesion.username, _tipo_evento("SECURITY_PERMISSION_DENIED"), "configuracion",
                 detalles={"permiso": "admin"}, exito=False)
        raise ErrorApi("Esta operación es exclusiva del administrador", 403)


# ----------------------------------------------------------------------
# Serialización a JSON
# ----------------------------------------------------------------------
def serializar(valor: Any) -> Any:
    """Convierte modelos y tipos del dominio a JSON seguro (sin Decimal ni bytes)"""
    if valor is None or isinstance(valor, (bool, int, float, str)):
        return valor
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, (bytes, bytearray)):
        return None
    to_dict = getattr(valor, "to_dict", None)
    if callable(to_dict):
        return serializar(to_dict())
    if isinstance(valor, dict):
        return {clave: serializar(item) for clave, item in valor.items()}
    if isinstance(valor, (list, tuple, set)):
        return [serializar(item) for item in valor]
    isoformat = getattr(valor, "isoformat", None)
    if callable(isoformat):
        return valor.isoformat()
    return str(valor)


def _fecha(cuerpo: dict, clave: str, requerida: bool = True) -> date | None:
    """Extrae una fecha ISO (AAAA-MM-DD) del cuerpo de la petición"""
    crudo = cuerpo.get(clave)
    if crudo in (None, ""):
        if requerida:
            raise ErrorApi(f"Falta la fecha «{clave}» (formato AAAA-MM-DD)")
        return None
    try:
        return date.fromisoformat(str(crudo)[:10])
    except ValueError:
        raise ErrorApi(f"La fecha «{clave}» no es válida (use AAAA-MM-DD)") from None


def _entero(cuerpo: dict, clave: str, requerido: bool = True) -> int | None:
    """Extrae un entero del cuerpo de la petición"""
    crudo = cuerpo.get(clave)
    if crudo in (None, ""):
        if requerido:
            raise ErrorApi(f"Falta el valor «{clave}»")
        return None
    try:
        return int(crudo)
    except (TypeError, ValueError):
        raise ErrorApi(f"El valor «{clave}» debe ser un número entero") from None


# ----------------------------------------------------------------------
# Núcleo de la API
# ----------------------------------------------------------------------
class ApiAcciones:
    """
    Acciones y consultas del protocolo 2

    Cada método abre su propia sesión de base de datos (las del nodo central
    son de vida corta) y cierra siempre, incluso cuando la acción lanza. Los
    modelos se serializan con ``to_dict`` y ``serializar`` para que el móvil
    reciba JSON plano.
    """

    def __init__(self, nucleo):
        """
        Args:
            nucleo: NucleoCentral del nodo central (motor, blobs, configuración)
        """
        self.nucleo = nucleo
        self.gestor_sesiones = GestorSesiones(nucleo.SessionFactory)

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------
    def _sesion(self):
        return self.nucleo.SessionFactory()

    @staticmethod
    def _ejecutar(operacion: Callable[[], Any]) -> Any:
        """Ejecuta un servicio y traduce sus errores a códigos HTTP"""
        try:
            return operacion()
        except (ErrorApi, ErrorSesion):
            raise
        except ValueError as error:
            raise ErrorApi(str(error), 400) from None
        except SQLAlchemyError as error:
            logger.error("Fallo de base de datos en una acción del móvil", exc_info=True)
            raise ErrorApi("Error interno de base de datos", 500) from error

    # ==================================================================
    # Autenticación
    # ==================================================================
    def login(self, cuerpo: dict, dispositivo_id: str | None) -> dict:
        """
        Inicio de sesión con usuario y contraseña de la base institucional

        El bloqueo por intentos, la caducidad y el historial los aplica
        ``AuthService``: exactamente las mismas reglas que en el escritorio.
        """
        username = str(cuerpo.get("username") or "").strip()
        password = str(cuerpo.get("password") or "")
        if not username or not password:
            raise ErrorApi("Debe escribir el usuario y la contraseña")
        resultado = self.gestor_sesiones.iniciar(username, password, dispositivo_id)
        _auditar(username, _tipo_evento("USER_LOGIN"), "usuario",
                 detalles={"dispositivo": dispositivo_id, "rol": resultado.get("rol")})
        return resultado

    def cerrar_sesion(self, token: str) -> dict:
        """Revoca la sesión del token (logout del móvil)"""
        valido = self.gestor_sesiones.validar(token, deslizar=False)
        self.gestor_sesiones.cerrar(token)
        _auditar(valido.username, _tipo_evento("USER_LOGOUT"), "usuario")
        return {"correcto": True}

    def info_sesion(self, token: str) -> dict:
        """Valida el token y devuelve los datos de la sesión vigente"""
        valido = self.gestor_sesiones.validar(token)
        return {
            "username": valido.username,
            "nombre_completo": valido.nombre_completo,
            "rol": valido.rol,
            "debe_cambiar_password": valido.debe_cambiar_password,
            "expira_en": valido.expira_en.isoformat() if valido.expira_en else None,
        }

    def cambiar_password(self, token: str, cuerpo: dict) -> dict:
        """Cambia la contraseña con la misma política del escritorio"""
        nueva = str(cuerpo.get("nueva") or "")
        actual = cuerpo.get("actual")
        self.gestor_sesiones.cambiar_password(token, nueva, actual)
        return {"correcto": True}

    def validar(self, token: str | None) -> SesionValida:
        """Valida el token de sesión (lo usa el enrutador antes de cada acción)"""
        return self.gestor_sesiones.validar(token)

    # ==================================================================
    # Consultas
    # ==================================================================
    def dashboard(self, sesion: SesionValida) -> dict:
        """
        Indicadores del panel de control, filtrados por el rol

        Cada bloque se evalúa solo si el rol accede al módulo correspondiente y
        una estadística que falle no hunde el resto del panel.
        """
        from src.utils.security import PermissionChecker

        bloques: dict[str, Any] = {}

        def incluir(modulo: str, clave: str, operacion) -> None:
            if not PermissionChecker.can_access_module(sesion.rol, modulo):
                return
            try:
                bloques[clave] = serializar(operacion())
            except Exception:  # pragma: no cover - un indicador roto no es fatal
                logger.warning("Indicador %s del panel no disponible", clave, exc_info=True)

        from src.services.academico_service import AcademicoService
        from src.services.contrato_service import ContratoService
        from src.services.documento_service import DocumentoService
        from src.services.empleado_service import EmpleadoService
        from src.services.incidencia_service import IncidenciaService
        from src.services.pago_service import PagoService

        db = self._sesion()
        try:
            incluir("empleados", "empleados", lambda: EmpleadoService(db).obtener_estadisticas())
            incluir("documentos", "documentos", lambda: DocumentoService(db).obtener_estadisticas())
            incluir("incidencias", "incidencias", lambda: IncidenciaService(db).obtener_estadisticas())
            incluir("contratos", "contratos", lambda: ContratoService(db).obtener_estadisticas())
            incluir("nomina", "nomina", lambda: PagoService(db).obtener_estadisticas())
            incluir("estudiantes", "academico", lambda: AcademicoService(db).estadisticas())
        finally:
            db.close()

        return {"rol": sesion.rol, "usuario": sesion.username, "indicadores": bloques}

    def auditoria(self, sesion: SesionValida, limite: int = 100) -> dict:
        """Visor de auditoría (solo administrador), como en el escritorio"""
        exigir_admin(sesion)
        from src.utils.audit_logger import get_audit_logger

        auditoria = get_audit_logger()
        eventos = auditoria.get_recent_events(limit=max(1, min(int(limite or 100), 500))) if auditoria else []
        return {"eventos": serializar(eventos)}

    # ==================================================================
    # Administración de usuarios (solo admin)
    # ==================================================================
    def listar_usuarios(self, sesion: SesionValida) -> dict:
        """Cuentas de la institución con su rol y estado"""
        exigir_admin(sesion)
        from src.services.auth_service import AuthService

        db = self._sesion()
        try:
            usuarios = self._ejecutar(lambda: AuthService(db).listar_usuarios())
            datos = serializar(usuarios)
            for fila in datos:
                fila.pop("password_hash", None)
                fila.pop("password_historial", None)
            return {"usuarios": datos}
        finally:
            db.close()

    def crear_usuario(self, sesion: SesionValida, cuerpo: dict) -> dict:
        """Alta de una cuenta institucional (admin)"""
        exigir_admin(sesion)
        from src.services.auth_service import AuthService

        db = self._sesion()
        try:
            creado = self._ejecutar(
                lambda: AuthService(db).crear_usuario(
                    username=str(cuerpo.get("username") or ""),
                    password=str(cuerpo.get("password") or ""),
                    rol=str(cuerpo.get("rol") or ""),
                    nombre_completo=str(cuerpo.get("nombre_completo") or ""),
                    debe_cambiar_password=bool(cuerpo.get("debe_cambiar_password", True)),
                )
            )
            _auditar(sesion.username, _tipo_evento("DATA_CREATE"), "usuario", creado.id,
                     {"username": creado.username, "rol": cuerpo.get("rol")})
            datos = serializar(creado)
            datos.pop("password_hash", None)
            datos.pop("password_historial", None)
            return {"usuario": datos}
        finally:
            db.close()

    def actualizar_usuario(self, sesion: SesionValida, usuario_id: int, cuerpo: dict) -> dict:
        """Modificación de rol, nombre, estado o contraseña de una cuenta (admin)"""
        exigir_admin(sesion)
        from src.models import Usuario
        from src.services.auth_service import AuthService

        db = self._sesion()
        try:
            def operar():
                servicio = AuthService(db)
                # ``usuario_actual`` es quien ejecuta la operación (para que no
                # se degrade ni se desactive a sí mismo), no la cuenta objetivo.
                actor = db.query(Usuario).filter(Usuario.username == sesion.username).first()
                return servicio.actualizar_usuario(usuario_id, cuerpo, usuario_actual=actor)

            actualizado = self._ejecutar(operar)
            _auditar(sesion.username, _tipo_evento("DATA_UPDATE"), "usuario", usuario_id,
                     {"campos": sorted(str(c) for c in cuerpo.keys())})
            datos = serializar(actualizado)
            datos.pop("password_hash", None)
            datos.pop("password_historial", None)
            return {"usuario": datos}
        finally:
            db.close()

    def desbloquear_usuario(self, sesion: SesionValida, usuario_id: int) -> dict:
        """Levanta el bloqueo por intentos fallidos de una cuenta (admin)"""
        exigir_admin(sesion)
        from src.services.auth_service import AuthService

        db = self._sesion()
        try:
            self._ejecutar(lambda: AuthService(db).desbloquear_usuario(usuario_id))
            _auditar(sesion.username, _tipo_evento("DATA_UPDATE"), "usuario", usuario_id,
                     {"operacion": "desbloquear"})
            return {"correcto": True}
        finally:
            db.close()

    # ==================================================================
    # Nómina (módulo nomina)
    # ==================================================================
    def generar_nomina_periodo(self, sesion: SesionValida, cuerpo: dict) -> dict:
        """Genera las nóminas de un periodo con el motor del escritorio"""
        exigir_permiso(sesion, "create", "nomina")
        desde = _fecha(cuerpo, "periodo_inicio")
        hasta = _fecha(cuerpo, "periodo_fin")
        from src.services.pago_service import PagoService

        db = self._sesion()
        try:
            pagos = self._ejecutar(lambda: PagoService(db).generar_nominas_periodo(desde, hasta))
            _auditar(sesion.username, _tipo_evento("DATA_CREATE"), "pago",
                     detalles={"periodo": f"{desde}..{hasta}", "generados": len(pagos)})
            return {"generados": len(pagos), "pagos": serializar(pagos)[:MAX_FILAS_LISTA]}
        finally:
            db.close()

    def marcar_pagado(self, sesion: SesionValida, pago_id: int) -> dict:
        """Marca un pago como realizado"""
        exigir_permiso(sesion, "update", "nomina")
        from src.services.pago_service import PagoService

        db = self._sesion()
        try:
            pagado = self._ejecutar(lambda: PagoService(db).marcar_pagado(pago_id))
            if not pagado:
                raise ErrorApi("El pago no existe", 404)
            _auditar(sesion.username, _tipo_evento("DATA_UPDATE"), "pago", pago_id,
                     {"operacion": "marcar_pagado"})
            return {"correcto": True}
        finally:
            db.close()

    def resumen_nomina(self, sesion: SesionValida, cuerpo: dict) -> dict:
        """Resumen y pagos de un periodo de nómina (totales ISSS, AFP, ISR, neto)"""
        exigir_permiso(sesion, "read", "nomina")
        desde = _fecha(cuerpo, "periodo_inicio")
        hasta = _fecha(cuerpo, "periodo_fin")
        from src.services.pago_service import PagoService

        db = self._sesion()
        try:
            servicio = PagoService(db)
            resumen = self._ejecutar(lambda: servicio.obtener_resumen_periodo(desde, hasta))
            pagos = self._ejecutar(lambda: servicio.listar_por_periodo(desde, hasta))
            return {"resumen": serializar(resumen), "pagos": serializar(pagos)[:MAX_FILAS_LISTA]}
        finally:
            db.close()

    # ==================================================================
    # Incidencias (módulo incidencias)
    # ==================================================================
    def aprobar_incidencia(self, sesion: SesionValida, incidencia_id: int, cuerpo: dict) -> dict:
        """Aprueba una incidencia a nombre del usuario de la sesión"""
        exigir_permiso(sesion, "update", "incidencias")
        from src.services.incidencia_service import IncidenciaService

        db = self._sesion()
        try:
            correcto = self._ejecutar(
                lambda: IncidenciaService(db).aprobar_incidencia(
                    incidencia_id,
                    aprobado_por=sesion.username,
                    comentarios=cuerpo.get("comentarios"),
                    dias_aprobados=_entero(cuerpo, "dias_aprobados", requerido=False),
                )
            )
            if not correcto:
                raise ErrorApi("La incidencia no existe", 404)
            _auditar(sesion.username, _tipo_evento("DATA_UPDATE"), "incidencia", incidencia_id,
                     {"operacion": "aprobar"})
            return {"correcto": True}
        finally:
            db.close()

    def rechazar_incidencia(self, sesion: SesionValida, incidencia_id: int, cuerpo: dict) -> dict:
        """Rechaza una incidencia a nombre del usuario de la sesión"""
        exigir_permiso(sesion, "update", "incidencias")
        from src.services.incidencia_service import IncidenciaService

        db = self._sesion()
        try:
            correcto = self._ejecutar(
                lambda: IncidenciaService(db).rechazar_incidencia(
                    incidencia_id,
                    rechazado_por=sesion.username,
                    comentarios=cuerpo.get("comentarios"),
                )
            )
            if not correcto:
                raise ErrorApi("La incidencia no existe", 404)
            _auditar(sesion.username, _tipo_evento("DATA_UPDATE"), "incidencia", incidencia_id,
                     {"operacion": "rechazar"})
            return {"correcto": True}
        finally:
            db.close()

    # ==================================================================
    # Contratos (módulo contratos)
    # ==================================================================
    def renovar_contrato(self, sesion: SesionValida, contrato_id: int, cuerpo: dict) -> dict:
        """Renueva un contrato vigente, encadenado al anterior"""
        exigir_permiso(sesion, "update", "contratos")
        from src.services.contrato_service import ContratoService

        db = self._sesion()
        try:
            nuevo = self._ejecutar(
                lambda: ContratoService(db).renovar_contrato(
                    contrato_id,
                    nueva_fecha_fin=_fecha(cuerpo, "nueva_fecha_fin"),
                    nuevo_salario=cuerpo.get("nuevo_salario"),
                    tipo=cuerpo.get("tipo"),
                    clausulas=cuerpo.get("clausulas"),
                    aprobado_por=sesion.username,
                )
            )
            _auditar(sesion.username, _tipo_evento("DATA_CREATE"), "contrato", getattr(nuevo, "id", None),
                     {"operacion": "renovar", "anterior": contrato_id})
            return {"contrato": serializar(nuevo)}
        finally:
            db.close()

    def terminar_contrato(self, sesion: SesionValida, contrato_id: int, cuerpo: dict) -> dict:
        """Termina un contrato y genera su finiquito con el motor del escritorio"""
        exigir_permiso(sesion, "update", "contratos")
        motivo = str(cuerpo.get("motivo") or "").strip()
        if not motivo:
            raise ErrorApi("El motivo de terminación es obligatorio")
        from src.services.contrato_service import ContratoService

        db = self._sesion()
        try:
            resultado = self._ejecutar(
                lambda: ContratoService(db).terminar_contrato(
                    contrato_id,
                    motivo=motivo,
                    fecha_terminacion=_fecha(cuerpo, "fecha_terminacion", requerida=False),
                    generar_liquidacion=bool(cuerpo.get("generar_liquidacion", True)),
                    metodo_pago=cuerpo.get("metodo_pago"),
                    registrado_por=sesion.username,
                )
            )
            _auditar(sesion.username, _tipo_evento("DATA_UPDATE"), "contrato", contrato_id,
                     {"operacion": "terminar", "motivo": motivo})
            return {"resultado": serializar(resultado)}
        finally:
            db.close()

    # ==================================================================
    # Académico (periodos, notas, boletines)
    # ==================================================================
    def cerrar_periodo(self, sesion: SesionValida, periodo_id: int, cuerpo: dict) -> dict:
        """Cierra un periodo académico: sus notas quedan inmutables"""
        exigir_permiso(sesion, "create", "notas")
        from src.services.academico_service import AcademicoService

        db = self._sesion()
        try:
            periodo = self._ejecutar(
                lambda: AcademicoService(db).cerrar_periodo(periodo_id, cuerpo.get("token"))
            )
            _auditar(sesion.username, _tipo_evento("DATA_UPDATE"), "periodo_academico", periodo_id,
                     {"operacion": "cerrar"})
            return {"periodo": serializar(periodo)}
        finally:
            db.close()

    def reabrir_periodo(self, sesion: SesionValida, periodo_id: int, cuerpo: dict) -> dict:
        """Reabre un periodo cerrado: decisión restringida al administrador"""
        exigir_permiso(sesion, "config", "notas")
        from src.services.academico_service import AcademicoService

        db = self._sesion()
        try:
            periodo = self._ejecutar(
                lambda: AcademicoService(db).reabrir_periodo(periodo_id, cuerpo.get("token"))
            )
            _auditar(sesion.username, _tipo_evento("DATA_UPDATE"), "periodo_academico", periodo_id,
                     {"operacion": "reabrir"})
            return {"periodo": serializar(periodo)}
        finally:
            db.close()

    def cargar_notas_lote(self, sesion: SesionValida, cuerpo: dict) -> dict:
        """
        Carga por lotes de notas finales

        La escritura efectiva la autoriza el token académico: el docente
        asignado al grado o un administrador, igual que en el escritorio.
        """
        exigir_permiso(sesion, "read", "notas")
        filas = cuerpo.get("filas")
        if not isinstance(filas, list) or not filas:
            raise ErrorApi("Debe enviar al menos una nota en «filas»")
        token = cuerpo.get("token")
        from src.services.nota_service import NotaService

        db = self._sesion()
        try:
            guardadas = self._ejecutar(lambda: NotaService(db).guardar_lote(filas, token))
            _auditar(sesion.username, _tipo_evento("DATA_CREATE"), "nota_final",
                     detalles={"operacion": "carga_lote", "guardadas": guardadas})
            return {"guardadas": guardadas}
        finally:
            db.close()

    def notas_de_grado(self, sesion: SesionValida, grado_id: int) -> dict:
        """Notas finales de un grado"""
        exigir_permiso(sesion, "read", "notas")
        from src.services.nota_service import NotaService

        db = self._sesion()
        try:
            notas = self._ejecutar(lambda: NotaService(db).listar_notas_de_grado(grado_id))
            return {"notas": serializar(notas)[:MAX_FILAS_LISTA]}
        finally:
            db.close()

    def boletin_estudiante(self, sesion: SesionValida, cuerpo: dict) -> dict:
        """Datos del boletín de un estudiante (el móvil lo dibuja como el diálogo del escritorio)"""
        exigir_permiso(sesion, "read", "notas")
        estudiante_id = _entero(cuerpo, "estudiante_id")
        periodo_id = _entero(cuerpo, "periodo_id")
        from src.services.nota_service import NotaService

        db = self._sesion()
        try:
            datos = self._ejecutar(lambda: NotaService(db).datos_boletin(estudiante_id, periodo_id))
            return {"boletin": serializar(datos)}
        finally:
            db.close()

    def acta_grado(self, sesion: SesionValida, cuerpo: dict) -> dict:
        """Datos del acta final de un grado"""
        exigir_permiso(sesion, "read", "notas")
        grado_id = _entero(cuerpo, "grado_id")
        from src.services.nota_service import NotaService

        db = self._sesion()
        try:
            datos = self._ejecutar(lambda: NotaService(db).datos_acta(grado_id))
            return {"acta": serializar(datos)}
        finally:
            db.close()

    def consolidado_periodo(self, sesion: SesionValida, cuerpo: dict) -> dict:
        """Consolidado de notas de un periodo académico"""
        exigir_permiso(sesion, "read", "notas")
        periodo_id = _entero(cuerpo, "periodo_id")
        from src.services.nota_service import NotaService

        db = self._sesion()
        try:
            filas = self._ejecutar(lambda: NotaService(db).consolidado_periodo(periodo_id))
            return {"filas": serializar(filas)[:MAX_FILAS_LISTA]}
        finally:
            db.close()

    def emitir_token_academico(self, sesion: SesionValida) -> dict:
        """
        Emite el token de sesión académica del usuario

        El token autoriza a escribir notas en los grados asignados al docente
        (o en todos, si es administrador). Vive solo una jornada.
        """
        exigir_permiso(sesion, "read", "notas")
        from src.models import Usuario
        from src.services.token_sesion_service import TokenSesionService

        db = self._sesion()
        try:
            usuario = db.query(Usuario).filter(Usuario.username == sesion.username).first()
            if usuario is None:
                raise ErrorApi("La cuenta ya no existe", 401)
            token, registro = self._ejecutar(lambda: TokenSesionService(db).emitir(usuario))
            return {
                "token": token,
                "alcance": registro.alcance,
                "expira_en": registro.expira_en.isoformat() if registro.expira_en else None,
            }
        finally:
            db.close()

    def revocar_token_academico(self, sesion: SesionValida, cuerpo: dict) -> dict:
        """Revoca un token académico propio"""
        exigir_permiso(sesion, "read", "notas")
        from src.services.token_sesion_service import TokenSesionService

        db = self._sesion()
        try:
            correcto = self._ejecutar(lambda: TokenSesionService(db).revocar(cuerpo.get("token")))
            return {"correcto": bool(correcto)}
        finally:
            db.close()

    # ==================================================================
    # Archivos (PDF y Excel por el canal de binarios)
    # ==================================================================
    def subir_archivo(self, sesion: SesionValida, nombre: str, contenido: bytes, dispositivo) -> dict:
        """Guarda un archivo en el almacén central (deduplicado por hash)"""
        exigir_permiso(sesion, "create", "documentos")
        if not contenido:
            raise ErrorApi("El archivo está vacío")
        hash_archivo = hash_bytes(contenido)
        self.nucleo.guardar_blob(dispositivo, hash_archivo, contenido)
        _auditar(sesion.username, _tipo_evento("DATA_CREATE"), "archivo",
                 detalles={"nombre": nombre, "hash": hash_archivo[:12], "tamano": len(contenido)})
        return {
            "hash": hash_archivo,
            "tamano": len(contenido),
            "nombre": nombre,
            "descarga": f"/api/v1/blob/{hash_archivo}",
        }

    def generar_archivo(self, sesion: SesionValida, tipo: str, cuerpo: dict, dispositivo) -> dict:
        """
        Genera un PDF o Excel con los generadores del escritorio

        El archivo queda en el almacén de binarios y la respuesta devuelve su
        hash; el móvil lo descarga con el endpoint de binarios existente.
        """
        ruta, nombre = self._producir_archivo(sesion, tipo, cuerpo)
        try:
            contenido = Path(ruta).read_bytes()
        except OSError:
            raise ErrorApi("No se pudo leer el archivo generado", 500) from None
        if not contenido:
            raise ErrorApi("El archivo generado está vacío", 500)
        hash_archivo = hash_bytes(contenido)
        self.nucleo.guardar_blob(dispositivo, hash_archivo, contenido)
        _auditar(sesion.username, _tipo_evento("DATA_READ"), "reporte", detalles={"tipo": tipo})
        return {
            "hash": hash_archivo,
            "tamano": len(contenido),
            "nombre": nombre,
            "descarga": f"/api/v1/blob/{hash_archivo}",
        }

    # ------------------------------------------------------------------
    # Producción de cada archivo (misma forma que la del escritorio)
    # ------------------------------------------------------------------
    def _producir_archivo(self, sesion: SesionValida, tipo: str, cuerpo: dict) -> tuple[str, str]:
        """Genera el archivo solicitado y devuelve (ruta, nombre)"""
        from src.services.academico_service import AcademicoService
        from src.services.contrato_service import ContratoService
        from src.services.empleado_service import EmpleadoService
        from src.services.incidencia_service import IncidenciaService
        from src.services.pago_service import PagoService
        from src.utils.pdf_generator import PDFGenerator

        db = self._sesion()
        temporal = tempfile.mkdtemp(prefix="sdep_movil_")
        try:
            generador = PDFGenerator()
            servicio_empleados = EmpleadoService(db)

            def empleado_o_error(empleado_id: int | None):
                empleado = servicio_empleados.obtener_empleado(empleado_id) if empleado_id else None
                if empleado is None:
                    raise ErrorApi("El empleado no existe", 404)
                return empleado

            if tipo == "constancia_trabajo":
                exigir_permiso(sesion, "report", "empleados")
                destino = str(Path(temporal) / "constancia_trabajo.pdf")
                nombre = "constancia_trabajo.pdf"
                self._ejecutar(lambda: generador.generate_constancia_trabajo(
                    empleado_o_error(_entero(cuerpo, "empleado_id")), destino))

            elif tipo == "ficha_empleado":
                exigir_permiso(sesion, "report", "empleados")
                destino = str(Path(temporal) / "ficha_empleado.pdf")
                nombre = "ficha_empleado.pdf"
                self._ejecutar(lambda: generador.generate_ficha_empleado(
                    empleado_o_error(_entero(cuerpo, "empleado_id")), destino))

            elif tipo == "reporte_empleados":
                exigir_permiso(sesion, "report", "empleados")
                destino = str(Path(temporal) / "reporte_empleados.pdf")
                nombre = "reporte_empleados.pdf"
                self._ejecutar(lambda: generador.generate_reporte_empleados(
                    servicio_empleados.listar_empleados_activos(), destino))

            elif tipo == "recibo_pago":
                exigir_permiso(sesion, "report", "nomina")
                pago_id = _entero(cuerpo, "pago_id")
                pago = self._ejecutar(lambda: PagoService(db).obtener_pago(pago_id))
                if pago is None:
                    raise ErrorApi("El pago no existe", 404)
                destino = str(Path(temporal) / f"recibo_{pago_id}.pdf")
                nombre = f"recibo_{pago_id}.pdf"
                self._ejecutar(lambda: generador.generate_recibo_pago(self._fila_recibo(pago), destino))

            elif tipo == "planilla_nomina":
                exigir_permiso(sesion, "report", "nomina")
                desde = _fecha(cuerpo, "periodo_inicio")
                hasta = _fecha(cuerpo, "periodo_fin")
                pagos = self._ejecutar(lambda: PagoService(db).listar_por_periodo(desde, hasta))
                filas = self._filas_planilla(pagos, servicio_empleados)
                destino = str(Path(temporal) / "planilla_nomina.pdf")
                nombre = "planilla_nomina.pdf"
                titulo = f"Periodo: {desde.isoformat()} a {hasta.isoformat()} | Registros: {len(filas)}"
                self._ejecutar(lambda: generador.generate_reporte_nomina(filas, destino, titulo))

            elif tipo == "reporte_incidencias":
                exigir_permiso(sesion, "report", "incidencias")
                incidencias = self._ejecutar(lambda: IncidenciaService(db).listar_todas())
                filas = self._filas_incidencias(incidencias, servicio_empleados)
                destino = str(Path(temporal) / "reporte_incidencias.pdf")
                nombre = "reporte_incidencias.pdf"
                self._ejecutar(lambda: generador.generate_reporte_incidencias(
                    filas, destino, titulo="Todas las incidencias"))

            elif tipo == "reporte_contratos":
                exigir_permiso(sesion, "report", "contratos")
                contratos = self._ejecutar(lambda: ContratoService(db).listar_contratos())
                filas = self._filas_contratos(contratos, servicio_empleados)
                destino = str(Path(temporal) / "reporte_contratos.pdf")
                nombre = "reporte_contratos.pdf"
                self._ejecutar(lambda: generador.generate_reporte_contratos(filas, destino))

            elif tipo == "reporte_vencimientos":
                exigir_permiso(sesion, "report", "documentos")
                from src.services.documento_service import DocumentoService

                documentos = DocumentoService(db).listar_vencidos() + DocumentoService(db).listar_por_vencer(30)
                filas = self._filas_vencimientos(documentos, servicio_empleados)
                destino = str(Path(temporal) / "reporte_vencimientos.pdf")
                nombre = "reporte_vencimientos.pdf"
                if not filas:
                    raise ErrorApi("No hay documentos vencidos ni por vencer")
                self._ejecutar(lambda: generador.generate_reporte_vencimientos(
                    filas, destino, titulo=f"Generado el {date.today().isoformat()}"))

            elif tipo == "liquidacion":
                exigir_permiso(sesion, "report", "contratos")
                contrato_id = _entero(cuerpo, "contrato_id")
                servicio_contratos = ContratoService(db)
                contrato = self._ejecutar(lambda: servicio_contratos.obtener_contrato(contrato_id))
                if contrato is None:
                    raise ErrorApi("El contrato no existe", 404)
                empleado = empleado_o_error(contrato.empleado_id)
                motivo = str(cuerpo.get("motivo") or "terminacion")
                finiquito = self._ejecutar(
                    lambda: servicio_contratos.calcular_liquidacion(empleado.id, motivo))
                destino = str(Path(temporal) / f"liquidacion_{contrato_id}.pdf")
                nombre = f"liquidacion_{contrato_id}.pdf"
                self._ejecutar(lambda: generador.generate_liquidacion(
                    empleado, finiquito.to_dict(), destino, contrato=contrato.numero))

            elif tipo == "excel_empleados":
                exigir_permiso(sesion, "report", "empleados")
                destino, nombre = self._exportar(temporal, "empleados.xlsx",
                                                 servicio_empleados.listar_empleados_activos())

            elif tipo == "excel_incidencias":
                exigir_permiso(sesion, "report", "incidencias")
                destino, nombre = self._exportar(temporal, "incidencias.xlsx",
                                                 IncidenciaService(db).listar_todas())

            elif tipo == "excel_nomina":
                exigir_permiso(sesion, "report", "nomina")
                desde = _fecha(cuerpo, "periodo_inicio")
                hasta = _fecha(cuerpo, "periodo_fin")
                destino, nombre = self._exportar(
                    temporal, "nomina.xlsx", PagoService(db).listar_por_periodo(desde, hasta))

            elif tipo == "excel_estudiantes":
                exigir_permiso(sesion, "report", "estudiantes")
                destino, nombre = self._exportar(temporal, "estudiantes.xlsx",
                                                 AcademicoService(db).listar_estudiantes_activos())

            elif tipo == "excel_contratos":
                exigir_permiso(sesion, "report", "contratos")
                contratos = self._ejecutar(lambda: ContratoService(db).listar_contratos())
                destino = str(Path(temporal) / "contratos.xlsx")
                nombre = "contratos.xlsx"
                from src.utils.exporter import exportar_archivo

                self._ejecutar(lambda: exportar_archivo(
                    serializar(self._filas_contratos(contratos, servicio_empleados)), destino))
            else:
                raise ErrorApi(f"Tipo de archivo desconocido: «{tipo}»", 404)
            return destino, nombre
        finally:
            db.close()

    # Filas con la misma forma que construye la interfaz de escritorio
    @staticmethod
    def _nombre_empleado(servicio, empleado_id: int) -> Any:
        empleado = servicio.obtener_empleado(empleado_id)
        return empleado.nombre_completo if empleado else "Desconocido"

    @classmethod
    def _fila_recibo(cls, pago) -> dict:
        return {
            "nombre_empleado": cls._nombre_empleado_from_pago(pago),
            "cedula": getattr(pago, "cedula_empleado", "") or "",
            "periodo_inicio": pago.periodo_inicio,
            "periodo_fin": pago.periodo_fin,
            "referencia_pago": pago.referencia_pago,
            "salario_base": float(pago.salario_base or 0),
            "bonificaciones": float(pago.bonificaciones or 0),
            "horas_extra": float(pago.horas_extra or 0),
            "aguinaldo": float(pago.aguinaldo or 0),
            "bono_vacacional": float(pago.bono_vacacional or 0),
            "monto_bruto": float(pago.monto_bruto or 0),
            "deduccion_seguro": float(pago.deduccion_seguro or 0),
            "deduccion_pension": float(pago.deduccion_pension or 0),
            "deduccion_impuesto": float(pago.deduccion_impuesto or 0),
            "otras_deducciones": float(pago.otras_deducciones or 0),
            "descuentos": float(pago.descuentos or 0),
            "monto_neto": float(pago.monto_neto or 0),
        }

    @staticmethod
    def _nombre_empleado_from_pago(pago) -> str:
        empleado = getattr(pago, "empleado", None)
        return empleado.nombre_completo if empleado is not None else "Desconocido"

    @classmethod
    def _filas_planilla(cls, pagos, servicio_empleados) -> list[dict]:
        filas = []
        for pago in pagos:
            empleado = servicio_empleados.obtener_empleado(pago.empleado_id)
            filas.append(
                {
                    "nombre_empleado": empleado.nombre_completo if empleado else "Desconocido",
                    "cedula": empleado.cedula if empleado else "",
                    "cargo": empleado.cargo if empleado else "",
                    "salario_base": float(pago.salario_base or 0),
                    "bonificaciones": float(pago.bonificaciones or 0),
                    "horas_extra": float(pago.horas_extra or 0),
                    "aguinaldo": float(pago.aguinaldo or 0),
                    "bono_vacacional": float(pago.bono_vacacional or 0),
                    "deduccion_seguro": float(pago.deduccion_seguro or 0),
                    "deduccion_pension": float(pago.deduccion_pension or 0),
                    "deduccion_impuesto": float(pago.deduccion_impuesto or 0),
                    "otras_deducciones": float(pago.otras_deducciones or 0),
                    "descuentos": float(pago.descuentos or 0),
                    "monto_neto": float(pago.monto_neto or 0),
                    "periodo_inicio": pago.periodo_inicio,
                    "periodo_fin": pago.periodo_fin,
                }
            )
        return filas

    @classmethod
    def _filas_incidencias(cls, incidencias, servicio_empleados) -> list[dict]:
        return [
            {
                "nombre_empleado": cls._nombre_empleado(servicio_empleados, inc.empleado_id),
                "tipo_incidencia": inc.tipo_incidencia,
                "fecha_inicio": inc.fecha_inicio,
                "fecha_fin": inc.fecha_fin,
                "dias_solicitados": inc.dias_solicitados,
                "estado": inc.estado,
                "motivo": inc.motivo or "",
            }
            for inc in incidencias
        ]

    @classmethod
    def _filas_contratos(cls, contratos, servicio_empleados) -> list[dict]:
        filas = []
        for contrato in contratos:
            empleado = servicio_empleados.obtener_empleado(contrato.empleado_id)
            filas.append(
                {
                    "Numero": contrato.numero,
                    "Empleado": empleado.nombre_completo if empleado else contrato.empleado_id,
                    "Cedula": getattr(empleado, "cedula", "") if empleado else "",
                    "Tipo": str(contrato.tipo_valor).capitalize(),
                    "Cargo": contrato.cargo,
                    "Departamento": contrato.departamento or "",
                    "Inicio": str(contrato.fecha_inicio or ""),
                    "Fin": str(contrato.fecha_fin) if contrato.fecha_fin else "Indefinido",
                    "Dias_vigencia": contrato.dias_vigencia,
                    "Salario_pactado": float(contrato.salario_pactado or 0),
                    "Horas_semanales": int(contrato.horas_semanales or 0),
                    "Estado": str(contrato.estado_valor).capitalize(),
                    "Liquidacion": float(contrato.liquidacion_monto or 0),
                }
            )
        return filas

    @classmethod
    def _filas_vencimientos(cls, documentos, servicio_empleados) -> list[dict]:
        filas = []
        for doc in documentos:
            dias = doc.dias_vencimiento
            if doc.activo != 1:
                estado = "Inactivo"
            elif dias is None:
                estado = "Sin vencimiento"
            elif dias < 0:
                estado = "Vencido"
            else:
                estado = "Por vencer"
            filas.append(
                {
                    "nombre_empleado": cls._nombre_empleado(servicio_empleados, doc.empleado_id),
                    "tipo_documento": doc.tipo_documento,
                    "titulo": doc.titulo,
                    "fecha_vencimiento": doc.fecha_vencimiento,
                    "estado": estado,
                }
            )
        return filas

    @staticmethod
    def _exportar(carpeta: str, nombre: str, filas) -> tuple[str, str]:
        """Exporta una lista de modelos a Excel con el exportador del escritorio"""
        from src.utils.exporter import exportar_archivo

        destino = str(Path(carpeta) / nombre)
        exportar_archivo(serializar(list(filas)), destino)
        return destino, nombre

"""
Academico Service
Servicio de lógica de negocio del módulo académico

Gestiona estudiantes, periodos académicos (años escolares), grados y
secciones, y la matrícula de los estudiantes. El cierre de un periodo es
la operación crítica: a partir de ahí las notas quedan bloqueadas (ver
``NotaService``) y solo un administrador puede volver a abrirlo.
"""

import logging
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from src.models import (
    EstadoPeriodoAcademico,
    Estudiante,
    Genero,
    Grado,
    Matricula,
    NivelEducativo,
    PeriodoAcademico,
    RolUsuario,
    TokenSesion,
)
from src.repositories import (
    EstudianteRepository,
    GradoRepository,
    MatriculaRepository,
    PeriodoAcademicoRepository,
    UsuarioRepository,
)
from src.services.token_sesion_service import TokenSesionService
from src.utils.audit_logger import AuditEventType, get_audit_logger
from src.utils.helpers import parse_date, utcnow

logger = logging.getLogger(__name__)

# Campos de texto del estudiante que se actualizan tal cual llegan
_CAMPOS_TEXTO_ESTUDIANTE = (
    "nombres",
    "apellidos",
    "representante",
    "telefono",
    "telefono_representante",
    "email",
    "direccion",
    "observaciones",
)


def _fecha(valor: object) -> date | None:
    """Acepta date o cadena y devuelve date; None si no representa fecha"""
    if valor is None:
        return None
    if isinstance(valor, str):
        return parse_date(valor) if valor.strip() else None
    if isinstance(valor, date):
        return valor
    return None


def _texto(valor: object) -> str | None:
    """Normaliza un texto opcional: vacíos y espacios quedan en None"""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


class AcademicoService:
    """
    Servicio del módulo académico

    Intermedia entre la interfaz y los repositorios con las reglas de
    negocio: unicidad de cédula y de periodos, coherencia de fechas,
    nivel del estudiante frente al grado y una sola matrícula activa por
    año escolar.
    """

    def __init__(self, session: Session):
        self.session = session
        self.estudiantes = EstudianteRepository(session)
        self.periodos = PeriodoAcademicoRepository(session)
        self.grados = GradoRepository(session)
        self.matriculas = MatriculaRepository(session)
        self.tokens = TokenSesionService(session)
        self._usuarios = UsuarioRepository(session)

    # ------------------------------------------------------------------
    # Estudiantes
    # ------------------------------------------------------------------
    def crear_estudiante(self, datos: dict[str, Any]) -> Estudiante:
        """
        Crea un estudiante con validaciones

        Raises:
            ValueError: Si faltan nombres/apellidos, el nivel no es válido
                o la cédula ya está registrada
        """
        nombres = _texto(datos.get("nombres"))
        apellidos = _texto(datos.get("apellidos"))
        if not nombres or not apellidos:
            raise ValueError("Los nombres y apellidos son requeridos")

        cedula = _texto(datos.get("cedula"))
        if cedula and self.estudiantes.get_by_cedula(cedula):
            raise ValueError("Ya existe un estudiante con esta cédula")

        estudiante = Estudiante(
            nombres=nombres,
            apellidos=apellidos,
            cedula=cedula,
            fecha_nacimiento=_fecha(datos.get("fecha_nacimiento")),
            genero=self._genero(datos.get("genero")),
            nivel=self._nivel(datos.get("nivel")),
            representante=_texto(datos.get("representante")),
            telefono=_texto(datos.get("telefono")),
            telefono_representante=_texto(datos.get("telefono_representante")),
            email=_texto(datos.get("email")),
            direccion=_texto(datos.get("direccion")),
            observaciones=_texto(datos.get("observaciones")),
            activo=1,
        )
        return self.estudiantes.create(estudiante)

    def actualizar_estudiante(self, estudiante_id: int, datos: dict[str, Any]) -> Estudiante:
        """
        Actualiza los datos de un estudiante

        Raises:
            ValueError: Si el estudiante no existe, quedaría sin nombre o
                la cédula nueva ya está registrada
        """
        estudiante = self.estudiantes.get_by_id(estudiante_id)
        if not estudiante:
            raise ValueError("Estudiante no encontrado")

        if "cedula" in datos:
            cedula = _texto(datos.get("cedula"))
            if cedula and cedula != estudiante.cedula:
                if self.estudiantes.get_by_cedula(cedula):
                    raise ValueError("Ya existe un estudiante con esta cédula")
            estudiante.cedula = cedula

        nombres = _texto(datos["nombres"]) if "nombres" in datos else estudiante.nombres
        apellidos = _texto(datos["apellidos"]) if "apellidos" in datos else estudiante.apellidos
        if not nombres or not apellidos:
            raise ValueError("Los nombres y apellidos son requeridos")
        estudiante.nombres = nombres
        estudiante.apellidos = apellidos

        if "nivel" in datos:
            estudiante.nivel = self._nivel(datos.get("nivel"))
        if "genero" in datos:
            estudiante.genero = self._genero(datos.get("genero"))
        if "fecha_nacimiento" in datos:
            estudiante.fecha_nacimiento = _fecha(datos.get("fecha_nacimiento"))
        for campo in _CAMPOS_TEXTO_ESTUDIANTE:
            if campo in datos and campo not in ("nombres", "apellidos"):
                setattr(estudiante, campo, _texto(datos.get(campo)))

        return self.estudiantes.update(estudiante)

    def obtener_estudiante(self, estudiante_id: int) -> Estudiante | None:
        """Obtiene un estudiante por ID"""
        return self.estudiantes.get_by_id(estudiante_id)

    def listar_estudiantes(self, skip: int = 0, limit: int | None = None) -> list[Estudiante]:
        """Lista los estudiantes con paginación opcional"""
        return self.estudiantes.get_all(skip, limit)

    def listar_estudiantes_activos(self) -> list[Estudiante]:
        """Lista solo los estudiantes activos"""
        return self.estudiantes.get_activos()

    def buscar_estudiantes(self, termino: str) -> list[Estudiante]:
        """Busca estudiantes por nombre, apellido o cédula"""
        return self.estudiantes.search_estudiantes(termino)

    def listar_estudiantes_por_nivel(self, nivel: str | NivelEducativo) -> list[Estudiante]:
        """Lista los estudiantes activos de un nivel educativo"""
        return self.estudiantes.get_by_nivel(nivel)

    def desactivar_estudiante(self, estudiante_id: int) -> bool:
        """Retira a un estudiante (baja lógica)"""
        return self.estudiantes.desactivar(estudiante_id)

    def activar_estudiante(self, estudiante_id: int) -> bool:
        """Reactiva a un estudiante retirado"""
        return self.estudiantes.activar(estudiante_id)

    def estadisticas(self) -> dict[str, Any]:
        """Resumen del módulo académico para el panel de estadísticas"""
        return {
            "estudiantes": self.estudiantes.count(),
            "estudiantes_activos": self.estudiantes.count_activos(),
            "por_nivel": self.estudiantes.get_estadisticas_por_nivel(),
            "periodos": self.periodos.count(),
            "grados": self.grados.count(),
            "matriculas_activas": self.matriculas.count_activas(),
        }

    # ------------------------------------------------------------------
    # Periodos académicos
    # ------------------------------------------------------------------
    def crear_periodo(self, datos: dict[str, Any]) -> PeriodoAcademico:
        """
        Crea un año escolar (nace abierto)

        Raises:
            ValueError: Si falta o se repite el nombre, o las fechas no
                son coherentes
        """
        nombre = _texto(datos.get("nombre"))
        if not nombre:
            raise ValueError("El nombre del periodo es requerido (ej. 2025-2026)")
        if self.periodos.get_by_nombre(nombre):
            raise ValueError("Ya existe un periodo con ese nombre")

        inicio = _fecha(datos.get("fecha_inicio"))
        fin = _fecha(datos.get("fecha_fin"))
        if inicio and fin and fin < inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio")

        periodo = PeriodoAcademico(
            nombre=nombre,
            fecha_inicio=inicio,
            fecha_fin=fin,
            estado=EstadoPeriodoAcademico.ABIERTO.value,
            observaciones=_texto(datos.get("observaciones")),
        )
        return self.periodos.create(periodo)

    def actualizar_periodo(self, periodo_id: int, datos: dict[str, Any]) -> PeriodoAcademico:
        """
        Actualiza nombre, fechas u observaciones de un periodo

        El estado no se cambia por aquí: se cierra o reabre con las
        operaciones específicas, que exigen token de administrador.
        """
        periodo = self.periodos.get_by_id(periodo_id)
        if not periodo:
            raise ValueError("Periodo no encontrado")
        if "estado" in datos:
            raise ValueError("El estado del periodo se cambia con cerrar/reabrir el periodo")

        if "nombre" in datos:
            nombre = _texto(datos.get("nombre"))
            if not nombre:
                raise ValueError("El nombre del periodo es requerido")
            if nombre != periodo.nombre and self.periodos.get_by_nombre(nombre):
                raise ValueError("Ya existe un periodo con ese nombre")
            periodo.nombre = nombre

        inicio = (
            _fecha(datos.get("fecha_inicio")) if "fecha_inicio" in datos else periodo.fecha_inicio
        )
        fin = _fecha(datos.get("fecha_fin")) if "fecha_fin" in datos else periodo.fecha_fin
        if inicio and fin and fin < inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio")
        periodo.fecha_inicio = inicio
        periodo.fecha_fin = fin

        if "observaciones" in datos:
            periodo.observaciones = _texto(datos.get("observaciones"))

        return self.periodos.update(periodo)

    def obtener_periodo(self, periodo_id: int) -> PeriodoAcademico | None:
        """Obtiene un periodo por ID"""
        return self.periodos.get_by_id(periodo_id)

    def listar_periodos(self, descendente: bool = True) -> list[PeriodoAcademico]:
        """Lista los periodos del más reciente al más antiguo"""
        return self.periodos.get_ordenados(descendente)

    def periodo_en_curso(self) -> PeriodoAcademico | None:
        """Periodo abierto más reciente (el año escolar que se está cursando)"""
        return self.periodos.get_ultimo_abierto()

    def cerrar_periodo(self, periodo_id: int, token: str | None) -> PeriodoAcademico:
        """
        Cierra el año escolar y bloquea sus notas

        Solo un administrador puede cerrar un periodo. A partir del cierre,
        ``NotaService`` rechaza cualquier alta, cambio o borrado de notas y
        los disparadores de SQLite lo impiden incluso por SQL directo.

        Raises:
            ValueError: Si el token no es válido, el solicitante no es
                administrador, el periodo no existe o ya está cerrado
        """
        sesion = self._exigir_token(token)
        if sesion.rol != RolUsuario.ADMIN.value:
            self._audit(
                AuditEventType.SECURITY_PERMISSION_DENIED,
                sesion.username,
                periodo_id,
                {"operacion": "cerrar_periodo", "rol": sesion.rol},
                success=False,
            )
            raise ValueError("Solo un administrador puede cerrar un periodo académico")

        periodo = self.periodos.get_by_id(periodo_id)
        if not periodo:
            raise ValueError("Periodo no encontrado")
        if periodo.esta_cerrado:
            raise ValueError(f"El periodo {periodo.nombre} ya está cerrado")

        periodo.estado = EstadoPeriodoAcademico.CERRADO
        periodo.cerrado_en = utcnow()
        periodo.cerrado_por = sesion.username
        actualizado = self.periodos.update(periodo)
        self._audit(
            AuditEventType.DATA_UPDATE,
            sesion.username,
            periodo.id,
            {"operacion": "cerrar_periodo", "periodo": periodo.nombre},
        )
        return actualizado

    def reabrir_periodo(self, periodo_id: int, token: str | None) -> PeriodoAcademico:
        """
        Reabre un periodo cerrado (solo administrador)

        Reabrir habilita de nuevo la edición de notas; se registra en
        auditoría para que el cambio quede trazado.
        """
        sesion = self._exigir_token(token)
        if sesion.rol != RolUsuario.ADMIN.value:
            self._audit(
                AuditEventType.SECURITY_PERMISSION_DENIED,
                sesion.username,
                periodo_id,
                {"operacion": "reabrir_periodo", "rol": sesion.rol},
                success=False,
            )
            raise ValueError("Solo un administrador puede reabrir un periodo académico")

        periodo = self.periodos.get_by_id(periodo_id)
        if not periodo:
            raise ValueError("Periodo no encontrado")
        if not periodo.esta_cerrado:
            raise ValueError(f"El periodo {periodo.nombre} ya está abierto")

        periodo.estado = EstadoPeriodoAcademico.ABIERTO
        periodo.cerrado_en = None
        periodo.cerrado_por = None
        actualizado = self.periodos.update(periodo)
        self._audit(
            AuditEventType.DATA_UPDATE,
            sesion.username,
            periodo.id,
            {"operacion": "reabrir_periodo", "periodo": periodo.nombre},
        )
        return actualizado

    # ------------------------------------------------------------------
    # Grados y secciones
    # ------------------------------------------------------------------
    def crear_grado(self, datos: dict[str, Any]) -> Grado:
        """
        Crea un grado/sección dentro de un periodo

        Raises:
            ValueError: Si el periodo no existe, falta el nombre, el nivel
                no es válido o ya está creado ese grado y sección
        """
        periodo = self._periodo_de(datos.get("periodo_id"))
        nivel = self._nivel(datos.get("nivel"))
        nombre = _texto(datos.get("nombre"))
        if not nombre:
            raise ValueError("El nombre del grado es requerido (ej. 1er Año)")
        seccion = (_texto(datos.get("seccion")) or "A").upper()

        if self.grados.get_por_nombre(periodo.id, nombre, seccion):
            raise ValueError(f"Ya existe {nombre} {seccion} en el periodo {periodo.nombre}")

        grado = Grado(
            periodo_id=periodo.id,
            nivel=nivel,
            nombre=nombre,
            seccion=seccion,
            profesor_id=self._profesor_valido(datos.get("profesor_id")),
            observaciones=_texto(datos.get("observaciones")),
        )
        return self.grados.create(grado)

    def actualizar_grado(self, grado_id: int, datos: dict[str, Any]) -> Grado:
        """Actualiza los datos de un grado/sección"""
        grado = self.grados.get_by_id(grado_id)
        if not grado:
            raise ValueError("Grado no encontrado")

        if "nombre" in datos or "seccion" in datos:
            nombre = _texto(datos["nombre"]) if "nombre" in datos else grado.nombre
            seccion = (
                (_texto(datos["seccion"]) or "A").upper() if "seccion" in datos else grado.seccion
            )
            if not nombre:
                raise ValueError("El nombre del grado es requerido")
            existente = self.grados.get_por_nombre(grado.periodo_id, nombre, seccion)
            if existente is not None and existente.id != grado.id:
                raise ValueError(f"Ya existe {nombre} {seccion} en ese periodo académico")
            grado.nombre = nombre
            grado.seccion = seccion

        if "nivel" in datos:
            grado.nivel = self._nivel(datos.get("nivel"))
        if "profesor_id" in datos:
            grado.profesor_id = self._profesor_valido(datos.get("profesor_id"))
        if "observaciones" in datos:
            grado.observaciones = _texto(datos.get("observaciones"))

        return self.grados.update(grado)

    def obtener_grado(self, grado_id: int) -> Grado | None:
        """Obtiene un grado por ID"""
        return self.grados.get_by_id(grado_id)

    def listar_grados(self, periodo_id: int | None = None) -> list[Grado]:
        """Lista los grados de un periodo (o todos)"""
        if periodo_id is None:
            return self.grados.get_all()
        return self.grados.get_by_periodo(periodo_id)

    def listar_grados_de_profesor(
        self, profesor_id: int, periodo_id: int | None = None
    ) -> list[Grado]:
        """Lista los grados asignados a un docente"""
        return self.grados.get_by_profesor(profesor_id, periodo_id)

    def asignar_profesor(self, grado_id: int, profesor_id: int | None) -> Grado:
        """
        Asigna (o quita) el docente responsable de un grado

        El docente asignado es el único profesor autorizado a registrar y
        modificar las notas de ese grado.
        """
        grado = self.grados.get_by_id(grado_id)
        if not grado:
            raise ValueError("Grado no encontrado")
        grado.profesor_id = self._profesor_valido(profesor_id)
        return self.grados.update(grado)

    # ------------------------------------------------------------------
    # Matrículas
    # ------------------------------------------------------------------
    def matricular(self, estudiante_id: int, grado_id: int) -> Matricula:
        """
        Matricula a un estudiante en un grado

        Reglas: el estudiante debe estar activo, su nivel debe coincidir
        con el del grado y no puede tener otra matrícula activa en el
        mismo año escolar.

        Raises:
            ValueError: Si algo de lo anterior no se cumple
        """
        estudiante = self.estudiantes.get_by_id(estudiante_id)
        if not estudiante:
            raise ValueError("Estudiante no encontrado")
        if not estudiante.activo:
            raise ValueError("El estudiante está retirado; reactívelo antes de matricularlo")

        grado = self.grados.get_by_id(grado_id)
        if not grado:
            raise ValueError("Grado no encontrado")
        if estudiante.nivel_valor != grado.nivel_valor:
            raise ValueError(
                f"El estudiante es del nivel {estudiante.nivel_valor} y el grado es "
                f"de {grado.nivel_valor}"
            )

        existente = self.matriculas.get_activa_en_periodo(estudiante.id, grado.periodo_id)
        if existente is not None:
            if existente.grado_id == grado.id:
                raise ValueError("El estudiante ya está matriculado en este grado")
            raise ValueError(
                f"El estudiante ya está matriculado en {existente.grado.nombre_completo} "
                "en este año escolar"
            )

        matricula = Matricula(
            estudiante_id=estudiante.id,
            grado_id=grado.id,
            activa=1,
        )
        return self.matriculas.create(matricula)

    def retirar_matricula(self, matricula_id: int) -> bool:
        """Retira al estudiante del grado (la matrícula queda en el historial)"""
        return self.matriculas.desactivar(matricula_id)

    def listar_matriculas_de_grado(self, grado_id: int) -> list[Matricula]:
        """Lista los estudiantes activos de un grado"""
        return self.matriculas.get_by_grado(grado_id)

    def listar_matriculas_de_estudiante(self, estudiante_id: int) -> list[Matricula]:
        """Lista el historial de matrículas de un estudiante"""
        return self.matriculas.get_by_estudiante(estudiante_id)

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    @staticmethod
    def _nivel(valor: object) -> NivelEducativo:
        """Normaliza el nivel educativo o falla con un mensaje claro"""
        if valor is None or str(valor).strip() == "":
            raise ValueError("El nivel educativo es requerido ('inicial' o 'secundaria')")
        try:
            return NivelEducativo.coerce(valor)
        except ValueError:
            raise ValueError("Nivel educativo inválido: use 'inicial' o 'secundaria'") from None

    @staticmethod
    def _genero(valor: object) -> Genero | None:
        """Normaliza el género opcional"""
        if valor is None or str(valor).strip() == "":
            return None
        try:
            return Genero.coerce(valor)
        except ValueError:
            raise ValueError("Género inválido") from None

    def _periodo_de(self, valor: object) -> PeriodoAcademico:
        """Resuelve el periodo indicado o falla con un mensaje claro"""
        try:
            periodo_id = int(str(valor))
        except (TypeError, ValueError):
            raise ValueError("El periodo académico es requerido") from None
        periodo = self.periodos.get_by_id(periodo_id)
        if not periodo:
            raise ValueError("Periodo académico no encontrado")
        return periodo

    def _profesor_valido(self, valor: object) -> int | None:
        """Valida que el usuario exista y esté activo; None lo desasigna"""
        if valor is None or str(valor).strip() == "":
            return None
        try:
            profesor_id = int(str(valor))
        except (TypeError, ValueError):
            raise ValueError("El profesor indicado no es válido") from None
        profesor = self._usuarios.get_by_id(profesor_id)
        if profesor is None or not profesor.activo:
            raise ValueError("El profesor indicado no existe o está inactivo")
        return profesor_id

    def _exigir_token(self, token: str | None) -> TokenSesion:
        """Valida el token de sesión o falla"""
        sesion = self.tokens.validar(token)
        if sesion is None:
            raise ValueError("Token de sesión inválido, expirado o revocado")
        return sesion

    def _audit(
        self,
        event_type: AuditEventType,
        usuario: str | None,
        entity_id: int | None = None,
        details: dict | None = None,
        success: bool = True,
    ) -> None:
        """Registra un evento de auditoría sin romper la operación"""
        try:
            audit = get_audit_logger()
            if audit:
                audit.log_event(
                    event_type=event_type,
                    entity_type="academico",
                    entity_id=entity_id,
                    user=usuario or "system",
                    details=details or {},
                    success=success,
                )
        except Exception:
            logger.warning("%s: operación auxiliar falló (se continúa)", "_audit", exc_info=True)

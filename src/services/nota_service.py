"""
Nota Service
Servicio de lógica de negocio de las calificaciones finales

Concentra las tres reglas del módulo académico:
1. Solo escriben las cuentas con token de sesión válido y autorizadas:
   la administración (admin/gestor) o el docente asignado al grado.
2. Las notas de un periodo cerrado son inmutables; cualquier alta, cambio
   o borrado se rechaza con un mensaje claro.
3. El guardado masivo de fin de año se hace en una sola transacción
   (executemany + un único commit) sobre el pool de conexiones.
"""

import logging
from typing import Any

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import Estudiante, Grado, NotaFinal, TokenSesion
from src.repositories import (
    ConfiguracionRepository,
    EstudianteRepository,
    GradoRepository,
    MatriculaRepository,
    NotaFinalRepository,
    PeriodoAcademicoRepository,
)
from src.services.token_sesion_service import TokenSesionService
from src.utils.audit_logger import AuditEventType, get_audit_logger
from src.utils.helpers import utcnow

logger = logging.getLogger(__name__)

# Escala de calificaciones por defecto (configurable en Configuración)
ESCALA_MINIMA_POR_DEFECTO = 0.0
ESCALA_MAXIMA_POR_DEFECTO = 20.0
NOTA_APROBATORIA_POR_DEFECTO = 10.0


def _texto(valor: object) -> str | None:
    """Normaliza un texto opcional: vacíos y espacios quedan en None"""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


class NotaService:
    """
    Servicio de notas finales

    Intermedia entre la interfaz y el repositorio de notas aplicando las
    reglas de autorización, el bloqueo por cierre del periodo y el
    guardado por lotes.
    """

    def __init__(self, session: Session):
        self.session = session
        self.repository = NotaFinalRepository(session)
        self.grados = GradoRepository(session)
        self.estudiantes = EstudianteRepository(session)
        self.matriculas = MatriculaRepository(session)
        self.periodos = PeriodoAcademicoRepository(session)
        self.tokens = TokenSesionService(session)

    # ------------------------------------------------------------------
    # Escala de calificaciones
    # ------------------------------------------------------------------
    def _config_float(self, clave: str, por_defecto: float) -> float:
        """Lee un parámetro numérico de configuración sin romperse"""
        try:
            valor = ConfiguracionRepository(self.session).get_valor(clave, por_defecto)
            return float(valor)
        except (SQLAlchemyError, TypeError, ValueError):
            logger.debug("No se pudo leer la configuración %s", clave, exc_info=True)
            return por_defecto

    def escala(self) -> tuple[float, float]:
        """Rango configurado de calificaciones (mínimo, máximo)"""
        minima = self._config_float("nota_minima", ESCALA_MINIMA_POR_DEFECTO)
        maxima = self._config_float("nota_maxima", ESCALA_MAXIMA_POR_DEFECTO)
        if maxima <= minima:
            maxima = minima + 1.0
        return minima, maxima

    def nota_aprobatoria(self) -> float:
        """Calificación mínima aprobatoria usada en boletines y actas"""
        return self._config_float("nota_aprobatoria", NOTA_APROBATORIA_POR_DEFECTO)

    # ------------------------------------------------------------------
    # Escritura de notas
    # ------------------------------------------------------------------
    def registrar(self, datos: dict[str, Any], token: str | None) -> NotaFinal:
        """
        Registra la nota final de un estudiante en una materia

        Raises:
            ValueError: Si el token no autoriza, el periodo está cerrado,
                el estudiante no está matriculado o la nota se repite
        """
        grado = self._grado_de(datos.get("grado_id"))
        sesion = self._autorizar(token, grado)
        self._exigir_periodo_abierto(grado)
        estudiante = self._estudiante_de(datos.get("estudiante_id"))
        self._exigir_matricula(estudiante, grado)

        materia = self._materia(datos.get("materia"))
        calificacion = self._calificacion(datos.get("calificacion"))
        if self.repository.get_una(estudiante.id, grado.id, materia) is not None:
            raise ValueError(
                "Ya existe una nota de esa materia para el estudiante: edítela en su lugar"
            )

        nota = NotaFinal(
            estudiante_id=estudiante.id,
            grado_id=grado.id,
            materia=materia,
            calificacion=calificacion,
            registrado_por=sesion.username,
            observaciones=_texto(datos.get("observaciones")),
        )
        return self.repository.create(nota)

    def actualizar(
        self,
        nota_id: int,
        calificacion: object,
        token: str | None,
        observaciones: object = None,
    ) -> NotaFinal:
        """
        Corrige la calificación de una nota existente

        Raises:
            ValueError: Si la nota no existe, el token no autoriza o el
                periodo ya está cerrado
        """
        nota = self.repository.get_by_id(nota_id)
        if not nota:
            raise ValueError("Nota no encontrada")
        grado = self._grado_de(nota.grado_id)
        sesion = self._autorizar(token, grado)
        self._exigir_periodo_abierto(grado)

        nota.calificacion = self._calificacion(calificacion)
        nota.registrado_por = sesion.username
        if observaciones is not None:
            nota.observaciones = _texto(observaciones)
        return self.repository.update(nota)

    def eliminar(self, nota_id: int, token: str | None) -> bool:
        """Elimina una nota (solo con autorización y periodo abierto)"""
        nota = self.repository.get_by_id(nota_id)
        if not nota:
            raise ValueError("Nota no encontrada")
        grado = self._grado_de(nota.grado_id)
        self._autorizar(token, grado)
        self._exigir_periodo_abierto(grado)
        return self.repository.delete(nota.id)

    def guardar_lote(self, filas: list[dict[str, Any]], token: str | None) -> int:
        """
        Guarda un lote de notas en una sola transacción

        Es el camino de fin de año: se validan todas las filas primero
        (autorización, periodo abierto y matrícula) y después viajan juntas
        al motor con executemany y un único commit. Si una fila falla, no
        se guarda ninguna, de modo que el acta nunca queda a medias.

        Returns:
            int: Cantidad de notas guardadas

        Raises:
            ValueError: Si el lote está vacío o alguna fila no cumple las
                reglas (el error indica qué fila y por qué)
        """
        if not filas:
            raise ValueError("No hay notas para guardar")
        sesion = self._exigir_token(token)

        preparadas: list[dict[str, Any]] = []
        grados: dict[int, Grado] = {}
        momento = utcnow()
        for numero, fila in enumerate(filas, start=1):
            try:
                if not isinstance(fila, dict):
                    raise ValueError("cada nota debe ser un diccionario")
                grado = self._grado_de(fila.get("grado_id"), cache=grados)
                self._autorizar_sesion(sesion, grado)
                self._exigir_periodo_abierto(grado)
                estudiante = self._estudiante_de(fila.get("estudiante_id"))
                self._exigir_matricula(estudiante, grado)
                preparadas.append(
                    {
                        "estudiante_id": estudiante.id,
                        "grado_id": grado.id,
                        "materia": self._materia(fila.get("materia")),
                        "calificacion": self._calificacion(fila.get("calificacion")),
                        "registrado_por": sesion.username,
                        "observaciones": _texto(fila.get("observaciones")),
                        "created_at": momento,
                        "updated_at": momento,
                    }
                )
            except ValueError as e:
                raise ValueError(f"Fila {numero}: {e}") from None

        try:
            insertadas = self.repository.insertar_lote(preparadas)
        except IntegrityError as e:
            raise ValueError(
                "El lote contiene notas repetidas (mismo estudiante, grado y materia)"
            ) from e
        self._audit_lote(sesion.username, insertadas)
        return insertadas

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def obtener_nota(self, nota_id: int) -> NotaFinal | None:
        """Obtiene una nota por ID"""
        return self.repository.get_by_id(nota_id)

    def listar_notas_de_grado(self, grado_id: int) -> list[NotaFinal]:
        """Lista las notas de un grado"""
        return self.repository.get_by_grado(grado_id)

    def listar_notas_de_estudiante(
        self, estudiante_id: int, periodo_id: int | None = None
    ) -> list[NotaFinal]:
        """Lista las notas de un estudiante (opcionalmente en un periodo)"""
        return self.repository.get_by_estudiante(estudiante_id, periodo_id)

    def consolidado_periodo(self, periodo_id: int) -> list[dict[str, Any]]:
        """
        Notas consolidadas de un periodo, listas para reportes

        Incluye estudiante y grado en cada fila para que los boletines y
        actas no vuelvan a consultar la base de datos.
        """
        return self.repository.consolidado_periodo(periodo_id)

    def promedio(self, estudiante_id: int, grado_id: int) -> float | None:
        """Promedio del estudiante en un grado (None si no tiene notas)"""
        notas = [
            nota
            for nota in self.repository.get_by_estudiante(estudiante_id)
            if nota.grado_id == grado_id
        ]
        if not notas:
            return None
        return round(sum(float(nota.calificacion) for nota in notas) / len(notas), 2)

    # ------------------------------------------------------------------
    # Datos para reportes PDF
    # ------------------------------------------------------------------
    def datos_boletin(self, estudiante_id: int, periodo_id: int) -> dict[str, Any]:
        """
        Datos del boletín de un estudiante en un periodo

        Raises:
            ValueError: Si el estudiante o el periodo no existen
        """
        estudiante = self._estudiante_de(estudiante_id)
        periodo = self.periodos.get_by_id(periodo_id)
        if periodo is None:
            raise ValueError("Periodo académico no encontrado")

        notas = self.repository.get_by_estudiante(estudiante_id, periodo_id)
        matricula = self.matriculas.get_activa_en_periodo(estudiante_id, periodo_id)
        grado: Grado | None = None
        if matricula is not None:
            grado = matricula.grado
        elif notas:
            grado = notas[0].grado

        filas: list[dict[str, Any]] = [
            {"materia": nota.materia, "calificacion": float(nota.calificacion)} for nota in notas
        ]
        promedio = (
            round(sum(fila["calificacion"] for fila in filas) / len(filas), 2) if filas else None
        )
        minima, maxima = self.escala()
        return {
            "estudiante": {
                "id": estudiante.id,
                "nombre": estudiante.nombre_completo,
                "cedula": estudiante.cedula,
                "nivel": estudiante.nivel_valor,
                "representante": estudiante.representante,
            },
            "periodo": {
                "id": periodo.id,
                "nombre": periodo.nombre,
                "estado": periodo.estado_valor,
                "esta_cerrado": periodo.esta_cerrado,
            },
            "grado": (
                {
                    "id": grado.id,
                    "nombre": grado.nombre_completo,
                    "seccion": grado.seccion,
                    "nivel": grado.nivel_valor,
                }
                if grado is not None
                else None
            ),
            "notas": filas,
            "promedio": promedio,
            "nota_minima": minima,
            "nota_maxima": maxima,
            "nota_aprobatoria": self.nota_aprobatoria(),
        }

    def datos_acta(self, grado_id: int) -> dict[str, Any]:
        """
        Datos del acta final de un grado

        Incluye a todos los estudiantes matriculados (aunque aún no tengan
        notas) y una columna por materia con la calificación final.
        """
        grado = self._grado_de(grado_id)
        consolidado = [
            fila
            for fila in self.repository.consolidado_periodo(grado.periodo_id)
            if fila["grado_id"] == grado.id
        ]
        materias = sorted({fila["materia"] for fila in consolidado})

        registros: dict[int, dict[str, Any]] = {}
        for matricula in self.matriculas.get_by_grado(grado.id):
            estudiante = matricula.estudiante
            registros[estudiante.id] = {
                "estudiante_id": estudiante.id,
                "estudiante": estudiante.nombre_completo,
                "cedula": estudiante.cedula,
                "notas": {},
                "promedio": None,
            }
        for fila in consolidado:
            registro = registros.setdefault(
                int(fila["estudiante_id"]),
                {
                    "estudiante_id": fila["estudiante_id"],
                    "estudiante": fila["estudiante"],
                    "cedula": fila["cedula"],
                    "notas": {},
                    "promedio": None,
                },
            )
            registro["notas"][fila["materia"]] = fila["calificacion"]

        for registro in registros.values():
            valores = list(registro["notas"].values())
            if valores:
                registro["promedio"] = round(sum(valores) / len(valores), 2)

        profesor = None
        if grado.profesor is not None:
            profesor = grado.profesor.nombre_completo or grado.profesor.username
        minima, maxima = self.escala()
        return {
            "periodo": {
                "id": grado.periodo.id,
                "nombre": grado.periodo.nombre,
                "estado": grado.periodo.estado_valor,
                "esta_cerrado": grado.periodo.esta_cerrado,
            },
            "grado": {
                "id": grado.id,
                "nombre": grado.nombre_completo,
                "nivel": grado.nivel_valor,
            },
            "materias": materias,
            "filas": [registros[clave] for clave in sorted(registros)],
            "profesor": profesor,
            "nota_minima": minima,
            "nota_maxima": maxima,
            "nota_aprobatoria": self.nota_aprobatoria(),
        }

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    def _calificacion(self, valor: object) -> float:
        """Valida y normaliza una calificación dentro de la escala"""
        if valor is None or str(valor).strip() == "":
            raise ValueError("la calificación es requerida")
        try:
            calificacion = float(str(valor).replace(",", "."))
        except (TypeError, ValueError):
            raise ValueError("la calificación debe ser un número") from None
        minima, maxima = self.escala()
        if calificacion < minima or calificacion > maxima:
            raise ValueError(f"la calificación debe estar entre {minima:g} y {maxima:g}")
        return round(calificacion, 2)

    def _materia(self, valor: object) -> str:
        """Valida el nombre de la materia"""
        materia = str(valor or "").strip()
        if not materia:
            raise ValueError("la materia es requerida")
        if len(materia) > 100:
            raise ValueError("el nombre de la materia no puede superar 100 caracteres")
        return materia

    def _grado_de(self, valor: object, cache: dict[int, Grado] | None = None) -> Grado:
        """Resuelve el grado indicado o falla con un mensaje claro"""
        try:
            grado_id = int(str(valor))
        except (TypeError, ValueError):
            raise ValueError("el grado es requerido") from None
        if cache is not None and grado_id in cache:
            return cache[grado_id]
        grado = self.grados.get_by_id(grado_id)
        if grado is None:
            raise ValueError("grado no encontrado")
        if cache is not None:
            cache[grado_id] = grado
        return grado

    def _estudiante_de(self, valor: object) -> Estudiante:
        """Resuelve el estudiante indicado o falla con un mensaje claro"""
        try:
            estudiante_id = int(str(valor))
        except (TypeError, ValueError):
            raise ValueError("el estudiante es requerido") from None
        estudiante = self.estudiantes.get_by_id(estudiante_id)
        if estudiante is None:
            raise ValueError("estudiante no encontrado")
        return estudiante

    def _exigir_matricula(self, estudiante: Estudiante, grado: Grado) -> None:
        """El estudiante debe estar matriculado en el grado del periodo"""
        matricula = self.matriculas.get_activa_en_periodo(estudiante.id, grado.periodo_id)
        if matricula is None or matricula.grado_id != grado.id:
            raise ValueError("el estudiante no está matriculado en el grado indicado")

    def _exigir_periodo_abierto(self, grado: Grado) -> None:
        """Bloquea cualquier escritura sobre un periodo cerrado"""
        periodo = grado.periodo
        if periodo is None:
            raise ValueError("el grado no tiene un periodo académico asociado")
        if periodo.esta_cerrado:
            raise ValueError(f"el periodo {periodo.nombre} está cerrado: las notas son inmutables")

    def _exigir_token(self, token: str | None) -> TokenSesion:
        """Valida el token de sesión o falla"""
        sesion = self.tokens.validar(token)
        if sesion is None:
            raise ValueError("token de sesión inválido, expirado o revocado")
        return sesion

    def _autorizar(self, token: str | None, grado: Grado) -> TokenSesion:
        """Valida el token y que pueda escribir en el grado"""
        sesion = self._exigir_token(token)
        self._autorizar_sesion(sesion, grado)
        return sesion

    def _autorizar_sesion(self, sesion: TokenSesion, grado: Grado) -> None:
        """Aplica la regla de autorización sobre un token ya validado"""
        if self.tokens.puede_escribir(sesion, grado):
            return
        self._audit(
            AuditEventType.SECURITY_PERMISSION_DENIED,
            sesion.username,
            grado.id,
            {
                "operacion": "escribir_nota",
                "grado": grado.nombre_completo,
                "rol": sesion.rol,
            },
            success=False,
        )
        raise ValueError(
            "solo la administración o el profesor asignado al grado pueden "
            "registrar o modificar sus notas"
        )

    def _audit_lote(self, usuario: str | None, cantidad: int) -> None:
        """Registra en auditoría el guardado masivo (el repositorio no lo ve)"""
        try:
            audit = get_audit_logger()
            if audit:
                audit.log_data_operation(
                    operation="create",
                    entity_type="NotaFinal",
                    data={"cantidad": cantidad, "usuario": usuario, "lote": True},
                )
        except Exception:
            logger.warning(
                "%s: operación auxiliar falló (se continúa)",
                "_audit_lote",
                exc_info=True,
            )

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
                    entity_type="nota_final",
                    entity_id=entity_id,
                    user=usuario or "system",
                    details=details or {},
                    success=success,
                )
        except Exception:
            logger.warning("%s: operación auxiliar falló (se continúa)", "_audit", exc_info=True)

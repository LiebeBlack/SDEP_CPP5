"""
Asistencia Service
Servicio de lógica de negocio para el control de asistencia

Registra la jornada diaria de cada empleado, calcula tardanzas y horas
extra contra el horario asignado, y entrega los totales que consume el
motor de nómina. También alimenta las alertas de ausentismo.
"""

import logging
from datetime import date, timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import Asistencia, Empleado, TipoAsistencia, TipoJornada
from src.nomina.tipos import CERO, HorasExtra, a_decimal
from src.repositories import (
    AsistenciaRepository,
    ConfiguracionRepository,
    EmpleadoRepository,
    HorarioRepository,
    IncidenciaRepository,
)
from src.utils.audit_logger import AuditEventType, get_audit_logger
from src.utils.jornada import (
    DIAS_DESCANSO_POR_DEFECTO,
    calcular_horas_trabajadas,
    calcular_minutos_tardanza,
    clasificar_horas_extra,
    es_feriado,
    es_fin_de_semana,
    parsear_hora,
)

logger = logging.getLogger(__name__)


class AsistenciaService:
    """
    Servicio de control de asistencia

    Traduce las marcas de entrada y salida a horas trabajadas, tardanzas
    y horas extra clasificadas, aplicando el horario del empleado y los
    parámetros configurados (tolerancia, días de descanso y feriados).
    """

    def __init__(self, session: Session):
        self.session = session
        self.repository = AsistenciaRepository(session)
        self.horario_repository = HorarioRepository(session)
        self.empleado_repository = EmpleadoRepository(session)
        self.incidencia_repository = IncidenciaRepository(session)
        self.config_repository = ConfiguracionRepository(session)

    # ------------------------------------------------------------------
    # Parámetros de configuración
    # ------------------------------------------------------------------
    def _valor(self, clave: str, por_defecto):
        """Lee un parámetro de configuración sin romperse si falta"""
        try:
            return self.config_repository.get_valor(clave, por_defecto)
        except (SQLAlchemyError, ValueError):
            logger.debug("No se pudo leer la configuración %s, se usa el valor por defecto", clave)
            return por_defecto

    def dias_descanso(self) -> tuple[int, ...]:
        """Días de la semana considerados de descanso"""
        valor = self._valor("dias_descanso", list(DIAS_DESCANSO_POR_DEFECTO))
        if isinstance(valor, str):
            return DIAS_DESCANSO_POR_DEFECTO
        if isinstance(valor, (list, tuple, set)):
            try:
                return tuple(sorted({int(dia) for dia in valor if 0 <= int(dia) <= 6}))
            except (TypeError, ValueError):
                return DIAS_DESCANSO_POR_DEFECTO
        return DIAS_DESCANSO_POR_DEFECTO

    def feriados(self) -> list[str]:
        """Fechas marcadas como feriado"""
        valor = self._valor("feriados", [])
        if isinstance(valor, (list, tuple)):
            return [str(fecha)[:10] for fecha in valor]
        return []

    def _es_dia_no_laborable(self, fecha: date) -> tuple[bool, bool]:
        """Indica (es_feriado, es_descanso) para una fecha"""
        return (
            es_feriado(fecha, self.feriados()),
            es_fin_de_semana(fecha, self.dias_descanso()),
        )

    # ------------------------------------------------------------------
    # Registro de jornadas
    # ------------------------------------------------------------------
    def registrar_jornada(
        self,
        empleado_id: int,
        fecha: date,
        hora_entrada: object = None,
        hora_salida: object = None,
        tipo: str | None = None,
        observaciones: str | None = None,
        registrado_por: str | None = None,
        justificada: bool = False,
        incidencia_id: int | None = None,
    ) -> Asistencia:
        """
        Registra la jornada de un empleado en una fecha

        Calcula horas trabajadas, tardanza y horas extra contra el
        horario del día. Si ya existe un registro para esa fecha se
        actualiza en lugar de duplicarlo.

        Args:
            empleado_id: Empleado de la jornada
            fecha: Día del registro
            hora_entrada: Hora real de entrada (time o texto "HH:MM")
            hora_salida: Hora real de salida
            tipo: Tipo explícito; si no se entrega se deduce de las horas
            observaciones: Notas del registro
            registrado_por: Usuario que captura
            justificada: Marca la ausencia como justificada
            incidencia_id: Incidencia que respalda la ausencia

        Raises:
            ValueError: Si el empleado no existe o la fecha es inválida
        """
        empleado = self.empleado_repository.get_by_id(empleado_id)
        if not empleado:
            raise ValueError("Empleado no encontrado")
        if not isinstance(fecha, date):
            raise ValueError("La fecha del registro es requerida")

        entrada = parsear_hora(hora_entrada)
        salida = parsear_hora(hora_salida)
        horario = self.horario_repository.get_dia(empleado_id, fecha.weekday())
        es_dia_feriado, es_descanso = self._es_dia_no_laborable(fecha)

        descanso = int(horario.descanso_minutos) if horario else 0
        tolerancia = int(
            horario.tolerancia_minutos
            if horario
            else self._valor("tolerancia_asistencia_minutos", 10)
        )
        horas_trabajadas = calcular_horas_trabajadas(entrada, salida, descanso)

        if horario is not None:
            minutos_tardanza = calcular_minutos_tardanza(
                entrada, horario.hora_inicio, tolerancia
            )
            horas_previstas = a_decimal(horario.horas_jornada)
            tipo_jornada = horario.tipo_jornada
        else:
            entrada_prevista = parsear_hora(self._valor("hora_entrada_default", "07:00"))
            salida_prevista = parsear_hora(self._valor("hora_salida_default", "15:00"))
            minutos_tardanza = (
                0
                if (es_dia_feriado or es_descanso)
                else calcular_minutos_tardanza(entrada, entrada_prevista, tolerancia)
            )
            # En feriado o día de descanso no hay jornada prevista que
            # cumplir: todo lo trabajado se paga como hora extra feriada.
            if es_dia_feriado or es_descanso:
                horas_previstas = CERO
            else:
                horas_previstas = (
                    calcular_horas_trabajadas(entrada_prevista, salida_prevista, 0)
                    if (entrada_prevista and salida_prevista)
                    else a_decimal(self._valor("horas_jornada_diaria", 8))
                )
            tipo_jornada = TipoJornada.DIURNA

        horas_extra = clasificar_horas_extra(
            horas_trabajadas,
            horas_previstas,
            tipo_jornada=tipo_jornada,
            dia_feriado=es_dia_feriado and horas_trabajadas > 0,
            dia_descanso=es_descanso and horas_trabajadas > 0,
        )

        tipo_final = (
            TipoAsistencia.coerce(tipo)
            if tipo
            else self._tipo_automatico(
                horas_trabajadas, minutos_tardanza, es_dia_feriado
            )
        )

        registro = self.repository.get_registro(empleado_id, fecha)
        if registro is None:
            registro = Asistencia(empleado_id=empleado_id, fecha=fecha)
            nuevo = True
        else:
            nuevo = False

        registro.tipo = tipo_final
        registro.hora_entrada = entrada
        registro.hora_salida = salida
        registro.horas_trabajadas = horas_trabajadas
        registro.minutos_tardanza = minutos_tardanza
        registro.horas_extra_diurnas = horas_extra.diurnas
        registro.horas_extra_nocturnas = horas_extra.nocturnas
        registro.horas_extra_feriadas = horas_extra.feriadas
        registro.justificada = 1 if justificada else 0
        registro.incidencia_id = incidencia_id
        registro.registrado_por = registrado_por
        registro.observaciones = observaciones
        if nuevo:
            registro = self.repository.create(registro)
        else:
            registro = self.repository.update(registro)

        self._auditar(registro, "registrar_jornada", empleado)
        return registro

    def _tipo_automatico(
        self, horas_trabajadas, minutos_tardanza: int, dia_feriado: bool
    ) -> TipoAsistencia:
        """Tipo de asistencia deducido de las horas registradas"""
        if dia_feriado and horas_trabajadas > 0:
            return TipoAsistencia.FERIADO
        if horas_trabajadas <= 0:
            return TipoAsistencia.AUSENTE
        if minutos_tardanza > 0:
            return TipoAsistencia.TARDANZA
        return TipoAsistencia.PRESENTE

    def registrar_ausencia(
        self,
        empleado_id: int,
        fecha: date,
        tipo: str = TipoAsistencia.AUSENTE.value,
        justificada: bool = False,
        incidencia_id: int | None = None,
        observaciones: str | None = None,
        registrado_por: str | None = None,
    ) -> Asistencia:
        """Registra una ausencia, permiso o vacaciones sin marcas de hora"""
        return self.registrar_jornada(
            empleado_id=empleado_id,
            fecha=fecha,
            hora_entrada=None,
            hora_salida=None,
            tipo=tipo,
            observaciones=observaciones,
            registrado_por=registrado_por,
            justificada=justificada,
            incidencia_id=incidencia_id,
        )

    def actualizar_asistencia(self, asistencia_id: int, datos: dict) -> Asistencia:
        """
        Actualiza un registro existente recalculoando los derivados

        Cualquier cambio en las horas o el tipo obliga a recalcular
        tardanzas y horas extra, que es lo que se hace aquí.
        """
        registro = self.repository.get_by_id(asistencia_id)
        if not registro:
            raise ValueError("Registro de asistencia no encontrado")

        entrada = parsear_hora(datos.get("hora_entrada"), registro.hora_entrada)
        salida = parsear_hora(datos.get("hora_salida"), registro.hora_salida)
        horario = self.horario_repository.get_dia(registro.empleado_id, registro.fecha.weekday())
        descanso = int(horario.descanso_minutos) if horario else 0
        tolerancia = int(horario.tolerancia_minutos) if horario else 10

        registro.hora_entrada = entrada
        registro.hora_salida = salida
        registro.horas_trabajadas = calcular_horas_trabajadas(entrada, salida, descanso)
        if horario is not None and entrada is not None:
            registro.minutos_tardanza = calcular_minutos_tardanza(
                entrada, horario.hora_inicio, tolerancia
            )

        # El tipo se normaliza al enum; el resto de campos editables son
        # texto, entero o clave foránea y se copian tal cual.
        if datos.get("tipo") is not None:
            registro.tipo = TipoAsistencia.coerce(datos["tipo"])
        else:
            registro.tipo = self._tipo_automatico(
                registro.horas_trabajadas,
                int(registro.minutos_tardanza or 0),
                self._es_dia_no_laborable(registro.fecha)[0],
            )
        for campo in ("observaciones", "incidencia_id"):
            if campo in datos and datos[campo] is not None:
                setattr(registro, campo, datos[campo])
        if datos.get("justificada") is not None:
            registro.justificada = 1 if datos["justificada"] else 0

        if horario is not None:
            horas_extra = clasificar_horas_extra(
                a_decimal(registro.horas_trabajadas),
                a_decimal(horario.horas_jornada),
                tipo_jornada=horario.tipo_jornada,
                dia_feriado=self._es_dia_no_laborable(registro.fecha)[0],
                dia_descanso=self._es_dia_no_laborable(registro.fecha)[1],
            )
            registro.horas_extra_diurnas = horas_extra.diurnas
            registro.horas_extra_nocturnas = horas_extra.nocturnas
            registro.horas_extra_feriadas = horas_extra.feriadas

        actualizado = self.repository.update(registro)
        self._auditar(actualizado, "actualizar_asistencia")
        return actualizado

    def eliminar_asistencia(self, asistencia_id: int) -> bool:
        """Elimina un registro de asistencia"""
        return self.repository.delete(asistencia_id)

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def obtener_asistencia(self, asistencia_id: int) -> Asistencia | None:
        return self.repository.get_by_id(asistencia_id)

    def listar_por_empleado(
        self, empleado_id: int, desde: date | None = None, hasta: date | None = None
    ) -> list[Asistencia]:
        return self.repository.get_by_empleado(empleado_id, desde, hasta)

    def listar_por_periodo(self, desde: date, hasta: date) -> list[Asistencia]:
        return self.repository.get_by_periodo(desde, hasta)

    def listar_por_fecha(self, fecha: date) -> list[Asistencia]:
        return self.repository.get_by_fecha(fecha)

    def listar_faltas(
        self, desde: date | None = None, hasta: date | None = None, solo_injustificadas: bool = False
    ) -> list[Asistencia]:
        return self.repository.get_faltas(desde, hasta, solo_injustificadas)

    def listar_tardanzas(self, desde: date, hasta: date) -> list[Asistencia]:
        """Registros con tardanza dentro de un período"""
        return [
            registro
            for registro in self.repository.get_por_tipo(
                TipoAsistencia.TARDANZA.value, desde, hasta
            )
        ]

    def empleados_sin_registro(self, fecha: date) -> list[Empleado]:
        """
        Empleados activos que aún no tienen asistencia registrada

        Alimenta la alerta de jornadas pendientes de captura y la carga
        rápida desde la interfaz.
        """
        activos = self.empleado_repository.get_activos()
        registrados = self.repository.get_empleados_con_registro(fecha)
        return [empleado for empleado in activos if empleado.id not in registrados]

    # ------------------------------------------------------------------
    # Totales para nómina y alertas
    # ------------------------------------------------------------------
    def obtener_totales(self, empleado_id: int, desde: date, hasta: date) -> dict:
        """Totales de asistencia de un empleado en un período"""
        return self.repository.get_totales_periodo(empleado_id, desde, hasta)

    def horas_extra_periodo(self, empleado_id: int, desde: date, hasta: date) -> HorasExtra:
        """
        Horas extra clasificadas de un período

        Es lo que el servicio de pagos entrega al motor de nómina para
        valorarlas con el recargo que corresponda.
        """
        totales = self.obtener_totales(empleado_id, desde, hasta)
        return HorasExtra(
            diurnas=a_decimal(totales.get("horas_extra_diurnas")),
            nocturnas=a_decimal(totales.get("horas_extra_nocturnas")),
            feriadas=a_decimal(totales.get("horas_extra_feriadas")),
        )

    def dias_trabajados_periodo(self, empleado_id: int, desde: date, hasta: date) -> int:
        """
        Días efectivamente trabajados en un período

        Cuenta los días con presencia o tardanza; las ausencias no
        justificadas quedan fuera, que es lo que descuenta la nómina.
        """
        registros = self.repository.get_by_empleado(empleado_id, desde, hasta)
        return len(
            [
                registro
                for registro in registros
                if float(registro.horas_trabajadas or 0) > 0
            ]
        )

    def aplicar_incidencias_aprobadas(
        self, empleado_id: int, desde: date, hasta: date
    ) -> int:
        """
        Genera registros de ausencia desde las incidencias aprobadas

        Toma las incidencias aprobadas del período y crea o actualiza el
        registro de asistencia correspondiente, de modo que la nómina vea
        los días justificados sin recapturarlos a mano.

        Returns:
            int: Cantidad de días marcados
        """
        incidencias = self.incidencia_repository.get_by_empleado(empleado_id)
        marcados = 0
        for incidencia in incidencias:
            estado = getattr(incidencia.estado, "value", incidencia.estado)
            if estado not in ("aprobado", "completado"):
                continue
            inicio = getattr(incidencia, "fecha_inicio", None)
            fin = getattr(incidencia, "fecha_fin", None) or inicio
            if not isinstance(inicio, date) or not isinstance(fin, date):
                continue
            if fin < desde or inicio > hasta:
                continue
            dia = max(inicio, desde)
            fin = min(fin, hasta)
            tipo = getattr(incidencia, "tipo_incidencia", None)
            tipo_valor = getattr(tipo, "value", tipo) or TipoAsistencia.PERMISO.value
            incidencia_id = getattr(incidencia, "id", None)
            while dia <= fin:
                registro = self.repository.get_registro(empleado_id, dia)
                # Idempotente: un día ya marcado por esta misma incidencia no
                # se vuelve a escribir (el usuario puede reaplicar el rango
                # tantas veces como quiera).
                if (
                    registro is not None
                    and bool(registro.justificada)
                    and getattr(registro, "incidencia_id", None) == incidencia_id
                ):
                    dia += timedelta(days=1)
                    continue
                if registro is None or float(registro.horas_trabajadas or 0) == 0:
                    self.registrar_jornada(
                        empleado_id=empleado_id,
                        fecha=dia,
                        tipo=tipo_valor,
                        justificada=True,
                        incidencia_id=incidencia_id,
                        observaciones=f"Justificado por incidencia #{incidencia_id}",
                    )
                    marcados += 1
                dia += timedelta(days=1)
        if marcados:
            logger.info(
                "Asistencia: %s días marcados desde incidencias aprobadas del empleado %s",
                marcados,
                empleado_id,
            )
        return marcados

    def resumen_periodo(self, empleado_id: int, desde: date, hasta: date) -> dict:
        """
        Resumen completo de asistencia de un empleado en un período

        Reúne totales, horas extra y días trabajados, más los datos del
        horario vigente, para mostrarlo en pantalla y en los reportes.
        """
        totales = self.obtener_totales(empleado_id, desde, hasta)
        horas_extra = self.horas_extra_periodo(empleado_id, desde, hasta)
        return {
            **totales,
            "dias_trabajados": self.dias_trabajados_periodo(empleado_id, desde, hasta),
            "horas_extra_total": float(horas_extra.total),
            "horas_semanales_horario": self.horario_repository.get_horas_semanales(empleado_id),
            "periodo_inicio": desde.isoformat(),
            "periodo_fin": hasta.isoformat(),
        }

    def obtener_estadisticas(
        self, desde: date | None = None, hasta: date | None = None
    ) -> dict:
        """Estadísticas de asistencia del período consultado"""
        return self.repository.get_estadisticas(desde, hasta)

    def empleados_con_exceso_horas(self, desde: date, hasta: date) -> list[dict]:
        """
        Empleados que superan el máximo de horas extra semanal configurado

        Se evalúa semana por semana dentro del período consultado para
        avisar antes de que el exceso se convierta en un problema legal.
        """
        limite = float(self._valor("max_horas_extra_semana", 10) or 10)
        if limite <= 0:
            return []
        resultado: list[dict] = []
        for empleado in self.empleado_repository.get_activos():
            registros = self.repository.get_by_empleado(empleado.id, desde, hasta)
            por_semana: dict[tuple[int, int], float] = {}
            for registro in registros:
                extra = float(registro.total_horas_extra or 0)
                if extra <= 0:
                    continue
                anio, semana, _ = registro.fecha.isocalendar()
                clave = (anio, semana)
                por_semana[clave] = por_semana.get(clave, 0.0) + extra
            for (anio, semana), total in por_semana.items():
                if total > limite:
                    resultado.append(
                        {
                            "empleado_id": empleado.id,
                            "empleado": empleado.nombre_completo,
                            "anio": anio,
                            "semana": semana,
                            "horas_extra": round(total, 2),
                            "limite": limite,
                        }
                    )
        return resultado

    def validar_datos_asistencia(self, datos: dict) -> list[str]:
        """Valida los datos mínimos de un registro de asistencia"""
        errores: list[str] = []
        if not datos.get("empleado_id"):
            errores.append("El empleado es requerido")
        if not datos.get("fecha"):
            errores.append("La fecha es requerida")
        elif not isinstance(datos.get("fecha"), date):
            errores.append("La fecha debe ser una fecha válida")
        entrada = parsear_hora(datos.get("hora_entrada"))
        salida = parsear_hora(datos.get("hora_salida"))
        if datos.get("hora_entrada") and entrada is None:
            errores.append("La hora de entrada debe tener formato HH:MM")
        if datos.get("hora_salida") and salida is None:
            errores.append("La hora de salida debe tener formato HH:MM")
        return errores

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    def _auditar(self, registro: Asistencia, operacion: str, empleado: Empleado | None = None) -> None:
        """Registra la operación en la auditoría sin afectar el flujo"""
        try:
            audit = get_audit_logger()
            if not audit:
                return
            audit.log_event(
                event_type=AuditEventType.DATA_CREATE
                if operacion == "registrar_jornada"
                else AuditEventType.DATA_UPDATE,
                entity_type="asistencia",
                entity_id=registro.id,
                user=registro.registrado_por or "system",
                details={
                    "empleado_id": registro.empleado_id,
                    "fecha": registro.fecha.isoformat() if registro.fecha else None,
                    "tipo": registro.tipo_valor,
                    "horas": float(registro.horas_trabajadas or 0),
                    "empleado": empleado.nombre_completo if empleado else None,
                },
                success=True,
            )
        except (SQLAlchemyError, ValueError, TypeError):
            logger.debug("No se pudo auditar el registro de asistencia", exc_info=True)

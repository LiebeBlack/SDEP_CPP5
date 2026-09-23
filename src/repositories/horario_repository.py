"""
Horario Repository
Repositorio para los horarios de trabajo

Gestiona la jornada semanal de cada empleado: consulta por día,
reemplazo completo del horario y totales de horas comprometidas.
"""

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import Horario

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class HorarioRepository(BaseRepository[Horario]):
    """Repositorio de horarios con manejo robusto de errores"""

    def __init__(self, session: Session):
        super().__init__(Horario, session)

    def get_by_empleado(self, empleado_id: int, solo_activos: bool = False) -> list[Horario]:
        """Horarios de un empleado ordenados por día de la semana"""
        try:
            query = self.session.query(Horario).filter(Horario.empleado_id == empleado_id)
            if solo_activos:
                query = query.filter(Horario.activo == 1)
            return query.order_by(Horario.dia_semana).all()
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo horarios del empleado {empleado_id}: {e}")
            return []

    def get_dia(self, empleado_id: int, dia_semana: int) -> Horario | None:
        """Horario activo de un empleado para un día concreto"""
        try:
            return (
                self.session.query(Horario)
                .filter(
                    Horario.empleado_id == empleado_id,
                    Horario.dia_semana == dia_semana,
                    Horario.activo == 1,
                )
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Error obteniendo el horario del empleado {empleado_id} día {dia_semana}: {e}"
            )
            return None

    def get_existentes(self, empleado_id: int) -> dict[int, Horario]:
        """Horarios de un empleado indexados por día de la semana"""
        try:
            return {
                int(horario.dia_semana): horario
                for horario in self.get_by_empleado(empleado_id)
            }
        except SQLAlchemyError as e:
            logger.error(f"Error indexando horarios del empleado {empleado_id}: {e}")
            return {}

    def get_activos(self) -> list[Horario]:
        """Todos los horarios vigentes del sistema"""
        try:
            return self.session.query(Horario).filter(Horario.activo == 1).all()
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo horarios activos: {e}")
            return []

    def get_horas_semanales(self, empleado_id: int) -> float:
        """Horas semanales comprometidas por el horario de un empleado"""
        try:
            horarios = self.get_by_empleado(empleado_id, solo_activos=True)
            return round(sum(horario.horas_jornada for horario in horarios), 2)
        except SQLAlchemyError as e:
            logger.error(f"Error calculando horas semanales del empleado {empleado_id}: {e}")
            return 0.0

    def eliminar_de_empleado(self, empleado_id: int) -> int:
        """Desactiva todos los horarios de un empleado (no borra el histórico)"""
        try:
            horarios = self.get_by_empleado(empleado_id)
            for horario in horarios:
                horario.activo = 0
            self.session.commit()
            return len(horarios)
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error desactivando horarios del empleado {empleado_id}: {e}")
            return 0

    def get_estadisticas(self) -> dict:
        """Estadísticas de los horarios registrados"""
        try:
            horarios = self.get_activos()
            empleados = {horario.empleado_id for horario in horarios}
            por_dia: dict[int, int] = {}
            for horario in horarios:
                por_dia[int(horario.dia_semana)] = por_dia.get(int(horario.dia_semana), 0) + 1
            return {
                "total_horarios": len(horarios),
                "empleados_con_horario": len(empleados),
                "por_dia": por_dia,
            }
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo estadísticas de horarios: {e}")
            return {"total_horarios": 0, "empleados_con_horario": 0, "por_dia": {}}

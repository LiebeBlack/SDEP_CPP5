"""
Planificador de respaldos automáticos

Comprueba si corresponde generar un respaldo según el intervalo
configurado y lo ejecuta usando el gestor de respaldos existente.

El diseño es deliberadamente sin hilos propios: la comprobación se
agenda con `after()` sobre la ventana de Tk, de modo que el respaldo
nunca toca la interfaz desde un hilo secundario (origen clásico de
cierres inesperados en aplicaciones de escritorio).

Uso típico desde la ventana principal:

    self._scheduler = BackupScheduler.desde_sesion(self.session)
    self._scheduler.programar(self, intervalo_ms=600_000)
"""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

INTERVALO_COMPROBACION_MS = 600_000  # 10 minutos
HORAS_INTERVALO_DEFECTO = 24
PREFIJO_PROGRAMADO = "scheduled_"


class BackupScheduler:
    """
    Comprobador y ejecutor de respaldos programados

    Args:
        obtener_valor: Función (clave, por_defecto) que devuelve el valor
            de configuración vigente. Si no se entrega se leen las
            variables de entorno/ajustes locales.
    """

    def __init__(self, obtener_valor: Callable[[str, Any], Any] | None = None):
        self._obtener_valor = obtener_valor or self._valor_por_defecto
        self._ultima_ejecucion: datetime | None = None
        self._resultado_ultimo: dict | None = None

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------
    @classmethod
    def desde_sesion(cls, session) -> "BackupScheduler":
        """Crea el planificador leyendo la configuración de la base de datos"""

        def obtener(clave: str, por_defecto):
            from src.repositories import ConfiguracionRepository

            return ConfiguracionRepository(session).get_valor(clave, por_defecto)

        return cls(obtener)

    @staticmethod
    def _valor_por_defecto(clave: str, por_defecto):
        """Lee el valor desde los ajustes locales cuando no hay sesión"""
        try:
            from src.config import settings

            valor = settings.get_config_value(clave)
            return por_defecto if valor is None else valor
        except (AttributeError, ValueError, TypeError):
            return por_defecto

    # ------------------------------------------------------------------
    # Estado del planificador
    # ------------------------------------------------------------------
    def esta_habilitado(self) -> bool:
        """Indica si los respaldos automáticos están habilitados"""
        valor = self._obtener_valor("backup_enabled", True)
        if isinstance(valor, str):
            return valor.strip().lower() in ("true", "1", "yes", "on", "si", "sí", "verdadero")
        return bool(valor)

    def intervalo_horas(self) -> int:
        """Horas entre respaldos automáticos"""
        try:
            valor = int(self._obtener_valor("backup_interval_hours", HORAS_INTERVALO_DEFECTO))
        except (TypeError, ValueError):
            return HORAS_INTERVALO_DEFECTO
        return max(1, valor)

    def ultima_ejecucion(self) -> datetime | None:
        """
        Momento del último respaldo programado

        Se toma el más reciente entre el registro en memoria y los
        respaldos ya guardados con el prefijo de programados, de modo que
        reiniciar la aplicación no vuelva a respaldar antes de tiempo.
        """
        candidatos: list[datetime] = []
        if self._ultima_ejecucion is not None:
            candidatos.append(self._ultima_ejecucion)
        for respaldo in self._respaldos_programados():
            fecha = self._fecha_de(respaldo)
            if fecha is not None:
                candidatos.append(fecha)
        return max(candidatos) if candidatos else None

    def proxima_ejecucion(self, ahora: datetime | None = None) -> datetime | None:
        """Momento en que corresponde el próximo respaldo (None si está deshabilitado)"""
        if not self.esta_habilitado():
            return None
        momento = ahora or datetime.now()
        ultima = self.ultima_ejecucion()
        if ultima is None:
            return momento
        return ultima + timedelta(hours=self.intervalo_horas())

    def debe_ejecutar(self, ahora: datetime | None = None) -> bool:
        """Indica si ya corresponde generar un respaldo automático"""
        if not self.esta_habilitado():
            return False
        momento = ahora or datetime.now()
        proxima = self.proxima_ejecucion(momento)
        return proxima is not None and momento >= proxima

    # ------------------------------------------------------------------
    # Ejecución
    # ------------------------------------------------------------------
    def ejecutar(self, forzar: bool = False) -> dict:
        """
        Genera un respaldo si corresponde

        Args:
            forzar: Ignora la comprobación de intervalo y el interruptor de
                respaldos automáticos (para el botón "Respaldar ahora").

        Returns:
            dict: resultado con las claves ejecutado, motivo, backup y
            verificacion. Nunca lanza excepciones: un respaldo fallido no
            debe tumbar la aplicación.
        """
        if not forzar and not self.debe_ejecutar():
            return {
                "ejecutado": False,
                "motivo": "todavía no corresponde"
                if self.esta_habilitado()
                else "respaldos automáticos deshabilitados",
                "backup": None,
                "verificacion": None,
            }

        try:
            from src.utils.backup_manager import get_backup_manager

            gestor = get_backup_manager()
            backup = gestor.create_scheduled_backup()
            verificacion = None
            nombre = (backup or {}).get("name")
            if nombre:
                verificacion = gestor.verify_backup_integrity(nombre)
                if not verificacion.get("integrity_ok", False):
                    logger.warning(
                        "El respaldo programado %s no superó la verificación de integridad",
                        nombre,
                    )
            self._ultima_ejecucion = datetime.now()
            self._resultado_ultimo = {
                "ejecutado": True,
                "motivo": "respaldo programado generado",
                "backup": backup,
                "verificacion": verificacion,
            }
            logger.info("Respaldo automático generado: %s", nombre)
            return self._resultado_ultimo
        except Exception as e:
            logger.error("No se pudo generar el respaldo automático: %s", e)
            self._ultima_ejecucion = datetime.now()
            return {
                "ejecutado": False,
                "motivo": f"error al respaldar: {e}",
                "backup": None,
                "verificacion": None,
            }

    def comprobar_y_ejecutar(self, callback: Callable[[dict], None] | None = None) -> dict:
        """
        Ejecuta la comprobación y avisa del resultado

        Args:
            callback: Función que recibe el resultado cuando sí se generó
                un respaldo (para actualizar la interfaz).
        """
        resultado = self.ejecutar()
        if resultado.get("ejecutado") and callback is not None:
            try:
                callback(resultado)
            except (ValueError, TypeError, RuntimeError):
                logger.debug("El aviso del respaldo programado falló", exc_info=True)
        return resultado

    # ------------------------------------------------------------------
    # Integración con Tk (sin hilos propios)
    # ------------------------------------------------------------------
    def programar(
        self,
        widget,
        intervalo_ms: int = INTERVALO_COMPROBACION_MS,
        callback: Callable[[dict], None] | None = None,
    ) -> str:
        """
        Agenda la comprobación periódica sobre un widget de Tk

        Returns:
            str: Identificador de la tarea programada, para poder cancelarla.
        """
        identificador: str = ""

        def _ciclo() -> None:
            nonlocal identificador
            try:
                self.comprobar_y_ejecutar(callback)
            finally:
                try:
                    identificador = widget.after(intervalo_ms, _ciclo)
                except RuntimeError:
                    # La ventana se cerró: se detiene el ciclo en silencio
                    logger.debug("Ventana cerrada: se detiene el planificador de respaldos")

        try:
            identificador = widget.after(intervalo_ms, _ciclo)
        except (AttributeError, RuntimeError):
            logger.debug("No se pudo programar el respaldo automático", exc_info=True)
        return identificador

    @staticmethod
    def cancelar(widget, identificador: str) -> None:
        """Cancela una comprobación programada"""
        if not identificador:
            return
        try:
            widget.after_cancel(identificador)
        except (AttributeError, RuntimeError, ValueError):
            logger.debug("No se pudo cancelar el planificador de respaldos", exc_info=True)

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    def _respaldos_programados(self) -> list:
        """Respaldos generados automáticamente por el planificador"""
        try:
            from src.utils.backup_manager import get_backup_manager

            respaldos = get_backup_manager().list_backups()
        except (OSError, ValueError, TypeError, RuntimeError):
            logger.debug("No se pudo listar los respaldos programados", exc_info=True)
            return []
        return [
            respaldo
            for respaldo in respaldos or []
            if str(
                respaldo.get("name", "") if isinstance(respaldo, dict) else getattr(respaldo, "name", "")
            ).startswith(PREFIJO_PROGRAMADO)
        ]

    @staticmethod
    def _fecha_de(respaldo) -> datetime | None:
        """Fecha declarada en los metadatos de un respaldo"""
        marca = (
            respaldo.get("timestamp")
            if isinstance(respaldo, dict)
            else getattr(respaldo, "timestamp", None)
        )
        if not isinstance(marca, str):
            return None
        try:
            return datetime.strptime(marca.strip()[:15], "%Y%m%d_%H%M%S")
        except ValueError:
            return None

    def estado(self) -> dict:
        """
        Estado del planificador para mostrarlo en la interfaz

        Returns:
            dict: habilitado, intervalo, última ejecución y próxima.
        """
        ultima = self.ultima_ejecucion()
        proxima = self.proxima_ejecucion()
        return {
            "habilitado": self.esta_habilitado(),
            "intervalo_horas": self.intervalo_horas(),
            "ultima_ejecucion": ultima.isoformat() if ultima else None,
            "proxima_ejecucion": proxima.isoformat() if proxima else None,
            "ultimo_resultado": self._resultado_ultimo,
        }


def get_backup_scheduler(session=None) -> BackupScheduler:
    """
    Instancia del planificador lista para usar

    Args:
        session: Sesión de base de datos para leer la configuración. Si no
            se entrega, se usan los ajustes locales.
    """
    if session is not None:
        return BackupScheduler.desde_sesion(session)
    return BackupScheduler()

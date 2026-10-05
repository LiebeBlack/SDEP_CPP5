"""
Backup Manager
Sistema de backup automático y restauración de base de datos

Este módulo proporciona funcionalidades para:
- Backups automáticos programados
- Backups manuales bajo demanda
- Restauración de backups
- Rotación de backups antiguos
- Compresión de backups
- Verificación de integridad de backups
"""

import shutil
import gzip
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BackupManager:
    """Gestor de backups de base de datos"""

    def __init__(self):
        """Inicializa el gestor de backups"""
        # Importar settings aquí para evitar problemas de inicialización
        from src.config import settings

        self.backup_dir = Path(settings.backups_dir)
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError):
            logger.error("No se pudo preparar la carpeta privada de respaldos", exc_info=True)
            raise RuntimeError("No se pudo preparar la carpeta de respaldos")

        # settings.database_path ya es una ruta absoluta y única (se
        # resuelve contra base_dir dentro de settings). Concatenarla otra
        # vez con base_dir producía una ruta anidada inexistente y TODOS
        # los respaldos fallaban con "Base de datos no encontrada" (y con
        # ello la restauración, los respaldos automáticos y el inicial).
        self.db_path = Path(settings.database_path)
        self.metadata_file = self.backup_dir / "backup_metadata.json"

        # Configuración de rotación
        self.max_backups = 10  # Máximo número de backups a mantener
        self.backup_retention_days = 30  # Días a mantener backups

        # Cargar metadatos existentes
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> dict:
        """Carga metadatos de backups existentes"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                if not isinstance(datos, dict):
                    raise ValueError("El archivo de metadatos no contiene un objeto JSON")
                return {
                    str(nombre): info
                    for nombre, info in datos.items()
                    if isinstance(info, dict)
                }
            except Exception as e:
                logger.error(f"Error cargando metadatos: {e}")
                return {}
        return {}

    def _save_metadata(self):
        """Guarda metadatos de respaldos mediante reemplazo atómico."""
        temporal = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.backup_dir,
                prefix=".backup_metadata_",
                suffix=".tmp",
                delete=False,
            ) as f:
                temporal = Path(f.name)
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporal, self.metadata_file)
        except Exception:
            if temporal is not None:
                try:
                    temporal.unlink(missing_ok=True)
                except OSError:
                    logger.warning("No se pudo limpiar metadatos temporales", exc_info=True)
            logger.error("Error guardando metadatos de respaldos", exc_info=True)
            raise

    def _backup_path(self, backup_info: dict) -> Path:
        """Resuelve únicamente rutas de backup contenidas en el almacén privado."""
        raw_path = backup_info.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            raise ValueError("Metadatos de backup sin ruta válida")
        candidato = Path(raw_path)
        # Los metadatos vigentes guardan solo el nombre del archivo: la ruta
        # absoluta del equipo de desarrollo no significa nada en otro y expone
        # la estructura de su disco. Se siguen aceptando rutas absolutas
        # dentro del almacén para no invalidar metadatos de versiones previas.
        if candidato.parent == Path("."):
            path = (self.backup_dir / candidato).resolve()
        else:
            path = candidato.resolve()
        try:
            path.relative_to(self.backup_dir.resolve())
        except ValueError as e:
            raise ValueError("La ruta del backup está fuera del almacén de respaldos") from e
        return path

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calcula checksum SHA256 de un archivo"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except OSError as e:
            logger.error("Error calculando checksum", exc_info=True)
            raise RuntimeError(f"No se pudo calcular el checksum de {file_path}") from e

    @staticmethod
    def _online_copy(source: Path, destination: Path, reintentos: int = 3) -> None:
        """
        Copia una base de datos SQLite de forma consistente

        Usa la API sqlite3 .backup() que produce una copia correcta
        aunque existan conexiones activas al archivo origen. Reintenta
        ante bloqueos temporales (base de datos ocupada, antivirus,
        permisos transitorios).
        """
        import sqlite3

        temp_path = destination.with_name(destination.name + ".tmp")
        ultimo_error = None
        for intento in range(reintentos):
            try:
                src_conn = sqlite3.connect(str(source), timeout=30)
                try:
                    dst_conn = sqlite3.connect(str(temp_path))
                    try:
                        src_conn.backup(dst_conn)
                    finally:
                        dst_conn.close()
                finally:
                    src_conn.close()
                shutil.move(str(temp_path), str(destination))
                return
            except (sqlite3.OperationalError, OSError, PermissionError) as e:
                ultimo_error = e
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        logger.debug("No se pudo eliminar el temporal del backup", exc_info=True)
                if intento < reintentos - 1:
                    time.sleep(0.3 * (intento + 1))
        if ultimo_error:
            raise ultimo_error
        raise RuntimeError(f"No se pudo copiar la base de datos: {destination}")

    def _compress_file(self, source: Path, destination: Path) -> bool:
        """Comprime un archivo usando gzip"""
        try:
            with open(source, "rb") as f_in:
                with gzip.open(destination, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception as e:
            logger.error(f"Error comprimiendo archivo: {e}")
            return False

    def _decompress_file(self, source: Path, destination: Path) -> bool:
        """Descomprime un archivo gzip"""
        try:
            with gzip.open(source, "rb") as f_in:
                with open(destination, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception as e:
            logger.error(f"Error descomprimiendo archivo: {e}")
            return False

    @staticmethod
    def _validate_sqlite(file_path: Path) -> bool:
        """
        Valida que un archivo sea una base SQLite íntegra

        PRAGMA integrity_check recorre la estructura interna de la base,
        algo que la comparación de bytes con el archivo original no puede
        garantizar: el respaldo con sqlite .backup() produce un archivo
        compactado que legítimamente difiere del original.
        """
        import sqlite3

        try:
            if not file_path.exists() or file_path.stat().st_size == 0:
                return False
            conn = sqlite3.connect(str(file_path))
            try:
                resultado = conn.execute("PRAGMA integrity_check").fetchone()
                return resultado is not None and resultado[0] == "ok"
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Error validando integridad SQLite: {e}")
            return False

    def create_backup(self, backup_name: str | None = None, compress: bool = True) -> dict:
        """
        Crea un backup de la base de datos

        Args:
            backup_name: Nombre personalizado para el backup
            compress: Si se debe comprimir el backup

        Returns:
            dict con información del backup creado
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = backup_name or f"backup_{timestamp}"
        if (
            not isinstance(backup_name, str)
            or not backup_name
            or len(backup_name) > 100
            or any(
                char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                for char in backup_name
            )
        ):
            raise ValueError("Nombre de backup no válido")

        # Crear archivo de backup
        backup_filename = f"{backup_name}.db"
        backup_path = self.backup_dir / backup_filename
        if backup_name in self.metadata or backup_path.exists():
            base_name = backup_name
            contador = 0
            while True:
                marca = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                sufijo = f"_{marca}" if contador == 0 else f"_{marca}_{contador}"
                backup_name = f"{base_name[:100 - len(sufijo)]}{sufijo}"
                backup_filename = f"{backup_name}.db"
                backup_path = self.backup_dir / backup_filename
                if backup_name not in self.metadata and not backup_path.exists():
                    break
                contador += 1

        try:
            # Respaldo consistente usando la API de copia de SQLite,
            # segura aunque haya conexiones abiertas al archivo.
            self._online_copy(self.db_path, backup_path)
            if not self._validate_sqlite(backup_path):
                raise RuntimeError("La copia del backup no superó la validación de SQLite")

            # Comprimir si se solicita
            if compress:
                compressed_path = backup_path.with_suffix(".db.gz")
                if not self._compress_file(backup_path, compressed_path):
                    raise RuntimeError("No se pudo comprimir el backup")
                backup_path.unlink()
                backup_path = compressed_path
                backup_filename = compressed_path.name

            # Calcular checksum y tamaño sobre el archivo almacenado final
            checksum = self._calculate_checksum(backup_path)

            # Guardar metadatos
            backup_info = {
                "name": backup_name,
                "filename": backup_filename,
                # Relativo al almacén de respaldos (ver ``_backup_path``).
                "path": backup_filename,
                "timestamp": timestamp,
                "size_bytes": backup_path.stat().st_size,
                "checksum": checksum,
                "compressed": compress,
                "version": 2,
            }

            self.metadata[backup_name] = backup_info
            self._save_metadata()

            # Rotación automática: no acumular respaldos sin límite
            try:
                self.rotate_backups()
            except Exception:
                logger.warning(
                    "%s: operación auxiliar falló (se continúa)", "create_backup", exc_info=True
                )

            logger.info(f"Backup creado exitosamente: {backup_name}")
            return backup_info

        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            self.metadata.pop(backup_name, None)
            # Limpiar archivos parciales
            for partial in (
                self.backup_dir / f"{backup_name}.db",
                self.backup_dir / f"{backup_name}.db.gz",
            ):
                try:
                    partial.unlink(missing_ok=True)
                except OSError:
                    logger.warning("No se pudo limpiar un backup parcial: %s", partial, exc_info=True)
            raise

    def restore_backup(self, backup_name: str, verify_checksum: bool = True) -> bool:
        """
        Restaura un backup de la base de datos

        Args:
            backup_name: Nombre del backup a restaurar
            verify_checksum: Si se debe verificar el checksum

        Returns:
            True si la restauración fue exitosa
        """
        if backup_name not in self.metadata:
            raise ValueError(f"Backup no encontrado: {backup_name}")

        backup_info = self.metadata[backup_name]
        backup_path = self._backup_path(backup_info)

        if not backup_path.exists():
            raise FileNotFoundError(f"Archivo de backup no encontrado: {backup_path}")

        restore_temp_path = None
        try:
            # Crear backup del estado actual antes de restaurar
            current_backup = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.create_backup(current_backup, compress=False)

            # v2: el checksum corresponde al archivo almacenado; verificar
            # antes de descomprimir para detectar corrupción de forma limpia
            if verify_checksum and backup_info.get("checksum") and backup_info.get("version") == 2:
                if self._calculate_checksum(backup_path) != backup_info["checksum"]:
                    raise Exception("Checksum verification failed: backup may be corrupted")

            # Descomprimir en un archivo temporal creado dentro del almacén.
            temp_restore_path = backup_path
            if backup_info["compressed"]:
                with tempfile.NamedTemporaryFile(
                    dir=self.backup_dir,
                    prefix=".restore_",
                    suffix=".db",
                    delete=False,
                ) as temp_restore:
                    restore_temp_path = Path(temp_restore.name)
                temp_restore_path = restore_temp_path
                if not self._decompress_file(backup_path, temp_restore_path):
                    raise RuntimeError("Error descomprimiendo backup")

            # Legado v1: el checksum correspondía al contenido descomprimido
            if verify_checksum and backup_info.get("checksum") and backup_info.get("version") != 2:
                if self._calculate_checksum(temp_restore_path) != backup_info["checksum"]:
                    raise Exception("Checksum verification failed: backup may be corrupted")

            # El contenido debe ser una base SQLite íntegra antes de restaurarla
            if not self._validate_sqlite(temp_restore_path):
                raise ValueError("El backup no contiene una base de datos SQLite íntegra")

            # Liberar conexiones del motor antes de reemplazar el archivo
            try:
                from src.config import db_config

                db_config.SessionLocal.remove()
                db_config.engine.dispose()
            except Exception:
                logger.warning(
                    "%s: operación auxiliar falló (se continúa)", "restore_backup", exc_info=True
                )

            # Preparar en el mismo volumen y reemplazar atómicamente para que
            # una interrupción no deje la base actual truncada o a medias.
            with tempfile.NamedTemporaryFile(
                dir=self.db_path.parent,
                prefix=f".{self.db_path.name}.restore_",
                suffix=".tmp",
                delete=False,
            ) as staged_file:
                staged_path = Path(staged_file.name)
            try:
                shutil.copy2(temp_restore_path, staged_path)
                if not self._validate_sqlite(staged_path):
                    raise ValueError("La copia preparada para restauración no es íntegra")
                os.replace(staged_path, self.db_path)
            finally:
                try:
                    staged_path.unlink(missing_ok=True)
                except OSError:
                    logger.warning("No se pudo limpiar la copia temporal de restauración", exc_info=True)

            try:
                from src.config import db_config

                db_config.engine.dispose()
            except Exception:
                logger.warning(
                    "%s: operación auxiliar falló (se continúa)", "restore_backup", exc_info=True
                )

            # Limpiar archivo temporal
            logger.info(f"Backup restaurado exitosamente: {backup_name}")
            return True

        except Exception as e:
            logger.error(f"Error restaurando backup: {e}")
            raise
        finally:
            if restore_temp_path is not None:
                try:
                    restore_temp_path.unlink(missing_ok=True)
                except OSError:
                    logger.warning("No se pudo limpiar el archivo temporal de restauración", exc_info=True)

    def list_backups(self) -> list[dict]:
        """
        Lista todos los backups disponibles

        Returns:
            Lista de información de backups
        """
        backups = []
        for name, info in self.metadata.items():
            try:
                backup_path = self._backup_path(info)
            except (KeyError, TypeError, ValueError):
                continue
            exists = backup_path.exists()
            info["exists"] = exists
            try:
                info["age_days"] = (
                    datetime.now() - datetime.strptime(info["timestamp"], "%Y%m%d_%H%M%S")
                ).days
            except (ValueError, KeyError, TypeError):
                # Metadatos corruptos o de un formato antiguo: no romper la lista
                info["age_days"] = 0
            backups.append(info)

        # Ordenar por timestamp (más reciente primero)
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        return backups

    def delete_backup(self, backup_name: str) -> bool:
        """
        Elimina un backup específico

        Args:
            backup_name: Nombre del backup a eliminar

        Returns:
            True si se eliminó correctamente
        """
        if backup_name not in self.metadata:
            return False

        backup_info = self.metadata[backup_name]
        backup_path = self._backup_path(backup_info)

        try:
            if backup_path.exists():
                backup_path.unlink()

            del self.metadata[backup_name]
            self._save_metadata()

            logger.info(f"Backup eliminado: {backup_name}")
            return True

        except Exception as e:
            logger.error(f"Error eliminando backup: {e}")
            return False

    def rotate_backups(self) -> dict:
        """
        Rotación automática de backups antiguos

        Política (en este orden):
          1. Se eliminan los backups más antiguos que backup_retention_days.
          2. Si aún quedan más de max_backups, se eliminan los más antiguos
             hasta respetar el límite (se conservan SIEMPRE los más recientes).

        Returns:
            dict con estadísticas de la rotación
        """
        stats: dict[str, Any] = {
            "total_before": len(self.metadata),
            "deleted_count": 0,
            "deleted_backups": [],
            "total_after": 0,
        }

        try:
            backups = self.list_backups()  # más reciente primero
            restantes = list(backups)
            cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)

            def _fecha(backup: dict) -> datetime | None:
                """Timestamp del backup o None si los metadatos están corruptos"""
                try:
                    return datetime.strptime(backup["timestamp"], "%Y%m%d_%H%M%S")
                except (ValueError, KeyError, TypeError):
                    return None

            # 1) Retención por antigüedad: se recorren de MÁS ANTIGUO a más
            #    reciente sobre una copia (nunca se muta la lista en iteración).
            for backup in list(reversed(restantes)):
                fecha = _fecha(backup)
                if fecha is not None and fecha < cutoff_date:
                    if self.delete_backup(backup["name"]):
                        stats["deleted_count"] += 1
                        stats["deleted_backups"].append(backup["name"])
                        restantes = [b for b in restantes if b["name"] != backup["name"]]

            # 2) Límite máximo: descartar los más antiguos hasta ajustarse.
            while len(restantes) > self.max_backups:
                objetivo = restantes[-1]  # el más antiguo (lista: nuevo -> viejo)
                if not self.delete_backup(objetivo["name"]):
                    break  # no se pudo eliminar: evitar bucle infinito
                stats["deleted_count"] += 1
                stats["deleted_backups"].append(objetivo["name"])
                restantes = restantes[:-1]

            stats["total_after"] = len(restantes)
            logger.info(f"Rotación de backups completada: {stats['deleted_count']} eliminados")

        except Exception as e:
            logger.error(f"Error en rotación de backups: {e}")

        return stats

    def verify_backup_integrity(self, backup_name: str) -> dict:
        """
        Verifica la integridad de un backup específico

        Args:
            backup_name: Nombre del backup a verificar

        Returns:
            dict con resultados de verificación
        """
        if backup_name not in self.metadata:
            raise ValueError(f"Backup no encontrado: {backup_name}")

        backup_info = self.metadata[backup_name]
        backup_path = self._backup_path(backup_info)

        result = {
            "backup_name": backup_name,
            "exists": backup_path.exists(),
            "checksum_valid": False,
            "size_correct": False,
            "integrity_ok": False,
        }

        try:
            if not backup_path.exists():
                return result

            # Verificar tamaño
            current_size = backup_path.stat().st_size
            result["size_correct"] = current_size == backup_info.get("size_bytes", -1)

            # Verificar checksum según el esquema de metadatos
            if backup_info.get("checksum"):
                if backup_info.get("version") == 2:
                    current_checksum = self._calculate_checksum(backup_path)
                    result["checksum_valid"] = current_checksum == backup_info["checksum"]
                    result["integrity_ok"] = (
                        result["exists"] and result["size_correct"] and result["checksum_valid"]
                    )
                elif backup_info.get("compressed"):
                    # Legado: verificar contra el contenido descomprimido
                    try:
                        with gzip.open(backup_path, "rb") as f:
                            contenido = hashlib.sha256()
                            for bloque in iter(lambda: f.read(65536), b""):
                                contenido.update(bloque)
                        result["checksum_valid"] = contenido.hexdigest() == backup_info["checksum"]
                    except Exception:
                        result["checksum_valid"] = False
                    result["integrity_ok"] = result["exists"] and result["checksum_valid"]
                else:
                    current_checksum = self._calculate_checksum(backup_path)
                    result["checksum_valid"] = current_checksum == backup_info["checksum"]
                    result["integrity_ok"] = result["checksum_valid"] and result["size_correct"]

        except Exception as e:
            logger.error(f"Error verificando integridad: {e}")

        return result

    def create_scheduled_backup(self) -> dict:
        """
        Crea un backup programado automático

        Este método está diseñado para ser llamado por un scheduler
        para crear backups automáticos en intervalos regulares
        """
        try:
            # Primero rotar backups antiguos
            self.rotate_backups()

            # Crear nuevo backup con nombre programado
            backup_name = f"scheduled_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return self.create_backup(backup_name)

        except Exception as e:
            logger.error(f"Error en backup programado: {e}")
            raise


# Instancia global del gestor de backups
backup_manager = BackupManager()


def get_backup_manager():
    """Retorna la instancia del gestor de backups"""
    global backup_manager
    if backup_manager is None:
        backup_manager = BackupManager()
    return backup_manager

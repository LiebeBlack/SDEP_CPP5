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

import os
import shutil
import sqlite3
import gzip
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class BackupManager:
    """Gestor de backups de base de datos"""
    
    def __init__(self):
        """Inicializa el gestor de backups"""
        # Importar settings aquí para evitar problemas de inicialización
        from src.config import settings
        
        self.backup_dir = Path(settings.base_dir) / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = Path(settings.base_dir) / settings.database_path
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        
        # Configuración de rotación
        self.max_backups = 10  # Máximo número de backups a mantener
        self.backup_retention_days = 30  # Días a mantener backups
        
        # Cargar metadatos existentes
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Carga metadatos de backups existentes"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error cargando metadatos: {e}")
                return {}
        return {}
    
    def _save_metadata(self):
        """Guarda metadatos de backups"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando metadatos: {e}")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calcula checksum SHA256 de un archivo"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculando checksum: {e}")
            return ""
    
    @staticmethod
    def _online_copy(source: Path, destination: Path) -> None:
        """
        Copia una base de datos SQLite de forma consistente

        Usa la API sqlite3 .backup() que produce una copia correcta
        aunque existan conexiones activas al archivo origen.
        """
        import sqlite3

        temp_path = destination.with_name(destination.name + ".tmp")
        try:
            src_conn = sqlite3.connect(str(source))
            try:
                dst_conn = sqlite3.connect(str(temp_path))
                try:
                    src_conn.backup(dst_conn)
                finally:
                    dst_conn.close()
            finally:
                src_conn.close()
            shutil.move(str(temp_path), str(destination))
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    def _compress_file(self, source: Path, destination: Path) -> bool:
        """Comprime un archivo usando gzip"""
        try:
            with open(source, 'rb') as f_in:
                with gzip.open(destination, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception as e:
            logger.error(f"Error comprimiendo archivo: {e}")
            return False
    
    def _decompress_file(self, source: Path, destination: Path) -> bool:
        """Descomprime un archivo gzip"""
        try:
            with gzip.open(source, 'rb') as f_in:
                with open(destination, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception as e:
            logger.error(f"Error descomprimiendo archivo: {e}")
            return False
    
    def create_backup(self, backup_name: Optional[str] = None, compress: bool = True) -> Dict:
        """
        Crea un backup de la base de datos
        
        Args:
            backup_name: Nombre personalizado para el backup
            compress: Si se debe comprimir el backup
            
        Returns:
            Dict con información del backup creado
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = backup_name or f"backup_{timestamp}"
        
        # Crear archivo de backup
        backup_filename = f"{backup_name}.db"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Respaldo consistente usando la API de copia de SQLite,
            # segura aunque haya conexiones abiertas al archivo.
            self._online_copy(self.db_path, backup_path)
            
            # Comprimir si se solicita
            if compress:
                compressed_path = backup_path.with_suffix('.db.gz')
                if self._compress_file(backup_path, compressed_path):
                    backup_path.unlink()  # Eliminar original
                    backup_path = compressed_path
                    backup_filename = compressed_path.name
            
            # Calcular checksum y tamaño sobre el archivo almacenado final
            checksum = self._calculate_checksum(backup_path)
            original_checksum = self._calculate_checksum(self.db_path)
            
            # Guardar metadatos
            backup_info = {
                "name": backup_name,
                "filename": backup_filename,
                "path": str(backup_path),
                "timestamp": timestamp,
                "size_bytes": backup_path.stat().st_size,
                "checksum": checksum,
                "compressed": compress,
                "original_db_checksum": original_checksum,
                "version": 2
            }
            
            self.metadata[backup_name] = backup_info
            self._save_metadata()
            
            logger.info(f"Backup creado exitosamente: {backup_name}")
            return backup_info
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            # Limpiar archivos parciales
            if backup_path.exists():
                backup_path.unlink()
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
        backup_path = Path(backup_info["path"])
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Archivo de backup no encontrado: {backup_path}")
        
        try:
            # Crear backup del estado actual antes de restaurar
            current_backup = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.create_backup(current_backup, compress=False)
            
            # Descomprimir si es necesario
            temp_restore_path = backup_path
            if backup_info["compressed"]:
                temp_restore_path = self.backup_dir / f"temp_restore_{backup_name}.db"
                if not self._decompress_file(backup_path, temp_restore_path):
                    raise Exception("Error descomprimiendo backup")
            
            # Verificar checksum si se solicita
            if verify_checksum and backup_info.get("checksum"):
                if backup_info.get("version") == 2:
                    # v2: el checksum corresponde al archivo guardado (comprimido o no)
                    if self._calculate_checksum(backup_path) != backup_info["checksum"]:
                        raise Exception("Checksum verification failed: backup may be corrupted")
                    if (
                        backup_info.get("original_db_checksum")
                        and backup_info.get("compressed")
                        and self._calculate_checksum(temp_restore_path)
                        != backup_info["original_db_checksum"]
                    ):
                        raise Exception(
                            "Checksum verification failed: contenido del backup inconsistente")
                elif backup_info.get("compressed"):
                    # Legado: el checksum correspondía al contenido descomprimido
                    if self._calculate_checksum(temp_restore_path) != backup_info["checksum"]:
                        raise Exception("Checksum verification failed: backup may be corrupted")
            
            # Liberar conexiones del motor antes de reemplazar el archivo
            try:
                from src.config import db_config
                db_config.SessionLocal.remove()
                db_config.engine.dispose()
            except Exception:
                pass
            
            # Restaurar base de datos
            shutil.copy2(temp_restore_path, self.db_path)
            
            try:
                from src.config import db_config
                db_config.engine.dispose()
            except Exception:
                pass
            
            # Limpiar archivo temporal
            if temp_restore_path != backup_path and temp_restore_path.exists():
                temp_restore_path.unlink()
            
            logger.info(f"Backup restaurado exitosamente: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error restaurando backup: {e}")
            raise
    
    def list_backups(self) -> List[Dict]:
        """
        Lista todos los backups disponibles
        
        Returns:
            Lista de información de backups
        """
        backups = []
        for name, info in self.metadata.items():
            backup_path = Path(info["path"])
            exists = backup_path.exists()
            info["exists"] = exists
            info["age_days"] = (datetime.now() - datetime.strptime(info["timestamp"], "%Y%m%d_%H%M%S")).days
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
        backup_path = Path(backup_info["path"])
        
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
    
    def rotate_backups(self) -> Dict:
        """
        Rotación automática de backups antiguos
        
        Elimina backups que exceden los límites de retención
        según la configuración
        
        Returns:
            Dict con estadísticas de la rotación
        """
        stats = {
            "total_before": len(self.metadata),
            "deleted_count": 0,
            "deleted_backups": [],
            "total_after": 0
        }
        
        try:
            backups = self.list_backups()
            
            # Eliminar backups por antigüedad (iterar sobre una copia)
            cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)
            pendientes = list(backups)
            
            for backup in pendientes:
                backup_date = datetime.strptime(backup["timestamp"], "%Y%m%d_%H%M%S")
                excede_maximo = len(pendientes) > self.max_backups
                
                if backup_date < cutoff_date or excede_maximo:
                    if self.delete_backup(backup["name"]):
                        stats["deleted_count"] += 1
                        stats["deleted_backups"].append(backup["name"])
                        pendientes.remove(backup)
            
            stats["total_after"] = len(pendientes)
            logger.info(f"Rotación de backups completada: {stats['deleted_count']} eliminados")
            
        except Exception as e:
            logger.error(f"Error en rotación de backups: {e}")
        
        return stats
    
    def verify_backup_integrity(self, backup_name: str) -> Dict:
        """
        Verifica la integridad de un backup específico
        
        Args:
            backup_name: Nombre del backup a verificar
            
        Returns:
            Dict con resultados de verificación
        """
        if backup_name not in self.metadata:
            raise ValueError(f"Backup no encontrado: {backup_name}")
        
        backup_info = self.metadata[backup_name]
        backup_path = Path(backup_info["path"])
        
        result = {
            "backup_name": backup_name,
            "exists": backup_path.exists(),
            "checksum_valid": False,
            "size_correct": False,
            "integrity_ok": False
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
                        result["exists"] and result["size_correct"]
                        and result["checksum_valid"]
                    )
                elif backup_info.get("compressed"):
                    # Legado: verificar contra el contenido descomprimido
                    try:
                        with gzip.open(backup_path, "rb") as f:
                            contenido = hashlib.sha256()
                            for bloque in iter(lambda: f.read(65536), b""):
                                contenido.update(bloque)
                        result["checksum_valid"] = (
                            contenido.hexdigest() == backup_info["checksum"]
                        )
                    except Exception:
                        result["checksum_valid"] = False
                    result["integrity_ok"] = (
                        result["exists"] and result["checksum_valid"]
                    )
                else:
                    current_checksum = self._calculate_checksum(backup_path)
                    result["checksum_valid"] = current_checksum == backup_info["checksum"]
                    result["integrity_ok"] = result["checksum_valid"] and result["size_correct"]
            
        except Exception as e:
            logger.error(f"Error verificando integridad: {e}")
        
        return result
    
    def create_scheduled_backup(self) -> Dict:
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
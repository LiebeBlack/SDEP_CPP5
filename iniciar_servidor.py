"""
Script de inicialización automática del servidor de sincronización

Este script configura e inicia el servidor central en cualquier computadora
sin necesidad de configuración manual. Crea la base de datos, inicializa el
esquema, crea usuarios por defecto y registra dispositivos automáticamente.

Uso:
    python iniciar_servidor.py                    # Modo autoconfigurado
    python iniciar_servidor.py --config archivo.json  # Con configuración personalizada
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def obtener_ip_local() -> str:
    """Obtiene la dirección IP local de la computadora"""
    import socket

    try:
        # Conectar a un servidor externo para obtener la IP local
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip_local = s.getsockname()[0]
        return ip_local
    except Exception:
        return "127.0.0.1"


def cargar_config(ruta_config: str | None = None) -> dict:
    """Carga la configuración del servidor desde archivo o usa valores por defecto"""
    if ruta_config and Path(ruta_config).exists():
        with open(ruta_config, "r", encoding="utf-8") as f:
            return json.load(f)

    # Configuración por defecto para ejecución local
    # host: 0.0.0.0 permite conexiones desde cualquier IP en la red local
    return {
        "db": "sqlite:///sync_central.db",
        "blobs": "sync_blobs",
        "host": "0.0.0.0",  # Acepta conexiones de cualquier IP en la red
        "puerto": 8765,
        "certificado": None,
        "clave": None,
        "max_ops_por_lote": 500,
        "max_bytes_peticion": 3 * 1024 * 1024,
        "max_bytes_blob": 64 * 1024 * 1024,
        "peticiones_por_minuto": 120,
    }


def inicializar_base_de_datos(config: dict) -> None:
    """Inicializa la base de datos y crea el esquema necesario"""
    from sync_agent.servidor import NucleoCentral, ServidorConfig

    logger.info("Inicializando base de datos central...")

    servidor_config = ServidorConfig(
        url_db=config["db"],
        dir_blobs=Path(config["blobs"]),
        host=config["host"],
        puerto=config["puerto"],
        certificado=config.get("certificado"),
        clave=config.get("clave"),
        max_ops_por_lote=config.get("max_ops_por_lote", 500),
        max_bytes_peticion=config.get("max_bytes_peticion", 3 * 1024 * 1024),
        max_bytes_blob=config.get("max_bytes_blob", 64 * 1024 * 1024),
        peticiones_por_minuto=config.get("peticiones_por_minuto", 120),
    )

    nucleo = NucleoCentral(servidor_config)
    nucleo.cerrar()

    logger.info("Base de datos inicializada correctamente")


def crear_usuarios_por_defecto(config: dict) -> None:
    """Crea usuarios administrativos por defecto si no existen"""
    from sync_agent.servidor import NucleoCentral, ServidorConfig

    logger.info("Creando usuarios por defecto...")

    servidor_config = ServidorConfig(
        url_db=config["db"],
        dir_blobs=Path(config["blobs"]),
        host=config["host"],
        puerto=config["puerto"],
    )

    nucleo = NucleoCentral(servidor_config)

    try:
        from src.services.auth_service import AuthService

        sesion = nucleo.SessionFactory()
        try:
            servicio = AuthService(sesion)

            # Usuarios por defecto
            usuarios = [
                ("admin", "Admin1234", "admin", "Administrador del Sistema"),
                ("manager", "Gestor1234", "manager", "Gestor Principal"),
                ("user", "Usuario1234", "user", "Usuario Estándar"),
                ("viewer", "Lector1234", "viewer", "Lector de Solo Lectura"),
            ]

            for username, password, rol, nombre_completo in usuarios:
                if servicio.usuario_por_username(username) is None:
                    servicio.crear_usuario(
                        username, password, rol, nombre_completo, debe_cambiar_password=False
                    )
                    logger.info(f"Usuario '{username}' creado con rol '{rol}'")
                else:
                    logger.info(f"Usuario '{username}' ya existe, omitiendo")

            sesion.commit()
        finally:
            sesion.close()
    except Exception as e:
        logger.error(f"Error al crear usuarios: {e}", exc_info=True)
    finally:
        nucleo.cerrar()


def crear_dispositivo_por_defecto(config: dict, nombre: str = "Computadora Principal") -> tuple[str, str]:
    """Crea un dispositivo por defecto para conexión local"""
    from sync_agent.servidor import NucleoCentral, ServidorConfig

    logger.info(f"Creando dispositivo por defecto: {nombre}...")

    servidor_config = ServidorConfig(
        url_db=config["db"],
        dir_blobs=Path(config["blobs"]),
        host=config["host"],
        puerto=config["puerto"],
    )

    nucleo = NucleoCentral(servidor_config)

    try:
        dispositivo_id, token = nucleo.crear_dispositivo(nombre)
        logger.info(f"Dispositivo creado: ID={dispositivo_id}")
        return dispositivo_id, token
    finally:
        nucleo.cerrar()


def iniciar_servidor(config: dict) -> None:
    """Inicia el servidor con la configuración proporcionada"""
    from sync_agent.servidor import ServidorConfig, ejecutar_servidor

    servidor_config = ServidorConfig(
        url_db=config["db"],
        dir_blobs=Path(config["blobs"]),
        host=config["host"],
        puerto=config["puerto"],
        certificado=config.get("certificado"),
        clave=config.get("clave"),
        max_ops_por_lote=config.get("max_ops_por_lote", 500),
        max_bytes_peticion=config.get("max_bytes_peticion", 3 * 1024 * 1024),
        max_bytes_blob=config.get("max_bytes_blob", 64 * 1024 * 1024),
        peticiones_por_minuto=config.get("peticiones_por_minuto", 120),
    )

    ip_local = obtener_ip_local()
    protocolo = "https" if config.get("certificado") else "http"

    logger.info("=" * 60)
    logger.info("INICIANDO SERVIDOR DE SINCRONIZACIÓN")
    logger.info("=" * 60)
    logger.info(f"Base de datos: {config['db']}")
    logger.info(f"Directorio de blobs: {config['blobs']}")
    logger.info(f"Host de escucha: {config['host']}")
    logger.info(f"Puerto: {config['puerto']}")
    logger.info(f"Protocolo: {protocolo}")
    logger.info("=" * 60)
    logger.info("URLS PARA CONEXIÓN DESDE OTROS DISPOSITIVOS:")
    logger.info(f"  Desde esta computadora: {protocolo}://127.0.0.1:{config['puerto']}")
    logger.info(f"  Desde otros dispositivos en la red: {protocolo}://{ip_local}:{config['puerto']}")
    logger.info("=" * 60)
    logger.info("IMPORTANTE: Para conectar desde Android u otros equipos,")
    logger.info(f"use la URL: {protocolo}://{ip_local}:{config['puerto']}")
    logger.info("=" * 60)

    try:
        exit_code = ejecutar_servidor(servidor_config)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nServidor detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error al iniciar servidor: {e}", exc_info=True)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Inicializa e inicia el servidor de sincronización automáticamente"
    )
    parser.add_argument(
        "--config",
        help="Archivo JSON de configuración (usará valores por defecto si no se especifica)",
    )
    parser.add_argument(
        "--sin-usuarios",
        action="store_true",
        help="No crear usuarios por defecto",
    )
    parser.add_argument(
        "--sin-dispositivo",
        action="store_true",
        help="No crear dispositivo por defecto",
    )
    parser.add_argument(
        "--solo-inicializar",
        action="store_true",
        help="Solo inicializa la base de datos y no inicia el servidor",
    )

    args = parser.parse_args()

    # Cargar configuración
    config = cargar_config(args.config)

    # Inicializar base de datos
    inicializar_base_de_datos(config)

    # Crear usuarios por defecto
    if not args.sin_usuarios:
        crear_usuarios_por_defecto(config)

    # Crear dispositivo por defecto
    if not args.sin_dispositivo:
        dispositivo_id, token = crear_dispositivo_por_defecto(config)
        print("\n" + "=" * 60)
        print("DISPOSITIVO POR DEFECTO CREADO")
        print("=" * 60)
        print(f"ID del dispositivo: {dispositivo_id}")
        print(f"Token: {token}")
        print("\nGUARDE ESTE TOKEN - no se puede recuperar después")
        print("Úselo para conectar este u otro equipo al servidor")
        print("=" * 60 + "\n")

    # Iniciar servidor (o solo inicializar)
    if not args.solo_inicializar:
        iniciar_servidor(config)
    else:
        logger.info("Inicialización completada. Use --sin-solo-inicializar para iniciar el servidor.")


if __name__ == "__main__":
    main()

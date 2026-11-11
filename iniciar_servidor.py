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
        if ip_local and not ip_local.startswith("127."):
            return ip_local
    except Exception:
        pass
    try:
        # Sin salida a Internet (o UDP bloqueado) se intenta resolver el
        # propio nombre del equipo, que suele dar la IP de la LAN.
        ip_local = socket.gethostbyname(socket.gethostname())
        if ip_local and not ip_local.startswith("127."):
            return ip_local
    except Exception:
        pass
    return "127.0.0.1"


def cargar_config(ruta_config: str | None = None) -> dict:
    """Carga la configuración del servidor desde archivo o usa valores por defecto"""
    if ruta_config:
        ruta = Path(ruta_config)
        if not ruta.exists():
            logger.error("El archivo de configuración no existe: %s", ruta_config)
            sys.exit(2)
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.error("No se pudo leer la configuración %s: %s", ruta_config, e)
            sys.exit(2)
        if not isinstance(config, dict):
            logger.error("La configuración %s no es un objeto JSON", ruta_config)
            sys.exit(2)
        return config

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
        # La configuración estándar habilita el alta de la app móvil en la
        # red; un archivo personalizado debe activarlo explícitamente y puede
        # desactivarlo para exigir alta supervisada desde la consola.
        "emparejamiento_abierto": True,
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
    """Aprovisiona las cuentas genéricas iniciales sin reemplazar cuentas propias."""
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
        from sync_agent.cuentas_iniciales import preparar_cuentas_iniciales

        sesion = nucleo.SessionFactory()
        try:
            servicio = AuthService(sesion)
            creadas, requieren_cambio = preparar_cuentas_iniciales(servicio)
            for username in creadas:
                logger.info("Cuenta genérica '%s' creada; use su clave inicial y cámbiela", username)
            for username in requieren_cambio:
                logger.warning("La cuenta '%s' conserva una clave inicial conocida; debe rotarla", username)
            sesion.commit()
        finally:
            sesion.close()
    except Exception as e:
        logger.error(f"Error al crear usuarios: {e}", exc_info=True)
    finally:
        nucleo.cerrar()


def crear_dispositivo_por_defecto(
    config: dict, nombre: str = "Computadora Principal"
) -> tuple[str | None, str | None]:
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
        # Solo se crea el dispositivo si el nodo aún no tiene ninguno:
        # ejecutarlo en cada arranque generaba dispositivos y tokens nuevos
        # duplicados en cada reinicio del servidor.
        if nucleo.listar_dispositivos():
            logger.info("Ya existen dispositivos registrados; no se crea uno nuevo")
            return None, None
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
        # El alta móvil es opt-in: la configuración estándar la activa
        # explícitamente; un archivo personalizado que omita la clave
        # conserva el nodo cerrado.
        emparejamiento_abierto=config.get("emparejamiento_abierto", False),
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
    logger.info(
        f"  Desde otros dispositivos en la red: {protocolo}://{ip_local}:{config['puerto']}"
    )
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
        if dispositivo_id:
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
        logger.info(
            "Inicialización completada. Ejecute de nuevo sin --solo-inicializar para "
            "iniciar el servidor."
        )


if __name__ == "__main__":
    main()

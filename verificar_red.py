"""
Script auxiliar para verificar la configuración de red y conexión del servidor

Este script ayuda a diagnosticar problemas de conexión entre el servidor
y los clientes (Android, otros PCs en la red).
"""

import socket
import sys


def obtener_ip_local():
    """Obtiene la dirección IP local de la computadora"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip_local = s.getsockname()[0]
        return ip_local
    except Exception as e:
        print(f"❌ Error al obtener IP local: {e}")
        return None


def verificar_puerto(puerto=8765):
    """Verifica si el puerto está en uso"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            resultado = s.connect_ex(("127.0.0.1", puerto))
            if resultado == 0:
                return True
        return False
    except Exception as e:
        print(f"❌ Error al verificar puerto: {e}")
        return None


def verificar_conexion_servidor(ip, puerto=8765):
    """Verifica si el servidor responde"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            resultado = s.connect_ex((ip, puerto))
            if resultado == 0:
                return True
        return False
    except Exception as e:
        print(f"❌ Error al conectar al servidor: {e}")
        return None


def main():
    print("=" * 60)
    print("VERIFICACIÓN DE RED Y SERVIDOR")
    print("=" * 60)

    # Obtener IP local
    print("\n1. Obteniendo IP local...")
    ip_local = obtener_ip_local()
    if ip_local:
        print(f"✅ IP local detectada: {ip_local}")
    else:
        print("❌ No se pudo detectar la IP local")
        return 1

    # Verificar puerto local
    print("\n2. Verificando puerto 8765...")
    puerto_en_uso = verificar_puerto(8765)
    if puerto_en_uso:
        print("✅ El puerto 8765 está en uso (servidor probablemente ejecutándose)")
    elif puerto_en_uso is False:
        print("⚠️  El puerto 8765 no está en uso (servidor no está ejecutándose)")
    else:
        print("❌ No se pudo verificar el puerto")

    # Verificar conexión local
    print("\n3. Verificando conexión local (127.0.0.1:8765)...")
    conexion_local = verificar_conexion_servidor("127.0.0.1", 8765)
    if conexion_local:
        print("✅ El servidor responde en localhost")
    elif conexion_local is False:
        print("❌ El servidor no responde en localhost")
    else:
        print("❌ No se pudo verificar la conexión local")

    # Verificar conexión por IP
    print(f"\n4. Verificando conexión por IP ({ip_local}:8765)...")
    conexion_ip = verificar_conexion_servidor(ip_local, 8765)
    if conexion_ip:
        print(f"✅ El servidor responde en {ip_local}:8765")
    elif conexion_ip is False:
        print(f"❌ El servidor no responde en {ip_local}:8765")
        print("   Esto puede indicar que el servidor no está escuchando en 0.0.0.0")
    else:
        print("❌ No se pudo verificar la conexión por IP")

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"IP local: {ip_local or 'No detectada'}")
    print(f"URL para esta PC: http://127.0.0.1:8765")
    print(
        f"URL para Android/otros PCs: http://{ip_local}:8765"
        if ip_local
        else "URL para Android: No disponible"
    )
    print("=" * 60)

    if puerto_en_uso and conexion_local and conexion_ip:
        print("\n✅ El servidor está correctamente configurado para red local")
        print("   Android y otros PCs deberían poder conectarse")
        return 0
    elif puerto_en_uso and conexion_local and not conexion_ip:
        print("\n⚠️  El servidor está ejecutándose pero solo en localhost")
        print("   Use --host 0.0.0.0 al iniciar el servidor")
        return 1
    elif not puerto_en_uso:
        print("\n⚠️  El servidor no está ejecutándose")
        print("   Inicie con: python iniciar_servidor.py")
        return 1
    else:
        print("\n❌ Hay problemas con la configuración del servidor")
        return 1


if __name__ == "__main__":
    sys.exit(main())

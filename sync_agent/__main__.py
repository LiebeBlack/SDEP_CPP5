"""
Interfaz de línea de comandos del Agente de Sincronización

Permite operar el paquete sin abrir la aplicación de escritorio::

    py -3 -m sync_agent init                      # prepara este equipo
    py -3 -m sync_agent agente                    # sincroniza en segundo plano
    py -3 -m sync_agent agente --una-vez          # un solo ciclo y salir
    py -3 -m sync_agent estado                    # resumen del equipo
    py -3 -m sync_agent conflictos                # bandeja de conflictos
    py -3 -m sync_agent servidor --db sqlite:///central.db --crear-dispositivo "Secretaría"
    py -3 -m sync_agent servidor --db sqlite:///central.db    # arranca el nodo central
    py -3 -m sync_agent dispositivos --db sqlite:///central.db --listar

El nodo central es un servicio HTTP propio (biblioteca estándar) que escribe el
SQLite central en modo WAL: los puestos nunca escriben directamente en él.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("sync_agent.cli")

SALIDA_CORRECTA = 0
SALIDA_ERROR = 1
SALIDA_INACTIVO = 2


# ----------------------------------------------------------------------
# Utilidades comunes
# ----------------------------------------------------------------------
def _configurar_logging(verboso: bool = False, silencioso: bool = False) -> None:
    """
    Configura el registro a consola del proceso de línea de comandos

    El registro va a **stderr** para que la salida estándar contenga solo el
    resultado del comando: ``estado --json`` y ``conflictos --json`` existen para
    que otro programa los consuma, y una línea de registro delante del JSON lo
    volvería ilegible.
    """
    nivel = logging.DEBUG if verboso else (logging.WARNING if silencioso else logging.INFO)
    raiz = logging.getLogger()
    raiz.setLevel(nivel)
    for manejador in list(raiz.handlers):
        raiz.removeHandler(manejador)
    manejador = logging.StreamHandler(sys.stderr)
    manejador.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    raiz.addHandler(manejador)


def _imprimir(datos: Any, como_json: bool = False) -> None:
    """Imprime un diccionario en texto legible o en JSON"""
    if como_json:
        print(json.dumps(datos, ensure_ascii=False, indent=2, default=str))
        return
    for clave, valor in datos.items():
        print(f"{str(clave).replace('_', ' ').capitalize():.<32} {valor}")


def _tabla(filas: list[dict], columnas: list[str]) -> None:
    """Imprime filas en columnas alineadas (salida de consola simple)"""
    if not filas:
        print("(sin registros)")
        return
    anchos = {
        columna: max(len(columna), *(len(str(fila.get(columna, ""))) for fila in filas))
        for columna in columnas
    }
    print("  ".join(columna.ljust(anchos[columna]) for columna in columnas))
    print("  ".join("-" * anchos[columna] for columna in columnas))
    for fila in filas:
        print("  ".join(str(fila.get(columna, "")).ljust(anchos[columna]) for columna in columnas))


def _abrir_local():
    """Abre la base local del sistema, dejando el esquema del agente listo"""
    from src.config import db_config

    db_config.init_db()
    db_config.preparar_sincronizacion()
    # La captura se engancha siempre desde la herramienta de consola: quien la
    # usa ha decidido replicar este equipo, y las escrituras hechas mientras
    # tanto deben quedar en el journal.
    db_config.activar_captura_sincronizacion()
    return db_config


def _resumen_local(como_json: bool = False) -> dict:
    """Reúne el estado operativo del agente guardado en la base local"""
    from sync_agent.config import cargar
    from sync_agent.esquema import (
        DIFERIDA,
        DIRECCION_SALIDA,
        PENDIENTE,
        ConflictoSync,
        CursorSync,
        EstadoSync,
        JournalOp,
    )

    db_config = _abrir_local()
    config = cargar()
    sesion = db_config.new_session()
    try:
        pendientes = (
            sesion.query(JournalOp)
            .filter(JournalOp.estado.in_((PENDIENTE, DIFERIDA)), JournalOp.direccion == DIRECCION_SALIDA)
            .count()
        )
        conflictos = sesion.query(ConflictoSync).filter(ConflictoSync.resuelto == 0).count()
        cursor = sesion.get(CursorSync, 1)
        estado = {fila.clave: fila.valor for fila in sesion.query(EstadoSync).all()}
    finally:
        db_config.close_session(sesion)

    return {
        "habilitado": config.habilitado,
        "configurado": config.configurado,
        "servidor": config.url_servidor or "(sin definir)",
        "equipo": config.nombre_equipo or "(sin nombre)",
        "dispositivo_id": config.dispositivo_id or "(sin asignar)",
        "intervalo_segundos": config.intervalo_segundos,
        "token": "configurado" if config.token else "(falta)",
        "pendientes_por_enviar": int(pendientes or 0),
        "conflictos_sin_revisar": int(conflictos or 0),
        "ultimo_seq_aplicado": int(cursor.ultimo_seq) if cursor else 0,
        "ultima_sincronizacion": estado.get("ultima_sincronizacion"),
        "desfase_reloj_segundos": estado.get("desfase_reloj"),
        "problemas": "; ".join(config.problemas()) or None,
    }


# ----------------------------------------------------------------------
# Subcomandos
# ----------------------------------------------------------------------
def cmd_init(args: argparse.Namespace) -> int:
    """Prepara el equipo: esquema, captura y adopción de los datos existentes"""
    from sync_agent.captura import adoptar_existentes

    db_config = _abrir_local()
    adoptadas = 0
    if not args.sin_adoptar:
        sesion = db_config.new_session()
        try:
            adoptadas = adoptar_existentes(sesion)
            sesion.commit()
        except Exception:
            sesion.rollback()
            logger.error("No se pudieron adoptar los datos existentes", exc_info=True)
            return SALIDA_ERROR
        finally:
            db_config.close_session(sesion)

    resumen = _resumen_local()
    resumen["filas_adoptadas"] = adoptadas
    print("Equipo preparado para la sincronización.")
    _imprimir(resumen)
    if resumen.get("problemas"):
        print("\nAún hay pendientes de configuración:")
        print(f"  {resumen['problemas']}")
        print("Defínalos en Configuración → Sincronización o con las variables SDP_SYNC_*.")
    return SALIDA_CORRECTA


def cmd_agente(args: argparse.Namespace) -> int:
    """Ejecuta el agente en primer plano (o un solo ciclo con --una-vez)"""
    import time

    from sync_agent import iniciar_agente
    from sync_agent.config import cargar

    _abrir_local()
    config = cargar()

    if args.una_vez:
        from sync_agent.agente import AgenteSincronizacion

        agente = AgenteSincronizacion(config)
        resultado = agente.ciclo()
        _imprimir(resultado, como_json=args.json)
        return SALIDA_CORRECTA if resultado.get("correcto") else SALIDA_ERROR

    if not config.activo:
        problemas = config.problemas() or ["sincronización deshabilitada en la configuración"]
        print("El agente no puede arrancar todavía:")
        for problema in problemas:
            print(f"  - {problema}")
        return SALIDA_INACTIVO

    agente = iniciar_agente(config)
    if not agente.activo():  # pragma: no cover - defensa ante carreras de arranque
        print("No se pudo iniciar el hilo de sincronización.")
        return SALIDA_INACTIVO

    print(
        f"Sincronizando cada {config.intervalo_segundos} s contra {config.url_servidor}\n"
        "Pulse Ctrl+C para detener."
    )
    try:
        while agente.activo():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nDeteniendo el agente…")
    finally:
        from sync_agent import detener_agente

        detener_agente(timeout=10.0)
    _imprimir(agente.estado(), como_json=args.json)
    return SALIDA_CORRECTA


def cmd_estado(args: argparse.Namespace) -> int:
    """Muestra el estado del equipo y de sus pendientes"""
    resumen = _resumen_local(como_json=args.json)
    _imprimir(resumen, como_json=args.json)
    return SALIDA_CORRECTA


def cmd_conflictos(args: argparse.Namespace) -> int:
    """Lista la bandeja de conflictos local (valores que perdieron una mezcla)"""
    from sync_agent.comun import loads
    from sync_agent.esquema import ConflictoSync

    db_config = _abrir_local()
    sesion = db_config.new_session()
    try:
        consulta = sesion.query(ConflictoSync)
        if not args.todos:
            consulta = consulta.filter(ConflictoSync.resuelto == 0)
        filas = consulta.order_by(ConflictoSync.detectado_en.desc()).limit(args.limite).all()
        registros = [
            {
                "tabla": fila.tabla,
                "fila": (fila.fila_uuid or "")[:8],
                "campo": fila.campo,
                "ganador": fila.ganador,
                "regla": fila.regla,
                "valor_local": _texto_corto(loads(fila.valor_local)),
                "valor_remoto": _texto_corto(loads(fila.valor_remoto)),
                "detectado_en": fila.detectado_en.isoformat(timespec="seconds")
                if fila.detectado_en
                else "",
            }
            for fila in filas
        ]
    finally:
        db_config.close_session(sesion)

    if args.json:
        print(json.dumps(registros, ensure_ascii=False, indent=2, default=str))
        return SALIDA_CORRECTA
    print(f"Conflictos {'registrados' if args.todos else 'sin revisar'}: {len(registros)}")
    _tabla(
        registros,
        ["tabla", "campo", "ganador", "regla", "valor_local", "valor_remoto", "detectado_en"],
    )
    if registros and not args.todos:
        print(
            "\nEl valor perdedor se conserva aquí: ninguna mezcla descarta datos en silencio."
        )
    return SALIDA_CORRECTA


def _texto_corto(valor: Any, limite: int = 28) -> str:
    """Reduce un valor a una línea corta para la tabla de consola"""
    if valor is None:
        return "—"
    if isinstance(valor, (bytes, bytearray)):
        texto = f"<binario {len(valor)} B>"
    else:
        texto = str(valor).replace("\n", " ")
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"


def _nucleo(args: argparse.Namespace):
    """Construye el núcleo del nodo central a partir de los argumentos"""
    from sync_agent.servidor import NucleoCentral, ServidorConfig

    config = ServidorConfig(
        url_db=args.db,
        dir_blobs=Path(args.blobs) if args.blobs else _dir_blobs_por_defecto(args.db),
        host=args.host,
        puerto=args.puerto,
        certificado=args.cert,
        clave=args.key,
    )
    return NucleoCentral(config), config


def _dir_blobs_por_defecto(url_db: str) -> Path:
    """Carpeta de binarios junto al archivo de base del nodo central"""
    ruta = url_db.split("sqlite:///")[-1] if "sqlite:///" in url_db else "sync_central.db"
    archivo = Path(ruta)
    return archivo.with_name(archivo.stem + "_blobs")


def _administrar_dispositivos(args: argparse.Namespace) -> int:
    """Ejecuta una operación administrativa sobre el nodo central"""
    nucleo, _config = _nucleo(args)
    try:
        if args.crear_dispositivo:
            dispositivo_id, token = nucleo.crear_dispositivo(args.crear_dispositivo)
            print(f"Puesto '{args.crear_dispositivo}' creado.")
            print(f"  Identificador: {dispositivo_id}")
            print(f"  Token:         {token}")
            print(
                "\nGuarde el token ahora: no se puede recuperar después "
                "(en la base solo queda su hash)."
            )
            print("En el puesto, regístrelo con SDP_SYNC_TOKEN o en Configuración → Sincronización.")
            return SALIDA_CORRECTA

        if args.revocar_dispositivo:
            if nucleo.revocar_dispositivo(args.revocar_dispositivo):
                print(f"Puesto {args.revocar_dispositivo} revocado: ya no podrá sincronizar.")
                return SALIDA_CORRECTA
            print(f"No existe un puesto con identificador {args.revocar_dispositivo}.")
            return SALIDA_ERROR

        if args.purgar_historial is not None:
            borradas = nucleo.purgar_historial(args.purgar_historial)
            print(f"Operaciones retiradas del historial central: {borradas}")
            return SALIDA_CORRECTA

        if args.exportar_conflictos:
            conflictos = nucleo.conflictos(solo_pendientes=not args.todos, limite=args.limite)
            destino = Path(args.exportar_conflictos)
            destino.write_text(
                json.dumps(conflictos, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
            print(f"Conflictos exportados a {destino} ({len(conflictos)} registros).")
            return SALIDA_CORRECTA

        # Sin operación concreta: se lista todo
        dispositivos = nucleo.listar_dispositivos()
        if args.json:
            print(json.dumps(dispositivos, ensure_ascii=False, indent=2, default=str))
            return SALIDA_CORRECTA
        print(f"Puestos registrados: {len(dispositivos)}")
        _tabla(dispositivos, ["dispositivo_id", "nombre", "activo", "ultima_conexion"])
        return SALIDA_CORRECTA
    finally:
        nucleo.cerrar()


def cmd_servidor(args: argparse.Namespace) -> int:
    """Arranca el nodo central o ejecuta una tarea administrativa"""
    administrativo = (
        args.crear_dispositivo
        or args.revocar_dispositivo
        or args.listar_dispositivos
        or args.exportar_conflictos
        or args.purgar_historial is not None
    )
    if administrativo:
        return _administrar_dispositivos(args)

    from sync_agent.servidor import ServidorConfig, ejecutar_servidor

    config = ServidorConfig(
        url_db=args.db,
        dir_blobs=Path(args.blobs) if args.blobs else _dir_blobs_por_defecto(args.db),
        host=args.host,
        puerto=args.puerto,
        certificado=args.cert,
        clave=args.key,
    )
    print(
        f"Nodo central escuchando en http{'s' if config.certificado else ''}://"
        f"{config.host}:{config.puerto}\nBase central: {config.url_db}"
    )
    return ejecutar_servidor(config)


def cmd_dispositivos(args: argparse.Namespace) -> int:
    """Administra los puestos autorizados en el nodo central"""
    args.listar_dispositivos = True
    if args.crear:
        args.crear_dispositivo = args.crear
    if args.revocar:
        args.revocar_dispositivo = args.revocar
    return _administrar_dispositivos(args)


# ----------------------------------------------------------------------
# Argumentos
# ----------------------------------------------------------------------
def _parser() -> argparse.ArgumentParser:
    """Construye el analizador de argumentos de la herramienta"""
    parser = argparse.ArgumentParser(
        prog="py -3 -m sync_agent",
        description="Agente de Sincronización de Datos Bidireccional (SDEP-CPP5)",
    )
    parser.add_argument("-v", "--verboso", action="store_true", help="Registro detallado")
    parser.add_argument("-q", "--silencioso", action="store_true", help="Solo avisos y errores")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    # --- init ---
    p_init = subparsers.add_parser(
        "init", help="Prepara este equipo (esquema, captura y adopción de datos previos)"
    )
    p_init.add_argument(
        "--sin-adoptar",
        action="store_true",
        help="No dar identidad global a los datos que ya existían en este puesto",
    )
    p_init.set_defaults(func=cmd_init)

    # --- agente ---
    p_agente = subparsers.add_parser("agente", help="Sincroniza en segundo plano")
    p_agente.add_argument(
        "--una-vez", action="store_true", help="Ejecuta un solo ciclo y termina"
    )
    p_agente.add_argument("--json", action="store_true", help="Salida en JSON")
    p_agente.set_defaults(func=cmd_agente)

    # --- estado ---
    p_estado = subparsers.add_parser("estado", help="Estado de la sincronización en este equipo")
    p_estado.add_argument("--json", action="store_true", help="Salida en JSON")
    p_estado.set_defaults(func=cmd_estado)

    # --- conflictos ---
    p_conf = subparsers.add_parser("conflictos", help="Bandeja de conflictos de la mezcla")
    p_conf.add_argument("--todos", action="store_true", help="Incluir los ya revisados")
    p_conf.add_argument("--limite", type=int, default=200, help="Máximo de registros a mostrar")
    p_conf.add_argument("--json", action="store_true", help="Salida en JSON")
    p_conf.set_defaults(func=cmd_conflictos)

    # --- servidor ---
    p_srv = subparsers.add_parser("servidor", help="Nodo central (servicio HTTP)")
    _agregar_argumentos_central(p_srv)
    p_srv.set_defaults(func=cmd_servidor)

    # --- dispositivos ---
    p_disp = subparsers.add_parser(
        "dispositivos", help="Alta, baja y listado de puestos en el nodo central"
    )
    _agregar_argumentos_central(p_disp)
    p_disp.add_argument("--listar", action="store_true", help="Lista los puestos registrados")
    p_disp.add_argument("--crear", metavar="NOMBRE", help="Da de alta un puesto")
    p_disp.add_argument("--revocar", metavar="ID", help="Revoca el acceso de un puesto")
    p_disp.set_defaults(func=cmd_dispositivos)

    return parser


def _agregar_argumentos_central(parser: argparse.ArgumentParser) -> None:
    """Opciones compartidas por ``servidor`` y ``dispositivos``"""
    parser.add_argument(
        "--db",
        default="sqlite:///sync_central.db",
        help="URL SQLAlchemy del archivo de base del nodo central",
    )
    parser.add_argument("--blobs", help="Carpeta de binarios (por defecto, junto a la base)")
    parser.add_argument("--host", default="0.0.0.0", help="Interfaz de escucha")
    parser.add_argument("--puerto", type=int, default=8765, help="Puerto de escucha")
    parser.add_argument("--cert", help="Certificado TLS (PEM)")
    parser.add_argument("--key", help="Clave privada TLS (PEM)")
    parser.add_argument(
        "--crear-dispositivo", metavar="NOMBRE", help="Da de alta un puesto y muestra su token"
    )
    parser.add_argument(
        "--listar-dispositivos", action="store_true", help="Lista los puestos registrados"
    )
    parser.add_argument(
        "--revocar-dispositivo", metavar="ID", help="Revoca el acceso de un puesto"
    )
    parser.add_argument(
        "--exportar-conflictos", metavar="ARCHIVO", help="Guarda los conflictos en JSON"
    )
    parser.add_argument(
        "--purgar-historial",
        type=int,
        metavar="DIAS",
        help="Retira del historial las operaciones con más de DIAS días",
    )
    parser.add_argument("--todos", action="store_true", help="Incluir conflictos ya revisados")
    parser.add_argument("--limite", type=int, default=200, help="Máximo de registros")
    parser.add_argument("--json", action="store_true", help="Salida en JSON")


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada del paquete (``py -3 -m sync_agent``)"""
    parser = _parser()
    args = parser.parse_args(argv)
    _configurar_logging(verboso=args.verboso, silencioso=args.silencioso)
    try:
        return int(args.func(args) or SALIDA_CORRECTA)
    except KeyboardInterrupt:  # pragma: no cover - interrupción del usuario
        print("\nInterrumpido por el usuario.")
        return SALIDA_CORRECTA
    except Exception as error:
        logger.error("La operación falló: %s", error, exc_info=args.verboso)
        print(f"Error: {error}", file=sys.stderr)
        return SALIDA_ERROR


if __name__ == "__main__":  # pragma: no cover - arranque por línea de comandos
    sys.exit(main())

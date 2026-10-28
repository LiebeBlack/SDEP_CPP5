"""
Contrato Service
Servicio de lógica de negocio para los contratos laborales

Administra el ciclo de vida contractual completo: alta del contrato,
renovaciones encadenadas, terminación con liquidación y sincronización
con los datos laborales del empleado.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import (
    Contrato,
    Empleado,
    EstadoContrato,
    EstadoIncidencia,
    TipoContrato,
    TipoIncidencia,
    TipoPago,
)
from src.nomina import (
    EntradaFiniquito,
    ParametrosNomina,
    ResultadoFiniquito,
    calcular_finiquito,
    cargar_parametros_desde,
    dias_vacaciones_pendientes,
    redondear,
)
from src.nomina.tipos import a_decimal
from src.repositories import (
    ConfiguracionRepository,
    ContratoRepository,
    EmpleadoRepository,
    IncidenciaRepository,
)
from src.utils.audit_logger import AuditEventType, get_audit_logger
from src.utils.helpers import parse_date_estricto, parse_float_estricto, parse_int_estricto

logger = logging.getLogger(__name__)

DIAS_UMBRAL_DEFECTO = 30


class ContratoService:
    """
    Servicio de contratos laborales

    Mantiene la coherencia entre el contrato vigente y los datos
    laborales del empleado, y genera la liquidación al terminar.
    """

    def __init__(self, session: Session):
        self.session = session
        self.repository = ContratoRepository(session)
        self.empleado_repository = EmpleadoRepository(session)
        self.incidencia_repository = IncidenciaRepository(session)
        self.config_repository = ConfiguracionRepository(session)

    # ------------------------------------------------------------------
    # Parámetros
    # ------------------------------------------------------------------
    def parametros(self) -> ParametrosNomina:
        """Parámetros de nómina vigentes (días de prestaciones, preaviso...)"""
        return cargar_parametros_desde(self.config_repository.get_valor)

    def umbral_por_vencer(self) -> int:
        """Días de anticipación con los que se avisa de un contrato por vencer"""
        try:
            return int(
                self.config_repository.get_valor(
                    "umbral_contrato_por_vencer_dias", DIAS_UMBRAL_DEFECTO
                )
            )
        except (SQLAlchemyError, TypeError, ValueError):
            return DIAS_UMBRAL_DEFECTO

    # ------------------------------------------------------------------
    # Alta y edición
    # ------------------------------------------------------------------
    def generar_numero(self, empleado_id: int, fecha_inicio: date | None = None) -> str:
        """
        Número único de contrato

        Formato CT-<año>-<empleado>-<secuencia>, donde la secuencia se
        calcula sobre los contratos ya registrados del empleado para que
        sea legible y no se repita.
        """
        anio = (fecha_inicio or date.today()).year
        secuencia = len(self.repository.get_by_empleado(empleado_id)) + 1
        numero = f"CT-{anio}-{empleado_id:04d}-{secuencia:02d}"
        while self.repository.get_by_numero(numero) is not None:
            secuencia += 1
            numero = f"CT-{anio}-{empleado_id:04d}-{secuencia:02d}"
        return numero

    def crear_contrato(self, datos: dict) -> Contrato:
        """
        Crea un contrato laboral

        Si el contrato nace vigente se marca como único contrato activo
        del empleado y, opcionalmente, se sincronizan su cargo,
        departamento y salario base con lo pactado.
        """
        errores = self.validar_datos_contrato(datos)
        if errores:
            raise ValueError("; ".join(errores))

        empleado_id = parse_int_estricto(datos.get("empleado_id"), "ID de empleado")
        if empleado_id is None or empleado_id <= 0:
            raise ValueError("El ID de empleado debe ser un entero positivo")
        empleado = self.empleado_repository.get_by_id(empleado_id)
        if not empleado:
            raise ValueError("Empleado no encontrado")

        fecha_inicio = (
            parse_date_estricto(datos.get("fecha_inicio"), "Fecha de inicio")
            or date.today()
        )
        fecha_fin = parse_date_estricto(datos.get("fecha_fin"), "Fecha de fin")
        salario_pactado = parse_float_estricto(
            datos.get("salario_pactado"), "Salario pactado"
        )
        if salario_pactado is None or salario_pactado <= 0:
            raise ValueError("El salario pactado debe ser mayor que cero")
        horas_semanales = parse_int_estricto(
            datos.get("horas_semanales", 40), "Horas semanales"
        )
        if horas_semanales is None:
            horas_semanales = 40
        if not 1 <= horas_semanales <= 60:
            raise ValueError("Las horas semanales deben estar entre 1 y 60")

        # Normalizar a valor de texto: si la interfaz entrega el miembro del
        # enum, ``str(miembro)`` produce "EstadoContrato.VIGENTE" y la
        # inserción falla al no ser un valor válido de la columna.
        try:
            estado = EstadoContrato.coerce(
                datos.get("estado") or EstadoContrato.VIGENTE.value
            ).value
        except ValueError as error:
            raise ValueError(f"Estado de contrato inválido: {error}") from None
        if estado == EstadoContrato.VIGENTE.value:
            vigente = self.repository.get_vigente(empleado_id)
            if vigente is not None:
                raise ValueError(
                    f"El empleado ya tiene un contrato vigente ({vigente.numero}). "
                    "Renueve o termine el contrato actual antes de crear otro."
                )

        contrato = Contrato(
            empleado_id=empleado_id,
            numero=str(datos.get("numero") or self.generar_numero(empleado_id, fecha_inicio)),
            tipo=self._valor_tipo(datos.get("tipo")),
            estado=estado,
            cargo=str(datos.get("cargo") or empleado.cargo),
            departamento=datos.get("departamento") or empleado.departamento,
            salario_pactado=redondear(a_decimal(salario_pactado)),
            horas_semanales=horas_semanales,
            fecha_inicio=fecha_inicio or date.today(),
            fecha_fin=fecha_fin,
            renovacion_automatica=1 if datos.get("renovacion_automatica") else 0,
            contrato_anterior_id=datos.get("contrato_anterior_id"),
            clausulas=datos.get("clausulas"),
            aprobado_por=datos.get("aprobado_por"),
            observaciones=datos.get("observaciones"),
        )
        creado = self.repository.create(contrato)

        if estado == EstadoContrato.VIGENTE.value and datos.get("sincronizar_empleado", True):
            self._sincronizar_empleado(creado, empleado)

        self._auditar(creado, "crear_contrato", AuditEventType.DATA_CREATE)
        return creado

    def actualizar_contrato(self, contrato_id: int, datos: dict) -> Contrato:
        """Actualiza los datos de un contrato existente"""
        contrato = self.repository.get_by_id(contrato_id)
        if not contrato:
            raise ValueError("Contrato no encontrado")

        datos = dict(datos)
        for campo_fecha, etiqueta in (
            ("fecha_inicio", "Fecha de inicio"),
            ("fecha_fin", "Fecha de fin"),
            ("fecha_terminacion", "Fecha de terminación"),
        ):
            if campo_fecha in datos:
                datos[campo_fecha] = parse_date_estricto(datos[campo_fecha], etiqueta)

        fecha_inicio = datos.get("fecha_inicio", contrato.fecha_inicio)
        fecha_fin = datos.get("fecha_fin", contrato.fecha_fin)
        if fecha_inicio is None:
            raise ValueError("La fecha de inicio es requerida")
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio")
        contrato_anterior_estado = contrato.estado
        contrato_anterior_fecha_terminacion = contrato.fecha_terminacion
        contrato_anterior_motivo_terminacion = contrato.motivo_terminacion
        contrato_anterior_salario = contrato.salario_pactado
        contrato_anterior_cargo = contrato.cargo
        contrato_anterior_departamento = contrato.departamento
        contrato_anterior_inicio = contrato.fecha_inicio
        contrato_anterior_fin = contrato.fecha_fin
        contrato_anterior_tipo = contrato.tipo
        contrato_anterior_numero = contrato.numero
        tipo_dato = datos.get("tipo", contrato.tipo_valor)
        try:
            tipo_valor = TipoContrato.coerce(tipo_dato).value
        except (TypeError, ValueError):
            raise ValueError("El tipo de contrato no es válido") from None
        if tipo_valor != TipoContrato.INDEFINIDO.value and fecha_fin is None:
            raise ValueError(
                "Los contratos temporales, por obra o pasantía requieren fecha de fin"
            )

        empleado_id_solicitado = datos.get("empleado_id", contrato.empleado_id)
        try:
            empleado_id_solicitado = parse_int_estricto(
                empleado_id_solicitado, "ID de empleado"
            )
        except ValueError as error:
            raise ValueError(str(error)) from None
        if empleado_id_solicitado != contrato.empleado_id:
            raise ValueError("No se puede reasignar un contrato a otro empleado")
        if "empleado_id" in datos:
            datos.pop("empleado_id")

        estado_dato = datos.get("estado", contrato.estado_valor)
        try:
            estado_valor = EstadoContrato.coerce(estado_dato).value
        except (TypeError, ValueError):
            raise ValueError("El estado de contrato no es válido") from None
        if estado_valor == EstadoContrato.VIGENTE.value:
            vigente = self.repository.get_vigente(contrato.empleado_id)
            if vigente is not None and vigente.id != contrato.id:
                raise ValueError(
                    f"El empleado ya tiene otro contrato vigente ({vigente.numero})"
                )
            if fecha_fin is not None and fecha_fin < date.today():
                raise ValueError("No se puede marcar como vigente un contrato cuya fecha de fin ya pasó")
        fecha_terminacion = datos.get("fecha_terminacion", contrato.fecha_terminacion)
        motivo_terminacion = datos.get("motivo_terminacion", contrato.motivo_terminacion)
        if fecha_terminacion is not None:
            if fecha_terminacion < fecha_inicio:
                raise ValueError("La fecha de terminación no puede ser anterior al inicio")
            if fecha_fin is not None and fecha_terminacion > fecha_fin:
                raise ValueError("La fecha de terminación no puede ser posterior al fin del contrato")
        if fecha_fin is not None and fecha_inicio > fecha_fin:
            raise ValueError("La fecha de fin no puede ser anterior a la fecha de inicio")
        if estado_valor == EstadoContrato.TERMINADO.value:
            if fecha_terminacion is None:
                raise ValueError("La fecha de terminación es requerida para cerrar el contrato")
            if not str(motivo_terminacion or "").strip():
                raise ValueError("El motivo de terminación es requerido para cerrar el contrato")
        elif fecha_terminacion is not None:
            raise ValueError("Solo los contratos terminados pueden tener fecha de terminación")
        elif motivo_terminacion is not None:
            raise ValueError("Solo los contratos terminados pueden tener motivo de terminación")

        if "numero" in datos and datos["numero"] != contrato.numero:
            numero = str(datos["numero"] or "").strip()
            if not numero or len(numero) > 50:
                raise ValueError("El número del contrato debe tener entre 1 y 50 caracteres")
            existente = self.repository.get_by_numero(numero)
            if existente is not None and existente.id != contrato.id:
                raise ValueError("Ya existe un contrato con ese número")
            contrato.numero = numero

        if "tipo" in datos and datos["tipo"]:
            contrato.tipo = TipoContrato.coerce(datos["tipo"])
        if "estado" in datos and datos["estado"]:
            contrato.estado = EstadoContrato.coerce(datos["estado"])
        if "salario_pactado" in datos and datos["salario_pactado"] is not None:
            importe = parse_float_estricto(datos["salario_pactado"], "Salario pactado")
            salario = redondear(a_decimal(importe))
            if salario <= 0:
                raise ValueError("El salario pactado debe ser mayor que cero")
            contrato.salario_pactado = salario

        for campo in (
            "cargo",
            "departamento",
            "clausulas",
            "observaciones",
            "aprobado_por",
            "fecha_inicio",
            "fecha_fin",
            "archivo_ruta",
            "motivo_terminacion",
            "fecha_terminacion",
        ):
            if campo in datos and (
                datos[campo] is not None
                or campo in {"fecha_inicio", "fecha_fin", "fecha_terminacion"}
            ):
                setattr(contrato, campo, datos[campo])

        if "horas_semanales" in datos and datos["horas_semanales"] is not None:
            horas = parse_int_estricto(datos["horas_semanales"], "Horas semanales")
            if horas is None:
                raise ValueError("Las horas semanales deben ser un número entero")
            if not 1 <= horas <= 60:
                raise ValueError("Las horas semanales deben estar entre 1 y 60")
            contrato.horas_semanales = horas
        if "renovacion_automatica" in datos:
            contrato.renovacion_automatica = 1 if datos["renovacion_automatica"] else 0

        if contrato.estado_valor == EstadoContrato.VIGENTE.value and datos.get(
            "sincronizar_empleado", False
        ):
            empleado = self.empleado_repository.get_by_id(contrato.empleado_id)
            if empleado:
                self._sincronizar_empleado(contrato, empleado)

        try:
            actualizado = self.repository.update(contrato)
        except Exception:
            contrato.estado = contrato_anterior_estado
            contrato.fecha_terminacion = contrato_anterior_fecha_terminacion
            contrato.motivo_terminacion = contrato_anterior_motivo_terminacion
            contrato.salario_pactado = contrato_anterior_salario
            contrato.cargo = contrato_anterior_cargo
            contrato.departamento = contrato_anterior_departamento
            contrato.fecha_inicio = contrato_anterior_inicio
            contrato.fecha_fin = contrato_anterior_fin
            contrato.tipo = contrato_anterior_tipo
            contrato.numero = contrato_anterior_numero
            raise
        self._auditar(actualizado, "actualizar_contrato", AuditEventType.DATA_UPDATE)
        return actualizado

    def renovar_contrato(
        self,
        contrato_id: int,
        nueva_fecha_fin: date | None = None,
        nuevo_salario: float | None = None,
        tipo: str | None = None,
        clausulas: str | None = None,
        aprobado_por: str | None = None,
    ) -> Contrato:
        """
        Renueva un contrato vigente

        El contrato anterior queda marcado como renovado y se crea uno
        nuevo encadenado a él, con inicio el día siguiente al vencimiento.
        """
        anterior = self.repository.get_by_id(contrato_id)
        if not anterior:
            raise ValueError("Contrato no encontrado")
        if anterior.estado_valor != EstadoContrato.VIGENTE.value:
            raise ValueError("Solo se puede renovar un contrato vigente")
        nueva_fecha_fin = parse_date_estricto(nueva_fecha_fin, "Nueva fecha de fin")
        if nueva_fecha_fin is None:
            raise ValueError("La nueva fecha de fin es requerida para renovar")

        empleado = self.empleado_repository.get_by_id(anterior.empleado_id)
        if not empleado:
            raise ValueError("Empleado no encontrado")

        if anterior.fecha_fin is None:
            raise ValueError("No se puede renovar un contrato indefinido sin fecha de vencimiento")
        if anterior.fecha_fin < date.today():
            raise ValueError("No se puede renovar un contrato que ya venció; registre un contrato nuevo")
        inicio = anterior.fecha_fin + timedelta(days=1)
        if nueva_fecha_fin < inicio:
            raise ValueError("La nueva fecha de fin debe ser posterior al inicio de la renovación")
        nuevo_tipo = TipoContrato.coerce(tipo or anterior.tipo_valor)
        if nuevo_tipo == TipoContrato.INDEFINIDO:
            raise ValueError("Una renovación debe tener fecha de fin y no puede ser indefinida")
        nuevo_salario = (
            parse_float_estricto(nuevo_salario, "Nuevo salario")
            if nuevo_salario is not None
            else float(anterior.salario_pactado or 0)
        )
        if nuevo_salario is None or nuevo_salario <= 0:
            raise ValueError("El nuevo salario debe ser mayor que cero")
        estado_anterior = anterior.estado
        anterior.estado = EstadoContrato.RENOVADO
        try:
            self.repository.update(anterior)
        except Exception:
            anterior.estado = estado_anterior
            raise

        datos = {
            "empleado_id": anterior.empleado_id,
            "tipo": tipo or anterior.tipo_valor,
            "cargo": anterior.cargo,
            "departamento": anterior.departamento,
            "salario_pactado": nuevo_salario,
            "horas_semanales": anterior.horas_semanales,
            "fecha_inicio": inicio,
            "fecha_fin": nueva_fecha_fin,
            "renovacion_automatica": bool(anterior.renovacion_automatica),
            "contrato_anterior_id": anterior.id,
            "clausulas": clausulas or anterior.clausulas,
            "aprobado_por": aprobado_por,
            "estado": EstadoContrato.VIGENTE.value,
        }
        try:
            nuevo = self.crear_contrato(datos)
        except Exception:
            # Si el alta del contrato nuevo falla, el anterior debe seguir
            # siendo el vigente: dejarlo como RENOVADO sin sucesor dejaría
            # al empleado sin contrato activo y sin forma de reintentar.
            anterior.estado = estado_anterior
            try:
                self.repository.update(anterior)
            except SQLAlchemyError:
                logger.error(
                    "No se pudo restaurar el estado del contrato %s tras fallar la renovación",
                    anterior.numero,
                    exc_info=True,
                )
            raise
        logger.info(
            "Contrato %s renovado como %s (empleado %s)",
            anterior.numero,
            nuevo.numero,
            anterior.empleado_id,
        )
        return nuevo

    def terminar_contrato(
        self,
        contrato_id: int,
        motivo: str,
        fecha_terminacion: date | None = None,
        generar_liquidacion: bool = True,
        metodo_pago: str | None = None,
        registrado_por: str | None = None,
    ) -> dict:
        """
        Termina un contrato y genera su liquidación

        Args:
            contrato_id: Contrato a terminar
            motivo: Razón del egreso (se usa para decidir el preaviso)
            fecha_terminacion: Fecha efectiva (hoy por defecto)
            generar_liquidacion: Si es True se crea el pago de liquidación
            metodo_pago: Método de pago de la liquidación
            registrado_por: Usuario que ejecuta la terminación

        Returns:
            dict: Contrato, finiquito calculado y pago generado (si aplica).
        """
        contrato = self.repository.get_by_id(contrato_id)
        if not contrato:
            raise ValueError("Contrato no encontrado")
        if contrato.estado_valor == EstadoContrato.TERMINADO.value:
            raise ValueError("El contrato ya está terminado")

        empleado = self.empleado_repository.get_by_id(contrato.empleado_id)
        if not empleado:
            raise ValueError("Empleado no encontrado")

        motivo = str(motivo or "").strip()
        if not motivo:
            raise ValueError("El motivo de terminación es requerido")
        egreso = parse_date_estricto(fecha_terminacion, "Fecha de terminación") or date.today()
        if egreso < contrato.fecha_inicio:
            raise ValueError("La fecha de terminación no puede ser anterior al inicio del contrato")
        if contrato.fecha_fin is not None and egreso > contrato.fecha_fin:
            raise ValueError("La fecha de terminación no puede ser posterior al fin del contrato")
        if (
            contrato.fecha_terminacion is not None
            and contrato.fecha_terminacion != egreso
        ):
            raise ValueError("El contrato ya tiene una terminación registrada con otra fecha")

        finiquito = self.calcular_liquidacion(contrato.empleado_id, motivo, egreso)

        # Valores previos: si la liquidación no se puede registrar, el
        # contrato se restaura. Dejarlo terminado y sin liquidación dejaba
        # al empleado sin contrato y sin pago, sin forma de reintentar.
        estado_anterior = contrato.estado
        fecha_terminacion_anterior = contrato.fecha_terminacion
        motivo_anterior = contrato.motivo_terminacion
        liquidacion_anterior = contrato.liquidacion_monto

        contrato.estado = EstadoContrato.TERMINADO
        contrato.fecha_terminacion = egreso
        contrato.motivo_terminacion = motivo
        contrato.liquidacion_monto = finiquito.neto
        self.repository.update(contrato)

        pago = None
        if generar_liquidacion and finiquito.neto > 0:
            try:
                pago = self._registrar_pago_liquidacion(
                    empleado, contrato, finiquito, egreso, metodo_pago
                )
            except Exception:
                contrato.estado = estado_anterior
                contrato.fecha_terminacion = fecha_terminacion_anterior
                contrato.motivo_terminacion = motivo_anterior
                contrato.liquidacion_monto = liquidacion_anterior
                try:
                    self.repository.update(contrato)
                except SQLAlchemyError:
                    logger.error(
                        "No se pudo restaurar el contrato %s tras fallar la liquidación",
                        contrato.numero,
                        exc_info=True,
                    )
                raise

        self._auditar(
            contrato, "terminar_contrato", AuditEventType.DATA_UPDATE, usuario=registrado_por
        )
        logger.info(
            "Contrato %s terminado (%s). Liquidación: %.2f",
            contrato.numero,
            motivo,
            float(finiquito.neto),
        )
        return {"contrato": contrato, "finiquito": finiquito, "pago": pago}

    # ------------------------------------------------------------------
    # Liquidaciones
    # ------------------------------------------------------------------
    def calcular_liquidacion(
        self,
        empleado_id: int,
        motivo: str,
        fecha_egreso: date | None = None,
        dias_ya_disfrutados: float = 0.0,
    ) -> ResultadoFiniquito:
        """
        Calcula el finiquito de un empleado

        Reúne el salario, las fechas de servicio y las vacaciones
        pendientes (descontando las ya disfrutadas por incidencias
        aprobadas).
        """
        empleado = self.empleado_repository.get_by_id(empleado_id)
        if not empleado:
            raise ValueError("Empleado no encontrado")

        parametros = self.parametros()
        egreso = fecha_egreso or date.today()
        ingreso = empleado.fecha_contratacion or egreso

        dias_vacaciones_anuales = a_decimal(
            self.config_repository.get_valor("dias_vacaciones_anual", 15)
        )
        pendientes = dias_vacaciones_pendientes(
            salario_mensual=a_decimal(empleado.salario_base),
            dias_vacaciones_anuales=dias_vacaciones_anuales,
            fecha_ingreso=ingreso,
            fecha_egreso=egreso,
            dias_ya_disfrutados=(
                a_decimal(dias_ya_disfrutados)
                if dias_ya_disfrutados
                else self._dias_vacaciones_disfrutados(empleado_id)
            ),
        )

        return calcular_finiquito(
            EntradaFiniquito(
                salario_mensual=a_decimal(empleado.salario_base),
                fecha_ingreso=ingreso,
                fecha_egreso=egreso,
                dias_vacaciones_pendientes=pendientes,
                motivo=motivo,
            ),
            parametros,
        )

    def _dias_vacaciones_disfrutados(self, empleado_id: int) -> Decimal:
        """
        Días de vacaciones ya disfrutados según las incidencias aprobadas

        Se suman los días aprobados de las incidencias de tipo vacaciones,
        que es como el sistema registra el disfrute efectivo.
        """
        total = 0
        for incidencia in self.incidencia_repository.get_by_empleado(empleado_id):
            estado = getattr(incidencia.estado, "value", incidencia.estado)
            if (
                estado != EstadoIncidencia.APROBADO.value
                and estado != EstadoIncidencia.COMPLETADO.value
            ):
                continue
            tipo = getattr(incidencia, "tipo_incidencia", None)
            tipo_valor = getattr(tipo, "value", tipo)
            if tipo_valor != TipoIncidencia.VACACIONES.value:
                continue
            total += int(incidencia.dias_aprobados or incidencia.dias_solicitados or 0)
        return a_decimal(total)

    def _registrar_pago_liquidacion(
        self,
        empleado: Empleado,
        contrato: Contrato,
        finiquito: ResultadoFiniquito,
        fecha: date,
        metodo_pago: str | None,
    ) -> object:
        """
        Registra el pago de la liquidación

        Se guarda como un pago de tipo liquidación donde el bruto son las
        asignaciones y las deducciones corresponden a los descuentos
        registrados. Los aportes de seguridad social se envían
        explícitamente en cero porque una liquidación no es salario sujeto
        a esos aportes.
        """
        from src.services.pago_service import PagoService

        servicio_pagos = PagoService(self.session)
        id_empleado = getattr(empleado, "id", None)
        if id_empleado is None:
            raise ValueError("Empleado sin identificador para registrar la liquidación")

        datos = {
            "empleado_id": int(id_empleado),
            "tipo_pago": TipoPago.LIQUIDACION.value,
            "periodo_inicio": fecha,
            "periodo_fin": fecha,
            "fecha_pago": fecha,
            "salario_base": float(finiquito.total_asignaciones),
            "deduccion_seguro": 0.0,
            "deduccion_pension": 0.0,
            "deduccion_impuesto": 0.0,
            "otras_deducciones": float(finiquito.total_deducciones),
            "descripcion": (
                f"Liquidación por terminación de contrato {contrato.numero}"
                f" ({finiquito.motivo or 'sin motivo indicado'})"
            ),
            "observaciones": (
                f"Prestaciones {finiquito.prestaciones:.2f} | "
                f"Indemnización {finiquito.indemnizacion:.2f} | "
                f"Preaviso {finiquito.preaviso:.2f} | "
                f"Vacaciones {finiquito.vacaciones:.2f} | "
                f"Aguinaldo {finiquito.aguinaldo:.2f}"
            ),
        }
        if metodo_pago:
            datos["metodo_pago"] = metodo_pago
        # La referencia de una liquidación es SIEMPRE LIQ-<número>. Antes
        # dependía de que llegara `registrado_por`, y el flujo real de la
        # interfaz no lo envía: toda liquidación quedaba con la referencia
        # genérica REC-. El usuario que ejecuta la terminación se registra
        # en la auditoría (ver terminar_contrato).
        datos["referencia_pago"] = f"LIQ-{contrato.numero}"
        return servicio_pagos.crear_pago(datos)

    # ------------------------------------------------------------------
    # Mantenimiento de estados
    # ------------------------------------------------------------------
    def sincronizar_estados(self) -> int:
        """
        Marca como vencidos los contratos cuya fecha de fin ya pasó

        Se ejecuta al abrir el módulo de contratos y en el arranque, para
        que los reportes reflejen siempre la realidad.
        """
        actualizados = 0
        for contrato in self.repository.get_vencidos():
            if contrato.estado_valor == EstadoContrato.VENCIDO.value:
                continue
            contrato.estado = EstadoContrato.VENCIDO
            self.repository.update(contrato)
            actualizados += 1
        if actualizados:
            logger.info("Contratos marcados como vencidos: %s", actualizados)
        return actualizados

    def marcar_renovables(self) -> int:
        """Marca como renovados los contratos vencidos con renovación automática"""
        actualizados = 0
        for contrato in self.repository.get_vencidos():
            if not contrato.renovacion_automatica:
                continue
            contrato.estado = EstadoContrato.RENOVADO
            self.repository.update(contrato)
            actualizados += 1
        return actualizados

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def obtener_contrato(self, contrato_id: int) -> Contrato | None:
        return self.repository.get_by_id(contrato_id)

    def listar_contratos(self) -> list[Contrato]:
        return self.repository.get_all(skip=0, limit=None)

    def listar_por_empleado(self, empleado_id: int) -> list[Contrato]:
        return self.repository.get_by_empleado(empleado_id)

    def obtener_vigente(self, empleado_id: int) -> Contrato | None:
        return self.repository.get_vigente(empleado_id)

    def listar_por_vencer(self, dias: int | None = None) -> list[Contrato]:
        return self.repository.get_por_vencer(dias or self.umbral_por_vencer())

    def listar_vencidos(self) -> list[Contrato]:
        return self.repository.get_vencidos()

    def listar_por_estado(self, estado: str) -> list[Contrato]:
        return self.repository.get_by_estado(estado)

    def obtener_estadisticas(self) -> dict:
        return self.repository.get_estadisticas()

    def empleados_sin_contrato(self) -> list[Empleado]:
        """Empleados activos que no tienen ningún contrato vigente"""
        return [
            empleado
            for empleado in self.empleado_repository.get_activos()
            if self.repository.get_vigente(empleado.id) is None
        ]

    # ------------------------------------------------------------------
    # Validación
    # ------------------------------------------------------------------
    def validar_datos_contrato(self, datos: dict) -> list[str]:
        """Valida los datos mínimos y coherentes de un contrato"""
        errores: list[str] = []

        try:
            empleado_id = parse_int_estricto(datos.get("empleado_id"), "ID de empleado")
            if empleado_id is None or empleado_id <= 0:
                errores.append("El empleado es requerido")
        except ValueError as error:
            errores.append(str(error))

        try:
            salario = parse_float_estricto(datos.get("salario_pactado"), "Salario pactado")
            if salario is None or salario <= 0:
                errores.append("El salario pactado debe ser mayor que cero")
        except ValueError as error:
            errores.append(str(error))

        fechas: dict[str, date | None] = {}
        for campo, etiqueta in (
            ("fecha_inicio", "Fecha de inicio"),
            ("fecha_fin", "Fecha de fin"),
        ):
            try:
                fechas[campo] = parse_date_estricto(datos.get(campo), etiqueta)
            except ValueError as error:
                errores.append(str(error))
                fechas[campo] = None

        fecha_inicio = fechas["fecha_inicio"]
        fecha_fin = fechas["fecha_fin"]
        if fecha_inicio is None:
            errores.append("La fecha de inicio es requerida")
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            errores.append("La fecha de fin no puede ser anterior a la de inicio")

        fecha_terminacion = None
        if "fecha_terminacion" in datos:
            try:
                fecha_terminacion = parse_date_estricto(
                    datos.get("fecha_terminacion"), "Fecha de terminación"
                )
            except ValueError as error:
                errores.append(str(error))
        if fecha_terminacion and fecha_inicio and fecha_terminacion < fecha_inicio:
            errores.append("La fecha de terminación no puede ser anterior a la fecha de inicio")
        if fecha_terminacion and fecha_fin and fecha_terminacion > fecha_fin:
            errores.append("La fecha de terminación no puede ser posterior a la fecha de fin")
        if datos.get("estado"):
            try:
                estado = EstadoContrato.coerce(datos["estado"])
            except (TypeError, ValueError):
                errores.append("El estado de contrato no es válido")
                estado = None
        else:
            estado = None
        if estado is not None:
            if estado == EstadoContrato.TERMINADO:
                if not fecha_terminacion:
                    errores.append("La fecha de terminación es requerida para cerrar el contrato")
                if not str(datos.get("motivo_terminacion") or "").strip():
                    errores.append("El motivo de terminación es requerido para cerrar el contrato")
            elif fecha_terminacion:
                errores.append("Solo los contratos terminados pueden tener fecha de terminación")

        if "numero" in datos and datos["numero"] is not None:
            numero_dato = str(datos["numero"]).strip()
            if not numero_dato:
                errores.append("El número de contrato no puede estar vacío")
            elif len(numero_dato) > 50:
                errores.append("El número de contrato no puede superar 50 caracteres")

        tipo_dato = datos.get("tipo") or TipoContrato.INDEFINIDO
        try:
            tipo_valor = TipoContrato.coerce(tipo_dato).value
        except (TypeError, ValueError):
            errores.append("El tipo de contrato no es válido")
            tipo_valor = TipoContrato.INDEFINIDO.value
        if tipo_valor != TipoContrato.INDEFINIDO.value and fecha_fin is None:
            errores.append("Los contratos temporales, por obra o pasantía requieren fecha de fin")

        try:
            horas = parse_int_estricto(datos.get("horas_semanales", 40), "Horas semanales")
            if horas is None:
                errores.append("Las horas semanales deben ser un número entero")
            elif not 1 <= horas <= 60:
                errores.append("Las horas semanales deben estar entre 1 y 60")
        except ValueError as error:
            errores.append(str(error))

        return errores

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    @staticmethod
    def _valor_tipo(tipo: object) -> TipoContrato:
        """Tipo de contrato normalizado, con indefinido como valor por defecto"""
        if not tipo:
            return TipoContrato.INDEFINIDO
        return TipoContrato.coerce(tipo)

    def _sincronizar_empleado(self, contrato: Contrato, empleado: Empleado) -> None:
        """
        Refleja en el empleado los datos pactados en el contrato vigente

        Mantiene una única fuente de verdad: si el contrato cambia de
        salario o cargo, la ficha del empleado queda alineada.
        """
        try:
            empleado.salario_base = float(contrato.salario_pactado or 0)
            if contrato.cargo:
                empleado.cargo = contrato.cargo
            if contrato.departamento:
                empleado.departamento = contrato.departamento
            self.empleado_repository.update(empleado)
        except SQLAlchemyError:
            logger.warning(
                "No se pudo sincronizar el empleado %s con el contrato %s",
                contrato.empleado_id,
                contrato.numero,
                exc_info=True,
            )

    def _auditar(
        self,
        contrato: Contrato,
        operacion: str,
        event_type: AuditEventType,
        usuario: str | None = None,
    ) -> None:
        """Registra la operación contractual en la auditoría"""
        try:
            audit = get_audit_logger()
            if not audit:
                return
            audit.log_event(
                event_type=event_type,
                entity_type="contrato",
                entity_id=contrato.id,
                user=usuario or contrato.aprobado_por or "system",
                details={
                    "operacion": operacion,
                    "numero": contrato.numero,
                    "empleado_id": contrato.empleado_id,
                    "estado": contrato.estado_valor,
                    "salario": float(contrato.salario_pactado or 0),
                },
                success=True,
            )
        except (SQLAlchemyError, ValueError, TypeError):
            logger.debug("No se pudo auditar la operación de contrato", exc_info=True)

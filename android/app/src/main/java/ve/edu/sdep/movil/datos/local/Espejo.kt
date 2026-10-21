package ve.edu.sdep.movil.datos.local

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonObject
import ve.edu.sdep.movil.datos.local.entidad.*

/**
 * Traducción entre las filas del espejo local y el payload del protocolo.
 *
 * Reglas, idénticas a las del agente de escritorio (`sync_agent/`):
 *
 * * **Solo los campos tocados.** Un alta lleva todas las columnas de dominio
 *   no nulas; una edición lleva únicamente las que cambiaron. Mandar la fila
 *   completa pisaría los cambios que otro equipo hizo en columnas distintas.
 * * **Las claves foráneas viajan como UUID.** `empleado_id` no es un número
 *   local: es el UUID global del empleado, que cada equipo traduce a su id
 *   ([conForaneasComoUuid] al salir, [AplicadorEspejo] al entrar).
 * * **Las rutas de archivo no viajan** (`foto_ruta`, `ruta_archivo`,
 *   `documento_soporte_ruta`, `archivo_ruta`): una ruta de otro equipo no
 *   significa nada aquí. El contenido sí, identificado por su hash.
 * * **`id` nunca viaja**: la identidad local no significa nada en otro equipo.
 *
 * Al aplicar un payload mandado por la red rige la regla de **presencia**:
 * una columna que viene en el payload se escribe (aunque venga vacía) y una
 * que no viene se conserva tal cual. Así una edición parcial de otro equipo
 * solo pisa lo que ese equipo tocó de verdad.
 */
object Espejo {

    /** Clave natural de una columna que unifica filas entre equipos */
    val CLAVE_NATURAL: Map<String, String> = mapOf(
        "empleados" to "cedula",
        "contratos" to "numero",
        "estudiantes" to "cedula",
        "periodos_academicos" to "nombre",
        "configuraciones" to "clave",
        "registros_moviles" to "uuid_movil",
    )

    /**
     * Claves naturales de varias columnas, evaluables solo en el equipo
     * receptor cuando sus claves foráneas ya se tradujeron a ids locales.
     */
    val CLAVE_NATURAL_COMPUESTA: Map<String, List<String>> = mapOf(
        "grados" to listOf("periodo_id", "nombre", "seccion"),
        "matriculas" to listOf("estudiante_id", "grado_id"),
        "notas_finales" to listOf("estudiante_id", "grado_id", "materia"),
    )

    /** Tablas con borrado lógico y su columna de estado (las demás borran filas) */
    val BORRADO_LOGICO: Map<String, String> = mapOf(
        "empleados" to "activo",
        "documentos" to "activo",
        "estudiantes" to "activo",
        "matriculas" to "activa",
        "registros_moviles" to "activo",
    )

    /** Todas las tablas del protocolo, en el mismo orden que el escritorio */
    val TABLAS: Set<String> = setOf(
        "empleados",
        "documentos",
        "incidencias",
        "contratos",
        "pagos",
        "configuraciones",
        "registros_moviles",
        "estudiantes",
        "periodos_academicos",
        "grados",
        "matriculas",
        "notas_finales",
    )

    /**
     * Columnas que son clave foránea hacia otra tabla replicada: el valor del
     * payload es el UUID del padre y debe traducirse a id local.
     */
    val CLAVES_FORANEAS: Map<String, Map<String, String>> = mapOf(
        "documentos" to mapOf("empleado_id" to "empleados"),
        "incidencias" to mapOf("empleado_id" to "empleados"),
        "contratos" to mapOf(
            "empleado_id" to "empleados",
            "contrato_anterior_id" to "contratos",
        ),
        "pagos" to mapOf("empleado_id" to "empleados"),
        "grados" to mapOf("periodo_id" to "periodos_academicos"),
        "matriculas" to mapOf(
            "estudiante_id" to "estudiantes",
            "grado_id" to "grados",
        ),
        "notas_finales" to mapOf(
            "estudiante_id" to "estudiantes",
            "grado_id" to "grados",
        ),
    )

    // ==================================================================
    // Lectura del payload (normalización de valores)
    // ==================================================================

    /** Texto de un campo, desenrollando la etiqueta de tipo si la trae */
    fun texto(campos: JsonObject, campo: String): String? {
        val elemento = campos[campo] ?: return null
        if (elemento is JsonNull) return null
        val primitivo = elemento as? JsonPrimitive ?: return elemento.desenvuelto()?.contentOrNull
        return primitivo.contentOrNull
    }

    fun entero(campos: JsonObject, campo: String): Int? {
        val elemento = campos[campo] ?: return null
        if (elemento is JsonNull) return null
        val crudo = elemento.textoCrudo() ?: return null
        return crudo.toIntOrNull() ?: crudo.toDoubleOrNull()?.toInt()
    }

    fun real(campos: JsonObject, campo: String): Double? {
        val elemento = campos[campo] ?: return null
        if (elemento is JsonNull) return null
        val crudo = elemento.textoCrudo() ?: return null
        return crudo.toDoubleOrNull()
    }

    /** Fecha u hora en ISO simple (sin etiqueta de tipo ni zona horaria) */
    fun fecha(campos: JsonObject, campo: String): String? {
        val texto = texto(campos, campo) ?: return null
        return normalizarIso(texto)
    }

    /** Fecha u hora a milisegundos, para las columnas propias del dispositivo */
    fun fechaMillis(campos: JsonObject, campo: String): Long? =
        Fechas.desdeIso(texto(campos, campo))

    /**
     * Hash declarado por una marca de binario (`{"__blob__": "…", "tamano": n}`)
     *
     * El contenido nunca viaja en el payload: solo su identidad, y el archivo
     * se transfiere después por el canal de binarios del nodo central.
     */
    fun hashBlob(campos: JsonObject, campo: String): String? {
        val elemento = campos[campo] as? JsonObject ?: return null
        return (elemento["__blob__"] as? JsonPrimitive)?.contentOrNull
    }

    /** Tamaño declarado por una marca de binario (null si no lo es) */
    fun tamanoBlob(campos: JsonObject, campo: String): Int? {
        val elemento = campos[campo] as? JsonObject ?: return null
        val crudo = (elemento["tamano"] as? JsonPrimitive)?.contentOrNull ?: return null
        return crudo.toIntOrNull()
    }

    /** Construye la marca de binario para enviar el hash de un contenido */
    fun marcaBlob(hash: String, tamano: Int): JsonObject =
        JsonObject(mapOf("__blob__" to JsonPrimitive(hash), "tamano" to JsonPrimitive(tamano)))

    /** Normaliza «2026-01-01T12:00:00.123456» o «…Z» a ISO sin milisegundos */
    fun normalizarIso(valor: String?): String? {
        val limpio = valor?.trim().orEmpty()
        if (limpio.isEmpty()) return null
        val sinZona = limpio.removeSuffix("Z")
        val parte = sinZona.split("T")
        val dia = parte.getOrNull(0) ?: return null
        val horaCruda = parte.getOrNull(1) ?: return dia
        val hora = horaCruda.substringBefore(".").substringBefore("+")
        return if (hora.isEmpty()) dia else "${dia}T$hora"
    }

    private fun JsonElement.textoCrudo(): String? = when (this) {
        is JsonPrimitive -> contentOrNull
        else -> desenvuelto()?.contentOrNull
    }

    private fun JsonElement.desenvuelto(): JsonPrimitive? =
        (this as? JsonObject)?.get("v") as? JsonPrimitive

    // La escritura del payload usa los ayudantes «poner» (tres sobrecargas
    // por tipo), que viven a nivel de archivo al final del mismo: llamados
    // desde payload() con el mapa local como receptor implícito.

    /**
     * Payload de una fila.
     *
     * @param completa true en un alta (todas las columnas de dominio no nulas);
     *   false en una edición (solo las columnas cuyo valor difiere de [anterior]).
     */
    fun payload(tabla: String, entidad: Any?, anterior: Any?, completa: Boolean): JsonObject? {
        val campos = mutableMapOf<String, JsonElement>()
        when (tabla) {
            "empleados" -> {
                val e = entidad as EmpleadoEntity
                val a = anterior as? EmpleadoEntity
                campos["nombres"] = JsonPrimitive(e.nombres)
                campos["apellidos"] = JsonPrimitive(e.apellidos)
                campos["cedula"] = JsonPrimitive(e.cedula)
                poner(campos, "fecha_nacimiento", e.fechaNacimiento, completa || a?.fechaNacimiento != e.fechaNacimiento)
                poner(campos, "genero", e.genero, completa || a?.genero != e.genero)
                poner(campos, "estado_civil", e.estadoCivil, completa || a?.estadoCivil != e.estadoCivil)
                poner(campos, "nacionalidad", e.nacionalidad, completa || a?.nacionalidad != e.nacionalidad)
                poner(campos, "peso", e.peso, completa || a?.peso != e.peso)
                poner(campos, "altura", e.altura, completa || a?.altura != e.altura)
                poner(campos, "tipo_sangre", e.tipoSangre, completa || a?.tipoSangre != e.tipoSangre)
                poner(campos, "telefono", e.telefono, completa || a?.telefono != e.telefono)
                poner(campos, "celular", e.celular, completa || a?.celular != e.celular)
                poner(campos, "email", e.email, completa || a?.email != e.email)
                poner(campos, "direccion", e.direccion, completa || a?.direccion != e.direccion)
                poner(campos, "ciudad", e.ciudad, completa || a?.ciudad != e.ciudad)
                poner(campos, "estado", e.estado, completa || a?.estado != e.estado)
                poner(campos, "codigo_postal", e.codigoPostal, completa || a?.codigoPostal != e.codigoPostal)
                campos["tipo_empleado"] = JsonPrimitive(e.tipoEmpleado)
                campos["cargo"] = JsonPrimitive(e.cargo)
                campos["departamento"] = JsonPrimitive(e.departamento)
                campos["fecha_contratacion"] = JsonPrimitive(e.fechaContratacion)
                poner(campos, "fecha_terminacion", e.fechaTerminacion, completa || a?.fechaTerminacion != e.fechaTerminacion)
                campos["salario_base"] = JsonPrimitive(e.salarioBase)
                poner(campos, "activo", e.activo, completa || a?.activo != e.activo)
                poner(campos, "nivel_educativo", e.nivelEducativo, completa || a?.nivelEducativo != e.nivelEducativo)
                poner(campos, "especialidad", e.especialidad, completa || a?.especialidad != e.especialidad)
                poner(campos, "titulo_obtenido", e.tituloObtenido, completa || a?.tituloObtenido != e.tituloObtenido)
                poner(campos, "titulo_secundaria", e.tituloSecundaria, completa || a?.tituloSecundaria != e.tituloSecundaria)
                poner(campos, "institucion_bancaria", e.institucionBancaria, completa || a?.institucionBancaria != e.institucionBancaria)
                poner(campos, "numero_cuenta", e.numeroCuenta, completa || a?.numeroCuenta != e.numeroCuenta)
                poner(campos, "tipo_cuenta", e.tipoCuenta, completa || a?.tipoCuenta != e.tipoCuenta)
                poner(campos, "carnet_discapacidad", e.carnetDiscapacidad, completa || a?.carnetDiscapacidad != e.carnetDiscapacidad)
                poner(campos, "enfermedades_preexistentes", e.enfermedadesPreexistentes, completa || a?.enfermedadesPreexistentes != e.enfermedadesPreexistentes)
                poner(campos, "alergias_medicamentosas", e.alergiasMedicamentosas, completa || a?.alergiasMedicamentosas != e.alergiasMedicamentosas)
                poner(campos, "alergias_alimentarias", e.alergiasAlimentarias, completa || a?.alergiasAlimentarias != e.alergiasAlimentarias)
                poner(campos, "tipo_contratacion", e.tipoContratacion, completa || a?.tipoContratacion != e.tipoContratacion)
                poner(campos, "hijos", e.hijos, completa || a?.hijos != e.hijos)
                poner(campos, "observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
                poner(campos, "contacto_emergencia_nombre", e.contactoEmergenciaNombre, completa || a?.contactoEmergenciaNombre != e.contactoEmergenciaNombre)
                poner(campos, "contacto_emergencia_telefono", e.contactoEmergenciaTelefono, completa || a?.contactoEmergenciaTelefono != e.contactoEmergenciaTelefono)
                poner(campos, "contacto_emergencia_relacion", e.contactoEmergenciaRelacion, completa || a?.contactoEmergenciaRelacion != e.contactoEmergenciaRelacion)
                if (completa) {
                    poner(campos, "created_at", e.creadoEn.ifBlank { null }, true)
                    poner(campos, "updated_at", e.actualizadoEn.ifBlank { null }, true)
                } else if (a?.actualizadoEn != e.actualizadoEn) {
                    poner(campos, "updated_at", e.actualizadoEn.ifBlank { null }, true)
                }
            }

            "documentos" -> {
                val e = entidad as DocumentoEntity
                val a = anterior as? DocumentoEntity
                campos["empleado_id"] = JsonPrimitive(e.empleadoId.toString())
                campos["tipo_documento"] = JsonPrimitive(e.tipoDocumento)
                campos["titulo"] = JsonPrimitive(e.titulo)
                poner(campos, "descripcion", e.descripcion, completa || a?.descripcion != e.descripcion)
                poner(campos, "numero_documento", e.numeroDocumento, completa || a?.numeroDocumento != e.numeroDocumento)
                poner(campos, "fecha_emision", e.fechaEmision, completa || a?.fechaEmision != e.fechaEmision)
                poner(campos, "fecha_vencimiento", e.fechaVencimiento, completa || a?.fechaVencimiento != e.fechaVencimiento)
                campos["nombre_archivo"] = JsonPrimitive(e.nombreArchivo)
                poner(campos, "tamano_bytes", e.tamanoBytes, completa || a?.tamanoBytes != e.tamanoBytes)
                poner(campos, "tipo_mime", e.tipoMime, completa || a?.tipoMime != e.tipoMime)
                // El contenido viaja como hash (canal de binarios), no como bytes
                if (e.contenidoHash != null && (completa || a?.contenidoHash != e.contenidoHash)) {
                    campos["contenido_binario"] = marcaBlob(
                        e.contenidoHash,
                        e.tamanoBytes ?: 0,
                    )
                }
                poner(campos, "activo", e.activo, completa || a?.activo != e.activo)
                poner(campos, "observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
            }

            "incidencias" -> {
                val e = entidad as IncidenciaEntity
                val a = anterior as? IncidenciaEntity
                campos["empleado_id"] = JsonPrimitive(e.empleadoId.toString())
                campos["tipo_incidencia"] = JsonPrimitive(e.tipoIncidencia)
                campos["estado"] = JsonPrimitive(e.estado)
                campos["fecha_inicio"] = JsonPrimitive(e.fechaInicio)
                campos["fecha_fin"] = JsonPrimitive(e.fechaFin)
                campos["fecha_solicitud"] = JsonPrimitive(e.fechaSolicitud)
                poner(campos, "fecha_aprobacion", e.fechaAprobacion, completa || a?.fechaAprobacion != e.fechaAprobacion)
                campos["motivo"] = JsonPrimitive(e.motivo)
                poner(campos, "descripcion", e.descripcion, completa || a?.descripcion != e.descripcion)
                campos["dias_solicitados"] = JsonPrimitive(e.diasSolicitados)
                poner(campos, "dias_aprobados", e.diasAprobados, completa || a?.diasAprobados != e.diasAprobados)
                poner(campos, "documento_soporte_nombre", e.documentoSoporteNombre, completa || a?.documentoSoporteNombre != e.documentoSoporteNombre)
                if (e.documentoSoporteHash != null && (completa || a?.documentoSoporteHash != e.documentoSoporteHash)) {
                    campos["documento_soporte_binario"] = marcaBlob(
                        e.documentoSoporteHash,
                        e.documentoSoporteBinario?.size ?: 0,
                    )
                }
                poner(campos, "aprobado_por", e.aprobadoPor, completa || a?.aprobadoPor != e.aprobadoPor)
                poner(campos, "comentarios_aprobacion", e.comentariosAprobacion, completa || a?.comentariosAprobacion != e.comentariosAprobacion)
                poner(campos, "afecta_nominas", e.afectaNominas, completa || a?.afectaNominas != e.afectaNominas)
                poner(campos, "descuento_dias", e.descuentoDias, completa || a?.descuentoDias != e.descuentoDias)
                poner(campos, "observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
            }

            "contratos" -> {
                val e = entidad as ContratoEntity
                val a = anterior as? ContratoEntity
                campos["empleado_id"] = JsonPrimitive(e.empleadoId.toString())
                campos["numero"] = JsonPrimitive(e.numero)
                campos["tipo"] = JsonPrimitive(e.tipo)
                campos["estado"] = JsonPrimitive(e.estado)
                campos["cargo"] = JsonPrimitive(e.cargo)
                poner(campos, "departamento", e.departamento, completa || a?.departamento != e.departamento)
                campos["salario_pactado"] = JsonPrimitive(e.salarioPactado)
                campos["horas_semanales"] = JsonPrimitive(e.horasSemanales)
                campos["fecha_inicio"] = JsonPrimitive(e.fechaInicio)
                poner(campos, "fecha_fin", e.fechaFin, completa || a?.fechaFin != e.fechaFin)
                poner(campos, "renovacion_automatica", e.renovacionAutomatica, completa || a?.renovacionAutomatica != e.renovacionAutomatica)
                poner(campos, "contrato_anterior_id", e.contratoAnteriorId?.toString(), completa || a?.contratoAnteriorId != e.contratoAnteriorId)
                poner(campos, "clausulas", e.clausulas, completa || a?.clausulas != e.clausulas)
                poner(campos, "motivo_terminacion", e.motivoTerminacion, completa || a?.motivoTerminacion != e.motivoTerminacion)
                poner(campos, "fecha_terminacion", e.fechaTerminacion, completa || a?.fechaTerminacion != e.fechaTerminacion)
                poner(campos, "liquidacion_monto", e.liquidacionMonto, completa || a?.liquidacionMonto != e.liquidacionMonto)
                poner(campos, "aprobado_por", e.aprobadoPor, completa || a?.aprobadoPor != e.aprobadoPor)
                poner(campos, "observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
            }

            "pagos" -> {
                val e = entidad as PagoEntity
                val a = anterior as? PagoEntity
                campos["empleado_id"] = JsonPrimitive(e.empleadoId.toString())
                campos["tipo_pago"] = JsonPrimitive(e.tipoPago)
                campos["metodo_pago"] = JsonPrimitive(e.metodoPago)
                campos["periodo_inicio"] = JsonPrimitive(e.periodoInicio)
                campos["periodo_fin"] = JsonPrimitive(e.periodoFin)
                campos["fecha_pago"] = JsonPrimitive(e.fechaPago)
                campos["monto_bruto"] = JsonPrimitive(e.montoBruto)
                campos["monto_neto"] = JsonPrimitive(e.montoNeto)
                campos["salario_base"] = JsonPrimitive(e.salarioBase)
                poner(campos, "descuentos", e.descuentos, completa || a?.descuentos != e.descuentos)
                poner(campos, "bonificaciones", e.bonificaciones, completa || a?.bonificaciones != e.bonificaciones)
                poner(campos, "horas_extra", e.horasExtra, completa || a?.horasExtra != e.horasExtra)
                poner(campos, "deduccion_seguro", e.deduccionSeguro, completa || a?.deduccionSeguro != e.deduccionSeguro)
                poner(campos, "deduccion_pension", e.deduccionPension, completa || a?.deduccionPension != e.deduccionPension)
                poner(campos, "deduccion_impuesto", e.deduccionImpuesto, completa || a?.deduccionImpuesto != e.deduccionImpuesto)
                poner(campos, "otras_deducciones", e.otrasDeducciones, completa || a?.otrasDeducciones != e.otrasDeducciones)
                poner(campos, "modalidad_calculo", e.modalidadCalculo, completa || a?.modalidadCalculo != e.modalidadCalculo)
                poner(campos, "base_gravable", e.baseGravable, completa || a?.baseGravable != e.baseGravable)
                poner(campos, "horas_extra_diurnas", e.horasExtraDiurnas, completa || a?.horasExtraDiurnas != e.horasExtraDiurnas)
                poner(campos, "horas_extra_nocturnas", e.horasExtraNocturnas, completa || a?.horasExtraNocturnas != e.horasExtraNocturnas)
                poner(campos, "horas_extra_feriadas", e.horasExtraFeriadas, completa || a?.horasExtraFeriadas != e.horasExtraFeriadas)
                poner(campos, "aguinaldo", e.aguinaldo, completa || a?.aguinaldo != e.aguinaldo)
                poner(campos, "bono_vacacional", e.bonoVacacional, completa || a?.bonoVacacional != e.bonoVacacional)
                poner(campos, "aporte_seguro_patronal", e.aporteSeguroPatronal, completa || a?.aporteSeguroPatronal != e.aporteSeguroPatronal)
                poner(campos, "aporte_pension_patronal", e.aportePensionPatronal, completa || a?.aportePensionPatronal != e.aportePensionPatronal)
                poner(campos, "isr_tramo", e.isrTramo, completa || a?.isrTramo != e.isrTramo)
                poner(campos, "dias_laborados", e.diasLaborados, completa || a?.diasLaborados != e.diasLaborados)
                poner(campos, "dias_periodo", e.diasPeriodo, completa || a?.diasPeriodo != e.diasPeriodo)
                poner(campos, "prorrateado", e.prorrateado, completa || a?.prorrateado != e.prorrateado)
                poner(campos, "descripcion", e.descripcion, completa || a?.descripcion != e.descripcion)
                poner(campos, "referencia_pago", e.referenciaPago, completa || a?.referenciaPago != e.referenciaPago)
                poner(campos, "observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
                poner(campos, "pagado", e.pagado, completa || a?.pagado != e.pagado)
                poner(campos, "fecha_registro_pago", e.fechaRegistroPago, completa || a?.fechaRegistroPago != e.fechaRegistroPago)
            }

            "estudiantes" -> {
                val e = entidad as EstudianteEntity
                val a = anterior as? EstudianteEntity
                campos["nombres"] = JsonPrimitive(e.nombres)
                campos["apellidos"] = JsonPrimitive(e.apellidos)
                poner(campos, "cedula", e.cedula, completa || a?.cedula != e.cedula)
                poner(campos, "fecha_nacimiento", e.fechaNacimiento, completa || a?.fechaNacimiento != e.fechaNacimiento)
                poner(campos, "genero", e.genero, completa || a?.genero != e.genero)
                campos["nivel"] = JsonPrimitive(e.nivel)
                poner(campos, "representante", e.representante, completa || a?.representante != e.representante)
                poner(campos, "telefono", e.telefono, completa || a?.telefono != e.telefono)
                poner(campos, "telefono_representante", e.telefonoRepresentante, completa || a?.telefonoRepresentante != e.telefonoRepresentante)
                poner(campos, "email", e.email, completa || a?.email != e.email)
                poner(campos, "direccion", e.direccion, completa || a?.direccion != e.direccion)
                poner(campos, "observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
                poner(campos, "activo", e.activo, completa || a?.activo != e.activo)
            }

            "periodos_academicos" -> {
                val e = entidad as PeriodoAcademicoEntity
                val a = anterior as? PeriodoAcademicoEntity
                campos["nombre"] = JsonPrimitive(e.nombre)
                poner(campos, "fecha_inicio", e.fechaInicio, completa || a?.fechaInicio != e.fechaInicio)
                poner(campos, "fecha_fin", e.fechaFin, completa || a?.fechaFin != e.fechaFin)
                campos["estado"] = JsonPrimitive(e.estado)
                poner(campos, "cerrado_en", e.cerradoEn, completa || a?.cerradoEn != e.cerradoEn)
                poner(campos, "cerrado_por", e.cerradoPor, completa || a?.cerradoPor != e.cerradoPor)
                poner(campos, "observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
            }

            "grados" -> {
                val e = entidad as GradoEntity
                val a = anterior as? GradoEntity
                campos["periodo_id"] = JsonPrimitive(e.periodoId.toString())
                campos["nivel"] = JsonPrimitive(e.nivel)
                campos["nombre"] = JsonPrimitive(e.nombre)
                campos["seccion"] = JsonPrimitive(e.seccion)
                poner(campos, "observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
            }

            "matriculas" -> {
                val e = entidad as MatriculaEntity
                val a = anterior as? MatriculaEntity
                campos["estudiante_id"] = JsonPrimitive(e.estudianteId.toString())
                campos["grado_id"] = JsonPrimitive(e.gradoId.toString())
                campos["fecha_matricula"] = JsonPrimitive(e.fechaMatricula)
                poner(campos, "activa", e.activa, completa || a?.activa != e.activa)
                poner(campos, "observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
            }

            "notas_finales" -> {
                val e = entidad as NotaFinalEntity
                val a = anterior as? NotaFinalEntity
                campos["estudiante_id"] = JsonPrimitive(e.estudianteId.toString())
                campos["grado_id"] = JsonPrimitive(e.gradoId.toString())
                campos["materia"] = JsonPrimitive(e.materia)
                campos["calificacion"] = JsonPrimitive(e.calificacion)
                poner(campos, "registrado_por", e.registradoPor, completa || a?.registradoPor != e.registradoPor)
                poner(campos, "observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
            }

            "configuraciones" -> {
                val e = entidad as ConfiguracionEntity
                val a = anterior as? ConfiguracionEntity
                campos["clave"] = JsonPrimitive(e.clave)
                poner(campos, "valor", e.valor, completa || a?.valor != e.valor)
                poner(campos, "descripcion", e.descripcion, completa || a?.descripcion != e.descripcion)
                campos["tipo_dato"] = JsonPrimitive(e.tipoDato)
                poner(campos, "categoria", e.categoria, completa || a?.categoria != e.categoria)
                poner(campos, "editable", e.editable, completa || a?.editable != e.editable)
            }

            else -> return null
        }

        // Nada que enviar en una edición sin cambios
        if (!completa && campos.isEmpty()) return null
        return JsonObject(campos)
    }

    /**
     * Expresa las claves foráneas del payload como UUID del padre.
     *
     * Un id local en el payload sería un dato incorrecto en el equipo receptor
     * (allí ese número es otra fila), así que la columna se omite si el padre
     * no tiene identidad global conocida: es preferible un dato incompleto a
     * uno equivocado. Es el espejo exacto de `identidad.traducir_payload_a_uuid`
     * del escritorio.
     *
     * @param uuidDe Resuelve (tabla padre, id local) → UUID; null si se desconoce
     */
    suspend fun conForaneasComoUuid(
        tabla: String,
        campos: JsonObject,
        uuidDe: suspend (tabla: String, idLocal: Long) -> String?,
    ): JsonObject {
        val foraneas = CLAVES_FORANEAS[tabla] ?: return campos
        val resultado = mutableMapOf<String, JsonElement>()
        for ((clave, valor) in campos) {
            val tablaPadre = foraneas[clave]
            if (tablaPadre == null) {
                resultado[clave] = valor
                continue
            }
            val idLocal = (valor as? JsonPrimitive)?.contentOrNull?.toLongOrNull()
            val uuid = idLocal?.let { uuidDe(tablaPadre, it) }
            if (uuid == null) {
                // Padre sin identidad global: la columna viaja incompleta y el
                // nodo central resolverá con lo que conozca.
                continue
            }
            resultado[clave] = JsonPrimitive(uuid)
        }
        return JsonObject(resultado)
    }

    /** Forma canónica (claves ordenadas, sin espacios) de un valor del protocolo */
    fun canonica(elemento: JsonElement?): String = when (elemento) {
        null, JsonNull -> "null"
        is JsonObject -> elemento.entries
            .sortedBy { it.key }
            .joinToString(",", "{", "}") { "\"${it.key}\":${canonica(it.value)}" }
        is JsonArray -> elemento.joinToString(",", "[", "]") { canonica(it) }
        is JsonPrimitive -> when {
            elemento.isString -> "\"${elemento.content.replace("\\", "\\\\").replace("\"", "\\\"")}\""
            else -> elemento.content
        }
        else -> elemento.toString()
    }

    // ==================================================================
    // Aplicación del payload sobre una fila local
    // ==================================================================

    /**
     * Aplica los campos del payload a una fila.
     *
     * Regla de presencia: las columnas que **vienen** en [campos] se escriben
     * (también si vienen vacías) y las que no vienen se conservan. Así una
     * edición parcial remota no borra lo que este equipo no tocó.
     *
     * @param base La fila existente (edición) o null (alta)
     */
    fun aplicar(tabla: String, base: Any?, campos: JsonObject): Any? = when (tabla) {
        "empleados" -> aplicarEmpleado(base as? EmpleadoEntity, campos)
        "documentos" -> aplicarDocumento(base as? DocumentoEntity, campos)
        "incidencias" -> aplicarIncidencia(base as? IncidenciaEntity, campos)
        "contratos" -> aplicarContrato(base as? ContratoEntity, campos)
        "pagos" -> aplicarPago(base as? PagoEntity, campos)
        "estudiantes" -> aplicarEstudiante(base as? EstudianteEntity, campos)
        "periodos_academicos" -> aplicarPeriodo(base as? PeriodoAcademicoEntity, campos)
        "grados" -> aplicarGrado(base as? GradoEntity, campos)
        "matriculas" -> aplicarMatricula(base as? MatriculaEntity, campos)
        "notas_finales" -> aplicarNota(base as? NotaFinalEntity, campos)
        "configuraciones" -> aplicarConfiguracion(base as? ConfiguracionEntity, campos)
        "registros_moviles" -> aplicarRegistroMovil(base as? RegistroEntity, campos)
        else -> null
    }

    // Helpers de presencia: si el campo no viene, se conserva el valor actual
    private fun textoO(campos: JsonObject, campo: String, actual: String?): String? =
        if (campos.containsKey(campo)) texto(campos, campo) else actual

    private fun enteroO(campos: JsonObject, campo: String, actual: Int?): Int? =
        if (campos.containsKey(campo)) entero(campos, campo) else actual

    private fun realO(campos: JsonObject, campo: String, actual: Double?): Double? =
        if (campos.containsKey(campo)) real(campos, campo) else actual

    private fun fechaO(campos: JsonObject, campo: String, actual: String?): String? =
        if (campos.containsKey(campo)) fecha(campos, campo) else actual

    private fun fechaMillisO(campos: JsonObject, campo: String, actual: Long): Long =
        if (campos.containsKey(campo)) fechaMillis(campos, campo) ?: actual else actual

    private fun aplicarEmpleado(base: EmpleadoEntity?, campos: JsonObject): EmpleadoEntity {
        val e = base ?: EmpleadoEntity(
            nombres = "", apellidos = "", cedula = "",
            tipoEmpleado = "docente", cargo = "", departamento = "",
            fechaContratacion = "", salarioBase = 0.0,
        )
        return e.copy(
            nombres = texto(campos, "nombres") ?: e.nombres,
            apellidos = texto(campos, "apellidos") ?: e.apellidos,
            cedula = texto(campos, "cedula") ?: e.cedula,
            fechaNacimiento = fechaO(campos, "fecha_nacimiento", e.fechaNacimiento),
            genero = textoO(campos, "genero", e.genero),
            estadoCivil = textoO(campos, "estado_civil", e.estadoCivil),
            nacionalidad = textoO(campos, "nacionalidad", e.nacionalidad),
            peso = realO(campos, "peso", e.peso),
            altura = realO(campos, "altura", e.altura),
            tipoSangre = textoO(campos, "tipo_sangre", e.tipoSangre),
            telefono = textoO(campos, "telefono", e.telefono),
            celular = textoO(campos, "celular", e.celular),
            email = textoO(campos, "email", e.email),
            direccion = textoO(campos, "direccion", e.direccion),
            ciudad = textoO(campos, "ciudad", e.ciudad),
            estado = textoO(campos, "estado", e.estado),
            codigoPostal = textoO(campos, "codigo_postal", e.codigoPostal),
            tipoEmpleado = texto(campos, "tipo_empleado") ?: e.tipoEmpleado,
            cargo = texto(campos, "cargo") ?: e.cargo,
            departamento = texto(campos, "departamento") ?: e.departamento,
            fechaContratacion = fecha(campos, "fecha_contratacion") ?: e.fechaContratacion,
            fechaTerminacion = fechaO(campos, "fecha_terminacion", e.fechaTerminacion),
            salarioBase = real(campos, "salario_base") ?: e.salarioBase,
            activo = enteroO(campos, "activo", e.activo) ?: e.activo,
            nivelEducativo = textoO(campos, "nivel_educativo", e.nivelEducativo),
            especialidad = textoO(campos, "especialidad", e.especialidad),
            tituloObtenido = textoO(campos, "titulo_obtenido", e.tituloObtenido),
            tituloSecundaria = textoO(campos, "titulo_secundaria", e.tituloSecundaria),
            institucionBancaria = textoO(campos, "institucion_bancaria", e.institucionBancaria),
            numeroCuenta = textoO(campos, "numero_cuenta", e.numeroCuenta),
            tipoCuenta = textoO(campos, "tipo_cuenta", e.tipoCuenta),
            carnetDiscapacidad = textoO(campos, "carnet_discapacidad", e.carnetDiscapacidad),
            enfermedadesPreexistentes = textoO(campos, "enfermedades_preexistentes", e.enfermedadesPreexistentes),
            alergiasMedicamentosas = textoO(campos, "alergias_medicamentosas", e.alergiasMedicamentosas),
            alergiasAlimentarias = textoO(campos, "alergias_alimentarias", e.alergiasAlimentarias),
            tipoContratacion = textoO(campos, "tipo_contratacion", e.tipoContratacion),
            hijos = textoO(campos, "hijos", e.hijos),
            observaciones = textoO(campos, "observaciones", e.observaciones),
            contactoEmergenciaNombre = textoO(campos, "contacto_emergencia_nombre", e.contactoEmergenciaNombre),
            contactoEmergenciaTelefono = textoO(campos, "contacto_emergencia_telefono", e.contactoEmergenciaTelefono),
            contactoEmergenciaRelacion = textoO(campos, "contacto_emergencia_relacion", e.contactoEmergenciaRelacion),
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
    }

    private fun aplicarDocumento(base: DocumentoEntity?, campos: JsonObject): DocumentoEntity {
        val e = base ?: DocumentoEntity(
            empleadoId = entero(campos, "empleado_id")?.toLong() ?: 0L,
            tipoDocumento = "", titulo = "", nombreArchivo = "",
        )
        return e.copy(
            empleadoId = entero(campos, "empleado_id")?.toLong() ?: e.empleadoId,
            tipoDocumento = texto(campos, "tipo_documento") ?: e.tipoDocumento,
            titulo = texto(campos, "titulo") ?: e.titulo,
            descripcion = textoO(campos, "descripcion", e.descripcion),
            numeroDocumento = textoO(campos, "numero_documento", e.numeroDocumento),
            fechaEmision = fechaO(campos, "fecha_emision", e.fechaEmision),
            fechaVencimiento = fechaO(campos, "fecha_vencimiento", e.fechaVencimiento),
            nombreArchivo = texto(campos, "nombre_archivo") ?: e.nombreArchivo,
            tamanoBytes = enteroO(campos, "tamano_bytes", e.tamanoBytes),
            tipoMime = textoO(campos, "tipo_mime", e.tipoMime),
            contenidoHash = hashBlob(campos, "contenido_binario") ?: e.contenidoHash,
            activo = enteroO(campos, "activo", e.activo) ?: e.activo,
            observaciones = textoO(campos, "observaciones", e.observaciones),
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
    }

    private fun aplicarIncidencia(base: IncidenciaEntity?, campos: JsonObject): IncidenciaEntity {
        val e = base ?: IncidenciaEntity(
            empleadoId = entero(campos, "empleado_id")?.toLong() ?: 0L,
            tipoIncidencia = "", estado = "pendiente",
            fechaInicio = "", fechaFin = "", fechaSolicitud = "",
            motivo = "", diasSolicitados = 0,
        )
        return e.copy(
            empleadoId = entero(campos, "empleado_id")?.toLong() ?: e.empleadoId,
            tipoIncidencia = texto(campos, "tipo_incidencia") ?: e.tipoIncidencia,
            estado = texto(campos, "estado") ?: e.estado,
            fechaInicio = fecha(campos, "fecha_inicio") ?: e.fechaInicio,
            fechaFin = fecha(campos, "fecha_fin") ?: e.fechaFin,
            fechaSolicitud = fecha(campos, "fecha_solicitud") ?: e.fechaSolicitud,
            fechaAprobacion = fechaO(campos, "fecha_aprobacion", e.fechaAprobacion),
            motivo = texto(campos, "motivo") ?: e.motivo,
            descripcion = textoO(campos, "descripcion", e.descripcion),
            diasSolicitados = entero(campos, "dias_solicitados") ?: e.diasSolicitados,
            diasAprobados = enteroO(campos, "dias_aprobados", e.diasAprobados),
            documentoSoporteNombre = textoO(campos, "documento_soporte_nombre", e.documentoSoporteNombre),
            documentoSoporteHash = hashBlob(campos, "documento_soporte_binario")
                ?: e.documentoSoporteHash,
            aprobadoPor = textoO(campos, "aprobado_por", e.aprobadoPor),
            comentariosAprobacion = textoO(campos, "comentarios_aprobacion", e.comentariosAprobacion),
            afectaNominas = enteroO(campos, "afecta_nominas", e.afectaNominas) ?: e.afectaNominas,
            descuentoDias = realO(campos, "descuento_dias", e.descuentoDias),
            observaciones = textoO(campos, "observaciones", e.observaciones),
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
    }

    private fun aplicarContrato(base: ContratoEntity?, campos: JsonObject): ContratoEntity {
        val e = base ?: ContratoEntity(
            empleadoId = entero(campos, "empleado_id")?.toLong() ?: 0L,
            numero = "", tipo = "indefinido", estado = "vigente",
            cargo = "", salarioPactado = 0.0, fechaInicio = "",
        )
        return e.copy(
            empleadoId = entero(campos, "empleado_id")?.toLong() ?: e.empleadoId,
            numero = texto(campos, "numero") ?: e.numero,
            tipo = texto(campos, "tipo") ?: e.tipo,
            estado = texto(campos, "estado") ?: e.estado,
            cargo = texto(campos, "cargo") ?: e.cargo,
            departamento = textoO(campos, "departamento", e.departamento),
            salarioPactado = real(campos, "salario_pactado") ?: e.salarioPactado,
            horasSemanales = entero(campos, "horas_semanales") ?: e.horasSemanales,
            fechaInicio = fecha(campos, "fecha_inicio") ?: e.fechaInicio,
            fechaFin = fechaO(campos, "fecha_fin", e.fechaFin),
            renovacionAutomatica = enteroO(campos, "renovacion_automatica", e.renovacionAutomatica) ?: e.renovacionAutomatica,
            contratoAnteriorId = if (campos.containsKey("contrato_anterior_id")) {
                entero(campos, "contrato_anterior_id")?.toLong()
            } else {
                e.contratoAnteriorId
            },
            clausulas = textoO(campos, "clausulas", e.clausulas),
            motivoTerminacion = textoO(campos, "motivo_terminacion", e.motivoTerminacion),
            fechaTerminacion = fechaO(campos, "fecha_terminacion", e.fechaTerminacion),
            liquidacionMonto = realO(campos, "liquidacion_monto", e.liquidacionMonto) ?: e.liquidacionMonto,
            aprobadoPor = textoO(campos, "aprobado_por", e.aprobadoPor),
            observaciones = textoO(campos, "observaciones", e.observaciones),
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
    }

    private fun aplicarPago(base: PagoEntity?, campos: JsonObject): PagoEntity {
        val e = base ?: PagoEntity(
            empleadoId = entero(campos, "empleado_id")?.toLong() ?: 0L,
            tipoPago = "", periodoInicio = "", periodoFin = "", fechaPago = "",
            montoBruto = 0.0, montoNeto = 0.0, salarioBase = 0.0,
        )
        return e.copy(
            empleadoId = entero(campos, "empleado_id")?.toLong() ?: e.empleadoId,
            tipoPago = texto(campos, "tipo_pago") ?: e.tipoPago,
            metodoPago = texto(campos, "metodo_pago") ?: e.metodoPago,
            periodoInicio = fecha(campos, "periodo_inicio") ?: e.periodoInicio,
            periodoFin = fecha(campos, "periodo_fin") ?: e.periodoFin,
            fechaPago = fecha(campos, "fecha_pago") ?: e.fechaPago,
            montoBruto = real(campos, "monto_bruto") ?: e.montoBruto,
            montoNeto = real(campos, "monto_neto") ?: e.montoNeto,
            descuentos = realO(campos, "descuentos", e.descuentos) ?: e.descuentos,
            bonificaciones = realO(campos, "bonificaciones", e.bonificaciones) ?: e.bonificaciones,
            horasExtra = realO(campos, "horas_extra", e.horasExtra) ?: e.horasExtra,
            salarioBase = real(campos, "salario_base") ?: e.salarioBase,
            deduccionSeguro = realO(campos, "deduccion_seguro", e.deduccionSeguro) ?: e.deduccionSeguro,
            deduccionPension = realO(campos, "deduccion_pension", e.deduccionPension) ?: e.deduccionPension,
            deduccionImpuesto = realO(campos, "deduccion_impuesto", e.deduccionImpuesto) ?: e.deduccionImpuesto,
            otrasDeducciones = realO(campos, "otras_deducciones", e.otrasDeducciones) ?: e.otrasDeducciones,
            modalidadCalculo = textoO(campos, "modalidad_calculo", e.modalidadCalculo) ?: e.modalidadCalculo,
            baseGravable = realO(campos, "base_gravable", e.baseGravable) ?: e.baseGravable,
            horasExtraDiurnas = realO(campos, "horas_extra_diurnas", e.horasExtraDiurnas) ?: e.horasExtraDiurnas,
            horasExtraNocturnas = realO(campos, "horas_extra_nocturnas", e.horasExtraNocturnas) ?: e.horasExtraNocturnas,
            horasExtraFeriadas = realO(campos, "horas_extra_feriadas", e.horasExtraFeriadas) ?: e.horasExtraFeriadas,
            aguinaldo = realO(campos, "aguinaldo", e.aguinaldo) ?: e.aguinaldo,
            bonoVacacional = realO(campos, "bono_vacacional", e.bonoVacacional) ?: e.bonoVacacional,
            aporteSeguroPatronal = realO(campos, "aporte_seguro_patronal", e.aporteSeguroPatronal) ?: e.aporteSeguroPatronal,
            aportePensionPatronal = realO(campos, "aporte_pension_patronal", e.aportePensionPatronal) ?: e.aportePensionPatronal,
            isrTramo = textoO(campos, "isr_tramo", e.isrTramo),
            diasLaborados = enteroO(campos, "dias_laborados", e.diasLaborados),
            diasPeriodo = enteroO(campos, "dias_periodo", e.diasPeriodo),
            prorrateado = enteroO(campos, "prorrateado", e.prorrateado),
            descripcion = textoO(campos, "descripcion", e.descripcion),
            referenciaPago = textoO(campos, "referencia_pago", e.referenciaPago),
            observaciones = textoO(campos, "observaciones", e.observaciones),
            pagado = enteroO(campos, "pagado", e.pagado) ?: e.pagado,
            fechaRegistroPago = fechaO(campos, "fecha_registro_pago", e.fechaRegistroPago),
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
    }

    private fun aplicarEstudiante(base: EstudianteEntity?, campos: JsonObject): EstudianteEntity {
        val e = base ?: EstudianteEntity(nombres = "", apellidos = "", nivel = "secundaria")
        return e.copy(
            nombres = texto(campos, "nombres") ?: e.nombres,
            apellidos = texto(campos, "apellidos") ?: e.apellidos,
            cedula = textoO(campos, "cedula", e.cedula),
            fechaNacimiento = fechaO(campos, "fecha_nacimiento", e.fechaNacimiento),
            genero = textoO(campos, "genero", e.genero),
            nivel = texto(campos, "nivel") ?: e.nivel,
            representante = textoO(campos, "representante", e.representante),
            telefono = textoO(campos, "telefono", e.telefono),
            telefonoRepresentante = textoO(campos, "telefono_representante", e.telefonoRepresentante),
            email = textoO(campos, "email", e.email),
            direccion = textoO(campos, "direccion", e.direccion),
            observaciones = textoO(campos, "observaciones", e.observaciones),
            activo = enteroO(campos, "activo", e.activo) ?: e.activo,
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
    }

    private fun aplicarPeriodo(base: PeriodoAcademicoEntity?, campos: JsonObject): PeriodoAcademicoEntity {
        val e = base ?: PeriodoAcademicoEntity(nombre = "")
        return e.copy(
            nombre = texto(campos, "nombre") ?: e.nombre,
            fechaInicio = fechaO(campos, "fecha_inicio", e.fechaInicio),
            fechaFin = fechaO(campos, "fecha_fin", e.fechaFin),
            estado = texto(campos, "estado") ?: e.estado,
            cerradoEn = fechaO(campos, "cerrado_en", e.cerradoEn),
            cerradoPor = textoO(campos, "cerrado_por", e.cerradoPor),
            observaciones = textoO(campos, "observaciones", e.observaciones),
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
    }

    private fun aplicarGrado(base: GradoEntity?, campos: JsonObject): GradoEntity {
        val e = base ?: GradoEntity(
            periodoId = entero(campos, "periodo_id")?.toLong() ?: 0L,
            nivel = "", nombre = "",
        )
        return e.copy(
            periodoId = entero(campos, "periodo_id")?.toLong() ?: e.periodoId,
            nivel = texto(campos, "nivel") ?: e.nivel,
            nombre = texto(campos, "nombre") ?: e.nombre,
            seccion = texto(campos, "seccion") ?: e.seccion,
            observaciones = textoO(campos, "observaciones", e.observaciones),
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
    }

    private fun aplicarMatricula(base: MatriculaEntity?, campos: JsonObject): MatriculaEntity {
        val e = base ?: MatriculaEntity(
            estudianteId = entero(campos, "estudiante_id")?.toLong() ?: 0L,
            gradoId = entero(campos, "grado_id")?.toLong() ?: 0L,
            fechaMatricula = "",
        )
        return e.copy(
            estudianteId = entero(campos, "estudiante_id")?.toLong() ?: e.estudianteId,
            gradoId = entero(campos, "grado_id")?.toLong() ?: e.gradoId,
            fechaMatricula = fecha(campos, "fecha_matricula") ?: e.fechaMatricula,
            activa = enteroO(campos, "activa", e.activa) ?: e.activa,
            observaciones = textoO(campos, "observaciones", e.observaciones),
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
    }

    private fun aplicarNota(base: NotaFinalEntity?, campos: JsonObject): NotaFinalEntity {
        val e = base ?: NotaFinalEntity(
            estudianteId = entero(campos, "estudiante_id")?.toLong() ?: 0L,
            gradoId = entero(campos, "grado_id")?.toLong() ?: 0L,
            materia = "", calificacion = 0.0,
        )
        return e.copy(
            estudianteId = entero(campos, "estudiante_id")?.toLong() ?: e.estudianteId,
            gradoId = entero(campos, "grado_id")?.toLong() ?: e.gradoId,
            materia = texto(campos, "materia") ?: e.materia,
            calificacion = real(campos, "calificacion") ?: e.calificacion,
            registradoPor = textoO(campos, "registrado_por", e.registradoPor),
            observaciones = textoO(campos, "observaciones", e.observaciones),
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
    }

    private fun aplicarConfiguracion(base: ConfiguracionEntity?, campos: JsonObject): ConfiguracionEntity {
        val e = base ?: ConfiguracionEntity(clave = "", tipoDato = "string")
        return e.copy(
            clave = texto(campos, "clave") ?: e.clave,
            valor = textoO(campos, "valor", e.valor),
            descripcion = textoO(campos, "descripcion", e.descripcion),
            tipoDato = texto(campos, "tipo_dato") ?: e.tipoDato,
            categoria = textoO(campos, "categoria", e.categoria),
            editable = enteroO(campos, "editable", e.editable) ?: e.editable,
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
    }

    /**
     * Registro de campo recibido de la red.
     *
     * `registros_moviles` vive en la tabla local `registros`: el id local es el
     * propio UUID y el borrado lógico (`activo`) se traduce a `eliminado`.
     */
    private fun aplicarRegistroMovil(base: RegistroEntity?, campos: JsonObject): RegistroEntity {
        val ahora = System.currentTimeMillis()
        val uuid = texto(campos, "uuid_movil") ?: base?.uuid ?: ""
        val e = base ?: RegistroEntity(
            uuid = uuid,
            titulo = "",
            contenido = "",
            categoria = "general",
            valor = null,
            creadoEn = ahora,
            actualizadoEn = ahora,
            estado = "SINCRONIZADO",
            eliminado = false,
            dispositivo = "remoto",
            usuario = "remoto",
            ultimaSync = null,
        )
        val activo = entero(campos, "activo")
        return e.copy(
            uuid = uuid,
            titulo = texto(campos, "titulo") ?: e.titulo,
            contenido = textoO(campos, "contenido", e.contenido) ?: e.contenido,
            categoria = texto(campos, "categoria") ?: e.categoria,
            valor = if (campos.containsKey("valor")) real(campos, "valor") else e.valor,
            creadoEn = fechaMillisO(campos, "creado_en", e.creadoEn),
            actualizadoEn = fechaMillisO(campos, "actualizado_en", e.actualizadoEn),
            dispositivo = textoO(campos, "dispositivo", e.dispositivo) ?: e.dispositivo,
            usuario = textoO(campos, "usuario", e.usuario) ?: e.usuario,
            eliminado = if (activo != null) activo == 0 else e.eliminado,
        )
    }
}

// ==================================================================
// Escritura del payload (construcción)
// ==================================================================

/** Añade el campo solo si cumple la regla de «solo lo tocado» */
private fun poner(
    campos: MutableMap<String, JsonElement>,
    campo: String,
    valor: String?,
    forzar: Boolean,
) {
    if (valor == null) {
        if (forzar) campos[campo] = JsonNull
    } else {
        campos[campo] = JsonPrimitive(valor)
    }
}

private fun poner(
    campos: MutableMap<String, JsonElement>,
    campo: String,
    valor: Int?,
    forzar: Boolean,
) {
    if (valor == null) {
        if (forzar) campos[campo] = JsonNull
    } else {
        campos[campo] = JsonPrimitive(valor)
    }
}

private fun poner(
    campos: MutableMap<String, JsonElement>,
    campo: String,
    valor: Double?,
    forzar: Boolean,
) {
    if (valor == null) {
        if (forzar) campos[campo] = JsonNull
    } else {
        campos[campo] = JsonPrimitive(valor)
    }
}

private fun poner(
    campos: MutableMap<String, JsonElement>,
    campo: String,
    valor: Boolean?,
    forzar: Boolean,
) {
    if (valor == null) {
        if (forzar) campos[campo] = JsonNull
    } else {
        campos[campo] = JsonPrimitive(valor)
    }
}

/** Lectura cómoda de un payload decodificado; tolera claves desconocidas */
fun JsonObject.deTexto(campo: String): String? = Espejo.texto(this, campo)

fun JsonObject.deEntero(campo: String): Int? = Espejo.entero(this, campo)

fun JsonObject.deReal(campo: String): Double? = Espejo.real(this, campo)

/** Convierte cualquier elemento del protocolo a su forma de texto simple */
fun JsonElement.aTexto(): String? = when (this) {
    is JsonNull -> null
    is JsonPrimitive -> contentOrNull
    else -> (this as? JsonObject)?.get("v")?.let { (it as? JsonPrimitive)?.contentOrNull }
}

/** Objeto JSON vacío reutilizable */
fun jsonObjectVacio(): JsonObject = JsonObject(emptyMap())

/** Decodifica un payload de texto JSON a objeto; null si no lo es */
fun textoAJsonObject(texto: String?): JsonObject? {
    if (texto.isNullOrBlank()) return null
    return runCatching {
        kotlinx.serialization.json.Json.parseToJsonElement(texto).jsonObject
    }.getOrNull()
}

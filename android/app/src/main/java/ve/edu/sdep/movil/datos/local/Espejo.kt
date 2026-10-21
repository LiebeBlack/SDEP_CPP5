package ve.edu.sdep.movil.datos.local

import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
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
 *   local: es el UUID global del empleado, que este equipo traduce a su id.
 * * **Las rutas de archivo no viajan** (`foto_ruta`, `ruta_archivo`,
 *   `documento_soporte_ruta`, `archivo_ruta`): una ruta de otro equipo no
 *   significa nada aquí. El contenido sí, identificado por su hash.
 * * **`id` nunca viaja**: la identidad local no significa nada en otro equipo.
 *
 * Los valores del protocolo pueden llegar con etiqueta de tipo
 * (`{"__t__": "datetime", "v": "…"}` para fechas y decimales); [texto],
 * [entero] y [real] las normalizan antes de aplicarlas.
 */
object Espejo {

    /** Clave natural de cada tabla (columna que unifica filas entre equipos) */
    val CLAVE_NATURAL: Map<String, List<String>> = mapOf(
        "empleados" to listOf("cedula"),
        "contratos" to listOf("numero"),
        "estudiantes" to listOf("cedula"),
        "periodos_academicos" to listOf("nombre"),
        "configuraciones" to listOf("clave"),
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

    fun booleano(campos: JsonObject, campo: String): Boolean? {
        val elemento = campos[campo] ?: return null
        if (elemento is JsonNull) return null
        (elemento as? JsonPrimitive)?.booleanOrNull?.let { return it }
        return when (elemento.textoCrudo()?.lowercase()) {
            "true", "1", "yes", "on", "si", "sí" -> true
            "false", "0", "no", "off" -> false
            else -> null
        }
    }

    /** Fecha u hora en ISO simple (sin etiqueta de tipo ni zona horaria) */
    fun fecha(campos: JsonObject, campo: String): String? {
        val texto = texto(campos, campo) ?: return null
        return normalizarIso(texto)
    }

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

    private fun JsonElement.desenvuelto(): JsonElement? =
        (this as? JsonObject)?.get("v")

    // ==================================================================
    // Escritura del payload (construcción)
    // ==================================================================

    /** Añade el campo solo si cumple la regla de «solo lo tocado» */
    private fun MutableMap<String, JsonElement>.poner(
        campo: String,
        valor: String?,
        forzar: Boolean,
    ) {
        if (valor == null) {
            if (forzar) this[campo] = JsonNull
        } else {
            this[campo] = JsonPrimitive(valor)
        }
    }

    private fun MutableMap<String, JsonElement>.poner(
        campo: String,
        valor: Int?,
        forzar: Boolean,
    ) {
        if (valor == null) {
            if (forzar) this[campo] = JsonNull
        } else {
            this[campo] = JsonPrimitive(valor)
        }
    }

    private fun MutableMap<String, JsonElement>.poner(
        campo: String,
        valor: Double?,
        forzar: Boolean,
    ) {
        if (valor == null) {
            if (forzar) this[campo] = JsonNull
        } else {
            this[campo] = JsonPrimitive(valor)
        }
    }

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
                fun tocado(campo: String, viejo: Any?, nuevo: Any?): Boolean = completa || viejo != nuevo
                campos["nombres"] = JsonPrimitive(e.nombres)
                campos["apellidos"] = JsonPrimitive(e.apellidos)
                campos["cedula"] = JsonPrimitive(e.cedula)
                poner("fecha_nacimiento", e.fechaNacimiento, completa || a?.fechaNacimiento != e.fechaNacimiento)
                poner("genero", e.genero, completa || a?.genero != e.genero)
                poner("estado_civil", e.estadoCivil, completa || a?.estadoCivil != e.estadoCivil)
                poner("nacionalidad", e.nacionalidad, completa || a?.nacionalidad != e.nacionalidad)
                poner("peso", e.peso, completa || a?.peso != e.peso)
                poner("altura", e.altura, completa || a?.altura != e.altura)
                poner("tipo_sangre", e.tipoSangre, completa || a?.tipoSangre != e.tipoSangre)
                poner("telefono", e.telefono, completa || a?.telefono != e.telefono)
                poner("celular", e.celular, completa || a?.celular != e.celular)
                poner("email", e.email, completa || a?.email != e.email)
                poner("direccion", e.direccion, completa || a?.direccion != e.direccion)
                poner("ciudad", e.ciudad, completa || a?.ciudad != e.ciudad)
                poner("estado", e.estado, completa || a?.estado != e.estado)
                poner("codigo_postal", e.codigoPostal, completa || a?.codigoPostal != e.codigoPostal)
                campos["tipo_empleado"] = JsonPrimitive(e.tipoEmpleado)
                campos["cargo"] = JsonPrimitive(e.cargo)
                campos["departamento"] = JsonPrimitive(e.departamento)
                campos["fecha_contratacion"] = JsonPrimitive(e.fechaContratacion)
                poner("fecha_terminacion", e.fechaTerminacion, completa || a?.fechaTerminacion != e.fechaTerminacion)
                campos["salario_base"] = JsonPrimitive(e.salarioBase)
                poner("activo", e.activo, completa || a?.activo != e.activo)
                poner("nivel_educativo", e.nivelEducativo, completa || a?.nivelEducativo != e.nivelEducativo)
                poner("especialidad", e.especialidad, completa || a?.especialidad != e.especialidad)
                poner("titulo_obtenido", e.tituloObtenido, completa || a?.tituloObtenido != e.tituloObtenido)
                poner("titulo_secundaria", e.tituloSecundaria, completa || a?.tituloSecundaria != e.tituloSecundaria)
                poner("institucion_bancaria", e.institucionBancaria, completa || a?.institucionBancaria != e.institucionBancaria)
                poner("numero_cuenta", e.numeroCuenta, completa || a?.numeroCuenta != e.numeroCuenta)
                poner("tipo_cuenta", e.tipoCuenta, completa || a?.tipoCuenta != e.tipoCuenta)
                poner("carnet_discapacidad", e.carnetDiscapacidad, completa || a?.carnetDiscapacidad != e.carnetDiscapacidad)
                poner("enfermedades_preexistentes", e.enfermedadesPreexistentes, completa || a?.enfermedadesPreexistentes != e.enfermedadesPreexistentes)
                poner("alergias_medicamentosas", e.alergiasMedicamentosas, completa || a?.alergiasMedicamentosas != e.alergiasMedicamentosas)
                poner("alergias_alimentarias", e.alergiasAlimentarias, completa || a?.alergiasAlimentarias != e.alergiasAlimentarias)
                poner("tipo_contratacion", e.tipoContratacion, completa || a?.tipoContratacion != e.tipoContratacion)
                poner("hijos", e.hijos, completa || a?.hijos != e.hijos)
                poner("observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
                poner("contacto_emergencia_nombre", e.contactoEmergenciaNombre, completa || a?.contactoEmergenciaNombre != e.contactoEmergenciaNombre)
                poner("contacto_emergencia_telefono", e.contactoEmergenciaTelefono, completa || a?.contactoEmergenciaTelefono != e.contactoEmergenciaTelefono)
                poner("contacto_emergencia_relacion", e.contactoEmergenciaRelacion, completa || a?.contactoEmergenciaRelacion != e.contactoEmergenciaRelacion)
                if (completa) {
                    poner("created_at", e.creadoEn.ifBlank { null }, true)
                    poner("updated_at", e.actualizadoEn.ifBlank { null }, true)
                } else if (a?.actualizadoEn != e.actualizadoEn) {
                    poner("updated_at", e.actualizadoEn.ifBlank { null }, true)
                }
            }

            "documentos" -> {
                val e = entidad as DocumentoEntity
                val a = anterior as? DocumentoEntity
                campos["empleado_id"] = JsonPrimitive(e.empleadoId.toString())
                campos["tipo_documento"] = JsonPrimitive(e.tipoDocumento)
                campos["titulo"] = JsonPrimitive(e.titulo)
                poner("descripcion", e.descripcion, completa || a?.descripcion != e.descripcion)
                poner("numero_documento", e.numeroDocumento, completa || a?.numeroDocumento != e.numeroDocumento)
                poner("fecha_emision", e.fechaEmision, completa || a?.fechaEmision != e.fechaEmision)
                poner("fecha_vencimiento", e.fechaVencimiento, completa || a?.fechaVencimiento != e.fechaVencimiento)
                campos["nombre_archivo"] = JsonPrimitive(e.nombreArchivo)
                poner("tamano_bytes", e.tamanoBytes, completa || a?.tamanoBytes != e.tamanoBytes)
                poner("tipo_mime", e.tamanoMime ?: e.tipoMime, completa || a?.tipoMime != e.tipoMime)
                // El contenido viaja como hash (canal de binarios), no como bytes
                if (e.contenidoHash != null && (completa || a?.contenidoHash != e.contenidoHash)) {
                    campos["contenido_binario"] = marcaBlob(
                        e.contenidoHash,
                        e.tamanoBytes ?: 0,
                    )
                }
                poner("activo", e.activo, completa || a?.activo != e.activo)
                poner("observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
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
                poner("fecha_aprobacion", e.fechaAprobacion, completa || a?.fechaAprobacion != e.fechaAprobacion)
                campos["motivo"] = JsonPrimitive(e.motivo)
                poner("descripcion", e.descripcion, completa || a?.descripcion != e.descripcion)
                campos["dias_solicitados"] = JsonPrimitive(e.diasSolicitados)
                poner("dias_aprobados", e.diasAprobados, completa || a?.diasAprobados != e.diasAprobados)
                poner("documento_soporte_nombre", e.documentoSoporteNombre, completa || a?.documentoSoporteNombre != e.documentoSoporteNombre)
                if (e.documentoSoporteHash != null && (completa || a?.documentoSoporteHash != e.documentoSoporteHash)) {
                    campos["documento_soporte_binario"] = marcaBlob(
                        e.documentoSoporteHash,
                        0,
                    )
                }
                poner("aprobado_por", e.aprobadoPor, completa || a?.aprobadoPor != e.aprobadoPor)
                poner("comentarios_aprobacion", e.comentariosAprobacion, completa || a?.comentariosAprobacion != e.comentariosAprobacion)
                poner("afecta_nominas", e.afectaNominas, completa || a?.afectaNominas != e.afectaNominas)
                poner("descuento_dias", e.descuentoDias, completa || a?.descuentoDias != e.descuentoDias)
                poner("observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
            }

            "contratos" -> {
                val e = entidad as ContratoEntity
                val a = anterior as? ContratoEntity
                campos["empleado_id"] = JsonPrimitive(e.empleadoId.toString())
                campos["numero"] = JsonPrimitive(e.numero)
                campos["tipo"] = JsonPrimitive(e.tipo)
                campos["estado"] = JsonPrimitive(e.estado)
                campos["cargo"] = JsonPrimitive(e.cargo)
                poner("departamento", e.departamento, completa || a?.departamento != e.departamento)
                campos["salario_pactado"] = JsonPrimitive(e.salarioPactado)
                campos["horas_semanales"] = JsonPrimitive(e.horasSemanales)
                campos["fecha_inicio"] = JsonPrimitive(e.fechaInicio)
                poner("fecha_fin", e.fechaFin, completa || a?.fechaFin != e.fechaFin)
                poner("renovacion_automatica", e.renovacionAutomatica, completa || a?.renovacionAutomatica != e.renovacionAutomatica)
                poner("contrato_anterior_id", e.contratoAnteriorId?.toString(), completa || a?.contratoAnteriorId != e.contratoAnteriorId)
                poner("clausulas", e.clausulas, completa || a?.clausulas != e.clausulas)
                poner("motivo_terminacion", e.motivoTerminacion, completa || a?.motivoTerminacion != e.motivoTerminacion)
                poner("fecha_terminacion", e.fechaTerminacion, completa || a?.fechaTerminacion != e.fechaTerminacion)
                poner("liquidacion_monto", e.liquidacionMonto, completa || a?.liquidacionMonto != e.liquidacionMonto)
                poner("aprobado_por", e.aprobadoPor, completa || a?.aprobadoPor != e.aprobadoPor)
                poner("observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
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
                poner("descuentos", e.descuentos, completa || a?.descuentos != e.descuentos)
                poner("bonificaciones", e.bonificaciones, completa || a?.bonificaciones != e.bonificaciones)
                poner("horas_extra", e.horasExtra, completa || a?.horasExtra != e.horasExtra)
                poner("deduccion_seguro", e.deduccionSeguro, completa || a?.deduccionSeguro != e.deduccionSeguro)
                poner("deduccion_pension", e.deduccionPension, completa || a?.deduccionPension != e.deduccionPension)
                poner("deduccion_impuesto", e.deduccionImpuesto, completa || a?.deduccionImpuesto != e.deduccionImpuesto)
                poner("otras_deducciones", e.otrasDeducciones, completa || a?.otrasDeducciones != e.otrasDeducciones)
                poner("modalidad_calculo", e.modalidadCalculo, completa || a?.modalidadCalculo != e.modalidadCalculo)
                poner("base_gravable", e.baseGravable, completa || a?.baseGravable != e.baseGravable)
                poner("horas_extra_diurnas", e.horasExtraDiurnas, completa || a?.horasExtraDiurnas != e.horasExtraDiurnas)
                poner("horas_extra_nocturnas", e.horasExtraNocturnas, completa || a?.horasExtraNocturnas != e.horasExtraNocturnas)
                poner("horas_extra_feriadas", e.horasExtraFeriadas, completa || a?.horasExtraFeriadas != e.horasExtraFeriadas)
                poner("aguinaldo", e.aguinaldo, completa || a?.aguinaldo != e.aguinaldo)
                poner("bono_vacacional", e.bonoVacacional, completa || a?.bonoVacacional != e.bonoVacacional)
                poner("aporte_seguro_patronal", e.aporteSeguroPatronal, completa || a?.aporteSeguroPatronal != e.aporteSeguroPatronal)
                poner("aporte_pension_patronal", e.aportePensionPatronal, completa || a?.aportePensionPatronal != e.aportePensionPatronal)
                poner("isr_tramo", e.isrTramo, completa || a?.isrTramo != e.isrTramo)
                poner("dias_laborados", e.diasLaborados, completa || a?.diasLaborados != e.diasLaborados)
                poner("dias_periodo", e.diasPeriodo, completa || a?.diasPeriodo != e.diasPeriodo)
                poner("prorrateado", e.prorrateado, completa || a?.prorrateado != e.prorrateado)
                poner("descripcion", e.descripcion, completa || a?.descripcion != e.descripcion)
                poner("referencia_pago", e.referenciaPago, completa || a?.referenciaPago != e.referenciaPago)
                poner("observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
                poner("pagado", e.pagado, completa || a?.pagado != e.pagado)
                poner("fecha_registro_pago", e.fechaRegistroPago, completa || a?.fechaRegistroPago != e.fechaRegistroPago)
            }

            "estudiantes" -> {
                val e = entidad as EstudianteEntity
                val a = anterior as? EstudianteEntity
                campos["nombres"] = JsonPrimitive(e.nombres)
                campos["apellidos"] = JsonPrimitive(e.apellidos)
                poner("cedula", e.cedula, completa || a?.cedula != e.cedula)
                poner("fecha_nacimiento", e.fechaNacimiento, completa || a?.fechaNacimiento != e.fechaNacimiento)
                poner("genero", e.genero, completa || a?.genero != e.genero)
                campos["nivel"] = JsonPrimitive(e.nivel)
                poner("representante", e.representante, completa || a?.representante != e.representante)
                poner("telefono", e.telefono, completa || a?.telefono != e.telefono)
                poner("telefono_representante", e.telefonoRepresentante, completa || a?.telefonoRepresentante != e.telefonoRepresentante)
                poner("email", e.email, completa || a?.email != e.email)
                poner("direccion", e.direccion, completa || a?.direccion != e.direccion)
                poner("observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
                poner("activo", e.activo, completa || a?.activo != e.activo)
            }

            "periodos_academicos" -> {
                val e = entidad as PeriodoAcademicoEntity
                val a = anterior as? PeriodoAcademicoEntity
                campos["nombre"] = JsonPrimitive(e.nombre)
                poner("fecha_inicio", e.fechaInicio, completa || a?.fechaInicio != e.fechaInicio)
                poner("fecha_fin", e.fechaFin, completa || a?.fechaFin != e.fechaFin)
                campos["estado"] = JsonPrimitive(e.estado)
                poner("cerrado_en", e.cerradoEn, completa || a?.cerradoEn != e.cerradoEn)
                poner("cerrado_por", e.cerradoPor, completa || a?.cerradoPor != e.cerradoPor)
                poner("observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
            }

            "grados" -> {
                val e = entidad as GradoEntity
                val a = anterior as? GradoEntity
                campos["periodo_id"] = JsonPrimitive(e.periodoId.toString())
                campos["nivel"] = JsonPrimitive(e.nivel)
                campos["nombre"] = JsonPrimitive(e.nombre)
                campos["seccion"] = JsonPrimitive(e.seccion)
                // La asignación de profesor es una decisión del escritorio: el
                // UUID viaja tal cual (usuarios no se replican) y solo se
                // envía en el alta o si cambió localmente por una acción.
                poner("profesor_uuid", e.profesorUuid, completa || a?.profesorUuid != e.profesorUuid)
                poner("observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
            }

            "matriculas" -> {
                val e = entidad as MatriculaEntity
                val a = anterior as? MatriculaEntity
                campos["estudiante_id"] = JsonPrimitive(e.estudianteId.toString())
                campos["grado_id"] = JsonPrimitive(e.gradoId.toString())
                campos["fecha_matricula"] = JsonPrimitive(e.fechaMatricula)
                poner("activa", e.activa, completa || a?.activa != e.activa)
                poner("observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
            }

            "notas_finales" -> {
                val e = entidad as NotaFinalEntity
                val a = anterior as? NotaFinalEntity
                campos["estudiante_id"] = JsonPrimitive(e.estudianteId.toString())
                campos["grado_id"] = JsonPrimitive(e.gradoId.toString())
                campos["materia"] = JsonPrimitive(e.materia)
                campos["calificacion"] = JsonPrimitive(e.calificacion)
                poner("registrado_por", e.registradoPor, completa || a?.registradoPor != e.registradoPor)
                poner("observaciones", e.observaciones, completa || a?.observaciones != e.observaciones)
            }

            "configuraciones" -> {
                val e = entidad as ConfiguracionEntity
                val a = anterior as? ConfiguracionEntity
                campos["clave"] = JsonPrimitive(e.clave)
                poner("valor", e.valor, completa || a?.valor != e.valor)
                poner("descripcion", e.descripcion, completa || a?.descripcion != e.descripcion)
                campos["tipo_dato"] = JsonPrimitive(e.tipoDato)
                poner("categoria", e.categoria, completa || a?.categoria != e.categoria)
                poner("editable", e.editable, completa || a?.editable != e.editable)
            }

            else -> return null
        }

        // Las claves foráneas viajan como identidad global, nunca como id local
        val foraneas = CLAVES_FORANEAS[tabla].orEmpty().keys
        for (columna in foraneas) {
            val valor = campos[columna] as? JsonPrimitive
            if (valor != null && valor.contentOrNull?.all { it in '0'..'9' } == true) {
                // Un id local en el payload sería un dato incorrecto en otro
                // equipo: se omite y el Aplicador lo resuelve por identidad.
                campos.remove(columna)
            }
        }

        // Nada que enviar en una edición sin cambios
        if (!completa && campos.isEmpty()) return null
        return JsonObject(campos)
    }

    // ==================================================================
    // Aplicación del payload sobre una fila local
    // ==================================================================

    /**
     * Aplica los campos del payload a una fila.
     *
     * @param base La fila existente (edición) o null (alta)
     * @param campos Payload ya traducido (claves foráneas como id local)
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
        else -> null
    }

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
            fechaNacimiento = fecha(campos, "fecha_nacimiento"),
            genero = texto(campos, "genero"),
            estadoCivil = texto(campos, "estado_civil"),
            nacionalidad = texto(campos, "nacionalidad"),
            peso = real(campos, "peso"),
            altura = real(campos, "altura"),
            tipoSangre = texto(campos, "tipo_sangre"),
            fotoRuta = e.fotoRuta,
            telefono = texto(campos, "telefono"),
            celular = texto(campos, "celular"),
            email = texto(campos, "email"),
            direccion = texto(campos, "direccion"),
            ciudad = texto(campos, "ciudad"),
            estado = texto(campos, "estado"),
            codigoPostal = texto(campos, "codigo_postal"),
            tipoEmpleado = texto(campos, "tipo_empleado") ?: e.tipoEmpleado,
            cargo = texto(campos, "cargo") ?: e.cargo,
            departamento = texto(campos, "departamento") ?: e.departamento,
            fechaContratacion = fecha(campos, "fecha_contratacion") ?: e.fechaContratacion,
            fechaTerminacion = fecha(campos, "fecha_terminacion"),
            salarioBase = real(campos, "salario_base") ?: e.salarioBase,
            activo = entero(campos, "activo") ?: e.activo,
            nivelEducativo = texto(campos, "nivel_educativo"),
            especialidad = texto(campos, "especialidad"),
            tituloObtenido = texto(campos, "titulo_obtenido"),
            tituloSecundaria = texto(campos, "titulo_secundaria"),
            institucionBancaria = texto(campos, "institucion_bancaria"),
            numeroCuenta = texto(campos, "numero_cuenta"),
            tipoCuenta = texto(campos, "tipo_cuenta"),
            carnetDiscapacidad = texto(campos, "carnet_discapacidad"),
            enfermedadesPreexistentes = texto(campos, "enfermedades_preexistentes"),
            alergiasMedicamentosas = texto(campos, "alergias_medicamentosas"),
            alergiasAlimentarias = texto(campos, "alergias_alimentarias"),
            tipoContratacion = texto(campos, "tipo_contratacion"),
            hijos = texto(campos, "hijos"),
            observaciones = texto(campos, "observaciones"),
            contactoEmergenciaNombre = texto(campos, "contacto_emergencia_nombre"),
            contactoEmergenciaTelefono = texto(campos, "contacto_emergencia_telefono"),
            contactoEmergenciaRelacion = texto(campos, "contacto_emergencia_relacion"),
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
            descripcion = texto(campos, "descripcion"),
            numeroDocumento = texto(campos, "numero_documento"),
            fechaEmision = fecha(campos, "fecha_emision"),
            fechaVencimiento = fecha(campos, "fecha_vencimiento"),
            nombreArchivo = texto(campos, "nombre_archivo") ?: e.nombreArchivo,
            rutaArchivo = e.rutaArchivo,
            tamanoBytes = entero(campos, "tamano_bytes"),
            tipoMime = texto(campos, "tipo_mime"),
            contenidoHash = hashBlob(campos, "contenido_binario") ?: e.contenidoHash,
            activo = entero(campos, "activo") ?: e.activo,
            observaciones = texto(campos, "observaciones"),
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
            fechaAprobacion = fecha(campos, "fecha_aprobacion"),
            motivo = texto(campos, "motivo") ?: e.motivo,
            descripcion = texto(campos, "descripcion"),
            diasSolicitados = entero(campos, "dias_solicitados") ?: e.diasSolicitados,
            diasAprobados = entero(campos, "dias_aprobados"),
            documentoSoporteNombre = texto(campos, "documento_soporte_nombre"),
            documentoSoporteHash = hashBlob(campos, "documento_soporte_binario")
                ?: e.documentoSoporteHash,
            aprobadoPor = texto(campos, "aprobado_por"),
            comentariosAprobacion = texto(campos, "comentarios_aprobacion"),
            afectaNominas = entero(campos, "afecta_nominas") ?: e.afectaNominas,
            descuentoDias = real(campos, "descuento_dias"),
            observaciones = texto(campos, "observaciones"),
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
            departamento = texto(campos, "departamento"),
            salarioPactado = real(campos, "salario_pactado") ?: e.salarioPactado,
            horasSemanales = entero(campos, "horas_semanales") ?: e.horasSemanales,
            fechaInicio = fecha(campos, "fecha_inicio") ?: e.fechaInicio,
            fechaFin = fecha(campos, "fecha_fin"),
            renovacionAutomatica = entero(campos, "renovacion_automatica") ?: e.renovacionAutomatica,
            contratoAnteriorId = entero(campos, "contrato_anterior_id")?.toLong(),
            archivoRuta = e.archivoRuta,
            clausulas = texto(campos, "clausulas"),
            motivoTerminacion = texto(campos, "motivo_terminacion"),
            fechaTerminacion = fecha(campos, "fecha_terminacion"),
            liquidacionMonto = real(campos, "liquidacion_monto") ?: e.liquidacionMonto,
            aprobadoPor = texto(campos, "aprobado_por"),
            observaciones = texto(campos, "observaciones"),
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
            descuentos = real(campos, "descuentos") ?: e.descuentos,
            bonificaciones = real(campos, "bonificaciones") ?: e.bonificaciones,
            horasExtra = real(campos, "horas_extra") ?: e.horasExtra,
            salarioBase = real(campos, "salario_base") ?: e.salarioBase,
            deduccionSeguro = real(campos, "deduccion_seguro") ?: e.deduccionSeguro,
            deduccionPension = real(campos, "deduccion_pension") ?: e.deduccionPension,
            deduccionImpuesto = real(campos, "deduccion_impuesto") ?: e.deduccionImpuesto,
            otrasDeducciones = real(campos, "otras_deducciones") ?: e.otrasDeducciones,
            modalidadCalculo = texto(campos, "modalidad_calculo") ?: e.modalidadCalculo,
            baseGravable = real(campos, "base_gravable") ?: e.baseGravable,
            horasExtraDiurnas = real(campos, "horas_extra_diurnas") ?: e.horasExtraDiurnas,
            horasExtraNocturnas = real(campos, "horas_extra_nocturnas") ?: e.horasExtraNocturnas,
            horasExtraFeriadas = real(campos, "horas_extra_feriadas") ?: e.horasExtraFeriadas,
            aguinaldo = real(campos, "aguinaldo") ?: e.aguinaldo,
            bonoVacacional = real(campos, "bono_vacacional") ?: e.bonoVacacional,
            aporteSeguroPatronal = real(campos, "aporte_seguro_patronal") ?: e.aporteSeguroPatronal,
            aportePensionPatronal = real(campos, "aporte_pension_patronal") ?: e.aportePensionPatronal,
            isrTramo = texto(campos, "isr_tramo"),
            diasLaborados = entero(campos, "dias_laborados"),
            diasPeriodo = entero(campos, "dias_periodo"),
            prorrateado = entero(campos, "prorrateado"),
            descripcion = texto(campos, "descripcion"),
            referenciaPago = texto(campos, "referencia_pago"),
            observaciones = texto(campos, "observaciones"),
            pagado = entero(campos, "pagado") ?: e.pagado,
            fechaRegistroPago = fecha(campos, "fecha_registro_pago"),
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
    }

    private fun aplicarEstudiante(base: EstudianteEntity?, campos: JsonObject): EstudianteEntity {
        val e = base ?: EstudianteEntity(nombres = "", apellidos = "", nivel = "secundaria")
        return e.copy(
            nombres = texto(campos, "nombres") ?: e.nombres,
            apellidos = texto(campos, "apellidos") ?: e.apellidos,
            cedula = texto(campos, "cedula"),
            fechaNacimiento = fecha(campos, "fecha_nacimiento"),
            genero = texto(campos, "genero"),
            nivel = texto(campos, "nivel") ?: e.nivel,
            representante = texto(campos, "representante"),
            telefono = texto(campos, "telefono"),
            telefonoRepresentante = texto(campos, "telefono_representante"),
            email = texto(campos, "email"),
            direccion = texto(campos, "direccion"),
            observaciones = texto(campos, "observaciones"),
            activo = entero(campos, "activo") ?: e.activo,
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
    }

    private fun aplicarPeriodo(base: PeriodoAcademicoEntity?, campos: JsonObject): PeriodoAcademicoEntity {
        val e = base ?: PeriodoAcademicoEntity(nombre = "")
        return e.copy(
            nombre = texto(campos, "nombre") ?: e.nombre,
            fechaInicio = fecha(campos, "fecha_inicio"),
            fechaFin = fecha(campos, "fecha_fin"),
            estado = texto(campos, "estado") ?: e.estado,
            cerradoEn = texto(campos, "cerrado_en"),
            cerradoPor = texto(campos, "cerrado_por"),
            observaciones = texto(campos, "observaciones"),
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
            profesorUuid = texto(campos, "profesor_uuid") ?: e.profesorUuid,
            observaciones = texto(campos, "observaciones"),
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
            activa = entero(campos, "activa") ?: e.activa,
            observaciones = texto(campos, "observaciones"),
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
            registradoPor = texto(campos, "registrado_por"),
            observaciones = texto(campos, "observaciones"),
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
    }

    private fun aplicarConfiguracion(base: ConfiguracionEntity?, campos: JsonObject): ConfiguracionEntity {
        val e = base ?: ConfiguracionEntity(clave = "", tipoDato = "string")
        return e.copy(
            clave = texto(campos, "clave") ?: e.clave,
            valor = texto(campos, "valor"),
            descripcion = texto(campos, "descripcion"),
            tipoDato = texto(campos, "tipo_dato") ?: e.tipoDato,
            categoria = texto(campos, "categoria"),
            editable = entero(campos, "editable") ?: e.editable,
            creadoEn = fecha(campos, "created_at") ?: e.creadoEn,
            actualizadoEn = fecha(campos, "updated_at") ?: e.actualizadoEn,
        )
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
    else -> EspechoFallback(this)
}

private fun EspechoFallback(elemento: JsonElement): String? =
    (elemento as? JsonObject)?.get("v")?.let { (it as? JsonPrimitive)?.contentOrNull }

/** Objeto JSON vacío reutilizable */
fun jsonObjectVacio(): JsonObject = JsonObject(emptyMap())

/** Decodifica un payload de texto JSON a objeto; null si no lo es */
fun textoAJsonObject(texto: String?): JsonObject? {
    if (texto.isNullOrBlank()) return null
    return runCatching {
        kotlinx.serialization.json.Json.parseToJsonElement(texto).jsonObject
    }.getOrNull()
}

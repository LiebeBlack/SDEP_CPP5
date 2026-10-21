package ve.edu.sdep.movil.dominio.modelo

/**
 * Enumeraciones del sistema, espejo exacto de `src/models/enums.py`.
 *
 * Los valores de cada miembro son los textos que la base de datos guarda y que
 * el protocolo sincroniza («snake_case»): así una fila leída en el escritorio
 * se lee igual en el teléfono, sin tabla de traducción.
 *
 * Toda coerción de texto sigue la política de `BaseEnum.coerce` del escritorio:
 * se acepta el miembro, su valor o su nombre; lo desconocido cae al valor por
 * defecto de la función, nunca lanza en una lectura (un dato de otro equipo no
 * debe tumbar la pantalla), pero las acciones de escritura validan aparte.
 */

// ----------------------------------------------------------------Personal
enum class TipoEmpleado(val valor: String, val etiqueta: String) {
    DOCENTE("docente", "Docente"),
    ADMINISTRATIVO("administrativo", "Administrativo"),
    MANTENIMIENTO("mantenimiento", "Mantenimiento"),
    ;

    companion object {
        fun desde(valor: String?): TipoEmpleado =
            entries.firstOrNull { it.valor == valor || it.name.equals(valor, true) } ?: DOCENTE
    }
}

enum class Genero(val valor: String, val etiqueta: String) {
    MASCULINO("masculino", "Masculino"),
    FEMENINO("femenino", "Femenino"),
    OTRO("otro", "Otro"),
    ;

    companion object {
        fun desde(valor: String?): Genero =
            entries.firstOrNull { it.valor == valor || it.name.equals(valor, true) } ?: MASCULINO
    }
}

enum class EstadoCivil(val valor: String, val etiqueta: String) {
    SOLTERO("soltero", "Soltero(a)"),
    CASADO("casado", "Casado(a)"),
    DIVORCIADO("divorciado", "Divorciado(a)"),
    VIUDO("viudo", "Viudo(a)"),
    UNION_LIBRE("union_libre", "Unión libre"),
    ;

    companion object {
        fun desde(valor: String?): EstadoCivil =
            entries.firstOrNull { it.valor == valor || it.name.equals(valor, true) } ?: SOLTERO
    }
}

// ----------------------------------------------------------------Documentos
enum class TipoDocumento(val valor: String, val etiqueta: String) {
    CEDULA("cedula", "Cédula"),
    TITULO("titulo", "Título"),
    REPOSO("reposo", "Reposo"),
    CERTIFICADO("certificado", "Certificado"),
    EXPEDIENTE("expediente", "Expediente"),
    OTRO("otro", "Otro"),
    ;

    companion object {
        fun desde(valor: String?): TipoDocumento =
            entries.firstOrNull { it.valor == valor || it.name.equals(valor, true) } ?: OTRO
    }
}

// ----------------------------------------------------------------Incidencias
enum class TipoIncidencia(val valor: String, val etiqueta: String) {
    REPOSO_MEDICO("reposo_medico", "Reposo médico"),
    AUSENCIA("ausencia", "Ausencia"),
    PERMISO("permiso", "Permiso"),
    VACACIONES("vacaciones", "Vacaciones"),
    LICENCIA("licencia", "Licencia"),
    ;

    companion object {
        fun desde(valor: String?): TipoIncidencia =
            entries.firstOrNull { it.valor == valor || it.name.equals(valor, true) } ?: AUSENCIA
    }
}

enum class EstadoIncidencia(val valor: String, val etiqueta: String) {
    PENDIENTE("pendiente", "Pendiente"),
    APROBADO("aprobado", "Aprobada"),
    RECHAZADO("rechazado", "Rechazada"),
    COMPLETADO("completado", "Completada"),
    ;

    companion object {
        fun desde(valor: String?): EstadoIncidencia =
            entries.firstOrNull { it.valor == valor || it.name.equals(valor, true) } ?: PENDIENTE
    }
}

// ----------------------------------------------------------------Nómina
enum class TipoPago(val valor: String, val etiqueta: String) {
    SALARIO_BASE("salario_base", "Salario base"),
    BONIFICACION("bonificacion", "Bonificación"),
    DESCUENTO("descuento", "Descuento"),
    HORAS_EXTRA("horas_extra", "Horas extra"),
    COMISION("comision", "Comisión"),
    LIQUIDACION("liquidacion", "Liquidación"),
    ;

    companion object {
        fun desde(valor: String?): TipoPago =
            entries.firstOrNull { it.valor == valor || it.name.equals(valor, true) } ?: SALARIO_BASE
    }
}

enum class MetodoPago(val valor: String, val etiqueta: String) {
    TRANSFERENCIA("transferencia", "Transferencia"),
    EFECTIVO("efectivo", "Efectivo"),
    CHEQUE("cheque", "Cheque"),
    DEPOSITO("deposito", "Depósito"),
    ;

    companion object {
        fun desde(valor: String?): MetodoPago =
            entries.firstOrNull { it.valor == valor || it.name.equals(valor, true) } ?: TRANSFERENCIA
    }
}

enum class ModoCalculoNomina(val valor: String, val etiqueta: String) {
    PORCENTAJE("porcentaje", "Porcentual (histórica)"),
    TRAMOS("tramos", "Tramos progresivos de ISR"),
    ;

    companion object {
        fun desde(valor: String?): ModoCalculoNomina =
            entries.firstOrNull { it.valor == valor || it.name.equals(valor, true) } ?: PORCENTAJE
    }
}

// ----------------------------------------------------------------Contratos
enum class TipoContrato(val valor: String, val etiqueta: String) {
    INDEFINIDO("indefinido", "Indefinido"),
    TEMPORAL("temporal", "Temporal"),
    OBRA("obra", "Por obra"),
    PASANTIA("pasantia", "Pasantía"),
    ;

    companion object {
        fun desde(valor: String?): TipoContrato =
            entries.firstOrNull { it.valor == valor || it.name.equals(valor, true) } ?: INDEFINIDO
    }
}

enum class EstadoContrato(val valor: String, val etiqueta: String) {
    VIGENTE("vigente", "Vigente"),
    RENOVADO("renovado", "Renovado"),
    VENCIDO("vencido", "Vencido"),
    TERMINADO("terminado", "Terminado"),
    ;

    companion object {
        fun desde(valor: String?): EstadoContrato =
            entries.firstOrNull { it.valor == valor || it.name.equals(valor, true) } ?: VIGENTE
    }
}

// ----------------------------------------------------------------Académico
enum class NivelEducativo(val valor: String, val etiqueta: String) {
    INICIAL("inicial", "Inicial"),
    SECUNDARIA("secundaria", "Secundaria"),
    ;

    companion object {
        fun desde(valor: String?): NivelEducativo =
            entries.firstOrNull { it.valor == valor || it.name.equals(valor, true) } ?: SECUNDARIA
    }
}

enum class EstadoPeriodoAcademico(val valor: String, val etiqueta: String) {
    ABIERTO("abierto", "Abierto"),
    CERRADO("cerrado", "Cerrado"),
    ;

    companion object {
        fun desde(valor: String?): EstadoPeriodoAcademico =
            entries.firstOrNull { it.valor == valor || it.name.equals(valor, true) } ?: ABIERTO
    }
}

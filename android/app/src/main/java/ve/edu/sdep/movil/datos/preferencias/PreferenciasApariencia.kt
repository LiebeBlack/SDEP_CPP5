package ve.edu.sdep.movil.datos.preferencias

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Cómo se elige el tema de la interfaz.
 *
 * Antes el teléfono seguía siempre al sistema: en un equipo configurado en
 * claro no había forma de ver el tema oscuro, aunque la paleta ya estaba
 * definida. El modo elegido se guarda y manda sobre el ajuste del teléfono.
 */
enum class ModoApariencia(val codigo: String, val etiqueta: String) {
    SISTEMA("sistema", "Sistema"),
    CLARO("claro", "Claro"),
    OSCURO("oscuro", "Oscuro"),
    ;

    /** ¿Se pinta oscuro con este modo, dado el estado del sistema? */
    fun esOscuro(sistemaOscuro: Boolean): Boolean = when (this) {
        SISTEMA -> sistemaOscuro
        CLARO -> false
        OSCURO -> true
    }

    companion object {
        /**
         * Valor guardado a modo, tolerando basura de versiones anteriores.
         *
         * Se guarda [codigo] y no el nombre de la constante: R8 puede renombrar
         * los campos del enumerado al ofuscar, y un valor guardado con el
         * nombre se volvería ilegible tras actualizar la aplicación.
         */
        fun desde(valor: String?): ModoApariencia =
            entries.firstOrNull { it.codigo == valor }
                ?: entries.firstOrNull { it.name.equals(valor, ignoreCase = true) }
                ?: SISTEMA
    }
}

/**
 * Preferencia de apariencia del puesto.
 *
 * Vive en las preferencias del teléfono y no en la bóveda cifrada: no es un
 * secreto, no viaja al nodo central y no tiene sentido pagar el coste del
 * Keystore en cada arranque para leerla. El valor se publica en un
 * ``StateFlow`` para que la raíz de la interfaz se recomponga al cambiarlo.
 */
@Singleton
class PreferenciasApariencia @Inject constructor(@ApplicationContext contexto: Context) {

    private val preferencias = contexto.getSharedPreferences(ARCHIVO, Context.MODE_PRIVATE)

    private val _modo = MutableStateFlow(ModoApariencia.desde(preferencias.getString(CLAVE, null)))
    val modo: StateFlow<ModoApariencia> = _modo.asStateFlow()

    fun cambiar(modo: ModoApariencia) {
        if (_modo.value == modo) return
        preferencias.edit().putString(CLAVE, modo.codigo).apply()
        _modo.value = modo
    }

    private companion object {
        const val ARCHIVO = "apariencia"
        const val CLAVE = "modo"
    }
}

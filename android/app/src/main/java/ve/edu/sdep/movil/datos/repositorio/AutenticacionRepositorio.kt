package ve.edu.sdep.movil.datos.repositorio

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import retrofit2.HttpException
import ve.edu.sdep.movil.datos.local.Fechas
import ve.edu.sdep.movil.datos.local.dao.SesionUsuarioDao
import ve.edu.sdep.movil.datos.local.entidad.SesionUsuarioEntity
import ve.edu.sdep.movil.datos.remoto.ApiSyncFactory
import ve.edu.sdep.movil.datos.remoto.CambioPasswordDto
import ve.edu.sdep.movil.datos.remoto.LoginDto
import ve.edu.sdep.movil.datos.remoto.mensajeDelServidor
import ve.edu.sdep.movil.datos.seguridad.Boveda
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Resultado
import ve.edu.sdep.movil.dominio.modelo.Rol
import ve.edu.sdep.movil.dominio.modelo.Sesion
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Ingreso a la aplicación contra el nodo central.
 *
 * Las cuentas viven en la base institucional (las mismas del escritorio): el
 * teléfono no guarda usuarios ni contraseñas. Hay dos caminos y ambos
 * terminan en una [Sesion] en memoria:
 *
 * 1. Usuario y contraseña, validados por `POST /auth/login` del nodo central,
 *    que devuelve un token de sesión.
 * 2. Huella (o credencial del dispositivo), que recupera ese token de la
 *    bóveda cifrada. Si no hay red, la sesión se reabre DENTRO de la ventana
 *    de gracia declarada por el servidor y se revalida en cuanto haya red.
 *
 * El token nunca se guarda en claro fuera de la bóveda (Keystore del equipo)
 * ni se escribe en los registros de la app.
 */
@Singleton
class AutenticacionRepositorio @Inject constructor(
    private val configuracionRepositorio: ConfiguracionRepositorio,
    private val apiFactory: ApiSyncFactory,
    private val boveda: Boveda,
    private val sesionRepositorio: SesionRepositorio,
    private val sincronizacion: SincronizacionRepositorio,
    private val sesionUsuarioDao: SesionUsuarioDao,
    private val json: Json,
) {

    /** Ingreso con usuario y contraseña, comprobados por el nodo central */
    suspend fun entrar(
        usuario: String,
        contrasena: String,
        activarBiometria: Boolean,
    ): Resultado<Sesion> = withContext(Dispatchers.IO) {
        val nombreUsuario = usuario.trim()
        if (nombreUsuario.isEmpty() || contrasena.isEmpty()) {
            return@withContext Resultado.Fallo("Escriba su usuario y su contraseña.")
        }

        val config = configuracionRepositorio.cargar()
        if (!config.completa) {
            return@withContext Resultado.Fallo(
                "Este teléfono todavía no encontró el sistema de escritorio. " +
                    "Compruebe que esté abierto y en la misma Wi-Fi, y reintente.",
            )
        }

        val respuesta = try {
            apiFactory.acciones(config, sesion = null).login(
                LoginDto(username = nombreUsuario, password = contrasena),
            )
        } catch (error: HttpException) {
            // Se muestra el texto que redactó el servidor: es el mismo que ve
            // el usuario en el escritorio (bloqueo, intentos restantes, cuenta
            // desactivada). Cuando no llega un mensaje, se conserva el genérico
            // que no revela qué usuarios existen.
            val mensaje = error.mensajeDelServidor(json)
            return@withContext when (error.code()) {
                401 -> Resultado.Fallo(mensaje ?: "Usuario o contraseña incorrectos.")
                403 -> Resultado.Fallo(
                    mensaje ?: "Esta cuenta no tiene acceso. Consulte al administrador.",
                )

                423 -> Resultado.Fallo(
                    mensaje
                        ?: "La cuenta está bloqueada por intentos fallidos. " +
                        "Consulte al administrador.",
                )

                429 -> Resultado.Fallo(
                    mensaje ?: "Demasiados intentos seguidos. Espere un minuto y reintente.",
                    error,
                )

                else -> Resultado.Fallo(
                    mensaje ?: "El nodo central respondió ${error.code()}. Revise la configuración.",
                    error,
                )
            }
        } catch (error: IOException) {
            return@withContext Resultado.Fallo(
                "Sin conexión con el nodo central. Reintente cuando el teléfono " +
                    "tenga red.",
                error,
                reintentable = true,
            )
        } catch (error: Exception) {
            return@withContext Resultado.Fallo(
                "No se pudo iniciar sesión: ${error.message ?: "error inesperado"}.",
                error,
            )
        }

        if (respuesta.sesionToken.isBlank()) {
            // Un 200 sin token dejaría una sesión «abierta» que no sirve para
            // nada: mejor decirlo ahora que fallar en la primera petición.
            return@withContext Resultado.Fallo(
                "El nodo central aceptó el ingreso pero no entregó una sesión. " +
                    "Actualice el servidor e intente de nuevo.",
            )
        }

        val sesion = Sesion(
            usuario = respuesta.username.ifBlank { nombreUsuario },
            nombre = respuesta.nombreCompleto ?: respuesta.username.ifBlank { nombreUsuario },
            rol = Rol.desde(respuesta.rol),
            cedula = respuesta.cedula,
            token = respuesta.sesionToken,
            expiraEn = Fechas.desdeIso(respuesta.expiraEn)
                ?: System.currentTimeMillis() + respuesta.vidaRelativaHoras * 3_600_000L,
            debeCambiarPassword = respuesta.debeCambiarPassword,
            minLongitudPassword = respuesta.passwordMinLongitud.coerceAtLeast(1),
        )
        // El espejo pertenece a una sola persona. Si entra otra cuenta, se
        // envía lo pendiente de la anterior y se borra antes de descargar lo
        // nuevo; si no se puede enviar, se rechaza el cambio.
        when (val cambio = sincronizacion.prepararCambioDeUsuario(sesion.usuario)) {
            is Resultado.Exito -> Unit
            is Resultado.Fallo -> return@withContext cambio
        }
        guardarCaché(sesion)
        sesionRepositorio.iniciar(sesion)
        if (activarBiometria) activarBiometria(sesion)
        Resultado.Exito(sesion)
    }

    /**
     * Ingreso con el token que desbloquea la bóveda tras la autenticación
     * biométrica.
     *
     * Con red se revalida el token contra el nodo central. Sin red se acepta
     * la sesión guardada mientras esté dentro de su ventana de gracia: los
     * datos se leen y los cambios quedan en cola, y el servidor tendrá la
     * última palabra en la próxima sincronización.
     */
    suspend fun entrarConBiometria(): Resultado<Sesion> = withContext(Dispatchers.IO) {
        val par = boveda.leerCredencialBiometrica()
            ?: return@withContext Resultado.Fallo("No hay una huella habilitada. Entre con su contraseña.")

        val config = configuracionRepositorio.cargar()
        if (!config.completa) {
            return@withContext Resultado.Fallo(
                "Este teléfono todavía no encontró el sistema de escritorio. " +
                    "Entre con su contraseña cuando esté disponible.",
            )
        }

        try {
            val info = apiFactory.acciones(config, sesion = par.token).sesion()
            val sesion = Sesion(
                usuario = info.username.ifBlank { par.usuario },
                nombre = info.nombreCompleto ?: info.username.ifBlank { par.usuario },
                rol = Rol.desde(info.rol),
                cedula = info.cedula,
                token = par.token,
                expiraEn = Fechas.desdeIso(info.expiraEn) ?: 0L,
                debeCambiarPassword = info.debeCambiarPassword,
                minLongitudPassword = info.passwordMinLongitud.coerceAtLeast(1),
            )
            when (val cambio = sincronizacion.prepararCambioDeUsuario(sesion.usuario)) {
                is Resultado.Exito -> Unit
                is Resultado.Fallo -> return@withContext cambio
            }
            boveda.guardarSesionToken(par.token)
            guardarCaché(sesion)
            sesionRepositorio.iniciar(sesion)
            Resultado.Exito(sesion)
        } catch (error: HttpException) {
            boveda.olvidarCredencialBiometrica()
            boveda.olvidarSesionToken()
            sesionUsuarioDao.limpiar()
            Resultado.Fallo(
                "La sesión guardada ya no es válida. Entre con su contraseña.",
                error,
            )
        } catch (error: IOException) {
            // Sin red: ventana de gracia con el caché local de la sesión.
            // La comprobación completa vive en la condición del retorno
            // temprano: así el compilador ve `caché` no nula en el resto de
            // la rama (antes cada acceso requería «?.» y no compilaba).
            val caché = sesionUsuarioDao.obtener()
            if (caché == null || caché.usuario != par.usuario || !vigente(caché.expiraEn)) {
                return@withContext Resultado.Fallo(
                    "Sin conexión y sin sesión vigente en este teléfono. " +
                        "Entre con su contraseña cuando haya red.",
                    error,
                    reintentable = true,
                )
            }
            val sesion = Sesion(
                usuario = caché.usuario,
                nombre = caché.nombreCompleto ?: caché.usuario,
                rol = Rol.desde(caché.rol),
                cedula = caché.cedula,
                token = par.token,
                expiraEn = caché.expiraEn,
                debeCambiarPassword = caché.debeCambiarPassword,
                offline = true,
                // Sin red no se conoce el mínimo vigente; se usa el del
                // escritorio por omisión y el servidor validará al guardar.
                minLongitudPassword = 6,
            )
            sesionRepositorio.iniciar(sesion)
            Resultado.Exito(sesion)
        } catch (error: Exception) {
            Resultado.Fallo(
                "No se pudo abrir la sesión: ${error.message ?: "error inesperado"}.",
                error,
            )
        }
    }

    /**
     * Habilita el desbloqueo biométrico para la sesión vigente.
     *
     * La llave guardada es el propio token de sesión (cifrado con el Keystore
     * del equipo): si se pierde el teléfono, sin el sensor y sin el PIN del
     * dispositivo esa llave no sirve para nada.
     */
    suspend fun activarBiometria(sesion: Sesion): Boolean = withContext(Dispatchers.Default) {
        if (sesion.token.isBlank()) return@withContext false
        boveda.guardarCredencialBiometrica(sesion.usuario, sesion.token)
    }

    /** Deja de ofrecer el desbloqueo biométrico */
    suspend fun olvidarBiometria(): Unit = withContext(Dispatchers.Default) {
        boveda.olvidarCredencialBiometrica()
    }

    fun hayCredencialBiometrica(): Boolean = boveda.leerCredencialBiometrica() != null

    /**
     * Cambia la contraseña de la cuenta en la base institucional.
     *
     * La autoridad es el nodo central: aquí no se guarda ningún hash de
     * contraseña, solo se pide el cambio con la sesión abierta.
     */
    suspend fun cambiarPassword(actual: String, nueva: String): Resultado<Unit> =
        withContext(Dispatchers.IO) {
            val sesion = sesionRepositorio.actual
                ?: return@withContext Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")
            val errorValidacion = validarPassword(nueva, sesion.minLongitudPassword)
            if (errorValidacion != null) return@withContext Resultado.Fallo(errorValidacion)
            if (actual.isEmpty()) return@withContext Resultado.Fallo("Escriba su contraseña actual.")

            val config = configuracionRepositorio.cargar()
            if (!config.completa) {
                return@withContext Resultado.Fallo(
                    "Sin vinculación con el sistema de escritorio. Busque el equipo de nuevo.",
                )
            }

            try {
                apiFactory.acciones(config, sesion.token)
                    .cambiarPassword(CambioPasswordDto(actual = actual, nueva = nueva))
                if (sesion.debeCambiarPassword) {
                    val actualizada = sesion.copy(debeCambiarPassword = false)
                    sesionRepositorio.iniciar(actualizada)
                    guardarCaché(actualizada)
                }
                Resultado.Exito(Unit)
            } catch (error: HttpException) {
                val mensaje = error.mensajeDelServidor(json)
                Resultado.Fallo(
                    mensaje ?: when (error.code()) {
                        400 -> "La nueva contraseña no cumple la política del sistema."
                        401, 403 -> "La contraseña actual no coincide o la sesión caducó."
                        else -> "El nodo central rechazó el cambio (${error.code()})."
                    },
                    error,
                )
            } catch (error: IOException) {
                Resultado.Fallo(
                    "Sin conexión con el nodo central. El cambio se aplicará cuando haya red.",
                    error,
                    reintentable = true,
                )
            } catch (error: Exception) {
                Resultado.Fallo(
                    "No se pudo cambiar la contraseña: ${error.message ?: "error inesperado"}.",
                    error,
                )
            }
        }

    /** Obtiene el perfil del usuario autenticado desde el nodo central */
    suspend fun obtenerPerfil(): Resultado<PerfilDto> = withContext(Dispatchers.IO) {
        val sesion = sesionRepositorio.actual
            ?: return@withContext Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")
        val config = configuracionRepositorio.cargar()
        if (!config.completa) {
            return@withContext Resultado.Fallo(
                "Sin vinculación con el sistema de escritorio. Busque el equipo de nuevo.",
            )
        }
        try {
            val perfil = apiFactory.acciones(config, sesion.token).perfil()
            Resultado.Exito(perfil)
        } catch (error: Exception) {
            Resultado.Fallo(
                "No se pudo cargar el perfil: ${error.message ?: "error inesperado"}.",
                error,
            )
        }
    }

    /** Actualiza el perfil propio (nombre y cédula) en el nodo central */
    suspend fun actualizarPerfil(dto: ActualizarPerfilDto): Resultado<PerfilDto> =
        withContext(Dispatchers.IO) {
            val sesion = sesionRepositorio.actual
                ?: return@withContext Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")
            val config = configuracionRepositorio.cargar()
            if (!config.completa) {
                return@withContext Resultado.Fallo(
                    "Sin vinculación con el sistema de escritorio. Busque el equipo de nuevo.",
                )
            }
            try {
                val perfil = apiFactory.acciones(config, sesion.token).actualizarPerfil(dto)
                Resultado.Exito(perfil)
            } catch (error: Exception) {
                Resultado.Fallo(
                    "No se pudo actualizar el perfil: ${error.message ?: "error inesperado"}.",
                    error,
                )
            }
        }

    /** Cierra la sesión local y revoca el token en el nodo central */
    suspend fun cerrarSesion() {
        val sesion = sesionRepositorio.actual
        val config = configuracionRepositorio.actual()
        if (sesion != null && sesion.token.isNotBlank() && config.completa) {
            // Mejor esfuerzo: si no hay red, el token caduca por su ventana
            runCatching { apiFactory.acciones(config, sesion.token).logout() }
        }
        boveda.olvidarSesionToken()
        boveda.olvidarCredencialBiometrica()
        sesionUsuarioDao.limpiar()
        sesionRepositorio.cerrar()
    }

    // ------------------------------------------------------------------
    // Interno
    // ------------------------------------------------------------------

    /** Guarda el caché de sesión que permite el reabrir sin red */
    private suspend fun guardarCaché(sesion: Sesion) {
        sesionUsuarioDao.guardar(
            SesionUsuarioEntity(
                id = 1,
                usuario = sesion.usuario,
                nombreCompleto = sesion.nombre,
                rol = sesion.rol.valor,
                cedula = sesion.cedula,
                expiraEn = sesion.expiraEn,
                debeCambiarPassword = sesion.debeCambiarPassword,
                actualizadoEn = System.currentTimeMillis(),
            ),
        )
        if (sesion.token.isNotBlank()) boveda.guardarSesionToken(sesion.token)
    }

    private fun vigente(expiraEn: Long): Boolean = expiraEn <= 0L || System.currentTimeMillis() <= expiraEn

    /**
     * Comprueba la contraseña con la política del servidor, no con una copia.
     *
     * Antes el teléfono exigía 8 caracteres y letras + números. La política del
     * escritorio es configurable (6 por omisión) y no exige esa combinación, así
     * que la app rechazaba contraseñas que el nodo central sí aceptaba. El
     * mínimo llega en la respuesta del login; el servidor sigue siendo la
     * autoridad final.
     */
    private fun validarPassword(nueva: String, minimo: Int): String? {
        val requerido = minimo.coerceAtLeast(1)
        if (nueva.length < requerido) {
            return "La contraseña debe tener al menos $requerido caracteres."
        }
        return null
    }
}

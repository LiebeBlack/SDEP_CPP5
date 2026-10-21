package ve.edu.sdep.movil.datos.repositorio

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.HttpException
import ve.edu.sdep.movil.datos.local.Fechas
import ve.edu.sdep.movil.datos.local.dao.SesionUsuarioDao
import ve.edu.sdep.movil.datos.local.entidad.SesionUsuarioEntity
import ve.edu.sdep.movil.datos.remoto.ApiSyncFactory
import ve.edu.sdep.movil.datos.remoto.CambioPasswordDto
import ve.edu.sdep.movil.datos.remoto.LoginDto
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
    private val sesionUsuarioDao: SesionUsuarioDao,
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
                "Este teléfono todavía no está vinculado al nodo central. " +
                    "Complete la dirección, el equipo y el token antes de entrar.",
            )
        }

        val respuesta = try {
            apiFactory.acciones(config, sesion = null).login(
                LoginDto(username = nombreUsuario, password = contrasena),
            )
        } catch (error: HttpException) {
            // El mismo mensaje para «no existe» y «contraseña incorrecta»: no se
            // revela qué usuarios tiene la institución.
            return@withContext when (error.code()) {
                401, 403 -> Resultado.Fallo("Usuario o contraseña incorrectos.")
                423 -> Resultado.Fallo(
                    "La cuenta está bloqueada por intentos fallidos. Consulte al administrador.",
                )

                else -> Resultado.Fallo(
                    "El nodo central respondió ${error.code()}. Revise la configuración.",
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

        val sesion = Sesion(
            usuario = respuesta.username.ifBlank { nombreUsuario },
            nombre = respuesta.nombreCompleto ?: respuesta.username.ifBlank { nombreUsuario },
            rol = Rol.desde(respuesta.rol),
            token = respuesta.sesionToken,
            expiraEn = Fechas.desdeIso(respuesta.expiraEn)
                ?: System.currentTimeMillis() + respuesta.vidaRelativaHoras * 3_600_000L,
            debeCambiarPassword = respuesta.debeCambiarPassword,
        )
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
                "Este teléfono todavía no está vinculado al nodo central.",
            )
        }

        try {
            val info = apiFactory.acciones(config, sesion = par.token).sesion()
            val sesion = Sesion(
                usuario = info.username.ifBlank { par.usuario },
                nombre = info.nombreCompleto ?: info.username.ifBlank { par.usuario },
                rol = Rol.desde(info.rol),
                token = par.token,
                expiraEn = Fechas.desdeIso(info.expiraEn) ?: 0L,
                debeCambiarPassword = info.debeCambiarPassword,
            )
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
            // Sin red: ventana de gracia con el caché local de la sesión
            val caché = sesionUsuarioDao.obtener()
            val coincide = caché != null && caché.usuario == par.usuario
            if (!coincide || !vigente(caché.expiraEn)) {
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
                token = par.token,
                expiraEn = caché.expiraEn,
                debeCambiarPassword = caché.debeCambiarPassword,
                offline = true,
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
            val errorValidacion = validarPassword(nueva)
            if (errorValidacion != null) return@withContext Resultado.Fallo(errorValidacion)
            if (actual.isEmpty()) return@withContext Resultado.Fallo("Escriba su contraseña actual.")

            val config = configuracionRepositorio.cargar()
            if (!config.completa) {
                return@withContext Resultado.Fallo("No hay conexión configurada con el nodo central.")
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
                Resultado.Fallo(
                    when (error.code()) {
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
                expiraEn = sesion.expiraEn,
                debeCambiarPassword = sesion.debeCambiarPassword,
                actualizadoEn = System.currentTimeMillis(),
            ),
        )
        if (sesion.token.isNotBlank()) boveda.guardarSesionToken(sesion.token)
    }

    private fun vigente(expiraEn: Long): Boolean = expiraEn <= 0L || System.currentTimeMillis() <= expiraEn

    private fun validarPassword(nueva: String): String? {
        if (nueva.length < 8) return "La contraseña debe tener al menos 8 caracteres."
        if (nueva.none { it.isDigit() } || nueva.none { it.isLetter() }) {
            return "La contraseña debe combinar letras y números."
        }
        return null
    }
}

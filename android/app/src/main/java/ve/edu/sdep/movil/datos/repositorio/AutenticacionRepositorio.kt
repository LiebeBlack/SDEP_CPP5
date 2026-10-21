package ve.edu.sdep.movil.datos.repositorio

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import ve.edu.sdep.movil.datos.local.dao.UsuarioDao
import ve.edu.sdep.movil.datos.local.entidad.UsuarioEntity
import ve.edu.sdep.movil.datos.seguridad.Boveda
import ve.edu.sdep.movil.datos.seguridad.HashContrasena
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Resultado
import ve.edu.sdep.movil.dominio.modelo.Rol
import ve.edu.sdep.movil.dominio.modelo.Sesion
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Ingreso a la aplicación.
 *
 * Hay dos caminos y ambos terminan en una ``Sesion`` en memoria:
 *
 * 1. Usuario y contraseña, comprobados contra la derivación PBKDF2 guardada.
 * 2. Huella (o rostro, o credencial del dispositivo), que solo desbloquea un
 *    token aleatorio guardado en la bóveda cifrada. Ese token no es la
 *    contraseña: si el teléfono se pierde y alguien copia la base, no puede
 *    entrar sin el Keystore del equipo y sin el sensor.
 *
 * Las cuentas son locales del teléfono, como en cada puesto del sistema de
 * escritorio. El primer arranque crea el administrador.
 */
@Singleton
class AutenticacionRepositorio @Inject constructor(
    private val usuariosDao: UsuarioDao,
    private val hashContrasena: HashContrasena,
    private val boveda: Boveda,
    private val sesionRepositorio: SesionRepositorio,
) {

    suspend fun hayUsuarios(): Boolean = usuariosDao.contar() > 0

    fun observarUsuarios(): Flow<List<UsuarioEntity>> = usuariosDao.observarTodas()

    /**
     * Crea la cuenta de administrador del primer arranque.
     *
     * No se puede llamar si ya existe alguna cuenta: evita que alguien con
     * acceso físico al teléfono agregue un administrador paralelo.
     */
    suspend fun crearPrimerAdministrador(
        nombre: String,
        usuario: String,
        contrasena: String,
        confirmacion: String,
    ): Resultado<Sesion> = withContext(Dispatchers.Default) {
        if (usuariosDao.contar() > 0) {
            return@withContext Resultado.Fallo(
                "Ya existe una cuenta en este teléfono. Entre con ella para crear más usuarios.",
            )
        }
        val error = validar(nombre, usuario, contrasena, confirmacion)
        if (error != null) return@withContext Resultado.Fallo(error)

        val entidad = UsuarioEntity(
            nombre = nombre.trim(),
            usuario = usuario.trim().lowercase(),
            hashContrasena = hashContrasena.crear(contrasena.toCharArray()),
            rol = Rol.ADMIN.name,
            activo = true,
            tokenBiometricoHash = null,
            creadoEn = System.currentTimeMillis(),
        )
        val id = usuariosDao.insertar(entidad)
        val sesion = Sesion(id, entidad.nombre, entidad.usuario, Rol.ADMIN)
        sesionRepositorio.iniciar(sesion)
        Resultado.Exito(sesion)
    }

    /**
     * Agrega una cuenta. Solo un administrador puede hacerlo.
     */
    suspend fun crearUsuario(
        autor: Sesion,
        nombre: String,
        usuario: String,
        contrasena: String,
        confirmacion: String,
        rol: Rol,
    ): Resultado<Unit> = withContext(Dispatchers.Default) {
        if (!autor.puede(Permiso.ADMINISTRAR_USUARIOS)) {
            return@withContext Resultado.Fallo("Solo un administrador puede crear cuentas.")
        }
        val error = validar(nombre, usuario, contrasena, confirmacion)
        if (error != null) return@withContext Resultado.Fallo(error)

        val nombreUsuario = usuario.trim().lowercase()
        if (usuariosDao.buscarPorUsuario(nombreUsuario) != null) {
            return@withContext Resultado.Fallo("Ya existe una cuenta con el usuario «$nombreUsuario».")
        }

        usuariosDao.insertar(
            UsuarioEntity(
                nombre = nombre.trim(),
                usuario = nombreUsuario,
                hashContrasena = hashContrasena.crear(contrasena.toCharArray()),
                rol = rol.name,
                activo = true,
                tokenBiometricoHash = null,
                creadoEn = System.currentTimeMillis(),
            ),
        )
        Resultado.Exito(Unit)
    }

    /** Ingreso con usuario y contraseña */
    suspend fun entrar(
        usuario: String,
        contrasena: String,
        activarBiometria: Boolean,
    ): Resultado<Sesion> = withContext(Dispatchers.Default) {
        val nombreUsuario = usuario.trim().lowercase()
        if (nombreUsuario.isEmpty() || contrasena.isEmpty()) {
            return@withContext Resultado.Fallo("Escriba su usuario y su contraseña.")
        }

        val entidad = usuariosDao.buscarPorUsuario(nombreUsuario)
        // El mismo mensaje para «no existe» y «contraseña incorrecta»: no se
        // revela qué usuarios tiene el teléfono.
        val mensajeGenerico = "Usuario o contraseña incorrectos."
        if (entidad == null) return@withContext Resultado.Fallo(mensajeGenerico)
        if (!entidad.activo) {
            return@withContext Resultado.Fallo("La cuenta está desactivada. Consulte al administrador.")
        }
        if (!hashContrasena.verificar(contrasena.toCharArray(), entidad.hashContrasena)) {
            return@withContext Resultado.Fallo(mensajeGenerico)
        }

        val sesion = Sesion(entidad.id, entidad.nombre, entidad.usuario, Rol.desde(entidad.rol))
        sesionRepositorio.iniciar(sesion)
        if (activarBiometria) activarBiometria(sesion)
        Resultado.Exito(sesion)
    }

    /**
     * Ingreso con el token que desbloquea la bóveda tras la autenticación
     * biométrica. Si el token no corresponde a ninguna cuenta (por ejemplo,
     * porque se desactivó la huella en otra sesión), se pide la contraseña.
     */
    suspend fun entrarConBiometria(): Resultado<Sesion> = withContext(Dispatchers.Default) {
        val par = boveda.leerCredencialBiometrica()
            ?: return@withContext Resultado.Fallo("No hay una huella habilitada. Entre con su contraseña.")

        val entidad = usuariosDao.buscarPorTokenBiometrico(hashContrasena.hashRapido(par.token))
            ?: return@withContext Resultado.Fallo(
                "El desbloqueo con huella ya no es válido. Entre con su contraseña.",
            )
        if (!entidad.activo) {
            return@withContext Resultado.Fallo("La cuenta está desactivada. Consulte al administrador.")
        }

        val sesion = Sesion(entidad.id, entidad.nombre, entidad.usuario, Rol.desde(entidad.rol))
        sesionRepositorio.iniciar(sesion)
        Resultado.Exito(sesion)
    }

    /** Habilita el desbloqueo biométrico para la cuenta de la sesión */
    suspend fun activarBiometria(sesion: Sesion): Boolean = withContext(Dispatchers.Default) {
        val token = UUID.randomUUID().toString() + UUID.randomUUID().toString()
        usuariosDao.asignarTokenBiometrico(sesion.usuarioId, hashContrasena.hashRapido(token))
        boveda.guardarCredencialBiometrica(sesion.usuario, token)
    }

    /** Deja de ofrecer el desbloqueo biométrico */
    suspend fun olvidarBiometria(usuarioId: Long) = withContext(Dispatchers.Default) {
        usuariosDao.asignarTokenBiometrico(usuarioId, null)
        boveda.olvidarCredencialBiometrica()
    }

    fun hayCredencialBiometrica(): Boolean = boveda.leerCredencialBiometrica() != null

    fun cerrarSesion() {
        sesionRepositorio.cerrar()
    }

    // ------------------------------------------------------------------
    // Validaciones compartidas
    // ------------------------------------------------------------------
    private fun validar(
        nombre: String,
        usuario: String,
        contrasena: String,
        confirmacion: String,
    ): String? {
        if (nombre.trim().length < 3) return "El nombre debe tener al menos 3 caracteres."
        if (!usuario.trim().matches(Regex("[A-Za-z0-9._-]{3,30}"))) {
            return "El usuario debe tener entre 3 y 30 caracteres: letras, números, punto, guion o guion bajo."
        }
        if (contrasena.length < 8) return "La contraseña debe tener al menos 8 caracteres."
        if (contrasena.none { it.isDigit() } || contrasena.none { it.isLetter() }) {
            return "La contraseña debe combinar letras y números."
        }
        if (contrasena != confirmacion) return "Las contraseñas no coinciden."
        return null
    }
}

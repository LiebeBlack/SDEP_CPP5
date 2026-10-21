package ve.edu.sdep.movil.datos.remoto

import kotlinx.serialization.json.JsonElement
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query
import retrofit2.http.QueryMap

/**
 * Cliente del protocolo 2 del nodo central: autenticación de usuario,
 * consultas, administración de cuentas, acciones de negocio y archivos.
 *
 * Dos cabeceras viajan en cada petición (las añade la fábrica, nunca cada
 * llamada): `Authorization: Bearer <token del equipo>` + `X-Dispositivo`,
 * las del puesto, y `X-Sesion`, el token de usuario que emite el login.
 * El servidor exige ambas: sin equipo emparejado no hay canal, y sin sesión
 * no hay permisos.
 *
 * Las respuestas de las acciones de negocio se devuelven como [JsonElement]:
 * son bolsas heterogéneas (un resultado con totales, otro con un contrato)
 * y quien las consume ya sabe qué forma espera — el mapeo vive en un solo
 * sitio, en su repositorio.
 */
interface ApiAcciones {

    // ------------------------------------------------------------------
    // Autenticación (solo pide la URL del nodo central)
    // ------------------------------------------------------------------
    @POST("api/v1/auth/login")
    suspend fun login(@Body cuerpo: LoginDto): SesionRespuestaDto

    @POST("api/v1/auth/logout")
    suspend fun logout(): CorrectoDto

    @GET("api/v1/auth/sesion")
    suspend fun sesion(): SesionInfoDto

    @POST("api/v1/auth/cambiar-password")
    suspend fun cambiarPassword(@Body cuerpo: CambioPasswordDto): CorrectoDto

    // ------------------------------------------------------------------
    // Consultas
    // ------------------------------------------------------------------
    @GET("api/v1/consultas/dashboard")
    suspend fun dashboard(): DashboardDto

    @GET("api/v1/consultas/auditoria")
    suspend fun auditoria(@Query("limite") limite: Int = 100): AuditoriaDto

    @GET("api/v1/consultas/docentes")
    suspend fun docentes(): List<DocenteDto>

    // ------------------------------------------------------------------
    // Administración de usuarios (solo admin)
    // ------------------------------------------------------------------
    @GET("api/v1/admin/usuarios")
    suspend fun listarUsuarios(): ListarUsuariosDto

    @POST("api/v1/admin/usuarios")
    suspend fun crearUsuario(@Body cuerpo: JsonElement): UsuarioRespuestaDto

    @PUT("api/v1/admin/usuarios/{id}")
    suspend fun actualizarUsuario(@Path("id") id: Long, @Body cuerpo: JsonElement): UsuarioRespuestaDto

    @POST("api/v1/admin/usuarios/{id}/desbloquear")
    suspend fun desbloquearUsuario(@Path("id") id: Long): CorrectoDto

    // ------------------------------------------------------------------
    // Nómina
    // ------------------------------------------------------------------
    @POST("api/v1/acciones/nomina/generar")
    suspend fun generarNomina(@Body cuerpo: JsonElement): JsonElement

    @POST("api/v1/acciones/nomina/resumen")
    suspend fun resumenNomina(@Body cuerpo: JsonElement): JsonElement

    @POST("api/v1/acciones/nomina/{id}/pagado")
    suspend fun marcarPagado(@Path("id") id: Long): CorrectoDto

    // ------------------------------------------------------------------
    // Incidencias
    // ------------------------------------------------------------------
    @POST("api/v1/acciones/incidencias/{id}/aprobar")
    suspend fun aprobarIncidencia(@Path("id") id: Long, @Body cuerpo: JsonElement): CorrectoDto

    @POST("api/v1/acciones/incidencias/{id}/rechazar")
    suspend fun rechazarIncidencia(@Path("id") id: Long, @Body cuerpo: JsonElement): CorrectoDto

    // ------------------------------------------------------------------
    // Contratos
    // ------------------------------------------------------------------
    @POST("api/v1/acciones/contratos/{id}/renovar")
    suspend fun renovarContrato(@Path("id") id: Long, @Body cuerpo: JsonElement): JsonElement

    @POST("api/v1/acciones/contratos/{id}/terminar")
    suspend fun terminarContrato(@Path("id") id: Long, @Body cuerpo: JsonElement): JsonElement

    // ------------------------------------------------------------------
    // Académico
    // ------------------------------------------------------------------
    @POST("api/v1/acciones/academicos/periodo/{id}/cerrar")
    suspend fun cerrarPeriodo(@Path("id") id: Long, @Body cuerpo: JsonElement): JsonElement

    @POST("api/v1/acciones/academicos/periodo/{id}/reabrir")
    suspend fun reabrirPeriodo(@Path("id") id: Long, @Body cuerpo: JsonElement): JsonElement

    @POST("api/v1/acciones/academicos/notas/lote")
    suspend fun cargarNotasLote(@Body cuerpo: JsonElement): JsonElement

    @GET("api/v1/acciones/academicos/notas/grado/{id}")
    suspend fun notasDeGrado(@Path("id") gradoId: Long): JsonElement

    @POST("api/v1/acciones/academicos/notas/boletin")
    suspend fun boletin(@Body cuerpo: JsonElement): JsonElement

    @POST("api/v1/acciones/academicos/notas/acta")
    suspend fun acta(@Body cuerpo: JsonElement): JsonElement

    @POST("api/v1/acciones/academicos/notas/consolidado")
    suspend fun consolidado(@Body cuerpo: JsonElement): JsonElement

    @POST("api/v1/acciones/academicos/token/emitir")
    suspend fun emitirTokenAcademico(): JsonElement

    @POST("api/v1/acciones/academicos/token/revocar")
    suspend fun revocarTokenAcademico(@Body cuerpo: JsonElement): CorrectoDto

    // ------------------------------------------------------------------
    // Archivos (PDF y Excel generados en el servidor)
    // ------------------------------------------------------------------
    @POST("api/v1/archivos/pdf/{tipo}")
    suspend fun generarPdf(@Path("tipo") tipo: String, @Body cuerpo: JsonElement): ArchivoDto

    @POST("api/v1/archivos/excel/{tipo}")
    suspend fun generarExcel(@Path("tipo") tipo: String, @Body cuerpo: JsonElement): ArchivoDto

    @POST("api/v1/archivos/subir")
    suspend fun subirArchivo(
        @Query("nombre") nombre: String,
        @Body cuerpo: ByteArray,
    ): ArchivoDto

    /** Descarga de un archivo por su hash (mismo endpoint de binarios v1) */
    @retrofit2.http.GET("api/v1/blob/{hash}")
    suspend fun descargar(@Path("hash") hash: String): ByteArray

    /** Compatibilidad con lecturas que llegan como pares clave-valor */
    @GET("api/v1/ping")
    suspend fun ping(@QueryMap parametros: Map<String, String> = emptyMap()): PingDto
}

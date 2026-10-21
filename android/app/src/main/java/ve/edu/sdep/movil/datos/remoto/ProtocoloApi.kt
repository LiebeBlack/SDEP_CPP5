package ve.edu.sdep.movil.datos.remoto

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Query

/**
 * Servicio HTTP del nodo central de sincronización.
 *
 * Son los mismos tres puntos que usa el agente del escritorio, con las mismas
 * cabeceras: ``Authorization: Bearer <token>`` y ``X-Dispositivo: <equipo>``.
 * La app no inventa un canal paralelo: se presenta como un puesto más, y el
 * administrador la da de alta con el comando que ya conoce.
 */
interface ProtocoloApi {

    /** Comprueba que el servicio responde y devuelve su versión y su hora */
    @GET("api/v1/ping")
    suspend fun ping(): PingDto

    /** Envía un lote de operaciones locales */
    @POST("api/v1/push")
    suspend fun enviar(@Body cuerpo: PushDto): PushRespuestaDto

    /** Descarga las operaciones posteriores al cursor indicado */
    @GET("api/v1/pull")
    suspend fun recibir(
        @Query("cursor") cursor: Int,
        @Query("limite") limite: Int,
    ): PullRespuestaDto
}

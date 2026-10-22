package ve.edu.sdep.movil.ui.navegacion

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import ve.edu.sdep.movil.datos.local.EsquemaTabla
import ve.edu.sdep.movil.dominio.modelo.Modulo
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Sesion
import ve.edu.sdep.movil.ui.ajustes.PantallaAjustes
import ve.edu.sdep.movil.ui.conflictos.PantallaConflictos
import ve.edu.sdep.movil.ui.empleados.PantallaEmpleado
import ve.edu.sdep.movil.ui.formulario.PantallaFormulario
import ve.edu.sdep.movil.ui.inicio.PantallaInicio
import ve.edu.sdep.movil.ui.login.PantallaLogin
import ve.edu.sdep.movil.ui.modulos.PantallaFichaModulo
import ve.edu.sdep.movil.ui.modulos.PantallaListaModulo
import ve.edu.sdep.movil.ui.modulos.PantallaModulos
import ve.edu.sdep.movil.ui.registros.PantallaEditor
import ve.edu.sdep.movil.ui.registros.PantallaRegistros
import ve.edu.sdep.movil.ui.sesion.SesionViewModel
import ve.edu.sdep.movil.ui.tablas.PantallaTabla

/**
 * Navegación raíz.
 *
 * El ingreso no es una pantalla del grafo: es una puerta. Mientras no haya
 * sesión se muestra el formulario de entrada; en cuanto la hay, se monta el
 * grafo interno. Así no se puede «volver atrás» a una pantalla autenticada
 * después de cerrar sesión, ni quedar en una ruta protegida sin sesión.
 *
 * La portada es [PantallaInicio] (soluciones por categoría). Las listas de
 * módulo siguen existiendo para los módulos con presentación propia, y las
 * tablas académicas sin pantalla dedicada usan [PantallaTabla]. Toda escritura
 * pasa por [PantallaFormulario], que genera los campos del esquema real.
 */
@Composable
fun NavegacionPrincipal(vistaModelo: SesionViewModel = hiltViewModel()) {
    val sesion by vistaModelo.sesion.collectAsStateWithLifecycle()

    val actual = sesion
    if (actual == null) {
        PantallaLogin()
    } else {
        NavegacionInterna(sesion = actual, alSalir = vistaModelo::salir)
    }
}

@Composable
private fun NavegacionInterna(sesion: Sesion, alSalir: () -> Unit) {
    val navegador = rememberNavController()

    NavHost(navegador, startDestination = Rutas.INICIO) {
        composable(Rutas.INICIO) {
            PantallaInicio(
                sesion = sesion,
                alAbrirModulo = { modulo -> navegador.navigate("${Rutas.LISTA}/${modulo.ruta}") },
                alAbrirTabla = { tabla -> navegador.navigate("${Rutas.TABLA}/$tabla") },
                alCaptura = { navegador.navigate(Rutas.REGISTROS) },
                alAjustes = { navegador.navigate(Rutas.AJUSTES) },
                alConflictos = { navegador.navigate(Rutas.CONFLICTOS) },
                alTodosLosModulos = { navegador.navigate(Rutas.MODULOS) },
            )
        }

        composable(Rutas.MODULOS) {
            PantallaModulos(
                sesion = sesion,
                alVolver = { navegador.popBackStack() },
                alAbrir = { modulo -> navegador.navigate("${Rutas.LISTA}/${modulo.ruta}") },
            )
        }

        composable(Rutas.REGISTROS) {
            PantallaRegistros(
                sesion = sesion,
                alNuevo = { navegador.navigate(Rutas.EDITOR) },
                alEditar = { uuid -> navegador.navigate("${Rutas.EDITOR}?uuid=$uuid") },
                alModulos = { navegador.navigate(Rutas.MODULOS) },
                alAjustes = { navegador.navigate(Rutas.AJUSTES) },
            )
        }

        composable(
            route = "${Rutas.LISTA}/{modulo}",
            arguments = listOf(navArgument("modulo") { type = NavType.StringType }),
        ) { entrada ->
            val ruta = entrada.arguments?.getString("modulo").orEmpty()
            val modulo = Modulo.desde(ruta)
            val tabla = modulo?.let { EsquemaTabla.tablaDeModulo(it) }
            PantallaListaModulo(
                sesion = sesion,
                rutaModulo = ruta,
                alVolver = { navegador.popBackStack() },
                alAbrir = { _, id ->
                    navegador.navigate("${Rutas.FICHA}/$ruta/$id")
                },
                alCrear = when {
                    tabla == null || !sesion.puede(Permiso.CREAR) -> null
                    tabla == "empleados" -> {
                        { navegador.navigate("${Rutas.EMPLEADO}/0") }
                    }

                    else -> {
                        { navegador.navigate("${Rutas.FORMULARIO}/$tabla") }
                    }
                },
            )
        }

        composable(
            route = "${Rutas.FICHA}/{modulo}/{id}",
            arguments = listOf(
                navArgument("modulo") { type = NavType.StringType },
                navArgument("id") { type = NavType.LongType },
            ),
        ) { entrada ->
            val ruta = entrada.arguments?.getString("modulo").orEmpty()
            val idFila = entrada.arguments?.getLong("id") ?: 0L
            val tabla = Modulo.desde(ruta)?.let { EsquemaTabla.tablaDeModulo(it) }
            PantallaFichaModulo(
                sesion = sesion,
                rutaModulo = ruta,
                id = idFila,
                alVolver = { navegador.popBackStack() },
                alEditar = when {
                    tabla == null || !sesion.puede(Permiso.EDITAR) -> null
                    tabla == "empleados" -> {
                        { navegador.navigate("${Rutas.EMPLEADO}/$idFila") }
                    }

                    else -> {
                        { navegador.navigate("${Rutas.FORMULARIO}/$tabla?id=$idFila") }
                    }
                },
            )
        }

        composable(
            route = "${Rutas.TABLA}/{tabla}",
            arguments = listOf(navArgument("tabla") { type = NavType.StringType }),
        ) { entrada ->
            val tabla = entrada.arguments?.getString("tabla").orEmpty()
            PantallaTabla(
                tabla = tabla,
                alVolver = { navegador.popBackStack() },
                alCrear = { navegador.navigate("${Rutas.FORMULARIO}/$tabla") },
                alEditar = { id -> navegador.navigate("${Rutas.FORMULARIO}/$tabla?id=$id") },
            )
        }

        composable(
            route = "${Rutas.FORMULARIO}/{tabla}?id={id}",
            arguments = listOf(
                navArgument("tabla") { type = NavType.StringType },
                navArgument("id") {
                    type = NavType.LongType
                    defaultValue = 0L
                },
            ),
        ) { entrada ->
            val tabla = entrada.arguments?.getString("tabla").orEmpty()
            val idFila = entrada.arguments?.getLong("id")?.takeIf { it > 0L }
            PantallaFormulario(
                tabla = tabla,
                id = idFila,
                alVolver = { navegador.popBackStack() },
            )
        }

        composable(
            route = "${Rutas.EMPLEADO}/{id}",
            arguments = listOf(
                navArgument("id") {
                    type = NavType.LongType
                    defaultValue = 0L
                },
            ),
        ) {
            PantallaEmpleado(sesion = sesion, alVolver = { navegador.popBackStack() })
        }

        composable(
            route = "${Rutas.EDITOR}?uuid={uuid}",
            arguments = listOf(
                navArgument("uuid") {
                    type = NavType.StringType
                    defaultValue = ""
                },
            ),
        ) {
            PantallaEditor(alVolver = { navegador.popBackStack() })
        }

        composable(Rutas.AJUSTES) {
            PantallaAjustes(
                sesion = sesion,
                alVolver = { navegador.popBackStack() },
                alCerrarSesion = alSalir,
                alVerConflictos = { navegador.navigate(Rutas.CONFLICTOS) },
            )
        }

        composable(Rutas.CONFLICTOS) {
            PantallaConflictos(alVolver = { navegador.popBackStack() })
        }
    }
}

/** Rutas del grafo interno; los módulos usan su propia ruta como argumento */
private object Rutas {
    const val INICIO = "inicio"
    const val REGISTROS = "registros"
    const val EDITOR = "editor"
    const val AJUSTES = "ajustes"
    const val CONFLICTOS = "conflictos"
    const val MODULOS = "modulos"
    const val LISTA = "modulo"
    const val FICHA = "ficha"
    const val TABLA = "tabla"
    const val FORMULARIO = "formulario"
    const val EMPLEADO = "empleado"
}

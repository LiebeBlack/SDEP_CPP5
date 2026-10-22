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
import ve.edu.sdep.movil.dominio.modelo.Sesion
import ve.edu.sdep.movil.ui.ajustes.PantallaAjustes
import ve.edu.sdep.movil.ui.conflictos.PantallaConflictos
import ve.edu.sdep.movil.ui.login.PantallaLogin
import ve.edu.sdep.movil.ui.modulos.PantallaFichaModulo
import ve.edu.sdep.movil.ui.modulos.PantallaListaModulo
import ve.edu.sdep.movil.ui.modulos.PantallaModulos
import ve.edu.sdep.movil.ui.registros.PantallaEditor
import ve.edu.sdep.movil.ui.registros.PantallaRegistros
import ve.edu.sdep.movil.ui.sesion.SesionViewModel

/**
 * Navegación raíz.
 *
 * El ingreso no es una pantalla del grafo: es una puerta. Mientras no haya
 * sesión se muestra el formulario de entrada; en cuanto la hay, se monta el
 * grafo interno. Así no se puede «volver atrás» a una pantalla autenticada
 * después de cerrar sesión, ni quedar en una ruta protegida sin sesión.
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

    NavHost(navegador, startDestination = Rutas.REGISTROS) {
        composable(Rutas.REGISTROS) {
            PantallaRegistros(
                sesion = sesion,
                alNuevo = { navegador.navigate(Rutas.EDITOR) },
                alEditar = { uuid -> navegador.navigate("${Rutas.EDITOR}?uuid=$uuid") },
                alModulos = { navegador.navigate(Rutas.MODULOS) },
                alAjustes = { navegador.navigate(Rutas.AJUSTES) },
            )
        }

        composable(Rutas.MODULOS) {
            PantallaModulos(
                sesion = sesion,
                alVolver = { navegador.popBackStack() },
                alAbrir = { modulo -> navegador.navigate("${Rutas.LISTA}/${modulo.ruta}") },
            )
        }

        composable(
            route = "${Rutas.LISTA}/{modulo}",
            arguments = listOf(navArgument("modulo") { type = NavType.StringType }),
        ) { entrada ->
            PantallaListaModulo(
                sesion = sesion,
                rutaModulo = entrada.arguments?.getString("modulo").orEmpty(),
                alVolver = { navegador.popBackStack() },
                alAbrir = { modulo, id ->
                    navegador.navigate("${Rutas.FICHA}/${modulo.ruta}/$id")
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
            PantallaFichaModulo(
                sesion = sesion,
                rutaModulo = entrada.arguments?.getString("modulo").orEmpty(),
                id = entrada.arguments?.getLong("id") ?: 0L,
                alVolver = { navegador.popBackStack() },
            )
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
    const val REGISTROS = "registros"
    const val EDITOR = "editor"
    const val AJUSTES = "ajustes"
    const val CONFLICTOS = "conflictos"
    const val MODULOS = "modulos"
    const val LISTA = "modulo"
    const val FICHA = "ficha"
}

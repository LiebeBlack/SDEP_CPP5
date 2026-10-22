package ve.edu.sdep.movil.ui.tema

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

/**
 * Paleta institucional.
 *
 * Verde profundo para la acción principal (el mismo del icono) y ámbar para
 * las advertencias de sincronización. Los colores están definidos a mano en
 * lugar de usar el color dinámico del sistema: en una aplicación de gestión,
 * que el botón «Eliminar» cambie de color según el fondo de pantalla del
 * teléfono no ayuda a nadie.
 *
 * Todas las funciones del esquema están declaradas, incluidas las superficies
 * (`surfaceContainer*`, `surfaceBright`, `surfaceDim`) y los colores inversos.
 * Cuando una función se omite, Material 3 aplica su paleta base violeta: las
 * tarjetas, menús y hojas de diálogo aparecían con tonos ajenos al verde
 * institucional, sobre todo en el tema oscuro.
 */
private val VerdeInstitucional = Color(0xFF1F6B4F)
private val VerdeClaro = Color(0xFF7FD8B0)
private val Ambar = Color(0xFF9A6700)
private val AmbarClaro = Color(0xFFFFDF9E)
private val RojoError = Color(0xFF8C1D18)

private val EsquemaClaro = lightColorScheme(
    // Acción principal
    primary = VerdeInstitucional,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFA8F0CE),
    onPrimaryContainer = Color(0xFF002114),
    inversePrimary = VerdeClaro,
    // Acción secundaria
    secondary = Color(0xFF4E6355),
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFD3E8D7),
    onSecondaryContainer = Color(0xFF0B1F15),
    // Advertencias y sincronización
    tertiary = Ambar,
    onTertiary = Color.White,
    tertiaryContainer = AmbarClaro,
    onTertiaryContainer = Color(0xFF2E1B00),
    // Fondo y superficies
    background = Color(0xFFF7FAF8),
    onBackground = Color(0xFF191C1A),
    surface = Color(0xFFF7FAF8),
    onSurface = Color(0xFF191C1A),
    surfaceVariant = Color(0xFFDCE5DD),
    onSurfaceVariant = Color(0xFF404943),
    surfaceTint = VerdeInstitucional,
    surfaceBright = Color(0xFFF7FAF8),
    surfaceDim = Color(0xFFD8DBD8),
    surfaceContainerLowest = Color.White,
    surfaceContainerLow = Color(0xFFF1F4F1),
    surfaceContainer = Color(0xFFEBEEEB),
    surfaceContainerHigh = Color(0xFFE5E8E5),
    surfaceContainerHighest = Color(0xFFDFE3DF),
    inverseSurface = Color(0xFF2E312F),
    inverseOnSurface = Color(0xFFEFF1EE),
    // Errores
    error = RojoError,
    onError = Color.White,
    errorContainer = Color(0xFFFFDAD6),
    onErrorContainer = Color(0xFF410002),
    // Bordes
    outline = Color(0xFF707973),
    outlineVariant = Color(0xFFC0C9C2),
    scrim = Color.Black,
)

private val EsquemaOscuro = darkColorScheme(
    // Acción principal
    primary = VerdeClaro,
    onPrimary = Color(0xFF003825),
    primaryContainer = Color(0xFF005138),
    onPrimaryContainer = Color(0xFFA8F0CE),
    inversePrimary = VerdeInstitucional,
    // Acción secundaria
    secondary = Color(0xFFB7CCBB),
    onSecondary = Color(0xFF223528),
    secondaryContainer = Color(0xFF384B3E),
    onSecondaryContainer = Color(0xFFD3E8D7),
    // Advertencias y sincronización
    tertiary = Color(0xFFF5BF48),
    onTertiary = Color(0xFF4B3400),
    tertiaryContainer = Color(0xFF6A4C00),
    onTertiaryContainer = AmbarClaro,
    // Fondo y superficies
    background = Color(0xFF0E1512),
    onBackground = Color(0xFFE0E3DF),
    surface = Color(0xFF0E1512),
    onSurface = Color(0xFFE0E3DF),
    surfaceVariant = Color(0xFF404943),
    onSurfaceVariant = Color(0xFFC0C9C2),
    surfaceTint = VerdeClaro,
    surfaceBright = Color(0xFF343B37),
    surfaceDim = Color(0xFF0E1512),
    surfaceContainerLowest = Color(0xFF090F0C),
    surfaceContainerLow = Color(0xFF171D1A),
    surfaceContainer = Color(0xFF1B211E),
    surfaceContainerHigh = Color(0xFF252B28),
    surfaceContainerHighest = Color(0xFF303633),
    inverseSurface = Color(0xFFE0E3DF),
    inverseOnSurface = Color(0xFF2B312E),
    // Errores
    error = Color(0xFFFFB4AB),
    onError = Color(0xFF690005),
    errorContainer = Color(0xFF93000A),
    onErrorContainer = Color(0xFFFFDAD6),
    // Bordes
    outline = Color(0xFF8A938C),
    outlineVariant = Color(0xFF404943),
    scrim = Color.Black,
)

@Composable
fun TemaSdep(
    oscuro: Boolean = isSystemInDarkTheme(),
    contenido: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (oscuro) EsquemaOscuro else EsquemaClaro,
        content = contenido,
    )
}

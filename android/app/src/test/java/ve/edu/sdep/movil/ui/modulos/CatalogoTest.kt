package ve.edu.sdep.movil.ui.modulos

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import ve.edu.sdep.movil.datos.local.entidad.DocumentoEntity
import ve.edu.sdep.movil.datos.local.entidad.EmpleadoEntity
import ve.edu.sdep.movil.dominio.modelo.Modulo
import java.time.LocalDate

/**
 * Reglas de presentación de las pantallas de consulta.
 *
 * Son funciones puras sobre el espejo: no tocan Room ni la red. Lo que se
 * comprueba aquí es lo que el usuario lee (etiqueta de vencimiento, búsqueda y
 * contenido de una ficha), no la sincronización.
 */
class CatalogoTest {

    private fun empleado(id: Long = 7) = EmpleadoEntity(
        id = id,
        nombres = "Ana",
        apellidos = "Pérez",
        cedula = "V-1",
        tipoEmpleado = "docente",
        cargo = "Docente",
        departamento = "Académico",
        fechaContratacion = "2024-01-15",
        salarioBase = 1000.0,
    )

    private fun documento(id: Long, titulo: String, vence: LocalDate?) = DocumentoEntity(
        id = id,
        empleadoId = 7,
        tipoDocumento = "acta",
        titulo = titulo,
        nombreArchivo = "acta.pdf",
        fechaVencimiento = vence?.toString(),
    )

    @Test
    fun `un documento vencido se marca en rojo y aparece en los avisos`() {
        val catalogo = Catalogo(
            Datos(
                empleados = listOf(empleado()),
                documentos = listOf(
                    documento(1, "Acta de grado", LocalDate.now().minusDays(3)),
                ),
            ),
        )

        val fila = catalogo.filas(Modulo.DOCUMENTOS).single()
        assertEquals("Vencido", fila.etiqueta)
        assertEquals(Tono.ERROR, fila.tono)

        val aviso = catalogo.alertas().single()
        assertEquals(Modulo.DOCUMENTOS, aviso.modulo)
        assertEquals(1L, aviso.fila.id)
    }

    @Test
    fun `un documento que vence pronto se avisa sin marcarlo como vencido`() {
        val catalogo = Catalogo(
            Datos(
                empleados = listOf(empleado()),
                documentos = listOf(
                    documento(2, "Certificado médico", LocalDate.now().plusDays(10)),
                ),
            ),
        )

        val fila = catalogo.filas(Modulo.DOCUMENTOS).single()
        assertEquals("Vence en 10 d", fila.etiqueta)
        assertEquals(Tono.ALERTA, fila.tono)
    }

    @Test
    fun `la busqueda ignora mayusculas y mira el titulo`() {
        val catalogo = Catalogo(
            Datos(
                empleados = listOf(empleado()),
                documentos = listOf(
                    documento(3, "Acta de grado", null),
                    documento(4, "Constancia de trabajo", null),
                ),
            ),
        )

        // El texto buscado es el TÍTULO: ambos documentos comparten el tipo
        // «acta», así que buscar «ACTA» devolvería las dos filas (la búsqueda
        // también mira el subtítulo, y eso es correcto).
        val encontrados = catalogo.buscar(Modulo.DOCUMENTOS, "CONSTANCIA DE TRABAJO")
        assertEquals(1, encontrados.size)
        assertEquals("Constancia de trabajo", encontrados.single().titulo)
        assertTrue(catalogo.buscar(Modulo.DOCUMENTOS, "no existe").isEmpty())
    }

    @Test
    fun `la ficha del empleado trae sus secciones y resuelve los campos`() {
        val catalogo = Catalogo(Datos(empleados = listOf(empleado(id = 7))))

        val ficha = catalogo.ficha(Modulo.EMPLEADOS, 7)
        assertNotNull(ficha)
        assertEquals("Ana Pérez", ficha!!.titulo)
        assertEquals("Datos personales", ficha.secciones.first().titulo)

        val cedula = ficha.secciones
            .flatMap { it.campos }
            .single { it.etiqueta == "Cédula" }
        assertEquals("V-1", cedula.valor)

        assertNull(catalogo.ficha(Modulo.EMPLEADOS, 99))
    }
}

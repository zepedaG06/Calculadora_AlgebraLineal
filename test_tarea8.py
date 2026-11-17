"""Pruebas de los requisitos del Programa 8 (métodos iterativos de Jacobi y Gauss-Seidel y renders integrados).

Comprueba las validaciones, el análisis de la diagonal, el reordenamiento, las reglas de actualización de cada método,
el criterio de parada, la detección de no convergencia, los tres casos de prueba obligatorios, la comparación con
Gauss-Jordan, el menú de consola y que cada sección de la GUI muestre su render al resolver.
Unidad: Álgebra Lineal (MTM0120), Programa 8.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
"""
import time
import unittest

import main
from modulos import graficos as g
from modulos import modulo_iterativos as it
from teoremas.teoremas_iterativos import LOGO_ITERATIVOS, TEOREMAS_ITERATIVOS

CASO_1, CASO_2, CASO_3, CASO_EXTRA = list(it.CASOS_DE_PRUEBA.values())


def resolver_caso(caso, **cambios):
    """Resuelve un caso de prueba con los cambios indicados."""
    datos = {**{k: caso[k] for k in ("A", "b", "x0", "tolerancia", "max_iteraciones", "reordenar")}, **cambios}
    return it.resolver_iterativos(datos["A"], datos["b"], datos["x0"], datos["tolerancia"], datos["max_iteraciones"], datos["reordenar"])


def sesion_consola(funcion, respuestas):
    """Ejecuta una función de consola con respuestas simuladas y retorna (resultado, texto mostrado)."""
    pendientes, mostrado = iter(respuestas), []
    resultado = funcion(entrada=lambda mensaje: (mostrado.append(mensaje), next(pendientes))[1],
                        salida=lambda texto="": mostrado.append(str(texto)))
    return resultado, "\n".join(mostrado)


class Validaciones(unittest.TestCase):
    """Datos de entrada: dimensiones, tolerancia, máximo de iteraciones y diagonal."""

    def test_datos_invalidos_con_mensaje_claro(self):
        """Comprueba que cada dato inválido se rechaza con un mensaje que explica el motivo."""
        A, b, x0 = [[4, 1], [1, 3]], [1, 2], [0, 0]
        casos = [((A[:1] + [[1]], b, x0, "0.001", 10), "cuadrada"), ((A, [1], x0, "0.001", 10), "b debe tener 2"),
                 ((A, b, [0], "0.001", 10), "x⁽⁰⁾"), ((A, b, x0, "-0.1", 10), "positivo"), ((A, b, x0, "0", 10), "positivo"),
                 ((A, b, x0, "abc", 10), "tolerancia"), ((A, b, x0, "0.001", 0), "entre 1"), ((A, b, x0, "0.001", "2.5"), "entero"),
                 (([[4, "x"], [1, 3]], b, x0, "0.001", 10), "a12")]
        for argumentos, mensaje in casos:
            with self.subTest(mensaje=mensaje), self.assertRaisesRegex(ValueError, mensaje):
                it.resolver_iterativos(*argumentos)

    def test_dominancia_diagonal(self):
        """Comprueba la dominancia estricta fila por fila y la detección de ceros en la diagonal."""
        self.assertTrue(it.analizar_diagonal([[4, 1, 2], [1, 5, 3], [0, 1, 2]])["dominante"])
        analisis = it.analizar_diagonal([[3, 2, 1], [2, 3, 2], [1, 2, 3]])
        self.assertFalse(analisis["dominante"])
        self.assertEqual([f["cumple"] for f in analisis["filas"]], [False, False, False])
        self.assertEqual([f["cumple"] for f in it.analizar_diagonal([[3, 1, 1], [2, 3, 2], [1, 1, 3]])["filas"]], [True, False, True])
        self.assertEqual(it.analizar_diagonal([[1, 2], [3, 0]])["ceros"], [1])
        self.assertFalse(it.analizar_diagonal([[2, 2], [1, 3]])["dominante"])

    def test_reordenamiento_solo_si_existe(self):
        """Comprueba que se encuentra un orden válido cuando existe y que no se fuerza cuando no existe."""
        self.assertEqual(it.buscar_reordenamiento([[1, 5], [4, 1]])["orden"], [1, 0])
        sin_ceros = it.buscar_reordenamiento([[1, 2, 2], [2, 1, 2], [2, 2, 1]])
        self.assertEqual(sin_ceros["tipo"], "sin_ceros")
        imposible = it.buscar_reordenamiento([[0, 1], [0, 2]])
        self.assertIsNone(imposible["orden"])
        r = it.resolver_iterativos([[0, 1], [0, 2]], [1, 2], [0, 0], "0.001", 10)
        self.assertFalse(r["definido"])
        self.assertIn("No existe ningún orden", r["conclusion"])
        r = it.resolver_iterativos([[0, 1], [1, 0]], [1, 2], [0, 0], "0.001", 10, reordenar=False)
        self.assertFalse(r["definido"])
        self.assertIn("desactivado", r["conclusion"])


class Metodos(unittest.TestCase):
    """Reglas de actualización, criterio de parada y detección de no convergencia."""

    def test_jacobi_usa_solo_la_iteracion_anterior(self):
        """Comprueba a mano la primera iteración de Jacobi: todas las componentes salen de x⁽⁰⁾."""
        r = it.jacobi([[4, 1], [2, 5]], [6, 9], [1, 1], 1e-12, 1)
        self.assertEqual(r["iteraciones"][1]["x"], [(6 - 1) / 4, (9 - 2) / 5])

    def test_gauss_seidel_usa_el_valor_recien_calculado(self):
        """Comprueba a mano la primera iteración de Gauss-Seidel: x₂ usa el x₁ nuevo."""
        r = it.gauss_seidel([[4, 1], [2, 5]], [6, 9], [1, 1], 1e-12, 1)
        x1 = (6 - 1) / 4
        self.assertEqual(r["iteraciones"][1]["x"], [x1, (9 - 2 * x1) / 5])

    def test_criterio_de_parada_y_residuo(self):
        """Comprueba que se detiene en la primera iteración con ‖x⁽ᵏ⁾ − x⁽ᵏ⁻¹⁾‖∞ ≤ ε y que registra el residuo."""
        r = it.jacobi([[4, 1], [1, 3]], [5, 4], [0, 0], 1e-6, 100)
        errores = [f["error"] for f in r["iteraciones"][1:]]
        self.assertLessEqual(errores[-1], 1e-6)
        self.assertTrue(all(e > 1e-6 for e in errores[:-1]))
        self.assertAlmostEqual(r["residuo"], it.norma_infinito(it.residuo([[4, 1], [1, 3]], [5, 4], r["solucion"])))
        r = it.jacobi([[4, 1], [1, 3]], [5, 4], [0, 0], 1e-12, 3)
        self.assertEqual((r["estado"], r["n_iteraciones"]), ("maximo", 3))
        self.assertTrue(any("máximo" in a for a in r["advertencias"]))

    def test_divergencia_sin_cerrar(self):
        """Comprueba que un error creciente y los valores no finitos se informan con una advertencia."""
        r = it.jacobi([[1, 3], [3, 1]], [4, 4], [0, 0], 1e-6, 50)
        self.assertFalse(r["convergio"])
        self.assertTrue(any("creciendo" in a for a in r["advertencias"]))
        r = it.jacobi([[1, 10], [10, 1]], [1, 1], [0, 0], 1e-6, 1000)
        self.assertEqual(r["estado"], "no_finito")
        self.assertTrue(all(abs(v) < float("inf") for v in r["iteraciones"][-1]["x"]))


class CasosDePrueba(unittest.TestCase):
    """Los tres casos obligatorios de la guía y el ejemplo adicional."""

    def test_caso_1_convergencia(self):
        """Comprueba que con diagonal dominante ambos convergen, Gauss-Seidel en menos iteraciones, y coinciden con Gauss-Jordan."""
        r = resolver_caso(CASO_1)
        self.assertTrue(r["analisis"]["dominante"])
        self.assertTrue(r["jacobi"]["convergio"] and r["gauss_seidel"]["convergio"])
        self.assertLess(r["gauss_seidel"]["n_iteraciones"], r["jacobi"]["n_iteraciones"])
        self.assertEqual(r["comparacion"]["menos_iteraciones"], "Gauss-Seidel")
        self.assertEqual(r["referencia"]["exacta"], [1, 2, -1, 1])
        for clave in ("jacobi", "gauss_seidel"):
            self.assertLess(r["comparacion"]["diferencias"][clave], 1e-5)
            self.assertLess(r[clave]["residuo"], 1e-4)
        self.assertTrue(r["verificacion"]["correcto"])

    def test_caso_2_reordenamiento(self):
        """Comprueba que el cero en la diagonal se resuelve intercambiando E1 y E2 y que la solución no cambia."""
        r = resolver_caso(CASO_2)
        self.assertEqual(r["analisis"]["ceros"], [1])
        self.assertTrue(r["reordenamiento"]["aplicado"])
        self.assertEqual(r["reordenamiento"]["orden"], [1, 0, 2])
        self.assertTrue(r["analisis_usado"]["dominante"])
        self.assertEqual(r["referencia"]["exacta"], [1, 2, 3])
        self.assertTrue(r["gauss_seidel"]["convergio"] and r["verificacion"]["correcto"])
        sin_reordenar = resolver_caso(CASO_2, reordenar=False)
        self.assertFalse(sin_reordenar["definido"])

    def test_caso_3_no_convergencia(self):
        """Comprueba que sin diagonal dominante se informa la no convergencia sin afirmar que la condición la cause."""
        r = resolver_caso(CASO_3)
        self.assertFalse(r["analisis"]["dominante"])
        self.assertFalse(r["jacobi"]["convergio"] or r["gauss_seidel"]["convergio"])
        self.assertTrue(r["jacobi"]["advertencias"] and r["gauss_seidel"]["advertencias"])
        self.assertEqual(r["referencia"]["exacta"], [1, 1, 1])
        texto = " ".join(e["conclusion"] for e in r["procedimiento"])
        self.assertIn("no implica que los métodos diverjan", texto)
        self.assertTrue(r["verificacion"]["correcto"])

    def test_condicion_suficiente_no_necesaria(self):
        """Comprueba que una matriz sin diagonal dominante también puede converger con Gauss-Seidel."""
        r = resolver_caso(CASO_EXTRA)
        self.assertFalse(r["analisis"]["dominante"])
        self.assertTrue(r["gauss_seidel"]["convergio"])


class ConsolaYRenders(unittest.TestCase):
    """Menú de consola y escenas de las iteraciones."""

    def test_menu_de_consola(self):
        """Comprueba la opción 6, el logotipo, los teoremas, un caso de prueba y la reentrada de datos inválidos."""
        self.assertIn(("6", "Métodos iterativos: Jacobi y Gauss-Seidel"), main.OPCIONES_MENU_PRINCIPAL)
        _, texto = sesion_consola(main.menu_iterativos, ["0", "2", "V"])
        self.assertIn(LOGO_ITERATIVOS, texto)
        self.assertTrue(all(titulo in texto for titulo, _ in TEOREMAS_ITERATIVOS))
        self.assertIn("Tabla de Jacobi", texto)
        informe, texto = sesion_consola(main.ejecutar_iterativos, ["2", "4 1", "1 3", "5 4", "0 0", "-1", "50", "", "", "", ""])
        self.assertIn("Error:", texto)
        self.assertTrue(informe["verificacion"]["correcto"])

    def test_escenas_de_iteraciones(self):
        """Comprueba la gráfica comparativa del error y las trayectorias en 2D y 3D."""
        r = resolver_caso(CASO_2)
        self.assertTrue(g.escena_errores_iterativos(r, 1, 700, 260))
        self.assertTrue(g.escena_iteraciones(r, 0.5, 0.6, 0.4, 700, 400))
        self.assertIsNone(g.escena_iteraciones(resolver_caso(CASO_1), 1, 0, 0, 700, 400))
        r2 = it.resolver_iterativos([[4, 1], [1, 3]], [5, 4], [0, 0], "1e-6", 50)
        self.assertEqual(len(g.trayectorias_iterativas(r2)), 2)
        self.assertTrue(g.escena_iteraciones(r2, 1, 0, 0, 700, 400))


class FondoAnimado(unittest.TestCase):
    """Escena del fondo animado: reproducible, ajustada al área y dentro de la paleta."""

    def test_escena_reproducible_y_en_paleta(self):
        """Comprueba que el fondo es reproducible, que los nodos no escapan del área y que solo usa tonos entre fondo y acento."""
        estados = [g.crear_fondo(7), g.crear_fondo(7)]
        for estado in estados:
            for _ in range(200):
                g.avanzar_fondo(estado, 1 / 30, 1200, 800)
        self.assertEqual(estados[0]["nodos"], estados[1]["nodos"])
        self.assertTrue(all(-31 <= n["x"] <= 1231 and -31 <= n["y"] <= 831 for n in estados[0]["nodos"]))
        escena = g.escena_fondo(estados[0], "#0B1B1C", "#04A7AD")
        colores = {p.get("color") or p.get("relleno") or p.get("borde") for p in escena}
        for color in colores:
            r = int(color[1:3], 16)
            self.assertTrue(0x04 <= r <= 0x0B, color)
        g.avanzar_fondo(estados[0], 1 / 30, 300, 200)
        self.assertLess(len(estados[0]["nodos"]), 20)
        self.assertTrue(g.rejilla_fondo(0, 0, 200, 200, "#0B1B1C", "#04A7AD"))


class RendersIntegrados(unittest.TestCase):
    """Cada sección de la GUI muestra su render animado al resolver."""

    @classmethod
    def setUpClass(cls):
        """Carga la GUI una vez para todas las pruebas de la clase."""
        cls.gui = main.cargar_aplicacion()

    def test_cada_seccion_muestra_su_render(self):
        """Comprueba con widgets reales que cada sección muestra su render, que no hay página aparte y que el fondo animado se dibuja y se apaga."""
        if self.gui.ctk is None:
            self.skipTest("CustomTkinter no disponible")
        try:
            app = self.gui.AplicacionAlgebraLineal()
        except self.gui.tk.TclError as error:
            self.skipTest(f"Pantalla Tk no disponible: {error}")
        errores = []
        app.report_callback_exception = lambda *args: errores.append(args)
        app.withdraw()

        def bombear(segundos=0.4):
            """Procesa los eventos de Tk durante un instante."""
            fin = time.monotonic() + segundos
            while time.monotonic() < fin:
                app.update()
                time.sleep(0.005)

        def renders(pagina):
            """Cuenta las tarjetas de render del área de resultados."""
            return [w for w in pagina.area_resultado.interior.winfo_children() if isinstance(w, self.gui.TarjetaRender)]
        try:
            self.assertNotIn("renders", [clave for clave, *_ in app.SECCIONES])
            self.assertIn("iterativos", [clave for clave, *_ in app.SECCIONES])
            for clave in ("calculadora", "vectorial", "axb", "propiedades_ax", "lu", "independencia", "determinantes", "matrices", "iterativos"):
                with self.subTest(seccion=clave):
                    pagina = app.ir_a(clave)
                    pagina.resolver()
                    bombear(2.5)
                    self.assertTrue(renders(pagina), f"«{clave}» no muestra un render")
            iterativos = app.paginas["iterativos"]
            for nombre in iterativos.ejemplos:
                with self.subTest(caso=nombre):
                    iterativos.cargar_ejemplo(nombre)
                    iterativos.resolver()
                    bombear(1.2)
                    self.assertTrue(iterativos.resultado["definido"])
                    self.assertTrue(iterativos.resultado["verificacion"]["correcto"])
            tarjeta = renders(iterativos)[0]
            tarjeta.reproductor.fijar(0.5)
            self.assertTrue(tarjeta.lienzo.ultima_escena)
            fondo = app.fondo_animado
            app.deiconify()
            bombear(0.5)
            fondo.actualizar_superficies()
            self.assertTrue(fondo.superficies)
            fondo._dibujar(0.03)
            self.assertTrue(any(lienzo.find_withtag("fondo_animado") for _w, lienzo in fondo.superficies))
            fondo.alternar(False)
            self.assertFalse(any(lienzo.find_withtag("fondo_animado") for _w, lienzo in fondo.superficies))
            fondo.alternar(True)
            app.withdraw()
            iterativos.entrada_tolerancia.delete(0, "end")
            iterativos.entrada_tolerancia.insert(0, "-5")
            iterativos.resolver()
            bombear(0.3)
            self.assertEqual(errores, [])
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()

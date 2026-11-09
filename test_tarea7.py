"""Pruebas de los requisitos del Programa 7 (módulo de Métodos Numéricos, renders y animaciones).

Comprueba las funciones elementales propias, el intérprete de funciones, la bisección, el graficador, la notación
posicional en base 10 y base 2, los errores numéricos, el motor de renders, el menú de consola y la GUI real.
Unidad: Álgebra Lineal (MTM0120), Programa 7.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
"""
import struct
import tempfile
import time
import unittest
from fractions import Fraction as F
from pathlib import Path

import main
from modulos import graficos as g
from modulos import modulo_numericos as n
from teoremas.teoremas_numericos import LOGO_NUMERICOS, TEOREMAS_NUMERICOS

RAIZ_CUBICA = 1.5213797068045676


def sesion_consola(funcion, respuestas):
    """Ejecuta una función de consola con respuestas simuladas y retorna (resultado, texto mostrado)."""
    pendientes, mostrado = iter(respuestas), []
    resultado = funcion(entrada=lambda mensaje: (mostrado.append(mensaje), next(pendientes))[1],
                        salida=lambda texto="": mostrado.append(str(texto)))
    return resultado, "\n".join(mostrado)


class FuncionesElementales(unittest.TestCase):
    """Seno, exponencial, logaritmo y demás funciones calculadas con series propias."""

    def test_valores_conocidos(self):
        """Comprueba las series contra valores conocidos con 15 cifras."""
        casos = [(n.seno(n.PI / 6), 0.5), (n.coseno(n.PI / 3), 0.5), (n.seno(100.0), -0.5063656411097588),
                 (n.exponencial(1.0), 2.718281828459045), (n.exponencial(-20.0), 2.061153622438558e-09),
                 (n.logaritmo_natural(10.0), 2.302585092994046), (n.logaritmo_10(1000.0), 3.0),
                 (n.arcotangente(1.0), n.PI / 4), (n.arcoseno(0.5), n.PI / 6), (n.raiz_cuadrada(2.0), 1.4142135623730951)]
        for obtenido, esperado in casos:
            with self.subTest(esperado=esperado):
                self.assertAlmostEqual(obtenido, esperado, delta=1e-14 * max(1.0, abs(esperado)))

    def test_dominios_y_desbordes(self):
        """Comprueba que fuera del dominio se lanza ValueError y que eˣ desborda como en la computadora."""
        for funcion, argumento in ((n.logaritmo_natural, 0.0), (n.raiz_cuadrada, -1.0), (n.arcoseno, 2.0)):
            with self.subTest(funcion=funcion.__name__), self.assertRaises(ValueError):
                funcion(argumento)
        with self.assertRaises(OverflowError):
            n.exponencial(710.0)
        self.assertEqual(n.exponencial(-800.0), 0.0)


class InterpreteDeFunciones(unittest.TestCase):
    """Lectura de funciones escritas como texto."""

    def test_precedencia_y_producto_implicito(self):
        """Comprueba la precedencia, el producto sin signo y las constantes."""
        casos = {"x^3 - x - 2": (2, 4), "-x^2": (3, -9), "2^-1": (0, 0.5), "(x+1)(x-1)": (3, 8), "2sen(x)": (0, 0),
                 "2e": (0, 2 * n.E), "2e3": (0, 2000), "x²+x³": (2, 12), "2,5x": (2, 5), "2**3": (0, 8), "cos(pi)": (0, -1),
                 "√(x)": (9, 3), "1/2x": (4, 2)}
        for texto, (x, esperado) in casos.items():
            with self.subTest(texto=texto):
                self.assertAlmostEqual(n.FuncionReal(texto).evaluar(x), esperado, places=12)

    def test_fuera_del_dominio_es_none(self):
        """Comprueba que un punto fuera del dominio se informa con None y no rompe el programa."""
        for texto, x in (("1/x", 0), ("sqrt(x)", -1), ("ln(x)", 0), ("(-8)^(1/3)", 0), ("e^x", 1000)):
            with self.subTest(texto=texto):
                self.assertIsNone(n.FuncionReal(texto).evaluar(x))

    def test_errores_de_escritura_con_posicion(self):
        """Comprueba los mensajes de error y la posición del carácter que los causa."""
        casos = {"x+": "incompleta", "(x": "Falta cerrar", "y+1": "no es válido", "sen x": "necesita paréntesis",
                 "x)": "Sobra", "1..2": "separador decimal", "": "Escribe una función"}
        for texto, mensaje in casos.items():
            with self.subTest(texto=texto), self.assertRaisesRegex(n.ErrorFuncion, mensaje):
                n.FuncionReal(texto)

    def test_leer_real(self):
        """Comprueba la lectura de números escritos como expresiones sin x."""
        self.assertAlmostEqual(n.leer_real("pi/2"), n.PI / 2)
        self.assertEqual(n.leer_exacto("1/3"), (F(1, 3), True))
        with self.assertRaisesRegex(ValueError, "sin x"):
            n.leer_real("2x")


class Biseccion(unittest.TestCase):
    """Opción 1: método de bisección con su procedimiento y su verificación."""

    def test_raiz_iteraciones_y_verificacion(self):
        """Comprueba la raíz de x³ − x − 2, la cota teórica de iteraciones y la verificación."""
        r = n.biseccion("x^3 - x - 2", 1, 2, 1e-6)
        self.assertTrue(r["definido"] and r["es_raiz"] and r["alcanzo_tolerancia"])
        self.assertLessEqual(abs(r["raiz"] - RAIZ_CUBICA), 1e-6)
        self.assertEqual(r["n"], r["n_teorico"])
        self.assertEqual(r["n"], 20)
        self.assertTrue(r["verificacion"]["correcto"])
        titulos = [e["titulo"] for e in r["procedimiento"]]
        self.assertEqual(titulos[:3], ["Datos del problema", "Teorema de Bolzano", "Cantidad de iteraciones"])
        self.assertEqual(titulos[-1], "Criterio de paro y resultado")

    def test_invariantes_de_cada_iteracion(self):
        """Comprueba que c es el punto medio, que el intervalo se divide a la mitad y que conserva el cambio de signo."""
        r = n.biseccion("cos(x) - x", 0, 1, 1e-10)
        for it in r["iteraciones"]:
            with self.subTest(n=it["n"]):
                self.assertEqual(it["c"], (it["a"] + it["b"]) / 2)
                self.assertAlmostEqual(it["b"] - it["a"], 1 / 2 ** (it["n"] - 1), delta=1e-15)
                self.assertLessEqual((it["fa"] > 0) - (it["fa"] < 0), 0 if it["fb"] > 0 else 1)
        self.assertAlmostEqual(r["raiz"], 0.7390851332151607, delta=1e-10)

    def test_bolzano_no_se_cumple(self):
        """Comprueba que sin cambio de signo no se inventa una raíz y que se sugiere un intervalo útil."""
        r = n.biseccion("x^2 + 1", -1, 1)
        self.assertFalse(r["definido"])
        self.assertIn("mismo signo", r["conclusion"])
        self.assertFalse(r["verificacion"]["correcto"])
        r = n.biseccion("x^2 - 1", -2, 2)
        self.assertIsNotNone(r["sugerencia"])
        p, q = r["sugerencia"]
        self.assertLessEqual(n.FuncionReal("x^2 - 1").evaluar(p) * n.FuncionReal("x^2 - 1").evaluar(q), 0)

    def test_discontinuidad_no_es_raiz(self):
        """Comprueba que el cambio de signo de tan(x) en [1, 2] se reconoce como un polo y no como una raíz."""
        r = n.biseccion("tan(x)", 1, 2, 1e-6)
        self.assertFalse(r["es_raiz"])
        self.assertIn("no es continua", r["advertencias"][0])
        self.assertFalse(r["verificacion"]["correcto"])
        self.assertFalse(n.biseccion("1/x", -1, 1)["definido"])

    def test_raiz_exacta_y_limites(self):
        """Comprueba la raíz en un extremo, el máximo de iteraciones y los datos inválidos."""
        r = n.biseccion("x", 0, 1)
        self.assertEqual((r["raiz"], r["n"]), (0, 0))
        r = n.biseccion("x^2 - 2", 1, 2, 1e-12, 3)
        self.assertFalse(r["alcanzo_tolerancia"])
        self.assertEqual(r["n"], 3)
        for args in (("x", 2, 1), ("x", -1, 1, 0), ("x", -1, 1, 1e-6, 0)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                n.biseccion(*args)


class Graficador(unittest.TestCase):
    """Opción 2: graficador de funciones con puntos notables."""

    def test_ceros_extremos_e_intersecciones(self):
        """Comprueba ceros, extremos e intersecciones verificados con las funciones originales."""
        r = n.informe_graficador(["x^2 - 1", "sen(x)", "x"], -5, 5)
        raices = [[round(x, 9) for x in d["raices"]] for d in r["analisis"]]
        self.assertEqual(raices[0], [-1.0, 1.0])
        self.assertEqual(raices[1], [round(-n.PI, 9), 0.0, round(n.PI, 9)])
        self.assertEqual(r["analisis"][0]["minimos"][0][1], -1.0)
        self.assertTrue(r["cortes"])
        self.assertTrue(r["verificacion"]["correcto"])

    def test_asintotas_y_subdesbordamiento(self):
        """Comprueba que no se unen los tramos de una asíntota ni se cuentan como raíces los ceros por redondeo."""
        tan = n.analizar_funcion("tan(x)", -5, 5)
        self.assertEqual(len(tan["saltos"]), 4)
        self.assertEqual(n.analizar_funcion("1/x", -1, 1)["raices"], [])
        exponencial = n.analizar_funcion("e^x", -800, 800)
        self.assertEqual(exponencial["raices"], [])
        self.assertTrue(exponencial["tramos_cero"])

    def test_limites_y_grafica_de_consola(self):
        """Comprueba los límites de datos y el dibujo con caracteres."""
        with self.assertRaises(ValueError):
            n.informe_graficador(["x", "x", "x", "x"], -1, 1)
        with self.assertRaises(ValueError):
            n.informe_graficador(["x"], 1, 1)
        lineas = n.grafica_ascii("sen(x)", -6.3, 6.3, 50, 10)
        self.assertEqual(len(lineas), 14)
        self.assertIn("*", "".join(lineas))


class NotacionPosicional(unittest.TestCase):
    """Opción 3: notación posicional en base 10 y base 2 y representación en la computadora."""

    def test_base_10_a_base_2_y_de_vuelta(self):
        """Comprueba 13.625 = 1101.101 en ambos sentidos con sus pesos y contribuciones."""
        r = n.informe_posicional("13.625", 10)
        self.assertEqual(r["binario"]["texto"], "1101.101")
        self.assertEqual([d["residuo"] for d in r["binario"]["divisiones"]], [1, 0, 1, 1])
        self.assertEqual([p["bit"] for p in r["binario"]["multiplicaciones"]], [1, 0, 1])
        self.assertTrue(r["verificacion"]["correcto"])
        de_vuelta = n.informe_posicional("1101.101", 2)
        self.assertEqual(de_vuelta["descomposicion"]["valor"], F(109, 8))
        self.assertEqual([f["peso"] for f in de_vuelta["descomposicion"]["filas"]][:2], [8, 4])

    def test_periodicos_y_negativos(self):
        """Comprueba el desarrollo periódico de 0.1 y los números negativos."""
        self.assertEqual(n.decimal_a_binario(F(1, 10))["texto"], "0.0(0011)")
        self.assertTrue(n.decimal_a_binario(F(1, 3))["periodico"])
        self.assertEqual(n.informe_posicional("-5.75", 10)["binario"]["texto"], "-101.11")

    def test_ieee754_coincide_con_la_computadora(self):
        """Comprueba que los bits de 0.1 son los que guarda Python y que el error de representación es exacto."""
        r = n.representacion_ieee754(F(1, 10), 64)
        self.assertEqual(r["cadena"], "".join(f"{b:08b}" for b in struct.pack(">d", 0.1)))
        self.assertEqual(r["exponente_real"], -4)
        self.assertEqual(r["almacenado"], F(0.1))
        self.assertEqual(r["error_representacion"], F(0.1) - F(1, 10))
        self.assertTrue(n.representacion_ieee754(F(13625, 1000), 32)["exacta"])

    def test_digitos_invalidos(self):
        """Comprueba que se rechazan dígitos que no existen en la base."""
        for texto, base in (("12", 2), ("abc", 10), ("1.2.3", 10), ("", 10), ("9" * 70, 10)):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                n.informe_posicional(texto, base)


class ErroresNumericos(unittest.TestCase):
    """Opción 4: errores absoluto, relativo y porcentual, redondeo, truncamiento y épsilon de la máquina."""

    def test_errores_de_pi(self):
        """Comprueba los errores de 3.14 como aproximación de π y sus cifras significativas."""
        r = n.informe_errores("pi", "3.14", 4)
        self.assertAlmostEqual(float(r["errores"]["absoluto"]), 0.0015926535897932, places=15)
        self.assertAlmostEqual(float(r["errores"]["relativo"]), 0.000506957382897, places=14)
        self.assertEqual(r["cifras_correctas"], 3)
        self.assertEqual((r["redondeado"], r["truncado"]), (F("3.142"), F("3.141")))
        self.assertTrue(r["verificacion"]["correcto"])

    def test_aritmetica_exacta_y_casos_limite(self):
        """Comprueba fracciones exactas, valor real 0 y aproximación exacta."""
        r = n.informe_errores("1/3", "0.333", 3)
        self.assertEqual(r["errores"]["absoluto"], F(1, 3000))
        self.assertIsNone(n.informe_errores("0", "0.5", 3)["errores"]["relativo"])
        self.assertIn("coincide exactamente", n.informe_errores("2.5", "2.5", 3)["conclusion"])

    def test_errores_de_la_maquina(self):
        """Comprueba el épsilon de la máquina y los ejemplos de redondeo, absorción y cancelación."""
        epsilon, _ = n.epsilon_de_maquina()
        self.assertEqual(epsilon, 2.0 ** -52)
        demostraciones = {d["expresion"]: d for d in n.demostraciones_punto_flotante()}
        self.assertNotEqual(F(demostraciones["0.1 + 0.2"]["calculado"]), demostraciones["0.1 + 0.2"]["exacto"])
        self.assertEqual(demostraciones["10¹⁶ + 1"]["calculado"], 1e16)
        cancelacion = n.cancelacion_raices()
        self.assertGreater(cancelacion[-1]["error_relativo"], cancelacion[0]["error_relativo"])
        taylor = n.truncamiento_taylor()
        self.assertLess(taylor[-1]["error"], 1e-12)

    def test_redondeo_nunca_peor_que_truncar(self):
        """Comprueba en la tabla que redondear da un error menor o igual que truncar."""
        for fila in n.tabla_redondeo(F(2, 3), 12):
            with self.subTest(n=fila["n"]):
                self.assertLessEqual(fila["error_redondeo"], fila["error_truncamiento"])


class MotorDeRenders(unittest.TestCase):
    """Escenas vectoriales independientes de la interfaz."""

    def test_vista_ida_y_vuelta_y_recorte(self):
        """Comprueba la conversión plano-píxel y el recorte de segmentos."""
        vista = g.Vista(-2, 3, -1, 4, 600, 400)
        for x, y in ((-2, -1), (0, 0), (3, 4), (1.25, 2.5)):
            px, py = vista.a_pixel(x, y)
            self.assertEqual(tuple(round(v, 9) for v in vista.a_plano(px, py)), (x, y))
        self.assertEqual(g.recortar_polilinea([(0, 0), (10, 10)], 2, 2, 8, 8), [[(2.0, 2.0), (8.0, 8.0)]])
        self.assertEqual(g.marcas_eje(-5, 5)[0], [-4.0, -2.0, 0.0, 2.0, 4.0])

    def test_animacion_de_biseccion(self):
        """Comprueba que el intervalo animado empieza en [a, b] y termina en el último intervalo."""
        r = n.biseccion("x^3 - x - 2", 1, 2, 1e-3)
        inicio, fin = g.estado_biseccion(r, 0), g.estado_biseccion(r, r["n"])
        self.assertEqual((inicio["a"], inicio["b"]), (1, 2))
        ultima = r["iteraciones"][-1]
        self.assertEqual((fin["a"], fin["b"]), (ultima["nuevo_a"], ultima["nuevo_b"]))
        for t in (0, 0.5, 3.3, r["n"]):
            self.assertTrue(g.escena_biseccion(r, t, 800, 420))

    def test_planos_que_se_cruzan(self):
        """Comprueba que el árbol BSP parte los planos sin perder área y que el render marca la solución."""
        planos = [([1.0, 0.0, 0.0], 0.0), ([0.0, 1.0, 0.0], 0.0)]
        piezas = [(g.plano_en_caja(*planos[0], 2), 0), (g.plano_en_caja(*planos[1], 2), 1)]
        ordenadas = g.ordenar_superficies(piezas, planos, (5.0, -7.0, 3.0))
        self.assertEqual(sorted(i for _, i in ordenadas), [0, 1, 1])
        escena = g.escena_sistema_3d([[1, 1, 1], [2, -1, 1], [1, 2, -1]], [6, 3, 2], [1, 2, 3], 1, 0.6, 0.4, 800, 500)
        self.assertIn("x = (1, 2, 3)", [p.get("texto") for p in escena])

    def test_transformacion_muestra_el_determinante(self):
        """Comprueba que el render de A informa |det(A)| y la orientación."""
        textos = [p.get("texto", "") for p in g.escena_transformacion_2d([[0, 1], [1, 0]], 1, 800, 500)]
        self.assertIn("Área = |det| = 1", textos)
        self.assertIn("orientación invertida", textos)
        textos = [p.get("texto", "") for p in g.escena_transformacion_3d([[1, 1, 0], [0, 2, 0], [0, 0, 1]], 1, 0.5, 0.4, 800, 500)]
        self.assertIn("Volumen = |det| = 2", textos)


class MenuDeConsola(unittest.TestCase):
    """Opción 5 del menú principal con las cuatro opciones del módulo."""

    def test_menu_y_teoremas(self):
        """Comprueba la opción del menú principal, el logotipo y los teoremas del módulo."""
        self.assertIn(("5", "Métodos numéricos"), main.OPCIONES_MENU_PRINCIPAL)
        _, texto = sesion_consola(main.menu_metodos_numericos, ["0", "V"])
        self.assertIn(LOGO_NUMERICOS, texto)
        self.assertTrue(all(titulo in texto for titulo, _ in TEOREMAS_NUMERICOS))

    def test_cuatro_opciones_con_reentrada(self):
        """Comprueba las cuatro opciones de consola y que los datos inválidos se vuelven a pedir."""
        informe, texto = sesion_consola(main.ejecutar_biseccion, ["x^3 - x - 2", "abc", "1", "2", ""])
        self.assertTrue(informe["verificacion"]["correcto"])
        self.assertIn("Error:", texto)
        self.assertIn("  n               a", texto)
        informe, texto = sesion_consola(main.ejecutar_graficador, ["sen(x)", "", ""])
        self.assertIn("*", texto)
        informe, texto = sesion_consola(main.ejecutar_posicional, ["7", "2", "102", "1101.101"])
        self.assertEqual(informe["decimal"], "13.625")
        self.assertEqual(texto.count("Error:"), 2)
        informe, _ = sesion_consola(main.ejecutar_errores, ["pi", "3.14", "4"])
        self.assertEqual(informe["cifras_correctas"], 3)


class InterfazGrafica(unittest.TestCase):
    """Páginas «Métodos numéricos» y «Renders y animaciones» con widgets reales."""

    @classmethod
    def setUpClass(cls):
        """Carga la GUI una vez para todas las pruebas de la clase."""
        cls.gui = main.cargar_aplicacion()

    def test_paginas_nuevas_con_widgets_reales(self):
        """Comprueba las cuatro opciones, los cinco modos de render, el zoom, el encadenamiento y la exportación a PNG."""
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
        try:
            pagina = app.ir_a("numericos")
            for nombre in ("1. Bisección", "2. Graficador", "3. Notación posicional", "4. Errores numéricos"):
                with self.subTest(opcion=nombre):
                    pagina.cambiar_opcion(nombre)
                    pagina.resolver()
                    bombear(0.3)
                    self.assertTrue(pagina.opcion.informe["definido"])
                    self.assertTrue(pagina.opcion.informe["verificacion"]["correcto"])
                    self.assertTrue(pagina.panel_pasos.pasos)
            pagina.cambiar_opcion("2. Graficador")
            lienzo = pagina.opcion.lienzo
            ancho = lienzo.vista.x_max - lienzo.vista.x_min
            lienzo.al_girar_rueda(-120, False, lienzo.winfo_rootx() + 200, lienzo.winfo_rooty() + 150)
            self.assertLess(lienzo.vista.x_max - lienzo.vista.x_min, ancho)
            pagina.cambiar_opcion("1. Bisección")
            pagina.opcion.cargar_ejemplo("Sin cambio de signo: x² + 1")
            bombear(0.2)
            self.assertFalse(pagina.opcion.informe["definido"])

            renders = app.ir_a("renders")
            for modo in renders.MODOS:
                with self.subTest(modo=modo):
                    renders.cambiar_modo(modo)
                    renders.reproductor.fijar(1.0)
                    bombear(0.1)
                    self.assertGreater(len(renders._escena(800, 500)), 10)
            with tempfile.TemporaryDirectory() as carpeta:
                ruta = Path(carpeta) / "render.png"
                self.gui.renderizar_png(renders._escena(400, 300), 400, 300, str(ruta))
                self.assertEqual(ruta.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

            determinantes = app.ir_a("determinantes")
            determinantes.resolver()
            app.ir_a("renders").cargar_transformacion([[0, 1], [1, 0]])
            bombear(0.2)
            self.assertEqual(renders.modo.get(), "Transformación del plano (2×2)")
            self.assertIn("orientación", renders.explicacion.cget("text"))
            app.ir_a("renders").cargar_sistema([[1, 1, 1], [2, -1, 1], [1, 2, -1]], [6, 3, 2])
            bombear(0.2)
            self.assertIn("(1, 2, 3)", renders.explicacion.cget("text"))
            self.assertEqual(errores, [])
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()

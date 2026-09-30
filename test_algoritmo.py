import importlib.util
import pathlib
import unittest
from fractions import Fraction


RUTA_PROGRAMA = pathlib.Path(__file__).with_name("Programa 1_Grupo3.py")
spec = importlib.util.spec_from_file_location("programa_algebra", RUTA_PROGRAMA)
programa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(programa)


class PruebasEliminacionPorFilas(unittest.TestCase):
    def test_sistema_consistente_determinado(self):
        A = [
            [Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(2), Fraction(-1), Fraction(1)],
            [Fraction(1), Fraction(2), Fraction(-1)],
        ]
        b = [Fraction(6), Fraction(2), Fraction(7)]

        resultado = programa.resolver_sistema(A, b)

        self.assertEqual(resultado["clasificacion"], "Sistema consistente determinado")
        self.assertEqual(resultado["solucion"], [Fraction(2), Fraction(3), Fraction(1)])
        self.assertTrue(resultado["verificacion"][0])

    def test_sistema_consistente_indeterminado(self):
        A = [
            [Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(2), Fraction(2), Fraction(2)],
        ]
        b = [Fraction(2), Fraction(4)]

        resultado = programa.resolver_sistema(A, b)

        self.assertEqual(resultado["clasificacion"], "Sistema consistente indeterminado")
        self.assertEqual(resultado["variables_libres"], [1, 2])
        self.assertTrue(resultado["verificacion"][0])

    def test_sistema_inconsistente(self):
        A = [
            [Fraction(1), Fraction(1)],
            [Fraction(1), Fraction(1)],
        ]
        b = [Fraction(2), Fraction(5)]

        resultado = programa.resolver_sistema(A, b)

        self.assertEqual(resultado["clasificacion"], "Sistema inconsistente")
        self.assertIsNone(resultado["verificacion"])

    def test_intercambio_por_pivote_cero(self):
        A = [
            [Fraction(0), Fraction(1)],
            [Fraction(2), Fraction(3)],
        ]
        b = [Fraction(4), Fraction(5)]

        resultado = programa.resolver_sistema(A, b)

        self.assertEqual(resultado["clasificacion"], "Sistema consistente determinado")
        operaciones = [paso["operacion"] for paso in resultado["pasos"]]
        self.assertTrue(any("F1 ↔ F2" in op or "F1 <-> F2" in op for op in operaciones))
        self.assertTrue(resultado["verificacion"][0])

    def test_caso1_prompt_solucion_unica(self):
        A = [
            [Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(2), Fraction(-1), Fraction(1)],
            [Fraction(1), Fraction(2), Fraction(-1)],
        ]
        b = [Fraction(6), Fraction(3), Fraction(2)]

        resultado = programa.resolver_sistema(A, b)

        self.assertEqual(resultado["clasificacion"], "Sistema consistente determinado")
        self.assertEqual(resultado["solucion"], [Fraction(1), Fraction(2), Fraction(3)])
        self.assertTrue(resultado["verificacion"][0])

    def test_caso2_prompt_infinitas_soluciones(self):
        A = [
            [Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(2), Fraction(2), Fraction(2)],
            [Fraction(1), Fraction(-1), Fraction(1)],
        ]
        b = [Fraction(6), Fraction(12), Fraction(2)]

        resultado = programa.resolver_sistema(A, b)

        self.assertEqual(resultado["clasificacion"], "Sistema consistente indeterminado")
        self.assertEqual(resultado["variables_libres"], [2])
        self.assertEqual(resultado["expresiones"][0], "4 - t")
        self.assertEqual(resultado["expresiones"][1], "2")
        self.assertEqual(resultado["expresiones"][2], "t")
        self.assertTrue(resultado["verificacion"][0])

    def test_caso3_prompt_inconsistente(self):
        A = [
            [Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(2), Fraction(2), Fraction(2)],
            [Fraction(1), Fraction(1), Fraction(1)],
        ]
        b = [Fraction(3), Fraction(6), Fraction(5)]

        resultado = programa.resolver_sistema(A, b)

        self.assertEqual(resultado["clasificacion"], "Sistema inconsistente")
        self.assertIsNone(resultado["verificacion"])

    def test_estructura_y_explicacion_pasos(self):
        A = [
            [Fraction(1), Fraction(2), Fraction(3)],
            [Fraction(3), Fraction(1), Fraction(-1)],
            [Fraction(2), Fraction(-3), Fraction(-4)],
        ]
        b = [Fraction(16), Fraction(1), Fraction(3)]

        resultado = programa.resolver_sistema(A, b)
        pasos = resultado["pasos"]

        self.assertGreater(len(pasos), 1)
        self.assertEqual(pasos[0]["operacion"], "Matriz aumentada inicial")
        self.assertIn("coeficientes", pasos[0]["explicacion"])

        # Verificar que todos los pasos contengan operacion, explicacion y matriz
        for paso in pasos:
            self.assertIn("operacion", paso)
            self.assertIn("explicacion", paso)
            self.assertIn("matriz", paso)
            self.assertTrue(len(paso["explicacion"]) > 0)
            self.assertTrue(len(paso["matriz"]) > 0)

    def test_verificacion_detallada_sustitucion_y_simplificacion(self):
        A = [
            [Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(2), Fraction(-1), Fraction(1)],
            [Fraction(1), Fraction(2), Fraction(-1)],
        ]
        b = [Fraction(6), Fraction(3), Fraction(2)]
        sol = [Fraction(1), Fraction(2), Fraction(3)]

        correcta, detalles = programa.verificar_solucion(A, b, sol)

        self.assertTrue(correcta)
        self.assertEqual(len(detalles), 3)

        # Ecuacion 1: x1 + x2 + x3 = 6
        self.assertEqual(detalles[0].ecuacion_original, "x1 + x2 + x3 = 6")
        self.assertEqual(detalles[0].sustitucion, "(1) + (2) + (3) = 6")
        self.assertEqual(detalles[0].simplificacion, ["1 + 2 + 3 = 6", "6 = 6"])
        self.assertTrue(detalles[0].coincide)

        # Ecuacion 2: 2x1 - x2 + x3 = 3
        self.assertEqual(detalles[1].ecuacion_original, "2x1 - x2 + x3 = 3")
        self.assertEqual(detalles[1].sustitucion, "2(1) - (2) + (3) = 3")
        self.assertEqual(detalles[1].simplificacion, ["2 - 2 + 3 = 3", "3 = 3"])
        self.assertTrue(detalles[1].coincide)

        # Ecuacion 3: x1 + 2x2 - x3 = 2
        self.assertEqual(detalles[2].ecuacion_original, "x1 + 2x2 - x3 = 2")
        self.assertEqual(detalles[2].sustitucion, "(1) + 2(2) - (3) = 2")
        self.assertEqual(detalles[2].simplificacion, ["1 + 4 - 3 = 2", "2 = 2"])
        self.assertTrue(detalles[2].coincide)

    def test_verificacion_con_solucion_incorrecta(self):
        A = [[Fraction(2), Fraction(-3), Fraction(1)]]
        b = [Fraction(7)]
        sol_falsa = [Fraction(1), Fraction(2), Fraction(4)]  # 2(1) - 3(2) + 4 = 0 != 7

        correcta, detalles = programa.verificar_solucion(A, b, sol_falsa)

        self.assertFalse(correcta)
        self.assertEqual(detalles[0].ecuacion_original, "2x1 - 3x2 + x3 = 7")
        self.assertEqual(detalles[0].sustitucion, "2(1) - 3(2) + (4) = 7")
        self.assertEqual(detalles[0].simplificacion, ["2 - 6 + 4 = 7", "0 = 7"])
        self.assertFalse(detalles[0].coincide)

    # -------------------------------------------------------------------------
    # Pruebas obligatorias requeridas por la auditoría y entrega
    # -------------------------------------------------------------------------

    def test_obligatorio_test1_2x2(self):
        """TEST 1 — 2x2: 2 ecuaciones, 2 variables. Sigue funcionando tras quitar boton 2x2."""
        A = [
            [Fraction(2), Fraction(1)],
            [Fraction(1), Fraction(-1)],
        ]
        b = [Fraction(5), Fraction(1)]

        resultado = programa.resolver_sistema(A, b)

        self.assertEqual(resultado["clasificacion"], "Sistema consistente determinado")
        self.assertEqual(resultado["solucion"], [Fraction(2), Fraction(1)])
        self.assertEqual(resultado["nombres_variables"], ["x1", "x2"])
        self.assertTrue(resultado["verificacion"][0])
        # Comprobar sustitución de la primera ecuación
        detalles = resultado["verificacion"][1]
        self.assertEqual(detalles[0].ecuacion_original, "2x1 + x2 = 5")
        self.assertEqual(detalles[0].sustitucion, "2(2) + (1) = 5")
        self.assertTrue(detalles[0].coincide)

    def test_obligatorio_test2_2x4(self):
        """
        TEST 2 — 2x4:
        1 2 0 1 | 5
        0 1 1 2 | 4
        Debe producir:
        x1 = -3 + 2s + 3t
        x2 = 4 - s - 2t
        x3 = s
        x4 = t
        Consistente indeterminado con infinitas soluciones.
        """
        A = [
            [Fraction(1), Fraction(2), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(1), Fraction(1), Fraction(2)],
        ]
        b = [Fraction(5), Fraction(4)]

        resultado = programa.resolver_sistema(A, b)

        self.assertEqual(resultado["clasificacion"], "Sistema consistente indeterminado")
        self.assertEqual(resultado["nombres_variables"], ["x1", "x2", "x3", "x4"])
        self.assertEqual(resultado["variables_basicas"], [0, 1])
        self.assertEqual(resultado["variables_libres"], [2, 3])
        self.assertEqual(resultado["parametros"], {2: "s", 3: "t"})

        self.assertEqual(resultado["expresiones"][0], "-3 + 2s + 3t")
        self.assertEqual(resultado["expresiones"][1], "4 - s - 2t")
        self.assertEqual(resultado["expresiones"][2], "s")
        self.assertEqual(resultado["expresiones"][3], "t")

        self.assertTrue(resultado["verificacion"][0])
        detalles = resultado["verificacion"][1]
        self.assertEqual(detalles[0].ecuacion_original, "x1 + 2x2 + x4 = 5")
        self.assertEqual(detalles[1].ecuacion_original, "x2 + x3 + 2x4 = 4")

    def test_obligatorio_test3_3x3_unica_solucion(self):
        """
        TEST 3 — 3x3 única solución:
        1 1 1 | 6
        2 -1 1 | 3
        1 2 -1 | 2
        Resultado: x1 = 1, x2 = 2, x3 = 3
        """
        A = [
            [Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(2), Fraction(-1), Fraction(1)],
            [Fraction(1), Fraction(2), Fraction(-1)],
        ]
        b = [Fraction(6), Fraction(3), Fraction(2)]

        resultado = programa.resolver_sistema(A, b)

        self.assertEqual(resultado["clasificacion"], "Sistema consistente determinado")
        self.assertEqual(resultado["solucion"], [Fraction(1), Fraction(2), Fraction(3)])
        self.assertEqual(resultado["nombres_variables"], ["x1", "x2", "x3"])
        self.assertTrue(resultado["verificacion"][0])

    def test_obligatorio_test4_infinitas_soluciones(self):
        """
        TEST 4 — infinitas soluciones:
        1 1 1 | 6
        2 2 2 | 12
        1 -1 1 | 2
        """
        A = [
            [Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(2), Fraction(2), Fraction(2)],
            [Fraction(1), Fraction(-1), Fraction(1)],
        ]
        b = [Fraction(6), Fraction(12), Fraction(2)]

        resultado = programa.resolver_sistema(A, b)

        self.assertEqual(resultado["clasificacion"], "Sistema consistente indeterminado")
        self.assertEqual(resultado["variables_libres"], [2])
        self.assertEqual(resultado["parametros"], {2: "t"})
        self.assertEqual(resultado["expresiones"][0], "4 - t")
        self.assertEqual(resultado["expresiones"][1], "2")
        self.assertEqual(resultado["expresiones"][2], "t")
        self.assertTrue(resultado["verificacion"][0])

    def test_obligatorio_test5_inconsistente(self):
        """
        TEST 5 — inconsistente:
        1 1 1 | 3
        2 2 2 | 6
        1 1 1 | 5
        """
        A = [
            [Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(2), Fraction(2), Fraction(2)],
            [Fraction(1), Fraction(1), Fraction(1)],
        ]
        b = [Fraction(3), Fraction(6), Fraction(5)]

        resultado = programa.resolver_sistema(A, b)

        self.assertEqual(resultado["clasificacion"], "Sistema inconsistente")
        self.assertIsNone(resultado["solucion"])
        self.assertIsNone(resultado["verificacion"])

    def test_obligatorio_test6_pivote_inicial_cero(self):
        """
        TEST 6 — pivote inicial cero:
        0 1 2 | 5
        1 2 3 | 8
        2 1 1 | 6
        Debe intercambiar filas y resolver correctamente.
        """
        A = [
            [Fraction(0), Fraction(1), Fraction(2)],
            [Fraction(1), Fraction(2), Fraction(3)],
            [Fraction(2), Fraction(1), Fraction(1)],
        ]
        b = [Fraction(5), Fraction(8), Fraction(6)]

        resultado = programa.resolver_sistema(A, b)

        self.assertEqual(resultado["clasificacion"], "Sistema consistente determinado")
        self.assertEqual(resultado["solucion"], [Fraction(3), Fraction(-5), Fraction(5)])
        operaciones = [paso["operacion"] for paso in resultado["pasos"]]
        self.assertTrue(any("F1 ↔ F2" in op or "F1 ↔ F3" in op for op in operaciones))
        self.assertTrue(resultado["verificacion"][0])

    def test_obligatorio_test7_sistema_homogeneo(self):
        """
        TEST 7 — sistema homogéneo:
        1 2 3 | 0
        2 4 6 | 0
        1 1 1 | 0
        Identifica homogéneo y consistente con infinitas soluciones.
        """
        A = [
            [Fraction(1), Fraction(2), Fraction(3)],
            [Fraction(2), Fraction(4), Fraction(6)],
            [Fraction(1), Fraction(1), Fraction(1)],
        ]
        b = [Fraction(0), Fraction(0), Fraction(0)]

        resultado = programa.resolver_sistema(A, b)

        self.assertTrue(resultado["homogeneo"])
        self.assertEqual(resultado["clasificacion"], "Sistema consistente indeterminado")
        self.assertTrue(resultado["verificacion"][0])

    def test_sistemas_rectangulares_adicionales(self):
        """Verifica compatibilidad con otras matrices rectangulares m != n (3x5, 4x3, 5x4)."""
        # 4x3 determinado
        A_4x3 = [
            [Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(2), Fraction(-1), Fraction(1)],
            [Fraction(1), Fraction(2), Fraction(-1)],
            [Fraction(3), Fraction(0), Fraction(2)],
        ]
        b_4x3 = [Fraction(6), Fraction(3), Fraction(2), Fraction(9)]
        res_4x3 = programa.resolver_sistema(A_4x3, b_4x3)
        self.assertEqual(res_4x3["clasificacion"], "Sistema consistente determinado")
        self.assertEqual(res_4x3["solucion"], [Fraction(1), Fraction(2), Fraction(3)])
        self.assertTrue(res_4x3["verificacion"][0])

        # 3x5 indeterminado
        A_3x5 = [
            [Fraction(1), Fraction(0), Fraction(0), Fraction(1), Fraction(2)],
            [Fraction(0), Fraction(1), Fraction(0), Fraction(2), Fraction(1)],
            [Fraction(0), Fraction(0), Fraction(1), Fraction(1), Fraction(1)],
        ]
        b_3x5 = [Fraction(3), Fraction(4), Fraction(5)]
        res_3x5 = programa.resolver_sistema(A_3x5, b_3x5)
        self.assertEqual(res_3x5["clasificacion"], "Sistema consistente indeterminado")
        self.assertEqual(res_3x5["variables_libres"], [3, 4])
        self.assertEqual(res_3x5["parametros"], {3: "s", 4: "t"})
        self.assertEqual(res_3x5["expresiones"][0], "3 - s - 2t")
        self.assertEqual(res_3x5["expresiones"][1], "4 - 2s - t")
        self.assertEqual(res_3x5["expresiones"][2], "5 - s - t")
        self.assertEqual(res_3x5["expresiones"][3], "s")
        self.assertEqual(res_3x5["expresiones"][4], "t")
        self.assertTrue(res_3x5["verificacion"][0])


class PruebasEntradaYFormato(unittest.TestCase):
    def test_convertir_numero_formatos_aceptados(self):
        self.assertEqual(programa.convertir_numero(" 3/2 "), Fraction(3, 2))
        self.assertEqual(programa.convertir_numero("2,5"), Fraction(5, 2))
        self.assertEqual(programa.convertir_numero("0.25"), Fraction(1, 4))
        self.assertEqual(programa.convertir_numero("−3"), Fraction(-3))

    def test_convertir_numero_errores_en_espanol(self):
        with self.assertRaisesRegex(ValueError, "vacía"):
            programa.convertir_numero("  ")
        with self.assertRaisesRegex(ValueError, "no es un número válido"):
            programa.convertir_numero("abc")
        with self.assertRaisesRegex(ValueError, "división entre cero"):
            programa.convertir_numero("1/0")

    def test_coeficientes_fraccionarios_entre_parentesis(self):
        fila = [Fraction(1, 2), Fraction(-1)]
        self.assertEqual(
            programa.formatear_ecuacion_original(fila, Fraction(1), ["x1", "x2"]),
            "(1/2)x1 - x2 = 1",
        )
        self.assertEqual(
            programa.formatear_sustitucion(fila, Fraction(1), [Fraction(4), Fraction(1)]),
            "(1/2)(4) - (1) = 1",
        )

    def test_parametro_con_coeficiente_fraccionario(self):
        resultado = programa.resolver_sistema([[Fraction(2), Fraction(1)]], [Fraction(4)])
        self.assertEqual(resultado["expresiones"][0], "2 - (1/2)t")

    def test_formatear_combinacion_lineal(self):
        texto = programa.formatear_combinacion_lineal(
            [Fraction(2), Fraction(-1), Fraction(0), Fraction(1, 2)], ["v1", "v2", "v3", "v4"]
        )
        self.assertEqual(texto, "2·v1 - v2 + (1/2)·v4")


class PruebasGaussJordanDetallado(unittest.TestCase):
    def test_no_intercambia_si_el_pivote_no_es_cero(self):
        A = [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]]
        b = [Fraction(5), Fraction(6)]
        resultado = programa.resolver_sistema(A, b)
        operaciones = [paso["operacion"] for paso in resultado["pasos"]]
        self.assertFalse(any("↔" in op for op in operaciones))
        self.assertEqual(resultado["solucion"], [Fraction(-4), Fraction(9, 2)])

    def test_pasos_guardan_filas_y_pivotes(self):
        A = [[Fraction(1), Fraction(1)], [Fraction(2), Fraction(-1)]]
        b = [Fraction(3), Fraction(0)]
        pasos = programa.resolver_sistema(A, b)["pasos"]
        eliminacion = next(p for p in pasos if p["tipo"] == "eliminacion")
        self.assertEqual(eliminacion["filas"], [1])
        self.assertEqual(eliminacion["fila_origen"], 0)
        self.assertEqual(eliminacion["pivotes"], [(0, 0)])
        self.assertEqual(eliminacion.operacion, "F2 → F2 - 2F1")
        self.assertEqual(pasos[-1]["tipo"], "final")
        self.assertEqual(pasos[-1]["pivotes"], [(0, 0), (1, 1)])

    def test_rango_de_sistema_inconsistente(self):
        A = [[Fraction(1), Fraction(1)], [Fraction(1), Fraction(1)]]
        b = [Fraction(2), Fraction(5)]
        resultado = programa.resolver_sistema(A, b)
        self.assertEqual(resultado["rango"], 1)
        self.assertEqual(resultado["rango_aumentada"], 2)
        self.assertEqual(resultado["filas_inconsistentes"], [1])

    def test_forma_vectorial_parametrica(self):
        A = [
            [Fraction(1), Fraction(2), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(1), Fraction(1), Fraction(2)],
        ]
        b = [Fraction(5), Fraction(4)]
        particular, direcciones = programa.resolver_sistema(A, b)["forma_vectorial"]
        self.assertEqual(particular, [-3, 4, 0, 0])
        self.assertEqual(direcciones, [("s", [2, -1, 1, 0]), ("t", [3, -2, 0, 1])])
        # Cada vector direccion resuelve el sistema homogeneo A·v = 0.
        for _, vector in direcciones:
            self.assertEqual(programa.multiplicar_matriz_vector(A, vector), [0, 0])

    def test_sistema_aleatorio_es_consistente(self):
        import random
        generador = random.Random(7)
        for _ in range(20):
            A, b = programa.sistema_aleatorio(3, 4, generador)
            A = [[Fraction(v) for v in fila] for fila in A]
            resultado = programa.resolver_sistema(A, [Fraction(v) for v in b])
            self.assertNotEqual(resultado["clasificacion"], "Sistema inconsistente")


class PruebasOtrasSecciones(unittest.TestCase):
    def test_independencia_dependientes_con_relacion(self):
        A = [
            [Fraction(1), Fraction(4), Fraction(7)],
            [Fraction(2), Fraction(5), Fraction(8)],
            [Fraction(3), Fraction(6), Fraction(9)],
        ]
        resultado = programa.analizar_independencia(A)
        self.assertFalse(resultado["independiente"])
        relacion = resultado["relacion"]
        self.assertTrue(any(c != 0 for c in relacion))
        self.assertTrue(all(c.denominator == 1 for c in relacion))
        self.assertEqual(programa.multiplicar_matriz_vector(A, relacion), [0, 0, 0])
        self.assertEqual(resultado["nombres_variables"], ["c1", "c2", "c3"])

    def test_independencia_base_canonica(self):
        A = [[Fraction(int(i == j)) for j in range(3)] for i in range(3)]
        resultado = programa.analizar_independencia(A)
        self.assertTrue(resultado["independiente"])
        self.assertIsNone(resultado["relacion"])
        self.assertEqual(resultado["observaciones"], [])

    def test_independencia_observaciones(self):
        A = [[Fraction(1), Fraction(0), Fraction(2)], [Fraction(0), Fraction(0), Fraction(3)]]
        resultado = programa.analizar_independencia(A)
        self.assertFalse(resultado["independiente"])
        texto = " ".join(resultado["observaciones"])
        self.assertIn("más vectores que componentes", texto)
        self.assertIn("v2 es el vector cero", texto)

    def test_forma_escalonada_por_filas(self):
        A = [
            [Fraction(1), Fraction(4), Fraction(7)],
            [Fraction(2), Fraction(5), Fraction(8)],
            [Fraction(3), Fraction(6), Fraction(9)],
        ]
        homogenea = programa.crear_matriz_aumentada(A, [Fraction(0)] * 3)
        escalonada, columnas_pivote, pasos = programa.forma_escalonada(homogenea, 3)
        self.assertEqual(escalonada, [[1, 4, 7, 0], [0, -3, -6, 0], [0, 0, 0, 0]])
        self.assertEqual(columnas_pivote, [0, 1])
        # Solo eliminacion hacia abajo: no hay escalamientos y los pivotes no se vuelven 1.
        self.assertNotIn("escalado", [p["tipo"] for p in pasos])
        self.assertEqual(pasos[-1]["operacion"], "Forma escalonada por filas")

    def test_forma_escalonada_con_pivote_cero(self):
        matriz = [[Fraction(0), Fraction(2), Fraction(0)], [Fraction(3), Fraction(1), Fraction(0)]]
        escalonada, columnas_pivote, pasos = programa.forma_escalonada(matriz, 2)
        self.assertEqual(escalonada, [[3, 1, 0], [0, 2, 0]])
        self.assertEqual(pasos[1]["operacion"], "F1 ↔ F2")
        self.assertEqual(columnas_pivote, [0, 1])

    def test_independencia_pivotes_y_veredicto(self):
        dependientes = programa.analizar_independencia(
            [[Fraction(1), Fraction(4), Fraction(7)],
             [Fraction(2), Fraction(5), Fraction(8)],
             [Fraction(3), Fraction(6), Fraction(9)]])
        self.assertEqual(dependientes["num_pivotes"], 2)
        self.assertEqual(dependientes["num_libres"], 1)
        self.assertEqual(dependientes["nombres_libres"], ["c3"])
        self.assertEqual(dependientes["veredicto"], "Linealmente Dependiente (L.D.)")
        self.assertEqual([fila[-1] for fila in dependientes["matriz_homogenea"]], [0, 0, 0])

        independientes = programa.analizar_independencia(
            [[Fraction(1), Fraction(0)], [Fraction(2), Fraction(1)], [Fraction(0), Fraction(3)]])
        self.assertEqual(independientes["num_pivotes"], 2)
        self.assertEqual(independientes["num_libres"], 0)
        self.assertEqual(independientes["veredicto"], "Linealmente Independiente (L.I.)")

    def test_modo_consola(self):
        import contextlib
        import io
        respuestas = iter(["3", "abc", "3", "1 2 3", "4 5 6", "7 8", "7 8 9"])
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            resultado = programa.independencia_consola(entrada=lambda _mensaje: next(respuestas))
        texto = salida.getvalue()
        self.assertFalse(resultado["independiente"])
        self.assertIn("se esperaban 3 componentes", texto)
        self.assertIn("Forma escalonada por filas:", texto)
        self.assertIn("Número de pivotes: 2", texto)
        self.assertIn("Veredicto: Linealmente Dependiente (L.D.)", texto)

    def test_producto_av_por_columnas(self):
        # Ejemplo de Lay 1.4: A = [a1 a2 a3], v = (4, 3, 7) -> Av = 4a1 + 3a2 + 7a3 = (3, 6)
        A = [[Fraction(1), Fraction(2), Fraction(-1)], [Fraction(0), Fraction(-5), Fraction(3)]]
        v = [Fraction(4), Fraction(3), Fraction(7)]
        datos = programa.analizar_producto_av(A, v, Fraction(2))
        self.assertEqual(datos["columnas"], [[1, 0], [2, -5], [-1, 3]])
        self.assertEqual(datos["combinacion"], "4·a1 + 3·a2 + 7·a3")
        self.assertEqual(datos["terminos"], [[4, 0], [6, -15], [-7, 21]])
        self.assertEqual(datos["Av"], [3, 6])
        suma = [sum(t[i] for t in datos["terminos"]) for i in range(2)]
        self.assertEqual(suma, datos["Av"])
        self.assertEqual(datos["A_cv"], [6, 12])
        self.assertTrue(datos["propiedad"])

    def test_producto_av_con_u(self):
        A = [[Fraction(1), Fraction(2), Fraction(-1)], [Fraction(0), Fraction(-5), Fraction(3)]]
        v = [Fraction(4), Fraction(3), Fraction(7)]
        u = [Fraction(2), Fraction(0), Fraction(-1)]
        datos = programa.analizar_producto_av(A, v, Fraction(2), u)
        self.assertEqual(datos["Au"], [3, -3])
        self.assertEqual(datos["combinacion_u"], "2·a1 - a3")
        self.assertEqual(datos["u_mas_v"], [6, 3, 6])
        self.assertEqual(datos["A_u_mas_v"], [6, 3])
        self.assertEqual(datos["Au_mas_Av"], [6, 3])
        self.assertTrue(datos["propiedad_suma"])
        # Sin u no se calcula la propiedad de la suma.
        self.assertIsNone(programa.analizar_producto_av(A, v, Fraction(2))["propiedad_suma"])

    def test_producto_av_dimension_incorrecta(self):
        A = [[Fraction(1), Fraction(2)]]
        with self.assertRaisesRegex(ValueError, "una componente por cada columna"):
            programa.analizar_producto_av(A, [Fraction(1)], Fraction(2))

    def test_detalle_producto_matriz_vector(self):
        A = [[Fraction(1), Fraction(2)], [Fraction(0), Fraction(-3)]]
        x = [Fraction(1), Fraction(-1)]
        self.assertEqual(
            programa.detalle_producto_matriz_vector(A, x),
            ["Fila 1:  (1) + 2(-1) = -1", "Fila 2:  -3(-1) = 3"],
        )


class PruebasOperacionesMatrices(unittest.TestCase):
    """Cobertura académica del módulo Operaciones con Matrices."""

    A = [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]]
    B = [[Fraction(5), Fraction(6)], [Fraction(7), Fraction(8)]]

    def test_suma_resta_y_dimension_incompatible(self):
        self.assertEqual(programa.sumar_matrices(self.A, self.B), [[6, 8], [10, 12]])
        self.assertEqual(programa.restar_matrices(self.A, self.B), [[-4, -4], [-4, -4]])
        with self.assertRaisesRegex(ValueError, "dimensiones"):
            programa.sumar_matrices([[1, 2]], [[1], [2]])

    def test_escalar_cero_negativo_y_fraccionario(self):
        self.assertEqual(programa.multiplicar_matriz_escalar(0, self.A), [[0, 0], [0, 0]])
        self.assertEqual(programa.multiplicar_matriz_escalar(-2, self.A), [[-2, -4], [-6, -8]])
        self.assertEqual(programa.multiplicar_matriz_escalar(Fraction(1, 2), self.A), [[Fraction(1, 2), 1], [Fraction(3, 2), 2]])

    def test_transpuesta_y_producto_rectangular(self):
        self.assertEqual(programa.transponer_matriz([[1, 2, 3], [4, 5, 6]]), [[1, 4], [2, 5], [3, 6]])
        self.assertEqual(programa.multiplicar_matrices([[1, 2, 3], [4, 5, 6]], [[1, 2], [3, 4], [5, 6]]), [[22, 28], [49, 64]])
        with self.assertRaisesRegex(ValueError, "no está definido"):
            programa.multiplicar_matrices([[1, 2]], [[1, 2]])

    def test_procedimientos_son_reales_y_entrada_por_entrada(self):
        dato = programa.procedimiento_operacion_matrices(self.A, "producto", self.B)
        self.assertEqual(dato["resultado"], [[19, 22], [43, 50]])
        self.assertTrue(any("(AB)1,1" in paso and "1·5 + 2·7" in paso for paso in dato["pasos"]))
        self.assertIn("2×2", dato["conclusion"])

    def test_cuatro_propiedades_de_transpuesta(self):
        datos = programa.verificar_propiedades_transpuesta(self.A, self.B, Fraction(-3, 2))
        self.assertTrue(datos["doble"]["coinciden"])
        self.assertTrue(datos["suma"]["coinciden"])
        self.assertTrue(datos["escalar"]["coinciden"])
        self.assertTrue(datos["producto"]["coinciden"])
        self.assertEqual(datos["producto"]["izquierda"], [[19, 43], [22, 50]])

    def test_propiedades_algebraicas_e_identidad(self):
        datos = programa.verificar_propiedades_algebraicas(self.A, self.B, programa.matriz_identidad(2), Fraction(2), Fraction(-1))
        for clave in ("asociatividad_suma", "conmutatividad_suma", "cero_aditivo", "inverso_aditivo", "asociatividad_producto", "distributividad_izquierda", "distributividad_derecha", "identidad_derecha", "identidad_izquierda", "distributividad_escalar", "suma_escalares", "producto_escalares"):
            self.assertTrue(datos[clave]["coinciden"], clave)

    def test_comparacion_muestra_diferencias(self):
        dato = programa.comparar_matrices([[1, 2]], [[1, 3]])
        self.assertFalse(dato["coinciden"])
        self.assertEqual(dato["diferencias"], [(1, 2, Fraction(2), Fraction(3))])

    def test_contraejemplos_validos(self):
        datos = programa.contraejemplos_matriciales()
        self.assertNotEqual(datos["no_conmutatividad"]["AB"], datos["no_conmutatividad"]["BA"])
        self.assertEqual(datos["cancelacion"]["AB"], datos["cancelacion"]["AC"])
        self.assertNotEqual(datos["cancelacion"]["B"], datos["cancelacion"]["C"])
        self.assertEqual(datos["divisores_cero"]["AB"], [[0, 0], [0, 0]])
        with self.assertRaises(ValueError):
            programa.multiplicar_matrices(datos["orden_rectangular"]["B"], datos["orden_rectangular"]["A"])
        ejercicios = programa.ejercicios_matrices()
        self.assertGreaterEqual(len(ejercicios), 5)
        self.assertTrue(any(ejercicio["tema"] == "Producto rectangular" for ejercicio in ejercicios))


if __name__ == "__main__":
    unittest.main()


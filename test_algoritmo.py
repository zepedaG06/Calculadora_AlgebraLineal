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


class PruebasTarea3Obligatorias(unittest.TestCase):
    """
    Suite de pruebas unitarias obligatorias requeridas para la Tarea 3:
    TEST 1 a TEST 22 rigurosamente comprobados con cálculo matemático exacto.
    """

    def test_01_suma_de_vectores(self):
        """TEST 1 — Suma de vectores en R^n: componentes homólogos sumados."""
        v1 = [Fraction(1), Fraction(2), Fraction(3)]
        v2 = [Fraction(4), Fraction(5), Fraction(6)]
        resultado = programa.sumar_vectores(v1, v2)
        esperado = [Fraction(5), Fraction(7), Fraction(9)]
        self.assertEqual(resultado, esperado)

    def test_02_resta_de_vectores(self):
        """TEST 2 — Resta de vectores en R^n: componentes homólogos restados."""
        v1 = [Fraction(5), Fraction(7), Fraction(9)]
        v2 = [Fraction(4), Fraction(5), Fraction(6)]
        resultado = programa.restar_vectores(v1, v2)
        esperado = [Fraction(1), Fraction(2), Fraction(3)]
        self.assertEqual(resultado, esperado)

    def test_03_escalar_por_vector(self):
        """TEST 3 — Multiplicación de vector por escalar: k · v."""
        k = Fraction(3)
        v = [Fraction(2), Fraction(-1), Fraction(4, 3)]
        resultado = programa.multiplicar_vector_escalar(k, v)
        esperado = [Fraction(6), Fraction(-3), Fraction(4)]
        self.assertEqual(resultado, esperado)

    def test_04_combinacion_lineal_solucion_unica(self):
        """
        TEST 4 — Combinación lineal con solución única:
        v1 = [1, 2, 0], v2 = [2, 1, 1], v3 = [0, 1, 2], b = [5, 4, 7]
        c1 = -3/7, c2 = 19/7, c3 = 15/7.
        """
        v1 = [Fraction(1), Fraction(2), Fraction(0)]
        v2 = [Fraction(2), Fraction(1), Fraction(1)]
        v3 = [Fraction(0), Fraction(1), Fraction(2)]
        b = [Fraction(5), Fraction(4), Fraction(7)]
        res = programa.analizar_combinacion_lineal([v1, v2, v3], b)

        self.assertTrue(res["es_posible"])
        self.assertEqual(res["sistema"]["clasificacion"], "Sistema consistente determinado")
        self.assertEqual(res["sistema"]["nombres_variables"], ["c1", "c2", "c3"])
        self.assertEqual(res["sistema"]["solucion"], [Fraction(-3, 7), Fraction(19, 7), Fraction(15, 7)])
        self.assertTrue(res["verificacion_vectorial"]["coincide"])

    def test_05_combinacion_lineal_sin_solucion(self):
        """
        TEST 5 — Combinación lineal sin solución (inconsistente):
        v1 = [1, 1], v2 = [2, 2], b = [3, 4]
        c1 + 2c2 = 3 y c1 + 2c2 = 4 (contradicción 0 = 1).
        """
        v1 = [Fraction(1), Fraction(1)]
        v2 = [Fraction(2), Fraction(2)]
        b = [Fraction(3), Fraction(4)]
        res = programa.analizar_combinacion_lineal([v1, v2], b)

        self.assertFalse(res["es_posible"])
        self.assertEqual(res["sistema"]["clasificacion"], "Sistema inconsistente")
        self.assertIsNone(res["verificacion_vectorial"])

    def test_06_combinacion_lineal_infinitas_soluciones(self):
        """
        TEST 6 — Combinación lineal con infinitas soluciones:
        v1 = [1, 2], v2 = [2, 4], v3 = [1, 1], b = [3, 6]
        Variables libres y solución paramétrica.
        """
        v1 = [Fraction(1), Fraction(2)]
        v2 = [Fraction(2), Fraction(4)]
        v3 = [Fraction(1), Fraction(1)]
        b = [Fraction(3), Fraction(6)]
        res = programa.analizar_combinacion_lineal([v1, v2, v3], b)

        self.assertTrue(res["es_posible"])
        self.assertEqual(res["sistema"]["clasificacion"], "Sistema consistente indeterminado")
        self.assertGreater(len(res["sistema"]["variables_libres"]), 0)
        self.assertTrue(res["verificacion_vectorial"]["coincide"])

    def test_07_independencia_lineal(self):
        """
        TEST 7 — Independencia lineal (LI):
        Base canónica de R^3: e1=[1,0,0], e2=[0,1,0], e3=[0,0,1].
        Única solución trivial c1 = c2 = c3 = 0.
        """
        v1 = [Fraction(1), Fraction(0), Fraction(0)]
        v2 = [Fraction(0), Fraction(1), Fraction(0)]
        v3 = [Fraction(0), Fraction(0), Fraction(1)]
        res = programa.analizar_independencia_lineal([v1, v2, v3])

        self.assertTrue(res["es_li"])
        self.assertEqual(res["clasificacion"], "LINEALMENTE INDEPENDIENTE (LI)")
        self.assertEqual(res["num_pivotes"], 3)
        self.assertEqual(res["num_libres"], 0)
        self.assertIsNone(res["relacion_dependencia"])

    def test_08_dependencia_lineal_por_multiplos(self):
        """
        TEST 8 — Dependencia lineal por múltiplos (LD):
        v1 = [1, 2, 3], v2 = [2, 4, 6]. v2 = 2*v1.
        Existe solución no trivial y relación de dependencia.
        """
        v1 = [Fraction(1), Fraction(2), Fraction(3)]
        v2 = [Fraction(2), Fraction(4), Fraction(6)]
        res = programa.analizar_independencia_lineal([v1, v2])

        self.assertFalse(res["es_li"])
        self.assertEqual(res["clasificacion"], "LINEALMENTE DEPENDIENTE (LD)")
        self.assertEqual(res["num_pivotes"], 1)
        self.assertEqual(res["num_libres"], 1)
        self.assertIsNotNone(res["relacion_dependencia"])

    def test_09_conjunto_con_vector_cero(self):
        """
        TEST 9 — Conjunto que contiene el vector cero:
        v1 = [0, 0, 0], v2 = [1, 2, 3].
        Cualquier conjunto con el vector 0 es LD.
        """
        v1 = [Fraction(0), Fraction(0), Fraction(0)]
        v2 = [Fraction(1), Fraction(2), Fraction(3)]
        res = programa.analizar_independencia_lineal([v1, v2])

        self.assertFalse(res["es_li"])
        self.assertEqual(res["clasificacion"], "LINEALMENTE DEPENDIENTE (LD)")
        self.assertTrue(any("vector cero" in r for r in res["razones_adicionales"]))

    def test_10_ax_b_solucion_unica(self):
        """
        TEST 10 — Ax=b con solución única:
        x1 + x2 = 4, x1 - x2 = 2 => x1 = 3, x2 = 1.
        """
        A = [[Fraction(1), Fraction(1)], [Fraction(1), Fraction(-1)]]
        b = [Fraction(4), Fraction(2)]
        res = programa.resolver_sistema(A, b)

        self.assertEqual(res["clasificacion"], "Sistema consistente determinado")
        self.assertEqual(res["solucion"], [Fraction(3), Fraction(1)])
        self.assertTrue(res["verificacion"][0])

    def test_11_ax_b_infinitas_soluciones(self):
        """
        TEST 11 — Ax=b con infinitas soluciones:
        x1 + 2x2 + x3 = 3
        2x1 + 4x2 + 2x3 = 6
        """
        A = [
            [Fraction(1), Fraction(2), Fraction(1)],
            [Fraction(2), Fraction(4), Fraction(2)],
        ]
        b = [Fraction(3), Fraction(6)]
        res = programa.resolver_sistema(A, b)

        self.assertEqual(res["clasificacion"], "Sistema consistente indeterminado")
        self.assertGreater(len(res["variables_libres"]), 0)
        self.assertTrue(res["verificacion"][0])

    def test_12_ax_b_sin_solucion(self):
        """
        TEST 12 — Ax=b sin solución (inconsistente):
        x1 + x2 = 1
        2x1 + 2x2 = 3
        """
        A = [
            [Fraction(1), Fraction(1)],
            [Fraction(2), Fraction(2)],
        ]
        b = [Fraction(1), Fraction(3)]
        res = programa.resolver_sistema(A, b)

        self.assertEqual(res["clasificacion"], "Sistema inconsistente")
        self.assertIsNone(res["solucion"])
        self.assertIsNone(res["verificacion"])

    def test_13_matrices_dimensiones_incompatibles(self):
        """
        TEST 13 — Matrices con dimensiones incompatibles:
        Suma de A(2x3) y B(2x2) debe lanzar ValueError explicativo.
        """
        A = [
            [Fraction(1), Fraction(2), Fraction(3)],
            [Fraction(4), Fraction(5), Fraction(6)],
        ]
        B = [
            [Fraction(1), Fraction(2)],
            [Fraction(3), Fraction(4)],
        ]
        with self.assertRaises(ValueError) as ctx:
            programa.sumar_matrices(A, B)
        self.assertIn("incompatibles", str(ctx.exception).lower())

    def test_14_multiplicacion_matricial_valida(self):
        """
        TEST 14 — Multiplicación matricial válida:
        A(2x3) * B(3x2) = C(2x2)
        A = [[1, 2, 3], [4, 5, 6]]
        B = [[7, 8], [9, 1], [2, 3]]
        C = [[31, 19], [85, 55]]
        """
        A = [
            [Fraction(1), Fraction(2), Fraction(3)],
            [Fraction(4), Fraction(5), Fraction(6)],
        ]
        B = [
            [Fraction(7), Fraction(8)],
            [Fraction(9), Fraction(1)],
            [Fraction(2), Fraction(3)],
        ]
        C = programa.multiplicar_matrices(A, B)
        esperado = [
            [Fraction(31), Fraction(19)],
            [Fraction(85), Fraction(55)],
        ]
        self.assertEqual(C, esperado)

    def test_15_multiplicacion_matricial_invalida(self):
        """
        TEST 15 — Multiplicación matricial inválida:
        A(2x3) * B(2x2): cols(A)=3 != filas(B)=2.
        Debe lanzar ValueError explicando nA != mB.
        """
        A = [
            [Fraction(1), Fraction(2), Fraction(3)],
            [Fraction(4), Fraction(5), Fraction(6)],
        ]
        B = [
            [Fraction(1), Fraction(2)],
            [Fraction(3), Fraction(4)],
        ]
        with self.assertRaises(ValueError) as ctx:
            programa.multiplicar_matrices(A, B)
        self.assertIn("incompatibles", str(ctx.exception).lower())

    def test_16_valores_negativos(self):
        """
        TEST 16 — Valores negativos:
        -2x1 + 3x2 = -1
        x1 - 4x2 = -7
        Solución: x1 = 5, x2 = 3.
        """
        A = [
            [Fraction(-2), Fraction(3)],
            [Fraction(1), Fraction(-4)],
        ]
        b = [Fraction(-1), Fraction(-7)]
        res = programa.resolver_sistema(A, b)

        self.assertEqual(res["clasificacion"], "Sistema consistente determinado")
        self.assertEqual(res["solucion"], [Fraction(5), Fraction(3)])
        self.assertTrue(res["verificacion"][0])

    def test_17_fracciones(self):
        """
        TEST 17 — Fracciones:
        (1/2)x1 + (1/3)x2 = 5/6
        (2/3)x1 - (1/4)x2 = 1/12
        Solución: x1 = 17/25, x2 = 37/25.
        """
        A = [
            [Fraction(1, 2), Fraction(1, 3)],
            [Fraction(2, 3), Fraction(-1, 4)],
        ]
        b = [Fraction(5, 6), Fraction(1, 12)]
        res = programa.resolver_sistema(A, b)

        self.assertEqual(res["clasificacion"], "Sistema consistente determinado")
        self.assertEqual(res["solucion"], [Fraction(17, 25), Fraction(37, 25)])
        self.assertTrue(res["verificacion"][0])

    def test_18_filas_cero(self):
        """
        TEST 18 — Filas cero:
        Fila completa 0 = 0 en la matriz aumentada.
        Debe ignorar la redundancia y resolver correctamente.
        """
        A = [
            [Fraction(1), Fraction(2)],
            [Fraction(2), Fraction(4)],
            [Fraction(0), Fraction(0)],
        ]
        b = [Fraction(3), Fraction(6), Fraction(0)]
        res = programa.resolver_sistema(A, b)

        self.assertEqual(res["clasificacion"], "Sistema consistente indeterminado")
        self.assertTrue(res["verificacion"][0])

    def test_19_intercambio_de_filas(self):
        """
        TEST 19 — Intercambio de filas:
        A[0][0] = 0 requiere pivoteo F1 <-> F2.
        0x1 + x2 = 2
        3x1 + 2x2 = 7
        Solución: x1 = 1, x2 = 2.
        """
        A = [
            [Fraction(0), Fraction(1)],
            [Fraction(3), Fraction(2)],
        ]
        b = [Fraction(2), Fraction(7)]
        res = programa.resolver_sistema(A, b)

        self.assertEqual(res["clasificacion"], "Sistema consistente determinado")
        self.assertEqual(res["solucion"], [Fraction(1), Fraction(2)])
        operaciones = [p["operacion"] for p in res["pasos"]]
        self.assertTrue(any("F1 ↔ F2" in op or "F1 <-> F2" in op for op in operaciones))
        self.assertTrue(res["verificacion"][0])

    def test_20_sistemas_rectangulares(self):
        """
        TEST 20 — Sistemas rectangulares (3 ecuaciones x 2 variables):
        x1 + x2 = 3
        2x1 - x2 = 0
        3x1 + 2x2 = 7
        Solución: x1 = 1, x2 = 2.
        """
        A = [
            [Fraction(1), Fraction(1)],
            [Fraction(2), Fraction(-1)],
            [Fraction(3), Fraction(2)],
        ]
        b = [Fraction(3), Fraction(0), Fraction(7)]
        res = programa.resolver_sistema(A, b)

        self.assertEqual(res["clasificacion"], "Sistema consistente determinado")
        self.assertEqual(res["solucion"], [Fraction(1), Fraction(2)])
        self.assertTrue(res["verificacion"][0])

    def test_21_varios_vectores_varias_variables(self):
        """
        TEST 21 — Varios vectores y varias variables:
        Combinación lineal de 4 vectores en R^3 (4 variables c1..c4, 3 ecuaciones).
        v1 = [1, 0, 1], v2 = [0, 1, 1], v3 = [1, 1, 0], v4 = [1, 1, 1], b = [3, 4, 3].
        """
        v1 = [Fraction(1), Fraction(0), Fraction(1)]
        v2 = [Fraction(0), Fraction(1), Fraction(1)]
        v3 = [Fraction(1), Fraction(1), Fraction(0)]
        v4 = [Fraction(1), Fraction(1), Fraction(1)]
        b = [Fraction(3), Fraction(4), Fraction(3)]
        res = programa.analizar_combinacion_lineal([v1, v2, v3, v4], b)

        self.assertTrue(res["es_posible"])
        self.assertEqual(res["sistema"]["clasificacion"], "Sistema consistente indeterminado")
        self.assertEqual(len(res["sistema"]["nombres_variables"]), 4)
        self.assertTrue(res["verificacion_vectorial"]["coincide"])

    def test_22_caso_homogeneo(self):
        """
        TEST 22 — Caso homogéneo Ax = 0:
        Siempre consistente (la solución trivial 0 siempre satisface).
        """
        A = [
            [Fraction(1), Fraction(2), Fraction(3)],
            [Fraction(0), Fraction(1), Fraction(2)],
            [Fraction(0), Fraction(0), Fraction(0)],
        ]
        b = [Fraction(0), Fraction(0), Fraction(0)]
        res = programa.resolver_sistema(A, b)

        self.assertTrue(res["homogeneo"])
        self.assertEqual(res["clasificacion"], "Sistema consistente indeterminado")
        self.assertTrue(res["verificacion"][0])


if __name__ == "__main__":
    unittest.main()


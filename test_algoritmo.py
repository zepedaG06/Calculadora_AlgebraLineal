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


if __name__ == "__main__":
    unittest.main()


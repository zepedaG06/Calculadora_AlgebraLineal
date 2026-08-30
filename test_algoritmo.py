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

        # Ecuacion 1: x + y + z = 6
        self.assertEqual(detalles[0].ecuacion_original, "x + y + z = 6")
        self.assertEqual(detalles[0].sustitucion, "(1) + (2) + (3) = 6")
        self.assertEqual(detalles[0].simplificacion, ["1 + 2 + 3 = 6", "6 = 6"])
        self.assertTrue(detalles[0].coincide)

        # Ecuacion 2: 2x - y + z = 3
        self.assertEqual(detalles[1].ecuacion_original, "2x - y + z = 3")
        self.assertEqual(detalles[1].sustitucion, "2(1) - (2) + (3) = 3")
        self.assertEqual(detalles[1].simplificacion, ["2 - 2 + 3 = 3", "3 = 3"])
        self.assertTrue(detalles[1].coincide)

        # Ecuacion 3: x + 2y - z = 2
        self.assertEqual(detalles[2].ecuacion_original, "x + 2y - z = 2")
        self.assertEqual(detalles[2].sustitucion, "(1) + 2(2) - (3) = 2")
        self.assertEqual(detalles[2].simplificacion, ["1 + 4 - 3 = 2", "2 = 2"])
        self.assertTrue(detalles[2].coincide)

    def test_verificacion_con_solucion_incorrecta(self):
        A = [[Fraction(2), Fraction(-3), Fraction(1)]]
        b = [Fraction(7)]
        sol_falsa = [Fraction(1), Fraction(2), Fraction(4)]  # 2(1) - 3(2) + 4 = 0 != 7

        correcta, detalles = programa.verificar_solucion(A, b, sol_falsa)

        self.assertFalse(correcta)
        self.assertEqual(detalles[0].ecuacion_original, "2x - 3y + z = 7")
        self.assertEqual(detalles[0].sustitucion, "2(1) - 3(2) + (4) = 7")
        self.assertEqual(detalles[0].simplificacion, ["2 - 6 + 4 = 7", "0 = 7"])
        self.assertFalse(detalles[0].coincide)


if __name__ == "__main__":
    unittest.main()


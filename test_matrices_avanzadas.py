"""Pruebas exactas de determinantes, inversas, propiedades avanzadas y regresión de familias.

Unidad: Álgebra Lineal (MTM0120), verificación automática de la Calculadora.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
"""
import itertools
import random
import unittest
from fractions import Fraction as F
from modulos import modulo_matrices as m
import main


class Determinantes(unittest.TestCase):
    """Determinantes por todos los métodos frente a valores conocidos y a Leibniz."""
    def test_valores_manuales_y_metodos(self):
        """Comprueba det(A) calculado a mano con todos los métodos disponibles."""
        casos = [([[5]], F(5)), ([[1, 2], [3, 4]], F(-2)),
                 ([[1, 2], [2, 4]], F(0)),
                 ([[6, 1, 1], [4, -2, 5], [2, 8, 7]], F(-306)),
                 ([[F(1, 2), F(1, 3)], [F(2, 3), F(3, 4)]], F(11, 72)),
                 ([[2, 1, 0, 3], [0, -3, 2, 1], [0, 0, 4, 2], [0, 0, 0, 5]], F(-120))]
        for A, esperado in casos:
            for metodo in ["triangular", "cofactores"] + (["2x2"] if len(A) == 2 else []) + (["sarrus"] if len(A) == 3 else []):
                with self.subTest(A=A, metodo=metodo):
                    resultado = m.calcular_determinante(A, metodo)
                    self.assertEqual(resultado["determinante"], esperado)
                    self.assertIsInstance(resultado["determinante"], F)
                    self.assertTrue(resultado["pasos"])

    def test_oraculo_permutaciones_hasta_orden_cinco(self):
        """Compara det(A) con la fórmula de Leibniz en matrices aleatorias hasta orden 5."""
        rng = random.Random(42)
        for n in range(1, 6):
            for _ in range(8):
                A = [[F(rng.randint(-3, 3), rng.randint(1, 4)) for _ in range(n)] for _ in range(n)]
                esperado = F(0)
                # Definición de Leibniz: algoritmo independiente de la eliminación.
                for p in itertools.permutations(range(n)):
                    inversiones = sum(p[i] > p[j] for i in range(n) for j in range(i + 1, n))
                    producto = F((-1) ** inversiones)
                    for i, j in enumerate(p):
                        producto *= A[i][j]
                    esperado += producto
                for metodo in ("triangular", "cofactores"):
                    with self.subTest(n=n, metodo=metodo):
                        self.assertEqual(m.determinante(A, metodo), esperado)

    def test_validacion(self):
        """Comprueba que se rechazan matrices vacías, no cuadradas, no numéricas y métodos inválidos."""
        for A in ([], [[]], [[1, 2], [3]], [[1, 2, 3], [4, 5, 6]], [["abc"]]):
            with self.subTest(A=A), self.assertRaises(ValueError):
                m.determinante(A)
        for metodo in ("sarrus", "desconocido"):
            with self.assertRaises(ValueError):
                m.determinante([[1, 2], [3, 4]], metodo)
        with self.assertRaises(ValueError):
            m.determinante([[1]], "2x2")

    def test_intercambios_y_no_mutacion(self):
        """Comprueba el cambio de signo por intercambios y que A no se modifica."""
        A = [[0, 1], [2, 3]]
        r = m.calcular_determinante(A)
        self.assertEqual(r["intercambios"], 1)
        self.assertEqual(r["determinante"], -2)
        self.assertEqual(A, [[0, 1], [2, 3]])
        self.assertEqual(m.determinante([[0, 1, 2], [0, 3, 4], [0, 5, 6]]), 0)

    def test_menores_cofactores_adjunta(self):
        """Comprueba submatrices, menores, cofactores y la adjunta."""
        A = [[1, 2], [3, 4]]
        self.assertEqual(m.submatriz(A, 0, 1), [[F(3)]])
        self.assertEqual(m.menor(A, 0, 1), 3)
        self.assertEqual(m.cofactor(A, 0, 1), -3)
        self.assertEqual(m.matriz_menores(A), [[4, 3], [2, 1]])
        self.assertEqual(m.adjunta(A), [[4, -2], [-3, 1]])
        self.assertEqual(m.adjunta([[5]]), [[1]])
        self.assertEqual(m.calcular_determinante(A, "cofactores", fila=1)["determinante"], -2)
        for i, j in ((-1, 0), (2, 0), (0, 2)):
            with self.assertRaises(ValueError):
                m.menor(A, i, j)


class Inversas(unittest.TestCase):
    """Inversas por Gauss-Jordan y por adjunta, singularidad y verificación."""
    MATRICES = [[[5]], [[1, 2], [3, 4]], [[0, 2], [1, 3]],
                [[1, 2, 3], [0, 1, 4], [5, 6, 0]],
                [[F(1, 2), F(1, 3)], [F(2, 3), F(3, 4)]],
                [[F(1, 2), 1, 0], [0, F(2, 3), 1], [1, 0, F(3, 4)]]]

    def test_ambos_metodos_y_productos(self):
        """Comprueba que Gauss-Jordan y adjunta dan la misma inversa y que A·A⁻¹ = I."""
        for A in self.MATRICES:
            with self.subTest(A=A):
                gj = m.calcular_inversa(A)
                adj = m.calcular_inversa(A, "adjunta")
                self.assertEqual(gj["inversa"], adj["inversa"])
                self.assertTrue(gj["verificacion"]["correcto"])
                self.assertEqual(m.multiplicar_matrices(A, gj["inversa"]), m.matriz_identidad(len(A)))
                self.assertEqual(m.multiplicar_matrices(adj["inversa"], A), m.matriz_identidad(len(A)))
                self.assertTrue(all(isinstance(v, F) for fila in gj["inversa"] for v in fila))
                self.assertTrue(m.comparar_metodos_inversa(A)["cumple"])

    def test_valor_manual(self):
        """Comprueba la inversa de una matriz 2 × 2 calculada a mano."""
        self.assertEqual(m.inversa_gauss_jordan([[1, 2], [3, 4]]), [[-2, 1], [F(3, 2), F(-1, 2)]])

    def test_singular_y_no_cuadrada(self):
        """Comprueba que se rechazan matrices singulares, no cuadradas y vacías."""
        for A in ([[1, 2], [2, 4]], [[0]], [[1, 2, 3], [4, 5, 6]], []):
            for funcion in (m.inversa_gauss_jordan, m.inversa_adjunta):
                with self.subTest(A=A, funcion=funcion), self.assertRaises(ValueError):
                    funcion(A)

    def test_verificacion_rechaza_falsa_inversa(self):
        """Comprueba que una inversa falsa no pasa la verificación."""
        self.assertFalse(m.verificar_inversa([[1, 2], [3, 4]], [[1, 0], [0, 1]])["correcto"])


class Propiedades(unittest.TestCase):
    """Propiedades avanzadas de inversas y determinantes."""
    def test_todas_con_lados_y_conclusion(self):
        """Comprueba que cada propiedad avanzada devuelve lados y conclusión."""
        for clave in m.PROPIEDADES_AVANZADAS:
            A = [[2, 1], [0, 3]] if clave == "det_triangular" else [[1, 2], [3, 4]]
            with self.subTest(clave=clave):
                r = m.verificar_propiedad_matricial(clave, {"A": A, "B": [[2, 0], [1, 3]]}, {"k": F(-3, 2)})
                self.assertTrue(r["cumple"])
                self.assertEqual(r["izquierda"], r["derecha"])
                self.assertEqual(r["conclusion"], "Se cumple para las matrices ingresadas")
                self.assertEqual(r["pasos"][-1], "Se cumple para las matrices ingresadas")

    def test_hipotesis(self):
        """Comprueba que se exigen las hipótesis de cada propiedad (por ejemplo, matriz invertible)."""
        for clave in ("inversa_inversa", "inversa_producto", "inversa_transpuesta", "det_inversa"):
            with self.subTest(clave=clave), self.assertRaises(ValueError):
                m.verificar_propiedad_matricial(clave, {"A": [[1, 2], [2, 4]], "B": [[1, 0], [0, 1]]})
        with self.assertRaises(ValueError):
            m.verificar_propiedad_matricial("inversa_producto", {"A": [[1]], "B": [[1, 0], [0, 1]]})
        with self.assertRaises(ValueError):
            m.verificar_propiedad_matricial("det_triangular", {"A": [[1, 2], [3, 4]]})

    def test_reglas_fila_incluyen_cero_y_singular(self):
        """Comprueba las reglas de fila del determinante con k = 0 y matrices singulares."""
        for A in ([[1, 2], [2, 4]], [[0, 1], [2, 3]]):
            for k in (F(0), F(2, 3), F(-4)):
                for clave in ("det_intercambio", "det_escalar_fila", "det_suma_fila"):
                    self.assertTrue(m.verificar_propiedad_matricial(clave, {"A": A}, {"k": k})["cumple"])


class Regresion(unittest.TestCase):
    """Regresión de familias paramétricas y compatibilidad de la GUI."""
    def test_operaciones_y_dimensiones(self):
        """Comprueba operaciones básicas y sus dimensiones."""
        A, C = [[1, 2, 3], [4, 5, 6]], [[1, 2], [0, 1], [2, 3]]
        self.assertEqual(m.multiplicar_matrices(A, C), [[7, 13], [16, 31]])
        self.assertEqual(m.dimensiones_matriz(m.multiplicar_matrices(C, A)), (3, 3))
        self.assertEqual(m.sumar_matrices([[1]], [[2]]), [[3]])
        self.assertEqual(m.restar_matrices([[1]], [[2]]), [[-1]])
        self.assertEqual(m.multiplicar_matriz_escalar(F(1, 2), [[2, 4]]), [[1, 2]])
        self.assertEqual(m.transponer_matriz(A), [[1, 4], [2, 5], [3, 6]])
        for funcion in (m.sumar_matrices, m.restar_matrices, m.multiplicar_matrices):
            with self.assertRaises(ValueError):
                funcion(A, [[1]])

    def test_gauss_jordan_enteros_normalizados(self):
        """Comprueba que Gauss-Jordan convierte los enteros a Fraction en todos los pasos."""
        reducida, _, pasos = m.gauss_jordan([[2, 1, 1], [1, 1, 0]], 2)
        self.assertTrue(all(isinstance(v, F) for fila in reducida for v in fila))
        self.assertTrue(all(isinstance(v, F) for p in pasos for fila in p.matriz for v in fila))

    def test_familia_completa(self):
        """Comprueba la verificación de toda la familia paramétrica."""
        r = m.resolver_sistema([[1, 2, 3], [2, 4, 6]], [1, 2])
        v = r["verificacion_general"]
        self.assertTrue(v["correcto"])
        self.assertEqual(len(v["direcciones"]), 2)
        self.assertTrue(all(d["producto"] == [0, 0] for d in v["direcciones"]))

    def test_direccion_incorrecta_detectada(self):
        """Comprueba que se detecta una dirección paramétrica incorrecta."""
        r = m.verificar_solucion_general([[1, 2]], [1], [1, 0], [("t", [1, 1])])
        self.assertTrue(r["particular"]["correcto"])
        self.assertFalse(r["correcto"])
        self.assertEqual(r["conclusion"], "No se cumple")

    def test_validacion_sistema(self):
        """Comprueba que se rechazan sistemas con dimensiones inválidas."""
        with self.assertRaises(ValueError):
            m.resolver_sistema([[1], [2]], [1])
        with self.assertRaises(ValueError):
            m.multiplicar_matriz_vector([[1, 2], [3]], [1, 2])

    def test_imports_compatibles(self):
        """Comprueba que la GUI usa las mismas funciones del núcleo."""
        gui = main.cargar_aplicacion()
        self.assertIs(gui.determinante, m.determinante)
        self.assertIs(gui.resolver_sistema, m.resolver_sistema)


if __name__ == "__main__":
    unittest.main()

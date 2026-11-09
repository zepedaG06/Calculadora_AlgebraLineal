"""Factorización LU, sustituciones encadenadas, verificadores y su integración en la GUI.

Unidad: Álgebra Lineal (MTM0120), verificación automática de la Calculadora.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
"""
from copy import deepcopy
from fractions import Fraction as F
from itertools import permutations
import random
import time
import unittest
from unittest.mock import Mock, patch

import main
from modulos import informes as d
from modulos import modulo_lu as lu
from modulos import modulo_matrices as m


def producto_ref(A, B):
    """Producto matricial de referencia, independiente de la Calculadora."""
    return [[sum((F(a) * F(b) for a, b in zip(fila, col)), F(0)) for col in zip(*B)] for fila in A]


def leibniz(A):
    """Determinante por la definición de Leibniz (oráculo independiente)."""
    total = F(0)
    for p in permutations(range(len(A))):
        termino = F((-1) ** sum(p[i] > p[j] for i in range(len(p)) for j in range(i + 1, len(p))))
        for i, j in enumerate(p):
            termino *= A[i][j]
        total += termino
    return total


def aplicar_reemplazos(A, operaciones):
    """Reproduce U aplicando a A solo las operaciones registradas."""
    U = [[F(v) for v in fila] for fila in A]
    for o in operaciones:
        i, k, mult = o["fila"], o["fila_pivote"], o["multiplicador"]
        U[i] = [a - mult * b for a, b in zip(U[i], U[k])]
    return U


LAY_A = [[3, -7, -2, 2], [-3, 5, 1, 0], [6, -4, 0, -5], [-9, 5, -5, 12]]
LAY_B = [-9, 5, 7, 11]
LAY_RECT = [[2, 4, -1, 5, -2], [-4, -5, 3, -8, 1], [2, -5, -4, 1, 8], [-6, 0, 7, -3, 1]]


class Factorizacion(unittest.TestCase):
    """Factorización A = LU: ejemplos del libro, reemplazos y oráculo aleatorio."""
    def test_ejemplo_del_libro_cuadrado(self):
        """Comprueba L y U del ejemplo cuadrado del libro de Lay."""
        r = lu.factorizar_lu(LAY_A)
        self.assertTrue(r["existe"])
        self.assertEqual(r["matriz_L"], [[1, 0, 0, 0], [-1, 1, 0, 0], [2, -5, 1, 0], [-3, 8, 3, 1]])
        self.assertEqual(r["matriz_U"], [[3, -7, -2, 2], [0, -2, -1, 2], [0, 0, -1, 1], [0, 0, 0, -1]])
        self.assertEqual(producto_ref(r["matriz_L"], r["matriz_U"]), LAY_A)

    def test_ejemplo_del_libro_rectangular_con_columna_sin_pivote(self):
        """Comprueba L y U del ejemplo rectangular de Lay, con una columna sin pivote."""
        r = lu.factorizar_lu(LAY_RECT)
        self.assertEqual(r["matriz_L"], [[1, 0, 0, 0], [-2, 1, 0, 0], [1, -3, 1, 0], [-3, 4, 2, 1]])
        self.assertEqual(r["matriz_U"], [[2, 4, -1, 5, -2], [0, 3, 1, 2, -3], [0, 0, 0, 2, 1], [0, 0, 0, 0, 5]])
        self.assertEqual(r["columnas_pivote"], [0, 1, 3, 4])
        self.assertTrue(any(e["titulo"] == "Columna 3 sin pivote" for e in r["etapas"]))

    def test_solo_reemplazos_de_filas_inferiores_y_multiplicadores_en_orden(self):
        """Comprueba que solo se usan reemplazos de filas inferiores y que los multiplicadores van en orden."""
        r = lu.factorizar_lu(LAY_A)
        self.assertTrue(all(o["fila"] > o["fila_pivote"] for o in r["operaciones"]))
        self.assertEqual(aplicar_reemplazos(LAY_A, r["operaciones"]), r["matriz_U"])
        self.assertEqual([(o["fila"], o["fila_pivote"]) for o in r["operaciones"]],
                         [(1, 0), (2, 0), (3, 0), (2, 1), (3, 1), (3, 2)])
        for o in r["operaciones"]:
            self.assertEqual(r["matriz_L"][o["fila"]][o["fila_pivote"]], o["multiplicador"])
        reemplazo = next(e for e in r["etapas"] if e["titulo"] == r["operaciones"][0]["operacion"])
        L_paso = next(v for v in reemplazo["valores"] if v["nombre"].startswith("L"))
        self.assertEqual(L_paso["pivotes"], [(1, 0)])
        self.assertEqual(len(reemplazo["calculos"]), 4)

    def test_oraculo_aleatorio_lu_igual_a_A(self):
        """Comprueba L·U = A en 250 matrices aleatorias que admiten la factorización."""
        rng = random.Random(2026)
        existentes = 0
        for _ in range(250):
            filas, columnas = rng.randint(1, 6), rng.randint(1, 6)
            A = [[F(rng.randint(-4, 4), rng.choice((1, 1, 2, 3))) for _ in range(columnas)] for _ in range(filas)]
            r = lu.factorizar_lu(A)
            with self.subTest(A=A):
                if not r["existe"]:
                    fila, columna, debajo = r["bloqueo"]
                    self.assertEqual(r["U_parcial"][fila][columna], 0)
                    self.assertNotEqual(r["U_parcial"][debajo][columna], 0)
                    self.assertEqual(producto_ref(r["L_parcial"], r["U_parcial"]), A)
                    continue
                existentes += 1
                self.assertEqual(producto_ref(r["matriz_L"], r["matriz_U"]), A)
                self.assertTrue(lu.es_triangular_inferior_unitaria(r["matriz_L"]))
                self.assertEqual(lu.pivotes_escalonada(r["matriz_U"]), r["pivotes"])
                self.assertEqual(aplicar_reemplazos(A, r["operaciones"]), r["matriz_U"])
        self.assertGreater(existentes, 100)

    def test_requiere_intercambio_sin_factorizacion_falsa(self):
        """Comprueba que, si hace falta intercambiar filas, no se inventa una factorización."""
        r = lu.resolver_lu([[0, 2, 1], [1, 1, 1], [2, 1, 3]], [3, 3, 6])
        self.assertFalse(r["existe"])
        self.assertIsNone(r["matriz_L"])
        self.assertIsNone(r["matriz_U"])
        self.assertIsNone(r["solucion"])
        self.assertIn("intercambiar F1 con F2", r["detalle"])
        self.assertEqual(r["mensaje"], lu.MENSAJE_SIN_PERMUTACION)
        v = lu.verificar_lu(r)
        self.assertTrue(v["correcto"])
        self.assertTrue(any("intercambios" in e["titulo"] for e in v["etapas"]))

    def test_no_modifica_los_datos(self):
        """Comprueba que A y b no se modifican."""
        A, b = deepcopy(LAY_A), deepcopy(LAY_B)
        r = lu.resolver_lu(A, b)
        lu.verificar_lu(r)
        self.assertEqual((A, b), (LAY_A, LAY_B))
        self.assertIsNot(r["matriz_A"], A)

    def test_validacion_de_datos(self):
        """Comprueba que se rechazan datos vacíos, irregulares, no numéricos o de tamaño incompatible."""
        for A, b in (([], []), ([[1, 2], [3]], [1, 2]), ([["x"]], [1]), ([[1, 2]], [1, 2])):
            with self.subTest(A=A, b=b), self.assertRaises(ValueError):
                lu.resolver_lu(A, b)


class Sustituciones(unittest.TestCase):
    """Sustitución hacia adelante y hacia atrás encadenadas."""
    def test_ejemplo_del_libro_encadena_y_y_x(self):
        """Comprueba que y de Ly = b se usa en Ux = y y da la x del libro."""
        r = lu.resolver_lu(LAY_A, LAY_B)
        self.assertEqual(r["vector_y"], [-9, -4, 5, 1])
        self.assertEqual(r["solucion"], [3, 4, -6, -1])
        # La etapa 3 guarda su propia copia de y: así la verificación puede comparar el enlace.
        self.assertEqual(r["atras"]["vector_y"], r["adelante"]["vector_y"])
        self.assertIsNot(r["atras"]["vector_y"], r["adelante"]["vector_y"])
        self.assertEqual(r["cadena"][1]["salidas"]["y"], r["cadena"][2]["entradas"]["y"])
        self.assertEqual(r["cadena"][0]["salidas"]["L"], r["cadena"][1]["entradas"]["L"])
        self.assertEqual(r["cadena"][0]["salidas"]["U"], r["cadena"][2]["entradas"]["U"])
        titulos = [e["titulo"] for e in r["etapas"]]
        orden = [titulos.index(t) for t in ("Etapa 1 · Factorización A = LU",
                                            "Etapa 2 · Sustitución hacia adelante: Ly = b",
                                            "Etapa 3 · Sustitución hacia atrás: Ux = y")]
        self.assertEqual(orden, sorted(orden))
        self.assertEqual(r["determinante"], leibniz(LAY_A))

    def test_adelante_con_diagonal_no_unitaria_y_errores(self):
        """Comprueba la sustitución hacia adelante con diagonal no unitaria y sus errores."""
        r = lu.sustitucion_adelante([[2, 0], [1, 3]], [4, 11])
        self.assertEqual(r["vector_y"], [2, 3])
        self.assertTrue(any("/ (3)" in linea for e in r["etapas"] for linea in e["calculos"]))
        for L, b in (([[1, 2], [0, 1]], [1, 1]), ([[0, 0], [1, 1]], [1, 1]), ([[1, 0], [0, 1]], [1])):
            with self.subTest(L=L, b=b), self.assertRaises(ValueError):
                lu.sustitucion_adelante(L, b)

    def test_atras_exige_forma_escalonada(self):
        """Comprueba que la sustitución hacia atrás exige U escalonada."""
        with self.assertRaises(ValueError):
            lu.sustitucion_atras([[0, 1], [1, 0]], [1, 1])
        with self.assertRaises(ValueError):
            lu.sustitucion_atras([[1, 1], [0, 1]], [1, 1], pivotes=[(0, 0), (1, 0)])

    def test_infinitas_soluciones_iguales_a_gauss_jordan(self):
        """Comprueba que la familia de soluciones por LU coincide con Gauss-Jordan."""
        b = [7, -12, 3, -9]
        r = lu.resolver_lu(LAY_RECT, b)
        g = m.resolver_sistema(LAY_RECT, b)
        self.assertEqual(r["clasificacion"], "Sistema consistente indeterminado")
        self.assertEqual(r["forma_vectorial"], g["forma_vectorial"])
        self.assertEqual(r["expresiones"], g["expresiones"])
        self.assertEqual(r["variables_libres"], [2])
        p, direcciones = r["forma_vectorial"]
        self.assertEqual(producto_ref(LAY_RECT, [[v] for v in p]), [[v] for v in b])
        for _, v in direcciones:
            self.assertEqual(producto_ref(LAY_RECT, [[x] for x in v]), [[0]] * 4)

    def test_inconsistente_por_fila_nula_de_U(self):
        """Comprueba que una fila nula de U con yᵢ ≠ 0 se reporta como inconsistencia."""
        A = [[1, 2, 3], [2, 4, 7], [3, 6, 10]]
        r = lu.resolver_lu(A, [6, 13, 20])
        self.assertEqual(r["clasificacion"], "Sistema inconsistente")
        self.assertEqual(r["filas_inconsistentes"], [2])
        self.assertEqual(r["matriz_final"][2], [0, 0, 0, 1])
        v = lu.verificar_lu(r)
        self.assertTrue(v["correcto"])
        self.assertTrue(any("Certificado" in e["titulo"] for e in v["etapas"]))

    def test_oraculo_aleatorio_contra_gauss_jordan(self):
        """Compara LU con Gauss-Jordan en 150 sistemas aleatorios de rango conocido."""
        rng = random.Random(806)
        for _ in range(150):
            filas, columnas = rng.randint(1, 5), rng.randint(1, 5)
            rango = rng.randint(1, min(filas, columnas))
            B = [[F(rng.randint(-3, 3)) for _ in range(rango)] for _ in range(filas)]
            C = [[F(rng.randint(-3, 3)) for _ in range(columnas)] for _ in range(rango)]
            A = producto_ref(B, C)
            b = [F(rng.randint(-4, 4)) for _ in range(filas)]
            r = lu.resolver_lu(A, b)
            with self.subTest(A=A, b=b):
                self.assertTrue(lu.verificar_lu(r)["correcto"])
                if not r["existe"]:
                    continue
                g = m.resolver_sistema(A, b)
                self.assertEqual(r["clasificacion"], g["clasificacion"])
                self.assertEqual(r["solucion"], g["solucion"])
                self.assertEqual(r["forma_vectorial"], g["forma_vectorial"])


class Verificacion(unittest.TestCase):
    """Verificación independiente y detección de datos alterados."""
    def test_comprobaciones_independientes_presentes(self):
        """Comprueba que el verificador incluye todas las comprobaciones independientes."""
        v = lu.verificar_lu(lu.resolver_lu(LAY_A, LAY_B))
        self.assertTrue(v["correcto"])
        nombres = [c["nombre"] for c in v["chequeos"]]
        self.assertEqual(nombres, ["Encadenamiento de datos", "Estructura de los resultados", "L·U = A", "U recalculada",
                                   "L·y = b", "Solución en el sistema original", "Coincide con Gauss-Jordan",
                                   "Determinante"])
        lu_vs_a = next(e for e in v["etapas"] if e["titulo"] == "L·U frente a A original")
        self.assertEqual(len(lu_vs_a["calculos"]), 16)
        self.assertIn("para las matrices ingresadas", lu_vs_a["conclusion"])
        self.assertTrue(any(e["titulo"] == "det(A) por cofactores" for e in v["etapas"]))

    def test_sarrus_para_3x3(self):
        """Comprueba que en 3 × 3 el determinante de la verificación se calcula por Sarrus."""
        v = lu.verificar_lu(lu.resolver_lu([[2, 1, 1], [4, -6, 0], [-2, 7, 2]], [5, -2, 9]))
        self.assertTrue(any(e["titulo"] == "det(A) por Sarrus" for e in v["etapas"]))

    def test_detecta_cada_dato_alterado(self):
        """Comprueba que el verificador detecta cada dato alterado del resultado."""
        base = lu.resolver_lu(LAY_A, LAY_B)
        rutas = [("matriz_L", 1, 0), ("matriz_U", 0, 3), ("vector_y", 2), ("solucion", 0), ("adelante", "vector_y", 1),
                 ("atras", "vector_y", 0), ("adelante", "vector_b", 0), ("factorizacion", "matriz_A", 0, 0), ("determinante",)]
        for ruta in rutas:
            with self.subTest(ruta=ruta):
                r = deepcopy(base)
                if ruta == ("determinante",):
                    r["determinante"] += 1
                else:
                    objeto = r
                    for clave in ruta[:-1]:
                        objeto = objeto[clave]
                    objeto[ruta[-1]] += 1
                self.assertFalse(lu.verificar_lu(r)["correcto"])

    def test_y_de_la_etapa_3_debe_ser_la_salida_de_la_etapa_2(self):
        """Comprueba que la y usada en Ux = y debe ser la salida de Ly = b."""
        r = deepcopy(lu.resolver_lu(LAY_A, LAY_B))
        r["atras"]["vector_y"][0] += 1
        v = lu.verificar_lu(r)
        fallidas = [c["nombre"] for c in v["chequeos"] if not c["correcto"]]
        self.assertEqual(fallidas, ["Encadenamiento de datos"])
        enlace = next(e for e in v["etapas"] if e["titulo"] == "Encadenamiento de datos")
        self.assertFalse(enlace["condiciones"][4]["cumple"])

    def test_resultados_deformados_no_rompen_el_verificador(self):
        """Comprueba que resultados deformados se reportan como fallos sin lanzar excepciones."""
        consistente = lu.resolver_lu(LAY_A, LAY_B)
        parametrico = lu.resolver_lu([[1, 2, 3], [2, 4, 7], [3, 6, 10]], [6, 13, 19])
        inconsistente = lu.resolver_lu([[1, 2, 3], [2, 4, 7], [3, 6, 10]], [6, 13, 20])
        casos = [
            ("L con una fila menos", consistente, lambda r: r["matriz_L"].pop()),
            ("U irregular", consistente, lambda r: r["matriz_U"][1].pop()),
            ("L ausente", consistente, lambda r: r.__setitem__("matriz_L", None)),
            ("y más corta", consistente, lambda r: r["vector_y"].pop()),
            ("solución que no es lista", consistente,
             lambda r: (r.__setitem__("solucion", 5), r["atras"].__setitem__("solucion", 5))),
            ("determinante omitido", consistente, lambda r: r.__setitem__("determinante", None)),
            ("dirección más corta", parametrico, lambda r: r["forma_vectorial"][1][0][1].pop()),
            ("inconsistente marcado como consistente", inconsistente,
             lambda r: r.__setitem__("clasificacion", "Sistema consistente determinado")),
            ("y más corta en inconsistente", inconsistente, lambda r: r["adelante"]["vector_y"].pop()),
        ]
        for nombre, base, alterar in casos:
            with self.subTest(caso=nombre):
                r = deepcopy(base)
                alterar(r)
                self.assertFalse(lu.verificar_lu(r)["correcto"])

    def test_verifica_contra_los_datos_que_se_le_entregan(self):
        """Comprueba que se verifica contra los A y b entregados al verificador."""
        r = lu.resolver_lu(LAY_A, LAY_B)
        otro_b = [v + 1 for v in LAY_B]
        self.assertFalse(lu.verificar_lu(r, vector_b=otro_b)["correcto"])
        self.assertTrue(lu.verificar_lu(r, matriz_A=LAY_A, vector_b=LAY_B)["correcto"])


class PropiedadInversa(unittest.TestCase):
    """Propiedades A⁻¹A = I y AA⁻¹ = I."""
    def test_propiedades_inversa_izquierda_y_derecha(self):
        """Comprueba A⁻¹A = I y AA⁻¹ = I con fracciones."""
        A = [[F(1, 2), -2, 0], [3, 1, 4], [0, 2, F(-1, 3)]]
        for clave, nombre in (("inversa_izquierda", "A⁻¹A"), ("inversa_derecha", "AA⁻¹")):
            with self.subTest(clave=clave):
                r = d.informe_propiedad_avanzada(clave, {"A": A})
                self.assertTrue(r["definido"])
                self.assertTrue(r["verificacion"]["correcto"])
                self.assertEqual(r["lados"][0]["resultado"], m.matriz_identidad(3))
                self.assertTrue(any(e["titulo"] == f"Calcular {nombre}" for e in r["lados"][0]["etapas"]))
                self.assertIn("A⁻¹", r["teoria"]["conclusion"])
                singular = d.informe_propiedad_avanzada(clave, {"A": [[1, 2], [2, 4]]})
                self.assertFalse(singular["definido"])
                self.assertIn("singular", singular["conclusion"])

    def test_expresion_reconoce_producto_por_la_inversa(self):
        """Comprueba que las expresiones A⁻¹A y AA⁻¹ se reconocen como la identidad."""
        A = [[2, 1], [7, 4]]
        for texto, enunciado in (("A^-1A", "A⁻¹A = I₂"), ("AA^-1", "AA⁻¹ = I₂")):
            with self.subTest(texto=texto):
                r = m.resolver_expresion_matricial(texto, {"A": A})
                v = m.verificar_resolucion(r)
                self.assertEqual(r["resultado"], m.matriz_identidad(2))
                self.assertEqual(r["identidad"][1], enunciado)
                self.assertTrue(v["identidad"]["ok"])
                self.assertTrue(v["correcto"])
        r = m.resolver_expresion_matricial("A^-1B", {"A": A, "B": [[1, 0], [0, 2]]})
        self.assertIsNone(r["identidad"])
        # La identidad de la inversa tiene prioridad sobre la distributividad.
        r = m.resolver_expresion_matricial("(A+B)^-1(A+B)", {"A": A, "B": [[1, 2], [3, 5]]})
        self.assertEqual(r["identidad"][1], "(A + B)⁻¹(A + B) = I₂")
        self.assertTrue(m.verificar_resolucion(r)["correcto"])


class IntegracionGUI(unittest.TestCase):
    """Página de factorización LU en la interfaz gráfica."""
    @classmethod
    def setUpClass(cls):
        """Carga la GUI una vez para todas las pruebas de la clase."""
        cls.gui = main.cargar_aplicacion()

    def pagina(self, matriz):
        """Crea una página LU con widgets simulados que lee la matriz indicada."""
        pagina = object.__new__(self.gui.PaginaLU)
        for atributo in ("app", "aviso", "panel_pasos", "area_resultado", "area_verificacion", "pestanas"):
            setattr(pagina, atributo, Mock())
        pagina.leer_datos = Mock(return_value=[[F(v) for v in fila] for fila in matriz])
        return pagina

    def test_tres_vistas_con_datos_de_la_factorizacion(self):
        """Comprueba que las tres pestañas de la página LU usan los datos de la factorización."""
        pagina = self.pagina([fila + [bi] for fila, bi in zip(LAY_A, LAY_B)])
        pagina.resolver()
        self.assertEqual(pagina.resultado["solucion"], [3, 4, -6, -1])
        pasos = pagina.panel_pasos.mostrar_pasos.call_args.args[0]
        self.assertEqual(pasos, pagina.resultado["etapas"])
        pagina.area_verificacion.llenar.assert_called_once()
        mensaje, tipo = pagina.app.notificar.call_args.args
        self.assertEqual(tipo, "exito")
        self.assertIn("6 reemplazos", mensaje)

    def test_sin_lu_no_inventa_resultado(self):
        """Comprueba que la página LU avisa, sin inventar resultados, si no hay factorización."""
        pagina = self.pagina([[0, 1, 1], [1, 1, 2]])
        pagina.resolver()
        self.assertFalse(pagina.resultado["existe"])
        self.assertEqual(pagina.app.notificar.call_args.args[1], "aviso")

    def test_propiedades_de_inversa_con_singular_se_dibujan_sin_error(self):
        # Antes faltaba «motivo» y la pestaña Verificación lanzaba KeyError.
        """Comprueba que las propiedades de inversa con matrices singulares se dibujan sin errores."""
        for clave in ("inversa_izquierda", "inversa_derecha", "inversa_inversa", "inversa_transpuesta", "det_inversa"):
            with self.subTest(clave=clave):
                r = d.informe_propiedad_avanzada(clave, {"A": [[1, 2], [2, 4]]})
                with patch.object(self.gui, "tarjeta_mensajes") as mensajes, \
                        patch.object(self.gui, "tarjeta_etapa"):
                    for constructor in self.gui.constructores_chequeo(r["verificacion"]):
                        constructor(Mock())
                self.assertIn("singular", mensajes.call_args.args[2][0])
        self.gui.constructores_chequeo({"aplicable": False, "correcto": False, "etapas": []})[0]

    def test_aleatorio_siempre_factoriza(self):
        """Comprueba que los datos aleatorios de la página LU siempre admiten A = LU."""
        pagina = object.__new__(self.gui.PaginaLU)
        for filas, columnas in ((1, 1), (3, 3), (4, 2), (2, 5), (10, 10)):
            matriz = pagina.valores_aleatorios(filas, columnas)
            r = lu.resolver_lu([f[:-1] for f in matriz], [f[-1] for f in matriz])
            self.assertTrue(r["existe"])
            self.assertNotEqual(r["clasificacion"], "Sistema inconsistente")

    def test_widgets_reales_ejemplos_y_encadenamiento(self):
        """Comprueba con widgets reales los ejemplos y el encadenamiento entre secciones."""
        if self.gui.ctk is None:
            self.skipTest("CustomTkinter no disponible")
        try:
            app = self.gui.AplicacionAlgebraLineal()
        except self.gui.tk.TclError as error:
            self.skipTest(f"Pantalla Tk no disponible: {error}")
        errores = []
        app.report_callback_exception = lambda *args: errores.append(args)
        app.withdraw()

        def bombear():
            """Procesa los eventos de Tk durante un instante."""
            fin = time.monotonic() + 0.25
            while time.monotonic() < fin:
                app.update()
                time.sleep(0.005)
        try:
            pagina = app.ir_a("lu")
            for nombre in pagina.ejemplos:
                with self.subTest(ejemplo=nombre):
                    pagina.cargar_ejemplo(nombre)
                    pagina.resolver()
                    bombear()
                    self.assertIsNotNone(pagina.resultado)
                    self.assertTrue(lu.verificar_lu(pagina.resultado)["correcto"])
                    for pestana in ("Procedimiento", "Verificación", "Resultado"):
                        pagina.pestanas.set(pestana)
                        bombear()
            pagina.aleatorio()
            pagina.resolver()
            bombear()
            self.assertTrue(pagina.resultado["existe"])

            # LU → Operaciones matriciales: AB − C con A = L, B = U y C = A original.
            pagina.cargar_ejemplo("Ejemplo del libro (4×4)")
            pagina.resolver()
            pagina._enviar_a_operaciones(pagina.resultado)
            bombear()
            self.assertEqual(app.pagina_actual, "matrices")
            matrices = app.paginas["matrices"]
            self.assertEqual(matrices._leer_matrices({"A", "B", "C"}),
                             {"A": pagina.resultado["matriz_L"], "B": pagina.resultado["matriz_U"], "C": LAY_A})
            resolucion = m.resolver_expresion_matricial("AB − C", matrices._leer_matrices({"A", "B", "C"}))
            self.assertEqual(resolucion["resultado"], [[0] * 4 for _ in range(4)])

            # Operaciones: el resultado de una expresión se encadena como B.
            matrices._guardar_resultado("B", [[1, 2], [3, 4]])
            self.assertEqual(matrices._leer_matrices({"B"})["B"], [[1, 2], [3, 4]])

            # LU → Ax = b (Gauss-Jordan) y Ax = b → LU con los mismos datos.
            pagina._enviar_a_axb(pagina.resultado)
            bombear()
            axb = app.paginas["axb"]
            self.assertEqual(axb.resultado["solucion"], [3, 4, -6, -1])
            axb._enviar_a_lu(LAY_A, LAY_B)
            bombear()
            self.assertEqual(app.pagina_actual, "lu")
            self.assertEqual(pagina.resultado["vector_y"], [-9, -4, 5, 1])

            # Determinantes e inversas → Operaciones: B = A⁻¹ y BA = I.
            det = app.ir_a("determinantes")
            det._enviar_inversa([[2, 1], [7, 4]], [[4, -1], [-7, 2]])
            bombear()
            leidas = app.paginas["matrices"]._leer_matrices({"A", "B"})
            self.assertEqual(m.multiplicar_matrices(leidas["B"], leidas["A"]), m.matriz_identidad(2))
            self.assertFalse(errores, errores)
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()

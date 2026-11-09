"""Pruebas de los requisitos del Programa 6 (Tarea 6).

Comprueba las reglas técnicas (sin librerías externas ni math, funciones puras, documentación, sin código
comentado), la factorización LU con sus mensajes exactos, la reutilización de funciones de la Calculadora,
la cobertura completa del verificador de propiedades, el encadenamiento de resultados y el menú de consola.
Unidad: Álgebra Lineal (MTM0120), Programa 6.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
"""
import ast
import contextlib
import io
import re
import time
import unittest
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch

import main
from modulos import informes as d
from modulos import modulo_lu as lu
from modulos import modulo_matrices as m
from teoremas.teoremas_lu import LOGO_LU, TEOREMAS_LU
from teoremas.teoremas_matrices import DEMOSTRACIONES_PROPIEDADES

RAIZ = Path(__file__).parent
ARCHIVOS = [RAIZ / "main.py", RAIZ / "Programa 1_Grupo3.py", *sorted((RAIZ / "modulos").glob("*.py")),
            *sorted((RAIZ / "teoremas").glob("*.py"))]
LAY_A = [[3, -7, -2, 2], [-3, 5, 1, 0], [6, -4, 0, -5], [-9, 5, -5, 12]]
LAY_B = [-9, 5, 7, 11]
PROPIEDADES_DE_LA_TAREA = [
    "(Aᵀ)ᵀ = A", "(A + B)ᵀ = Aᵀ + Bᵀ", "(kA)ᵀ = kAᵀ", "(AB)ᵀ = BᵀAᵀ", "A(B + C) = AB + AC", "(AB)C = A(BC)",
    "(A⁻¹)⁻¹ = A", "(AB)⁻¹ = B⁻¹A⁻¹", "(Aᵀ)⁻¹ = (A⁻¹)ᵀ", "A·A⁻¹ = I",
    "det(Aᵀ) = det(A)", "det(AB) = det(A)·det(B)", "det(A⁻¹) = 1/det(A)", "det(kA) = kⁿ·det(A)",
    "Permutación de filas: det cambia de signo", "Reemplazo Fi ← Fi + kFj: det se conserva",
    "Multiplicar una fila por k: det se multiplica por k", "det(triangular) = producto de la diagonal",
]


def sesion_consola(funcion, respuestas):
    """Ejecuta una función de consola con respuestas simuladas y retorna (resultado, texto mostrado)."""
    pendientes, mostrado = iter(respuestas), []
    resultado = funcion(entrada=lambda mensaje: (mostrado.append(mensaje), next(pendientes))[1],
                        salida=lambda texto="": mostrado.append(str(texto)))
    return resultado, "\n".join(mostrado)


def retorna_valor(funcion):
    """Indica si una función retorna algún valor distinto de None, sin contar las funciones anidadas.

    Entrada: nodo ast.FunctionDef. Salida: True o False.
    """
    pendientes = list(funcion.body)
    while pendientes:
        nodo = pendientes.pop()
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        if isinstance(nodo, ast.Return) and nodo.value is not None and not (
                isinstance(nodo.value, ast.Constant) and nodo.value.value is None):
            return True
        pendientes.extend(ast.iter_child_nodes(nodo))
    return False


class ReglasTecnicas(unittest.TestCase):
    """Reglas técnicas: librerías, funciones puras, documentación y código comentado."""
    def test_sin_numpy_scipy_ni_math(self):
        """Comprueba que ningún archivo importa NumPy, SciPy ni math."""
        for ruta in ARCHIVOS:
            for nodo in ast.walk(ast.parse(ruta.read_text(encoding="utf-8"))):
                if isinstance(nodo, ast.Import):
                    nombres = [alias.name for alias in nodo.names]
                elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0:
                    nombres = [nodo.module]
                else:
                    continue
                for nombre in nombres:
                    with self.subTest(archivo=ruta.name, modulo=nombre):
                        self.assertNotIn(nombre.split(".")[0], {"numpy", "scipy", "math", "sympy"})

    def test_modulos_de_calculo_son_funciones_puras(self):
        """Comprueba que los módulos de cálculo no usan input() ni print()."""
        for ruta in [*(RAIZ / "modulos").glob("*.py"), *(RAIZ / "teoremas").glob("*.py")]:
            llamadas = {nodo.func.id for nodo in ast.walk(ast.parse(ruta.read_text(encoding="utf-8")))
                        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)}
            with self.subTest(archivo=ruta.name):
                self.assertFalse(llamadas & {"input", "print"})

    def test_docstrings_de_modulo_y_de_cada_funcion(self):
        """Comprueba que cada archivo y cada función tienen docstring con el formato de la guía."""
        for ruta in ARCHIVOS:
            arbol = ast.parse(ruta.read_text(encoding="utf-8"))
            with self.subTest(archivo=str(ruta.relative_to(RAIZ))):
                docstring = ast.get_docstring(arbol) or ""
                self.assertIn("Unidad", docstring)
                self.assertIn("Autores", docstring)
                sin_docstring = [nodo.name for nodo in ast.walk(arbol)
                                 if isinstance(nodo, (ast.FunctionDef, ast.ClassDef)) and not ast.get_docstring(nodo)]
                self.assertEqual(sin_docstring, [])
                fuera_de_formato = []
                for nodo in ast.walk(arbol):
                    if not isinstance(nodo, ast.FunctionDef):
                        continue
                    texto = ast.get_docstring(nodo)
                    entradas = [a.arg for a in nodo.args.args + nodo.args.kwonlyargs
                                if a.arg != "self" and not a.arg.startswith("_")]
                    if (len([linea for linea in texto.splitlines() if linea.strip()]) > 3
                            or (entradas and "Entrada" not in texto)
                            or (retorna_valor(nodo) and "Salida" not in texto)):
                        fuera_de_formato.append(nodo.name)
                self.assertEqual(fuera_de_formato, [])

    def test_sin_codigo_comentado(self):
        """Comprueba que no queda código comentado (código muerto)."""
        patron = re.compile(r"^#\s*(def |class |return\b|import |from \w+ import|print\(|[a-z_][a-z0-9_]*(\[[^\]]*\])?\s*=[^=])")
        for ruta in ARCHIVOS:
            for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
                comentario = linea.strip()
                if comentario.startswith("#"):
                    with self.subTest(archivo=ruta.name, linea=numero):
                        self.assertIsNone(patron.match(comentario), comentario)

    def test_mcd_y_mcm_nativos(self):
        """Comprueba el mcd y el mcm propios que reemplazan al módulo math."""
        self.assertEqual(m.maximo_comun_divisor(84, -36), 12)
        self.assertEqual(m.minimo_comun_multiplo([4, 6, 10]), 60)
        self.assertEqual(m.minimo_comun_multiplo([]), 1)
        relacion = m.analizar_independencia([[1, 2], [2, 4]])["relacion"]
        self.assertTrue(all(c.denominator == 1 for c in relacion))


class FactorizacionLU(unittest.TestCase):
    """Módulo LU: mensajes exactos, reutilización y verificación."""
    def test_multiplicador_como_en_el_ejemplo_de_la_guia(self):
        """Comprueba calcular_multiplicador con el ejemplo de la guía."""
        matriz_U = [[F(2), F(1)], [F(6), F(4)]]
        self.assertEqual(lu.calcular_multiplicador(matriz_U, 1, 0, 0), 3)

    def test_mensajes_exactos_de_la_salida(self):
        """Comprueba los mensajes exactos de verificación que pide la guía."""
        resultado = lu.resolver_lu(LAY_A, LAY_B)
        self.assertEqual(resultado["verificacion_factorizacion"]["mensaje"], "La factorización es correcta (L · U == A)")
        self.assertEqual(resultado["comprobacion"]["mensaje"], "Comprobación exitosa: A · x == b")
        lineas = "\n".join(lu.formatear_resultado_lu(resultado))
        for texto in ("Matriz L:", "Matriz U:", "La factorización es correcta (L · U == A)", "Vector intermedio y",
                      "Vector solución x", "Comprobación exitosa: A · x == b"):
            self.assertIn(texto, lineas)
        sin_lu = lu.resolver_lu([[0, 1], [1, 1]], [1, 2])
        self.assertEqual(sin_lu["mensaje"],
                         "La matriz no admite Factorización LU sin permutación (requiere pivoteo parcial PA = LU)")
        self.assertIsNone(sin_lu["matriz_L"])

    def test_reutiliza_funciones_de_la_calculadora(self):
        """Comprueba que el módulo LU reutiliza las funciones de la Calculadora."""
        espias = {nombre: patch.object(lu, nombre, wraps=getattr(m, nombre)) for nombre in
                  ("multiplicar_matrices", "multiplicar_matriz_vector", "son_iguales", "sumar_multiplo_fila",
                   "buscar_fila_pivote", "obtener_solucion_unica")}
        llamadas = {}
        for nombre, espia in espias.items():
            llamadas[nombre] = espia.start()
        try:
            lu.resolver_lu(LAY_A, LAY_B)
        finally:
            patch.stopall()
        for nombre, simulacro in llamadas.items():
            with self.subTest(funcion=nombre):
                self.assertTrue(simulacro.called)
        definidas = {nodo.name for nodo in ast.walk(ast.parse((RAIZ / "modulos/modulo_lu.py").read_text(encoding="utf-8")))
                     if isinstance(nodo, ast.FunctionDef)}
        self.assertFalse(definidas & {"multiplicar_matrices", "producto", "transpuesta", "transponer_matriz",
                                      "son_iguales", "_producto", "_producto_vector"})

    def test_reduccion_de_las_matrices_aumentadas(self):
        """Comprueba que [L | b] y [U | y] se reducen hasta obtener y y x."""
        resultado = lu.resolver_lu(LAY_A, LAY_B)
        reducida_L = resultado["adelante"]["matriz_reducida"]
        self.assertEqual([fila[:4] for fila in reducida_L], m.matriz_identidad(4))
        self.assertEqual([fila[-1] for fila in reducida_L], [-9, -4, 5, 1])
        reducida_U = resultado["atras"]["matriz_reducida"]
        self.assertEqual([fila[:4] for fila in reducida_U], m.matriz_identidad(4))
        self.assertEqual([fila[-1] for fila in reducida_U], [3, 4, -6, -1])

    def test_verificacion_detecta_factorizacion_incorrecta(self):
        """Comprueba que se detecta una L alterada con el mensaje de factorización incorrecta."""
        resultado = lu.resolver_lu(LAY_A, LAY_B)
        matriz_L = [fila[:] for fila in resultado["matriz_L"]]
        matriz_L[2][0] += 1
        verificacion = lu.verificar_factorizacion(LAY_A, matriz_L, resultado["matriz_U"])
        self.assertFalse(verificacion["correcta"])
        self.assertEqual(verificacion["mensaje"], "La factorización no es correcta (L · U != A)")
        comprobacion = lu.comprobar_solucion(LAY_A, [3, 4, -6, 0], LAY_B)
        self.assertFalse(comprobacion["correcta"])


class CoberturaDePropiedades(unittest.TestCase):
    """Tabla completa de propiedades, diagnóstico y encadenamiento."""
    def matrices(self, n):
        """Retorna matrices A, B y C invertibles de orden n para las pruebas."""
        A = [[F(i + 2) if i == j else F(1, i + j + 2) for j in range(n)] for i in range(n)]
        B = [[F(j + 1) if i == j else F(-1, 3) if i > j else F(0) for j in range(n)] for i in range(n)]
        C = [[F((i + 1) * (j + 2), 3) for j in range(n)] for i in range(n)]
        return A, B, C

    def test_tabla_completa_con_diagnostico(self):
        """Comprueba la tabla completa de propiedades con su diagnóstico para órdenes 1 a 4."""
        for n in (1, 2, 3, 4):
            A, B, C = self.matrices(n)
            informe = m.verificar_propiedades_clave(A, B, C, F(-3, 2))
            with self.subTest(n=n):
                self.assertEqual([r["propiedad"] for r in informe["resultados"]], PROPIEDADES_DE_LA_TAREA)
                for resultado in informe["resultados"]:
                    if n == 1 and resultado["categoria"] == "Efecto de operaciones de fila" and \
                            not resultado["propiedad"].startswith("det(triangular)"):
                        self.assertTrue(resultado["diagnostico"].startswith("No aplica"))
                    else:
                        self.assertEqual(resultado["diagnostico"], "Se cumple", resultado["propiedad"])
                        self.assertTrue(resultado["pasos"])

    def test_diagnostico_no_se_cumple_si_falla_una_funcion_interna(self):
        """Comprueba que, si una función interna falla, el diagnóstico es «No se cumple»."""
        A, B, C = self.matrices(3)
        with patch.object(m, "transponer_matriz", lambda X: [[F(0)] * len(X) for _ in X[0]]):
            informe = m.verificar_propiedades_clave(A, B, C, 2)
        diagnosticos = {r["propiedad"]: r["diagnostico"] for r in informe["resultados"]}
        self.assertEqual(diagnosticos["(Aᵀ)ᵀ = A"], "No se cumple")

    def test_encadenamiento_reutiliza_AB(self):
        """Comprueba que AB se calcula una sola vez y se reutiliza."""
        A, B, C = self.matrices(3)
        with patch.object(m, "multiplicar_matrices", wraps=m.multiplicar_matrices) as producto:
            informe = m.verificar_propiedades_clave(A, B, C, 2)
        productos_AB = [llamada for llamada in producto.call_args_list
                        if llamada.args[0] == A and llamada.args[1] == B]
        self.assertEqual(len(productos_AB), 1)
        self.assertEqual(informe["intermedios"]["AB"], m.multiplicar_matrices(A, B))

    def test_no_aplica_explica_la_hipotesis(self):
        """Comprueba que «No aplica» explica la hipótesis que falla."""
        informe = m.verificar_propiedades_clave([[1, 2], [2, 4]], [[1, 0], [0, 1]], [[1, 1], [0, 1]], 2)
        diagnosticos = {r["propiedad"]: r["diagnostico"] for r in informe["resultados"]}
        self.assertIn("singular", diagnosticos["(A⁻¹)⁻¹ = A"])
        self.assertEqual(diagnosticos["det(kA) = kⁿ·det(A)"], "Se cumple")
        informe = m.verificar_propiedades_clave([[1, 2, 3]], None, None, 2)
        diagnosticos = {r["propiedad"]: r["diagnostico"] for r in informe["resultados"]}
        self.assertEqual(diagnosticos["(Aᵀ)ᵀ = A"], "Se cumple")
        self.assertEqual(diagnosticos["(AB)ᵀ = BᵀAᵀ"], "No aplica: falta la matriz B.")
        self.assertEqual(diagnosticos["det(Aᵀ) = det(A)"], "No aplica: A debe ser cuadrada.")

    def test_det_kA_en_las_propiedades_avanzadas(self):
        """Comprueba det(kA) = kⁿ·det(A) como propiedad avanzada con su demostración."""
        self.assertEqual(m.PROPIEDADES_AVANZADAS["det_escalar_matriz"], "det(kA) = kⁿ·det(A)")
        self.assertIn("det_escalar_matriz", DEMOSTRACIONES_PROPIEDADES)
        A = [[F(1, 2), 2, 0], [1, -1, 3], [0, 4, F(2, 3)]]
        informe = d.informe_propiedad_avanzada("det_escalar_matriz", {"A": A}, {"k": F(-2, 3)})
        self.assertTrue(informe["verificacion"]["correcto"])
        self.assertEqual(informe["lados"][0]["resultado"], F(-2, 3) ** 3 * m.determinante(A))

    def test_informe_de_cobertura_para_la_gui(self):
        """Comprueba el informe de cobertura que usa la GUI."""
        A, B, C = self.matrices(2)
        informe = m.verificar_propiedades_clave(A, B, C, 2)
        vistas = d.informe_cobertura(informe, {"A": A, "B": B, "C": C})
        self.assertEqual(len(vistas["procedimiento"]), 1 + len(PROPIEDADES_DE_LA_TAREA))
        self.assertTrue(vistas["verificacion"]["correcto"])
        self.assertTrue(all("Se cumple" in e["conclusion"] for e in vistas["verificacion"]["etapas"]))


class MenuDeConsola(unittest.TestCase):
    """Menú principal de consola y reentrada de datos."""
    def test_opcion_en_el_menu_principal(self):
        """Comprueba que el menú principal ofrece la opción del módulo LU."""
        self.assertIn(("2", "Factorización LU y solución Ax = b"), main.OPCIONES_MENU_PRINCIPAL)
        _, texto = sesion_consola(main.menu_principal, ["S"])
        self.assertIn("2. Factorización LU y solución Ax = b", texto)

    def test_logotipo_y_teoremas_del_modulo(self):
        """Comprueba el logotipo y la opción «0. Ver Teoremas Clave del Módulo»."""
        _, texto = sesion_consola(main.menu_factorizacion_lu, ["0", "V"])
        self.assertIn(LOGO_LU, texto)
        self.assertIn("0. Ver Teoremas Clave del Módulo", texto)
        self.assertTrue(all(titulo in texto for titulo, _ in TEOREMAS_LU))

    def test_reentrada_de_datos_invalidos_sin_colapsar(self):
        """Comprueba que los datos inválidos se vuelven a pedir sin cerrar el programa."""
        respuestas = ["0", "dos", "2", "11", "2", "1 x", "1/2 1/3", "1 2 3", "1 -1", "5/6", "1/0 0", "5/6 0"]
        resultado, texto = sesion_consola(main.ejecutar_factorizacion_lu, respuestas)
        self.assertEqual(texto.count("Error:"), 7)
        self.assertEqual(resultado["solucion"], [1, 1])
        for mensaje in ("La factorización es correcta (L · U == A)", "Comprobación exitosa: A · x == b"):
            self.assertIn(mensaje, texto)

    def test_sin_lu_muestra_el_mensaje_de_pivoteo(self):
        """Comprueba el mensaje de pivoteo parcial cuando no existe A = LU."""
        _, texto = sesion_consola(main.ejecutar_factorizacion_lu, ["2", "2", "0 1", "1 1", "1 2"])
        self.assertIn("La matriz no admite Factorización LU sin permutación (requiere pivoteo parcial PA = LU)", texto)

    def test_verificador_de_propiedades_en_consola(self):
        """Comprueba el verificador de propiedades desde la consola."""
        respuestas = ["2", "2", "1 2", "3 4", "2", "2", "2 0", "1 3", "2", "2", "0 1", "1 1", "3"]
        informe, texto = sesion_consola(main.ejecutar_verificador_propiedades, respuestas)
        self.assertEqual(informe["cumplidas"], informe["evaluadas"])
        self.assertEqual(texto.count("Se cumple"), 18)

    def test_main_con_consola(self):
        """Comprueba que main con --consola abre el menú de texto."""
        salida = io.StringIO()
        with patch("sys.stdin", io.StringIO("2\n0\nV\nS\n")), contextlib.redirect_stdout(salida):
            main.main(["--consola"])
        texto = salida.getvalue()
        self.assertIn("2. Factorización LU y solución Ax = b", texto)
        self.assertIn("Existencia de A = LU", texto)


class InterfazGrafica(unittest.TestCase):
    """Página LU, modo «Cobertura completa» y det(kA) en la GUI."""
    @classmethod
    def setUpClass(cls):
        """Carga la GUI una vez para todas las pruebas de la clase."""
        cls.gui = main.cargar_aplicacion()

    def test_pagina_lu_cobertura_y_det_kA_con_widgets_reales(self):
        """Comprueba con widgets reales la página LU, la cobertura y det(kA)."""
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
            pagina = app.ir_a("lu")
            self.assertEqual(pagina.titulo, "Factorización LU y solución Ax = b")
            pagina.resolver()
            bombear()
            self.assertEqual(pagina.resultado["comprobacion"]["mensaje"], "Comprobación exitosa: A · x == b")
            self.assertIn("Comprobación exitosa: A · x == b", pagina.texto_copiar(pagina.resultado))
            pagina.mostrar_teoremas()
            bombear(1.5)
            self.assertEqual(len(pagina.area_resultado.interior.winfo_children()), 1 + len(TEOREMAS_LU))

            matrices = app.ir_a("matrices")
            matrices._cambiar_modo("Cobertura completa")
            matrices.resolver()
            bombear()
            self.assertTrue(matrices.hay_resultado)
            self.assertEqual(len(matrices.panel_pasos.pasos), 1 + len(PROPIEDADES_DE_LA_TAREA))

            determinantes = app.ir_a("determinantes")
            determinantes.operacion.set("det(kA) = kⁿ·det(A)")
            determinantes.escalar.delete(0, "end")
            determinantes.escalar.insert(0, "-1/2")
            determinantes.resolver()
            bombear()
            self.assertTrue(determinantes.informe["verificacion"]["correcto"])
            self.assertFalse(errores, errores)
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()

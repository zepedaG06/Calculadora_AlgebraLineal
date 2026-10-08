"""Auditoría reproducible: oráculos independientes y contratos de la GUI."""
import itertools
import random
import time
import unittest
from copy import deepcopy
from fractions import Fraction as F
from unittest.mock import Mock, patch
import main
from modulos import modulo_matrices as m
from modulos import informes as d


def leibniz(A):
    n = len(A)
    total = F(0)
    for p in itertools.permutations(range(n)):
        term = F((-1) ** sum(p[i] > p[j] for i in range(n) for j in range(i + 1, n)))
        for i, j in enumerate(p):
            term *= F(A[i][j])
        total += term
    return total


def product(A, B):
    return [[sum((F(a) * F(b) for a, b in zip(row, col)), F(0))
             for col in zip(*B)] for row in A]


def identity(n):
    return [[F(i == j) for j in range(n)] for i in range(n)]


def families(n):
    I = identity(n)
    diagonal = [[F((-1)**i * (i+2), i+1) if i == j else F(0)
                 for j in range(n)] for i in range(n)]
    upper = [[diagonal[i][j] if i == j else F(i-j, j+1) if j > i else F(0)
              for j in range(n)] for i in range(n)]
    lower = [list(row) for row in zip(*upper)]
    zero_row = deepcopy(upper)
    zero_row[-1] = [F(0)] * n
    zero_col = deepcopy(lower)
    for row in zero_col:
        row[-1] = F(0)
    cases = [I, diagonal, upper, lower, zero_row, zero_col]
    if n > 1:
        for factor in (1, F(-3, 2)):
            repeated = deepcopy(upper)
            repeated[-1] = [factor * x for x in repeated[0]]
            cases.append(repeated)
        swapped = deepcopy(I)
        swapped[0], swapped[-1] = swapped[-1], swapped[0]
        cases.append(swapped)
    return cases


class AuditoriaExacta(unittest.TestCase):
    def check_matrix(self, A, expected):
        original = deepcopy(A)
        methods = ['triangular', 'cofactores']
        methods += ['2x2'] if len(A) == 2 else ['sarrus'] if len(A) == 3 else []
        for method in methods:
            report = d.informe_determinante(A, method)
            self.assertEqual(report['resultado'], expected)
            self.assertIsInstance(report['resultado'], F)
            self.assertTrue(report['verificacion']['correcto'])
            self.assertTrue(report['procedimiento'])
            self.assertTrue(report['conclusion'])
        inverses = []
        for method in ('gauss_jordan', 'adjunta'):
            report = d.informe_inversa(A, method)
            self.assertTrue(report['verificacion']['correcto'])
            self.assertEqual(report['definido'], expected != 0)
            self.assertTrue(report['procedimiento'])
            if expected:
                inv = report['resultado']
                self.assertTrue(all(isinstance(x, F) for row in inv for x in row))
                self.assertEqual(product(A, inv), identity(len(A)))
                self.assertEqual(product(inv, A), identity(len(A)))
                inverses.append(inv)
            else:
                self.assertIsNone(report['resultado'])
                self.assertIn('No tiene inversa', report['conclusion'])
        if expected:
            self.assertEqual(*inverses)
        self.assertEqual(A, original)

    def test_ejercicios_A_a_E(self):
        cases = [([[1, 2], [3, 4]], -2, [[-2, 1], [F(3, 2), F(-1, 2)]]),
                 ([[1, 2], [2, 4]], 0, None), (identity(3), 1, identity(3)),
                 ([[2, 0, 0], [0, 3, 0], [0, 0, 4]], 24,
                  [[F(1, 2), 0, 0], [0, F(1, 3), 0], [0, 0, F(1, 4)]]),
                 ([[0, 1], [1, 0]], -1, [[0, 1], [1, 0]])]
        for A, det, inv in cases:
            with self.subTest(A=A):
                self.check_matrix(A, F(det))
                if inv is not None:
                    self.assertEqual(m.inversa_adjunta(A), inv)

    def test_familias_ordenes_uno_a_diez(self):
        for n in range(1, 11):
            for index, A in enumerate(families(n)):
                # Familias triangulares: producto diagonal; permutación: signo.
                expected = F(1)
                for i in range(n):
                    expected *= A[i][i]
                if n > 1 and index == 8:
                    expected = F(-1)
                elif n > 1 and index in (6, 7):
                    expected = F(0)
                for method in ('triangular', 'cofactores'):
                    with self.subTest(n=n, family=index, method=method):
                        self.assertEqual(m.determinante(A, method), expected)
                with self.subTest(n=n, family=index):
                    self.check_matrix(A, expected)

    def test_aleatorios_semilla_fija_oraculo_hasta_seis(self):
        rng = random.Random(20261008)
        for n in range(1, 7):
            for case in range(5):
                A = [[F(rng.randint(-5, 5), rng.randint(1, 5)) for j in range(n)] for i in range(n)]
                with self.subTest(n=n, case=case):
                    self.check_matrix(A, leibniz(A))
                    for row in range(n):
                        self.assertEqual(m.calcular_determinante(A, 'cofactores', row)['determinante'], leibniz(A))

    def test_decimales_y_numeros_grandes(self):
        for A in ([['0.1', '-0.2'], ['0.3', '0.4']],
                  [[10**30, -3], [7, 10**25]], [[F(-7, 11)]]):
            with self.subTest(A=A):
                self.check_matrix(A, leibniz(A))

    def test_no_finitos_y_metodo_invalido_singular(self):
        for value in (float('inf'), float('-inf'), float('nan'), '1/0', None):
            for operation in (m.determinante, m.inversa_gauss_jordan, m.inversa_adjunta):
                with self.subTest(value=value, operation=operation), self.assertRaises(ValueError):
                    operation([[value]])
        for A in ([[0]], [[1]]):
            with self.subTest(A=A), self.assertRaisesRegex(ValueError, 'Método'):
                d.informe_inversa(A, 'inexistente')

    def test_propiedades_lados_independientes(self):
        rng = random.Random(17)
        for n in range(1, 7):
            A = [[F(1) if i == j else F(rng.randint(-3, 3)) if j > i else F(0)
                  for j in range(n)] for i in range(n)]
            B = [list(row) for row in zip(*A)]
            ai, bi = m.inversa_adjunta(A), m.inversa_adjunta(B)
            expected = {'inversa_inversa': A,
                        'inversa_producto': product(bi, ai),
                        'inversa_transpuesta': [list(row) for row in zip(*ai)],
                        'det_inversa': F(1) / leibniz(A), 'det_triangular': F(1)}
            for key, rhs in expected.items():
                with self.subTest(n=n, key=key):
                    report = d.informe_propiedad_avanzada(key, {'A': A, 'B': B})
                    self.assertTrue(report['verificacion']['correcto'])
                    self.assertEqual(report['lados'][0]['resultado'], rhs)
                    self.assertEqual(report['lados'][1]['resultado'], rhs)
            if n > 1:
                for k in (F(0), F(-3, 2), F(100000)):
                    for key in ('det_intercambio', 'det_escalar_fila', 'det_suma_fila'):
                        transformed = deepcopy(A)
                        if key == 'det_intercambio':
                            transformed[0], transformed[1] = transformed[1], transformed[0]
                        elif key == 'det_escalar_fila':
                            transformed[0] = [k*x for x in A[0]]
                        else:
                            transformed[0] = [x+k*y for x, y in zip(A[0], A[1])]
                        with self.subTest(n=n, key=key, k=k):
                            r = d.informe_propiedad_avanzada(key, {'A': A}, {'k': k})
                            self.assertTrue(r['verificacion']['correcto'])
                            self.assertEqual(r['lados'][0]['resultado'], leibniz(transformed))


class AuditoriaEntradaYPresentacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gui = main.cargar_aplicacion()

    def page(self, text, operation='Inversa Gauss-Jordan'):
        page = object.__new__(self.gui.PaginaDeterminantes)
        page.entradas = {'A': Mock(), 'B': Mock()}
        page.entradas['A'].get.return_value = text
        page.entradas['B'].get.return_value = '1 0\n0 1'
        page.operacion = Mock()
        page.operacion.get.return_value = operation
        page.escalar = Mock()
        page.escalar.get.return_value = '2'
        for attr in ('app', 'area_resultado', 'panel_pasos', 'area_verificacion', 'pestanas'):
            setattr(page, attr, Mock())
        return page

    def test_entradas_invalidas_tres_vistas_sin_excepcion(self):
        for text in ('', '1 2\n3', '1 2 3\n4 5 6', 'abc', '1/', '1/0', ';',
                     '1 ' * 11, '\n'.join(['1'] * 11)):
            with self.subTest(text=text):
                page = self.page(text)
                page.resolver()
                self.assertFalse(page.informe['definido'])
                self.assertFalse(page.informe['verificacion']['correcto'])
                self.assertTrue(page.informe['conclusion'])
                page.app.notificar.assert_called_once()
                page.panel_pasos.mostrar_pasos.assert_called_once()
                page.area_verificacion.llenar.assert_called_once()

    def test_entrada_decimal_coma_fraccion_y_negativos(self):
        page = self.page('0,1; -1/2\n3; 0.4')
        self.assertEqual(page._leer('A'), [[F(1, 10), F(-1, 2)], [F(3), F(2, 5)]])

    def test_todas_las_operaciones_gui(self):
        for operation in self.gui.PaginaDeterminantes.OPERACIONES:
            text = '1 2 3\n0 1 4\n0 0 1' if 'Sarrus' in operation else '1 2\n0 1'
            page = self.page(text, operation)
            page.resolver()
            with self.subTest(operation=operation):
                self.assertTrue(page.informe['definido'])
                self.assertTrue(page.informe['verificacion']['correcto'])
                data = page.informe['datos_resultado']
                self.assertEqual(data['formula'], operation)
                self.assertEqual(data['valores'][0]['valor'], page._leer('A'))

    def test_resultado_renderiza_original_y_operacion(self):
        page = self.page('1 2\n3 4')
        page.resolver()
        with patch.object(self.gui, 'tarjeta_estado'), patch.object(self.gui, 'tarjeta_seccion'), patch.object(self.gui, 'cuerpo_etapa') as render:
            for constructor in self.gui.constructores_informe(page.informe):
                constructor(Mock())
            self.assertTrue(any(call.args[1] == page.informe['datos_resultado'] for call in render.call_args_list))

    def test_widgets_reales_pestanas_pasos_y_scroll(self):
        if self.gui.ctk is None:
            self.skipTest('CustomTkinter no disponible')
        try:
            app = self.gui.AplicacionAlgebraLineal()
        except self.gui.tk.TclError as error:
            self.skipTest(f'Pantalla Tk no disponible: {error}')
        errors = []
        app.report_callback_exception = lambda *args: errors.append(args)
        app.withdraw()
        try:
            app.cambiar_pagina('determinantes')
            page = app.paginas['determinantes']
            def pump():
                end = time.monotonic() + 0.25
                while time.monotonic() < end:
                    app.update()
                    time.sleep(0.005)
            for operation in page.OPERACIONES:
                page.operacion.set(operation)
                page.entradas['A'].delete('1.0', 'end')
                page.entradas['A'].insert('1.0', '1 2 3\n0 1 4\n0 0 1' if 'Sarrus' in operation else '1 2\n0 1')
                page.resolver()
                pump()
                self.assertTrue(page.informe['verificacion']['correcto'], operation)
                for tab in ('Resultado', 'Procedimiento', 'Verificación'):
                    page.pestanas.set(tab)
                    pump()
                    self.assertEqual(page.pestanas.get(), tab)
                panel = page.panel_pasos
                panel.selector.set('Paso a paso')
                panel._cambiar_modo()
                panel.ir_a(len(panel.pasos)-1)
                pump()
                self.assertEqual(panel.indice, len(panel.pasos)-1)
                panel.ir_a(0)
                self.assertEqual(panel.indice, 0)
                panel.selector.set('Todos')
                panel._cambiar_modo()
            # Comprobar el desplazamiento con contenido que excede ambos ejes.
            area = page.area_verificacion
            area.canvas.configure(scrollregion=(0, 0, 3000, 6000))
            area.canvas.xview_moveto(0)
            area.canvas.yview_moveto(0)
            before = (area.canvas.xview()[0], area.canvas.yview()[0])
            area.desplazar(150, horizontal=True)
            area.desplazar(150)
            self.assertGreater(area.canvas.xview()[0], before[0])
            self.assertGreater(area.canvas.yview()[0], before[1])
            for text in ('1 2\n2 4', 'abc', ''):
                page.entradas['A'].delete('1.0', 'end')
                page.entradas['A'].insert('1.0', text)
                page.operacion.set('Inversa Gauss-Jordan')
                page.resolver()
                pump()
                self.assertFalse(page.informe['definido'])
            self.assertFalse(errors, errors)
        finally:
            app.destroy()


if __name__ == '__main__':
    unittest.main()

"""Regresiones de desarrollos completos, condiciones y evaluación independiente."""
from copy import deepcopy
from fractions import Fraction as F
from itertools import permutations
import random
import unittest
from unittest.mock import Mock, patch

from modulos import modulo_matrices as m
from modulos import informes as d
import main


def producto_ref(A, B):
    return [[sum((F(a)*F(b) for a, b in zip(fila, col)), F(0))
             for col in zip(*B)] for fila in A]


def det_ref(A):
    if not A:
        return F(1)
    total = F(0)
    for p in permutations(range(len(A))):
        signo = (-1)**sum(p[i] > p[j] for i in range(len(p)) for j in range(i+1, len(p)))
        termino = F(signo)
        for i, j in enumerate(p):
            termino *= A[i][j]
        total += termino
    return total


def inversa_ref(A):
    det = det_ref(A)
    return [[(-1)**(i+j)*det_ref([[x for k, x in enumerate(fila) if k != i]
                                for l, fila in enumerate(A) if l != j])/det
             for j in range(len(A))] for i in range(len(A))]


def etapas_recursivas(etapas):
    for e in etapas:
        yield e
        yield from etapas_recursivas(e.get('subpasos', []))


class AuditoriaExpresiones(unittest.TestCase):
    A = [[F(1, 2), -2], [3, 1]]
    B = [[1, 0], [-1, F(2, 3)]]
    C = [[0, -3], [2, 1]]

    def resolver(self, expresion, datos=None):
        datos = datos or {'A': self.A, 'B': self.B, 'C': self.C}
        original = deepcopy(datos)
        r = m.resolver_expresion_matricial(expresion, datos, {'r': F(-2, 3), 's': F(3, 2)})
        self.assertIsNone(r['error'])
        v = m.verificar_resolucion(r)
        self.assertTrue(v['correcto'], expresion)
        self.assertEqual(datos, original)
        for p in r['operaciones']:
            self.assertTrue(p['operandos'])
            self.assertTrue(p['regla'])
            self.assertTrue(p['condicion']['cumple'])
            if p['tipo'] in ('producto', 'suma', 'resta', 'escalar', 'transpuesta'):
                self.assertEqual(len(p['entradas']), len(p['resultado'])*len(p['resultado'][0]))
                self.assertTrue(all(e['lineas'] for e in p['entradas']))
        return r, v

    def test_transpuesta_producto_dos_rutas_completas(self):
        r, v = self.resolver('(AB)^T')
        rhs = v['identidad']['resolucion']
        self.assertEqual([p['expresion'] for p in r['operaciones']], ['AB', '(AB)ᵀ'])
        self.assertEqual([p['expresion'] for p in rhs['operaciones']], ['Bᵀ', 'Aᵀ', 'BᵀAᵀ'])
        self.assertEqual(r['resultado'], [list(c) for c in zip(*producto_ref(self.A, self.B))])
        pasos = d.pasos_expresion(r, v)
        self.assertEqual([p['titulo'] for p in pasos if p['tipo'] == 'seccion'],
                         ['Lado izquierdo: (AB)ᵀ', 'Lado derecho: BᵀAᵀ'])
        self.assertEqual(len(pasos[-1]['etapa']['calculos']), 4)
        self.assertIn('para las matrices ingresadas', pasos[-1]['etapa']['conclusion'])
        self.assertEqual({n for n, _ in rhs['pasos'][0]['matrices']}, {'A', 'B'})

    def test_distributividades_operaciones_intermedias(self):
        for texto, li, ld in [('A(B+C)', ['suma', 'producto'], ['producto', 'producto', 'suma']),
                              ('(A+B)C', ['suma', 'producto'], ['producto', 'producto', 'suma']),
                              ('A(B-C)', ['resta', 'producto'], ['producto', 'producto', 'resta'])]:
            with self.subTest(texto=texto):
                r, v = self.resolver(texto)
                self.assertEqual([p['tipo'] for p in r['operaciones']], li)
                self.assertEqual([p['tipo'] for p in v['identidad']['resolucion']['operaciones']], ld)

    def test_lista_completa_de_expresiones_y_anidamientos(self):
        for texto in ['AB', 'BA', 'A+B', 'A-B', '2A-3B+C', 'A^TB^T', 'B^TA^T',
                      '(A+B)^T', '(A-B)^T', '(ABC)^T', 'A^TBC',
                      '(A(B+C)-2B)^T', '(1/2)A-(3/4)B+C', 'r(A+B)',
                      '(rA)B', 'A(rB)', 'A^-1B^-1', '(A^-1)^-1', '(A^T)^-1']:
            with self.subTest(texto=texto):
                self.resolver(texto)

    def test_transpuesta_tres_factores_desarrolla_las_tres(self):
        _, v = self.resolver('(ABC)^T')
        pasos = v['identidad']['resolucion']['operaciones']
        self.assertEqual([p['expresion'] for p in pasos if p['tipo'] == 'transpuesta'], ['Cᵀ', 'Bᵀ', 'Aᵀ'])
        self.assertEqual(len([p for p in pasos if p['tipo'] == 'producto']), 2)

    def test_inversa_producto_det_y_reduccion_en_ambos_lados(self):
        r, v = self.resolver('(AB)^-1')
        rhs = v['identidad']['resolucion']
        self.assertEqual([p['tipo'] for p in rhs['operaciones']], ['inversa', 'inversa', 'producto'])
        self.assertEqual(r['resultado'], inversa_ref(producto_ref(self.A, self.B)))
        for p in [*r['operaciones'], *rhs['operaciones']]:
            if p['tipo'] == 'inversa':
                etapas = list(etapas_recursivas(p['etapas']))
                self.assertTrue(any(v['nombre'] == 'det(A)' for e in etapas for v in e['valores']))
                self.assertTrue(any(v['separador'] == 2 for e in etapas for v in e['valores']))
                self.assertTrue(any(e['calculos'] for e in etapas))

    def test_inversas_sintaxis_y_precedencia(self):
        for texto in ['A^-1', 'A^(-1)', 'A⁻¹']:
            r, _ = self.resolver(texto)
            self.assertEqual(r['resultado'], inversa_ref(self.A))
        for texto in ['A^2', 'A^-10', 'A^-1.5', 'A^-', 'A^(1)', 'A^-1/2', 'A=B', 'A//2']:
            with self.subTest(texto=texto), self.assertRaises(m.ErrorExpresion):
                m.analizar_expresion_matricial(texto)
        r, _ = self.resolver('-A^-1')
        self.assertEqual(r['resultado'], [[-x for x in fila] for fila in inversa_ref(self.A)])

    def test_inversa_tres_factores_desarrolla_cada_inversa(self):
        r, v = self.resolver('(ABC)^-1')
        self.assertEqual(r['resultado'], inversa_ref(producto_ref(producto_ref(self.A, self.B), self.C)))
        self.assertEqual([p['expresion'] for p in v['identidad']['resolucion']['operaciones'] if p['tipo'] == 'inversa'], ['C⁻¹', 'B⁻¹', 'A⁻¹'])

    def test_rectangulares_compatibles_y_dimensiones_incompatibles(self):
        A, B = [[1, -1, F(1, 2)], [0, 2, 3]], [[2], [0], [-1]]
        r, _ = self.resolver('(AB)^T', {'A': A, 'B': B})
        self.assertEqual(r['dimension'], (1, 2))
        for texto in ['BA', 'A+B', 'A^-1']:
            with self.subTest(texto=texto):
                r = m.resolver_expresion_matricial(texto, {'A': A, 'B': B})
                self.assertIsNotNone(r['error'])
                self.assertIsNone(r['resultado'])
                self.assertFalse(m.verificar_resolucion(r)['aplicable'])

    def test_producto_rectangular_invertible_no_impone_inversa_factores(self):
        r, v = self.resolver('(AB)^-1', {'A': [[1, 0]], 'B': [[2], [3]]})
        self.assertEqual(r['resultado'], [[F(1, 2)]])
        self.assertFalse(v['identidad']['definida'])
        self.assertIsNone(v['identidad']['ok'])
        self.assertIn('no evaluable', d.pasos_expresion(r, v)[-1]['etapa']['titulo'])

    def test_singular_no_es_identidad_falsa(self):
        r = m.resolver_expresion_matricial('(AB)^-1', {'A': [[1, 2], [2, 4]], 'B': self.B})
        self.assertIn('det(M)=0', r['error'])
        self.assertIsNone(r['identidad'])
        self.assertTrue(r['operaciones'][-1]['etapas'])

    def test_no_reutiliza_lado_izquierdo_y_detecta_corrupcion(self):
        r, v = self.resolver('(AB)^T')
        rhs = deepcopy(v['identidad']['resolucion']['resultado'])
        r['resultado'][0][0] += 1
        self.assertEqual(v['identidad']['resolucion']['resultado'], rhs)
        self.assertFalse(m.verificar_resolucion(r)['correcto'])

    def test_identidad_muestra_los_factores_reales_en_orden(self):
        _, v = self.resolver('A^TB^T')
        self.assertEqual(v['identidad']['enunciado'], 'AᵀBᵀ = (BA)ᵀ')
        self.assertNotEqual(producto_ref(self.A, self.B), producto_ref(self.B, self.A))

    def test_ordenes_y_productos_aleatorios_reproducibles(self):
        rng = random.Random(806)
        for n in (1, 2, 3, 5, 10):
            datos = {nombre: [[F(rng.randint(-3, 3), rng.randint(1, 4)) for _ in range(n)] for _ in range(n)] for nombre in 'ABC'}
            for texto in ('AB', '(AB)^T', 'A(B+C)', '(A+B)C', '(ABC)^T'):
                with self.subTest(n=n, texto=texto):
                    self.resolver(texto, datos)
            r, _ = self.resolver('AB', datos)
            self.assertEqual(r['resultado'], producto_ref(datos['A'], datos['B']))


class AuditoriaPropiedades(unittest.TestCase):
    def test_todo_el_catalogo_general_con_ambos_procedimientos(self):
        for n in (1, 2, 3, 5):
            datos = {nombre: [[F((i+1)*(j+2)+k, 3) for j in range(n)] for i in range(n)] for k, nombre in enumerate('ABC')}
            for p in m.PROPIEDADES_MATRICIALES:
                if not p['general']:
                    continue
                with self.subTest(n=n, clave=p['clave']):
                    r = m.verificar_propiedad_matricial(p['clave'], datos, {'r': F(-2, 3), 's': F(0)})
                    self.assertTrue(r['cumple'])
                    self.assertIn('para las matrices ingresadas', r['conclusion'])
                    for lado in r['lados'][:2]:
                        self.assertTrue(lado['resolucion']['pasos'])
                        self.assertTrue(m.verificar_resolucion(lado['resolucion'], False)['correcto'])

    def test_todas_las_propiedades_avanzadas_y_comprobacion_independiente(self):
        for n in (1, 2, 3, 5):
            A = [[F(i+2) if i == j else F(-1, 2) if j > i else F(0) for j in range(n)] for i in range(n)]
            B = [[F(j+1) if i == j else F(1, 3) if i > j else F(0) for j in range(n)] for i in range(n)]
            for clave in m.PROPIEDADES_AVANZADAS:
                if n == 1 and clave in ('det_intercambio', 'det_suma_fila'):
                    continue
                with self.subTest(n=n, clave=clave):
                    r = d.informe_propiedad_avanzada(clave, {'A': A, 'B': B}, {'k': F(-3, 2)})
                    self.assertTrue(r['definido'])
                    self.assertTrue(r['verificacion']['correcto'])
                    self.assertEqual(r['lados'][0]['resultado'], r['lados'][1]['resultado'])
                    self.assertTrue(all(l['etapas'] for l in r['lados']))
                    if clave == 'inversa_producto':
                        self.assertEqual(r['lados'][0]['resultado'], inversa_ref(producto_ref(A, B)))
                        self.assertTrue(any('A·A⁻¹ frente a I' == e['titulo'] for e in r['verificacion']['etapas']))
                    if clave == 'det_producto':
                        self.assertEqual(r['lados'][0]['resultado'], det_ref(A)*det_ref(B))

    def test_singular_con_procedimiento_y_diagnostico(self):
        for clave in ('inversa_inversa', 'inversa_producto', 'inversa_transpuesta', 'det_inversa'):
            r = d.informe_propiedad_avanzada(clave, {'A': [[1, 0], [0, 1]], 'B': [[1, 2], [2, 4]]} if clave == 'inversa_producto' else {'A': [[0]]})
            self.assertFalse(r['definido'])
            self.assertIn('singular', r['conclusion'])
            self.assertNotIn('No se cumple', r['conclusion'])
            self.assertTrue(r['procedimiento'])
            self.assertFalse(r['verificacion']['aplicable'])

    def test_det_producto_admite_singulares(self):
        r = d.informe_propiedad_avanzada('det_producto', {'A': [[0]], 'B': [[2]]})
        self.assertTrue(r['definido'])
        self.assertEqual(r['lados'][0]['resultado'], 0)

    def test_contraejemplos_y_condiciones(self):
        r = m.verificar_propiedad_matricial('no_conmutatividad', {'A': [[1, 2], [0, 1]], 'B': [[0, 1], [1, 0]]})
        self.assertFalse(r['cumple'])
        self.assertIn('contraejemplo', r['conclusion'])
        r = m.verificar_propiedad_matricial('transpuesta_producto', {'A': [[1, 2]], 'B': [[3, 4]]})
        self.assertIsNone(r['cumple'])
        self.assertNotIn('No se cumple', r['conclusion'])

    def test_eliminacion_con_aritmetica_real_y_certificados(self):
        r = m.resolver_sistema([[2, 1], [4, 3]], [1, -2])
        for p in r['pasos']:
            if p['tipo'] in ('escalado', 'eliminacion'):
                self.assertEqual(len(p['calculos']), 3)
        for A, b in (([[1, 2], [2, 4]], [1, 3]), ([[1, 0], [0, 1], [2, 3]], [0, 0, 0])):
            datos = m.resolver_sistema(A, b) if b != [0]*len(b) else m.analizar_independencia(A)
            v = d.verificacion_sistema(datos, independencia=b == [0]*len(b))
            self.assertTrue(v['correcto'])
            self.assertTrue(v['etapas'][0]['subpasos'])

    def test_apis_compatibles_tambien_exponen_los_desarrollos(self):
        A, B = [[1, 2], [3, 4]], [[2, 0], [0, 3]]
        for r in m.verificar_propiedades_transpuesta(A, B, F(-1, 2)).values():
            self.assertTrue(r['lados'])
            self.assertTrue(all(v['correcto'] for v in r['verificaciones']))
        for r in m.verificar_propiedades_algebraicas(A, B, A).values():
            self.assertEqual(len(r['lados']), 2)
            self.assertTrue(all(v['correcto'] for v in r['verificaciones']))
        r = m.procedimiento_operacion_matrices(A, 'producto', B)
        self.assertIn(m.matriz_a_texto(A, False), r['pasos'])
        self.assertTrue(r['verificacion']['correcto'])
        # La verificación debe revisar la salida pública, incluso si se corrompe
        # el producto primitivo que utiliza la API antigua.
        with patch.object(m, 'multiplicar_matrices', return_value=[[99, 99], [99, 99]]):
            r = m.procedimiento_operacion_matrices(A, 'producto', B)
        self.assertFalse(r['verificacion']['correcto'])


class AuditoriaIntegracionGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gui = main.cargar_aplicacion()

    def test_panel_recibe_ambos_lados_y_comparacion(self):
        pagina = object.__new__(self.gui.PaginaMatrices)
        for atributo in ('app', 'entrada_expresion', 'aviso', 'panel_pasos', 'area_resultado', 'area_verificacion', 'pestanas'):
            setattr(pagina, atributo, Mock())
        pagina.entrada_expresion.get.return_value = '(AB)^T'
        pagina._leer_matrices = Mock(return_value={'A': [[1, 2], [0, 1]], 'B': [[2, 0], [1, 3]]})
        pagina._leer_escalares = Mock(return_value={})
        pagina._resolver_expresion()
        pasos = pagina.panel_pasos.mostrar_pasos.call_args.args[0]
        self.assertEqual(len([p for p in pasos if p['tipo'] == 'seccion']), 2)
        self.assertEqual(pasos[-1]['tipo'], 'didactica')
        self.assertIn('Bᵀ', [p.get('expresion') for p in pasos])

    def test_error_frecuente_indefinido_no_invalida_la_propiedad(self):
        r = m.verificar_propiedad_matricial('transpuesta_producto', {'A': [[1, 2]], 'B': [[1, 2, 3], [4, 5, 6]]})
        self.assertTrue(r['cumple'])
        self.assertTrue(r['lados'][-1]['resolucion']['error'])
        with patch.object(self.gui, 'tarjeta_estado') as estado:
            self.gui.constructores_verificacion_propiedad(r)[0](Mock())
            self.assertEqual(estado.call_args.args[1], 'Cálculos verificados')
        r = m.verificar_propiedad_matricial('transpuesta_producto', {'A': [[1, 2]], 'B': [[1, 2]]})
        with patch.object(self.gui, 'tarjeta_estado') as estado:
            self.gui.constructores_verificacion_propiedad(r)[0](Mock())
            self.assertIn('no evaluable', estado.call_args.args[1])

    def test_verificacion_renderiza_tarjetas_completas(self):
        r = m.resolver_expresion_matricial('(AB)^T', {'A': [[1]], 'B': [[2]]})
        v = m.verificar_resolucion(r)
        with patch.object(self.gui, 'tarjeta_estado'), patch.object(self.gui, 'tarjeta_seccion'), \
             patch.object(self.gui, '_tarjeta_comparacion'), patch.object(self.gui, 'etiqueta'), \
             patch.object(self.gui, 'tarjeta_mensajes'), patch.object(self.gui, 'SeccionPlegable') as seccion, \
             patch.object(self.gui, 'tarjeta_paso_matricial') as tarjeta, patch.object(self.gui.ctk, 'CTkFrame'):
            for constructor in self.gui.constructores_verificacion(r, v):
                constructor(Mock())
            llamada = next(c for c in seccion.call_args_list if c.args[1] == 'Cálculos de la ruta alternativa')
            llamada.args[4](Mock())
            self.assertEqual(tarjeta.call_count, len(r['pasos']) + len(v['identidad']['resolucion']['pasos']))
            self.assertTrue(all(c.args[3] for c in tarjeta.call_args_list))

    def test_widgets_reales_muestran_transpuestas_inversas_y_comparaciones(self):
        if self.gui.ctk is None:
            self.skipTest('CustomTkinter no disponible')
        try:
            root = self.gui.ctk.CTk()
        except self.gui.tk.TclError as error:
            self.skipTest(f'Pantalla Tk no disponible: {error}')
        root.withdraw()
        errores = []
        root.report_callback_exception = lambda *args: errores.append(args)
        def textos(widget):
            resultado = []
            try:
                resultado.append(str(widget.cget('text')))
            except (ValueError, self.gui.tk.TclError):
                pass
            for hijo in widget.winfo_children():
                resultado.extend(textos(hijo))
            return resultado
        try:
            for expresion, esperados in [('(AB)^T', ['Calcular Aᵀ', 'Calcular Bᵀ', 'Verificación de ambos lados']),
                                         ('(AB)^-1', ['Calcular A⁻¹', 'Calcular B⁻¹', 'Construir [A | I]']),
                                         ('A(B+C)', ['Calcular B + C', 'Calcular AB', 'Calcular AC'])]:
                r = m.resolver_expresion_matricial(expresion, {'A': [[1, 2], [0, 1]], 'B': [[2, 0], [1, 3]], 'C': [[0, 1], [-1, 0]]})
                pasos = d.pasos_expresion(r, m.verificar_resolucion(r))
                frame = self.gui.ctk.CTkScrollableFrame(root)
                frame.pack(fill='both', expand=True)
                for i in range(len(pasos)):
                    self.gui.tarjeta_paso_matricial(frame, pasos, i, True).pack(fill='x')
                root.update_idletasks()
                contenido = '\n'.join(textos(frame))
                for esperado in esperados:
                    self.assertIn(esperado, contenido)
                self.assertIn('Lado izquierdo', contenido)
                self.assertIn('Lado derecho', contenido)
                frame.destroy()
            self.assertFalse(errores, errores)
        finally:
            for identificador in root.tk.splitlist(root.tk.call('after', 'info')):
                root.tk.call('after', 'cancel', identificador)
            root.destroy()


if __name__ == '__main__':
    unittest.main()

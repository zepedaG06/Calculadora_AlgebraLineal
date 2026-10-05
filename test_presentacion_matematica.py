"""Regresión de datos didácticos y comprobaciones independientes."""
from copy import deepcopy
from fractions import Fraction as F
import unittest
from modulos import modulo_matrices as m
from modulos import informes as d


class DeterminantesDidacticos(unittest.TestCase):
    def test_metodos_con_formulas_datos_y_verificacion(self):
        for metodo, A, esperado in (("2x2", [[1, 2], [3, 4]], -2),
                                   ("sarrus", [[6, 1, 1], [4, -2, 5], [2, 8, 7]], -306),
                                   ("cofactores", [[1, 2], [3, 4]], -2),
                                   ("triangular", [[0, 1], [2, 3]], -2)):
            with self.subTest(metodo=metodo):
                r = d.informe_determinante(A, metodo)
                self.assertEqual(r["resultado"], esperado)
                self.assertTrue(r["procedimiento"][0]["condiciones"])
                self.assertTrue(r["verificacion"]["correcto"])
                self.assertNotEqual(metodo, r["verificacion"]["metodo"])
                self.assertTrue(any(e["formula"] for e in r["procedimiento"]))

    def test_sarrus_expone_seis_productos_y_sumas(self):
        etapas = m.calcular_determinante([[1, 2, 3], [4, 5, 6], [7, 8, 10]], "sarrus")["etapas"]
        positivos = next(e for e in etapas if e["titulo"] == "Diagonales positivas")
        negativos = next(e for e in etapas if e["titulo"] == "Diagonales negativas")
        self.assertEqual(len(positivos["calculos"]), 4)
        self.assertEqual(len(negativos["calculos"]), 4)
        self.assertIn("Suma =", positivos["calculos"][-1])

    def test_cofactores_guardan_submatriz_signo_termino_y_desarrollo(self):
        etapas = m.calcular_determinante([[1, 2], [3, 4]], "cofactores")["etapas"]
        terminos = [e for e in etapas if e["titulo"].startswith("Menor y cofactor")]
        self.assertEqual(len(terminos), 2)
        self.assertEqual(terminos[0]["valores"][0]["valor"], [[4]])
        self.assertTrue(terminos[0]["subpasos"])
        self.assertIn("Signo", terminos[1]["calculos"][2])
        self.assertIn("a·C", terminos[1]["calculos"][-1])

    def test_triangular_estados_separados_y_pivotes(self):
        etapas = m.calcular_determinante([[2, 1], [4, 3]])["etapas"]
        inicial = etapas[0]["valores"][0]["valor"]
        self.assertEqual(inicial, [[2, 1], [4, 3]])
        self.assertTrue(any(v["pivotes"] for e in etapas for v in e["valores"]))
        operacion = next(e for e in etapas if "←" in e["titulo"])
        self.assertEqual(operacion["valores"][0]["valor"], [[2, 1], [0, 1]])
        self.assertIn("conserva", operacion["explicacion"])

    def test_verificacion_detecta_determinante_falso(self):
        self.assertFalse(d.verificar_determinante([[1, 2], [3, 4]], F(99), "triangular")["correcto"])


class InversasDidacticas(unittest.TestCase):
    def test_gauss_jordan_separacion_bloques_y_operaciones(self):
        r = d.informe_inversa([[0, 2], [1, 3]])
        self.assertTrue(r["verificacion"]["correcto"])
        aumentadas = [v for e in r["procedimiento"] for v in e["valores"] if v["separador"] is not None]
        self.assertTrue(aumentadas)
        self.assertTrue(all(v["separador"] == 2 for v in aumentadas))
        self.assertTrue(any(v["pivotes"] for v in aumentadas))
        self.assertTrue(any("↔" in e["titulo"] for e in r["procedimiento"]))
        self.assertEqual(r["procedimiento"][-1]["titulo"], "Separar I y A⁻¹")
        self.assertTrue(any("(AB)1,1" in linea for e in r["verificacion"]["etapas"] for linea in e["calculos"]))

    def test_adjunta_detalla_todos_los_menores(self):
        r = d.informe_inversa([[1, 2], [3, 4]], "adjunta")
        menores = [e for e in r["procedimiento"] if e["titulo"].startswith("Menor y cofactor")]
        self.assertEqual(len(menores), 4)
        self.assertTrue(all(e["subpasos"] for e in menores))
        self.assertTrue(r["verificacion"]["correcto"])

    def test_singular_con_diagnostico_y_certificado(self):
        for metodo in ("gauss_jordan", "adjunta"):
            r = d.informe_inversa([[1, 2], [2, 4]], metodo)
            self.assertFalse(r["definido"])
            self.assertIsNone(r["resultado"])
            self.assertTrue(r["verificacion"]["correcto"])
            self.assertIn("det(A)=0", r["conclusion"])
            self.assertTrue(any("Certificado" in e["titulo"] for e in r["verificacion"]["etapas"]))

    def test_falsa_inversa_no_pasa_verificacion(self):
        self.assertFalse(d.verificacion_inversa([[1, 2], [3, 4]], [[1, 0], [0, 1]])["correcto"])


class SistemasDidacticos(unittest.TestCase):
    def test_unica_original_A_b_aumentada_y_pivotes(self):
        r = m.resolver_sistema([[2, 1], [1, -1]], [5, 1])
        pasos = d.procedimiento_sistema(r)
        self.assertEqual([v["nombre"] for v in pasos[0]["valores"]], ["A", "b", "[A | b]"])
        self.assertEqual(pasos[0]["valores"][-1]["separador"], 2)
        self.assertTrue(any(v["pivotes"] for e in pasos for v in e["valores"]))
        self.assertTrue(d.verificacion_sistema(r)["correcto"])
        malo = deepcopy(r)
        malo["solucion"] = [F(20), F(1)]
        self.assertFalse(d.verificacion_sistema(malo)["correcto"])

    def test_infinitas_todas_las_direcciones(self):
        r = m.resolver_sistema([[1, 2, 3]], [1])
        pasos = d.procedimiento_sistema(r)
        self.assertEqual(pasos[-1]["titulo"], "Parametrizar")
        self.assertEqual(len(pasos[-1]["valores"]), 3)
        self.assertTrue(d.verificacion_sistema(r)["correcto"])
        malo = deepcopy(r)
        malo["forma_vectorial"][1][0][1][0] = F(100)
        self.assertFalse(d.verificacion_sistema(malo)["correcto"])

    def test_inconsistencia_certificada_con_originales(self):
        A, b = [[1, 2], [2, 4]], [1, 3]
        r = d.verificacion_sistema(m.resolver_sistema(A, b))
        self.assertTrue(r["correcto"])
        self.assertEqual(r["yA"], [0, 0])
        self.assertNotEqual(r["yb"], 0)
        self.assertEqual(m.multiplicar_matrices([r["y"]], A)[0], [0, 0])
        self.assertEqual(sum(yi * bi for yi, bi in zip(r["y"], b)), r["yb"])

    def test_combinacion_reconstruida_por_componentes(self):
        r = m.resolver_sistema([[1, 0, 1], [0, 1, 1]], [2, 3], ["c1", "c2", "c3"])
        informe = d.verificacion_sistema(r, combinacion=True)
        self.assertTrue(informe["correcto"])
        self.assertTrue(any("Componente 1:" in linea for e in informe["etapas"] for linea in e["calculos"]))

    def test_LD_relacion_y_LI_certificado_rectangular(self):
        for A, esperado in (([[1, 2], [2, 4]], False), ([[1, 0], [0, 1], [2, 3]], True)):
            with self.subTest(A=A):
                r = m.analizar_independencia(A)
                self.assertEqual(r["independiente"], esperado)
                informe = d.verificacion_sistema(r, independencia=True)
                self.assertTrue(informe["correcto"])
                self.assertTrue(d.procedimiento_sistema(r, independencia=True))
                if esperado:
                    self.assertIn("Certificado", informe["etapas"][0]["titulo"])
                else:
                    malo = deepcopy(r)
                    malo["relacion"] = [0, 0]
                    self.assertFalse(d.verificacion_sistema(malo, independencia=True)["correcto"])


class PropiedadesDidacticas(unittest.TestCase):
    def test_av_ambos_lados_y_comprobacion_independiente(self):
        datos = m.analizar_producto_av([[1, 2], [3, 4]], [1, -1], F(1, 2), [2, 3])
        informe = d.informe_propiedades_av(datos)
        self.assertTrue(informe["verificacion"]["correcto"])
        titulos = [e["titulo"] for e in informe["procedimiento"]]
        self.assertIn("LADO IZQUIERDO: A(cv)", titulos)
        self.assertIn("LADO DERECHO: c(Av)", titulos)
        self.assertIn("LADO IZQUIERDO: A(u+v)", titulos)
        self.assertIn("LADO DERECHO: Au+Av", titulos)
        for clave in ("Av", "A_cv", "c_Av", "Au", "A_u_mas_v", "Au_mas_Av"):
            malo = deepcopy(datos)
            malo[clave][0] += 1
            self.assertFalse(d.informe_propiedades_av(malo)["verificacion"]["correcto"], clave)

    def test_avanzadas_lados_condiciones_y_rutas_alternas(self):
        for clave in m.PROPIEDADES_AVANZADAS:
            A = [[2, 1], [0, 3]] if clave == "det_triangular" else [[1, 2], [3, 4]]
            with self.subTest(clave=clave):
                r = d.informe_propiedad_avanzada(clave, {"A": A, "B": [[2, 0], [1, 3]]}, {"k": F(-1, 2)})
                self.assertTrue(r["verificacion"]["correcto"])
                self.assertEqual(len(r["lados"]), 2)
                self.assertTrue(all(l["etapas"] for l in r["lados"]))
                self.assertTrue(r["procedimiento"][0]["condiciones"])
                self.assertTrue(any("recálculo" in e["titulo"] for e in r["verificacion"]["etapas"]))

    def test_distributivas_lados_originales_y_condiciones_reales(self):
        casos = [("distributiva_izquierda", {"A": [[1, 2, 3], [4, 5, 6]], "B": [[1, 0], [0, 1], [1, 1]], "C": [[2, 1], [1, 2], [0, 1]]}),
                 ("distributiva_derecha", {"A": [[1, 2, 3], [4, 5, 6]], "B": [[2, 1, 0], [0, 1, 2]], "C": [[1, 0], [0, 1], [1, 1]]})]
        for clave, matrices in casos:
            with self.subTest(clave=clave):
                r = m.verificar_propiedad_matricial(clave, matrices)
                self.assertTrue(r["cumple"])
                principal = r["lados"][:2]
                self.assertEqual(len(principal[0]["resolucion"]["operaciones"]), 2)
                self.assertEqual(len(principal[1]["resolucion"]["operaciones"]), 3)
                self.assertIsNot(principal[0]["resolucion"]["matrices"], principal[1]["resolucion"]["matrices"])
                condiciones = d.condiciones_propiedad(r)
                self.assertEqual(len(condiciones["condiciones"]), 5)
                self.assertTrue(all(c["cumple"] for c in condiciones["condiciones"]))
                malo = deepcopy(principal[0]["resolucion"])
                malo["resultado"][0][0] += 1
                verificacion = m.verificar_resolucion(malo, usar_identidades=False)
                self.assertFalse(verificacion["correcto"])
                self.assertIsNone(verificacion["identidad"])

    def test_incompatibilidad_identificada_sin_falso_exito(self):
        r = m.verificar_propiedad_matricial("distributiva_izquierda", {"A": [[1, 2]], "B": [[1]], "C": [[1, 2]]})
        self.assertIsNone(r["cumple"])
        self.assertTrue(any(not c["cumple"] for c in d.condiciones_propiedad(r)["condiciones"]))
        self.assertFalse(m.verificar_resolucion(r["lados"][0]["resolucion"])["aplicable"])

    def test_comparacion_incluye_todas_las_entradas(self):
        r = d.comparar([[1, 2], [3, 4]], [[1, 2], [3, 5]])
        self.assertEqual(len(r["calculos"]), 4)
        self.assertIn("≠", r["calculos"][-1])
        self.assertEqual(r["conclusion"], "No se cumple")


if __name__ == "__main__":
    unittest.main()

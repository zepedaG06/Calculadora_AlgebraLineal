"""Informes educativos (resultado, procedimiento y verificación) construidos sobre el núcleo exacto.

Propósito: convertir los cálculos de modulo_matrices en etapas verificables: ambos lados de cada propiedad
por rutas separadas, sustituciones, productos fila por columna y certificados exactos.
Unidad: Álgebra Lineal (MTM0120), sistemas, determinantes, inversas, propiedades y factorización LU.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
"""
from fractions import Fraction
from . import modulo_matrices as m
from .pasos import etapa, valor, condicion
from teoremas.teoremas_matrices import DEMOSTRACIONES_PROPIEDADES


def comparar(izquierda, derecha, titulo="Comparación exacta"):
    """Compara dos resultados entrada por entrada y muestra ambas entradas aunque coincidan.

    Entrada: lado izquierdo, lado derecho (matriz, vector o número) y título. Salida: etapa con la conclusión.
    """
    def como_matriz(dato):
        """Convierte un escalar o un vector en matriz para compararlo entrada por entrada.

        Entrada: número, vector o matriz. Salida: lista anidada.
        """
        if not isinstance(dato, list):
            return [[Fraction(dato)]]
        return dato if dato and isinstance(dato[0], list) else [[v] for v in dato]
    L, R = como_matriz(izquierda), como_matriz(derecha)
    iguales = izquierda == derecha
    calculos = []
    if (len(L), len(L[0])) == (len(R), len(R[0])):
        calculos = [f"({i+1},{j+1}): {L[i][j]} {'=' if L[i][j] == R[i][j] else '≠'} {R[i][j]}"
                    for i in range(len(L)) for j in range(len(L[0]))]
    else:
        calculos = [f"Dimensiones diferentes: {len(L)}×{len(L[0])} y {len(R)}×{len(R[0])}."]
    return etapa(titulo, valores=[valor("Lado izquierdo", izquierda), valor("Lado derecho", derecha)],
                 calculos=calculos, conclusion="Se cumple para las matrices ingresadas" if iguales else "No se cumple para las matrices ingresadas")


def condiciones_propiedad(informe):
    """Reúne las dimensiones reales y la condición de cada operación de ambos lados de una propiedad.

    Entrada: informe de verificar_propiedad_matricial. Salida: etapa con las condiciones (✓/✗).
    """
    condiciones = []
    valores = {}
    for lado in informe["lados"]:
        r = lado["resolucion"]
        valores.update(r["matrices"])
        for c in r["condiciones"]:
            condiciones.append(condicion(f"{lado['etiqueta']} · {c['operacion']}: {c['requisito']}", c["cumple"]))
    return etapa("Datos y condiciones de ambos lados", formula=informe["propiedad"]["condiciones"],
                 valores=[valor(n, M) for n, M in valores.items()], condiciones=condiciones)


def pasos_expresion(resolucion, verificacion):
    """Arma el panel de pasos: las operaciones de cada lado y la comparación final si hay identidad.

    Entrada: resolución y verificación de una expresión. Salida: lista de pasos para mostrar.
    """
    identidad = verificacion.get("identidad")
    if not identidad:
        return list(resolucion["pasos"])
    pasos = []
    lados = [("Lado izquierdo", resolucion)]
    if identidad.get("resolucion"):
        lados.append(("Lado derecho", identidad["resolucion"]))
    for etiqueta, ruta in lados:
        pasos.append({"tipo": "seccion", "titulo": f"{etiqueta}: {ruta['expresion']}",
                      "detalle": "Evaluación desde las matrices originales; cada operación tiene sus propios operandos."})
        for paso in ruta["pasos"]:
            pasos.append({**paso, "lado": etiqueta})
    if identidad["definida"]:
        pasos.append({"tipo": "didactica", "etapa": comparar(resolucion["resultado"], identidad["resolucion"]["resultado"], "Verificación de ambos lados")})
    else:
        pasos.append({"tipo": "didactica", "etapa": etapa("Identidad no evaluable con estos datos", conclusion=identidad["motivo"])})
    return pasos


def producto(A, B, nombre="AB"):
    """Calcula X·Y con el procedimiento fila por columna del núcleo y lo empaqueta como etapa.

    Entrada: matrices X, Y y nombre del producto. Salida: (producto, etapa con sus cálculos).
    """
    calculo = m.procedimiento_operacion_matrices(A, "producto", B)
    resultado, pasos = calculo["resultado"], calculo["pasos"]
    return resultado, etapa(f"Calcular {nombre}", formula=f"({nombre})ij = Σ aik bkj",
        valores=[valor("Primer factor", A), valor("Segundo factor", B), valor(nombre, resultado)],
        condiciones=[condicion(f"{len(A)}×{len(A[0])} por {len(B)}×{len(B[0])}; {len(A[0])} = {len(B)}; resultado {len(resultado)}×{len(resultado[0])}.")],
        calculos=pasos)


def producto_vector(A, v, nombre="Av", por_columnas=False):
    """Calcula A·v por filas o, con por_columnas=True, como combinación de las columnas de A.

    Entrada: A, v, nombre y por_columnas (bool). Salida: (vector resultado, etapa con sus cálculos).
    """
    resultado = m.multiplicar_matriz_vector(A, v)
    lineas = m.detalle_producto_matriz_vector(A, v)
    if por_columnas:
        lineas = [f"Componente {i+1}: " + " + ".join(f"({v[j]})·({A[i][j]})" for j in range(len(v))) + f" = {resultado[i]}"
                  for i in range(len(A))]
    return resultado, etapa(f"Calcular {nombre}", formula="Σ cj vj, componente por componente" if por_columnas else "(Av)i = Σ aij vj",
        valores=[valor("A (columnas originales)", A), valor("Coeficientes" if por_columnas else "Vector", v), valor(nombre, resultado)],
        calculos=lineas, condiciones=[condicion(f"A: {len(A)}×{len(A[0])}; vector: {len(v)}×1; resultado: {len(A)}×1.")])


def verificar_determinante(A, obtenido, metodo):
    """Recalcula det(A) desde la A original con otro método (cofactores o reducción) y compara.

    Entrada: A, determinante obtenido y método usado. Salida: diccionario con «correcto», método y etapas.
    """
    alternativo = "cofactores" if metodo == "triangular" else "triangular"
    otro = m.calcular_determinante(A, alternativo)
    etapas = [etapa("Método independiente", f"Se recalcula desde A original mediante {alternativo}.", valores=[valor("A original", A)]),
              *otro["etapas"], comparar(obtenido, otro["determinante"], "Comparar determinantes")]
    return {"correcto": obtenido == otro["determinante"], "metodo": alternativo, "obtenido": otro["determinante"], "etapas": etapas}


def resumen_determinante(A, calculo):
    """Resume en una sola etapa el cálculo principal de det(A) según el método usado.

    Entrada: A y el diccionario de calcular_determinante. Salida: etapa con fórmula, cálculos y conclusión.
    """
    A, metodo, det = m.validar_cuadrada(A), calculo["metodo"], calculo["determinante"]
    etapas = {e["titulo"]: e for e in calculo["etapas"]}
    if metodo == "sarrus":
        calculos = ([f"Positiva: {c}" for c in etapas["Diagonales positivas"]["calculos"]] +
                    [f"Negativa: {c}" for c in etapas["Diagonales negativas"]["calculos"]])
        return etapa("Regla de Sarrus", formula="det(A) = suma positiva − suma negativa = "
                     + etapas["Resta final de Sarrus"]["calculos"][0], valores=[valor("A", A)], calculos=calculos)
    if metodo == "cofactores":
        n = len(A)
        calculos = []
        for j in range(n):
            menor = m.menor(A, 0, j)
            c = (-1) ** j * menor
            calculos.append(f"a1,{j+1}·C1,{j+1} = ({A[0][j]})·({c}) = {A[0][j] * c}   (M1,{j+1} = {menor})")
        return etapa("Expansión por cofactores de la fila 1", formula="det(A) = Σⱼ a1,j·C1,j;  C1,j = (-1)^(1+j)·M1,j",
                     valores=[valor("A", A)], calculos=calculos + [f"det(A) = {det}"])
    if metodo == "2x2":
        return etapa("Fórmula 2×2", formula="det(A) = ad − bc", valores=[valor("A", A)],
                     calculos=etapas["Fórmula 2×2 y sustitución"]["calculos"])
    return etapa("Reducción triangular", formula="det(A) = (-1)^intercambios · ∏ tᵢᵢ",
                 valores=[valor("Triangular T", calculo["triangular"])], calculos=etapas["Producto diagonal y signo"]["calculos"])


def informe_determinante(A, metodo):
    """Calcula det(A) con el método elegido y lo verifica por un método independiente.

    Entrada: A cuadrada y método. Salida: informe con resultado, resumen, procedimiento y verificación.
    """
    calculo = m.calcular_determinante(A, metodo)
    return {"definido": True, "titulo": f"det(A) = {m.formatear_numero(calculo['determinante'])}",
        "resultado": calculo["determinante"], "conclusion": calculo["etapas"][-1]["conclusion"],
        "intermedios": [resumen_determinante(A, calculo)],
        "procedimiento": calculo["etapas"], "verificacion": verificar_determinante(A, calculo["determinante"], metodo)}


def verificacion_inversa(A, inversa):
    """Calcula A·A⁻¹ y A⁻¹·A con detalle y compara ambos productos con la identidad.

    Entrada: A y su inversa. Salida: diccionario con «correcto» y etapas.
    """
    ai, paso_ai = producto(A, inversa, "A·A⁻¹")
    ia, paso_ia = producto(inversa, A, "A⁻¹·A")
    I = m.matriz_identidad(len(A))
    correcto = ai == I and ia == I
    return {"correcto": correcto, "etapas": [paso_ai, comparar(ai, I, "A·A⁻¹ frente a I"),
                                             paso_ia, comparar(ia, I, "A⁻¹·A frente a I")]}


def coherencia_adjunta(A, calculo):
    """Recalcula det(A) por otro método y comprueba que cofactores, adjunta e inversa sean coherentes con A.

    Entrada: A y el cálculo por adjunta. Salida: diccionario con «correcto» y etapas.
    """
    n = len(A)
    d, C, adj, inversa = calculo["determinante"], calculo["cofactores"], calculo["adjunta"], calculo["inversa"]
    metodo, nombre = {2: ("2x2", "la fórmula 2×2"), 3: ("sarrus", "la regla de Sarrus")}.get(n, ("triangular", "reducción triangular"))
    otro = m.calcular_determinante(A, metodo)
    etapas = [etapa(f"det(A) por {nombre}", "Se recalcula desde la A original con otro método.", subpasos=otro["etapas"]),
              comparar(d, otro["determinante"], "det(A) por cofactores frente al recálculo")]
    filas = [sum((A[i][j] * C[i][j] for j in range(n)), Fraction(0)) for i in range(n)]
    etapas.append(etapa("det(A) con los cofactores de cada fila", "Expandir por cualquier fila debe dar el mismo determinante.",
                        formula="det(A) = Σⱼ aᵢⱼ·Cᵢⱼ para cada fila i",
                        calculos=[f"Fila {i+1}: " + " + ".join(f"({A[i][j]})·({C[i][j]})" for j in range(n)) + f" = {filas[i]}"
                                  for i in range(n)],
                        condiciones=[condicion(f"Todas las filas dan det(A) = {d}.", all(f == d for f in filas))]))
    transpuesta = m.transponer_matriz(C)
    etapas.append(comparar(adj, transpuesta, "adj(A) frente a Cᵀ"))
    A_adj, paso = producto(A, adj, "A·adj(A)")
    det_I = [[d if i == j else Fraction(0) for j in range(n)] for i in range(n)]
    etapas += [paso, comparar(A_adj, det_I, "A·adj(A) frente a det(A)·I")]
    escalada = [[v / d for v in fila] for fila in adj]
    etapas.append(comparar(inversa, escalada, "A⁻¹ frente a adj(A)/det(A)"))
    gauss = m.calcular_inversa(A, "gauss_jordan")
    etapas += [etapa("A⁻¹ por Gauss-Jordan", "Método independiente: [A | I] → [I | A⁻¹], sin cofactores.", subpasos=gauss["etapas"]),
               comparar(inversa, gauss["inversa"], "A⁻¹ por adjunta frente a A⁻¹ por Gauss-Jordan")]
    correcto = (d == otro["determinante"] and all(f == d for f in filas) and adj == transpuesta
                and A_adj == det_I and inversa == escalada and inversa == gauss["inversa"])
    return {"correcto": correcto, "etapas": etapas}


def informe_inversa(A, metodo="gauss_jordan"):
    """Calcula A⁻¹ por Gauss-Jordan o por adjunta y cofactores, con procedimiento y verificación.

    Entrada: A cuadrada y método. Salida: informe; si det(A) = 0, diagnóstico y motivo en lugar de la inversa.
    """
    if metodo not in ("gauss_jordan", "adjunta"):
        raise ValueError("Método de inversa desconocido.")
    A = m.validar_cuadrada(A)
    metodo_det = "cofactores" if metodo == "adjunta" else "triangular"
    det = m.calcular_determinante(A, metodo_det)
    if det["determinante"] == 0:
        etapas = list(det["etapas"])
        if metodo == "gauss_jordan":
            I = m.matriz_identidad(len(A))
            aumentada = [f + i for f, i in zip(A, I)]
            _, pivotes, pasos = m.gauss_jordan(aumentada, len(A))
            etapas = [etapa("A e identidad", valores=[valor("A", A), valor("I", I)]),
                      *etapas_eliminacion(pasos, len(A), bloques=True),
                      etapa("Faltan pivotes", calculos=[f"Pivotes: {len(pivotes)}; requeridos: {len(A)}."])]
        relacion = m.analizar_independencia(A)["relacion"]
        cero, paso = producto_vector(A, relacion, "A·c", por_columnas=True)
        correcto = any(relacion) and cero == [0] * len(A)
        verificacion = {"correcto": correcto, "etapas": [etapa("Certificado de singularidad", "c≠0 y Ac=0 impiden que exista inversa.",
            valores=[valor("c no trivial", relacion)]), paso, comparar(cero, [Fraction(0)] * len(A)),
            *verificar_determinante(A, Fraction(0), metodo_det)["etapas"]]}
        return {"definido": False, "titulo": "A no es invertible", "resultado": None,
                "intermedios": [resumen_determinante(A, det)],
                "conclusion": "A es singular porque det(A)=0. No tiene inversa.", "procedimiento": etapas, "verificacion": verificacion}
    calculo = m.calcular_inversa(A, metodo)
    informe = {"definido": True, "titulo": "Inversa A⁻¹", "resultado": calculo["inversa"],
               "conclusion": "A es invertible; ambos productos con A deben ser I.",
               "procedimiento": calculo["etapas"], "verificacion": verificacion_inversa(A, calculo["inversa"])}
    if metodo == "adjunta":
        d = calculo["determinante"]
        coherencia = coherencia_adjunta(A, calculo)
        informe["conclusion"] = (f"det(A) = {m.formatear_numero(d)} ≠ 0, así que A es invertible y "
                                 f"A⁻¹ = (1/det(A))·adj(A) = ({m.formatear_numero(1 / d)})·adj(A).")
        informe["intermedios"] = [etapa(
            "Determinante, menores, cofactores y adjunta", formula="Cᵢⱼ = (-1)^(i+j)·Mᵢⱼ;  adj(A) = Cᵀ;  A⁻¹ = (1/det(A))·adj(A)",
            valores=[valor("det(A)", d), valor("Matriz de menores M", calculo["menores"]),
                     valor("Matriz de cofactores C", calculo["cofactores"]), valor("Adjunta adj(A) = Cᵀ", calculo["adjunta"])],
            calculos=[f"1/det(A) = 1/({d}) = {1 / d}"])]
        informe["verificacion"] = {"correcto": coherencia["correcto"] and informe["verificacion"]["correcto"],
                                   "etapas": [*coherencia["etapas"], *informe["verificacion"]["etapas"]]}
    return informe


def informe_comparacion_inversas(A):
    """Calcula A⁻¹ por ambos métodos y compara los resultados con sus verificaciones.

    Entrada: A cuadrada. Salida: informe de la comparación (o el diagnóstico si A es singular).
    """
    gj, adj = informe_inversa(A), informe_inversa(A, "adjunta")
    if not gj["definido"]:
        return gj
    comparacion = comparar(gj["resultado"], adj["resultado"], "Gauss-Jordan frente a adjunta")
    return {"definido": True, "titulo": "Ambos métodos de inversa coinciden" if gj["resultado"] == adj["resultado"] else "Los métodos difieren",
        "resultado": gj["resultado"], "conclusion": comparacion["conclusion"],
        "procedimiento": [etapa("Método Gauss-Jordan"), *gj["procedimiento"], etapa("Método de adjunta"), *adj["procedimiento"]],
        "verificacion": {"correcto": gj["verificacion"]["correcto"] and adj["verificacion"]["correcto"] and gj["resultado"] == adj["resultado"],
                         "etapas": [comparacion, *gj["verificacion"]["etapas"], *adj["verificacion"]["etapas"]]}}


def informe_propiedad_avanzada(clave, matrices, escalares=None):
    """Verifica una propiedad de inversas o determinantes por dos rutas y la recalcula con otros algoritmos.

    Entrada: clave, matrices y escalares. Salida: informe con lados, procedimiento y verificación.
    """
    if clave.startswith("inversa_") or clave == "det_inversa":
        datos, etapas, chequeos = {}, [], []
        for nombre in (("A", "B") if clave == "inversa_producto" else ("A",)):
            A = m.validar_cuadrada(matrices[nombre])
            datos[nombre] = A
            det = m.calcular_determinante(A)
            etapas.append(etapa(f"Comprobar invertibilidad de {nombre}", valores=[valor(nombre, A)], subpasos=det["etapas"],
                                condiciones=[condicion(f"det({nombre})={det['determinante']}≠0", det["determinante"] != 0)]))
            if det["determinante"] == 0:
                chequeos.extend(informe_inversa(A)["verificacion"]["etapas"])
        if clave == "inversa_producto" and len(datos["A"]) != len(datos["B"]):
            raise ValueError("A y B deben ser cuadradas del mismo orden.")
        if chequeos:
            return {"definido": False, "titulo": "Propiedad no evaluable", "resultado": None,
                    "conclusion": "La propiedad no puede evaluarse: alguna matriz es singular (det=0) y su inversa no está definida.",
                    "procedimiento": etapas, "verificacion": {
                        "aplicable": False, "correcto": False, "etapas": chequeos,
                        "motivo": "No hay lados que comparar: la inversa de una matriz singular no existe. "
                                  "Abajo se comprueba que la matriz es singular."}}
    calculo = m.verificar_propiedad_avanzada(clave, matrices, escalares)
    etapas = [etapa("Datos y condiciones", formula=calculo["propiedad"],
                    valores=[valor(nombre, M) for nombre, M in matrices.items()], condiciones=calculo["condiciones"])]
    for lado in calculo["lados"]:
        etapas += [etapa(lado["etiqueta"], "Cálculo desde datos originales, sin usar el resultado del otro lado."), *lado["etapas"]]
    etapas.append(comparar(calculo["izquierda"], calculo["derecha"]))
    alternativo = m.verificar_propiedad_avanzada(clave, matrices, escalares, metodo_inversa="adjunta", metodo_determinante="cofactores")
    verificacion = [etapa("Recálculo independiente de ambos lados", "Se usan adjunta y expansión por cofactores en lugar de Gauss-Jordan y reducción triangular.")]
    for lado in alternativo["lados"]:
        verificacion += [etapa(lado["etiqueta"] + " — ruta de comprobación"), *lado["etapas"]]
    verificacion += [comparar(calculo["izquierda"], alternativo["izquierda"], "Lado izquierdo: cálculo frente a recálculo"),
                     comparar(calculo["derecha"], alternativo["derecha"], "Lado derecho: cálculo frente a recálculo"),
                     comparar(alternativo["izquierda"], alternativo["derecha"], "Comparar los dos lados recalculados")]
    if clave == "inversa_producto":
        AB, paso = producto(matrices["A"], matrices["B"], "AB (desde datos originales)")
        verificacion += [paso, *verificacion_inversa(AB, calculo["izquierda"])["etapas"]]
    correcto = calculo["izquierda"] == alternativo["izquierda"] and calculo["derecha"] == alternativo["derecha"]
    return {"definido": True, "titulo": calculo["conclusion"], "resultado": None, "lados": calculo["lados"],
            "conclusion": calculo["propiedad"] + ": " + calculo["conclusion"], "procedimiento": etapas,
            "teoria": etapa("Demostración general", "Esta explicación usa las hipótesis del teorema; es independiente de la comprobación numérica.",
                             formula=calculo["propiedad"], conclusion=DEMOSTRACIONES_PROPIEDADES[clave]),
            "verificacion": {"correcto": correcto, "etapas": verificacion}}


def informe_cobertura(informe, matrices):
    """Arma el procedimiento y la verificación de la tabla completa de propiedades clave.

    Entrada: resultado de verificar_propiedades_clave y matrices usadas. Salida: diccionario con ambas vistas.
    """
    datos = etapa("Datos y resultados intermedios reutilizados",
                  "Cada resultado intermedio se calcula una sola vez y se pasa como argumento a las propiedades que lo usan.",
                  valores=[valor(nombre, M) for nombre, M in matrices.items()] + [valor("k", informe["k"])]
                  + [valor(nombre, dato) for nombre, dato in informe["intermedios"].items()])
    procedimiento, comparaciones = [datos], []
    for resultado in informe["resultados"]:
        if resultado["cumple"] is None:
            procedimiento.append(etapa(resultado["propiedad"], resultado["categoria"],
                                       condiciones=[condicion(resultado["diagnostico"], False)]))
            continue
        procedimiento.append(etapa(resultado["propiedad"], resultado["categoria"], formula=resultado["propiedad"],
                                   valores=[valor("Miembro izquierdo", resultado["izquierda"]),
                                            valor("Miembro derecho", resultado["derecha"])],
                                   calculos=resultado["pasos"], conclusion=resultado["diagnostico"]))
        comparaciones.append(comparar(resultado["izquierda"], resultado["derecha"], resultado["propiedad"]))
    if not comparaciones:
        verificacion = {"aplicable": False, "correcto": False, "etapas": [],
                        "motivo": "Ninguna propiedad es aplicable con estas matrices: revisa sus dimensiones."}
    else:
        verificacion = {"correcto": informe["cumplidas"] == informe["evaluadas"], "etapas": comparaciones}
    return {"procedimiento": procedimiento, "verificacion": verificacion}


def etapas_eliminacion(pasos, n, bloques=False):
    """Convierte cada paso de eliminación en una etapa con la matriz, sus pivotes y la separación de bloques.

    Entrada: pasos, columnas del primer bloque y bloques (bool). Salida: lista de etapas.
    """
    etapas = []
    for paso in pasos:
        texto = paso["explicacion"] if not bloques else "La operación se aplica a todas las columnas de ambos bloques."
        etapas.append(etapa(paso["operacion"], texto,
            valores=[valor("Matriz aumentada", paso["matriz"], separador=n, pivotes=paso.get("pivotes", []), filas=paso.get("filas", []))],
            calculos=paso.get("calculos", []) + [f"Pivote ({i+1},{j+1}) = {paso['matriz'][i][j]}" for i, j in paso.get("pivotes", [])]))
    return etapas


def procedimiento_sistema(r, combinacion=False, independencia=False):
    """Construye las etapas de un sistema: datos, eliminación, interpretación de la RREF y parametrización.

    Entrada: resultado de resolver_sistema y el modo (combinación o independencia). Salida: lista de etapas.
    """
    inicial = r["matriz_inicial"]
    A, b = [f[:-1] for f in inicial], [f[-1] for f in inicial]
    n = len(A[0])
    nombres = r["nombres_variables"]
    formula = " + ".join(f"{nombres[j]}v{j+1}" for j in range(n)) + (" = 0" if independencia else " = b")
    etapas = [etapa("Datos originales y modelo", formula=formula if combinacion or independencia else "Ax=b",
        valores=[valor("A = [v1 … vn]" if combinacion or independencia else "A", A), valor("b", b), valor("[A | b]" if not independencia else "[A | 0]", inicial, separador=n)],
        condiciones=[condicion(f"A: {len(A)}×{n}; b: {len(b)}×1; incógnitas: {n}; aumentada: {len(A)}×{n+1}.")],
        calculos=[m.formatear_ecuacion_original(f, bi, nombres) for f, bi in zip(A, b)])]
    etapas.extend(etapas_eliminacion(r["pasos"], n))
    if independencia and r["variables_libres"]:
        etapas += [etapa("Gauss-Jordan para despejar los coeficientes", "La forma escalonada permite contar pivotes; la RREF permite parametrizar."),
                   *etapas_eliminacion(r["pasos_gauss_jordan"], n)]
    basicas = [nombres[j] for j in r["variables_basicas"]]
    libres = [nombres[j] for j in r["variables_libres"]]
    etapas.append(etapa("Interpretar la RREF", valores=[valor("RREF", r["matriz_final"], separador=n)],
        calculos=[m.formatear_ecuacion_original(f[:-1], f[-1], nombres) for f in r["matriz_final"]] +
                 ["Variables básicas: " + (", ".join(basicas) or "ninguna"), "Variables libres: " + (", ".join(libres) or "ninguna"),
                  "[0 … 0 | 0] no es contradicción; [0 … 0 | d], d≠0, sí lo es."], conclusion=r["clasificacion"]))
    if r["expresiones"] is not None:
        p, direcciones = r["forma_vectorial"]
        etapas.append(etapa("Parametrizar", formula="x = p + Σ t v; los parámetros son arbitrarios.",
            calculos=[f"{nombres[j]} = {texto}" for j, texto in r["expresiones"].items()],
            valores=[valor("Particular p", p)] + [valor(f"Dirección de {t}", v) for t, v in direcciones]))
    if independencia and r["relacion"] is not None:
        etapas.append(etapa("Elegir una relación no trivial", "Se eligen parámetros y se eliminan denominadores; al menos un coeficiente es distinto de cero.",
            valores=[valor("Coeficientes c", r["relacion"])], formula=m.formatear_combinacion_lineal(r["relacion"], [f"v{j+1}" for j in range(n)]) + " = 0"))
    return etapas


def certificado_inconsistencia(A, b):
    """Encuentra y con yᵀA = 0 y yᵀb ≠ 0 reduciendo [A | b | I], lo que prueba que Ax = b no tiene solución.

    Entrada: A y b originales. Salida: diccionario con y, yᵀA, yᵀb, «correcto» y etapas.
    """
    n, filas = len(A[0]), len(A)
    I = m.matriz_identidad(filas)
    reducida, _, operaciones = m.gauss_jordan([a + [bi] + e for a, bi, e in zip(A, b, I)], n)
    for f in reducida:
        if all(v == 0 for v in f[:n]) and f[n] != 0:
            y = f[n+1:]
            ya = m.multiplicar_matrices([y], A)[0]
            yb = sum((yi * bi for yi, bi in zip(y, b)), Fraction(0))
            correcto = ya == [0] * n and yb != 0
            return {"correcto": correcto, "y": y, "yA": ya, "yb": yb,
                "etapas": [etapa("Construir el certificado", "Se reduce [A | b | I]; el bloque I registra la combinación de filas y.",
                    subpasos=etapas_eliminacion(operaciones, n, bloques=True)),
                    etapa("Certificado independiente de inconsistencia", "Si Ax=b tuviera solución, yᵀAx=yᵀb implicaría 0=yᵀb≠0.",
                    valores=[valor("y", y), valor("A original", A), valor("b original", b)],
                    calculos=[f"yᵀA = {ya}", "yᵀb = " + " + ".join(f"({yi})·({bi})" for yi, bi in zip(y, b)) + f" = {yb}"],
                    conclusion="Se cumple: el sistema original es inconsistente." if correcto else "No se cumple") ]}
    raise ArithmeticError("No se encontró un certificado de inconsistencia.")


def verificacion_sistema(r, combinacion=False, independencia=False):
    """Verifica un sistema con los datos originales: sustitución, familia paramétrica o certificado.

    Entrada: resultado de resolver_sistema y el modo. Salida: diccionario con «correcto» y etapas.
    """
    A = [f[:-1] for f in r["matriz_inicial"]]
    b = [f[-1] for f in r["matriz_inicial"]]
    if independencia and r["independiente"]:
        filas, n = len(A), len(A[0])
        reducida, pivotes, operaciones = m.gauss_jordan([a + e for a, e in zip(A, m.matriz_identidad(filas))], n)
        L = [f[n:] for f in reducida[:n]]
        LA, paso = producto(L, A, "L·A")
        I = m.matriz_identidad(n)
        correcto = len(pivotes) == n and LA == I
        return {"correcto": correcto, "etapas": [etapa("Certificado: obtener L desde [A | I]", "Se conservan las primeras n filas del bloque derecho de la reducción.",
            subpasos=etapas_eliminacion(operaciones, n, bloques=True)),
            etapa("Certificado de independencia", "Una inversa por la izquierda L con LA=I prueba: Ac=0 ⇒ LAc=c=0. No basta comprobar un único vector trivial.",
            valores=[valor("L", L)]), paso, comparar(LA, I), etapa("Conclusión", conclusion="Se cumple: solo existe la solución trivial." if correcto else "No se cumple")]}
    if independencia:
        c = r["relacion"]
        obtenido, paso = producto_vector(A, c, "Σ cj vj", por_columnas=True)
        correcto = any(c) and obtenido == [0] * len(A)
        return {"correcto": correcto, "etapas": [etapa("Relación no trivial", formula=m.formatear_combinacion_lineal(c, [f"v{j+1}" for j in range(len(c))]) + " = 0",
            condiciones=[condicion("Existe un coeficiente no nulo.", any(c))]), paso, comparar(obtenido, [Fraction(0)] * len(A)),
            etapa("Conclusión", conclusion="Se cumple: hay una relación no trivial, por tanto son L.D." if correcto else "No se cumple")]}
    if r["solucion"] is None and r["solucion_particular"] is None:
        return certificado_inconsistencia(A, b)
    x = r["solucion"] if r["solucion"] is not None else r["solucion_particular"]
    obtenido, paso = producto_vector(A, x, "Σ cj vj" if combinacion else "A·x" if r["solucion"] is not None else "A·p", por_columnas=combinacion)
    etapas = [etapa("Verificar contra los datos originales", "Se sustituyen los coeficientes encontrados en las columnas originales." if combinacion else "Se sustituyen los valores en las ecuaciones originales, no en la RREF."), paso, comparar(obtenido, b)]
    correcto = obtenido == b
    if r["forma_vectorial"] is not None:
        for t, v in r["forma_vectorial"][1]:
            av, paso_v = producto_vector(A, v, f"A·v({t})", por_columnas=combinacion)
            etapas += [etapa(f"Dirección del parámetro {t}", "Debe pertenecer al espacio nulo de A."), paso_v, comparar(av, [Fraction(0)] * len(A))]
            correcto = correcto and av == [0] * len(A)
    etapas.append(etapa("Conclusión de la verificación", conclusion="Se cumple" if correcto else "No se cumple"))
    return {"correcto": correcto, "etapas": etapas}


def informe_propiedades_av(datos):
    """Calcula los dos lados de A(cv) = c(Av) y A(u + v) = Au + Av y los compara por columnas.

    Entrada: diccionario con A, v, c y u. Salida: diccionario con procedimiento y verificación.
    """
    A, v, c, u = datos["A"], datos["v"], datos["c"], datos["u"]
    etapas = [etapa("Datos y condiciones", valores=[valor("A", A), valor("v", v), valor("c", c)] + ([valor("u", u)] if u is not None else []),
        condiciones=[condicion(f"A: {len(A)}×{len(A[0])}; u y v tienen {len(v)} componentes; cada producto tiene {len(A)} componentes.")])]
    terminos = [[v[j]*A[i][j] for i in range(len(A))] for j in range(len(v))]
    for j, termino in enumerate(terminos):
        etapas.append(etapa(f"Escalar la columna a{j+1}", formula=f"v{j+1}a{j+1}",
            valores=[valor(f"a{j+1}", [f[j] for f in A]), valor(f"v{j+1}a{j+1}", termino)],
            calculos=[f"({v[j]})·({A[i][j]})={termino[i]}" for i in range(len(A))]))
    suma_columnas = [sum((t[i] for t in terminos), Fraction(0)) for i in range(len(A))]
    etapas.append(etapa("Sumar las columnas escaladas", formula="Av = v1 a1 + … + vn an", valores=[valor("Av", suma_columnas)],
        calculos=[" + ".join(f"({t[i]})" for t in terminos) + f" = {suma_columnas[i]}" for i in range(len(A))]))
    av, avpaso = producto_vector(A, v)
    etapas.append(avpaso)
    cv = [c * vi for vi in v]
    izquierda, li = producto_vector(A, cv, "A(cv)")
    rhs_av, der = producto_vector(A, v, "Av (lado derecho desde los datos originales)")
    derecha = [c * vi for vi in rhs_av]
    etapas += [etapa("LADO IZQUIERDO: A(cv)", formula="Primero cv, después A(cv)", valores=[valor("cv", cv)],
                     calculos=[f"cv{i+1}=({c})·({vi})={cv[i]}" for i, vi in enumerate(v)]), li,
               etapa("LADO DERECHO: c(Av)"), der,
               etapa("Escalar Av", valores=[valor("c(Av)", derecha)], calculos=[f"({c})·({vi})={derecha[i]}" for i, vi in enumerate(rhs_av)]), comparar(izquierda, derecha)]
    if u is not None:
        suma = [ui + vi for ui, vi in zip(u, v)]
        izquierda, li = producto_vector(A, suma, "A(u+v)")
        au, pu = producto_vector(A, u, "Au (lado derecho)")
        rhs_av, pv = producto_vector(A, v, "Av (lado derecho)")
        derecha = [ui + vi for ui, vi in zip(au, rhs_av)]
        etapas += [etapa("LADO IZQUIERDO: A(u+v)", valores=[valor("u+v", suma)], calculos=[f"({ui})+({vi})={si}" for ui, vi, si in zip(u, v, suma)]), li,
                   etapa("LADO DERECHO: Au+Av"), pu, pv, etapa("Sumar Au+Av", valores=[valor("Au+Av", derecha)],
                   calculos=[f"({ui})+({vi})={si}" for ui, vi, si in zip(au, rhs_av, derecha)]), comparar(izquierda, derecha)]
    # El recálculo por columnas usa operandos originales, no los productos
    # que se compararon ni las identidades que se están comprobando.
    verificaciones = []
    casos = [("Av", v, datos["Av"]), ("A(cv)", cv, datos["A_cv"])]
    if u is not None:
        casos += [("Au", u, datos["Au"]), ("A(u+v)", [a+b for a, b in zip(u, v)], datos["A_u_mas_v"])]
    correcto = True
    for nombre, vector, esperado in casos:
        reconstruido = [Fraction(0)] * len(A)
        for j, coef in enumerate(vector):
            for i in range(len(A)):
                reconstruido[i] += coef * A[i][j]
        _, paso = producto_vector(A, vector, nombre + " por columnas", por_columnas=True)
        verificaciones += [paso, comparar(reconstruido, esperado, nombre + ": columnas frente a filas")]
        correcto = correcto and reconstruido == esperado
    c_av = [c * componente for componente in suma_columnas]
    verificaciones += [etapa("Recálculo del lado derecho c(Av)", valores=[valor("c(Av) por columnas", c_av)],
                            calculos=[f"({c})·({vi})={ci}" for vi, ci in zip(suma_columnas, c_av)]),
                       comparar(c_av, datos["c_Av"], "Lado derecho escalar: cálculo frente a recálculo"),
                       comparar(datos["A_cv"], c_av, "Comparar A(cv) y c(Av)")]
    correcto = correcto and c_av == datos["c_Av"] and datos["A_cv"] == c_av
    if u is not None:
        au_columnas = [sum((u[j] * A[i][j] for j in range(len(u))), Fraction(0)) for i in range(len(A))]
        suma = [au + av for au, av in zip(au_columnas, suma_columnas)]
        verificaciones += [etapa("Recálculo del lado derecho Au+Av", valores=[valor("Au+Av por columnas", suma)],
                                calculos=[f"({au})+({av})={si}" for au, av, si in zip(au_columnas, suma_columnas, suma)]),
                           comparar(suma, datos["Au_mas_Av"], "Lado derecho suma: cálculo frente a recálculo"),
                           comparar(datos["A_u_mas_v"], suma, "Comparar A(u+v) y Au+Av")]
        correcto = correcto and suma == datos["Au_mas_Av"] and datos["A_u_mas_v"] == suma
    verificaciones.append(etapa("Conclusión", conclusion="Se cumple" if correcto else "No se cumple"))
    return {"procedimiento": etapas, "verificacion": {"correcto": correcto, "etapas": verificaciones}}

"""Informes educativos para resultado, procedimiento y verificación.

Consume el núcleo existente y conserva todos los datos originales.
Los lados de una propiedad se calculan por rutas separadas, sin imponer igualdad.
Las verificaciones incluyen sustituciones, productos y certificados exactos.
"""
from fractions import Fraction
from . import modulo_matrices as m
from .pasos import etapa, valor, condicion


def comparar(izquierda, derecha, titulo="Comparación exacta"):
    """Muestra ambas entradas de cada posición, incluso cuando coinciden."""
    def como_matriz(dato):
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
                 calculos=calculos, conclusion="Se cumple" if iguales else "No se cumple")


def condiciones_propiedad(informe):
    """Recoge dimensiones reales y condiciones de cada operación de ambos lados."""
    condiciones = []
    valores = {}
    for lado in informe["lados"]:
        r = lado["resolucion"]
        valores.update(r["matrices"])
        for c in r["condiciones"]:
            condiciones.append(condicion(f"{lado['etiqueta']} · {c['operacion']}: {c['requisito']}", c["cumple"]))
    return etapa("Datos y condiciones de ambos lados", formula=informe["propiedad"]["condiciones"],
                 valores=[valor(n, M) for n, M in valores.items()], condiciones=condiciones)


def producto(A, B, nombre="AB"):
    """Reutiliza el producto y su procedimiento fila por columna."""
    calculo = m.procedimiento_operacion_matrices(A, "producto", B)
    resultado, pasos = calculo["resultado"], calculo["pasos"]
    return resultado, etapa(f"Calcular {nombre}", formula=f"({nombre})ij = Σ aik bkj",
        valores=[valor("Primer factor", A), valor("Segundo factor", B), valor(nombre, resultado)],
        condiciones=[condicion(f"{len(A)}×{len(A[0])} por {len(B)}×{len(B[0])}; {len(A[0])} = {len(B)}; resultado {len(resultado)}×{len(resultado[0])}.")],
        calculos=pasos)


def producto_vector(A, v, nombre="Av", por_columnas=False):
    """Explica el producto por filas o reconstruye la combinación por componentes."""
    resultado = m.multiplicar_matriz_vector(A, v)
    lineas = m.detalle_producto_matriz_vector(A, v)
    if por_columnas:
        lineas = [f"Componente {i+1}: " + " + ".join(f"({v[j]})·({A[i][j]})" for j in range(len(v))) + f" = {resultado[i]}"
                  for i in range(len(A))]
    return resultado, etapa(f"Calcular {nombre}", formula="Σ cj vj, componente por componente" if por_columnas else "(Av)i = Σ aij vj",
        valores=[valor("A (columnas originales)", A), valor("Coeficientes" if por_columnas else "Vector", v), valor(nombre, resultado)],
        calculos=lineas, condiciones=[condicion(f"A: {len(A)}×{len(A[0])}; vector: {len(v)}×1; resultado: {len(A)}×1.")])


def verificar_determinante(A, obtenido, metodo):
    """Usa un método distinto del procedimiento, sin recibir sus matrices reducidas."""
    alternativo = "cofactores" if metodo == "triangular" else "triangular"
    otro = m.calcular_determinante(A, alternativo)
    etapas = [etapa("Método independiente", f"Se recalcula desde A original mediante {alternativo}.", valores=[valor("A original", A)]),
              *otro["etapas"], comparar(obtenido, otro["determinante"], "Comparar determinantes")]
    return {"correcto": obtenido == otro["determinante"], "metodo": alternativo, "obtenido": otro["determinante"], "etapas": etapas}


def informe_determinante(A, metodo):
    calculo = m.calcular_determinante(A, metodo)
    return {"definido": True, "titulo": f"det(A) = {m.formatear_numero(calculo['determinante'])}",
        "resultado": calculo["determinante"], "conclusion": calculo["etapas"][-1]["conclusion"],
        "procedimiento": calculo["etapas"], "verificacion": verificar_determinante(A, calculo["determinante"], metodo)}


def verificacion_inversa(A, inversa):
    """Calcula ambos productos con detalle y los compara con la identidad."""
    ai, paso_ai = producto(A, inversa, "A·A⁻¹")
    ia, paso_ia = producto(inversa, A, "A⁻¹·A")
    I = m.matriz_identidad(len(A))
    correcto = ai == I and ia == I
    return {"correcto": correcto, "etapas": [paso_ai, comparar(ai, I, "A·A⁻¹ frente a I"),
                                             paso_ia, comparar(ia, I, "A⁻¹·A frente a I")]}


def informe_inversa(A, metodo="gauss_jordan"):
    A = m.validar_cuadrada(A)
    det = m.calcular_determinante(A)
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
            *verificar_determinante(A, Fraction(0), "triangular")["etapas"]]}
        return {"definido": False, "titulo": "A no es invertible", "resultado": None,
                "conclusion": "A es singular porque det(A)=0. No tiene inversa.", "procedimiento": etapas, "verificacion": verificacion}
    calculo = m.calcular_inversa(A, metodo)
    return {"definido": True, "titulo": "Inversa A⁻¹", "resultado": calculo["inversa"],
            "conclusion": "A es invertible; ambos productos con A deben ser I.",
            "procedimiento": calculo["etapas"], "verificacion": verificacion_inversa(A, calculo["inversa"])}


def informe_comparacion_inversas(A):
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
    """Expone cada ruta y la verifica cambiando algoritmos de inversa y determinante."""
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
    correcto = calculo["izquierda"] == alternativo["izquierda"] and calculo["derecha"] == alternativo["derecha"]
    return {"definido": True, "titulo": calculo["conclusion"], "resultado": None, "lados": calculo["lados"],
            "conclusion": calculo["propiedad"] + ": " + calculo["conclusion"], "procedimiento": etapas,
            "verificacion": {"correcto": correcto, "etapas": verificacion}}


def etapas_eliminacion(pasos, n, bloques=False):
    """Conserva cada estado de eliminación y su pivote, sin confundir A con [A|b]."""
    etapas = []
    for paso in pasos:
        texto = paso["explicacion"] if not bloques else "La operación se aplica a todas las columnas de ambos bloques."
        etapas.append(etapa(paso["operacion"], texto,
            valores=[valor("Matriz aumentada", paso["matriz"], separador=n, pivotes=paso.get("pivotes", []), filas=paso.get("filas", []))],
            calculos=[f"Pivote ({i+1},{j+1}) = {paso['matriz'][i][j]}" for i, j in paso.get("pivotes", [])]))
    return etapas


def procedimiento_sistema(r, combinacion=False, independencia=False):
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
    """Encuentra y con yᵀA=0 e yᵀb≠0 y lo verifica contra datos originales."""
    n, filas = len(A[0]), len(A)
    I = m.matriz_identidad(filas)
    reducida, _, _ = m.gauss_jordan([a + [bi] + e for a, bi, e in zip(A, b, I)], n)
    for f in reducida:
        if all(v == 0 for v in f[:n]) and f[n] != 0:
            y = f[n+1:]
            ya = m.multiplicar_matrices([y], A)[0]
            yb = sum((yi * bi for yi, bi in zip(y, b)), Fraction(0))
            correcto = ya == [0] * n and yb != 0
            return {"correcto": correcto, "y": y, "yA": ya, "yb": yb,
                "etapas": [etapa("Certificado independiente de inconsistencia", "Si Ax=b tuviera solución, yᵀAx=yᵀb implicaría 0=yᵀb≠0.",
                    valores=[valor("y", y), valor("A original", A), valor("b original", b)],
                    calculos=[f"yᵀA = {ya}", "yᵀb = " + " + ".join(f"({yi})·({bi})" for yi, bi in zip(y, b)) + f" = {yb}"],
                    conclusion="Se cumple: el sistema original es inconsistente." if correcto else "No se cumple") ]}
    raise ArithmeticError("No se encontró un certificado de inconsistencia.")


def verificacion_sistema(r, combinacion=False, independencia=False):
    A = [f[:-1] for f in r["matriz_inicial"]]
    b = [f[-1] for f in r["matriz_inicial"]]
    if independencia and r["independiente"]:
        filas, n = len(A), len(A[0])
        reducida, pivotes, _ = m.gauss_jordan([a + e for a, e in zip(A, m.matriz_identidad(filas))], n)
        L = [f[n:] for f in reducida[:n]]
        LA, paso = producto(L, A, "L·A")
        I = m.matriz_identidad(n)
        correcto = len(pivotes) == n and LA == I
        return {"correcto": correcto, "etapas": [etapa("Certificado de independencia", "Una inversa por la izquierda L con LA=I prueba: Ac=0 ⇒ LAc=c=0. No basta comprobar un único vector trivial.",
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
    """Explica los dos lados de las propiedades de Av y comprueba por columnas."""
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

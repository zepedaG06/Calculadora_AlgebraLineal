"""Logica de la seccion Calculadora.

Este es el caso de uso general: recibe A y b, construye [A | b], reutiliza
`nucleo.gauss_jordan`, clasifica el sistema y reutiliza `nucleo.verificacion`.
La interfaz de la calculadora solo recoge entradas y presenta este resultado.
"""

from fractions import Fraction

from .nucleo.formato import formatear_numero, nombres_parametros, obtener_nombres_variables
from .nucleo.gauss_jordan import gauss_jordan
from .nucleo.verificacion import verificar_solucion


def crear_matriz_aumentada(A, b):
    """Construye [A | b], primer paso del procedimiento general."""
    if len(A) != len(b):
        raise ValueError("La matriz A y el vector b deben tener la misma cantidad de filas.")
    return [A[i][:] + [b[i]] for i in range(len(A))]


def fila_inconsistente(fila, num_variables):
    return all(fila[columna] == 0 for columna in range(num_variables)) and fila[-1] != 0


def es_sistema_homogeneo(b):
    return all(valor == 0 for valor in b)


def clasificar_sistema(matriz_rref, columnas_pivote, num_variables):
    if any(fila_inconsistente(fila, num_variables) for fila in matriz_rref):
        return "Sistema inconsistente", "No tiene solucion."
    if len(columnas_pivote) == num_variables:
        return "Sistema consistente determinado", "Tiene una unica solucion."
    return "Sistema consistente indeterminado", "Tiene infinitas soluciones."


def obtener_solucion_unica(matriz_rref, columnas_pivote, num_variables):
    solucion = [Fraction(0) for _ in range(num_variables)]
    for fila, columna in enumerate(columnas_pivote):
        solucion[columna] = matriz_rref[fila][-1]
    return solucion


def obtener_solucion_parametrica(matriz_rref, columnas_pivote, num_variables):
    variables_libres = [c for c in range(num_variables) if c not in columnas_pivote]
    parametros = dict(zip(variables_libres, nombres_parametros(len(variables_libres))))
    expresiones = {libre: parametro for libre, parametro in parametros.items()}
    for fila, columna_pivote in enumerate(columnas_pivote):
        terminos = []
        independiente = matriz_rref[fila][-1]
        if independiente != 0:
            terminos.append(formatear_numero(independiente))
        for columna_libre in variables_libres:
            coeficiente = -matriz_rref[fila][columna_libre]
            if coeficiente == 0:
                continue
            parametro = parametros[columna_libre]
            if coeficiente == 1:
                terminos.append(parametro)
            elif coeficiente == -1:
                terminos.append(f"-{parametro}")
            else:
                terminos.append(f"{formatear_numero(coeficiente)}{parametro}")
        expresiones[columna_pivote] = " + ".join(terminos).replace("+ -", "- ") if terminos else "0"
    return {i: expresiones[i] for i in range(num_variables)}, variables_libres, parametros


def resolver_sistema(A, b):
    """Ejecuta el flujo completo de la Calculadora para resolver Ax=b."""
    if not A or not A[0]:
        raise ValueError("La matriz A no puede estar vacia.")
    num_variables = len(A[0])
    if any(len(fila) != num_variables for fila in A):
        raise ValueError("Todas las filas de A deben tener la misma cantidad de columnas.")
    aumentada = crear_matriz_aumentada(A, b)
    matriz_final, columnas_pivote, pasos = gauss_jordan(aumentada, num_variables)
    clasificacion, descripcion = clasificar_sistema(matriz_final, columnas_pivote, num_variables)
    resultado = {
        "matriz_inicial": aumentada,
        "matriz_final": matriz_final,
        "pasos": pasos,
        "columnas_pivote": columnas_pivote,
        "variables_basicas": columnas_pivote,
        "variables_libres": [c for c in range(num_variables) if c not in columnas_pivote],
        "nombres_variables": obtener_nombres_variables(num_variables),
        "clasificacion": clasificacion,
        "descripcion": descripcion,
        "homogeneo": es_sistema_homogeneo(b),
        "solucion": None,
        "expresiones": None,
        "solucion_particular": None,
        "verificacion": None,
    }
    if clasificacion == "Sistema consistente determinado":
        resultado["solucion"] = obtener_solucion_unica(matriz_final, columnas_pivote, num_variables)
        resultado["verificacion"] = verificar_solucion(A, b, resultado["solucion"])
    elif clasificacion == "Sistema consistente indeterminado":
        expresiones, libres, parametros = obtener_solucion_parametrica(matriz_final, columnas_pivote, num_variables)
        particular = [Fraction(0) for _ in range(num_variables)]
        for fila, columna in enumerate(columnas_pivote):
            particular[columna] = matriz_final[fila][-1]
        resultado.update(expresiones=expresiones, variables_libres=libres, parametros=parametros, solucion_particular=particular, verificacion=verificar_solucion(A, b, particular))
    return resultado


def resolver_calculadora(A, b):
    """Punto de entrada con nombre explícito para la pantalla Calculadora."""
    return resolver_sistema(A, b)

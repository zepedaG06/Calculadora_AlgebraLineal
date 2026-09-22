"""Conversion y presentacion de datos matematicos.

Este modulo no resuelve sistemas. Convierte las entradas de la interfaz a
Fraction y genera textos de matrices, ecuaciones y sustituciones.
"""

from fractions import Fraction


def convertir_numero(texto):
    texto = texto.strip()
    if not texto:
        raise ValueError("Hay una casilla vacia.")
    return Fraction(texto)


def formatear_numero(numero):
    if numero == 0:
        return "0"
    if numero.denominator == 1:
        return str(numero.numerator)
    return f"{numero.numerator}/{numero.denominator}"


def matriz_a_texto(matriz):
    if not matriz or not matriz[0]:
        return ""
    anchos = [0] * len(matriz[0])
    for fila in matriz:
        for columna, valor in enumerate(fila):
            anchos[columna] = max(anchos[columna], len(formatear_numero(valor)))
    anchos = [max(ancho, 4) for ancho in anchos]
    lineas = []
    for fila in matriz:
        coeficientes = "  ".join(f"{formatear_numero(fila[c]):>{anchos[c]}}" for c in range(len(fila) - 1))
        independiente = f"{formatear_numero(fila[-1]):>{anchos[-1]}}"
        lineas.append(f"[ {coeficientes} | {independiente} ]")
    return "\n".join(lineas)


def obtener_nombres_variables(num_variables):
    return [f"x{i + 1}" for i in range(num_variables)]


def nombres_parametros(cantidad):
    if cantidad == 1:
        return ["t"]
    if cantidad == 2:
        return ["s", "t"]
    if cantidad == 3:
        return ["r", "s", "t"]
    base = ["r", "s", "t", "u", "v", "w"]
    if cantidad <= len(base):
        return base[:cantidad]
    return [f"t{i + 1}" for i in range(cantidad)]


def formatear_ecuacion_original(fila_coefs, termino_indep, nombres_vars):
    terminos = []
    for indice, coeficiente in enumerate(fila_coefs):
        if coeficiente == 0:
            continue
        variable = nombres_vars[indice]
        if coeficiente == 1:
            termino = variable if not terminos else f"+ {variable}"
        elif coeficiente == -1:
            termino = f"-{variable}" if not terminos else f"- {variable}"
        elif coeficiente > 0:
            valor = formatear_numero(coeficiente)
            valor = f"({valor})" if coeficiente.denominator != 1 else valor
            termino = f"{valor}{variable}" if not terminos else f"+ {valor}{variable}"
        else:
            valor = formatear_numero(abs(coeficiente))
            valor = f"({valor})" if abs(coeficiente).denominator != 1 else valor
            termino = f"-{valor}{variable}" if not terminos else f"- {valor}{variable}"
        terminos.append(termino)
    return f"{' '.join(terminos) if terminos else '0'} = {formatear_numero(termino_indep)}"


def formatear_sustitucion(fila_coefs, termino_indep, solucion):
    terminos = []
    for indice, coeficiente in enumerate(fila_coefs):
        if coeficiente == 0:
            continue
        valor = f"({formatear_numero(solucion[indice])})"
        if coeficiente == 1:
            termino = valor if not terminos else f"+ {valor}"
        elif coeficiente == -1:
            termino = f"-{valor}" if not terminos else f"- {valor}"
        elif coeficiente > 0:
            termino = f"{formatear_numero(coeficiente)}{valor}" if not terminos else f"+ {formatear_numero(coeficiente)}{valor}"
        else:
            termino = f"-{formatear_numero(abs(coeficiente))}{valor}" if not terminos else f"- {formatear_numero(abs(coeficiente))}{valor}"
        terminos.append(termino)
    return f"{' '.join(terminos) if terminos else '0'} = {formatear_numero(termino_indep)}"


def formatear_simplificacion(fila_coefs, termino_indep, solucion):
    productos = [coeficiente * solucion[indice] for indice, coeficiente in enumerate(fila_coefs) if coeficiente != 0]
    pasos = []
    if len(productos) > 1:
        partes = [formatear_numero(productos[0])]
        for producto in productos[1:]:
            partes.append(f"+ {formatear_numero(producto)}" if producto >= 0 else f"- {formatear_numero(abs(producto))}")
        pasos.append(f"{' '.join(partes)} = {formatear_numero(termino_indep)}")
    suma = sum(productos) if productos else Fraction(0)
    pasos.append(f"{formatear_numero(suma)} = {formatear_numero(termino_indep)}")
    return pasos, suma == termino_indep, suma

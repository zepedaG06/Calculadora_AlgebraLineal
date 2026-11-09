"""Estructura de datos de cada etapa de un procedimiento (independiente de la GUI).

Propósito: guardar fórmulas, operandos, cálculos y condiciones verificables; las matrices se copian para
conservar el estado real de cada operación, tanto en la vista completa como en la de paso a paso.
Unidad: Álgebra Lineal (MTM0120), presentación de procedimientos de la Calculadora.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
"""
from copy import deepcopy


def valor(nombre, dato, separador=None, pivotes=(), filas=()):
    """Describe un escalar, vector o matriz para mostrarlo dentro de una etapa.

    Entrada: nombre, dato, separador de bloques, pivotes y filas resaltadas. Salida: diccionario con una copia del dato.
    """
    return {"nombre": nombre, "valor": deepcopy(dato), "separador": separador,
            "pivotes": list(pivotes), "filas": list(filas)}


def etapa(titulo, explicacion="", formula="", valores=(), calculos=(), condiciones=(),
          conclusion="", subpasos=()):
    """Construye una etapa del procedimiento sin widgets ni impresión en consola.

    Entrada: título, explicación, fórmula, valores, cálculos, condiciones, conclusión y subpasos. Salida: diccionario.
    """
    return {"titulo": titulo, "explicacion": explicacion, "formula": formula,
            "valores": deepcopy(list(valores)), "calculos": list(calculos),
            "condiciones": deepcopy(list(condiciones)), "conclusion": conclusion,
            "subpasos": deepcopy(list(subpasos))}


def condicion(texto, cumple=True):
    """Construye una condición verificable para mostrarla con ✓ o ✗.

    Entrada: texto y cumple (bool). Salida: diccionario {texto, cumple}.
    """
    return {"texto": texto, "cumple": bool(cumple)}

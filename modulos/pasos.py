"""Datos de presentación matemática independientes de la GUI.

Cada etapa guarda fórmulas, operandos, cálculos y condiciones verificables.
Las matrices se copian para conservar el estado real de cada operación.
El mismo formato permite tarjetas completas o navegación paso a paso.
"""
from copy import deepcopy


def valor(nombre, dato, separador=None, pivotes=(), filas=()):
    """Describe un escalar, vector o matriz y su separación de bloques."""
    return {"nombre": nombre, "valor": deepcopy(dato), "separador": separador,
            "pivotes": list(pivotes), "filas": list(filas)}


def etapa(titulo, explicacion="", formula="", valores=(), calculos=(), condiciones=(),
          conclusion="", subpasos=()):
    """Construye una etapa sin widgets, texto de consola ni datos compartidos mutables."""
    return {"titulo": titulo, "explicacion": explicacion, "formula": formula,
            "valores": deepcopy(list(valores)), "calculos": list(calculos),
            "condiciones": deepcopy(list(condiciones)), "conclusion": conclusion,
            "subpasos": deepcopy(list(subpasos))}


def condicion(texto, cumple=True):
    return {"texto": texto, "cumple": bool(cumple)}

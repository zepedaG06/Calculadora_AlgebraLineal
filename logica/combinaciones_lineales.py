"""Logica de la seccion Combinaciones Lineales.

Convierte c1*v1 + ... + cn*vn = w en A*c=w. Reutiliza el solucionador de
`calculadora.py`, que a su vez usa el nucleo de Gauss-Jordan y verificacion.
"""

from .calculadora import resolver_sistema


def resolver_combinacion_lineal(vectores, objetivo):
    if not vectores:
        raise ValueError("Debe existir al menos un vector.")
    dimension = len(objetivo)
    if any(len(vector) != dimension for vector in vectores):
        raise ValueError("Todos los vectores deben tener la misma dimension que el objetivo.")
    A = [[vectores[columna][fila] for columna in range(len(vectores))] for fila in range(dimension)]
    return resolver_sistema(A, objetivo)

"""Logica de la seccion Independencia Lineal.

Construye el sistema homogeneo A*c=0 y observa si existe alguna solucion no
trivial. Reutiliza el solucionador general de `calculadora.py`.
"""

from fractions import Fraction

from .calculadora import resolver_sistema


def analizar_independencia(A):
    """Resuelve A*c=0 y comprueba si la solucion trivial es la unica."""
    if not A or not A[0]:
        raise ValueError("La matriz no puede estar vacia.")
    resultado = resolver_sistema(A, [Fraction(0) for _ in A])
    resultado["independiente"] = resultado["clasificacion"] == "Sistema consistente determinado" and all(x == 0 for x in (resultado["solucion"] or []))
    return resultado

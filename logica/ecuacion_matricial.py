"""Logica de la seccion Ecuacion Matricial Ax=b.

Este apartado recibe directamente una matriz A y un vector b. Reutiliza el
flujo de `calculadora.py` porque ambos problemas son sistemas lineales; la
separacion permite explicar esta opcion como caso de uso independiente.
"""

from .calculadora import resolver_sistema


def resolver_ecuacion_matricial(A, b):
    """Resuelve Ax=b y devuelve pasos, clasificacion y solucion."""
    return resolver_sistema(A, b)

"""Operaciones elementales con vectores y matrices.

Este modulo ofrece calculos basicos con validaciones de dimensiones para una
capa separada del resto de la logica de sistemas lineales.
"""

from fractions import Fraction


def _normalizar_escalar(valor):
    if isinstance(valor, Fraction):
        return valor
    if isinstance(valor, int):
        return Fraction(valor, 1)
    if isinstance(valor, str):
        return Fraction(valor.strip())
    return Fraction(valor)


def _normalizar_vector(vector):
    return [_normalizar_escalar(valor) for valor in vector]


def _normalizar_matriz(matriz):
    return [[_normalizar_escalar(valor) for valor in fila] for fila in matriz]


def sumar_vectores(vector_a, vector_b):
    vector_a = _normalizar_vector(vector_a)
    vector_b = _normalizar_vector(vector_b)
    if len(vector_a) != len(vector_b):
        raise ValueError("Los vectores deben tener la misma longitud.")
    return [a + b for a, b in zip(vector_a, vector_b)]


def restar_vectores(vector_a, vector_b):
    vector_a = _normalizar_vector(vector_a)
    vector_b = _normalizar_vector(vector_b)
    if len(vector_a) != len(vector_b):
        raise ValueError("Los vectores deben tener la misma longitud.")
    return [a - b for a, b in zip(vector_a, vector_b)]


def multiplicar_vector_por_escalar(vector, escalar):
    vector = _normalizar_vector(vector)
    escalar = _normalizar_escalar(escalar)
    return [valor * escalar for valor in vector]


def sumar_matrices(matriz_a, matriz_b):
    matriz_a = _normalizar_matriz(matriz_a)
    matriz_b = _normalizar_matriz(matriz_b)
    if len(matriz_a) != len(matriz_b) or len(matriz_a[0]) != len(matriz_b[0]):
        raise ValueError("Las matrices deben tener las mismas dimensiones m x n.")
    return [
        [a + b for a, b in zip(fila_a, fila_b)]
        for fila_a, fila_b in zip(matriz_a, matriz_b)
    ]


def restar_matrices(matriz_a, matriz_b):
    matriz_a = _normalizar_matriz(matriz_a)
    matriz_b = _normalizar_matriz(matriz_b)
    if len(matriz_a) != len(matriz_b) or len(matriz_a[0]) != len(matriz_b[0]):
        raise ValueError("Las matrices deben tener las mismas dimensiones m x n.")
    return [
        [a - b for a, b in zip(fila_a, fila_b)]
        for fila_a, fila_b in zip(matriz_a, matriz_b)
    ]


def multiplicar_matriz_por_escalar(matriz, escalar):
    matriz = _normalizar_matriz(matriz)
    escalar = _normalizar_escalar(escalar)
    return [[valor * escalar for valor in fila] for fila in matriz]


def multiplicar_matrices(matriz_a, matriz_b):
    matriz_a = _normalizar_matriz(matriz_a)
    matriz_b = _normalizar_matriz(matriz_b)
    if not matriz_a or not matriz_b:
        raise ValueError("Las matrices no pueden estar vacias.")
    if len(matriz_a[0]) != len(matriz_b):
        raise ValueError("Las columnas de A deben coincidir con las filas de B.")

    columnas_b = len(matriz_b[0])
    return [
        [
            sum(matriz_a[fila][k] * matriz_b[k][columna] for k in range(len(matriz_b)))
            for columna in range(columnas_b)
        ]
        for fila in range(len(matriz_a))
    ]

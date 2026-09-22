"""Algoritmo general de eliminacion por filas.

Todas las secciones reutilizan este procedimiento para reducir matrices
exactamente con Fraction y registrar cada operacion elemental.
"""

from fractions import Fraction

from .formato import formatear_numero
from .modelos import PasoEliminacion

EPSILON = Fraction(0)


def copiar_matriz(matriz):
    return [fila[:] for fila in matriz]


def intercambiar_filas(matriz, i, j):
    matriz[i], matriz[j] = matriz[j], matriz[i]


def multiplicar_fila(matriz, i, escalar):
    matriz[i] = [escalar * valor for valor in matriz[i]]


def sumar_multiplo_fila(matriz, destino, origen, factor):
    matriz[destino] = [matriz[destino][c] + factor * matriz[origen][c] for c in range(len(matriz[destino]))]


def buscar_fila_pivote(matriz, fila_inicio, columna):
    for fila in range(fila_inicio, len(matriz)):
        if matriz[fila][columna] != EPSILON:
            return fila
    return None


def gauss_jordan(matriz_aumentada, num_variables):
    """Reduce [A | b] a RREF y registra cada operacion para explicarla."""
    matriz = copiar_matriz(matriz_aumentada)
    pasos = [PasoEliminacion("Matriz aumentada inicial", "Se plantea la matriz aumentada [A | b] con los coeficientes del sistema y los términos independientes.", copiar_matriz(matriz), "inicial")]
    columnas_pivote = []
    fila_pivote = 0
    for columna in range(num_variables):
        if fila_pivote >= len(matriz):
            break
        candidatos = [fila for fila in range(fila_pivote, len(matriz)) if matriz[fila][columna] != 0]
        if not candidatos:
            continue
        fila_encontrada = max(candidatos, key=lambda fila: abs(matriz[fila][columna]))
        if fila_encontrada != fila_pivote:
            intercambiar_filas(matriz, fila_pivote, fila_encontrada)
            pasos.append(PasoEliminacion(f"F{fila_pivote + 1} ↔ F{fila_encontrada + 1}", f"Se intercambian F{fila_pivote + 1} y F{fila_encontrada + 1} para colocar en la posición pivote un valor no nulo de la columna {columna + 1} (variable x{columna + 1}).", copiar_matriz(matriz), "intercambio"))
        valor_pivote = matriz[fila_pivote][columna]
        if valor_pivote != 1:
            inverso = Fraction(1, 1) / valor_pivote
            multiplicar_fila(matriz, fila_pivote, inverso)
            k_inv = formatear_numero(inverso)
            operacion = f"F{fila_pivote + 1} → -F{fila_pivote + 1}" if inverso == -1 else f"F{fila_pivote + 1} → {k_inv if inverso.denominator == 1 else f'({k_inv})'}F{fila_pivote + 1}"
            pasos.append(PasoEliminacion(operacion, f"Se multiplica F{fila_pivote + 1} por {k_inv} para convertir el pivote de la columna {columna + 1} (variable x{columna + 1}) en 1.", copiar_matriz(matriz), "escalado"))
        for fila in range(len(matriz)):
            if fila == fila_pivote:
                continue
            factor = matriz[fila][columna]
            if factor == 0:
                continue
            sumar_multiplo_fila(matriz, fila, fila_pivote, -factor)
            factor_abs = abs(factor)
            k_str = formatear_numero(factor_abs)
            if factor > 0:
                operacion = f"F{fila + 1} → F{fila + 1} - F{fila_pivote + 1}" if factor_abs == 1 else f"F{fila + 1} → F{fila + 1} - {k_str if factor_abs.denominator == 1 else f'({k_str})'}F{fila_pivote + 1}"
            else:
                operacion = f"F{fila + 1} → F{fila + 1} + F{fila_pivote + 1}" if factor_abs == 1 else f"F{fila + 1} → F{fila + 1} + {k_str if factor_abs.denominator == 1 else f'({k_str})'}F{fila_pivote + 1}"
            posicion = "debajo" if fila > fila_pivote else "arriba"
            pasos.append(PasoEliminacion(operacion, f"Se hace cero el elemento de F{fila + 1} en la columna {columna + 1} (variable x{columna + 1}), {posicion} del pivote, usando F{fila_pivote + 1}.", copiar_matriz(matriz), "eliminacion"))
        columnas_pivote.append(columna)
        fila_pivote += 1
    return matriz, columnas_pivote, pasos

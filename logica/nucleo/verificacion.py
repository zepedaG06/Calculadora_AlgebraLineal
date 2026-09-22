"""Verificacion de soluciones contra el sistema original."""

from .formato import formatear_ecuacion_original, formatear_simplificacion, formatear_sustitucion, obtener_nombres_variables
from .modelos import DetalleVerificacion


def verificar_solucion(A_original, b_original, solucion):
    """Comprueba Ax=b usando los datos originales, no la matriz reducida."""
    if not A_original or not b_original or len(A_original) != len(b_original):
        return False, []
    num_vars = len(A_original[0])
    if any(len(fila) != num_vars for fila in A_original) or len(solucion) != num_vars:
        return False, []
    nombres_vars = obtener_nombres_variables(num_vars)
    detalles = []
    correcta = True
    for indice, fila in enumerate(A_original):
        esperado = b_original[indice]
        suma_directa = sum(fila[j] * solucion[j] for j in range(num_vars))
        coincide = suma_directa == esperado
        simplificacion, _, _ = formatear_simplificacion(fila, esperado, solucion)
        correcta = correcta and coincide
        detalles.append(DetalleVerificacion(indice + 1, formatear_ecuacion_original(fila, esperado, nombres_vars), formatear_sustitucion(fila, esperado, solucion), simplificacion, suma_directa, esperado, coincide))
    return correcta, detalles

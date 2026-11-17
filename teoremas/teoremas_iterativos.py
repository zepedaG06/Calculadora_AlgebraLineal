"""Logotipo ASCII y teoremas clave del módulo de métodos iterativos (Jacobi y Gauss-Seidel).

Propósito: contenido académico de la opción «0. Ver Teoremas Clave del Módulo» (GUI y consola).
Unidad: Álgebra Lineal (MTM0120), Programa 8: métodos iterativos de Jacobi y Gauss-Seidel.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
"""

LOGO_ITERATIVOS = r"""
  +---------------------------------------------------+
  |   UAM - GRUPO 3 - JACOBI Y GAUSS-SEIDEL           |
  |                                                   |
  |   x(k) = ( b - (L + U) x(k-1) ) / D     Jacobi    |
  |   x(k) = ( b - L x(k) - U x(k-1) ) / D  G-Seidel  |
  |                                                   |
  |   Parar si  || x(k) - x(k-1) ||inf <= epsilon     |
  +---------------------------------------------------+
"""

TEOREMAS_ITERATIVOS = (
    ("Idea de los métodos iterativos",
     "Se despeja xᵢ de la ecuación i: xᵢ = (bᵢ − Σⱼ≠ᵢ aᵢⱼ xⱼ) / aᵢᵢ. A partir de un vector inicial x⁽⁰⁾ se generan "
     "aproximaciones x⁽¹⁾, x⁽²⁾, … que, si el método converge, se acercan a la solución de Ax = b."),
    ("Método de Jacobi",
     "Todas las componentes de x⁽ᵏ⁾ se calculan con los valores de la iteración anterior x⁽ᵏ⁻¹⁾: es una "
     "actualización simultánea. En forma matricial, x⁽ᵏ⁾ = D⁻¹(b − (L + U)x⁽ᵏ⁻¹⁾)."),
    ("Método de Gauss-Seidel",
     "Cada componente nueva se usa de inmediato en la misma iteración: para xᵢ⁽ᵏ⁾ se usan x₁⁽ᵏ⁾, …, xᵢ₋₁⁽ᵏ⁾ ya "
     "calculados y xᵢ₊₁⁽ᵏ⁻¹⁾, …, xₙ⁽ᵏ⁻¹⁾. Suele necesitar menos iteraciones que Jacobi."),
    ("Ceros en la diagonal",
     "Ambos métodos dividen entre aᵢᵢ, así que no pueden iniciar si algún aᵢᵢ = 0. Reordenar las ecuaciones no cambia "
     "la solución y puede dejar la diagonal sin ceros; si ningún orden lo logra, los métodos no se pueden aplicar."),
    ("Diagonal estrictamente dominante",
     "Si |aᵢᵢ| > Σⱼ≠ᵢ |aᵢⱼ| en cada fila, Jacobi y Gauss-Seidel convergen desde cualquier x⁽⁰⁾. Es una condición "
     "suficiente, no necesaria: un sistema sin diagonal dominante también puede converger."),
    ("Criterio de parada",
     "Se detiene la iteración cuando ‖x⁽ᵏ⁾ − x⁽ᵏ⁻¹⁾‖∞ ≤ ε o al llegar al máximo de iteraciones. El residuo ‖Ax − b‖∞ "
     "comprueba cuánto se aleja la aproximación de cumplir el sistema."),
    ("Convergencia y radio espectral",
     "Los métodos convergen para todo x⁽⁰⁾ si y solo si el radio espectral de su matriz de iteración es menor que 1. "
     "El cociente entre errores sucesivos estima ese radio: si es mayor que 1, el error crece y el método diverge."),
    ("Matrices simétricas definidas positivas",
     "Si A es simétrica definida positiva, Gauss-Seidel converge aunque A no sea diagonal dominante; Jacobi no "
     "siempre. Por eso no cumplir la condición suficiente no demuestra la divergencia."),
)


def texto_teoremas_iterativos():
    """Une los teoremas del módulo de métodos iterativos en un texto numerado para la consola o la GUI.

    Salida: cadena con un teorema por bloque.
    """
    return "\n\n".join(f"{numero}. {titulo}\n{texto}" for numero, (titulo, texto) in enumerate(TEOREMAS_ITERATIVOS, 1))

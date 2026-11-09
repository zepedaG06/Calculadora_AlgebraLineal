"""Logotipo ASCII y teoremas clave del módulo de Factorización LU.

Propósito: contenido académico de la opción «0. Ver Teoremas Clave del Módulo» (GUI y consola).
Unidad: Álgebra Lineal (MTM0120), Programa 6: factorización LU y solución de sistemas Ax = b.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
"""

LOGO_LU = r"""
  +---------------------------------------------------+
  |   UAM - GRUPO 3 - FACTORIZACION LU   ( A = L U )  |
  |                                                   |
  |     [ 1  0  0 ]     [ u  u  u ]                   |
  |     [ l  1  0 ]  x  [ 0  u  u ]   =   A           |
  |     [ l  l  1 ]     [ 0  0  u ]                   |
  |          L               U                        |
  |                                                   |
  |  Ly = b (hacia adelante) -> Ux = y (hacia atras)  |
  +---------------------------------------------------+
"""

TEOREMAS_LU = (
    ("Existencia de A = LU",
     "Si A (m×n) se lleva a una forma escalonada U usando solo reemplazos Fi ← Fi − l·Fj con i > j, entonces "
     "A = LU, donde L (m×m) es triangular inferior con unos en la diagonal principal."),
    ("Multiplicadores de L",
     "Cada multiplicador l = (elemento a eliminar) / (pivote) se guarda en L en la posición (i, j): la fila que se "
     "modifica y la columna del pivote. Así L registra ordenadamente todos los reemplazos."),
    ("Por qué L·U = A",
     "Cada reemplazo es una matriz elemental E. Si U = Eₚ⋯E₁A, entonces A = E₁⁻¹⋯Eₚ⁻¹U = LU; invertir un reemplazo "
     "solo cambia el signo de su multiplicador, por eso L es triangular inferior unitaria."),
    ("Pivoteo y permutación",
     "Si una posición pivote vale 0 y debajo hay un valor distinto de cero, hace falta intercambiar filas: la matriz "
     "no admite LU sin permutación y se usa PA = LU, con P una matriz de permutación."),
    ("Sustitución hacia adelante",
     "Ax = b equivale a L(Ux) = b. Con y = Ux se resuelve primero Ly = b reduciendo [L | b]: "
     "y₁ = b₁ y yᵢ = bᵢ − Σⱼ<ᵢ lᵢⱼ·yⱼ."),
    ("Sustitución hacia atrás",
     "Después se resuelve Ux = y reduciendo [U | y] desde la última fila con pivote: xₖ = (yₖ − Σⱼ>ₖ uₖⱼ·xⱼ) / uₖₖ. "
     "Una fila nula de U con yᵢ ≠ 0 indica que no hay solución; una columna sin pivote, una variable libre."),
    ("Determinante",
     "Si A es cuadrada, det(A) = det(L)·det(U) = 1·∏ uᵢᵢ. A es invertible si y solo si todos los uᵢᵢ son "
     "distintos de cero."),
    ("Verificación",
     "L·U == A comprueba la factorización y A·x == b comprueba la solución con los datos originales. Una "
     "comprobación numérica es un caso particular, no una demostración general."),
    ("Ventaja práctica",
     "Con una sola factorización se resuelven varios sistemas Ax = b₁, Ax = b₂, … repitiendo solo las dos "
     "sustituciones, que son mucho más baratas que una nueva eliminación."),
)


def texto_teoremas_lu():
    """Une los teoremas clave del módulo LU en un texto numerado para la consola o la GUI.

    Salida: cadena con un teorema por bloque.
    """
    return "\n\n".join(f"{numero}. {titulo}\n{texto}" for numero, (titulo, texto) in enumerate(TEOREMAS_LU, 1))

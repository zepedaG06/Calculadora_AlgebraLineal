"""Teoremas clave de operaciones, determinantes e inversas.

Las condiciones acompañan cada igualdad para evitar generalizaciones falsas.
El contenido se comparte entre la GUI y la consulta por consola.
Las comprobaciones numéricas son casos particulares, no demostraciones.
"""

TEOREMAS_MATRICES = (
    ("Suma, resta y escalar", "A±B requiere dimensiones iguales; se opera entrada por entrada. rA multiplica cada entrada por r."),
    ("Producto", "Si A es m×n y B es n×q, AB es m×q. Cada entrada es el producto de una fila de A por una columna de B. En general AB≠BA."),
    ("Transpuesta", "Aᵀ intercambia filas y columnas: (Aᵀ)ij=Aji. (A+B)ᵀ=Aᵀ+Bᵀ; (rA)ᵀ=rAᵀ; (AB)ᵀ=BᵀAᵀ; (Aᵀ)ᵀ=A."),
    ("Determinante", "Es un escalar asociado a una matriz cuadrada. Para orden 1 es su entrada; para 2×2 es ad−bc. Sarrus solo es válido para 3×3."),
    ("Menores y cofactores", "Mij es el determinante al suprimir fila i y columna j. Cij=(-1)^(i+j)Mij. det(A)=Σ aij Cij por cualquier fila fija (también por columna)."),
    ("Singularidad e invertibilidad", "Para A cuadrada: det(A)≠0 si y solo si A es invertible. Si det(A)=0, A es singular y no tiene inversa."),
    ("Inversa y Gauss-Jordan", "A⁻¹ satisface AA⁻¹=A⁻¹A=I y es única. Se reduce [A|I] a [I|A⁻¹]; si faltan pivotes en el bloque A, no existe inversa."),
    ("Adjunta", "adj(A) es la transpuesta de la matriz de cofactores. A adj(A)=det(A)I. Si det(A)≠0, A⁻¹=adj(A)/det(A)."),
    ("Propiedades de inversas", "Para matrices invertibles: (A⁻¹)⁻¹=A; (Aᵀ)⁻¹=(A⁻¹)ᵀ; det(A⁻¹)=1/det(A). Para A y B del mismo orden e invertibles: (AB)⁻¹=B⁻¹A⁻¹."),
    ("Operaciones de fila y determinante", "Intercambiar dos filas cambia el signo; multiplicar una fila por k multiplica det por k; sumar a una fila un múltiplo de otra fila distinta conserva det."),
    ("Triangulares y producto", "El determinante de una matriz triangular es el producto de su diagonal. det(I)=1; det(Aᵀ)=det(A); det(AB)=det(A)det(B) para matrices cuadradas del mismo orden."),
    ("Ax=b y soluciones infinitas", "Una fila [0…0|d], d≠0, es contradicción; [0…0|0] no lo es. Sin variables libres hay solución única; con libres y sin contradicción hay infinitas. Para x=p+Σ tv, comprobar Ap=b y Av=0."),
    ("Independencia y combinación lineal", "Los vectores son columnas de A. Resolver Ac=0: solo solución trivial significa L.I.; una solución no trivial significa L.D. Resolver Ac=b comprueba si b es combinación de las columnas; calcular Ax es una operación distinta."),
)

LOGO_ASCII = r"""
  +--------------------------------------+
  |  UAM - GRUPO 3 - ALGEBRA LINEAL       |
  |       [ A | I ]  ->  [ I | A^-1 ]     |
  +--------------------------------------+
"""


def texto_teoremas():
    """Devuelve el contenido académico listo para consulta sin realizar E/S."""
    return "\n\n".join(f"{i}. {titulo}\n{texto}" for i, (titulo, texto) in enumerate(TEOREMAS_MATRICES, 1))

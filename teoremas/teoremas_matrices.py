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
    ("Factorización LU", "Si A (m×n) se lleva a una forma escalonada U solo con reemplazos Fi−mFk (i>k), entonces A=LU: L es m×m triangular inferior con unos en la diagonal y guarda cada multiplicador m en (i,k). Si una posición pivote es 0 con un valor no nulo debajo, hace falta un intercambio y A=LU no existe (se usa PA=LU)."),
    ("Ax=b con A=LU", "Ax=b equivale a L(Ux)=b. Primero Ly=b por sustitución hacia adelante (y1, y2, …); después Ux=y por sustitución hacia atrás (desde la última fila con pivote). Una fila nula de U con yi≠0 es inconsistencia; una columna sin pivote es una variable libre. Si A es cuadrada, det(A)=∏uii."),
)

LOGO_ASCII = r"""
  +--------------------------------------+
  |  UAM - GRUPO 3 - ALGEBRA LINEAL       |
  |       [ A | I ]  ->  [ I | A^-1 ]     |
  +--------------------------------------+
"""


DEMOSTRACIONES_PROPIEDADES = {
    "inversa_izquierda": "Si det(A)≠0, Gauss-Jordan reduce [A|I] a [I|X]; las mismas operaciones son E=Eₖ…E₁ con EA=I y EI=X, así que X=E y XA=I. Por definición, X=A⁻¹ y A⁻¹A=I.",
    "inversa_derecha": "Por la propiedad anterior, A⁻¹A=I. Tomando determinantes, det(A⁻¹)det(A)=1, así que A⁻¹ es invertible; multiplicar A⁻¹A=I por (A⁻¹)⁻¹ a la izquierda da A=(A⁻¹)⁻¹. Luego AA⁻¹=(A⁻¹)⁻¹A⁻¹=I.",
    "inversa_inversa": "Si X=A⁻¹, AX=XA=I. Por definición y unicidad de la inversa, X⁻¹=A.",
    "inversa_producto": "Sean A y B cuadradas invertibles del mismo orden. (AB)(B⁻¹A⁻¹)=A(BB⁻¹)A⁻¹=I y (B⁻¹A⁻¹)(AB)=B⁻¹(A⁻¹A)B=I. Por unicidad, (AB)⁻¹=B⁻¹A⁻¹.",
    "inversa_transpuesta": "Transponer AA⁻¹=A⁻¹A=I da (A⁻¹)ᵀAᵀ=Aᵀ(A⁻¹)ᵀ=I. Por unicidad, (Aᵀ)⁻¹=(A⁻¹)ᵀ.",
    "det_inversa": "Por multiplicatividad, det(A)det(A⁻¹)=det(AA⁻¹)=det(I)=1. Como det(A)≠0, det(A⁻¹)=1/det(A).",
    "det_producto": "Las columnas de AB son combinaciones de las columnas de A con coeficientes de B. Al expandir por multilinealidad del determinante, los términos con columnas repetidas son cero; los restantes son det(A) multiplicado por la suma con signos de permutaciones que define det(B). Así det(AB)=det(A)det(B).",
    "det_transpuesta": "En la fórmula de Leibniz, cambiar cada permutación por su inversa conserva su signo e intercambia los índices de fila y columna. Las sumas para det(A) y det(Aᵀ) son iguales.",
    "det_identidad": "En la fórmula de Leibniz para I, solo la permutación identidad aporta un término distinto de cero: su signo y su producto son 1.",
    "det_intercambio": "El determinante es alternante en sus filas: intercambiar dos filas cambia el signo de cada término de la suma de Leibniz.",
    "det_escalar_fila": "Por multilinealidad en las filas, det(...,kFi,...)=k det(...,Fi,...), incluso si k=0.",
    "det_suma_fila": "Para i≠j, la multilinealidad da det(...,Fi+kFj,...)=det(A)+k det(...,Fj,...,Fj,...). El segundo determinante es cero por tener dos filas iguales.",
    "det_triangular": "En una matriz triangular, toda permutación distinta de la identidad selecciona alguna entrada del lado nulo de la diagonal. En Leibniz solo permanece el producto de la diagonal.",
}


def texto_teoremas():
    """Devuelve el contenido académico listo para consulta sin realizar E/S."""
    return "\n\n".join(f"{i}. {titulo}\n{texto}" for i, (titulo, texto) in enumerate(TEOREMAS_MATRICES, 1))

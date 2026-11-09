"""Logotipo ASCII y teoremas clave del módulo de Métodos Numéricos.

Propósito: contenido académico de la opción «0. Ver Teoremas Clave del Módulo» (GUI y consola).
Unidad: Álgebra Lineal (MTM0120), Programa 7: módulo de Métodos Numéricos.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
"""

LOGO_NUMERICOS = r"""
  +---------------------------------------------------+
  |     UAM - GRUPO 3 - METODOS NUMERICOS             |
  |                                                   |
  |        f(x)         a --- c --- b                 |
  |         |    /      f(a)*f(c) < 0 ?               |
  |     ----+---*----   13 = 1101 (base 2)            |
  |         | /         E = |v - v*|                  |
  |                                                   |
  |  Biseccion - Graficador - Base 10 y 2 - Errores   |
  +---------------------------------------------------+
"""

TEOREMAS_NUMERICOS = (
    ("Teorema de Bolzano",
     "Si f es continua en [a, b] y f(a)·f(b) < 0, existe al menos un r en (a, b) con f(r) = 0. Es la garantía del "
     "método de bisección; sin continuidad no aplica: 1/x cambia de signo en [−1, 1] y no tiene raíces."),
    ("Método de bisección",
     "Se calcula c = (a + b)/2. Si f(a) y f(c) tienen signos opuestos, la raíz está en [a, c]; si no, en [c, b]. "
     "Cada iteración conserva el cambio de signo y reduce el intervalo a la mitad."),
    ("Cota del error de la bisección",
     "Tras n iteraciones, |c(n) − r| ≤ (b − a)/2ⁿ. Por eso las iteraciones necesarias se conocen de antemano: "
     "n ≥ log₂((b − a)/tol). La convergencia es lineal: se gana un bit correcto por iteración."),
    ("Gráfica de una función",
     "Una gráfica en pantalla es una muestra finita de puntos (x, f(x)) unidos por segmentos. Cuantos más puntos, "
     "mejor la aproximación; en una asíntota los puntos no deben unirse."),
    ("Notación posicional",
     "En base β, un número vale la suma de cada dígito d por βᵏ, donde k es su posición y 0 ≤ d < β. La posición determina el peso de cada dígito: "
     "1101.1₂ = 1·2³ + 1·2² + 0·2¹ + 1·2⁰ + 1·2⁻¹ = 13.5."),
    ("Conversión de base 10 a base 2",
     "La parte entera se divide sucesivamente entre 2 y los residuos se leen del último al primero. La parte "
     "fraccionaria se multiplica sucesivamente por 2 y las partes enteras se leen del primero al último."),
    ("Fracciones finitas en base 2",
     "Una fracción irreducible p/q tiene desarrollo binario finito si y solo si q es una potencia de 2. Por eso "
     "0.1 = 1/10 es periódico en base 2 y la computadora no puede guardarlo exactamente."),
    ("Punto flotante IEEE 754",
     "Un número se guarda como (−1)ˢ × 1.m × 2ᵉ. En doble precisión: 1 bit de signo, 11 de exponente con sesgo 1023 "
     "y 52 de mantisa. El épsilon de la máquina es ε = 2⁻⁵² y el redondeo cumple |x − x*|/|x| ≤ ε/2."),
    ("Errores absoluto y relativo",
     "Ea = |v − v*| mide la distancia; Er = Ea/|v| la compara con el tamaño de v (con v ≠ 0); E% = 100·Er. "
     "Si Er ≤ 0.5·10^(1−n), v* tiene al menos n cifras significativas correctas."),
    ("Redondeo y truncamiento",
     "Con n cifras significativas, redondear da un error de a lo sumo media unidad de la última cifra y truncar, "
     "menos de una unidad. El error de truncamiento de una serie es lo que se deja de sumar."),
    ("Cancelación de cifras",
     "Al restar números casi iguales, las cifras correctas se cancelan y el error relativo crece. Se evita "
     "reescribiendo la fórmula: √(x+1) − √x = 1/(√(x+1) + √x)."),
)


def texto_teoremas_numericos():
    """Une los teoremas del módulo de Métodos Numéricos en un texto numerado para la consola o la GUI.

    Salida: cadena con un teorema por bloque.
    """
    return "\n\n".join(f"{numero}. {titulo}\n{texto}" for numero, (titulo, texto) in enumerate(TEOREMAS_NUMERICOS, 1))

"""
Programa 1 - Algebra Lineal
Solucion de sistemas de ecuaciones lineales por eliminacion por filas.

Restricciones cumplidas:
- No usa PySide6.
- No usa NumPy.
- No usa SciPy.
- La eliminacion por filas esta implementada manualmente.
"""

import os
from fractions import Fraction
import tkinter as tk
from tkinter import messagebox

try:
    import customtkinter as ctk
except ModuleNotFoundError:
    ctk = None

try:
    from PIL import Image
except ModuleNotFoundError:
    Image = None


EPSILON = Fraction(0)

# Carpeta donde vive este archivo, para poder cargar el logo sin importar
# desde donde se ejecute el programa.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_LOGO = os.path.join(BASE_DIR, "universidad_americana.png")
if not os.path.exists(RUTA_LOGO):
    RUTA_LOGO = os.path.join(BASE_DIR, "logo_uam.png")


# -----------------------------------------------------------------------------
# Logica matematica
# -----------------------------------------------------------------------------

def convertir_numero(texto):
    """Convierte la entrada del usuario a Fraction para trabajar con valores exactos."""
    texto = texto.strip()
    if not texto:
        raise ValueError("Hay una casilla vacia.")
    return Fraction(texto)


def formatear_numero(numero):
    """Muestra las fracciones de forma legible: 2 en lugar de 2/1."""
    if numero == 0:
        return "0"
    if numero.denominator == 1:
        return str(numero.numerator)
    return f"{numero.numerator}/{numero.denominator}"


def copiar_matriz(matriz):
    """Copia una matriz para no modificar los datos originales usados en la verificacion."""
    return [fila[:] for fila in matriz]


def crear_matriz_aumentada(A, b):
    """Construye la matriz aumentada [A | b]."""
    return [A[i][:] + [b[i]] for i in range(len(A))]


def intercambiar_filas(matriz, i, j):
    """Operacion elemental Fi <-> Fj."""
    matriz[i], matriz[j] = matriz[j], matriz[i]


def multiplicar_fila(matriz, i, escalar):
    """Operacion elemental Fi -> kFi."""
    matriz[i] = [escalar * valor for valor in matriz[i]]


def sumar_multiplo_fila(matriz, destino, origen, factor):
    """
    Operacion elemental Fdestino -> Fdestino + factor * Forigen.
    Se usa para generar ceros arriba o debajo de un pivote.
    """
    matriz[destino] = [
        matriz[destino][c] + factor * matriz[origen][c]
        for c in range(len(matriz[destino]))
    ]


def matriz_a_texto(matriz):
    """Convierte una matriz aumentada en texto alineado para mostrarla en la interfaz."""
    if not matriz or not matriz[0]:
        return ""
    num_cols = len(matriz[0])
    anchos = [0] * num_cols
    for fila in matriz:
        for c, val in enumerate(fila):
            txt = formatear_numero(val)
            if len(txt) > anchos[c]:
                anchos[c] = len(txt)
    anchos = [max(w, 4) for w in anchos]
    lineas = []
    for fila in matriz:
        coeficientes = "  ".join(f"{formatear_numero(fila[c]):>{anchos[c]}}" for c in range(num_cols - 1))
        independiente = f"{formatear_numero(fila[-1]):>{anchos[-1]}}"
        lineas.append(f"[ {coeficientes} | {independiente} ]")
    return "\n".join(lineas)


def buscar_fila_pivote(matriz, fila_inicio, columna):
    """Busca una fila con entrada no nula en la columna candidata a pivote."""
    for fila in range(fila_inicio, len(matriz)):
        if matriz[fila][columna] != EPSILON:
            return fila
    return None


class PasoEliminacion(dict):
    """
    Representa un paso en el procedimiento de eliminacion por filas.
    Compatible como diccionario (paso['operacion']), como objeto con atributos
    (paso.operacion) y como secuencia (paso[0]=operacion, paso[1]=matriz, paso[2]=explicacion)
    para garantizar maxima compatibilidad con tests y codigo previo.
    """

    def __init__(self, operacion, explicacion, matriz, tipo="operacion"):
        super().__init__(
            operacion=operacion,
            explicacion=explicacion,
            matriz=matriz,
            tipo=tipo,
        )
        self.operacion = operacion
        self.explicacion = explicacion
        self.matriz = matriz
        self.tipo = tipo

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self["operacion"]
            elif key == 1:
                return self["matriz"]
            elif key == 2:
                return self["explicacion"]
            raise IndexError("Indice de paso fuera de rango (0-2)")
        return super().__getitem__(key)


def gauss_jordan(matriz_aumentada, num_variables, prefijo_variable="x"):
    """
    Reduce [A | b] a forma escalonada reducida por filas.

    Todas las operaciones se hacen con Fraction para evitar errores
    de redondeo. En cada columna se selecciona como pivote la fila
    disponible con mayor valor absoluto y se registra cada operación.
    """
    matriz = copiar_matriz(matriz_aumentada)
    pasos = [
        PasoEliminacion(
            operacion="Matriz aumentada inicial",
            explicacion="Se plantea la matriz aumentada [A | b] con los coeficientes del sistema y los términos independientes.",
            matriz=copiar_matriz(matriz),
            tipo="inicial",
        )
    ]

    columnas_pivote = []
    fila_pivote = 0
    num_filas = len(matriz)

    for columna in range(num_variables):
        if fila_pivote >= num_filas:
            break

        # Elegir la mejor fila pivote entre las filas disponibles.
        candidatos = [
            fila for fila in range(fila_pivote, num_filas)
            if matriz[fila][columna] != 0
        ]
        if not candidatos:
            continue

        fila_encontrada = max(
            candidatos,
            key=lambda fila: abs(matriz[fila][columna])
        )

        if fila_encontrada != fila_pivote:
            intercambiar_filas(matriz, fila_pivote, fila_encontrada)
            pasos.append(
                PasoEliminacion(
                    operacion=f"F{fila_pivote + 1} ↔ F{fila_encontrada + 1}",
                    explicacion=(
                        f"Se intercambian F{fila_pivote + 1} y F{fila_encontrada + 1} "
                        f"para colocar en la posición pivote un valor no nulo "
                        f"de la columna {columna + 1} (variable {prefijo_variable}{columna + 1})."
                    ),
                    matriz=copiar_matriz(matriz),
                    tipo="intercambio",
                )
            )

        valor_pivote = matriz[fila_pivote][columna]

        # Convertir el pivote en 1.
        if valor_pivote != 1:
            inverso = Fraction(1, 1) / valor_pivote
            multiplicar_fila(matriz, fila_pivote, inverso)

            if inverso == -1:
                op_str = f"F{fila_pivote + 1} → -F{fila_pivote + 1}"
            else:
                k_inv = str(inverso.numerator) if inverso.denominator == 1 else f"({formatear_numero(inverso)})"
                op_str = f"F{fila_pivote + 1} → {k_inv}F{fila_pivote + 1}"

            pasos.append(
                PasoEliminacion(
                    operacion=op_str,
                    explicacion=(
                        f"Se multiplica F{fila_pivote + 1} por "
                        f"{formatear_numero(inverso)} para convertir el pivote "
                        f"de la columna {columna + 1} (variable {prefijo_variable}{columna + 1}) en 1."
                    ),
                    matriz=copiar_matriz(matriz),
                    tipo="escalado",
                )
            )

        # Hacer cero la columna del pivote en TODAS las demás filas.
        for fila in range(num_filas):
            if fila == fila_pivote:
                continue

            factor = matriz[fila][columna]
            if factor == 0:
                continue

            sumar_multiplo_fila(matriz, fila, fila_pivote, -factor)

            factor_abs = abs(factor)
            k_str = str(factor_abs.numerator) if factor_abs.denominator == 1 else f"({formatear_numero(factor_abs)})"
            if factor > 0:
                if factor_abs == 1:
                    op_str = f"F{fila + 1} → F{fila + 1} - F{fila_pivote + 1}"
                else:
                    op_str = f"F{fila + 1} → F{fila + 1} - {k_str}F{fila_pivote + 1}"
            else:
                if factor_abs == 1:
                    op_str = f"F{fila + 1} → F{fila + 1} + F{fila_pivote + 1}"
                else:
                    op_str = f"F{fila + 1} → F{fila + 1} + {k_str}F{fila_pivote + 1}"

            posicion = "debajo" if fila > fila_pivote else "arriba"
            pasos.append(
                PasoEliminacion(
                    operacion=op_str,
                    explicacion=(
                        f"Se hace cero el elemento de F{fila + 1} en la columna "
                        f"{columna + 1} (variable {prefijo_variable}{columna + 1}), {posicion} del pivote, usando F{fila_pivote + 1}."
                    ),
                    matriz=copiar_matriz(matriz),
                    tipo="eliminacion",
                )
            )

        columnas_pivote.append(columna)
        fila_pivote += 1

    return matriz, columnas_pivote, pasos

def fila_inconsistente(fila, num_variables):
    """Detecta una contradiccion: 0x1 + 0x2 + ... + 0xn = k, con k distinto de 0."""
    coeficientes_cero = all(fila[c] == 0 for c in range(num_variables))
    return coeficientes_cero and fila[-1] != 0


def es_sistema_homogeneo(b):
    """Un sistema es homogeneo cuando el vector b es todo ceros (Ax = 0)."""
    return all(valor == 0 for valor in b)


def clasificar_sistema(matriz_rref, columnas_pivote, num_variables):
    """Clasifica el sistema segun la forma escalonada reducida."""
    for fila in matriz_rref:
        if fila_inconsistente(fila, num_variables):
            return "Sistema inconsistente", "No tiene solucion."

    if len(columnas_pivote) == num_variables:
        return "Sistema consistente determinado", "Tiene una unica solucion."

    return "Sistema consistente indeterminado", "Tiene infinitas soluciones."


def obtener_solucion_unica(matriz_rref, columnas_pivote, num_variables):
    """Lee la solucion cuando cada variable tiene columna pivote."""
    solucion = [Fraction(0) for _ in range(num_variables)]
    for fila, columna in enumerate(columnas_pivote):
        solucion[columna] = matriz_rref[fila][-1]
    return solucion


def nombres_parametros(cantidad):
    """
    Genera nombres estándar para variables libres.
    - Para 1 variable libre: ['t']
    - Para 2 variables libres: ['s', 't']
    - Para 3 variables libres: ['r', 's', 't']
    - Para más variables libres: ['r', 's', 't', 'u', ...] o ['t1', 't2', ...]
    """
    if cantidad == 1:
        return ["t"]
    elif cantidad == 2:
        return ["s", "t"]
    elif cantidad == 3:
        return ["r", "s", "t"]
    base = ["r", "s", "t", "u", "v", "w"]
    if cantidad <= len(base):
        return base[:cantidad]
    return [f"t{i + 1}" for i in range(cantidad)]


def obtener_solucion_parametrica(matriz_rref, columnas_pivote, num_variables):
    """
    Expresa variables básicas en función de variables libres.

    Si una columna no es pivote, su variable queda libre y recibe un parámetro.
    """
    variables_libres = [c for c in range(num_variables) if c not in columnas_pivote]
    parametros = dict(zip(variables_libres, nombres_parametros(len(variables_libres))))
    expresiones = {}

    for libre, parametro in parametros.items():
        expresiones[libre] = parametro

    for fila, columna_pivote in enumerate(columnas_pivote):
        terminos = []
        independiente = matriz_rref[fila][-1]

        if independiente != 0:
            terminos.append(formatear_numero(independiente))

        for columna_libre in variables_libres:
            coeficiente = -matriz_rref[fila][columna_libre]
            if coeficiente == 0:
                continue

            parametro = parametros[columna_libre]
            if coeficiente == 1:
                terminos.append(parametro)
            elif coeficiente == -1:
                terminos.append(f"-{parametro}")
            else:
                terminos.append(f"{formatear_numero(coeficiente)}{parametro}")

        expresiones[columna_pivote] = " + ".join(terminos).replace("+ -", "- ") if terminos else "0"

    expresiones_ordenadas = {i: expresiones[i] for i in range(num_variables)}
    return expresiones_ordenadas, variables_libres, parametros


def obtener_nombres_variables(num_variables, prefijo="x"):
    """Genera nombres de variables consistentes: x1, x2, x3, ... o c1, c2, c3, ..."""
    return [f"{prefijo}{i + 1}" for i in range(num_variables)]


def formatear_ecuacion_original(fila_coefs, termino_indep, nombres_vars):
    """
    Formatea la ecuacion algebraica original a partir de los coeficientes y terminos independientes.
    Omite coeficientes 0, muestra 1x como x, -1x como -x, y maneja signos + / - correctamente.
    """
    terminos = []
    for j, c in enumerate(fila_coefs):
        if c == 0:
            continue
        var = nombres_vars[j]
        if c == 1:
            term_str = var if not terminos else f"+ {var}"
        elif c == -1:
            term_str = f"-{var}" if not terminos else f"- {var}"
        elif c > 0:
            c_str = formatear_numero(c)
            if c.denominator != 1:
                c_str = f"({c_str})"
            term_str = f"{c_str}{var}" if not terminos else f"+ {c_str}{var}"
        else:
            c_str = formatear_numero(abs(c))
            if abs(c).denominator != 1:
                c_str = f"({c_str})"
            term_str = f"-{c_str}{var}" if not terminos else f"- {c_str}{var}"
        terminos.append(term_str)

    lado_izq = " ".join(terminos) if terminos else "0"
    lado_der = formatear_numero(termino_indep)
    return f"{lado_izq} = {lado_der}"


def formatear_sustitucion(fila_coefs, termino_indep, solucion):
    """
    Genera la expresion de sustitucion explicita con parentesis para cada variable:
    ejemplo: 2(1) - (2) + (3) = 3 o 2(1) - 3(2) + (4) = 7.
    """
    terminos = []
    for j, c in enumerate(fila_coefs):
        if c == 0:
            continue
        val = solucion[j]
        val_str = f"({formatear_numero(val)})"

        if c == 1:
            term_str = val_str if not terminos else f"+ {val_str}"
        elif c == -1:
            term_str = f"-{val_str}" if not terminos else f"- {val_str}"
        elif c > 0:
            c_str = formatear_numero(c)
            term_str = f"{c_str}{val_str}" if not terminos else f"+ {c_str}{val_str}"
        else:
            c_str = formatear_numero(abs(c))
            term_str = f"-{c_str}{val_str}" if not terminos else f"- {c_str}{val_str}"
        terminos.append(term_str)

    lado_izq = " ".join(terminos) if terminos else "0"
    lado_der = formatear_numero(termino_indep)
    return f"{lado_izq} = {lado_der}"


def formatear_simplificacion(fila_coefs, termino_indep, solucion):
    """
    Evalua paso a paso la simplificacion de los terminos sustituidos:
    1. Productos individuales evaluados: 2 - 2 + 3 = 3
    2. Suma total evaluada: 3 = 3
    """
    pasos_simpl = []
    productos = []

    for j, c in enumerate(fila_coefs):
        if c == 0:
            continue
        prod = c * solucion[j]
        productos.append(prod)

    if len(productos) > 1:
        partes = []
        for p in productos:
            if not partes:
                partes.append(formatear_numero(p))
            else:
                if p >= 0:
                    partes.append(f"+ {formatear_numero(p)}")
                else:
                    partes.append(f"- {formatear_numero(abs(p))}")
        linea_intermedia = f"{' '.join(partes)} = {formatear_numero(termino_indep)}"
        pasos_simpl.append(linea_intermedia)

    suma_total = sum(productos) if productos else Fraction(0)
    linea_final = f"{formatear_numero(suma_total)} = {formatear_numero(termino_indep)}"
    pasos_simpl.append(linea_final)

    coincide = (suma_total == termino_indep)
    return pasos_simpl, coincide, suma_total


class DetalleVerificacion(dict):
    """
    Representa la verificacion explicativa de una ecuacion individual del sistema.
    Soporta acceso como dict (d['ecuacion_original']), atributos (d.ecuacion_original)
    e indexacion por tupla [0]=suma_obtenida, [1]=esperado, [2]=coincide para maxima compatibilidad.
    """

    def __init__(self, indice, ecuacion_original, sustitucion, simplificacion, suma_obtenida, esperado, coincide):
        super().__init__(
            indice=indice,
            ecuacion_original=ecuacion_original,
            sustitucion=sustitucion,
            simplificacion=simplificacion,
            suma_obtenida=suma_obtenida,
            esperado=esperado,
            coincide=coincide,
        )
        self.indice = indice
        self.ecuacion_original = ecuacion_original
        self.sustitucion = sustitucion
        self.simplificacion = simplificacion
        self.suma_obtenida = suma_obtenida
        self.esperado = esperado
        self.coincide = coincide

    def __getitem__(self, key):
        if isinstance(key, int):
            return [self["suma_obtenida"], self["esperado"], self["coincide"]][key]
        return super().__getitem__(key)


def verificar_solucion(A_original, b_original, solucion):
    """
    Verifica Ax = b usando el sistema original de forma explicativa y pedagogica.
    Genera la ecuacion original, la sustitucion explicita y la simplificacion paso a paso.
    """
    if not A_original or not b_original:
        return False, []

    num_vars = len(A_original[0])

    if len(A_original) != len(b_original):
        return False, []

    if any(len(fila) != num_vars for fila in A_original):
        return False, []

    if len(solucion) != num_vars:
        return False, []

    nombres_vars = obtener_nombres_variables(num_vars)
    detalles = []
    correcta = True

    for i, fila in enumerate(A_original):
        esperado = b_original[i]

        # La comprobación real se hace con el sistema ORIGINAL,
        # no con la matriz reducida.
        suma_directa = sum(
            fila[j] * solucion[j] for j in range(num_vars)
        )
        coincide = suma_directa == esperado

        orig_str = formatear_ecuacion_original(fila, esperado, nombres_vars)
        sust_str = formatear_sustitucion(fila, esperado, solucion)
        simpl_pasos, _, _ = formatear_simplificacion(fila, esperado, solucion)

        # La suma calculada directamente es la autoridad de la verificación.
        correcta = correcta and coincide

        detalles.append(
            DetalleVerificacion(
                indice=i + 1,
                ecuacion_original=orig_str,
                sustitucion=sust_str,
                simplificacion=simpl_pasos,
                suma_obtenida=suma_directa,
                esperado=esperado,
                coincide=coincide,
            )
        )

    return correcta, detalles


def resolver_sistema(A, b, prefijo_variable="x"):
    """
    Funcion principal de la parte matematica para resolver sistemas Ax = b.
    Acepta el prefijo_variable ('x' para sistemas de ecuaciones, 'c' para combinacion lineal).
    """
    num_variables = len(A[0])
    nombres_vars = obtener_nombres_variables(num_variables, prefijo=prefijo_variable)
    aumentada = crear_matriz_aumentada(A, b)
    rref, columnas_pivote, pasos = gauss_jordan(aumentada, num_variables, prefijo_variable=prefijo_variable)
    clasificacion, descripcion = clasificar_sistema(rref, columnas_pivote, num_variables)

    resultado = {
        "matriz_inicial": aumentada,
        "matriz_final": rref,
        "pasos": pasos,
        "columnas_pivote": columnas_pivote,
        "variables_basicas": columnas_pivote,
        "variables_libres": [c for c in range(num_variables) if c not in columnas_pivote],
        "nombres_variables": nombres_vars,
        "prefijo_variable": prefijo_variable,
        "clasificacion": clasificacion,
        "descripcion": descripcion,
        "homogeneo": es_sistema_homogeneo(b),
        "solucion": None,
        "expresiones": None,
        "solucion_particular": None,
        "verificacion": None,
    }

    if clasificacion == "Sistema consistente determinado":
        solucion = obtener_solucion_unica(rref, columnas_pivote, num_variables)
        resultado["solucion"] = solucion
        resultado["verificacion"] = verificar_solucion(A, b, solucion)

    elif clasificacion == "Sistema consistente indeterminado":
        expresiones, libres, parametros = obtener_solucion_parametrica(
            rref, columnas_pivote, num_variables
        )
        # Para verificar una solución infinita elegimos todos los parámetros = 0.
        # Así, las variables libres valen 0 y cada variable básica toma
        # exactamente el término independiente de su fila pivote.
        solucion_particular = [Fraction(0) for _ in range(num_variables)]
        for fila, columna_pivote in enumerate(columnas_pivote):
            solucion_particular[columna_pivote] = rref[fila][-1]

        resultado["expresiones"] = expresiones
        resultado["variables_libres"] = libres
        resultado["parametros"] = parametros
        resultado["solucion_particular"] = solucion_particular
        resultado["verificacion"] = verificar_solucion(A, b, solucion_particular)

    return resultado


# -----------------------------------------------------------------------------
# Modulo de Vectores en R^n (Tarea 3)
# -----------------------------------------------------------------------------

def validar_vector(v, nombre="Vector"):
    """
    Valida algebraicamente que la entrada sea una lista no vacia con elementos numericos/Fraction.
    Garantiza que el objeto corresponda a un vector valido en R^n.
    """
    if not isinstance(v, list) or len(v) == 0:
        raise ValueError(f"{nombre} debe ser una lista con al menos un elemento.")
    for i, x in enumerate(v):
        if not isinstance(x, (Fraction, int)):
            raise ValueError(f"El componente {i + 1} de {nombre} no es un valor numerico valido.")


def sumar_vectores(v1, v2):
    """
    Suma algebraica de dos vectores en R^n componente a componente:
    v1 + v2 = [u_1 + v_1, u_2 + v_2, ..., u_n + v_n].
    Procedimiento algebraico:
    1. Verifica que ambos vectores pertenezcan al mismo espacio R^n (dimensiones compatibles).
    2. Realiza la adicion escalar de los componentes homólogos.
    """
    validar_vector(v1, "v1")
    validar_vector(v2, "v2")
    if len(v1) != len(v2):
        raise ValueError(
            f"Dimensiones incompatibles para suma de vectores: "
            f"v1 pertenece a R^{len(v1)} y v2 pertenece a R^{len(v2)}. "
            f"Para sumarse, ambos vectores deben tener exactamente la misma dimension."
        )
    return [v1[i] + v2[i] for i in range(len(v1))]


def restar_vectores(v1, v2):
    """
    Resta algebraica de dos vectores en R^n componente a componente:
    v1 - v2 = [u_1 - v_1, u_2 - v_2, ..., u_n - v_n].
    Procedimiento algebraico:
    1. Verifica que ambos vectores pertenezcan al mismo espacio R^n (dimensiones compatibles).
    2. Suma al primer vector el opuesto aditivo del segundo vector.
    """
    validar_vector(v1, "v1")
    validar_vector(v2, "v2")
    if len(v1) != len(v2):
        raise ValueError(
            f"Dimensiones incompatibles para resta de vectores: "
            f"v1 pertenece a R^{len(v1)} y v2 pertenece a R^{len(v2)}. "
            f"Para restarse, ambos vectores deben tener exactamente la misma dimension."
        )
    return [v1[i] - v2[i] for i in range(len(v1))]


def multiplicar_vector_escalar(escalar, v):
    """
    Multiplicacion de un vector en R^n por un escalar c:
    c * v = [c * v_1, c * v_2, ..., c * v_n].
    Procedimiento algebraico:
    Escala la magnitud del vector multiplicando cada una de sus coordenadas por el escalar.
    """
    validar_vector(v, "v")
    c = escalar if isinstance(escalar, Fraction) else Fraction(escalar)
    return [c * x for x in v]


def formatear_vector(v):
    """Retorna la representacion textual de un vector en R^n: [x1, x2, ..., xn]."""
    return "[" + ", ".join(formatear_numero(x) for x in v) + "]"


# -----------------------------------------------------------------------------
# Modulo de Operaciones con Matrices (Tarea 3)
# -----------------------------------------------------------------------------

def validar_matriz(matriz, nombre="Matriz"):
    """
    Valida que una matriz sea una lista de listas no vacia, rectangular,
    con elementos numericos o Fraction exactos.
    """
    if not isinstance(matriz, list) or len(matriz) == 0:
        raise ValueError(f"{nombre} debe tener al menos una fila.")
    num_cols = len(matriz[0]) if isinstance(matriz[0], list) else 0
    if num_cols == 0:
        raise ValueError(f"{nombre} debe tener al menos una columna.")
    for i, fila in enumerate(matriz):
        if not isinstance(fila, list) or len(fila) != num_cols:
            raise ValueError(
                f"{nombre} mal formada: la fila {i + 1} tiene longitud distinta a la primera fila."
            )
        for j, val in enumerate(fila):
            if not isinstance(val, (Fraction, int)):
                raise ValueError(
                    f"Elemento no numerico en posicion ({i + 1}, {j + 1}) de {nombre}."
                )


def dimensiones_matriz(matriz):
    """Retorna las dimensiones (filas, columnas) de una matriz."""
    return len(matriz), len(matriz[0])


def sumar_matrices(A, B):
    """
    Suma de matrices A + B implementada manualmente mediante bucles anidados.
    Procedimiento algebraico:
    C[i][j] = A[i][j] + B[i][j].
    Requiere que ambas matrices tengan exactamente las mismas dimensiones (m x n).
    """
    validar_matriz(A, "A")
    validar_matriz(B, "B")
    mA, nA = dimensiones_matriz(A)
    mB, nB = dimensiones_matriz(B)
    if mA != mB or nA != nB:
        raise ValueError(
            f"Dimensiones incompatibles para suma de matrices: "
            f"A es de {mA}x{nA} y B es de {mB}x{nB}. "
            f"Para sumarse, ambas matrices deben tener el mismo tamano (filas y columnas iguales)."
        )
    return [[A[i][j] + B[i][j] for j in range(nA)] for i in range(mA)]


def restar_matrices(A, B):
    """
    Resta de matrices A - B implementada manualmente mediante bucles anidados.
    Procedimiento algebraico:
    C[i][j] = A[i][j] - B[i][j].
    Requiere que ambas matrices tengan exactamente las mismas dimensiones (m x n).
    """
    validar_matriz(A, "A")
    validar_matriz(B, "B")
    mA, nA = dimensiones_matriz(A)
    mB, nB = dimensiones_matriz(B)
    if mA != mB or nA != nB:
        raise ValueError(
            f"Dimensiones incompatibles para resta de matrices: "
            f"A es de {mA}x{nA} y B es de {mB}x{nB}. "
            f"Para restarse, ambas matrices deben tener el mismo tamano (filas y columnas iguales)."
        )
    return [[A[i][j] - B[i][j] for j in range(nA)] for i in range(mA)]


def multiplicar_matriz_escalar(escalar, A):
    """
    Multiplicacion de una matriz A por un escalar c:
    (c * A)[i][j] = c * A[i][j].
    Procedimiento algebraico:
    Multiplica cada entrada de la matriz por el factor escalar especificado.
    """
    validar_matriz(A, "A")
    c = escalar if isinstance(escalar, Fraction) else Fraction(escalar)
    mA, nA = dimensiones_matriz(A)
    return [[c * A[i][j] for j in range(nA)] for i in range(mA)]


def multiplicar_matrices(A, B):
    """
    Multiplicacion matricial A(m x n) * B(n x p) = C(m x p)
    implementada manualmente mediante bucles anidados (sin librerias externas).
    Procedimiento algebraico:
    Cada entrada C[i][j] es el producto punto entre la fila i de A y la columna j de B:
    C[i][j] = sum_{k=0}^{n-1} A[i][k] * B[k][j].
    Valida algebraicamente que el numero de columnas de A coincida con las filas de B (nA == mB).
    """
    validar_matriz(A, "A")
    validar_matriz(B, "B")
    mA, nA = dimensiones_matriz(A)
    mB, pB = dimensiones_matriz(B)

    if nA != mB:
        raise ValueError(
            f"Dimensiones incompatibles para multiplicacion matricial: "
            f"A tiene {nA} columnas pero B tiene {mB} filas. "
            f"Para multiplicar A({mA}x{nA}) por B({mB}x{pB}), el numero de columnas de A "
            f"debe ser exactamente igual al numero de filas de B (nA = mB)."
        )

    C = [[Fraction(0) for _ in range(pB)] for _ in range(mA)]
    for i in range(mA):
        for j in range(pB):
            suma = Fraction(0)
            for k in range(nA):
                suma += A[i][k] * B[k][j]
            C[i][j] = suma
    return C


def matriz_simple_a_texto(matriz):
    """Formatea una matriz estandar en texto alineado entre corchetes."""
    if not matriz or not matriz[0]:
        return "[]"
    num_cols = len(matriz[0])
    anchos = [0] * num_cols
    for fila in matriz:
        for c, val in enumerate(fila):
            txt = formatear_numero(val)
            if len(txt) > anchos[c]:
                anchos[c] = len(txt)
    anchos = [max(w, 4) for w in anchos]
    lineas = []
    for fila in matriz:
        elementos = "  ".join(f"{formatear_numero(fila[c]):>{anchos[c]}}" for c in range(num_cols))
        lineas.append(f"[ {elementos} ]")
    return "\n".join(lineas)


# -----------------------------------------------------------------------------
# Modulo de Combinacion Lineal y Ecuacion Vectorial (Tarea 3)
# -----------------------------------------------------------------------------

def construir_matriz_desde_vectores(vectores):
    """
    Construye la matriz A cuyas COLUMNAS corresponden a los vectores {v1, v2, ..., vk}.
    Si cada vector vi pertenece a R^n, la matriz resultante tendra dimension n x k.
    Procedimiento algebraico:
    Cada columna j de la matriz A es el vector v_{j+1}.
    """
    if not vectores:
        raise ValueError("El conjunto de vectores no puede estar vacio.")
    n = len(vectores[0])
    for idx, v in enumerate(vectores):
        validar_vector(v, f"v{idx + 1}")
        if len(v) != n:
            raise ValueError(
                f"Dimension incompatible: el vector v{idx + 1} tiene dimension {len(v)}, "
                f"mientras que v1 tiene dimension {n}. Todos los vectores deben estar en el mismo R^{n}."
            )
    k = len(vectores)
    A = [[vectores[j][i] for j in range(k)] for i in range(n)]
    return A


def verificar_combinacion_lineal(vectores, b, solucion):
    """
    Comprueba formalmente la combinacion lineal c1*v1 + c2*v2 + ... + ck*vk = b.
    Procedimiento algebraico:
    1. Multiplica cada escalar cj por el vector correspondiente vj.
    2. Suma los vectores ponderados para obtener el vector calculado v_calculado.
    3. Compara v_calculado componente a componente con el vector objetivo b.
    4. Retorna el estado y la expresion textual sustituida.
    """
    k = len(vectores)
    n = len(b)
    v_calculado = [Fraction(0) for _ in range(n)]

    for j in range(k):
        cj = solucion[j]
        for i in range(n):
            v_calculado[i] += cj * vectores[j][i]

    coincide = (v_calculado == b)

    terminos = []
    for j in range(k):
        cj = solucion[j]
        c_str = f"({formatear_numero(cj)})"
        terminos.append(f"{c_str}v{j + 1}")
    expresion_combinacion = " + ".join(terminos)

    detalles = {
        "coincide": coincide,
        "expresion_combinacion": expresion_combinacion,
        "vector_calculado": v_calculado,
        "vector_esperado": b,
    }
    return coincide, detalles


def analizar_combinacion_lineal(vectores, b):
    """
    Determina si un vector objetivo b es combinacion lineal de {v1, ..., vk}:
    c1*v1 + c2*v2 + ... + ck*vk = b.

    Procedimiento algebraico:
    1. Plantea la ecuacion vectorial c1*v1 + ... + ck*vk = b.
    2. Transforma la ecuacion vectorial en el sistema de ecuaciones A*c = b,
       donde las columnas de A son los vectores vi y c = [c1, ..., ck]^T.
    3. Construye la matriz aumentada [A | b] = [v1 v2 ... vk | b].
    4. Resuelve el sistema mediante eliminacion manual de Gauss-Jordan con variables c1, ..., ck.
    5. Concluye si existe o no combinacion lineal, si es unica o infinita, y verifica el resultado.
    """
    if not vectores:
        raise ValueError("Debe ingresar al menos un vector.")
    n = len(vectores[0])
    validar_vector(b, "b")
    if len(b) != n:
        raise ValueError(
            f"El vector objetivo b tiene dimension {len(b)}, pero los vectores vi "
            f"pertenecen a R^{n}. Para plantear la combinacion lineal deben tener la misma dimension."
        )

    A = construir_matriz_desde_vectores(vectores)
    res_sistema = resolver_sistema(A, b, prefijo_variable="c")

    clasificacion = res_sistema["clasificacion"]
    es_posible = ("inconsistente" not in clasificacion.lower())
    k = len(vectores)

    if clasificacion == "Sistema consistente determinado":
        conclusion = (
            f"El vector b SI es combinacion lineal unica del conjunto de vectores. "
            f"Existen valores unicos para los coeficientes c1, ..., c{k} que satisfacen b = c1*v1 + ... + ck*vk."
        )
        sol = res_sistema["solucion"]
        coincide_vec, det_vec = verificar_combinacion_lineal(vectores, b, sol)
    elif clasificacion == "Sistema consistente indeterminado":
        conclusion = (
            f"El vector b SI es combinacion lineal del conjunto de vectores, "
            f"con INFINITAS combinaciones posibles debido a la presencia de variables libres."
        )
        sol_part = res_sistema["solucion_particular"]
        coincide_vec, det_vec = verificar_combinacion_lineal(vectores, b, sol_part)
    else:
        conclusion = (
            f"El vector b NO es combinacion lineal del conjunto de vectores dados. "
            f"El sistema es inconsistente (b no pertenece al espacio generado Gen{{v1, ..., v{k}}})."
        )
        coincide_vec, det_vec = False, None

    return {
        "vectores": vectores,
        "b": b,
        "matriz_A": A,
        "sistema": res_sistema,
        "es_posible": es_posible,
        "conclusion": conclusion,
        "verificacion_vectorial": det_vec,
    }


# -----------------------------------------------------------------------------
# Modulo de Independencia Lineal (Tarea 3)
# -----------------------------------------------------------------------------

def analizar_independencia_lineal(vectores):
    """
    Determina si un conjunto de vectores {v1, v2, ..., vk} en R^n es:
    - Linealmente Independiente (LI), o
    - Linealmente Dependiente (LD).

    Procedimiento algebraico:
    1. Plantea la ecuacion vectorial homogenea:
       c1*v1 + c2*v2 + ... + ck*vk = 0.
    2. Construye el sistema homogeneo correspondiente [A | 0], donde las columnas
       de A son los vectores v1, ..., vk.
    3. Resuelve el sistema homogeneo mediante eliminacion manual de Gauss-Jordan.
    4. Analiza la cantidad de pivotes y variables libres:
       - Si cada columna tiene pivote (rango = k, sin variables libres):
         la UNICA solucion es la trivial c1 = c2 = ... = ck = 0 => LINEALMENTE INDEPENDIENTE.
       - Si existen columnas sin pivote (variables libres):
         existen soluciones NO triviales => LINEALMENTE DEPENDIENTE.
    """
    if not vectores:
        raise ValueError("Debe ingresar al menos un vector.")
    n = len(vectores[0])
    k = len(vectores)
    A = construir_matriz_desde_vectores(vectores)
    b_cero = [Fraction(0) for _ in range(n)]

    res_sistema = resolver_sistema(A, b_cero, prefijo_variable="c")

    num_pivotes = len(res_sistema["columnas_pivote"])
    num_libres = len(res_sistema["variables_libres"])

    tiene_vector_cero = any(all(x == 0 for x in v) for v in vectores)
    es_li = (num_pivotes == k)

    razones = []
    if tiene_vector_cero:
        razones.append("El conjunto contiene el vector cero (0), por lo que siempre es linealmente dependiente.")
    if k > n:
        razones.append(f"El conjunto contiene {k} vectores en R^{n} (k > n). Por teorema de algebra lineal, cualquier conjunto con mas vectores que la dimension del espacio es forzosamente linealmente dependiente.")

    if es_li:
        clasificacion_il = "LINEALMENTE INDEPENDIENTE (LI)"
        conclusion = (
            f"El conjunto de vectores es LINEALMENTE INDEPENDIENTE. "
            f"El sistema homogeneo tiene unicamente la solucion trivial (c1 = c2 = ... = c{k} = 0). "
            f"Cada vector aporta una direccion independiente ({num_pivotes} pivotes para {k} columnas, sin variables libres). "
            f"Ningun vector del conjunto puede expresarse como combinacion lineal de los demas."
        )
        relacion_dependencia = None
    else:
        clasificacion_il = "LINEALMENTE DEPENDIENTE (LD)"
        conclusion = (
            f"El conjunto de vectores es LINEALMENTE DEPENDIENTE. "
            f"El sistema homogeneo admite soluciones NO triviales (se encontraron {num_libres} variable(s) libre(s)). "
            f"Existe al menos una relacion no trivial entre los vectores que genera el vector cero."
        )
        sol_no_trivial = [Fraction(0) for _ in range(k)]
        if res_sistema["variables_libres"]:
            primera_libre = res_sistema["variables_libres"][0]
            sol_no_trivial[primera_libre] = Fraction(1)
            for fila_idx, col_piv in enumerate(res_sistema["columnas_pivote"]):
                coef_libre = res_sistema["matriz_final"][fila_idx][primera_libre]
                sol_no_trivial[col_piv] = -coef_libre

        terminos_rel = []
        for j in range(k):
            cj = sol_no_trivial[j]
            if cj != 0:
                terminos_rel.append(f"({formatear_numero(cj)})v{j + 1}")
        relacion_dependencia = " + ".join(terminos_rel) + " = 0" if terminos_rel else None

    return {
        "es_li": es_li,
        "clasificacion": clasificacion_il,
        "vectores": vectores,
        "matriz_A": A,
        "sistema": res_sistema,
        "num_vectores": k,
        "dimension": n,
        "num_pivotes": num_pivotes,
        "num_libres": num_libres,
        "conclusion": conclusion,
        "razones_adicionales": razones,
        "relacion_dependencia": relacion_dependencia,
    }


# -----------------------------------------------------------------------------
# Configuracion visual
# -----------------------------------------------------------------------------
# Paleta basada en los colores del escudo de la Universidad Americana (UAM):
# el turquesa/teal institucional como color primario, con un fondo oscuro
# de contraste para que la interfaz se vea moderna y profesional.

# Cada valor es una tupla (modo_claro, modo_oscuro). CustomTkinter aplica
# automaticamente el color correcto segun el modo activo (ctk.set_appearance_mode).
# En modo claro: fondo blanco y texto en el turquesa institucional #04A7AD.
PALETA = {
    "fondo": ("#FFFFFF", "#0B1B1C"),
    "sidebar": ("#FFFFFF", "#08292B"),
    "panel": ("#FFFFFF", "#0F2F31"),
    "panel_2": ("#EAF8F8", "#153B3E"),
    "entrada": ("#FFFFFF", "#0B2426"),
    "borde": ("#BFEBEA", "#1F5457"),
    "texto": ("#04A7AD", "#F4FBFB"),
    "texto_2": ("#04A7AD", "#C8E7E6"),
    "texto_3": ("#4FC2C7", "#7FB8B7"),
    "primario": ("#04A7AD", "#04A7AD"),
    "primario_hover": ("#03888D", "#03888D"),
    "secundario": ("#EAF8F8", "#1F5457"),
    "secundario_hover": ("#D4F1F0", "#2B6E71"),
    "exito": ("#1FA463", "#2ED573"),
    "advertencia": ("#C97F0E", "#F5A623"),
    "error": ("#D93C3C", "#EF4B4B"),
}

FUENTE_TITULO = ("Segoe UI", 26, "bold")
FUENTE_SUBTITULO = ("Segoe UI", 14)
FUENTE_SECCION = ("Segoe UI", 17, "bold")
FUENTE_NORMAL = ("Segoe UI", 13)
FUENTE_PEQUENA = ("Segoe UI", 11)
FUENTE_MONO = ("Consolas", 15)


# -----------------------------------------------------------------------------
# Componentes de interfaz
# -----------------------------------------------------------------------------

def configurar_customtkinter():
    if ctk is None:
        return
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def resolver_color(par):
    """
    Convierte una tupla (claro, oscuro) de PALETA en el color concreto que
    corresponde al modo oscuro permanente. Se usa para widgets nativos de
    tkinter (como tk.Canvas).
    """
    if isinstance(par, tuple):
        return par[1]
    return par


def cargar_logo(tamano=(96, 96)):
    """Carga el logo de la UAM como CTkImage, si esta disponible. Imprime info de depuración."""
    if ctk is None or Image is None:
        print("cargar_logo: customtkinter o PIL no disponibles (ctk, Image):", bool(ctk), bool(Image))
        return None
    print("cargar_logo: buscando logo en:", RUTA_LOGO, "->", os.path.exists(RUTA_LOGO))
    if not os.path.exists(RUTA_LOGO):
        return None
    try:
        imagen = Image.open(RUTA_LOGO).convert("RGBA")
        logo = ctk.CTkImage(light_image=imagen, dark_image=imagen, size=tamano)
        return logo
    except Exception as e:
        print("Error cargando logo:", e)
        return None


def crear_tarjeta(parent, titulo=None):
    tarjeta = ctk.CTkFrame(
        parent,
        fg_color=PALETA["panel"],
        corner_radius=12,
        border_width=1,
        border_color=PALETA["borde"],
    )
    if titulo:
        ctk.CTkLabel(
            tarjeta,
            text=titulo,
            font=FUENTE_SECCION,
            text_color=PALETA["texto"],
        ).pack(anchor="w", padx=18, pady=(16, 8))
    return tarjeta


class MatrixInputPanel(ctk.CTkFrame):
    """Componente visual para capturar la matriz aumentada [A | b]."""

    def __init__(self, parent, on_resolver, on_limpiar):
        super().__init__(parent, fg_color=PALETA["panel"], corner_radius=12, border_width=1, border_color=PALETA["borde"])
        self.on_resolver = on_resolver
        self.on_limpiar = on_limpiar
        self.entradas = []
        self.m = 0
        self.n = 0

        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=18, pady=(16, 8))

        ctk.CTkLabel(self.header, text="Matriz aumentada [A | b]", font=FUENTE_SECCION).pack(side="left")
        self.dimension_label = ctk.CTkLabel(self.header, text="", font=FUENTE_PEQUENA, text_color=PALETA["texto_3"])
        self.dimension_label.pack(side="right")

        self.canvas_frame = ctk.CTkFrame(self, fg_color=PALETA["panel_2"], corner_radius=10)
        self.canvas_frame.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg=resolver_color(PALETA["panel_2"]),
            highlightthickness=0,
            height=230,
        )
        self.scroll_y = ctk.CTkScrollbar(
            self.canvas_frame, orientation="vertical", command=self.canvas.yview,
            button_color=PALETA["primario"], button_hover_color=PALETA["primario_hover"],
        )
        self.scroll_x = ctk.CTkScrollbar(
            self.canvas_frame, orientation="horizontal", command=self.canvas.xview,
            button_color=PALETA["primario"], button_hover_color=PALETA["primario_hover"],
        )
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(12, 4), pady=(12, 4))
        self.scroll_y.grid(row=0, column=1, sticky="ns", pady=(12, 4), padx=(0, 8))
        self.scroll_x.grid(row=1, column=0, sticky="ew", padx=(12, 4), pady=(0, 8))
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        self.grid_host = ctk.CTkFrame(self.canvas, fg_color="transparent")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.grid_host, anchor="nw")
        self.grid_host.bind("<Configure>", self._actualizar_scroll)

        self.actions = ctk.CTkFrame(self, fg_color="transparent")
        self.actions.pack(fill="x", padx=18, pady=(0, 16))

        self.solve_button = ctk.CTkButton(
            self.actions,
            text="Resolver sistema",
            height=42,
            corner_radius=8,
            fg_color=PALETA["primario"],
            hover_color=PALETA["primario_hover"],
            text_color="#04191A",
            font=("Segoe UI", 13, "bold"),
            command=self.on_resolver,
        )
        self.solve_button.pack(side="left")

        ctk.CTkButton(
            self.actions,
            text="Limpiar",
            height=42,
            corner_radius=8,
            fg_color=PALETA["secundario"],
            hover_color=PALETA["secundario_hover"],
            command=self.on_limpiar,
        ).pack(side="left", padx=10)

    def _actualizar_scroll(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def actualizar_tema_canvas(self):
        """Vuelve a pintar el canvas nativo con el color correcto tras cambiar de tema."""
        self.canvas.configure(bg=resolver_color(PALETA["panel_2"]))

    def crear_matriz(self, m, n):
        for widget in self.grid_host.winfo_children():
            widget.destroy()

        self.m = m
        self.n = n
        self.entradas = []
        self.dimension_label.configure(text=f"{m} ecuaciones x {n} variables")

        for j in range(n):
            ctk.CTkLabel(
                self.grid_host,
                text=f"x{j + 1}",
                font=("Segoe UI", 12, "bold"),
                text_color=PALETA["primario"],
            ).grid(row=0, column=j, padx=4, pady=(4, 8))

        ctk.CTkLabel(
            self.grid_host,
            text="b",
            font=("Segoe UI", 12, "bold"),
            text_color=PALETA["primario"],
        ).grid(row=0, column=n + 1, padx=4, pady=(4, 8))

        for i in range(m):
            fila = []
            for j in range(n):
                entrada = ctk.CTkEntry(
                    self.grid_host,
                    width=72,
                    height=36,
                    justify="center",
                    font=FUENTE_NORMAL,
                    fg_color=PALETA["entrada"],
                    border_color=PALETA["borde"],
                )
                entrada.grid(row=i + 1, column=j, padx=4, pady=5)
                entrada.insert(0, "0")
                fila.append(entrada)

            separador = ctk.CTkFrame(self.grid_host, width=2, height=36, fg_color=PALETA["primario"])
            separador.grid(row=i + 1, column=n, padx=12, pady=5)

            entrada_b = ctk.CTkEntry(
                self.grid_host,
                width=72,
                height=36,
                justify="center",
                font=FUENTE_NORMAL,
                fg_color=PALETA["entrada"],
                border_color=PALETA["borde"],
            )
            entrada_b.grid(row=i + 1, column=n + 1, padx=4, pady=5)
            entrada_b.insert(0, "0")
            fila.append(entrada_b)
            self.entradas.append(fila)

        self._actualizar_scroll()

    def limpiar(self):
        for fila in self.entradas:
            for entrada in fila:
                entrada.delete(0, "end")
                entrada.insert(0, "0")

    def leer_datos(self):
        A = []
        b = []
        for fila in self.entradas:
            valores = [convertir_numero(entrada.get()) for entrada in fila]
            A.append(valores[:-1])
            b.append(valores[-1])
        return A, b


class ProcessPanel(ctk.CTkFrame):
    """Muestra las operaciones elementales, explicaciones pedagogicas y la matriz tras cada paso con scroll 2D."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent", corner_radius=0, border_width=0)

        self.canvas_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.canvas_frame.pack(fill="both", expand=True, padx=4, pady=4)

        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg=resolver_color(PALETA["panel"]),
            highlightthickness=0,
            bd=0,
        )
        self.scroll_y = ctk.CTkScrollbar(
            self.canvas_frame, orientation="vertical", command=self.canvas.yview,
            button_color=PALETA["primario"], button_hover_color=PALETA["primario_hover"],
        )
        self.scroll_x = ctk.CTkScrollbar(
            self.canvas_frame, orientation="horizontal", command=self.canvas.xview,
            button_color=PALETA["primario"], button_hover_color=PALETA["primario_hover"],
        )
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns", padx=(4, 0))
        self.scroll_x.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        self.grid_host = ctk.CTkFrame(self.canvas, fg_color="transparent")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.grid_host, anchor="nw")

        self.grid_host.bind("<Configure>", self._actualizar_scroll)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        self.mostrar_placeholder()

    def _on_mousewheel(self, event):
        if event.state & 0x0001:
            self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _actualizar_scroll(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        width = max(event.width, self.grid_host.winfo_reqwidth())
        self.canvas.itemconfig(self.canvas_window, width=width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def limpiar(self):
        for widget in self.grid_host.winfo_children():
            widget.destroy()

    def mostrar_placeholder(self):
        self.limpiar()
        ctk.CTkLabel(
            self.grid_host,
            text="Crea un sistema, ingresa los coeficientes y presiona Resolver sistema para ver el procedimiento paso a paso.",
            font=FUENTE_NORMAL,
            text_color=PALETA["texto_3"],
            wraplength=520,
            justify="left",
        ).pack(anchor="w", padx=14, pady=14)

    def mostrar_pasos(self, pasos):
        self.limpiar()
        for indice, paso in enumerate(pasos):
            if isinstance(paso, dict):
                operacion = paso.get("operacion", "")
                explicacion = paso.get("explicacion", "")
                matriz = paso.get("matriz", [])
                tipo = paso.get("tipo", "")
            elif hasattr(paso, "operacion"):
                operacion = paso.operacion
                explicacion = paso.explicacion
                matriz = paso.matriz
                tipo = getattr(paso, "tipo", "")
            else:
                operacion = paso[0]
                matriz = paso[1]
                explicacion = paso[2] if len(paso) > 2 else ""
                tipo = ""

            es_inicial = (indice == 0) or (tipo == "inicial")
            titulo_paso = "Matriz aumentada inicial" if es_inicial else f"Paso {indice}"

            item = ctk.CTkFrame(self.grid_host, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
            item.pack(fill="x", expand=True, pady=(0, 12), padx=2)

            cabecera = ctk.CTkFrame(item, fg_color="transparent")
            cabecera.pack(fill="x", padx=14, pady=(10, 6))

            ctk.CTkLabel(
                cabecera,
                text=titulo_paso,
                font=("Segoe UI", 12, "bold"),
                text_color="#04191A",
                fg_color=PALETA["primario"],
                corner_radius=6,
                padx=8,
                pady=2,
            ).pack(side="left", padx=(0, 10))

            if not es_inicial:
                ctk.CTkLabel(
                    cabecera,
                    text=f"Operación: {operacion}",
                    font=("Segoe UI", 13, "bold"),
                    text_color=PALETA["texto"],
                ).pack(side="left")

            if explicacion:
                frame_expl = ctk.CTkFrame(item, fg_color=PALETA["entrada"], corner_radius=6, border_width=1, border_color=PALETA["borde"])
                frame_expl.pack(fill="x", padx=14, pady=(2, 8))

                ctk.CTkLabel(
                    frame_expl,
                    text="Explicación:",
                    font=("Segoe UI", 11, "bold"),
                    text_color=PALETA["primario"],
                ).pack(anchor="w", padx=10, pady=(6, 2))

                ctk.CTkLabel(
                    frame_expl,
                    text=explicacion,
                    font=FUENTE_NORMAL,
                    text_color=PALETA["texto_2"],
                    wraplength=540,
                    justify="left",
                ).pack(anchor="w", padx=10, pady=(0, 8))

            frame_matriz = ctk.CTkFrame(item, fg_color="transparent")
            frame_matriz.pack(fill="x", padx=14, pady=(0, 10))

            etiqueta_mat = "Matriz inicial:" if es_inicial else "Matriz resultante:"
            ctk.CTkLabel(
                frame_matriz,
                text=etiqueta_mat,
                font=FUENTE_PEQUENA,
                text_color=PALETA["texto_3"],
            ).pack(anchor="w", pady=(0, 2))

            ctk.CTkLabel(
                frame_matriz,
                text=matriz_a_texto(matriz),
                font=FUENTE_MONO,
                text_color=PALETA["texto_2"],
                justify="left",
            ).pack(anchor="w")


class ResultPanel(ctk.CTkFrame):
    """Presenta clasificacion, variables, solucion y verificacion explicativa detallada."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent", corner_radius=0, border_width=0)

        self.canvas_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.canvas_frame.pack(fill="both", expand=True, padx=4, pady=4)

        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg=resolver_color(PALETA["panel"]),
            highlightthickness=0,
            bd=0,
        )
        self.scroll_y = ctk.CTkScrollbar(
            self.canvas_frame, orientation="vertical", command=self.canvas.yview,
            button_color=PALETA["primario"], button_hover_color=PALETA["primario_hover"],
        )
        self.scroll_x = ctk.CTkScrollbar(
            self.canvas_frame, orientation="horizontal", command=self.canvas.xview,
            button_color=PALETA["primario"], button_hover_color=PALETA["primario_hover"],
        )
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns", padx=(4, 0))
        self.scroll_x.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        self.grid_host = ctk.CTkFrame(self.canvas, fg_color="transparent")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.grid_host, anchor="nw")

        self.grid_host.bind("<Configure>", self._actualizar_scroll)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        self.mostrar_placeholder()

    def _on_mousewheel(self, event):
        if event.state & 0x0001:
            self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _actualizar_scroll(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        width = max(event.width, self.grid_host.winfo_reqwidth())
        self.canvas.itemconfig(self.canvas_window, width=width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def limpiar(self):
        for widget in self.grid_host.winfo_children():
            widget.destroy()

    def mostrar_placeholder(self):
        self.limpiar()
        ctk.CTkLabel(
            self.grid_host,
            text="Aqui se mostraran la clasificacion, la solucion y la verificacion explicativa paso a paso.",
            font=FUENTE_NORMAL,
            text_color=PALETA["texto_3"],
            wraplength=480,
            justify="left",
        ).pack(anchor="w", padx=14, pady=14)

    def _estado_color(self, clasificacion):
        if "inconsistente" in clasificacion.lower():
            return PALETA["error"]
        if "indeterminado" in clasificacion.lower():
            return PALETA["advertencia"]
        return PALETA["exito"]

    def mostrar_resultado(self, resultado):
        self.limpiar()
        color = self._estado_color(resultado["clasificacion"])
        nombres_vars = resultado.get("nombres_variables", obtener_nombres_variables(len(resultado["matriz_inicial"][0]) - 1))

        # 1. Estado y clasificacion
        estado = ctk.CTkFrame(self.grid_host, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        estado.pack(fill="x", expand=True, pady=(0, 12), padx=2)
        ctk.CTkFrame(estado, fg_color=color, width=5, corner_radius=8).pack(side="left", fill="y")
        texto_estado = ctk.CTkFrame(estado, fg_color="transparent")
        texto_estado.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(texto_estado, text="Clasificación del sistema", font=FUENTE_PEQUENA, text_color=PALETA["texto_3"]).pack(anchor="w")
        ctk.CTkLabel(texto_estado, text=resultado["clasificacion"], font=("Segoe UI", 15, "bold"), text_color=PALETA["texto"]).pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(texto_estado, text=resultado["descripcion"], font=FUENTE_PEQUENA, text_color=PALETA["texto_2"]).pack(anchor="w")

        # 2. Informacion de variables y homogeneidad
        tarjeta_vars = ctk.CTkFrame(self.grid_host, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        tarjeta_vars.pack(fill="x", expand=True, pady=(0, 12), padx=2)

        etiqueta_homogeneo = "Sistema homogéneo (Ax = 0)" if resultado["homogeneo"] else "Sistema no homogéneo"
        ctk.CTkLabel(
            tarjeta_vars,
            text=etiqueta_homogeneo,
            font=("Segoe UI", 12, "bold"),
            text_color=PALETA["primario"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        basicas = ", ".join(nombres_vars[c] for c in resultado["variables_basicas"]) or "ninguna"
        libres = ", ".join(nombres_vars[c] for c in resultado["variables_libres"]) or "ninguna"
        ctk.CTkLabel(tarjeta_vars, text=f"Variables básicas: {basicas}", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(tarjeta_vars, text=f"Variables libres: {libres}", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=(2, 12))

        # 3. Interpretación vectorial (Ax = b como combinacion lineal de columnas)
        mat_ini = resultado.get("matriz_inicial")
        if mat_ini and len(mat_ini) > 0 and len(mat_ini[0]) > 1:
            self._mostrar_interpretacion_vectorial(mat_ini, nombres_vars)

        # 4. Solucion
        if resultado["solucion"] is not None:
            self._mostrar_solucion_unica(resultado["solucion"], nombres_vars)

        if resultado["expresiones"] is not None:
            self._mostrar_solucion_parametrica(
                resultado["expresiones"],
                nombres_vars,
                resultado.get("solucion_particular"),
            )

        # 5. Verificacion explicativa
        if resultado["verificacion"] is not None:
            es_param = (resultado["clasificacion"] == "Sistema consistente indeterminado")
            self._mostrar_verificacion(resultado["verificacion"], es_parametrico=es_param)
        else:
            self._mostrar_verificacion_inconsistente()

    def _mostrar_interpretacion_vectorial(self, matriz_aumentada, nombres_vars):
        """Muestra la ecuacion Ax = b interpretada como combinacion lineal de las columnas de A."""
        tarjeta = ctk.CTkFrame(self.grid_host, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        tarjeta.pack(fill="x", expand=True, pady=(0, 12), padx=2)
        ctk.CTkLabel(tarjeta, text="Interpretación como Combinación Lineal (Ax = b)", font=("Segoe UI", 14, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 4))

        m = len(matriz_aumentada)
        n = len(matriz_aumentada[0]) - 1
        terminos = []
        for j in range(n):
            col_v = [matriz_aumentada[i][j] for i in range(m)]
            terminos.append(f"{nombres_vars[j]} * {formatear_vector(col_v)}")
        b_vec = [matriz_aumentada[i][-1] for i in range(m)]
        expresion = " + ".join(terminos) + f" = {formatear_vector(b_vec)}"

        ctk.CTkLabel(
            tarjeta,
            text="La ecuación matricial Ax = b equivale a la combinación lineal de las columnas de A ponderadas por las variables del vector x:",
            font=FUENTE_PEQUENA,
            text_color=PALETA["texto_3"],
            wraplength=620,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 6))

        ctk.CTkLabel(
            tarjeta,
            text=expresion,
            font=FUENTE_MONO,
            text_color=PALETA["texto_2"],
            wraplength=620,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 12))

    def _mostrar_solucion_unica(self, solucion, nombres_vars):
        tarjeta = ctk.CTkFrame(self.grid_host, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        tarjeta.pack(fill="x", expand=True, pady=(0, 12), padx=2)
        ctk.CTkLabel(tarjeta, text="Solución encontrada", font=("Segoe UI", 15, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 6))
        for i, valor in enumerate(solucion):
            var_nombre = nombres_vars[i]
            ctk.CTkLabel(tarjeta, text=f"{var_nombre} = {formatear_numero(valor)}", font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(tarjeta, text="").pack(pady=2)

    def _mostrar_solucion_parametrica(self, expresiones, nombres_vars, solucion_particular=None):
        tarjeta = ctk.CTkFrame(self.grid_host, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        tarjeta.pack(fill="x", expand=True, pady=(0, 12), padx=2)
        ctk.CTkLabel(tarjeta, text="Solución paramétrica (infinitas soluciones)", font=("Segoe UI", 15, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 6))
        for i in range(len(expresiones)):
            var_nombre = nombres_vars[i]
            ctk.CTkLabel(tarjeta, text=f"{var_nombre} = {expresiones[i]}", font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)

        if solucion_particular is not None:
            ctk.CTkLabel(tarjeta, text="Solución particular evaluada (parámetro(s) = 0):", font=("Segoe UI", 11, "bold"), text_color=PALETA["texto_3"]).pack(anchor="w", padx=16, pady=(10, 2))
            part_str = ",  ".join(f"{nombres_vars[i]} = {formatear_numero(solucion_particular[i])}" for i in range(len(solucion_particular)))
            ctk.CTkLabel(tarjeta, text=part_str, font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=(0, 6))
        ctk.CTkLabel(tarjeta, text="").pack(pady=2)

    def _mostrar_verificacion(self, verificacion, es_parametrico=False):
        correcta, detalles = verificacion

        tarjeta_principal = ctk.CTkFrame(self.grid_host, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        tarjeta_principal.pack(fill="x", expand=True, pady=(0, 14), padx=2)

        header_frame = ctk.CTkFrame(tarjeta_principal, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            header_frame,
            text="VERIFICACIÓN DE LA SOLUCIÓN",
            font=("Segoe UI", 15, "bold"),
            text_color=PALETA["primario"],
        ).pack(side="left")

        subtitulo = (
            "Sustitución y comprobación con la solución particular en cada ecuación original:"
            if es_parametrico
            else "Sustitución de los valores encontrados en cada ecuación del sistema original:"
        )
        ctk.CTkLabel(
            tarjeta_principal,
            text=subtitulo,
            font=FUENTE_PEQUENA,
            text_color=PALETA["texto_3"],
            wraplength=600,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 10))

        for detalle in detalles:
            item = ctk.CTkFrame(tarjeta_principal, fg_color=PALETA["entrada"], corner_radius=8, border_width=1, border_color=PALETA["borde"])
            item.pack(fill="x", expand=True, padx=14, pady=(0, 12))

            cabecera = ctk.CTkFrame(item, fg_color="transparent")
            cabecera.pack(fill="x", padx=12, pady=(10, 6))

            ctk.CTkLabel(
                cabecera,
                text=f"Ecuación {detalle.indice}",
                font=("Segoe UI", 12, "bold"),
                text_color="#04191A",
                fg_color=PALETA["primario"],
                corner_radius=6,
                padx=8,
                pady=2,
            ).pack(side="left", padx=(0, 10))

            color_estado = PALETA["exito"] if detalle.coincide else PALETA["error"]
            texto_estado = "✓ Ecuación verificada correctamente" if detalle.coincide else "✗ La igualdad no se cumple"
            ctk.CTkLabel(
                cabecera,
                text=texto_estado,
                font=("Segoe UI", 12, "bold"),
                text_color=color_estado,
            ).pack(side="left")

            cuerpo = ctk.CTkFrame(item, fg_color="transparent")
            cuerpo.pack(fill="x", padx=14, pady=(2, 10))

            # 1. Ecuacion original
            ctk.CTkLabel(cuerpo, text="Ecuación original:", font=("Segoe UI", 11, "bold"), text_color=PALETA["texto_3"]).pack(anchor="w", pady=(2, 0))
            ctk.CTkLabel(cuerpo, text=detalle.ecuacion_original, font=FUENTE_MONO, text_color=PALETA["texto"]).pack(anchor="w", padx=10, pady=(1, 4))

            # 2. Sustitucion
            ctk.CTkLabel(cuerpo, text="Sustitución:", font=("Segoe UI", 11, "bold"), text_color=PALETA["texto_3"]).pack(anchor="w", pady=(2, 0))
            ctk.CTkLabel(cuerpo, text=detalle.sustitucion, font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=10, pady=(1, 4))

            # 3. Simplificacion
            ctk.CTkLabel(cuerpo, text="Simplificación:", font=("Segoe UI", 11, "bold"), text_color=PALETA["texto_3"]).pack(anchor="w", pady=(2, 0))
            for linea_s in detalle.simplificacion:
                ctk.CTkLabel(cuerpo, text=linea_s, font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=10, pady=1)

        # Resultado final
        color_final = PALETA["exito"] if correcta else PALETA["error"]
        tarjeta_final = ctk.CTkFrame(tarjeta_principal, fg_color=PALETA["panel_2"], corner_radius=8, border_width=2, border_color=color_final)
        tarjeta_final.pack(fill="x", expand=True, padx=14, pady=(0, 14))

        if correcta:
            ctk.CTkLabel(
                tarjeta_final,
                text="✓ RESULTADO FINAL: Todas las ecuaciones fueron verificadas correctamente.",
                font=("Segoe UI", 13, "bold"),
                text_color=PALETA["exito"],
            ).pack(anchor="w", padx=14, pady=(10, 2))
            ctk.CTkLabel(
                tarjeta_final,
                text="La solución encontrada satisface todas las ecuaciones del sistema original.",
                font=FUENTE_NORMAL,
                text_color=PALETA["texto_2"],
            ).pack(anchor="w", padx=14, pady=(0, 10))
        else:
            ctk.CTkLabel(
                tarjeta_final,
                text="✗ RESULTADO FINAL: La solución no satisface el sistema original.",
                font=("Segoe UI", 13, "bold"),
                text_color=PALETA["error"],
            ).pack(anchor="w", padx=14, pady=(10, 2))
            ctk.CTkLabel(
                tarjeta_final,
                text="Una o más ecuaciones no cumplen la igualdad tras sustituir los valores.",
                font=FUENTE_NORMAL,
                text_color=PALETA["texto_2"],
            ).pack(anchor="w", padx=14, pady=(0, 10))

    def _mostrar_verificacion_inconsistente(self):
        tarjeta = ctk.CTkFrame(self.grid_host, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["error"])
        tarjeta.pack(fill="x", expand=True, pady=(0, 14), padx=2)

        ctk.CTkLabel(
            tarjeta,
            text="VERIFICACIÓN NO APLICABLE",
            font=("Segoe UI", 15, "bold"),
            text_color=PALETA["error"],
        ).pack(anchor="w", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            tarjeta,
            text="El sistema es inconsistente y no tiene solución.",
            font=("Segoe UI", 13, "bold"),
            text_color=PALETA["texto"],
        ).pack(anchor="w", padx=16, pady=(2, 4))

        ctk.CTkLabel(
            tarjeta,
            text="Por definición matemática, no existe ningún conjunto de valores para las variables que satisfaga simultáneamente las ecuaciones del sistema.",
            font=FUENTE_NORMAL,
            text_color=PALETA["texto_2"],
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 14))


# -----------------------------------------------------------------------------
# Ventana principal
# -----------------------------------------------------------------------------

class AplicacionAlgebraLineal(ctk.CTk):
    """Aplicacion de escritorio moderna hecha con CustomTkinter."""

    def __init__(self):
        super().__init__()
        self.title("Calculadora de Algebra Lineal - Grupo 3 - UAM")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(fg_color=PALETA["fondo"])

        self.logo_grande = cargar_logo((56, 56))
        self.logo_pequeno = cargar_logo((34, 34))
        self._configurar_icono_ventana()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.crear_sidebar()
        self.crear_contenido_principal()
        self.crear_sistema()

    def _configurar_icono_ventana(self):
        """Usa el logo de la UAM como icono de la ventana (si esta disponible)."""
        if Image is None or not os.path.exists(RUTA_LOGO):
            return
        try:
            self._icono_tk = tk.PhotoImage(file=RUTA_LOGO)
            self.iconphoto(True, self._icono_tk)
        except Exception:
            pass

    def crear_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=PALETA["sidebar"], corner_radius=0, width=240)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        marca = ctk.CTkFrame(sidebar, fg_color="transparent")
        marca.pack(fill="x", padx=24, pady=(28, 8))

        fila_marca = ctk.CTkFrame(marca, fg_color="transparent")
        fila_marca.pack(anchor="w")

        if self.logo_grande is not None:
            self._label_logo_grande = ctk.CTkLabel(fila_marca, image=self.logo_grande, text="")
            self._label_logo_grande.pack(side="left", padx=(0, 12))

        texto_marca = ctk.CTkFrame(fila_marca, fg_color="transparent")
        texto_marca.pack(side="left")
        ctk.CTkLabel(texto_marca, text="Algebra\nLineal", font=("Segoe UI", 19, "bold"), justify="left", text_color=PALETA["texto"]).pack(anchor="w")

        ctk.CTkLabel(marca, text="Universidad Americana \u2022 Grupo 3", font=FUENTE_PEQUENA, text_color=PALETA["texto_3"]).pack(anchor="w", pady=(10, 0))

        ctk.CTkFrame(sidebar, height=1, fg_color=PALETA["borde"]).pack(fill="x", padx=24, pady=18)

        self.nav_botones = {}
        self.nav_botones["ax_b"] = self._nav_item(sidebar, "Ecuación Matricial (Ax=b)", "ax_b", activo=True)
        self.nav_botones["vectores"] = self._nav_item(sidebar, "Vectores en R^n", "vectores")
        self.nav_botones["combinacion"] = self._nav_item(sidebar, "Combinación Lineal", "combinacion")
        self.nav_botones["independencia"] = self._nav_item(sidebar, "Independencia Lineal", "independencia")
        self.nav_botones["matrices"] = self._nav_item(sidebar, "Operaciones con Matrices", "matrices")
        self.nav_botones["metodo"] = self._nav_item(sidebar, "Método de Eliminación", "metodo")
        self.nav_botones["ayuda"] = self._nav_item(sidebar, "Ayuda", "ayuda")

        ctk.CTkFrame(sidebar, fg_color="transparent").pack(fill="both", expand=True)

        pie = ctk.CTkFrame(sidebar, fg_color="transparent")
        pie.pack(fill="x", padx=24, pady=(0, 20))
        if self.logo_pequeno is not None:
            self._label_logo_pequeno = ctk.CTkLabel(pie, image=self.logo_pequeno, text="")
            self._label_logo_pequeno.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(pie, text="Excellentia\nAcademica", font=("Segoe UI", 10), text_color=PALETA["texto_3"], justify="left").pack(side="left")

    def _nav_item(self, parent, texto, pagina, activo=False):
        color = PALETA["primario"] if activo else "transparent"
        texto_color = "#04191A" if activo else PALETA["texto"]
        item = ctk.CTkButton(
            parent,
            text=texto,
            anchor="w",
            height=38,
            corner_radius=8,
            fg_color=color,
            hover_color=PALETA["secundario_hover"],
            text_color=texto_color,
            command=lambda: self.cambiar_pagina(pagina),
        )
        item.pack(fill="x", padx=16, pady=4)
        return item

    def cambiar_pagina(self, pagina):
        if pagina == "calculadora":
            pagina = "ax_b"
        for nombre, boton in self.nav_botones.items():
            if nombre == pagina:
                boton.configure(fg_color=PALETA["primario"], text_color="#04191A")
            else:
                boton.configure(fg_color="transparent", text_color=PALETA["texto"])
        if pagina in self.paginas:
            self.paginas[pagina].tkraise()

    def crear_contenido_principal(self):
        contenedor = ctk.CTkFrame(self, fg_color=PALETA["fondo"], corner_radius=0)
        contenedor.grid(row=0, column=1, sticky="nsew")
        contenedor.grid_columnconfigure(0, weight=1)
        contenedor.grid_rowconfigure(0, weight=1)

        self.paginas = {
            "ax_b": self._crear_pagina_calculadora(contenedor),
            "vectores": self._crear_pagina_vectores(contenedor),
            "combinacion": self._crear_pagina_combinacion(contenedor),
            "independencia": self._crear_pagina_independencia(contenedor),
            "matrices": self._crear_pagina_matrices(contenedor),
            "metodo": self._crear_pagina_metodo(contenedor),
            "ayuda": self._crear_pagina_ayuda(contenedor),
        }
        self.paginas["calculadora"] = self.paginas["ax_b"]
        for pagina in self.paginas.values():
            pagina.grid(row=0, column=0, sticky="nsew")

        self.paginas["ax_b"].tkraise()

    def _crear_encabezado(self, parent, titulo, subtitulo):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text=titulo, font=FUENTE_TITULO, text_color=PALETA["texto"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text=subtitulo,
            font=FUENTE_SUBTITULO,
            text_color=PALETA["texto_2"],
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    def _crear_pagina_calculadora(self, parent):
        pagina = ctk.CTkFrame(parent, fg_color=PALETA["fondo"], corner_radius=0)
        pagina.grid_columnconfigure(0, weight=1)
        pagina.grid_rowconfigure(1, weight=1)

        self._crear_encabezado(
            pagina,
            "Calculadora de Algebra Lineal",
            "Solucion de sistemas de ecuaciones lineales por eliminacion por filas",
        )

        contenido = ctk.CTkFrame(pagina, fg_color="transparent")
        contenido.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        contenido.grid_columnconfigure(0, weight=2)
        contenido.grid_columnconfigure(1, weight=3)
        contenido.grid_rowconfigure(1, weight=1)

        self.config_panel = crear_tarjeta(contenido, "Configuracion del sistema")
        self.config_panel.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        self.crear_configuracion(self.config_panel)

        self.matrix_panel = MatrixInputPanel(contenido, self.resolver_desde_interfaz, self.limpiar_matriz)
        self.matrix_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 14))

        derecha = ctk.CTkFrame(contenido, fg_color="transparent")
        derecha.grid(row=1, column=1, sticky="nsew")
        derecha.grid_columnconfigure(0, weight=1)
        derecha.grid_rowconfigure(0, weight=1)

        self.tab_derecha = ctk.CTkTabview(
            derecha,
            fg_color=PALETA["panel"],
            corner_radius=12,
            border_width=1,
            border_color=PALETA["borde"],
            segmented_button_fg_color=PALETA["panel_2"],
            segmented_button_selected_color=PALETA["primario"],
            segmented_button_selected_hover_color=PALETA["primario_hover"],
            segmented_button_unselected_color=PALETA["panel_2"],
            segmented_button_unselected_hover_color=PALETA["secundario_hover"],
            text_color=PALETA["texto"],
        )
        self.tab_derecha.grid(row=0, column=0, sticky="nsew")

        tab_proc = self.tab_derecha.add("Procedimiento Paso a Paso")
        tab_res = self.tab_derecha.add("Resultado y Verificación")

        self.process_panel = ProcessPanel(tab_proc)
        self.process_panel.pack(fill="both", expand=True)

        self.result_panel = ResultPanel(tab_res)
        self.result_panel.pack(fill="both", expand=True)

        return pagina

    # -------------------------------------------------------------------------
    # Pagina: Vectores en R^n (Tarea 3)
    # -------------------------------------------------------------------------

    def _crear_pagina_vectores(self, parent):
        pagina = ctk.CTkFrame(parent, fg_color=PALETA["fondo"], corner_radius=0)
        pagina.grid_columnconfigure(0, weight=1)
        pagina.grid_rowconfigure(1, weight=1)

        self._crear_encabezado(
            pagina,
            "Operaciones con Vectores en R^n",
            "Suma, resta y multiplicación por un escalar con procedimiento componente a componente",
        )

        contenido = ctk.CTkFrame(pagina, fg_color="transparent")
        contenido.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        contenido.grid_columnconfigure(0, weight=2)
        contenido.grid_columnconfigure(1, weight=3)
        contenido.grid_rowconfigure(1, weight=1)

        # Columna izquierda
        izq = ctk.CTkFrame(contenido, fg_color="transparent")
        izq.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 14))

        # Configuracion
        cfg = crear_tarjeta(izq, "Configuración de dimensión")
        cfg.pack(fill="x", pady=(0, 12))
        fila_cfg = ctk.CTkFrame(cfg, fg_color="transparent")
        fila_cfg.pack(fill="x", padx=18, pady=(0, 14))

        ctk.CTkLabel(fila_cfg, text="Dimensión n (R^n):", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(side="left", padx=(0, 8))
        self.entrada_dim_vec = ctk.CTkEntry(fila_cfg, width=65, height=36, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
        self.entrada_dim_vec.insert(0, "3")
        self.entrada_dim_vec.pack(side="left", padx=(0, 14))

        ctk.CTkButton(
            fila_cfg,
            text="Configurar",
            width=100,
            height=36,
            corner_radius=8,
            fg_color=PALETA["primario"],
            hover_color=PALETA["primario_hover"],
            text_color="#04191A",
            font=("Segoe UI", 12, "bold"),
            command=self._generar_entradas_vectores,
        ).pack(side="left")

        # Tarjeta de entradas con scroll 2D
        tarjeta_entradas = crear_tarjeta(izq, "Vectores u, v y Escalar k")
        tarjeta_entradas.pack(fill="both", expand=True, pady=(0, 12))

        self.canvas_vec_frame = ctk.CTkFrame(tarjeta_entradas, fg_color=PALETA["panel_2"], corner_radius=10)
        self.canvas_vec_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.canvas_vec = tk.Canvas(self.canvas_vec_frame, bg=resolver_color(PALETA["panel_2"]), highlightthickness=0, height=210)
        self.scroll_y_vec = ctk.CTkScrollbar(self.canvas_vec_frame, orientation="vertical", command=self.canvas_vec.yview, button_color=PALETA["primario"])
        self.scroll_x_vec = ctk.CTkScrollbar(self.canvas_vec_frame, orientation="horizontal", command=self.canvas_vec.xview, button_color=PALETA["primario"])
        self.canvas_vec.configure(yscrollcommand=self.scroll_y_vec.set, xscrollcommand=self.scroll_x_vec.set)

        self.canvas_vec.grid(row=0, column=0, sticky="nsew", padx=(10, 4), pady=(10, 4))
        self.scroll_y_vec.grid(row=0, column=1, sticky="ns", pady=(10, 4), padx=(0, 6))
        self.scroll_x_vec.grid(row=1, column=0, sticky="ew", padx=(10, 4), pady=(0, 6))
        self.canvas_vec_frame.grid_rowconfigure(0, weight=1)
        self.canvas_vec_frame.grid_columnconfigure(0, weight=1)

        self.grid_host_vec = ctk.CTkFrame(self.canvas_vec, fg_color="transparent")
        self.canvas_vec_window = self.canvas_vec.create_window((0, 0), window=self.grid_host_vec, anchor="nw")
        self.grid_host_vec.bind("<Configure>", lambda e: self.canvas_vec.configure(scrollregion=self.canvas_vec.bbox("all")))

        # Escalar k
        frame_esc = ctk.CTkFrame(tarjeta_entradas, fg_color="transparent")
        frame_esc.pack(fill="x", padx=14, pady=(0, 8))
        ctk.CTkLabel(frame_esc, text="Escalar k:", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(side="left", padx=(0, 8))
        self.entrada_escalar_k = ctk.CTkEntry(frame_esc, width=75, height=34, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
        self.entrada_escalar_k.insert(0, "2")
        self.entrada_escalar_k.pack(side="left")

        # Selector de operacion a resolver
        frame_sel_op = ctk.CTkFrame(tarjeta_entradas, fg_color="transparent")
        frame_sel_op.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkLabel(frame_sel_op, text="Operación:", font=("Segoe UI", 12, "bold"), text_color=PALETA["primario"]).pack(side="left", padx=(0, 8))
        self.seg_op_vec = ctk.CTkSegmentedButton(
            frame_sel_op,
            values=["u + v", "u - v", "v - u", "k · u", "k · v"],
            selected_color=PALETA["primario"],
            selected_hover_color=PALETA["primario_hover"],
        )
        self.seg_op_vec.set("u + v")
        self.seg_op_vec.pack(side="left", fill="x", expand=True)

        # Botones de accion con boton Resolver destacado
        frame_ops = ctk.CTkFrame(tarjeta_entradas, fg_color="transparent")
        frame_ops.pack(fill="x", padx=14, pady=(0, 14))

        ctk.CTkButton(
            frame_ops,
            text="Resolver operación",
            height=40,
            corner_radius=8,
            fg_color=PALETA["primario"],
            hover_color=PALETA["primario_hover"],
            text_color="#04191A",
            font=("Segoe UI", 13, "bold"),
            command=self._resolver_operacion_vector,
        ).pack(side="left")

        ctk.CTkButton(
            frame_ops,
            text="Limpiar",
            height=40,
            corner_radius=8,
            fg_color=PALETA["secundario"],
            hover_color=PALETA["secundario_hover"],
            command=self._limpiar_vectores,
        ).pack(side="left", padx=10)

        # Columna derecha (Resultados)
        self.tarjeta_res_vec = ctk.CTkScrollableFrame(contenido, fg_color=PALETA["panel"], corner_radius=12, border_width=1, border_color=PALETA["borde"])
        self.tarjeta_res_vec.grid(row=0, column=1, rowspan=2, sticky="nsew")
        self._mostrar_placeholder_vectores()

        self._generar_entradas_vectores()
        return pagina

    def _resolver_operacion_vector(self):
        op_map = {
            "u + v": "suma",
            "u - v": "resta_uv",
            "v - u": "resta_vu",
            "k · u": "escalar_u",
            "k · v": "escalar_v",
        }
        op = self.seg_op_vec.get()
        self._operar_vectores(op_map.get(op, "suma"))

    def _generar_entradas_vectores(self):
        try:
            n = int(self.entrada_dim_vec.get())
            if n <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "La dimensión n debe ser un entero positivo.")
            return

        for w in self.grid_host_vec.winfo_children():
            w.destroy()

        self.entradas_u = []
        self.entradas_v = []

        ctk.CTkLabel(self.grid_host_vec, text="Vector u:", font=("Segoe UI", 12, "bold"), text_color=PALETA["primario"]).grid(row=0, column=0, padx=6, pady=4, sticky="w")
        for j in range(n):
            ctk.CTkLabel(self.grid_host_vec, text=f"u{j + 1}", font=("Segoe UI", 11), text_color=PALETA["texto_3"]).grid(row=1, column=j + 1, padx=3, pady=(2, 0))
            e = ctk.CTkEntry(self.grid_host_vec, width=62, height=32, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
            e.insert(0, "0")
            e.grid(row=2, column=j + 1, padx=3, pady=(0, 8))
            self.entradas_u.append(e)

        ctk.CTkLabel(self.grid_host_vec, text="Vector v:", font=("Segoe UI", 12, "bold"), text_color=PALETA["primario"]).grid(row=3, column=0, padx=6, pady=4, sticky="w")
        for j in range(n):
            ctk.CTkLabel(self.grid_host_vec, text=f"v{j + 1}", font=("Segoe UI", 11), text_color=PALETA["texto_3"]).grid(row=4, column=j + 1, padx=3, pady=(2, 0))
            e = ctk.CTkEntry(self.grid_host_vec, width=62, height=32, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
            e.insert(0, "0")
            e.grid(row=5, column=j + 1, padx=3, pady=(0, 6))
            self.entradas_v.append(e)

        self.canvas_vec.configure(scrollregion=self.canvas_vec.bbox("all"))

    def _limpiar_vectores(self):
        for e in self.entradas_u + self.entradas_v:
            e.delete(0, "end")
            e.insert(0, "0")
        self.entrada_escalar_k.delete(0, "end")
        self.entrada_escalar_k.insert(0, "1")
        self._mostrar_placeholder_vectores()

    def _mostrar_placeholder_vectores(self):
        for w in self.tarjeta_res_vec.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.tarjeta_res_vec,
            text="Selecciona una operación (u + v, u - v, k·u, etc.) para ver el procedimiento paso a paso y el vector resultante.",
            font=FUENTE_NORMAL,
            text_color=PALETA["texto_3"],
            wraplength=520,
            justify="left",
        ).pack(anchor="w", padx=16, pady=16)

    def _operar_vectores(self, tipo_op):
        try:
            u = [convertir_numero(e.get()) for e in self.entradas_u]
            v = [convertir_numero(e.get()) for e in self.entradas_v]
            k_val = convertir_numero(self.entrada_escalar_k.get())
        except Exception as error:
            messagebox.showerror("Error en datos de entrada", str(error))
            return

        for w in self.tarjeta_res_vec.winfo_children():
            w.destroy()

        n = len(u)
        lineas_proc = []
        if tipo_op == "suma":
            titulo = "Suma de vectores: u + v"
            res = sumar_vectores(u, v)
            for i in range(n):
                lineas_proc.append(f"Componente {i + 1}: u{i + 1} + v{i + 1} = ({formatear_numero(u[i])}) + ({formatear_numero(v[i])}) = {formatear_numero(res[i])}")
        elif tipo_op == "resta_uv":
            titulo = "Resta de vectores: u - v"
            res = restar_vectores(u, v)
            for i in range(n):
                lineas_proc.append(f"Componente {i + 1}: u{i + 1} - v{i + 1} = ({formatear_numero(u[i])}) - ({formatear_numero(v[i])}) = {formatear_numero(res[i])}")
        elif tipo_op == "resta_vu":
            titulo = "Resta de vectores: v - u"
            res = restar_vectores(v, u)
            for i in range(n):
                lineas_proc.append(f"Componente {i + 1}: v{i + 1} - u{i + 1} = ({formatear_numero(v[i])}) - ({formatear_numero(u[i])}) = {formatear_numero(res[i])}")
        elif tipo_op == "escalar_u":
            titulo = f"Multiplicación por escalar: {formatear_numero(k_val)} · u"
            res = multiplicar_vector_escalar(k_val, u)
            for i in range(n):
                lineas_proc.append(f"Componente {i + 1}: k · u{i + 1} = ({formatear_numero(k_val)}) · ({formatear_numero(u[i])}) = {formatear_numero(res[i])}")
        elif tipo_op == "escalar_v":
            titulo = f"Multiplicación por escalar: {formatear_numero(k_val)} · v"
            res = multiplicar_vector_escalar(k_val, v)
            for i in range(n):
                lineas_proc.append(f"Componente {i + 1}: k · v{i + 1} = ({formatear_numero(k_val)}) · ({formatear_numero(v[i])}) = {formatear_numero(res[i])}")

        # Tarjeta 1: Operacion
        t_op = ctk.CTkFrame(self.tarjeta_res_vec, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        t_op.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(t_op, text=titulo, font=("Segoe UI", 15, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(t_op, text=f"Vector u = {formatear_vector(u)}", font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(t_op, text=f"Vector v = {formatear_vector(v)}", font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(t_op, text=f"Escalar k = {formatear_numero(k_val)}", font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=(2, 12))

        # Tarjeta 2: Procedimiento paso a paso
        t_proc = ctk.CTkFrame(self.tarjeta_res_vec, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        t_proc.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(t_proc, text="Procedimiento componente a componente:", font=("Segoe UI", 14, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 6))
        for linea in lineas_proc:
            ctk.CTkLabel(t_proc, text=linea, font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(t_proc, text="").pack(pady=2)

        # Tarjeta 3: Resultado final
        t_res = ctk.CTkFrame(self.tarjeta_res_vec, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["exito"])
        t_res.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(t_res, text="Vector resultante:", font=("Segoe UI", 14, "bold"), text_color=PALETA["exito"]).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(t_res, text=f"Resultado = {formatear_vector(res)}", font=("Consolas", 16, "bold"), text_color=PALETA["texto"]).pack(anchor="w", padx=16, pady=(2, 12))

    # -------------------------------------------------------------------------
    # Pagina: Combinacion Lineal y Ecuacion Vectorial (Tarea 3)
    # -------------------------------------------------------------------------

    def _crear_pagina_combinacion(self, parent):
        pagina = ctk.CTkFrame(parent, fg_color=PALETA["fondo"], corner_radius=0)
        pagina.grid_columnconfigure(0, weight=1)
        pagina.grid_rowconfigure(1, weight=1)

        self._crear_encabezado(
            pagina,
            "Combinación Lineal y Ecuación Vectorial",
            "Determina si b = c1·v1 + c2·v2 + ... + ck·vk mediante eliminación de Gauss-Jordan",
        )

        contenido = ctk.CTkFrame(pagina, fg_color="transparent")
        contenido.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        contenido.grid_columnconfigure(0, weight=2)
        contenido.grid_columnconfigure(1, weight=3)
        contenido.grid_rowconfigure(1, weight=1)

        izq = ctk.CTkFrame(contenido, fg_color="transparent")
        izq.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 14))

        cfg = crear_tarjeta(izq, "Configuración del conjunto")
        cfg.pack(fill="x", pady=(0, 12))
        fila_cfg = ctk.CTkFrame(cfg, fg_color="transparent")
        fila_cfg.pack(fill="x", padx=18, pady=(0, 14))

        ctk.CTkLabel(fila_cfg, text="Dimensión n:", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(side="left", padx=(0, 6))
        self.entrada_dim_comb = ctk.CTkEntry(fila_cfg, width=58, height=36, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
        self.entrada_dim_comb.insert(0, "3")
        self.entrada_dim_comb.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(fila_cfg, text="Vectores k:", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(side="left", padx=(0, 6))
        self.entrada_k_comb = ctk.CTkEntry(fila_cfg, width=58, height=36, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
        self.entrada_k_comb.insert(0, "3")
        self.entrada_k_comb.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            fila_cfg,
            text="Generar",
            width=90,
            height=36,
            corner_radius=8,
            fg_color=PALETA["primario"],
            hover_color=PALETA["primario_hover"],
            text_color="#04191A",
            font=("Segoe UI", 12, "bold"),
            command=self._generar_entradas_combinacion,
        ).pack(side="left")

        tarjeta_mat = crear_tarjeta(izq, "Vectores [ v1  v2 ... vk | b ]")
        tarjeta_mat.pack(fill="both", expand=True, pady=(0, 12))

        self.canvas_comb_frame = ctk.CTkFrame(tarjeta_mat, fg_color=PALETA["panel_2"], corner_radius=10)
        self.canvas_comb_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.canvas_comb = tk.Canvas(self.canvas_comb_frame, bg=resolver_color(PALETA["panel_2"]), highlightthickness=0, height=210)
        self.scroll_y_comb = ctk.CTkScrollbar(self.canvas_comb_frame, orientation="vertical", command=self.canvas_comb.yview, button_color=PALETA["primario"])
        self.scroll_x_comb = ctk.CTkScrollbar(self.canvas_comb_frame, orientation="horizontal", command=self.canvas_comb.xview, button_color=PALETA["primario"])
        self.canvas_comb.configure(yscrollcommand=self.scroll_y_comb.set, xscrollcommand=self.scroll_x_comb.set)

        self.canvas_comb.grid(row=0, column=0, sticky="nsew", padx=(10, 4), pady=(10, 4))
        self.scroll_y_comb.grid(row=0, column=1, sticky="ns", pady=(10, 4), padx=(0, 6))
        self.scroll_x_comb.grid(row=1, column=0, sticky="ew", padx=(10, 4), pady=(0, 6))
        self.canvas_comb_frame.grid_rowconfigure(0, weight=1)
        self.canvas_comb_frame.grid_columnconfigure(0, weight=1)

        self.grid_host_comb = ctk.CTkFrame(self.canvas_comb, fg_color="transparent")
        self.canvas_comb_window = self.canvas_comb.create_window((0, 0), window=self.grid_host_comb, anchor="nw")
        self.grid_host_comb.bind("<Configure>", lambda e: self.canvas_comb.configure(scrollregion=self.canvas_comb.bbox("all")))

        acciones_comb = ctk.CTkFrame(tarjeta_mat, fg_color="transparent")
        acciones_comb.pack(fill="x", padx=14, pady=(0, 14))

        ctk.CTkButton(
            acciones_comb,
            text="Resolver combinación lineal",
            height=40,
            corner_radius=8,
            fg_color=PALETA["primario"],
            hover_color=PALETA["primario_hover"],
            text_color="#04191A",
            font=("Segoe UI", 13, "bold"),
            command=self._resolver_combinacion,
        ).pack(side="left")

        ctk.CTkButton(
            acciones_comb,
            text="Limpiar",
            height=40,
            corner_radius=8,
            fg_color=PALETA["secundario"],
            hover_color=PALETA["secundario_hover"],
            command=self._limpiar_combinacion,
        ).pack(side="left", padx=10)

        # Panel derecho con pestañas
        derecha = ctk.CTkFrame(contenido, fg_color="transparent")
        derecha.grid(row=0, column=1, rowspan=2, sticky="nsew")
        derecha.grid_columnconfigure(0, weight=1)
        derecha.grid_rowconfigure(0, weight=1)

        self.tab_comb = ctk.CTkTabview(
            derecha,
            fg_color=PALETA["panel"],
            corner_radius=12,
            border_width=1,
            border_color=PALETA["borde"],
            segmented_button_selected_color=PALETA["primario"],
            text_color=PALETA["texto"],
        )
        self.tab_comb.grid(row=0, column=0, sticky="nsew")

        tab_proc_c = self.tab_comb.add("Procedimiento Paso a Paso")
        tab_res_c = self.tab_comb.add("Resultado y Verificación")

        self.proc_panel_comb = ProcessPanel(tab_proc_c)
        self.proc_panel_comb.pack(fill="both", expand=True)

        self.res_scroll_comb = ctk.CTkScrollableFrame(tab_res_c, fg_color="transparent")
        self.res_scroll_comb.pack(fill="both", expand=True, padx=6, pady=6)
        self._mostrar_placeholder_combinacion()

        self._generar_entradas_combinacion()
        return pagina

    def _generar_entradas_combinacion(self):
        try:
            n = int(self.entrada_dim_comb.get())
            k = int(self.entrada_k_comb.get())
            if n <= 0 or k <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Dimensión y cantidad de vectores deben ser enteros positivos.")
            return

        for w in self.grid_host_comb.winfo_children():
            w.destroy()

        self.entradas_vectores_comb = [[] for _ in range(k)]
        self.entradas_b_comb = []

        # Encabezados
        for j in range(k):
            ctk.CTkLabel(self.grid_host_comb, text=f"v{j + 1}", font=("Segoe UI", 12, "bold"), text_color=PALETA["primario"]).grid(row=0, column=j, padx=4, pady=(4, 6))

        ctk.CTkLabel(self.grid_host_comb, text="b", font=("Segoe UI", 12, "bold"), text_color=PALETA["exito"]).grid(row=0, column=k + 1, padx=4, pady=(4, 6))

        for i in range(n):
            for j in range(k):
                e = ctk.CTkEntry(self.grid_host_comb, width=64, height=34, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
                e.grid(row=i + 1, column=j, padx=4, pady=4)
                e.insert(0, "0")
                self.entradas_vectores_comb[j].append(e)

            sep = ctk.CTkFrame(self.grid_host_comb, width=2, height=34, fg_color=PALETA["primario"])
            sep.grid(row=i + 1, column=k, padx=10, pady=4)

            eb = ctk.CTkEntry(self.grid_host_comb, width=64, height=34, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
            eb.grid(row=i + 1, column=k + 1, padx=4, pady=4)
            eb.insert(0, "0")
            self.entradas_b_comb.append(eb)

        self.canvas_comb.configure(scrollregion=self.canvas_comb.bbox("all"))

    def _limpiar_combinacion(self):
        for col in self.entradas_vectores_comb:
            for e in col:
                e.delete(0, "end")
                e.insert(0, "0")
        for eb in self.entradas_b_comb:
            eb.delete(0, "end")
            eb.insert(0, "0")
        self.proc_panel_comb.mostrar_placeholder()
        self._mostrar_placeholder_combinacion()

    def _mostrar_placeholder_combinacion(self):
        for w in self.res_scroll_comb.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.res_scroll_comb,
            text="Configura los vectores y presiona 'Analizar combinación lineal' para ver la ecuación vectorial, el sistema equivalente y la verificación.",
            font=FUENTE_NORMAL,
            text_color=PALETA["texto_3"],
            wraplength=500,
            justify="left",
        ).pack(anchor="w", padx=16, pady=16)

    def _resolver_combinacion(self):
        try:
            k = len(self.entradas_vectores_comb)
            vectores = []
            for j in range(k):
                v_j = [convertir_numero(e.get()) for e in self.entradas_vectores_comb[j]]
                vectores.append(v_j)
            b = [convertir_numero(e.get()) for e in self.entradas_b_comb]

            res = analizar_combinacion_lineal(vectores, b)
            self.proc_panel_comb.mostrar_pasos(res["sistema"]["pasos"])
            self._mostrar_resultado_combinacion(res)
            self.tab_comb.set("Procedimiento Paso a Paso")
        except Exception as error:
            messagebox.showerror("Error en Combinación Lineal", str(error))

    def _mostrar_resultado_combinacion(self, res):
        for w in self.res_scroll_comb.winfo_children():
            w.destroy()

        # 1. Ecuacion Vectorial
        t_ec = ctk.CTkFrame(self.res_scroll_comb, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        t_ec.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(t_ec, text="Ecuación Vectorial y Sistema Matricial", font=("Segoe UI", 14, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 4))

        k = len(res["vectores"])
        terminos_vec = [f"c{j + 1} · {formatear_vector(res['vectores'][j])}" for j in range(k)]
        ec_vec_str = " + ".join(terminos_vec) + f" = {formatear_vector(res['b'])}"

        ctk.CTkLabel(t_ec, text="Ecuación vectorial planteada:", font=FUENTE_PEQUENA, text_color=PALETA["texto_3"]).pack(anchor="w", padx=16, pady=(2, 0))
        ctk.CTkLabel(t_ec, text=ec_vec_str, font=FUENTE_MONO, text_color=PALETA["texto_2"], wraplength=600, justify="left").pack(anchor="w", padx=16, pady=(0, 8))

        flujo = (
            "Transformación algebraica:\n"
            "Ecuación Vectorial  ──>  Sistema de Ecuaciones  ──>  Matriz Aumentada [A | b]  ──>  Gauss-Jordan"
        )
        ctk.CTkLabel(t_ec, text=flujo, font=("Segoe UI", 11, "italic"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(0, 12))

        # 2. Conclusion
        color_concl = PALETA["exito"] if res["es_posible"] else PALETA["error"]
        t_concl = ctk.CTkFrame(self.res_scroll_comb, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=color_concl)
        t_concl.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(t_concl, text="Conclusión Algebraica", font=("Segoe UI", 14, "bold"), text_color=color_concl).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(t_concl, text=res["conclusion"], font=FUENTE_NORMAL, text_color=PALETA["texto"], wraplength=600, justify="left").pack(anchor="w", padx=16, pady=(0, 12))

        # 3. Coeficientes
        sis = res["sistema"]
        if sis["solucion"] is not None:
            t_coef = ctk.CTkFrame(self.res_scroll_comb, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
            t_coef.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(t_coef, text="Coeficientes encontrados:", font=("Segoe UI", 14, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 4))
            for j, c_val in enumerate(sis["solucion"]):
                ctk.CTkLabel(t_coef, text=f"c{j + 1} = {formatear_numero(c_val)}", font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
            ctk.CTkLabel(t_coef, text="").pack(pady=2)

        elif sis["expresiones"] is not None:
            t_coef = ctk.CTkFrame(self.res_scroll_comb, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
            t_coef.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(t_coef, text="Solución paramétrica de coeficientes (infinitas combinaciones):", font=("Segoe UI", 14, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 4))
            for j in range(k):
                ctk.CTkLabel(t_coef, text=f"c{j + 1} = {sis['expresiones'][j]}", font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
            ctk.CTkLabel(t_coef, text="").pack(pady=2)

        # 4. Verificacion vectorial
        v_det = res["verificacion_vectorial"]
        if v_det is not None:
            t_ver = ctk.CTkFrame(self.res_scroll_comb, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["exito"])
            t_ver.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(t_ver, text="✓ Verificación Vectorial", font=("Segoe UI", 14, "bold"), text_color=PALETA["exito"]).pack(anchor="w", padx=16, pady=(12, 4))
            ctk.CTkLabel(t_ver, text="Sustitución de coeficientes en la combinación lineal:", font=FUENTE_PEQUENA, text_color=PALETA["texto_3"]).pack(anchor="w", padx=16, pady=(2, 0))
            ctk.CTkLabel(t_ver, text=v_det["expresion_combinacion"], font=FUENTE_MONO, text_color=PALETA["texto_2"], wraplength=600, justify="left").pack(anchor="w", padx=16, pady=(2, 4))
            ctk.CTkLabel(t_ver, text=f"= {formatear_vector(v_det['vector_calculado'])}", font=FUENTE_MONO, text_color=PALETA["texto"]).pack(anchor="w", padx=16, pady=2)
            ctk.CTkLabel(t_ver, text=f"= b {formatear_vector(v_det['vector_esperado'])} (Coincidencia exacta)", font=FUENTE_MONO, text_color=PALETA["exito"]).pack(anchor="w", padx=16, pady=(2, 12))

    # -------------------------------------------------------------------------
    # Pagina: Independencia Lineal (Tarea 3)
    # -------------------------------------------------------------------------

    def _crear_pagina_independencia(self, parent):
        pagina = ctk.CTkFrame(parent, fg_color=PALETA["fondo"], corner_radius=0)
        pagina.grid_columnconfigure(0, weight=1)
        pagina.grid_rowconfigure(1, weight=1)

        self._crear_encabezado(
            pagina,
            "Independencia Lineal de Vectores",
            "Determina si un conjunto de vectores es Linealmente Independiente (LI) o Dependiente (LD)",
        )

        contenido = ctk.CTkFrame(pagina, fg_color="transparent")
        contenido.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        contenido.grid_columnconfigure(0, weight=2)
        contenido.grid_columnconfigure(1, weight=3)
        contenido.grid_rowconfigure(1, weight=1)

        izq = ctk.CTkFrame(contenido, fg_color="transparent")
        izq.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 14))

        cfg = crear_tarjeta(izq, "Configuración del conjunto")
        cfg.pack(fill="x", pady=(0, 12))
        fila_cfg = ctk.CTkFrame(cfg, fg_color="transparent")
        fila_cfg.pack(fill="x", padx=18, pady=(0, 14))

        ctk.CTkLabel(fila_cfg, text="Dimensión n:", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(side="left", padx=(0, 6))
        self.entrada_dim_ind = ctk.CTkEntry(fila_cfg, width=58, height=36, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
        self.entrada_dim_ind.insert(0, "3")
        self.entrada_dim_ind.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(fila_cfg, text="Vectores k:", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(side="left", padx=(0, 6))
        self.entrada_k_ind = ctk.CTkEntry(fila_cfg, width=58, height=36, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
        self.entrada_k_ind.insert(0, "3")
        self.entrada_k_ind.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            fila_cfg,
            text="Generar",
            width=90,
            height=36,
            corner_radius=8,
            fg_color=PALETA["primario"],
            hover_color=PALETA["primario_hover"],
            text_color="#04191A",
            font=("Segoe UI", 12, "bold"),
            command=self._generar_entradas_independencia,
        ).pack(side="left")

        tarjeta_mat = crear_tarjeta(izq, "Vectores [ v1  v2 ... vk ]")
        tarjeta_mat.pack(fill="both", expand=True, pady=(0, 12))

        self.canvas_ind_frame = ctk.CTkFrame(tarjeta_mat, fg_color=PALETA["panel_2"], corner_radius=10)
        self.canvas_ind_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.canvas_ind = tk.Canvas(self.canvas_ind_frame, bg=resolver_color(PALETA["panel_2"]), highlightthickness=0, height=210)
        self.scroll_y_ind = ctk.CTkScrollbar(self.canvas_ind_frame, orientation="vertical", command=self.canvas_ind.yview, button_color=PALETA["primario"])
        self.scroll_x_ind = ctk.CTkScrollbar(self.canvas_ind_frame, orientation="horizontal", command=self.canvas_ind.xview, button_color=PALETA["primario"])
        self.canvas_ind.configure(yscrollcommand=self.scroll_y_ind.set, xscrollcommand=self.scroll_x_ind.set)

        self.canvas_ind.grid(row=0, column=0, sticky="nsew", padx=(10, 4), pady=(10, 4))
        self.scroll_y_ind.grid(row=0, column=1, sticky="ns", pady=(10, 4), padx=(0, 6))
        self.scroll_x_ind.grid(row=1, column=0, sticky="ew", padx=(10, 4), pady=(0, 6))
        self.canvas_ind_frame.grid_rowconfigure(0, weight=1)
        self.canvas_ind_frame.grid_columnconfigure(0, weight=1)

        self.grid_host_ind = ctk.CTkFrame(self.canvas_ind, fg_color="transparent")
        self.canvas_ind_window = self.canvas_ind.create_window((0, 0), window=self.grid_host_ind, anchor="nw")
        self.grid_host_ind.bind("<Configure>", lambda e: self.canvas_ind.configure(scrollregion=self.canvas_ind.bbox("all")))

        acciones_ind = ctk.CTkFrame(tarjeta_mat, fg_color="transparent")
        acciones_ind.pack(fill="x", padx=14, pady=(0, 14))

        ctk.CTkButton(
            acciones_ind,
            text="Resolver independencia lineal",
            height=40,
            corner_radius=8,
            fg_color=PALETA["primario"],
            hover_color=PALETA["primario_hover"],
            text_color="#04191A",
            font=("Segoe UI", 13, "bold"),
            command=self._resolver_independencia,
        ).pack(side="left")

        ctk.CTkButton(
            acciones_ind,
            text="Limpiar",
            height=40,
            corner_radius=8,
            fg_color=PALETA["secundario"],
            hover_color=PALETA["secundario_hover"],
            command=self._limpiar_independencia,
        ).pack(side="left", padx=10)

        derecha = ctk.CTkFrame(contenido, fg_color="transparent")
        derecha.grid(row=0, column=1, rowspan=2, sticky="nsew")
        derecha.grid_columnconfigure(0, weight=1)
        derecha.grid_rowconfigure(0, weight=1)

        self.tab_ind = ctk.CTkTabview(
            derecha,
            fg_color=PALETA["panel"],
            corner_radius=12,
            border_width=1,
            border_color=PALETA["borde"],
            segmented_button_selected_color=PALETA["primario"],
            text_color=PALETA["texto"],
        )
        self.tab_ind.grid(row=0, column=0, sticky="nsew")

        tab_proc_i = self.tab_ind.add("Procedimiento (Gauss-Jordan)")
        tab_res_i = self.tab_ind.add("Análisis y Conclusión")

        self.proc_panel_ind = ProcessPanel(tab_proc_i)
        self.proc_panel_ind.pack(fill="both", expand=True)

        self.res_scroll_ind = ctk.CTkScrollableFrame(tab_res_i, fg_color="transparent")
        self.res_scroll_ind.pack(fill="both", expand=True, padx=6, pady=6)
        self._mostrar_placeholder_independencia()

        self._generar_entradas_independencia()
        return pagina

    def _generar_entradas_independencia(self):
        try:
            n = int(self.entrada_dim_ind.get())
            k = int(self.entrada_k_ind.get())
            if n <= 0 or k <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Dimensión y cantidad de vectores deben ser enteros positivos.")
            return

        for w in self.grid_host_ind.winfo_children():
            w.destroy()

        self.entradas_vectores_ind = [[] for _ in range(k)]

        for j in range(k):
            ctk.CTkLabel(self.grid_host_ind, text=f"v{j + 1}", font=("Segoe UI", 12, "bold"), text_color=PALETA["primario"]).grid(row=0, column=j, padx=4, pady=(4, 6))

        for i in range(n):
            for j in range(k):
                e = ctk.CTkEntry(self.grid_host_ind, width=64, height=34, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
                e.grid(row=i + 1, column=j, padx=4, pady=4)
                e.insert(0, "0")
                self.entradas_vectores_ind[j].append(e)

        self.canvas_ind.configure(scrollregion=self.canvas_ind.bbox("all"))

    def _limpiar_independencia(self):
        for col in self.entradas_vectores_ind:
            for e in col:
                e.delete(0, "end")
                e.insert(0, "0")
        self.proc_panel_ind.mostrar_placeholder()
        self._mostrar_placeholder_independencia()

    def _mostrar_placeholder_independencia(self):
        for w in self.res_scroll_ind.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.res_scroll_ind,
            text="Configura los vectores y presiona 'Determinar independencia lineal' para resolver el sistema homogéneo [A | 0] y analizar pivotes.",
            font=FUENTE_NORMAL,
            text_color=PALETA["texto_3"],
            wraplength=500,
            justify="left",
        ).pack(anchor="w", padx=16, pady=16)

    def _resolver_independencia(self):
        try:
            k = len(self.entradas_vectores_ind)
            vectores = []
            for j in range(k):
                v_j = [convertir_numero(e.get()) for e in self.entradas_vectores_ind[j]]
                vectores.append(v_j)

            res = analizar_independencia_lineal(vectores)
            self.proc_panel_ind.mostrar_pasos(res["sistema"]["pasos"])
            self._mostrar_resultado_independencia(res)
            self.tab_ind.set("Procedimiento (Gauss-Jordan)")
        except Exception as error:
            messagebox.showerror("Error en Independencia Lineal", str(error))

    def _mostrar_resultado_independencia(self, res):
        for w in self.res_scroll_ind.winfo_children():
            w.destroy()

        color_est = PALETA["exito"] if res["es_li"] else PALETA["advertencia"]

        # Banner de Clasificacion
        t_clas = ctk.CTkFrame(self.res_scroll_ind, fg_color=PALETA["panel_2"], corner_radius=10, border_width=2, border_color=color_est)
        t_clas.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(t_clas, text="Clasificación del conjunto:", font=FUENTE_PEQUENA, text_color=PALETA["texto_3"]).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(t_clas, text=res["clasificacion"], font=("Segoe UI", 16, "bold"), text_color=color_est).pack(anchor="w", padx=16, pady=(0, 12))

        # Analisis Cuantitativo
        t_anal = ctk.CTkFrame(self.res_scroll_ind, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        t_anal.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(t_anal, text="Análisis de Pivotes y Variables Libres:", font=("Segoe UI", 14, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 6))

        ctk.CTkLabel(t_anal, text=f"• Dimensión del espacio: R^{res['dimension']}", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(t_anal, text=f"• Cantidad de vectores (k): {res['num_vectores']}", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(t_anal, text=f"• Columnas con pivote (rango): {res['num_pivotes']}", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(t_anal, text=f"• Variables libres: {res['num_libres']}", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=(2, 12))

        # Conclusion detallada
        t_concl = ctk.CTkFrame(self.res_scroll_ind, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        t_concl.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(t_concl, text="Justificación Algebraica:", font=("Segoe UI", 14, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 6))
        ctk.CTkLabel(t_concl, text=res["conclusion"], font=FUENTE_NORMAL, text_color=PALETA["texto"], wraplength=600, justify="left").pack(anchor="w", padx=16, pady=(0, 6))

        if res["razones_adicionales"]:
            for r in res["razones_adicionales"]:
                ctk.CTkLabel(t_concl, text=f"Nota teórica: {r}", font=("Segoe UI", 11, "italic"), text_color=PALETA["advertencia"], wraplength=600, justify="left").pack(anchor="w", padx=16, pady=(2, 4))
        ctk.CTkLabel(t_concl, text="").pack(pady=2)

        # Si es LD: Relacion de dependencia
        if res["relacion_dependencia"]:
            t_rel = ctk.CTkFrame(self.res_scroll_ind, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["advertencia"])
            t_rel.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(t_rel, text="Relación de dependencia no trivial encontrada:", font=("Segoe UI", 14, "bold"), text_color=PALETA["advertencia"]).pack(anchor="w", padx=16, pady=(12, 4))
            ctk.CTkLabel(t_rel, text=res["relacion_dependencia"], font=("Consolas", 15, "bold"), text_color=PALETA["texto"]).pack(anchor="w", padx=16, pady=(2, 12))

    # -------------------------------------------------------------------------
    # Pagina: Operaciones con Matrices (Tarea 3)
    # -------------------------------------------------------------------------

    def _crear_pagina_matrices(self, parent):
        pagina = ctk.CTkFrame(parent, fg_color=PALETA["fondo"], corner_radius=0)
        pagina.grid_columnconfigure(0, weight=1)
        pagina.grid_rowconfigure(1, weight=1)

        self._crear_encabezado(
            pagina,
            "Operaciones Básicas con Matrices",
            "Suma, resta, multiplicación por escalar y multiplicación matricial A · B manual",
        )

        contenido = ctk.CTkFrame(pagina, fg_color="transparent")
        contenido.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        contenido.grid_columnconfigure(0, weight=2)
        contenido.grid_columnconfigure(1, weight=3)
        contenido.grid_rowconfigure(1, weight=1)

        izq = ctk.CTkFrame(contenido, fg_color="transparent")
        izq.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 14))

        # Selector de operacion
        cfg_op = crear_tarjeta(izq, "Operación a realizar")
        cfg_op.pack(fill="x", pady=(0, 12))
        self.seg_op_mat = ctk.CTkSegmentedButton(
            cfg_op,
            values=["A + B", "A - B", "k · A", "A · B"],
            command=lambda v: self._actualizar_op_matrices(),
            selected_color=PALETA["primario"],
            selected_hover_color=PALETA["primario_hover"],
        )
        self.seg_op_mat.set("A · B")
        self.seg_op_mat.pack(fill="x", padx=18, pady=(0, 14))

        # Dimensiones
        cfg_dim = crear_tarjeta(izq, "Dimensiones")
        cfg_dim.pack(fill="x", pady=(0, 12))
        fila_dim = ctk.CTkFrame(cfg_dim, fg_color="transparent")
        fila_dim.pack(fill="x", padx=18, pady=(0, 14))

        ctk.CTkLabel(fila_dim, text="A:", font=("Segoe UI", 12, "bold"), text_color=PALETA["primario"]).pack(side="left", padx=(0, 4))
        self.ent_mA = ctk.CTkEntry(fila_dim, width=42, height=34, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
        self.ent_mA.insert(0, "2")
        self.ent_mA.pack(side="left", padx=(0, 2))
        ctk.CTkLabel(fila_dim, text="x", font=FUENTE_NORMAL, text_color=PALETA["texto_3"]).pack(side="left", padx=2)
        self.ent_nA = ctk.CTkEntry(fila_dim, width=42, height=34, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
        self.ent_nA.insert(0, "3")
        self.ent_nA.pack(side="left", padx=(0, 10))

        self.label_b_dims = ctk.CTkLabel(fila_dim, text="B:", font=("Segoe UI", 12, "bold"), text_color=PALETA["primario"])
        self.label_b_dims.pack(side="left", padx=(0, 4))
        self.ent_mB = ctk.CTkEntry(fila_dim, width=42, height=34, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
        self.ent_mB.insert(0, "3")
        self.ent_mB.pack(side="left", padx=(0, 2))
        self.label_x_b = ctk.CTkLabel(fila_dim, text="x", font=FUENTE_NORMAL, text_color=PALETA["texto_3"])
        self.label_x_b.pack(side="left", padx=2)
        self.ent_nB = ctk.CTkEntry(fila_dim, width=42, height=34, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
        self.ent_nB.insert(0, "2")
        self.ent_nB.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            fila_dim,
            text="Crear",
            width=70,
            height=34,
            corner_radius=8,
            fg_color=PALETA["primario"],
            hover_color=PALETA["primario_hover"],
            text_color="#04191A",
            font=("Segoe UI", 12, "bold"),
            command=self._generar_entradas_matrices,
        ).pack(side="left")

        # Entradas de matrices con scroll 2D
        tarjeta_mats = crear_tarjeta(izq, "Entradas de Matrices")
        tarjeta_mats.pack(fill="both", expand=True, pady=(0, 12))

        self.canvas_mat_frame = ctk.CTkFrame(tarjeta_mats, fg_color=PALETA["panel_2"], corner_radius=10)
        self.canvas_mat_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.canvas_mat = tk.Canvas(self.canvas_mat_frame, bg=resolver_color(PALETA["panel_2"]), highlightthickness=0, height=210)
        self.scroll_y_mat = ctk.CTkScrollbar(self.canvas_mat_frame, orientation="vertical", command=self.canvas_mat.yview, button_color=PALETA["primario"])
        self.scroll_x_mat = ctk.CTkScrollbar(self.canvas_mat_frame, orientation="horizontal", command=self.canvas_mat.xview, button_color=PALETA["primario"])
        self.canvas_mat.configure(yscrollcommand=self.scroll_y_mat.set, xscrollcommand=self.scroll_x_mat.set)

        self.canvas_mat.grid(row=0, column=0, sticky="nsew", padx=(10, 4), pady=(10, 4))
        self.scroll_y_mat.grid(row=0, column=1, sticky="ns", pady=(10, 4), padx=(0, 6))
        self.scroll_x_mat.grid(row=1, column=0, sticky="ew", padx=(10, 4), pady=(0, 6))
        self.canvas_mat_frame.grid_rowconfigure(0, weight=1)
        self.canvas_mat_frame.grid_columnconfigure(0, weight=1)

        self.grid_host_mat = ctk.CTkFrame(self.canvas_mat, fg_color="transparent")
        self.canvas_mat_window = self.canvas_mat.create_window((0, 0), window=self.grid_host_mat, anchor="nw")
        self.grid_host_mat.bind("<Configure>", lambda e: self.canvas_mat.configure(scrollregion=self.canvas_mat.bbox("all")))

        acciones_mat = ctk.CTkFrame(tarjeta_mats, fg_color="transparent")
        acciones_mat.pack(fill="x", padx=14, pady=(0, 14))

        ctk.CTkButton(
            acciones_mat,
            text="Resolver operación",
            height=40,
            corner_radius=8,
            fg_color=PALETA["primario"],
            hover_color=PALETA["primario_hover"],
            text_color="#04191A",
            font=("Segoe UI", 13, "bold"),
            command=self._operar_matrices,
        ).pack(side="left")

        ctk.CTkButton(
            acciones_mat,
            text="Limpiar",
            height=40,
            corner_radius=8,
            fg_color=PALETA["secundario"],
            hover_color=PALETA["secundario_hover"],
            command=self._limpiar_matrices,
        ).pack(side="left", padx=10)

        # Columna derecha (Resultados de matrices)
        self.res_scroll_mat = ctk.CTkScrollableFrame(contenido, fg_color=PALETA["panel"], corner_radius=12, border_width=1, border_color=PALETA["borde"])
        self.res_scroll_mat.grid(row=0, column=1, rowspan=2, sticky="nsew")
        self._mostrar_placeholder_matrices()

        self._generar_entradas_matrices()
        return pagina

    def _actualizar_op_matrices(self):
        op = self.seg_op_mat.get()
        if op in ("A + B", "A - B"):
            # Para suma/resta ambas matrices tienen el mismo tamano
            self.label_b_dims.configure(text="B:")
            self.ent_mB.configure(state="normal")
            self.ent_nB.configure(state="normal")
            self.label_x_b.configure(text="x")
            self.ent_mB.delete(0, "end")
            self.ent_mB.insert(0, self.ent_mA.get())
            self.ent_nB.delete(0, "end")
            self.ent_nB.insert(0, self.ent_nA.get())
        elif op == "k · A":
            self.label_b_dims.configure(text="k:")
            self.ent_mB.delete(0, "end")
            self.ent_mB.insert(0, "2")
            self.label_x_b.configure(text="")
            self.ent_nB.configure(state="disabled")
        else:
            # Multiplicacion
            self.label_b_dims.configure(text="B:")
            self.ent_mB.configure(state="normal")
            self.ent_nB.configure(state="normal")
            self.label_x_b.configure(text="x")
            self.ent_mB.delete(0, "end")
            self.ent_mB.insert(0, self.ent_nA.get())
            self.ent_nB.delete(0, "end")
            self.ent_nB.insert(0, "2")
        self._generar_entradas_matrices()

    def _generar_entradas_matrices(self):
        for w in self.grid_host_mat.winfo_children():
            w.destroy()

        try:
            mA = int(self.ent_mA.get())
            nA = int(self.ent_nA.get())
            if mA <= 0 or nA <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Dimensiones de A deben ser enteros positivos.")
            return

        op = self.seg_op_mat.get()
        self.entradas_mat_A = []
        self.entradas_mat_B = []

        # Matriz A
        ctk.CTkLabel(self.grid_host_mat, text=f"Matriz A ({mA}x{nA}):", font=("Segoe UI", 12, "bold"), text_color=PALETA["primario"]).grid(row=0, column=0, columnspan=nA, sticky="w", padx=6, pady=(4, 6))

        for i in range(mA):
            fila_e = []
            for j in range(nA):
                e = ctk.CTkEntry(self.grid_host_mat, width=58, height=32, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
                e.grid(row=i + 1, column=j, padx=3, pady=3)
                e.insert(0, "0")
                fila_e.append(e)
            self.entradas_mat_A.append(fila_e)

        fila_offset = mA + 2

        if op == "k · A":
            ctk.CTkLabel(self.grid_host_mat, text="Escalar k:", font=("Segoe UI", 12, "bold"), text_color=PALETA["primario"]).grid(row=fila_offset, column=0, sticky="w", padx=6, pady=(10, 4))
            self.entrada_escalar_mat_k = ctk.CTkEntry(self.grid_host_mat, width=65, height=32, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
            self.entrada_escalar_mat_k.grid(row=fila_offset + 1, column=0, padx=3, pady=3)
            self.entrada_escalar_mat_k.insert(0, self.ent_mB.get() or "2")
        else:
            try:
                mB = int(self.ent_mB.get())
                nB = int(self.ent_nB.get())
                if mB <= 0 or nB <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Dimensiones de B deben ser enteros positivos.")
                return

            ctk.CTkLabel(self.grid_host_mat, text=f"Matriz B ({mB}x{nB}):", font=("Segoe UI", 12, "bold"), text_color=PALETA["primario"]).grid(row=fila_offset, column=0, columnspan=nB, sticky="w", padx=6, pady=(10, 6))

            for i in range(mB):
                fila_e = []
                for j in range(nB):
                    e = ctk.CTkEntry(self.grid_host_mat, width=58, height=32, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
                    e.grid(row=fila_offset + 1 + i, column=j, padx=3, pady=3)
                    e.insert(0, "0")
                    fila_e.append(e)
                self.entradas_mat_B.append(fila_e)

        self.canvas_mat.configure(scrollregion=self.canvas_mat.bbox("all"))

    def _limpiar_matrices(self):
        for fila in self.entradas_mat_A:
            for e in fila:
                e.delete(0, "end")
                e.insert(0, "0")
        for fila in self.entradas_mat_B:
            for e in fila:
                e.delete(0, "end")
                e.insert(0, "0")
        self._mostrar_placeholder_matrices()

    def _mostrar_placeholder_matrices(self):
        for w in self.res_scroll_mat.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.res_scroll_mat,
            text="Selecciona la operación deseada y presiona 'Calcular operación' para ver la verificación de dimensiones, el desglose manual paso a paso y la matriz resultante.",
            font=FUENTE_NORMAL,
            text_color=PALETA["texto_3"],
            wraplength=520,
            justify="left",
        ).pack(anchor="w", padx=16, pady=16)

    def _operar_matrices(self):
        op = self.seg_op_mat.get()
        try:
            A = [[convertir_numero(e.get()) for e in fila] for fila in self.entradas_mat_A]
            mA, nA = dimensiones_matriz(A)

            if op == "k · A":
                k_val = convertir_numero(self.entrada_escalar_mat_k.get())
                res = multiplicar_matriz_escalar(k_val, A)
            else:
                B = [[convertir_numero(e.get()) for e in fila] for fila in self.entradas_mat_B]
                mB, nB = dimensiones_matriz(B)
                if op == "A + B":
                    res = sumar_matrices(A, B)
                elif op == "A - B":
                    res = restar_matrices(A, B)
                elif op == "A · B":
                    res = multiplicar_matrices(A, B)
        except Exception as error:
            # Mostrar error amigable tanto en modal como en la tarjeta
            for w in self.res_scroll_mat.winfo_children():
                w.destroy()
            t_err = ctk.CTkFrame(self.res_scroll_mat, fg_color=PALETA["panel_2"], corner_radius=10, border_width=2, border_color=PALETA["error"])
            t_err.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(t_err, text="✗ Error de Operación Matricial", font=("Segoe UI", 14, "bold"), text_color=PALETA["error"]).pack(anchor="w", padx=16, pady=(12, 4))
            ctk.CTkLabel(t_err, text=str(error), font=FUENTE_NORMAL, text_color=PALETA["texto"], wraplength=580, justify="left").pack(anchor="w", padx=16, pady=(0, 12))
            messagebox.showerror("Error en Operación Matricial", str(error))
            return

        for w in self.res_scroll_mat.winfo_children():
            w.destroy()

        # 1. Resumen de la Operacion
        t_resumen = ctk.CTkFrame(self.res_scroll_mat, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        t_resumen.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(t_resumen, text=f"Operación: {op}", font=("Segoe UI", 15, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(t_resumen, text=f"Dimensión de A: {mA} x {nA}", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
        if op != "k · A":
            ctk.CTkLabel(t_resumen, text=f"Dimensión de B: {mB} x {nB}", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
            mR, nR = dimensiones_matriz(res)
            ctk.CTkLabel(t_resumen, text=f"Dimensión resultante: {mR} x {nR}", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=(2, 12))
        else:
            ctk.CTkLabel(t_resumen, text=f"Escalar k = {formatear_numero(k_val)}", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=(2, 12))

        # 2. Desglose paso a paso del calculo manual
        t_pasos = ctk.CTkFrame(self.res_scroll_mat, fg_color=PALETA["panel_2"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        t_pasos.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(t_pasos, text="Procedimiento manual paso a paso:", font=("Segoe UI", 14, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 6))

        if op == "A · B":
            for i in range(mA):
                for j in range(nB):
                    prods = [f"({formatear_numero(A[i][k])})·({formatear_numero(B[k][j])})" for k in range(nA)]
                    linea_p = f"C[{i + 1},{j + 1}] = {' + '.join(prods)} = {formatear_numero(res[i][j])}"
                    ctk.CTkLabel(t_pasos, text=linea_p, font=FUENTE_MONO, text_color=PALETA["texto_2"], wraplength=600, justify="left").pack(anchor="w", padx=16, pady=2)
        elif op in ("A + B", "A - B"):
            signo = "+" if op == "A + B" else "-"
            for i in range(mA):
                for j in range(nA):
                    linea_p = f"C[{i + 1},{j + 1}] = ({formatear_numero(A[i][j])}) {signo} ({formatear_numero(B[i][j])}) = {formatear_numero(res[i][j])}"
                    ctk.CTkLabel(t_pasos, text=linea_p, font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
        elif op == "k · A":
            for i in range(mA):
                for j in range(nA):
                    linea_p = f"C[{i + 1},{j + 1}] = ({formatear_numero(k_val)}) · ({formatear_numero(A[i][j])}) = {formatear_numero(res[i][j])}"
                    ctk.CTkLabel(t_pasos, text=linea_p, font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(t_pasos, text="").pack(pady=2)

        # 3. Matriz Resultante
        t_mat_final = ctk.CTkFrame(self.res_scroll_mat, fg_color=PALETA["panel_2"], corner_radius=10, border_width=2, border_color=PALETA["exito"])
        t_mat_final.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(t_mat_final, text="Matriz resultante:", font=("Segoe UI", 14, "bold"), text_color=PALETA["exito"]).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(t_mat_final, text=matriz_simple_a_texto(res), font=FUENTE_MONO, text_color=PALETA["texto"], justify="left").pack(anchor="w", padx=16, pady=(0, 12))

    def _crear_pagina_metodo(self, parent):
        pagina = ctk.CTkFrame(parent, fg_color=PALETA["fondo"], corner_radius=0)
        pagina.grid_columnconfigure(0, weight=1)
        pagina.grid_rowconfigure(1, weight=1)

        self._crear_encabezado(
            pagina,
            "Métodos y Procedimientos Algebraicos",
            "Fundamentos teóricos de Gauss-Jordan, vectores, combinación e independencia lineal",
        )

        cuerpo = ctk.CTkScrollableFrame(pagina, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))

        pasos_metodo = [
            ("1. Operaciones con Vectores en R^n",
             "La suma u + v y la resta u - v se calculan sumando o restando las componentes homólogas. La multiplicación por escalar c·v multiplica cada componente por c. Dos vectores solo pueden sumarse o restarse si pertenecen al mismo espacio R^n."),
            ("2. Ecuación Vectorial y Combinación Lineal",
             "La ecuación vectorial c1·v1 + c2·v2 + ... + ck·vk = b se transforma en el sistema matricial A·c = b colocando los vectores vi como COLUMNAS de la matriz A. Resolver este sistema determina si b se encuentra en el espacio generado por los vectores."),
            ("3. Independencia Lineal y Sistemas Homogéneos",
             "Un conjunto {v1, ..., vk} es Linealmente Independiente (LI) si la única solución de c1·v1 + ... + ck·vk = 0 es la trivial (c1 = ... = ck = 0). Si tras reducir la matriz [A | 0] cada columna tiene pivote (rango = k), el conjunto es LI; si existen variables libres, existen soluciones no triviales y es Linealmente Dependiente (LD)."),
            ("4. Interpretación de la Ecuación Matricial Ax = b",
             "El producto matriz-vector Ax representa exactamente la combinación lineal de las columnas de A ponderadas por las incógnitas x1, x2, ..., xn: x1·col1(A) + ... + xn·coln(A) = b."),
            ("5. Operaciones con Matrices",
             "Suma y resta (A ± B) requieren que A y B tengan dimensiones idénticas m x n. Para la multiplicación matricial A(m x n) · B(n x p), el número de columnas de A debe ser estrictamente igual al número de filas de B; cada entrada C_ij es el producto punto de la fila i de A por la columna j de B."),
            ("6. Eliminación de Gauss-Jordan",
             "Se plantea la matriz aumentada [A | b]. En cada columna se elige un pivote no nulo mediante pivoteo parcial, se escala la fila para convertir el pivote en 1 (Fi -> Fi / k) y se anulan los demás elementos de la columna arriba y abajo (Fk -> Fk + c·Fpivote)."),
            ("7. Clasificación de Sistemas",
             "Inconsistente: surge una fila 0 = k (k != 0). Consistente determinado: cada columna de variables tiene pivote (solución única). Consistente indeterminado: sobran columnas sin pivote (infinitas soluciones parametrizadas)."),
            ("8. Verificación Algebraica",
             "En Ax=b se sustituye en cada ecuación original para corroborar la igualdad. En combinación lineal se evalúa la suma vectorial ponderada (c1)v1 + ... + (ck)vk y se compara con el vector objetivo b."),
        ]

        for titulo, texto in pasos_metodo:
            tarjeta = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
            tarjeta.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(tarjeta, text=titulo, font=("Segoe UI", 15, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(12, 4))
            ctk.CTkLabel(
                tarjeta, text=texto, font=FUENTE_NORMAL, text_color=PALETA["texto_2"],
                wraplength=780, justify="left",
            ).pack(anchor="w", padx=16, pady=(0, 12))

        return pagina

    def _crear_pagina_ayuda(self, parent):
        pagina = ctk.CTkFrame(parent, fg_color=PALETA["fondo"], corner_radius=0)
        pagina.grid_columnconfigure(0, weight=1)
        pagina.grid_rowconfigure(1, weight=1)

        self._crear_encabezado(
            pagina,
            "Ayuda y Glosario",
            "Instrucciones de uso de los módulos de la Tarea 3 y conceptos algebraicos clave",
        )

        cuerpo = ctk.CTkScrollableFrame(pagina, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))

        tarjeta_uso = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        tarjeta_uso.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(tarjeta_uso, text="Guía de uso de los módulos", font=("Segoe UI", 15, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(14, 6))
        pasos_uso = [
            "1. Ecuación Matricial (Ax = b): define ecuaciones y variables, ingresa coeficientes y términos independientes. Muestra pasos de Gauss-Jordan, solución y la interpretación como combinación lineal de columnas.",
            "2. Vectores en R^n: define la dimensión n, introduce los vectores u y v o el escalar k, y pulsa la operación deseada para ver el procedimiento componente a componente.",
            "3. Combinación Lineal: introduce k vectores y el vector objetivo b. Construye automáticamente [v1 ... vk | b] y resuelve para hallar los coeficientes c1, ..., ck con verificación vectorial.",
            "4. Independencia Lineal: introduce el conjunto {v1, ..., vk}. Construye el sistema homogéneo [A | 0] y determina si es LI (solución trivial única) o LD (variables libres con relación explícita).",
            "5. Operaciones con Matrices: selecciona A + B, A - B, k·A o A·B, define dimensiones y calcula. Incluye validación estricta de dimensiones y desglose manual por bucles anidados.",
            "6. Entrada de valores: acepta enteros, decimales y fracciones exactas como '3/2' o '-5/7'.",
        ]
        for paso in pasos_uso:
            ctk.CTkLabel(
                tarjeta_uso, text=paso, font=FUENTE_NORMAL, text_color=PALETA["texto_2"],
                wraplength=780, justify="left",
            ).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(tarjeta_uso, text="").pack(pady=4)

        conceptos = [
            ("Vector en R^n", "Una lista ordenada de n números reales que representa un punto o dirección en el espacio de dimensión n."),
            ("Combinación Lineal", "Expresión de la forma c1·v1 + c2·v2 + ... + ck·vk donde los ci son escalares y los vi vectores."),
            ("Espacio Generado (Gen)", "Conjunto de todas las posibles combinaciones lineales de los vectores dados."),
            ("Independencia Lineal (LI)", "Propiedad donde la única forma de que c1·v1 + ... + ck·vk sea el vector cero es que todos los ci sean cero."),
            ("Dependencia Lineal (LD)", "Existe al menos una solución no trivial (no todos los ci son cero) que da el vector cero; un vector es combinación lineal de otros."),
            ("Multiplicación Matricial (A · B)", "Operación válida solo si las columnas de A igualan las filas de B (nA = mB)."),
            ("Pivote", "El primer coeficiente no nulo de una fila en la forma escalonada, utilizado para eliminar los demás valores de su columna."),
            ("Forma Escalonada Reducida (RREF)", "Forma final de Gauss-Jordan donde cada pivote es 1 y es la única entrada no nula de su columna."),
            ("Variables básicas y libres", "Básicas corresponden a columnas con pivote; libres corresponden a columnas sin pivote y reciben parámetros (t, s, r, ...)."),
        ]

        tarjeta_conceptos = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        tarjeta_conceptos.pack(fill="x")
        ctk.CTkLabel(tarjeta_conceptos, text="Conceptos algebraicos clave", font=("Segoe UI", 15, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(14, 6))
        for nombre, definicion in conceptos:
            fila = ctk.CTkFrame(tarjeta_conceptos, fg_color="transparent")
            fila.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(fila, text=f"{nombre}:", font=("Segoe UI", 13, "bold"), text_color=PALETA["texto"]).pack(anchor="w")
            ctk.CTkLabel(
                fila, text=definicion, font=FUENTE_NORMAL, text_color=PALETA["texto_2"],
                wraplength=780, justify="left",
            ).pack(anchor="w")
        ctk.CTkLabel(tarjeta_conceptos, text="").pack(pady=4)

        return pagina

    def crear_configuracion(self, parent):
        fila = ctk.CTkFrame(parent, fg_color="transparent")
        fila.pack(fill="x", padx=18, pady=(0, 16))

        ctk.CTkLabel(fila, text="Ecuaciones", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(side="left", padx=(0, 8))
        self.entrada_m = ctk.CTkEntry(fila, width=70, height=38, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
        self.entrada_m.insert(0, "3")
        self.entrada_m.pack(side="left", padx=(0, 18))

        ctk.CTkLabel(fila, text="Variables", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(side="left", padx=(0, 8))
        self.entrada_n = ctk.CTkEntry(fila, width=70, height=38, justify="center", fg_color=PALETA["entrada"], border_color=PALETA["borde"])
        self.entrada_n.insert(0, "3")
        self.entrada_n.pack(side="left", padx=(0, 18))

        ctk.CTkButton(
            fila,
            text="Crear sistema",
            width=150,
            height=40,
            corner_radius=8,
            fg_color=PALETA["primario"],
            hover_color=PALETA["primario_hover"],
            text_color="#04191A",
            font=("Segoe UI", 13, "bold"),
            command=self.crear_sistema,
        ).pack(side="left")

        ctk.CTkLabel(
            fila,
            text="Enteros, decimales o fracciones como 3/2.",
            font=FUENTE_PEQUENA,
            text_color=PALETA["texto_3"],
        ).pack(side="left", padx=14)

    def crear_sistema(self):
        try:
            m = int(self.entrada_m.get())
            n = int(self.entrada_n.get())
            if m <= 0 or n <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Entrada invalida", "m y n deben ser enteros positivos.")
            return

        self.matrix_panel.crear_matriz(m, n)
        self.process_panel.mostrar_placeholder()
        self.result_panel.mostrar_placeholder()

    def limpiar_matriz(self):
        self.matrix_panel.limpiar()
        self.process_panel.mostrar_placeholder()
        self.result_panel.mostrar_placeholder()

    def resolver_desde_interfaz(self):
        try:
            A, b = self.matrix_panel.leer_datos()
            resultado = resolver_sistema(A, b)
            self.process_panel.mostrar_pasos(resultado["pasos"])
            self.result_panel.mostrar_resultado(resultado)
            self.tab_derecha.set("Procedimiento Paso a Paso")
        except Exception as error:
            messagebox.showerror("Error", str(error))


# -----------------------------------------------------------------------------
# Inicio del programa
# -----------------------------------------------------------------------------

def main():
    if ctk is None:
        raise SystemExit(
            "CustomTkinter no esta instalado. Ejecuta: py -m pip install customtkinter"
        )
    configurar_customtkinter()
    app = AplicacionAlgebraLineal()
    app.mainloop()


if __name__ == "__main__":
    main()
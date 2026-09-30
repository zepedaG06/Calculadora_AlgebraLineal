"""
Programa 1 - Algebra Lineal
Calculadora de algebra lineal del Grupo 3 (Universidad Americana).

Secciones:
- Sistemas de ecuaciones lineales por eliminacion de Gauss-Jordan.
- Combinaciones lineales (w pertenece a Gen{v1, ..., vn}).
- Ecuacion matricial Ax = b.
- Propiedades del producto matriz-vector Ax.
- Independencia lineal.

Restricciones cumplidas:
- No usa PySide6.
- No usa NumPy.
- No usa SciPy.
- La eliminacion por filas esta implementada manualmente.
"""

import os
import random
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
from fractions import Fraction
from math import lcm

try:
    import customtkinter as ctk
except ModuleNotFoundError:
    ctk = None

try:
    from PIL import Image, ImageTk
except ModuleNotFoundError:
    Image = None
    ImageTk = None


# Carpeta donde vive este archivo, para poder cargar el logo sin importar
# desde donde se ejecute el programa.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_LOGO = os.path.join(BASE_DIR, "universidad_americana.png")
if not os.path.exists(RUTA_LOGO):
    RUTA_LOGO = os.path.join(BASE_DIR, "logo_uam.png")

# Tamano maximo de filas/columnas que se pueden capturar en la interfaz.
LIMITE_DIMENSION = 10


# -----------------------------------------------------------------------------
# Logica matematica
# -----------------------------------------------------------------------------

def convertir_numero(texto):
    """
    Convierte la entrada del usuario a Fraction para trabajar con valores exactos.
    Acepta enteros (3), decimales con punto o coma (0.5 o 0,5) y fracciones (3/2).
    """
    texto = str(texto).strip().replace(" ", "").replace("−", "-")
    if not texto:
        raise ValueError("Hay una casilla vacía.")
    if "," in texto and "." not in texto and texto.count(",") == 1:
        texto = texto.replace(",", ".")
    try:
        return Fraction(texto)
    except ZeroDivisionError:
        raise ValueError(f"'{texto}' tiene una división entre cero.") from None
    except ValueError:
        raise ValueError(
            f"'{texto}' no es un número válido. Usa enteros, decimales o fracciones como 3/2."
        ) from None


def formatear_numero(numero):
    """Muestra las fracciones de forma legible: 2 en lugar de 2/1."""
    if numero == 0:
        return "0"
    if numero.denominator == 1:
        return str(numero.numerator)
    return f"{numero.numerator}/{numero.denominator}"


def formatear_coeficiente(valor):
    """
    Texto del valor absoluto de un coeficiente que va pegado a una variable.
    Las fracciones van entre parentesis para evitar ambiguedades: (1/2)x1.
    """
    valor = abs(Fraction(valor))
    texto = formatear_numero(valor)
    return f"({texto})" if valor.denominator != 1 else texto


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
    """Convierte una matriz aumentada en texto alineado (se usa al copiar resultados)."""
    if not matriz or not matriz[0]:
        return ""
    num_cols = len(matriz[0])
    anchos = [0] * num_cols
    for fila in matriz:
        for c, val in enumerate(fila):
            anchos[c] = max(anchos[c], len(formatear_numero(val)))
    anchos = [max(w, 4) for w in anchos]
    lineas = []
    for fila in matriz:
        coeficientes = "  ".join(f"{formatear_numero(fila[c]):>{anchos[c]}}" for c in range(num_cols - 1))
        independiente = f"{formatear_numero(fila[-1]):>{anchos[-1]}}"
        lineas.append(f"[ {coeficientes} | {independiente} ]")
    return "\n".join(lineas)


def buscar_fila_pivote(matriz, fila_inicio, columna):
    """Busca la primera fila (desde fila_inicio) con entrada no nula en la columna."""
    for fila in range(fila_inicio, len(matriz)):
        if matriz[fila][columna] != 0:
            return fila
    return None


class PasoEliminacion(dict):
    """
    Representa un paso en el procedimiento de eliminacion por filas.
    Compatible como diccionario (paso['operacion']), como objeto con atributos
    (paso.operacion) y como secuencia (paso[0]=operacion, paso[1]=matriz, paso[2]=explicacion).

    Tambien guarda que filas cambiaron, donde estan los pivotes y que fila se uso
    como referencia, para poder resaltarlos en la interfaz.
    """

    def __init__(self, operacion, explicacion, matriz, tipo="operacion",
                 filas=(), pivotes=(), fila_origen=None):
        super().__init__(
            operacion=operacion,
            explicacion=explicacion,
            matriz=matriz,
            tipo=tipo,
            filas=list(filas),
            pivotes=list(pivotes),
            fila_origen=fila_origen,
        )

    def __getattr__(self, nombre):
        try:
            return super().__getitem__(nombre)
        except KeyError:
            raise AttributeError(nombre) from None

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


def texto_resta_de_filas(destino, origen, factor):
    """Texto de la operacion Fdestino -> Fdestino - factor*Forigen, por ejemplo 'F2 → F2 - 2F1'."""
    factor_abs = abs(factor)
    k_str = "" if factor_abs == 1 else (
        str(factor_abs.numerator) if factor_abs.denominator == 1 else f"({formatear_numero(factor_abs)})"
    )
    signo = "-" if factor > 0 else "+"
    return f"F{destino + 1} → F{destino + 1} {signo} {k_str}F{origen + 1}"


def _texto_intercambio(fila_pivote, fila_encontrada, variable):
    return (
        f"En la posición pivote de la {variable} hay un 0, así que se "
        f"intercambia F{fila_pivote + 1} con F{fila_encontrada + 1}, la primera "
        f"fila de abajo con un valor distinto de cero."
    )


def gauss_jordan(matriz_aumentada, num_variables, nombres_variables=None):
    """
    Reduce [A | b] a forma escalonada reducida por filas.

    Todas las operaciones se hacen con Fraction para evitar errores de redondeo.
    En cada columna se usa como pivote la fila actual; solo si su entrada es 0
    se intercambia con la primera fila de abajo que tenga un valor distinto de
    cero, igual que al resolver a mano. Cada operacion queda registrada.
    """
    nombres = nombres_variables or obtener_nombres_variables(num_variables)
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

        fila_encontrada = buscar_fila_pivote(matriz, fila_pivote, columna)
        if fila_encontrada is None:
            # Toda la columna es cero desde la fila pivote: la variable sera libre.
            continue

        variable = f"columna {columna + 1} (variable {nombres[columna]})"
        pivote = [(fila_pivote, columna)]

        if fila_encontrada != fila_pivote:
            intercambiar_filas(matriz, fila_pivote, fila_encontrada)
            pasos.append(
                PasoEliminacion(
                    operacion=f"F{fila_pivote + 1} ↔ F{fila_encontrada + 1}",
                    explicacion=_texto_intercambio(fila_pivote, fila_encontrada, variable),
                    matriz=copiar_matriz(matriz),
                    tipo="intercambio",
                    filas=(fila_pivote, fila_encontrada),
                    pivotes=pivote,
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
                        f"Se multiplica F{fila_pivote + 1} por {formatear_numero(inverso)} "
                        f"para convertir en 1 el pivote de la {variable}."
                    ),
                    matriz=copiar_matriz(matriz),
                    tipo="escalado",
                    filas=(fila_pivote,),
                    pivotes=pivote,
                )
            )

        # Hacer cero la columna del pivote en TODAS las demas filas.
        for fila in range(num_filas):
            if fila == fila_pivote:
                continue

            factor = matriz[fila][columna]
            if factor == 0:
                continue

            sumar_multiplo_fila(matriz, fila, fila_pivote, -factor)

            posicion = "debajo" if fila > fila_pivote else "arriba"
            pasos.append(
                PasoEliminacion(
                    operacion=texto_resta_de_filas(fila, fila_pivote, factor),
                    explicacion=(
                        f"Se hace cero el elemento de F{fila + 1} en la {variable}, "
                        f"{posicion} del pivote, usando F{fila_pivote + 1}."
                    ),
                    matriz=copiar_matriz(matriz),
                    tipo="eliminacion",
                    filas=(fila,),
                    pivotes=pivote,
                    fila_origen=fila_pivote,
                )
            )

        columnas_pivote.append(columna)
        fila_pivote += 1

    if columnas_pivote:
        columnas = ", ".join(str(c + 1) for c in columnas_pivote)
        resumen = (
            f"Se obtuvo la forma escalonada reducida: hay pivotes iguales a 1 en las columnas "
            f"{columnas} y el resto de cada columna pivote es cero."
        )
    else:
        resumen = "La matriz de coeficientes no tiene pivotes: todas sus entradas son cero."
    pasos.append(
        PasoEliminacion(
            operacion="Forma escalonada reducida",
            explicacion=resumen,
            matriz=copiar_matriz(matriz),
            tipo="final",
            pivotes=list(enumerate(columnas_pivote)),
        )
    )

    return matriz, columnas_pivote, pasos


def forma_escalonada(matriz_aumentada, num_variables, nombres_variables=None, explicacion_inicial=None):
    """
    Reduce [A | b] a una forma escalonada por filas (eliminacion gaussiana).

    A diferencia de Gauss-Jordan, solo se hacen ceros DEBAJO de cada pivote y
    los pivotes no se convierten en 1. Devuelve (matriz, columnas_pivote, pasos).
    """
    nombres = nombres_variables or obtener_nombres_variables(num_variables)
    matriz = copiar_matriz(matriz_aumentada)
    pasos = [
        PasoEliminacion(
            operacion="Matriz aumentada inicial",
            explicacion=explicacion_inicial or "Se plantea la matriz aumentada [A | b].",
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

        fila_encontrada = buscar_fila_pivote(matriz, fila_pivote, columna)
        if fila_encontrada is None:
            continue

        variable = f"columna {columna + 1} (variable {nombres[columna]})"
        pivote = [(fila_pivote, columna)]

        if fila_encontrada != fila_pivote:
            intercambiar_filas(matriz, fila_pivote, fila_encontrada)
            pasos.append(
                PasoEliminacion(
                    operacion=f"F{fila_pivote + 1} ↔ F{fila_encontrada + 1}",
                    explicacion=_texto_intercambio(fila_pivote, fila_encontrada, variable),
                    matriz=copiar_matriz(matriz),
                    tipo="intercambio",
                    filas=(fila_pivote, fila_encontrada),
                    pivotes=pivote,
                )
            )

        valor_pivote = matriz[fila_pivote][columna]
        for fila in range(fila_pivote + 1, num_filas):
            if matriz[fila][columna] == 0:
                continue
            factor = matriz[fila][columna] / valor_pivote
            sumar_multiplo_fila(matriz, fila, fila_pivote, -factor)
            pasos.append(
                PasoEliminacion(
                    operacion=texto_resta_de_filas(fila, fila_pivote, factor),
                    explicacion=(
                        f"Se hace cero el elemento de F{fila + 1} en la {variable}, debajo del pivote "
                        f"{formatear_numero(valor_pivote)}, usando F{fila_pivote + 1} con multiplicador "
                        f"{formatear_numero(factor)}."
                    ),
                    matriz=copiar_matriz(matriz),
                    tipo="eliminacion",
                    filas=(fila,),
                    pivotes=pivote,
                    fila_origen=fila_pivote,
                )
            )

        columnas_pivote.append(columna)
        fila_pivote += 1

    if columnas_pivote:
        columnas = ", ".join(str(c + 1) for c in columnas_pivote)
        resumen = (
            f"Se obtuvo la forma escalonada por filas: debajo de cada pivote solo hay ceros. "
            f"Hay {len(columnas_pivote)} pivote(s), en las columnas {columnas}."
        )
    else:
        resumen = "La matriz de coeficientes no tiene pivotes: todas sus entradas son cero."
    pasos.append(
        PasoEliminacion(
            operacion="Forma escalonada por filas",
            explicacion=resumen,
            matriz=copiar_matriz(matriz),
            tipo="final",
            pivotes=list(enumerate(columnas_pivote)),
        )
    )
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
    Genera nombres estandar para variables libres.
    - Para 1 variable libre: ['t']
    - Para 2 variables libres: ['s', 't']
    - Para 3 variables libres: ['r', 's', 't']
    - Para mas variables libres: ['r', 's', 't', 'u', ...] o ['t1', 't2', ...]
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
    Expresa variables basicas en funcion de variables libres.

    Si una columna no es pivote, su variable queda libre y recibe un parametro.
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
                signo = "-" if coeficiente < 0 else ""
                terminos.append(f"{signo}{formatear_coeficiente(coeficiente)}{parametro}")

        expresiones[columna_pivote] = " + ".join(terminos).replace("+ -", "- ") if terminos else "0"

    expresiones_ordenadas = {i: expresiones[i] for i in range(num_variables)}
    return expresiones_ordenadas, variables_libres, parametros


def obtener_forma_vectorial(matriz_rref, columnas_pivote, num_variables):
    """
    Forma vectorial parametrica x = p + t1*v1 + t2*v2 + ...

    p es la solucion particular (todos los parametros en 0) y cada v es el
    vector direccion asociado a una variable libre.
    """
    libres = [c for c in range(num_variables) if c not in columnas_pivote]
    particular = [Fraction(0) for _ in range(num_variables)]
    for fila, columna in enumerate(columnas_pivote):
        particular[columna] = matriz_rref[fila][-1]

    direcciones = []
    for libre, parametro in zip(libres, nombres_parametros(len(libres))):
        vector = [Fraction(0) for _ in range(num_variables)]
        vector[libre] = Fraction(1)
        for fila, columna in enumerate(columnas_pivote):
            vector[columna] = -matriz_rref[fila][libre]
        direcciones.append((parametro, vector))
    return particular, direcciones


SUPERINDICES = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def espacio_real(n):
    """Nombre del espacio R^n con superindice: espacio_real(3) -> 'R³'."""
    return "R" + str(n).translate(SUPERINDICES)


def obtener_nombres_variables(num_variables, prefijo="x"):
    """Genera nombres de variables consistentes: x1, x2, x3, ..."""
    return [f"{prefijo}{i + 1}" for i in range(num_variables)]


def unir_terminos(terminos, union=""):
    """
    Une pares (coeficiente, texto) en una expresion como '2x1 - x2 + (1/2)x3'.
    Omite coeficientes 0, muestra 1x como x y -1x como -x.
    """
    partes = []
    for coeficiente, texto in terminos:
        if coeficiente == 0:
            continue
        cuerpo = texto if abs(coeficiente) == 1 else f"{formatear_coeficiente(coeficiente)}{union}{texto}"
        if not partes:
            partes.append(f"-{cuerpo}" if coeficiente < 0 else cuerpo)
        else:
            partes.append(f"- {cuerpo}" if coeficiente < 0 else f"+ {cuerpo}")
    return " ".join(partes) if partes else "0"


def formatear_ecuacion_original(fila_coefs, termino_indep, nombres_vars):
    """
    Formatea la ecuacion algebraica original a partir de los coeficientes y terminos independientes.
    Omite coeficientes 0, muestra 1x como x, -1x como -x, y maneja signos + / - correctamente.
    """
    lado_izq = unir_terminos(zip(fila_coefs, nombres_vars))
    return f"{lado_izq} = {formatear_numero(termino_indep)}"


def formatear_sustitucion(fila_coefs, termino_indep, solucion):
    """
    Genera la expresion de sustitucion explicita con parentesis para cada variable:
    ejemplo: 2(1) - (2) + (3) = 3 o 2(1) - 3(2) + (4) = 7.
    """
    valores = [f"({formatear_numero(valor)})" for valor in solucion]
    lado_izq = unir_terminos(zip(fila_coefs, valores))
    return f"{lado_izq} = {formatear_numero(termino_indep)}"


def formatear_simplificacion(fila_coefs, termino_indep, solucion):
    """
    Evalua paso a paso la simplificacion de los terminos sustituidos:
    1. Productos individuales evaluados: 2 - 2 + 3 = 3
    2. Suma total evaluada: 3 = 3
    """
    pasos_simpl = []
    productos = [c * solucion[j] for j, c in enumerate(fila_coefs) if c != 0]

    if len(productos) > 1:
        partes = []
        for p in productos:
            if not partes:
                partes.append(formatear_numero(p))
            elif p >= 0:
                partes.append(f"+ {formatear_numero(p)}")
            else:
                partes.append(f"- {formatear_numero(abs(p))}")
        pasos_simpl.append(f"{' '.join(partes)} = {formatear_numero(termino_indep)}")

    suma_total = sum(productos) if productos else Fraction(0)
    pasos_simpl.append(f"{formatear_numero(suma_total)} = {formatear_numero(termino_indep)}")

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

    def __getattr__(self, nombre):
        try:
            return super().__getitem__(nombre)
        except KeyError:
            raise AttributeError(nombre) from None

    def __getitem__(self, key):
        if isinstance(key, int):
            return [self["suma_obtenida"], self["esperado"], self["coincide"]][key]
        return super().__getitem__(key)


def verificar_solucion(A_original, b_original, solucion, nombres_vars=None):
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

    nombres_vars = nombres_vars or obtener_nombres_variables(num_vars)
    detalles = []
    correcta = True

    for i, fila in enumerate(A_original):
        esperado = b_original[i]

        # La comprobacion real se hace con el sistema ORIGINAL,
        # no con la matriz reducida.
        suma_directa = sum(fila[j] * solucion[j] for j in range(num_vars))
        coincide = suma_directa == esperado
        correcta = correcta and coincide

        simpl_pasos, _, _ = formatear_simplificacion(fila, esperado, solucion)
        detalles.append(
            DetalleVerificacion(
                indice=i + 1,
                ecuacion_original=formatear_ecuacion_original(fila, esperado, nombres_vars),
                sustitucion=formatear_sustitucion(fila, esperado, solucion),
                simplificacion=simpl_pasos,
                suma_obtenida=suma_directa,
                esperado=esperado,
                coincide=coincide,
            )
        )

    return correcta, detalles


def resolver_sistema(A, b, nombres_variables=None):
    """Funcion principal de la parte matematica."""
    if not A or not A[0]:
        raise ValueError("El sistema no puede estar vacío.")
    num_variables = len(A[0])
    nombres_vars = list(nombres_variables) if nombres_variables else obtener_nombres_variables(num_variables)
    aumentada = crear_matriz_aumentada(A, b)
    rref, columnas_pivote, pasos = gauss_jordan(aumentada, num_variables, nombres_vars)
    clasificacion, descripcion = clasificar_sistema(rref, columnas_pivote, num_variables)
    filas_inconsistentes = [i for i, fila in enumerate(rref) if fila_inconsistente(fila, num_variables)]
    rango = len(columnas_pivote)

    resultado = {
        "matriz_inicial": aumentada,
        "matriz_final": rref,
        "pasos": pasos,
        "columnas_pivote": columnas_pivote,
        "variables_basicas": columnas_pivote,
        "variables_libres": [c for c in range(num_variables) if c not in columnas_pivote],
        "nombres_variables": nombres_vars,
        "clasificacion": clasificacion,
        "descripcion": descripcion,
        "homogeneo": es_sistema_homogeneo(b),
        "rango": rango,
        "rango_aumentada": rango + (1 if filas_inconsistentes else 0),
        "filas_inconsistentes": filas_inconsistentes,
        "solucion": None,
        "expresiones": None,
        "parametros": {},
        "forma_vectorial": None,
        "solucion_particular": None,
        "verificacion": None,
    }

    if clasificacion == "Sistema consistente determinado":
        solucion = obtener_solucion_unica(rref, columnas_pivote, num_variables)
        resultado["solucion"] = solucion
        resultado["verificacion"] = verificar_solucion(A, b, solucion, nombres_vars)

    elif clasificacion == "Sistema consistente indeterminado":
        expresiones, libres, parametros = obtener_solucion_parametrica(
            rref, columnas_pivote, num_variables
        )
        # Para verificar una solucion infinita elegimos todos los parametros = 0.
        # Asi, las variables libres valen 0 y cada variable basica toma
        # exactamente el termino independiente de su fila pivote.
        particular, direcciones = obtener_forma_vectorial(rref, columnas_pivote, num_variables)

        resultado["expresiones"] = expresiones
        resultado["variables_libres"] = libres
        resultado["parametros"] = parametros
        resultado["forma_vectorial"] = (particular, direcciones)
        resultado["solucion_particular"] = particular
        resultado["verificacion"] = verificar_solucion(A, b, particular, nombres_vars)

    return resultado


def multiplicar_matriz_vector(A, x):
    """Calcula el producto matriz-vector A*x usando fracciones exactas."""
    if not A or not A[0]:
        raise ValueError("La matriz no puede estar vacia.")
    if len(A[0]) != len(x):
        raise ValueError("La cantidad de columnas de A debe coincidir con la dimension del vector.")
    return [sum(A[i][j] * x[j] for j in range(len(x))) for i in range(len(A))]


# -----------------------------------------------------------------------------
# Operaciones con matrices y propiedades teóricas
# -----------------------------------------------------------------------------

def validar_matriz(matriz, nombre="Matriz"):
    """Valida una matriz rectangular no vacía y convierte sus entradas a Fraction."""
    if not isinstance(matriz, list) or not matriz:
        raise ValueError(f"{nombre} debe ser una matriz no vacía.")
    if not all(isinstance(fila, list) and fila for fila in matriz):
        raise ValueError(f"{nombre} debe tener filas no vacías.")
    columnas = len(matriz[0])
    if any(len(fila) != columnas for fila in matriz):
        raise ValueError(f"{nombre} debe ser rectangular: todas sus filas deben tener la misma longitud.")
    try:
        return [[valor if isinstance(valor, Fraction) else Fraction(valor) for valor in fila] for fila in matriz]
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError(f"{nombre} contiene una entrada no numérica válida.") from error


def dimensiones_matriz(matriz):
    matriz = validar_matriz(matriz)
    return len(matriz), len(matriz[0])


def matriz_cero(filas, columnas):
    return [[Fraction(0) for _ in range(columnas)] for _ in range(filas)]


def matriz_identidad(orden):
    if not isinstance(orden, int) or orden < 1:
        raise ValueError("El orden de la identidad debe ser un entero positivo.")
    return [[Fraction(int(i == j)) for j in range(orden)] for i in range(orden)]


def transponer_matriz(A):
    A = validar_matriz(A, "A")
    return [[A[i][j] for i in range(len(A))] for j in range(len(A[0]))]


def sumar_matrices(A, B):
    A, B = validar_matriz(A, "A"), validar_matriz(B, "B")
    da, db = (len(A), len(A[0])), (len(B), len(B[0]))
    if da != db:
        raise ValueError(f"A es {da[0]}×{da[1]} y B es {db[0]}×{db[1]}; A + B no está definida: las dimensiones deben ser iguales.")
    return [[A[i][j] + B[i][j] for j in range(da[1])] for i in range(da[0])]


def restar_matrices(A, B):
    A, B = validar_matriz(A, "A"), validar_matriz(B, "B")
    da, db = (len(A), len(A[0])), (len(B), len(B[0]))
    if da != db:
        raise ValueError(f"A es {da[0]}×{da[1]} y B es {db[0]}×{db[1]}; A - B no está definida: las dimensiones deben ser iguales.")
    return [[A[i][j] - B[i][j] for j in range(da[1])] for i in range(da[0])]


def multiplicar_matriz_escalar(escalar, A):
    A = validar_matriz(A, "A")
    try:
        escalar = escalar if isinstance(escalar, Fraction) else Fraction(escalar)
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError("El escalar debe ser un número válido.") from error
    return [[escalar * valor for valor in fila] for fila in A]


def multiplicar_matrices(A, B):
    A, B = validar_matriz(A, "A"), validar_matriz(B, "B")
    m, n, p, q = len(A), len(A[0]), len(B), len(B[0])
    if n != p:
        raise ValueError(f"A es {m}×{n} y B es {p}×{q}; AB no está definido porque columnas(A) = {n} ≠ filas(B) = {p}.")
    return [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(q)] for i in range(m)]


def _terminos(izquierda, derecha, operador="·"):
    return " + ".join(f"{formatear_numero(a)}{operador}{formatear_numero(b)}" for a, b in zip(izquierda, derecha)) or "0"


def procedimiento_operacion_matrices(A, operacion, B=None, escalar=None):
    """Calcula una operación y devuelve resultado, pasos reales y conclusión académica."""
    A = validar_matriz(A, "A")
    m, n = dimensiones_matriz(A)
    pasos = [f"Datos: A es una matriz {m}×{n}."]
    if operacion in ("suma", "resta", "producto"):
        B = validar_matriz(B, "B")
        p, q = dimensiones_matriz(B)
        pasos.append(f"B es una matriz {p}×{q}.")
    if operacion in ("suma", "resta"):
        if (m, n) != (p, q):
            raise ValueError(f"A es {m}×{n} y B es {p}×{q}. La operación no está definida porque suma y resta exigen dimensiones idénticas.")
        signo, resultado = ("+", sumar_matrices(A, B)) if operacion == "suma" else ("−", restar_matrices(A, B))
        pasos.append(f"Condición cumplida: {m}×{n} = {p}×{q}. Se opera entrada por entrada.")
        for i in range(m):
            pasos.append("Fila " + str(i + 1) + ": " + ", ".join(
                f"({formatear_numero(A[i][j])}) {signo} ({formatear_numero(B[i][j])}) = {formatear_numero(resultado[i][j])}" for j in range(n)))
        return {"resultado": resultado, "pasos": pasos, "conclusion": f"La operación A {signo} B está definida y su resultado es una matriz {m}×{n}."}
    if operacion == "escalar":
        escalar = escalar if isinstance(escalar, Fraction) else Fraction(escalar)
        resultado = multiplicar_matriz_escalar(escalar, A)
        pasos.append(f"Se multiplica cada entrada por el escalar r = {formatear_numero(escalar)}.")
        for i in range(m):
            pasos.append("Fila " + str(i + 1) + ": " + ", ".join(
                f"{formatear_numero(escalar)}({formatear_numero(A[i][j])}) = {formatear_numero(resultado[i][j])}" for j in range(n)))
        return {"resultado": resultado, "pasos": pasos, "conclusion": f"rA está definida y conserva las dimensiones {m}×{n}."}
    if operacion == "transpuesta":
        resultado = transponer_matriz(A)
        pasos += ["Cada fila de A se convierte en una columna de Aᵀ."]
        pasos += [f"Fila {i + 1} de A = columna {i + 1} de Aᵀ: ({', '.join(formatear_numero(x) for x in fila)})." for i, fila in enumerate(A)]
        return {"resultado": resultado, "pasos": pasos, "conclusion": f"Aᵀ tiene dimensiones {n}×{m}; se intercambiaron filas y columnas."}
    if operacion == "producto":
        if n != p:
            raise ValueError(f"A es {m}×{n} y B es {p}×{q}. AB no está definido porque {n} ≠ {p}.")
        resultado = multiplicar_matrices(A, B)
        pasos.append(f"Condición cumplida: columnas(A) = filas(B) = {n}. AB tendrá dimensión {m}×{q}.")
        for i in range(m):
            for j in range(q):
                columna = [B[k][j] for k in range(n)]
                pasos.append(f"(AB){i + 1},{j + 1} = {_terminos(A[i], columna)} = {formatear_numero(resultado[i][j])}.")
        return {"resultado": resultado, "pasos": pasos, "conclusion": f"AB está definida y su resultado es una matriz {m}×{q}."}
    raise ValueError("Operación matricial desconocida.")


def comparar_matrices(izquierda, derecha, nombre_izquierdo="Lado izquierdo", nombre_derecho="Lado derecho"):
    izquierda, derecha = validar_matriz(izquierda, nombre_izquierdo), validar_matriz(derecha, nombre_derecho)
    di, dd = dimensiones_matriz(izquierda), dimensiones_matriz(derecha)
    diferencias = []
    if di == dd:
        for i in range(di[0]):
            for j in range(di[1]):
                if izquierda[i][j] != derecha[i][j]:
                    diferencias.append((i + 1, j + 1, izquierda[i][j], derecha[i][j]))
    else:
        diferencias.append(("dimensiones", di, dd))
    return {"izquierda": izquierda, "derecha": derecha, "dimensiones_izquierda": di,
            "dimensiones_derecha": dd, "coinciden": not diferencias, "diferencias": diferencias,
            "conclusion": ("Las dimensiones y todas las entradas coinciden exactamente." if not diferencias
                           else "La igualdad no se verifica: revise las diferencias indicadas.")}


def verificar_propiedades_transpuesta(A, B=None, escalar=Fraction(1)):
    """Verifica casos particulares; no los presenta como demostración general."""
    A = validar_matriz(A, "A")
    r = escalar if isinstance(escalar, Fraction) else Fraction(escalar)
    propiedades = {}
    propiedades["doble"] = comparar_matrices(transponer_matriz(transponer_matriz(A)), A, "(Aᵀ)ᵀ", "A")
    propiedades["escalar"] = comparar_matrices(transponer_matriz(multiplicar_matriz_escalar(r, A)),
                                                  multiplicar_matriz_escalar(r, transponer_matriz(A)), "(rA)ᵀ", "rAᵀ")
    if B is not None:
        B = validar_matriz(B, "B")
        try:
            propiedades["suma"] = comparar_matrices(transponer_matriz(sumar_matrices(A, B)),
                                                       sumar_matrices(transponer_matriz(A), transponer_matriz(B)),
                                                       "(A+B)ᵀ", "Aᵀ+Bᵀ")
        except ValueError as error:
            propiedades["suma"] = {"definida": False, "error": str(error)}
        try:
            propiedades["producto"] = comparar_matrices(transponer_matriz(multiplicar_matrices(A, B)),
                                                           multiplicar_matrices(transponer_matriz(B), transponer_matriz(A)),
                                                           "(AB)ᵀ", "BᵀAᵀ")
        except ValueError as error:
            propiedades["producto"] = {"definida": False, "error": str(error)}
    return propiedades


def verificar_propiedades_algebraicas(A, B, C, r=Fraction(1), s=Fraction(1)):
    A, B, C = validar_matriz(A, "A"), validar_matriz(B, "B"), validar_matriz(C, "C")
    r, s = Fraction(r), Fraction(s)
    resultados = {}
    def prueba(nombre, izquierda, derecha):
        resultados[nombre] = comparar_matrices(izquierda, derecha, "Lado izquierdo", "Lado derecho")
    if dimensiones_matriz(A) == dimensiones_matriz(B) == dimensiones_matriz(C):
        prueba("asociatividad_suma", sumar_matrices(sumar_matrices(A, B), C), sumar_matrices(A, sumar_matrices(B, C)))
        prueba("conmutatividad_suma", sumar_matrices(A, B), sumar_matrices(B, A))
        prueba("distributividad_escalar", multiplicar_matriz_escalar(r, sumar_matrices(A, B)),
               sumar_matrices(multiplicar_matriz_escalar(r, A), multiplicar_matriz_escalar(r, B)))
    prueba("cero_aditivo", sumar_matrices(A, matriz_cero(*dimensiones_matriz(A))), A)
    prueba("inverso_aditivo", sumar_matrices(A, multiplicar_matriz_escalar(-1, A)), matriz_cero(*dimensiones_matriz(A)))
    prueba("suma_escalares", multiplicar_matriz_escalar(r + s, A),
           sumar_matrices(multiplicar_matriz_escalar(r, A), multiplicar_matriz_escalar(s, A)))
    prueba("producto_escalares", multiplicar_matriz_escalar(r, multiplicar_matriz_escalar(s, A)),
           multiplicar_matriz_escalar(r * s, A))
    prueba("identidad_derecha", multiplicar_matrices(A, matriz_identidad(dimensiones_matriz(A)[1])), A)
    prueba("identidad_izquierda", multiplicar_matrices(matriz_identidad(dimensiones_matriz(A)[0]), A), A)
    try:
        prueba("asociatividad_producto", multiplicar_matrices(multiplicar_matrices(A, B), C), multiplicar_matrices(A, multiplicar_matrices(B, C)))
    except ValueError as error:
        resultados["asociatividad_producto"] = {"definida": False, "error": str(error)}
    try:
        prueba("distributividad_izquierda", multiplicar_matrices(A, sumar_matrices(B, C)),
               sumar_matrices(multiplicar_matrices(A, B), multiplicar_matrices(A, C)))
    except ValueError as error:
        resultados["distributividad_izquierda"] = {"definida": False, "error": str(error)}
    try:
        prueba("distributividad_derecha", multiplicar_matrices(sumar_matrices(A, B), C),
               sumar_matrices(multiplicar_matrices(A, C), multiplicar_matrices(B, C)))
    except ValueError as error:
        resultados["distributividad_derecha"] = {"definida": False, "error": str(error)}
    return resultados


def contraejemplos_matriciales():
    """Contraejemplos exactos, listos para ser explicados y comprobados."""
    A, B = [[1, 2], [0, 1]], [[1, 0], [3, 1]]
    C, D = [[1, 0], [0, 0]], [[0, 0], [1, 0]]
    E, F, G = [[1, 0], [0, 0]], [[1, 0], [0, 0]], [[1, 0], [2, 0]]
    return {
        "no_conmutatividad": {"A": A, "B": B, "AB": multiplicar_matrices(A, B), "BA": multiplicar_matrices(B, A),
            "conclusion": "AB y BA están definidos pero son distintos; el producto matricial no es conmutativo en general."},
        "orden_rectangular": {"A": [[1, 2, 3], [4, 5, 6]], "B": [[1, 0, 1, 0], [0, 1, 0, 1], [1, 1, 0, 0]],
            "AB": multiplicar_matrices([[1, 2, 3], [4, 5, 6]], [[1, 0, 1, 0], [0, 1, 0, 1], [1, 1, 0, 0]]),
            "conclusion": "AB está definido (2×3 por 3×4), pero BA no está definido porque B tiene 4 columnas y A tiene 2 filas."},
        "cancelacion": {"A": E, "B": F, "C": G, "AB": multiplicar_matrices(E, F), "AC": multiplicar_matrices(E, G),
            "conclusion": "AB = AC pero B ≠ C; no se puede cancelar A sin hipótesis adicionales (por ejemplo, A invertible)."},
        "divisores_cero": {"A": C, "B": D, "AB": multiplicar_matrices(C, D),
            "conclusion": "AB = 0 aunque A y B no son matrices cero: existen divisores de cero."},
    }


def ejercicios_matrices():
    """Banco breve y variado de ejercicios; cada uno explicita qué debe justificarse."""
    return [
        {"tema": "Suma con fracciones", "A": [["1/2", "-1"], ["3", "0"]], "B": [["1/3", "2"], ["-3", "5/2"]],
         "consigna": "Calcule A+B entrada por entrada y justifique la compatibilidad de dimensiones."},
        {"tema": "Producto rectangular", "A": [[1, 2, -1], [0, 3, 4]], "B": [[2, 1], [-1, 0], [3, 2]],
         "consigna": "Calcule AB fila por columna e indique la dimensión del resultado."},
        {"tema": "Transpuesta", "A": [[1, -2, 3], ["1/2", 0, 4]],
         "consigna": "Calcule Aᵀ y verifique (Aᵀ)ᵀ=A para este caso particular."},
        {"tema": "Propiedad y contraejemplo", "consigna": "Decida si AB=BA vale siempre. Dé un contraejemplo y compruebe ambos productos."},
        {"tema": "Cancelación", "consigna": "Explique por qué AB=AC no implica B=C sin que A sea invertible."},
    ]


def detalle_producto_matriz_vector(A, x):
    """Explica el producto Ax fila por fila: 'Fila 1: 1(2) + 3(-1) = -1'."""
    lineas = []
    for i, fila in enumerate(A):
        valores = [f"({formatear_numero(v)})" for v in x]
        terminos = [(a, v) for a, v in zip(fila, valores)]
        texto = unir_terminos(terminos) if any(a != 0 for a in fila) else "0"
        total = sum(a * v for a, v in zip(fila, x))
        lineas.append(f"Fila {i + 1}:  {texto} = {formatear_numero(total)}")
    return lineas


def analizar_producto_av(A, v, c, u=None):
    """
    Producto matriz-vector por columnas: si A = [a1 a2 ... an], entonces
    Av = v1*a1 + v2*a2 + ... + vn*an. Tambien comprueba la propiedad A(cv) = c(Av)
    y, si se da un segundo vector u, la propiedad A(u + v) = Au + Av.
    """
    if not A or not A[0]:
        raise ValueError("La matriz A no puede estar vacía.")
    if len(A[0]) != len(v) or (u is not None and len(u) != len(v)):
        raise ValueError("v y u deben tener una componente por cada columna a1…an de A.")
    simbolos = [f"a{j + 1}" for j in range(len(v))]
    columnas = [[fila[j] for fila in A] for j in range(len(v))]
    terminos = [[v[j] * valor for valor in columnas[j]] for j in range(len(v))]
    Av = multiplicar_matriz_vector(A, v)
    cv = [c * valor for valor in v]
    A_cv = multiplicar_matriz_vector(A, cv)
    c_Av = [c * valor for valor in Av]
    datos = {
        "A": A, "v": v, "c": c, "u": u,
        "columnas": columnas,
        "terminos": terminos,
        "combinacion": formatear_combinacion_lineal(v, simbolos),
        "Av": Av,
        "cv": cv, "A_cv": A_cv, "c_Av": c_Av,
        "propiedad": A_cv == c_Av,
        "propiedad_suma": None,
    }
    if u is not None:
        Au = multiplicar_matriz_vector(A, u)
        u_mas_v = [a + b for a, b in zip(u, v)]
        A_u_mas_v = multiplicar_matriz_vector(A, u_mas_v)
        Au_mas_Av = [a + b for a, b in zip(Au, Av)]
        datos.update(
            Au=Au,
            combinacion_u=formatear_combinacion_lineal(u, simbolos),
            u_mas_v=u_mas_v,
            A_u_mas_v=A_u_mas_v,
            Au_mas_Av=Au_mas_Av,
            propiedad_suma=A_u_mas_v == Au_mas_Av,
        )
    return datos


def combinacion_no_trivial(direcciones):
    """
    Construye coeficientes no todos nulos que resuelven Ac = 0, sumando los
    vectores direccion (todos los parametros = 1) y quitando denominadores.
    """
    n = len(direcciones[0][1])
    coeficientes = [sum(vector[i] for _, vector in direcciones) for i in range(n)]
    factor = lcm(*(c.denominator for c in coeficientes))
    return [c * factor for c in coeficientes]


def formatear_combinacion_lineal(coeficientes, simbolos):
    """Ejemplo: [2, -1, 0, 1/2] y [v1..v4] -> '2·v1 - v2 + (1/2)·v4'."""
    return unir_terminos(zip(coeficientes, simbolos), union="·")


def _plural(cantidad, singular, plural):
    return f"{cantidad} {singular if cantidad == 1 else plural}"


def analizar_independencia(A):
    """
    Estudia si las columnas de A (los vectores v1, ..., vp de Rn) son linealmente
    independientes:
    1. Construye el sistema homogeneo [A | 0].
    2. Lo reduce a forma escalonada por filas y cuenta pivotes y variables libres.
    3. Veredicto: L.I. si hay un pivote en cada columna (sin variables libres),
       L.D. en caso contrario.
    Ademas resuelve A·c = 0 por Gauss-Jordan para dar una relacion de dependencia.
    """
    if not A or not A[0]:
        raise ValueError("La matriz no puede estar vacia.")
    num_componentes = len(A)
    num_vectores = len(A[0])
    b = [Fraction(0) for _ in A]
    nombres = obtener_nombres_variables(num_vectores, "c")

    homogenea = crear_matriz_aumentada(A, b)
    escalonada, columnas_pivote, pasos = forma_escalonada(
        homogenea, num_vectores, nombres,
        explicacion_inicial=(
            "Se construye el sistema homogéneo [A | 0]: cada vector es una columna de A "
            "y la última columna es de ceros."
        ),
    )
    num_pivotes = len(columnas_pivote)
    libres = [nombres[c] for c in range(num_vectores) if c not in columnas_pivote]
    independiente = not libres

    resultado = resolver_sistema(A, b, nombres)
    resultado.update(
        matriz_homogenea=homogenea,
        matriz_escalonada=escalonada,
        pasos_gauss_jordan=resultado["pasos"],
        pasos=pasos,
        columnas_pivote=columnas_pivote,
        num_pivotes=num_pivotes,
        num_libres=len(libres),
        nombres_libres=libres,
        independiente=independiente,
    )

    pivotes_texto = _plural(num_pivotes, "pivote", "pivotes")
    if independiente:
        resultado["veredicto"] = "Linealmente Independiente (L.I.)"
        resultado["justificacion"] = (
            f"La forma escalonada tiene {pivotes_texto} y hay {_plural(num_vectores, 'vector', 'vectores')}: "
            f"cada columna tiene pivote, así que no hay variables libres. El sistema homogéneo "
            f"A·c = 0 solo tiene la solución trivial c = 0."
        )
    else:
        resultado["veredicto"] = "Linealmente Dependiente (L.D.)"
        resultado["justificacion"] = (
            f"La forma escalonada tiene {pivotes_texto} para {num_vectores} vectores, así que hay "
            f"{_plural(len(libres), 'variable libre', 'variables libres')} ({', '.join(libres)}). "
            f"El sistema homogéneo A·c = 0 tiene infinitas soluciones, entre ellas soluciones no triviales."
        )
    resultado["teorema"] = (
        "Teorema: v1, …, vp son linealmente independientes si y solo si A·c = 0 tiene únicamente "
        "la solución trivial, es decir, si hay un pivote en cada columna de A (pivotes = p)."
    )

    observaciones = []
    if num_vectores > num_componentes:
        observaciones.append(
            f"Hay {num_vectores} vectores de {num_componentes} componentes: un conjunto con más "
            f"vectores que componentes siempre es linealmente dependiente."
        )
    for j in range(num_vectores):
        if all(A[i][j] == 0 for i in range(num_componentes)):
            observaciones.append(
                f"v{j + 1} es el vector cero; cualquier conjunto que lo contenga es dependiente."
            )
    resultado["observaciones"] = observaciones
    resultado["relacion"] = None
    if not independiente:
        resultado["relacion"] = combinacion_no_trivial(resultado["forma_vectorial"][1])
    return resultado


def informe_independencia(resultado):
    """Lineas de texto con la salida pedida: matriz reducida, pivotes y veredicto."""
    num_vectores = len(resultado["nombres_variables"])
    columnas = ", ".join(str(c + 1) for c in resultado["columnas_pivote"]) or "ninguna"
    lineas = [
        "Sistema homogéneo [A | 0]:",
        matriz_a_texto(resultado["matriz_homogenea"]),
        "",
        "Forma escalonada por filas:",
        matriz_a_texto(resultado["matriz_escalonada"]),
        "",
        f"Número de pivotes: {resultado['num_pivotes']} (columnas pivote: {columnas})",
        f"Variables libres: {resultado['num_libres']}"
        + (f" ({', '.join(resultado['nombres_libres'])})" if resultado["nombres_libres"] else ""),
        "",
        f"Veredicto: {resultado['veredicto']}",
        resultado["justificacion"],
    ]
    if resultado["relacion"] is not None:
        simbolos = [f"v{j + 1}" for j in range(num_vectores)]
        lineas.append(f"Relación de dependencia: {formatear_combinacion_lineal(resultado['relacion'], simbolos)} = 0")
    return lineas


def sistema_aleatorio(m, n, generador=None):
    """Genera un sistema m x n con coeficientes enteros pequenos y una solucion entera."""
    generador = generador or random
    x = [generador.randint(-4, 4) for _ in range(n)]
    A = []
    for _ in range(m):
        fila = [generador.randint(-5, 5) for _ in range(n)]
        if all(v == 0 for v in fila):
            fila[generador.randrange(n)] = 1
        A.append(fila)
    b = [sum(a * xi for a, xi in zip(fila, x)) for fila in A]
    return A, b


def resumen_texto(resultado):
    """Texto plano con el resultado, pensado para copiarlo al portapapeles."""
    nombres = resultado["nombres_variables"]
    lineas = [f"{resultado['clasificacion']}: {resultado['descripcion']}"]
    if resultado["solucion"] is not None:
        lineas += [f"{nombres[i]} = {formatear_numero(v)}" for i, v in enumerate(resultado["solucion"])]
    elif resultado["expresiones"] is not None:
        lineas += [f"{nombres[i]} = {expr}" for i, expr in resultado["expresiones"].items()]
    lineas += ["", "Forma escalonada reducida:", matriz_a_texto(resultado["matriz_final"])]
    return "\n".join(lineas)


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
TEXTO_SOBRE_PRIMARIO = "#04191A"

# Fuentes nativas de cada sistema (Segoe UI/Consolas solo existen en Windows).
if sys.platform == "darwin":
    FAMILIA, FAMILIA_MONO = "Helvetica Neue", "Menlo"
elif sys.platform.startswith("win"):
    FAMILIA, FAMILIA_MONO = "Segoe UI", "Consolas"
else:
    FAMILIA, FAMILIA_MONO = "DejaVu Sans", "DejaVu Sans Mono"

FUENTE_TITULO = (FAMILIA, 26, "bold")
FUENTE_SUBTITULO = (FAMILIA, 14)
FUENTE_SECCION = (FAMILIA, 17, "bold")
FUENTE_NORMAL = (FAMILIA, 13)
FUENTE_NEGRITA = (FAMILIA, 13, "bold")
FUENTE_PEQUENA = (FAMILIA, 11)
FUENTE_PEQUENA_NEGRITA = (FAMILIA, 11, "bold")
FUENTE_DATO = (FAMILIA, 26, "bold")
FUENTE_MONO = (FAMILIA_MONO, 14)

ATAJO_RESOLVER = "⌘ + Enter" if sys.platform == "darwin" else "Ctrl + Enter"

# tipo de paso -> (color de PALETA, nombre visible)
TIPOS_DE_PASO = {
    "inicial": ("texto_3", "Matriz inicial"),
    "intercambio": ("advertencia", "Intercambio"),
    "escalado": ("primario", "Escalamiento"),
    "eliminacion": ("exito", "Eliminación"),
    "final": ("primario", "Resultado"),
}

# Si CustomTkinter no esta instalado, las clases de la interfaz heredan de
# object para que el modulo (y sus pruebas) se pueda importar igual; main()
# muestra entonces un mensaje claro.
_Marco = ctk.CTkFrame if ctk is not None else object
_Ventana = ctk.CTk if ctk is not None else object


# -----------------------------------------------------------------------------
# Utilidades de interfaz
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


def mezclar_colores(color_a, color_b, t):
    """Interpola dos colores #RRGGBB; t=0 devuelve color_a y t=1 color_b."""
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def animar(widget, duracion_ms, al_avanzar, al_terminar=None):
    """
    Ejecuta una animacion de duracion_ms llamando al_avanzar(t) con t entre
    0 y 1 (con desaceleracion suave). Se detiene sola si el widget se destruye.
    """
    inicio = time.perf_counter()

    def paso():
        try:
            if not widget.winfo_exists():
                return
            t = min(1.0, (time.perf_counter() - inicio) * 1000 / duracion_ms)
            al_avanzar(1 - (1 - t) ** 3)
            if t < 1:
                widget.after(15, paso)
            elif al_terminar is not None:
                al_terminar()
        except tk.TclError:
            pass

    paso()


def escala_de(widget):
    """Factor de escala de CustomTkinter (pantallas HiDPI en Windows/Linux)."""
    try:
        return ctk.ScalingTracker.get_widget_scaling(widget)
    except Exception:
        return 1.0


_FUENTES_MEDIDA = {}


def _fuente_medida(widget, pixeles, negrita=False, familia=None):
    """Fuente (cacheada) para medir textos dibujados en un Canvas; por defecto monoespaciada."""
    familia = familia or FAMILIA_MONO
    clave = (str(widget.tk), familia, pixeles, negrita)
    if clave not in _FUENTES_MEDIDA:
        _FUENTES_MEDIDA[clave] = tkfont.Font(
            root=widget, family=familia, size=-pixeles, weight="bold" if negrita else "normal"
        )
    return _FUENTES_MEDIDA[clave]


def es_descendiente(widget, ancestro):
    while widget is not None:
        if widget is ancestro:
            return True
        widget = getattr(widget, "master", None)
    return False


def widget_bajo_puntero(widget):
    try:
        x, y = widget.winfo_pointerxy()
        return widget.winfo_containing(x, y)
    except (tk.TclError, KeyError):
        return None


def efecto_hover(tarjeta, activo=None, normal=None):
    """Ilumina el borde de una tarjeta mientras el puntero esta encima."""
    activo = activo or PALETA["primario"]
    normal = normal or PALETA["borde"]
    estado = {"dentro": False}

    def comprobar():
        try:
            if es_descendiente(widget_bajo_puntero(tarjeta), tarjeta):
                tarjeta.after(150, comprobar)
            else:
                estado["dentro"] = False
                tarjeta.configure(border_color=normal)
        except tk.TclError:
            pass

    def entrar(_evento):
        if not estado["dentro"]:
            estado["dentro"] = True
            tarjeta.configure(border_color=activo)
            tarjeta.after(150, comprobar)

    tarjeta.bind("<Enter>", entrar, add="+")


def destello(tarjeta, color=None, duracion=800):
    """Resalta el borde de una tarjeta y lo devuelve suavemente a su color normal."""
    inicio = resolver_color(color or PALETA["primario"])
    fin = resolver_color(PALETA["borde"])
    animar(tarjeta, duracion, lambda t: tarjeta.configure(border_color=mezclar_colores(inicio, fin, t)))


def cargar_logo(tamano=(96, 96)):
    """Carga el logo de la UAM como CTkImage (con Pillow) o como PhotoImage reducido."""
    if not os.path.exists(RUTA_LOGO):
        return None
    if Image is not None and ctk is not None:
        try:
            imagen = Image.open(RUTA_LOGO).convert("RGBA")
            return ctk.CTkImage(light_image=imagen, dark_image=imagen, size=tamano)
        except Exception as error:
            print("cargar_logo: fallo creando CTkImage con PIL:", error)
    try:
        foto = tk.PhotoImage(file=RUTA_LOGO)
        factor = max(1, foto.width() // tamano[0])
        return foto.subsample(factor, factor)
    except Exception as error:
        print("cargar_logo: no se pudo cargar el logo:", error)
        return None


def etiqueta(parent, texto, fuente=None, color="texto_2", ajustar=None, **kwargs):
    """
    CTkLabel alineado a la izquierda con un color de PALETA (o un color directo).
    ajustar: si se indica, el texto se parte en lineas segun el ancho visible del
    AreaDesplazable que lo contiene (ancho - ajustar, o ajustar(ancho) si es una funcion).
    """
    opciones = {"anchor": "w", "justify": "left"}
    if ajustar is not None:
        opciones["wraplength"] = 200
    opciones.update(kwargs)
    label = ctk.CTkLabel(parent, text=texto, font=fuente or FUENTE_NORMAL,
                         text_color=PALETA.get(color, color), **opciones)
    if ajustar is not None:
        _ajustar_a_area(label, ajustar)
    return label


def _ajustar_a_area(label, margen, minimo=60):
    area = label.master
    while area is not None and not getattr(area, "_es_area_desplazable", False):
        area = getattr(area, "master", None)
    if area is None:
        label.configure(wraplength=520)
        return

    def ajustar():
        try:
            if not label.winfo_exists():
                return
            ancho_px = area.canvas.winfo_width()
            if ancho_px <= 1:
                return
            ancho = ancho_px / escala_de(label)
            objetivo = max(minimo, round(margen(ancho) if callable(margen) else ancho - margen))
            if abs(objetivo - label.cget("wraplength")) > 4:
                label.configure(wraplength=objetivo)
        except tk.TclError:
            pass

    area.registrar_ajuste(ajustar)


def chip(parent, texto, fondo, color_texto, fuente=None):
    """Etiqueta pequena con fondo redondeado."""
    return ctk.CTkLabel(
        parent, text=texto, font=fuente or FUENTE_PEQUENA_NEGRITA,
        fg_color=PALETA.get(fondo, fondo), text_color=PALETA.get(color_texto, color_texto),
        corner_radius=7, height=24, padx=8,
    )


def boton_primario(parent, texto, comando, **kwargs):
    opciones = dict(
        height=40, corner_radius=10, font=FUENTE_NEGRITA,
        fg_color=PALETA["primario"], hover_color=PALETA["primario_hover"],
        text_color=TEXTO_SOBRE_PRIMARIO,
    )
    opciones.update(kwargs)
    return ctk.CTkButton(parent, text=texto, command=comando, **opciones)


def boton_secundario(parent, texto, comando, **kwargs):
    opciones = dict(
        height=36, corner_radius=10, font=FUENTE_NORMAL,
        fg_color=PALETA["secundario"], hover_color=PALETA["secundario_hover"],
        text_color=PALETA["texto"], text_color_disabled=PALETA["texto_3"],
    )
    opciones.update(kwargs)
    return ctk.CTkButton(parent, text=texto, command=comando, **opciones)


def separador_vertical(parent):
    return ctk.CTkFrame(parent, width=1, height=46, fg_color=PALETA["borde"])


def crear_tarjeta(parent, titulo=None, subtitulo=None, fondo=None):
    tarjeta = ctk.CTkFrame(
        parent,
        fg_color=fondo or PALETA["panel"],
        corner_radius=14,
        border_width=1,
        border_color=PALETA["borde"],
    )
    if titulo:
        etiqueta(tarjeta, titulo, FUENTE_SECCION, "texto", ajustar=48).pack(
            anchor="w", padx=18, pady=(16, 2 if subtitulo else 10))
    if subtitulo:
        etiqueta(tarjeta, subtitulo, FUENTE_PEQUENA, "texto_3", ajustar=48).pack(
            anchor="w", padx=18, pady=(0, 10))
    return tarjeta


def tarjeta_seccion(parent, titulo, subtitulo=None):
    """Tarjeta de resultado (fondo panel_2) empaquetada a lo ancho del contenedor."""
    tarjeta = crear_tarjeta(parent, titulo, subtitulo, fondo=PALETA["panel_2"])
    tarjeta.pack(fill="x", padx=2, pady=(0, 12))
    efecto_hover(tarjeta)
    return tarjeta


def placeholder(parent, icono, texto):
    """Mensaje centrado para paneles vacios."""
    marco = ctk.CTkFrame(parent, fg_color="transparent")
    marco.pack(fill="x", pady=(70, 20))
    ctk.CTkLabel(marco, text=icono, font=(FAMILIA, 46, "bold"), text_color=PALETA["borde"]).pack()
    mensaje = ctk.CTkLabel(marco, text=texto, font=FUENTE_NORMAL, text_color=PALETA["texto_3"],
                           wraplength=200, justify="center")
    mensaje.pack(pady=(8, 0))
    _ajustar_a_area(mensaje, lambda ancho: min(420, ancho - 60))
    return marco


# -----------------------------------------------------------------------------
# Dibujo de matrices y vectores (tk.Canvas, rapido aunque haya muchos pasos)
# -----------------------------------------------------------------------------

def _texto_valor(valor):
    if valor is None:
        return "?"
    if isinstance(valor, str):
        return valor
    return formatear_numero(Fraction(valor))


def _corchetes(lienzo, x1, x2, y1, y2, esc, color):
    punta = round(6 * esc)
    grosor = max(1, round(2 * esc))
    lienzo.create_line(x1 + punta, y1, x1, y1, x1, y2, x1 + punta, y2, fill=color, width=grosor)
    lienzo.create_line(x2 - punta, y1, x2, y1, x2, y2, x2 - punta, y2, fill=color, width=grosor)


def _rectangulo_redondeado(lienzo, x1, y1, x2, y2, radio, **kwargs):
    puntos = [
        x1 + radio, y1, x2 - radio, y1, x2, y1, x2, y1 + radio,
        x2, y2 - radio, x2, y2, x2 - radio, y2, x1 + radio, y2,
        x1, y2, x1, y2 - radio, x1, y1 + radio, x1, y1,
    ]
    return lienzo.create_polygon(puntos, smooth=True, **kwargs)


def _dibujar_matriz_en(lienzo, x_base, y_base, matriz, esc, separador=True, filas=(), estilo="relleno",
                       fila_origen=None, pivotes=(), tamano=14):
    """
    Dibuja una matriz (aumentada si separador=True) en un Canvas existente y
    devuelve (ancho, alto).
    - filas: filas modificadas, se resaltan con relleno o con contorno.
    - fila_origen: fila usada como referencia (contorno punteado).
    - pivotes: posiciones (fila, columna) que se encierran en un ovalo.
    Los ceros se muestran atenuados para que se note la forma escalonada.
    """
    px = max(8, round(tamano * esc))
    medir = _fuente_medida(lienzo, px, negrita=True).measure
    textos = [[formatear_numero(v) for v in fila] for fila in matriz]
    num_filas = len(matriz)
    num_cols = len(matriz[0]) if matriz else 0
    relleno = round(10 * esc)
    alto = round(30 * esc)
    margen = round(14 * esc)
    hueco = round(16 * esc) if separador and num_cols > 1 else 0
    y0 = y_base + round(4 * esc)

    anchos = [
        max([medir(textos[i][j]) for i in range(num_filas)] + [medir("00")]) + 2 * relleno
        for j in range(num_cols)
    ]
    xs = []
    x = x_base + margen
    for j in range(num_cols):
        if hueco and j == num_cols - 1:
            x += hueco
        xs.append(x)
        x += anchos[j]
    x_final = x + margen
    ancho_total = x_final - x_base
    alto_total = num_filas * alto + 2 * round(4 * esc)

    color_texto = resolver_color(PALETA["texto"])
    color_tenue = resolver_color(PALETA["texto_3"])
    color_primario = resolver_color(PALETA["primario"])
    radio = round(8 * esc)
    izquierda, derecha = x_base + margen - 5, x_final - margen + 5

    for i in filas:
        y = y0 + i * alto
        if estilo == "relleno":
            _rectangulo_redondeado(lienzo, izquierda, y + 2, derecha, y + alto - 2,
                                   radio, fill=resolver_color(PALETA["borde"]), outline="")
        else:
            _rectangulo_redondeado(lienzo, izquierda, y + 2, derecha, y + alto - 2,
                                   radio, fill="", outline=color_primario, width=max(1, round(esc)))
    if fila_origen is not None:
        y = y0 + fila_origen * alto
        lienzo.create_rectangle(izquierda, y + 3, derecha, y + alto - 3, outline=color_tenue, dash=(4, 3))

    _corchetes(lienzo, x_base + round(6 * esc), x_final - round(6 * esc), y0 + 1,
               y0 + num_filas * alto - 1, esc, color_primario)
    if hueco:
        x_sep = xs[-1] - hueco / 2
        lienzo.create_line(x_sep, y0 + 4, x_sep, y0 + num_filas * alto - 4,
                           fill=color_primario, width=max(1, round(2 * esc)), dash=(4, 3))

    posiciones_pivote = {tuple(p) for p in pivotes}
    for i in range(num_filas):
        resaltada = i in filas and estilo == "relleno"
        cy = y0 + i * alto + alto / 2
        for j in range(num_cols):
            texto = textos[i][j]
            x_derecha = xs[j] + anchos[j] - relleno
            es_pivote = (i, j) in posiciones_pivote
            if es_pivote:
                ancho_texto = medir(texto)
                cx = x_derecha - ancho_texto / 2
                rx = ancho_texto / 2 + round(7 * esc)
                ry = alto / 2 - round(3 * esc)
                lienzo.create_oval(cx - rx, cy - ry, cx + rx, cy + ry,
                                   outline=color_primario, width=max(1, round(2 * esc)))
            if es_pivote:
                color = color_primario
            elif matriz[i][j] == 0:
                color = color_tenue
            else:
                color = color_texto
            negrita = es_pivote or resaltada
            lienzo.create_text(x_derecha, cy, text=texto, anchor="e", fill=color,
                               font=(FAMILIA_MONO, -px, "bold" if negrita else "normal"))
    return ancho_total, alto_total


def dibujar_matriz(parent, matriz, fondo=None, **opciones):
    """Crea un Canvas del tamano justo con la matriz dibujada (ver _dibujar_matriz_en)."""
    lienzo = tk.Canvas(parent, width=10, height=10, bg=resolver_color(fondo or PALETA["panel_2"]),
                       highlightthickness=0, bd=0)
    ancho, alto = _dibujar_matriz_en(lienzo, 0, 0, matriz, escala_de(parent), **opciones)
    lienzo.configure(width=ancho, height=alto)
    return lienzo


def _chip_en(lienzo, x, y, texto, fondo, color, esc):
    """Dibuja una etiqueta redondeada en un Canvas y devuelve (ancho, alto)."""
    px = round(11 * esc)
    ancho = _fuente_medida(lienzo, px, True, FAMILIA).measure(texto) + round(16 * esc)
    alto = round(24 * esc)
    _rectangulo_redondeado(lienzo, x, y, x + ancho, y + alto, round(7 * esc),
                           fill=resolver_color(fondo), outline="")
    lienzo.create_text(x + ancho / 2, y + alto / 2, text=texto, fill=resolver_color(color),
                       font=(FAMILIA, -px, "bold"))
    return ancho, alto


def dibujar_expresion(parent, partes, fondo=None, tamano=14):
    """
    Dibuja una expresion con vectores columna y matrices, por ejemplo
    ['x =', [1, 2], '+ t', [3, 4]]. Un texto se dibuja tal cual, una lista
    de valores como vector columna y una lista de listas como matriz.
    Los valores None se muestran como '?' (entradas aun no validas).
    """
    esc = escala_de(parent)
    k = esc * tamano / 14
    px = max(8, round(tamano * esc))
    medir = _fuente_medida(parent, px).measure
    alto_fila = round(28 * k)
    margen_y = round(6 * k)
    relleno = round(9 * k)
    interior = round(5 * k)
    separacion = round(9 * k)

    def como_matriz(parte):
        if parte and isinstance(parte[0], (list, tuple)):
            return parte
        return [[valor] for valor in parte]

    filas_max = max([len(como_matriz(p)) for p in partes if not isinstance(p, str)] or [1])
    alto = filas_max * alto_fila + 2 * margen_y
    lienzo = tk.Canvas(parent, height=alto, width=10, bg=resolver_color(fondo or PALETA["panel_2"]),
                       highlightthickness=0, bd=0)
    color_texto = resolver_color(PALETA["texto"])
    color_primario = resolver_color(PALETA["primario"])
    color_error = resolver_color(PALETA["error"])
    fuente = (FAMILIA_MONO, -px)
    centro = alto / 2
    x = round(4 * esc)

    for parte in partes:
        if isinstance(parte, str):
            lienzo.create_text(x, centro, text=parte, anchor="w", fill=color_texto, font=fuente)
            x += medir(parte) + separacion
            continue
        matriz = como_matriz(parte)
        textos = [[_texto_valor(v) for v in fila] for fila in matriz]
        num_cols = max(len(fila) for fila in textos)
        anchos = [
            max(medir(fila[j]) for fila in textos if j < len(fila)) + 2 * relleno
            for j in range(num_cols)
        ]
        ancho = sum(anchos) + 2 * interior
        y_arriba = centro - len(matriz) * alto_fila / 2
        y_abajo = centro + len(matriz) * alto_fila / 2
        _corchetes(lienzo, x, x + ancho, y_arriba + 2, y_abajo - 2, esc, color_primario)
        x_col = x + interior
        for j in range(num_cols):
            for i, fila in enumerate(textos):
                if j < len(fila):
                    color = color_error if fila[j] == "?" else color_texto
                    lienzo.create_text(x_col + anchos[j] - relleno, y_arriba + i * alto_fila + alto_fila / 2,
                                       text=fila[j], anchor="e", fill=color, font=fuente)
            x_col += anchos[j]
        x += ancho + separacion

    lienzo.configure(width=x)
    return lienzo


def partes_combinacion(coeficientes, vectores, resultado_final):
    """Partes para dibujar '2·[v1] - [v2] = [w]' omitiendo coeficientes cero."""
    partes = []
    for coeficiente, vector in zip(coeficientes, vectores):
        if coeficiente == 0:
            continue
        numero = "" if abs(coeficiente) == 1 else f"{formatear_coeficiente(coeficiente)}·"
        if partes:
            partes.append(f"{'-' if coeficiente < 0 else '+'} {numero}".rstrip())
        elif coeficiente < 0 or numero:
            partes.append(f"{'-' if coeficiente < 0 else ''}{numero}")
        partes.append(vector)
    if not partes:
        partes = ["0"]
    return partes + ["=", resultado_final]


# -----------------------------------------------------------------------------
# Componentes de interfaz
# -----------------------------------------------------------------------------

class BarraDesplazamiento(tk.Canvas):
    """
    Barra de desplazamiento delgada con forma de pildora (turquesa al pasar
    el mouse). Es mas liviana que CTkScrollbar, que redibuja toda la ventana
    cada vez que cambia de posicion.
    """

    GROSOR = 10

    def __init__(self, parent, orientacion, comando, fondo):
        vertical = orientacion == "vertical"
        super().__init__(parent, bg=resolver_color(fondo), highlightthickness=0, bd=0,
                         width=self.GROSOR if vertical else 20, height=20 if vertical else self.GROSOR)
        self.vertical = vertical
        self.comando = comando
        self.inicio, self.fin = 0.0, 1.0
        self._arrastre = None
        self._pildora = self.create_line(0, 0, 0, 0, width=self.GROSOR - 4, capstyle="round",
                                         fill=resolver_color(PALETA["borde"]))
        self.bind("<Configure>", lambda _e: self._dibujar())
        self.bind("<Enter>", lambda _e: self.itemconfigure(self._pildora, fill=resolver_color(PALETA["primario"])))
        self.bind("<Leave>", lambda _e: self.itemconfigure(self._pildora, fill=resolver_color(PALETA["borde"])))
        self.bind("<Button-1>", self._presionar)
        self.bind("<B1-Motion>", self._arrastrar)
        self.bind("<ButtonRelease-1>", lambda _e: setattr(self, "_arrastre", None))

    def set(self, inicio, fin):
        self.inicio, self.fin = float(inicio), float(fin)
        self._dibujar()

    def _largo(self):
        return max(1, self.winfo_height() if self.vertical else self.winfo_width())

    def _dibujar(self):
        largo = self._largo()
        margen = self.GROSOR / 2
        util = max(1, largo - 2 * margen)
        a = margen + self.inicio * util
        b = max(a + 12, margen + self.fin * util)
        centro = self.GROSOR / 2
        if self.vertical:
            self.coords(self._pildora, centro, a, centro, b)
        else:
            self.coords(self._pildora, a, centro, b, centro)

    def _posicion(self, evento):
        return (evento.y if self.vertical else evento.x) / self._largo()

    def _presionar(self, evento):
        posicion = self._posicion(evento)
        if self.inicio <= posicion <= self.fin:
            self._arrastre = posicion - self.inicio
        else:
            self._arrastre = None
            self.comando("scroll", -1 if posicion < self.inicio else 1, "pages")

    def _arrastrar(self, evento):
        if self._arrastre is not None:
            self.comando("moveto", self._posicion(evento) - self._arrastre)


class AreaDesplazable(_Marco):
    """
    Contenedor con desplazamiento vertical y horizontal. Las barras solo
    aparecen cuando el contenido no cabe. El contenido se agrega en .interior.
    """

    def __init__(self, parent, fondo, **kwargs):
        super().__init__(parent, fg_color="transparent", corner_radius=0, **kwargs)
        self._es_area_desplazable = True
        self._token = 0
        color_fondo = resolver_color(fondo)

        self.canvas = tk.Canvas(self, bg=color_fondo, highlightthickness=0, bd=0, width=100, height=100,
                                xscrollincrement=1, yscrollincrement=1)
        self.barra_y = BarraDesplazamiento(self, "vertical", self.canvas.yview, fondo)
        self.barra_x = BarraDesplazamiento(self, "horizontal", self.canvas.xview, fondo)
        self.canvas.configure(
            yscrollcommand=lambda a, b: self._ajustar_barra(self.barra_y, a, b),
            xscrollcommand=lambda a, b: self._ajustar_barra(self.barra_x, a, b),
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.barra_y.grid(row=0, column=1, sticky="ns", padx=(4, 0))
        self.barra_x.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.barra_y.grid_remove()
        self.barra_x.grid_remove()
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.interior = tk.Frame(self.canvas, bg=color_fondo, bd=0, highlightthickness=0)
        self._ventana = self.canvas.create_window(0, 0, window=self.interior, anchor="nw")
        self._ajustes = []
        self.interior.bind("<Configure>", self._actualizar)
        self.canvas.bind("<Configure>", self._al_redimensionar)

    def _al_redimensionar(self, _evento=None):
        self._actualizar()
        for ajuste in list(self._ajustes):
            ajuste()

    def registrar_ajuste(self, funcion):
        """Registra una funcion que se llama cuando cambia el ancho visible (textos adaptables)."""
        self._ajustes.append(funcion)
        funcion()

    @staticmethod
    def _ajustar_barra(barra, inicio, fin):
        visible = float(inicio) > 0.0 or float(fin) < 1.0
        if visible != bool(barra.winfo_manager()):
            if visible:
                barra.grid()
            else:
                barra.grid_remove()
        barra.set(inicio, fin)

    def _actualizar(self, _evento=None):
        ancho = max(self.canvas.winfo_width(), self.interior.winfo_reqwidth())
        self.canvas.itemconfigure(self._ventana, width=ancho)
        self.canvas.configure(scrollregion=(0, 0, ancho, self.interior.winfo_reqheight()))

    def puede_desplazar(self, horizontal=False):
        vista = self.canvas.xview() if horizontal else self.canvas.yview()
        return vista != (0.0, 1.0)

    def desplazar(self, pixeles, horizontal=False):
        pixeles = int(pixeles)
        if pixeles:
            (self.canvas.xview_scroll if horizontal else self.canvas.yview_scroll)(pixeles, "units")

    def al_inicio(self):
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def limpiar(self):
        self._token += 1
        self._ajustes = []
        for hijo in self.interior.winfo_children():
            hijo.destroy()

    def llenar(self, constructores, retardo=45):
        """
        Reemplaza el contenido llamando a cada constructor(interior) con un
        pequeno retardo entre uno y otro: las tarjetas aparecen en cascada y la
        ventana sigue respondiendo aunque haya muchos pasos.
        """
        self.limpiar()
        self.al_inicio()
        token = self._token
        constructores = list(constructores)

        def siguiente(indice):
            if token != self._token or indice >= len(constructores):
                return
            try:
                constructores[indice](self.interior)
            except tk.TclError:
                return
            self.after(retardo if indice < 25 else 1, lambda: siguiente(indice + 1))

        siguiente(0)


def instalar_desplazamiento(raiz):
    """
    Un solo manejador global de rueda del mouse/trackpad: desplaza el
    AreaDesplazable mas cercano bajo el puntero. Funciona en Windows, macOS y Linux.
    """

    def buscar_area(evento, horizontal):
        try:
            widget = raiz.winfo_containing(evento.x_root, evento.y_root)
        except (KeyError, tk.TclError):
            return None
        while widget is not None:
            if getattr(widget, "_es_area_desplazable", False) and widget.puede_desplazar(horizontal):
                return widget
            widget = getattr(widget, "master", None)
        return None

    def mover(evento, pixeles, horizontal):
        area = buscar_area(evento, horizontal)
        if area is not None:
            area.desplazar(pixeles, horizontal)

    def rueda(evento):
        delta = evento.delta
        # Windows (y Tk 9) usan multiplos de 120; macOS con Tk 8.6 entrega deltas pequenos.
        pixeles = -delta / 120 * 60 if abs(delta) >= 120 else -delta * 8
        mover(evento, pixeles, bool(evento.state & 0x1))

    def tactil(evento):
        try:
            dx, dy = (float(v) for v in raiz.tk.splitlist(raiz.tk.call("tk::PreciseScrollDeltas", evento.delta)))
        except (tk.TclError, ValueError):
            return
        if dy:
            mover(evento, -dy, False)
        if dx:
            mover(evento, -dx, True)

    raiz.bind_all("<MouseWheel>", rueda, add="+")
    raiz.bind_all("<Shift-MouseWheel>", rueda, add="+")
    if sys.platform.startswith("linux"):
        raiz.bind_all("<Button-4>", lambda e: mover(e, -60, bool(e.state & 0x1)), add="+")
        raiz.bind_all("<Button-5>", lambda e: mover(e, 60, bool(e.state & 0x1)), add="+")
    try:
        raiz.bind_all("<TouchpadScroll>", tactil, add="+")  # Tk 9 (trackpads)
    except tk.TclError:
        pass


class Contador(_Marco):
    """Selector numerico  −  3  +  con limites."""

    def __init__(self, parent, texto, valor, minimo, maximo, al_cambiar=None):
        super().__init__(parent, fg_color="transparent")
        self.minimo = minimo
        self.maximo = maximo
        self.valor = valor
        self.al_cambiar = al_cambiar

        etiqueta(self, texto, FUENTE_PEQUENA_NEGRITA, "texto_3").pack(anchor="w", pady=(0, 4))
        caja = ctk.CTkFrame(self, fg_color=PALETA["entrada"], corner_radius=10,
                            border_width=1, border_color=PALETA["borde"])
        caja.pack(anchor="w")
        opciones = dict(width=30, height=28, corner_radius=8, fg_color="transparent",
                        hover_color=PALETA["secundario_hover"], text_color=PALETA["primario"],
                        text_color_disabled=PALETA["borde"], font=(FAMILIA, 17, "bold"))
        self.boton_menos = ctk.CTkButton(caja, text="−", command=lambda: self.cambiar(-1), **opciones)
        self.boton_menos.pack(side="left", padx=(3, 0), pady=3)
        self.etiqueta_valor = ctk.CTkLabel(caja, text=str(valor), width=34, font=FUENTE_NEGRITA,
                                           text_color=PALETA["texto"])
        self.etiqueta_valor.pack(side="left")
        self.boton_mas = ctk.CTkButton(caja, text="+", command=lambda: self.cambiar(1), **opciones)
        self.boton_mas.pack(side="left", padx=(0, 3), pady=3)
        self._actualizar_botones()

    def get(self):
        return self.valor

    def set(self, valor, notificar=False):
        valor = max(self.minimo, min(self.maximo, int(valor)))
        cambio = valor != self.valor
        self.valor = valor
        self.etiqueta_valor.configure(text=str(valor))
        self._actualizar_botones()
        if cambio:
            inicio = resolver_color(PALETA["primario"])
            fin = resolver_color(PALETA["texto"])
            animar(self.etiqueta_valor, 450,
                   lambda t: self.etiqueta_valor.configure(text_color=mezclar_colores(inicio, fin, t)))
        if cambio and notificar and self.al_cambiar is not None:
            self.al_cambiar(valor)

    def cambiar(self, delta):
        self.set(self.valor + delta, notificar=True)

    def _actualizar_botones(self):
        self.boton_menos.configure(state="normal" if self.valor > self.minimo else "disabled")
        self.boton_mas.configure(state="normal" if self.valor < self.maximo else "disabled")


TECLAS_SIN_CAMBIO = {"Return", "KP_Enter", "Up", "Down", "Left", "Right", "Tab", "Shift_L", "Shift_R",
                     "Control_L", "Control_R", "Meta_L", "Meta_R", "Alt_L", "Alt_R", "Escape"}


class MatrizEntrada(_Marco):
    """
    Rejilla de casillas para capturar matrices.
    - Valida cada casilla mientras se escribe (borde rojo si no es un numero).
    - Enter avanza a la siguiente casilla; flechas arriba/abajo cambian de fila.
    - Al cambiar el tamano conserva los valores ya escritos.
    """

    ANCHO_CELDA = 60

    def __init__(self, parent, al_cambiar=None):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.al_cambiar = al_cambiar
        self.celdas = []
        self.separador = None
        self.encabezados = []
        self.encabezados_fila = None
        self._tarea = None

    def configurar(self, filas, columnas, encabezados, encabezados_fila=None, separador=None, valores=None):
        anteriores = self.textos()
        separador_anterior = self.separador
        for hijo in self.winfo_children():
            hijo.destroy()
        self.celdas = []
        self.separador = separador
        self.encabezados = list(encabezados)
        self.encabezados_fila = list(encabezados_fila) if encabezados_fila else None

        desplazamiento = 1 if encabezados_fila else 0

        def columna_grid(j):
            return desplazamiento + j + (1 if separador is not None and j >= separador else 0)

        for j, texto in enumerate(encabezados):
            ctk.CTkLabel(self, text=texto, font=FUENTE_PEQUENA_NEGRITA,
                         text_color=PALETA["primario"]).grid(row=0, column=columna_grid(j), pady=(0, 4))

        for i in range(filas):
            if encabezados_fila:
                ctk.CTkLabel(self, text=encabezados_fila[i], font=FUENTE_PEQUENA_NEGRITA, width=30,
                             text_color=PALETA["texto_3"]).grid(row=i + 1, column=0, padx=(0, 6))
            fila = []
            for j in range(columnas):
                entrada = ctk.CTkEntry(
                    self, width=self.ANCHO_CELDA, height=36, justify="center", font=FUENTE_MONO,
                    corner_radius=8, border_width=2, fg_color=PALETA["entrada"],
                    border_color=PALETA["borde"], text_color=PALETA["texto"],
                )
                entrada.grid(row=i + 1, column=columna_grid(j), padx=2, pady=3)
                entrada.insert(0, self._valor_inicial(anteriores, separador_anterior, i, j, valores))
                self._enlazar(entrada, i, j)
                fila.append(entrada)
            self.celdas.append(fila)

        if separador is not None and filas:
            ctk.CTkFrame(self, width=3, fg_color=PALETA["primario"], corner_radius=2).grid(
                row=1, column=desplazamiento + separador, rowspan=filas, sticky="ns", padx=8, pady=6)

        for fila in self.celdas:
            for entrada in fila:
                self._validar(entrada)

    def _valor_inicial(self, anteriores, separador_anterior, i, j, valores):
        if valores is not None:
            if i < len(valores) and j < len(valores[i]):
                valor = valores[i][j]
                return formatear_numero(valor) if isinstance(valor, Fraction) else str(valor)
            return "0"
        if i >= len(anteriores):
            return "0"
        fila = anteriores[i]
        # Con matriz aumentada se conservan por separado el bloque A y la columna b.
        if self.separador is not None and separador_anterior is not None:
            if j >= self.separador:
                k = separador_anterior + (j - self.separador)
            elif j < separador_anterior:
                k = j
            else:
                return "0"
        else:
            k = j
        return fila[k] if k < len(fila) else "0"

    def _enlazar(self, entrada, i, j):
        entrada.bind("<KeyRelease>", lambda e: self._al_escribir(entrada, e))
        entrada.bind("<FocusIn>", lambda e: self._al_enfocar(entrada))
        entrada.bind("<FocusOut>", lambda e: self._validar(entrada, enfocada=False))
        entrada.bind("<Return>", lambda e: self._mover(e, i, j, siguiente=True))
        entrada.bind("<KP_Enter>", lambda e: self._mover(e, i, j, siguiente=True))
        entrada.bind("<Down>", lambda e: self._mover(e, i + 1, j))
        entrada.bind("<Up>", lambda e: self._mover(e, i - 1, j))

    def _mover(self, evento, i, j, siguiente=False):
        # Ctrl+Enter (o Cmd+Enter en macOS) se deja pasar para resolver.
        if evento.state & 0x4 or (sys.platform == "darwin" and evento.state & 0x8):
            return None
        if siguiente:
            j += 1
            if j >= len(self.celdas[0]):
                j = 0
                i = (i + 1) % len(self.celdas)
        if 0 <= i < len(self.celdas):
            self.celdas[i][j].focus_set()
        return "break"

    def _al_enfocar(self, entrada):
        self._validar(entrada, enfocada=True)

        def seleccionar():
            try:
                entrada.select_range(0, "end")
                entrada.icursor("end")
            except tk.TclError:
                pass

        entrada.after(1, seleccionar)

    def _al_escribir(self, entrada, evento):
        if evento.keysym in TECLAS_SIN_CAMBIO:
            return
        self._validar(entrada, enfocada=True)
        if self._tarea is not None:
            self.after_cancel(self._tarea)
        self._tarea = self.after(150, self._notificar)

    def _notificar(self):
        self._tarea = None
        if self.al_cambiar is not None:
            self.al_cambiar()

    def _validar(self, entrada, enfocada=False):
        try:
            convertir_numero(entrada.get())
            valido = True
        except ValueError:
            valido = False
        if not valido:
            color = PALETA["error"]
        else:
            color = PALETA["primario"] if enfocada else PALETA["borde"]
        entrada.configure(border_color=color)
        return valido

    def textos(self):
        return [[entrada.get() for entrada in fila] for fila in self.celdas]

    def valores(self):
        """Lee la matriz como Fraction; si una casilla es invalida la enfoca y explica el error."""
        matriz = []
        for i, fila in enumerate(self.celdas):
            valores_fila = []
            for j, entrada in enumerate(fila):
                try:
                    valores_fila.append(convertir_numero(entrada.get()))
                except ValueError as error:
                    entrada.configure(border_color=PALETA["error"])
                    entrada.focus_set()
                    nombre_fila = self.encabezados_fila[i] if self.encabezados_fila else f"fila {i + 1}"
                    nombre_col = self.encabezados[j] if j < len(self.encabezados) else f"columna {j + 1}"
                    raise ValueError(f"Casilla {nombre_fila}, {nombre_col}: {error}") from None
            matriz.append(valores_fila)
        return matriz

    def limpiar(self):
        for fila in self.celdas:
            for entrada in fila:
                entrada.delete(0, "end")
                entrada.insert(0, "0")
                self._validar(entrada)
        self._notificar()


class TarjetaPaso(tk.Canvas):
    """
    Tarjeta de un paso de Gauss-Jordan: operacion, explicacion y matriz con la
    fila modificada resaltada. En modo detallado muestra la matriz antes y despues.

    Todo se dibuja en un solo Canvas (en vez de ~15 widgets por tarjeta) para
    que un sistema grande, con cien pasos o mas, se muestre y desplace con fluidez.
    """

    def __init__(self, parent, pasos, indice, detallado=False, fondo=None):
        super().__init__(parent, bg=resolver_color(fondo or PALETA["panel"]), highlightthickness=0, bd=0,
                         height=10)
        self.pasos = pasos
        self.indice = indice
        self.detallado = detallado
        self._esc = escala_de(parent)
        self._borde = None
        self._ancho_dibujado = None
        self.configure(width=self._dibujar(None))
        self.bind("<Configure>", self._al_configurar)
        self.bind("<Enter>", lambda _e: self._color_borde(PALETA["primario"]))
        self.bind("<Leave>", lambda _e: self._color_borde(PALETA["borde"]))

    def _al_configurar(self, evento):
        if evento.width > 1 and evento.width != self._ancho_dibujado:
            self._ancho_dibujado = evento.width
            self._dibujar(evento.width)

    def _color_borde(self, color):
        if self._borde is not None:
            self.itemconfigure(self._borde, outline=resolver_color(color))

    def destello(self):
        inicio = resolver_color(PALETA["primario"])
        fin = resolver_color(PALETA["borde"])
        animar(self, 800, lambda t: self._color_borde(mezclar_colores(inicio, fin, t)))

    def _dibujar(self, ancho):
        """Dibuja la tarjeta con el ancho dado (None = ancho natural) y devuelve el ancho natural."""
        self.delete("all")
        esc = self._esc
        paso = self.pasos[self.indice]
        tipo = paso.get("tipo", "")
        clave_color, nombre_tipo = TIPOS_DE_PASO.get(tipo, ("primario", "Operación"))
        color_texto = resolver_color(PALETA["texto"])
        color_tenue = resolver_color(PALETA["texto_3"])
        margen = round(16 * esc)

        if tipo == "inicial":
            titulo = "Inicio"
        elif tipo == "final":
            titulo = "Final"
        else:
            titulo = f"Paso {self.indice}"
        x, y = margen, round(14 * esc)
        ancho_chip, alto_chip = _chip_en(self, x, y, titulo, PALETA["primario"], TEXTO_SOBRE_PRIMARIO, esc)
        x += ancho_chip + round(8 * esc)
        ancho_chip, _ = _chip_en(self, x, y, nombre_tipo, PALETA["panel"], PALETA[clave_color], esc)
        x += ancho_chip + round(12 * esc)
        if tipo not in ("inicial", "final"):
            px = round(14 * esc)
            self.create_text(x, y + alto_chip / 2, text=paso["operacion"], anchor="w", fill=color_texto,
                             font=(FAMILIA_MONO, -px, "bold"))
            x += _fuente_medida(self, px, True).measure(paso["operacion"])
        ancho_contenido = x
        y += alto_chip + round(10 * esc)

        ancho_texto = (ancho - 2 * margen) if ancho else round(520 * esc)
        texto = self.create_text(margen, y, text=paso["explicacion"], anchor="nw", width=max(200, ancho_texto),
                                 fill=resolver_color(PALETA["texto_2"]), font=(FAMILIA, -round(13 * esc)))
        y = self.bbox(texto)[3] + round(12 * esc)

        filas = paso.get("filas", [])
        pivotes = paso.get("pivotes", [])
        origen = paso.get("fila_origen")
        x_matriz = margen - round(8 * esc)
        if self.detallado and self.indice > 0 and tipo != "final":
            fuente_etiqueta = (FAMILIA, -round(11 * esc), "bold")
            self.create_text(margen, y, text="ANTES", anchor="nw", fill=color_tenue, font=fuente_etiqueta)
            y_matriz = y + round(18 * esc)
            ancho_1, alto_1 = _dibujar_matriz_en(self, x_matriz, y_matriz, self.pasos[self.indice - 1]["matriz"],
                                                 esc, filas=filas, estilo="contorno", fila_origen=origen)
            x_flecha = x_matriz + ancho_1 + round(10 * esc)
            self.create_text(x_flecha, y_matriz + alto_1 / 2, text="→", anchor="w",
                             fill=resolver_color(PALETA["primario"]), font=(FAMILIA, -round(26 * esc), "bold"))
            x_despues = x_flecha + round(40 * esc)
            self.create_text(x_despues + round(8 * esc), y, text="DESPUÉS", anchor="nw", fill=color_tenue,
                             font=fuente_etiqueta)
            ancho_2, alto_2 = _dibujar_matriz_en(self, x_despues, y_matriz, paso["matriz"], esc, filas=filas,
                                                 fila_origen=origen, pivotes=pivotes)
            ancho_contenido = max(ancho_contenido, x_despues + ancho_2)
            y = y_matriz + max(alto_1, alto_2)
        else:
            ancho_1, alto_1 = _dibujar_matriz_en(self, x_matriz, y, paso["matriz"], esc, filas=filas,
                                                 fila_origen=origen, pivotes=pivotes)
            ancho_contenido = max(ancho_contenido, x_matriz + ancho_1)
            y += alto_1
        y += margen

        natural = max(ancho_contenido + margen, round(300 * esc))
        ancho_final = ancho or natural
        self._borde = _rectangulo_redondeado(
            self, 1, 1, ancho_final - 1, y - 1, round(12 * esc),
            fill=resolver_color(PALETA["panel_2"]), outline=resolver_color(PALETA["borde"]),
        )
        self.tag_lower(self._borde)
        if int(float(self.cget("height"))) != round(y):
            self.configure(height=round(y))
        return natural


class PanelPasos(_Marco):
    """Muestra el procedimiento completo (en cascada) o paso a paso con reproduccion automatica."""

    def __init__(self, parent, fondo, texto_vacio):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.texto_vacio = texto_vacio
        self.pasos = []
        self.indice = 0
        self._tarea_reproducir = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=0, column=0, sticky="ew", padx=4, pady=(2, 8))
        self.selector = ctk.CTkSegmentedButton(
            barra, values=["Todos", "Paso a paso"], command=self._cambiar_modo,
            font=FUENTE_PEQUENA_NEGRITA, height=30,
            fg_color=PALETA["panel_2"], selected_color=PALETA["primario"],
            selected_hover_color=PALETA["primario_hover"], unselected_color=PALETA["panel_2"],
            unselected_hover_color=PALETA["secundario_hover"], text_color=PALETA["texto"],
        )
        self.selector.set("Todos")
        self.selector.pack(side="left")

        self.controles = ctk.CTkFrame(barra, fg_color="transparent")
        self.boton_anterior = boton_secundario(self.controles, "◀", lambda: self.ir_a(self.indice - 1),
                                               width=34, height=30)
        self.boton_anterior.pack(side="left")
        self.etiqueta_posicion = ctk.CTkLabel(self.controles, text="", width=64, font=FUENTE_PEQUENA_NEGRITA,
                                              text_color=PALETA["texto"])
        self.etiqueta_posicion.pack(side="left")
        self.boton_siguiente = boton_secundario(self.controles, "▶", lambda: self.ir_a(self.indice + 1),
                                                width=34, height=30)
        self.boton_siguiente.pack(side="left")
        self.boton_reproducir = boton_secundario(self.controles, "▶  Reproducir", self.alternar_reproduccion,
                                                 width=124, height=30, font=FUENTE_PEQUENA_NEGRITA)
        self.boton_reproducir.pack(side="left", padx=(10, 0))

        self.progreso = ctk.CTkProgressBar(self, height=6, corner_radius=3,
                                           progress_color=PALETA["primario"], fg_color=PALETA["panel_2"])
        self.progreso.set(0)

        self.area = AreaDesplazable(self, fondo)
        self.area.grid(row=2, column=0, sticky="nsew")
        self.mostrar_placeholder()

    def mostrar_placeholder(self, texto=None):
        self.detener()
        self.pasos = []
        self.controles.pack_forget()
        self.progreso.grid_remove()
        self.area.llenar([lambda p: placeholder(p, "☰", texto or self.texto_vacio)])

    def mostrar_pasos(self, pasos):
        self.detener()
        self.pasos = list(pasos)
        self.indice = 0
        self._renderizar()

    def _cambiar_modo(self, _valor=None):
        self.detener()
        if self.pasos:
            self._renderizar()

    def _renderizar(self):
        if self.selector.get() == "Paso a paso":
            self.controles.pack(side="right")
            self.progreso.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 10))
            self._renderizar_actual()
        else:
            self.controles.pack_forget()
            self.progreso.grid_remove()
            self.area.llenar([
                lambda p, i=i: TarjetaPaso(p, self.pasos, i).pack(fill="x", padx=2, pady=(0, 12))
                for i in range(len(self.pasos))
            ])

    def _renderizar_actual(self):
        total = len(self.pasos)
        self.etiqueta_posicion.configure(text=f"{self.indice + 1} / {total}")
        self.boton_anterior.configure(state="normal" if self.indice > 0 else "disabled")
        self.boton_siguiente.configure(state="normal" if self.indice < total - 1 else "disabled")
        objetivo = (self.indice + 1) / total
        inicio = self.progreso.get()
        animar(self.progreso, 300, lambda t: self.progreso.set(inicio + (objetivo - inicio) * t))

        def construir(parent):
            tarjeta = TarjetaPaso(parent, self.pasos, self.indice, detallado=True)
            tarjeta.pack(fill="x", padx=2, pady=(0, 12))
            tarjeta.destello()

        self.area.llenar([construir])

    def ir_a(self, indice):
        if not self.pasos:
            return
        self.indice = max(0, min(len(self.pasos) - 1, indice))
        self._renderizar_actual()

    def alternar_reproduccion(self):
        if self._tarea_reproducir is not None:
            self.detener()
            return
        if self.indice >= len(self.pasos) - 1:
            self.ir_a(0)
        self.boton_reproducir.configure(text="⏸  Pausar")
        self._tarea_reproducir = self.after(1400, self._avanzar)

    def _avanzar(self):
        self._tarea_reproducir = None
        self.ir_a(self.indice + 1)
        if self.indice < len(self.pasos) - 1:
            self._tarea_reproducir = self.after(1400, self._avanzar)
        else:
            self.detener()

    def detener(self):
        if self._tarea_reproducir is not None:
            self.after_cancel(self._tarea_reproducir)
            self._tarea_reproducir = None
        self.boton_reproducir.configure(text="▶  Reproducir")


class SeccionPlegable(_Marco):
    """Seccion que se abre/cierra al hacer clic en su cabecera; el cuerpo se crea al abrirla."""

    def __init__(self, parent, titulo, detalle, correcto, construir, abierto=False):
        super().__init__(parent, fg_color=PALETA["entrada"], corner_radius=10,
                         border_width=1, border_color=PALETA["borde"])
        self._construir = construir
        self._cuerpo = None
        self.abierto = False

        cabecera = ctk.CTkFrame(self, fg_color="transparent")
        cabecera.pack(fill="x", padx=10, pady=6)
        self._flecha = etiqueta(cabecera, "▸", FUENTE_NEGRITA, "primario", width=16)
        self._flecha.pack(side="left")
        etiqueta(cabecera, titulo, FUENTE_PEQUENA_NEGRITA, "texto").pack(side="left", padx=(4, 10))
        etiqueta(cabecera, detalle, FUENTE_MONO, "texto_2").pack(side="left")
        estado = "✓ Se cumple" if correcto else "✕ No se cumple"
        etiqueta(cabecera, estado, FUENTE_PEQUENA_NEGRITA, "exito" if correcto else "error").pack(
            side="right", padx=(10, 4))

        for widget in (cabecera, *cabecera.winfo_children()):
            widget.bind("<Button-1>", self.alternar)
            try:
                widget.configure(cursor="hand2")
            except (ValueError, tk.TclError):
                pass
        if abierto:
            self.alternar()

    def alternar(self, _evento=None):
        if self._cuerpo is None:
            self._cuerpo = ctk.CTkFrame(self, fg_color="transparent")
            self._construir(self._cuerpo)
        if self.abierto:
            self._cuerpo.pack_forget()
            self._flecha.configure(text="▸")
        else:
            self._cuerpo.pack(fill="x", padx=16, pady=(0, 10))
            self._flecha.configure(text="▾")
        self.abierto = not self.abierto


class Notificador:
    """Notificaciones flotantes que entran deslizandose por la esquina inferior derecha."""

    COLORES = {"exito": "exito", "error": "error", "info": "primario", "aviso": "advertencia"}
    ICONOS = {"exito": "✓", "error": "✕", "info": "i", "aviso": "!"}

    def __init__(self, ventana):
        self.ventana = ventana
        self.actual = None
        self._tarea = None

    def mostrar(self, texto, tipo="info", duracion=3400):
        self.cerrar(inmediato=True)
        color = PALETA[self.COLORES.get(tipo, "primario")]
        marco = ctk.CTkFrame(self.ventana, fg_color=PALETA["panel_2"], corner_radius=12,
                             border_width=2, border_color=color)
        ctk.CTkLabel(marco, text=self.ICONOS.get(tipo, "i"), width=28, height=28, corner_radius=14,
                     fg_color=color, text_color=TEXTO_SOBRE_PRIMARIO,
                     font=(FAMILIA, 14, "bold")).pack(side="left", padx=(14, 10), pady=12)
        etiqueta(marco, texto, FUENTE_NORMAL, "texto", wraplength=360).pack(side="left", padx=(0, 18), pady=12)
        for widget in (marco, *marco.winfo_children()):
            widget.bind("<Button-1>", lambda _e: self.cerrar())

        self.actual = marco
        inicio, fin = 90, -24
        marco.place(relx=1.0, rely=1.0, x=-24, y=inicio, anchor="se")
        marco.lift()
        animar(marco, 320, lambda t: marco.place(y=inicio + (fin - inicio) * t))
        self._tarea = self.ventana.after(duracion, self.cerrar)

    def cerrar(self, inmediato=False):
        if self._tarea is not None:
            self.ventana.after_cancel(self._tarea)
            self._tarea = None
        marco, self.actual = self.actual, None
        if marco is None:
            return
        if inmediato:
            marco.destroy()
        else:
            animar(marco, 240, lambda t: marco.place(y=-24 + 120 * t), marco.destroy)


class ItemNavegacion(_Marco):
    """Elemento del menu lateral con icono, texto y estados hover/activo."""

    def __init__(self, parent, icono, texto, comando):
        super().__init__(parent, fg_color="transparent", corner_radius=10, height=42)
        self.activo = False
        self.icono = ctk.CTkLabel(self, text=icono, width=26, font=(FAMILIA, 16, "bold"),
                                  text_color=PALETA["texto_3"])
        self.icono.pack(side="left", padx=(16, 8), pady=8)
        self.texto = ctk.CTkLabel(self, text=texto, font=FUENTE_NORMAL, text_color=PALETA["texto_2"], anchor="w")
        self.texto.pack(side="left", fill="x", expand=True)
        for widget in (self, self.icono, self.texto):
            widget.bind("<Button-1>", lambda _e: comando())
            widget.bind("<Enter>", self._entrar)
            widget.bind("<Leave>", self._salir)
        for widget in (self.icono, self.texto):
            widget.configure(cursor="hand2")

    def activar(self, activo):
        self.activo = activo
        self.configure(fg_color=PALETA["secundario"] if activo else "transparent")
        self.icono.configure(text_color=PALETA["primario"] if activo else PALETA["texto_3"])
        self.texto.configure(text_color=PALETA["texto"] if activo else PALETA["texto_2"],
                             font=FUENTE_NEGRITA if activo else FUENTE_NORMAL)

    def _entrar(self, _evento):
        if not self.activo:
            self.configure(fg_color=PALETA["panel_2"])

    def _salir(self, _evento):
        if not self.activo and not es_descendiente(widget_bajo_puntero(self), self):
            self.configure(fg_color="transparent")


# -----------------------------------------------------------------------------
# Bloques para mostrar resultados
# -----------------------------------------------------------------------------

def tarjeta_estado(parent, titulo, descripcion, color, icono):
    """Tarjeta principal del resultado con icono de estado y un brillo inicial."""
    tarjeta = ctk.CTkFrame(parent, fg_color=PALETA["panel_2"], corner_radius=14,
                           border_width=2, border_color=color)
    tarjeta.pack(fill="x", padx=2, pady=(2, 12))
    ctk.CTkLabel(tarjeta, text=icono, width=46, height=46, corner_radius=23, fg_color=color,
                 text_color=TEXTO_SOBRE_PRIMARIO, font=(FAMILIA, 22, "bold")).pack(side="left", padx=16, pady=16)
    textos = ctk.CTkFrame(tarjeta, fg_color="transparent")
    textos.pack(side="left", fill="x", expand=True, pady=14, padx=(0, 16))
    etiqueta(textos, titulo, (FAMILIA, 18, "bold"), "texto", ajustar=120).pack(anchor="w")
    etiqueta(textos, descripcion, FUENTE_NORMAL, "texto_2", ajustar=120).pack(anchor="w", pady=(3, 0))

    inicio = resolver_color(color)
    fin = resolver_color(PALETA["borde"])
    animar(tarjeta, 1200, lambda t: tarjeta.configure(border_color=mezclar_colores(inicio, fin, t * 0.55)))
    return tarjeta


def fila_indicadores(parent, datos):
    """Fila de indicadores numericos (los enteros se animan contando desde 0)."""
    fila = ctk.CTkFrame(parent, fg_color="transparent")
    fila.pack(fill="x", padx=2, pady=(0, 12))
    for k, (valor, texto) in enumerate(datos):
        fila.grid_columnconfigure(k, weight=1, uniform="indicadores")
        caja = ctk.CTkFrame(fila, fg_color=PALETA["panel_2"], corner_radius=12,
                            border_width=1, border_color=PALETA["borde"])
        caja.grid(row=0, column=k, sticky="nsew", padx=(0 if k == 0 else 8, 0))
        es_entero = isinstance(valor, int) and not isinstance(valor, bool)
        numero = etiqueta(caja, "0" if es_entero else str(valor), FUENTE_DATO, "primario")
        numero.pack(anchor="w", padx=14, pady=(10, 0))
        etiqueta(caja, texto, FUENTE_PEQUENA, "texto_3",
                 ajustar=lambda w, n=len(datos): (w - 8 * (n - 1)) / n - 44).pack(anchor="w", padx=14, pady=(0, 12))
        if es_entero:
            animar(numero, 600, lambda t, n=numero, v=valor: n.configure(text=str(round(v * t))))
        efecto_hover(caja)
    return fila


def estado_de_sistema(resultado):
    """(color, icono) segun la clasificacion del sistema."""
    clasificacion = resultado["clasificacion"]
    if clasificacion == "Sistema inconsistente":
        return PALETA["error"], "✕"
    if clasificacion == "Sistema consistente indeterminado":
        return PALETA["advertencia"], "∞"
    return PALETA["exito"], "✓"


def tarjeta_solucion_unica(parent, solucion, nombres, simbolo="x", titulo="Solución única"):
    tarjeta = tarjeta_seccion(parent, titulo)
    cuerpo = ctk.CTkFrame(tarjeta, fg_color="transparent")
    cuerpo.pack(fill="x", padx=16, pady=(0, 16))
    dibujar_expresion(cuerpo, [f"{simbolo} =", solucion]).pack(side="left", anchor="n")
    chips = ctk.CTkFrame(cuerpo, fg_color="transparent")
    chips.pack(side="left", anchor="n", padx=(18, 0))
    for k, (nombre, valor) in enumerate(zip(nombres, solucion)):
        chip(chips, f"{nombre} = {formatear_numero(valor)}", "entrada", "texto", FUENTE_MONO).grid(
            row=k // 2, column=k % 2, padx=4, pady=4, sticky="w")
    return tarjeta


def tarjeta_solucion_parametrica(parent, resultado, simbolo="x", titulo="Solución general (infinitas soluciones)"):
    nombres = resultado["nombres_variables"]
    parametros = resultado["parametros"]
    tarjeta = tarjeta_seccion(
        parent, titulo,
        "Las variables libres pueden tomar cualquier valor real; las básicas dependen de ellas.",
    )
    lista = ctk.CTkFrame(tarjeta, fg_color="transparent")
    lista.pack(fill="x", padx=16, pady=(0, 6))
    for i, expresion in resultado["expresiones"].items():
        fila = ctk.CTkFrame(lista, fg_color="transparent")
        fila.pack(anchor="w", pady=1)
        etiqueta(fila, f"{nombres[i]} = {expresion}", FUENTE_MONO, "texto").pack(side="left")
        if i in parametros:
            chip(fila, "libre", "panel", "advertencia").pack(side="left", padx=(10, 0))

    if resultado.get("forma_vectorial"):
        particular, direcciones = resultado["forma_vectorial"]
        etiqueta(tarjeta, "FORMA VECTORIAL PARAMÉTRICA", FUENTE_PEQUENA_NEGRITA, "primario").pack(
            anchor="w", padx=16, pady=(10, 2))
        partes = [f"{simbolo} ="]
        if any(v != 0 for v in particular):
            partes.append(particular)
        for parametro, vector in direcciones:
            partes += [f"+ {parametro}" if len(partes) > 1 else parametro, vector]
        dibujar_expresion(tarjeta, partes).pack(anchor="w", padx=14, pady=(0, 6))

    particular = resultado.get("solucion_particular")
    if particular is not None:
        texto = ",  ".join(f"{nombres[i]} = {formatear_numero(v)}" for i, v in enumerate(particular))
        etiqueta(tarjeta, f"Solución particular (parámetros = 0):  {texto}", FUENTE_PEQUENA, "texto_3",
                 ajustar=44).pack(anchor="w", padx=16, pady=(4, 16))
    return tarjeta


def tarjeta_inconsistente(parent, resultado):
    tarjeta = tarjeta_seccion(parent, "¿Por qué no tiene solución?")
    filas = resultado["filas_inconsistentes"]
    if filas:
        i = filas[0]
        fila = resultado["matriz_final"][i]
        etiqueta(tarjeta, f"Al reducir la matriz, la fila F{i + 1} quedó así:", FUENTE_NORMAL, "texto_2").pack(
            anchor="w", padx=16)
        dibujar_matriz(tarjeta, [fila], filas=[0]).pack(anchor="w", padx=12, pady=6)
        etiqueta(
            tarjeta,
            f"Equivale a la ecuación 0 = {formatear_numero(fila[-1])}, que es imposible. "
            f"Por eso ningún valor de las variables satisface todas las ecuaciones a la vez.",
            FUENTE_NORMAL, "texto_2", ajustar=44,
        ).pack(anchor="w", padx=16, pady=(0, 16))
    return tarjeta


def _cuerpo_verificacion(marco, detalle):
    for titulo, lineas in (("Sustitución", [detalle.sustitucion]), ("Simplificación", detalle.simplificacion)):
        etiqueta(marco, titulo, FUENTE_PEQUENA_NEGRITA, "texto_3").pack(anchor="w", pady=(4, 0))
        for linea in lineas:
            etiqueta(marco, linea, FUENTE_MONO, "texto_2").pack(anchor="w", padx=10)


def tarjeta_verificacion(parent, verificacion, es_parametrico=False):
    correcta, detalles = verificacion
    subtitulo = (
        "Se sustituye la solución particular (parámetros = 0) en cada ecuación original. Haz clic para ver el detalle."
        if es_parametrico else
        "Se sustituyen los valores encontrados en cada ecuación original. Haz clic para ver el detalle."
    )
    tarjeta = tarjeta_seccion(parent, "Verificación", subtitulo)
    cumplidas = sum(1 for d in detalles if d.coincide)
    etiqueta(
        tarjeta,
        f"{'✓' if correcta else '✕'}  {cumplidas} de {len(detalles)} ecuaciones se cumplen",
        FUENTE_NEGRITA, "exito" if correcta else "error",
    ).pack(anchor="w", padx=16, pady=(0, 8))
    for detalle in detalles:
        SeccionPlegable(
            tarjeta, f"Ecuación {detalle.indice}", detalle.ecuacion_original, detalle.coincide,
            construir=lambda marco, d=detalle: _cuerpo_verificacion(marco, d),
            abierto=len(detalles) <= 3 or not detalle.coincide,
        ).pack(fill="x", padx=14, pady=(0, 8))
    ctk.CTkFrame(tarjeta, fg_color="transparent", height=6).pack()
    return tarjeta


def tarjeta_mensajes(parent, titulo, mensajes, color="advertencia"):
    tarjeta = tarjeta_seccion(parent, titulo)
    for mensaje in mensajes:
        fila = ctk.CTkFrame(tarjeta, fg_color="transparent")
        fila.pack(fill="x", padx=16, pady=(0, 8))
        etiqueta(fila, "●", FUENTE_PEQUENA, color).pack(side="left", anchor="n", padx=(0, 8), pady=2)
        etiqueta(fila, mensaje, FUENTE_NORMAL, "texto_2", ajustar=64).pack(side="left", anchor="w")
    ctk.CTkFrame(tarjeta, fg_color="transparent", height=6).pack()
    return tarjeta


def constructores_solucion(resultado, simbolo="x"):
    """Tarjetas comunes: solucion (unica/parametrica/ninguna) y verificacion."""
    lista = []
    if resultado["solucion"] is not None:
        lista.append(lambda p: tarjeta_solucion_unica(p, resultado["solucion"], resultado["nombres_variables"], simbolo))
    elif resultado["expresiones"] is not None:
        lista.append(lambda p: tarjeta_solucion_parametrica(p, resultado, simbolo))
    else:
        lista.append(lambda p: tarjeta_inconsistente(p, resultado))
    if resultado["verificacion"] is not None:
        lista.append(lambda p: tarjeta_verificacion(p, resultado["verificacion"], resultado["expresiones"] is not None))
    return lista


def indicadores_sistema(parent, resultado, etiqueta_rango="Rango de A"):
    return fila_indicadores(parent, [
        (resultado["rango"], etiqueta_rango),
        (resultado["rango_aumentada"], "Rango de [A | b]"),
        (len(resultado["variables_basicas"]), "Variables básicas"),
        (len(resultado["variables_libres"]), "Variables libres"),
    ])


def fila_copiar(parent, app, texto):
    fila = ctk.CTkFrame(parent, fg_color="transparent")
    fila.pack(fill="x", padx=2, pady=(0, 16))
    boton_secundario(fila, "⧉  Copiar resultado", lambda: app.copiar(texto), width=170).pack(side="left")
    return fila


def columnas_de(matriz):
    return [[fila[j] for fila in matriz] for j in range(len(matriz[0]))]


# -----------------------------------------------------------------------------
# Paginas
# -----------------------------------------------------------------------------

class PaginaBase(_Marco):
    titulo = ""
    subtitulo = ""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=PALETA["fondo"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=1)

        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 12))
        etiqueta(encabezado, self.titulo, FUENTE_TITULO, "texto").pack(anchor="w")
        self._subrayado = ctk.CTkFrame(encabezado, fg_color=PALETA["primario"], width=1, height=3, corner_radius=2)
        self._subrayado.pack(anchor="w", pady=(6, 6))
        etiqueta(encabezado, self.subtitulo, FUENTE_SUBTITULO, "texto_2").pack(anchor="w")

    def al_mostrar(self):
        animar(self._subrayado, 500, lambda t: self._subrayado.configure(width=max(1, round(72 * t))))


class PaginaSistema(PaginaBase):
    """
    Plantilla comun: barra de configuracion arriba, datos a la izquierda y
    pestanas de Resultado/Procedimiento a la derecha. Las subclases definen
    como se arma la rejilla, la vista previa y como se presenta el resultado.
    """

    etiqueta_filas = "Ecuaciones"
    etiqueta_columnas = "Variables"
    filas_inicial = 3
    columnas_inicial = 3
    minimo_filas = 1
    minimo_columnas = 1
    titulo_datos = "Datos"
    texto_boton = "Resolver"
    ejemplos = {}
    ejemplo_inicial = None
    vacio_resultado = "Ingresa los datos y presiona Resolver para ver aquí el resultado."
    vacio_pasos = "Aquí aparecerá cada operación elemental con la matriz resultante."

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.resultado = None
        self.grid_rowconfigure(2, weight=1)
        self._crear_barra()
        self._crear_contenido()

        valores = None
        if self.ejemplo_inicial:
            filas, columnas, valores = self.ejemplos[self.ejemplo_inicial]
            self.contador_filas.set(filas)
            self.contador_columnas.set(columnas)
        self.reconstruir(valores)
        self.mostrar_vacio()

    # --- construccion ---------------------------------------------------

    def _crear_barra(self):
        barra = crear_tarjeta(self)
        barra.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 14))
        fila = ctk.CTkFrame(barra, fg_color="transparent")
        fila.pack(fill="x", padx=18, pady=12)

        self.contador_filas = Contador(fila, self.etiqueta_filas, self.filas_inicial, self.minimo_filas,
                                       LIMITE_DIMENSION, lambda _v: self.reconstruir())
        self.contador_filas.pack(side="left", padx=(0, 18))
        self.contador_columnas = Contador(fila, self.etiqueta_columnas, self.columnas_inicial,
                                          self.minimo_columnas, LIMITE_DIMENSION, lambda _v: self.reconstruir())
        self.contador_columnas.pack(side="left", padx=(0, 18))
        self.controles_extra(fila)
        separador_vertical(fila).pack(side="left", padx=(0, 18))

        grupo = ctk.CTkFrame(fila, fg_color="transparent")
        grupo.pack(side="left")
        etiqueta(grupo, "Ejemplos", FUENTE_PEQUENA_NEGRITA, "texto_3").pack(anchor="w", pady=(0, 4))
        # Boton + menu nativo: CTkOptionMenu fuerza un redibujado completo de la ventana.
        self.boton_ejemplos = boton_secundario(grupo, "Cargar ejemplo…   ▾", self._abrir_ejemplos,
                                               width=190, height=34)
        self.boton_ejemplos.pack(anchor="w")
        self.menu_ejemplos = tk.Menu(
            self, tearoff=0, font=FUENTE_NORMAL, bd=0, relief="flat",
            bg=resolver_color(PALETA["panel_2"]), fg=resolver_color(PALETA["texto"]),
            activebackground=resolver_color(PALETA["primario"]), activeforeground=TEXTO_SOBRE_PRIMARIO,
        )
        for nombre in self.ejemplos:
            self.menu_ejemplos.add_command(label=nombre, command=lambda n=nombre: self.cargar_ejemplo(n))

        acciones = ctk.CTkFrame(fila, fg_color="transparent")
        acciones.pack(side="left", padx=(14, 0))
        etiqueta(acciones, "Acciones", FUENTE_PEQUENA_NEGRITA, "texto_3").pack(anchor="w", pady=(0, 4))
        botones = ctk.CTkFrame(acciones, fg_color="transparent")
        botones.pack(anchor="w")
        boton_secundario(botones, "⚄  Aleatorio", self.aleatorio, width=112, height=34).pack(side="left")
        boton_secundario(botones, "↺  Limpiar", self.limpiar, width=100, height=34).pack(side="left", padx=(8, 0))

    def controles_extra(self, fila):
        """Permite a una subclase agregar controles a la barra superior."""

    def _abrir_ejemplos(self):
        boton = self.boton_ejemplos
        self.menu_ejemplos.tk_popup(boton.winfo_rootx(), boton.winfo_rooty() + boton.winfo_height() + 4)

    def _crear_contenido(self):
        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 22))
        contenido.grid_columnconfigure(0, weight=1, uniform="columnas")
        contenido.grid_columnconfigure(1, weight=1, uniform="columnas")
        contenido.grid_rowconfigure(0, weight=1)

        self.tarjeta_datos = crear_tarjeta(contenido)
        self.tarjeta_datos.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.tarjeta_datos.grid_columnconfigure(0, weight=1)
        self.tarjeta_datos.grid_rowconfigure(1, weight=1)

        cabecera = ctk.CTkFrame(self.tarjeta_datos, fg_color="transparent")
        cabecera.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))
        etiqueta(cabecera, self.titulo_datos, FUENTE_SECCION, "texto").pack(side="left")
        self.etiqueta_dimension = chip(cabecera, "", "panel_2", "texto_3", FUENTE_PEQUENA)
        self.etiqueta_dimension.pack(side="right")

        self.area_datos = AreaDesplazable(self.tarjeta_datos, PALETA["panel"])
        self.area_datos.grid(row=1, column=0, sticky="nsew", padx=(14, 10), pady=(0, 8))
        self.construir_entradas(self.area_datos.interior)
        marco_previa = ctk.CTkFrame(self.area_datos.interior, fg_color=PALETA["panel_2"], corner_radius=10)
        marco_previa.pack(fill="x", anchor="w", padx=4, pady=(14, 6))
        etiqueta(marco_previa, "VISTA PREVIA", FUENTE_PEQUENA_NEGRITA, "primario").pack(anchor="w", padx=14, pady=(10, 4))
        self.contenido_previa = ctk.CTkFrame(marco_previa, fg_color="transparent")
        self.contenido_previa.pack(fill="x", padx=14, pady=(0, 12))

        acciones = ctk.CTkFrame(self.tarjeta_datos, fg_color="transparent")
        acciones.grid(row=2, column=0, sticky="ew", padx=18, pady=(4, 16))
        boton_primario(acciones, self.texto_boton, self.resolver, height=44, width=190).pack(side="left")
        etiqueta(acciones, f"o presiona {ATAJO_RESOLVER}", FUENTE_PEQUENA, "texto_3").pack(side="left", padx=12)

        self.pestanas = ctk.CTkTabview(
            contenido, fg_color=PALETA["panel"], corner_radius=14, border_width=1, border_color=PALETA["borde"],
            segmented_button_fg_color=PALETA["panel_2"], segmented_button_selected_color=PALETA["primario"],
            segmented_button_selected_hover_color=PALETA["primario_hover"],
            segmented_button_unselected_color=PALETA["panel_2"],
            segmented_button_unselected_hover_color=PALETA["secundario_hover"], text_color=PALETA["texto"],
        )
        self.pestanas.grid(row=0, column=1, sticky="nsew")
        pestana_resultado = self.pestanas.add("Resultado")
        pestana_pasos = self.pestanas.add("Procedimiento")

        pestana_resultado.grid_columnconfigure(0, weight=1)
        pestana_resultado.grid_rowconfigure(1, weight=1)
        self.aviso = ctk.CTkLabel(
            pestana_resultado, text="⟳  Los datos cambiaron. Presiona «Resolver» para actualizar el resultado.",
            font=FUENTE_PEQUENA_NEGRITA, fg_color=PALETA["panel_2"], text_color=PALETA["advertencia"],
            corner_radius=8, height=32,
        )
        self.area_resultado = AreaDesplazable(pestana_resultado, PALETA["panel"])
        self.area_resultado.grid(row=1, column=0, sticky="nsew")
        self.crear_procedimiento(pestana_pasos)

    def construir_entradas(self, parent):
        self.matriz = MatrizEntrada(parent, al_cambiar=self._al_cambiar_datos)
        self.matriz.pack(anchor="w", padx=4, pady=4)

    def crear_procedimiento(self, pestana):
        self.panel_pasos = PanelPasos(pestana, PALETA["panel"], self.vacio_pasos)
        self.panel_pasos.pack(fill="both", expand=True)

    # --- datos -------------------------------------------------------------

    def configuracion_rejilla(self, filas, columnas):
        raise NotImplementedError

    def texto_dimension(self, filas, columnas):
        return f"{filas} × {columnas}"

    def configurar_entradas(self, filas, columnas, valores):
        cfg = self.configuracion_rejilla(filas, columnas)
        self.matriz.configurar(filas, cfg["columnas"], cfg["encabezados"], cfg.get("encabezados_fila"),
                               cfg.get("separador"), valores)

    def reconstruir(self, valores=None):
        filas, columnas = self.contador_filas.get(), self.contador_columnas.get()
        self.configurar_entradas(filas, columnas, valores)
        self.etiqueta_dimension.configure(text=self.texto_dimension(filas, columnas))
        self._al_cambiar_datos()

    def valores_previa(self):
        return [[_numero_o_nada(texto) for texto in fila] for fila in self.matriz.textos()]

    def construir_previa(self, parent, valores):
        raise NotImplementedError

    def _al_cambiar_datos(self):
        for hijo in self.contenido_previa.winfo_children():
            hijo.destroy()
        try:
            self.construir_previa(self.contenido_previa, self.valores_previa())
        except (ValueError, IndexError, ZeroDivisionError):
            etiqueta(self.contenido_previa, "Vista previa no disponible.", FUENTE_PEQUENA, "texto_3").pack(anchor="w")
        if self.resultado is not None:
            self.aviso.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 8))

    def leer_datos(self):
        return self.matriz.valores()

    def limpiar_entradas(self):
        self.matriz.limpiar()

    def valores_aleatorios(self, filas, columnas):
        A, b = sistema_aleatorio(filas, columnas)
        return [fila + [bi] for fila, bi in zip(A, b)]

    # --- acciones ------------------------------------------------------------

    def cargar_ejemplo(self, nombre):
        filas, columnas, valores = self.ejemplos[nombre]
        self.contador_filas.set(filas)
        self.contador_columnas.set(columnas)
        self.reconstruir(valores)
        destello(self.tarjeta_datos)
        self.app.notificar(f"Ejemplo cargado: {nombre}. Presiona «{self.texto_boton}».", "info")

    def aleatorio(self):
        filas, columnas = self.contador_filas.get(), self.contador_columnas.get()
        self.reconstruir(self.valores_aleatorios(filas, columnas))
        destello(self.tarjeta_datos)
        self.app.notificar("Se generaron datos aleatorios.", "info")

    def limpiar(self):
        self.resultado = None
        self.limpiar_entradas()
        self.mostrar_vacio()

    def mostrar_vacio(self):
        self.resultado = None
        self.aviso.grid_remove()
        self.area_resultado.llenar([lambda p: placeholder(p, "∑", self.vacio_resultado)])
        self.procedimiento_vacio()

    def procedimiento_vacio(self):
        self.panel_pasos.mostrar_placeholder()

    def resolver(self):
        try:
            datos = self.leer_datos()
        except ValueError as error:
            self.app.notificar(str(error), "error")
            return
        try:
            resultado = self.calcular(datos)
        except Exception as error:
            self.app.notificar(f"No se pudo resolver: {error}", "error")
            return

        self.resultado = resultado
        self.aviso.grid_remove()
        constructores = self.construir_resultado(resultado)
        texto = self.texto_copiar(resultado)
        if texto:
            constructores.append(lambda p: fila_copiar(p, self.app, texto))
        self.area_resultado.llenar(constructores, retardo=80)
        self.mostrar_procedimiento(resultado)
        self.pestanas.set("Resultado")
        mensaje, tipo = self.mensaje_resuelto(resultado)
        self.app.notificar(mensaje, tipo)

    def calcular(self, datos):
        raise NotImplementedError

    def construir_resultado(self, resultado):
        raise NotImplementedError

    def mostrar_procedimiento(self, resultado):
        self.panel_pasos.mostrar_pasos(resultado["pasos"])

    def texto_copiar(self, resultado):
        return resumen_texto(resultado)

    def mensaje_resuelto(self, resultado):
        operaciones = len(resultado["pasos"]) - 2
        tipo = {"Sistema inconsistente": "error",
                "Sistema consistente indeterminado": "aviso"}.get(resultado["clasificacion"], "exito")
        return f"{resultado['clasificacion']} · {operaciones} operaciones elementales.", tipo


def _numero_o_nada(texto):
    try:
        return convertir_numero(texto)
    except ValueError:
        return None


class PaginaCalculadora(PaginaSistema):
    titulo = "Calculadora de Álgebra Lineal"
    subtitulo = "Resuelve sistemas de ecuaciones lineales por eliminación de Gauss-Jordan"
    titulo_datos = "Matriz aumentada [A | b]"
    texto_boton = "Resolver sistema"
    ejemplos = {
        "Solución única (3×3)": (3, 3, [[1, 1, 1, 6], [2, -1, 1, 3], [1, 2, -1, 2]]),
        "Infinitas soluciones": (3, 3, [[1, 1, 1, 6], [2, 2, 2, 12], [1, -1, 1, 2]]),
        "Sistema inconsistente": (3, 3, [[1, 1, 1, 3], [2, 2, 2, 6], [1, 1, 1, 5]]),
        "Pivote inicial cero": (3, 3, [[0, 1, 2, 5], [1, 2, 3, 8], [2, 1, 1, 6]]),
        "Rectangular 2×4": (2, 4, [[1, 2, 0, 1, 5], [0, 1, 1, 2, 4]]),
        "Sistema homogéneo": (3, 3, [[1, 2, 3, 0], [2, 4, 6, 0], [1, 1, 1, 0]]),
        "Con fracciones": (2, 2, [["1/2", "1/3", "5/6"], [2, -1, 1]]),
    }
    ejemplo_inicial = "Solución única (3×3)"
    vacio_resultado = "Escribe los coeficientes del sistema y presiona «Resolver sistema»."

    def configuracion_rejilla(self, filas, columnas):
        return {
            "columnas": columnas + 1,
            "encabezados": obtener_nombres_variables(columnas) + ["b"],
            "encabezados_fila": [f"F{i + 1}" for i in range(filas)],
            "separador": columnas,
        }

    def texto_dimension(self, filas, columnas):
        return f"{filas} ecuaciones × {columnas} variables"

    def construir_previa(self, parent, valores):
        nombres = obtener_nombres_variables(len(valores[0]) - 1)
        for i, fila in enumerate(valores):
            if any(v is None for v in fila):
                etiqueta(parent, f"F{i + 1}: hay un valor no válido", FUENTE_MONO, "error").pack(anchor="w")
            else:
                etiqueta(parent, formatear_ecuacion_original(fila[:-1], fila[-1], nombres),
                         FUENTE_MONO, "texto").pack(anchor="w")

    def calcular(self, matriz):
        return resolver_sistema([fila[:-1] for fila in matriz], [fila[-1] for fila in matriz])

    def construir_resultado(self, resultado):
        color, icono = estado_de_sistema(resultado)
        descripcion = resultado["descripcion"]
        if resultado["homogeneo"]:
            descripcion += " Es un sistema homogéneo (Ax = 0)."
        return [
            lambda p: tarjeta_estado(p, resultado["clasificacion"], descripcion, color, icono),
            lambda p: indicadores_sistema(p, resultado),
        ] + constructores_solucion(resultado)


class PaginaAxb(PaginaSistema):
    titulo = "Ecuación matricial Ax = b"
    subtitulo = "Interpreta el sistema como un producto matriz-vector y encuentra el vector x"
    etiqueta_filas = "Filas de A"
    etiqueta_columnas = "Columnas de A"
    titulo_datos = "Matriz A y vector b"
    texto_boton = "Resolver Ax = b"
    ejemplos = {
        "Solución única": (3, 3, [[2, 1, -1, 8], [-3, -1, 2, -11], [-2, 1, 2, -3]]),
        "Infinitas soluciones": (2, 3, [[1, 2, -1, 3], [2, 4, 1, 3]]),
        "Sin solución": (3, 2, [[1, 1, 2], [1, -1, 0], [2, 1, 5]]),
        "Homogéneo Ax = 0": (2, 4, [[1, 2, 0, -1, 0], [0, 0, 1, 3, 0]]),
        "Rectangular 4×3": (4, 3, [[1, 1, 1, 6], [2, -1, 1, 3], [1, 2, -1, 2], [3, 0, 2, 9]]),
    }
    ejemplo_inicial = "Solución única"
    vacio_resultado = "Escribe A y b y presiona «Resolver Ax = b»."

    def configuracion_rejilla(self, filas, columnas):
        return {
            "columnas": columnas + 1,
            "encabezados": [f"a{j + 1}" for j in range(columnas)] + ["b"],
            "encabezados_fila": [f"F{i + 1}" for i in range(filas)],
            "separador": columnas,
        }

    def texto_dimension(self, filas, columnas):
        return f"A es {filas} × {columnas}"

    def construir_previa(self, parent, valores):
        A = [fila[:-1] for fila in valores]
        b = [fila[-1] for fila in valores]
        n = len(A[0])
        dibujar_expresion(parent, [A, obtener_nombres_variables(n), "=", b], tamano=12).pack(anchor="w")
        columnas = " + ".join(f"x{j + 1}·a{j + 1}" for j in range(n))
        etiqueta(parent, f"Equivale a {columnas} = b, donde a1, …, a{n} son las columnas de A.",
                 FUENTE_PEQUENA, "texto_3", ajustar=48).pack(anchor="w", pady=(6, 0))

    def calcular(self, matriz):
        return resolver_sistema([fila[:-1] for fila in matriz], [fila[-1] for fila in matriz])

    def construir_resultado(self, resultado):
        color, icono = estado_de_sistema(resultado)
        A = [fila[:-1] for fila in resultado["matriz_inicial"]]
        b = [fila[-1] for fila in resultado["matriz_inicial"]]
        constructores = [
            lambda p: tarjeta_estado(p, resultado["clasificacion"], resultado["descripcion"], color, icono),
            lambda p: indicadores_sistema(p, resultado),
        ] + constructores_solucion(resultado)

        x = resultado["solucion"] if resultado["solucion"] is not None else resultado["solucion_particular"]
        if x is not None:
            titulo = "Comprobación: A·x = b" if resultado["solucion"] is not None else \
                "Comprobación con la solución particular: A·p = b"
            constructores.insert(3, lambda p: self._tarjeta_producto(p, A, x, b, titulo))
        return constructores

    @staticmethod
    def _tarjeta_producto(parent, A, x, b, titulo):
        Ax = multiplicar_matriz_vector(A, x)
        tarjeta = tarjeta_seccion(parent, titulo, "Se multiplica A por el vector encontrado y se compara con b.")
        dibujar_expresion(tarjeta, [A, x, "=", Ax]).pack(anchor="w", padx=14)
        igual = Ax == b
        etiqueta(tarjeta, "✓  A·x coincide con b" if igual else "✕  A·x no coincide con b",
                 FUENTE_NEGRITA, "exito" if igual else "error").pack(anchor="w", padx=16, pady=(6, 16))
        return tarjeta


class PaginaCombinaciones(PaginaSistema):
    titulo = "Combinaciones lineales"
    subtitulo = "Determina si w pertenece al espacio generado por v1, …, vn (w ∈ Gen{v1, …, vn})"
    etiqueta_filas = "Componentes"
    etiqueta_columnas = "Vectores"
    titulo_datos = "Vectores v1 … vn y w"
    texto_boton = "Resolver combinación"
    ejemplos = {
        "Combinación única": (3, 3, [[1, 0, 1, 2], [0, 1, 1, 3], [1, 1, 0, 3]]),
        "Infinitas combinaciones": (2, 3, [[1, 0, 1, 2], [0, 1, 1, 3]]),
        "w fuera del generado": (3, 2, [[1, 2, 1], [2, 4, 0], [3, 6, 0]]),
        "Vectores en R²": (2, 2, [[1, 1, 3], [1, -1, 1]]),
    }
    ejemplo_inicial = "Combinación única"
    vacio_resultado = "Escribe los vectores como columnas y presiona «Resolver combinación»."

    def configuracion_rejilla(self, filas, columnas):
        return {
            "columnas": columnas + 1,
            "encabezados": [f"v{j + 1}" for j in range(columnas)] + ["w"],
            "encabezados_fila": [str(i + 1) for i in range(filas)],
            "separador": columnas,
        }

    def texto_dimension(self, filas, columnas):
        return f"{columnas} vectores de {espacio_real(filas)}"

    def construir_previa(self, parent, valores):
        n = len(valores[0]) - 1
        partes = []
        for j in range(n):
            partes += [f"{'' if j == 0 else '+ '}c{j + 1}·", [fila[j] for fila in valores]]
        partes += ["=", [fila[-1] for fila in valores]]
        dibujar_expresion(parent, partes, tamano=12).pack(anchor="w")
        etiqueta(parent, "Se resuelve el sistema cuya matriz aumentada es [v1 … vn | w].",
                 FUENTE_PEQUENA, "texto_3").pack(anchor="w", pady=(6, 0))

    def calcular(self, matriz):
        n = len(matriz[0]) - 1
        return resolver_sistema([fila[:-1] for fila in matriz], [fila[-1] for fila in matriz],
                                obtener_nombres_variables(n, "c"))

    def construir_resultado(self, resultado):
        A = [fila[:-1] for fila in resultado["matriz_inicial"]]
        w = [fila[-1] for fila in resultado["matriz_inicial"]]
        vectores = columnas_de(A)
        simbolos = [f"v{j + 1}" for j in range(len(vectores))]
        generado = f"Gen{{{', '.join(simbolos)}}}" if len(simbolos) <= 4 else f"Gen{{v1, …, v{len(simbolos)}}}"
        clasificacion = resultado["clasificacion"]

        if clasificacion == "Sistema consistente determinado":
            estado = ("w es combinación lineal de los vectores",
                      f"Existe una única elección de coeficientes, así que w ∈ {generado}.", PALETA["exito"], "✓")
        elif clasificacion == "Sistema consistente indeterminado":
            estado = ("w es combinación lineal (de infinitas maneras)",
                      f"w ∈ {generado}, pero los coeficientes no son únicos: hay coeficientes libres.",
                      PALETA["advertencia"], "∞")
        else:
            estado = ("w no es combinación lineal de los vectores",
                      f"El sistema es inconsistente, así que w ∉ {generado}.", PALETA["error"], "✕")

        constructores = [
            lambda p: tarjeta_estado(p, *estado),
            lambda p: fila_indicadores(p, [
                (resultado["rango"], "Rango de [v1 … vn]"),
                (len(vectores), "Vectores"),
                (len(w), "Componentes"),
                (len(resultado["variables_libres"]), "Coeficientes libres"),
            ]),
        ]
        coeficientes = resultado["solucion"] if resultado["solucion"] is not None else resultado["solucion_particular"]
        if coeficientes is not None:
            titulo = "Combinación encontrada" if resultado["solucion"] is not None else \
                "Un ejemplo concreto (parámetros = 0)"
            constructores.append(lambda p: self._tarjeta_combinacion(p, titulo, coeficientes, vectores, simbolos, w))
        return constructores + constructores_solucion(resultado, simbolo="c")

    @staticmethod
    def _tarjeta_combinacion(parent, titulo, coeficientes, vectores, simbolos, w):
        tarjeta = tarjeta_seccion(parent, titulo)
        etiqueta(tarjeta, f"w = {formatear_combinacion_lineal(coeficientes, simbolos)}",
                 (FAMILIA_MONO, 16, "bold"), "primario").pack(anchor="w", padx=16)
        dibujar_expresion(tarjeta, partes_combinacion(coeficientes, vectores, w)).pack(
            anchor="w", padx=14, pady=(6, 16))
        return tarjeta


class PaginaIndependencia(PaginaSistema):
    titulo = "Independencia lineal"
    subtitulo = "Reduce [A | 0] a forma escalonada por filas, cuenta pivotes y variables libres y da el veredicto"
    etiqueta_filas = "Dimensión (n)"
    etiqueta_columnas = "Vectores (p)"
    titulo_datos = "Vectores v1 … vp de Rⁿ"
    texto_boton = "Analizar independencia"
    ejemplos = {
        "Independientes (base de R³)": (3, 3, [[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
        "Independientes en R⁴": (4, 3, [[1, 0, 2], [2, 1, 0], [0, 3, 1], [1, 1, 1]]),
        "Dependientes": (3, 3, [[1, 4, 7], [2, 5, 8], [3, 6, 9]]),
        "Más vectores que dimensión": (2, 3, [[1, 0, 2], [0, 1, 3]]),
        "Con vector cero": (3, 2, [[1, 0], [2, 0], [3, 0]]),
    }
    ejemplo_inicial = "Dependientes"
    vacio_resultado = "Escribe los vectores como columnas y presiona «Analizar independencia»."
    vacio_pasos = "Aquí aparecerá la reducción de [A | 0] a forma escalonada por filas."

    def configuracion_rejilla(self, filas, columnas):
        return {
            "columnas": columnas,
            "encabezados": [f"v{j + 1}" for j in range(columnas)],
            "encabezados_fila": [str(i + 1) for i in range(filas)],
            "separador": None,
        }

    def texto_dimension(self, filas, columnas):
        return f"p = {columnas} vectores de {espacio_real(filas)}"

    def valores_aleatorios(self, filas, columnas):
        return [[random.randint(-5, 5) for _ in range(columnas)] for _ in range(filas)]

    def construir_previa(self, parent, valores):
        p = len(valores[0])
        partes = []
        for j in range(p):
            partes += [f"{'' if j == 0 else '+ '}c{j + 1}·", [fila[j] for fila in valores]]
        partes += ["=", [0] * len(valores)]
        dibujar_expresion(parent, partes, tamano=12).pack(anchor="w")
        etiqueta(parent, "SISTEMA HOMOGÉNEO [A | 0]", FUENTE_PEQUENA_NEGRITA, "primario").pack(
            anchor="w", pady=(10, 2))
        if all(v is not None for fila in valores for v in fila):
            dibujar_matriz(parent, [fila + [Fraction(0)] for fila in valores], tamano=12).pack(anchor="w")
        else:
            etiqueta(parent, "Corrige las casillas en rojo para ver [A | 0].", FUENTE_PEQUENA, "error").pack(
                anchor="w")

    def calcular(self, matriz):
        return analizar_independencia(matriz)

    def construir_resultado(self, resultado):
        A = [fila[:-1] for fila in resultado["matriz_homogenea"]]
        vectores = columnas_de(A)
        simbolos = [f"v{j + 1}" for j in range(len(vectores))]
        ceros = [0] * len(A)
        independiente = resultado["independiente"]

        if independiente:
            estado = ("Linealmente Independiente (L.I.)",
                      "Hay un pivote en cada columna: la única solución de A·c = 0 es la trivial.",
                      PALETA["exito"], "✓")
        else:
            estado = ("Linealmente Dependiente (L.D.)",
                      "Hay variables libres: A·c = 0 tiene soluciones no triviales.",
                      PALETA["advertencia"], "!")

        constructores = [
            lambda p: tarjeta_estado(p, *estado),
            lambda p: fila_indicadores(p, [
                (resultado["num_pivotes"], "Pivotes"),
                (resultado["num_libres"], "Variables libres"),
                (len(vectores), "Vectores (p)"),
                (len(A), "Dimensión (n)"),
            ]),
            lambda p: self._tarjeta_reduccion(p, resultado),
            lambda p: self._tarjeta_veredicto(p, resultado),
        ]
        if resultado["observaciones"]:
            constructores.append(lambda p: tarjeta_mensajes(p, "Observaciones", resultado["observaciones"]))

        if independiente:
            def trivial(parent):
                tarjeta = tarjeta_seccion(parent, "Solución trivial")
                dibujar_expresion(tarjeta, ["c =", resultado["solucion"]]).pack(anchor="w", padx=14)
                etiqueta(tarjeta, "Ningún vector se puede escribir como combinación lineal de los demás.",
                         FUENTE_NORMAL, "texto_2", ajustar=44).pack(anchor="w", padx=16, pady=(6, 16))
            constructores.append(trivial)
        else:
            relacion = resultado["relacion"]

            def dependencia(parent):
                tarjeta = tarjeta_seccion(parent, "Relación de dependencia",
                                          "Un ejemplo de coeficientes no nulos (todos los parámetros = 1).")
                etiqueta(tarjeta, f"{formatear_combinacion_lineal(relacion, simbolos)} = 0",
                         (FAMILIA_MONO, 16, "bold"), "primario").pack(anchor="w", padx=16)
                dibujar_expresion(tarjeta, partes_combinacion(relacion, vectores, ceros)).pack(
                    anchor="w", padx=14, pady=(6, 4))
                k = max(j for j, c in enumerate(relacion) if c != 0)
                otros = [(-relacion[j] / relacion[k], simbolos[j]) for j in range(len(relacion)) if j != k]
                despeje = formatear_combinacion_lineal([c for c, _ in otros], [s for _, s in otros])
                etiqueta(tarjeta, f"Despejando: {simbolos[k]} = {despeje}", FUENTE_MONO, "texto_2").pack(
                    anchor="w", padx=16, pady=(4, 16))
            constructores.append(dependencia)
            constructores.append(lambda p: tarjeta_solucion_parametrica(
                p, resultado, simbolo="c", titulo="Todas las soluciones de A·c = 0"))
        return constructores

    @staticmethod
    def _tarjeta_reduccion(parent, resultado):
        tarjeta = tarjeta_seccion(parent, "Matriz reducida",
                                  "Del sistema homogéneo [A | 0] a su forma escalonada por filas "
                                  "(el procedimiento completo está en la pestaña Procedimiento).")
        etiqueta(tarjeta, "SISTEMA HOMOGÉNEO [A | 0]", FUENTE_PEQUENA_NEGRITA, "texto_3").pack(anchor="w", padx=16)
        dibujar_matriz(tarjeta, resultado["matriz_homogenea"]).pack(anchor="w", padx=8, pady=(2, 10))
        etiqueta(tarjeta, "FORMA ESCALONADA POR FILAS", FUENTE_PEQUENA_NEGRITA, "texto_3").pack(anchor="w", padx=16)
        dibujar_matriz(tarjeta, resultado["matriz_escalonada"],
                       pivotes=list(enumerate(resultado["columnas_pivote"]))).pack(anchor="w", padx=8, pady=(2, 8))
        columnas = ", ".join(str(c + 1) for c in resultado["columnas_pivote"]) or "ninguna"
        libres = ", ".join(resultado["nombres_libres"]) or "ninguna"
        etiqueta(tarjeta, f"Columnas pivote: {columnas}      Variables libres: {libres}",
                 FUENTE_NEGRITA, "texto", ajustar=44).pack(anchor="w", padx=16, pady=(0, 16))
        return tarjeta

    @staticmethod
    def _tarjeta_veredicto(parent, resultado):
        independiente = resultado["independiente"]
        tarjeta = tarjeta_seccion(parent, "Veredicto teórico")
        fila = ctk.CTkFrame(tarjeta, fg_color="transparent")
        fila.pack(fill="x", padx=16, pady=(0, 8))
        chip(fila, "L.I." if independiente else "L.D.", "exito" if independiente else "advertencia",
             TEXTO_SOBRE_PRIMARIO, (FAMILIA, 15, "bold")).pack(side="left")
        etiqueta(fila, resultado["veredicto"], FUENTE_SECCION, "texto").pack(side="left", padx=(12, 0))
        etiqueta(tarjeta, resultado["justificacion"], FUENTE_NORMAL, "texto_2", ajustar=44).pack(
            anchor="w", padx=16)
        etiqueta(tarjeta, resultado["teorema"], FUENTE_PEQUENA, "texto_3", ajustar=44).pack(
            anchor="w", padx=16, pady=(8, 16))
        return tarjeta

    def texto_copiar(self, resultado):
        return "\n".join(informe_independencia(resultado))

    def mensaje_resuelto(self, resultado):
        mensaje = (f"Veredicto: {resultado['veredicto']} · "
                   f"{_plural(resultado['num_pivotes'], 'pivote', 'pivotes')}, "
                   f"{_plural(resultado['num_libres'], 'variable libre', 'variables libres')}.")
        return mensaje, "exito" if resultado["independiente"] else "aviso"


class PaginaPropiedades(PaginaSistema):
    titulo = "Propiedades del producto Av"
    subtitulo = ("Carga las columnas a1, a2, … de A y el vector v (y, si quieres, u): calcula "
                 "Av = v1·a1 + … + vn·an y comprueba sus propiedades")
    etiqueta_filas = "Componentes (m)"
    etiqueta_columnas = "Vectores a1…an (n)"
    filas_inicial = 2
    columnas_inicial = 3
    titulo_datos = "Columnas de A y vectores"
    texto_boton = "Calcular Av"
    # nombre: (m, n, (A, v, c, u)); u se usa solo si se activa con «Añadir u».
    ejemplos = {
        "Ejemplo del libro (2×3)": (2, 3, ([[1, 2, -1], [0, -5, 3]], [4, 3, 7], "2", [2, 0, -1])),
        "Matriz 2×2": (2, 2, ([[1, 2], [3, 4]], [1, -1], "3", [0, 2])),
        "Tres columnas en R³": (3, 3, ([[1, 0, 2], [2, 1, 0], [0, 3, 1]], [2, -1, 1], "-2", [1, 1, -1])),
        "Con fracciones": (3, 2, ([["1/2", 1], [0, "3/4"], [2, -1]], [2, "1/3"], "1/2", ["1/2", -1])),
    }
    ejemplo_inicial = "Ejemplo del libro (2×3)"
    vacio_resultado = "Escribe las columnas a1…an, el vector v y c, y presiona «Calcular Av»."
    vacio_pasos = "Aquí aparecerá Av como combinación de las columnas y la comprobación fila por fila."

    def __init__(self, parent, app):
        self.con_u = False
        self._u_guardado = []
        super().__init__(parent, app)

    def controles_extra(self, fila):
        grupo = ctk.CTkFrame(fila, fg_color="transparent")
        grupo.pack(side="left", padx=(0, 18))
        etiqueta(grupo, "Escalar c", FUENTE_PEQUENA_NEGRITA, "texto_3").pack(anchor="w", pady=(0, 4))
        self.entrada_c = ctk.CTkEntry(grupo, width=74, height=34, justify="center", font=FUENTE_MONO,
                                      corner_radius=10, border_width=2, fg_color=PALETA["entrada"],
                                      border_color=PALETA["borde"], text_color=PALETA["texto"])
        self.entrada_c.insert(0, "2")
        self.entrada_c.pack(anchor="w")
        self.entrada_c.bind("<KeyRelease>", lambda _e: self._validar_c())

    def _validar_c(self):
        valido = _numero_o_nada(self.entrada_c.get()) is not None
        self.entrada_c.configure(border_color=PALETA["borde"] if valido else PALETA["error"])
        self._al_cambiar_datos()

    def construir_entradas(self, parent):
        etiqueta(parent, "Matriz A = [a1  a2  …  an]  (cada columna es un vector)", FUENTE_PEQUENA_NEGRITA,
                 "texto_3").pack(anchor="w", padx=4, pady=(4, 2))
        self.matriz_a = MatrizEntrada(parent, al_cambiar=self._al_cambiar_datos)
        self.matriz_a.pack(anchor="w", padx=4)

        # El tamano de v (y u) es el mismo n que la cantidad de columnas a1…an
        # (Av solo existe asi), por eso ambos contadores van sincronizados.
        cabecera = ctk.CTkFrame(parent, fg_color="transparent")
        cabecera.pack(anchor="w", padx=4, pady=(14, 4))
        self.etiqueta_vectores = etiqueta(cabecera, "Vector v", FUENTE_PEQUENA_NEGRITA, "texto_3")
        self.etiqueta_vectores.pack(side="left", anchor="s", pady=(0, 6))
        self.contador_v = Contador(cabecera, "Componentes (n)", self.contador_columnas.get(),
                                   self.minimo_columnas, LIMITE_DIMENSION, self._cambiar_tamano_v)
        self.contador_v.pack(side="left", padx=(16, 0))
        self.boton_u = boton_secundario(cabecera, "+  Añadir u", self.alternar_u, width=112, height=30,
                                        font=FUENTE_PEQUENA_NEGRITA)
        self.boton_u.pack(side="left", anchor="s", padx=(12, 0), pady=(0, 2))
        self.matriz_v = MatrizEntrada(parent, al_cambiar=self._al_cambiar_datos)
        self.matriz_v.pack(anchor="w", padx=4)
        etiqueta(parent, "Los vectores tienen una componente por cada columna a1…an: al cambiar n también "
                         "cambia la cantidad de columnas de A.",
                 FUENTE_PEQUENA, "texto_3", ajustar=40).pack(anchor="w", padx=4, pady=(6, 0))

    def _cambiar_tamano_v(self, componentes):
        self.contador_columnas.set(componentes)
        self.reconstruir()

    def alternar_u(self):
        """Muestra u como una segunda columna junto a v (o la quita), conservando los valores escritos."""
        textos = self.matriz_v.textos()
        if self.con_u:
            self._u_guardado = [fila[1] for fila in textos]
        self.con_u = not self.con_u
        self.boton_u.configure(text="−  Quitar u" if self.con_u else "+  Añadir u")
        self.etiqueta_vectores.configure(text="Vectores v y u" if self.con_u else "Vector v")
        valores = []
        for i, fila in enumerate(textos):
            valores.append([fila[0]] + ([self._u_guardado[i] if i < len(self._u_guardado) else "0"]
                                        if self.con_u else []))
        self._configurar_v(len(textos), valores)
        self.etiqueta_dimension.configure(
            text=self.texto_dimension(self.contador_filas.get(), self.contador_columnas.get()))
        self._al_cambiar_datos()
        if self.con_u:
            self.matriz_v.celdas[0][1].focus_set()

    def _configurar_v(self, componentes, valores=None):
        encabezados = ["v", "u"] if self.con_u else ["v"]
        self.matriz_v.configurar(componentes, len(encabezados), encabezados,
                                 [str(i + 1) for i in range(componentes)], None, valores)

    def crear_procedimiento(self, pestana):
        self.area_pasos = AreaDesplazable(pestana, PALETA["panel"])
        self.area_pasos.pack(fill="both", expand=True)

    def texto_dimension(self, filas, columnas):
        vectores = "u, v" if self.con_u else "v"
        return f"A: {filas} × {columnas} · {vectores} ∈ {espacio_real(columnas)}"

    def configurar_entradas(self, filas, columnas, valores):
        A = v = None
        if valores is not None:
            A, v, c, u = valores
            self._u_guardado = [str(x) for x in u]
            self.entrada_c.delete(0, "end")
            self.entrada_c.insert(0, str(c))
            self.entrada_c.configure(border_color=PALETA["borde"])
        self.matriz_a.configurar(filas, columnas, [f"a{j + 1}" for j in range(columnas)],
                                 [str(i + 1) for i in range(filas)], None, A)
        filas_v = None
        if v is not None:
            filas_v = [[v[i]] + ([self._u_guardado[i]] if self.con_u else []) for i in range(columnas)]
        self._configurar_v(columnas, filas_v)
        self.contador_v.set(columnas)

    def valores_previa(self):
        A = [[_numero_o_nada(t) for t in fila] for fila in self.matriz_a.textos()]
        vectores = [[_numero_o_nada(t) for t in fila] for fila in self.matriz_v.textos()]
        v = [fila[0] for fila in vectores]
        u = [fila[1] for fila in vectores] if self.con_u else None
        return A, v, u, _numero_o_nada(self.entrada_c.get())

    def construir_previa(self, parent, valores):
        A, v, u, c = valores
        partes = ["A =", A, "  v =", v] + (["  u =", u] if u is not None else [])
        dibujar_expresion(parent, partes, tamano=12).pack(anchor="w")
        simbolos = [f"a{j + 1}" for j in range(len(v))]
        for nombre, vector in (("v", v), ("u", u)):
            if vector is None:
                continue
            if all(x is not None for x in vector):
                combinacion = formatear_combinacion_lineal(vector, simbolos)
            else:
                combinacion = " + ".join(f"{nombre}{j + 1}·{s}" for j, s in enumerate(simbolos))
            etiqueta(parent, f"A{nombre} = {combinacion}", FUENTE_MONO, "texto", ajustar=40).pack(
                anchor="w", pady=(6 if nombre == "v" else 2, 0))
        etiqueta(parent, f"c = {_texto_valor(c)}", FUENTE_MONO, "texto" if c is not None else "error").pack(
            anchor="w", pady=(2, 0))

    def leer_datos(self):
        A = self.matriz_a.valores()
        vectores = self.matriz_v.valores()
        try:
            c = convertir_numero(self.entrada_c.get())
        except ValueError as error:
            self.entrada_c.configure(border_color=PALETA["error"])
            raise ValueError(f"Escalar c: {error}") from None
        v = [fila[0] for fila in vectores]
        u = [fila[1] for fila in vectores] if self.con_u else None
        return A, v, c, u

    def limpiar_entradas(self):
        self.matriz_a.limpiar()
        self.matriz_v.limpiar()

    def valores_aleatorios(self, filas, columnas):
        A = [[random.randint(-4, 4) for _ in range(columnas)] for _ in range(filas)]
        v = [random.randint(-3, 3) for _ in range(columnas)]
        u = [random.randint(-3, 3) for _ in range(columnas)]
        return A, v, str(random.choice([-3, -2, 2, 3, 4])), u

    def calcular(self, datos):
        return analizar_producto_av(*datos)

    @staticmethod
    def _coeficiente(valor):
        return ("-" if valor < 0 else "") + formatear_coeficiente(valor)

    @staticmethod
    def _todo_se_cumple(datos):
        return datos["propiedad"] and datos["propiedad_suma"] is not False

    def construir_resultado(self, datos):
        c = formatear_numero(datos["c"])
        con_u = datos["u"] is not None
        cumple = self._todo_se_cumple(datos)
        propiedades = "A(cv) = c(Av) y A(u + v) = Au + Av" if con_u else "A(cv) = c(Av)"
        estado = (
            "Productos Av y Au calculados" if con_u else "Producto Av calculado",
            f"Av = {datos['combinacion']}. " + (f"Se cumple {propiedades}." if cumple
                                              else "Alguna propiedad no se cumple."),
            PALETA["exito"] if cumple else PALETA["error"], "✓" if cumple else "✕",
        )

        def combinacion(parent, nombre, vector, resultado, texto):
            tarjeta = tarjeta_seccion(parent, f"A{nombre} como combinación de las columnas de A",
                                      f"Cada columna aj se multiplica por la componente {nombre}j y luego se suman.")
            etiqueta(tarjeta, f"A{nombre} = {texto}", (FAMILIA_MONO, 16, "bold"), "primario",
                     ajustar=44).pack(anchor="w", padx=16)
            dibujar_expresion(tarjeta, [f"A{nombre} ="] + partes_combinacion(vector, datos["columnas"], resultado),
                              tamano=13).pack(anchor="w", padx=14, pady=(6, 0))
            partes = ["="]
            for j, columna in enumerate(datos["columnas"]):
                partes += (["+"] if j else []) + [[vector[j] * valor for valor in columna]]
            dibujar_expresion(tarjeta, partes + ["=", resultado], tamano=13).pack(anchor="w", padx=14, pady=(0, 14))

        def fila_por_fila(parent):
            tarjeta = tarjeta_seccion(parent, "Comprobación fila por fila",
                                      "Cada componente de Av es el producto de una fila de A por v.")
            for linea in detalle_producto_matriz_vector(datos["A"], datos["v"]):
                etiqueta(tarjeta, linea, FUENTE_MONO, "texto_2").pack(anchor="w", padx=16)
            dibujar_expresion(tarjeta, ["Av =", datos["Av"]]).pack(anchor="w", padx=14, pady=(6, 14))

        def comparar(parent, titulo, lineas_de_partes, se_cumple):
            tarjeta = tarjeta_seccion(parent, titulo)
            for partes in lineas_de_partes:
                dibujar_expresion(tarjeta, partes, tamano=13).pack(anchor="w", padx=14)
            etiqueta(tarjeta, ("✓  Los dos vectores son iguales." if se_cumple else "✕  Los vectores son distintos."),
                     FUENTE_NEGRITA, "exito" if se_cumple else "error", ajustar=44).pack(
                anchor="w", padx=16, pady=(6, 16))

        constructores = [
            lambda p: tarjeta_estado(p, *estado),
            lambda p: combinacion(p, "v", datos["v"], datos["Av"], datos["combinacion"]),
        ]
        if con_u:
            constructores.append(lambda p: combinacion(p, "u", datos["u"], datos["Au"], datos["combinacion_u"]))
        constructores += [
            fila_por_fila,
            lambda p: comparar(p, f"Propiedad  A(cv) = c(Av)   con c = {c}",
                               [["cv =", datos["cv"]], ["A(cv) =", datos["A_cv"], " c(Av) =", datos["c_Av"]]],
                               datos["propiedad"]),
        ]
        if con_u:
            constructores.append(lambda p: comparar(
                p, "Propiedad  A(u + v) = Au + Av",
                [["u + v =", datos["u_mas_v"]], ["A(u + v) =", datos["A_u_mas_v"], " Au + Av =", datos["Au_mas_Av"]]],
                datos["propiedad_suma"]))
        return constructores

    def mostrar_procedimiento(self, datos):
        c = formatear_numero(datos["c"])
        n = len(datos["v"])
        con_u = datos["u"] is not None
        columnas = []
        for j, columna in enumerate(datos["columnas"]):
            columnas += [f"a{j + 1} =", columna]
        escaladas = []
        for j, termino in enumerate(datos["terminos"]):
            escaladas += [f"{self._coeficiente(datos['v'][j])}·a{j + 1} =", termino]
        suma = []
        for j, termino in enumerate(datos["terminos"]):
            suma += (["+"] if j else []) + [termino]
        simbolica = " + ".join(f"v{j + 1}·a{j + 1}" for j in range(n))
        comparaciones = [f"A(cv) {'=' if datos['propiedad'] else '≠'} c(Av)"]

        pasos = [
            ("Datos", None, (["A =", datos["A"]],
                             ["v =", datos["v"]] + (["u =", datos["u"]] if con_u else []) + [f"c = {c}"])),
            ("Separar A en sus columnas a1 … an", None, columnas),
            ("Escribir Av como combinación lineal de las columnas",
             [f"Av = {simbolica}", f"Av = {datos['combinacion']}"], None),
            ("Multiplicar cada columna por su componente de v", None, escaladas),
            ("Sumar los vectores obtenidos", None, suma + ["=", datos["Av"]]),
            ("Comprobar fila por fila", detalle_producto_matriz_vector(datos["A"], datos["v"]), None),
            (f"Multiplicar v por c = {c}", None, ["cv =", datos["cv"]]),
            ("Calcular A(cv)", detalle_producto_matriz_vector(datos["A"], datos["cv"]), None),
            (f"Multiplicar Av por c = {c}", None, ["c(Av) =", datos["c_Av"]]),
        ]
        if con_u:
            comparaciones.append(f"A(u + v) {'=' if datos['propiedad_suma'] else '≠'} Au + Av")
            pasos += [
                ("Calcular Au como combinación de las columnas",
                 [f"Au = {datos['combinacion_u']}"] + detalle_producto_matriz_vector(datos["A"], datos["u"]),
                 ["Au =", datos["Au"]]),
                ("Sumar u + v componente a componente", None, ["u + v =", datos["u_mas_v"]]),
                ("Calcular A(u + v)", detalle_producto_matriz_vector(datos["A"], datos["u_mas_v"]), None),
                ("Sumar Au + Av", None, ["Au + Av =", datos["Au_mas_Av"]]),
            ]
        pasos.append(("Comparar", comparaciones, None))

        def tarjeta(parent, numero, titulo, lineas, partes):
            marco = ctk.CTkFrame(parent, fg_color=PALETA["panel_2"], corner_radius=12,
                                 border_width=1, border_color=PALETA["borde"])
            marco.pack(fill="x", padx=2, pady=(0, 12))
            cabecera = ctk.CTkFrame(marco, fg_color="transparent")
            cabecera.pack(fill="x", padx=14, pady=(12, 6))
            chip(cabecera, f"Paso {numero}", "primario", TEXTO_SOBRE_PRIMARIO).pack(side="left")
            etiqueta(cabecera, titulo, FUENTE_NEGRITA, "texto", ajustar=120).pack(side="left", padx=(10, 0))
            for linea in lineas or []:
                etiqueta(marco, linea, FUENTE_MONO, "texto_2").pack(anchor="w", padx=18)
            # partes puede ser una sola expresion (lista) o varias lineas (tupla de listas).
            for linea in (partes if isinstance(partes, tuple) else [partes] if partes else []):
                dibujar_expresion(marco, linea, tamano=13).pack(anchor="w", padx=14)
            ctk.CTkFrame(marco, fg_color="transparent", height=10).pack()
            efecto_hover(marco)

        self.area_pasos.llenar([
            lambda p, n=n, paso=paso: tarjeta(p, n, *paso) for n, paso in enumerate(pasos, start=1)
        ])

    def procedimiento_vacio(self):
        self.area_pasos.llenar([lambda p: placeholder(p, "☰", self.vacio_pasos)])

    @staticmethod
    def _vector(valores):
        return "(" + ", ".join(formatear_numero(x) for x in valores) + ")"

    def texto_copiar(self, datos):
        vec = self._vector
        lineas = [
            f"Av = {datos['combinacion']} = {vec(datos['Av'])}",
            f"A(cv) = {vec(datos['A_cv'])}   c(Av) = {vec(datos['c_Av'])}",
        ]
        if datos["u"] is not None:
            lineas += [
                f"Au = {datos['combinacion_u']} = {vec(datos['Au'])}",
                f"A(u + v) = {vec(datos['A_u_mas_v'])}   Au + Av = {vec(datos['Au_mas_Av'])}",
            ]
        return "\n".join(lineas)

    def mensaje_resuelto(self, datos):
        if not self._todo_se_cumple(datos):
            return "Alguna propiedad no se cumplió.", "error"
        if datos["u"] is not None:
            return (f"Av = {self._vector(datos['Av'])}, Au = {self._vector(datos['Au'])} · "
                    f"se cumplen ambas propiedades."), "exito"
        return f"Av = {self._vector(datos['Av'])} · se cumple A(cv) = c(Av).", "exito"


class PaginaMatrices(PaginaBase):
    """Interfaz integrada para cálculo, verificación y práctica de matrices."""
    titulo = "Operaciones con Matrices y Propiedades Teóricas"
    subtitulo = "Resultados exactos, procedimientos verificables y conclusiones para examen"

    OPCIONES = ("A + B", "A − B", "rA", "Aᵀ", "AB", "Propiedades de la transpuesta",
                "Propiedades algebraicas", "Contraejemplos", "Ejercicios tipo examen")

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.grid_rowconfigure(1, weight=1)
        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        cuerpo.grid_columnconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(1, weight=1)
        controles = crear_tarjeta(cuerpo, "Datos y operación")
        controles.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        fila = ctk.CTkFrame(controles, fg_color="transparent")
        fila.pack(fill="x", padx=16, pady=12)
        self.dimension_a = ctk.CTkEntry(fila, width=68, placeholder_text="2×2")
        self.dimension_b = ctk.CTkEntry(fila, width=68, placeholder_text="2×2")
        self.dimension_c = ctk.CTkEntry(fila, width=68, placeholder_text="2×2")
        self.dimension_a.insert(0, "2x2")
        self.dimension_b.insert(0, "2x2")
        self.dimension_c.insert(0, "2x2")
        etiqueta(fila, "A:", FUENTE_PEQUENA_NEGRITA, "texto").pack(side="left")
        self.dimension_a.pack(side="left", padx=(5, 14))
        etiqueta(fila, "B:", FUENTE_PEQUENA_NEGRITA, "texto").pack(side="left")
        self.dimension_b.pack(side="left", padx=(5, 14))
        etiqueta(fila, "C:", FUENTE_PEQUENA_NEGRITA, "texto").pack(side="left")
        self.dimension_c.pack(side="left", padx=(5, 14))
        boton_secundario(fila, "Actualizar dimensiones", self.reconstruir, width=170).pack(side="left", padx=(0, 14))
        self.operacion = ctk.CTkOptionMenu(fila, values=list(self.OPCIONES), width=230)
        self.operacion.set("A + B")
        self.operacion.pack(side="left", padx=(0, 12))
        etiqueta(fila, "r:", FUENTE_PEQUENA_NEGRITA, "texto").pack(side="left")
        self.escalar = ctk.CTkEntry(fila, width=75)
        self.escalar.insert(0, "1/2")
        self.escalar.pack(side="left", padx=5)
        boton_primario(fila, "Calcular y comprobar", self.calcular, width=195).pack(side="right")

        izquierda = crear_tarjeta(cuerpo, "Matrices de entrada")
        izquierda.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.entrada_area = AreaDesplazable(izquierda, PALETA["panel"])
        self.entrada_area.pack(fill="both", expand=True, padx=12, pady=12)
        derecha = crear_tarjeta(cuerpo, "Resultado, procedimiento y comprobación")
        derecha.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        self.salida = ctk.CTkTextbox(derecha, wrap="word", font=FUENTE_MONO, fg_color=PALETA["entrada"], text_color=PALETA["texto"])
        self.salida.pack(fill="both", expand=True, padx=12, pady=12)
        self.reconstruir()

    @staticmethod
    def _dimension(texto):
        partes = texto.lower().replace("×", "x").split("x")
        if len(partes) != 2:
            raise ValueError("Usa dimensiones positivas con el formato filas×columnas; por ejemplo, 2x3.")
        filas, columnas = (int(x.strip()) for x in partes)
        if not (1 <= filas <= LIMITE_DIMENSION and 1 <= columnas <= LIMITE_DIMENSION):
            raise ValueError(f"Cada dimensión debe estar entre 1 y {LIMITE_DIMENSION}.")
        return filas, columnas

    def reconstruir(self):
        try:
            fa, ca = self._dimension(self.dimension_a.get())
            fb, cb = self._dimension(self.dimension_b.get())
            fc, cc = self._dimension(self.dimension_c.get())
        except ValueError as error:
            self._escribir("Error de dimensiones\n\n" + str(error))
            return
        self.entrada_area.limpiar()
        p = self.entrada_area.interior
        etiqueta(p, f"A ({fa}×{ca})", FUENTE_SECCION, "primario").pack(anchor="w")
        self.entrada_a = MatrizEntrada(p)
        self.entrada_a.pack(anchor="w", padx=4, pady=(4, 14))
        self.entrada_a.configurar(fa, ca, [f"a{j + 1}" for j in range(ca)], valores=[[1 if i == j else 0 for j in range(ca)] for i in range(fa)])
        etiqueta(p, f"B ({fb}×{cb})", FUENTE_SECCION, "primario").pack(anchor="w")
        self.entrada_b = MatrizEntrada(p)
        self.entrada_b.pack(anchor="w", padx=4, pady=(4, 14))
        self.entrada_b.configurar(fb, cb, [f"b{j + 1}" for j in range(cb)], valores=[[1 if i == j else 0 for j in range(cb)] for i in range(fb)])
        etiqueta(p, f"C ({fc}×{cc})", FUENTE_SECCION, "primario").pack(anchor="w")
        self.entrada_c = MatrizEntrada(p)
        self.entrada_c.pack(anchor="w", padx=4, pady=(4, 14))
        self.entrada_c.configurar(fc, cc, [f"c{j + 1}" for j in range(cc)], valores=[[1 if i == j else 0 for j in range(cc)] for i in range(fc)])
        etiqueta(p, "Para las propiedades algebraicas, elija A, B y C con las dimensiones compatibles requeridas por cada producto.", FUENTE_PEQUENA, "texto_3", ajustar=45).pack(anchor="w", padx=4)
        self._escribir("Ingrese las matrices. Se aceptan enteros, decimales y fracciones exactas como −3/2.")

    def _escribir(self, texto):
        self.salida.configure(state="normal")
        self.salida.delete("1.0", "end")
        self.salida.insert("1.0", texto)
        self.salida.configure(state="disabled")

    @staticmethod
    def _matriz_texto(A):
        return matriz_a_texto(validar_matriz(A))

    def _comparacion_texto(self, nombre, dato):
        if dato.get("definida") is False:
            return f"{nombre}: no aplicable\n{dato['error']}\n"
        lineas = [f"{nombre}", f"Lado izquierdo ({dato['dimensiones_izquierda'][0]}×{dato['dimensiones_izquierda'][1]}):\n{self._matriz_texto(dato['izquierda'])}",
                  f"Lado derecho ({dato['dimensiones_derecha'][0]}×{dato['dimensiones_derecha'][1]}):\n{self._matriz_texto(dato['derecha'])}",
                  ("✓ Coinciden exactamente entrada por entrada." if dato["coinciden"] else f"✗ Diferencias: {dato['diferencias']}"),
                  "Esta es una verificación del caso introducido; no sustituye la demostración algebraica general.\n"]
        return "\n".join(lineas)

    def calcular(self):
        try:
            A, B, C, r = self.entrada_a.valores(), self.entrada_b.valores(), self.entrada_c.valores(), convertir_numero(self.escalar.get())
            op = self.operacion.get()
            if op in ("A + B", "A − B", "rA", "Aᵀ", "AB"):
                clave = {"A + B": "suma", "A − B": "resta", "rA": "escalar", "Aᵀ": "transpuesta", "AB": "producto"}[op]
                dato = procedimiento_operacion_matrices(A, clave, B, r)
                texto = f"{op}\n\nA =\n{self._matriz_texto(A)}\n\n" + (f"B =\n{self._matriz_texto(B)}\n\n" if clave in ("suma", "resta", "producto") else "")
                texto += "PROCEDIMIENTO\n" + "\n".join(f"{i + 1}. {x}" for i, x in enumerate(dato["pasos"]))
                texto += f"\n\nRESULTADO\n{self._matriz_texto(dato['resultado'])}\n\nCONCLUSIÓN\n{dato['conclusion']}"
            elif op == "Propiedades de la transpuesta":
                datos = verificar_propiedades_transpuesta(A, B, r)
                nombres = {"doble": "(Aᵀ)ᵀ = A", "suma": "(A+B)ᵀ = Aᵀ+Bᵀ", "escalar": "(rA)ᵀ = rAᵀ", "producto": "(AB)ᵀ = BᵀAᵀ"}
                texto = "PROPIEDADES DE LA TRANSPUESTA\n\n" + "\n".join(self._comparacion_texto(nombres[k], v) for k, v in datos.items())
            elif op == "Propiedades algebraicas":
                datos = verificar_propiedades_algebraicas(A, B, C, r, Fraction(2))
                texto = "PROPIEDADES ALGEBRAICAS (s = 2)\n\n" + "\n".join(self._comparacion_texto(k.replace("_", " "), v) for k, v in datos.items())
            elif op == "Contraejemplos":
                datos = contraejemplos_matriciales()
                texto = "CONTRAEJEMPLOS: AFIRMACIONES FALSAS EN GENERAL\n\n"
                for nombre, dato in datos.items():
                    texto += nombre.replace("_", " ").upper() + "\n"
                    for clave, valor in dato.items():
                        texto += f"{clave} =\n{self._matriz_texto(valor)}\n" if isinstance(valor, list) else f"{clave}: {valor}\n"
                    texto += "\n"
            else:
                texto = "EJERCICIOS TIPO EXAMEN\n\n"
                for numero, ejercicio in enumerate(ejercicios_matrices(), 1):
                    texto += f"{numero}. {ejercicio['tema']}\n{ejercicio['consigna']}\n"
                    for clave in ("A", "B"):
                        if clave in ejercicio:
                            texto += f"{clave} =\n{self._matriz_texto([[convertir_numero(x) for x in fila] for fila in ejercicio[clave]])}\n"
                    texto += "\n"
            self._escribir(texto)
        except ValueError as error:
            self._escribir("OPERACIÓN NO REALIZADA\n\n" + str(error) + "\n\nRevise las dimensiones antes de calcular.")


class PaginaInformativa(PaginaBase):
    """Pagina de lectura: las tarjetas aparecen en cascada cada vez que se abre."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.grid_rowconfigure(1, weight=1)
        self.area = AreaDesplazable(self, PALETA["fondo"])
        self.area.grid(row=1, column=0, sticky="nsew", padx=(24, 12), pady=(0, 20))

    def constructores(self):
        return []

    def al_mostrar(self):
        super().al_mostrar()
        self.area.llenar(self.constructores(), retardo=55)


def tarjeta_numerada(parent, numero, titulo, texto):
    tarjeta = crear_tarjeta(parent)
    tarjeta.pack(fill="x", pady=(0, 12), padx=(0, 4))
    ctk.CTkLabel(tarjeta, text=str(numero), width=36, height=36, corner_radius=18, fg_color=PALETA["primario"],
                 text_color=TEXTO_SOBRE_PRIMARIO, font=(FAMILIA, 15, "bold")).pack(side="left", anchor="n",
                                                                                  padx=16, pady=16)
    textos = ctk.CTkFrame(tarjeta, fg_color="transparent")
    textos.pack(side="left", fill="x", expand=True, pady=14, padx=(0, 16))
    etiqueta(textos, titulo, (FAMILIA, 15, "bold"), "texto").pack(anchor="w")
    etiqueta(textos, texto, FUENTE_NORMAL, "texto_2", ajustar=110).pack(anchor="w", pady=(4, 0))
    efecto_hover(tarjeta)
    return tarjeta


class PaginaMetodo(PaginaInformativa):
    titulo = "Método de eliminación de Gauss-Jordan"
    subtitulo = "Cómo el programa reduce la matriz aumentada paso a paso"

    PASOS = [
        ("Matriz aumentada [A | b]",
         "Se colocan juntos los coeficientes A y la columna de términos independientes b. Cada fila representa una ecuación."),
        ("Buscar el pivote",
         "Se recorre cada columna de izquierda a derecha. Si en la posición pivote hay un 0, se intercambia esa fila "
         "con la primera fila de abajo que tenga un valor distinto de cero (Fi ↔ Fj)."),
        ("Convertir el pivote en 1",
         "La fila del pivote se multiplica por el inverso del pivote (Fi → (1/k)Fi)."),
        ("Hacer ceros en la columna",
         "A cada una de las demás filas se le suma un múltiplo de la fila pivote para anular la columna, "
         "arriba y abajo del pivote (Fi → Fi − k·Fp)."),
        ("Repetir con la siguiente columna",
         "Se continúa hasta llegar a la forma escalonada reducida: cada pivote vale 1 y es el único valor no nulo de su columna."),
        ("Clasificar el sistema",
         "Si aparece una fila 0 = k con k ≠ 0, el sistema es inconsistente. Si todas las variables tienen pivote, "
         "hay solución única. Si alguna no tiene pivote, hay infinitas soluciones."),
        ("Variables básicas y libres",
         "Las columnas con pivote son variables básicas; las demás son libres y se expresan con parámetros (t, s, r, …)."),
        ("Verificar la solución",
         "Los valores obtenidos se sustituyen en el sistema original (Ax = b) para comprobar cada ecuación."),
    ]

    def constructores(self):
        lista = [
            lambda p, n=n, t=titulo, x=texto: tarjeta_numerada(p, n, t, x)
            for n, (titulo, texto) in enumerate(self.PASOS, start=1)
        ]
        _, _, pasos = gauss_jordan([[Fraction(2), Fraction(1), Fraction(5)],
                                    [Fraction(1), Fraction(-1), Fraction(1)]], 2)

        def encabezado(parent):
            marco = ctk.CTkFrame(parent, fg_color="transparent")
            marco.pack(fill="x", pady=(14, 10))
            etiqueta(marco, "Ejemplo resuelto", FUENTE_SECCION, "texto").pack(anchor="w")
            etiqueta(marco, "2x1 + x2 = 5   y   x1 − x2 = 1.  La fila modificada se resalta y el pivote va encerrado.",
                     FUENTE_NORMAL, "texto_2").pack(anchor="w", pady=(2, 0))

        lista.append(encabezado)
        lista += [
            lambda p, i=i: TarjetaPaso(p, pasos, i, fondo=PALETA["fondo"]).pack(fill="x", pady=(0, 12), padx=(0, 4))
            for i in range(len(pasos))
        ]
        return lista


class PaginaAyuda(PaginaInformativa):
    titulo = "Ayuda"
    subtitulo = "Cómo usar la calculadora y significado de los conceptos clave"

    USO = [
        "Elige una sección en el menú lateral. Ajusta el tamaño con los botones − y +; los valores ya escritos se conservan.",
        "Escribe los datos en las casillas. Una casilla con borde rojo tiene un valor no válido.",
        "Revisa la vista previa: muestra el sistema o la ecuación vectorial que se va a resolver.",
        f"Presiona el botón para resolver (o {ATAJO_RESOLVER}). El resultado aparece en la pestaña «Resultado».",
        "En «Procedimiento» elige «Todos» para ver cada operación o «Paso a paso» para avanzar (o reproducir) una a una.",
        "¿Sin datos? Usa «Cargar ejemplo…» o «Aleatorio». «Limpiar» pone todas las casillas en 0.",
    ]
    ATAJOS = [
        ("Enter", "Ir a la siguiente casilla"),
        ("↑  /  ↓", "Moverse a la casilla de arriba o de abajo"),
        (ATAJO_RESOLVER, "Resolver en la sección actual"),
        ("Shift + rueda", "Desplazamiento horizontal"),
    ]
    FORMATOS = [("Enteros", "3,  -7"), ("Decimales", "0.25  o  0,25"), ("Fracciones", "3/2,  -1/4")]
    CONCEPTOS = [
        ("Matriz aumentada", "La matriz [A | b] que combina los coeficientes del sistema con los términos independientes."),
        ("Operación elemental", "Intercambiar filas, multiplicar una fila por un escalar no nulo o sumar a una fila un múltiplo de otra."),
        ("Pivote", "El primer valor distinto de cero de una fila, usado para eliminar el resto de su columna."),
        ("Forma escalonada por filas", "Debajo de cada pivote solo hay ceros y cada pivote queda a la derecha del de la fila anterior."),
        ("Forma escalonada reducida", "Cada pivote vale 1 y es el único valor distinto de cero en su columna."),
        ("Rango", "La cantidad de pivotes. Si rango(A) < rango([A | b]) el sistema es inconsistente."),
        ("Variables básicas y libres", "Básicas: columnas con pivote. Libres: columnas sin pivote, se expresan con parámetros."),
        ("Combinación lineal", "Un vector de la forma c1·v1 + … + cn·vn. w ∈ Gen{v1, …, vn} si existe tal combinación igual a w."),
        ("Independencia lineal", "Los vectores son L.I. si c1·v1 + … + cp·vp = 0 solo se cumple con todos los ci = 0: "
                                 "en la forma escalonada de [A | 0] hay un pivote en cada columna."),
        ("Sistema homogéneo", "Todos los términos independientes son 0 (Ax = 0). Siempre tiene al menos la solución trivial."),
        ("Producto Ax", "Si A = [a1 … an], entonces Ax = x1·a1 + … + xn·an: una combinación lineal de las columnas de A."),
        ("Linealidad de Ax", "Para toda matriz A: A(u + v) = Au + Av y A(cu) = c(Au)."),
    ]

    def constructores(self):
        def uso(parent):
            tarjeta = crear_tarjeta(parent, "Cómo usar la calculadora")
            tarjeta.pack(fill="x", pady=(0, 12), padx=(0, 4))
            for n, texto in enumerate(self.USO, start=1):
                fila = ctk.CTkFrame(tarjeta, fg_color="transparent")
                fila.pack(fill="x", padx=18, pady=3)
                ctk.CTkLabel(fila, text=str(n), width=24, height=24, corner_radius=12, fg_color=PALETA["secundario"],
                             text_color=PALETA["primario"], font=FUENTE_PEQUENA_NEGRITA).pack(side="left", anchor="n")
                etiqueta(fila, texto, FUENTE_NORMAL, "texto_2", ajustar=96).pack(side="left", padx=(10, 0))
            ctk.CTkFrame(tarjeta, fg_color="transparent", height=10).pack()
            efecto_hover(tarjeta)

        def atajos_y_formatos(parent):
            fila = ctk.CTkFrame(parent, fg_color="transparent")
            fila.pack(fill="x", pady=(0, 12), padx=(0, 4))
            fila.grid_columnconfigure((0, 1), weight=1, uniform="ayuda")
            for columna, (titulo, datos) in enumerate((("Atajos de teclado", self.ATAJOS),
                                                         ("Números aceptados", self.FORMATOS))):
                tarjeta = crear_tarjeta(fila, titulo)
                tarjeta.grid(row=0, column=columna, sticky="nsew", padx=(0, 12) if columna == 0 else 0)
                for clave, texto in datos:
                    renglon = ctk.CTkFrame(tarjeta, fg_color="transparent")
                    renglon.pack(fill="x", padx=18, pady=3)
                    chip(renglon, clave, "entrada", "primario", FUENTE_MONO).pack(side="left")
                    etiqueta(renglon, texto, FUENTE_NORMAL, "texto_2").pack(side="left", padx=(10, 0))
                ctk.CTkFrame(tarjeta, fg_color="transparent", height=12).pack()
                efecto_hover(tarjeta)

        def conceptos(parent):
            etiqueta(parent, "Conceptos clave", FUENTE_SECCION, "texto").pack(anchor="w", pady=(6, 10))
            rejilla = ctk.CTkFrame(parent, fg_color="transparent")
            rejilla.pack(fill="x", padx=(0, 4))
            rejilla.grid_columnconfigure((0, 1), weight=1, uniform="conceptos")
            for k, (nombre, definicion) in enumerate(self.CONCEPTOS):
                tarjeta = crear_tarjeta(rejilla)
                tarjeta.grid(row=k // 2, column=k % 2, sticky="nsew", padx=(0, 12) if k % 2 == 0 else 0, pady=(0, 12))
                etiqueta(tarjeta, nombre, FUENTE_NEGRITA, "primario", ajustar=lambda w: (w - 16) / 2 - 40).pack(anchor="w", padx=16, pady=(14, 2))
                etiqueta(tarjeta, definicion, FUENTE_NORMAL, "texto_2", ajustar=lambda w: (w - 16) / 2 - 40).pack(
                    anchor="w", padx=16, pady=(0, 14))
                efecto_hover(tarjeta)

        return [uso, atajos_y_formatos, conceptos]


# -----------------------------------------------------------------------------
# Ventana principal
# -----------------------------------------------------------------------------

class AplicacionAlgebraLineal(_Ventana):
    """Aplicacion de escritorio moderna hecha con CustomTkinter."""

    SECCIONES = [
        ("calculadora", "▦", "Calculadora", PaginaCalculadora),
        ("vectorial", "Σ", "Combinaciones lineales", PaginaCombinaciones),
        ("axb", "≡", "Ecuación Ax = b", PaginaAxb),
        ("propiedades_ax", "⇄", "Propiedades de Ax", PaginaPropiedades),
        ("matrices", "▦", "Operaciones con matrices", PaginaMatrices),
        ("independencia", "⊥", "Independencia lineal", PaginaIndependencia),
        ("metodo", "☰", "Método de eliminación", PaginaMetodo),
        ("ayuda", "?", "Ayuda", PaginaAyuda),
    ]

    def __init__(self):
        super().__init__()
        _FUENTES_MEDIDA.clear()
        self.title("Calculadora de Álgebra Lineal - Grupo 3 - UAM")
        self._centrar(1280, 820)
        self.minsize(1160, 680)
        self.configure(fg_color=PALETA["fondo"])

        self.logo_grande = cargar_logo((52, 52))
        self.logo_pequeno = cargar_logo((30, 30))
        # CustomTkinter coloca su propio icono en Windows poco despues de iniciar.
        self.after(300, self._configurar_icono_ventana)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.notificador = Notificador(self)
        self.pagina_actual = None
        self.crear_sidebar()
        self.crear_contenido_principal()
        instalar_desplazamiento(self)
        self._configurar_atajos()
        self.cambiar_pagina("calculadora")

    def _centrar(self, ancho, alto):
        ancho = min(ancho, self.winfo_screenwidth() - 60)
        alto = min(alto, self.winfo_screenheight() - 80)
        x = max(0, (self.winfo_screenwidth() - ancho) // 2)
        y = max(0, (self.winfo_screenheight() - alto) // 3)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _configurar_icono_ventana(self):
        """Usa el logo de la UAM como icono de la ventana (necesita Pillow: el logo es WebP)."""
        if Image is None or ImageTk is None or not os.path.exists(RUTA_LOGO):
            return
        try:
            imagen = Image.open(RUTA_LOGO).convert("RGBA").resize((64, 64), Image.LANCZOS)
            self._icono_tk = ImageTk.PhotoImage(imagen, master=self)
            self.iconphoto(True, self._icono_tk)
        except Exception as error:
            print("_configurar_icono_ventana: fallo al establecer icono:", error)

    def crear_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=PALETA["sidebar"], corner_radius=0, width=236)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.pack_propagate(False)

        marca = ctk.CTkFrame(sidebar, fg_color="transparent")
        marca.pack(fill="x", padx=22, pady=(26, 6))
        fila_marca = ctk.CTkFrame(marca, fg_color="transparent")
        fila_marca.pack(anchor="w")
        if self.logo_grande is not None:
            ctk.CTkLabel(fila_marca, image=self.logo_grande, text="").pack(side="left", padx=(0, 12))
        etiqueta(fila_marca, "Álgebra\nLineal", (FAMILIA, 20, "bold"), "texto").pack(side="left")
        etiqueta(marca, "Universidad Americana • Grupo 3", FUENTE_PEQUENA, "texto_3").pack(anchor="w", pady=(10, 0))

        ctk.CTkFrame(sidebar, height=1, fg_color=PALETA["borde"]).pack(fill="x", padx=22, pady=(16, 14))
        etiqueta(sidebar, "SECCIONES", (FAMILIA, 10, "bold"), "texto_3").pack(anchor="w", padx=28, pady=(0, 6))

        self.nav = ctk.CTkFrame(sidebar, fg_color="transparent")
        self.nav.pack(fill="x", padx=12)
        self.nav_botones = {}
        for clave, icono, texto, _clase in self.SECCIONES:
            item = ItemNavegacion(self.nav, icono, texto, lambda c=clave: self.cambiar_pagina(c))
            item.pack(fill="x", pady=2)
            self.nav_botones[clave] = item
        self.indicador = ctk.CTkFrame(self.nav, width=4, height=22, corner_radius=2, fg_color=PALETA["primario"])
        self._indicador_y = None

        ctk.CTkFrame(sidebar, fg_color="transparent").pack(fill="both", expand=True)

        pie = ctk.CTkFrame(sidebar, fg_color="transparent")
        pie.pack(fill="x", padx=22, pady=(0, 20))
        if self.logo_pequeno is not None:
            ctk.CTkLabel(pie, image=self.logo_pequeno, text="").pack(side="left", padx=(0, 8))
        etiqueta(pie, "Excellentia\nAcademica", (FAMILIA, 10), "texto_3").pack(side="left")

    def crear_contenido_principal(self):
        self.contenedor = ctk.CTkFrame(self, fg_color=PALETA["fondo"], corner_radius=0)
        self.contenedor.grid(row=0, column=1, sticky="nsew")
        self.contenedor.grid_columnconfigure(0, weight=1)
        self.contenedor.grid_rowconfigure(0, weight=1)

        # Las paginas se crean la primera vez que se visitan y solo la activa
        # queda en pantalla: apilar paginas ocultas vuelve lento el dibujado (sobre todo en macOS).
        self.paginas = {}
        self._clases_pagina = {clave: clase for clave, _icono, _texto, clase in self.SECCIONES}

    def obtener_pagina(self, clave):
        if clave not in self.paginas:
            self.paginas[clave] = self._clases_pagina[clave](self.contenedor, self)
        return self.paginas[clave]

    def cambiar_pagina(self, pagina):
        if pagina == self.pagina_actual:
            return
        anterior = self.paginas.get(self.pagina_actual)
        nueva = self.obtener_pagina(pagina)
        self.pagina_actual = pagina
        for nombre, item in self.nav_botones.items():
            item.activar(nombre == pagina)
        if anterior is not None:
            anterior.grid_remove()
        nueva.grid(row=0, column=0, sticky="nsew")
        nueva.al_mostrar()
        self.after(10, self._mover_indicador)

    def _mover_indicador(self):
        """Desliza la barrita del menu hasta la seccion activa."""
        item = self.nav_botones[self.pagina_actual]
        self.update_idletasks()
        escala = escala_de(self.nav)
        destino = (item.winfo_y() + (item.winfo_height() - 22 * escala) / 2) / escala
        origen = self._indicador_y if self._indicador_y is not None else destino
        self._indicador_y = destino
        self.indicador.lift()

        def mover(t):
            self.indicador.place(x=0, y=origen + (destino - origen) * t)

        animar(self.indicador, 280, mover)

    def _configurar_atajos(self):
        secuencias = ["<Control-Return>", "<Control-KP_Enter>"]
        if sys.platform == "darwin":
            secuencias.append("<Command-Return>")
        for secuencia in secuencias:
            self.bind_all(secuencia, self._atajo_resolver, add="+")

    def _atajo_resolver(self, _evento=None):
        pagina = self.paginas.get(self.pagina_actual)
        if isinstance(pagina, PaginaSistema):
            pagina.resolver()
        return "break"

    def notificar(self, texto, tipo="info"):
        self.notificador.mostrar(texto, tipo)

    def copiar(self, texto):
        self.clipboard_clear()
        self.clipboard_append(texto)
        self.notificar("Resultado copiado al portapapeles.", "exito")


# -----------------------------------------------------------------------------
# Inicio del programa
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Modo consola: independencia lineal solo con la biblioteca estandar de Python
# -----------------------------------------------------------------------------

def _pedir_entero(mensaje, minimo=1, entrada=input):
    while True:
        try:
            valor = int(entrada(mensaje).strip())
            if valor >= minimo:
                return valor
        except ValueError:
            pass
        print(f"  Escribe un número entero mayor o igual que {minimo}.")


def independencia_consola(entrada=input):
    """
    Pide la cantidad de vectores p y su dimension n, lee los vectores, construye el
    sistema homogeneo [A | 0], lo reduce a forma escalonada por filas y muestra la
    matriz reducida, el numero de pivotes y el veredicto (L.I. o L.D.).
    """
    print("=" * 64)
    print("Independencia lineal por reducción a forma escalonada por filas")
    print("=" * 64)
    p = _pedir_entero("Cantidad de vectores p: ", entrada=entrada)
    n = _pedir_entero("Dimensión n (componentes de cada vector): ", entrada=entrada)
    print(f"Escribe cada vector de {espacio_real(n)} con sus {n} componentes separadas por espacios "
          f"(se aceptan 3, -1/2 o 0.5).")

    vectores = []
    for j in range(p):
        while True:
            partes = entrada(f"  v{j + 1} = ").replace(";", " ").split()
            try:
                if len(partes) != n:
                    raise ValueError(f"se esperaban {n} componentes y se recibieron {len(partes)}.")
                vectores.append([convertir_numero(texto) for texto in partes])
                break
            except ValueError as error:
                print(f"    Error: {error}")

    A = [[vectores[j][i] for j in range(p)] for i in range(n)]
    resultado = analizar_independencia(A)

    print()
    print("Operaciones elementales aplicadas:")
    operaciones = [paso["operacion"] for paso in resultado["pasos"] if paso["tipo"] not in ("inicial", "final")]
    for numero, operacion in enumerate(operaciones, start=1):
        print(f"  {numero}. {operacion}")
    if not operaciones:
        print("  (ninguna: la matriz ya estaba en forma escalonada)")
    print()
    for linea in informe_independencia(resultado):
        print(linea)
    return resultado


def main():
    if "--consola" in sys.argv[1:] or ctk is None:
        if ctk is None:
            print("CustomTkinter no está instalado; se abre el modo consola.")
            print("Para la interfaz gráfica ejecuta: pip install -r requirements.txt\n")
        try:
            independencia_consola()
        except (KeyboardInterrupt, EOFError):
            print("\nPrograma terminado.")
        return
    configurar_customtkinter()
    app = AplicacionAlgebraLineal()
    app.mainloop()


if __name__ == "__main__":
    main()

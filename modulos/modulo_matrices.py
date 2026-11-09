"""Núcleo de álgebra lineal exacta de la Calculadora (listas anidadas y Fraction).

Propósito: sistemas Ax = b, operaciones y expresiones matriciales, determinantes,
inversas, independencia lineal y verificador de propiedades con «Se cumple»/«No se cumple».
Unidad: Álgebra Lineal (MTM0120), matrices, determinantes, inversas y sistemas lineales.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
Funciones puras: reciben listas anidadas y retornan resultados; no usan input() ni print().
"""
from fractions import Fraction
import random
from .pasos import etapa, valor as valor_visual, condicion

LIMITE_DIMENSION = 10


def maximo_comun_divisor(a, b):
    """Calcula el máximo común divisor con el algoritmo de Euclides (sin el módulo math).

    Entrada: enteros a y b. Salida: entero no negativo mcd(a, b).
    """
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def minimo_comun_multiplo(enteros):
    """Calcula el mínimo común múltiplo con mcm(a, b) = a·b / mcd(a, b).

    Entrada: iterable de enteros positivos. Salida: su mcm (1 si está vacío).
    """
    resultado = 1
    for entero in enteros:
        resultado = resultado * entero // maximo_comun_divisor(resultado, entero)
    return resultado

def convertir_numero(texto):
    """Convierte el texto ingresado (entero, decimal con punto o coma, o fracción como 3/2) en Fraction.

    Entrada: texto. Salida: Fraction exacta; lanza ValueError si está vacío o no es un número.
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
    """Escribe un número exacto de forma legible: 2 en lugar de 2/1 y -1/2 como fracción.

    Entrada: número (Fraction, int o texto numérico). Salida: cadena.
    """
    numero = Fraction(numero)
    if numero == 0:
        return "0"
    if numero.denominator == 1:
        return str(numero.numerator)
    return f"{numero.numerator}/{numero.denominator}"


def formatear_coeficiente(valor):
    """Escribe el valor absoluto de un coeficiente que va junto a una variable; las fracciones van entre paréntesis.

    Entrada: valor numérico. Salida: cadena, por ejemplo '2' o '(1/2)'.
    """
    valor = abs(Fraction(valor))
    texto = formatear_numero(valor)
    return f"({texto})" if valor.denominator != 1 else texto


def copiar_matriz(matriz):
    """Copia una matriz fila por fila para no alterar los datos originales que luego se verifican.

    Entrada: matriz (lista anidada). Salida: copia independiente.
    """
    return [fila[:] for fila in matriz]


def crear_matriz_aumentada(A, b):
    """Construye la matriz aumentada [A | b].

    Entrada: A (m × n) y b (m componentes). Salida: lista anidada m × (n + 1).
    """
    return [A[i][:] + [b[i]] for i in range(len(A))]


def intercambiar_filas(matriz, i, j):
    """Aplica la operación elemental Fi ↔ Fj sobre la misma matriz.

    Entrada: matriz y los índices i y j (desde 0). Salida: None; modifica la matriz.
    """
    matriz[i], matriz[j] = matriz[j], matriz[i]


def multiplicar_fila(matriz, i, escalar):
    """Aplica la operación elemental Fi ← k·Fi sobre la misma matriz.

    Entrada: matriz, índice i y escalar k. Salida: None; modifica la matriz.
    """
    matriz[i] = [escalar * valor for valor in matriz[i]]


def sumar_multiplo_fila(matriz, destino, origen, factor):
    """Aplica el reemplazo Fdestino ← Fdestino + factor·Forigen, usado para crear ceros junto a un pivote.

    Entrada: matriz, índices destino y origen, y factor. Salida: None; modifica la matriz.
    """
    matriz[destino] = [
        matriz[destino][c] + factor * matriz[origen][c]
        for c in range(len(matriz[destino]))
    ]


def matriz_a_texto(matriz, aumentada=True):
    """Convierte una matriz en texto alineado; con aumentada=True separa la última columna con '|'.

    Entrada: matriz y aumentada (bool). Salida: cadena de varias líneas ('' si la matriz está vacía).
    """
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
        if not aumentada or num_cols == 1:
            lineas.append("[ " + "  ".join(f"{formatear_numero(fila[c]):>{anchos[c]}}" for c in range(num_cols)) + " ]")
            continue
        coeficientes = "  ".join(f"{formatear_numero(fila[c]):>{anchos[c]}}" for c in range(num_cols - 1))
        independiente = f"{formatear_numero(fila[-1]):>{anchos[-1]}}"
        lineas.append(f"[ {coeficientes} | {independiente} ]")
    return "\n".join(lineas)


def buscar_fila_pivote(matriz, fila_inicio, columna):
    """Busca, desde fila_inicio hacia abajo, la primera fila con entrada no nula en la columna.

    Entrada: matriz, fila_inicio y columna. Salida: índice de esa fila o None si toda la columna es cero.
    """
    for fila in range(fila_inicio, len(matriz)):
        if matriz[fila][columna] != 0:
            return fila
    return None


class PasoEliminacion(dict):
    """Paso de una eliminación por filas: operación, explicación, matriz resultante, filas y pivotes resaltados.

    Se usa como diccionario, con atributos o como tupla histórica (operación, matriz, explicación).
    """

    def __init__(self, operacion, explicacion, matriz, tipo="operacion",
                 filas=(), pivotes=(), fila_origen=None):
        """Guarda los datos del paso para mostrarlo y resaltarlo en la interfaz.

        Entrada: operación, explicación, matriz, tipo, filas, pivotes y fila_origen. Salida: None.
        """
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
        """Permite leer las claves como atributos (paso.operacion).

        Entrada: nombre de la clave. Salida: su valor; lanza AttributeError si no existe.
        """
        try:
            return super().__getitem__(nombre)
        except KeyError:
            raise AttributeError(nombre) from None

    def __getitem__(self, key):
        """Acceso por clave o por índice histórico: 0 = operación, 1 = matriz, 2 = explicación.

        Entrada: clave (str) o índice (int). Salida: el valor guardado.
        """
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
    """Escribe la operación Fdestino → Fdestino − factor·Forigen, por ejemplo 'F2 → F2 - 2F1'.

    Entrada: índices destino y origen (desde 0) y factor. Salida: cadena.
    """
    factor_abs = abs(factor)
    k_str = "" if factor_abs == 1 else (
        str(factor_abs.numerator) if factor_abs.denominator == 1 else f"({formatear_numero(factor_abs)})"
    )
    signo = "-" if factor > 0 else "+"
    return f"F{destino + 1} → F{destino + 1} {signo} {k_str}F{origen + 1}"


def _texto_intercambio(fila_pivote, fila_encontrada, variable):
    """Explica por qué se intercambian dos filas cuando la posición pivote vale 0.

    Entrada: fila pivote, fila encontrada y nombre de la variable. Salida: cadena.
    """
    return (
        f"En la posición pivote de la {variable} hay un 0, así que se "
        f"intercambia F{fila_pivote + 1} con F{fila_encontrada + 1}, la primera "
        f"fila de abajo con un valor distinto de cero."
    )


def _detallar_eliminacion(pasos):
    """Agrega a cada paso el cálculo entrada por entrada de la fila modificada, comparando dos estados seguidos.

    Entrada: lista de PasoEliminacion. Salida: None; completa la clave «calculos» de cada paso.
    """
    for anterior, paso in zip(pasos, pasos[1:]):
        antes, despues = anterior["matriz"], paso["matriz"]
        calculos = []
        if paso["tipo"] == "intercambio":
            i, j = paso["filas"]
            calculos = [f"F{i+1} ← F{j+1} original; F{j+1} ← F{i+1} original."]
        elif paso["tipo"] == "escalado":
            i, c = paso["pivotes"][0]
            factor = despues[i][c] / antes[i][c]
            calculos = [f"F{i+1}, columna {j+1}: ({factor})·({v}) = {despues[i][j]}" for j, v in enumerate(antes[i])]
        elif paso["tipo"] == "eliminacion":
            i, origen = paso["filas"][0], paso["fila_origen"]
            c = paso["pivotes"][0][1]
            factor = (despues[i][c] - antes[i][c]) / antes[origen][c]
            calculos = [f"F{i+1}, columna {j+1}: ({v}) + ({factor})·({antes[origen][j]}) = {despues[i][j]}" for j, v in enumerate(antes[i])]
        paso["calculos"] = calculos


def gauss_jordan(matriz_aumentada, num_variables, nombres_variables=None):
    """Reduce [A | b] a la forma escalonada reducida con Fraction y registra cada operación elemental.

    Entrada: matriz aumentada, número de variables y nombres opcionales.
    Salida: (matriz reducida, columnas pivote, lista de pasos).
    """
    nombres = nombres_variables or obtener_nombres_variables(num_variables)
    matriz = validar_matriz(matriz_aumentada, "Matriz aumentada")
    if not isinstance(num_variables, int) or not 1 <= num_variables < len(matriz[0]):
        raise ValueError("La matriz aumentada debe contener las columnas de variables y términos independientes.")
    if len(nombres) != num_variables:
        raise ValueError("Debe proporcionarse un nombre por variable.")
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
            # Toda la columna es cero desde la fila pivote: la variable será libre.
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

        # El pivote se normaliza a 1 para llegar a la forma escalonada reducida.
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

        # Gauss-Jordan anula la columna del pivote arriba y abajo, no solo debajo.
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

    _detallar_eliminacion(pasos)
    return matriz, columnas_pivote, pasos


def forma_escalonada(matriz_aumentada, num_variables, nombres_variables=None, explicacion_inicial=None):
    """Reduce [A | b] a una forma escalonada: solo anula debajo de cada pivote y no lo convierte en 1.

    Entrada: matriz aumentada, número de variables, nombres y explicación inicial opcionales.
    Salida: (matriz escalonada, columnas pivote, lista de pasos).
    """
    nombres = nombres_variables or obtener_nombres_variables(num_variables)
    matriz = validar_matriz(matriz_aumentada, "Matriz aumentada")
    if not isinstance(num_variables, int) or not 1 <= num_variables < len(matriz[0]):
        raise ValueError("La matriz aumentada debe contener variables y términos independientes.")
    if len(nombres) != num_variables:
        raise ValueError("Debe proporcionarse un nombre por variable.")
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
            factor = Fraction(matriz[fila][columna]) / Fraction(valor_pivote)
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
    _detallar_eliminacion(pasos)
    return matriz, columnas_pivote, pasos


def fila_inconsistente(fila, num_variables):
    """Indica si una fila representa 0x1 + … + 0xn = k con k ≠ 0 (una contradicción).

    Entrada: fila de la matriz aumentada y número de variables. Salida: True o False.
    """
    coeficientes_cero = all(fila[c] == 0 for c in range(num_variables))
    return coeficientes_cero and fila[-1] != 0


def es_sistema_homogeneo(b):
    """Indica si el sistema es homogéneo (Ax = 0).

    Entrada: vector b. Salida: True si todas sus componentes son cero.
    """
    return all(valor == 0 for valor in b)


def clasificar_sistema(matriz_rref, columnas_pivote, num_variables):
    """Clasifica el sistema a partir de su forma escalonada reducida.

    Entrada: RREF, columnas pivote y número de variables. Salida: (clasificación, descripción).
    """
    for fila in matriz_rref:
        if fila_inconsistente(fila, num_variables):
            return "Sistema inconsistente", "No tiene solución."

    if len(columnas_pivote) == num_variables:
        return "Sistema consistente determinado", "Tiene una única solución."

    return "Sistema consistente indeterminado", "Tiene infinitas soluciones."


def obtener_solucion_unica(matriz_rref, columnas_pivote, num_variables):
    """Lee la solución única cuando cada variable tiene columna pivote.

    Entrada: RREF, columnas pivote y número de variables. Salida: lista con el valor de cada variable.
    """
    solucion = [Fraction(0) for _ in range(num_variables)]
    for fila, columna in enumerate(columnas_pivote):
        solucion[columna] = matriz_rref[fila][-1]
    return solucion


def nombres_parametros(cantidad):
    """Genera los nombres de los parámetros de las variables libres: t; s, t; r, s, t; … o t1, t2, ….

    Entrada: cantidad de variables libres. Salida: lista de nombres.
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
    """Expresa cada variable básica en función de los parámetros de las variables libres.

    Entrada: RREF, columnas pivote y número de variables.
    Salida: (expresiones por variable, variables libres, parámetro de cada libre).
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
    """Construye la forma vectorial x = p + t1·v1 + t2·v2 + … de la solución general.

    Entrada: RREF, columnas pivote y número de variables. Salida: (particular p, lista de (parámetro, dirección v)).
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
    """Escribe el nombre del espacio Rⁿ con superíndice, por ejemplo 'R³'.

    Entrada: dimensión n. Salida: cadena.
    """
    return "R" + str(n).translate(SUPERINDICES)


def obtener_nombres_variables(num_variables, prefijo="x"):
    """Genera nombres de variables consecutivos: x1, x2, x3, ….

    Entrada: cantidad y prefijo (por defecto 'x'). Salida: lista de nombres.
    """
    return [f"{prefijo}{i + 1}" for i in range(num_variables)]


def unir_terminos(terminos, union=""):
    """Une pares (coeficiente, texto) en una expresión como '2x1 - x2 + (1/2)x3', omitiendo ceros.

    Entrada: pares (coeficiente, texto) y separador entre ambos. Salida: cadena ('0' si no quedan términos).
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
    """Escribe una ecuación del sistema, por ejemplo '2x1 - x2 = 3'.

    Entrada: coeficientes de la fila, término independiente y nombres de variables. Salida: cadena.
    """
    lado_izq = unir_terminos(zip(fila_coefs, nombres_vars))
    return f"{lado_izq} = {formatear_numero(termino_indep)}"


def formatear_sustitucion(fila_coefs, termino_indep, solucion):
    """Escribe la ecuación con cada variable sustituida entre paréntesis, por ejemplo '2(1) - (2) = 0'.

    Entrada: coeficientes, término independiente y solución. Salida: cadena.
    """
    valores = [f"({formatear_numero(valor)})" for valor in solucion]
    lado_izq = unir_terminos(zip(fila_coefs, valores))
    return f"{lado_izq} = {formatear_numero(termino_indep)}"


def formatear_simplificacion(fila_coefs, termino_indep, solucion):
    """Simplifica la sustitución en dos pasos: productos individuales y suma total.

    Entrada: coeficientes, término independiente y solución. Salida: (líneas de simplificación, coincide, suma total).
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
    """Verificación explicada de una ecuación: original, sustitución, simplificación y si se cumple.

    Se usa como diccionario, con atributos o como tupla histórica (suma obtenida, esperado, coincide).
    """

    def __init__(self, indice, ecuacion_original, sustitucion, simplificacion, suma_obtenida, esperado, coincide):
        """Guarda los datos de la verificación de una ecuación.

        Entrada: índice, ecuación, sustitución, simplificación, suma obtenida, esperado y coincide. Salida: None.
        """
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
        """Permite leer las claves como atributos (detalle.coincide).

        Entrada: nombre de la clave. Salida: su valor; lanza AttributeError si no existe.
        """
        try:
            return super().__getitem__(nombre)
        except KeyError:
            raise AttributeError(nombre) from None

    def __getitem__(self, key):
        """Acceso por clave o por índice histórico: 0 = suma obtenida, 1 = esperado, 2 = coincide.

        Entrada: clave (str) o índice (int). Salida: el valor guardado.
        """
        if isinstance(key, int):
            return [self["suma_obtenida"], self["esperado"], self["coincide"]][key]
        return super().__getitem__(key)


def verificar_solucion(A_original, b_original, solucion, nombres_vars=None):
    """Sustituye la solución en cada ecuación del sistema original y explica la simplificación.

    Entrada: A y b originales, solución y nombres opcionales. Salida: (todas se cumplen, lista de DetalleVerificacion).
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

        # La comprobación se hace con el sistema original, no con la matriz reducida.
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
    """Resuelve Ax = b por Gauss-Jordan: clasifica, obtiene la solución única o paramétrica y la verifica.

    Entrada: A (m × n), b (m) y nombres opcionales.
    Salida: diccionario con RREF, pasos, rangos, clasificación, solución y verificación.
    """
    A = validar_matriz(A, "A")
    b = [Fraction(valor) for valor in b]
    if len(b) != len(A):
        raise ValueError("b debe tener una componente por cada fila de A.")
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
        # La particular y las direcciones se verifican por separado para
        # garantizar Ax=b para cualquier valor de los parámetros.
        particular, direcciones = obtener_forma_vectorial(rref, columnas_pivote, num_variables)

        resultado["expresiones"] = expresiones
        resultado["variables_libres"] = libres
        resultado["parametros"] = parametros
        resultado["forma_vectorial"] = (particular, direcciones)
        resultado["solucion_particular"] = particular
        resultado["verificacion"] = verificar_solucion(A, b, particular, nombres_vars)
        resultado["verificacion_general"] = verificar_solucion_general(A, b, particular, direcciones)

    return resultado


def multiplicar_matriz_vector(A, x):
    """Calcula el producto matriz-vector A·x con aritmética exacta.

    Entrada: A (m × n) y x (n componentes). Salida: lista de m componentes; lanza ValueError si n no coincide.
    """
    A = validar_matriz(A, "A")
    x = [Fraction(valor) for valor in x]
    if len(A[0]) != len(x):
        raise ValueError("La cantidad de columnas de A debe coincidir con la dimension del vector.")
    return [sum(A[i][j] * x[j] for j in range(len(x))) for i in range(len(A))]



def validar_matriz(matriz, nombre="Matriz"):
    """Comprueba que la matriz sea rectangular y no vacía y convierte sus entradas a Fraction.

    Entrada: matriz y nombre para los mensajes. Salida: nueva lista anidada; lanza ValueError si no es válida.
    """
    if not isinstance(matriz, list) or not matriz:
        raise ValueError(f"{nombre} debe ser una matriz no vacía.")
    if not all(isinstance(fila, list) and fila for fila in matriz):
        raise ValueError(f"{nombre} debe tener filas no vacías.")
    columnas = len(matriz[0])
    if any(len(fila) != columnas for fila in matriz):
        raise ValueError(f"{nombre} debe ser rectangular: todas sus filas deben tener la misma longitud.")
    try:
        return [[valor if isinstance(valor, Fraction) else Fraction(valor) for valor in fila] for fila in matriz]
    except (TypeError, ValueError, ZeroDivisionError, OverflowError) as error:
        raise ValueError(f"{nombre} contiene una entrada no numérica válida.") from error


def dimensiones_matriz(matriz):
    """Obtiene las dimensiones de una matriz válida.

    Entrada: matriz. Salida: tupla (filas, columnas).
    """
    matriz = validar_matriz(matriz)
    return len(matriz), len(matriz[0])


def verificar_solucion_general(A, b, particular, direcciones):
    """Comprueba una familia paramétrica: A·p = b para la particular y A·v = 0 para cada dirección.

    Entrada: A, b, particular p y lista de (parámetro, v). Salida: diccionario con cada producto y «correcto».
    """
    A = validar_matriz(A, "A")
    b = [Fraction(v) for v in b]
    if len(b) != len(A):
        raise ValueError("Dimensión de b incompatible con A.")
    ap = multiplicar_matriz_vector(A, particular)
    verificaciones = []
    for parametro, vector in direcciones:
        av = multiplicar_matriz_vector(A, vector)
        verificaciones.append({"parametro": parametro, "vector": vector, "producto": av,
                               "correcto": av == [Fraction(0)] * len(A)})
    correcto = ap == b and all(v["correcto"] for v in verificaciones)
    return {"particular": {"producto": ap, "esperado": b, "correcto": ap == b},
            "direcciones": verificaciones, "correcto": correcto,
            "conclusion": "Se cumple" if correcto else "No se cumple"}


def validar_cuadrada(A):
    """Valida A y exige que sea cuadrada y no vacía.

    Entrada: matriz A. Salida: A con entradas Fraction; lanza ValueError si no es cuadrada.
    """
    A = validar_matriz(A, "A")
    if len(A) != len(A[0]):
        raise ValueError("A debe ser cuadrada.")
    return A


def submatriz(A, i, j):
    """Elimina la fila i y la columna j de A.

    Entrada: matriz A e índices i, j desde 0. Salida: submatriz; lanza ValueError si los índices no son válidos.
    """
    A = validar_matriz(A, "A")
    if not isinstance(i, int) or not isinstance(j, int) or not (0 <= i < len(A) and 0 <= j < len(A[0])):
        raise ValueError("Índice de fila o columna fuera de rango.")
    return [[v for c, v in enumerate(fila) if c != j] for r, fila in enumerate(A) if r != i]


def menor(A, i, j):
    """Calcula el menor Mij = det(A sin la fila i ni la columna j); en orden 1 vale 1 (determinante vacío).

    Entrada: A cuadrada e índices i, j. Salida: Fraction.
    """
    A = validar_cuadrada(A)
    reducida = submatriz(A, i, j)
    return Fraction(1) if len(A) == 1 else determinante(reducida)


def cofactor(A, i, j):
    """Calcula el cofactor Cij = (-1)^(i+j)·Mij.

    Entrada: A cuadrada e índices i, j. Salida: Fraction.
    """
    return (-1) ** (i + j) * menor(A, i, j)


def matriz_menores(A):
    """Calcula la matriz de todos los menores Mij.

    Entrada: A cuadrada. Salida: matriz n × n de menores.
    """
    A = validar_cuadrada(A)
    return [[menor(A, i, j) for j in range(len(A))] for i in range(len(A))]


def matriz_cofactores(A):
    """Calcula la matriz de cofactores Cij = (-1)^(i+j)·Mij.

    Entrada: A cuadrada. Salida: matriz n × n de cofactores.
    """
    A = validar_cuadrada(A)
    return _cofactores_desde_menores(matriz_menores(A))


def _cofactores_desde_menores(menores):
    """Aplica los signos alternados (-1)^(i+j) a una matriz de menores ya calculada.

    Entrada: matriz de menores. Salida: matriz de cofactores.
    """
    n = len(menores)
    return [[(-1) ** (i + j) * menores[i][j] for j in range(n)] for i in range(n)]


def adjunta(A):
    """Calcula la adjunta adj(A), la transpuesta de la matriz de cofactores.

    Entrada: A cuadrada. Salida: adj(A).
    """
    return transponer_matriz(matriz_cofactores(A))


def _determinante_menor(S):
    """Calcula el determinante de un menor: con ad − bc si es 2 × 2 (como a mano) y por reducción si es mayor.

    Entrada: submatriz cuadrada. Salida: diccionario de calcular_determinante.
    """
    return calcular_determinante(S, "2x2" if len(S) == 2 else "triangular")


def _desarrollo_menor(S):
    """Escribe el desarrollo 'ad − bc = ' de un menor 2 × 2.

    Entrada: submatriz. Salida: cadena (vacía si no es 2 × 2).
    """
    if len(S) != 2:
        return ""
    return f"({S[0][0]})·({S[1][1]}) − ({S[0][1]})·({S[1][0]}) = "


def calcular_determinante(A, metodo="triangular", fila=0):
    """Calcula det(A) con la fórmula 2 × 2, Sarrus, cofactores o reducción triangular, sin modificar A.

    Entrada: A cuadrada, método y fila de expansión (cofactores).
    Salida: diccionario con determinante, método, pasos, etapas, triangular e intercambios.
    """
    A = validar_cuadrada(A)
    n = len(A)
    metodos = {"2x2", "sarrus", "cofactores", "triangular"}
    if metodo not in metodos:
        raise ValueError("Método desconocido: use 2x2, sarrus, cofactores o triangular.")
    if metodo == "2x2" and n != 2:
        raise ValueError("La fórmula 2×2 requiere una matriz de orden 2.")
    if metodo == "sarrus" and n != 3:
        raise ValueError("Sarrus solo se aplica a matrices 3×3.")
    pasos = [f"A es {n}×{n} (sin columna de términos independientes):", matriz_a_texto(A, aumentada=False)]
    etapas = [etapa("Datos y condiciones", valores=[valor_visual("A", A)], condiciones=[
        condicion(f"A es {n}×{n}: cuadrada y no vacía."),
        condicion(f"Método {metodo}" + (": orden 2 requerido." if metodo == "2x2" else ": orden 3 requerido." if metodo == "sarrus" else ": aplicable a cualquier orden."))])]
    intercambios = 0
    triangular = None
    if metodo == "2x2":
        valor = A[0][0] * A[1][1] - A[0][1] * A[1][0]
        pasos.append(f"det(A) = ad − bc = {A[0][0]}·{A[1][1]} − {A[0][1]}·{A[1][0]} = {valor}")
        etapas.append(etapa("Fórmula 2×2 y sustitución", formula="det(A) = ad − bc", calculos=[
            f"ad = ({A[0][0]})·({A[1][1]}) = {A[0][0] * A[1][1]}",
            f"bc = ({A[0][1]})·({A[1][0]}) = {A[0][1] * A[1][0]}",
            f"ad − bc = {A[0][0] * A[1][1]} − ({A[0][1] * A[1][0]}) = {valor}"]))
    elif metodo == "sarrus":
        # Con índices módulo 3 se recorren las diagonales sin copiar las dos primeras columnas a la derecha.
        positivos = [A[0][j] * A[1][(j + 1) % 3] * A[2][(j + 2) % 3] for j in range(3)]
        negativos = [A[0][j] * A[1][(j - 1) % 3] * A[2][(j - 2) % 3] for j in range(3)]
        valor = sum(positivos, Fraction(0)) - sum(negativos, Fraction(0))
        pasos += ["Sarrus: suma de diagonales descendentes menos ascendentes.",
                  f"Productos descendentes: {positivos}", f"Productos ascendentes: {negativos}"]
        for titulo, sentido, productos in (("Diagonales positivas", 1, positivos), ("Diagonales negativas", -1, negativos)):
            calculos = []
            for j, producto in enumerate(productos):
                indices = [(i, (j + sentido * i) % 3) for i in range(3)]
                calculos.append(" · ".join(f"a{i+1},{c+1}({A[i][c]})" for i, c in indices) + f" = {producto}")
            etapas.append(etapa(titulo, valores=[valor_visual("A", A)], calculos=calculos + [f"Suma = {sum(productos, Fraction(0))}"]))
        etapas.append(etapa("Resta final de Sarrus", formula="det(A) = suma positiva − suma negativa",
                            calculos=[f"{sum(positivos, Fraction(0))} − ({sum(negativos, Fraction(0))}) = {valor}"]))
    elif metodo == "cofactores":
        if not isinstance(fila, int) or not 0 <= fila < n:
            raise ValueError("Fila de expansión fuera de rango.")
        valor = Fraction(0)
        pasos.append(f"Expansión por fila {fila + 1}: det(A) = Σ aij Cij.")
        etapas.append(etapa(f"Expansión por fila {fila + 1}", formula="det(A) = Σ aij Cij; Cij = (-1)^(i+j) Mij"))
        terminos = []
        for j in range(n):
            reducida = submatriz(A, fila, j)
            calculo_menor = _determinante_menor(reducida) if n > 1 else None
            m = calculo_menor["determinante"] if calculo_menor else Fraction(1)
            c = (-1) ** (fila + j) * m
            valor += A[fila][j] * c
            terminos.append(A[fila][j] * c)
            etapas.append(etapa(f"Menor y cofactor ({fila + 1},{j + 1})", valores=[valor_visual("Submatriz", reducida)] if n > 1 else [],
                calculos=[f"a{fila+1},{j+1} = {A[fila][j]}", f"M{fila+1},{j+1} = {_desarrollo_menor(reducida)}{m}" + (" (determinante vacío = 1)" if n == 1 else ""),
                          f"Signo (-1)^({fila+1}+{j+1}) = {(-1)**(fila+j)}", f"C{fila+1},{j+1} = {c}",
                          f"a·C = ({A[fila][j]})·({c}) = {A[fila][j]*c}"],
                subpasos=calculo_menor["etapas"] if calculo_menor else []))
            pasos += [f"Submatriz para M{fila + 1},{j + 1}:",
                      matriz_a_texto(submatriz(A, fila, j), aumentada=False) if n > 1 else "[]: det vacío = 1",
                      f"M = {m}; C = (-1)^({fila + 1}+{j + 1})·{m} = {c}; a·C = {A[fila][j] * c}"]
        etapas.append(etapa("Sumar los términos de la expansión", calculos=[" + ".join(f"({t})" for t in terminos) + f" = {valor}"]))
    else:
        triangular = copiar_matriz(A)
        # No se escalan filas: multiplicar una fila por k multiplicaría det(A) por k y habría que compensarlo.
        pasos.append("Solo intercambios y sumas de múltiplos de filas; no se escalan filas.")
        for j in range(n):
            pivote = buscar_fila_pivote(triangular, j, j)
            if pivote is None:
                pasos.append(f"Columna {j + 1} sin pivote: determinante cero.")
                etapas.append(etapa(f"Columna {j+1} sin pivote", "Las entradas restantes de esta columna son cero; la diagonal tendrá un cero.", valores=[valor_visual("Matriz actual", triangular)]))
                continue
            if pivote != j:
                intercambiar_filas(triangular, j, pivote)
                intercambios += 1
                pasos += [f"F{j + 1} ↔ F{pivote + 1}: cambia el signo.", matriz_a_texto(triangular, False)]
                etapas.append(etapa(f"F{j+1} ↔ F{pivote+1}", "Un intercambio cambia el signo del determinante.",
                                    valores=[valor_visual("Matriz después del intercambio", triangular, filas=[j, pivote])]))
            pasos.append(f"Pivote ({j + 1},{j + 1}) = {triangular[j][j]}")
            etapas.append(etapa(f"Pivote ({j+1},{j+1}) = {triangular[j][j]}", valores=[valor_visual("Matriz actual", triangular, pivotes=[(j, j)])]))
            for i in range(j + 1, n):
                if triangular[i][j] != 0:
                    factor = -triangular[i][j] / triangular[j][j]
                    sumar_multiplo_fila(triangular, i, j, factor)
                    pasos += [f"F{i + 1} ← F{i + 1} + ({factor})F{j + 1}: conserva det.", matriz_a_texto(triangular, False)]
                    etapas.append(etapa(f"F{i+1} ← F{i+1} + ({factor})F{j+1}", "Sumar un múltiplo de otra fila conserva el determinante.",
                        calculos=[f"Multiplicador aplicado: {factor}"] + [
                            f"Columna {c+1}: ({triangular[i][c] - factor*triangular[j][c]}) + ({factor})·({triangular[j][c]}) = {triangular[i][c]}" for c in range(n)],
                        valores=[valor_visual("Matriz después de la operación", triangular, pivotes=[(j, j)], filas=[i])]))
        producto = Fraction(1)
        for i in range(n):
            producto *= triangular[i][i]
        # det de una triangular = producto de su diagonal; cada intercambio cambió el signo una vez.
        valor = (-1) ** intercambios * producto
        pasos.append(f"det(A) = (-1)^{intercambios} · producto diagonal = {valor}")
        etapas.append(etapa("Producto diagonal y signo", formula="det(A) = (-1)^intercambios · ∏ tii",
                            valores=[valor_visual("Triangular T", triangular)], calculos=[
                                " · ".join(f"({triangular[i][i]})" for i in range(n)) + f" = {producto}",
                                f"Intercambios: {intercambios}; (-1)^{intercambios}·({producto}) = {valor}",
                                "No se escalaron filas: no hay factores de escala que compensar."]))
    pasos.append(f"det(A) = {formatear_numero(valor)}")
    pasos.append("A es singular: no tiene inversa." if valor == 0 else "A es invertible porque det(A) ≠ 0.")
    etapas.append(etapa("Resultado", valores=[valor_visual("det(A)", valor)], conclusion=pasos[-1]))
    return {"determinante": valor, "metodo": metodo, "pasos": pasos,
            "triangular": triangular, "intercambios": intercambios, "etapas": etapas}


def determinante(A, metodo="triangular"):
    """Calcula det(A) de forma exacta; la reducción triangular es el método predeterminado.

    Entrada: A cuadrada y método. Salida: Fraction.
    """
    return calcular_determinante(A, metodo)["determinante"]


def verificar_inversa(A, inversa):
    """Comprueba A·A⁻¹ = I y A⁻¹·A = I con el producto matricial de la Calculadora.

    Entrada: A y su supuesta inversa. Salida: diccionario con ambos productos, identidad, «correcto» y procedimientos.
    """
    A, inversa = validar_cuadrada(A), validar_cuadrada(inversa)
    identidad = matriz_identidad(len(A))
    izquierdo = multiplicar_matrices(A, inversa)
    derecho = multiplicar_matrices(inversa, A)
    correcto = izquierdo == identidad and derecho == identidad
    return {"A_por_inversa": izquierdo, "inversa_por_A": derecho, "identidad": identidad,
            "correcto": correcto, "conclusion": "Se cumple para las matrices ingresadas" if correcto else "No se cumple para las matrices ingresadas",
            "procedimientos": [procedimiento_operacion_matrices(A, "producto", inversa),
                               procedimiento_operacion_matrices(inversa, "producto", A)]}


def calcular_inversa(A, metodo="gauss_jordan"):
    """Calcula A⁻¹ por Gauss-Jordan sobre [A | I] o por adj(A)/det(A), con todo el procedimiento.

    Entrada: A cuadrada y método. Salida: diccionario con inversa, pasos, etapas y verificación;
    lanza ValueError si A es singular.
    """
    A = validar_cuadrada(A)
    if metodo not in ("gauss_jordan", "adjunta"):
        raise ValueError("Método de inversa desconocido.")
    n = len(A)
    pasos = ["A:", matriz_a_texto(A, False)]
    etapas = [etapa("Datos y condiciones", valores=[valor_visual("A", A)],
                    condiciones=[condicion(f"A es cuadrada de orden {n}. La inversa requiere n pivotes (det(A)≠0).")])]
    detalles = {}
    if metodo == "gauss_jordan":
        identidad = matriz_identidad(n)
        aumentada = [a + i for a, i in zip(A, identidad)]
        etapas.append(etapa("Construir [A | I]", formula="[A | I] → [I | A⁻¹]", valores=[
            valor_visual("A", A), valor_visual("I", identidad), valor_visual("[A | I]", aumentada, separador=n)]))
        reducida, pivotes, operaciones = gauss_jordan(aumentada, n)
        # Con menos de n pivotes A no es equivalente por filas a I, así que no es invertible.
        if len(pivotes) != n:
            raise ValueError("A no es invertible: es singular (det(A)=0); faltan pivotes en [A|I].")
        inversa = [fila[n:] for fila in reducida]
        pasos.append("[A | I] → [I | A⁻¹]. La barra separa los dos bloques de n columnas.")
        for paso in operaciones:
            # En [A | I] la barra separa dos bloques de n columnas; no hay una columna b como en Ax = b.
            filas = [[formatear_numero(v) for v in fila] for fila in paso.matriz]
            texto = "\n".join("[ " + "  ".join(f[:n]) + " | " + "  ".join(f[n:]) + " ]" for f in filas)
            pasos += [paso.operacion, texto]
            etapas.append(etapa(paso.operacion if paso.tipo not in ("inicial", "final") else "Bloques iniciales" if paso.tipo == "inicial" else "Bloques reducidos",
                "La misma operación se aplica a ambos bloques." if paso.tipo not in ("inicial", "final") else "El bloque derecho contiene n columnas, no una columna b.",
                valores=[valor_visual("Matriz aumentada por bloques", paso.matriz, separador=n, pivotes=paso.pivotes, filas=paso.filas)],
                calculos=paso.get("calculos", []) + [f"Pivote: fila {i+1}, columna {j+1}, valor {paso.matriz[i][j]}" for i, j in paso.pivotes]))
        etapas.append(etapa("Separar I y A⁻¹", valores=[valor_visual("Bloque izquierdo I", [f[:n] for f in reducida]), valor_visual("A⁻¹", inversa)]))
        detalles.update({"matriz_aumentada": aumentada, "matriz_reducida": reducida,
                         "operaciones": operaciones, "pivotes": pivotes})
    else:
        # det(A) se obtiene con los mismos cofactores (expansión por la fila 1): así el
        # determinante, la matriz de cofactores, la adjunta y la inversa quedan encadenados.
        menores = matriz_cero(n, n)
        for i in range(n):
            for j in range(n):
                reducida = submatriz(A, i, j)
                md = _determinante_menor(reducida) if n > 1 else None
                menores[i][j] = md["determinante"] if md else Fraction(1)
                c = (-1) ** (i+j) * menores[i][j]
                etapas.append(etapa(f"Menor y cofactor ({i+1},{j+1})",
                    valores=[valor_visual("Submatriz", reducida)] if md else [],
                    calculos=[f"M{i+1},{j+1} = {_desarrollo_menor(reducida)}{menores[i][j]}", f"C{i+1},{j+1} = (-1)^({i+1}+{j+1})·({menores[i][j]}) = {c}"],
                    subpasos=md["etapas"] if md else []))
        cofactores = _cofactores_desde_menores(menores)
        terminos = [A[0][j] * cofactores[0][j] for j in range(n)]
        d = sum(terminos, Fraction(0))
        etapas += [etapa("Matrices de menores y cofactores", valores=[valor_visual("Menores", menores), valor_visual("Cofactores", cofactores)]),
                   etapa("det(A) por cofactores de la fila 1", "Se usan las entradas de la fila 1 de A y sus cofactores ya calculados.",
                         formula="det(A) = " + " + ".join(f"a1,{j+1}·C1,{j+1}" for j in range(n)),
                         calculos=[" + ".join(f"({A[0][j]})·({cofactores[0][j]})" for j in range(n)) + f" = {d}"],
                         valores=[valor_visual("det(A)", d)],
                         condiciones=[condicion(f"det(A) = {d} ≠ 0: A es invertible." if d else "det(A) = 0: A es singular.", d != 0)])]
        if d == 0:
            raise ValueError("A no es invertible: det(A)=0; la matriz es singular.")
        adj = transponer_matriz(cofactores)
        inversa = multiplicar_matriz_escalar(Fraction(1) / d, adj)
        etapas += [etapa("Transponer los cofactores", formula="adj(A) = Cᵀ", valores=[valor_visual("C", cofactores), valor_visual("adj(A)", adj)],
                         calculos=[f"adj(A){i+1},{j+1} = C{j+1},{i+1} = {adj[i][j]}" for i in range(n) for j in range(n)]),
                   etapa("Escalar la adjunta", formula=f"A⁻¹ = (1/det(A))adj(A) = ({Fraction(1)/d})adj(A)",
                         valores=[valor_visual("A⁻¹", inversa)], calculos=[
                             f"A⁻¹{i+1},{j+1} = ({Fraction(1)/d})·({adj[i][j]}) = {inversa[i][j]}" for i in range(n) for j in range(n)])]
        pasos += [f"det(A) = {d}", "A⁻¹ = (1/det(A)) adj(A)"]
        for titulo, matriz in (("Matriz de menores", menores), ("Cofactores: Cij = (-1)^(i+j) Mij", cofactores),
                               ("Adjunta: transpuesta de cofactores", adj)):
            pasos += [titulo, matriz_a_texto(matriz, False)]
        detalles.update({"determinante": d, "menores": menores, "cofactores": cofactores, "adjunta": adj})
    verificacion = verificar_inversa(A, inversa)
    if not verificacion["correcto"]:
        raise ArithmeticError("La inversa calculada no supera la verificación exacta.")
    pasos += ["A⁻¹:", matriz_a_texto(inversa, False), "A·A⁻¹:", matriz_a_texto(verificacion["A_por_inversa"], False),
              "A⁻¹·A:", matriz_a_texto(verificacion["inversa_por_A"], False), "Ambos productos son I. Se cumple"]
    return {"inversa": inversa, "metodo": metodo, "pasos": pasos, "etapas": etapas, "verificacion": verificacion, **detalles}


def inversa_gauss_jordan(A):
    """Calcula A⁻¹ reduciendo [A | I] a [I | A⁻¹].

    Entrada: A cuadrada. Salida: A⁻¹; lanza ValueError si A es singular.
    """
    return calcular_inversa(A, "gauss_jordan")["inversa"]


def inversa_adjunta(A):
    """Calcula A⁻¹ = adj(A) / det(A).

    Entrada: A cuadrada. Salida: A⁻¹; lanza ValueError si A es singular.
    """
    return calcular_inversa(A, "adjunta")["inversa"]


def comparar_metodos_inversa(A):
    """Calcula la inversa por Gauss-Jordan y por adjunta y comprueba que coincidan.

    Entrada: A cuadrada e invertible. Salida: diccionario con ambas inversas, «cumple», conclusión y lados.
    """
    gj, adj = calcular_inversa(A), calcular_inversa(A, "adjunta")
    izquierda, derecha = gj["inversa"], adj["inversa"]
    return {"gauss_jordan": izquierda, "adjunta": derecha, "cumple": izquierda == derecha,
            "conclusion": "Se cumple para las matrices ingresadas" if izquierda == derecha else "No se cumple para las matrices ingresadas",
            "lados": [{"etiqueta": "Gauss-Jordan", "resultado": izquierda, "etapas": gj["etapas"]},
                      {"etiqueta": "Adjunta", "resultado": derecha, "etapas": adj["etapas"]}]}


PROPIEDADES_AVANZADAS = {
    "inversa_izquierda": "A⁻¹A = I",
    "inversa_derecha": "AA⁻¹ = I",
    "inversa_inversa": "(A⁻¹)⁻¹ = A",
    "inversa_producto": "(AB)⁻¹ = B⁻¹A⁻¹",
    "inversa_transpuesta": "(Aᵀ)⁻¹ = (A⁻¹)ᵀ",
    "det_inversa": "det(A⁻¹) = 1/det(A)",
    "det_intercambio": "Intercambiar filas cambia el signo del determinante",
    "det_escalar_fila": "Multiplicar una fila por k multiplica det por k",
    "det_suma_fila": "Sumar un múltiplo de otra fila conserva det",
    "det_triangular": "Determinante triangular = producto diagonal",
    "det_producto": "det(AB) = det(A)det(B)",
    "det_escalar_matriz": "det(kA) = kⁿ·det(A)",
    "det_transpuesta": "det(Aᵀ) = det(A)",
    "det_identidad": "det(I) = 1",
}


def verificar_propiedad_avanzada(clave, matrices, escalares=None, metodo_inversa="gauss_jordan", metodo_determinante="triangular"):
    """Calcula por separado ambos lados de una propiedad de inversas o determinantes y los compara.

    Entrada: clave, matrices, escalares (k) y métodos de inversa y determinante.
    Salida: diccionario con lados, «cumple», condiciones y conclusión; lanza ValueError si falla una hipótesis.
    """
    if clave not in PROPIEDADES_AVANZADAS:
        raise ValueError("Propiedad desconocida.")
    A = validar_cuadrada(matrices["A"])
    n = len(A)
    k = Fraction((escalares or {}).get("k", 2))
    pasos = [PROPIEDADES_AVANZADAS[clave], "A:", matriz_a_texto(A, False)]
    izq, der = [], []
    condiciones = [condicion(f"A es {n}×{n}: cuadrada.")]
    if clave.startswith("inversa_") or clave == "det_inversa":
        condiciones.append(condicion(f"det(A) = {determinante(A)}; se requiere det(A)≠0.", determinante(A) != 0))

    def invertir(M, nombre, etapas):
        """Calcula M⁻¹ con el método elegido y registra det(M) y el procedimiento.

        Entrada: matriz M, nombre a mostrar y lista de etapas. Salida: M⁻¹.
        """
        detallar_det(M, f"det({nombre[:-2]})", etapas)
        calculo = calcular_inversa(M, metodo_inversa)
        etapas.append(etapa(f"Calcular {nombre}", formula="[M|I] → [I|M⁻¹]" if metodo_inversa == "gauss_jordan" else "M⁻¹ = adj(M)/det(M)",
            valores=[valor_visual("M", M), valor_visual(nombre, calculo["inversa"])], subpasos=calculo["etapas"]))
        return calculo["inversa"]

    def detallar_det(M, nombre, etapas):
        """Calcula det(M) con el método elegido y registra sus pasos.

        Entrada: matriz M, nombre a mostrar y lista de etapas. Salida: det(M).
        """
        calculo = calcular_determinante(M, metodo_determinante)
        etapas.append(etapa(f"Calcular {nombre}", valores=[valor_visual("M", M), valor_visual(nombre, calculo["determinante"])], subpasos=calculo["etapas"]))
        return calculo["determinante"]

    def detallar_producto(M, N, nombre, etapas):
        """Calcula M·N fila por columna y registra el procedimiento.

        Entrada: matrices M y N, nombre a mostrar y lista de etapas. Salida: M·N.
        """
        calculo = procedimiento_operacion_matrices(M, "producto", N)
        etapas.append(etapa(f"Calcular {nombre}", valores=[valor_visual("Primer factor", M), valor_visual("Segundo factor", N), valor_visual(nombre, calculo["resultado"])], calculos=calculo["pasos"]))
        return calculo["resultado"]

    def transponer(M, nombre, etapas):
        """Calcula Mᵀ y registra cada entrada.

        Entrada: matriz M, nombre a mostrar y lista de etapas. Salida: Mᵀ.
        """
        resultado = transponer_matriz(M)
        etapas.append(etapa(f"Calcular {nombre}", formula="(Mᵀ)ij = Mji", valores=[valor_visual("M", M), valor_visual(nombre, resultado)],
            calculos=[f"({i+1},{j+1}): {resultado[i][j]} ← M{j+1},{i+1}" for i in range(len(resultado)) for j in range(len(resultado[0]))]))
        return resultado
    if clave in ("inversa_izquierda", "inversa_derecha"):
        inversa = invertir(A, "A⁻¹", izq)
        izquierda = (detallar_producto(inversa, A, "A⁻¹A", izq) if clave == "inversa_izquierda"
                     else detallar_producto(A, inversa, "AA⁻¹", izq))
        derecha = matriz_identidad(n)
        der.append(etapa("Construir la identidad", f"I es {n}×{n}: unos en la diagonal y ceros fuera de ella.",
                         valores=[valor_visual("I", derecha)]))
        pasos += ["A⁻¹:", matriz_a_texto(inversa, False)]
    elif clave == "inversa_inversa":
        izquierda = invertir(invertir(A, "A⁻¹", izq), "(A⁻¹)⁻¹", izq)
        derecha = copiar_matriz(A)
        der.append(etapa("Leer A original", valores=[valor_visual("A", derecha)]))
    elif clave == "inversa_producto":
        B = validar_cuadrada(matrices["B"])
        if len(B) != n:
            raise ValueError("A y B deben ser invertibles y cuadradas del mismo orden para esta propiedad.")
        condiciones += [condicion(f"B es {len(B)}×{len(B)}; mismo orden que A."), condicion(f"det(B) = {determinante(B)}; se requiere det(B)≠0.", determinante(B) != 0)]
        izquierda = invertir(detallar_producto(A, B, "AB", izq), "(AB)⁻¹", izq)
        bi, ai = invertir(B, "B⁻¹", der), invertir(A, "A⁻¹", der)
        derecha = detallar_producto(bi, ai, "B⁻¹A⁻¹", der)
        pasos += ["B:", matriz_a_texto(B, False), "A y B son invertibles y del mismo orden."]
    elif clave == "inversa_transpuesta":
        izquierda = invertir(transponer(A, "Aᵀ", izq), "(Aᵀ)⁻¹", izq)
        derecha = transponer(invertir(A, "A⁻¹", der), "(A⁻¹)ᵀ", der)
    elif clave == "det_inversa":
        izquierda = detallar_det(invertir(A, "A⁻¹", izq), "det(A⁻¹)", izq)
        d = detallar_det(A, "det(A)", der)
        derecha = Fraction(1) / d
        der.append(etapa("Recíproco del determinante", formula=f"1/det(A) = 1/({d}) = {derecha}", valores=[valor_visual("1/det(A)", derecha)]))
    elif clave == "det_producto":
        B = validar_cuadrada(matrices["B"])
        if len(B) != n:
            raise ValueError("det(AB)=det(A)det(B) requiere matrices cuadradas del mismo orden.")
        izquierda = detallar_det(detallar_producto(A, B, "AB", izq), "det(AB)", izq)
        da, db = detallar_det(A, "det(A)", der), detallar_det(B, "det(B)", der)
        derecha = da * db
        der.append(etapa("Multiplicar determinantes", formula=f"({da})·({db}) = {derecha}", valores=[valor_visual("det(A)det(B)", derecha)]))
    elif clave == "det_escalar_matriz":
        matriz_kA = multiplicar_matriz_escalar(k, A)
        izq.append(etapa("Calcular kA", f"Cada entrada de A se multiplica por k = {k}.", valores=[valor_visual("A", A), valor_visual("kA", matriz_kA)],
                         calculos=[f"({i+1},{j+1}): ({k})·({A[i][j]}) = {matriz_kA[i][j]}" for i in range(n) for j in range(n)]))
        izquierda = detallar_det(matriz_kA, "det(kA)", izq)
        det_A = detallar_det(A, "det(A)", der)
        derecha = k ** n * det_A
        der.append(etapa("Multiplicar det(A) por kⁿ", formula=f"({k})^{n}·({det_A}) = {derecha}", valores=[valor_visual("kⁿ·det(A)", derecha)]))
        condiciones.append(condicion(f"k = {k} y n = {n}: kA multiplica las {n} filas de A por k."))
        pasos.append(f"k = {k}, n = {n}")
    elif clave == "det_transpuesta":
        izquierda = detallar_det(transponer(A, "Aᵀ", izq), "det(Aᵀ)", izq)
        derecha = detallar_det(A, "det(A)", der)
    elif clave == "det_identidad":
        I = matriz_identidad(n)
        izq.append(etapa("Construir la identidad", valores=[valor_visual("I", I)]))
        izquierda = detallar_det(I, "det(I)", izq)
        derecha = Fraction(1)
        der.append(etapa("Valor del teorema", valores=[valor_visual("1", derecha)]))
    elif clave == "det_triangular":
        superior = all(A[i][j] == 0 for i in range(n) for j in range(i))
        inferior = all(A[i][j] == 0 for i in range(n) for j in range(i + 1, n))
        if not (superior or inferior):
            raise ValueError("Esta propiedad requiere una matriz triangular.")
        condiciones.append(condicion("A es triangular superior o inferior."))
        izquierda, derecha = detallar_det(A, "det(A)", izq), Fraction(1)
        for i in range(n):
            derecha *= A[i][i]
        der.append(etapa("Producto diagonal desde A original", calculos=[" · ".join(f"({A[i][i]})" for i in range(n)) + f" = {derecha}"], valores=[valor_visual("Producto diagonal", derecha)]))
    else:
        modificada = copiar_matriz(A)
        if clave in ("det_intercambio", "det_suma_fila") and n < 2:
            raise ValueError("Esta operación requiere dos filas distintas.")
        if clave == "det_intercambio":
            intercambiar_filas(modificada, 0, 1)
            derecha = -detallar_det(A, "det(A)", der)
            der.append(etapa("Cambiar el signo", valores=[valor_visual("−det(A)", derecha)]))
            pasos.append("F1 ↔ F2")
        elif clave == "det_escalar_fila":
            multiplicar_fila(modificada, 0, k)
            d = detallar_det(A, "det(A)", der)
            derecha = k * d
            der.append(etapa("Multiplicar det(A) por k", formula=f"({k})·({d}) = {derecha}"))
            pasos.append(f"F1 ← ({k})F1")
        else:
            sumar_multiplo_fila(modificada, 0, 1, k)
            derecha = detallar_det(A, "det(A)", der)
            pasos.append(f"F1 ← F1 + ({k})F2")
        izq.append(etapa("Aplicar operación de fila", pasos[-1], valores=[valor_visual("Original A", A), valor_visual("Modificada", modificada)]))
        condiciones.append(condicion("Se usan filas distintas F1 y F2." if clave != "det_escalar_fila" else f"Escalar k={k}; también se admite k=0."))
        izquierda = detallar_det(modificada, "det(modificada)", izq)
        pasos += ["Matriz después de la operación:", matriz_a_texto(modificada, False)]
    cumple = izquierda == derecha
    representacion = lambda x: matriz_a_texto(x, False) if isinstance(x, list) else formatear_numero(x)
    pasos += ["LADO IZQUIERDO:", representacion(izquierda), "LADO DERECHO:", representacion(derecha),
              "COMPARACIÓN: " + ("coinciden exactamente" if cumple else "difieren"),
               "Caso particular; no sustituye una demostración general.", "Se cumple para las matrices ingresadas" if cumple else "No se cumple para las matrices ingresadas"]
    return {"propiedad": PROPIEDADES_AVANZADAS[clave], "izquierda": izquierda, "derecha": derecha,
            "cumple": cumple, "comparacion": "Igualdad exacta" if cumple else "Valores distintos",
            "conclusion": "Se cumple para las matrices ingresadas" if cumple else "No se cumple para las matrices ingresadas", "pasos": pasos,
            "condiciones": condiciones, "lados": [{"etiqueta": "Lado izquierdo", "resultado": izquierda, "etapas": izq},
                                                    {"etiqueta": "Lado derecho", "resultado": derecha, "etapas": der}]}


CATEGORIAS_PROPIEDADES_CLAVE = ("Operaciones y transposición", "Matriz inversa", "Determinantes",
                                "Efecto de operaciones de fila")


def verificar_propiedades_clave(matriz_A, matriz_B=None, matriz_C=None, escalar_k=2):
    """Evalúa ambos miembros de cada propiedad clave (transposición, inversa, determinantes y operaciones de fila).

    Entrada: A, B y C opcionales (listas anidadas) y el escalar k.
    Salida: diccionario con «resultados» (diagnóstico «Se cumple»/«No se cumple»/«No aplica»), intermedios y totales.
    """
    A = validar_matriz(matriz_A, "A")
    B = validar_matriz(matriz_B, "B") if matriz_B is not None else None
    C = validar_matriz(matriz_C, "C") if matriz_C is not None else None
    k = Fraction(escalar_k)
    calculados = {}

    def obtener(nombre, calcular):
        """Calcula un resultado intermedio una sola vez y lo reutiliza en las demás propiedades.

        Entrada: nombre del resultado y función que lo calcula. Salida: el resultado guardado.
        """
        if nombre not in calculados:
            calculados[nombre] = calcular()
        return calculados[nombre]

    def exigir(cumple, motivo):
        """Detiene la propiedad con «No aplica» cuando falla una hipótesis del teorema.

        Entrada: condición (bool) y motivo. Salida: None; lanza ValueError con el motivo si no se cumple.
        """
        if not cumple:
            raise ValueError(motivo)

    def matriz_B():
        """Obtiene B o detiene la propiedad si no se ingresó.

        Salida: matriz B.
        """
        exigir(B is not None, "falta la matriz B.")
        return B

    def matriz_C():
        """Obtiene C o detiene la propiedad si no se ingresó.

        Salida: matriz C.
        """
        exigir(C is not None, "falta la matriz C.")
        return C

    def dimension(nombre, M):
        """Escribe 'X es m×n' para los motivos de «No aplica».

        Entrada: nombre y matriz. Salida: cadena.
        """
        return f"{nombre} es {len(M)}×{len(M[0])}"

    def exigir_suma(nombre_X, X, nombre_Y, Y):
        """Exige que X e Y tengan las mismas dimensiones para poder sumarlas.

        Entrada: nombre y matriz de cada sumando. Salida: None; detiene la propiedad si no se cumple.
        """
        exigir((len(X), len(X[0])) == (len(Y), len(Y[0])),
               f"{dimension(nombre_X, X)} y {dimension(nombre_Y, Y)}: la suma exige dimensiones iguales.")

    def exigir_producto(nombre_X, X, nombre_Y, Y):
        """Exige columnas(X) = filas(Y) para poder calcular XY.

        Entrada: nombre y matriz de cada factor. Salida: None; detiene la propiedad si no se cumple.
        """
        exigir(len(X[0]) == len(Y), f"{dimension(nombre_X, X)} y {dimension(nombre_Y, Y)}: el producto exige "
                                    f"columnas({nombre_X}) = filas({nombre_Y}).")

    def orden_A():
        """Exige que A sea cuadrada.

        Salida: el orden n de A.
        """
        exigir(len(A) == len(A[0]), "A debe ser cuadrada.")
        return len(A)

    def transpuesta_A():
        """Obtiene Aᵀ, calculada una sola vez.

        Salida: Aᵀ.
        """
        return obtener("Aᵀ", lambda: transponer_matriz(A))

    def transpuesta_B():
        """Obtiene Bᵀ, calculada una sola vez.

        Salida: Bᵀ.
        """
        return obtener("Bᵀ", lambda: transponer_matriz(matriz_B()))

    def producto_AB():
        """Obtiene AB, calculado una sola vez tras comprobar columnas(A) = filas(B).

        Salida: AB.
        """
        exigir_producto("A", A, "B", matriz_B())
        return obtener("AB", lambda: multiplicar_matrices(A, B))

    def escalar_kA():
        """Obtiene kA, calculada una sola vez.

        Salida: kA.
        """
        return obtener("kA", lambda: multiplicar_matriz_escalar(k, A))

    def inversa_A():
        """Obtiene A⁻¹ por Gauss-Jordan, calculada una sola vez (exige A cuadrada e invertible).

        Salida: A⁻¹.
        """
        orden_A()
        return obtener("A⁻¹", lambda: inversa_gauss_jordan(A))

    def inversa_B():
        """Obtiene B⁻¹ por Gauss-Jordan, calculada una sola vez (exige B cuadrada del orden de A).

        Salida: B⁻¹.
        """
        exigir(len(matriz_B()) == len(B[0]) == len(A), "B debe ser cuadrada y del mismo orden que A.")
        return obtener("B⁻¹", lambda: inversa_gauss_jordan(B))

    def det_A():
        """Obtiene det(A), calculado una sola vez (exige A cuadrada).

        Salida: det(A).
        """
        orden_A()
        return obtener("det(A)", lambda: determinante(A))

    def con_fila(operacion):
        """Aplica una operación de fila a una copia de A (exige al menos dos filas).

        Entrada: función que modifica la matriz. Salida: la copia modificada.
        """
        exigir(orden_A() >= 2, "se necesitan al menos dos filas distintas.")
        modificada = copiar_matriz(A)
        operacion(modificada)
        return modificada

    def p_doble_transpuesta():
        """Calcula los miembros de (Aᵀ)ᵀ = A.

        Salida: (izquierda, derecha, pasos encadenados).
        """
        return transponer_matriz(transpuesta_A()), A, ["AT = transpuesta(A)", "izquierda = transpuesta(AT)", "derecha = A"]

    def p_transpuesta_suma():
        """Calcula los miembros de (A + B)ᵀ = Aᵀ + Bᵀ.

        Salida: (izquierda, derecha, pasos encadenados).
        """
        exigir_suma("A", A, "B", matriz_B())
        return (transponer_matriz(sumar_matrices(A, matriz_B())), sumar_matrices(transpuesta_A(), transpuesta_B()),
                ["izquierda = transpuesta(suma(A, B))", "derecha = suma(AT, BT)  (AT y BT se reutilizan)"])

    def p_transpuesta_escalar():
        """Calcula los miembros de (kA)ᵀ = kAᵀ.

        Salida: (izquierda, derecha, pasos encadenados).
        """
        return (transponer_matriz(escalar_kA()), multiplicar_matriz_escalar(k, transpuesta_A()),
                [f"kA = escalar({k}, A)", "izquierda = transpuesta(kA)", f"derecha = escalar({k}, AT)"])

    def p_transpuesta_producto():
        """Calcula los miembros de (AB)ᵀ = BᵀAᵀ.

        Salida: (izquierda, derecha, pasos encadenados).
        """
        return (transponer_matriz(producto_AB()), multiplicar_matrices(transpuesta_B(), transpuesta_A()),
                ["AB = producto(A, B)  (se calcula una vez y se reutiliza)", "izquierda = transpuesta(AB)",
                 "derecha = producto(transpuesta(B), transpuesta(A))"])

    def p_distributiva():
        """Calcula los miembros de A(B + C) = AB + AC.

        Salida: (izquierda, derecha, pasos encadenados).
        """
        exigir_suma("B", matriz_B(), "C", matriz_C())
        exigir_producto("A", A, "B", B)
        producto_AC = obtener("AC", lambda: multiplicar_matrices(A, matriz_C()))
        return (multiplicar_matrices(A, sumar_matrices(matriz_B(), matriz_C())), sumar_matrices(producto_AB(), producto_AC),
                ["izquierda = producto(A, suma(B, C))", "AC = producto(A, C)", "derecha = suma(AB, AC)  (AB se reutiliza)"])

    def p_asociativa():
        """Calcula los miembros de (AB)C = A(BC).

        Salida: (izquierda, derecha, pasos encadenados).
        """
        exigir_producto("A", A, "B", matriz_B())
        exigir_producto("B", B, "C", matriz_C())
        producto_BC = obtener("BC", lambda: multiplicar_matrices(matriz_B(), matriz_C()))
        return (multiplicar_matrices(producto_AB(), matriz_C()), multiplicar_matrices(A, producto_BC),
                ["izquierda = producto(AB, C)  (AB se reutiliza)", "BC = producto(B, C)", "derecha = producto(A, BC)"])

    def p_doble_inversa():
        """Calcula los miembros de (A⁻¹)⁻¹ = A.

        Salida: (izquierda, derecha, pasos encadenados).
        """
        return inversa_gauss_jordan(inversa_A()), A, ["Ainv = inversa(A)", "izquierda = inversa(Ainv)", "derecha = A"]

    def p_inversa_producto():
        """Calcula los miembros de (AB)⁻¹ = B⁻¹A⁻¹.

        Salida: (izquierda, derecha, pasos encadenados).
        """
        inversa_de_B, inversa_de_A = inversa_B(), inversa_A()
        return (inversa_gauss_jordan(producto_AB()), multiplicar_matrices(inversa_de_B, inversa_de_A),
                ["izquierda = inversa(AB)  (AB se reutiliza)", "derecha = producto(Binv, Ainv)"])

    def p_inversa_transpuesta():
        """Calcula los miembros de (Aᵀ)⁻¹ = (A⁻¹)ᵀ.

        Salida: (izquierda, derecha, pasos encadenados).
        """
        return (inversa_gauss_jordan(transpuesta_A()), transponer_matriz(inversa_A()),
                ["izquierda = inversa(AT)", "derecha = transpuesta(Ainv)  (Ainv se reutiliza)"])

    def p_producto_por_inversa():
        """Calcula los miembros de A·A⁻¹ = I.

        Salida: (izquierda, derecha, pasos encadenados).
        """
        return (multiplicar_matrices(A, inversa_A()), matriz_identidad(orden_A()),
                ["izquierda = producto(A, Ainv)", f"derecha = identidad({len(A)})"])

    def p_det_transpuesta():
        """Calcula los miembros de det(Aᵀ) = det(A).

        Salida: (izquierda, derecha, pasos encadenados).
        """
        return determinante(transpuesta_A()), det_A(), ["izquierda = det(AT)", "derecha = det(A)"]

    def p_det_producto():
        """Calcula los miembros de det(AB) = det(A)·det(B).

        Salida: (izquierda, derecha, pasos encadenados).
        """
        exigir(len(matriz_B()) == len(B[0]) == orden_A(), "B debe ser cuadrada y del mismo orden que A.")
        det_B = obtener("det(B)", lambda: determinante(B))
        return determinante(producto_AB()), det_A() * det_B, ["izquierda = det(AB)", "derecha = det(A) · det(B)"]

    def p_det_inversa():
        """Calcula los miembros de det(A⁻¹) = 1/det(A).

        Salida: (izquierda, derecha, pasos encadenados).
        """
        return determinante(inversa_A()), Fraction(1) / det_A(), ["izquierda = det(Ainv)", "derecha = 1 / det(A)"]

    def p_det_escalar():
        """Calcula los miembros de det(kA) = kⁿ·det(A).

        Salida: (izquierda, derecha, pasos encadenados).
        """
        n = orden_A()
        return (determinante(escalar_kA()), k ** n * det_A(),
                ["izquierda = det(kA)  (kA se reutiliza)", f"derecha = ({k})^{n} · det(A)"])

    def p_permutacion():
        """Calcula los miembros de det(A con F1 ↔ F2) = −det(A).

        Salida: (izquierda, derecha, pasos encadenados).
        """
        permutada = con_fila(lambda M: intercambiar_filas(M, 0, 1))
        return determinante(permutada), -det_A(), ["A' = A con F1 ↔ F2", "izquierda = det(A')", "derecha = −det(A)"]

    def p_reemplazo():
        """Calcula los miembros de det(A con F1 ← F1 + kF2) = det(A).

        Salida: (izquierda, derecha, pasos encadenados).
        """
        reemplazada = con_fila(lambda M: sumar_multiplo_fila(M, 0, 1, k))
        return determinante(reemplazada), det_A(), [f"A' = A con F1 ← F1 + ({k})F2", "izquierda = det(A')", "derecha = det(A)"]

    def p_escalamiento():
        """Calcula los miembros de det(A con F1 ← kF1) = k·det(A).

        Salida: (izquierda, derecha, pasos encadenados).
        """
        escalada = con_fila(lambda M: multiplicar_fila(M, 0, k))
        return determinante(escalada), k * det_A(), [f"A' = A con F1 ← ({k})F1", "izquierda = det(A')", f"derecha = ({k}) · det(A)"]

    def p_triangular():
        """Calcula los miembros de det(T) = producto de la diagonal, con T la parte triangular superior de A.

        Salida: (izquierda, derecha, pasos encadenados).
        """
        n = orden_A()
        triangular = [[A[i][j] if j >= i else Fraction(0) for j in range(n)] for i in range(n)]
        diagonal = Fraction(1)
        for i in range(n):
            diagonal *= triangular[i][i]
        # La expansión por cofactores no usa la diagonal, así que el miembro izquierdo es independiente del derecho.
        return (calcular_determinante(triangular, "cofactores")["determinante"], diagonal,
                ["T = parte triangular superior de A", "izquierda = det(T) por cofactores", "derecha = producto de la diagonal de T"])

    catalogo = [
        ("Operaciones y transposición", "(Aᵀ)ᵀ = A", p_doble_transpuesta),
        ("Operaciones y transposición", "(A + B)ᵀ = Aᵀ + Bᵀ", p_transpuesta_suma),
        ("Operaciones y transposición", "(kA)ᵀ = kAᵀ", p_transpuesta_escalar),
        ("Operaciones y transposición", "(AB)ᵀ = BᵀAᵀ", p_transpuesta_producto),
        ("Operaciones y transposición", "A(B + C) = AB + AC", p_distributiva),
        ("Operaciones y transposición", "(AB)C = A(BC)", p_asociativa),
        ("Matriz inversa", "(A⁻¹)⁻¹ = A", p_doble_inversa),
        ("Matriz inversa", "(AB)⁻¹ = B⁻¹A⁻¹", p_inversa_producto),
        ("Matriz inversa", "(Aᵀ)⁻¹ = (A⁻¹)ᵀ", p_inversa_transpuesta),
        ("Matriz inversa", "A·A⁻¹ = I", p_producto_por_inversa),
        ("Determinantes", "det(Aᵀ) = det(A)", p_det_transpuesta),
        ("Determinantes", "det(AB) = det(A)·det(B)", p_det_producto),
        ("Determinantes", "det(A⁻¹) = 1/det(A)", p_det_inversa),
        ("Determinantes", "det(kA) = kⁿ·det(A)", p_det_escalar),
        ("Efecto de operaciones de fila", "Permutación de filas: det cambia de signo", p_permutacion),
        ("Efecto de operaciones de fila", "Reemplazo Fi ← Fi + kFj: det se conserva", p_reemplazo),
        ("Efecto de operaciones de fila", "Multiplicar una fila por k: det se multiplica por k", p_escalamiento),
        ("Efecto de operaciones de fila", "det(triangular) = producto de la diagonal", p_triangular),
    ]
    resultados = []
    for categoria, propiedad, calcular in catalogo:
        try:
            izquierda, derecha, pasos = calcular()
            cumple = son_iguales(izquierda, derecha)
            diagnostico = "Se cumple" if cumple else "No se cumple"
        except (ValueError, ZeroDivisionError) as error:
            izquierda = derecha = cumple = None
            pasos, diagnostico = [], f"No aplica: {error}"
        resultados.append({"categoria": categoria, "propiedad": propiedad, "izquierda": izquierda, "derecha": derecha,
                           "pasos": pasos, "cumple": cumple, "diagnostico": diagnostico})
    evaluadas = [r for r in resultados if r["cumple"] is not None]
    return {"resultados": resultados, "intermedios": calculados, "k": k,
            "evaluadas": len(evaluadas), "cumplidas": sum(1 for r in evaluadas if r["cumple"])}


def matriz_cero(filas, columnas):
    """Construye la matriz nula.

    Entrada: filas y columnas. Salida: matriz de ceros (Fraction).
    """
    return [[Fraction(0) for _ in range(columnas)] for _ in range(filas)]


def matriz_identidad(orden):
    """Construye la identidad de orden n.

    Entrada: orden (entero positivo). Salida: matriz identidad; lanza ValueError si el orden no es válido.
    """
    if not isinstance(orden, int) or orden < 1:
        raise ValueError("El orden de la identidad debe ser un entero positivo.")
    return [[Fraction(int(i == j)) for j in range(orden)] for i in range(orden)]


def transponer_matriz(A):
    """Calcula la transpuesta: la fila i de A pasa a ser la columna i.

    Entrada: matriz A (m × n). Salida: Aᵀ (n × m).
    """
    A = validar_matriz(A, "A")
    return [[A[i][j] for i in range(len(A))] for j in range(len(A[0]))]


def sumar_matrices(A, B):
    """Suma A + B entrada por entrada.

    Entrada: A y B de las mismas dimensiones. Salida: A + B; lanza ValueError si las dimensiones difieren.
    """
    A, B = validar_matriz(A, "A"), validar_matriz(B, "B")
    da, db = (len(A), len(A[0])), (len(B), len(B[0]))
    if da != db:
        raise ValueError(f"A es {da[0]}×{da[1]} y B es {db[0]}×{db[1]}; A + B no está definida: las dimensiones deben ser iguales.")
    return [[A[i][j] + B[i][j] for j in range(da[1])] for i in range(da[0])]


def restar_matrices(A, B):
    """Resta A − B entrada por entrada.

    Entrada: A y B de las mismas dimensiones. Salida: A − B; lanza ValueError si las dimensiones difieren.
    """
    A, B = validar_matriz(A, "A"), validar_matriz(B, "B")
    da, db = (len(A), len(A[0])), (len(B), len(B[0]))
    if da != db:
        raise ValueError(f"A es {da[0]}×{da[1]} y B es {db[0]}×{db[1]}; A - B no está definida: las dimensiones deben ser iguales.")
    return [[A[i][j] - B[i][j] for j in range(da[1])] for i in range(da[0])]


def multiplicar_matriz_escalar(escalar, A):
    """Multiplica cada entrada de A por el escalar.

    Entrada: escalar y matriz A. Salida: nueva matriz; lanza ValueError si el escalar no es numérico.
    """
    A = validar_matriz(A, "A")
    try:
        escalar = escalar if isinstance(escalar, Fraction) else Fraction(escalar)
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError("El escalar debe ser un número válido.") from error
    return [[escalar * valor for valor in fila] for fila in A]


def multiplicar_matrices(A, B):
    """Calcula el producto matricial AB fila por columna.

    Entrada: A (m × n) y B (n × q). Salida: AB (m × q); lanza ValueError si columnas(A) ≠ filas(B).
    """
    A, B = validar_matriz(A, "A"), validar_matriz(B, "B")
    m, n, p, q = len(A), len(A[0]), len(B), len(B[0])
    if n != p:
        raise ValueError(f"A es {m}×{n} y B es {p}×{q}; AB no está definido porque columnas(A) = {n} ≠ filas(B) = {p}.")
    return [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(q)] for i in range(m)]


def _terminos(izquierda, derecha, operador="·"):
    """Escribe la suma de productos de una fila por una columna, por ejemplo '1·2 + 3·4'.

    Entrada: entradas de la fila, de la columna y el operador. Salida: cadena.
    """
    return " + ".join(f"{formatear_numero(a)}{operador}{formatear_numero(b)}" for a, b in zip(izquierda, derecha)) or "0"


def procedimiento_operacion_matrices(A, operacion, B=None, escalar=None):
    """Calcula una operación básica (suma, resta, producto, escalar o transpuesta) con sus pasos y verificación.

    Entrada: A, operación, B y escalar según corresponda.
    Salida: diccionario con resultado, pasos, conclusión, resolución y verificación.
    """
    A = validar_matriz(A, "A")
    m, n = dimensiones_matriz(A)
    pasos = [f"Datos: A es una matriz {m}×{n}.", "A:", matriz_a_texto(A, False)]
    if operacion in ("suma", "resta", "producto"):
        B = validar_matriz(B, "B")
        p, q = dimensiones_matriz(B)
        pasos.append(f"B es una matriz {p}×{q}.")
        pasos += ["B:", matriz_a_texto(B, False)]
    def informe(resultado, conclusion):
        """Empaqueta el resultado de la operación con sus pasos, la resolución por expresión y su verificación.

        Entrada: resultado y conclusión. Salida: diccionario del informe.
        """
        textos = {"suma": "A+B", "resta": "A-B", "producto": "AB", "escalar": "rA", "transpuesta": "Aᵀ"}
        resolucion = resolver_expresion_matricial(textos[operacion], {"A": A, **({"B": B} if B is not None else {})}, {"r": escalar} if escalar is not None else {})
        resolucion["resultado"] = resultado
        resolucion["pasos"][-1]["resultado"] = resultado
        verificacion = verificar_resolucion(resolucion, usar_identidades=False)
        return {"resultado": resultado, "pasos": pasos + ["Resultado:", matriz_a_texto(resultado, False)],
                "conclusion": conclusion, "resolucion": resolucion, "verificacion": verificacion}
    if operacion in ("suma", "resta"):
        if (m, n) != (p, q):
            raise ValueError(f"A es {m}×{n} y B es {p}×{q}. La operación no está definida porque suma y resta exigen dimensiones idénticas.")
        signo, resultado = ("+", sumar_matrices(A, B)) if operacion == "suma" else ("−", restar_matrices(A, B))
        pasos.append(f"Condición cumplida: {m}×{n} = {p}×{q}. Se opera entrada por entrada.")
        for i in range(m):
            pasos.append("Fila " + str(i + 1) + ": " + ", ".join(
                f"({formatear_numero(A[i][j])}) {signo} ({formatear_numero(B[i][j])}) = {formatear_numero(resultado[i][j])}" for j in range(n)))
        return informe(resultado, f"La operación A {signo} B está definida y su resultado es una matriz {m}×{n}.")
    if operacion == "escalar":
        escalar = escalar if isinstance(escalar, Fraction) else Fraction(escalar)
        resultado = multiplicar_matriz_escalar(escalar, A)
        pasos.append(f"Se multiplica cada entrada por el escalar r = {formatear_numero(escalar)}.")
        for i in range(m):
            pasos.append("Fila " + str(i + 1) + ": " + ", ".join(
                f"{formatear_numero(escalar)}({formatear_numero(A[i][j])}) = {formatear_numero(resultado[i][j])}" for j in range(n)))
        return informe(resultado, f"rA está definida y conserva las dimensiones {m}×{n}.")
    if operacion == "transpuesta":
        resultado = transponer_matriz(A)
        pasos += ["Cada fila de A se convierte en una columna de Aᵀ."]
        pasos += [f"Fila {i + 1} de A = columna {i + 1} de Aᵀ: ({', '.join(formatear_numero(x) for x in fila)})." for i, fila in enumerate(A)]
        return informe(resultado, f"Aᵀ tiene dimensiones {n}×{m}; se intercambiaron filas y columnas.")
    if operacion == "producto":
        if n != p:
            raise ValueError(f"A es {m}×{n} y B es {p}×{q}. AB no está definido porque {n} ≠ {p}.")
        resultado = multiplicar_matrices(A, B)
        pasos.append(f"Condición cumplida: columnas(A) = filas(B) = {n}. AB tendrá dimensión {m}×{q}.")
        for i in range(m):
            for j in range(q):
                columna = [B[k][j] for k in range(n)]
                pasos.append(f"(AB){i + 1},{j + 1} = {_terminos(A[i], columna)} = {formatear_numero(resultado[i][j])}.")
        return informe(resultado, f"AB está definida y su resultado es una matriz {m}×{q}.")
    raise ValueError("Operación matricial desconocida.")


def comparar_matrices(izquierda, derecha, nombre_izquierdo="Lado izquierdo", nombre_derecho="Lado derecho"):
    """Compara dos matrices en dimensiones y entrada por entrada.

    Entrada: ambas matrices y sus nombres. Salida: diccionario con dimensiones, diferencias, «coinciden» y conclusión.
    """
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


def son_iguales(izquierda, derecha):
    """Comprobación de igualdad exacta entre dos matrices, dos vectores o dos escalares.

    Entrada: listas anidadas, listas simples o números. Salida: True o False.
    """
    def como_matriz(dato):
        """Convierte un vector en matriz columna y deja intactas las matrices.

        Entrada: lista. Salida: lista anidada.
        """
        return dato if dato and isinstance(dato[0], list) else [[valor] for valor in dato]
    if isinstance(izquierda, list) != isinstance(derecha, list):
        return False
    if not isinstance(izquierda, list):
        return Fraction(izquierda) == Fraction(derecha)
    if not izquierda or not derecha:
        return izquierda == derecha
    return comparar_matrices(como_matriz(izquierda), como_matriz(derecha))["coinciden"]


def verificar_propiedades_transpuesta(A, B=None, escalar=Fraction(1)):
    """Comprueba con A (y B) las propiedades de la transpuesta como casos particulares.

    Entrada: A, B opcional y escalar. Salida: diccionario propiedad → comparación de ambos lados.
    """
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
    claves = {"doble": "transpuesta_doble", "escalar": "transpuesta_escalar", "suma": "transpuesta_suma", "producto": "transpuesta_producto"}
    for nombre, resultado in propiedades.items():
        informe = verificar_propiedad_matricial(claves[nombre], {"A": A, **({"B": B} if B is not None else {})}, {"r": r})
        resultado["lados"] = informe["lados"]
        resultado["verificaciones"] = [verificar_resolucion(l["resolucion"], False) for l in informe["lados"][:2]]
    return propiedades


def verificar_propiedades_algebraicas(A, B, C, r=Fraction(1), s=Fraction(1)):
    """Comprueba con A, B, C, r y s las propiedades de suma, escalares y producto.

    Entrada: matrices A, B, C y escalares r, s. Salida: diccionario propiedad → comparación (o motivo si no está definida).
    """
    A, B, C = validar_matriz(A, "A"), validar_matriz(B, "B"), validar_matriz(C, "C")
    r, s = Fraction(r), Fraction(s)
    resultados = {}
    def prueba(nombre, izquierda, derecha):
        """Compara ambos lados de una propiedad y guarda el resultado.

        Entrada: nombre, lado izquierdo y lado derecho. Salida: None.
        """
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
    claves = {"cero_aditivo": "matriz_cero", "distributividad_escalar": "escalar_suma_matrices",
              "distributividad_izquierda": "distributiva_izquierda", "distributividad_derecha": "distributiva_derecha"}
    for nombre, resultado in resultados.items():
        informe = verificar_propiedad_matricial(claves.get(nombre, nombre), {"A": A, "B": B, "C": C}, {"r": r, "s": s})
        resultado["lados"] = informe["lados"]
        resultado["verificaciones"] = [verificar_resolucion(l["resolucion"], False) for l in informe["lados"][:2]]
    return resultados


def contraejemplos_matriciales():
    """Construye los contraejemplos clásicos del producto: no conmutatividad, orden, cancelación y divisores de cero.

    Salida: diccionario con las matrices, sus productos y la conclusión de cada contraejemplo.
    """
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
    """Construye el banco de ejercicios tipo examen con la expresión, propiedad o contraejemplo que los resuelve.

    Salida: lista de diccionarios (tema, matrices, consigna y forma de resolverlo).
    """
    return [
        {"tema": "Suma con fracciones", "A": [["1/2", "-1"], ["3", "0"]], "B": [["1/3", "2"], ["-3", "5/2"]],
         "consigna": "Calcule A+B entrada por entrada y justifique la compatibilidad de dimensiones.",
         "expresion": "A + B"},
        {"tema": "Producto rectangular", "A": [[1, 2, -1], [0, 3, 4]], "B": [[2, 1], [-1, 0], [3, 2]],
         "consigna": "Calcule AB fila por columna e indique la dimensión del resultado.",
         "expresion": "AB"},
        {"tema": "Transpuesta", "A": [[1, -2, 3], ["1/2", 0, 4]],
         "consigna": "Calcule Aᵀ y verifique (Aᵀ)ᵀ=A para este caso particular.",
         "propiedad": "transpuesta_doble"},
        {"tema": "Propiedad y contraejemplo", "consigna": "Decida si AB=BA vale siempre. Dé un contraejemplo y compruebe ambos productos.",
         "contraejemplo": "no_conmutatividad"},
        {"tema": "Cancelación", "consigna": "Explique por qué AB=AC no implica B=C sin que A sea invertible.",
         "contraejemplo": "cancelacion"},
        {"tema": "Distributividad con tres matrices", "A": [[1, 2], [0, -1], [3, 1]],
         "B": [[2, 0, 1], [1, -1, 2]], "C": [[0, 3, -1], ["1/2", 1, 0]],
         "consigna": "Calcule A(B + C) paso a paso y compruébelo calculando AB + AC por separado.",
         "expresion": "A(B + C)"},
        {"tema": "Transpuesta de un producto", "A": [[1, 2, 0], [-1, 3, 1]], "B": [[2, 1], [0, -1], [1, 4]],
         "consigna": "Calcule (AB)ᵀ y compare con BᵀAᵀ; explique por qué se invierte el orden.",
         "expresion": "(AB)ᵀ"},
        {"tema": "Combinación con escalares", "A": [[1, -1], [2, 0]], "B": [["1/2", 2], [-1, 3]],
         "C": [[4, 0], [-2, 1]],
         "consigna": "Calcule 2A − 3B + C indicando el orden de las operaciones.",
         "expresion": "2A − 3B + C"},
    ]



_TABLA_SUBINDICES = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def subindice(i, j):
    """Escribe el subíndice de una entrada: '₁₂', o '₁,₁₀' si algún índice tiene dos cifras.

    Entrada: índices i y j (desde 1). Salida: cadena.
    """
    texto = f"{i}{j}" if i < 10 and j < 10 else f"{i},{j}"
    return texto.translate(_TABLA_SUBINDICES)


def formatear_dimension(dimension):
    """Escribe una dimensión como 'm×n'.

    Entrada: tupla (filas, columnas). Salida: cadena.
    """
    return f"{dimension[0]}×{dimension[1]}"


def matriz_en_linea(matriz):
    """Escribe una matriz en una línea, por ejemplo '[1 2; 3 4]'.

    Entrada: matriz. Salida: cadena.
    """
    return "[" + "; ".join(" ".join(formatear_numero(v) for v in fila) for fila in matriz) + "]"


def _entre_parentesis(valor):
    """Escribe un número entre paréntesis para las sustituciones, por ejemplo (-1/2).

    Entrada: número. Salida: cadena.
    """
    return f"({formatear_numero(valor)})"


def _suma_en_texto(valores):
    """Escribe una suma con sus signos, por ejemplo [2, -2, 3] → '2 - 2 + 3'.

    Entrada: lista de números. Salida: cadena ('0' si está vacía).
    """
    partes = []
    for valor in valores:
        if not partes:
            partes.append(formatear_numero(valor))
        else:
            partes.append(f"- {formatear_numero(-valor)}" if valor < 0 else f"+ {formatear_numero(valor)}")
    return " ".join(partes) if partes else "0"


class ErrorExpresion(ValueError):
    """Error de escritura o de dimensiones en una expresión matricial; guarda la posición del carácter."""

    def __init__(self, mensaje, posicion=None):
        """Guarda el mensaje y la posición del error.

        Entrada: mensaje y posición (índice del carácter o None). Salida: None.
        """
        super().__init__(mensaje)
        self.posicion = posicion


def tokenizar_expresion(texto):
    """Divide la expresión en símbolos: números, matrices, identidades, escalares, operadores, paréntesis, ᵀ y ⁻¹.

    Entrada: texto de la expresión. Salida: lista de (tipo, valor, posición, lexema); lanza ErrorExpresion.
    """
    texto = texto.replace("−", "-").replace("×", "*").replace("·", "*")
    tokens = []
    i, n = 0, len(texto)
    while i < n:
        caracter = texto[i]
        if caracter.isspace():
            i += 1
        elif caracter.isdigit() or (caracter == "." and i + 1 < n and texto[i + 1].isdigit()):
            j = i
            while j < n and (texto[j].isdigit() or texto[j] == "."):
                j += 1
            if j + 1 < n and texto[j] == "/" and texto[j + 1].isdigit():
                j += 1
                while j < n and texto[j].isdigit():
                    j += 1
            lexema = texto[i:j]
            try:
                valor = Fraction(lexema)
            except (ValueError, ZeroDivisionError):
                raise ErrorExpresion(f"«{lexema}» no es un número válido.", i) from None
            tokens.append(("numero", valor, i, lexema))
            i = j
        elif texto.startswith("⁻¹", i):
            tokens.append(("INV", "INV", i, "⁻¹"))
            i += 2
        elif caracter in ("ᵀ", "'"):  # antes que isalpha(): «ᵀ» cuenta como letra en Python
            tokens.append(("T", "T", i, caracter))
            i += 1
        elif caracter == "I" and i + 1 < n and texto[i + 1].isdigit():
            j = i + 1
            while j < n and texto[j].isdigit():
                j += 1
            tokens.append(("identidad", int(texto[i + 1:j]), i, texto[i:j]))
            i = j
        elif caracter.isalpha() and caracter.isupper():
            tokens.append(("matriz", caracter, i, caracter))
            i += 1
        elif caracter in ("r", "s"):
            tokens.append(("escalar", caracter, i, caracter))
            i += 1
        elif caracter.isalpha():
            raise ErrorExpresion(f"«{caracter}» no es un símbolo válido: las matrices van en mayúscula "
                                 f"(A, B, C) y los escalares son números, r o s.", i)
        elif caracter in "+-*()":
            tokens.append((caracter, caracter, i, caracter))
            i += 1
        elif caracter == "^":
            j = i + 1
            while j < n and texto[j].isspace():
                j += 1
            if j < n and texto[j] in "Tt":
                tokens.append(("T", "T", i, texto[i:j + 1]))
                i = j + 1
            elif texto.startswith("-1", j) and (j + 2 == n or not (texto[j+2].isdigit() or texto[j+2] == ".")):
                tokens.append(("INV", "INV", i, texto[i:j+2]))
                i = j + 2
            elif texto.startswith("(-1)", j):
                tokens.append(("INV", "INV", i, texto[i:j+4]))
                i = j + 4
            else:
                raise ErrorExpresion("Después de ^ solo se admite T o -1 (inversa), por ejemplo A^T o A^-1.", i)
        else:
            raise ErrorExpresion(f"El carácter «{caracter}» no está permitido.", i)
    return tokens


class NodoExpresion:
    """Nodo del árbol de una expresión matricial (operación o dato) con su posición en el texto."""

    PRECEDENCIA = {"suma": 1, "resta": 1, "producto": 2, "negativo": 3, "transpuesta": 4, "inversa": 4,
                   "matriz": 5, "identidad": 5, "numero": 5, "escalar": 5}

    def __init__(self, tipo, hijos=(), valor=None, posicion=None, parentesis=False):
        """Crea un nodo del árbol.

        Entrada: tipo, hijos, valor, posición y si el usuario lo agrupó entre paréntesis. Salida: None.
        """
        self.tipo = tipo
        self.hijos = list(hijos)
        self.valor = valor
        self.posicion = posicion
        self.parentesis = parentesis

    @property
    def precedencia(self):
        """Prioridad del nodo para decidir dónde hacen falta paréntesis.

        Salida: entero (mayor = se evalúa antes).
        """
        return self.PRECEDENCIA[self.tipo]

    @property
    def es_hoja(self):
        """Indica si el nodo es un dato (matriz, número, escalar o identidad) sin hijos.

        Salida: True o False.
        """
        return not self.hijos

    def _operando(self, hijo, minimo, derecha=False, en_producto=False):
        """Escribe un hijo con paréntesis solo si la precedencia o la agrupación del usuario lo exigen.

        Entrada: hijo, precedencia mínima y su posición. Salida: cadena.
        """
        texto = hijo.texto()
        if (hijo.precedencia < minimo or (derecha and hijo.tipo == "negativo")
                or (hijo.parentesis and not hijo.es_hoja)):
            return f"({texto})"
        if en_producto and hijo.tipo == "numero" and (hijo.valor.denominator != 1 or hijo.valor < 0):
            return f"({texto})"
        return texto

    def texto(self):
        """Escribe la expresión en notación habitual con los paréntesis mínimos, por ejemplo A(B + C).

        Salida: cadena.
        """
        tipo = self.tipo
        if tipo in ("matriz", "escalar"):
            return self.valor
        if tipo == "identidad":
            return "I" + str(self.valor).translate(_TABLA_SUBINDICES)
        if tipo == "numero":
            return formatear_numero(self.valor)
        if tipo == "transpuesta":
            return self._operando(self.hijos[0], 5) + "ᵀ"
        if tipo == "inversa":
            return self._operando(self.hijos[0], 5) + "⁻¹"
        if tipo == "negativo":
            return "−" + self._operando(self.hijos[0], 3)
        if tipo in ("suma", "resta"):
            signo = " + " if tipo == "suma" else " − "
            return self._operando(self.hijos[0], 1) + signo + self._operando(self.hijos[1], 2, derecha=True)
        izquierda = self._operando(self.hijos[0], 2, en_producto=True)
        derecha = self._operando(self.hijos[1], 3, derecha=True, en_producto=True)
        separador = "·" if derecha[0].isdigit() else ""
        return izquierda + separador + derecha

    def texto_completo(self, externo=True):
        """Escribe la expresión con cada operación entre paréntesis para mostrar el orden real de cálculo.

        Entrada: externo (sin paréntesis exteriores). Salida: cadena.
        """
        tipo = self.tipo
        if self.es_hoja:
            if tipo == "numero" and not externo and (self.valor.denominator != 1 or self.valor < 0):
                return f"({self.texto()})"
            return self.texto()
        if tipo in ("transpuesta", "inversa"):
            hijo = self.hijos[0]
            return (hijo.texto() if hijo.es_hoja else f"({hijo.texto_completo()})") + ("ᵀ" if tipo == "transpuesta" else "⁻¹")
        if tipo == "negativo":
            texto = "−" + self.hijos[0].texto_completo(False)
        else:
            signo = {"suma": " + ", "resta": " − ", "producto": "·"}[tipo]
            texto = self.hijos[0].texto_completo(False) + signo + self.hijos[1].texto_completo(False)
        return texto if externo else f"({texto})"

    def nombres_matrices(self):
        """Reúne las letras de matriz que aparecen en la subexpresión.

        Salida: conjunto de nombres.
        """
        if self.tipo == "matriz":
            return {self.valor}
        nombres = set()
        for hijo in self.hijos:
            nombres |= hijo.nombres_matrices()
        return nombres

    def nombres_escalares(self):
        """Reúne los escalares (r, s) que aparecen en la subexpresión.

        Salida: conjunto de nombres.
        """
        if self.tipo == "escalar":
            return {self.valor}
        nombres = set()
        for hijo in self.hijos:
            nombres |= hijo.nombres_escalares()
        return nombres

    def es_matricial(self):
        """Indica si el valor de la subexpresión es una matriz (y no un número).

        Salida: True o False.
        """
        if self.tipo in ("matriz", "identidad"):
            return True
        if self.tipo in ("numero", "escalar"):
            return False
        return any(hijo.es_matricial() for hijo in self.hijos)


class _AnalizadorExpresion:
    """Analizador descendente de expresiones matriciales; la precedencia va de la suma a ᵀ y ⁻¹.

    Gramática: expresion → termino → factor → postfijo → primario (ver cada método).
    """

    INICIO_DE_FACTOR = ("numero", "matriz", "identidad", "escalar", "(", "-")

    def __init__(self, tokens, longitud):
        """Prepara la lectura de los símbolos.

        Entrada: lista de símbolos y longitud del texto. Salida: None.
        """
        self.tokens = tokens
        self.longitud = longitud
        self.indice = 0

    def actual(self):
        """Obtiene el símbolo en la posición de lectura.

        Salida: el símbolo, o None al final.
        """
        return self.tokens[self.indice] if self.indice < len(self.tokens) else None

    def ver(self):
        """Obtiene el tipo del símbolo actual sin avanzar.

        Salida: tipo, o None al final.
        """
        token = self.actual()
        return token[0] if token else None

    def tomar(self):
        """Obtiene el símbolo actual y avanza una posición.

        Salida: el símbolo leído.
        """
        token = self.actual()
        self.indice += 1
        return token

    def expresion(self):
        """Regla expresion := termino (('+' | '-') termino)*.

        Salida: nodo de la suma o resta.
        """
        nodo = self.termino()
        while self.ver() in ("+", "-"):
            token = self.tomar()
            nodo = NodoExpresion("suma" if token[0] == "+" else "resta", [nodo, self.termino()], posicion=token[2])
        return nodo

    def termino(self):
        """Regla termino := factor (['*'] factor)*; el producto también se reconoce por yuxtaposición (AB, 2A).

        Salida: nodo del producto.
        """
        nodo = self.factor()
        while True:
            tipo = self.ver()
            if tipo == "*":
                token = self.tomar()
                if self.ver() not in self.INICIO_DE_FACTOR:
                    raise ErrorExpresion("Falta un factor después del signo de multiplicación.", token[2])
            elif tipo not in ("numero", "matriz", "identidad", "escalar", "("):
                return nodo
            nodo = NodoExpresion("producto", [nodo, self.factor()])

    def factor(self):
        """Regla factor := '-' factor | postfijo.

        Salida: nodo del factor.
        """
        if self.ver() == "-":
            token = self.tomar()
            return NodoExpresion("negativo", [self.factor()], posicion=token[2])
        return self.postfijo()

    def postfijo(self):
        """Regla postfijo := primario ('ᵀ' | '⁻¹')*.

        Salida: nodo con sus transpuestas e inversas.
        """
        nodo = self.primario()
        while self.ver() in ("T", "INV"):
            token = self.tomar()
            nodo = NodoExpresion("transpuesta" if token[0] == "T" else "inversa", [nodo], posicion=token[2])
        return nodo

    def primario(self):
        """Regla primario := número | matriz | identidad | escalar | '(' expresion ')'.

        Salida: nodo; lanza ErrorExpresion si falta un operando o un paréntesis.
        """
        token = self.actual()
        if token is None:
            raise ErrorExpresion("La expresión está incompleta: falta un operando al final.", self.longitud)
        tipo, valor, posicion, lexema = token
        if tipo == "(":
            self.tomar()
            if self.ver() == ")":
                raise ErrorExpresion("Hay un par de paréntesis vacío «()».", posicion)
            nodo = self.expresion()
            if self.ver() != ")":
                raise ErrorExpresion("Falta cerrar un paréntesis «)».", posicion)
            self.tomar()
            nodo.parentesis = True
            return nodo
        if tipo in ("numero", "matriz", "identidad", "escalar"):
            self.tomar()
            return NodoExpresion(tipo, valor=valor, posicion=posicion)
        if tipo == ")":
            raise ErrorExpresion("Hay un paréntesis «)» sin una expresión antes.", posicion)
        if tipo == "T":
            raise ErrorExpresion("La transpuesta ᵀ debe ir justo después de una matriz o de un paréntesis.", posicion)
        raise ErrorExpresion(f"Falta un operando antes de «{lexema}».", posicion)


def analizar_expresion_matricial(texto):
    """Convierte el texto de una expresión en su árbol de nodos.

    Entrada: texto. Salida: NodoExpresion raíz; lanza ErrorExpresion con la posición del problema.
    """
    if not texto or not texto.strip():
        raise ErrorExpresion("Escribe una expresión, por ejemplo A(B + C).", 0)
    tokens = tokenizar_expresion(texto)
    analizador = _AnalizadorExpresion(tokens, len(texto))
    nodo = analizador.expresion()
    sobrante = analizador.actual()
    if sobrante is not None:
        if sobrante[0] == ")":
            raise ErrorExpresion("Hay un paréntesis de cierre «)» que no tiene apertura.", sobrante[2])
        raise ErrorExpresion(f"No se esperaba «{sobrante[3]}» en esta posición.", sobrante[2])
    return nodo


def _letra(nodo, defecto):
    """Elige la letra de las entradas de un operando: a para A, b para B; la de defecto si es una subexpresión.

    Entrada: nodo y letra por defecto. Salida: cadena.
    """
    if nodo.tipo == "matriz":
        return nodo.valor.lower()
    if nodo.tipo == "identidad":
        return "δ"
    return defecto


def _nombre_operando(nodo):
    """Escribe el nombre de un operando: la hoja tal cual y las subexpresiones entre paréntesis.

    Entrada: nodo. Salida: cadena.
    """
    return nodo.texto() if nodo.es_hoja or nodo.tipo == "transpuesta" else f"({nodo.texto()})"


def _argumento(nodo):
    """Escribe un nodo entre paréntesis para usarlo como argumento, por ejemplo dim(A) o columnas(B + C).

    Entrada: nodo. Salida: cadena.
    """
    return f"({nodo.texto()})"


def _buscar_posicion(nodo, tipo, valor):
    """Busca la posición en el texto del primer nodo con ese tipo y valor.

    Entrada: nodo raíz, tipo y valor. Salida: índice del carácter o None.
    """
    if nodo.tipo == tipo and nodo.valor == valor:
        return nodo.posicion
    for hijo in nodo.hijos:
        posicion = _buscar_posicion(hijo, tipo, valor)
        if posicion is not None:
            return posicion
    return None


def revisar_dimensiones(nodo, dimensiones, escalares=("r", "s")):
    """Recorre la expresión solo con dimensiones (sin calcular) y anota la condición de cada operación.

    Entrada: árbol, dimensiones por matriz y escalares disponibles.
    Salida: (condiciones, dimensión final o None si alguna operación no está definida).
    """
    condiciones = []

    def recorrer(n):
        """Calcula la dimensión de una subexpresión y anota su condición.

        Entrada: nodo. Salida: (filas, columnas) o None si es un número.
        """
        if n.tipo == "matriz":
            if n.valor not in dimensiones:
                raise ErrorExpresion(f"La matriz {n.valor} no está definida." + (
                    " Para la transpuesta escribe Aᵀ, A^T o A'." if n.valor == "T" else
                    " Para la identidad escribe I2, I3, …" if n.valor == "I" else ""), n.posicion)
            return dimensiones[n.valor]
        if n.tipo == "identidad":
            if not 1 <= n.valor <= LIMITE_DIMENSION:
                raise ErrorExpresion(f"La identidad debe tener orden entre 1 y {LIMITE_DIMENSION}.", n.posicion)
            return (n.valor, n.valor)
        if n.tipo == "numero":
            return None
        if n.tipo == "escalar":
            if n.valor not in escalares:
                raise ErrorExpresion(f"Falta el valor del escalar {n.valor}.", n.posicion)
            return None
        dims = [recorrer(h) for h in n.hijos]
        texto = n.texto()
        if n.tipo == "inversa":
            cumple = dims[0] is not None and dims[0][0] == dims[0][1]
            condiciones.append({"operacion": texto, "requisito": "Matriz cuadrada; se comprobará det≠0 durante el cálculo.",
                                "cumple": cumple, "dimension": dims[0] if cumple else None})
            if not cumple:
                raise _DimensionNoDefinida()
            return dims[0]
        if n.tipo == "transpuesta":
            if dims[0] is None:
                return None
            m, k = dims[0]
            condiciones.append({"operacion": texto, "requisito": f"siempre definida: {formatear_dimension((m, k))} → "
                                f"{formatear_dimension((k, m))}", "cumple": True, "dimension": (k, m)})
            return (k, m)
        if n.tipo == "negativo":
            if dims[0] is not None:
                condiciones.append({"operacion": texto, "requisito": "multiplicar por −1 conserva el tamaño",
                                    "cumple": True, "dimension": dims[0]})
            return dims[0]
        izquierda, derecha = dims
        nombres = [_argumento(h) for h in n.hijos]
        if n.tipo in ("suma", "resta"):
            if izquierda is None and derecha is None:
                return None
            if izquierda is None or derecha is None:
                condiciones.append({"operacion": texto, "requisito": "no se puede sumar o restar un número y una matriz",
                                    "cumple": False, "dimension": None})
                raise _DimensionNoDefinida()
            cumple = izquierda == derecha
            condiciones.append({
                "operacion": texto,
                "requisito": f"dim{nombres[0]} = dim{nombres[1]}: {formatear_dimension(izquierda)} "
                             f"{'=' if cumple else '≠'} {formatear_dimension(derecha)}",
                "cumple": cumple, "dimension": izquierda if cumple else None})
            if not cumple:
                raise _DimensionNoDefinida()
            return izquierda
        if izquierda is None or derecha is None:
            matriz = izquierda or derecha
            if matriz is not None:
                condiciones.append({"operacion": texto, "requisito": "escalar por matriz: conserva el tamaño "
                                    f"{formatear_dimension(matriz)}", "cumple": True, "dimension": matriz})
            return matriz
        cumple = izquierda[1] == derecha[0]
        condiciones.append({
            "operacion": texto,
            "requisito": f"columnas{nombres[0]} = filas{nombres[1]}: {izquierda[1]} {'=' if cumple else '≠'} "
                         f"{derecha[0]}",
            "cumple": cumple, "dimension": (izquierda[0], derecha[1]) if cumple else None})
        if not cumple:
            raise _DimensionNoDefinida()
        return (izquierda[0], derecha[1])

    try:
        final = recorrer(nodo)
    except _DimensionNoDefinida:
        final = None
    return condiciones, final


class _DimensionNoDefinida(Exception):
    """Señal interna: una operación no está definida con las dimensiones dadas."""


class _OperacionNoDefinida(Exception):
    """Señal interna con el mensaje de la operación que no se pudo calcular."""
    def __init__(self, mensaje):
        """Guarda el motivo por el que la operación no está definida.

        Entrada: mensaje. Salida: None.
        """
        super().__init__(mensaje)


TIPOS_OPERACION_MATRICIAL = {
    "inversa": "Inversa",
    "suma": "Suma", "resta": "Resta", "producto": "Producto", "escalar": "Escalar por matriz",
    "transpuesta": "Transposición", "aritmetica": "Operación con números",
    "datos": "Datos", "respuesta": "Respuesta",
}

REGLAS_OPERACION = {
    "inversa": "Inversa: reducir [M | I] a [I | M⁻¹], con det(M)≠0",
    "suma": "Definición de la suma: se suman las entradas de la misma posición",
    "resta": "Definición de la resta: se restan las entradas de la misma posición",
    "producto": "Producto matricial: cada entrada es una fila de la izquierda por una columna de la derecha",
    "escalar": "Multiplicación por escalar: el escalar multiplica cada entrada",
    "transpuesta": "Transpuesta: las filas pasan a ser columnas",
    "aritmetica": "Aritmética de números reales",
}


class _ResolutorMatricial:
    """Evalúa el árbol de abajo hacia arriba y registra cada operación intermedia con su procedimiento."""

    def __init__(self, matrices, escalares):
        """Prepara la evaluación.

        Entrada: matrices y escalares ya validados. Salida: None.
        """
        self.matrices = matrices
        self.escalares = escalares
        self.pasos = []

    def valor(self, nodo):
        """Evalúa un nodo y sus hijos, registrando cada operación.

        Entrada: nodo. Salida: (tipo, valor) con tipo 'matriz' o 'numero'.
        """
        tipo = nodo.tipo
        if tipo == "matriz":
            return ("matriz", self.matrices[nodo.valor])
        if tipo == "identidad":
            return ("matriz", matriz_identidad(nodo.valor))
        if tipo == "numero":
            return ("numero", nodo.valor)
        if tipo == "escalar":
            return ("numero", self.escalares[nodo.valor])
        operandos = [self.valor(hijo) for hijo in nodo.hijos]
        return getattr(self, "_" + tipo)(nodo, *operandos)

    def _registrar(self, nodo, tipo, operandos, condicion, cumple, regla, descripcion, entradas=(),
                   resultado=None, advertencias=(), extra=()):
        """Agrega un paso con operandos, condición, regla, cálculo por entrada y resultado.

        Entrada: nodo, tipo y datos del paso. Salida: el diccionario del paso.
        """
        paso = {
            "tipo": tipo,
            "titulo": f"Calcular {nodo.texto()}",
            "expresion": nodo.texto(),
            "operandos": [(_nombre_operando(h), v) for h, v in operandos],
            "condicion": {"texto": condicion, "cumple": cumple},
            "regla": regla,
            "descripcion": descripcion,
            "entradas": list(entradas),
            "resultado": resultado,
            "dimension": (len(resultado), len(resultado[0])) if isinstance(resultado, list) else None,
            "advertencias": list(advertencias),
            "extra": list(extra),
        }
        self.pasos.append(paso)
        return paso

    def _fallar(self, nodo, tipo, operandos, condicion, mensaje):
        """Registra la operación no definida y detiene la evaluación.

        Entrada: nodo, tipo, operandos, condición y mensaje. Salida: no retorna; lanza _OperacionNoDefinida.
        """
        self._registrar(nodo, tipo, operandos, condicion, False, REGLAS_OPERACION.get(tipo, ""), mensaje)
        raise _OperacionNoDefinida(mensaje)

    def _aritmetica(self, nodo, operandos, valor, simbolo):
        """Opera dos números (o niega uno) y registra el paso.

        Entrada: nodo, operandos, valor y símbolo. Salida: ('numero', valor).
        """
        a, b = (operandos + [None])[:2]
        texto = (f"{_entre_parentesis(a[1])} {simbolo} {_entre_parentesis(b[1])} = {formatear_numero(valor)}"
                 if b is not None else f"−{_entre_parentesis(a[1])} = {formatear_numero(valor)}")
        paso = self._registrar(nodo, "aritmetica", list(zip(nodo.hijos, [o[1] for o in operandos])),
                               "Operación entre números: siempre definida.", True, REGLAS_OPERACION["aritmetica"],
                               "Se opera con los escalares antes de usarlos con matrices.", [{"lineas": [texto]}], valor)
        paso["simbolo"] = simbolo if b is not None else "negativo"
        return ("numero", valor)

    def _suma(self, nodo, a, b, resta=False):
        """Suma o resta matrices entrada por entrada (o números) y registra cada entrada.

        Entrada: nodo, operandos a y b, y resta (bool). Salida: ('matriz', resultado) o ('numero', valor).
        """
        signo = "−" if resta else "+"
        tipo = "resta" if resta else "suma"
        izquierda, derecha = nodo.hijos
        if a[0] == "numero" and b[0] == "numero":
            return self._aritmetica(nodo, [a, b], a[1] - b[1] if resta else a[1] + b[1], signo)
        operandos = list(zip(nodo.hijos, [a[1], b[1]]))
        nx, ny = _nombre_operando(izquierda), _nombre_operando(derecha)
        if a[0] != b[0]:
            self._fallar(nodo, tipo, operandos, "Uno de los operandos es un número y el otro una matriz.",
                         f"No se puede calcular {nodo.texto()}: no está definido {'restar' if resta else 'sumar'} "
                         f"un número y una matriz.")
        X, Y = a[1], b[1]
        dx, dy = (len(X), len(X[0])), (len(Y), len(Y[0]))
        condicion = (f"dim{_argumento(izquierda)} = {formatear_dimension(dx)} y dim{_argumento(derecha)} = "
                     f"{formatear_dimension(dy)}: "
                     + ("tienen el mismo tamaño ✓" if dx == dy else "tamaños distintos ✗"))
        if dx != dy:
            self._fallar(nodo, tipo, operandos, condicion,
                         f"No se puede calcular {nodo.texto()}: {nx} es {formatear_dimension(dx)} y {ny} es "
                         f"{formatear_dimension(dy)}. La {'resta' if resta else 'suma'} solo está definida para "
                         f"matrices del mismo tamaño.")
        x, y = _letra(izquierda, "x"), _letra(derecha, "y")
        R = [[X[i][j] - Y[i][j] if resta else X[i][j] + Y[i][j] for j in range(dx[1])] for i in range(dx[0])]
        entradas = []
        for i in range(dx[0]):
            for j in range(dx[1]):
                sub = subindice(i + 1, j + 1)
                entradas.append({"posicion": (i + 1, j + 1), "lineas": [
                    f"Entrada ({i + 1},{j + 1}):  {x}{sub} {signo} {y}{sub} = {_entre_parentesis(X[i][j])} {signo} "
                    f"{_entre_parentesis(Y[i][j])} = {formatear_numero(R[i][j])}"]})
        nombres = "" if (izquierda.es_hoja and derecha.es_hoja) else f"   (X = {izquierda.texto()}, Y = {derecha.texto()})"
        regla = f"({'X' if x == 'x' else x.upper()} {signo} {'Y' if y == 'y' else y.upper()})ᵢⱼ = {x}ᵢⱼ {signo} {y}ᵢⱼ{nombres}"
        descripcion = (f"Se {'restan' if resta else 'suman'} las entradas que ocupan la misma posición en {nx} y {ny}; "
                       f"el resultado conserva el tamaño {formatear_dimension(dx)}.")
        self._registrar(nodo, tipo, operandos, condicion, True, regla, descripcion, entradas, R)
        return ("matriz", R)

    def _resta(self, nodo, a, b):
        """Resta dos operandos reutilizando la rutina de la suma.

        Entrada: nodo y operandos a y b. Salida: ('matriz', A − B) o ('numero', a − b).
        """
        return self._suma(nodo, a, b, resta=True)

    def _escalar_por_matriz(self, nodo, escalar, matriz, operandos, nombre_matriz, letra, titulo=None):
        """Multiplica una matriz por un escalar y registra cada entrada.

        Entrada: nodo, escalar, matriz, operandos, nombre, letra y título opcional. Salida: ('matriz', resultado).
        """
        r = escalar
        R = [[r * v for v in fila] for fila in matriz]
        entradas = []
        for i, fila in enumerate(matriz):
            for j, v in enumerate(fila):
                entradas.append({"posicion": (i + 1, j + 1), "lineas": [
                    f"Entrada ({i + 1},{j + 1}):  {_entre_parentesis(r)}·{letra}{subindice(i + 1, j + 1)} = "
                    f"{_entre_parentesis(r)}·{_entre_parentesis(v)} = {formatear_numero(R[i][j])}"]})
        dimension = formatear_dimension((len(matriz), len(matriz[0])))
        paso = self._registrar(
            nodo, "escalar", operandos,
            f"Un escalar puede multiplicar cualquier matriz: {nombre_matriz} es {dimension} y el resultado también ✓",
            True, f"(r·X)ᵢⱼ = r·xᵢⱼ   con r = {formatear_numero(r)}",
            f"Se multiplica cada entrada de {nombre_matriz} por {formatear_numero(r)}; el tamaño no cambia.",
            entradas, R)
        paso["escalar"] = r
        if titulo:
            paso["titulo"] = titulo
        return ("matriz", R)

    def _producto(self, nodo, a, b):
        """Calcula el producto fila por columna (o escalar por matriz) con su condición de dimensiones.

        Entrada: nodo y operandos a y b. Salida: ('matriz', producto) o ('numero', valor).
        """
        izquierda, derecha = nodo.hijos
        if a[0] == "numero" and b[0] == "numero":
            return self._aritmetica(nodo, [a, b], a[1] * b[1], "·")
        operandos = list(zip(nodo.hijos, [a[1], b[1]]))
        if a[0] == "numero":
            return self._escalar_por_matriz(nodo, a[1], b[1], operandos, _nombre_operando(derecha), _letra(derecha, "x"))
        if b[0] == "numero":
            return self._escalar_por_matriz(nodo, b[1], a[1], operandos, _nombre_operando(izquierda), _letra(izquierda, "x"))

        X, Y = a[1], b[1]
        m, n, p, q = len(X), len(X[0]), len(Y), len(Y[0])
        nx, ny = _nombre_operando(izquierda), _nombre_operando(derecha)
        condicion = (f"{nx} es {m}×{n} y {ny} es {p}×{q}: columnas{_argumento(izquierda)} = {n} "
                     + (f"= filas{_argumento(derecha)} = {p} ✓  →  el resultado será {m}×{q}" if n == p
                        else f"≠ filas{_argumento(derecha)} = {p} ✗"))
        if n != p:
            self._fallar(nodo, "producto", operandos, condicion,
                         f"No se puede calcular {nodo.texto()}: {nx} es {m}×{n} y {ny} es {p}×{q}. El producto exige "
                         f"que el número de columnas de {nx} ({n}) sea igual al número de filas de {ny} ({p}).")
        x, y = _letra(izquierda, "x"), _letra(derecha, "y")
        R = [[sum(X[i][k] * Y[k][j] for k in range(n)) for j in range(q)] for i in range(m)]
        entradas = []
        for i in range(m):
            for j in range(q):
                sub = subindice(i + 1, j + 1)
                simbolico = " + ".join(f"{x}{subindice(i + 1, k + 1)}·{y}{subindice(k + 1, j + 1)}" for k in range(n))
                sustitucion = " + ".join(f"{_entre_parentesis(X[i][k])}{_entre_parentesis(Y[k][j])}" for k in range(n))
                productos = [X[i][k] * Y[k][j] for k in range(n)]
                lineas = [f"Entrada ({i + 1},{j + 1}): fila {i + 1} de {nx} por columna {j + 1} de {ny}",
                          f"   c{sub} = {simbolico}",
                          f"        = {sustitucion}"]
                if n > 1:
                    lineas.append(f"        = {_suma_en_texto(productos)}")
                lineas.append(f"        = {formatear_numero(R[i][j])}")
                entradas.append({"posicion": (i + 1, j + 1), "lineas": lineas})

        advertencias = ["Es un producto fila por columna, no entrada por entrada: cada entrada combina una fila "
                        f"completa de {nx} con una columna completa de {ny}."]
        if (m, n) == (p, q):
            elemento = [[X[i][j] * Y[i][j] for j in range(n)] for i in range(m)]
            if elemento != R:
                advertencias.append(f"Multiplicar solo las entradas de la misma posición daría {matriz_en_linea(elemento)}, "
                                    f"que no es {nodo.texto()}.")
        if q == m:
            invertido = multiplicar_matrices(Y, X)
            orden = f"{ny}{nx}" if izquierda.es_hoja and derecha.es_hoja else f"{ny}·{nx}"
            if invertido != R:
                advertencias.append(f"El orden importa: {orden} también está definido y da {matriz_en_linea(invertido)}, "
                                    f"distinto de {nodo.texto()}.")
            else:
                advertencias.append(f"En este caso {orden} da el mismo resultado, pero en general el producto de "
                                    f"matrices no es conmutativo.")
        else:
            advertencias.append(f"El orden importa: {ny}·{nx} ni siquiera está definido "
                                f"(columnas{_argumento(derecha)} = {q} ≠ filas{_argumento(izquierda)} = {m}).")
        nombres = "" if (izquierda.es_hoja and derecha.es_hoja) else f"   (X = {izquierda.texto()}, Y = {derecha.texto()})"
        self._registrar(
            nodo, "producto", operandos, condicion, True,
            f"cᵢⱼ = Σₖ {x}ᵢₖ·{y}ₖⱼ,  k = 1, …, {n}{nombres}",
            f"Cada entrada (i, j) es la fila i de {nx} multiplicada por la columna j de {ny}: se multiplican "
            f"{n} pares de números y se suman. El resultado es {m}×{q}.",
            entradas, R, advertencias)
        return ("matriz", R)

    def _transpuesta(self, nodo, a):
        """Calcula la transpuesta, registra cada entrada y advierte sobre (XY)ᵀ = YᵀXᵀ.

        Entrada: nodo y operando. Salida: ('matriz', transpuesta).
        """
        hijo = nodo.hijos[0]
        operandos = [(hijo, a[1])]
        if a[0] == "numero":
            self._fallar(nodo, "transpuesta", operandos, "La transpuesta se aplica a matrices.",
                         f"No se puede calcular {nodo.texto()}: {hijo.texto()} es un número, no una matriz.")
        X = a[1]
        m, n = len(X), len(X[0])
        nombre = _nombre_operando(hijo)
        x = _letra(hijo, "x")
        R = [[X[i][j] for i in range(m)] for j in range(n)]
        entradas = [{"posicion": (i + 1, j + 1), "lineas": [
            f"Entrada ({i + 1},{j + 1}) = entrada ({j + 1},{i + 1}) de {nombre} = {x}{subindice(j + 1, i + 1)} = "
            f"{formatear_numero(R[i][j])}"]}
            for i in range(n) for j in range(m)]
        extra = [f"Fila {i + 1} de {nombre} = ({', '.join(formatear_numero(v) for v in X[i])})  →  columna {i + 1} "
                 f"de {nodo.texto()}" for i in range(m)]
        advertencias = []
        if hijo.tipo == "producto" and hijo.hijos[0].es_matricial() and hijo.hijos[1].es_matricial():
            p_izq, p_der = hijo.hijos
            advertencias.append(f"Propiedad: ({p_izq.texto()}{p_der.texto()})ᵀ = {p_der.texto()}ᵀ{p_izq.texto()}ᵀ; al "
                                f"transponer un producto se invierte el orden de los factores.")
            try:
                Xi = evaluar_independiente(p_izq, self.matrices, self.escalares)
                Yi = evaluar_independiente(p_der, self.matrices, self.escalares)
                if len(Xi) == len(Yi[0]):
                    sin_invertir = multiplicar_matrices(transponer_matriz(Xi), transponer_matriz(Yi))
                    if sin_invertir != R:
                        advertencias.append(f"Si se olvida invertir el orden, {_nombre_operando(p_izq)}ᵀ{_nombre_operando(p_der)}ᵀ "
                                            f"da {matriz_en_linea(sin_invertir)}, que es otra matriz.")
                else:
                    advertencias.append(f"Sin invertir el orden, {_nombre_operando(p_izq)}ᵀ{_nombre_operando(p_der)}ᵀ ni siquiera "
                                        f"está definido.")
            except ErrorExpresion:
                pass
        self._registrar(
            nodo, "transpuesta", operandos,
            f"La transpuesta siempre está definida: {nombre} es {m}×{n}, así que {nodo.texto()} es {n}×{m} ✓",
            True, f"(Xᵀ)ᵢⱼ = xⱼᵢ",
            f"La fila i de {nombre} se escribe como la columna i de {nodo.texto()}.",
            entradas, R, advertencias, extra)
        return ("matriz", R)

    def _negativo(self, nodo, a):
        """Calcula el negativo de un número o de una matriz (multiplicar por −1).

        Entrada: nodo y operando. Salida: ('matriz', −X) o ('numero', −a).
        """
        hijo = nodo.hijos[0]
        if a[0] == "numero":
            return self._aritmetica(nodo, [a], -a[1], "−")
        return self._escalar_por_matriz(nodo, Fraction(-1), a[1], [(hijo, a[1])], _nombre_operando(hijo),
                                        _letra(hijo, "x"), titulo=f"Calcular {nodo.texto()} (multiplicar por −1)")

    def _inversa(self, nodo, a):
        """Calcula la inversa por Gauss-Jordan si la matriz es cuadrada y det ≠ 0.

        Entrada: nodo y operando. Salida: ('matriz', inversa); si es singular registra el diagnóstico y se detiene.
        """
        operandos = [(nodo.hijos[0], a[1])]
        if a[0] != "matriz" or len(a[1]) != len(a[1][0]):
            self._fallar(nodo, "inversa", operandos, "Se requiere una matriz cuadrada.", "La inversa no está definida: el operando no es una matriz cuadrada.")
        det = calcular_determinante(a[1])
        if det["determinante"] == 0:
            paso = self._registrar(nodo, "inversa", operandos, "det(M)=0: matriz singular.", False,
                                   REGLAS_OPERACION["inversa"], "La matriz es singular; no tiene inversa.")
            paso["etapas"] = det["etapas"]
            raise _OperacionNoDefinida("La inversa no está definida porque det(M)=0.")
        calculo = calcular_inversa(a[1])
        paso = self._registrar(nodo, "inversa", operandos, f"Matriz cuadrada, det(M)={det['determinante']}≠0.", True,
                               REGLAS_OPERACION["inversa"], "Se aplican operaciones elementales a ambos bloques.", resultado=calculo["inversa"])
        paso["etapas"] = det["etapas"] + calculo["etapas"]
        return "matriz", calculo["inversa"]


def evaluar_independiente(nodo, matrices, escalares=None):
    """Recalcula la expresión desde los datos originales con algoritmos distintos a los del procedimiento.

    Entrada: árbol, matrices y escalares. Salida: matriz o número resultante; lanza ErrorExpresion.
    """
    escalares = escalares or {}
    tipo = nodo.tipo
    if tipo == "matriz":
        return [fila[:] for fila in matrices[nodo.valor]]
    if tipo == "identidad":
        return matriz_identidad(nodo.valor)
    if tipo == "numero":
        return nodo.valor
    if tipo == "escalar":
        return escalares[nodo.valor]
    valores = [evaluar_independiente(h, matrices, escalares) for h in nodo.hijos]
    es_matriz = [isinstance(v, list) for v in valores]
    if tipo == "inversa":
        return inversa_adjunta(valores[0])
    if tipo == "transpuesta":
        X = valores[0]
        if not es_matriz[0]:
            raise ErrorExpresion("La transpuesta se aplica a matrices.")
        return [[fila[j] for fila in X] for j in range(len(X[0]))]
    if tipo == "negativo":
        return [[-v for v in fila] for fila in valores[0]] if es_matriz[0] else -valores[0]
    X, Y = valores
    if tipo in ("suma", "resta"):
        if not any(es_matriz):
            return X + Y if tipo == "suma" else X - Y
        if not all(es_matriz) or (len(X), len(X[0])) != (len(Y), len(Y[0])):
            raise ErrorExpresion("Dimensiones incompatibles en una suma o resta.")
        signo = 1 if tipo == "suma" else -1
        return [[a + signo * b for a, b in zip(fila_x, fila_y)] for fila_x, fila_y in zip(X, Y)]
    if not any(es_matriz):
        return X * Y
    if not es_matriz[0]:
        return [[X * v for v in fila] for fila in Y]
    if not es_matriz[1]:
        return [[Y * v for v in fila] for fila in X]
    m, n, p, q = len(X), len(X[0]), len(Y), len(Y[0])
    if n != p:
        raise ErrorExpresion("Dimensiones incompatibles en un producto.")
    R = [[Fraction(0)] * q for _ in range(m)]
    for k in range(n):
        for i in range(m):
            for j in range(q):
                R[i][j] += X[i][k] * Y[k][j]
    return R


def _nodo(tipo, *hijos, parentesis=False):
    """Crea un NodoExpresion a partir del tipo y sus hijos.

    Entrada: tipo, hijos y parentesis (bool). Salida: el nodo.
    """
    return NodoExpresion(tipo, hijos, parentesis=parentesis)


def identidad_para_verificar(nodo):
    """Reconoce si la expresión tiene la forma de una propiedad conocida para comprobarla por otra ruta.

    Entrada: árbol de la expresión. Salida: (nombre, enunciado, expresión equivalente) o None.
    """
    tipo = nodo.tipo
    hijos = nodo.hijos
    def transpuesta_desarrollada(n):
        """Aplica (XY)ᵀ = YᵀXᵀ de forma recursiva a un producto.

        Entrada: nodo. Salida: nodo desarrollado.
        """
        if n.tipo == "producto" and all(h.es_matricial() for h in n.hijos):
            x, y = n.hijos
            return _nodo("producto", transpuesta_desarrollada(y), transpuesta_desarrollada(x))
        return _nodo("transpuesta", n)
    def inversa_desarrollada(n):
        """Aplica (XY)⁻¹ = Y⁻¹X⁻¹ de forma recursiva a un producto.

        Entrada: nodo. Salida: nodo desarrollado.
        """
        if n.tipo == "producto" and all(h.es_matricial() for h in n.hijos):
            x, y = n.hijos
            return _nodo("producto", inversa_desarrollada(y), inversa_desarrollada(x))
        return _nodo("inversa", n)
    if tipo == "inversa":
        hijo = hijos[0]
        if hijo.tipo == "producto" and all(h.es_matricial() for h in hijo.hijos):
            x, y = hijo.hijos
            return ("Inversa de un producto", "(AB)⁻¹ = B⁻¹A⁻¹ (factores cuadrados invertibles)",
                    _nodo("producto", inversa_desarrollada(y), inversa_desarrollada(x)))
        if hijo.tipo == "inversa":
            return ("Doble inversa", "(A⁻¹)⁻¹ = A", hijo.hijos[0])
        if hijo.tipo == "transpuesta":
            return ("Inversa de la transpuesta", "(Aᵀ)⁻¹ = (A⁻¹)ᵀ", _nodo("transpuesta", _nodo("inversa", hijo.hijos[0])))
    if tipo == "producto":
        izquierda, derecha = hijos
        for inversa, otro, enunciado in ((izquierda, derecha, "A⁻¹A = I"), (derecha, izquierda, "AA⁻¹ = I")):
            if inversa.tipo == "inversa" and otro.es_matricial() and inversa.hijos[0].texto() == otro.texto():
                # I debe tener el orden de A, que solo se conoce al evaluar la expresión.
                return ("Producto por la inversa", enunciado, NodoExpresion("identidad", valor=None))
        for compuesto, otro, primero in ((izquierda, derecha, True), (derecha, izquierda, False)):
            if compuesto.tipo == "producto" and otro.es_matricial():
                a, b = compuesto.hijos
                if a.es_matricial() != b.es_matricial():
                    escalar, matriz = (b, a) if a.es_matricial() else (a, b)
                    producto = _nodo("producto", matriz, otro) if primero else _nodo("producto", otro, matriz)
                    return ("Escalar en un producto", "(rA)B = A(rB) = r(AB)", _nodo("producto", escalar, producto))
        if derecha.tipo in ("suma", "resta") and izquierda.es_matricial() and derecha.es_matricial():
            y, z = derecha.hijos
            return ("Distributividad por la izquierda", "A(B ± C) = AB ± AC",
                    _nodo(derecha.tipo, _nodo("producto", izquierda, y), _nodo("producto", izquierda, z)))
        if derecha.tipo in ("suma", "resta") and not izquierda.es_matricial() and derecha.es_matricial():
            y, z = derecha.hijos
            return ("Distributividad del escalar", "r(A ± B) = rA ± rB",
                    _nodo(derecha.tipo, _nodo("producto", izquierda, y), _nodo("producto", izquierda, z)))
        if izquierda.tipo in ("suma", "resta") and izquierda.es_matricial() and derecha.es_matricial():
            x, y = izquierda.hijos
            return ("Distributividad por la derecha", "(A ± B)C = AC ± BC",
                    _nodo(izquierda.tipo, _nodo("producto", x, derecha), _nodo("producto", y, derecha)))
        if izquierda.tipo in ("suma", "resta") and not izquierda.es_matricial() and derecha.es_matricial():
            x, y = izquierda.hijos
            return ("Distributividad respecto de la suma de escalares", "(r ± s)A = rA ± sA",
                    _nodo(izquierda.tipo, _nodo("producto", x, derecha), _nodo("producto", y, derecha)))
        if (izquierda.tipo == "transpuesta" and derecha.tipo == "transpuesta"
                and izquierda.es_matricial() and derecha.es_matricial()):
            return ("Transpuesta de un producto", "BᵀAᵀ = (AB)ᵀ",
                    _nodo("transpuesta", _nodo("producto", derecha.hijos[0], izquierda.hijos[0])))
        if izquierda.tipo == "inversa" and derecha.tipo == "inversa":
            return ("Inversa de un producto", "B⁻¹A⁻¹ = (AB)⁻¹", _nodo("inversa", _nodo("producto", derecha.hijos[0], izquierda.hijos[0])))
        if izquierda.tipo == "producto" and all(h.es_matricial() for h in (*izquierda.hijos, derecha)):
            x, y = izquierda.hijos
            return ("Asociatividad del producto", "(AB)C = A(BC)",
                    _nodo("producto", x, _nodo("producto", y, derecha, parentesis=True)))
        if derecha.tipo == "producto" and all(h.es_matricial() for h in (izquierda, *derecha.hijos)):
            y, z = derecha.hijos
            return ("Asociatividad del producto", "A(BC) = (AB)C",
                    _nodo("producto", _nodo("producto", izquierda, y, parentesis=True), z))
    if tipo == "transpuesta":
        hijo = hijos[0]
        if hijo.tipo == "producto" and hijo.hijos[0].es_matricial() and hijo.hijos[1].es_matricial():
            x, y = hijo.hijos
            return ("Transpuesta de un producto", "(AB)ᵀ = BᵀAᵀ",
                    _nodo("producto", transpuesta_desarrollada(y), transpuesta_desarrollada(x)))
        if hijo.tipo == "producto":
            x, y = hijo.hijos
            escalar, matriz = (x, y) if not x.es_matricial() else (y, x)
            return ("Transpuesta de un múltiplo escalar", "(rA)ᵀ = rAᵀ",
                    _nodo("producto", escalar, _nodo("transpuesta", matriz)))
        if hijo.tipo in ("suma", "resta"):
            x, y = hijo.hijos
            return ("Transpuesta de una suma", "(A ± B)ᵀ = Aᵀ ± Bᵀ",
                    _nodo(hijo.tipo, _nodo("transpuesta", x), _nodo("transpuesta", y)))
        if hijo.tipo == "transpuesta":
            return ("Doble transpuesta", "(Aᵀ)ᵀ = A", hijo.hijos[0])
    if tipo in ("suma", "resta") and nodo.es_matricial():
        izquierda, derecha = hijos
        if izquierda.tipo == "producto" and derecha.tipo == "producto":
            (a, b), (c, d) = izquierda.hijos, derecha.hijos
            if a.texto() == c.texto():
                return ("Distributividad (factor común a la izquierda)", "AB ± AC = A(B ± C)",
                        _nodo("producto", a, _nodo(tipo, b, d)))
            if b.texto() == d.texto():
                return ("Distributividad (factor común a la derecha)", "AC ± BC = (A ± B)C",
                        _nodo("producto", _nodo(tipo, a, c), b))
        if izquierda.tipo == "transpuesta" and derecha.tipo == "transpuesta":
            return ("Transpuesta de una suma", "Aᵀ ± Bᵀ = (A ± B)ᵀ",
                    _nodo("transpuesta", _nodo(tipo, izquierda.hijos[0], derecha.hijos[0])))
        if izquierda.tipo in ("suma", "resta"):
            x, y = izquierda.hijos
            # (X ± Y) ± Z = X ± (Y ∓ Z) cuando corresponde: se reagrupa la suma
            if izquierda.tipo == "suma":
                return ("Asociatividad de la suma", "(A + B) ± C = A + (B ± C)",
                        _nodo("suma", x, _nodo(tipo, y, derecha)))
            return ("Asociatividad de la suma", "(A − B) ± C = A − (B ∓ C)",
                    _nodo("resta", x, _nodo("resta" if tipo == "suma" else "suma", y, derecha)))
        if tipo == "suma":
            return ("Conmutatividad de la suma", "A + B = B + A", _nodo("suma", derecha, izquierda))
        return ("Definición de la resta", "A − B = A + (−1)B",
                _nodo("suma", izquierda, _nodo("producto", NodoExpresion("numero", valor=Fraction(-1)), derecha)))
    return None


def _preparar_datos(nodo, matrices, escalares):
    """Valida las matrices y escalares que usa la expresión.

    Entrada: árbol, matrices y escalares. Salida: (matrices válidas, escalares válidos); lanza ErrorExpresion si falta alguno.
    """
    matrices_validas = {}
    for nombre in sorted(nodo.nombres_matrices()):
        if nombre not in matrices:
            raise ErrorExpresion(f"La matriz {nombre} no está definida." + (
                " Para la transpuesta escribe Aᵀ, A^T o A'." if nombre == "T" else
                " Para la identidad escribe I2, I3, …" if nombre == "I" else ""),
                _buscar_posicion(nodo, "matriz", nombre))
        matrices_validas[nombre] = validar_matriz(matrices[nombre], nombre)
    escalares_validos = {}
    for nombre in sorted(nodo.nombres_escalares()):
        if nombre not in (escalares or {}):
            raise ErrorExpresion(f"Falta el valor del escalar {nombre}.", _buscar_posicion(nodo, "escalar", nombre))
        escalares_validos[nombre] = Fraction(escalares[nombre])
    return matrices_validas, escalares_validos


def resolver_expresion_matricial(expresion, matrices, escalares=None):
    """Resuelve una expresión como 'A(B + C)' paso a paso respetando paréntesis y precedencia.

    Entrada: texto o árbol, matrices y escalares.
    Salida: diccionario con árbol, condiciones, pasos, resultado o error y la identidad para verificar.
    """
    nodo = expresion if isinstance(expresion, NodoExpresion) else analizar_expresion_matricial(expresion)
    matrices_validas, escalares_validos = _preparar_datos(nodo, matrices, escalares)
    dimensiones = {nombre: (len(M), len(M[0])) for nombre, M in matrices_validas.items()}
    condiciones, dimension_final = revisar_dimensiones(nodo, dimensiones, escalares_validos)

    resolutor = _ResolutorMatricial(matrices_validas, escalares_validos)
    error = None
    tipo_resultado, resultado = None, None
    try:
        tipo_resultado, resultado = resolutor.valor(nodo)
    except _OperacionNoDefinida as falla:
        error = str(falla)

    operaciones = resolutor.pasos
    for k, paso in enumerate(operaciones):
        if paso["condicion"]["cumple"]:
            paso["siguiente"] = (operaciones[k + 1]["titulo"] if k + 1 < len(operaciones)
                                 else "Ninguna: este es el resultado final.")
        else:
            paso["siguiente"] = "El cálculo se detiene: esta operación no está definida."

    identidad = None if error else identidad_para_verificar(nodo)
    texto = nodo.texto()
    if identidad:
        nombre, _, alternativa = identidad
        if alternativa.tipo == "identidad" and alternativa.valor is None:
            alternativa = NodoExpresion("identidad", valor=len(resultado))
        identidad = (nombre, f"{texto} = {alternativa.texto()}", alternativa)
    datos = {
        "tipo": "datos",
        "titulo": "Datos del ejercicio",
        "expresion": texto,
        "interpretacion": nodo.texto_completo(),
        "matrices": [(nombre, M) for nombre, M in matrices_validas.items()],
        "escalares": escalares_validos,
        "condiciones": condiciones,
        "primera": operaciones[0]["titulo"] if operaciones else "No hay operaciones: la expresión es un solo dato.",
        "propiedad": identidad[:2] if identidad else None,
    }
    pasos = [datos] + operaciones
    if error is None:
        definiciones = []
        for paso in operaciones:
            regla = REGLAS_OPERACION[paso["tipo"]]
            if regla not in definiciones:
                definiciones.append(regla)
        dimension = (len(resultado), len(resultado[0])) if tipo_resultado == "matriz" else None
        conclusion = (
            f"{texto} está definida para estas matrices. Se calculó con {_plural(len(operaciones), 'operación', 'operaciones')} "
            f"en el orden que indican los paréntesis y la precedencia"
            + (f", y el resultado es una matriz {formatear_dimension(dimension)}." if dimension else
               f", y el resultado es el número {formatear_numero(resultado)}.")
        )
        pasos.append({
            "tipo": "respuesta",
            "titulo": "Respuesta final",
            "expresion": texto,
            "resultado": resultado,
            "dimension": dimension,
            "orden": [paso["expresion"] for paso in operaciones],
            "definiciones": definiciones,
            "propiedad": identidad[:2] if identidad else None,
            "conclusion": conclusion,
        })
    for numero, paso in enumerate(pasos, start=1):
        paso["numero"] = numero

    return {
        "expresion": texto,
        "interpretacion": nodo.texto_completo(),
        "nodo": nodo,
        "matrices": matrices_validas,
        "escalares": escalares_validos,
        "condiciones": condiciones,
        "dimension_esperada": dimension_final,
        "pasos": pasos,
        "operaciones": operaciones,
        "resultado": resultado,
        "tipo_resultado": tipo_resultado,
        "dimension": (len(resultado), len(resultado[0])) if tipo_resultado == "matriz" else None,
        "error": error,
        "identidad": identidad,
    }


def _comparar_valores(obtenido, esperado):
    """Compara dos matrices (o dos números) entrada por entrada.

    Entrada: valor obtenido y valor esperado. Salida: diccionario de comparación con «coinciden».
    """
    if isinstance(obtenido, list) and isinstance(esperado, list):
        return comparar_matrices(obtenido, esperado, "Obtenido", "Esperado")
    if not isinstance(obtenido, list) and not isinstance(esperado, list):
        coinciden = Fraction(obtenido) == Fraction(esperado)
        return {"izquierda": obtenido, "derecha": esperado, "dimensiones_izquierda": None,
                "dimensiones_derecha": None, "coinciden": coinciden,
                "diferencias": [] if coinciden else [("valor", obtenido, esperado)],
                "conclusion": "Los números coinciden." if coinciden else "Los números son distintos."}
    return {"izquierda": obtenido, "derecha": esperado, "dimensiones_izquierda": None, "dimensiones_derecha": None,
            "coinciden": False, "diferencias": [("tipo", obtenido, esperado)],
            "conclusion": "Uno es un número y el otro una matriz."}


def _verificar_operacion(paso):
    """Recalcula una operación intermedia desde sus operandos con un método independiente.

    Entrada: paso del procedimiento. Salida: diccionario con método, dimensiones, entradas que coinciden y «ok».
    """
    tipo = paso["tipo"]
    valores = [v for _, v in paso["operandos"]]
    obtenido = paso["resultado"]
    calculos, etapas = [], []
    if tipo == "aritmetica":
        a = valores[0]
        b = valores[1] if len(valores) > 1 else None
        esperado = {"+": lambda: a + b, "−": lambda: a - b, "·": lambda: a * b,
                    "negativo": lambda: -a}[paso["simbolo"]]()
        metodo = "Se repite la operación con los números."
    elif tipo in ("suma", "resta"):
        X, Y = valores
        signo = 1 if tipo == "suma" else -1
        esperado = [[X[i][j] + signo * Y[i][j] for j in range(len(X[0]))] for i in range(len(X))]
        metodo = f"Se vuelve a {'sumar' if tipo == 'suma' else 'restar'} cada par de entradas de la misma posición."
    elif tipo == "escalar":
        escalar = paso["escalar"]
        X = next(v for v in valores if isinstance(v, list))
        esperado = [[escalar * v for v in fila] for fila in X]
        metodo = f"Se comprueba (rX)ᵢⱼ = r·xᵢⱼ en cada entrada, con r = {formatear_numero(escalar)}."
    elif tipo == "inversa":
        calculo = calcular_inversa(valores[0], "adjunta")
        esperado, etapas = calculo["inversa"], calculo["etapas"]
        metodo = "Se recalcula desde el operando mediante adjunta y determinante, sin usar la reducción Gauss-Jordan."
    elif tipo == "transpuesta":
        X = valores[0]
        esperado = [[X[i][j] for i in range(len(X))] for j in range(len(X[0]))]
        metodo = "Se comprueba (Xᵀ)ᵢⱼ = xⱼᵢ en cada entrada."
    else:
        X, Y = valores
        esperado = [[Fraction(0)] * len(Y[0]) for _ in X]
        for k in range(len(Y)):
            for i in range(len(X)):
                for j in range(len(Y[0])):
                    esperado[i][j] += X[i][k] * Y[k][j]
                    calculos.append(f"k={k+1}, ({i+1},{j+1}): subtotal + ({X[i][k]})·({Y[k][j]}) = {esperado[i][j]}")
        metodo = ("Se recalcula como suma de productos columna·fila (Σₖ columnaₖ(X)·filaₖ(Y)), un método "
                  "distinto del de fila por columna.")
    comparacion = _comparar_valores(obtenido, esperado)
    dimension_esperada = (len(esperado), len(esperado[0])) if isinstance(esperado, list) else None
    dimension_obtenida = (len(obtenido), len(obtenido[0])) if isinstance(obtenido, list) else None
    total = len(esperado) * len(esperado[0]) if isinstance(esperado, list) else 1
    diferencias = [d for d in comparacion["diferencias"] if isinstance(d[0], int)]
    return {
        "numero": paso.get("numero"),
        "expresion": paso["expresion"],
        "metodo": metodo,
        "dimension_esperada": dimension_esperada,
        "dimension_obtenida": dimension_obtenida,
        "dimensiones_ok": dimension_esperada == dimension_obtenida,
        "entradas_total": total,
        "entradas_ok": total - len(diferencias) if dimension_esperada == dimension_obtenida else 0,
        "diferencias": comparacion["diferencias"],
        "ok": comparacion["coinciden"],
        "obtenido": copiar_matriz(obtenido) if isinstance(obtenido, list) else obtenido,
        "esperado": esperado,
        "comparacion": comparacion,
        "calculos": calculos,
        "etapas": etapas,
    }


ALCANCE_VERIFICACION = ("Esta es una comprobación numérica de este ejercicio concreto; no es una demostración "
                        "general de ninguna propiedad.")


def verificar_resolucion(resolucion, usar_identidades=True):
    """Verifica una resolución: cada operación, el recálculo completo y, si existe, la ruta por propiedad.

    Entrada: resolución y usar_identidades (bool). Salida: diccionario con las tres comprobaciones y «correcto».
    """
    if resolucion["error"]:
        return {"aplicable": False, "motivo": resolucion["error"], "pasos": [], "global": None,
                "identidad": None, "correcto": False, "alcance": ALCANCE_VERIFICACION}
    pasos = [_verificar_operacion(p) for p in resolucion["operaciones"]]

    independiente = evaluar_independiente(resolucion["nodo"], resolucion["matrices"], resolucion["escalares"])
    comparacion = _comparar_valores(resolucion["resultado"], independiente)
    global_ = {
        "metodo": ("Se recalcula toda la expresión desde las matrices originales, sin usar los resultados "
                   "intermedios del procedimiento; los productos se acumulan como suma de productos columna·fila y las inversas se obtienen por adjunta y determinante."),
        "esperado": independiente,
        "comparacion": comparacion,
        "ok": comparacion["coinciden"],
    }

    identidad = None
    if usar_identidades and resolucion["identidad"]:
        nombre, enunciado, alternativa = resolucion["identidad"]
        try:
            ruta = resolver_expresion_matricial(alternativa, resolucion["matrices"], resolucion["escalares"])
        except ErrorExpresion as error:
            ruta = None
            identidad = {"nombre": nombre, "enunciado": enunciado, "expresion": alternativa.texto(),
                         "definida": False, "motivo": str(error), "ok": None}
        if ruta is not None:
            if ruta["error"]:
                identidad = {"nombre": nombre, "enunciado": enunciado, "expresion": ruta["expresion"],
                             "definida": False, "motivo": ruta["error"], "ok": None, "resolucion": ruta}
            else:
                comparacion_ruta = _comparar_valores(resolucion["resultado"], ruta["resultado"])
                identidad = {"nombre": nombre, "enunciado": enunciado, "expresion": ruta["expresion"],
                             "definida": True, "resolucion": ruta, "comparacion": comparacion_ruta,
                             "ok": comparacion_ruta["coinciden"]}

    correcto = all(p["ok"] for p in pasos) and global_["ok"] and (identidad is None or identidad["ok"] is not False)
    return {"aplicable": True, "pasos": pasos, "global": global_, "identidad": identidad,
            "correcto": correcto, "alcance": ALCANCE_VERIFICACION}


def describir_diferencias(diferencias):
    """Convierte las diferencias de comparar_matrices en frases legibles.

    Entrada: lista de diferencias. Salida: lista de cadenas.
    """
    lineas = []
    for diferencia in diferencias:
        if diferencia[0] == "dimensiones":
            lineas.append(f"Dimensiones distintas: {formatear_dimension(diferencia[1])} y "
                          f"{formatear_dimension(diferencia[2])}.")
        elif diferencia[0] in ("valor", "tipo"):
            lineas.append("Los valores comparados no coinciden.")
        else:
            i, j, a, b = diferencia
            lineas.append(f"Entrada ({i},{j}): se obtuvo {formatear_numero(a)} y debía ser {formatear_numero(b)}.")
    return lineas



PROPIEDADES_MATRICIALES = [
    {"clave": "conmutatividad_suma", "grupo": "Suma", "nombre": "Conmutatividad de la suma",
     "izquierda": "A + B", "derecha": "B + A", "general": True,
     "condiciones": "A y B del mismo tamaño m×n.",
     "demostracion": "(A + B)ᵢⱼ = aᵢⱼ + bᵢⱼ = bᵢⱼ + aᵢⱼ = (B + A)ᵢⱼ para toda posición (i, j), porque la suma de "
                     "números reales es conmutativa."},
    {"clave": "asociatividad_suma", "grupo": "Suma", "nombre": "Asociatividad de la suma",
     "izquierda": "(A + B) + C", "derecha": "A + (B + C)", "general": True,
     "condiciones": "A, B y C del mismo tamaño m×n.",
     "demostracion": "((A + B) + C)ᵢⱼ = (aᵢⱼ + bᵢⱼ) + cᵢⱼ = aᵢⱼ + (bᵢⱼ + cᵢⱼ) = (A + (B + C))ᵢⱼ."},
    {"clave": "matriz_cero", "grupo": "Suma", "nombre": "Matriz cero (neutro de la suma)",
     "izquierda": "A + O", "derecha": "A", "general": True, "extra": "cero",
     "condiciones": "O es la matriz cero del mismo tamaño que A.",
     "demostracion": "(A + O)ᵢⱼ = aᵢⱼ + 0 = aᵢⱼ."},
    {"clave": "inverso_aditivo", "grupo": "Suma", "nombre": "Inverso aditivo",
     "izquierda": "A + (−A)", "derecha": "O", "general": True, "extra": "cero",
     "condiciones": "O es la matriz cero del mismo tamaño que A.",
     "demostracion": "(A + (−A))ᵢⱼ = aᵢⱼ + (−aᵢⱼ) = 0."},
    {"clave": "escalar_suma_matrices", "grupo": "Escalares", "nombre": "Escalar por una suma de matrices",
     "izquierda": "r(A + B)", "derecha": "rA + rB", "general": True,
     "condiciones": "A y B del mismo tamaño; r es cualquier número real.",
     "demostracion": "(r(A + B))ᵢⱼ = r(aᵢⱼ + bᵢⱼ) = raᵢⱼ + rbᵢⱼ = (rA + rB)ᵢⱼ."},
    {"clave": "suma_escalares", "grupo": "Escalares", "nombre": "Suma de escalares por una matriz",
     "izquierda": "(r + s)A", "derecha": "rA + sA", "general": True,
     "condiciones": "A de cualquier tamaño; r y s números reales.",
     "demostracion": "((r + s)A)ᵢⱼ = (r + s)aᵢⱼ = raᵢⱼ + saᵢⱼ = (rA + sA)ᵢⱼ."},
    {"clave": "producto_escalares", "grupo": "Escalares", "nombre": "Producto de escalares",
     "izquierda": "r(sA)", "derecha": "(rs)A", "general": True,
     "condiciones": "A de cualquier tamaño; r y s números reales.",
     "demostracion": "(r(sA))ᵢⱼ = r(saᵢⱼ) = (rs)aᵢⱼ = ((rs)A)ᵢⱼ."},
    {"clave": "asociatividad_producto", "grupo": "Producto", "nombre": "Asociatividad del producto",
     "izquierda": "(AB)C", "derecha": "A(BC)", "general": True,
     "condiciones": "A es m×n, B es n×p y C es p×q.",
     "demostracion": "((AB)C)ᵢⱼ = Σₗ (Σₖ aᵢₖbₖₗ) cₗⱼ = Σₖ aᵢₖ (Σₗ bₖₗcₗⱼ) = (A(BC))ᵢⱼ: solo se reordena una "
                     "suma finita."},
    {"clave": "distributiva_izquierda", "grupo": "Producto", "nombre": "Distributividad por la izquierda",
     "izquierda": "A(B + C)", "derecha": "AB + AC", "general": True,
     "condiciones": "A es m×n; B y C son n×p.",
     "demostracion": "(A(B + C))ᵢⱼ = Σₖ aᵢₖ(bₖⱼ + cₖⱼ) = Σₖ aᵢₖbₖⱼ + Σₖ aᵢₖcₖⱼ = (AB + AC)ᵢⱼ."},
    {"clave": "distributiva_derecha", "grupo": "Producto", "nombre": "Distributividad por la derecha",
     "izquierda": "(A + B)C", "derecha": "AC + BC", "general": True,
     "condiciones": "A y B son m×n; C es n×p.",
     "demostracion": "((A + B)C)ᵢⱼ = Σₖ (aᵢₖ + bᵢₖ)cₖⱼ = Σₖ aᵢₖcₖⱼ + Σₖ bᵢₖcₖⱼ = (AC + BC)ᵢⱼ."},
    {"clave": "identidad_derecha", "grupo": "Producto", "nombre": "Identidad a la derecha",
     "izquierda": "AI", "derecha": "A", "general": True, "extra": "identidad_columnas",
     "condiciones": "Si A es m×n, I es la identidad n×n.",
     "demostracion": "(AI)ᵢⱼ = Σₖ aᵢₖδₖⱼ = aᵢⱼ, porque δₖⱼ vale 1 si k = j y 0 en otro caso."},
    {"clave": "identidad_izquierda", "grupo": "Producto", "nombre": "Identidad a la izquierda",
     "izquierda": "IA", "derecha": "A", "general": True, "extra": "identidad_filas",
     "condiciones": "Si A es m×n, I es la identidad m×m.",
     "demostracion": "(IA)ᵢⱼ = Σₖ δᵢₖaₖⱼ = aᵢⱼ."},
    {"clave": "transpuesta_doble", "grupo": "Transpuesta", "nombre": "Transpuesta de la transpuesta",
     "izquierda": "(Aᵀ)ᵀ", "derecha": "A", "general": True,
     "condiciones": "A de cualquier tamaño.",
     "demostracion": "((Aᵀ)ᵀ)ᵢⱼ = (Aᵀ)ⱼᵢ = aᵢⱼ."},
    {"clave": "transpuesta_suma", "grupo": "Transpuesta", "nombre": "Transpuesta de una suma",
     "izquierda": "(A + B)ᵀ", "derecha": "Aᵀ + Bᵀ", "general": True,
     "condiciones": "A y B del mismo tamaño.",
     "demostracion": "((A + B)ᵀ)ᵢⱼ = (A + B)ⱼᵢ = aⱼᵢ + bⱼᵢ = (Aᵀ)ᵢⱼ + (Bᵀ)ᵢⱼ."},
    {"clave": "transpuesta_escalar", "grupo": "Transpuesta", "nombre": "Transpuesta de un múltiplo escalar",
     "izquierda": "(rA)ᵀ", "derecha": "rAᵀ", "general": True,
     "condiciones": "A de cualquier tamaño; r número real.",
     "demostracion": "((rA)ᵀ)ᵢⱼ = (rA)ⱼᵢ = r·aⱼᵢ = r(Aᵀ)ᵢⱼ."},
    {"clave": "transpuesta_producto", "grupo": "Transpuesta", "nombre": "Transpuesta de un producto",
     "izquierda": "(AB)ᵀ", "derecha": "BᵀAᵀ", "general": True, "error_comun": "AᵀBᵀ",
     "condiciones": "A es m×n y B es n×p; entonces (AB)ᵀ y BᵀAᵀ son p×m.",
     "demostracion": "((AB)ᵀ)ᵢⱼ = (AB)ⱼᵢ = Σₖ aⱼₖbₖᵢ = Σₖ (Bᵀ)ᵢₖ(Aᵀ)ₖⱼ = (BᵀAᵀ)ᵢⱼ. El orden de los factores se "
                     "invierte; AᵀBᵀ en general es otra matriz o ni siquiera está definida."},
    {"clave": "no_conmutatividad", "grupo": "Advertencias", "nombre": "El producto no es conmutativo",
     "izquierda": "AB", "derecha": "BA", "general": False, "contraejemplo": "no_conmutatividad",
     "condiciones": "Para que AB y BA estén definidos y se puedan comparar, A y B deben ser cuadradas del mismo tamaño.",
     "advertencia": "AB = BA no es una propiedad: falla para la mayoría de las matrices. Que se cumpla en un ejemplo "
                    "no la convierte en verdadera en general."},
    {"clave": "cancelacion", "grupo": "Advertencias", "nombre": "La cancelación no siempre vale",
     "tipo": "cancelacion", "general": False, "contraejemplo": "cancelacion",
     "condiciones": "A es m×n; B y C son n×p, de modo que AB y AC estén definidos.",
     "advertencia": "De AB = AC no se puede concluir B = C, salvo hipótesis adicionales (por ejemplo, A invertible)."},
    {"clave": "divisores_cero", "grupo": "Advertencias", "nombre": "Matrices no nulas con producto cero",
     "tipo": "divisores_cero", "general": False, "contraejemplo": "divisores_cero",
     "condiciones": "A es m×n y B es n×p, de modo que AB esté definido.",
     "advertencia": "AB = O no implica que A = O o B = O: existen matrices no nulas cuyo producto es la matriz cero."},
]

PROPIEDADES_MATRICIALES.extend([
    {"clave": "transpuesta_resta", "grupo": "Transpuesta", "nombre": "Transpuesta de una resta",
     "izquierda": "(A-B)ᵀ", "derecha": "Aᵀ-Bᵀ", "general": True,
     "condiciones": "A y B tienen las mismas dimensiones.",
     "demostracion": "((A-B)ᵀ)ij = aji-bji = (Aᵀ-Bᵀ)ij."},
    {"clave": "escalar_producto_izquierda", "grupo": "Escalares", "nombre": "Escalar en el primer factor",
     "izquierda": "(rA)B", "derecha": "r(AB)", "general": True,
     "condiciones": "A: m×n; B: n×p; r escalar.",
     "demostracion": "Σ (r aik)bkj = r Σ aik bkj."},
    {"clave": "escalar_producto_derecha", "grupo": "Escalares", "nombre": "Escalar en el segundo factor",
     "izquierda": "A(rB)", "derecha": "r(AB)", "general": True,
     "condiciones": "A: m×n; B: n×p; r escalar.",
     "demostracion": "Σ aik(r bkj) = r Σ aik bkj."},
])

PROPIEDADES_POR_CLAVE = {p["clave"]: p for p in PROPIEDADES_MATRICIALES}


def _matrices_extra(propiedad, A):
    """Construye las matrices auxiliares de una propiedad (O o I) con el tamaño compatible con A.

    Entrada: propiedad y matriz A. Salida: diccionario nombre → matriz (vacío si no hacen falta).
    """
    m, n = len(A), len(A[0])
    extra = propiedad.get("extra")
    if extra == "cero":
        return {"O": matriz_cero(m, n)}
    if extra == "identidad_columnas":
        return {"I": matriz_identidad(n)}
    if extra == "identidad_filas":
        return {"I": matriz_identidad(m)}
    return {}


def _es_cero(matriz):
    """Indica si todas las entradas de la matriz son cero.

    Entrada: matriz. Salida: True o False.
    """
    return all(v == 0 for fila in matriz for v in fila)


def verificar_propiedad_matricial(clave, matrices, escalares=None):
    """Comprueba una propiedad calculando cada lado por separado y comparándolos entrada por entrada.

    Entrada: clave, matrices y escalares.
    Salida: informe con lados, comparaciones, «cumple» y conclusión (caso particular, no demostración).
    """
    if clave in PROPIEDADES_AVANZADAS:
        return verificar_propiedad_avanzada(clave, matrices, escalares)
    propiedad = PROPIEDADES_POR_CLAVE[clave]
    datos = {nombre: validar_matriz(M, nombre) for nombre, M in matrices.items()}
    if "A" in datos:
        datos.update(_matrices_extra(propiedad, datos["A"]))
    escalares = {k: Fraction(v) for k, v in (escalares or {}).items()}
    tipo = propiedad.get("tipo", "igualdad")
    informe = {"propiedad": propiedad, "tipo": tipo, "lados": [], "comparaciones": [], "conclusion": "",
               "cumple": None, "matrices_extra": {k: v for k, v in datos.items() if k in ("O", "I")}}

    def lado(etiqueta, expresion):
        """Resuelve un miembro de la propiedad desde los datos originales y lo agrega al informe.

        Entrada: etiqueta y expresión. Salida: la resolución.
        """
        resolucion = resolver_expresion_matricial(expresion, datos, escalares)
        informe["lados"].append({"etiqueta": etiqueta, "resolucion": resolucion})
        return resolucion

    if tipo == "igualdad":
        izquierda = lado("Lado izquierdo", propiedad["izquierda"])
        derecha = lado("Lado derecho", propiedad["derecha"])
        if izquierda["error"] or derecha["error"]:
            motivo = izquierda["error"] or derecha["error"]
            informe["conclusion"] = (f"No se puede comprobar con estas matrices: {motivo} "
                                     f"Condiciones de la propiedad: {propiedad['condiciones']}")
            return informe
        comparacion = _comparar_valores(izquierda["resultado"], derecha["resultado"])
        informe["comparaciones"].append({"titulo": f"{izquierda['expresion']}  frente a  {derecha['expresion']}",
                                         "comparacion": comparacion})
        informe["cumple"] = comparacion["coinciden"]
        if propiedad["general"]:
            informe["conclusion"] = (
                f"Con estas matrices, {izquierda['expresion']} y {derecha['expresion']} coinciden en tamaño y en todas "
                f"sus entradas. Esto comprueba la propiedad en este caso particular; que valga para todas las "
                f"matrices lo garantiza la demostración general." if comparacion["coinciden"] else
                f"Los dos lados no coinciden con estas matrices. La comprobación detecta una inconsistencia entre "
                f"los cálculos y el teorema; revisa el desarrollo de ambos lados.")
        elif comparacion["coinciden"]:
            informe["conclusion"] = (f"En este caso {izquierda['expresion']} = {derecha['expresion']}, pero eso no la "
                                     f"convierte en propiedad: con otras matrices falla (carga el contraejemplo).")
        else:
            informe["conclusion"] = (f"{izquierda['expresion']} ≠ {derecha['expresion']} con estas matrices: este ejemplo es "
                                     f"un contraejemplo y muestra que la igualdad no vale en general.")
        if propiedad.get("error_comun"):
            try:
                comun = lado("Error frecuente", propiedad["error_comun"])
                if not comun["error"]:
                    informe["comparaciones"].append({
                        "titulo": f"{comun['expresion']}  frente a  {izquierda['expresion']}",
                        "comparacion": _comparar_valores(comun["resultado"], izquierda["resultado"])})
            except ErrorExpresion:
                pass
        informe["conclusion"] += " Se cumple para las matrices ingresadas." if informe["cumple"] else " No se cumple para las matrices ingresadas."
        return informe

    if tipo == "cancelacion":
        AB, AC = lado("Producto AB", "AB"), lado("Producto AC", "AC")
        if AB["error"] or AC["error"]:
            informe["conclusion"] = f"No se puede estudiar la cancelación: {AB['error'] or AC['error']}"
            return informe
        productos = _comparar_valores(AB["resultado"], AC["resultado"])
        factores = _comparar_valores(datos["B"], datos["C"])
        informe["comparaciones"] += [{"titulo": "AB  frente a  AC", "comparacion": productos},
                                     {"titulo": "B  frente a  C", "comparacion": factores}]
        if productos["coinciden"] and not factores["coinciden"]:
            informe["cumple"] = False
            informe["conclusion"] = ("AB = AC pero B ≠ C: es un contraejemplo. No se puede «cancelar» A; haría falta, "
                                     "por ejemplo, que A fuera invertible.")
        elif productos["coinciden"]:
            informe["conclusion"] = ("Aquí AB = AC y también B = C, así que este caso no contradice nada; aun así la "
                                     "cancelación no vale en general (carga el contraejemplo).")
        else:
            informe["conclusion"] = ("AB ≠ AC, así que estas matrices no sirven para estudiar la cancelación. Carga el "
                                     "contraejemplo para ver un caso con AB = AC y B ≠ C.")
        return informe

    AB = lado("Producto AB", "AB")
    if AB["error"]:
        informe["conclusion"] = f"No se puede calcular AB: {AB['error']}"
        return informe
    cero = matriz_cero(len(AB["resultado"]), len(AB["resultado"][0]))
    informe["comparaciones"].append({"titulo": "AB  frente a  O", "comparacion": _comparar_valores(AB["resultado"], cero)})
    a_nula, b_nula, producto_nulo = _es_cero(datos["A"]), _es_cero(datos["B"]), _es_cero(AB["resultado"])
    if producto_nulo and not a_nula and not b_nula:
        informe["cumple"] = False
        informe["conclusion"] = ("AB = O aunque ni A ni B son la matriz cero: son divisores de cero. Por eso de AB = O "
                                 "no se puede concluir A = O o B = O.")
    elif producto_nulo:
        informe["conclusion"] = "AB = O, pero A o B ya es la matriz cero, así que este caso no es un contraejemplo."
    else:
        informe["conclusion"] = ("AB ≠ O con estas matrices. Carga el contraejemplo para ver dos matrices no nulas "
                                 "con producto cero.")
    return informe


def detalle_producto_matriz_vector(A, x):
    """Explica el producto Ax fila por fila, por ejemplo 'Fila 1: (1)(2) + (3)(-1) = -1'.

    Entrada: A y x. Salida: lista de líneas.
    """
    lineas = []
    for i, fila in enumerate(A):
        valores = [f"({formatear_numero(v)})" for v in x]
        terminos = [(a, v) for a, v in zip(fila, valores)]
        texto = unir_terminos(terminos) if any(a != 0 for a in fila) else "0"
        total = sum(a * v for a, v in zip(fila, x))
        lineas.append(f"Fila {i + 1}:  {texto} = {formatear_numero(total)}")
    return lineas


def analizar_producto_av(A, v, c, u=None):
    """Calcula Av = v1·a1 + … + vn·an por columnas y comprueba A(cv) = c(Av) y, si hay u, A(u + v) = Au + Av.

    Entrada: A, v, c y u opcional. Salida: diccionario con productos, combinaciones y propiedades.
    """
    A = validar_matriz(A, "A")
    v = [Fraction(valor) for valor in v]
    c = Fraction(c)
    u = [Fraction(valor) for valor in u] if u is not None else None
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
    """Construye coeficientes no todos nulos con Ac = 0 sumando las direcciones y quitando denominadores.

    Entrada: lista de (parámetro, dirección). Salida: lista de coeficientes enteros.
    """
    n = len(direcciones[0][1])
    coeficientes = [sum(vector[i] for _, vector in direcciones) for i in range(n)]
    factor = minimo_comun_multiplo(c.denominator for c in coeficientes)
    return [c * factor for c in coeficientes]


def formatear_combinacion_lineal(coeficientes, simbolos):
    """Escribe una combinación lineal, por ejemplo [2, -1, 0, 1/2] → '2·v1 - v2 + (1/2)·v4'.

    Entrada: coeficientes y símbolos. Salida: cadena.
    """
    return unir_terminos(zip(coeficientes, simbolos), union="·")


def _plural(cantidad, singular, plural):
    """Escribe una cantidad con la palabra en singular o plural.

    Entrada: cantidad, singular y plural. Salida: cadena, por ejemplo '3 pivotes'.
    """
    return f"{cantidad} {singular if cantidad == 1 else plural}"


def analizar_independencia(A):
    """Decide si las columnas de A son linealmente independientes reduciendo [A | 0] y contando pivotes.

    Entrada: A (columnas = vectores). Salida: diccionario con escalonada, pivotes, libres, veredicto,
    justificación y una relación de dependencia si existe.
    """
    A = validar_matriz(A, "A")
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
    """Escribe el informe de independencia: [A | 0], forma escalonada, pivotes, libres y veredicto.

    Entrada: resultado de analizar_independencia. Salida: lista de líneas.
    """
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
    """Genera un sistema m × n con coeficientes enteros pequeños y solución entera.

    Entrada: m, n y generador aleatorio opcional. Salida: (A, b).
    """
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
    """Escribe el resultado de un sistema en texto plano para copiarlo al portapapeles.

    Entrada: resultado de resolver_sistema. Salida: cadena.
    """
    nombres = resultado["nombres_variables"]
    lineas = [f"{resultado['clasificacion']}: {resultado['descripcion']}"]
    if resultado["solucion"] is not None:
        lineas += [f"{nombres[i]} = {formatear_numero(v)}" for i, v in enumerate(resultado["solucion"])]
    elif resultado["expresiones"] is not None:
        lineas += [f"{nombres[i]} = {expr}" for i, expr in resultado["expresiones"].items()]
    lineas += ["", "Forma escalonada reducida:", matriz_a_texto(resultado["matriz_final"])]
    return "\n".join(lineas)



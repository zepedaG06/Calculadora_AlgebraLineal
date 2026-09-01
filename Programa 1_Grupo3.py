"""
Programa 1 - Álgebra Lineal
Solución de sistemas de ecuaciones lineales por eliminación por filas.

Restricciones cumplidas:
- No usa PySide6.
- No usa NumPy.
- No usa SciPy.
- La eliminación por filas está implementada manualmente.
"""

import os
from fractions import Fraction
import tkinter as tk
from tkinter import messagebox

# Importaciones opcionales para mejoras visuales (mantenimiento de compatibilidad)
try:
    import customtkinter as ctk
except ModuleNotFoundError:
    ctk = None

try:
    from PIL import Image
except ModuleNotFoundError:
    Image = None

# Tolerancia simbólica exacta para comparaciones
EPSILON = Fraction(0)

# Ruta base del sistema para la localización de recursos (imágenes, logos)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_LOGO = os.path.join(BASE_DIR, "logo_uam.png")


# =============================================================================
# LÓGICA MATEMÁTICA Y OPERACIONES ELEMENTALES
# =============================================================================

def convertir_numero(texto):
    """
    Convierte una cadena de texto a un objeto Fraction para procesamiento numérico exacto.

    Args:
        texto (str): Representación en cadena del número o fracción.

    Returns:
        Fraction: Valor numérico exacto.

    Raises:
        ValueError: Si la entrada está vacía o el formato no es válido.
    """
    texto = texto.strip()
    if not texto:
        raise ValueError("Hay una casilla vacía.")
    return Fraction(texto)


def formatear_numero(numero):
    """
    Convierte un objeto Fraction a un formato de texto legible para la interfaz gráfica.

    Args:
        numero (Fraction): Número racional a formatear.

    Returns:
        str: Cadena formateada (ej. "2" en lugar de "2/1", "-3/4").
    """
    if numero == 0:
        return "0"
    if numero.denominator == 1:
        return str(numero.numerator)
    return f"{numero.numerator}/{numero.denominator}"


def copiar_matriz(matriz):
    """
    Crea una copia profunda (deep copy) de una matriz bidimensional.

    Args:
        matriz (list[list[Fraction]]): Matriz a duplicar.

    Returns:
        list[list[Fraction]]: Copia independiente de la matriz.
    """
    return [fila[:] for fila in matriz]


def crear_matriz_aumentada(A, b):
    """
    Construye la matriz aumentada [A | b] concatenando el vector de términos independientes.

    Args:
        A (list[list[Fraction]]): Matriz de coeficientes de dimensión m x n.
        b (list[Fraction]): Vector de términos independientes de dimensión m.

    Returns:
        list[list[Fraction]]: Matriz aumentada de dimensión m x (n + 1).
    """
    return [A[i][:] + [b[i]] for i in range(len(A))]


def intercambiar_filas(matriz, i, j):
    """
    Ejecuta la Operación Elemental de Fila I: $F_i \leftrightarrow F_j$.

    Args:
        matriz (list[list[Fraction]]): Matriz sobre la que se opera.
        i (int): Índice de la primera fila.
        j (int): Índice de la segunda fila.
    """
    matriz[i], matriz[j] = matriz[j], matriz[i]


def multiplicar_fila(matriz, i, escalar):
    """
    Ejecuta la Operación Elemental de Fila II: $F_i \to k \cdot F_i$ ($k \neq 0$).

    Args:
        matriz (list[list[Fraction]]): Matriz sobre la que se opera.
        i (int): Índice de la fila a escalar.
        escalar (Fraction): Factor por el cual se multiplica la fila.
    """
    matriz[i] = [escalar * valor for valor in matriz[i]]


def sumar_multiplo_fila(matriz, destino, origen, factor):
    """
    Ejecuta la Operación Elemental de Fila III: $F_{\text{destino}} \to F_{\text{destino}} + k \cdot F_{\text{origen}}$.

    Args:
        matriz (list[list[Fraction]]): Matriz sobre la que se opera.
        destino (int): Índice de la fila que se modifica.
        origen (int): Índice de la fila pivote/referencia.
        factor (Fraction): Multiplicador aplicado a la fila origen antes de sumar.
    """
    matriz[destino] = [
        matriz[destino][c] + factor * matriz[origen][c]
        for c in range(len(matriz[destino]))
    ]


def matriz_a_texto(matriz):
    """
    Formatea una matriz aumentada en un bloque de texto plano con columnas alineadas.

    Args:
        matriz (list[list[Fraction]]): Matriz aumentada a formatear.

    Returns:
        str: Representación matricial con delimitadores y formato estético.
    """
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
    """
    Localiza la primera fila con un valor no nulo en una columna dada para selección de pivote.

    Args:
        matriz (list[list[Fraction]]): Matriz de trabajo.
        fila_inicio (int): Índice de fila desde donde inicia la búsqueda hacia abajo.
        columna (int): Índice de columna donde se busca el pivote.

    Returns:
        int | None: Índice de la fila encontrada o None si no existen pivotes candidatos.
    """
    for fila in range(fila_inicio, len(matriz)):
        if matriz[fila][columna] != EPSILON:
            return fila
    return None


class PasoEliminacion(dict):
    """
    Estructura de datos para registrar la traza paso a paso del algoritmo de Gauss-Jordan.

    Proporciona triple acceso a los datos del paso:
    - Como diccionario: paso['operacion']
    - Como atributos de objeto: paso.operacion
    - Como tupla/secuencia indexada: paso[0] (operación), paso[1] (matriz), paso[2] (explicación)
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
            raise IndexError("Índice de paso fuera de rango (0-2)")
        return super().__getitem__(key)


def gauss_jordan(matriz_aumentada, num_variables):
    """
    Aplica el algoritmo de reducción de Gauss-Jordan para transformar una matriz
    aumentada a su Forma Escalonada Reducida por Filas (RREF).

    Args:
        matriz_aumentada (list[list[Fraction]]): Matriz inicial [A | b].
        num_variables (int): Número de variables del sistema (columnas de A).

    Returns:
        tuple: (matriz_rref, columnas_pivote, traza_pasos)
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

    for columna in range(num_variables):
        fila_encontrada = buscar_fila_pivote(matriz, fila_pivote, columna)

        if fila_encontrada is None:
            continue

        # Paso 1: Intercambio de fila si el elemento diagonal es cero
        if fila_encontrada != fila_pivote:
            intercambiar_filas(matriz, fila_pivote, fila_encontrada)
            pasos.append(
                PasoEliminacion(
                    operacion=f"F{fila_pivote + 1} ↔ F{fila_encontrada + 1}",
                    explicacion=(
                        f"Se intercambian la fila {fila_pivote + 1} y la fila {fila_encontrada + 1} "
                        f"porque el elemento en la posición pivote actual es cero. Se necesita una fila con un "
                        f"valor no nulo en la columna {columna + 1} para continuar la eliminación."
                    ),
                    matriz=copiar_matriz(matriz),
                    tipo="intercambio",
                )
            )

        # Paso 2: Normalizar la fila del pivote para obtener un '1' principal
        valor_pivote = matriz[fila_pivote][columna]
        if valor_pivote != 1:
            inverso = Fraction(1, 1) / valor_pivote
            multiplicar_fila(matriz, fila_pivote, inverso)
            if valor_pivote == -1:
                op_str = f"F{fila_pivote + 1} → -F{fila_pivote + 1}"
                expl = (
                    f"Se multiplica la fila {fila_pivote + 1} por -1 para convertir el pivote "
                    f"de la columna {columna + 1} en 1."
                )
            else:
                inv_str = f"({formatear_numero(inverso)})" if inverso.denominator != 1 else formatear_numero(inverso)
                op_str = f"F{fila_pivote + 1} → {inv_str}F{fila_pivote + 1}"
                expl = (
                    f"Se multiplica la fila {fila_pivote + 1} por {formatear_numero(inverso)} "
                    f"(equivalente a dividir entre {formatear_numero(valor_pivote)}) para convertir el pivote "
                    f"de la columna {columna + 1} en 1."
                )
            pasos.append(
                PasoEliminacion(
                    operacion=op_str,
                    explicacion=expl,
                    matriz=copiar_matriz(matriz),
                    tipo="escalado",
                )
            )

        # Paso 3: Anular los elementos restantes arriba y abajo de la columna pivote
        for fila in range(len(matriz)):
            if fila == fila_pivote:
                continue

            factor = matriz[fila][columna]
            if factor != 0:
                sumar_multiplo_fila(matriz, fila, fila_pivote, -factor)
                posicion = "debajo" if fila > fila_pivote else "arriba"
                abs_factor = abs(factor)
                signo = "-" if factor > 0 else "+"

                if abs_factor == 1:
                    op_str = f"F{fila + 1} → F{fila + 1} {signo} F{fila_pivote + 1}"
                    if factor > 0:
                        expl = (
                            f"Se resta la fila {fila_pivote + 1} a la fila {fila + 1} para generar "
                            f"un cero {posicion} del pivote en la columna {columna + 1}."
                        )
                    else:
                        expl = (
                            f"Se suma la fila {fila_pivote + 1} a la fila {fila + 1} para generar "
                            f"un cero {posicion} del pivote en la columna {columna + 1}."
                        )
                else:
                    fact_str = f"({formatear_numero(abs_factor)})" if abs_factor.denominator != 1 else formatear_numero(abs_factor)
                    op_str = f"F{fila + 1} → F{fila + 1} {signo} {fact_str}F{fila_pivote + 1}"
                    if factor > 0:
                        expl = (
                            f"Se multiplica la fila {fila_pivote + 1} por {formatear_numero(abs_factor)} y se resta el resultado "
                            f"a la fila {fila + 1} para generar un cero {posicion} del pivote en la columna {columna + 1}."
                        )
                    else:
                        expl = (
                            f"Se multiplica la fila {fila_pivote + 1} por {formatear_numero(abs_factor)} y se suma el resultado "
                            f"a la fila {fila + 1} para generar un cero {posicion} del pivote en la columna {columna + 1}."
                        )

                pasos.append(
                    PasoEliminacion(
                        operacion=op_str,
                        explicacion=expl,
                        matriz=copiar_matriz(matriz),
                        tipo="eliminacion",
                    )
                )

        columnas_pivote.append(columna)
        fila_pivote += 1

        if fila_pivote == len(matriz):
            break

    return matriz, columnas_pivote, pasos


def fila_inconsistente(fila, num_variables):
    """
    Determina si una fila de la matriz reducida contiene una contradicción del tipo [0 0 ... 0 | k] con k != 0.
    """
    coeficientes_cero = all(fila[c] == 0 for c in range(num_variables))
    return coeficientes_cero and fila[-1] != 0


def es_sistema_homogeneo(b):
    """Verifica si el vector de términos independientes b es nulo en su totalidad (Ax = 0)."""
    return all(valor == 0 for valor in b)


def clasificar_sistema(matriz_rref, columnas_pivote, num_variables):
    """
    Aplica el Teorema de Rouché-Frobenius para clasificar la naturaleza de las soluciones del sistema.

    Returns:
        tuple: (clasificación_str, descripción_str)
    """
    for fila in matriz_rref:
        if fila_inconsistente(fila, num_variables):
            return "Sistema inconsistente", "No tiene solución."

    if len(columnas_pivote) == num_variables:
        return "Sistema consistente determinado", "Tiene una única solución."

    return "Sistema consistente indeterminado", "Tiene infinitas soluciones."


def obtener_solucion_unica(matriz_rref, columnas_pivote, num_variables):
    """Extrae los valores numéricos directos de la solución para un sistema consistente determinado."""
    solucion = [Fraction(0) for _ in range(num_variables)]
    for fila, columna in enumerate(columnas_pivote):
        solucion[columna] = matriz_rref[fila][-1]
    return solucion


def nombres_parametros(cantidad):
    """Genera identificadores algebraicos para los parámetros de variables libres (t, s, r, ...)."""
    base = ["t", "s", "r", "u", "v", "w"]
    if cantidad <= len(base):
        return base[:cantidad]
    return base + [f"p{i}" for i in range(1, cantidad - len(base) + 1)]


def obtener_solucion_parametrica(matriz_rref, columnas_pivote, num_variables):
    """
    Construye las expresiones algebraicas de la solución paramétrica de un sistema
    con infinitas soluciones (variables básicas en función de variables libres).
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

    return expresiones, variables_libres, parametros


def obtener_nombres_variables(num_variables):
    """Genera las etiquetas estandarizadas de las variables (x, y, z o x1, x2, ...)."""
    if num_variables == 2:
        return ["x", "y"]
    elif num_variables == 3:
        return ["x", "y", "z"]
    elif num_variables == 4:
        return ["x", "y", "z", "w"]
    return [f"x{i + 1}" for i in range(num_variables)]


def formatear_ecuacion_original(fila_coefs, termino_indep, nombres_vars):
    """Formatea la representación algebraica canónica de una ecuación original del sistema."""
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
    """Sustituye explícitamente la solución calculada en la ecuación original."""
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
    """Calcula paso a paso la simplificación numérica de la comprobación."""
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
    """Estructura para almacenar y exponer los detalles pedagógicos de la comprobación."""

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
    Comprueba si la solución obtenida satisface cada ecuación del sistema original $A \cdot x = b$.

    Returns:
        tuple: (es_correcta_bool, lista_detalles)
    """
    num_vars = len(A_original[0])
    nombres_vars = obtener_nombres_variables(num_vars)
    detalles = []
    correcta = True

    for i, fila in enumerate(A_original):
        esperado = b_original[i]
        orig_str = formatear_ecuacion_original(fila, esperado, nombres_vars)
        sust_str = formatear_sustitucion(fila, esperado, solucion)
        simpl_pasos, coincide, suma = formatear_simplificacion(fila, esperado, solucion)
        correcta = correcta and coincide

        detalles.append(
            DetalleVerificacion(
                indice=i + 1,
                ecuacion_original=orig_str,
                sustitucion=sust_str,
                simplificacion=simpl_pasos,
                suma_obtenida=suma,
                esperado=esperado,
                coincide=coincide,
            )
        )

    return correcta, detalles


def resolver_sistema(A, b):
    """
    Función orquestadora matemática principal.
    Procesa el sistema, ejecuta Gauss-Jordan, clasifica la solución y efectúa la verificación.
    """
    num_variables = len(A[0])
    nombres_vars = obtener_nombres_variables(num_variables)
    aumentada = crear_matriz_aumentada(A, b)
    rref, columnas_pivote, pasos = gauss_jordan(aumentada, num_variables)
    clasificacion, descripcion = clasificar_sistema(rref, columnas_pivote, num_variables)

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
        solucion_particular = [Fraction(0) for _ in range(num_variables)]
        for variable, expresion in expresiones.items():
            if variable not in libres:
                solucion_particular[variable] = rref[columnas_pivote.index(variable)][-1]

        resultado["expresiones"] = expresiones
        resultado["variables_libres"] = libres
        resultado["parametros"] = parametros
        resultado["solucion_particular"] = solucion_particular
        resultado["verificacion"] = verificar_solucion(A, b, solucion_particular)

    return resultado


# =============================================================================
# CONFIGURACIÓN DE TEMA Y ESTILOS DE INTERFAZ GRÁFICA
# =============================================================================

# Definición de la paleta institucional (UAM)
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

# Tipografías del sistema
FUENTE_TITULO = ("Segoe UI", 26, "bold")
FUENTE_SUBTITULO = ("Segoe UI", 14)
FUENTE_SECCION = ("Segoe UI", 17, "bold")
FUENTE_NORMAL = ("Segoe UI", 13)
FUENTE_PEQUENA = ("Segoe UI", 11)
FUENTE_MONO = ("Consolas", 15)


# =============================================================================
# COMPONENTES VISUALES Y HELPER FUNCTIONS FOR GUI
# =============================================================================

def configurar_customtkinter():
    """Inicializa la configuración global del entorno CustomTkinter."""
    if ctk is None:
        return
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def resolver_color(par):
    """Resuelve la tupla de color (claro, oscuro) devolviendo el valor para modo oscuro por defecto."""
    if isinstance(par, tuple):
        return par[1]
    return par


def cargar_logo(tamano=(96, 96)):
    """Maneja la carga y escalado de la imagen del logotipo institucional."""
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
    """Contenedor genérico de tipo tarjeta con borde estilizado."""
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
    """Componente para la entrada dinámica de datos de la matriz [A | b]."""

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
        """Ajusta la región desplazable del canvas al redimensionar los elementos internos."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def actualizar_tema_canvas(self):
        """Actualiza dinámicamente los colores de fondo del canvas nativo."""
        self.canvas.configure(bg=resolver_color(PALETA["panel_2"]))

    def crear_matriz(self, m, n):
        """Genera dinámicamente la cuadrícula de cajas de texto (Entry) según la dimensión m x n."""
        for widget in self.grid_host.winfo_children():
            widget.destroy()

        self.m = m
        self.n = n
        self.entradas = []
        self.dimension_label.configure(text=f"{m} ecuaciones x {n} variables")

        ctk.CTkLabel(self.grid_host, text="A", font=FUENTE_PEQUENA, text_color=PALETA["primario"]).grid(row=0, column=0, columnspan=n, pady=(4, 8))
        ctk.CTkLabel(self.grid_host, text="b", font=FUENTE_PEQUENA, text_color=PALETA["primario"]).grid(row=0, column=n + 1, pady=(4, 8))

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
        """Reinicia todos los campos numéricos de la matriz a cero."""
        for fila in self.entradas:
            for entrada in fila:
                entrada.delete(0, "end")
                entrada.insert(0, "0")

    def leer_datos(self):
        """Lee y extrae las matrices numéricas A y b de los controles gráficos de la interfaz."""
        A = []
        b = []
        for fila in self.entradas:
            valores = [convertir_numero(entrada.get()) for entrada in fila]
            A.append(valores[:-1])
            b.append(valores[-1])
        return A, b


class ProcessPanel(ctk.CTkFrame):
    """
    Panel desplazable encargado de visualizar de forma interactiva la traza
    de operaciones elementales de fila y los estados intermedios del sistema.
    """

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
        """Maneja los eventos del scroll del ratón con soporte para desplazamiento horizontal mediante Shift."""
        if event.state & 0x0001:
            self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _actualizar_scroll(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        pass

    def mostrar_placeholder(self):
        """Muestra un mensaje cuando el panel está vacío y no se ha resuelto ningún sistema."""
        for w in self.grid_host.winfo_children():
            w.destroy()
        ph = ctk.CTkLabel(
            self.grid_host,
            text="Ingrese un sistema y haga clic en 'Resolver sistema'\npara ver aquí el paso a paso.",
            font=FUENTE_NORMAL,
            text_color=PALETA["texto_3"],
            justify="center",
        )
        ph.pack(padx=40, pady=60)
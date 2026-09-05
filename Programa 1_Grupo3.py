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


def gauss_jordan(matriz_aumentada, num_variables):
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
                        f"de la columna {columna + 1} (variable x{columna + 1})."
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
                        f"de la columna {columna + 1} (variable x{columna + 1}) en 1."
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
                        f"{columna + 1} (variable x{columna + 1}), {posicion} del pivote, usando F{fila_pivote + 1}."
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


def obtener_nombres_variables(num_variables):
    """Genera nombres de variables consistentes: x1, x2, x3, ..."""
    return [f"x{i + 1}" for i in range(num_variables)]


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


def resolver_sistema(A, b):
    """Funcion principal de la parte matematica."""
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

        # 3. Solucion
        if resultado["solucion"] is not None:
            self._mostrar_solucion_unica(resultado["solucion"], nombres_vars)

        if resultado["expresiones"] is not None:
            self._mostrar_solucion_parametrica(
                resultado["expresiones"],
                nombres_vars,
                resultado.get("solucion_particular"),
            )

        # 4. Verificacion explicativa
        if resultado["verificacion"] is not None:
            es_param = (resultado["clasificacion"] == "Sistema consistente indeterminado")
            self._mostrar_verificacion(resultado["verificacion"], es_parametrico=es_param)
        else:
            self._mostrar_verificacion_inconsistente()

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
        self.nav_botones["calculadora"] = self._nav_item(sidebar, "Calculadora", "calculadora", activo=True)
        self.nav_botones["metodo"] = self._nav_item(sidebar, "Metodo de Eliminacion", "metodo")
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
        for nombre, boton in self.nav_botones.items():
            if nombre == pagina:
                boton.configure(fg_color=PALETA["primario"], text_color="#04191A")
            else:
                boton.configure(fg_color="transparent", text_color=PALETA["texto"])
        self.paginas[pagina].tkraise()

    def crear_contenido_principal(self):
        contenedor = ctk.CTkFrame(self, fg_color=PALETA["fondo"], corner_radius=0)
        contenedor.grid(row=0, column=1, sticky="nsew")
        contenedor.grid_columnconfigure(0, weight=1)
        contenedor.grid_rowconfigure(0, weight=1)

        self.paginas = {
            "calculadora": self._crear_pagina_calculadora(contenedor),
            "metodo": self._crear_pagina_metodo(contenedor),
            "ayuda": self._crear_pagina_ayuda(contenedor),
        }
        for pagina in self.paginas.values():
            pagina.grid(row=0, column=0, sticky="nsew")

        self.paginas["calculadora"].tkraise()

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

    def _crear_pagina_metodo(self, parent):
        pagina = ctk.CTkFrame(parent, fg_color=PALETA["fondo"], corner_radius=0)
        pagina.grid_columnconfigure(0, weight=1)
        pagina.grid_rowconfigure(1, weight=1)

        self._crear_encabezado(
            pagina,
            "Metodo de Eliminacion de Gauss-Jordan",
            "Como el programa reduce la matriz aumentada paso a paso",
        )

        cuerpo = ctk.CTkScrollableFrame(pagina, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))

        pasos_metodo = [
            ("1. Matriz aumentada [A | b]",
             "Se construye colocando junto a la matriz de coeficientes A la columna de terminos independientes b. Cada fila representa una ecuacion del sistema."),
            ("2. Buscar el pivote",
             "En cada columna se busca una fila con un valor distinto de cero para usarlo como pivote. Si la fila del pivote tiene un cero en esa columna, se intercambia con otra fila (Fi <-> Fj)."),
            ("3. Normalizar el pivote",
             "La fila del pivote se multiplica por el inverso del valor del pivote, de modo que el pivote quede en 1 (Fi -> Fi / k)."),
            ("4. Eliminar la columna",
             "Se suma un multiplo de la fila pivote a todas las demas filas para convertir en cero el resto de la columna del pivote (Fi -> Fi + factor * Fpivote)."),
            ("5. Repetir por columnas",
             "El proceso se repite para cada columna de variables hasta llegar a la forma escalonada reducida (cada pivote en 1, con ceros arriba y abajo)."),
            ("6. Clasificar el sistema",
             "Si aparece una fila 0 = k con k distinto de cero, el sistema es inconsistente. Si cada variable tiene columna pivote, es consistente determinado (solucion unica). Si sobran variables sin pivote, es consistente indeterminado (infinitas soluciones)."),
            ("7. Variables basicas y libres",
             "Las columnas que contienen un pivote corresponden a variables basicas. Las columnas sin pivote corresponden a variables libres, que se expresan como parametros (t, s, r, ...)."),
            ("8. Verificar la solucion",
             "Los valores obtenidos se sustituyen en el sistema original (Ax = b) para comprobar que cada ecuacion se cumple."),
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
            "Ayuda",
            "Como usar la calculadora y significado de los conceptos clave",
        )

        cuerpo = ctk.CTkScrollableFrame(pagina, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))

        tarjeta_uso = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        tarjeta_uso.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(tarjeta_uso, text="Como usar la calculadora", font=("Segoe UI", 15, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(14, 6))
        pasos_uso = [
            "1. En 'Calculadora', escribe el numero de ecuaciones y variables y presiona 'Crear sistema'.",
            "2. Llena la matriz A con los coeficientes y la columna b con los terminos independientes (acepta enteros, decimales o fracciones como 3/2).",
            "3. Presiona 'Resolver sistema' para ver cada operacion elemental en 'Proceso de Eliminacion'.",
            "4. Revisa 'Resultado' para ver la clasificacion del sistema, las variables basicas/libres, la solucion y su verificacion.",
            "5. Usa 'Limpiar' para reiniciar la matriz actual sin cambiar el tamano del sistema.",
        ]
        for paso in pasos_uso:
            ctk.CTkLabel(
                tarjeta_uso, text=paso, font=FUENTE_NORMAL, text_color=PALETA["texto_2"],
                wraplength=780, justify="left",
            ).pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(tarjeta_uso, text="").pack(pady=4)

        conceptos = [
            ("Matriz aumentada", "La matriz [A | b] que combina los coeficientes del sistema con los terminos independientes."),
            ("Operacion elemental", "Un intercambio de filas, una multiplicacion de una fila por un escalar, o la suma de un multiplo de una fila a otra."),
            ("Pivote", "El primer valor distinto de cero de una fila, usado como referencia para eliminar el resto de su columna."),
            ("Forma escalonada reducida", "Resultado final de Gauss-Jordan: cada pivote vale 1 y tiene ceros arriba y abajo de el."),
            ("Variables basicas", "Las variables cuya columna en la matriz reducida contiene un pivote."),
            ("Variables libres", "Las variables sin columna pivote; su valor se deja como parametro (t, s, r, ...)."),
            ("Sistema consistente", "Tiene al menos una solucion (determinado: unica, o indeterminado: infinitas)."),
            ("Sistema inconsistente", "No tiene solucion; aparece una fila equivalente a 0 = k con k distinto de cero."),
            ("Sistema homogeneo", "Aquel en el que todos los terminos independientes (b) son cero; siempre es consistente porque x = 0 es una solucion."),
        ]

        tarjeta_conceptos = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        tarjeta_conceptos.pack(fill="x")
        ctk.CTkLabel(tarjeta_conceptos, text="Conceptos clave", font=("Segoe UI", 15, "bold"), text_color=PALETA["primario"]).pack(anchor="w", padx=16, pady=(14, 6))
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

        ctk.CTkButton(
            fila,
            text="2 × 2",
            width=80,
            height=40,
            corner_radius=8,
            fg_color=PALETA["secundario"],
            hover_color=PALETA["secundario_hover"],
            text_color=PALETA["texto"],
            font=("Segoe UI", 12, "bold"),
            command=self.crear_sistema_2x2,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkLabel(
            fila,
            text="Enteros, decimales o fracciones como 3/2.",
            font=FUENTE_PEQUENA,
            text_color=PALETA["texto_3"],
        ).pack(side="left", padx=14)

    def crear_sistema_2x2(self):
        """Crea rápidamente un sistema de 2 ecuaciones con 2 variables."""
        self.entrada_m.delete(0, "end")
        self.entrada_m.insert(0, "2")
        self.entrada_n.delete(0, "end")
        self.entrada_n.insert(0, "2")
        self.matrix_panel.crear_matriz(2, 2)

        # Ejemplo sencillo para que el usuario vea inmediatamente
        # cómo se organiza [A | b] en un sistema 2x2.
        ejemplo = [
            ["2", "1", "5"],
            ["1", "-1", "1"],
        ]
        for i, fila in enumerate(ejemplo):
            for j, valor in enumerate(fila):
                self.matrix_panel.entradas[i][j].delete(0, "end")
                self.matrix_panel.entradas[i][j].insert(0, valor)

        self.process_panel.mostrar_placeholder()
        self.result_panel.mostrar_placeholder()


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
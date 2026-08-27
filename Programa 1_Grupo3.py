"""
Programa 1 - Algebra Lineal
Solucion de sistemas de ecuaciones lineales por eliminacion por filas.

Restricciones cumplidas:
- No usa PySide6.
- No usa NumPy.
- No usa SciPy.
- La eliminacion por filas esta implementada manualmente.
"""

from fractions import Fraction
import tkinter as tk
from tkinter import messagebox

try:
    import customtkinter as ctk
except ModuleNotFoundError:
    ctk = None


EPSILON = Fraction(0)


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
    lineas = []
    for fila in matriz:
        coeficientes = "  ".join(f"{formatear_numero(x):>8}" for x in fila[:-1])
        independiente = f"{formatear_numero(fila[-1]):>8}"
        lineas.append(f"[ {coeficientes} | {independiente} ]")
    return "\n".join(lineas)


def buscar_fila_pivote(matriz, fila_inicio, columna):
    """Busca una fila con entrada no nula en la columna candidata a pivote."""
    for fila in range(fila_inicio, len(matriz)):
        if matriz[fila][columna] != EPSILON:
            return fila
    return None


def gauss_jordan(matriz_aumentada, num_variables):
    """
    Reduce la matriz aumentada hasta forma escalonada reducida.

    La normalizacion deja cada pivote igual a 1. La eliminacion se aplica en
    todas las filas distintas de la fila pivote, lo cual facilita leer
    soluciones unicas o parametricas.
    """
    matriz = copiar_matriz(matriz_aumentada)
    pasos = [("Matriz aumentada inicial", copiar_matriz(matriz))]
    columnas_pivote = []
    fila_pivote = 0

    for columna in range(num_variables):
        fila_encontrada = buscar_fila_pivote(matriz, fila_pivote, columna)

        if fila_encontrada is None:
            continue

        if fila_encontrada != fila_pivote:
            intercambiar_filas(matriz, fila_pivote, fila_encontrada)
            pasos.append(
                (f"F{fila_pivote + 1} <-> F{fila_encontrada + 1}", copiar_matriz(matriz))
            )

        valor_pivote = matriz[fila_pivote][columna]
        if valor_pivote != 1:
            multiplicar_fila(matriz, fila_pivote, Fraction(1, 1) / valor_pivote)
            pasos.append(
                (
                    f"F{fila_pivote + 1} -> F{fila_pivote + 1} / {formatear_numero(valor_pivote)}",
                    copiar_matriz(matriz),
                )
            )

        for fila in range(len(matriz)):
            if fila == fila_pivote:
                continue

            factor = matriz[fila][columna]
            if factor != 0:
                sumar_multiplo_fila(matriz, fila, fila_pivote, -factor)
                signo = "-" if factor > 0 else "+"
                pasos.append(
                    (
                        f"F{fila + 1} -> F{fila + 1} {signo} {formatear_numero(abs(factor))}F{fila_pivote + 1}",
                        copiar_matriz(matriz),
                    )
                )

        columnas_pivote.append(columna)
        fila_pivote += 1

        if fila_pivote == len(matriz):
            break

    return matriz, columnas_pivote, pasos


def fila_inconsistente(fila, num_variables):
    """Detecta una contradiccion: 0x1 + 0x2 + ... + 0xn = k, con k distinto de 0."""
    coeficientes_cero = all(fila[c] == 0 for c in range(num_variables))
    return coeficientes_cero and fila[-1] != 0


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
    """Genera nombres simples para variables libres."""
    base = ["t", "s", "r", "u", "v", "w"]
    if cantidad <= len(base):
        return base[:cantidad]
    return base + [f"p{i}" for i in range(1, cantidad - len(base) + 1)]


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
                terminos.append(f"{formatear_numero(coeficiente)}{parametro}")

        expresiones[columna_pivote] = " + ".join(terminos).replace("+ -", "- ") if terminos else "0"

    return expresiones, variables_libres, parametros


def verificar_solucion(A_original, b_original, solucion):
    """
    Verifica Ax = b usando el sistema original.
    No resuelve el sistema; solo sustituye los valores obtenidos.
    """
    resultados = []
    correcta = True

    for i, fila in enumerate(A_original):
        suma = sum(fila[j] * solucion[j] for j in range(len(solucion)))
        esperado = b_original[i]
        coincide = suma == esperado
        correcta = correcta and coincide
        resultados.append((suma, esperado, coincide))

    return correcta, resultados


def resolver_sistema(A, b):
    """Funcion principal de la parte matematica."""
    num_variables = len(A[0])
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
        "clasificacion": clasificacion,
        "descripcion": descripcion,
        "solucion": None,
        "expresiones": None,
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
        resultado["verificacion"] = verificar_solucion(A, b, solucion_particular)

    return resultado


# -----------------------------------------------------------------------------
# Configuracion visual
# -----------------------------------------------------------------------------

PALETA = {
    "fondo": "#0F172A",
    "sidebar": "#111827",
    "panel": "#1E293B",
    "panel_2": "#273449",
    "entrada": "#0F172A",
    "borde": "#334155",
    "texto": "#F8FAFC",
    "texto_2": "#CBD5E1",
    "texto_3": "#94A3B8",
    "primario": "#2563EB",
    "primario_hover": "#1D4ED8",
    "secundario": "#334155",
    "secundario_hover": "#475569",
    "exito": "#22C55E",
    "advertencia": "#F59E0B",
    "error": "#EF4444",
}

FUENTE_TITULO = ("Segoe UI", 26, "bold")
FUENTE_SUBTITULO = ("Segoe UI", 14)
FUENTE_SECCION = ("Segoe UI", 17, "bold")
FUENTE_NORMAL = ("Segoe UI", 13)
FUENTE_PEQUENA = ("Segoe UI", 11)
FUENTE_MONO = ("Consolas", 13)


# -----------------------------------------------------------------------------
# Componentes de interfaz
# -----------------------------------------------------------------------------

def configurar_customtkinter():
    if ctk is None:
        return
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def crear_tarjeta(parent, titulo=None):
    tarjeta = ctk.CTkFrame(
        parent,
        fg_color=PALETA["panel"],
        corner_radius=8,
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
        super().__init__(parent, fg_color=PALETA["panel"], corner_radius=8, border_width=1, border_color=PALETA["borde"])
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

        self.canvas_frame = ctk.CTkFrame(self, fg_color=PALETA["panel_2"], corner_radius=8)
        self.canvas_frame.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg=PALETA["panel_2"],
            highlightthickness=0,
            height=230,
        )
        self.scroll_y = ctk.CTkScrollbar(self.canvas_frame, orientation="vertical", command=self.canvas.yview)
        self.scroll_x = ctk.CTkScrollbar(self.canvas_frame, orientation="horizontal", command=self.canvas.xview)
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
            fg_color=PALETA["primario"],
            hover_color=PALETA["primario_hover"],
            command=self.on_resolver,
        )
        self.solve_button.pack(side="left")

        ctk.CTkButton(
            self.actions,
            text="Limpiar",
            height=42,
            fg_color=PALETA["secundario"],
            hover_color=PALETA["secundario_hover"],
            command=self.on_limpiar,
        ).pack(side="left", padx=10)

    def _actualizar_scroll(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def crear_matriz(self, m, n):
        for widget in self.grid_host.winfo_children():
            widget.destroy()

        self.m = m
        self.n = n
        self.entradas = []
        self.dimension_label.configure(text=f"{m} ecuaciones x {n} variables")

        ctk.CTkLabel(self.grid_host, text="A", font=FUENTE_PEQUENA, text_color=PALETA["texto_3"]).grid(row=0, column=0, columnspan=n, pady=(4, 8))
        ctk.CTkLabel(self.grid_host, text="b", font=FUENTE_PEQUENA, text_color=PALETA["texto_3"]).grid(row=0, column=n + 1, pady=(4, 8))

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

            separador = ctk.CTkFrame(self.grid_host, width=2, height=36, fg_color=PALETA["texto_3"])
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
    """Muestra las operaciones elementales y la matriz despues de cada paso."""

    def __init__(self, parent):
        super().__init__(parent, fg_color=PALETA["panel"], corner_radius=8, border_width=1, border_color=PALETA["borde"])
        ctk.CTkLabel(self, text="Proceso de Eliminacion", font=FUENTE_SECCION).pack(anchor="w", padx=18, pady=(16, 8))
        self.contenedor = ctk.CTkScrollableFrame(self, fg_color="transparent", height=280)
        self.contenedor.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        self.mostrar_placeholder()

    def limpiar(self):
        for widget in self.contenedor.winfo_children():
            widget.destroy()

    def mostrar_placeholder(self):
        self.limpiar()
        ctk.CTkLabel(
            self.contenedor,
            text="Crea un sistema, ingresa los coeficientes y presiona Resolver sistema.",
            font=FUENTE_NORMAL,
            text_color=PALETA["texto_3"],
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=8)

    def mostrar_pasos(self, pasos):
        self.limpiar()
        for indice, (descripcion, matriz) in enumerate(pasos, start=1):
            item = ctk.CTkFrame(self.contenedor, fg_color=PALETA["panel_2"], corner_radius=8)
            item.pack(fill="x", pady=(0, 10))

            ctk.CTkLabel(
                item,
                text=f"Paso {indice}: {descripcion}",
                font=FUENTE_NORMAL,
                text_color=PALETA["texto"],
            ).pack(anchor="w", padx=14, pady=(10, 4))

            ctk.CTkLabel(
                item,
                text=matriz_a_texto(matriz),
                font=FUENTE_MONO,
                text_color=PALETA["texto_2"],
                justify="left",
            ).pack(anchor="w", padx=14, pady=(0, 12))


class ResultPanel(ctk.CTkFrame):
    """Presenta clasificacion, variables, solucion y verificacion."""

    def __init__(self, parent):
        super().__init__(parent, fg_color=PALETA["panel"], corner_radius=8, border_width=1, border_color=PALETA["borde"])
        ctk.CTkLabel(self, text="Resultado", font=FUENTE_SECCION).pack(anchor="w", padx=18, pady=(16, 8))
        self.contenido = ctk.CTkFrame(self, fg_color="transparent")
        self.contenido.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        self.mostrar_placeholder()

    def limpiar(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

    def mostrar_placeholder(self):
        self.limpiar()
        ctk.CTkLabel(
            self.contenido,
            text="Aqui se mostraran la clasificacion, la solucion y la verificacion.",
            font=FUENTE_NORMAL,
            text_color=PALETA["texto_3"],
            wraplength=360,
            justify="left",
        ).pack(anchor="w", pady=8)

    def _estado_color(self, clasificacion):
        if "inconsistente" in clasificacion.lower():
            return PALETA["error"]
        if "indeterminado" in clasificacion.lower():
            return PALETA["advertencia"]
        return PALETA["exito"]

    def mostrar_resultado(self, resultado):
        self.limpiar()
        color = self._estado_color(resultado["clasificacion"])

        estado = ctk.CTkFrame(self.contenido, fg_color=PALETA["panel_2"], corner_radius=8)
        estado.pack(fill="x", pady=(0, 12))
        ctk.CTkFrame(estado, fg_color=color, width=5, corner_radius=8).pack(side="left", fill="y")
        texto_estado = ctk.CTkFrame(estado, fg_color="transparent")
        texto_estado.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(texto_estado, text="Clasificacion del sistema", font=FUENTE_PEQUENA, text_color=PALETA["texto_3"]).pack(anchor="w")
        ctk.CTkLabel(texto_estado, text=resultado["clasificacion"], font=("Segoe UI", 15, "bold"), text_color=PALETA["texto"]).pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(texto_estado, text=resultado["descripcion"], font=FUENTE_PEQUENA, text_color=PALETA["texto_2"]).pack(anchor="w")

        basicas = ", ".join(f"x{c + 1}" for c in resultado["variables_basicas"]) or "ninguna"
        libres = ", ".join(f"x{c + 1}" for c in resultado["variables_libres"]) or "ninguna"
        ctk.CTkLabel(self.contenido, text=f"Variables basicas: {basicas}", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(anchor="w", pady=2)
        ctk.CTkLabel(self.contenido, text=f"Variables libres: {libres}", font=FUENTE_NORMAL, text_color=PALETA["texto_2"]).pack(anchor="w", pady=(2, 12))

        if resultado["solucion"] is not None:
            self._mostrar_solucion_unica(resultado["solucion"])

        if resultado["expresiones"] is not None:
            self._mostrar_solucion_parametrica(resultado["expresiones"])

        if resultado["verificacion"] is not None:
            self._mostrar_verificacion(resultado["verificacion"])

    def _mostrar_solucion_unica(self, solucion):
        tarjeta = ctk.CTkFrame(self.contenido, fg_color=PALETA["panel_2"], corner_radius=8)
        tarjeta.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(tarjeta, text="Solucion", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
        for i, valor in enumerate(solucion, start=1):
            ctk.CTkLabel(tarjeta, text=f"x{i} = {formatear_numero(valor)}", font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=14, pady=1)
        ctk.CTkLabel(tarjeta, text="").pack(pady=3)

    def _mostrar_solucion_parametrica(self, expresiones):
        tarjeta = ctk.CTkFrame(self.contenido, fg_color=PALETA["panel_2"], corner_radius=8)
        tarjeta.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(tarjeta, text="Solucion parametrica", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
        for i in range(len(expresiones)):
            ctk.CTkLabel(tarjeta, text=f"x{i + 1} = {expresiones[i]}", font=FUENTE_MONO, text_color=PALETA["texto_2"]).pack(anchor="w", padx=14, pady=1)
        ctk.CTkLabel(tarjeta, text="").pack(pady=3)

    def _mostrar_verificacion(self, verificacion):
        correcta, detalles = verificacion
        color = PALETA["exito"] if correcta else PALETA["error"]
        texto = "Solucion verificada" if correcta else "La solucion no coincide"

        tarjeta = ctk.CTkFrame(self.contenido, fg_color=PALETA["panel_2"], corner_radius=8)
        tarjeta.pack(fill="x")
        ctk.CTkLabel(tarjeta, text="Verificacion", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        ctk.CTkLabel(tarjeta, text=texto, font=FUENTE_NORMAL, text_color=color).pack(anchor="w", padx=14, pady=(0, 6))

        for i, (obtenido, esperado, coincide) in enumerate(detalles, start=1):
            marca = "correcto" if coincide else "incorrecto"
            ctk.CTkLabel(
                tarjeta,
                text=f"Ecuacion {i}: {formatear_numero(obtenido)} = {formatear_numero(esperado)} ({marca})",
                font=FUENTE_PEQUENA,
                text_color=PALETA["texto_2"],
            ).pack(anchor="w", padx=14, pady=1)
        ctk.CTkLabel(tarjeta, text="").pack(pady=3)


# -----------------------------------------------------------------------------
# Ventana principal
# -----------------------------------------------------------------------------

class AplicacionAlgebraLineal(ctk.CTk):
    """Aplicacion de escritorio moderna hecha con CustomTkinter."""

    def __init__(self):
        super().__init__()
        self.title("Calculadora de Algebra Lineal - Grupo 3")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(fg_color=PALETA["fondo"])

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.crear_sidebar()
        self.crear_contenido_principal()
        self.crear_sistema()

    def crear_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=PALETA["sidebar"], corner_radius=0, width=240)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text="Algebra\nLineal", font=("Segoe UI", 26, "bold"), justify="left").pack(anchor="w", padx=24, pady=(28, 8))
        ctk.CTkLabel(sidebar, text="Calculadora academica", font=FUENTE_PEQUENA, text_color=PALETA["texto_3"]).pack(anchor="w", padx=24, pady=(0, 28))

        self._nav_item(sidebar, "Calculadora", activo=True)
        self._nav_item(sidebar, "Metodo de Eliminacion")
        self._nav_item(sidebar, "Ayuda")

        ctk.CTkFrame(sidebar, fg_color="transparent").pack(fill="both", expand=True)
        ctk.CTkLabel(sidebar, text="Tema", font=FUENTE_PEQUENA, text_color=PALETA["texto_3"]).pack(anchor="w", padx=24, pady=(0, 6))
        self.theme_switch = ctk.CTkSwitch(sidebar, text="Modo claro", command=self.cambiar_tema)
        self.theme_switch.pack(anchor="w", padx=24, pady=(0, 24))

    def _nav_item(self, parent, texto, activo=False):
        color = PALETA["primario"] if activo else "transparent"
        item = ctk.CTkButton(
            parent,
            text=texto,
            anchor="w",
            height=38,
            fg_color=color,
            hover_color=PALETA["secundario_hover"],
            text_color=PALETA["texto"],
            command=lambda: None,
        )
        item.pack(fill="x", padx=16, pady=4)

    def crear_contenido_principal(self):
        contenedor = ctk.CTkFrame(self, fg_color=PALETA["fondo"], corner_radius=0)
        contenedor.grid(row=0, column=1, sticky="nsew")
        contenedor.grid_columnconfigure(0, weight=1)
        contenedor.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(contenedor, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Calculadora de Algebra Lineal", font=FUENTE_TITULO).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Solucion de sistemas de ecuaciones lineales por eliminacion por filas",
            font=FUENTE_SUBTITULO,
            text_color=PALETA["texto_2"],
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        contenido = ctk.CTkFrame(contenedor, fg_color="transparent")
        contenido.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        contenido.grid_columnconfigure(0, weight=3)
        contenido.grid_columnconfigure(1, weight=2)
        contenido.grid_rowconfigure(1, weight=1)

        self.config_panel = crear_tarjeta(contenido, "Configuracion del sistema")
        self.config_panel.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        self.crear_configuracion(self.config_panel)

        self.matrix_panel = MatrixInputPanel(contenido, self.resolver_desde_interfaz, self.limpiar_matriz)
        self.matrix_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 14))

        derecha = ctk.CTkFrame(contenido, fg_color="transparent")
        derecha.grid(row=1, column=1, sticky="nsew")
        derecha.grid_rowconfigure(0, weight=3)
        derecha.grid_rowconfigure(1, weight=2)
        derecha.grid_columnconfigure(0, weight=1)

        self.process_panel = ProcessPanel(derecha)
        self.process_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 14))

        self.result_panel = ResultPanel(derecha)
        self.result_panel.grid(row=1, column=0, sticky="nsew")

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
            fg_color=PALETA["primario"],
            hover_color=PALETA["primario_hover"],
            command=self.crear_sistema,
        ).pack(side="left")

        ctk.CTkLabel(
            fila,
            text="Puedes escribir enteros, decimales o fracciones como 3/2.",
            font=FUENTE_PEQUENA,
            text_color=PALETA["texto_3"],
        ).pack(side="left", padx=18)

    def cambiar_tema(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")

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

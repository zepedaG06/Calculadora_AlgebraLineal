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
from teoremas.teoremas_matrices import TEOREMAS_MATRICES, texto_teoremas, LOGO_ASCII
from modulos import informes as didactica

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

# Conserva las APIs históricas, incluidas las utilidades internas del parser.
from modulos import modulo_matrices as _matematica
globals().update({nombre: valor for nombre, valor in vars(_matematica).items()
                  if not nombre.startswith("__")})


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
        def ajustar_al_marco(_evento=None):
            if not label.winfo_exists():
                return
            ancho = label.master.winfo_width() / escala_de(label)
            if ancho <= 1:
                return
            objetivo = max(minimo, round(margen(ancho) if callable(margen) else ancho - margen))
            if abs(objetivo - label.cget("wraplength")) > 4:
                label.configure(wraplength=objetivo)
        label.master.bind("<Configure>", ajustar_al_marco, add="+")
        label.after_idle(ajustar_al_marco)
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
    columna_separador = (num_cols - 1 if separador is True else separador) if separador is not False and separador is not None else None
    hueco = round(16 * esc) if columna_separador is not None and 0 < columna_separador < num_cols else 0
    y0 = y_base + round(4 * esc)

    anchos = [
        max([medir(textos[i][j]) for i in range(num_filas)] + [medir("00")]) + 2 * relleno
        for j in range(num_cols)
    ]
    xs = []
    x = x_base + margen
    for j in range(num_cols):
        if hueco and j == columna_separador:
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
        x_sep = xs[columna_separador] - hueco / 2
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


def color_de_fondo(widget):
    """Color de fondo efectivo de un widget (sigue subiendo mientras el fondo sea transparente)."""
    while widget is not None:
        try:
            color = widget.cget("fg_color")
        except (ValueError, tk.TclError, AttributeError):
            try:
                return widget.cget("bg")
            except tk.TclError:
                break
        if color not in (None, "transparent"):
            return resolver_color(color)
        widget = getattr(widget, "master", None)
    return resolver_color(PALETA["fondo"])


class _FichasCanvas(tk.Canvas):
    """
    Base para controles dibujados en un solo Canvas (zonas clicables con hover).
    Es mucho mas liviano que varios CTkButton: en macOS cada widget extra encarece
    el dibujado de toda la pagina.
    """

    def __init__(self, parent):
        self._esc = escala_de(parent)
        super().__init__(parent, bg=color_de_fondo(parent), highlightthickness=0, bd=0, width=10, height=10)
        self._zonas = {}
        self._hover = None
        self.bind("<Motion>", self._mover)
        self.bind("<Leave>", lambda _e: self._resaltar(None))
        self.bind("<Button-1>", self._clic)

    def _zona_en(self, x, y):
        for clave, (x1, y1, x2, y2, _fondo, activa) in self._zonas.items():
            if activa and x1 <= x <= x2 and y1 <= y <= y2:
                return clave
        return None

    def _mover(self, evento):
        self._resaltar(self._zona_en(evento.x, evento.y))

    def _resaltar(self, clave):
        if clave == self._hover:
            return
        self._hover = clave
        for k, (_x1, _y1, _x2, _y2, fondo, _activa) in self._zonas.items():
            self.itemconfigure(fondo, fill=resolver_color(PALETA["secundario_hover"] if k == clave
                                                          else self._color_reposo(k)))
        self.configure(cursor="hand2" if clave is not None else "")

    def _color_reposo(self, _clave):
        return PALETA["entrada"]

    def _clic(self, evento):
        clave = self._zona_en(evento.x, evento.y)
        if clave is not None:
            self._activar(clave)

    def _activar(self, clave):
        raise NotImplementedError


class Contador(_FichasCanvas):
    """Selector numerico  −  3  +  con limites, dibujado en un solo Canvas."""

    def __init__(self, parent, texto, valor, minimo, maximo, al_cambiar=None, en_linea=False):
        super().__init__(parent)
        self.texto = texto
        self.minimo = minimo
        self.maximo = maximo
        self.valor = valor
        self.al_cambiar = al_cambiar
        self.en_linea = en_linea
        self._dibujar()

    def _dibujar(self):
        esc = self._esc
        self.delete("all")
        px_rotulo = round(11 * esc)
        ancho_rotulo = _fuente_medida(self, px_rotulo, True, FAMILIA).measure(self.texto)
        ancho, alto = round(104 * esc), round(34 * esc)
        if self.en_linea:
            x0, y0 = ancho_rotulo + round(6 * esc), 0
            self.create_text(0, alto / 2, text=self.texto, anchor="w", fill=resolver_color(PALETA["texto_3"]),
                             font=(FAMILIA, -px_rotulo, "bold"))
        else:
            x0, y0 = 0, round(18 * esc)
            self.create_text(0, 0, text=self.texto, anchor="nw", fill=resolver_color(PALETA["texto_3"]),
                             font=(FAMILIA, -px_rotulo, "bold"))
        _rectangulo_redondeado(self, x0 + 1, y0 + 1, x0 + ancho - 1, y0 + alto - 1, round(10 * esc),
                               fill=resolver_color(PALETA["entrada"]), outline=resolver_color(PALETA["borde"]))
        margen, boton = round(3 * esc), round(30 * esc)
        self._zonas, self._signos = {}, {}
        for clave, signo, x1 in (("menos", "−", x0 + margen), ("mas", "+", x0 + ancho - margen - boton)):
            fondo = _rectangulo_redondeado(self, x1, y0 + margen, x1 + boton, y0 + alto - margen, round(8 * esc),
                                           fill=resolver_color(PALETA["entrada"]), outline="")
            self._signos[clave] = self.create_text(x1 + boton / 2, y0 + alto / 2, text=signo,
                                                   font=(FAMILIA, -round(17 * esc), "bold"))
            self._zonas[clave] = [x1, y0 + margen, x1 + boton, y0 + alto - margen, fondo, True]
        self._valor_id = self.create_text(x0 + ancho / 2, y0 + alto / 2, text=str(self.valor),
                                          fill=resolver_color(PALETA["texto"]), font=(FAMILIA, -round(13 * esc), "bold"))
        self.configure(width=max(x0 + ancho, ancho_rotulo), height=y0 + alto)
        self._actualizar_botones()

    def get(self):
        return self.valor

    def set(self, valor, notificar=False):
        valor = max(self.minimo, min(self.maximo, int(valor)))
        cambio = valor != self.valor
        self.valor = valor
        self.itemconfigure(self._valor_id, text=str(valor))
        self._actualizar_botones()
        if cambio:
            inicio = resolver_color(PALETA["primario"])
            fin = resolver_color(PALETA["texto"])
            animar(self, 450, lambda t: self.itemconfigure(self._valor_id, fill=mezclar_colores(inicio, fin, t)))
        if cambio and notificar and self.al_cambiar is not None:
            self.al_cambiar(valor)

    def cambiar(self, delta):
        self.set(self.valor + delta, notificar=True)

    def _activar(self, clave):
        self.cambiar(-1 if clave == "menos" else 1)
        self._hover = None
        self._resaltar(clave if self._zonas[clave][5] else None)

    def _actualizar_botones(self):
        for clave, activa in (("menos", self.valor > self.minimo), ("mas", self.valor < self.maximo)):
            self._zonas[clave][5] = activa
            self.itemconfigure(self._signos[clave],
                               fill=resolver_color(PALETA["primario"] if activa else PALETA["borde"]))


class BarraFichas(_FichasCanvas):
    """Fila de botones pequenos (por ejemplo los simbolos A, B, (, ᵀ, +) dibujados en un Canvas."""

    def __init__(self, parent, fichas, fuente=None):
        super().__init__(parent)
        self.fichas = list(fichas)  # [(texto, comando)]
        familia, tamano = (fuente or FUENTE_MONO)[:2]
        esc = self._esc
        px = round(tamano * esc)
        medir = _fuente_medida(self, px, False, familia).measure
        alto, separacion, x = round(32 * esc), round(3 * esc), 0
        for indice, (texto, _comando) in enumerate(self.fichas):
            ancho = max(round(30 * esc), medir(texto) + round(16 * esc))
            fondo = _rectangulo_redondeado(self, x, 1, x + ancho, alto - 1, round(8 * esc),
                                           fill=resolver_color(PALETA["secundario"]), outline="")
            self.create_text(x + ancho / 2, alto / 2, text=texto, fill=resolver_color(PALETA["texto"]),
                             font=(familia, -px))
            self._zonas[indice] = [x, 1, x + ancho, alto - 1, fondo, True]
            x += ancho + separacion
        self.configure(width=x - separacion, height=alto)

    def _color_reposo(self, _clave):
        return PALETA["secundario"]

    def _activar(self, clave):
        self.fichas[clave][1]()


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

        # Encabezados como tk.Label (no CTkLabel): son muchos y asi la pagina se dibuja mas rapido.
        fondo = color_de_fondo(self)
        fuente = (FAMILIA, -round(11 * escala_de(self)), "bold")
        for j, texto in enumerate(encabezados):
            tk.Label(self, text=texto, font=fuente, bg=fondo, fg=resolver_color(PALETA["primario"])).grid(
                row=0, column=columna_grid(j), pady=(0, 4))

        for i in range(filas):
            if encabezados_fila:
                tk.Label(self, text=encabezados_fila[i], font=fuente, bg=fondo, width=3,
                         fg=resolver_color(PALETA["texto_3"])).grid(row=i + 1, column=0, padx=(0, 6))
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

    def __init__(self, parent, fondo, texto_vacio, constructor=None):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.texto_vacio = texto_vacio
        # constructor(parent, pasos, indice, detallado) -> widget de la tarjeta (por defecto, Gauss-Jordan)
        self.constructor = constructor or (
            lambda contenedor, pasos, indice, detallado: TarjetaPaso(contenedor, pasos, indice, detallado=detallado))
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
                lambda p, i=i: self.constructor(p, self.pasos, i, False).pack(fill="x", padx=2, pady=(0, 12))
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
            tarjeta = self.constructor(parent, self.pasos, self.indice, True)
            tarjeta.pack(fill="x", padx=2, pady=(0, 12))
            if hasattr(tarjeta, "destello"):
                tarjeta.destello()
            else:
                destello(tarjeta)

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

    def __init__(self, parent, titulo, detalle, correcto, construir, abierto=False, estado=None):
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
        # estado: (texto, color) propio; por defecto «Se cumple / No se cumple» segun correcto.
        texto_estado, color_estado = estado if estado is not None else (
            "✓ Se cumple" if correcto else "✕ No se cumple", "exito" if correcto else "error")
        if texto_estado:
            etiqueta(cabecera, texto_estado, FUENTE_PEQUENA_NEGRITA, color_estado).pack(side="right", padx=(10, 4))

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


def constructores_solucion(resultado, simbolo="x", incluir_verificacion=True):
    """Tarjetas comunes: solucion (unica/parametrica/ninguna) y verificacion."""
    lista = []
    if resultado["solucion"] is not None:
        lista.append(lambda p: tarjeta_solucion_unica(p, resultado["solucion"], resultado["nombres_variables"], simbolo))
    elif resultado["expresiones"] is not None:
        lista.append(lambda p: tarjeta_solucion_parametrica(p, resultado, simbolo))
    else:
        lista.append(lambda p: tarjeta_inconsistente(p, resultado))
    if incluir_verificacion and resultado["verificacion"] is not None:
        lista.append(lambda p: tarjeta_verificacion(p, resultado["verificacion"], resultado["expresiones"] is not None))
    general = resultado.get("verificacion_general")
    if incluir_verificacion and general:
        mensajes = [f"Solución particular: Ap = {general['particular']['producto']}; "
                    f"b = {general['particular']['esperado']}."]
        mensajes += [f"Dirección {d['parametro']}: A·{d['vector']} = {d['producto']}; "
                     f"{'es el vector cero' if d['correcto'] else 'no es el vector cero'}." for d in general['direcciones']]
        mensajes.append(general['conclusion'])
        lista.append(lambda p: tarjeta_mensajes(p, "Verificación de toda la familia paramétrica", mensajes,
                                               "exito" if general['correcto'] else "error"))
    return lista


def cuerpo_etapa(parent, paso, detallado=False):
    """Representa datos estructurados con las matrices y secciones existentes."""
    if paso["explicacion"]:
        etiqueta(parent, paso["explicacion"], FUENTE_NORMAL, "texto_2", ajustar=40).pack(anchor="w", padx=16, pady=(0, 6))
    if paso["formula"]:
        etiqueta(parent, paso["formula"], FUENTE_NEGRITA, "primario", ajustar=40).pack(anchor="w", padx=16, pady=(0, 8))
    for condicion in paso["condiciones"]:
        etiqueta(parent, ("✓ " if condicion["cumple"] else "✗ ") + condicion["texto"], FUENTE_NORMAL,
                 "exito" if condicion["cumple"] else "error", ajustar=40).pack(anchor="w", padx=16, pady=(0, 4))
    for dato in paso["valores"]:
        nombre, numero = dato["nombre"], dato["valor"]
        if isinstance(numero, list):
            matriz = numero if numero and isinstance(numero[0], list) else [[v] for v in numero]
            if not matriz or not matriz[0]:
                etiqueta(parent, nombre + ": matriz vacía", FUENTE_NORMAL, ajustar=40).pack(anchor="w", padx=16)
                continue
            cabecera = ctk.CTkFrame(parent, fg_color="transparent")
            cabecera.pack(anchor="w", padx=16, pady=(6, 2))
            etiqueta(cabecera, nombre, FUENTE_NEGRITA, "texto").pack(side="left")
            chip(cabecera, f"{len(matriz)}×{len(matriz[0])}", "panel", "primario").pack(side="left", padx=8)
            dibujar_matriz(parent, matriz, separador=dato.get("separador"), pivotes=dato.get("pivotes", []),
                           filas=dato.get("filas", [])).pack(anchor="w", padx=12, pady=(0, 8))
        else:
            etiqueta(parent, f"{nombre} = {formatear_numero(numero)}", (FAMILIA_MONO, 17, "bold"), "primario", ajustar=40).pack(anchor="w", padx=16, pady=6)

    def lineas(marco):
        for linea in paso["calculos"]:
            etiqueta(marco, linea, FUENTE_MONO, "texto_2", ajustar=40).pack(anchor="w", padx=16, pady=2)
    if len(paso["calculos"]) > 8:
        SeccionPlegable(parent, "Cálculo de cada entrada", f"{len(paso['calculos'])} cálculos", True, lineas,
                        abierto=detallado, estado=("Ver detalle", "primario")).pack(fill="x", padx=12, pady=(4, 8))
    else:
        lineas(parent)
    if paso["subpasos"]:
        def desarrollar(marco):
            for i in range(len(paso["subpasos"])):
                tarjeta_etapa(marco, paso["subpasos"], i, detallado).pack(fill="x", padx=4, pady=(0, 8))
        SeccionPlegable(parent, "Desarrollar el cálculo", "Operaciones intermedias", True, desarrollar,
                        abierto=detallado, estado=("Ver pasos", "primario")).pack(fill="x", padx=12, pady=(6, 8))
    if paso["conclusion"]:
        etiqueta(parent, paso["conclusion"], FUENTE_NEGRITA,
                 "error" if paso["conclusion"].startswith("No se cumple") else "exito", ajustar=40).pack(anchor="w", padx=16, pady=(6, 8))


def tarjeta_etapa(parent, pasos, indice, detallado=False):
    """Tarjeta reutilizable para PanelPasos; no mezcla las tres vistas."""
    paso = pasos[indice]
    tarjeta = crear_tarjeta(parent, f"Paso {indice+1} — {paso['titulo']}", fondo=PALETA["panel_2"])
    cuerpo_etapa(tarjeta, paso, detallado)
    ctk.CTkFrame(tarjeta, fg_color="transparent", height=8).pack()
    return tarjeta


def constructores_etapas(etapas):
    return [lambda p, i=i: tarjeta_etapa(p, etapas, i).pack(fill="x", padx=2, pady=(0, 12)) for i in range(len(etapas))]


def constructores_chequeo(informe):
    if informe.get("aplicable") is False:
        return [lambda p: tarjeta_mensajes(p, "No hay resultado que verificar", [informe["motivo"]], "advertencia"),
                *constructores_etapas(informe["etapas"])]
    correcto = informe["correcto"]
    return [lambda p: tarjeta_estado(p, "Verificación superada" if correcto else "Verificación con diferencias",
                                     "Comprobación exacta con los datos originales; el detalle aparece a continuación.",
                                     PALETA["exito"] if correcto else PALETA["error"], "✓" if correcto else "✗"),
            *constructores_etapas(informe["etapas"])]


def constructores_informe(informe):
    """Respuesta breve y prominente; los cálculos pertenecen a las otras pestañas."""
    lista = [lambda p: tarjeta_estado(p, informe["titulo"], informe["conclusion"],
             PALETA["exito"] if informe["definido"] else PALETA["advertencia"], "✓" if informe["definido"] else "!")]
    if informe.get("datos_resultado"):
        datos_originales = informe["datos_resultado"]
        lista.append(lambda p: cuerpo_etapa(tarjeta_seccion(p, "Datos y operación"), datos_originales))
    if informe["resultado"] is not None:
        datos = didactica.etapa("Respuesta final", valores=[didactica.valor("Resultado", informe["resultado"])])
        lista.append(lambda p: cuerpo_etapa(tarjeta_seccion(p, "Respuesta final"), datos))
    if informe.get("lados"):
        datos = didactica.comparar(informe["lados"][0]["resultado"], informe["lados"][1]["resultado"])
        datos["calculos"] = []
        lista.append(lambda p: cuerpo_etapa(tarjeta_seccion(p, "Los dos lados"), datos))
    if informe.get("teoria"):
        lista.append(lambda p: cuerpo_etapa(tarjeta_seccion(p, "Demostración general"), informe["teoria"]))
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
        etiqueta(encabezado, self.titulo, FUENTE_TITULO, "texto", ajustar=12).pack(anchor="w")
        self._subrayado = ctk.CTkFrame(encabezado, fg_color=PALETA["primario"], width=1, height=3, corner_radius=2)
        self._subrayado.pack(anchor="w", pady=(6, 6))
        etiqueta(encabezado, self.subtitulo, FUENTE_SUBTITULO, "texto_2", ajustar=12).pack(anchor="w")

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
    es_combinacion = False
    es_independencia = False

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
        pestana_verificacion = self.pestanas.add("Verificación")

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
        self.area_verificacion = AreaDesplazable(pestana_verificacion, PALETA["panel"])
        self.area_verificacion.pack(fill="both", expand=True)

    def construir_entradas(self, parent):
        self.matriz = MatrizEntrada(parent, al_cambiar=self._al_cambiar_datos)
        self.matriz.pack(anchor="w", padx=4, pady=4)

    def crear_procedimiento(self, pestana):
        self.panel_pasos = PanelPasos(pestana, PALETA["panel"], self.vacio_pasos, constructor=tarjeta_etapa)
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
            self.panel_pasos.mostrar_placeholder("Los datos cambiaron: vuelve a resolver para actualizar el procedimiento.")
            self.area_verificacion.llenar([lambda p: placeholder(p, "✓", "Los datos cambiaron: vuelve a resolver para verificar los nuevos datos.")])

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
        self.area_verificacion.llenar([lambda p: placeholder(p, "✓", "Aquí se comprobará el resultado con los datos originales.")])

    def procedimiento_vacio(self):
        self.panel_pasos.mostrar_placeholder()

    def resolver(self):
        try:
            datos = self.leer_datos()
        except ValueError as error:
            self.mostrar_vacio()
            self.area_resultado.llenar([lambda p, texto=str(error): tarjeta_mensajes(p, "Datos no válidos", [texto], "error")])
            self.app.notificar(str(error), "error")
            return
        try:
            resultado = self.calcular(datos)
        except Exception as error:
            self.mostrar_vacio()
            self.area_resultado.llenar([lambda p, texto=str(error): tarjeta_mensajes(p, "No se puede realizar la operación", [texto], "error")])
            self.app.notificar(f"No se pudo resolver: {error}", "error")
            return

        self.resultado = resultado
        self.aviso.grid_remove()
        constructores = self.construir_resultado(resultado)
        if "nombres_variables" in resultado:
            nombres = resultado["nombres_variables"]
            constructores.append(lambda p: tarjeta_mensajes(p, "Variables y parámetros", [
                "Básicas: " + (", ".join(nombres[i] for i in resultado["variables_basicas"]) or "ninguna"),
                "Libres: " + (", ".join(nombres[i] for i in resultado["variables_libres"]) or "ninguna"),
                "Parámetros: " + (", ".join(resultado["parametros"].values()) or "ninguno")], "primario"))
        texto = self.texto_copiar(resultado)
        if texto:
            constructores.append(lambda p: fila_copiar(p, self.app, texto))
        self.area_resultado.llenar(constructores, retardo=80)
        self.mostrar_procedimiento(resultado)
        self.mostrar_verificacion(resultado)
        self.pestanas.set("Resultado")
        mensaje, tipo = self.mensaje_resuelto(resultado)
        self.app.notificar(mensaje, tipo)

    def calcular(self, datos):
        raise NotImplementedError

    def construir_resultado(self, resultado):
        raise NotImplementedError

    def mostrar_procedimiento(self, resultado):
        self.panel_pasos.mostrar_pasos(didactica.procedimiento_sistema(resultado, self.es_combinacion, self.es_independencia))

    def mostrar_verificacion(self, resultado):
        informe = didactica.verificacion_sistema(resultado, self.es_combinacion, self.es_independencia)
        self.area_verificacion.llenar(constructores_chequeo(informe), retardo=45)

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
        ] + constructores_solucion(resultado, incluir_verificacion=False)


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
        ] + constructores_solucion(resultado, incluir_verificacion=False)

        return constructores


class PaginaCombinaciones(PaginaSistema):
    es_combinacion = True
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
        return constructores + constructores_solucion(resultado, simbolo="c", incluir_verificacion=False)

    @staticmethod
    def _tarjeta_combinacion(parent, titulo, coeficientes, vectores, simbolos, w):
        tarjeta = tarjeta_seccion(parent, titulo)
        etiqueta(tarjeta, f"w = {formatear_combinacion_lineal(coeficientes, simbolos)}",
                 (FAMILIA_MONO, 16, "bold"), "primario").pack(anchor="w", padx=16)
        dibujar_expresion(tarjeta, partes_combinacion(coeficientes, vectores, w)).pack(
            anchor="w", padx=14, pady=(6, 16))
        return tarjeta


class PaginaIndependencia(PaginaSistema):
    es_independencia = True
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
        cumple = self._todo_se_cumple(datos)
        respuesta = didactica.etapa("Productos", valores=[didactica.valor("Av", datos["Av"])] +
                                   ([didactica.valor("Au", datos["Au"])] if datos["u"] is not None else []))
        mensajes = ["A(cv) = c(Av): " + ("Se cumple" if datos["propiedad"] else "No se cumple")]
        if datos["u"] is not None:
            mensajes.append("A(u+v) = Au+Av: " + ("Se cumple" if datos["propiedad_suma"] else "No se cumple"))
        return [lambda p: tarjeta_estado(p, "Producto Av calculado", "Resultado exacto; el cálculo de ambos lados está en Procedimiento.",
                                        PALETA["exito"] if cumple else PALETA["error"], "✓" if cumple else "✗"),
                *constructores_etapas([respuesta]), lambda p: tarjeta_mensajes(p, "Propiedades", mensajes, "primario")]

    def mostrar_procedimiento(self, datos):
        self.informe_av = didactica.informe_propiedades_av(datos)
        self.panel_pasos.mostrar_pasos(self.informe_av["procedimiento"])

    def mostrar_verificacion(self, datos):
        self.area_verificacion.llenar(constructores_chequeo(self.informe_av["verificacion"]), retardo=45)

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


# --- Tarjetas del modulo de matrices ---------------------------------------------

COLORES_OPERACION_MATRICIAL = {
    "suma": "exito", "resta": "exito", "producto": "primario", "escalar": "advertencia",
    "transpuesta": "texto_3", "aritmetica": "texto_3", "datos": "texto_3", "respuesta": "primario",
}


def _superindice_dimension(dimension):
    return str(dimension[0]).translate(SUPERINDICES) + "ˣ" + str(dimension[1]).translate(SUPERINDICES)


def dibujar_valores(parent, elementos, tamano=13):
    """Dibuja en una fila pares (etiqueta, valor): las matrices como matriz y los numeros como texto."""
    partes = []
    for k, (nombre, valor) in enumerate(elementos):
        prefijo = ("   " if k else "") + f"{nombre} ="
        if isinstance(valor, list):
            partes += [prefijo, valor]
        else:
            partes.append(f"{prefijo} {formatear_numero(Fraction(valor))}")
    return dibujar_expresion(parent, partes, tamano=tamano)


def _lineas(parent, lineas, color="texto_2", fuente=None, ajustar=40, pady=(0, 0)):
    for linea in lineas:
        etiqueta(parent, linea, fuente or FUENTE_NORMAL, color, ajustar=ajustar).pack(anchor="w", pady=pady)


def _subtitulo_seccion(parent, texto):
    etiqueta(parent, texto, FUENTE_PEQUENA_NEGRITA, "texto_3").pack(anchor="w", pady=(10, 2))


def tarjeta_paso_matricial(parent, pasos, indice, detallado=False):
    """Tarjeta de un paso del procedimiento con matrices (datos, operacion intermedia o respuesta)."""
    paso = pasos[indice]
    tipo = paso["tipo"]
    if tipo == "didactica":
        return tarjeta_etapa(parent, [paso["etapa"]], 0, detallado)
    if tipo == "seccion":
        marco = ctk.CTkFrame(parent, fg_color="transparent")
        etiqueta(marco, paso["titulo"], FUENTE_SECCION, "primario", ajustar=20).pack(anchor="w", pady=(6, 0))
        if paso.get("detalle"):
            etiqueta(marco, paso["detalle"], FUENTE_PEQUENA, "texto_3", ajustar=20).pack(anchor="w")
        return marco

    falla = tipo not in ("datos", "respuesta") and not paso["condicion"]["cumple"]
    tarjeta = ctk.CTkFrame(parent, fg_color=PALETA["panel_2"], corner_radius=12, border_width=2 if falla else 1,
                           border_color=PALETA["error"] if falla else PALETA["borde"])
    cabecera = ctk.CTkFrame(tarjeta, fg_color="transparent")
    cabecera.pack(fill="x", padx=14, pady=(12, 6))
    prefijo = f"{paso['lado']} · " if paso.get("lado") else ""
    chip(cabecera, f"{prefijo}Paso {paso['numero']}", "primario", TEXTO_SOBRE_PRIMARIO).pack(side="left")
    chip(cabecera, TIPOS_OPERACION_MATRICIAL.get(tipo, tipo), "panel",
         "error" if falla else COLORES_OPERACION_MATRICIAL.get(tipo, "primario")).pack(side="left", padx=(8, 0))
    etiqueta(cabecera, paso["titulo"], FUENTE_NEGRITA, "texto", ajustar=230).pack(side="left", padx=(10, 0))

    cuerpo = ctk.CTkFrame(tarjeta, fg_color="transparent")
    cuerpo.pack(fill="x", padx=16, pady=(0, 12))
    if tipo == "datos":
        _cuerpo_datos(cuerpo, paso)
    elif tipo == "respuesta":
        _cuerpo_respuesta(cuerpo, paso)
    else:
        _cuerpo_operacion(cuerpo, paso, detallado)
    if not falla:
        efecto_hover(tarjeta)
    return tarjeta


def _cuerpo_datos(cuerpo, paso):
    etiqueta(cuerpo, f"Expresión:  {paso['expresion']}", (FAMILIA_MONO, 15, "bold"), "primario", ajustar=40).pack(anchor="w")
    etiqueta(cuerpo, f"Se calcula como:  {paso['interpretacion']}", FUENTE_MONO, "texto_2", ajustar=40).pack(
        anchor="w", pady=(2, 0))
    if paso["matrices"]:
        _subtitulo_seccion(cuerpo, "MATRICES Y DIMENSIONES")
        rejilla = ctk.CTkFrame(cuerpo, fg_color="transparent")
        rejilla.pack(anchor="w")
        for k, (nombre, M) in enumerate(paso["matrices"]):
            celda = ctk.CTkFrame(rejilla, fg_color="transparent")
            celda.grid(row=k // 2, column=k % 2, sticky="nw", padx=(0, 18), pady=(0, 6))
            dimension = (len(M), len(M[0]))
            etiqueta(celda, f"{nombre} ∈ ℝ{_superindice_dimension(dimension)}  ({formatear_dimension(dimension)})",
                     FUENTE_PEQUENA_NEGRITA, "texto").pack(anchor="w")
            dibujar_valores(celda, [(nombre, M)]).pack(anchor="w")
    if paso["escalares"]:
        etiqueta(cuerpo, "Escalares:  " + ",  ".join(f"{k} = {formatear_numero(v)}" for k, v in paso["escalares"].items()),
                 FUENTE_MONO, "texto").pack(anchor="w", pady=(6, 0))
    if paso["condiciones"]:
        _subtitulo_seccion(cuerpo, "CONDICIONES DE DIMENSIÓN (EN EL ORDEN DE CÁLCULO)")
        for k, condicion in enumerate(paso["condiciones"], start=1):
            marca = "✓" if condicion["cumple"] else "✗"
            etiqueta(cuerpo, f"{k}. {marca}  {condicion['operacion']}:  {condicion['requisito']}", FUENTE_MONO,
                     "exito" if condicion["cumple"] else "error", ajustar=40).pack(anchor="w")
        if not paso["condiciones"][-1]["cumple"]:
            etiqueta(cuerpo, "Las operaciones siguientes no se revisan porque esta no está definida.",
                     FUENTE_PEQUENA, "texto_3", ajustar=40).pack(anchor="w")
    _subtitulo_seccion(cuerpo, "PRIMERA OPERACIÓN")
    etiqueta(cuerpo, paso["primera"], FUENTE_NORMAL, "texto_2", ajustar=40).pack(anchor="w")
    if paso["propiedad"]:
        nombre, enunciado = paso["propiedad"]
        _subtitulo_seccion(cuerpo, "PROPIEDAD QUE SE USARÁ PARA VERIFICAR")
        etiqueta(cuerpo, f"{nombre}:  {enunciado}", FUENTE_NORMAL, "texto_2", ajustar=40).pack(anchor="w")


def _cuerpo_operacion(cuerpo, paso, detallado):
    condicion = paso["condicion"]
    etiqueta(cuerpo, ("✓  " if condicion["cumple"] else "✗  ") + "Condición: " + condicion["texto"],
             FUENTE_PEQUENA_NEGRITA, "exito" if condicion["cumple"] else "error", ajustar=40).pack(anchor="w")
    if not condicion["cumple"]:
        etiqueta(cuerpo, paso["descripcion"], FUENTE_NORMAL, "error", ajustar=40).pack(anchor="w", pady=(6, 8))
        dibujar_valores(cuerpo, paso["operandos"]).pack(anchor="w")
        for i in range(len(paso.get("etapas", []))):
            tarjeta_etapa(cuerpo, paso["etapas"], i, detallado).pack(fill="x", pady=6)
        etiqueta(cuerpo, paso["siguiente"], FUENTE_PEQUENA_NEGRITA, "texto_3", ajustar=40).pack(anchor="w", pady=(8, 0))
        return
    etiqueta(cuerpo, "Regla:  " + paso["regla"], FUENTE_MONO, "texto_2", ajustar=40).pack(anchor="w", pady=(6, 0))
    etiqueta(cuerpo, paso["descripcion"], FUENTE_NORMAL, "texto_2", ajustar=40).pack(anchor="w", pady=(4, 8))
    _subtitulo_seccion(cuerpo, "OPERANDOS")
    dibujar_valores(cuerpo, paso["operandos"]).pack(anchor="w")
    for linea in paso["extra"]:
        etiqueta(cuerpo, linea, FUENTE_MONO, "texto_3", ajustar=40).pack(anchor="w")
    for i in range(len(paso.get("etapas", []))):
        tarjeta_etapa(cuerpo, paso["etapas"], i, detallado).pack(fill="x", pady=6)
    _subtitulo_seccion(cuerpo, "RESULTADO DE ESTE PASO")
    fila = ctk.CTkFrame(cuerpo, fg_color="transparent")
    fila.pack(anchor="w")
    dibujar_valores(fila, [(paso["expresion"], paso["resultado"])]).pack(side="left")
    if paso["dimension"]:
        chip(fila, formatear_dimension(paso["dimension"]), "panel", "primario").pack(side="left", padx=(10, 0))

    entradas = paso["entradas"]
    if entradas:
        def construir(marco):
            for entrada in entradas:
                etiqueta(marco, "\n".join(entrada["lineas"]), FUENTE_MONO, "texto_2", ajustar=80).pack(
                    anchor="w", pady=(0, 4))
        SeccionPlegable(cuerpo, "Cálculo de cada entrada", _plural(len(entradas), "entrada", "entradas"), True,
                        construir, abierto=detallado or len(entradas) <= 4, estado=("", "texto_3")).pack(
            fill="x", pady=(10, 0))
    for advertencia in paso["advertencias"]:
        etiqueta(cuerpo, "⚠  " + advertencia, FUENTE_PEQUENA, "advertencia", ajustar=40).pack(anchor="w", pady=(6, 0))
    etiqueta(cuerpo, "Siguiente:  " + paso["siguiente"], FUENTE_PEQUENA_NEGRITA, "texto_3", ajustar=40).pack(
        anchor="w", pady=(8, 0))


def _cuerpo_respuesta(cuerpo, paso):
    etiqueta(cuerpo, f"Expresión original:  {paso['expresion']}", FUENTE_MONO, "texto", ajustar=40).pack(anchor="w")
    fila = ctk.CTkFrame(cuerpo, fg_color="transparent")
    fila.pack(anchor="w", pady=(6, 0))
    dibujar_valores(fila, [(paso["expresion"], paso["resultado"])]).pack(side="left")
    if paso["dimension"]:
        chip(fila, f"matriz {formatear_dimension(paso['dimension'])}", "panel", "primario").pack(side="left", padx=(10, 0))
    if paso["orden"]:
        _subtitulo_seccion(cuerpo, "ORDEN DE LAS OPERACIONES")
        _lineas(cuerpo, [f"{k}. {expresion}" for k, expresion in enumerate(paso["orden"], start=1)], fuente=FUENTE_MONO)
        _subtitulo_seccion(cuerpo, "REGLAS UTILIZADAS")
        _lineas(cuerpo, [f"• {regla}" for regla in paso["definiciones"]])
    if paso["propiedad"]:
        _subtitulo_seccion(cuerpo, "PROPIEDAD USADA EN LA VERIFICACIÓN")
        etiqueta(cuerpo, f"{paso['propiedad'][0]}:  {paso['propiedad'][1]}", FUENTE_NORMAL, "texto_2", ajustar=40).pack(anchor="w")
    _subtitulo_seccion(cuerpo, "CONCLUSIÓN")
    etiqueta(cuerpo, paso["conclusion"], FUENTE_NORMAL, "texto", ajustar=40).pack(anchor="w")


def _texto_comparacion(comparacion):
    """(linea, correcta) que explican una comparacion: dimensiones, entradas que coinciden y diferencias."""
    di, dd = comparacion["dimensiones_izquierda"], comparacion["dimensiones_derecha"]
    if di is None:
        return [(("✓ " if comparacion["coinciden"] else "✕ ") + comparacion["conclusion"], comparacion["coinciden"])]
    lineas = [(f"{'✓' if di == dd else '✕'} Dimensiones: {formatear_dimension(di)} y {formatear_dimension(dd)} "
               + ("coinciden" if di == dd else "no coinciden"), di == dd)]
    if di == dd:
        total = di[0] * di[1]
        iguales = total - len(comparacion["diferencias"])
        lineas.append((f"{'✓' if iguales == total else '✕'} Entradas que coinciden: {iguales} de {total}", iguales == total))
    lineas += [(linea, False) for linea in describir_diferencias(comparacion["diferencias"]) if di == dd]
    return lineas


def _tarjeta_comparacion(parent, titulo, izquierda, derecha, comparacion, nota=None):
    tarjeta = tarjeta_seccion(parent, titulo, nota)
    # Una matriz debajo de la otra: con expresiones largas no caben lado a lado.
    for elemento in (izquierda, derecha):
        dibujar_valores(tarjeta, [elemento]).pack(anchor="w", padx=14)
    for linea, correcta in _texto_comparacion(comparacion):
        etiqueta(tarjeta, linea, FUENTE_PEQUENA_NEGRITA, "exito" if correcta else "error", ajustar=44).pack(
            anchor="w", padx=16)
    detalle = didactica.comparar(izquierda[1], derecha[1])
    def entradas(marco):
        for linea in detalle["calculos"]:
            etiqueta(marco, linea, FUENTE_MONO, "texto_2", ajustar=40).pack(anchor="w", padx=12, pady=2)
    SeccionPlegable(tarjeta, "Comparación elemento por elemento", f"{len(detalle['calculos'])} posiciones", comparacion["coinciden"],
                    entradas, abierto=not comparacion["coinciden"]).pack(fill="x", padx=14, pady=(6, 8))
    etiqueta(tarjeta, detalle["conclusion"], FUENTE_NEGRITA, "exito" if comparacion["coinciden"] else "error").pack(anchor="w", padx=16, pady=6)
    ctk.CTkFrame(tarjeta, fg_color="transparent", height=10).pack()
    return tarjeta


def constructores_resultado_expresion(resolucion, informe, app):
    expresion = resolucion["expresion"]
    if resolucion["error"]:
        hechas = [p for p in resolucion["operaciones"] if p["condicion"]["cumple"]]

        def realizadas(parent):
            tarjeta = tarjeta_seccion(parent, "Operaciones realizadas antes del error")
            if not hechas:
                etiqueta(tarjeta, "Ninguna: la primera operación ya no está definida.", FUENTE_NORMAL, "texto_2",
                         ajustar=44).pack(anchor="w", padx=16, pady=(0, 14))
                return
            for paso in hechas:
                dibujar_valores(tarjeta, [(paso["expresion"], paso["resultado"])]).pack(anchor="w", padx=14)
            ctk.CTkFrame(tarjeta, fg_color="transparent", height=10).pack()

        def condiciones(parent):
            tarjeta = tarjeta_seccion(parent, "Condiciones de dimensión")
            for condicion in resolucion["condiciones"]:
                etiqueta(tarjeta, f"{'✓' if condicion['cumple'] else '✗'}  {condicion['operacion']}:  "
                                  f"{condicion['requisito']}", FUENTE_MONO,
                         "exito" if condicion["cumple"] else "error", ajustar=44).pack(anchor="w", padx=16)
            ctk.CTkFrame(tarjeta, fg_color="transparent", height=10).pack()

        return [
            lambda p: tarjeta_estado(p, f"{expresion} no está definida", resolucion["error"], PALETA["error"], "✕"),
            condiciones, realizadas,
        ]

    resultado, dimension = resolucion["resultado"], resolucion["dimension"]
    correcto = informe["correcto"]
    titulo = f"{expresion} = matriz {formatear_dimension(dimension)}" if dimension else \
        f"{expresion} = {formatear_numero(resultado)}"
    descripcion = ("Verificación superada: cada operación intermedia y el resultado final se recalcularon por "
                   "caminos independientes y coinciden." if correcto else
                   "La verificación encontró diferencias: revisa la pestaña Verificación.")
    respuesta = resolucion["pasos"][-1]

    def resultado_final(parent):
        tarjeta = tarjeta_seccion(parent, "Resultado")
        fila = ctk.CTkFrame(tarjeta, fg_color="transparent")
        fila.pack(anchor="w", padx=14, pady=(0, 14))
        dibujar_valores(fila, [(expresion, resultado)], tamano=14).pack(side="left")
        if dimension:
            chip(fila, formatear_dimension(dimension), "panel", "primario").pack(side="left", padx=(10, 0))

    def conclusion(parent):
        tarjeta = tarjeta_seccion(parent, "Conclusión")
        etiqueta(tarjeta, respuesta["conclusion"], FUENTE_NORMAL, "texto", ajustar=44).pack(anchor="w", padx=16)
        etiqueta(tarjeta, ALCANCE_VERIFICACION, FUENTE_PEQUENA, "texto_3", ajustar=44).pack(anchor="w", padx=16, pady=(6, 14))

    texto_copia = "\n".join([
        f"Expresión: {expresion}",
        f"Se calcula como: {resolucion['interpretacion']}",
        "Orden: " + " → ".join(p["expresion"] for p in resolucion["operaciones"]),
        f"Resultado ({formatear_dimension(dimension)}):" if dimension else f"Resultado: {formatear_numero(resultado)}",
        matriz_a_texto(resultado, aumentada=False) if dimension else "",
        f"Verificación: {'superada' if correcto else 'con diferencias'}",
    ])
    return [
        lambda p: tarjeta_estado(p, titulo, descripcion, PALETA["exito"] if correcto else PALETA["error"],
                                 "✓" if correcto else "✕"),
        resultado_final, conclusion,
        lambda p: fila_copiar(p, app, texto_copia),
    ]


def constructores_verificacion(resolucion, informe):
    if not informe["aplicable"]:
        return [
            lambda p: tarjeta_estado(p, "No hay resultado que verificar", informe["motivo"], PALETA["error"], "✕"),
            lambda p: tarjeta_mensajes(p, "¿Qué se revisó?", [
                "Se revisaron las dimensiones de cada operación en el orden de cálculo; la operación marcada con ✗ "
                "no está definida, así que no existe un resultado que comprobar."], "error"),
        ]
    correcto = informe["correcto"]
    lista = [lambda p: tarjeta_estado(
        p, "Verificación superada" if correcto else "Se encontraron diferencias",
        "Todas las comprobaciones coinciden en dimensiones y en cada entrada." if correcto else
        "Al menos una comprobación no coincide: revisa los detalles marcados con ✕.",
        PALETA["exito"] if correcto else PALETA["error"], "✓" if correcto else "✕")]

    def por_paso(parent):
        tarjeta = tarjeta_seccion(parent, "1. Cada operación intermedia",
                                  "Cada resultado se recalcula desde sus propios operandos con un método independiente "
                                  "y se compara entrada por entrada.")
        if not informe["pasos"]:
            etiqueta(tarjeta, "No hay operaciones intermedias.", FUENTE_NORMAL, "texto_2").pack(anchor="w", padx=16, pady=(0, 14))
            return
        for chequeo in informe["pasos"]:
            def cuerpo(marco, c=chequeo):
                lineas = [f"Método: {c['metodo']}"]
                if c["dimension_esperada"]:
                    lineas.append(f"Dimensión esperada {formatear_dimension(c['dimension_esperada'])} · obtenida "
                                  f"{formatear_dimension(c['dimension_obtenida']) if c['dimension_obtenida'] else '—'}  "
                                  + ("✓" if c["dimensiones_ok"] else "✕"))
                lineas.append(f"Entradas que coinciden: {c['entradas_ok']} de {c['entradas_total']}")
                lineas += describir_diferencias(c["diferencias"])
                lineas += c.get("calculos", [])
                _lineas(marco, lineas, ajustar=80)
                for i in range(len(c.get("etapas", []))):
                    tarjeta_etapa(marco, c["etapas"], i, True).pack(fill="x", pady=6)
                tarjeta_etapa(marco, [didactica.comparar(c["obtenido"], c["esperado"], f"Comparar {c['expresion']}")], 0, True).pack(fill="x", pady=6)
            SeccionPlegable(tarjeta, f"Paso {chequeo['numero']}", chequeo["expresion"], chequeo["ok"], cuerpo,
                            abierto=not chequeo["ok"],
                            estado=(f"{'✓' if chequeo['ok'] else '✕'} {chequeo['entradas_ok']}/{chequeo['entradas_total']} "
                                    f"entradas", "exito" if chequeo["ok"] else "error")).pack(fill="x", padx=14, pady=(0, 8))
        ctk.CTkFrame(tarjeta, fg_color="transparent", height=6).pack()

    def recalculo(parent):
        global_ = informe["global"]
        nota = global_["metodo"]
        esperada = resolucion["dimension_esperada"]
        if esperada:
            nota += f" Dimensión esperada según las reglas: {formatear_dimension(esperada)}."
        _tarjeta_comparacion(parent, "2. Recálculo independiente desde los datos originales",
                             ("Procedimiento", resolucion["resultado"]), ("Recálculo", global_["esperado"]),
                             global_["comparacion"], nota)

    lista += [por_paso, recalculo]
    identidad = informe["identidad"]
    if identidad:
        def ruta(parent):
            titulo = f"3. Ruta alternativa: {identidad['nombre']}"
            if not identidad["definida"]:
                tarjeta_mensajes(parent, titulo, [f"La ruta {identidad['expresion']} no está definida: {identidad['motivo']}"])
                return
            nota = (f"Propiedad {identidad['enunciado']}. Se calcula {identidad['expresion']} desde las matrices "
                    f"originales, sin reutilizar el resultado del procedimiento, y se compara.")
            tarjeta = _tarjeta_comparacion(parent, titulo, (resolucion["expresion"], resolucion["resultado"]),
                                           (identidad["expresion"], identidad["resolucion"]["resultado"]),
                                           identidad["comparacion"], nota)
            operaciones = identidad["resolucion"]["operaciones"]

            def cuerpo(marco):
                for etiqueta_lado, r in (("Lado izquierdo", resolucion), ("Lado derecho", identidad["resolucion"])):
                    etiqueta(marco, etiqueta_lado, FUENTE_SECCION, "primario").pack(anchor="w", pady=8)
                    for k in range(len(r["pasos"])):
                        tarjeta_paso_matricial(marco, r["pasos"], k, True).pack(fill="x", pady=6)
            SeccionPlegable(tarjeta, "Cálculos de la ruta alternativa", _plural(len(operaciones), "operación", "operaciones"),
                            True, cuerpo, abierto=True, estado=("", "texto_3")).pack(fill="x", padx=14, pady=(0, 12))
        lista.append(ruta)
    lista.append(lambda p: tarjeta_mensajes(p, "Alcance de esta verificación", [
        ALCANCE_VERIFICACION,
        "Para la demostración general de una propiedad, usa el modo Propiedades: allí se muestra el argumento "
        "algebraico válido para todas las matrices de dimensiones compatibles."], "primario"))
    return lista


def constructores_resultado_propiedad(informe, al_cargar_contraejemplo):
    propiedad = informe["propiedad"]
    general, cumple = propiedad["general"], informe["cumple"]
    if general and cumple:
        estado = (propiedad["nombre"], "Se comprobó con tus matrices: ambos lados coinciden. La propiedad vale en "
                  "general por la demostración de abajo.", PALETA["exito"], "✓")
    elif general and cumple is False:
        estado = (propiedad["nombre"], "Los lados no coinciden con estas matrices.", PALETA["error"], "✕")
    elif general:
        estado = (propiedad["nombre"], "No se pudo comprobar con estas matrices (revisa las dimensiones).",
                  PALETA["advertencia"], "!")
    elif cumple is False:
        estado = (propiedad["nombre"], "Con tus matrices se obtiene un contraejemplo: la afirmación es falsa en "
                  "general.", PALETA["advertencia"], "!")
    else:
        estado = (propiedad["nombre"], "La afirmación es falsa en general; estas matrices no la contradicen, pero "
                  "el contraejemplo sí.", PALETA["advertencia"], "!")

    if informe["tipo"] == "igualdad":
        enunciado = f"{informe['lados'][0]['resolucion']['expresion']} = {informe['lados'][1]['resolucion']['expresion']}" \
            if len(informe["lados"]) >= 2 else f"{propiedad['izquierda']} = {propiedad['derecha']}"
    elif informe["tipo"] == "cancelacion":
        enunciado = "Si AB = AC, ¿se puede concluir que B = C?"
    else:
        enunciado = "Si AB = O, ¿se puede concluir que A = O o B = O?"

    def enunciado_y_condiciones(parent):
        tarjeta = tarjeta_seccion(parent, "Enunciado y condiciones")
        etiqueta(tarjeta, enunciado, (FAMILIA_MONO, 16, "bold"), "primario", ajustar=44).pack(anchor="w", padx=16)
        etiqueta(tarjeta, "Condiciones: " + propiedad["condiciones"], FUENTE_NORMAL, "texto_2", ajustar=44).pack(
            anchor="w", padx=16, pady=(4, 0))
        if informe["matrices_extra"]:
            dibujar_valores(tarjeta, list(informe["matrices_extra"].items())).pack(anchor="w", padx=14, pady=(6, 0))
        ctk.CTkFrame(tarjeta, fg_color="transparent", height=10).pack()

    lista = [lambda p: tarjeta_estado(p, *estado), enunciado_y_condiciones]
    for lado in informe["lados"]:
        def tarjeta_lado(parent, lado=lado):
            resolucion = lado["resolucion"]
            tarjeta = tarjeta_seccion(parent, f"{lado['etiqueta']}:  {resolucion['expresion']}")
            if resolucion["error"]:
                etiqueta(tarjeta, resolucion["error"], FUENTE_NORMAL, "error", ajustar=44).pack(anchor="w", padx=16, pady=(0, 14))
                return
            fila = ctk.CTkFrame(tarjeta, fg_color="transparent")
            fila.pack(anchor="w", padx=14)
            dibujar_valores(fila, [(resolucion["expresion"], resolucion["resultado"])]).pack(side="left")
            if resolucion["dimension"]:
                chip(fila, formatear_dimension(resolucion["dimension"]), "panel", "primario").pack(side="left", padx=(10, 0))
            etiqueta(tarjeta, f"Calculado con {_plural(len(resolucion['operaciones']), 'operación', 'operaciones')}; "
                              f"el detalle está en la pestaña Procedimiento.", FUENTE_PEQUENA, "texto_3", ajustar=44).pack(
                anchor="w", padx=16, pady=(4, 14))
        lista.append(tarjeta_lado)
    for comparacion in informe["comparaciones"]:
        def tarjeta_comp(parent, c=comparacion):
            nota = None
            if propiedad.get("error_comun") and c["titulo"].startswith(propiedad["error_comun"]):
                nota = ("Este cálculo muestra el error frecuente de no invertir el orden: en general "
                        f"{propiedad['error_comun']} no es igual a {propiedad['izquierda']}.")
            izquierda, _, derecha = c["titulo"].partition("  frente a  ")
            _tarjeta_comparacion(parent, f"Comparación: {izquierda} y {derecha}",
                                 (izquierda, c["comparacion"]["izquierda"]), (derecha, c["comparacion"]["derecha"]),
                                 c["comparacion"], nota)
        lista.append(tarjeta_comp)

    def conclusion(parent):
        tarjeta = tarjeta_seccion(parent, "Conclusión")
        etiqueta(tarjeta, informe["conclusion"], FUENTE_NORMAL, "texto", ajustar=44).pack(anchor="w", padx=16, pady=(0, 14))

    def teoria(parent):
        if general:
            tarjeta = tarjeta_seccion(parent, "Demostración general",
                                      "Válida para todas las matrices de dimensiones compatibles (no depende de los "
                                      "números de este ejemplo).")
            etiqueta(tarjeta, propiedad["demostracion"], FUENTE_MONO, "texto_2", ajustar=44).pack(anchor="w", padx=16, pady=(0, 14))
            return
        tarjeta = tarjeta_seccion(parent, "Advertencia")
        etiqueta(tarjeta, propiedad["advertencia"], FUENTE_NORMAL, "advertencia", ajustar=44).pack(anchor="w", padx=16)
        if propiedad.get("contraejemplo"):
            boton_secundario(tarjeta, "Cargar el contraejemplo en A, B y C",
                             lambda: al_cargar_contraejemplo(propiedad["contraejemplo"]), width=260).pack(
                anchor="w", padx=16, pady=(8, 14))
        else:
            ctk.CTkFrame(tarjeta, fg_color="transparent", height=10).pack()

    return lista + [conclusion, teoria]


def constructores_verificacion_propiedad(informe):
    lista = []
    todo_correcto = True
    no_evaluable = False
    for lado in informe["lados"]:
        resolucion = lado["resolucion"]
        verificacion = verificar_resolucion(resolucion, usar_identidades=False)
        if lado["etiqueta"] != "Error frecuente":
            no_evaluable = no_evaluable or not verificacion["aplicable"]
            todo_correcto = todo_correcto and verificacion["correcto"] and verificacion["aplicable"]
        elif verificacion["aplicable"]:
            todo_correcto = todo_correcto and verificacion["correcto"]

        def tarjeta_lado(parent, lado=lado, resolucion=resolucion, verificacion=verificacion):
            titulo = f"{lado['etiqueta']}:  {resolucion['expresion']}"
            if not verificacion["aplicable"]:
                tarjeta_mensajes(parent, titulo, [verificacion["motivo"]], "error")
                return
            lineas = [f"{'✓' if c['ok'] else '✕'}  Paso {c['numero']} · {c['expresion']}: {c['entradas_ok']} de "
                      f"{c['entradas_total']} entradas coinciden" for c in verificacion["pasos"]]
            lineas.append(f"{'✓' if verificacion['global']['ok'] else '✕'}  Recálculo independiente desde los datos "
                          f"originales")
            if verificacion["identidad"] and verificacion["identidad"]["definida"]:
                lineas.append(f"{'✓' if verificacion['identidad']['ok'] else '✕'}  Ruta alternativa "
                              f"({verificacion['identidad']['nombre']}): {verificacion['identidad']['expresion']}")
            tarjeta = tarjeta_seccion(parent, titulo)
            for linea in lineas:
                etiqueta(tarjeta, linea, FUENTE_PEQUENA_NEGRITA, "exito" if linea.startswith("✓") else "error",
                         ajustar=44).pack(anchor="w", padx=16)
            ctk.CTkFrame(tarjeta, fg_color="transparent", height=10).pack()
        lista.append(tarjeta_lado)
        if verificacion["aplicable"]:
            chequeo = didactica.comparar(resolucion["resultado"], verificacion["global"]["esperado"],
                                        lado["etiqueta"] + ": recálculo entrada por entrada")
            lista.extend(constructores_etapas([chequeo]))

    lista.insert(0, lambda p: tarjeta_estado(
        p, "Propiedad no evaluable con estos datos" if no_evaluable else "Cálculos verificados" if todo_correcto else "Hay cálculos con diferencias",
        "Cada lado se calculó por separado y cada operación se recalculó de forma independiente." if todo_correcto
        else "Algún lado no está definido: revisa las condiciones; esto no refuta el teorema." if no_evaluable
        else "Revisa los pasos marcados con ✕.", PALETA["advertencia"] if no_evaluable else PALETA["exito"] if todo_correcto else PALETA["error"],
        "✓" if todo_correcto else "✕"))
    lista.append(lambda p: tarjeta_mensajes(p, "Comprobación frente a demostración", [
        "Comparar los dos lados con tus matrices es una comprobación de un caso particular.",
        "La demostración general (en la pestaña Resultado) es la que garantiza la propiedad para todas las matrices "
        "de dimensiones compatibles; un solo ejemplo numérico nunca la demuestra."], "primario"))
    for c in informe["comparaciones"]:
        lista.extend(constructores_etapas([didactica.comparar(c["comparacion"]["izquierda"], c["comparacion"]["derecha"], c["titulo"])]))
    lista.append(lambda p: tarjeta_mensajes(p, "Conclusión de la propiedad", [informe["conclusion"]], "primario"))
    return lista


class PaginaMatrices(PaginaBase):
    """
    Operaciones con matrices y propiedades teoricas. Permite escribir o construir
    expresiones con A, B y C (sumas, restas, escalares, productos, transpuestas y
    parentesis anidados), ver cada operacion intermedia, verificar el resultado por
    caminos independientes, comprobar propiedades y estudiar contraejemplos.
    """

    titulo = "Operaciones con Matrices y Propiedades Teóricas"
    subtitulo = "Expresiones con A, B y C paso a paso, verificación independiente y propiedades teóricas"
    MODOS = ("Expresión", "Propiedades", "Contraejemplos", "Ejercicios")
    EXPRESIONES = ("A + B", "A − B", "3A", "Aᵀ", "AB", "A + B − C", "2A − 3B + C", "A(B + C)", "AB + AC",
                   "(A + B)C", "A(B − C)", "AB − AC", "(AB)ᵀ", "BᵀAᵀ", "(A + B)ᵀ", "Aᵀ + Bᵀ", "AᵀBC", "r(A + B)ᵀ")
    TOKENS = ("A", "B", "C", "(", ")", "ᵀ", "+", "−", "r")
    MATRICES_INICIALES = {"A": [[1, 2], [3, 4]], "B": [[0, 1], [-1, 2]], "C": [[2, 0], [1, -3]]}
    ESCALARES_INICIALES = {"r": "2", "s": "1/2"}
    CONTRAEJEMPLOS = {
        "no_conmutatividad": ("El producto no es conmutativo", "propiedad", "no_conmutatividad"),
        "orden_rectangular": ("AB está definido pero BA no", "expresion", "BA"),
        "cancelacion": ("La cancelación no siempre vale", "propiedad", "cancelacion"),
        "divisores_cero": ("Matrices no nulas con producto cero", "propiedad", "divisores_cero"),
    }

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.modo = "Expresión"
        self.propiedad = "distributiva_izquierda"
        self.hay_resultado = False
        self._tarea_previa = None
        self.grid_rowconfigure(2, weight=1)
        self._crear_barra()
        self._crear_contenido()
        self._cambiar_modo("Expresión")

    # --- construccion ---------------------------------------------------

    def _crear_barra(self):
        barra = crear_tarjeta(self)
        barra.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 14))
        fila = ctk.CTkFrame(barra, fg_color="transparent")
        fila.pack(fill="x", padx=18, pady=(12, 8))
        self.selector_modo = ctk.CTkSegmentedButton(
            fila, values=list(self.MODOS), command=self._cambiar_modo, font=FUENTE_PEQUENA_NEGRITA, height=32,
            fg_color=PALETA["panel_2"], selected_color=PALETA["primario"], selected_hover_color=PALETA["primario_hover"],
            unselected_color=PALETA["panel_2"], unselected_hover_color=PALETA["secundario_hover"],
            text_color=PALETA["texto"])
        self.selector_modo.pack(side="left")

        escalares = ctk.CTkFrame(fila, fg_color="transparent")
        escalares.pack(side="right")
        self.entradas_escalares = {}
        for nombre in ("r", "s"):
            etiqueta(escalares, f"{nombre} =", FUENTE_MONO, "texto_3").pack(side="left", padx=(12, 4))
            entrada = ctk.CTkEntry(escalares, width=64, height=32, justify="center", font=FUENTE_MONO, corner_radius=8,
                                   border_width=2, fg_color=PALETA["entrada"], border_color=PALETA["borde"],
                                   text_color=PALETA["texto"])
            entrada.insert(0, self.ESCALARES_INICIALES[nombre])
            entrada.pack(side="left")
            entrada.bind("<KeyRelease>", lambda _e, en=entrada: self._validar_escalar(en))
            self.entradas_escalares[nombre] = entrada

        self.fila_controles = ctk.CTkFrame(barra, fg_color="transparent")
        self.fila_controles.pack(fill="x", padx=18, pady=(0, 12))

        self.controles_expresion = ctk.CTkFrame(self.fila_controles, fg_color="transparent")
        etiqueta(self.controles_expresion, "Expresión", FUENTE_PEQUENA_NEGRITA, "texto_3").pack(side="left", padx=(0, 8))
        self.entrada_expresion = ctk.CTkEntry(
            self.controles_expresion, width=230, height=36, font=(FAMILIA_MONO, 15), corner_radius=10, border_width=2,
            fg_color=PALETA["entrada"], border_color=PALETA["borde"], text_color=PALETA["texto"])
        self.entrada_expresion.insert(0, "A(B + C)")
        self.entrada_expresion.pack(side="left")
        self.entrada_expresion.bind("<KeyRelease>", lambda e: None if e.keysym in ("Return", "KP_Enter")
                                    else self._programar_previa())
        self.entrada_expresion.bind("<Return>", lambda _e: self.resolver())
        BarraFichas(self.controles_expresion, [(t, lambda t=t: self._insertar(t)) for t in self.TOKENS]).pack(
            side="left", padx=(8, 0))
        self.boton_expresiones = boton_secundario(self.controles_expresion, "Ejemplos  ▾", self._abrir_expresiones,
                                                  width=112, height=34)
        self.boton_expresiones.pack(side="left", padx=(8, 0))
        self.menu_expresiones = self._menu()
        for expresion in self.EXPRESIONES:
            self.menu_expresiones.add_command(label=expresion, command=lambda e=expresion: self._usar_expresion(e))

        self.controles_propiedad = ctk.CTkFrame(self.fila_controles, fg_color="transparent")
        etiqueta(self.controles_propiedad, "Propiedad", FUENTE_PEQUENA_NEGRITA, "texto_3").pack(side="left", padx=(0, 8))
        self.boton_propiedad = boton_secundario(self.controles_propiedad, "", self._abrir_propiedades, width=330,
                                                height=34, anchor="w")
        self.boton_propiedad.pack(side="left")
        self.boton_contraejemplo = boton_secundario(self.controles_propiedad, "Cargar contraejemplo",
                                                    lambda: self._estudiar_contraejemplo(
                                                        PROPIEDADES_POR_CLAVE[self.propiedad]["contraejemplo"]),
                                                    width=170, height=34)
        self.menu_propiedades = self._menu()
        grupos = []
        for propiedad in PROPIEDADES_MATRICIALES:
            if propiedad["grupo"] not in grupos:
                grupos.append(propiedad["grupo"])
        for grupo in grupos:
            submenu = self._menu(self.menu_propiedades)
            for propiedad in PROPIEDADES_MATRICIALES:
                if propiedad["grupo"] == grupo:
                    submenu.add_command(label=self._texto_propiedad(propiedad),
                                        command=lambda c=propiedad["clave"]: self._usar_propiedad(c))
            self.menu_propiedades.add_cascade(label=grupo, menu=submenu)

        self.controles_info = etiqueta(self.fila_controles, "", FUENTE_PEQUENA, "texto_3", ajustar=None)

    def _menu(self, padre=None):
        return tk.Menu(padre or self, tearoff=0, font=FUENTE_NORMAL, bd=0, relief="flat",
                       bg=resolver_color(PALETA["panel_2"]), fg=resolver_color(PALETA["texto"]),
                       activebackground=resolver_color(PALETA["primario"]), activeforeground=TEXTO_SOBRE_PRIMARIO)

    @staticmethod
    def _texto_propiedad(propiedad):
        if propiedad.get("tipo", "igualdad") == "igualdad":
            return f"{propiedad['nombre']}:  {propiedad['izquierda']} = {propiedad['derecha']}"
        return propiedad["nombre"]

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
        etiqueta(cabecera, "Matrices A, B y C", FUENTE_SECCION, "texto").pack(side="left")
        chip(cabecera, "tamaño con − y +", "panel_2", "texto_3", FUENTE_PEQUENA).pack(side="right")

        self.area_datos = AreaDesplazable(self.tarjeta_datos, PALETA["panel"])
        self.area_datos.grid(row=1, column=0, sticky="nsew", padx=(14, 10), pady=(0, 8))
        self.bloques = {}
        for nombre in ("A", "B", "C"):
            self._crear_bloque(self.area_datos.interior, nombre)
        marco_previa = ctk.CTkFrame(self.area_datos.interior, fg_color=PALETA["panel_2"], corner_radius=10)
        marco_previa.pack(fill="x", anchor="w", padx=4, pady=(6, 6))
        etiqueta(marco_previa, "INTERPRETACIÓN Y DIMENSIONES", FUENTE_PEQUENA_NEGRITA, "primario").pack(
            anchor="w", padx=14, pady=(10, 4))
        self.contenido_previa = ctk.CTkFrame(marco_previa, fg_color="transparent")
        self.contenido_previa.pack(fill="x", padx=14, pady=(0, 12))

        acciones = ctk.CTkFrame(self.tarjeta_datos, fg_color="transparent")
        acciones.grid(row=2, column=0, sticky="ew", padx=18, pady=(4, 16))
        boton_primario(acciones, "Calcular y verificar", self.resolver, height=44, width=180).pack(side="left")
        boton_secundario(acciones, "⚄  Aleatorio", self.aleatorio, width=104, height=34).pack(side="left", padx=(10, 0))
        boton_secundario(acciones, "↺  Limpiar", self.limpiar, width=92, height=34).pack(side="left", padx=(8, 0))

        self.pestanas = ctk.CTkTabview(
            contenido, fg_color=PALETA["panel"], corner_radius=14, border_width=1, border_color=PALETA["borde"],
            segmented_button_fg_color=PALETA["panel_2"], segmented_button_selected_color=PALETA["primario"],
            segmented_button_selected_hover_color=PALETA["primario_hover"],
            segmented_button_unselected_color=PALETA["panel_2"],
            segmented_button_unselected_hover_color=PALETA["secundario_hover"], text_color=PALETA["texto"])
        self.pestanas.grid(row=0, column=1, sticky="nsew")
        pestana_resultado = self.pestanas.add("Resultado")
        pestana_pasos = self.pestanas.add("Procedimiento")
        pestana_verificacion = self.pestanas.add("Verificación")
        pestana_resultado.grid_columnconfigure(0, weight=1)
        pestana_resultado.grid_rowconfigure(1, weight=1)
        self.aviso = ctk.CTkLabel(
            pestana_resultado, text="⟳  Los datos cambiaron. Presiona «Calcular y verificar» para actualizar.",
            font=FUENTE_PEQUENA_NEGRITA, fg_color=PALETA["panel_2"], text_color=PALETA["advertencia"],
            corner_radius=8, height=32)
        self.area_resultado = AreaDesplazable(pestana_resultado, PALETA["panel"])
        self.area_resultado.grid(row=1, column=0, sticky="nsew")
        self.panel_pasos = PanelPasos(pestana_pasos, PALETA["panel"],
                                      "Aquí aparecerá cada operación intermedia: condición de dimensiones, regla, "
                                      "cálculo de cada entrada y resultado.", constructor=tarjeta_paso_matricial)
        self.panel_pasos.pack(fill="both", expand=True)
        self.area_verificacion = AreaDesplazable(pestana_verificacion, PALETA["panel"])
        self.area_verificacion.pack(fill="both", expand=True)

    def _crear_bloque(self, parent, nombre):
        valores = self.MATRICES_INICIALES[nombre]
        marco = ctk.CTkFrame(parent, fg_color="transparent")
        marco.pack(anchor="w", fill="x", padx=4, pady=(4, 12))
        cabecera = ctk.CTkFrame(marco, fg_color="transparent")
        cabecera.pack(anchor="w")
        chip(cabecera, nombre, "primario", TEXTO_SOBRE_PRIMARIO, (FAMILIA, 14, "bold")).pack(side="left", padx=(0, 12))
        filas = Contador(cabecera, "filas", len(valores), 1, LIMITE_DIMENSION,
                         lambda _v, n=nombre: self._redimensionar(n), en_linea=True)
        filas.pack(side="left", padx=(0, 12))
        columnas = Contador(cabecera, "columnas", len(valores[0]), 1, LIMITE_DIMENSION,
                            lambda _v, n=nombre: self._redimensionar(n), en_linea=True)
        columnas.pack(side="left")
        matriz = MatrizEntrada(marco, al_cambiar=self._al_cambiar_datos)
        matriz.pack(anchor="w", pady=(6, 0))
        self.bloques[nombre] = {"filas": filas, "columnas": columnas, "matriz": matriz}
        self._configurar_matriz(nombre, valores)

    # --- datos ---------------------------------------------------------------

    def _configurar_matriz(self, nombre, valores=None):
        bloque = self.bloques[nombre]
        filas, columnas = bloque["filas"].get(), bloque["columnas"].get()
        bloque["matriz"].configurar(filas, columnas, [str(j + 1) for j in range(columnas)],
                                    [str(i + 1) for i in range(filas)], None, valores)

    def _redimensionar(self, nombre):
        self._configurar_matriz(nombre)
        self._al_cambiar_datos()

    def establecer_matriz(self, nombre, valores):
        bloque = self.bloques[nombre]
        bloque["filas"].set(len(valores))
        bloque["columnas"].set(len(valores[0]))
        self._configurar_matriz(nombre, valores)

    def _dimensiones(self):
        return {nombre: (b["filas"].get(), b["columnas"].get()) for nombre, b in self.bloques.items()}

    def _leer_matrices(self, nombres):
        matrices = {}
        for nombre in sorted(nombres):
            if nombre in self.bloques:
                try:
                    matrices[nombre] = self.bloques[nombre]["matriz"].valores()
                except ValueError as error:
                    raise ValueError(f"Matriz {nombre}: {error}") from None
        return matrices

    def _leer_escalares(self, nombres):
        escalares = {}
        for nombre in sorted(nombres):
            entrada = self.entradas_escalares[nombre]
            try:
                escalares[nombre] = convertir_numero(entrada.get())
            except ValueError as error:
                entrada.configure(border_color=PALETA["error"])
                raise ValueError(f"Escalar {nombre}: {error}") from None
        return escalares

    def _validar_escalar(self, entrada):
        valido = _numero_o_nada(entrada.get()) is not None
        entrada.configure(border_color=PALETA["borde"] if valido else PALETA["error"])
        self._al_cambiar_datos()

    def _insertar(self, token):
        self.entrada_expresion.insert("insert", token)
        self.entrada_expresion.focus_set()
        self._programar_previa()

    def _usar_expresion(self, expresion):
        self.entrada_expresion.delete(0, "end")
        self.entrada_expresion.insert(0, expresion)
        self._al_cambiar_datos()

    def _usar_propiedad(self, clave):
        self.propiedad = clave
        propiedad = PROPIEDADES_POR_CLAVE[clave]
        self.boton_propiedad.configure(text="  " + self._texto_propiedad(propiedad) + "  ▾")
        if propiedad.get("contraejemplo"):
            self.boton_contraejemplo.pack(side="left", padx=(8, 0))
        else:
            self.boton_contraejemplo.pack_forget()
        self._al_cambiar_datos()

    def _abrir_expresiones(self):
        boton = self.boton_expresiones
        self.menu_expresiones.tk_popup(boton.winfo_rootx(), boton.winfo_rooty() + boton.winfo_height() + 4)

    def _abrir_propiedades(self):
        boton = self.boton_propiedad
        self.menu_propiedades.tk_popup(boton.winfo_rootx(), boton.winfo_rooty() + boton.winfo_height() + 4)

    def _programar_previa(self):
        if self._tarea_previa is not None:
            self.after_cancel(self._tarea_previa)
        self._tarea_previa = self.after(150, self._al_cambiar_datos)

    def _al_cambiar_datos(self):
        self._tarea_previa = None
        self._actualizar_previa()
        if self.hay_resultado and self.modo in ("Expresión", "Propiedades"):
            self.aviso.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 8))
            self.panel_pasos.mostrar_placeholder("Los datos cambiaron: vuelve a calcular.")
            self.area_verificacion.llenar([lambda p: placeholder(p, "✓", "Los datos cambiaron: vuelve a calcular.")])

    # --- vista previa -----------------------------------------------------

    def _actualizar_previa(self):
        for hijo in self.contenido_previa.winfo_children():
            hijo.destroy()
        parent = self.contenido_previa
        dimensiones = self._dimensiones()
        escalares = {n for n, e in self.entradas_escalares.items() if _numero_o_nada(e.get()) is not None}
        if self.modo == "Expresión":
            texto = self.entrada_expresion.get()
            try:
                nodo = analizar_expresion_matricial(texto)
                condiciones, final = revisar_dimensiones(nodo, dimensiones, escalares)
            except ErrorExpresion as error:
                self.entrada_expresion.configure(border_color=PALETA["error"])
                if error.posicion is not None and texto.strip():
                    marca = " " * min(error.posicion, len(texto)) + "▲"
                    etiqueta(parent, texto + "\n" + marca, FUENTE_MONO, "error").pack(anchor="w")
                etiqueta(parent, str(error), FUENTE_NORMAL, "error", ajustar=48).pack(anchor="w", pady=(4, 0))
                return
            self.entrada_expresion.configure(border_color=PALETA["borde"])
            self._previa_expresion(parent, nodo, condiciones, final)
        elif self.modo == "Propiedades":
            propiedad = PROPIEDADES_POR_CLAVE[self.propiedad]
            if propiedad.get("tipo", "igualdad") != "igualdad":
                etiqueta(parent, propiedad["advertencia"], FUENTE_NORMAL, "texto_2", ajustar=48).pack(anchor="w")
                etiqueta(parent, "Condiciones: " + propiedad["condiciones"], FUENTE_PEQUENA, "texto_3", ajustar=48).pack(
                    anchor="w", pady=(4, 0))
                return
            etiqueta(parent, f"{propiedad['izquierda']}  =  {propiedad['derecha']}", (FAMILIA_MONO, 15, "bold"),
                     "primario").pack(anchor="w")
            etiqueta(parent, "Condiciones: " + propiedad["condiciones"], FUENTE_PEQUENA, "texto_3", ajustar=48).pack(
                anchor="w", pady=(2, 6))
            extra = {}
            if propiedad.get("extra"):
                m, n = dimensiones["A"]
                extra = {"cero": {"O": (m, n)}, "identidad_columnas": {"I": (n, n)},
                         "identidad_filas": {"I": (m, m)}}[propiedad["extra"]]
            for lado in (propiedad["izquierda"], propiedad["derecha"]):
                nodo = analizar_expresion_matricial(lado)
                try:
                    condiciones, final = revisar_dimensiones(nodo, {**dimensiones, **extra}, escalares)
                except ErrorExpresion as error:
                    etiqueta(parent, f"{nodo.texto()}:  {error}", FUENTE_PEQUENA_NEGRITA, "error", ajustar=48).pack(anchor="w")
                    continue
                etiqueta(parent, f"{nodo.texto()}:  " + (f"matriz {formatear_dimension(final)}" if final else
                                                         "no está definida con estos tamaños" if condiciones else "—"),
                         FUENTE_PEQUENA_NEGRITA, "exito" if final else "error").pack(anchor="w")
        elif self.modo == "Contraejemplos":
            etiqueta(parent, "Cada contraejemplo muestra que una afirmación es falsa en general. Usa «Estudiar paso a "
                             "paso» para cargarlo en A, B y C.", FUENTE_NORMAL, "texto_2", ajustar=48).pack(anchor="w")
        else:
            etiqueta(parent, "Elige un ejercicio y presiona «Resolver en la calculadora»: se cargan sus matrices y se "
                             "resuelve con procedimiento y verificación.", FUENTE_NORMAL, "texto_2", ajustar=48).pack(anchor="w")

    @staticmethod
    def _previa_expresion(parent, nodo, condiciones, final):
        etiqueta(parent, "Se calcula como:  " + nodo.texto_completo(), FUENTE_MONO, "primario", ajustar=48).pack(anchor="w")
        if condiciones:
            etiqueta(parent, "Orden de cálculo y condiciones:", FUENTE_PEQUENA_NEGRITA, "texto_3").pack(anchor="w", pady=(6, 0))
            for k, condicion in enumerate(condiciones, start=1):
                etiqueta(parent, f"{k}. {'✓' if condicion['cumple'] else '✗'}  {condicion['operacion']}:  "
                                 f"{condicion['requisito']}", FUENTE_MONO, "exito" if condicion["cumple"] else "error",
                         ajustar=48).pack(anchor="w")
        if final:
            etiqueta(parent, f"Resultado esperado: matriz {formatear_dimension(final)}", FUENTE_PEQUENA_NEGRITA,
                     "texto").pack(anchor="w", pady=(6, 0))
        elif condiciones and not condiciones[-1]["cumple"]:
            etiqueta(parent, "Con estos tamaños la expresión no está definida: cambia las dimensiones o la expresión.",
                     FUENTE_PEQUENA_NEGRITA, "error", ajustar=48).pack(anchor="w", pady=(6, 0))

    # --- modos y acciones -------------------------------------------------

    def _cambiar_modo(self, modo):
        self.modo = modo
        self.selector_modo.set(modo)
        for controles in (self.controles_expresion, self.controles_propiedad, self.controles_info):
            controles.pack_forget()
        if modo == "Expresión":
            self.controles_expresion.pack(side="left")
        elif modo == "Propiedades":
            self.controles_propiedad.pack(side="left")
            self._usar_propiedad(self.propiedad)
        else:
            self.controles_info.configure(text="Contraejemplos clásicos del producto de matrices." if modo == "Contraejemplos"
                                          else "Ejercicios tipo examen con su resolución guiada.")
            self.controles_info.pack(side="left")
        self.hay_resultado = False
        self.aviso.grid_remove()
        if modo == "Contraejemplos":
            self._mostrar_contraejemplos()
        elif modo == "Ejercicios":
            self._mostrar_ejercicios()
        else:
            texto = ("Escribe una expresión (o elige un ejemplo) y presiona «Calcular y verificar»." if modo == "Expresión"
                     else "Elige una propiedad y presiona «Calcular y verificar» para comprobarla con tus matrices.")
            self._vaciar(texto)
        self._actualizar_previa()

    def _vaciar(self, texto):
        self.area_resultado.llenar([lambda p: placeholder(p, "▦", texto)])
        self.panel_pasos.mostrar_placeholder()
        self.area_verificacion.llenar([lambda p: placeholder(
            p, "✓", "Aquí aparecerá la verificación: cada operación recalculada, el recálculo independiente y, cuando "
                    "exista, una ruta alternativa por propiedad.")])

    def resolver(self):
        try:
            if self.modo == "Expresión":
                self._resolver_expresion()
            elif self.modo == "Propiedades":
                self._resolver_propiedad()
            elif self.modo == "Contraejemplos":
                self._mostrar_contraejemplos()
            else:
                self._mostrar_ejercicios()
        except (ErrorExpresion, ValueError) as error:
            self.app.notificar(str(error), "error")

    def _resolver_expresion(self):
        nodo = analizar_expresion_matricial(self.entrada_expresion.get())
        matrices = self._leer_matrices(nodo.nombres_matrices())
        escalares = self._leer_escalares(nodo.nombres_escalares())
        resolucion = resolver_expresion_matricial(nodo, matrices, escalares)
        informe = verificar_resolucion(resolucion)
        self.hay_resultado = True
        self.aviso.grid_remove()
        self.area_resultado.llenar(constructores_resultado_expresion(resolucion, informe, self.app), retardo=70)
        self.panel_pasos.mostrar_pasos(didactica.pasos_expresion(resolucion, informe))
        self.area_verificacion.llenar(constructores_verificacion(resolucion, informe), retardo=60)
        self.pestanas.set("Resultado")
        if resolucion["error"]:
            self.app.notificar(f"{resolucion['expresion']} no está definida con estas dimensiones (ver paso marcado).", "error")
        elif informe["correcto"]:
            self.app.notificar(f"{resolucion['expresion']} calculada · verificación superada ✓", "exito")
        else:
            self.app.notificar("La verificación encontró diferencias: revisa la pestaña Verificación.", "error")

    def _resolver_propiedad(self):
        propiedad = PROPIEDADES_POR_CLAVE[self.propiedad]
        tipo = propiedad.get("tipo", "igualdad")
        if tipo == "igualdad":
            nombres, escalares = set(), set()
            for expresion in (propiedad["izquierda"], propiedad["derecha"], propiedad.get("error_comun")):
                if expresion:
                    nodo = analizar_expresion_matricial(expresion)
                    nombres |= nodo.nombres_matrices()
                    escalares |= nodo.nombres_escalares()
            nombres = {n for n in nombres if n in self.bloques} | {"A"}
        else:
            nombres, escalares = ({"A", "B", "C"} if tipo == "cancelacion" else {"A", "B"}), set()
        informe = verificar_propiedad_matricial(self.propiedad, self._leer_matrices(nombres),
                                                self._leer_escalares(escalares))
        self.hay_resultado = True
        self.aviso.grid_remove()
        self.area_resultado.llenar(constructores_resultado_propiedad(informe, self._estudiar_contraejemplo), retardo=70)
        pasos = [{"tipo": "didactica", "etapa": didactica.condiciones_propiedad(informe)}]
        abreviaturas = {"Lado izquierdo": "Izq.", "Lado derecho": "Der.", "Error frecuente": "Error frecuente"}
        for lado in informe["lados"]:
            resolucion = lado["resolucion"]
            pasos.append({"tipo": "seccion", "titulo": f"{lado['etiqueta']}:  {resolucion['expresion']}",
                          "detalle": f"Se calcula por separado desde los datos originales ("
                                     f"{_plural(len(resolucion['operaciones']), 'operación', 'operaciones')})."})
            for paso in resolucion["pasos"]:
                copia = dict(paso)
                copia["lado"] = abreviaturas.get(lado["etiqueta"], lado["etiqueta"])
                pasos.append(copia)
        if pasos:
            self.panel_pasos.mostrar_pasos(pasos)
        else:
            self.panel_pasos.mostrar_placeholder()
        self.area_verificacion.llenar(constructores_verificacion_propiedad(informe), retardo=60)
        self.pestanas.set("Resultado")
        tipo_aviso = "exito" if informe["cumple"] and propiedad["general"] else "aviso"
        self.app.notificar(f"{propiedad['nombre']}: {informe['conclusion'].split('.')[0]}.", tipo_aviso)

    def _mostrar_contraejemplos(self):
        datos = contraejemplos_matriciales()

        def tarjeta(parent, clave, dato):
            titulo, _tipo, _objetivo = self.CONTRAEJEMPLOS[clave]
            caja = tarjeta_seccion(parent, titulo)
            matrices = [(k, dato[k]) for k in ("A", "B", "C") if k in dato]
            productos = [(k, dato[k]) for k in ("AB", "BA", "AC") if k in dato]
            dibujar_valores(caja, matrices).pack(anchor="w", padx=14)
            if productos:
                dibujar_valores(caja, productos).pack(anchor="w", padx=14, pady=(4, 0))
            etiqueta(caja, dato["conclusion"], FUENTE_NORMAL, "texto_2", ajustar=44).pack(anchor="w", padx=16, pady=(6, 0))
            boton_secundario(caja, "Estudiar paso a paso", lambda: self._estudiar_contraejemplo(clave), width=190).pack(
                anchor="w", padx=16, pady=(8, 14))

        self.hay_resultado = False
        self.area_resultado.llenar([lambda p, c=c, d=d: tarjeta(p, c, d) for c, d in datos.items()], retardo=60)
        self.panel_pasos.mostrar_placeholder("Usa «Estudiar paso a paso» en un contraejemplo para ver aquí sus cálculos.")
        self.area_verificacion.llenar([lambda p: placeholder(
            p, "✓", "Al estudiar un contraejemplo, aquí se verifican los cálculos de cada lado.")])

    def _estudiar_contraejemplo(self, clave):
        dato = contraejemplos_matriciales()[clave]
        for nombre in ("A", "B", "C"):
            if nombre in dato:
                self.establecer_matriz(nombre, dato[nombre])
        _titulo, tipo, objetivo = self.CONTRAEJEMPLOS[clave]
        if tipo == "expresion":
            self._cambiar_modo("Expresión")
            self._usar_expresion(objetivo)
        else:
            self.propiedad = objetivo
            self._cambiar_modo("Propiedades")
        destello(self.tarjeta_datos)
        self.resolver()

    def _mostrar_ejercicios(self):
        def tarjeta(parent, numero, ejercicio):
            caja = tarjeta_seccion(parent, f"{numero}. {ejercicio['tema']}")
            etiqueta(caja, ejercicio["consigna"], FUENTE_NORMAL, "texto_2", ajustar=44).pack(anchor="w", padx=16)
            matrices = [(k, [[convertir_numero(v) for v in fila] for fila in ejercicio[k]])
                        for k in ("A", "B", "C") if k in ejercicio]
            if matrices:
                dibujar_valores(caja, matrices).pack(anchor="w", padx=14, pady=(6, 0))
            boton_secundario(caja, "Resolver en la calculadora", lambda: self._resolver_ejercicio(ejercicio),
                             width=210).pack(anchor="w", padx=16, pady=(8, 14))

        self.hay_resultado = False
        self.area_resultado.llenar([lambda p, n=n, e=e: tarjeta(p, n, e)
                                    for n, e in enumerate(ejercicios_matrices(), start=1)], retardo=60)
        self.panel_pasos.mostrar_placeholder("Elige un ejercicio y presiona «Resolver en la calculadora».")
        self.area_verificacion.llenar([lambda p: placeholder(p, "✓", "Aquí aparecerá la verificación del ejercicio.")])

    def _resolver_ejercicio(self, ejercicio):
        for nombre in ("A", "B", "C"):
            if nombre in ejercicio:
                self.establecer_matriz(nombre, ejercicio[nombre])
        if ejercicio.get("contraejemplo"):
            self._estudiar_contraejemplo(ejercicio["contraejemplo"])
            return
        if ejercicio.get("propiedad"):
            self.propiedad = ejercicio["propiedad"]
            self._cambiar_modo("Propiedades")
        else:
            self._cambiar_modo("Expresión")
            self._usar_expresion(ejercicio.get("expresion", "A + B"))
        destello(self.tarjeta_datos)
        self.resolver()

    def aleatorio(self):
        for nombre, bloque in self.bloques.items():
            filas, columnas = bloque["filas"].get(), bloque["columnas"].get()
            self._configurar_matriz(nombre, [[random.randint(-4, 4) for _ in range(columnas)] for _ in range(filas)])
        self._al_cambiar_datos()
        destello(self.tarjeta_datos)
        self.app.notificar("Se generaron matrices aleatorias con los tamaños actuales.", "info")

    def limpiar(self):
        for bloque in self.bloques.values():
            bloque["matriz"].limpiar()
        self.hay_resultado = False
        self.aviso.grid_remove()
        if self.modo in ("Expresión", "Propiedades"):
            self._vaciar("Las matrices quedaron en cero. Escribe sus entradas y presiona «Calcular y verificar».")
        self._actualizar_previa()


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

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.area.destroy()
        self.pestanas = ctk.CTkTabview(self, fg_color=PALETA["panel"], corner_radius=14,
            border_width=1, border_color=PALETA["borde"], segmented_button_fg_color=PALETA["panel_2"],
            segmented_button_selected_color=PALETA["primario"], segmented_button_unselected_color=PALETA["panel_2"],
            text_color=PALETA["texto"])
        self.pestanas.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        resultado = self.pestanas.add("Resultado")
        procedimiento = self.pestanas.add("Procedimiento")
        verificacion = self.pestanas.add("Verificación")
        self.area = AreaDesplazable(resultado, PALETA["panel"])
        self.area.pack(fill="both", expand=True)
        self.area_resultado = self.area
        self.panel_pasos = PanelPasos(procedimiento, PALETA["panel"], "Ejemplo docente de Gauss-Jordan", constructor=tarjeta_etapa)
        self.panel_pasos.pack(fill="both", expand=True)
        self.area_verificacion = AreaDesplazable(verificacion, PALETA["panel"])
        self.area_verificacion.pack(fill="both", expand=True)
        self.resultado = resolver_sistema([[2, 1], [1, -1]], [5, 1])

    def constructores(self):
        r = self.resultado
        teoria = didactica.etapa("Reglas del método", "Conceptos generales; después se desarrolla el ejemplo numérico.",
                                subpasos=[didactica.etapa(t, x) for t, x in self.PASOS])
        self.panel_pasos.mostrar_pasos([teoria, *didactica.procedimiento_sistema(r)])
        self.area_verificacion.llenar(constructores_chequeo(didactica.verificacion_sistema(r)), retardo=45)
        return [lambda p: tarjeta_estado(p, "Ejemplo resuelto: x1=2, x2=1", "Sistema original: 2x1+x2=5; x1−x2=1. Explora los pasos y la sustitución en sus pestañas.", PALETA["exito"], "✓"),
                *constructores_solucion(r, incluir_verificacion=False)]


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
        "En «Operaciones con matrices» escribe una expresión con A, B y C (por ejemplo 2A − 3B + C, A(B + C) o "
        "(AB)ᵀ) o constrúyela con los botones de símbolos; la transpuesta también se escribe A^T o A'. La inversa se escribe A^-1, A^(-1) o A⁻¹.",
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
        ("Producto de matrices", "AB existe si columnas(A) = filas(B); (AB)ᵢⱼ = Σₖ aᵢₖbₖⱼ. En general AB ≠ BA."),
        ("Transpuesta", "Aᵀ intercambia filas y columnas: (Aᵀ)ᵢⱼ = aⱼᵢ, y (AB)ᵀ = BᵀAᵀ (se invierte el orden)."),
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

class PaginaTeoremas(PaginaInformativa):
    titulo = "0. Ver Teoremas Clave del Módulo"
    subtitulo = "Condiciones y conceptos para comprender y defender los algoritmos"

    def constructores(self):
        return [lambda p, i=i, t=t, d=d: tarjeta_numerada(p, i, t, d)
                for i, (t, d) in enumerate(TEOREMAS_MATRICES, 1)]


class PaginaDeterminantes(PaginaBase):
    """Consulta educativa de determinantes, inversas y sus propiedades."""
    titulo = "Determinantes, inversas y propiedades"
    subtitulo = "Fracciones exactas, procedimiento completo y verificación automática"
    OPERACIONES = {
        "Determinante triangular": ("det", "triangular"),
        "Determinante 2×2": ("det", "2x2"),
        "Determinante Sarrus 3×3": ("det", "sarrus"),
        "Determinante por cofactores": ("det", "cofactores"),
        "Inversa Gauss-Jordan": ("inv", "gauss_jordan"),
        "Inversa por adjunta": ("inv", "adjunta"),
        "Comparar y verificar ambas inversas": ("comparar", ""),
        **{texto: ("prop", clave) for clave, texto in PROPIEDADES_AVANZADAS.items()},
    }

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.informe = None
        self.grid_rowconfigure(1, weight=1)
        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        contenido.grid_columnconfigure(0, weight=1, uniform="det_columnas")
        contenido.grid_columnconfigure(1, weight=1, uniform="det_columnas")
        contenido.grid_rowconfigure(0, weight=1)
        tarjeta = crear_tarjeta(contenido, "Datos", "Una fila por línea; separar entradas con espacios o punto y coma. Se aceptan fracciones y decimales.")
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        datos = AreaDesplazable(tarjeta, PALETA["panel"])
        datos.pack(fill="both", expand=True, padx=12, pady=8)
        self.entradas = {}
        for nombre, valores in (("A", "1 2\n3 4"), ("B", "2 0\n1 3")):
            etiqueta(datos.interior, nombre + (" (solo para la propiedad del producto)" if nombre == "B" else ""), FUENTE_NEGRITA, ajustar=40).pack(anchor="w", padx=8)
            entrada = ctk.CTkTextbox(datos.interior, height=100, font=FUENTE_MONO, wrap="none")
            entrada.pack(fill="x", padx=8, pady=(4, 10))
            entrada.insert("1.0", valores)
            entrada.bind("<KeyRelease>", self._datos_cambiaron, add="+")
            self.entradas[nombre] = entrada
        etiqueta(datos.interior, "Escalar k para operaciones de fila:", FUENTE_NORMAL, ajustar=40).pack(anchor="w", padx=8)
        self.escalar = ctk.CTkEntry(datos.interior, width=120)
        self.escalar.insert(0, "2")
        self.escalar.pack(anchor="w", padx=8, pady=6)
        self.escalar.bind("<KeyRelease>", self._datos_cambiaron, add="+")
        self.operacion = ctk.CTkOptionMenu(datos.interior, values=list(self.OPERACIONES), width=330,
                                         command=lambda _v: self._datos_cambiaron())
        self.operacion.pack(anchor="w", padx=8, pady=8)
        boton_primario(tarjeta, "Calcular", self.resolver).pack(anchor="w", padx=20, pady=(4, 16))
        self.pestanas = ctk.CTkTabview(contenido, fg_color=PALETA["panel"], corner_radius=14,
            border_width=1, border_color=PALETA["borde"], segmented_button_fg_color=PALETA["panel_2"],
            segmented_button_selected_color=PALETA["primario"], segmented_button_unselected_color=PALETA["panel_2"],
            text_color=PALETA["texto"])
        self.pestanas.grid(row=0, column=1, sticky="nsew")
        resultado = self.pestanas.add("Resultado")
        procedimiento = self.pestanas.add("Procedimiento")
        verificacion = self.pestanas.add("Verificación")
        self.area_resultado = AreaDesplazable(resultado, PALETA["panel"])
        self.area_resultado.pack(fill="both", expand=True)
        self.panel_pasos = PanelPasos(procedimiento, PALETA["panel"], "Aquí se mostrarán las fórmulas y operaciones intermedias.", constructor=tarjeta_etapa)
        self.panel_pasos.pack(fill="both", expand=True)
        self.area_verificacion = AreaDesplazable(verificacion, PALETA["panel"])
        self.area_verificacion.pack(fill="both", expand=True)
        self.area_resultado.llenar([lambda p: placeholder(p, "Δ", "Selecciona una operación y presiona Calcular.")])
        self.area_verificacion.llenar([lambda p: placeholder(p, "✓", "Aquí aparecerá la comprobación independiente.")])

    def _datos_cambiaron(self, _evento=None):
        if self.informe is None:
            return
        self.informe = None
        self.area_resultado.llenar([lambda p: tarjeta_mensajes(p, "Datos modificados", ["Presiona Calcular para actualizar las tres vistas."], "advertencia")])
        self.panel_pasos.mostrar_placeholder("Los datos cambiaron: vuelve a calcular.")
        self.area_verificacion.llenar([lambda p: placeholder(p, "✓", "Los datos cambiaron: vuelve a calcular.")])

    def _leer(self, nombre):
        texto = self.entradas[nombre].get("1.0", "end").strip()
        matriz = [[convertir_numero(v) for v in fila.replace(";", " ").split()]
                  for fila in texto.splitlines() if fila.strip()]
        if len(matriz) > LIMITE_DIMENSION or any(len(fila) > LIMITE_DIMENSION for fila in matriz):
            raise ValueError(f"La GUI admite matrices de hasta {LIMITE_DIMENSION}×{LIMITE_DIMENSION}.")
        return validar_matriz(matriz, nombre)

    def resolver(self):
        datos = {}
        try:
            tipo, metodo = self.OPERACIONES[self.operacion.get()]
            A = self._leer("A")
            datos["A"] = A
            if tipo == "det":
                informe = didactica.informe_determinante(A, metodo)
            elif tipo == "inv":
                informe = didactica.informe_inversa(A, metodo)
            elif tipo == "comparar":
                informe = didactica.informe_comparacion_inversas(A)
            else:
                if metodo in ("inversa_producto", "det_producto"):
                    datos["B"] = self._leer("B")
                escalares = {"k": convertir_numero(self.escalar.get())} if metodo in ("det_escalar_fila", "det_suma_fila") else None
                informe = didactica.informe_propiedad_avanzada(metodo, datos, escalares)
        except (ValueError, ArithmeticError) as error:
            mensaje = str(error)
            condiciones = didactica.etapa("Datos y condición incumplida", valores=[didactica.valor(n, M) for n, M in datos.items()],
                                         condiciones=[didactica.condicion(mensaje, False)])
            informe = {"definido": False, "titulo": "Operación no definida", "resultado": None, "conclusion": mensaje,
                       "procedimiento": [condiciones], "verificacion": {"aplicable": False, "correcto": False,
                       "motivo": "No existe resultado: la condición necesaria no se cumple.", "etapas": [condiciones]}}
            self.app.notificar(mensaje, "error")
        informe["datos_resultado"] = didactica.etapa("Datos y operación", formula=self.operacion.get(),
            valores=[didactica.valor(n, M) for n, M in datos.items()])
        self.informe = informe
        self.area_resultado.llenar(constructores_informe(informe), retardo=45)
        self.panel_pasos.mostrar_pasos(informe["procedimiento"])
        self.area_verificacion.llenar(constructores_chequeo(informe["verificacion"]), retardo=45)
        self.pestanas.set("Resultado")


class AplicacionAlgebraLineal(_Ventana):
    """Aplicacion de escritorio moderna hecha con CustomTkinter."""

    SECCIONES = [
        ("teoremas", "0", "Teoremas clave", PaginaTeoremas),
        ("calculadora", "▦", "Calculadora", PaginaCalculadora),
        ("vectorial", "Σ", "Combinaciones lineales", PaginaCombinaciones),
        ("axb", "≡", "Ecuación Ax = b", PaginaAxb),
        ("propiedades_ax", "⇄", "Propiedades de Ax", PaginaPropiedades),
        ("matrices", "⊞", "Operaciones matriciales", PaginaMatrices),
        ("determinantes", "Δ", "Determinantes e inversas", PaginaDeterminantes),
        ("independencia", "⊥", "Independencia lineal", PaginaIndependencia),
        ("metodo", "☰", "Método de eliminación", PaginaMetodo),
        ("ayuda", "?", "Ayuda", PaginaAyuda),
    ]

    def __init__(self):
        super().__init__()
        _FUENTES_MEDIDA.clear()
        self.title("Calculadora de Álgebra Lineal - Grupo 3 - UAM")
        self._centrar(1280, 820)
        self.minsize(min(1160, self.winfo_screenwidth() - 60),
                     min(680, self.winfo_screenheight() - 80))
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

    def destroy(self):
        """Cancela animaciones y tareas diferidas antes de destruir los widgets."""
        for identificador in self.tk.splitlist(self.tk.call("after", "info")):
            self.tk.call("after", "cancel", identificador)
        _FUENTES_MEDIDA.clear()
        super().destroy()

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

        self.nav = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        self.nav.pack(fill="both", expand=True, padx=12)
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
        resolver = getattr(self.paginas.get(self.pagina_actual), "resolver", None)
        if resolver is not None:
            resolver()
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
    if "--teoremas" in sys.argv[1:]:
        print(LOGO_ASCII)
        print("0. Ver Teoremas Clave del Módulo\n")
        print(texto_teoremas())
        return
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

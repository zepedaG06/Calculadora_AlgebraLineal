"""Interfaz gráfica de la Calculadora de Álgebra Lineal (CustomTkinter).

Propósito: capturar datos, mostrar Resultado, Procedimiento y Verificación de cada sección (sistemas,
combinaciones, Ax = b, propiedades de Ax, operaciones matriciales, determinantes e inversas, factorización LU,
independencia lineal y métodos numéricos), animar y renderizar los resultados y encadenarlos entre secciones.
Todo el cálculo vive en modulos/.
Unidad: Álgebra Lineal (MTM0120), Programa 7: módulo de Métodos Numéricos, renders y animaciones.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
Notas: la paleta usa el turquesa institucional de la UAM con tuplas (modo claro, modo oscuro); si
CustomTkinter no está instalado, las clases heredan de object para que el módulo se pueda importar igual.
No usa NumPy, SciPy ni el módulo math: la eliminación por filas está implementada con Fraction.
"""

import os
import random
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
from fractions import Fraction
from tkinter import filedialog
from teoremas.teoremas_matrices import TEOREMAS_MATRICES, texto_teoremas, LOGO_ASCII
from modulos import informes as didactica
from modulos import graficos
from modulos import modulo_lu
from modulos import modulo_numericos as numericos
from modulos.graficos import mezclar_colores
from teoremas.teoremas_lu import LOGO_LU, TEOREMAS_LU
from teoremas.teoremas_numericos import LOGO_NUMERICOS, TEOREMAS_NUMERICOS

try:
    import customtkinter as ctk
except ModuleNotFoundError:
    ctk = None

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
except ModuleNotFoundError:
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageTk = None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_LOGO = os.path.join(BASE_DIR, "universidad_americana.png")
if not os.path.exists(RUTA_LOGO):
    RUTA_LOGO = os.path.join(BASE_DIR, "logo_uam.png")

LIMITE_DIMENSION = 10



from modulos import modulo_matrices as _matematica
globals().update({nombre: valor for nombre, valor in vars(_matematica).items()
                  if not nombre.startswith("__")})



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

_Marco = ctk.CTkFrame if ctk is not None else object
_Ventana = ctk.CTk if ctk is not None else object



def configurar_customtkinter():
    """Aplica el modo oscuro y el tema base de CustomTkinter, si está instalado."""
    if ctk is None:
        return
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def resolver_color(par):
    """Elige el color oscuro de un par (claro, oscuro) de PALETA para los widgets nativos de tkinter.

    Entrada: tupla de colores o un color directo. Salida: cadena '#RRGGBB'.
    """
    if isinstance(par, tuple):
        return par[1]
    return par


def animar(widget, duracion_ms, al_avanzar, al_terminar=None):
    """Ejecuta una animación con desaceleración suave; se detiene sola si el widget se destruye.

    Entrada: widget, duración en ms, al_avanzar(t) con t entre 0 y 1 y al_terminar opcional. Salida: None.
    """
    inicio = time.perf_counter()

    def paso():
        """Avanza un cuadro de la animación y se reprograma hasta completar la duración."""
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
    """Obtiene el factor de escala de CustomTkinter (pantallas HiDPI en Windows y Linux).

    Entrada: widget. Salida: número (1.0 si no se puede consultar).
    """
    try:
        return ctk.ScalingTracker.get_widget_scaling(widget)
    except Exception:
        return 1.0


_FUENTES_MEDIDA = {}


def _fuente_medida(widget, pixeles, negrita=False, familia=None):
    """Obtiene (y guarda en caché) la fuente con la que se miden los textos dibujados en un Canvas.

    Entrada: widget, tamaño en píxeles, negrita y familia. Salida: objeto tkinter.font.Font.
    """
    familia = familia or FAMILIA_MONO
    clave = (str(widget.tk), familia, pixeles, negrita)
    if clave not in _FUENTES_MEDIDA:
        _FUENTES_MEDIDA[clave] = tkfont.Font(
            root=widget, family=familia, size=-pixeles, weight="bold" if negrita else "normal"
        )
    return _FUENTES_MEDIDA[clave]


def es_descendiente(widget, ancestro):
    """Indica si un widget es el ancestro indicado o está dentro de él en la jerarquía de Tk.

    Entrada: widget y ancestro. Salida: True o False.
    """
    while widget is not None:
        if widget is ancestro:
            return True
        widget = getattr(widget, "master", None)
    return False


def widget_bajo_puntero(widget):
    """Busca el widget que está bajo el puntero del mouse.

    Entrada: cualquier widget de la ventana. Salida: el widget encontrado o None.
    """
    try:
        x, y = widget.winfo_pointerxy()
        return widget.winfo_containing(x, y)
    except (tk.TclError, KeyError):
        return None


def efecto_hover(tarjeta, activo=None, normal=None):
    """Ilumina el borde de una tarjeta mientras el puntero está encima.

    Entrada: tarjeta y colores de borde activo y normal. Salida: None.
    """
    activo = activo or PALETA["primario"]
    normal = normal or PALETA["borde"]
    estado = {"dentro": False}

    def comprobar():
        """Restaura el borde cuando el puntero ya salió de la tarjeta; si no, vuelve a comprobar más tarde."""
        try:
            if es_descendiente(widget_bajo_puntero(tarjeta), tarjeta):
                tarjeta.after(150, comprobar)
            else:
                estado["dentro"] = False
                tarjeta.configure(border_color=normal)
        except tk.TclError:
            pass

    def entrar(_evento):
        """Ilumina el borde al entrar el puntero y programa la comprobación de salida."""
        if not estado["dentro"]:
            estado["dentro"] = True
            tarjeta.configure(border_color=activo)
            tarjeta.after(150, comprobar)

    tarjeta.bind("<Enter>", entrar, add="+")


def destello(tarjeta, color=None, duracion=800):
    """Resalta el borde de una tarjeta y lo devuelve suavemente a su color normal.

    Entrada: tarjeta, color del destello y duración en ms. Salida: None.
    """
    inicio = resolver_color(color or PALETA["primario"])
    fin = resolver_color(PALETA["borde"])
    animar(tarjeta, duracion, lambda t: tarjeta.configure(border_color=mezclar_colores(inicio, fin, t)))


def cargar_logo(tamano=(96, 96)):
    """Carga el logo de la UAM como CTkImage (con Pillow) o como PhotoImage reducido.

    Entrada: tamaño (ancho, alto). Salida: la imagen, o None si no se pudo cargar.
    """
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
    """Crea un texto alineado a la izquierda; con «ajustar» se parte en líneas según el ancho visible.

    Entrada: contenedor, texto, fuente, color y ajustar (margen o función). Salida: CTkLabel.
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
    """Ajusta el ancho de línea de un texto al ancho visible del área desplazable que lo contiene.

    Entrada: etiqueta, margen (número o función) y ancho mínimo. Salida: None.
    """
    area = label.master
    while area is not None and not getattr(area, "_es_area_desplazable", False):
        area = getattr(area, "master", None)
    if area is None:
        def ajustar_al_marco(_evento=None):
            """Recalcula el ancho de línea cuando cambia el tamaño del contenedor directo."""
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
        """Recalcula el ancho de línea con el ancho visible del AreaDesplazable."""
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
    """Crea una etiqueta pequeña con fondo redondeado.

    Entrada: contenedor, texto, colores de fondo y texto, y fuente. Salida: CTkLabel.
    """
    return ctk.CTkLabel(
        parent, text=texto, font=fuente or FUENTE_PEQUENA_NEGRITA,
        fg_color=PALETA.get(fondo, fondo), text_color=PALETA.get(color_texto, color_texto),
        corner_radius=7, height=24, padx=8,
    )


def boton_primario(parent, texto, comando, **kwargs):
    """Crea un botón con el color primario de la paleta.

    Entrada: contenedor, texto, comando y opciones de estilo. Salida: CTkButton.
    """
    opciones = dict(
        height=40, corner_radius=10, font=FUENTE_NEGRITA,
        fg_color=PALETA["primario"], hover_color=PALETA["primario_hover"],
        text_color=TEXTO_SOBRE_PRIMARIO,
    )
    opciones.update(kwargs)
    return ctk.CTkButton(parent, text=texto, command=comando, **opciones)


def boton_secundario(parent, texto, comando, **kwargs):
    """Crea un botón secundario (fondo suave) de la paleta.

    Entrada: contenedor, texto, comando y opciones de estilo. Salida: CTkButton.
    """
    opciones = dict(
        height=36, corner_radius=10, font=FUENTE_NORMAL,
        fg_color=PALETA["secundario"], hover_color=PALETA["secundario_hover"],
        text_color=PALETA["texto"], text_color_disabled=PALETA["texto_3"],
    )
    opciones.update(kwargs)
    return ctk.CTkButton(parent, text=texto, command=comando, **opciones)


def separador_vertical(parent):
    """Crea una línea vertical delgada para separar grupos de controles.

    Entrada: contenedor. Salida: CTkFrame.
    """
    return ctk.CTkFrame(parent, width=1, height=46, fg_color=PALETA["borde"])


def crear_tarjeta(parent, titulo=None, subtitulo=None, fondo=None):
    """Crea un marco redondeado con borde y, si se indican, título y subtítulo.

    Entrada: contenedor, título, subtítulo y color de fondo. Salida: CTkFrame de la tarjeta.
    """
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
    """Crea una tarjeta de resultado empaquetada a lo ancho del contenedor.

    Entrada: contenedor, título y subtítulo. Salida: CTkFrame de la tarjeta.
    """
    tarjeta = crear_tarjeta(parent, titulo, subtitulo, fondo=PALETA["panel_2"])
    tarjeta.pack(fill="x", padx=2, pady=(0, 12))
    efecto_hover(tarjeta)
    return tarjeta


def placeholder(parent, icono, texto):
    """Crea el mensaje centrado de un panel vacío.

    Entrada: contenedor, icono y texto. Salida: CTkFrame con el mensaje.
    """
    marco = ctk.CTkFrame(parent, fg_color="transparent")
    marco.pack(fill="x", pady=(70, 20))
    ctk.CTkLabel(marco, text=icono, font=(FAMILIA, 46, "bold"), text_color=PALETA["borde"]).pack()
    mensaje = ctk.CTkLabel(marco, text=texto, font=FUENTE_NORMAL, text_color=PALETA["texto_3"],
                           wraplength=200, justify="center")
    mensaje.pack(pady=(8, 0))
    _ajustar_a_area(mensaje, lambda ancho: min(420, ancho - 60))
    return marco



def _texto_valor(valor):
    """Escribe una entrada de la vista previa: '?' si no es válida, el texto tal cual o el número formateado.

    Entrada: valor (None, texto o número). Salida: cadena.
    """
    if valor is None:
        return "?"
    if isinstance(valor, str):
        return valor
    return formatear_numero(Fraction(valor))


def _corchetes(lienzo, x1, x2, y1, y2, esc, color):
    """Dibuja los corchetes izquierdo y derecho de una matriz en el Canvas.

    Entrada: lienzo, coordenadas del rectángulo, escala y color. Salida: None.
    """
    punta = round(6 * esc)
    grosor = max(1, round(2 * esc))
    lienzo.create_line(x1 + punta, y1, x1, y1, x1, y2, x1 + punta, y2, fill=color, width=grosor)
    lienzo.create_line(x2 - punta, y1, x2, y1, x2, y2, x2 - punta, y2, fill=color, width=grosor)


def _rectangulo_redondeado(lienzo, x1, y1, x2, y2, radio, **kwargs):
    """Dibuja un rectángulo con esquinas redondeadas en el Canvas.

    Entrada: lienzo, coordenadas, radio y opciones de dibujo. Salida: identificador del polígono.
    """
    puntos = [
        x1 + radio, y1, x2 - radio, y1, x2, y1, x2, y1 + radio,
        x2, y2 - radio, x2, y2, x2 - radio, y2, x1 + radio, y2,
        x1, y2, x1, y2 - radio, x1, y1 + radio, x1, y1,
    ]
    return lienzo.create_polygon(puntos, smooth=True, **kwargs)


def _dibujar_matriz_en(lienzo, x_base, y_base, matriz, esc, separador=True, filas=(), estilo="relleno",
                       fila_origen=None, pivotes=(), tamano=14):
    """Dibuja una matriz (o [A | b]) en un Canvas: resalta filas y pivotes y atenúa los ceros.

    Entrada: lienzo, posición, matriz, escala, separador, filas, estilo, fila_origen, pivotes y tamaño.
    Salida: (ancho, alto) ocupados.
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
    """Crea un Canvas del tamaño justo con la matriz dibujada.

    Entrada: contenedor, matriz, color de fondo y opciones de _dibujar_matriz_en. Salida: tk.Canvas.
    """
    lienzo = tk.Canvas(parent, width=10, height=10, bg=resolver_color(fondo or PALETA["panel_2"]),
                       highlightthickness=0, bd=0)
    ancho, alto = _dibujar_matriz_en(lienzo, 0, 0, matriz, escala_de(parent), **opciones)
    lienzo.configure(width=ancho, height=alto)
    return lienzo


def _chip_en(lienzo, x, y, texto, fondo, color, esc):
    """Dibuja una etiqueta redondeada en un Canvas.

    Entrada: lienzo, posición, texto, colores y escala. Salida: (ancho, alto) ocupados.
    """
    px = round(11 * esc)
    ancho = _fuente_medida(lienzo, px, True, FAMILIA).measure(texto) + round(16 * esc)
    alto = round(24 * esc)
    _rectangulo_redondeado(lienzo, x, y, x + ancho, y + alto, round(7 * esc),
                           fill=resolver_color(fondo), outline="")
    lienzo.create_text(x + ancho / 2, y + alto / 2, text=texto, fill=resolver_color(color),
                       font=(FAMILIA, -px, "bold"))
    return ancho, alto


def dibujar_expresion(parent, partes, fondo=None, tamano=14):
    """Dibuja una expresión como ['x =', [1, 2], '+ t', [3, 4]]: textos, vectores columna y matrices ('?' si es None).

    Entrada: contenedor, lista de partes, fondo y tamaño. Salida: tk.Canvas.
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
        """Convierte un vector en matriz columna y deja intactas las matrices.

        Entrada: lista. Salida: lista anidada.
        """
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
    """Arma las partes para dibujar '2·[v1] - [v2] = [w]' omitiendo coeficientes cero.

    Entrada: coeficientes, vectores y resultado final. Salida: lista de partes para dibujar_expresion.
    """
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



class BarraDesplazamiento(tk.Canvas):
    """Barra de desplazamiento delgada con forma de píldora, más liviana que CTkScrollbar.

    CTkScrollbar redibuja toda la ventana cada vez que cambia de posición.
    """

    GROSOR = 10

    def __init__(self, parent, orientacion, comando, fondo):
        """Crea la barra y enlaza el arrastre y el clic con el comando de desplazamiento.

        Entrada: contenedor, orientación ('vertical' u 'horizontal'), comando y fondo. Salida: None.
        """
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
        """Actualiza la fracción visible y redibuja la píldora.

        Entrada: inicio y fin (entre 0 y 1). Salida: None.
        """
        self.inicio, self.fin = float(inicio), float(fin)
        self._dibujar()

    def _largo(self):
        """Mide el largo útil de la barra (alto o ancho según la orientación).

        Salida: entero en píxeles (al menos 1).
        """
        return max(1, self.winfo_height() if self.vertical else self.winfo_width())

    def _dibujar(self):
        """Coloca la píldora según la fracción visible del contenido."""
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
        """Calcula la posición relativa del evento a lo largo de la barra.

        Entrada: evento del mouse. Salida: número entre 0 y 1.
        """
        return (evento.y if self.vertical else evento.x) / self._largo()

    def _presionar(self, evento):
        """Inicia el arrastre sobre la píldora o avanza una página si el clic cae fuera de ella.

        Entrada: evento del mouse. Salida: None.
        """
        posicion = self._posicion(evento)
        if self.inicio <= posicion <= self.fin:
            self._arrastre = posicion - self.inicio
        else:
            self._arrastre = None
            self.comando("scroll", -1 if posicion < self.inicio else 1, "pages")

    def _arrastrar(self, evento):
        """Desplaza el contenido mientras se arrastra la píldora.

        Entrada: evento del mouse. Salida: None.
        """
        if self._arrastre is not None:
            self.comando("moveto", self._posicion(evento) - self._arrastre)


class AreaDesplazable(_Marco):
    """Contenedor con desplazamiento vertical y horizontal; el contenido se agrega en .interior.

    Las barras solo aparecen cuando el contenido no cabe.
    """

    def __init__(self, parent, fondo, **kwargs):
        """Crea el Canvas con su marco interior y las barras que aparecen solo cuando hacen falta.

        Entrada: contenedor y color de fondo. Salida: None.
        """
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
        """Actualiza la región desplazable y los textos adaptables al cambiar el tamaño."""
        self._actualizar()
        for ajuste in list(self._ajustes):
            ajuste()

    def registrar_ajuste(self, funcion):
        """Registra una función que se llama cuando cambia el ancho visible (textos adaptables).

        Entrada: función que recibe el ancho. Salida: None.
        """
        self._ajustes.append(funcion)
        funcion()

    @staticmethod
    def _ajustar_barra(barra, inicio, fin):
        """Muestra u oculta una barra según si el contenido cabe y actualiza su posición.

        Entrada: barra y fracción visible (inicio, fin). Salida: None.
        """
        visible = float(inicio) > 0.0 or float(fin) < 1.0
        if visible != bool(barra.winfo_manager()):
            if visible:
                barra.grid()
            else:
                barra.grid_remove()
        barra.set(inicio, fin)

    def _actualizar(self, _evento=None):
        """Ajusta el ancho del interior y la región desplazable al contenido actual."""
        ancho = max(self.canvas.winfo_width(), self.interior.winfo_reqwidth())
        self.canvas.itemconfigure(self._ventana, width=ancho)
        self.canvas.configure(scrollregion=(0, 0, ancho, self.interior.winfo_reqheight()))

    def puede_desplazar(self, horizontal=False):
        """Indica si el contenido excede el área en la dirección indicada.

        Entrada: horizontal (bool). Salida: True o False.
        """
        vista = self.canvas.xview() if horizontal else self.canvas.yview()
        return vista != (0.0, 1.0)

    def desplazar(self, pixeles, horizontal=False):
        """Desplaza el contenido la cantidad de píxeles indicada.

        Entrada: píxeles y horizontal (bool). Salida: None.
        """
        pixeles = int(pixeles)
        if pixeles:
            (self.canvas.xview_scroll if horizontal else self.canvas.yview_scroll)(pixeles, "units")

    def al_inicio(self):
        """Lleva la vista a la esquina superior izquierda."""
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def limpiar(self):
        """Elimina el contenido e invalida los llenados en curso."""
        self._token += 1
        self._ajustes = []
        for hijo in self.interior.winfo_children():
            hijo.destroy()

    def llenar(self, constructores, retardo=45):
        """Reemplaza el contenido llamando a cada constructor(interior) con un pequeño retardo (efecto cascada).

        Entrada: lista de constructores y retardo en ms. Salida: None; la ventana sigue respondiendo.
        """
        self.limpiar()
        self.al_inicio()
        token = self._token
        constructores = list(constructores)

        def siguiente(indice):
            """Construye la tarjeta número «indice» y programa la siguiente.

            Entrada: índice del constructor. Salida: None.
            """
            if token != self._token or indice >= len(constructores):
                return
            try:
                constructores[indice](self.interior)
            except tk.TclError:
                return
            self.after(retardo if indice < 25 else 1, lambda: siguiente(indice + 1))

        siguiente(0)


def instalar_desplazamiento(raiz):
    """Instala un único manejador de rueda y trackpad que desplaza el área más cercana bajo el puntero.

    Entrada: ventana raíz. Salida: None; funciona en Windows, macOS y Linux.
    """

    def buscar_area(evento, horizontal):
        """Busca el AreaDesplazable más cercano bajo el puntero que pueda desplazarse.

        Entrada: evento y horizontal (bool). Salida: el área o None.
        """
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
        """Desplaza el área bajo el puntero la cantidad indicada.

        Entrada: evento, píxeles y horizontal (bool). Salida: None.
        """
        try:
            lienzo = raiz.winfo_containing(evento.x_root, evento.y_root)
        except (KeyError, tk.TclError):
            lienzo = None
        if getattr(lienzo, "_recibe_rueda", False):
            lienzo.al_girar_rueda(pixeles, horizontal, evento.x_root, evento.y_root)
            return
        area = buscar_area(evento, horizontal)
        if area is not None:
            area.desplazar(pixeles, horizontal)

    def rueda(evento):
        """Convierte el giro de la rueda del mouse en píxeles y desplaza el área.

        Entrada: evento de la rueda. Salida: None.
        """
        delta = evento.delta
        pixeles = -delta / 120 * 60 if abs(delta) >= 120 else -delta * 8
        mover(evento, pixeles, bool(evento.state & 0x1))

    def tactil(evento):
        """Desplaza con los deltas precisos del trackpad (Tk 9) en ambos ejes.

        Entrada: evento táctil. Salida: None.
        """
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
        raiz.bind_all("<TouchpadScroll>", tactil, add="+")
    except tk.TclError:
        pass


def color_de_fondo(widget):
    """Obtiene el color de fondo efectivo de un widget, subiendo mientras el fondo sea transparente.

    Entrada: widget. Salida: color '#RRGGBB'.
    """
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
    """Base de los controles dibujados en un solo Canvas (zonas clicables con hover).

    Es más liviano que varios CTkButton: en macOS cada widget extra encarece el dibujado.
    """

    def __init__(self, parent):
        """Crea el Canvas, el registro de zonas clicables y los enlaces de movimiento y clic.

        Entrada: contenedor y opciones del Canvas. Salida: None.
        """
        self._esc = escala_de(parent)
        super().__init__(parent, bg=color_de_fondo(parent), highlightthickness=0, bd=0, width=10, height=10)
        self._zonas = {}
        self._hover = None
        self.bind("<Motion>", self._mover)
        self.bind("<Leave>", lambda _e: self._resaltar(None))
        self.bind("<Button-1>", self._clic)

    def _zona_en(self, x, y):
        """Busca la zona activa que contiene el punto.

        Entrada: coordenadas x, y. Salida: clave de la zona o None.
        """
        for clave, (x1, y1, x2, y2, _fondo, activa) in self._zonas.items():
            if activa and x1 <= x <= x2 and y1 <= y <= y2:
                return clave
        return None

    def _mover(self, evento):
        """Resalta la zona bajo el puntero.

        Entrada: evento de movimiento. Salida: None.
        """
        self._resaltar(self._zona_en(evento.x, evento.y))

    def _resaltar(self, clave):
        """Cambia el color de la zona resaltada y el cursor.

        Entrada: clave de la zona (o None). Salida: None.
        """
        if clave == self._hover:
            return
        self._hover = clave
        for k, (_x1, _y1, _x2, _y2, fondo, _activa) in self._zonas.items():
            self.itemconfigure(fondo, fill=resolver_color(PALETA["secundario_hover"] if k == clave
                                                          else self._color_reposo(k)))
        self.configure(cursor="hand2" if clave is not None else "")

    def _color_reposo(self, _clave):
        """Obtiene el color de una zona cuando no está resaltada.

        Salida: color de la paleta.
        """
        return PALETA["entrada"]

    def _clic(self, evento):
        """Activa la zona en la que se hizo clic.

        Entrada: evento del clic. Salida: None.
        """
        clave = self._zona_en(evento.x, evento.y)
        if clave is not None:
            self._activar(clave)

    def _activar(self, clave):
        """Ejecuta la acción de una zona; cada subclase la define.

        Entrada: clave de la zona. Salida: None; lanza NotImplementedError en la base.
        """
        raise NotImplementedError


class Contador(_FichasCanvas):
    """Selector numérico  −  3  +  con límites, dibujado en un solo Canvas."""

    def __init__(self, parent, texto, valor, minimo, maximo, al_cambiar=None, en_linea=False):
        """Crea el selector con su rótulo, límites, valor inicial y la función a llamar al cambiar.

        Entrada: contenedor, texto, valor, mínimo, máximo, al_cambiar y en_linea. Salida: None.
        """
        super().__init__(parent)
        self.texto = texto
        self.minimo = minimo
        self.maximo = maximo
        self.valor = valor
        self.al_cambiar = al_cambiar
        self.en_linea = en_linea
        self._dibujar()

    def _dibujar(self):
        """Dibuja el rótulo, los botones − y + y el valor actual."""
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
        """Obtiene el valor actual del selector.

        Salida: entero.
        """
        return self.valor

    def set(self, valor, notificar=False):
        """Fija el valor dentro de [mínimo, máximo] y, si se pide, notifica el cambio.

        Entrada: valor y notificar (bool). Salida: None.
        """
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
        """Suma delta al valor actual y notifica el cambio.

        Entrada: delta (+1 o −1). Salida: None.
        """
        self.set(self.valor + delta, notificar=True)

    def _activar(self, clave):
        """Resta o suma una unidad según el botón pulsado.

        Entrada: clave del botón ('menos' o 'mas'). Salida: None.
        """
        self.cambiar(-1 if clave == "menos" else 1)
        self._hover = None
        self._resaltar(clave if self._zonas[clave][5] else None)

    def _actualizar_botones(self):
        """Deshabilita − o + cuando el valor llega a un límite."""
        for clave, activa in (("menos", self.valor > self.minimo), ("mas", self.valor < self.maximo)):
            self._zonas[clave][5] = activa
            self.itemconfigure(self._signos[clave],
                               fill=resolver_color(PALETA["primario"] if activa else PALETA["borde"]))


class BarraFichas(_FichasCanvas):
    """Fila de botones pequeños (por ejemplo A, B, (, ᵀ, +) dibujados en un solo Canvas."""

    def __init__(self, parent, fichas, fuente=None):
        """Dibuja en un solo Canvas una fila de fichas clicables.

        Entrada: contenedor, lista de (texto, acción) y fuente. Salida: None.
        """
        super().__init__(parent)
        self.fichas = list(fichas)
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
        """Obtiene el color de las fichas en reposo.

        Salida: color de la paleta.
        """
        return PALETA["secundario"]

    def _activar(self, clave):
        """Ejecuta la acción de la ficha pulsada.

        Entrada: índice de la ficha. Salida: None.
        """
        self.fichas[clave][1]()


TECLAS_SIN_CAMBIO = {"Return", "KP_Enter", "Up", "Down", "Left", "Right", "Tab", "Shift_L", "Shift_R",
                     "Control_L", "Control_R", "Meta_L", "Meta_R", "Alt_L", "Alt_R", "Escape"}


class MatrizEntrada(_Marco):
    """Rejilla de casillas para capturar matrices: valida al escribir, navega con Enter y flechas.

    Al cambiar el tamaño conserva los valores ya escritos.
    """

    ANCHO_CELDA = 60

    def __init__(self, parent, al_cambiar=None):
        """Crea la rejilla vacía.

        Entrada: contenedor y al_cambiar (función llamada cuando cambia algún valor). Salida: None.
        """
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.al_cambiar = al_cambiar
        self.celdas = []
        self.separador = None
        self.encabezados = []
        self.encabezados_fila = None
        self._tarea = None

    def configurar(self, filas, columnas, encabezados, encabezados_fila=None, separador=None, valores=None):
        """Reconstruye la rejilla con el tamaño, encabezados y separador indicados, conservando los valores.

        Entrada: filas, columnas, encabezados, encabezados_fila, separador y valores. Salida: None.
        """
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
            """Calcula la columna de la rejilla de Tk para la columna j, dejando hueco a la barra separadora.

            Entrada: j. Salida: entero.
            """
            return desplazamiento + j + (1 if separador is not None and j >= separador else 0)

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
        """Elige el valor inicial de la casilla (i, j): el indicado, el que ya estaba escrito o 0.

        Entrada: textos anteriores, separador anterior, i, j y valores. Salida: cadena.
        """
        if valores is not None:
            if i < len(valores) and j < len(valores[i]):
                valor = valores[i][j]
                return formatear_numero(valor) if isinstance(valor, Fraction) else str(valor)
            return "0"
        if i >= len(anteriores):
            return "0"
        fila = anteriores[i]
        # En [A | b] el bloque A y la columna b se conservan por separado al cambiar de tamaño.
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
        """Enlaza validación, foco y navegación con Enter y flechas a una casilla.

        Entrada: casilla y su posición (i, j). Salida: None.
        """
        entrada.bind("<KeyRelease>", lambda e: self._al_escribir(entrada, e))
        entrada.bind("<FocusIn>", lambda e: self._al_enfocar(entrada))
        entrada.bind("<FocusOut>", lambda e: self._validar(entrada, enfocada=False))
        entrada.bind("<Return>", lambda e: self._mover(e, i, j, siguiente=True))
        entrada.bind("<KP_Enter>", lambda e: self._mover(e, i, j, siguiente=True))
        entrada.bind("<Down>", lambda e: self._mover(e, i + 1, j))
        entrada.bind("<Up>", lambda e: self._mover(e, i - 1, j))

    def _mover(self, evento, i, j, siguiente=False):
        """Mueve el foco a otra casilla; deja pasar Ctrl/⌘ + Enter para resolver.

        Entrada: evento, posición (i, j) y siguiente. Salida: 'break' si consume el evento, si no None.
        """
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
        """Valida la casilla enfocada y selecciona su texto.

        Entrada: casilla. Salida: None.
        """
        self._validar(entrada, enfocada=True)

        def seleccionar():
            """Selecciona todo el texto de la casilla y deja el cursor al final."""
            try:
                entrada.select_range(0, "end")
                entrada.icursor("end")
            except tk.TclError:
                pass

        entrada.after(1, seleccionar)

    def _al_escribir(self, entrada, evento):
        """Valida mientras se escribe y programa el aviso de cambio.

        Entrada: casilla y evento de teclado. Salida: None.
        """
        if evento.keysym in TECLAS_SIN_CAMBIO:
            return
        self._validar(entrada, enfocada=True)
        if self._tarea is not None:
            self.after_cancel(self._tarea)
        self._tarea = self.after(150, self._notificar)

    def _notificar(self):
        """Llama a al_cambiar tras una pausa en la escritura."""
        self._tarea = None
        if self.al_cambiar is not None:
            self.al_cambiar()

    def _validar(self, entrada, enfocada=False):
        """Pinta el borde de la casilla según si su texto es un número válido.

        Entrada: casilla y enfocada (bool). Salida: True o False.
        """
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
        """Obtiene los textos escritos en todas las casillas.

        Salida: lista anidada de cadenas.
        """
        return [[entrada.get() for entrada in fila] for fila in self.celdas]

    def valores(self):
        """Lee la matriz como Fraction; si una casilla es inválida la enfoca y explica el error.

        Salida: lista anidada de Fraction; lanza ValueError con la casilla inválida.
        """
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
        """Pone 0 en todas las casillas y notifica el cambio."""
        for fila in self.celdas:
            for entrada in fila:
                entrada.delete(0, "end")
                entrada.insert(0, "0")
                self._validar(entrada)
        self._notificar()


class PanelPasos(_Marco):
    """Muestra el procedimiento completo (en cascada) o paso a paso con reproducción automática."""

    def __init__(self, parent, fondo, texto_vacio, constructor):
        """Crea la barra «Todos / Paso a paso», los controles de reproducción y el área de tarjetas.

        Entrada: contenedor, fondo, texto_vacio y constructor(contenedor, pasos, índice, detallado). Salida: None.
        """
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.texto_vacio = texto_vacio
        self.constructor = constructor
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
        """Muestra el mensaje de panel vacío y oculta los controles de navegación.

        Entrada: texto opcional. Salida: None.
        """
        self.detener()
        self.pasos = []
        self.controles.pack_forget()
        self.progreso.grid_remove()
        self.area.llenar([lambda p: placeholder(p, "☰", texto or self.texto_vacio)])

    def mostrar_pasos(self, pasos):
        """Recibe la lista de pasos y los muestra desde el primero.

        Entrada: lista de pasos. Salida: None.
        """
        self.detener()
        self.pasos = list(pasos)
        self.indice = 0
        self._renderizar()

    def _cambiar_modo(self, _valor=None):
        """Cambia entre la vista «Todos» y «Paso a paso»."""
        self.detener()
        if self.pasos:
            self._renderizar()

    def _renderizar(self):
        """Dibuja todos los pasos en cascada o solo el paso actual según el modo."""
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
        """Dibuja el paso actual con su posición y la barra de progreso."""
        total = len(self.pasos)
        self.etiqueta_posicion.configure(text=f"{self.indice + 1} / {total}")
        self.boton_anterior.configure(state="normal" if self.indice > 0 else "disabled")
        self.boton_siguiente.configure(state="normal" if self.indice < total - 1 else "disabled")
        objetivo = (self.indice + 1) / total
        inicio = self.progreso.get()
        animar(self.progreso, 300, lambda t: self.progreso.set(inicio + (objetivo - inicio) * t))

        def construir(parent):
            """Construye la tarjeta detallada del paso actual y la resalta.

            Entrada: contenedor. Salida: None.
            """
            tarjeta = self.constructor(parent, self.pasos, self.indice, True)
            tarjeta.pack(fill="x", padx=2, pady=(0, 12))
            if hasattr(tarjeta, "destello"):
                tarjeta.destello()
            else:
                destello(tarjeta)

        self.area.llenar([construir])

    def ir_a(self, indice):
        """Va al paso indicado, limitado al primero y al último.

        Entrada: índice del paso. Salida: None.
        """
        if not self.pasos:
            return
        self.indice = max(0, min(len(self.pasos) - 1, indice))
        self._renderizar_actual()

    def alternar_reproduccion(self):
        """Inicia o pausa el avance automático de los pasos."""
        if self._tarea_reproducir is not None:
            self.detener()
            return
        if self.indice >= len(self.pasos) - 1:
            self.ir_a(0)
        self.boton_reproducir.configure(text="⏸  Pausar")
        self._tarea_reproducir = self.after(1400, self._avanzar)

    def _avanzar(self):
        """Avanza un paso y reprograma la reproducción hasta el final."""
        self._tarea_reproducir = None
        self.ir_a(self.indice + 1)
        if self.indice < len(self.pasos) - 1:
            self._tarea_reproducir = self.after(1400, self._avanzar)
        else:
            self.detener()

    def detener(self):
        """Detiene la reproducción automática."""
        if self._tarea_reproducir is not None:
            self.after_cancel(self._tarea_reproducir)
            self._tarea_reproducir = None
        self.boton_reproducir.configure(text="▶  Reproducir")


class SeccionPlegable(_Marco):
    """Sección que se abre o cierra al hacer clic en su cabecera; el cuerpo se crea al abrirla."""

    def __init__(self, parent, titulo, detalle, correcto, construir, abierto=False, estado=None):
        """Crea una cabecera clicable; construir llena el cuerpo al abrirse.

        Entrada: contenedor, título, detalle, correcto, construir, abierto y estado=(texto, color). Salida: None.
        """
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
        """Abre o cierra la sección; el cuerpo se construye la primera vez."""
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
    """Notificaciones flotantes que entran deslizándose por la esquina inferior derecha."""

    COLORES = {"exito": "exito", "error": "error", "info": "primario", "aviso": "advertencia"}
    ICONOS = {"exito": "✓", "error": "✕", "info": "i", "aviso": "!"}

    def __init__(self, ventana):
        """Prepara el aviso flotante de la ventana.

        Entrada: ventana principal. Salida: None.
        """
        self.ventana = ventana
        self.actual = None
        self._tarea = None

    def mostrar(self, texto, tipo="info", duracion=3400):
        """Muestra un aviso con el color de su tipo durante la duración indicada.

        Entrada: texto, tipo (info, exito, aviso o error) y duración en ms. Salida: None.
        """
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
        """Oculta el aviso actual, con o sin animación.

        Entrada: inmediato (bool). Salida: None.
        """
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
    """Elemento del menú lateral con icono, texto y estados hover y activo."""

    def __init__(self, parent, icono, texto, comando):
        """Crea el elemento del menú lateral.

        Entrada: contenedor, icono, texto y comando al hacer clic. Salida: None.
        """
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
        """Marca o desmarca el elemento como sección activa.

        Entrada: activo (bool). Salida: None.
        """
        self.activo = activo
        self.configure(fg_color=PALETA["secundario"] if activo else "transparent")
        self.icono.configure(text_color=PALETA["primario"] if activo else PALETA["texto_3"])
        self.texto.configure(text_color=PALETA["texto"] if activo else PALETA["texto_2"],
                             font=FUENTE_NEGRITA if activo else FUENTE_NORMAL)

    def _entrar(self, _evento):
        """Resalta el elemento al pasar el puntero."""
        if not self.activo:
            self.configure(fg_color=PALETA["panel_2"])

    def _salir(self, _evento):
        """Quita el resaltado al salir el puntero."""
        if not self.activo and not es_descendiente(widget_bajo_puntero(self), self):
            self.configure(fg_color="transparent")



def tarjeta_estado(parent, titulo, descripcion, color, icono):
    """Crea la tarjeta principal del resultado con icono de estado y un brillo inicial.

    Entrada: contenedor, título, descripción, color e icono. Salida: CTkFrame de la tarjeta.
    """
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
    """Crea una fila de indicadores numéricos; los enteros se animan contando desde 0.

    Entrada: contenedor y lista de (valor, etiqueta). Salida: CTkFrame de la fila.
    """
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
    """Elige el color y el icono según la clasificación del sistema.

    Entrada: resultado de resolver_sistema. Salida: (color, icono).
    """
    clasificacion = resultado["clasificacion"]
    if clasificacion == "Sistema inconsistente":
        return PALETA["error"], "✕"
    if clasificacion == "Sistema consistente indeterminado":
        return PALETA["advertencia"], "∞"
    return PALETA["exito"], "✓"


def tarjeta_solucion_unica(parent, solucion, nombres, simbolo="x", titulo="Solución única"):
    """Crea la tarjeta con el vector solución y el valor de cada variable.

    Entrada: contenedor, solución, nombres, símbolo y título. Salida: CTkFrame de la tarjeta.
    """
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
    """Crea la tarjeta con las variables básicas en función de los parámetros y la forma x = p + Σ t·v.

    Entrada: contenedor, resultado, símbolo y título. Salida: CTkFrame de la tarjeta.
    """
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
    """Crea la tarjeta con la fila 0 = c (c ≠ 0) que hace inconsistente al sistema.

    Entrada: contenedor y resultado. Salida: CTkFrame de la tarjeta.
    """
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


def tarjeta_mensajes(parent, titulo, mensajes, color="advertencia"):
    """Crea una tarjeta con un título y una lista de mensajes con viñetas.

    Entrada: contenedor, título, mensajes y color. Salida: CTkFrame de la tarjeta.
    """
    tarjeta = tarjeta_seccion(parent, titulo)
    for mensaje in mensajes:
        fila = ctk.CTkFrame(tarjeta, fg_color="transparent")
        fila.pack(fill="x", padx=16, pady=(0, 8))
        etiqueta(fila, "●", FUENTE_PEQUENA, color).pack(side="left", anchor="n", padx=(0, 8), pady=2)
        etiqueta(fila, mensaje, FUENTE_NORMAL, "texto_2", ajustar=64).pack(side="left", anchor="w")
    ctk.CTkFrame(tarjeta, fg_color="transparent", height=6).pack()
    return tarjeta


def constructores_solucion(resultado, simbolo="x"):
    """Elige la tarjeta de solución: única, paramétrica o explicación de la inconsistencia.

    Entrada: resultado del sistema y símbolo de las incógnitas. Salida: lista de constructores.
    """
    if resultado["solucion"] is not None:
        return [lambda p: tarjeta_solucion_unica(p, resultado["solucion"], resultado["nombres_variables"], simbolo)]
    if resultado["expresiones"] is not None:
        return [lambda p: tarjeta_solucion_parametrica(p, resultado, simbolo)]
    return [lambda p: tarjeta_inconsistente(p, resultado)]


def cuerpo_etapa(parent, paso, detallado=False):
    """Dibuja el contenido de una etapa: explicación, fórmula, valores, condiciones, cálculos y subpasos.

    Entrada: contenedor, etapa y detallado (bool). Salida: None.
    """
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
        """Agrega los cálculos de la etapa, uno por línea.

        Entrada: marco. Salida: None.
        """
        for linea in paso["calculos"]:
            etiqueta(marco, linea, FUENTE_MONO, "texto_2", ajustar=40).pack(anchor="w", padx=16, pady=2)
    if len(paso["calculos"]) > 8:
        SeccionPlegable(parent, "Cálculo de cada entrada", f"{len(paso['calculos'])} cálculos", True, lineas,
                        abierto=detallado, estado=("Ver detalle", "primario")).pack(fill="x", padx=12, pady=(4, 8))
    else:
        lineas(parent)
    if paso["subpasos"]:
        def desarrollar(marco):
            """Agrega las tarjetas de los subpasos de la etapa.

            Entrada: marco. Salida: None.
            """
            for i in range(len(paso["subpasos"])):
                tarjeta_etapa(marco, paso["subpasos"], i, detallado).pack(fill="x", padx=4, pady=(0, 8))
        SeccionPlegable(parent, "Desarrollar el cálculo", "Operaciones intermedias", True, desarrollar,
                        abierto=detallado, estado=("Ver pasos", "primario")).pack(fill="x", padx=12, pady=(6, 8))
    if paso["conclusion"]:
        etiqueta(parent, paso["conclusion"], FUENTE_NEGRITA,
                 "error" if paso["conclusion"].startswith("No se cumple") else "exito", ajustar=40).pack(anchor="w", padx=16, pady=(6, 8))


def tarjeta_etapa(parent, pasos, indice, detallado=False):
    """Crea la tarjeta de una etapa para PanelPasos.

    Entrada: contenedor, lista de etapas, índice y detallado (bool). Salida: CTkFrame de la tarjeta.
    """
    paso = pasos[indice]
    tarjeta = crear_tarjeta(parent, f"Paso {indice+1} — {paso['titulo']}", fondo=PALETA["panel_2"])
    cuerpo_etapa(tarjeta, paso, detallado)
    ctk.CTkFrame(tarjeta, fg_color="transparent", height=8).pack()
    return tarjeta


def constructores_etapas(etapas):
    """Prepara un constructor de tarjeta por cada etapa.

    Entrada: lista de etapas. Salida: lista de constructores.
    """
    return [lambda p, i=i: tarjeta_etapa(p, etapas, i).pack(fill="x", padx=2, pady=(0, 12)) for i in range(len(etapas))]


def constructores_chequeo(informe):
    """Prepara la pestaña Verificación: estado global (o motivo) y una tarjeta por etapa.

    Entrada: informe con «correcto», «etapas» y, si no aplica, «motivo». Salida: lista de constructores.
    """
    if informe.get("aplicable") is False:
        motivo = informe.get("motivo", "La operación no está definida con estos datos.")
        return [lambda p: tarjeta_mensajes(p, "No hay resultado que verificar", [motivo], "advertencia"),
                *constructores_etapas(informe["etapas"])]
    correcto = informe["correcto"]
    return [lambda p: tarjeta_estado(p, "Verificación superada" if correcto else "Verificación con diferencias",
                                     "Comprobación exacta con los datos originales; el detalle aparece a continuación.",
                                     PALETA["exito"] if correcto else PALETA["error"], "✓" if correcto else "✗"),
            *constructores_etapas(informe["etapas"])]


def constructores_informe(informe):
    """Prepara la respuesta breve de un informe (título, resultado y valores) para la pestaña Resultado.

    Entrada: informe de determinante, inversa o propiedad. Salida: lista de constructores.
    """
    lista = [lambda p: tarjeta_estado(p, informe["titulo"], informe["conclusion"],
             PALETA["exito"] if informe["definido"] else PALETA["advertencia"], "✓" if informe["definido"] else "!")]
    if informe.get("datos_resultado"):
        datos_originales = informe["datos_resultado"]
        lista.append(lambda p: cuerpo_etapa(tarjeta_seccion(p, "Datos y operación"), datos_originales))
    for intermedio in informe.get("intermedios", []):
        lista.append(lambda p, e=intermedio: cuerpo_etapa(tarjeta_seccion(p, e["titulo"]), e, detallado=True))
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
    """Crea la fila de indicadores: rango de A, rango de [A | b], variables básicas y libres.

    Entrada: contenedor, resultado y etiqueta del rango. Salida: CTkFrame de la fila.
    """
    return fila_indicadores(parent, [
        (resultado["rango"], etiqueta_rango),
        (resultado["rango_aumentada"], "Rango de [A | b]"),
        (len(resultado["variables_basicas"]), "Variables básicas"),
        (len(resultado["variables_libres"]), "Variables libres"),
    ])


def fila_copiar(parent, app, texto):
    """Crea el botón «Copiar resultado» que copia el texto al portapapeles.

    Entrada: contenedor, aplicación y texto. Salida: CTkFrame con el botón.
    """
    fila = ctk.CTkFrame(parent, fg_color="transparent")
    fila.pack(fill="x", padx=2, pady=(0, 16))
    boton_secundario(fila, "⧉  Copiar resultado", lambda: app.copiar(texto), width=170).pack(side="left")
    return fila


def tarjeta_encadenar(parent, titulo, descripcion, acciones):
    """Crea botones que llevan un resultado a otra sección sin volver a escribirlo.

    Entrada: contenedor, título, descripción y lista de (texto, acción). Salida: CTkFrame de la tarjeta.
    """
    tarjeta = tarjeta_seccion(parent, titulo, descripcion)
    for texto, comando in acciones:
        boton_secundario(tarjeta, "↪  " + texto, comando, height=34).pack(anchor="w", padx=16, pady=(0, 8))
    ctk.CTkFrame(tarjeta, fg_color="transparent", height=6).pack()
    return tarjeta


def columnas_de(matriz):
    """Separa las columnas de una matriz.

    Entrada: matriz m × n. Salida: lista de n vectores.
    """
    return [[fila[j] for fila in matriz] for j in range(len(matriz[0]))]



class PaginaBase(_Marco):
    """Página con encabezado (título, subrayado animado y subtítulo); base de todas las secciones."""
    titulo = ""
    subtitulo = ""

    def __init__(self, parent, app):
        """Crea el encabezado de la página con el título y el subtítulo de la clase.

        Entrada: contenedor y aplicación. Salida: None.
        """
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
        """Anima el subrayado del título al mostrar la página."""
        animar(self._subrayado, 500, lambda t: self._subrayado.configure(width=max(1, round(72 * t))))


class PaginaSistema(PaginaBase):
    """Plantilla de las secciones de sistemas: barra arriba, datos a la izquierda y pestañas a la derecha.

    Las subclases definen la rejilla, la vista previa, el cálculo y la presentación del resultado.
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
        """Crea la barra, el contenido y carga el ejemplo inicial de la sección.

        Entrada: contenedor y aplicación. Salida: None.
        """
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


    def _crear_barra(self):
        """Crea la barra superior: contadores de tamaño, controles extra, ejemplos y acciones."""
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
        """Permite a una subclase agregar controles a la barra superior.

        Entrada: fila de la barra. Salida: None.
        """

    def _abrir_ejemplos(self):
        """Abre el menú de ejemplos debajo de su botón."""
        boton = self.boton_ejemplos
        self.menu_ejemplos.tk_popup(boton.winfo_rootx(), boton.winfo_rooty() + boton.winfo_height() + 4)

    def _crear_contenido(self):
        """Crea la tarjeta de datos con vista previa y las pestañas Resultado, Procedimiento y Verificación."""
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
        """Crea la rejilla de captura de la matriz.

        Entrada: contenedor. Salida: None.
        """
        self.matriz = MatrizEntrada(parent, al_cambiar=self._al_cambiar_datos)
        self.matriz.pack(anchor="w", padx=4, pady=4)

    def crear_procedimiento(self, pestana):
        """Crea el panel de pasos de la pestaña Procedimiento.

        Entrada: pestaña. Salida: None.
        """
        self.panel_pasos = PanelPasos(pestana, PALETA["panel"], self.vacio_pasos, constructor=tarjeta_etapa)
        self.panel_pasos.pack(fill="both", expand=True)


    def configuracion_rejilla(self, filas, columnas):
        """Define columnas, encabezados y separador de la rejilla; cada subclase lo implementa.

        Entrada: filas y columnas. Salida: diccionario de configuración.
        """
        raise NotImplementedError

    def texto_dimension(self, filas, columnas):
        """Escribe el texto del chip con las dimensiones actuales.

        Entrada: filas y columnas. Salida: cadena.
        """
        return f"{filas} × {columnas}"

    def configurar_entradas(self, filas, columnas, valores):
        """Reconfigura la rejilla con el tamaño y los valores indicados.

        Entrada: filas, columnas y valores opcionales. Salida: None.
        """
        cfg = self.configuracion_rejilla(filas, columnas)
        self.matriz.configurar(filas, cfg["columnas"], cfg["encabezados"], cfg.get("encabezados_fila"),
                               cfg.get("separador"), valores)

    def reconstruir(self, valores=None):
        """Reconstruye la rejilla con el tamaño de los contadores y actualiza la vista previa.

        Entrada: valores opcionales. Salida: None.
        """
        filas, columnas = self.contador_filas.get(), self.contador_columnas.get()
        self.configurar_entradas(filas, columnas, valores)
        self.etiqueta_dimension.configure(text=self.texto_dimension(filas, columnas))
        self._al_cambiar_datos()

    def valores_previa(self):
        """Lee los valores escritos para la vista previa.

        Salida: lista anidada con números o None en las casillas inválidas.
        """
        return [[_numero_o_nada(texto) for texto in fila] for fila in self.matriz.textos()]

    def construir_previa(self, parent, valores):
        """Dibuja la vista previa de los datos; cada subclase la define.

        Entrada: contenedor y valores. Salida: None.
        """
        raise NotImplementedError

    def _al_cambiar_datos(self):
        """Redibuja la vista previa y avisa que el resultado anterior quedó desactualizado."""
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
        """Lee la matriz escrita como Fraction.

        Salida: lista anidada; lanza ValueError con la casilla inválida.
        """
        return self.matriz.valores()

    def limpiar_entradas(self):
        """Pone en 0 todas las casillas."""
        self.matriz.limpiar()

    def valores_aleatorios(self, filas, columnas):
        """Genera un sistema aleatorio con solución entera.

        Entrada: filas y columnas. Salida: matriz aumentada [A | b].
        """
        A, b = sistema_aleatorio(filas, columnas)
        return [fila + [bi] for fila, bi in zip(A, b)]


    def establecer_datos(self, filas, columnas, valores):
        """Carga datos completos (un ejemplo o el resultado de otra sección) ajustando el tamaño.

        Entrada: filas, columnas y valores. Salida: None.
        """
        self.contador_filas.set(filas)
        self.contador_columnas.set(columnas)
        self.reconstruir(valores)
        destello(self.tarjeta_datos)

    def cargar_ejemplo(self, nombre):
        """Carga un ejemplo de la sección y lo notifica.

        Entrada: nombre del ejemplo. Salida: None.
        """
        self.establecer_datos(*self.ejemplos[nombre])
        self.app.notificar(f"Ejemplo cargado: {nombre}. Presiona «{self.texto_boton}».", "info")

    def aleatorio(self):
        """Llena la rejilla con datos aleatorios del tamaño actual."""
        filas, columnas = self.contador_filas.get(), self.contador_columnas.get()
        self.reconstruir(self.valores_aleatorios(filas, columnas))
        destello(self.tarjeta_datos)
        self.app.notificar("Se generaron datos aleatorios.", "info")

    def limpiar(self):
        """Limpia las casillas y vacía las tres pestañas."""
        self.resultado = None
        self.limpiar_entradas()
        self.mostrar_vacio()

    def mostrar_vacio(self):
        """Muestra los mensajes iniciales en Resultado, Procedimiento y Verificación."""
        self.resultado = None
        self.aviso.grid_remove()
        self.area_resultado.llenar([lambda p: placeholder(p, "∑", self.vacio_resultado)])
        self.procedimiento_vacio()
        self.area_verificacion.llenar([lambda p: placeholder(p, "✓", "Aquí se comprobará el resultado con los datos originales.")])

    def procedimiento_vacio(self):
        """Muestra el mensaje inicial del panel de pasos."""
        self.panel_pasos.mostrar_placeholder()

    def resolver(self):
        """Lee los datos, calcula y llena las tres pestañas; ante un error lo explica sin cerrarse."""
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
        """Calcula el resultado de la sección; cada subclase lo define.

        Entrada: datos leídos. Salida: diccionario del resultado.
        """
        raise NotImplementedError

    def construir_resultado(self, resultado):
        """Prepara las tarjetas de la pestaña Resultado; cada subclase lo define.

        Entrada: resultado. Salida: lista de constructores.
        """
        raise NotImplementedError

    def mostrar_procedimiento(self, resultado):
        """Muestra las etapas de la eliminación en la pestaña Procedimiento.

        Entrada: resultado. Salida: None.
        """
        self.panel_pasos.mostrar_pasos(didactica.procedimiento_sistema(resultado, self.es_combinacion, self.es_independencia))

    def mostrar_verificacion(self, resultado):
        """Muestra la verificación con los datos originales.

        Entrada: resultado. Salida: None.
        """
        informe = didactica.verificacion_sistema(resultado, self.es_combinacion, self.es_independencia)
        self.area_verificacion.llenar(constructores_chequeo(informe), retardo=45)

    def texto_copiar(self, resultado):
        """Escribe el resultado en texto plano para el portapapeles.

        Entrada: resultado. Salida: cadena.
        """
        return resumen_texto(resultado)

    def mensaje_resuelto(self, resultado):
        """Resume el resultado en una notificación.

        Entrada: resultado. Salida: (texto, tipo).
        """
        operaciones = len(resultado["pasos"]) - 2
        tipo = {"Sistema inconsistente": "error",
                "Sistema consistente indeterminado": "aviso"}.get(resultado["clasificacion"], "exito")
        return f"{resultado['clasificacion']} · {operaciones} operaciones elementales.", tipo


def _numero_o_nada(texto):
    """Convierte el texto en número si es válido.

    Entrada: texto. Salida: Fraction o None.
    """
    try:
        return convertir_numero(texto)
    except ValueError:
        return None


class PaginaCalculadora(PaginaSistema):
    """Página «Calculadora»: sistemas de ecuaciones por Gauss-Jordan."""
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
        """Define la rejilla [A | b] con las variables x1…xn y la columna b.

        Entrada: filas y columnas. Salida: diccionario de configuración.
        """
        return {
            "columnas": columnas + 1,
            "encabezados": obtener_nombres_variables(columnas) + ["b"],
            "encabezados_fila": [f"F{i + 1}" for i in range(filas)],
            "separador": columnas,
        }

    def texto_dimension(self, filas, columnas):
        """Escribe 'm ecuaciones × n variables'.

        Entrada: filas y columnas. Salida: cadena.
        """
        return f"{filas} ecuaciones × {columnas} variables"

    def construir_previa(self, parent, valores):
        """Muestra cada ecuación escrita en forma algebraica.

        Entrada: contenedor y valores. Salida: None.
        """
        nombres = obtener_nombres_variables(len(valores[0]) - 1)
        for i, fila in enumerate(valores):
            if any(v is None for v in fila):
                etiqueta(parent, f"F{i + 1}: hay un valor no válido", FUENTE_MONO, "error").pack(anchor="w")
            else:
                etiqueta(parent, formatear_ecuacion_original(fila[:-1], fila[-1], nombres),
                         FUENTE_MONO, "texto").pack(anchor="w")

    def calcular(self, matriz):
        """Separa [A | b] y resuelve el sistema por Gauss-Jordan.

        Entrada: matriz aumentada. Salida: diccionario de resolver_sistema.
        """
        return resolver_sistema([fila[:-1] for fila in matriz], [fila[-1] for fila in matriz])

    def construir_resultado(self, resultado):
        """Prepara las tarjetas de clasificación, indicadores y solución.

        Entrada: resultado. Salida: lista de constructores.
        """
        color, icono = estado_de_sistema(resultado)
        descripcion = resultado["descripcion"]
        if resultado["homogeneo"]:
            descripcion += " Es un sistema homogéneo (Ax = 0)."
        return [
            lambda p: tarjeta_estado(p, resultado["clasificacion"], descripcion, color, icono),
            lambda p: indicadores_sistema(p, resultado),
        ] + constructores_solucion(resultado) + constructores_render_sistema(self.app, resultado)


class PaginaAxb(PaginaSistema):
    """Página «Ecuación Ax = b»: el sistema como producto matriz-vector."""
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
        """Define la rejilla [A | b] con las columnas a1…an y b.

        Entrada: filas y columnas. Salida: diccionario de configuración.
        """
        return {
            "columnas": columnas + 1,
            "encabezados": [f"a{j + 1}" for j in range(columnas)] + ["b"],
            "encabezados_fila": [f"F{i + 1}" for i in range(filas)],
            "separador": columnas,
        }

    def texto_dimension(self, filas, columnas):
        """Escribe 'A es m × n'.

        Entrada: filas y columnas. Salida: cadena.
        """
        return f"A es {filas} × {columnas}"

    def construir_previa(self, parent, valores):
        """Muestra A·x = b y su lectura como combinación de columnas.

        Entrada: contenedor y valores. Salida: None.
        """
        A = [fila[:-1] for fila in valores]
        b = [fila[-1] for fila in valores]
        n = len(A[0])
        dibujar_expresion(parent, [A, obtener_nombres_variables(n), "=", b], tamano=12).pack(anchor="w")
        columnas = " + ".join(f"x{j + 1}·a{j + 1}" for j in range(n))
        etiqueta(parent, f"Equivale a {columnas} = b, donde a1, …, a{n} son las columnas de A.",
                 FUENTE_PEQUENA, "texto_3", ajustar=48).pack(anchor="w", pady=(6, 0))

    def calcular(self, matriz):
        """Separa [A | b] y resuelve el sistema por Gauss-Jordan.

        Entrada: matriz aumentada. Salida: diccionario de resolver_sistema.
        """
        return resolver_sistema([fila[:-1] for fila in matriz], [fila[-1] for fila in matriz])

    def construir_resultado(self, resultado):
        """Prepara las tarjetas de clasificación, solución y encadenamiento con la factorización LU.

        Entrada: resultado. Salida: lista de constructores.
        """
        color, icono = estado_de_sistema(resultado)
        A = [fila[:-1] for fila in resultado["matriz_inicial"]]
        b = [fila[-1] for fila in resultado["matriz_inicial"]]
        constructores = [
            lambda p: tarjeta_estado(p, resultado["clasificacion"], resultado["descripcion"], color, icono),
            lambda p: indicadores_sistema(p, resultado),
        ] + constructores_solucion(resultado)
        constructores.append(lambda p: tarjeta_encadenar(
            p, "Encadenar con «Factorización LU»", "Los mismos A y b se resuelven con A = LU, Ly = b y Ux = y.",
            [("Resolver este sistema por factorización LU", lambda: self._enviar_a_lu(A, b))]))
        return constructores + constructores_render_sistema(self.app, resultado)

    def _enviar_a_lu(self, A, b):
        """Encadena A y b a la página de factorización LU y la resuelve.

        Entrada: A y b. Salida: None.
        """
        pagina = self.app.ir_a("lu")
        pagina.establecer_datos(len(A), len(A[0]), [fila + [bi] for fila, bi in zip(A, b)])
        pagina.resolver()


class PaginaLU(PaginaSistema):
    """Página «Factorización LU y solución Ax = b»: L, U, Ly = b, Ux = y y sus verificaciones."""

    titulo = "Factorización LU y solución Ax = b"
    subtitulo = ("A = LU solo con reemplazos de filas, verificación L · U == A y solución en dos etapas: "
                 "Ly = b (hacia adelante) y Ux = y (hacia atrás)")
    etiqueta_filas = "Filas de A (m)"
    etiqueta_columnas = "Columnas de A (n)"
    titulo_datos = "Matriz A y vector b"
    texto_boton = "Factorizar y resolver"
    ejemplos = {
        "Ejemplo del libro (4×4)": (4, 4, [[3, -7, -2, 2, -9], [-3, 5, 1, 0, 5], [6, -4, 0, -5, 7],
                                           [-9, 5, -5, 12, 11]]),
        "Solución única (3×3)": (3, 3, [[2, 1, 1, 5], [4, -6, 0, -2], [-2, 7, 2, 9]]),
        "Rectangular 4×5 (infinitas)": (4, 5, [[2, 4, -1, 5, -2, 7], [-4, -5, 3, -8, 1, -12],
                                               [2, -5, -4, 1, 8, 3], [-6, 0, 7, -3, 1, -9]]),
        "Columna sin pivote (3×3)": (3, 3, [[1, 2, 3, 6], [2, 4, 7, 13], [3, 6, 10, 19]]),
        "Sistema inconsistente": (3, 3, [[1, 2, 3, 6], [2, 4, 7, 13], [3, 6, 10, 20]]),
        "Con fracciones": (2, 2, [["1/2", "1/3", "5/6"], [1, -1, 0]]),
        "Requiere intercambio (sin LU)": (3, 3, [[0, 2, 1, 3], [1, 1, 1, 3], [2, 1, 3, 6]]),
    }
    ejemplo_inicial = "Ejemplo del libro (4×4)"
    vacio_resultado = "Escribe A y b y presiona «Factorizar y resolver»."
    vacio_pasos = ("Aquí aparecerá cada reemplazo con su multiplicador, la reducción de [L | b] (Ly = b) "
                   "y la reducción de [U | y] (Ux = y).")

    def controles_extra(self, fila):
        """Agrega a la barra el acceso «0. Ver Teoremas Clave del Módulo».

        Entrada: fila de la barra. Salida: None.
        """
        grupo = ctk.CTkFrame(fila, fg_color="transparent")
        grupo.pack(side="left", padx=(0, 18))
        etiqueta(grupo, "Teoría", FUENTE_PEQUENA_NEGRITA, "texto_3").pack(anchor="w", pady=(0, 4))
        boton_secundario(grupo, "0. Ver Teoremas Clave del Módulo", self.mostrar_teoremas, width=250,
                         height=34).pack(anchor="w")

    def construir_entradas(self, parent):
        """Muestra el logotipo ASCII del módulo sobre la rejilla de A y b.

        Entrada: contenedor. Salida: None.
        """
        etiqueta(parent, LOGO_LU.strip("\n"), (FAMILIA_MONO, 10), "primario", justify="left").pack(
            anchor="w", padx=4, pady=(0, 8))
        super().construir_entradas(parent)

    def mostrar_teoremas(self):
        """Llena la pestaña Resultado con los teoremas clave del módulo LU."""
        self.area_resultado.llenar(
            [lambda p: tarjeta_estado(p, "0. Ver Teoremas Clave del Módulo", "Factorización LU y solución de Ax = b.",
                                      PALETA["primario"], "0")]
            + [lambda p, n=n, t=t, d=d: tarjeta_numerada(p, n, t, d) for n, (t, d) in enumerate(TEOREMAS_LU, 1)],
            retardo=45)
        self.pestanas.set("Resultado")

    def configuracion_rejilla(self, filas, columnas):
        """Define la rejilla [A | b]: columnas a1…an, la columna b y una barra separadora.

        Entrada: filas y columnas. Salida: diccionario de configuración.
        """
        return {
            "columnas": columnas + 1,
            "encabezados": [f"a{j + 1}" for j in range(columnas)] + ["b"],
            "encabezados_fila": [f"F{i + 1}" for i in range(filas)],
            "separador": columnas,
        }

    def texto_dimension(self, filas, columnas):
        """Escribe las dimensiones de A, L y U.

        Entrada: filas y columnas. Salida: cadena.
        """
        return f"A {filas} × {columnas} · L {filas} × {filas} · U {filas} × {columnas}"

    def construir_previa(self, parent, valores):
        """Muestra Ax = b y las tres etapas del método.

        Entrada: contenedor y valores. Salida: None.
        """
        matriz_A = [fila[:-1] for fila in valores]
        vector_b = [fila[-1] for fila in valores]
        dibujar_expresion(parent, [matriz_A, obtener_nombres_variables(len(matriz_A[0])), "=", vector_b],
                          tamano=12).pack(anchor="w")
        for texto in ("1. A = LU con reemplazos Fi ← Fi − l·Fj (sin intercambios ni escalamientos).",
                      "2. Hacia adelante: reducir [L | b] da el vector intermedio y.",
                      "3. Hacia atrás: reducir [U | y] da la solución x."):
            etiqueta(parent, texto, FUENTE_PEQUENA, "texto_3", ajustar=48).pack(anchor="w", pady=(4, 0))

    def valores_aleatorios(self, filas, columnas):
        """Genera [A | b] aleatorio como producto L·U, para que A = LU exista sin permutar, con solución entera.

        Entrada: filas y columnas. Salida: matriz aumentada [A | b].
        """
        # Se parte de L y U enteras con pivotes no nulos para que A = LU exista sin intercambios.
        matriz_L = [[1 if i == j else random.randint(-3, 3) if j < i else 0 for j in range(filas)] for i in range(filas)]
        matriz_U = [[random.choice([-3, -2, -1, 1, 2, 3]) if i == j else random.randint(-4, 4) if j > i else 0
                     for j in range(columnas)] for i in range(filas)]
        vector_x = [random.randint(-3, 3) for _ in range(columnas)]
        return [fila + [sum(a * v for a, v in zip(fila, vector_x))] for fila in multiplicar_matrices(matriz_L, matriz_U)]

    def calcular(self, matriz):
        """Separa [A | b] y encadena la resolución completa por LU.

        Entrada: matriz aumentada. Salida: diccionario de resolver_lu.
        """
        return modulo_lu.resolver_lu([fila[:-1] for fila in matriz], [fila[-1] for fila in matriz])

    def construir_resultado(self, resultado):
        """Prepara las tarjetas de estado, mensajes de verificación, L, U, y, x y encadenamientos.

        Entrada: resultado de resolver_lu. Salida: lista de constructores.
        """
        a_gauss = ("Resolver con Gauss-Jordan en «Ecuación Ax = b»", lambda: self._enviar_a_axb(resultado))
        if not resultado["existe"]:
            bloqueo = resultado["factorizacion"]["etapas"][-1]
            return [
                lambda p: tarjeta_estado(p, "Factorización LU no disponible", resultado["mensaje"],
                                         PALETA["advertencia"], "!"),
                lambda p: cuerpo_etapa(tarjeta_seccion(p, "Dónde se detiene la eliminación"), bloqueo),
                lambda p: tarjeta_encadenar(p, "Encadenar con otra sección",
                                            "Gauss-Jordan sí permite intercambios y resuelve el mismo sistema.", [a_gauss]),
            ]
        color, icono = estado_de_sistema(resultado)
        operaciones = resultado["factorizacion"]["operaciones"]
        mensajes = [resultado["verificacion_factorizacion"]["mensaje"], resultado["comprobacion"]["mensaje"]]
        verificado = resultado["verificacion_factorizacion"]["correcta"] and resultado["comprobacion"]["correcta"] is not False
        factorizacion = didactica.etapa(
            "A = LU", valores=[didactica.valor("L", resultado["matriz_L"]),
                               didactica.valor("U", resultado["matriz_U"], pivotes=resultado["pivotes"])],
            calculos=[f"l{o['fila'] + 1},{o['fila_pivote'] + 1} = {formatear_numero(o['multiplicador'])}   ({o['operacion']})"
                      for o in operaciones] or ["Sin reemplazos: A ya estaba en forma escalonada y L = I."])
        intermedio = didactica.etapa("y", valores=[didactica.valor("y", resultado["vector_y"])])
        constructores = [
            lambda p: tarjeta_estado(p, f"A = LU · {resultado['clasificacion']}",
                                     f"{resultado['descripcion']} El detalle de cada comprobación está en la pestaña "
                                     f"Verificación.", color, icono),
            lambda p: tarjeta_mensajes(p, "Verificación", mensajes, "exito" if verificado else "error"),
            lambda p: fila_indicadores(p, [(resultado["rango"], "Pivotes"), (len(operaciones), "Reemplazos"),
                                           (resultado["m"], "Filas (m)"), (resultado["n"], "Columnas (n)")]),
            lambda p: cuerpo_etapa(tarjeta_seccion(p, "Factorización A = LU",
                                                   "L guarda los multiplicadores en el orden en que se usaron; "
                                                   "U es la forma escalonada de A."), factorizacion),
            lambda p: cuerpo_etapa(tarjeta_seccion(p, "1. Sustitución hacia adelante: Ly = b",
                                                   "Vector intermedio y; es la entrada de la etapa siguiente."), intermedio),
        ]
        titulo = "2. Sustitución hacia atrás: Ux = y"
        if resultado["solucion"] is not None:
            constructores.append(lambda p: tarjeta_solucion_unica(p, resultado["solucion"], resultado["nombres_variables"],
                                                                  titulo=f"{titulo} → solución única"))
        elif resultado["expresiones"] is not None:
            constructores.append(lambda p: tarjeta_solucion_parametrica(p, resultado,
                                                                        titulo=f"{titulo} → infinitas soluciones"))
        else:
            constructores.append(lambda p: tarjeta_inconsistente(p, resultado))
        if resultado["determinante"] is not None:
            det = resultado["determinante"]
            constructores.append(lambda p: tarjeta_mensajes(p, "Determinante a partir de U", [
                f"det(A) = det(L)·det(U) = ∏ uᵢᵢ = {formatear_numero(det)}",
                "A es invertible (det(A) ≠ 0)." if det != 0 else "A es singular (det(A) = 0): no tiene inversa."],
                "primario"))
        constructores.append(lambda p: tarjeta_lienzo(
            p, "Mapa de calor de L y U", "El color indica el tamaño y el signo de cada entrada: se ven los ceros que crea la eliminación.",
            lambda ancho, _alto: graficos.escena_mapa_calor([("L", resultado["matriz_L"]), ("U", resultado["matriz_U"])], ancho)))
        constructores.append(lambda p: tarjeta_encadenar(
            p, "Encadenar con otras secciones", "Los datos pasan tal cual, sin volver a escribirlos.",
            [("Comprobar L·U = A en «Operaciones matriciales»", lambda: self._enviar_a_operaciones(resultado)),
             a_gauss]))
        return constructores

    def _enviar_a_operaciones(self, resultado):
        """Encadena L, U y A original como A, B y C de Operaciones matriciales y calcula AB − C.

        Entrada: resultado de resolver_lu. Salida: None.
        """
        pagina = self.app.ir_a("matrices")
        for nombre, matriz in (("A", resultado["matriz_L"]), ("B", resultado["matriz_U"]), ("C", resultado["matriz_A"])):
            pagina.establecer_matriz(nombre, matriz)
        pagina._cambiar_modo("Expresión")
        pagina._usar_expresion("AB − C")
        pagina.resolver()
        self.app.notificar("Se cargaron A = L, B = U y C = A original: si L·U = A, AB − C es la matriz cero.", "info")

    def _enviar_a_axb(self, resultado):
        """Encadena A y b a la sección «Ecuación Ax = b» y la resuelve por Gauss-Jordan.

        Entrada: resultado de resolver_lu. Salida: None.
        """
        pagina = self.app.ir_a("axb")
        pagina.establecer_datos(resultado["m"], resultado["n"],
                                [fila + [bi] for fila, bi in zip(resultado["matriz_A"], resultado["vector_b"])])
        pagina.resolver()

    def mostrar_procedimiento(self, resultado):
        """Muestra las etapas encadenadas: factorización, [L | b] y [U | y].

        Entrada: resultado de resolver_lu. Salida: None.
        """
        self.panel_pasos.mostrar_pasos(resultado["etapas"])

    def mostrar_verificacion(self, resultado):
        """Muestra la verificación independiente desde los datos originales.

        Entrada: resultado de resolver_lu. Salida: None.
        """
        self.area_verificacion.llenar(constructores_chequeo(modulo_lu.verificar_lu(resultado)), retardo=45)

    def texto_copiar(self, resultado):
        """Escribe L, U, y, x y los mensajes en texto plano para el portapapeles.

        Entrada: resultado de resolver_lu. Salida: cadena.
        """
        return "\n".join(modulo_lu.formatear_resultado_lu(resultado))

    def mensaje_resuelto(self, resultado):
        """Resume el resultado de la factorización en una notificación.

        Entrada: resultado de resolver_lu. Salida: (texto, tipo).
        """
        if not resultado["existe"]:
            return modulo_lu.MENSAJE_SIN_PERMUTACION, "aviso"
        tipo = {"Sistema inconsistente": "error",
                "Sistema consistente indeterminado": "aviso"}.get(resultado["clasificacion"], "exito")
        reemplazos = _plural(len(resultado["factorizacion"]["operaciones"]), "reemplazo", "reemplazos")
        return f"A = LU con {reemplazos} · {resultado['clasificacion']}.", tipo


class PaginaCombinaciones(PaginaSistema):
    """Página «Combinaciones lineales»: ¿w pertenece a Gen{v1, …, vn}?"""
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
        """Define la rejilla con los vectores v1…vn como columnas y w.

        Entrada: filas y columnas. Salida: diccionario de configuración.
        """
        return {
            "columnas": columnas + 1,
            "encabezados": [f"v{j + 1}" for j in range(columnas)] + ["w"],
            "encabezados_fila": [str(i + 1) for i in range(filas)],
            "separador": columnas,
        }

    def texto_dimension(self, filas, columnas):
        """Escribe la cantidad de vectores y el espacio Rⁿ.

        Entrada: filas y columnas. Salida: cadena.
        """
        return f"{columnas} vectores de {espacio_real(filas)}"

    def construir_previa(self, parent, valores):
        """Muestra la ecuación vectorial c1·v1 + … + cn·vn = w.

        Entrada: contenedor y valores. Salida: None.
        """
        n = len(valores[0]) - 1
        partes = []
        for j in range(n):
            partes += [f"{'' if j == 0 else '+ '}c{j + 1}·", [fila[j] for fila in valores]]
        partes += ["=", [fila[-1] for fila in valores]]
        dibujar_expresion(parent, partes, tamano=12).pack(anchor="w")
        etiqueta(parent, "Se resuelve el sistema cuya matriz aumentada es [v1 … vn | w].",
                 FUENTE_PEQUENA, "texto_3").pack(anchor="w", pady=(6, 0))

    def calcular(self, matriz):
        """Resuelve el sistema de los coeficientes c1…cn.

        Entrada: matriz [v1 … vn | w]. Salida: diccionario de resolver_sistema.
        """
        n = len(matriz[0]) - 1
        return resolver_sistema([fila[:-1] for fila in matriz], [fila[-1] for fila in matriz],
                                obtener_nombres_variables(n, "c"))

    def construir_resultado(self, resultado):
        """Prepara las tarjetas con el veredicto y los coeficientes de la combinación.

        Entrada: resultado. Salida: lista de constructores.
        """
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
        if len(w) in (2, 3) and len(vectores) <= PaginaRenders.MAXIMO_VECTORES:
            constructores.append(lambda p: tarjeta_encadenar(
                p, "Ver la combinación animada", "Cada coeficiente por su vector se coloca a continuación del anterior hasta llegar a w.",
                [("Abrir en «Renders y animaciones»", lambda: self.app.ir_a("renders").cargar_combinacion(vectores, w))]))
        return constructores + constructores_solucion(resultado, simbolo="c")

    @staticmethod
    def _tarjeta_combinacion(parent, titulo, coeficientes, vectores, simbolos, w):
        """Crea la tarjeta que dibuja la combinación lineal con sus coeficientes y su resultado.

        Entrada: contenedor, título, coeficientes, vectores, símbolos y w. Salida: CTkFrame de la tarjeta.
        """
        tarjeta = tarjeta_seccion(parent, titulo)
        etiqueta(tarjeta, f"w = {formatear_combinacion_lineal(coeficientes, simbolos)}",
                 (FAMILIA_MONO, 16, "bold"), "primario").pack(anchor="w", padx=16)
        dibujar_expresion(tarjeta, partes_combinacion(coeficientes, vectores, w)).pack(
            anchor="w", padx=14, pady=(6, 16))
        return tarjeta


class PaginaIndependencia(PaginaSistema):
    """Página «Independencia lineal»: veredicto L.I. o L.D. desde [A | 0]."""
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
        """Define la rejilla con los vectores v1…vp como columnas.

        Entrada: filas y columnas. Salida: diccionario de configuración.
        """
        return {
            "columnas": columnas,
            "encabezados": [f"v{j + 1}" for j in range(columnas)],
            "encabezados_fila": [str(i + 1) for i in range(filas)],
            "separador": None,
        }

    def texto_dimension(self, filas, columnas):
        """Escribe 'p vectores de Rⁿ'.

        Entrada: filas y columnas. Salida: cadena.
        """
        return f"p = {columnas} vectores de {espacio_real(filas)}"

    def valores_aleatorios(self, filas, columnas):
        """Genera vectores aleatorios con componentes enteras entre −5 y 5.

        Entrada: filas y columnas. Salida: matriz con los vectores como columnas.
        """
        return [[random.randint(-5, 5) for _ in range(columnas)] for _ in range(filas)]

    def construir_previa(self, parent, valores):
        """Muestra la ecuación c1·v1 + … + cp·vp = 0 y la matriz [A | 0].

        Entrada: contenedor y valores. Salida: None.
        """
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
        """Analiza la independencia lineal de las columnas.

        Entrada: matriz A. Salida: diccionario de analizar_independencia.
        """
        return analizar_independencia(matriz)

    def construir_resultado(self, resultado):
        """Prepara las tarjetas con el veredicto, los indicadores y la solución trivial o la relación de dependencia.

        Entrada: resultado. Salida: lista de constructores.
        """
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
                """Crea la tarjeta con la solución trivial c = 0.

                Entrada: contenedor. Salida: None.
                """
                tarjeta = tarjeta_seccion(parent, "Solución trivial")
                dibujar_expresion(tarjeta, ["c =", resultado["solucion"]]).pack(anchor="w", padx=14)
                etiqueta(tarjeta, "Ningún vector se puede escribir como combinación lineal de los demás.",
                         FUENTE_NORMAL, "texto_2", ajustar=44).pack(anchor="w", padx=16, pady=(6, 16))
            constructores.append(trivial)
        else:
            relacion = resultado["relacion"]

            def dependencia(parent):
                """Crea la tarjeta con una relación de dependencia no trivial y su despeje.

                Entrada: contenedor. Salida: None.
                """
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
        """Crea la tarjeta con el veredicto L.I./L.D., su justificación y el teorema.

        Entrada: contenedor y resultado. Salida: CTkFrame de la tarjeta.
        """
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
        """Escribe el informe de independencia en texto plano.

        Entrada: resultado. Salida: cadena.
        """
        return "\n".join(informe_independencia(resultado))

    def mensaje_resuelto(self, resultado):
        """Resume el veredicto, los pivotes y las variables libres en una notificación.

        Entrada: resultado. Salida: (texto, tipo).
        """
        mensaje = (f"Veredicto: {resultado['veredicto']} · "
                   f"{_plural(resultado['num_pivotes'], 'pivote', 'pivotes')}, "
                   f"{_plural(resultado['num_libres'], 'variable libre', 'variables libres')}.")
        return mensaje, "exito" if resultado["independiente"] else "aviso"


class PaginaPropiedades(PaginaSistema):
    """Página «Propiedades de Ax»: Av por columnas, A(cv) = c(Av) y A(u + v) = Au + Av."""
    titulo = "Propiedades del producto Av"
    subtitulo = ("Carga las columnas a1, a2, … de A y el vector v (y, si quieres, u): calcula "
                 "Av = v1·a1 + … + vn·an y comprueba sus propiedades")
    etiqueta_filas = "Componentes (m)"
    etiqueta_columnas = "Vectores a1…an (n)"
    filas_inicial = 2
    columnas_inicial = 3
    titulo_datos = "Columnas de A y vectores"
    texto_boton = "Calcular Av"
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
        """Prepara el estado del vector u opcional y crea la página.

        Entrada: contenedor y aplicación. Salida: None.
        """
        self.con_u = False
        self._u_guardado = []
        super().__init__(parent, app)

    def controles_extra(self, fila):
        """Agrega a la barra la casilla del escalar c.

        Entrada: fila de la barra. Salida: None.
        """
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
        """Marca la casilla de c según si es un número válido y actualiza la vista previa."""
        valido = _numero_o_nada(self.entrada_c.get()) is not None
        self.entrada_c.configure(border_color=PALETA["borde"] if valido else PALETA["error"])
        self._al_cambiar_datos()

    def construir_entradas(self, parent):
        """Crea las rejillas de A (columnas a1…an) y de los vectores v y u.

        Entrada: contenedor. Salida: None.
        """
        etiqueta(parent, "Matriz A = [a1  a2  …  an]  (cada columna es un vector)", FUENTE_PEQUENA_NEGRITA,
                 "texto_3").pack(anchor="w", padx=4, pady=(4, 2))
        self.matriz_a = MatrizEntrada(parent, al_cambiar=self._al_cambiar_datos)
        self.matriz_a.pack(anchor="w", padx=4)

        # Av solo existe si v tiene tantas componentes como columnas tiene A: los dos contadores van sincronizados.
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
        """Sincroniza la cantidad de columnas de A con las componentes de v.

        Entrada: número de componentes. Salida: None.
        """
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
        """Reconfigura la rejilla de v (y u) con las componentes indicadas.

        Entrada: componentes y valores opcionales. Salida: None.
        """
        encabezados = ["v", "u"] if self.con_u else ["v"]
        self.matriz_v.configurar(componentes, len(encabezados), encabezados,
                                 [str(i + 1) for i in range(componentes)], None, valores)

    def texto_dimension(self, filas, columnas):
        """Escribe las dimensiones de A y el espacio de los vectores.

        Entrada: filas y columnas. Salida: cadena.
        """
        vectores = "u, v" if self.con_u else "v"
        return f"A: {filas} × {columnas} · {vectores} ∈ {espacio_real(columnas)}"

    def configurar_entradas(self, filas, columnas, valores):
        """Carga A, v, c y u en las rejillas con el tamaño indicado.

        Entrada: filas, columnas y valores opcionales. Salida: None.
        """
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
        """Lee A, v, u y c escritos para la vista previa.

        Salida: (A, v, u, c) con None en las casillas inválidas.
        """
        A = [[_numero_o_nada(t) for t in fila] for fila in self.matriz_a.textos()]
        vectores = [[_numero_o_nada(t) for t in fila] for fila in self.matriz_v.textos()]
        v = [fila[0] for fila in vectores]
        u = [fila[1] for fila in vectores] if self.con_u else None
        return A, v, u, _numero_o_nada(self.entrada_c.get())

    def construir_previa(self, parent, valores):
        """Muestra A, v (y u) y Av como combinación de columnas.

        Entrada: contenedor y valores. Salida: None.
        """
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
        """Lee A, v, c y u como Fraction.

        Salida: (A, v, c, u); lanza ValueError con la casilla inválida.
        """
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
        """Pone en 0 las rejillas de A y de los vectores."""
        self.matriz_a.limpiar()
        self.matriz_v.limpiar()

    def valores_aleatorios(self, filas, columnas):
        """Genera A, v, c y u aleatorios.

        Entrada: filas y columnas. Salida: (A, v, c, u).
        """
        A = [[random.randint(-4, 4) for _ in range(columnas)] for _ in range(filas)]
        v = [random.randint(-3, 3) for _ in range(columnas)]
        u = [random.randint(-3, 3) for _ in range(columnas)]
        return A, v, str(random.choice([-3, -2, 2, 3, 4])), u

    def calcular(self, datos):
        """Calcula Av y las propiedades de linealidad.

        Entrada: (A, v, c, u). Salida: diccionario de analizar_producto_av.
        """
        return analizar_producto_av(*datos)

    @staticmethod
    def _todo_se_cumple(datos):
        """Indica si se cumplen todas las propiedades evaluadas.

        Entrada: resultado. Salida: True o False.
        """
        return datos["propiedad"] and datos["propiedad_suma"] is not False

    def construir_resultado(self, datos):
        """Prepara las tarjetas con los productos y el diagnóstico de cada propiedad.

        Entrada: resultado. Salida: lista de constructores.
        """
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
        """Muestra ambos lados de cada propiedad en la pestaña Procedimiento.

        Entrada: resultado. Salida: None.
        """
        self.informe_av = didactica.informe_propiedades_av(datos)
        self.panel_pasos.mostrar_pasos(self.informe_av["procedimiento"])

    def mostrar_verificacion(self, datos):
        """Muestra el recálculo por columnas en la pestaña Verificación.

        Entrada: resultado. Salida: None.
        """
        self.area_verificacion.llenar(constructores_chequeo(self.informe_av["verificacion"]), retardo=45)

    @staticmethod
    def _vector(valores):
        """Escribe un vector como '(a, b, …)'.

        Entrada: lista de números. Salida: cadena.
        """
        return "(" + ", ".join(formatear_numero(x) for x in valores) + ")"

    def texto_copiar(self, datos):
        """Escribe Av, A(cv), c(Av) y, si hay u, A(u + v) y Au + Av en texto plano.

        Entrada: resultado. Salida: cadena.
        """
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
        """Resume el resultado de las propiedades en una notificación.

        Entrada: resultado. Salida: (texto, tipo).
        """
        if not self._todo_se_cumple(datos):
            return "Alguna propiedad no se cumplió.", "error"
        if datos["u"] is not None:
            return (f"Av = {self._vector(datos['Av'])}, Au = {self._vector(datos['Au'])} · "
                    f"se cumplen ambas propiedades."), "exito"
        return f"Av = {self._vector(datos['Av'])} · se cumple A(cv) = c(Av).", "exito"



COLORES_OPERACION_MATRICIAL = {
    "suma": "exito", "resta": "exito", "producto": "primario", "escalar": "advertencia",
    "transpuesta": "texto_3", "aritmetica": "texto_3", "datos": "texto_3", "respuesta": "primario",
}


def _superindice_dimension(dimension):
    """Escribe una dimensión como superíndice 'ᵐˣⁿ' para mostrar ℝᵐˣⁿ.

    Entrada: tupla (filas, columnas). Salida: cadena.
    """
    return str(dimension[0]).translate(SUPERINDICES) + "ˣ" + str(dimension[1]).translate(SUPERINDICES)


def dibujar_valores(parent, elementos, tamano=13):
    """Dibuja en una fila pares (etiqueta, valor): las matrices como matriz y los números como texto.

    Entrada: contenedor, lista de pares y tamaño. Salida: tk.Canvas.
    """
    partes = []
    for k, (nombre, valor) in enumerate(elementos):
        prefijo = ("   " if k else "") + f"{nombre} ="
        if isinstance(valor, list):
            partes += [prefijo, valor]
        else:
            partes.append(f"{prefijo} {formatear_numero(Fraction(valor))}")
    return dibujar_expresion(parent, partes, tamano=tamano)


def _lineas(parent, lineas, color="texto_2", fuente=None, ajustar=40, pady=(0, 0)):
    """Agrega cada línea de texto como etiqueta con el color y la fuente indicados.

    Entrada: contenedor, líneas, color, fuente, ajustar y espaciado. Salida: None.
    """
    for linea in lineas:
        etiqueta(parent, linea, fuente or FUENTE_NORMAL, color, ajustar=ajustar).pack(anchor="w", pady=pady)


def _subtitulo_seccion(parent, texto):
    """Agrega un subtítulo en mayúsculas dentro de una tarjeta.

    Entrada: contenedor y texto. Salida: None.
    """
    etiqueta(parent, texto, FUENTE_PEQUENA_NEGRITA, "texto_3").pack(anchor="w", pady=(10, 2))


def tarjeta_paso_matricial(parent, pasos, indice, detallado=False):
    """Crea la tarjeta de un paso con matrices: datos, operación intermedia o respuesta.

    Entrada: contenedor, pasos, índice y detallado (bool). Salida: la tarjeta creada.
    """
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
    """Llena la tarjeta de datos: expresión, matrices con dimensiones, escalares y condiciones.

    Entrada: cuerpo de la tarjeta y paso. Salida: None.
    """
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
    """Llena la tarjeta de una operación: condición, regla, operandos, resultado y cálculo de cada entrada.

    Entrada: cuerpo de la tarjeta, paso y detallado (bool). Salida: None.
    """
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
            """Agrega el desarrollo de cada entrada del resultado.

            Entrada: marco. Salida: None.
            """
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
    """Llena la tarjeta de la respuesta final: resultado, orden de operaciones, reglas y conclusión.

    Entrada: cuerpo de la tarjeta y paso. Salida: None.
    """
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
    """Explica una comparación: dimensiones, entradas que coinciden y diferencias.

    Entrada: diccionario de comparación. Salida: lista de (línea, correcta).
    """
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
    """Crea la tarjeta que compara dos resultados en dimensiones y entrada por entrada.

    Entrada: contenedor, título, ambos resultados, comparación y nota. Salida: CTkFrame de la tarjeta.
    """
    tarjeta = tarjeta_seccion(parent, titulo, nota)
    for elemento in (izquierda, derecha):
        dibujar_valores(tarjeta, [elemento]).pack(anchor="w", padx=14)
    for linea, correcta in _texto_comparacion(comparacion):
        etiqueta(tarjeta, linea, FUENTE_PEQUENA_NEGRITA, "exito" if correcta else "error", ajustar=44).pack(
            anchor="w", padx=16)
    detalle = didactica.comparar(izquierda[1], derecha[1])
    def entradas(marco):
        """Agrega la comparación de cada entrada.

        Entrada: marco. Salida: None.
        """
        for linea in detalle["calculos"]:
            etiqueta(marco, linea, FUENTE_MONO, "texto_2", ajustar=40).pack(anchor="w", padx=12, pady=2)
    SeccionPlegable(tarjeta, "Comparación elemento por elemento", f"{len(detalle['calculos'])} posiciones", comparacion["coinciden"],
                    entradas, abierto=not comparacion["coinciden"]).pack(fill="x", padx=14, pady=(6, 8))
    etiqueta(tarjeta, detalle["conclusion"], FUENTE_NEGRITA, "exito" if comparacion["coinciden"] else "error").pack(anchor="w", padx=16, pady=6)
    ctk.CTkFrame(tarjeta, fg_color="transparent", height=10).pack()
    return tarjeta


def constructores_resultado_expresion(resolucion, informe, app, al_guardar=None):
    """Prepara la pestaña Resultado de una expresión: estado, resultado, conclusión y encadenamiento.

    Entrada: resolución, informe de verificación, aplicación y al_guardar. Salida: lista de constructores.
    """
    expresion = resolucion["expresion"]
    if resolucion["error"]:
        hechas = [p for p in resolucion["operaciones"] if p["condicion"]["cumple"]]

        def realizadas(parent):
            """Crea la tarjeta con las operaciones calculadas antes de la que no está definida.

            Entrada: contenedor. Salida: None.
            """
            tarjeta = tarjeta_seccion(parent, "Operaciones realizadas antes del error")
            if not hechas:
                etiqueta(tarjeta, "Ninguna: la primera operación ya no está definida.", FUENTE_NORMAL, "texto_2",
                         ajustar=44).pack(anchor="w", padx=16, pady=(0, 14))
                return
            for paso in hechas:
                dibujar_valores(tarjeta, [(paso["expresion"], paso["resultado"])]).pack(anchor="w", padx=14)
            ctk.CTkFrame(tarjeta, fg_color="transparent", height=10).pack()

        def condiciones(parent):
            """Crea la tarjeta con las condiciones de dimensión de cada operación.

            Entrada: contenedor. Salida: None.
            """
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
        """Crea la tarjeta con la matriz (o el número) resultante y su dimensión.

        Entrada: contenedor. Salida: None.
        """
        tarjeta = tarjeta_seccion(parent, "Resultado")
        fila = ctk.CTkFrame(tarjeta, fg_color="transparent")
        fila.pack(anchor="w", padx=14, pady=(0, 14))
        dibujar_valores(fila, [(expresion, resultado)], tamano=14).pack(side="left")
        if dimension:
            chip(fila, formatear_dimension(dimension), "panel", "primario").pack(side="left", padx=(10, 0))

    def conclusion(parent):
        """Crea la tarjeta con la conclusión y el alcance de la verificación.

        Entrada: contenedor. Salida: None.
        """
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
    def encadenar(parent):
        """Crea la tarjeta con los botones «Usar como A/B/C» para encadenar el resultado.

        Entrada: contenedor. Salida: None.
        """
        tarjeta = tarjeta_seccion(parent, "Usar el resultado en otra expresión",
                                  "Se guarda como A, B o C (con su tamaño) para encadenar el siguiente cálculo.")
        fila = ctk.CTkFrame(tarjeta, fg_color="transparent")
        fila.pack(anchor="w", padx=16, pady=(0, 14))
        for k, nombre in enumerate(("A", "B", "C")):
            boton_secundario(fila, f"↪  Usar como {nombre}", lambda n=nombre: al_guardar(n, resultado),
                             width=128, height=34).pack(side="left", padx=(0 if k == 0 else 8, 0))

    return [
        lambda p: tarjeta_estado(p, titulo, descripcion, PALETA["exito"] if correcto else PALETA["error"],
                                 "✓" if correcto else "✕"),
        resultado_final, conclusion,
        *([encadenar] if dimension and al_guardar else []),
        lambda p: fila_copiar(p, app, texto_copia),
    ]


def constructores_cobertura(informe):
    """Prepara la pestaña Resultado de la tabla de propiedades: resumen y una tarjeta por categoría.

    Entrada: resultado de verificar_propiedades_clave. Salida: lista de constructores.
    """
    evaluadas, cumplidas = informe["evaluadas"], informe["cumplidas"]
    todas = evaluadas and cumplidas == evaluadas
    lista = [lambda p: tarjeta_estado(
        p, f"Cobertura completa: {cumplidas} de {evaluadas} propiedades se cumplen",
        f"Ambos miembros se calcularon con las funciones internas y k = {formatear_numero(informe['k'])}. Las que no "
        f"aplican indican la hipótesis que falta.", PALETA["exito"] if todas else PALETA["advertencia"],
        "✓" if todas else "!")]
    for categoria in CATEGORIAS_PROPIEDADES_CLAVE:
        filas = [r for r in informe["resultados"] if r["categoria"] == categoria]
        mensajes = [f"{'✓' if r['cumple'] else '✗' if r['cumple'] is False else '·'}  {r['propiedad']}: "
                    f"{r['diagnostico']}" for r in filas]
        color = ("error" if any(r["cumple"] is False for r in filas) else
                 "advertencia" if any(r["cumple"] is None for r in filas) else "exito")
        lista.append(lambda p, c=categoria, m=mensajes, col=color: tarjeta_mensajes(p, c, m, col))
    return lista


def constructores_verificacion(resolucion, informe):
    """Prepara la pestaña Verificación de una expresión: por paso, recálculo y ruta alternativa.

    Entrada: resolución e informe de verificar_resolucion. Salida: lista de constructores.
    """
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
        """Crea la tarjeta con el recálculo independiente de cada operación intermedia.

        Entrada: contenedor. Salida: None.
        """
        tarjeta = tarjeta_seccion(parent, "1. Cada operación intermedia",
                                  "Cada resultado se recalcula desde sus propios operandos con un método independiente "
                                  "y se compara entrada por entrada.")
        if not informe["pasos"]:
            etiqueta(tarjeta, "No hay operaciones intermedias.", FUENTE_NORMAL, "texto_2").pack(anchor="w", padx=16, pady=(0, 14))
            return
        for chequeo in informe["pasos"]:
            def cuerpo(marco, c=chequeo):
                """Muestra el detalle del recálculo de un paso: método, dimensiones y entradas.

                Entrada: marco y comprobación. Salida: None.
                """
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
        """Crea la tarjeta que compara el resultado con el recálculo desde los datos originales.

        Entrada: contenedor. Salida: None.
        """
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
            """Crea la tarjeta que compara el resultado con la ruta alternativa por propiedad.

            Entrada: contenedor. Salida: None.
            """
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
                """Muestra los pasos de ambos lados de la ruta alternativa.

                Entrada: marco. Salida: None.
                """
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
    """Prepara la pestaña Resultado de una propiedad: estado, enunciado, lados, comparaciones y teoría.

    Entrada: informe y al_cargar_contraejemplo. Salida: lista de constructores.
    """
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
        """Crea la tarjeta con el enunciado y las condiciones de la propiedad.

        Entrada: contenedor. Salida: None.
        """
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
            """Crea la tarjeta con el resultado de un lado de la propiedad.

            Entrada: contenedor y lado. Salida: None.
            """
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
            """Crea la tarjeta con la comparación de los dos lados.

            Entrada: contenedor y comparación. Salida: None.
            """
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
        """Crea la tarjeta con la conclusión de la propiedad.

        Entrada: contenedor. Salida: None.
        """
        tarjeta = tarjeta_seccion(parent, "Conclusión")
        etiqueta(tarjeta, informe["conclusion"], FUENTE_NORMAL, "texto", ajustar=44).pack(anchor="w", padx=16, pady=(0, 14))

    def teoria(parent):
        """Crea la tarjeta con la demostración general o la advertencia y su contraejemplo.

        Entrada: contenedor. Salida: None.
        """
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
    """Prepara la pestaña Verificación de una propiedad: cada lado recalculado y comparado.

    Entrada: informe de la propiedad. Salida: lista de constructores.
    """
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
            """Crea la tarjeta con las comprobaciones de un lado de la propiedad.

            Entrada: contenedor, lado, resolución y verificación. Salida: None.
            """
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
    """Página «Operaciones matriciales»: expresiones con A, B y C, propiedades, cobertura y contraejemplos.

    Muestra cada operación intermedia y verifica el resultado por caminos independientes.
    """

    titulo = "Operaciones con Matrices y Propiedades Teóricas"
    subtitulo = "Expresiones con A, B y C paso a paso, verificación independiente y propiedades teóricas"
    MODOS = ("Expresión", "Propiedades", "Cobertura completa", "Contraejemplos", "Ejercicios")
    EXPRESIONES = ("A + B", "A − B", "3A", "Aᵀ", "AB", "A + B − C", "2A − 3B + C", "A(B + C)", "AB + AC",
                   "(A + B)C", "A(B − C)", "AB − AC", "(AB)ᵀ", "BᵀAᵀ", "(A + B)ᵀ", "Aᵀ + Bᵀ", "AᵀBC", "r(A + B)ᵀ",
                   "A⁻¹A", "AA⁻¹", "(AB)⁻¹")
    TOKENS = ("A", "B", "C", "(", ")", "ᵀ", "⁻¹", "+", "−", "r")
    MATRICES_INICIALES = {"A": [[1, 2], [3, 4]], "B": [[0, 1], [-1, 2]], "C": [[2, 0], [1, -3]]}
    ESCALARES_INICIALES = {"r": "2", "s": "1/2"}
    CONTRAEJEMPLOS = {
        "no_conmutatividad": ("El producto no es conmutativo", "propiedad", "no_conmutatividad"),
        "orden_rectangular": ("AB está definido pero BA no", "expresion", "BA"),
        "cancelacion": ("La cancelación no siempre vale", "propiedad", "cancelacion"),
        "divisores_cero": ("Matrices no nulas con producto cero", "propiedad", "divisores_cero"),
    }

    def __init__(self, parent, app):
        """Crea la barra de modos, los bloques A, B y C y las pestañas; inicia en modo Expresión.

        Entrada: contenedor y aplicación. Salida: None.
        """
        super().__init__(parent, app)
        self.modo = "Expresión"
        self.propiedad = "distributiva_izquierda"
        self.hay_resultado = False
        self._tarea_previa = None
        self.grid_rowconfigure(2, weight=1)
        self._crear_barra()
        self._crear_contenido()
        self._cambiar_modo("Expresión")


    def _crear_barra(self):
        """Crea el selector de modos, los escalares r y s y los controles de expresión y propiedades."""
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
        """Crea un menú desplegable con los colores de la paleta.

        Entrada: widget padre opcional. Salida: tk.Menu.
        """
        return tk.Menu(padre or self, tearoff=0, font=FUENTE_NORMAL, bd=0, relief="flat",
                       bg=resolver_color(PALETA["panel_2"]), fg=resolver_color(PALETA["texto"]),
                       activebackground=resolver_color(PALETA["primario"]), activeforeground=TEXTO_SOBRE_PRIMARIO)

    @staticmethod
    def _texto_propiedad(propiedad):
        """Escribe una propiedad para el menú: nombre e igualdad.

        Entrada: diccionario de la propiedad. Salida: cadena.
        """
        if propiedad.get("tipo", "igualdad") == "igualdad":
            return f"{propiedad['nombre']}:  {propiedad['izquierda']} = {propiedad['derecha']}"
        return propiedad["nombre"]

    def _crear_contenido(self):
        """Crea la tarjeta de datos (A, B, C y vista previa) y las tres pestañas."""
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
        """Crea el bloque de una matriz con sus contadores de tamaño y su rejilla.

        Entrada: contenedor y nombre de la matriz. Salida: None.
        """
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


    def _configurar_matriz(self, nombre, valores=None):
        """Reconfigura la rejilla de una matriz con el tamaño de sus contadores.

        Entrada: nombre y valores opcionales. Salida: None.
        """
        bloque = self.bloques[nombre]
        filas, columnas = bloque["filas"].get(), bloque["columnas"].get()
        bloque["matriz"].configurar(filas, columnas, [str(j + 1) for j in range(columnas)],
                                    [str(i + 1) for i in range(filas)], None, valores)

    def _redimensionar(self, nombre):
        """Aplica un nuevo tamaño a una matriz y actualiza la vista previa.

        Entrada: nombre de la matriz. Salida: None.
        """
        self._configurar_matriz(nombre)
        self._al_cambiar_datos()

    def establecer_matriz(self, nombre, valores):
        """Carga una matriz completa (por ejemplo, un resultado encadenado) ajustando su tamaño.

        Entrada: nombre (A, B o C) y matriz. Salida: None.
        """
        bloque = self.bloques[nombre]
        bloque["filas"].set(len(valores))
        bloque["columnas"].set(len(valores[0]))
        self._configurar_matriz(nombre, valores)

    def _dimensiones(self):
        """Lee las dimensiones elegidas para A, B y C.

        Salida: diccionario nombre → (filas, columnas).
        """
        return {nombre: (b["filas"].get(), b["columnas"].get()) for nombre, b in self.bloques.items()}

    def _leer_matrices(self, nombres):
        """Lee como Fraction las matrices indicadas.

        Entrada: nombres. Salida: diccionario nombre → matriz; lanza ValueError con la casilla inválida.
        """
        matrices = {}
        for nombre in sorted(nombres):
            if nombre in self.bloques:
                try:
                    matrices[nombre] = self.bloques[nombre]["matriz"].valores()
                except ValueError as error:
                    raise ValueError(f"Matriz {nombre}: {error}") from None
        return matrices

    def _leer_escalares(self, nombres):
        """Lee los escalares indicados.

        Entrada: nombres (r, s). Salida: diccionario nombre → Fraction; lanza ValueError si alguno no es válido.
        """
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
        """Marca la casilla de un escalar según su validez y actualiza la vista previa.

        Entrada: casilla. Salida: None.
        """
        valido = _numero_o_nada(entrada.get()) is not None
        entrada.configure(border_color=PALETA["borde"] if valido else PALETA["error"])
        self._al_cambiar_datos()

    def _insertar(self, token):
        """Inserta un símbolo en la expresión en la posición del cursor.

        Entrada: símbolo. Salida: None.
        """
        self.entrada_expresion.insert("insert", token)
        self.entrada_expresion.focus_set()
        self._programar_previa()

    def _usar_expresion(self, expresion):
        """Reemplaza la expresión escrita por la indicada.

        Entrada: expresión. Salida: None.
        """
        self.entrada_expresion.delete(0, "end")
        self.entrada_expresion.insert(0, expresion)
        self._al_cambiar_datos()

    def _guardar_resultado(self, nombre, matriz):
        """Encadena el resultado: pasa a ser la matriz «nombre» de la siguiente expresión.

        Entrada: nombre (A, B o C) y matriz. Salida: None.
        """
        self.establecer_matriz(nombre, matriz)
        self._al_cambiar_datos()
        destello(self.tarjeta_datos)
        self.app.notificar(f"El resultado se guardó en {nombre}. Escribe la siguiente expresión y calcula.", "info")

    def _usar_propiedad(self, clave):
        """Selecciona la propiedad del modo Propiedades.

        Entrada: clave de la propiedad. Salida: None.
        """
        self.propiedad = clave
        propiedad = PROPIEDADES_POR_CLAVE[clave]
        self.boton_propiedad.configure(text="  " + self._texto_propiedad(propiedad) + "  ▾")
        if propiedad.get("contraejemplo"):
            self.boton_contraejemplo.pack(side="left", padx=(8, 0))
        else:
            self.boton_contraejemplo.pack_forget()
        self._al_cambiar_datos()

    def _abrir_expresiones(self):
        """Abre el menú de expresiones de ejemplo."""
        boton = self.boton_expresiones
        self.menu_expresiones.tk_popup(boton.winfo_rootx(), boton.winfo_rooty() + boton.winfo_height() + 4)

    def _abrir_propiedades(self):
        """Abre el menú de propiedades."""
        boton = self.boton_propiedad
        self.menu_propiedades.tk_popup(boton.winfo_rootx(), boton.winfo_rooty() + boton.winfo_height() + 4)

    def _programar_previa(self):
        """Programa la actualización de la vista previa tras una pausa al escribir."""
        if self._tarea_previa is not None:
            self.after_cancel(self._tarea_previa)
        self._tarea_previa = self.after(150, self._al_cambiar_datos)

    def _al_cambiar_datos(self):
        """Actualiza la vista previa y avisa que el resultado anterior quedó desactualizado."""
        self._tarea_previa = None
        self._actualizar_previa()
        if self.hay_resultado and self.modo in ("Expresión", "Propiedades", "Cobertura completa"):
            self.aviso.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 8))
            self.panel_pasos.mostrar_placeholder("Los datos cambiaron: vuelve a calcular.")
            self.area_verificacion.llenar([lambda p: placeholder(p, "✓", "Los datos cambiaron: vuelve a calcular.")])


    def _actualizar_previa(self):
        """Muestra la interpretación y las condiciones de dimensión según el modo."""
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
        elif self.modo == "Cobertura completa":
            etiqueta(parent, "Se evalúan ambos miembros de todas las propiedades clave (transposición, inversa, "
                             "determinantes y operaciones de fila) con A, B, C y k = r.", FUENTE_NORMAL, "texto_2",
                     ajustar=48).pack(anchor="w")
            for nombre, (filas, columnas) in dimensiones.items():
                etiqueta(parent, f"{nombre}: {filas}×{columnas}" + ("  (cuadrada)" if filas == columnas else ""),
                         FUENTE_MONO, "texto").pack(anchor="w")
            etiqueta(parent, "Las propiedades de inversa y determinante requieren A (y B) cuadradas del mismo orden; si "
                             "una hipótesis falla, se indica «No aplica» con el motivo.", FUENTE_PEQUENA, "texto_3",
                     ajustar=48).pack(anchor="w", pady=(6, 0))
        elif self.modo == "Contraejemplos":
            etiqueta(parent, "Cada contraejemplo muestra que una afirmación es falsa en general. Usa «Estudiar paso a "
                             "paso» para cargarlo en A, B y C.", FUENTE_NORMAL, "texto_2", ajustar=48).pack(anchor="w")
        else:
            etiqueta(parent, "Elige un ejercicio y presiona «Resolver en la calculadora»: se cargan sus matrices y se "
                             "resuelve con procedimiento y verificación.", FUENTE_NORMAL, "texto_2", ajustar=48).pack(anchor="w")

    @staticmethod
    def _previa_expresion(parent, nodo, condiciones, final):
        """Muestra el orden de cálculo de la expresión y la condición de cada operación.

        Entrada: contenedor, árbol, condiciones y dimensión final. Salida: None.
        """
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


    def _cambiar_modo(self, modo):
        """Cambia de modo, muestra sus controles y vacía las pestañas.

        Entrada: nombre del modo. Salida: None.
        """
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
            self.controles_info.configure(text={
                "Cobertura completa": "Verificador de todas las propiedades clave con A, B, C y k = r.",
                "Contraejemplos": "Contraejemplos clásicos del producto de matrices."}.get(
                    modo, "Ejercicios tipo examen con su resolución guiada."))
            self.controles_info.pack(side="left")
        self.hay_resultado = False
        self.aviso.grid_remove()
        if modo == "Contraejemplos":
            self._mostrar_contraejemplos()
        elif modo == "Ejercicios":
            self._mostrar_ejercicios()
        else:
            texto = {"Expresión": "Escribe una expresión (o elige un ejemplo) y presiona «Calcular y verificar».",
                     "Propiedades": "Elige una propiedad y presiona «Calcular y verificar» para comprobarla con tus matrices."
                     }.get(modo, "Presiona «Calcular y verificar» para evaluar todas las propiedades clave.")
            self._vaciar(texto)
        self._actualizar_previa()

    def _vaciar(self, texto):
        """Muestra los mensajes iniciales en las tres pestañas.

        Entrada: texto opcional. Salida: None.
        """
        self.area_resultado.llenar([lambda p: placeholder(p, "▦", texto)])
        self.panel_pasos.mostrar_placeholder()
        self.area_verificacion.llenar([lambda p: placeholder(
            p, "✓", "Aquí aparecerá la verificación: cada operación recalculada, el recálculo independiente y, cuando "
                    "exista, una ruta alternativa por propiedad.")])

    def resolver(self):
        """Calcula según el modo activo y notifica cualquier error sin cerrarse."""
        try:
            if self.modo == "Expresión":
                self._resolver_expresion()
            elif self.modo == "Propiedades":
                self._resolver_propiedad()
            elif self.modo == "Cobertura completa":
                self._resolver_cobertura()
            elif self.modo == "Contraejemplos":
                self._mostrar_contraejemplos()
            else:
                self._mostrar_ejercicios()
        except (ErrorExpresion, ValueError) as error:
            self.app.notificar(str(error), "error")

    def _resolver_cobertura(self):
        """Evalúa la tabla completa de propiedades clave con A, B, C y k = r y llena las tres pestañas."""
        matrices = self._leer_matrices({"A", "B", "C"})
        escalar_k = self._leer_escalares({"r"})["r"]
        informe = verificar_propiedades_clave(matrices["A"], matrices["B"], matrices["C"], escalar_k)
        vistas = didactica.informe_cobertura(informe, matrices)
        self.hay_resultado = True
        self.aviso.grid_remove()
        self.area_resultado.llenar(constructores_cobertura(informe), retardo=50)
        self.panel_pasos.mostrar_pasos([{"tipo": "didactica", "etapa": e} for e in vistas["procedimiento"]])
        self.area_verificacion.llenar(constructores_chequeo(vistas["verificacion"]), retardo=45)
        self.pestanas.set("Resultado")
        todas = informe["evaluadas"] and informe["cumplidas"] == informe["evaluadas"]
        self.app.notificar(f"Se cumplen {informe['cumplidas']} de {informe['evaluadas']} propiedades evaluadas.",
                           "exito" if todas else "aviso")

    def _resolver_expresion(self):
        """Resuelve la expresión, la verifica y llena las tres pestañas."""
        nodo = analizar_expresion_matricial(self.entrada_expresion.get())
        matrices = self._leer_matrices(nodo.nombres_matrices())
        escalares = self._leer_escalares(nodo.nombres_escalares())
        resolucion = resolver_expresion_matricial(nodo, matrices, escalares)
        informe = verificar_resolucion(resolucion)
        self.hay_resultado = True
        self.aviso.grid_remove()
        self.area_resultado.llenar(constructores_resultado_expresion(resolucion, informe, self.app,
                                                                    al_guardar=self._guardar_resultado), retardo=70)
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
        """Calcula ambos lados de la propiedad seleccionada y llena las tres pestañas."""
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
        """Muestra las tarjetas de los contraejemplos clásicos."""
        datos = contraejemplos_matriciales()

        def tarjeta(parent, clave, dato):
            """Crea la tarjeta de un contraejemplo con sus matrices, productos y conclusión.

            Entrada: contenedor, clave y datos. Salida: None.
            """
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
        """Carga un contraejemplo en A, B y C y lo resuelve paso a paso.

        Entrada: clave del contraejemplo. Salida: None.
        """
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
        """Muestra el banco de ejercicios tipo examen."""
        def tarjeta(parent, numero, ejercicio):
            """Crea la tarjeta de un ejercicio con su consigna y sus matrices.

            Entrada: contenedor, número y ejercicio. Salida: None.
            """
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
        """Carga las matrices de un ejercicio y lo resuelve en el modo que corresponde.

        Entrada: ejercicio. Salida: None.
        """
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
        """Llena A, B y C con valores aleatorios de sus tamaños actuales."""
        for nombre, bloque in self.bloques.items():
            filas, columnas = bloque["filas"].get(), bloque["columnas"].get()
            self._configurar_matriz(nombre, [[random.randint(-4, 4) for _ in range(columnas)] for _ in range(filas)])
        self._al_cambiar_datos()
        destello(self.tarjeta_datos)
        self.app.notificar("Se generaron matrices aleatorias con los tamaños actuales.", "info")

    def limpiar(self):
        """Pone en 0 las matrices y vacía los resultados."""
        for bloque in self.bloques.values():
            bloque["matriz"].limpiar()
        self.hay_resultado = False
        self.aviso.grid_remove()
        if self.modo in ("Expresión", "Propiedades"):
            self._vaciar("Las matrices quedaron en cero. Escribe sus entradas y presiona «Calcular y verificar».")
        self._actualizar_previa()


class PaginaInformativa(PaginaBase):
    """Página de lectura: las tarjetas aparecen en cascada cada vez que se abre."""

    def __init__(self, parent, app):
        """Crea el área desplazable de la página de lectura.

        Entrada: contenedor y aplicación. Salida: None.
        """
        super().__init__(parent, app)
        self.grid_rowconfigure(1, weight=1)
        self.area = AreaDesplazable(self, PALETA["fondo"])
        self.area.grid(row=1, column=0, sticky="nsew", padx=(24, 12), pady=(0, 20))

    def constructores(self):
        """Prepara las tarjetas de la página; cada subclase las define.

        Salida: lista de constructores.
        """
        return []

    def al_mostrar(self):
        """Llena la página con sus tarjetas en cascada al mostrarla."""
        super().al_mostrar()
        self.area.llenar(self.constructores(), retardo=55)


def tarjeta_numerada(parent, numero, titulo, texto):
    """Crea una tarjeta con un número destacado, un título y un texto explicativo.

    Entrada: contenedor, número, título y texto. Salida: CTkFrame de la tarjeta.
    """
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
    """Página «Método de eliminación»: reglas de Gauss-Jordan con un ejemplo resuelto."""
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
        """Crea las pestañas y resuelve el ejemplo docente.

        Entrada: contenedor y aplicación. Salida: None.
        """
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
        """Llena el procedimiento y la verificación del ejemplo y prepara las tarjetas del resultado.

        Salida: lista de constructores.
        """
        r = self.resultado
        teoria = didactica.etapa("Reglas del método", "Conceptos generales; después se desarrolla el ejemplo numérico.",
                                subpasos=[didactica.etapa(t, x) for t, x in self.PASOS])
        self.panel_pasos.mostrar_pasos([teoria, *didactica.procedimiento_sistema(r)])
        self.area_verificacion.llenar(constructores_chequeo(didactica.verificacion_sistema(r)), retardo=45)
        return [lambda p: tarjeta_estado(p, "Ejemplo resuelto: x1=2, x2=1", "Sistema original: 2x1+x2=5; x1−x2=1. Explora los pasos y la sustitución en sus pestañas.", PALETA["exito"], "✓"),
                *constructores_solucion(r)]


class PaginaAyuda(PaginaInformativa):
    """Página «Ayuda»: uso de la calculadora, atajos, formatos numéricos y conceptos."""
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
        "En «Factorización LU» escribe A y b: se obtiene A = LU con reemplazos de filas, se verifica LU = A y se "
        "resuelve Ly = b (hacia adelante) y luego Ux = y (hacia atrás).",
        "Los botones «↪» encadenan datos: llevan un resultado (L y U, A⁻¹, el resultado de una expresión o un "
        "sistema) a otra sección sin volver a escribirlo.",
        "En «Métodos numéricos» elige Bisección, Graficador, Notación posicional o Errores numéricos. Las funciones se "
        "escriben como x^3 - x - 2, 2sen(x) o e^x; cada opción anima el procedimiento, lo explica y lo verifica.",
        "En el graficador usa la rueda para acercar, arrastra para mover y haz doble clic para volver a la vista inicial.",
        "En «Renders y animaciones» se ve cómo una matriz deforma el plano o el espacio, las rectas y planos de un sistema "
        "y las combinaciones lineales. En 3D, arrastra para girar. Cada gráfica se puede guardar con el botón «PNG».",
    ]
    ATAJOS = [
        ("Enter", "Ir a la siguiente casilla"),
        ("↑  /  ↓", "Moverse a la casilla de arriba o de abajo"),
        (ATAJO_RESOLVER, "Resolver en la sección actual"),
        ("Shift + rueda", "Desplazamiento horizontal"),
    ]
    FORMATOS = [("Enteros", "3,  -7"), ("Decimales", "0.25  o  0,25"), ("Fracciones", "3/2,  -1/4"),
                ("Funciones", "x^2 - 2,  sen(x),  e^x,  ln(x)")]
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
        ("Factorización LU", "A = LU: L es triangular inferior con unos en la diagonal y guarda los multiplicadores; "
                             "U es la forma escalonada de A. Ax = b se resuelve con Ly = b y después Ux = y."),
        ("Inversa", "A⁻¹ existe solo si det(A) ≠ 0 y cumple A⁻¹A = AA⁻¹ = I."),
        ("Bisección", "Si f es continua y f(a)·f(b) < 0, hay una raíz en [a, b]. Cada iteración divide el intervalo a la mitad."),
        ("Notación posicional", "Cada dígito vale según su posición: en base β, la posición k pesa βᵏ."),
        ("Error absoluto y relativo", "Ea = |v − v*| mide la distancia; Er = Ea/|v| la compara con el tamaño de v."),
    ]

    def constructores(self):
        """Prepara las tarjetas de ayuda.

        Salida: lista de constructores.
        """
        def uso(parent):
            """Crea la tarjeta con los pasos para usar la calculadora.

            Entrada: contenedor. Salida: None.
            """
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
            """Crea las tarjetas de atajos de teclado y formatos numéricos aceptados.

            Entrada: contenedor. Salida: None.
            """
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
            """Crea la rejilla de tarjetas con los conceptos clave.

            Entrada: contenedor. Salida: None.
            """
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



class PaginaTeoremas(PaginaInformativa):
    """Página «0. Ver Teoremas Clave del Módulo» de operaciones, determinantes e inversas."""
    titulo = "0. Ver Teoremas Clave del Módulo"
    subtitulo = "Condiciones y conceptos para comprender y defender los algoritmos"

    def constructores(self):
        """Prepara una tarjeta numerada por teorema.

        Salida: lista de constructores.
        """
        return [lambda p, i=i, t=t, d=d: tarjeta_numerada(p, i, t, d)
                for i, (t, d) in enumerate(TEOREMAS_MATRICES, 1)]


class PaginaDeterminantes(PaginaBase):
    """Página «Determinantes e inversas»: det(A), A⁻¹ y sus propiedades con procedimiento y verificación."""
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
        """Crea los cuadros de A y B, el escalar k, el menú de operaciones y las tres pestañas.

        Entrada: contenedor y aplicación. Salida: None.
        """
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
        etiqueta(datos.interior, "Escalar k (operaciones de fila y det(kA)):", FUENTE_NORMAL, ajustar=40).pack(anchor="w", padx=8)
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
        """Avisa que los resultados quedaron desactualizados al editar los datos."""
        if self.informe is None:
            return
        self.informe = None
        self.area_resultado.llenar([lambda p: tarjeta_mensajes(p, "Datos modificados", ["Presiona Calcular para actualizar las tres vistas."], "advertencia")])
        self.panel_pasos.mostrar_placeholder("Los datos cambiaron: vuelve a calcular.")
        self.area_verificacion.llenar([lambda p: placeholder(p, "✓", "Los datos cambiaron: vuelve a calcular.")])

    def _leer(self, nombre):
        """Lee una matriz del cuadro de texto (una fila por línea).

        Entrada: nombre (A o B). Salida: matriz de Fraction; lanza ValueError si no es válida.
        """
        texto = self.entradas[nombre].get("1.0", "end").strip()
        matriz = [[convertir_numero(v) for v in fila.replace(";", " ").split()]
                  for fila in texto.splitlines() if fila.strip()]
        if len(matriz) > LIMITE_DIMENSION or any(len(fila) > LIMITE_DIMENSION for fila in matriz):
            raise ValueError(f"La GUI admite matrices de hasta {LIMITE_DIMENSION}×{LIMITE_DIMENSION}.")
        return validar_matriz(matriz, nombre)

    def resolver(self):
        """Calcula la operación elegida y llena las tres pestañas; ante un error muestra la condición incumplida."""
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
                escalares = {"k": convertir_numero(self.escalar.get())} if metodo in ("det_escalar_fila", "det_suma_fila", "det_escalar_matriz") else None
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
        constructores = constructores_informe(informe)
        if informe["definido"] and self.OPERACIONES[self.operacion.get()][0] == "inv":
            A, inversa = datos["A"], informe["resultado"]
            constructores.append(lambda p: tarjeta_encadenar(
                p, "Encadenar con «Operaciones matriciales»",
                "La A original pasa como A y la inversa calculada como B: BA = A⁻¹A y AB = AA⁻¹ deben dar I.",
                [("Comprobar A⁻¹A = I con B = A⁻¹", lambda: self._enviar_inversa(A, inversa))]))
        A_datos = datos.get("A")
        if A_datos and len(A_datos) in (2, 3) and len(A_datos) == len(A_datos[0]):
            espacio = "el plano" if len(A_datos) == 2 else "el espacio"
            constructores.append(lambda p: tarjeta_encadenar(
                p, f"Ver cómo A deforma {espacio}", "|det(A)| es el factor por el que A multiplica las áreas y los volúmenes.",
                [("Abrir en «Renders y animaciones»", lambda: self.app.ir_a("renders").cargar_transformacion(A_datos))]))
        self.area_resultado.llenar(constructores, retardo=45)
        self.panel_pasos.mostrar_pasos(informe["procedimiento"])
        self.area_verificacion.llenar(constructores_chequeo(informe["verificacion"]), retardo=45)
        self.pestanas.set("Resultado")

    def _enviar_inversa(self, A, inversa):
        """Encadena A y A⁻¹ a Operaciones matriciales para comprobar A⁻¹A = I.

        Entrada: A y su inversa. Salida: None.
        """
        pagina = self.app.ir_a("matrices")
        pagina.establecer_matriz("A", A)
        pagina.establecer_matriz("B", inversa)
        pagina._cambiar_modo("Expresión")
        pagina._usar_expresion("BA")
        pagina.resolver()
        self.app.notificar("B = A⁻¹ viene de «Determinantes e inversas»: BA = A⁻¹A debe ser la identidad.", "info")


_ANCLAS_PILLOW = {"center": "mm", "w": "lm", "e": "rm", "n": "mt", "s": "mb", "nw": "lt", "ne": "rt", "sw": "lb", "se": "rb"}
_FUENTES_PILLOW = {}


def _fuente_pillow(tamano, negrita=False, mono=False):
    """Busca una fuente con símbolos matemáticos para el render en PNG y la guarda en caché.

    Entrada: tamaño en píxeles, negrita y mono (bool). Salida: fuente de Pillow.
    """
    clave = (tamano, negrita, mono)
    if clave not in _FUENTES_PILLOW:
        candidatas = (("Menlo.ttc", "/System/Library/Fonts/Menlo.ttc", "consola.ttf", "DejaVuSansMono.ttf") if mono else
                      ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "seguisym.ttf", "segoeui.ttf", "DejaVuSans.ttf", "Arial.ttf"))
        for nombre in candidatas:
            try:
                _FUENTES_PILLOW[clave] = ImageFont.truetype(nombre, tamano)
                break
            except OSError:
                continue
        else:
            _FUENTES_PILLOW[clave] = ImageFont.load_default(tamano)
    return _FUENTES_PILLOW[clave]


def _trazos_punteados(puntos, trazo, hueco):
    """Divide una polilínea en los trazos de una línea punteada.

    Entrada: puntos, largo del trazo y del hueco. Salida: lista de pares de puntos.
    """
    trazos = []
    for (x1, y1), (x2, y2) in zip(puntos, puntos[1:]):
        largo = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        recorrido = 0.0
        while recorrido < largo:
            fin = min(largo, recorrido + trazo)
            trazos.append(((x1 + (x2 - x1) * recorrido / largo, y1 + (y2 - y1) * recorrido / largo),
                           (x1 + (x2 - x1) * fin / largo, y1 + (y2 - y1) * fin / largo)))
            recorrido += trazo + hueco
    return trazos


def renderizar_png(escena, ancho, alto, ruta, factor=2):
    """Renderiza una escena en un PNG: dibuja al doble de resolución y reduce para suavizar los bordes.

    Entrada: escena, tamaño lógico, ruta y factor de escala. Salida: None; lanza ValueError si falta Pillow.
    """
    if Image is None:
        raise ValueError("Para exportar imágenes hace falta Pillow: pip install -r requirements.txt")
    s = factor * 2
    imagen = Image.new("RGB", (int(ancho * s), int(alto * s)), graficos.TEMA["fondo"])
    dibujo = ImageDraw.Draw(imagen)
    for pieza in escena:
        tipo = pieza["tipo"]
        if tipo == "linea":
            puntos = [(x * s, y * s) for x, y in pieza["puntos"]]
            grosor = max(1, round(pieza["ancho"] * s))
            if pieza["punteada"]:
                for trazo in _trazos_punteados(puntos, 5 * s, 4 * s):
                    dibujo.line(trazo, fill=pieza["color"], width=grosor)
            elif len(puntos) >= 2:
                dibujo.line(puntos, fill=pieza["color"], width=grosor, joint="curve")
        elif tipo == "poligono":
            puntos = [(x * s, y * s) for x, y in pieza["puntos"]]
            if pieza["relleno"] and len(puntos) >= 3:
                dibujo.polygon(puntos, fill=pieza["relleno"])
            if pieza["borde"]:
                dibujo.line(puntos + puntos[:1], fill=pieza["borde"], width=max(1, round(pieza["ancho"] * s)))
        elif tipo == "circulo":
            r = pieza["radio"] * s
            x, y = pieza["x"] * s, pieza["y"] * s
            dibujo.ellipse((x - r, y - r, x + r, y + r), fill=pieza["relleno"], outline=pieza["borde"],
                           width=max(1, round(pieza["ancho"] * s)))
        else:
            dibujo.text((pieza["x"] * s, pieza["y"] * s), pieza["texto"], fill=pieza["color"],
                        font=_fuente_pillow(round(pieza["tamano"] * s * 1.05), pieza["negrita"], pieza["mono"]),
                        anchor=_ANCLAS_PILLOW[pieza["ancla"]])
    imagen.resize((int(ancho * factor), int(alto * factor)), Image.LANCZOS).save(ruta)


class LienzoEscena(tk.Canvas):
    """Lienzo que dibuja una escena de modulos/graficos.py y la vuelve a calcular al cambiar de tamaño."""

    def __init__(self, parent, generador=None, alto=None):
        """Crea el lienzo.

        Entrada: contenedor, generador(ancho, alto) que retorna la escena (o (escena, alto natural)) y alto fijo. Salida: None.
        """
        escala = escala_de(parent)
        super().__init__(parent, highlightthickness=0, bd=0, bg=graficos.TEMA["fondo"], height=round((alto or 120) * escala))
        self.escala = escala
        self.generador = generador
        self.ultima_escena = []
        self._pendiente = None
        self.bind("<Configure>", lambda _evento: self.programar())

    def tamano_logico(self):
        """Obtiene el tamaño del lienzo sin la escala de la pantalla.

        Salida: (ancho, alto).
        """
        return self.winfo_width() / self.escala, self.winfo_height() / self.escala

    def programar(self):
        """Agrupa varios cambios seguidos en un solo redibujado."""
        if self._pendiente is None:
            self._pendiente = self.after_idle(self.dibujar)

    def dibujar(self):
        """Calcula la escena con el tamaño actual y la pinta."""
        self._pendiente = None
        ancho, alto = self.tamano_logico()
        if self.generador is None or ancho <= 2 or alto <= 2:
            return
        resultado = self.generador(ancho, alto)
        if isinstance(resultado, tuple):
            resultado, natural = resultado
            if abs(natural - alto) > 1:
                self.configure(height=round(natural * self.escala))
        self.pintar(resultado)

    def pintar(self, escena):
        """Convierte las primitivas de la escena en elementos del Canvas.

        Entrada: lista de primitivas. Salida: None.
        """
        self.ultima_escena = escena
        self.delete("all")
        e = self.escala
        for pieza in escena:
            tipo = pieza["tipo"]
            if tipo == "linea":
                puntos = [c * e for punto in pieza["puntos"] for c in punto]
                if len(puntos) >= 4:
                    self.create_line(puntos, fill=pieza["color"], width=pieza["ancho"] * e, capstyle="round", joinstyle="round",
                                     dash=(5, 4) if pieza["punteada"] else "")
            elif tipo == "poligono":
                puntos = [c * e for punto in pieza["puntos"] for c in punto]
                self.create_polygon(puntos, fill=pieza["relleno"], outline=pieza["borde"] or "", width=pieza["ancho"] * e)
            elif tipo == "circulo":
                r = pieza["radio"] * e
                x, y = pieza["x"] * e, pieza["y"] * e
                self.create_oval(x - r, y - r, x + r, y + r, fill=pieza["relleno"], outline=pieza["borde"] or "", width=pieza["ancho"] * e)
            else:
                fuente = (FAMILIA_MONO if pieza["mono"] else FAMILIA, -round(pieza["tamano"] * e * 1.08), "bold" if pieza["negrita"] else "normal")
                self.create_text(pieza["x"] * e, pieza["y"] * e, text=pieza["texto"], fill=pieza["color"], font=fuente, anchor=pieza["ancla"])

    def exportar_png(self, nombre="render"):
        """Pide dónde guardar y renderiza la escena actual en un PNG de alta resolución.

        Entrada: nombre sugerido del archivo. Salida: ruta guardada, o None si se canceló.
        """
        ruta = filedialog.asksaveasfilename(parent=self, defaultextension=".png", initialfile=f"{nombre}.png",
                                            filetypes=[("Imagen PNG", "*.png")], title="Exportar render")
        if not ruta:
            return None
        renderizar_png(self.ultima_escena, *self.tamano_logico(), ruta)
        return ruta


class LienzoGrafico(LienzoEscena):
    """Gráfica interactiva: la rueda acerca, arrastrar mueve, doble clic restablece y el cursor lee los valores."""

    _recibe_rueda = True

    def __init__(self, parent):
        """Crea la gráfica vacía y enlaza el mouse.

        Entrada: contenedor. Salida: None.
        """
        super().__init__(parent, self._escena, alto=380)
        self.funciones, self.marcadores = [], []
        self.vista, self.rango_inicial, self._curvas, self._arrastre, self._puntero = None, None, None, None, None
        self.progreso = 1.0
        self.bind("<ButtonPress-1>", self._presionar)
        self.bind("<B1-Motion>", self._arrastrar)
        self.bind("<ButtonRelease-1>", self._soltar)
        self.bind("<Motion>", self._mover)
        self.bind("<Leave>", self._salir)
        self.bind("<Double-Button-1>", lambda _evento: self.restablecer())

    def mostrar(self, funciones, x_min, x_max, marcadores=()):
        """Carga funciones y puntos notables y encuadra la vista.

        Entrada: funciones, intervalo y marcadores. Salida: None.
        """
        self.funciones, self.marcadores = list(funciones), list(marcadores)
        self.rango_inicial = (x_min, x_max)
        self.restablecer()

    def restablecer(self):
        """Vuelve a la vista inicial."""
        if self.rango_inicial is None:
            return
        ancho, alto = self.tamano_logico()
        self.vista = graficos.vista_para_funciones(self.funciones, *self.rango_inicial, max(ancho, 100), max(alto, 100))
        self._curvas = None
        self.programar()

    def _escena(self, ancho, alto):
        """Construye la escena con la vista actual; las curvas solo se recalculan si la vista cambió.

        Entrada: tamaño lógico. Salida: lista de primitivas.
        """
        if self.vista is None:
            return [graficos.rectangulo(0, 0, ancho, alto, graficos.TEMA["fondo"]),
                    graficos.texto(ancho / 2, alto / 2, "Escribe una función y presiona «Graficar».", graficos.TEMA["texto_3"], 14)]
        if (self.vista.ancho, self.vista.alto) != (ancho, alto):
            self.vista = self.vista.redimensionada(ancho, alto)
            self._curvas = None
        if self._curvas is None:
            self._curvas = graficos.curvas_en_vista(self.funciones, self.vista)
        return graficos.escena_grafica(self.vista, self._curvas, self.progreso, self.marcadores, cursor=self._datos_cursor())

    def _datos_cursor(self):
        """Lee las funciones en la posición del puntero.

        Salida: diccionario para la escena, o None si el puntero no está sobre la gráfica.
        """
        if self._puntero is None or self._arrastre is not None or self.progreso < 1:
            return None
        x, y = self.vista.a_plano(self._puntero[0] / self.escala, self._puntero[1] / self.escala)
        filas = [{"color": graficos.TEMA["texto"], "texto": f"x = {numericos.formatear_real(x, 6)}", "punto": None}]
        for k, funcion in enumerate(self.funciones):
            valor = funcion.evaluar(x)
            filas.append({"color": graficos.SERIES[k], "texto": f"{'fgh'[k]}(x) = {numericos.formatear_real(valor, 6)}",
                          "punto": (x, valor) if valor is not None else None})
        return {"x": x, "y": y, "filas": filas}

    def al_girar_rueda(self, pixeles, horizontal, x_root, y_root):
        """Acerca o aleja alrededor del puntero; el giro horizontal mueve la vista.

        Entrada: píxeles girados, horizontal (bool) y posición del puntero en la pantalla. Salida: None.
        """
        if self.vista is None:
            return
        if horizontal:
            self.vista = self.vista.desplazada(-pixeles, 0)
        else:
            factor = max(0.5, min(2.0, 1.004 ** pixeles))
            nueva = self.vista.acercada(factor, (x_root - self.winfo_rootx()) / self.escala, (y_root - self.winfo_rooty()) / self.escala)
            if not 1e-10 < nueva.x_max - nueva.x_min < 1e10:
                return
            self.vista = nueva
        self._curvas = None
        self.programar()

    def _presionar(self, evento):
        """Empieza a arrastrar la vista.

        Entrada: evento del mouse. Salida: None.
        """
        self._arrastre = (evento.x, evento.y)

    def _arrastrar(self, evento):
        """Mueve la vista con el arrastre.

        Entrada: evento del mouse. Salida: None.
        """
        if self.vista is None or self._arrastre is None:
            return
        self.vista = self.vista.desplazada((evento.x - self._arrastre[0]) / self.escala, (evento.y - self._arrastre[1]) / self.escala)
        self._arrastre = (evento.x, evento.y)
        self._curvas = None
        self.programar()

    def _soltar(self, _evento):
        """Termina el arrastre."""
        self._arrastre = None
        self.programar()

    def _mover(self, evento):
        """Actualiza el cursor de lectura.

        Entrada: evento del mouse. Salida: None.
        """
        self._puntero = (evento.x, evento.y)
        if self.vista is not None:
            self.programar()

    def _salir(self, _evento):
        """Oculta el cursor de lectura al salir de la gráfica."""
        self._puntero = None
        if self.vista is not None:
            self.programar()


class Reproductor(_Marco):
    """Controles de una animación: reproducir, pausar, reiniciar, línea de tiempo, velocidad y exportar."""

    VELOCIDADES = {"½×": 0.5, "1×": 1.0, "2×": 2.0}

    def __init__(self, parent, al_cambiar, formato=None, al_exportar=None):
        """Crea los controles.

        Entrada: contenedor, al_cambiar(t), formato(t) del texto de posición y al_exportar. Salida: None.
        """
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.al_cambiar, self.formato = al_cambiar, formato
        self.t, self.maximo, self.segundos, self.bucle = 0.0, 1.0, 4.0, False
        self.velocidad, self._tarea, self._ultimo = 1.0, None, 0.0
        self.boton_reiniciar = boton_secundario(self, "⏮", self.reiniciar, width=38, height=32)
        self.boton_reiniciar.pack(side="left")
        self.boton = boton_primario(self, "▶", self.alternar, width=46, height=32)
        self.boton.pack(side="left", padx=(6, 10))
        self.linea_tiempo = ctk.CTkSlider(self, from_=0, to=1, command=self._al_mover, height=16,
                                          progress_color=PALETA["primario"], button_color=PALETA["primario"],
                                          button_hover_color=PALETA["primario_hover"], fg_color=PALETA["panel_2"])
        self.linea_tiempo.set(0)
        self.linea_tiempo.pack(side="left", fill="x", expand=True)
        self.etiqueta = etiqueta(self, "", FUENTE_PEQUENA_NEGRITA, "texto", width=112, anchor="e")
        self.etiqueta.pack(side="left", padx=(8, 8))
        self.selector = ctk.CTkSegmentedButton(self, values=list(self.VELOCIDADES), command=self._cambiar_velocidad, font=FUENTE_PEQUENA_NEGRITA,
                                               height=28, fg_color=PALETA["panel_2"], selected_color=PALETA["primario"],
                                               selected_hover_color=PALETA["primario_hover"], unselected_color=PALETA["panel_2"],
                                               unselected_hover_color=PALETA["secundario_hover"], text_color=PALETA["texto"])
        self.selector.set("1×")
        self.selector.pack(side="left")
        self.extras = ctk.CTkFrame(self, fg_color="transparent", width=1, height=1)
        self.extras.pack(side="left", padx=(8, 0))
        if al_exportar is not None:
            boton_secundario(self, "PNG", al_exportar, width=52, height=32, font=FUENTE_PEQUENA_NEGRITA).pack(side="left", padx=(8, 0))

    def configurar(self, maximo=1.0, segundos=4.0, bucle=False):
        """Define la duración de la animación.

        Entrada: valor final de t, segundos totales y bucle (bool). Salida: None.
        """
        self.maximo, self.segundos, self.bucle = max(float(maximo), 1e-9), max(0.2, float(segundos)), bucle

    def fijar(self, t, notificar=True):
        """Lleva la animación al instante t.

        Entrada: t y notificar (bool). Salida: None.
        """
        self.t = max(0.0, min(self.maximo, float(t)))
        self.linea_tiempo.set(self.t / self.maximo)
        if self.formato is not None:
            self.etiqueta.configure(text=self.formato(self.t))
        if notificar:
            self.al_cambiar(self.t)

    def reproducir(self, desde_inicio=True):
        """Inicia la animación.

        Entrada: desde_inicio (bool). Salida: None.
        """
        self.pausar()
        if desde_inicio or self.t >= self.maximo:
            self.fijar(0.0)
        self.boton.configure(text="⏸")
        self._ultimo = time.perf_counter()
        self._tarea = self.after(16, self._tic)

    def pausar(self):
        """Detiene la animación sin perder la posición."""
        if self._tarea is not None:
            self.after_cancel(self._tarea)
            self._tarea = None
        self.boton.configure(text="▶")

    def alternar(self):
        """Reproduce o pausa según el estado actual."""
        if self._tarea is not None:
            self.pausar()
        else:
            self.reproducir(desde_inicio=False)

    def reiniciar(self):
        """Vuelve al inicio sin reproducir."""
        self.pausar()
        self.fijar(0.0)

    def _tic(self):
        """Avanza un cuadro según el tiempo real; se pausa si la animación dejó de estar visible."""
        self._tarea = None
        if not self.winfo_viewable():
            self.pausar()
            return
        ahora = time.perf_counter()
        t = self.t + (ahora - self._ultimo) * self.velocidad * self.maximo / self.segundos
        self._ultimo = ahora
        if t >= self.maximo and not self.bucle:
            self.fijar(self.maximo)
            self.pausar()
            return
        self.fijar(t % self.maximo if self.bucle else t)
        self._tarea = self.after(16, self._tic)

    def _al_mover(self, valor):
        """Lleva la animación al punto elegido en la línea de tiempo.

        Entrada: valor entre 0 y 1. Salida: None.
        """
        self.pausar()
        self.fijar(float(valor) * self.maximo)

    def _cambiar_velocidad(self, valor):
        """Cambia la velocidad de reproducción.

        Entrada: texto de la velocidad. Salida: None.
        """
        self.velocidad = self.VELOCIDADES[valor]


def exportar_lienzo(app, lienzo, nombre):
    """Exporta un lienzo a PNG y notifica el resultado.

    Entrada: aplicación, lienzo y nombre sugerido. Salida: None.
    """
    try:
        ruta = lienzo.exportar_png(nombre)
    except (ValueError, OSError) as error:
        app.notificar(f"No se pudo exportar: {error}", "error")
        return
    if ruta:
        app.notificar(f"Render guardado en {os.path.basename(ruta)}", "exito")


def tarjeta_lienzo(parent, titulo, subtitulo, generador, alto=None):
    """Crea una tarjeta de resultado con un render dentro.

    Entrada: contenedor, título, subtítulo, generador de la escena y alto fijo opcional. Salida: CTkFrame de la tarjeta.
    """
    tarjeta = tarjeta_seccion(parent, titulo, subtitulo)
    LienzoEscena(tarjeta, generador, alto=alto).pack(fill="x", padx=12, pady=(0, 12))
    return tarjeta


def constructores_render_sistema(app, resultado):
    """Agrega el acceso al render de rectas o planos cuando el sistema tiene 2 o 3 incógnitas.

    Entrada: aplicación y resultado de resolver_sistema. Salida: lista de constructores (vacía si no aplica).
    """
    A = [fila[:-1] for fila in resultado["matriz_inicial"]]
    b = [fila[-1] for fila in resultado["matriz_inicial"]]
    if len(A[0]) not in (2, 3) or len(A) > PaginaRenders.MAXIMO_FILAS:
        return []
    figura = "una recta" if len(A[0]) == 2 else "un plano"
    return [lambda p: tarjeta_encadenar(p, "Ver el sistema en el espacio", f"Cada ecuación es {figura}; la solución es donde se cruzan.",
                                        [("Abrir en «Renders y animaciones»", lambda: app.ir_a("renders").cargar_sistema(A, b))])]


class OpcionNumerica:
    """Base de las cuatro opciones del módulo: datos a la izquierda y animación en la primera pestaña."""

    nombre = ""
    titulo_datos = ""
    EJEMPLOS = {}

    def __init__(self, pagina):
        """Crea el marco de datos y el marco de la animación de la opción.

        Entrada: página de métodos numéricos. Salida: None.
        """
        self.pagina = pagina
        self.informe = None
        self.campos = {}
        self.marco_datos = ctk.CTkFrame(pagina.datos.interior, fg_color="transparent")
        self.marco_visual = ctk.CTkFrame(pagina.pestana_animacion, fg_color="transparent")
        if self.EJEMPLOS:
            etiqueta(self.marco_datos, "Ejemplos", FUENTE_PEQUENA_NEGRITA, "texto_3").pack(anchor="w", padx=8)
            self.menu = ctk.CTkOptionMenu(self.marco_datos, values=list(self.EJEMPLOS), command=self.cargar_ejemplo, height=32,
                                          dynamic_resizing=False, fg_color=PALETA["secundario"], button_color=PALETA["secundario_hover"],
                                          button_hover_color=PALETA["primario_hover"], text_color=PALETA["texto"])
            self.menu.pack(fill="x", padx=8, pady=(2, 10))
        self.construir_datos(self.marco_datos)
        self.construir_visual(self.marco_visual)

    def campo(self, nombre, rotulo, valor=""):
        """Crea una casilla con su rótulo; Enter resuelve.

        Entrada: clave, rótulo y valor inicial. Salida: CTkEntry.
        """
        etiqueta(self.marco_datos, rotulo, FUENTE_PEQUENA_NEGRITA, "texto_3", ajustar=30).pack(anchor="w", padx=8)
        entrada = ctk.CTkEntry(self.marco_datos, height=34, font=(FAMILIA_MONO, 13), fg_color=PALETA["entrada"], border_color=PALETA["borde"],
                               text_color=PALETA["texto"])
        entrada.insert(0, valor)
        entrada.pack(fill="x", padx=8, pady=(2, 10))
        entrada.bind("<Return>", lambda _evento: self.pagina.resolver(), add="+")
        entrada.bind("<KeyRelease>", self.pagina.datos_cambiaron, add="+")
        self.campos[nombre] = entrada
        return entrada

    def fijar_campos(self, valores):
        """Escribe varios valores en las casillas.

        Entrada: diccionario clave → texto. Salida: None.
        """
        for nombre, valor in valores.items():
            self.campos[nombre].delete(0, "end")
            self.campos[nombre].insert(0, valor)

    def valor(self, nombre):
        """Lee una casilla.

        Entrada: clave. Salida: texto sin espacios en los extremos.
        """
        return self.campos[nombre].get().strip()

    def cargar_ejemplo(self, nombre):
        """Carga un ejemplo y lo resuelve.

        Entrada: nombre del ejemplo. Salida: None.
        """
        self.fijar_campos(self.EJEMPLOS[nombre])
        self.pagina.resolver()

    def construir_datos(self, parent):
        """Crea las casillas de la opción; cada subclase lo define.

        Entrada: contenedor. Salida: None.
        """

    def construir_visual(self, parent):
        """Crea los lienzos de la opción; cada subclase lo define.

        Entrada: contenedor. Salida: None.
        """

    def calcular(self):
        """Lee los datos y calcula el informe; cada subclase lo define.

        Salida: informe; lanza ValueError si los datos no son válidos.
        """
        raise NotImplementedError

    def mostrar_visual(self, informe):
        """Muestra y reproduce la animación; cada subclase lo define.

        Entrada: informe. Salida: None.
        """

    def constructores_resultado(self, informe):
        """Prepara las tarjetas de la pestaña Resultado; cada subclase lo define.

        Entrada: informe. Salida: lista de constructores.
        """
        raise NotImplementedError

    def texto_vacio(self):
        """Indica qué hacer antes del primer cálculo.

        Salida: cadena.
        """
        return "Escribe los datos y presiona el botón."


class OpcionBiseccion(OpcionNumerica):
    """Opción 1: método de bisección con el intervalo animado y la curva de convergencia."""

    nombre = "1. Bisección"
    titulo_datos = "Método de bisección"
    EJEMPLOS = {
        "x³ − x − 2 en [1, 2]": {"funcion": "x^3 - x - 2", "a": "1", "b": "2", "tol": "1e-6", "iter": "50"},
        "cos(x) − x en [0, 1]": {"funcion": "cos(x) - x", "a": "0", "b": "1", "tol": "1e-8", "iter": "50"},
        "eˣ − 3x en [0, 1]": {"funcion": "e^x - 3x", "a": "0", "b": "1", "tol": "1e-6", "iter": "50"},
        "√2: x² − 2 en [1, 2]": {"funcion": "x^2 - 2", "a": "1", "b": "2", "tol": "1e-10", "iter": "60"},
        "Sin cambio de signo: x² + 1": {"funcion": "x^2 + 1", "a": "-1", "b": "1", "tol": "1e-6", "iter": "50"},
        "Discontinuidad: tan(x) en [1, 2]": {"funcion": "tan(x)", "a": "1", "b": "2", "tol": "1e-6", "iter": "50"},
    }

    def construir_datos(self, parent):
        """Crea las casillas de f, a, b, tolerancia e iteraciones.

        Entrada: contenedor. Salida: None.
        """
        self.campo("funcion", "Función f(x)", "x^3 - x - 2")
        self.campo("a", "Extremo a (admite pi/2, sqrt(2)…)", "1")
        self.campo("b", "Extremo b", "2")
        self.campo("tol", "Tolerancia", "1e-6")
        self.campo("iter", f"Máximo de iteraciones (hasta {numericos.LIMITE_ITERACIONES})", "50")

    def construir_visual(self, parent):
        """Crea la línea de tiempo, el lienzo de la animación y el de convergencia.

        Entrada: contenedor. Salida: None.
        """
        self.seguir = ctk.BooleanVar(value=True)
        self.reproductor = Reproductor(parent, self._al_tiempo, self._formato, lambda: exportar_lienzo(self.pagina.app, self.lienzo, "biseccion"))
        self.reproductor.pack(fill="x", padx=6, pady=(4, 6))
        ctk.CTkSwitch(self.reproductor.extras, text="Seguir", variable=self.seguir, command=self._redibujar, font=FUENTE_PEQUENA,
                      text_color=PALETA["texto"], progress_color=PALETA["primario"], width=44).pack(side="left")
        self.lienzo = LienzoEscena(parent, self._escena, alto=330)
        self.lienzo.pack(fill="both", expand=True, padx=6)
        self.convergencia = LienzoEscena(parent, self._escena_convergencia, alto=170)
        self.convergencia.pack(fill="x", padx=6, pady=(8, 4))

    def _formato(self, t):
        """Escribe la posición de la animación.

        Entrada: t. Salida: cadena.
        """
        if self.informe is None or not self.informe.get("iteraciones"):
            return ""
        return f"Iteración {min(self.informe['n'], int(t) + 1)} de {self.informe['n']}"

    def _al_tiempo(self, _t):
        """Redibuja la animación; la convergencia solo cambia al pasar de iteración."""
        self.lienzo.dibujar()
        if int(self.reproductor.t) != getattr(self, "_iteracion_dibujada", None):
            self._iteracion_dibujada = int(self.reproductor.t)
            self.convergencia.dibujar()

    def _redibujar(self):
        """Redibuja al cambiar la opción de seguir el intervalo."""
        self.lienzo.dibujar()

    def _escena(self, ancho, alto):
        """Construye el cuadro actual.

        Entrada: tamaño lógico. Salida: lista de primitivas.
        """
        if self.informe is None:
            return [graficos.rectangulo(0, 0, ancho, alto, graficos.TEMA["fondo"]),
                    graficos.texto(ancho / 2, alto / 2, "Escribe f, a y b y presiona «Calcular y animar».", graficos.TEMA["texto_3"], 14)]
        if not self.informe["definido"]:
            return graficos.escena_intervalo_sin_raiz(self.informe, ancho, alto)
        return graficos.escena_biseccion(self.informe, self.reproductor.t, ancho, alto, self.seguir.get())

    def _escena_convergencia(self, ancho, alto):
        """Construye la gráfica de convergencia.

        Entrada: tamaño lógico. Salida: lista de primitivas.
        """
        if self.informe is None or not self.informe["definido"]:
            mensaje = "Aquí se verá cómo baja el error en cada iteración." if self.informe is None else "No hay iteraciones: la bisección no se pudo aplicar."
            return [graficos.rectangulo(0, 0, ancho, alto, graficos.TEMA["fondo"]),
                    graficos.texto(ancho / 2, alto / 2, mensaje, graficos.TEMA["texto_3"], 12)]
        return graficos.escena_convergencia(self.informe, self.reproductor.t, ancho, alto)

    def calcular(self):
        """Lee los datos y aplica la bisección.

        Salida: informe; lanza ValueError si los datos no son válidos.
        """
        try:
            iteraciones = int(self.valor("iter"))
        except ValueError:
            raise ValueError("El máximo de iteraciones debe ser un número entero.") from None
        return numericos.biseccion(self.valor("funcion"), numericos.leer_real(self.valor("a"), "a"), numericos.leer_real(self.valor("b"), "b"),
                                   numericos.leer_real(self.valor("tol"), "La tolerancia"), iteraciones)

    def mostrar_visual(self, informe):
        """Reinicia la animación con el informe nuevo.

        Entrada: informe. Salida: None.
        """
        self.reproductor.pausar()
        self._iteracion_dibujada = None
        if informe["definido"] and informe["iteraciones"]:
            self.reproductor.configurar(informe["n"], max(4.0, informe["n"] * 1.1))
            self.reproductor.fijar(0.0)
            self.convergencia.dibujar()
            self.pagina.after(250, self.reproductor.reproducir)
        else:
            self.reproductor.configurar(1, 1)
            self.reproductor.fijar(1.0 if informe["definido"] else 0.0)
            self.convergencia.dibujar()

    def constructores_resultado(self, informe):
        """Prepara el estado, los indicadores, las advertencias y la tabla de iteraciones.

        Entrada: informe. Salida: lista de constructores.
        """
        if not informe["definido"]:
            lista = [lambda p: tarjeta_estado(p, informe["titulo"], informe["conclusion"], PALETA["advertencia"], "!")]
            if informe.get("sugerencia"):
                p_, q_ = informe["sugerencia"]
                lista.append(lambda p: tarjeta_encadenar(p, "Intervalo sugerido", "En este subintervalo f sí cambia de signo.",
                                                         [(f"Usar [{numericos.formatear_real(p_, 6)}, {numericos.formatear_real(q_, 6)}]",
                                                           lambda: self._usar_intervalo(p_, q_))]))
            return lista
        color, icono = (PALETA["exito"], "✓") if informe["es_raiz"] and informe["alcanzo_tolerancia"] else (PALETA["advertencia"], "!")
        if not informe["es_raiz"]:
            color, icono = PALETA["error"], "✕"
        lista = [lambda p: tarjeta_estado(p, informe["titulo"], informe["conclusion"], color, icono),
                 lambda p: fila_indicadores(p, [(informe["n"], "Iteraciones realizadas"), (informe["n_teorico"], "Cota teórica de iteraciones"),
                                                (numericos.formatear_real(informe["iteraciones"][-1]["cota_error"], 2) if informe["iteraciones"] else "0", "Cota del error")])]
        if informe["advertencias"]:
            lista.append(lambda p: tarjeta_mensajes(p, "Advertencias", informe["advertencias"], "advertencia"))
        if informe["iteraciones"]:
            filas = [[str(it["n"]), numericos.formatear_real(it["a"], 8), numericos.formatear_real(it["b"], 8), numericos.formatear_real(it["c"], 8),
                      numericos.formatear_real(it["fc"], 4), numericos.formatear_real(it["cota_error"], 3)] for it in informe["iteraciones"]]
            lista.append(lambda p: tarjeta_lienzo(
                p, "Tabla de iteraciones", "c = (a + b)/2; la cota del error es (b − a)/2.",
                lambda ancho, _alto: (graficos.escena_tabla(["n", "a", "b", "c", "f(c)", "cota"], filas, ancho, [0.5, 1.5, 1.5, 1.5, 1.3, 1.1], resaltar=len(filas) - 1),
                                      graficos.alto_tabla(len(filas), con_titulo=False))))
        return lista

    def _usar_intervalo(self, a, b):
        """Usa el intervalo sugerido y vuelve a resolver.

        Entrada: extremos. Salida: None.
        """
        self.fijar_campos({"a": repr(a), "b": repr(b)})
        self.pagina.resolver()

    def texto_vacio(self):
        """Indica qué hacer antes del primer cálculo.

        Salida: cadena.
        """
        return "Escribe f(x) y un intervalo [a, b] con f(a)·f(b) < 0."


class OpcionGraficador(OpcionNumerica):
    """Opción 2: graficador interactivo de hasta tres funciones, con trazado animado y puntos notables."""

    nombre = "2. Graficador"
    titulo_datos = "Graficador de funciones"
    EJEMPLOS = {
        "Parábola y recta": {"f": "x^2 - 2", "g": "x", "h": "", "x_min": "-4", "x_max": "4"},
        "Seno, coseno y su suma": {"f": "sen(x)", "g": "cos(x)", "h": "sen(x) + cos(x)", "x_min": "-2pi", "x_max": "2pi"},
        "Cúbica": {"f": "x^3 - 3x + 1", "g": "", "h": "", "x_min": "-3", "x_max": "3"},
        "Exponencial y logaritmo": {"f": "e^x", "g": "ln(x)", "h": "x", "x_min": "-3", "x_max": "4"},
        "Asíntotas: tan(x) y 1/x": {"f": "tan(x)", "g": "1/x", "h": "", "x_min": "-5", "x_max": "5"},
        "Onda amortiguada": {"f": "e^(-x/4)sen(3x)", "g": "e^(-x/4)", "h": "-e^(-x/4)", "x_min": "0", "x_max": "14"},
    }

    def construir_datos(self, parent):
        """Crea las casillas de las funciones y del intervalo.

        Entrada: contenedor. Salida: None.
        """
        self.campo("f", "f(x)", "x^3 - 3x + 1")
        self.campo("g", "g(x) (opcional)", "")
        self.campo("h", "h(x) (opcional)", "")
        self.campo("x_min", "x mínimo (admite -2pi…)", "-3")
        self.campo("x_max", "x máximo", "3")
        etiqueta(parent, "Funciones: sen, cos, tan, exp, ln, log, sqrt, abs, asen, acos, atan, senh, cosh, tanh. Constantes: pi, e.",
                 FUENTE_PEQUENA, "texto_3", ajustar=30).pack(anchor="w", padx=8, pady=(0, 8))

    def construir_visual(self, parent):
        """Crea la línea de tiempo del trazado, el botón de vista y la gráfica interactiva.

        Entrada: contenedor. Salida: None.
        """
        self.reproductor = Reproductor(parent, self._al_tiempo, lambda t: f"Trazado {round(t * 100)} %", lambda: exportar_lienzo(self.pagina.app, self.lienzo, "grafica"))
        self.reproductor.pack(fill="x", padx=6, pady=(4, 6))
        boton_secundario(self.reproductor.extras, "Vista inicial", lambda: self.lienzo.restablecer(), width=88, height=32, font=FUENTE_PEQUENA_NEGRITA).pack(side="left")
        self.lienzo = LienzoGrafico(parent)
        self.lienzo.pack(fill="both", expand=True, padx=6)
        etiqueta(parent, "Rueda: acercar y alejar  ·  Arrastrar: mover  ·  Doble clic: vista inicial  ·  El cursor lee los valores",
                 FUENTE_PEQUENA, "texto_3").pack(anchor="w", padx=8, pady=(6, 2))

    def _al_tiempo(self, t):
        """Actualiza el avance del trazado.

        Entrada: t entre 0 y 1. Salida: None.
        """
        self.lienzo.progreso = t
        self.lienzo.dibujar()

    def calcular(self):
        """Lee los datos y analiza las funciones.

        Salida: informe; lanza ValueError si los datos no son válidos.
        """
        return numericos.informe_graficador([self.valor("f"), self.valor("g"), self.valor("h")],
                                            numericos.leer_real(self.valor("x_min"), "x mínimo"), numericos.leer_real(self.valor("x_max"), "x máximo"))

    def mostrar_visual(self, informe):
        """Carga las funciones y anima su trazado de izquierda a derecha.

        Entrada: informe. Salida: None.
        """
        marcadores = []
        for k, datos in enumerate(informe["analisis"]):
            for x in datos["raices"]:
                marcadores.append({"x": x, "y": 0.0, "color": graficos.TEMA["exito"], "etiqueta": f"x = {numericos.formatear_real(x, 4)}"})
            for x, y in datos["maximos"] + datos["minimos"]:
                marcadores.append({"x": x, "y": y, "color": graficos.SERIES[k], "radio": 4})
        for corte in informe["cortes"]:
            marcadores.append({"x": corte["x"], "y": corte["y"], "color": graficos.TEMA["texto"], "radio": 5})
        if len(marcadores) > 40:
            marcadores = [{**m, "etiqueta": None} for m in marcadores]
        self.reproductor.pausar()
        self.lienzo.progreso = 0.0
        self.lienzo.mostrar(informe["funciones"], informe["x_min"], informe["x_max"], marcadores)
        self.reproductor.configurar(1.0, 2.4)
        self.reproductor.fijar(0.0)
        self.pagina.after(150, self.reproductor.reproducir)

    def constructores_resultado(self, informe):
        """Prepara el estado, los puntos notables de cada función y sus intersecciones.

        Entrada: informe. Salida: lista de constructores.
        """
        lista = [lambda p: tarjeta_estado(p, informe["titulo"], informe["conclusion"], PALETA["exito"], "∿")]
        for k, datos in enumerate(informe["analisis"]):
            nombre = "fgh"[k]
            mensajes = [f"Ceros: {', '.join(numericos.formatear_real(r, 8) for r in datos['raices']) or 'ninguno en el intervalo'}",
                        f"Máximos locales: {numericos.texto_puntos(datos['maximos'])}",
                        f"Mínimos locales: {numericos.texto_puntos(datos['minimos'])}"]
            if datos["corte_y"] is not None:
                mensajes.append(f"Corte con el eje y: {numericos.formatear_real(datos['corte_y'], 8)}")
            if datos["saltos"]:
                mensajes.append("Discontinuidades cerca de x = " + ", ".join(numericos.formatear_real(s, 5) for s in datos["saltos"]))
            lista.append(lambda p, n=nombre, f=datos["funcion"], m=mensajes: tarjeta_mensajes(p, f"{n}(x) = {f.texto}", m, "primario"))
        if informe["cortes"]:
            filas = [f"{'fgh'[c['i']]} y {'fgh'[c['j']]} en ({numericos.formatear_real(c['x'], 7)}, {numericos.formatear_real(c['y'], 7)})" for c in informe["cortes"]]
            lista.append(lambda p: tarjeta_mensajes(p, "Intersecciones", filas, "advertencia"))
        return lista

    def texto_vacio(self):
        """Indica qué hacer antes del primer cálculo.

        Salida: cadena.
        """
        return "Escribe hasta tres funciones y presiona «Graficar»."


class OpcionPosicional(OpcionNumerica):
    """Opción 3: notación posicional en base 10 y base 2, conversión y representación en la computadora."""

    nombre = "3. Notación posicional"
    titulo_datos = "Notación posicional"
    EJEMPLOS = {
        "13.625 en base 10": {"numero": "13.625", "base": "Base 10"},
        "0.1 (no se guarda exacto)": {"numero": "0.1", "base": "Base 10"},
        "255 en base 10": {"numero": "255", "base": "Base 10"},
        "-5.75 en base 10": {"numero": "-5.75", "base": "Base 10"},
        "1101.101 en base 2": {"numero": "1101.101", "base": "Base 2"},
        "11111111 en base 2": {"numero": "11111111", "base": "Base 2"},
    }

    def construir_datos(self, parent):
        """Crea la casilla del número y los selectores de base y de precisión.

        Entrada: contenedor. Salida: None.
        """
        self.campo("numero", "Número (con punto o coma decimal)", "13.625")
        etiqueta(parent, "Está escrito en", FUENTE_PEQUENA_NEGRITA, "texto_3").pack(anchor="w", padx=8)
        self.base = self._selector(parent, ["Base 10", "Base 2"], lambda _v: self.pagina.datos_cambiaron())
        etiqueta(parent, "Precisión en la computadora", FUENTE_PEQUENA_NEGRITA, "texto_3").pack(anchor="w", padx=8)
        self.precision = self._selector(parent, ["32 bits", "64 bits"], lambda _v: self._redibujar())
        self.precision.set("64 bits")

    def _selector(self, parent, valores, comando):
        """Crea un selector segmentado con los colores de la paleta.

        Entrada: contenedor, valores y comando. Salida: CTkSegmentedButton.
        """
        selector = ctk.CTkSegmentedButton(parent, values=valores, command=comando, font=FUENTE_PEQUENA_NEGRITA, height=30,
                                          fg_color=PALETA["panel_2"], selected_color=PALETA["primario"],
                                          selected_hover_color=PALETA["primario_hover"], unselected_color=PALETA["panel_2"],
                                          unselected_hover_color=PALETA["secundario_hover"], text_color=PALETA["texto"])
        selector.set(valores[0])
        selector.pack(fill="x", padx=8, pady=(2, 10))
        return selector

    def construir_visual(self, parent):
        """Crea la línea de tiempo y los tres renders en un área desplazable.

        Entrada: contenedor. Salida: None.
        """
        self.t = 0.0
        self.reproductor = Reproductor(parent, self._al_tiempo, lambda t: f"{round(t * 100)} %", lambda: exportar_lienzo(self.pagina.app, self.lienzo_posicional, "notacion_posicional"))
        self.reproductor.pack(fill="x", padx=6, pady=(4, 6))
        area = AreaDesplazable(parent, PALETA["panel"])
        area.pack(fill="both", expand=True)
        self.lienzo_posicional = LienzoEscena(area.interior, self._escena_posicional, alto=250)
        self.lienzo_posicional.pack(fill="x", padx=4, pady=(0, 8))
        self.lienzo_conversion = LienzoEscena(area.interior, self._escena_conversion, alto=200)
        self.lienzo_conversion.pack(fill="x", padx=4, pady=(0, 8))
        self.lienzo_ieee = LienzoEscena(area.interior, self._escena_ieee, alto=190)
        self.lienzo_ieee.pack(fill="x", padx=4, pady=(0, 8))

    def _vacio(self, ancho, alto):
        """Muestra el mensaje inicial en un lienzo.

        Entrada: tamaño lógico. Salida: lista de primitivas.
        """
        return [graficos.rectangulo(0, 0, ancho, alto, graficos.TEMA["fondo"]),
                graficos.texto(ancho / 2, alto / 2, "Escribe un número y presiona «Convertir y animar».", graficos.TEMA["texto_3"], 13)]

    def _escena_posicional(self, ancho, alto):
        """Construye el render de dígitos y pesos.

        Entrada: tamaño lógico. Salida: (primitivas, alto natural) o primitivas.
        """
        return self._vacio(ancho, alto) if self.informe is None else graficos.escena_posicional(self.informe["descomposicion"], self.t, ancho)

    def _escena_conversion(self, ancho, alto):
        """Construye el render de la conversión a base 2.

        Entrada: tamaño lógico. Salida: (primitivas, alto natural) o primitivas.
        """
        return self._vacio(ancho, alto) if self.informe is None else graficos.escena_conversion(self.informe["binario"], self.t, ancho)

    def _escena_ieee(self, ancho, alto):
        """Construye el render de los bits en la precisión elegida.

        Entrada: tamaño lógico. Salida: (primitivas, alto natural) o primitivas.
        """
        if self.informe is None:
            return self._vacio(ancho, alto)
        return graficos.escena_ieee754(self.informe["ieee32" if self.precision.get() == "32 bits" else "ieee64"], self.t, ancho)

    def _al_tiempo(self, t):
        """Actualiza los tres renders.

        Entrada: t entre 0 y 1. Salida: None.
        """
        self.t = t
        self._redibujar()

    def _redibujar(self):
        """Redibuja los tres renders."""
        for lienzo in (self.lienzo_posicional, self.lienzo_conversion, self.lienzo_ieee):
            lienzo.dibujar()

    def cargar_ejemplo(self, nombre):
        """Carga un ejemplo con su base y lo resuelve.

        Entrada: nombre del ejemplo. Salida: None.
        """
        datos = self.EJEMPLOS[nombre]
        self.base.set(datos["base"])
        self.fijar_campos({"numero": datos["numero"]})
        self.pagina.resolver()

    def calcular(self):
        """Lee el número y su base y calcula el informe.

        Salida: informe; lanza ValueError si el número no es válido en esa base.
        """
        return numericos.informe_posicional(self.valor("numero"), 2 if self.base.get() == "Base 2" else 10)

    def mostrar_visual(self, informe):
        """Anima los tres renders.

        Entrada: informe. Salida: None.
        """
        self.reproductor.pausar()
        self.reproductor.configurar(1.0, 6.0)
        self.reproductor.fijar(0.0)
        self.pagina.after(150, self.reproductor.reproducir)

    def constructores_resultado(self, informe):
        """Prepara el estado, las equivalencias y lo que guarda la computadora.

        Entrada: informe. Salida: lista de constructores.
        """
        ieee64, ieee32 = informe["ieee64"], informe["ieee32"]
        equivalencias = [f"Base 10: {informe['decimal']}", f"Base 2: {informe['binario']['texto']}"]
        if informe["binario"]["periodico"]:
            equivalencias.append("Los paréntesis marcan los bits que se repiten sin fin: el desarrollo en base 2 es periódico.")
        elif informe["binario"]["truncado"]:
            equivalencias.append(f"Se muestran {numericos.LIMITE_BITS_FRACCION} bits fraccionarios; el desarrollo continúa.")
        guardado = []
        for rep in (ieee32, ieee64):
            if rep["tipo"] == "infinito":
                guardado.append(f"{rep['bits']} bits: el número es demasiado grande y se guarda como infinito.")
            else:
                guardado.append(f"{rep['bits']} bits: {numericos.decimal_exacto(rep['almacenado'], 30)} "
                                + ("(exacto)" if rep["exacta"] else f"(error {numericos.decimal_exacto(rep['error_representacion'], 4)})"))
        return [lambda p: tarjeta_estado(p, informe["titulo"], informe["conclusion"], PALETA["exito"], "₂"),
                lambda p: tarjeta_mensajes(p, "Equivalencias", equivalencias, "primario"),
                lambda p: tarjeta_mensajes(p, "Valor que guarda la computadora", guardado, "advertencia")]


class OpcionErrores(OpcionNumerica):
    """Opción 4: errores absoluto, relativo y porcentual, redondeo, truncamiento y errores de la máquina."""

    nombre = "4. Errores numéricos"
    titulo_datos = "Errores numéricos"
    EJEMPLOS = {
        "π ≈ 3.14": {"real": "pi", "aprox": "3.14", "cifras": "4"},
        "π ≈ 22/7": {"real": "pi", "aprox": "22/7", "cifras": "6"},
        "1/3 ≈ 0.333": {"real": "1/3", "aprox": "0.333", "cifras": "3"},
        "√2 ≈ 1.414": {"real": "sqrt(2)", "aprox": "1.414", "cifras": "5"},
        "e ≈ 2.718": {"real": "e", "aprox": "2.718", "cifras": "4"},
    }

    def construir_datos(self, parent):
        """Crea las casillas del valor real, el aproximado y las cifras.

        Entrada: contenedor. Salida: None.
        """
        self.campo("real", "Valor real v (admite pi, 1/3, sqrt(2)…)", "pi")
        self.campo("aprox", "Valor aproximado v*", "3.14")
        self.campo("cifras", "Cifras significativas n (1 a 15)", "4")

    def construir_visual(self, parent):
        """Crea la línea de tiempo y los renders de errores en un área desplazable.

        Entrada: contenedor. Salida: None.
        """
        self.t = 0.0
        self.reproductor = Reproductor(parent, self._al_tiempo, lambda t: f"{round(t * 100)} %", lambda: exportar_lienzo(self.pagina.app, self.lienzo_barras, "errores"))
        self.reproductor.pack(fill="x", padx=6, pady=(4, 6))
        area = AreaDesplazable(parent, PALETA["panel"])
        area.pack(fill="both", expand=True)
        self.lienzo_recta = LienzoEscena(area.interior, self._escena_recta, alto=130)
        self.lienzo_recta.pack(fill="x", padx=4, pady=(0, 8))
        self.lienzo_barras = LienzoEscena(area.interior, self._escena_barras, alto=240)
        self.lienzo_barras.pack(fill="x", padx=4, pady=(0, 8))
        self.lienzo_acumulacion = LienzoEscena(area.interior, self._escena_acumulacion, alto=220)
        self.lienzo_acumulacion.pack(fill="x", padx=4, pady=(0, 8))
        self.lienzo_taylor = LienzoEscena(area.interior, self._escena_taylor, alto=220)
        self.lienzo_taylor.pack(fill="x", padx=4, pady=(0, 8))
        self.lienzo_cancelacion = LienzoEscena(area.interior, self._escena_cancelacion, alto=220)
        self.lienzo_cancelacion.pack(fill="x", padx=4, pady=(0, 8))

    def _vacio(self, ancho, alto):
        """Muestra el mensaje inicial en un lienzo.

        Entrada: tamaño lógico. Salida: lista de primitivas.
        """
        return [graficos.rectangulo(0, 0, ancho, alto, graficos.TEMA["fondo"]),
                graficos.texto(ancho / 2, alto / 2, "Escribe v y v* y presiona «Calcular y animar».", graficos.TEMA["texto_3"], 13)]

    def _escena_recta(self, ancho, alto):
        """Construye el acercamiento en la recta numérica.

        Entrada: tamaño lógico. Salida: primitivas, con su alto natural si hay informe.
        """
        return self._vacio(ancho, alto) if self.informe is None else graficos.escena_recta_numerica(self.informe["real"], self.informe["aproximado"], self.t, ancho)

    def _escena_barras(self, ancho, alto):
        """Construye la comparación de redondeo y truncamiento.

        Entrada: tamaño lógico. Salida: lista de primitivas.
        """
        return self._vacio(ancho, alto) if self.informe is None else graficos.escena_barras_error(self.informe["tabla"], ancho, alto, self.t, self.informe["cifras"])

    def _escena_acumulacion(self, ancho, alto):
        """Construye la gráfica del error acumulado al sumar 0.1.

        Entrada: tamaño lógico. Salida: lista de primitivas.
        """
        if self.informe is None:
            return self._vacio(ancho, alto)
        serie = [{"texto": "|Σ 0.1 − n/10|", "color": graficos.TEMA["rosa"], "puntos": self.informe["acumulacion"]}]
        return graficos.escena_lineas_log(serie, "Error de redondeo acumulado al sumar 0.1 muchas veces", ancho, alto, "cantidad de sumas n", self.t)

    def _escena_taylor(self, ancho, alto):
        """Construye la gráfica del error de truncamiento de la serie de eˣ.

        Entrada: tamaño lógico. Salida: lista de primitivas.
        """
        if self.informe is None:
            return self._vacio(ancho, alto)
        serie = [{"texto": "|e − Σ 1/k!|", "color": graficos.TEMA["violeta"], "puntos": [(f["n"], f["error"]) for f in self.informe["taylor"]]}]
        return graficos.escena_lineas_log(serie, "Error de truncamiento: aproximar e con una suma finita", ancho, alto, "términos sumados", self.t)

    def _escena_cancelacion(self, ancho, alto):
        """Construye la gráfica de la pérdida de cifras al restar números casi iguales.

        Entrada: tamaño lógico. Salida: lista de primitivas.
        """
        if self.informe is None:
            return self._vacio(ancho, alto)
        serie = [{"texto": "√(x+1) − √x", "color": graficos.TEMA["error"], "puntos": [(f["k"], f["error_relativo"]) for f in self.informe["cancelacion"]]}]
        return graficos.escena_lineas_log(serie, "Cancelación: error relativo al restar números casi iguales", ancho, alto, "k en x = 10ᵏ", self.t)

    def _al_tiempo(self, t):
        """Actualiza los renders.

        Entrada: t entre 0 y 1. Salida: None.
        """
        self.t = t
        for lienzo in (self.lienzo_recta, self.lienzo_barras, self.lienzo_acumulacion, self.lienzo_taylor, self.lienzo_cancelacion):
            lienzo.dibujar()

    def calcular(self):
        """Lee los datos y calcula el informe.

        Salida: informe; lanza ValueError si los datos no son válidos.
        """
        try:
            cifras = int(self.valor("cifras"))
        except ValueError:
            raise ValueError("Las cifras significativas deben ser un número entero.") from None
        return numericos.informe_errores(self.valor("real"), self.valor("aprox"), cifras)

    def mostrar_visual(self, informe):
        """Anima los renders.

        Entrada: informe. Salida: None.
        """
        self.reproductor.pausar()
        self.reproductor.configurar(1.0, 4.5)
        self.reproductor.fijar(0.0)
        self.pagina.after(150, self.reproductor.reproducir)

    def constructores_resultado(self, informe):
        """Prepara los errores, el redondeo, el truncamiento y los ejemplos de la aritmética de la máquina.

        Entrada: informe. Salida: lista de constructores.
        """
        errores = informe["errores"]
        decimal = numericos.decimal_exacto
        indicadores = [(decimal(errores["absoluto"], 4), "Error absoluto Ea")]
        if errores["relativo"] is not None:
            indicadores += [(decimal(errores["relativo"], 4), "Error relativo Er"), (decimal(errores["porcentual"], 3) + " %", "Error porcentual E%")]
        filas = [[str(f["n"]), decimal(f["redondeado"], 14), decimal(f["error_redondeo"], 3), decimal(f["truncado"], 14), decimal(f["error_truncamiento"], 3)]
                 for f in informe["tabla"]]
        demostraciones = [f"{d['titulo']}: {d['expresion']} da {numericos.formatear_real(d['calculado'], 17)}, pero lo exacto es {decimal(d['exacto'], 17)}. {d['explicacion']}"
                          for d in informe["demostraciones"]]
        n = informe["cifras"]
        return [lambda p: tarjeta_estado(p, informe["titulo"], informe["conclusion"], PALETA["exito"], "ε"),
                lambda p: fila_indicadores(p, indicadores),
                lambda p: tarjeta_mensajes(p, f"Con {n} cifras significativas", [
                    f"Redondeado: {decimal(informe['redondeado'], 20)}", f"Truncado: {decimal(informe['truncado'], 20)}"], "primario"),
                lambda p: tarjeta_lienzo(p, "Redondeo y truncamiento", "Valor y error para cada cantidad de cifras significativas.",
                                         lambda ancho, _alto: (graficos.escena_tabla(["n", "redondeado", "error", "truncado", "error"], filas, ancho, [0.4, 1.6, 1, 1.6, 1]),
                                                               graficos.alto_tabla(len(filas), con_titulo=False))),
                lambda p: tarjeta_mensajes(p, "Errores de la aritmética de la computadora", demostraciones, "advertencia"),
                lambda p: tarjeta_mensajes(p, "Épsilon de la máquina", [
                    f"ε = {numericos.formatear_real(informe['epsilon'], 16)} = 2⁻⁵²: el menor ε con 1 + ε > 1 en doble precisión.",
                    f"Se obtuvo dividiendo entre 2 durante {len(informe['pasos_epsilon']) - 1} pasos."], "primario")]


class PaginaNumericos(PaginaBase):
    """Página «Métodos numéricos»: bisección, graficador, notación posicional y errores, con animaciones."""

    titulo = "Métodos Numéricos"
    subtitulo = "Bisección, graficador, notación posicional en base 10 y base 2, y errores numéricos"
    OPCIONES = (OpcionBiseccion, OpcionGraficador, OpcionPosicional, OpcionErrores)
    TEXTO_BOTON = {"1. Bisección": "Calcular y animar", "2. Graficador": "Graficar", "3. Notación posicional": "Convertir y animar",
                   "4. Errores numéricos": "Calcular y animar"}

    def __init__(self, parent, app):
        """Crea el selector de opciones, los datos y las cuatro pestañas.

        Entrada: contenedor y aplicación. Salida: None.
        """
        super().__init__(parent, app)
        self.grid_rowconfigure(2, weight=1)
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 12))
        nombres = [clase.nombre for clase in self.OPCIONES]
        self.selector = ctk.CTkSegmentedButton(barra, values=nombres, command=self.cambiar_opcion, font=FUENTE_NEGRITA, height=38,
                                               fg_color=PALETA["panel_2"], selected_color=PALETA["primario"], selected_hover_color=PALETA["primario_hover"],
                                               unselected_color=PALETA["panel_2"], unselected_hover_color=PALETA["secundario_hover"], text_color=PALETA["texto"])
        self.selector.pack(side="left")
        boton_secundario(barra, "0. Ver Teoremas Clave del Módulo", self.mostrar_teoremas, width=250, height=38).pack(side="right")

        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))
        contenido.grid_columnconfigure(0, weight=0, minsize=290)
        contenido.grid_columnconfigure(1, weight=1)
        contenido.grid_rowconfigure(0, weight=1)
        self.tarjeta_datos = crear_tarjeta(contenido)
        self.tarjeta_datos.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.titulo_opcion = etiqueta(self.tarjeta_datos, "", FUENTE_SECCION, "texto", ajustar=30)
        self.titulo_opcion.pack(anchor="w", padx=18, pady=(14, 4))
        self.datos = AreaDesplazable(self.tarjeta_datos, PALETA["panel"])
        self.datos.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        self.aviso_datos = etiqueta(self.tarjeta_datos, "Los datos cambiaron: vuelve a calcular.", FUENTE_PEQUENA, "advertencia")
        self.boton_resolver = boton_primario(self.tarjeta_datos, "Calcular", self.resolver)
        self.boton_resolver.pack(fill="x", padx=16, pady=(4, 16))

        self.pestanas = ctk.CTkTabview(contenido, fg_color=PALETA["panel"], corner_radius=14, border_width=1, border_color=PALETA["borde"],
                                       segmented_button_fg_color=PALETA["panel_2"], segmented_button_selected_color=PALETA["primario"],
                                       segmented_button_unselected_color=PALETA["panel_2"], text_color=PALETA["texto"])
        self.pestanas.grid(row=0, column=1, sticky="nsew")
        self.pestana_animacion = self.pestanas.add("Animación")
        resultado, procedimiento, verificacion = self.pestanas.add("Resultado"), self.pestanas.add("Procedimiento"), self.pestanas.add("Verificación")
        self.area_resultado = AreaDesplazable(resultado, PALETA["panel"])
        self.area_resultado.pack(fill="both", expand=True)
        self.panel_pasos = PanelPasos(procedimiento, PALETA["panel"], "Aquí se explicará cada paso del procedimiento.", constructor=tarjeta_etapa)
        self.panel_pasos.pack(fill="both", expand=True)
        self.area_verificacion = AreaDesplazable(verificacion, PALETA["panel"])
        self.area_verificacion.pack(fill="both", expand=True)

        self.opciones = {}
        self.opcion = None
        self.cambiar_opcion(nombres[0])

    def cambiar_opcion(self, nombre):
        """Muestra los datos y la animación de una opción, y sus últimos resultados.

        Entrada: nombre de la opción. Salida: None.
        """
        if self.opcion is not None:
            self.opcion.marco_datos.pack_forget()
            self.opcion.marco_visual.pack_forget()
        if nombre not in self.opciones:
            clase = next(c for c in self.OPCIONES if c.nombre == nombre)
            self.opciones[nombre] = clase(self)
        self.opcion = self.opciones[nombre]
        self.selector.set(nombre)
        self.titulo_opcion.configure(text=self.opcion.titulo_datos)
        self.boton_resolver.configure(text=self.TEXTO_BOTON[nombre])
        self.opcion.marco_datos.pack(fill="x", pady=(4, 0))
        self.opcion.marco_visual.pack(fill="both", expand=True)
        self.aviso_datos.pack_forget()
        self.datos.al_inicio()
        if self.opcion.informe is not None:
            self._llenar_pestanas(self.opcion.informe)
        else:
            self._vaciar_pestanas()
        self.pestanas.set("Animación")

    def _vaciar_pestanas(self):
        """Muestra los mensajes iniciales en las pestañas de texto."""
        texto = self.opcion.texto_vacio()
        self.area_resultado.llenar([lambda p: placeholder(p, "∿", texto)])
        self.panel_pasos.mostrar_placeholder("Aquí se explicará cada paso del procedimiento.")
        self.area_verificacion.llenar([lambda p: placeholder(p, "✓", "Aquí se comprobará el resultado de forma independiente.")])

    def _llenar_pestanas(self, informe):
        """Llena Resultado, Procedimiento y Verificación con un informe.

        Entrada: informe. Salida: None.
        """
        self.area_resultado.llenar(self.opcion.constructores_resultado(informe), retardo=45)
        self.panel_pasos.mostrar_pasos(informe["procedimiento"])
        self.area_verificacion.llenar(constructores_chequeo(informe["verificacion"]), retardo=45)

    def datos_cambiaron(self, _evento=None):
        """Avisa que el resultado en pantalla ya no corresponde a los datos escritos."""
        if self.opcion is not None and self.opcion.informe is not None:
            self.aviso_datos.pack(anchor="w", padx=18, before=self.boton_resolver)

    def resolver(self):
        """Calcula la opción activa, llena las pestañas y reproduce la animación; un error se explica sin cerrar."""
        opcion = self.opcion
        try:
            informe = opcion.calcular()
        except (ValueError, ArithmeticError) as error:
            mensaje = str(error)
            self.app.notificar(mensaje, "error")
            self.area_resultado.llenar([lambda p: tarjeta_mensajes(p, "Revisa los datos", [mensaje], "error")])
            self.panel_pasos.mostrar_placeholder("Corrige los datos para ver el procedimiento.")
            self.area_verificacion.llenar([lambda p: placeholder(p, "✓", "No hay resultado que verificar.")])
            self.pestanas.set("Resultado")
            return
        opcion.informe = informe
        self.aviso_datos.pack_forget()
        self._llenar_pestanas(informe)
        self.pestanas.set("Animación")
        opcion.mostrar_visual(informe)
        if not informe["definido"]:
            self.app.notificar(informe["conclusion"], "aviso")
        elif informe["verificacion"]["correcto"]:
            self.app.notificar(f"{informe['titulo']} · verificación superada ✓", "exito")
        else:
            self.app.notificar(informe["conclusion"], "error")

    def mostrar_teoremas(self):
        """Muestra el logotipo y los teoremas clave del módulo en la pestaña Resultado."""
        self.area_resultado.llenar(
            [lambda p: etiqueta(p, LOGO_NUMERICOS.strip("\n"), (FAMILIA_MONO, 11), "primario", justify="left").pack(anchor="w", padx=4, pady=(0, 8)),
             lambda p: tarjeta_estado(p, "0. Ver Teoremas Clave del Módulo", "Métodos numéricos: bisección, gráficas, notación posicional y errores.",
                                      PALETA["primario"], "0")]
            + [lambda p, n=n, t=t, d=d: tarjeta_numerada(p, n, t, d) for n, (t, d) in enumerate(TEOREMAS_NUMERICOS, 1)], retardo=40)
        self.pestanas.set("Resultado")


class PaginaRenders(PaginaBase):
    """Página «Renders y animaciones»: transformaciones lineales, sistemas y combinaciones en 2D y 3D."""

    titulo = "Renders y animaciones"
    subtitulo = "Mira cómo una matriz deforma el espacio, cómo se cruzan las ecuaciones y cómo se combinan los vectores"
    MAXIMO_FILAS = 5
    MAXIMO_VECTORES = 4
    MODOS = {
        "Transformación del plano (2×2)": {"tipo": "transformacion", "n": 2, "ejemplo": [[2, 1], [1, 1]]},
        "Transformación del espacio (3×3)": {"tipo": "transformacion", "n": 3, "ejemplo": [[1, 1, 0], [0, 2, 0], ["1/2", 0, 1]]},
        "Sistema de 2 incógnitas (rectas)": {"tipo": "sistema", "n": 2, "ejemplo": [[1, 1, 3], [1, -1, 1]]},
        "Sistema de 3 incógnitas (planos)": {"tipo": "sistema", "n": 3, "ejemplo": [[1, 1, 1, 6], [2, -1, 1, 3], [1, 2, -1, 2]]},
        "Combinación lineal en R²": {"tipo": "combinacion", "n": 2, "ejemplo": [[1, 1, 4], [0, 2, 2]]},
        "Combinación lineal en R³": {"tipo": "combinacion", "n": 3, "ejemplo": [[1, 0, 1, 3], [0, 1, 1, 3], [1, 1, 0, 2]]},
    }

    def __init__(self, parent, app):
        """Crea los datos, el lienzo, la línea de tiempo y la explicación.

        Entrada: contenedor y aplicación. Salida: None.
        """
        super().__init__(parent, app)
        self.grid_rowconfigure(1, weight=1)
        self.t, self.giro, self.inclinacion = 0.0, 0.7, 0.45
        self.escena_actual, self._arrastre, self._tarea_giro = None, None, None
        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        contenido.grid_columnconfigure(0, weight=0, minsize=410)
        contenido.grid_columnconfigure(1, weight=1)
        contenido.grid_rowconfigure(0, weight=1)

        tarjeta = crear_tarjeta(contenido, "Datos")
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        area = AreaDesplazable(tarjeta, PALETA["panel"])
        area.pack(fill="both", expand=True, padx=8, pady=4)
        self.modo = ctk.CTkOptionMenu(area.interior, values=list(self.MODOS), command=self.cambiar_modo, height=34, dynamic_resizing=False,
                                      fg_color=PALETA["secundario"], button_color=PALETA["secundario_hover"],
                                      button_hover_color=PALETA["primario_hover"], text_color=PALETA["texto"])
        self.modo.pack(fill="x", padx=8, pady=(4, 8))
        self.fila_contadores = ctk.CTkFrame(area.interior, fg_color="transparent", width=1, height=1)
        self.fila_contadores.pack(anchor="w", padx=8)
        self.contador_filas = Contador(self.fila_contadores, "ecuaciones", 2, 1, self.MAXIMO_FILAS, lambda _v: self._reconstruir(), en_linea=True)
        self.contador_vectores = Contador(self.fila_contadores, "vectores", 2, 1, self.MAXIMO_VECTORES, lambda _v: self._reconstruir(), en_linea=True)
        self.matriz = MatrizEntrada(area.interior)
        self.matriz.pack(anchor="w", padx=8, pady=(6, 8))
        self.boton = boton_primario(tarjeta, "Renderizar y animar", self.resolver)
        self.boton.pack(fill="x", padx=16, pady=(4, 16))

        derecha = crear_tarjeta(contenido)
        derecha.grid(row=0, column=1, sticky="nsew")
        self.reproductor = Reproductor(derecha, self._al_tiempo, lambda t: f"{round(t * 100)} %", lambda: exportar_lienzo(self.app, self.lienzo, "render"))
        self.reproductor.pack(fill="x", padx=10, pady=(10, 6))
        self.reproductor.configurar(1.0, 4.0)
        self.girar = ctk.BooleanVar(value=True)
        self.interruptor_giro = ctk.CTkSwitch(self.reproductor.extras, text="Girar", variable=self.girar, command=self._iniciar_giro, font=FUENTE_PEQUENA,
                                              text_color=PALETA["texto"], progress_color=PALETA["primario"], width=44)
        self.lienzo = LienzoEscena(derecha, self._escena, alto=430)
        self.lienzo.pack(fill="both", expand=True, padx=10)
        self.lienzo.bind("<ButtonPress-1>", self._presionar)
        self.lienzo.bind("<B1-Motion>", self._arrastrar)
        self.lienzo.bind("<ButtonRelease-1>", self._soltar)
        self.explicacion = etiqueta(derecha, "", FUENTE_NORMAL, "texto_2", ajustar=44)
        self.explicacion.pack(anchor="w", padx=14, pady=(8, 12))
        self.cambiar_modo(next(iter(self.MODOS)))

    def _es_3d(self):
        """Indica si la escena actual se dibuja en tres dimensiones.

        Salida: True o False.
        """
        return self.MODOS[self.modo.get()]["n"] == 3

    def cambiar_modo(self, nombre):
        """Prepara la rejilla del modo con su ejemplo.

        Entrada: nombre del modo. Salida: None.
        """
        datos = self.MODOS[nombre]
        self.modo.set(nombre)
        self.contador_filas.set(len(datos["ejemplo"]), False)
        self.contador_vectores.set(len(datos["ejemplo"][0]) - 1 if datos["tipo"] == "combinacion" else 2, False)
        self._reconstruir(datos["ejemplo"])
        self.escena_actual = None
        self.resolver()

    def _reconstruir(self, valores=None):
        """Ajusta la rejilla al modo y al tamaño elegido.

        Entrada: valores opcionales. Salida: None.
        """
        datos = self.MODOS[self.modo.get()]
        n, tipo = datos["n"], datos["tipo"]
        self.contador_filas.pack_forget()
        self.contador_vectores.pack_forget()
        if tipo == "transformacion":
            self.matriz.configurar(n, n, [f"col {j + 1}" for j in range(n)], [f"F{i + 1}" for i in range(n)], None, valores)
        elif tipo == "sistema":
            self.contador_filas.pack(side="left")
            filas = self.contador_filas.get()
            self.matriz.configurar(filas, n + 1, [f"x{j + 1}" for j in range(n)] + ["b"], [f"F{i + 1}" for i in range(filas)], n, valores)
        else:
            self.contador_vectores.pack(side="left")
            vectores = self.contador_vectores.get()
            self.matriz.configurar(n, vectores + 1, [f"v{j + 1}" for j in range(vectores)] + ["w"], [f"F{i + 1}" for i in range(n)], vectores, valores)

    def cargar_transformacion(self, A):
        """Carga una matriz 2×2 o 3×3 desde otra sección y la anima.

        Entrada: matriz A. Salida: None.
        """
        self._cargar(next(m for m, d in self.MODOS.items() if d["tipo"] == "transformacion" and d["n"] == len(A)), A)

    def cargar_sistema(self, A, b):
        """Carga un sistema de 2 o 3 incógnitas desde otra sección y lo anima.

        Entrada: A y b. Salida: None.
        """
        self.contador_filas.set(len(A), False)
        self._cargar(next(m for m, d in self.MODOS.items() if d["tipo"] == "sistema" and d["n"] == len(A[0])),
                     [fila + [bi] for fila, bi in zip(A, b)])

    def cargar_combinacion(self, vectores, w):
        """Carga vectores de R² o R³ desde otra sección y anima la combinación.

        Entrada: vectores (lista de columnas) y w. Salida: None.
        """
        self.contador_vectores.set(len(vectores), False)
        filas = [[v[i] for v in vectores] + [w[i]] for i in range(len(w))]
        self._cargar(next(m for m, d in self.MODOS.items() if d["tipo"] == "combinacion" and d["n"] == len(w)), filas)

    def _cargar(self, modo, valores):
        """Selecciona un modo, escribe los valores y resuelve.

        Entrada: modo y valores. Salida: None.
        """
        self.modo.set(modo)
        self._reconstruir(valores)
        self.resolver()

    def resolver(self):
        """Lee los datos, prepara la escena y su explicación y reproduce la animación."""
        datos = self.MODOS[self.modo.get()]
        try:
            matriz = self.matriz.valores()
        except ValueError as error:
            self.app.notificar(str(error), "error")
            return
        if datos["tipo"] == "transformacion":
            self.escena_actual, texto = self._preparar_transformacion(matriz)
        elif datos["tipo"] == "sistema":
            self.escena_actual, texto = self._preparar_sistema(matriz, datos["n"])
        else:
            self.escena_actual, texto = self._preparar_combinacion(matriz, datos["n"])
        self.explicacion.configure(text=texto)
        if self._es_3d():
            self.interruptor_giro.pack(side="left")
            self._iniciar_giro()
        else:
            self.interruptor_giro.pack_forget()
        self.reproductor.reproducir()

    def _preparar_transformacion(self, A):
        """Prepara el render de una transformación lineal y explica qué significa su determinante.

        Entrada: matriz A. Salida: (generador de la escena, explicación).
        """
        n = len(A)
        det = calcular_determinante(A)["determinante"]
        medida = "las áreas" if n == 2 else "los volúmenes"
        figura = "el plano" if n == 2 else "el espacio"
        texto = (f"Las columnas de A son las imágenes de la base canónica. det(A) = {formatear_numero(det)}: A multiplica {medida} por "
                 f"{formatear_numero(abs(det))}" + ("; un signo negativo indica que invierte la orientación." if det < 0 else "."))
        if det == 0:
            texto = f"det(A) = 0: A aplasta {figura} en una dimensión menor y por eso no tiene inversa."
        if n == 2:
            return (lambda ancho, alto: graficos.escena_transformacion_2d(A, self.t, ancho, alto)), texto
        return (lambda ancho, alto: graficos.escena_transformacion_3d(A, self.t, self.giro, self.inclinacion, ancho, alto)), texto

    def _preparar_sistema(self, matriz, n):
        """Resuelve el sistema con el núcleo exacto y prepara el render de rectas o planos.

        Entrada: matriz aumentada y cantidad de incógnitas. Salida: (generador de la escena, explicación).
        """
        A, b = [fila[:-1] for fila in matriz], [fila[-1] for fila in matriz]
        r = resolver_sistema(A, b)
        punto = r["solucion"] if r["solucion"] is not None else r["solucion_particular"]
        figura = "una recta" if n == 2 else "un plano"
        if r["solucion"] is not None:
            texto = f"Cada ecuación es {figura}. {r['clasificacion']}: se cruzan en x = ({', '.join(formatear_numero(v) for v in punto)})."
        elif punto is not None:
            texto = f"Cada ecuación es {figura}. {r['clasificacion']}: comparten infinitos puntos; se marca uno de ellos."
        else:
            texto = f"Cada ecuación es {figura}. {r['clasificacion']}: no existe un punto común a todas las ecuaciones."
        if n == 2:
            return (lambda ancho, alto: graficos.escena_sistema_2d(A, b, punto, self.t, ancho, alto)), texto
        return (lambda ancho, alto: graficos.escena_sistema_3d(A, b, punto, self.t, self.giro, self.inclinacion, ancho, alto)), texto

    def _preparar_combinacion(self, matriz, n):
        """Resuelve los coeficientes con el núcleo exacto y prepara el render de la combinación.

        Entrada: matriz [v₁ … vₖ | w] y dimensión. Salida: (generador de la escena, explicación).
        """
        A, w = [fila[:-1] for fila in matriz], [fila[-1] for fila in matriz]
        vectores = columnas_de(A)
        r = resolver_sistema(A, w, obtener_nombres_variables(len(vectores), "c"))
        coeficientes = r["solucion"] if r["solucion"] is not None else r["solucion_particular"]
        if coeficientes is None:
            texto = "w no pertenece al espacio generado por estos vectores: el sistema de coeficientes es inconsistente."
        else:
            simbolos = [f"v{j + 1}" for j in range(len(vectores))]
            texto = f"w = {formatear_combinacion_lineal(coeficientes, simbolos)}: cada flecha de color es un coeficiente por su vector y se coloca a continuación de la anterior."
        return (lambda ancho, alto: graficos.escena_combinacion(coeficientes, vectores, w, self.t, self.giro, self.inclinacion, ancho, alto)), texto

    def _escena(self, ancho, alto):
        """Construye el cuadro actual.

        Entrada: tamaño lógico. Salida: lista de primitivas.
        """
        if self.escena_actual is None:
            return [graficos.rectangulo(0, 0, ancho, alto, graficos.TEMA["fondo"])]
        return self.escena_actual(ancho, alto)

    def _al_tiempo(self, t):
        """Redibuja el cuadro del instante t.

        Entrada: t entre 0 y 1. Salida: None.
        """
        self.t = t
        self.lienzo.dibujar()

    def _iniciar_giro(self):
        """Inicia el giro automático de la cámara si está activado."""
        if self._tarea_giro is None and self.girar.get() and self._es_3d():
            self._tarea_giro = self.after(33, self._tic_giro)

    def _tic_giro(self):
        """Gira la cámara un poco; se detiene si el lienzo no está visible o el modo no es 3D."""
        self._tarea_giro = None
        if not (self.girar.get() and self._es_3d() and self.lienzo.winfo_viewable()):
            return
        if self._arrastre is None:
            self.giro += 0.012
            self.lienzo.dibujar()
        self._tarea_giro = self.after(33, self._tic_giro)

    def al_mostrar(self):
        """Anima el encabezado y reanuda el giro y la animación al volver a la página."""
        super().al_mostrar()
        self._iniciar_giro()
        self.after(150, self._reanudar)

    def _reanudar(self):
        """Continúa la animación que se pausó porque la página aún no estaba visible."""
        if self.reproductor._tarea is None and self.reproductor.t < self.reproductor.maximo:
            self.reproductor.reproducir(desde_inicio=False)

    def _presionar(self, evento):
        """Empieza a girar la cámara con el mouse.

        Entrada: evento del mouse. Salida: None.
        """
        self._arrastre = (evento.x, evento.y)

    def _arrastrar(self, evento):
        """Gira la cámara con el arrastre.

        Entrada: evento del mouse. Salida: None.
        """
        if self._arrastre is None or not self._es_3d():
            return
        self.giro += (evento.x - self._arrastre[0]) * 0.01
        self.inclinacion = max(-1.4, min(1.4, self.inclinacion + (evento.y - self._arrastre[1]) * 0.01))
        self._arrastre = (evento.x, evento.y)
        self.lienzo.dibujar()

    def _soltar(self, _evento):
        """Termina el giro con el mouse."""
        self._arrastre = None


class AplicacionAlgebraLineal(_Ventana):
    """Ventana principal de la Calculadora de Álgebra Lineal, hecha con CustomTkinter."""

    SECCIONES = [
        ("teoremas", "0", "Teoremas clave", PaginaTeoremas),
        ("calculadora", "▦", "Calculadora", PaginaCalculadora),
        ("vectorial", "Σ", "Combinaciones lineales", PaginaCombinaciones),
        ("axb", "≡", "Ecuación Ax = b", PaginaAxb),
        ("propiedades_ax", "⇄", "Propiedades de Ax", PaginaPropiedades),
        ("matrices", "⊞", "Operaciones matriciales", PaginaMatrices),
        ("determinantes", "Δ", "Determinantes e inversas", PaginaDeterminantes),
        ("lu", "◩", "Factorización LU y Ax = b", PaginaLU),
        ("independencia", "⊥", "Independencia lineal", PaginaIndependencia),
        ("numericos", "∿", "Métodos numéricos", PaginaNumericos),
        ("renders", "◈", "Renders y animaciones", PaginaRenders),
        ("metodo", "☰", "Método de eliminación", PaginaMetodo),
        ("ayuda", "?", "Ayuda", PaginaAyuda),
    ]

    def __init__(self):
        """Crea la ventana, el menú lateral, el contenedor de páginas y los atajos; abre la Calculadora.

        El icono se aplica con retraso porque CustomTkinter coloca el suyo poco después de iniciar en Windows.
        """
        super().__init__()
        _FUENTES_MEDIDA.clear()
        self.title("Calculadora de Álgebra Lineal - Grupo 3 - UAM")
        self._centrar(1280, 820)
        self.minsize(min(1160, self.winfo_screenwidth() - 60),
                     min(680, self.winfo_screenheight() - 80))
        self.configure(fg_color=PALETA["fondo"])

        self.logo_grande = cargar_logo((52, 52))
        self.logo_pequeno = cargar_logo((30, 30))
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
        """Centra la ventana con el tamaño indicado, limitado al de la pantalla.

        Entrada: ancho y alto. Salida: None.
        """
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
        """Crea el menú lateral con el logo, las secciones y el pie."""
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
        """Crea el contenedor de páginas; cada página se crea al visitarla y solo la activa queda en pantalla."""
        self.contenedor = ctk.CTkFrame(self, fg_color=PALETA["fondo"], corner_radius=0)
        self.contenedor.grid(row=0, column=1, sticky="nsew")
        self.contenedor.grid_columnconfigure(0, weight=1)
        self.contenedor.grid_rowconfigure(0, weight=1)

        self.paginas = {}
        self._clases_pagina = {clave: clase for clave, _icono, _texto, clase in self.SECCIONES}

    def obtener_pagina(self, clave):
        """Obtiene la página de una sección; la crea la primera vez que se visita.

        Entrada: clave de la sección. Salida: la página.
        """
        if clave not in self.paginas:
            self.paginas[clave] = self._clases_pagina[clave](self.contenedor, self)
        return self.paginas[clave]

    def ir_a(self, clave):
        """Muestra una sección para cargarle datos encadenados desde otra.

        Entrada: clave de la sección. Salida: la página mostrada.
        """
        self.cambiar_pagina(clave)
        return self.paginas[clave]

    def cambiar_pagina(self, pagina):
        """Muestra la sección indicada y marca su elemento en el menú.

        Entrada: clave de la sección. Salida: None.
        """
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
        """Desliza la barrita del menú hasta la sección activa."""
        item = self.nav_botones[self.pagina_actual]
        self.update_idletasks()
        escala = escala_de(self.nav)
        destino = (item.winfo_y() + (item.winfo_height() - 22 * escala) / 2) / escala
        origen = self._indicador_y if self._indicador_y is not None else destino
        self._indicador_y = destino
        self.indicador.lift()

        def mover(t):
            """Coloca el indicador en la fracción t del recorrido.

            Entrada: t entre 0 y 1. Salida: None.
            """
            self.indicador.place(x=0, y=origen + (destino - origen) * t)

        animar(self.indicador, 280, mover)

    def _configurar_atajos(self):
        """Enlaza Ctrl/⌘ + Enter con «resolver» de la página activa."""
        secuencias = ["<Control-Return>", "<Control-KP_Enter>"]
        if sys.platform == "darwin":
            secuencias.append("<Command-Return>")
        for secuencia in secuencias:
            self.bind_all(secuencia, self._atajo_resolver, add="+")

    def _atajo_resolver(self, _evento=None):
        """Ejecuta «resolver» en la página activa.

        Entrada: evento de teclado. Salida: 'break' para que Tk no procese más la tecla.
        """
        resolver = getattr(self.paginas.get(self.pagina_actual), "resolver", None)
        if resolver is not None:
            resolver()
        return "break"

    def notificar(self, texto, tipo="info"):
        """Muestra un aviso flotante.

        Entrada: texto y tipo (info, exito, aviso o error). Salida: None.
        """
        self.notificador.mostrar(texto, tipo)

    def copiar(self, texto):
        """Copia el texto al portapapeles y lo notifica.

        Entrada: texto. Salida: None.
        """
        self.clipboard_clear()
        self.clipboard_append(texto)
        self.notificar("Resultado copiado al portapapeles.", "exito")




def _pedir_entero(mensaje, minimo=1, entrada=input):
    """Pide un entero mayor o igual que el mínimo y repite la pregunta ante un error.

    Entrada: mensaje, mínimo y función de entrada. Salida: el entero leído.
    """
    while True:
        try:
            valor = int(entrada(mensaje).strip())
            if valor >= minimo:
                return valor
        except ValueError:
            pass
        print(f"  Escribe un número entero mayor o igual que {minimo}.")


def independencia_consola(entrada=input):
    """Lee p vectores de Rⁿ, reduce [A | 0] y muestra la forma escalonada, los pivotes y el veredicto L.I./L.D.

    Entrada: función de entrada. Salida: diccionario de analizar_independencia.
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
    """Abre la GUI; con --teoremas muestra los teoremas y con --consola el análisis de independencia."""
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

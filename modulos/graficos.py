"""Motor de renders y animaciones: construye escenas vectoriales sin depender de la interfaz.

Propósito: traducir gráficas, procedimientos numéricos y transformaciones lineales a listas de primitivas
(líneas, polígonos, círculos y textos) que la GUI dibuja en un Canvas y exporta a PNG con el mismo resultado.
Unidad: Álgebra Lineal (MTM0120), Programa 7: módulo de Métodos Numéricos y visualización de la Calculadora.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
Notas: funciones puras (sin input() ni print()) y sin NumPy ni math; en 3D, las superficies que se cruzan se
ordenan con un árbol BSP para dibujarlas de atrás hacia adelante.
"""
from fractions import Fraction

from .modulo_matrices import formatear_ecuacion_original
from .modulo_numericos import (arcotangente, coseno, decimal_exacto, formatear_real, logaritmo_10,
                               muestrear_funcion, rango_automatico, seno)

TEMA = {
    "fondo": "#0F2F31", "panel": "#153B3E", "rejilla": "#1A4347", "rejilla_fuerte": "#2A5F62", "eje": "#7FB8B7",
    "texto": "#F4FBFB", "texto_2": "#C8E7E6", "texto_3": "#7FB8B7", "primario": "#29D3D9", "exito": "#2ED573",
    "advertencia": "#F5A623", "error": "#EF4B4B", "rosa": "#FF6B9D", "violeta": "#A78BFA",
}
SERIES = (TEMA["primario"], TEMA["advertencia"], TEMA["rosa"], TEMA["violeta"], TEMA["exito"])


def mezclar_colores(color_a, color_b, t):
    """Interpola dos colores: t = 0 da el primero y t = 1 el segundo.

    Entrada: colores '#RRGGBB' y t entre 0 y 1. Salida: color intermedio '#RRGGBB'.
    """
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def suavizar(t):
    """Aplica la curva suave 3t² − 2t³, que arranca y termina sin brusquedad.

    Entrada: t. Salida: valor entre 0 y 1.
    """
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def linea(puntos, color, ancho=1.5, punteada=False):
    """Describe una línea poligonal.

    Entrada: puntos (x, y) en píxeles lógicos, color, ancho y punteada (bool). Salida: primitiva.
    """
    return {"tipo": "linea", "puntos": list(puntos), "color": color, "ancho": ancho, "punteada": punteada}


def poligono(puntos, relleno, borde=None, ancho=1.0):
    """Describe un polígono relleno.

    Entrada: puntos, relleno, borde opcional y ancho del borde. Salida: primitiva.
    """
    return {"tipo": "poligono", "puntos": list(puntos), "relleno": relleno, "borde": borde, "ancho": ancho}


def circulo(x, y, radio, relleno, borde=None, ancho=1.0):
    """Describe un círculo.

    Entrada: centro, radio, relleno, borde opcional y ancho del borde. Salida: primitiva.
    """
    return {"tipo": "circulo", "x": x, "y": y, "radio": radio, "relleno": relleno, "borde": borde, "ancho": ancho}


def texto(x, y, cadena, color=None, tamano=12, negrita=False, ancla="center", mono=False):
    """Describe un texto.

    Entrada: posición, cadena, color, tamaño, negrita, ancla (como en Tk) y mono (bool). Salida: primitiva.
    """
    return {"tipo": "texto", "x": x, "y": y, "texto": str(cadena), "color": color or TEMA["texto"], "tamano": tamano,
            "negrita": negrita, "ancla": ancla, "mono": mono}


def rectangulo(x1, y1, x2, y2, relleno, borde=None, ancho=1.0):
    """Describe un rectángulo como polígono.

    Entrada: esquinas, relleno, borde opcional y ancho. Salida: primitiva.
    """
    return poligono([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], relleno, borde, ancho)


def flecha(x1, y1, x2, y2, color, ancho=2.5, punta=10.0):
    """Describe una flecha con su punta rellena.

    Entrada: origen, destino, color, ancho y largo de la punta. Salida: lista de primitivas.
    """
    dx, dy = x2 - x1, y2 - y1
    largo = (dx * dx + dy * dy) ** 0.5
    if largo < 1e-6:
        return [circulo(x1, y1, ancho, color)]
    ux, uy = dx / largo, dy / largo
    punta = min(punta, largo * 0.6)
    base_x, base_y = x2 - ux * punta, y2 - uy * punta
    mitad = punta * 0.45
    return [linea([(x1, y1), (base_x, base_y)], color, ancho),
            poligono([(x2, y2), (base_x - uy * mitad, base_y + ux * mitad), (base_x + uy * mitad, base_y - ux * mitad)], color)]


def marcas_eje(minimo, maximo, cantidad=8):
    """Elige marcas «redondas» (múltiplos de 1, 2 o 5 × 10ᵏ) para un eje.

    Entrada: extremos del eje y cantidad aproximada de marcas. Salida: (lista de marcas, paso).
    """
    rango = maximo - minimo
    if rango <= 0:
        return [minimo], 1.0
    bruto = rango / max(1, cantidad)
    potencia = 10.0 ** int(logaritmo_10(bruto) // 1)
    proporcion = bruto / potencia
    paso = (1 if proporcion <= 1 else 2 if proporcion <= 2 else 5 if proporcion <= 5 else 10) * potencia
    inicio = int(minimo / paso // 1)
    marcas = []
    k = inicio
    while k * paso <= maximo + paso * 1e-9:
        if k * paso >= minimo - paso * 1e-9:
            marcas.append(k * paso)
        k += 1
    return marcas, paso


def texto_marca(valor, paso):
    """Escribe el número de una marca sin los decimales que el paso no justifica.

    Entrada: valor y paso del eje. Salida: cadena.
    """
    if abs(valor) < paso * 1e-6:
        return "0"
    # Hacen falta tantas cifras como órdenes de magnitud separan al valor del paso: si no, las marcas se repiten.
    cifras = int(logaritmo_10(abs(valor) / abs(paso)) // 1) + 2
    return formatear_real(valor, max(3, min(15, cifras)))


class Vista:
    """Ventana de coordenadas: traduce (x, y) del plano a píxeles lógicos de la escena y viceversa."""

    def __init__(self, x_min, x_max, y_min, y_max, ancho, alto, margenes=(62, 14, 18, 32)):
        """Guarda la ventana y el área de dibujo.

        Entrada: extremos en x y en y, tamaño de la escena y márgenes (izq, der, arriba, abajo). Salida: None.
        """
        self.x_min, self.x_max, self.y_min, self.y_max = x_min, x_max, y_min, y_max
        self.ancho, self.alto = ancho, alto
        self.izquierda, self.arriba = margenes[0], margenes[2]
        self.derecha, self.abajo = ancho - margenes[1], alto - margenes[3]
        self.margenes = margenes

    def a_pixel(self, x, y):
        """Convierte un punto del plano a píxeles; el eje y se invierte porque la pantalla crece hacia abajo.

        Entrada: x, y. Salida: (px, py).
        """
        px = self.izquierda + (x - self.x_min) / (self.x_max - self.x_min) * (self.derecha - self.izquierda)
        py = self.arriba + (self.y_max - y) / (self.y_max - self.y_min) * (self.abajo - self.arriba)
        return px, py

    def a_plano(self, px, py):
        """Convierte píxeles a un punto del plano.

        Entrada: px, py. Salida: (x, y).
        """
        x = self.x_min + (px - self.izquierda) / (self.derecha - self.izquierda) * (self.x_max - self.x_min)
        y = self.y_max - (py - self.arriba) / (self.abajo - self.arriba) * (self.y_max - self.y_min)
        return x, y

    def acercada(self, factor, px, py):
        """Calcula la vista ampliada manteniendo fijo el punto bajo el cursor.

        Entrada: factor (< 1 acerca) y píxel fijo. Salida: nueva Vista.
        """
        x, y = self.a_plano(px, py)
        return Vista(x + (self.x_min - x) * factor, x + (self.x_max - x) * factor, y + (self.y_min - y) * factor,
                     y + (self.y_max - y) * factor, self.ancho, self.alto, self.margenes)

    def desplazada(self, dx_px, dy_px):
        """Calcula la vista movida una cantidad de píxeles.

        Entrada: desplazamiento en píxeles. Salida: nueva Vista.
        """
        dx = -dx_px / (self.derecha - self.izquierda) * (self.x_max - self.x_min)
        dy = dy_px / (self.abajo - self.arriba) * (self.y_max - self.y_min)
        return Vista(self.x_min + dx, self.x_max + dx, self.y_min + dy, self.y_max + dy, self.ancho, self.alto, self.margenes)

    def redimensionada(self, ancho, alto):
        """Conserva la ventana del plano para un nuevo tamaño de escena.

        Entrada: ancho y alto. Salida: nueva Vista.
        """
        return Vista(self.x_min, self.x_max, self.y_min, self.y_max, ancho, alto, self.margenes)


def recortar_polilinea(puntos, x1, y1, x2, y2):
    """Recorta una polilínea al rectángulo con el algoritmo de Liang-Barsky, segmento por segmento.

    Entrada: puntos y rectángulo. Salida: lista de polilíneas visibles.
    """
    trozos, actual = [], []
    for (ax, ay), (bx, by) in zip(puntos, puntos[1:]):
        dx, dy = bx - ax, by - ay
        t0, t1, visible = 0.0, 1.0, True
        for p, q in ((-dx, ax - x1), (dx, x2 - ax), (-dy, ay - y1), (dy, y2 - ay)):
            if p == 0:
                if q < 0:
                    visible = False
                    break
            else:
                r = q / p
                if p < 0:
                    t0 = max(t0, r)
                else:
                    t1 = min(t1, r)
                if t0 > t1:
                    visible = False
                    break
        if not visible:
            if actual:
                trozos.append(actual)
            actual = []
            continue
        inicio, fin = (ax + t0 * dx, ay + t0 * dy), (ax + t1 * dx, ay + t1 * dy)
        if not actual:
            actual = [inicio]
        elif t0 > 0:
            trozos.append(actual)
            actual = [inicio]
        actual.append(fin)
        if t1 < 1:
            trozos.append(actual)
            actual = []
    if actual:
        trozos.append(actual)
    return trozos


def escena_ejes(vista, formato_y=None, marcas_x=9, marcas_y=7, bandas=()):
    """Dibuja el fondo, las bandas resaltadas, la rejilla, los ejes y las marcas numeradas de una vista.

    Entrada: vista, formato de las marcas de y, cantidad de marcas y bandas (x1, x2, color). Salida: lista de primitivas.
    """
    escena = [rectangulo(0, 0, vista.ancho, vista.alto, TEMA["fondo"]),
              rectangulo(vista.izquierda, vista.arriba, vista.derecha, vista.abajo, mezclar_colores(TEMA["fondo"], "#000000", 0.18))]
    if vista.derecha - vista.izquierda < 40 or vista.abajo - vista.arriba < 30:
        return escena
    for banda in bandas:
        p1, p2 = vista.a_pixel(banda["x1"], 0)[0], vista.a_pixel(banda["x2"], 0)[0]
        p1, p2 = max(vista.izquierda, min(vista.derecha, p1)), max(vista.izquierda, min(vista.derecha, p2))
        escena.append(rectangulo(p1, vista.arriba, max(p2, p1 + 1), vista.abajo, banda["color"]))
    valores_x, paso_x = marcas_eje(vista.x_min, vista.x_max, marcas_x)
    valores_y, paso_y = marcas_eje(vista.y_min, vista.y_max, marcas_y)
    for x in valores_x:
        px, _ = vista.a_pixel(x, 0)
        escena.append(linea([(px, vista.arriba), (px, vista.abajo)], TEMA["rejilla"], 1))
        escena.append(texto(px, vista.abajo + 6, texto_marca(x, paso_x), TEMA["texto_3"], 10, ancla="n"))
    for y in valores_y:
        _, py = vista.a_pixel(0, y)
        escena.append(linea([(vista.izquierda, py), (vista.derecha, py)], TEMA["rejilla"], 1))
        etiqueta = formato_y(y) if formato_y else texto_marca(y, paso_y)
        escena.append(texto(vista.izquierda - 6, py, etiqueta, TEMA["texto_3"], 10, ancla="e"))
    if vista.x_min <= 0 <= vista.x_max:
        px, _ = vista.a_pixel(0, 0)
        escena.append(linea([(px, vista.arriba), (px, vista.abajo)], TEMA["eje"], 1.5))
    if vista.y_min <= 0 <= vista.y_max and formato_y is None:
        _, py = vista.a_pixel(0, 0)
        escena.append(linea([(vista.izquierda, py), (vista.derecha, py)], TEMA["eje"], 1.5))
    escena.append(rectangulo(vista.izquierda, vista.arriba, vista.derecha, vista.abajo, "", TEMA["rejilla_fuerte"], 1))
    return escena


def tramos_a_pixeles(tramos, vista, progreso=1.0):
    """Convierte tramos del plano en polilíneas recortadas, hasta la fracción del eje x indicada.

    Entrada: tramos, vista y progreso (0 a 1). Salida: (polilíneas, último punto visible o None).
    """
    limite = vista.x_min + (vista.x_max - vista.x_min) * progreso
    resultado, ultimo = [], None
    for tramo in tramos:
        # Se limita el valor para que un polo no produzca coordenadas enormes antes de recortar.
        rango = vista.y_max - vista.y_min
        bajo, alto = vista.y_min - 50 * rango, vista.y_max + 50 * rango
        puntos = [vista.a_pixel(x, max(bajo, min(alto, y))) for x, y in tramo if x <= limite]
        if len(puntos) < 2:
            continue
        trozos = recortar_polilinea(puntos, vista.izquierda, vista.arriba, vista.derecha, vista.abajo)
        resultado.extend(trozos)
        if trozos:
            ultimo = trozos[-1][-1]
    return resultado, ultimo


def escena_grafica(vista, curvas, progreso=1.0, marcadores=(), bandas=(), verticales=(), cursor=None, leyenda=True, formato_y=None):
    """Dibuja una gráfica completa: ejes, bandas, curvas, puntos notables, leyenda y cursor.

    Entrada: vista, curvas (tramos, color, texto), progreso de trazado, marcadores, bandas, verticales, cursor,
    leyenda (bool) y formato de y. Salida: lista de primitivas.
    """
    escena = escena_ejes(vista, formato_y, bandas=bandas)
    for curva in curvas:
        trozos, cabeza = tramos_a_pixeles(curva["tramos"], vista, progreso)
        for trozo in trozos:
            escena.append(linea(trozo, mezclar_colores(TEMA["fondo"], curva["color"], 0.25), curva.get("ancho", 2.5) + 3))
            escena.append(linea(trozo, curva["color"], curva.get("ancho", 2.5)))
        if progreso < 1 and cabeza:
            escena.append(circulo(cabeza[0], cabeza[1], 5, TEMA["texto"], curva["color"], 2))
    for vertical in verticales:
        px, _ = vista.a_pixel(vertical["x"], 0)
        if vista.izquierda <= px <= vista.derecha:
            escena.append(linea([(px, vista.arriba), (px, vista.abajo)], vertical["color"], vertical.get("ancho", 1.5), True))
            if vertical.get("etiqueta"):
                escena.append(texto(px, vista.arriba + 26, vertical["etiqueta"], vertical["color"], 13, True, "n"))
    ocupadas = []
    for marcador in marcadores:
        px, py = vista.a_pixel(marcador["x"], marcador["y"])
        if vista.izquierda <= px <= vista.derecha and vista.arriba <= py <= vista.abajo:
            escena.append(circulo(px, py, marcador.get("radio", 5), marcador["color"], TEMA["fondo"], 2))
            if marcador.get("etiqueta"):
                izquierda = px > vista.derecha - 90
                largo = len(marcador["etiqueta"]) * 6.4
                caja = (px - 9 - largo, py - 24, px - 9, py - 9) if izquierda else (px + 9, py - 24, px + 9 + largo, py - 9)
                # Una etiqueta que se encimaría con otra se omite: el cursor sigue mostrando ese valor.
                if all(caja[2] < o[0] or caja[0] > o[2] or caja[3] < o[1] or caja[1] > o[3] for o in ocupadas):
                    ocupadas.append(caja)
                    escena.append(texto(px + (-9 if izquierda else 9), py - 9, marcador["etiqueta"], TEMA["texto"], 11,
                                        ancla="se" if izquierda else "sw"))
    nombradas = [curva for curva in curvas if curva.get("texto")] if leyenda else []
    if nombradas:
        ancho_leyenda = max(len(curva["texto"]) for curva in nombradas) * 7.1 + 50
        escena.append(rectangulo(vista.izquierda + 6, vista.arriba + 4, vista.izquierda + 6 + ancho_leyenda,
                                 vista.arriba + 10 + 19 * len(nombradas), TEMA["panel"], TEMA["rejilla_fuerte"]))
        y = vista.arriba + 16
        for curva in nombradas:
            escena.append(linea([(vista.izquierda + 14, y), (vista.izquierda + 34, y)], curva["color"], 3))
            escena.append(texto(vista.izquierda + 40, y, curva["texto"], TEMA["texto"], 12, True, "w"))
            y += 19
    if cursor is not None:
        escena.extend(_escena_cursor(vista, cursor))
    return escena


def _escena_cursor(vista, cursor):
    """Dibuja la cruz del cursor y la etiqueta con los valores de cada función.

    Entrada: vista y cursor (x, y, filas de (color, texto)). Salida: lista de primitivas.
    """
    px, py = vista.a_pixel(cursor["x"], cursor["y"])
    if not (vista.izquierda <= px <= vista.derecha and vista.arriba <= py <= vista.abajo):
        return []
    escena = [linea([(px, vista.arriba), (px, vista.abajo)], TEMA["eje"], 1, True),
              linea([(vista.izquierda, py), (vista.derecha, py)], TEMA["eje"], 1, True)]
    for fila in cursor["filas"]:
        if fila.get("punto") is not None:
            mx, my = vista.a_pixel(*fila["punto"])
            if vista.arriba <= my <= vista.abajo:
                escena.append(circulo(mx, my, 4.5, fila["color"], TEMA["texto"], 1.5))
    ancho = max(len(f["texto"]) for f in cursor["filas"]) * 7.2 + 18
    alto = 19 * len(cursor["filas"]) + 10
    x1 = px + 14 if px + 14 + ancho < vista.derecha else px - 14 - ancho
    y1 = py + 14 if py + 14 + alto < vista.abajo else py - 14 - alto
    escena.append(rectangulo(x1, y1, x1 + ancho, y1 + alto, TEMA["panel"], TEMA["rejilla_fuerte"]))
    for k, fila in enumerate(cursor["filas"]):
        escena.append(texto(x1 + 9, y1 + 14 + 19 * k, fila["texto"], fila["color"], 12, ancla="w", mono=True))
    return escena


def vista_para_funciones(funciones, x_min, x_max, ancho, alto):
    """Elige el rango vertical que mejor muestra las funciones en el intervalo.

    Entrada: funciones, intervalo y tamaño de la escena. Salida: Vista.
    """
    valores = []
    for funcion in funciones:
        for tramo in muestrear_funcion(funcion, x_min, x_max, 240)["tramos"]:
            valores.extend(y for _, y in tramo)
    y_min, y_max = rango_automatico(valores)
    return Vista(x_min, x_max, y_min, y_max, ancho, alto)


def curvas_en_vista(funciones, vista, colores=SERIES, nombres="fgh"):
    """Muestrea cada función con la resolución y el rango de la vista actual.

    Entrada: funciones, vista, colores y nombres. Salida: lista de curvas para escena_grafica.
    """
    puntos = max(60, min(900, int(vista.derecha - vista.izquierda)))
    umbral = (vista.y_max - vista.y_min) * 0.6
    curvas = []
    for k, funcion in enumerate(funciones):
        curvas.append({"tramos": muestrear_funcion(funcion, vista.x_min, vista.x_max, puntos, umbral)["tramos"],
                       "color": colores[k % len(colores)], "texto": f"{nombres[k % len(nombres)]}(x) = {funcion.texto}"})
    return curvas


def estado_biseccion(informe, t):
    """Calcula el intervalo animado: en cada iteración aparece c y luego el intervalo se reduce a la mitad.

    Entrada: informe de biseccion y t entre 0 y n (cantidad de iteraciones). Salida: diccionario con a, b, c, k y fase.
    """
    iteraciones = informe["iteraciones"]
    if not iteraciones:
        return {"a": informe["a"], "b": informe["b"], "c": informe["raiz"], "k": 0, "fase": 1.0, "final": True, "iteracion": None, "piso": 0.0}
    t = max(0.0, min(float(len(iteraciones)), t))
    k = min(int(t), len(iteraciones) - 1)
    fase = t - k if t < len(iteraciones) else 1.0
    it = iteraciones[k]
    cierre = suavizar((fase - 0.45) / 0.55)
    return {"a": it["a"] + (it["nuevo_a"] - it["a"]) * cierre, "b": it["b"] + (it["nuevo_b"] - it["b"]) * cierre,
            "c": it["c"], "k": k + 1, "fase": fase, "final": t >= len(iteraciones), "iteracion": it,
            "piso": it["cota_error"] if it["mitad"] == "exacta" else 0.0}


def vista_biseccion(informe, estado, ancho, alto, seguir=True):
    """Encuadra la animación; con seguir=True la cámara se acerca al intervalo a medida que se reduce.

    Entrada: informe, estado de estado_biseccion, tamaño de la escena y seguir (bool). Salida: Vista.
    """
    funcion = informe["funcion"]
    a0, b0 = informe["a"], informe["b"]
    if seguir:
        a, b = estado["a"], estado["b"]
    else:
        a, b = a0, b0
    # Con una raíz exacta el intervalo se reduce a un punto: el piso evita una vista de ancho cero.
    margen = max(b - a, estado["piso"], abs(a) * 1e-13, (b0 - a0) * 1e-13) * 0.35
    x_min, x_max = a - margen, b + margen
    valores = [funcion.evaluar(x_min + (x_max - x_min) * i / 60) for i in range(61)]
    valores = [y for y in valores if y is not None] or [-1.0, 1.0]
    y_min, y_max = rango_automatico(valores)
    y_min, y_max = min(y_min, 0.0), max(y_max, 0.0)
    holgura = (y_max - y_min) * 0.12 or 1.0
    return Vista(x_min, x_max, y_min - holgura, y_max + holgura, ancho, alto)


def escena_biseccion(informe, t, ancho, alto, seguir=True):
    """Dibuja un cuadro de la animación: curva, intervalo [a, b], punto medio c y signos de f.

    Entrada: informe de biseccion, t, tamaño de la escena y seguir (bool). Salida: lista de primitivas.
    """
    estado = estado_biseccion(informe, t)
    vista = vista_biseccion(informe, estado, ancho, alto, seguir)
    funcion = informe["funcion"]
    curva = {"tramos": muestrear_funcion(funcion, vista.x_min, vista.x_max, max(80, min(500, int(ancho))), (vista.y_max - vista.y_min) * 0.6)["tramos"],
             "color": SERIES[0], "texto": f"f(x) = {funcion.texto}"}
    banda = {"x1": estado["a"], "x2": estado["b"], "color": mezclar_colores(TEMA["fondo"], TEMA["primario"], 0.14)}
    verticales = [{"x": estado["a"], "color": TEMA["advertencia"], "etiqueta": "a"},
                  {"x": estado["b"], "color": TEMA["rosa"], "etiqueta": "b"}]
    marcadores = []
    for nombre, x, color in (("f(a)", estado["a"], TEMA["advertencia"]), ("f(b)", estado["b"], TEMA["rosa"])):
        y = funcion.evaluar(x)
        if y is not None:
            marcadores.append({"x": x, "y": y, "color": color, "etiqueta": f"{nombre} {'+' if y > 0 else '−' if y < 0 else '0'}"})
    if estado["fase"] > 0.08 or estado["final"]:
        y_c = funcion.evaluar(estado["c"])
        verticales.append({"x": estado["c"], "color": TEMA["exito"], "etiqueta": "c"})
        if y_c is not None:
            marcadores.append({"x": estado["c"], "y": y_c, "color": TEMA["exito"], "radio": 7,
                               "etiqueta": f"f(c) {'+' if y_c > 0 else '−' if y_c < 0 else '0'}"})
    escena = escena_grafica(vista, [curva], bandas=[banda], verticales=verticales, marcadores=marcadores)
    if estado["iteracion"] is None:
        linea_estado = f"Raíz en un extremo: x = {formatear_real(informe['raiz'])}"
    elif estado["final"]:
        linea_estado = f"Resultado tras {informe['n']} iteraciones: x ≈ {formatear_real(informe['raiz'])}"
    else:
        it = estado["iteracion"]
        texto_mitad = {"izquierda": "la raíz queda en [a, c]: b ← c", "derecha": "la raíz queda en [c, b]: a ← c", "exacta": "f(c) = 0"}[it["mitad"]]
        linea_estado = f"Iteración {it['n']}: c = {formatear_real(it['c'], 8)};  {texto_mitad}"
    escena.append(rectangulo(vista.izquierda + 8, vista.abajo - 32, vista.derecha - 8, vista.abajo - 6, TEMA["panel"], TEMA["rejilla_fuerte"]))
    escena.append(texto(vista.izquierda + 18, vista.abajo - 19, linea_estado, TEMA["texto"], 12, True, "w"))
    return escena


def escena_intervalo_sin_raiz(informe, ancho, alto):
    """Muestra por qué no aplica la bisección: f y los extremos del intervalo, sin cambio de signo.

    Entrada: informe no definido de biseccion y tamaño de la escena. Salida: lista de primitivas.
    """
    funcion, a, b = informe["funcion"], informe["a"], informe["b"]
    margen = (b - a) * 0.15
    vista = vista_para_funciones([funcion], a - margen, b + margen, ancho, alto)
    vista = Vista(vista.x_min, vista.x_max, min(vista.y_min, -abs(vista.y_max) * 0.1), max(vista.y_max, abs(vista.y_min) * 0.1), ancho, alto)
    marcadores = []
    for nombre, x, color in (("f(a)", a, TEMA["advertencia"]), ("f(b)", b, TEMA["rosa"])):
        y = funcion.evaluar(x)
        if y is not None:
            marcadores.append({"x": x, "y": y, "color": color, "radio": 7, "etiqueta": f"{nombre} {'+' if y > 0 else '−' if y < 0 else '0'}"})
    verticales = [{"x": a, "color": TEMA["advertencia"], "etiqueta": "a"}, {"x": b, "color": TEMA["rosa"], "etiqueta": "b"}]
    bandas = []
    if informe.get("sugerencia"):
        bandas.append({"x1": informe["sugerencia"][0], "x2": informe["sugerencia"][1], "color": mezclar_colores(TEMA["fondo"], TEMA["exito"], 0.5)})
    curvas = curvas_en_vista([funcion], vista)
    return escena_grafica(vista, curvas, marcadores=marcadores, verticales=verticales, bandas=bandas)


def escena_lineas_log(series, titulo, ancho, alto, etiqueta_x="", progreso=1.0, marca_x=None):
    """Dibuja series en escala logarítmica en y, útil porque los errores cambian en muchos órdenes de magnitud.

    Entrada: series (texto, color, puntos (x, y)), título, tamaño, etiqueta de x, progreso y marca vertical.
    Salida: lista de primitivas.
    """
    positivos = [y for s in series for _, y in s["puntos"] if y and y > 0]
    if not positivos:
        return [rectangulo(0, 0, ancho, alto, TEMA["fondo"]), texto(ancho / 2, alto / 2, "No hay errores distintos de cero que graficar.", TEMA["texto_3"], 13)]
    bajo, alto_log = logaritmo_10(min(positivos)), logaritmo_10(max(positivos))
    if alto_log - bajo < 1:
        bajo, alto_log = bajo - 0.5, alto_log + 0.5
    xs = [x for s in series for x, _ in s["puntos"]]
    x_min, x_max = min(xs), max(xs)
    if x_min == x_max:
        x_min, x_max = x_min - 1, x_max + 1
    vista = Vista(x_min, x_max, bajo - 0.3, alto_log + 0.3, ancho, alto, (62, 14, 34, 36))
    escena = escena_ejes(vista, formato_y=lambda y: f"10^{round(y)}" if abs(y - round(y)) < 1e-6 else "", marcas_y=6)
    escena.append(texto(vista.izquierda, 16, titulo, TEMA["texto"], 13, True, "w"))
    if etiqueta_x:
        escena.append(texto(vista.derecha, alto - 6, etiqueta_x, TEMA["texto_3"], 10, ancla="se"))
    limite = x_min + (x_max - x_min) * progreso
    for s in series:
        puntos = [vista.a_pixel(x, logaritmo_10(y)) for x, y in s["puntos"] if y and y > 0 and x <= limite]
        if len(puntos) >= 2:
            escena.append(linea(puntos, s["color"], 2.5, s.get("punteada", False)))
        if not s.get("punteada"):
            escena.extend(circulo(px, py, 2.8, s["color"]) for px, py in puntos)
    if marca_x is not None:
        px, _ = vista.a_pixel(marca_x, 0)
        if vista.izquierda <= px <= vista.derecha:
            escena.append(linea([(px, vista.arriba), (px, vista.abajo)], TEMA["exito"], 1.5, True))
    escena.append(rectangulo(vista.derecha - 196, vista.arriba + 3, vista.derecha - 6, vista.arriba + 7 + 17 * len(series), TEMA["panel"], TEMA["rejilla_fuerte"]))
    y = vista.arriba + 13
    for s in series:
        escena.append(linea([(vista.derecha - 190, y), (vista.derecha - 170, y)], s["color"], 3, s.get("punteada", False)))
        escena.append(texto(vista.derecha - 164, y, s["texto"], TEMA["texto"], 11, ancla="w"))
        y += 17
    return escena


def escena_convergencia(informe, t, ancho, alto):
    """Muestra cómo baja la cota del error de la bisección, comparada con la recta teórica (b − a)/2ⁿ.

    Entrada: informe de biseccion, t, tamaño de la escena. Salida: lista de primitivas.
    """
    iteraciones = informe["iteraciones"]
    if not iteraciones:
        return [rectangulo(0, 0, ancho, alto, TEMA["fondo"]), texto(ancho / 2, alto / 2, "No hubo iteraciones: la raíz está en un extremo.", TEMA["texto_3"], 13)]
    ancho_inicial = informe["b"] - informe["a"]
    series = [{"texto": "cota (b − a)/2ⁿ", "color": TEMA["advertencia"], "punteada": True,
               "puntos": [(it["n"], ancho_inicial / 2 ** it["n"]) for it in iteraciones]},
              {"texto": "|f(c)|", "color": TEMA["primario"],
               "puntos": [(it["n"], abs(it["fc"])) for it in iteraciones if it["fc"] != 0]}]
    series[1]["puntos"] = series[1]["puntos"] or [(1, 1e-300)]
    k = min(len(iteraciones), int(t) + 1)
    n = len(iteraciones)
    progreso = (k - 1) / (n - 1) if n > 1 else 1.0
    return escena_lineas_log(series, "Convergencia: cada iteración reduce el error a la mitad", ancho, alto, "iteración n", progreso, k)


def alto_tabla(filas, alto_fila=25, con_titulo=True):
    """Calcula el alto natural de una tabla.

    Entrada: cantidad de filas, alto de fila y con_titulo (bool). Salida: píxeles lógicos.
    """
    return (filas + 1) * alto_fila + (30 if con_titulo else 8)


def escena_tabla(encabezados, filas, ancho, proporciones=None, titulo=None, resaltar=None, alto_fila=25, revelar=None):
    """Dibuja una tabla ligera en un solo lienzo, con la fila actual resaltada.

    Entrada: encabezados, filas de textos, ancho, proporciones de columnas, título, fila a resaltar, alto de fila y
    cantidad de filas visibles. Salida: lista de primitivas.
    """
    alto = alto_tabla(len(filas), alto_fila, titulo is not None)
    proporciones = proporciones or [1] * len(encabezados)
    total = sum(proporciones)
    util = ancho - 16
    columnas, x = [], 8.0
    for p in proporciones:
        columnas.append(x)
        x += util * p / total
    escena = [rectangulo(0, 0, ancho, alto, TEMA["fondo"])]
    y = 4.0
    if titulo:
        escena.append(texto(8, y + 11, titulo, TEMA["texto"], 13, True, "w"))
        y += 26
    escena.append(rectangulo(8, y, ancho - 8, y + alto_fila, TEMA["panel"]))
    for columna, encabezado in zip(columnas, encabezados):
        escena.append(texto(columna + 8, y + alto_fila / 2, encabezado, TEMA["primario"], 11, True, "w"))
    y += alto_fila
    for i, fila in enumerate(filas):
        if revelar is not None and i >= revelar:
            break
        if i == resaltar:
            escena.append(rectangulo(8, y, ancho - 8, y + alto_fila, mezclar_colores(TEMA["fondo"], TEMA["exito"], 0.22)))
        elif i % 2:
            escena.append(rectangulo(8, y, ancho - 8, y + alto_fila, mezclar_colores(TEMA["fondo"], "#000000", 0.14)))
        for columna, valor in zip(columnas, fila):
            escena.append(texto(columna + 8, y + alto_fila / 2, valor, TEMA["texto_2"], 11, ancla="w", mono=True))
        y += alto_fila
    return escena


def escena_posicional(descomposicion, t, ancho):
    """Dibuja cada dígito con su peso y su contribución; las barras muestran cuánto aporta cada posición.

    Entrada: descomposición de descomponer_posicional, t entre 0 y 1 y ancho. Salida: (primitivas, alto natural).
    """
    filas, base = descomposicion["filas"], descomposicion["base"]
    alto = 250
    escena = [rectangulo(0, 0, ancho, alto, TEMA["fondo"]),
              texto(12, 16, f"Notación posicional en base {base}: cada posición k pesa {base}ᵏ", TEMA["texto"], 13, True, "w")]
    n = len(filas)
    enteros = len(descomposicion["entero"])
    separacion = 16 if descomposicion["fraccion"] else 0
    celda = min(70.0, (ancho - 24 - separacion) / max(1, n))
    x0 = 12 + (ancho - 24 - separacion - celda * n) / 2
    maximo = max((float(f["contribucion"]) for f in filas), default=1.0) or 1.0
    tam = max(8, min(20, int(celda * 0.42)))
    tam_chico = max(7, min(11, int(celda * 0.2)))
    if descomposicion["signo"] < 0 and t > 0.02:
        escena.append(texto(x0 - 4, 146 + min(46, celda - 2) / 2, "−", TEMA["texto"], tam, True, "e"))
    for i, fila in enumerate(filas):
        aparicion = suavizar((t * (n + 2) - i) / 2)
        x = x0 + celda * i + (separacion if i >= enteros else 0)
        color = TEMA["primario"] if i < enteros else TEMA["advertencia"]
        base_barra = 118.0
        barra = (float(fila["contribucion"]) / maximo) ** 0.5 * 62 * aparicion
        escena.append(rectangulo(x + 3, base_barra - barra, x + celda - 3, base_barra, mezclar_colores(TEMA["fondo"], color, 0.55)))
        if aparicion > 0.02:
            # Si las celdas son angostas, solo una de cada cuatro posiciones lleva su peso para que no se encimen.
            if celda >= 26 or fila["posicion"] % 4 == 0:
                escena.append(texto(x + celda / 2, 134, f"{base}{str(fila['posicion']).translate(str.maketrans('0123456789-', '⁰¹²³⁴⁵⁶⁷⁸⁹⁻'))}",
                                    TEMA["texto_3"], tam_chico + 1))
            escena.append(rectangulo(x + 2, 146, x + celda - 2, 146 + min(46, celda - 2), mezclar_colores(TEMA["fondo"], color, 0.28 * aparicion),
                                     mezclar_colores(TEMA["fondo"], color, aparicion), 1.5))
            escena.append(texto(x + celda / 2, 146 + min(46, celda - 2) / 2, fila["digito"], TEMA["texto"], tam, True, mono=True))
            if celda > 34:
                escena.append(texto(x + celda / 2, 204, decimal_exacto(fila["contribucion"], 4), TEMA["texto_2"], tam_chico))
    if separacion:
        x_punto = x0 + celda * enteros + separacion / 2
        escena.append(circulo(x_punto, 188, 3, TEMA["texto"]))
    if t > 0.7:
        valor = decimal_exacto(descomposicion["valor"], 40)
        color_total = mezclar_colores(TEMA["fondo"], TEMA["exito"], suavizar((t - 0.7) / 0.3))
        escena.append(texto(ancho / 2, 232, f"Suma de contribuciones = {valor}", color_total, 14, True))
    return escena, alto


def _recortar(cadena, maximo):
    """Acorta un texto que no cabe en su espacio.

    Entrada: cadena y máximo de caracteres. Salida: cadena, terminada en «…» si se acortó.
    """
    maximo = max(4, int(maximo))
    return cadena if len(cadena) <= maximo else cadena[:maximo - 1] + "…"


def escena_conversion(binario, t, ancho):
    """Dibuja las divisiones entre 2 y las multiplicaciones por 2, revelando cada bit y su sentido de lectura.

    Entrada: conversión de decimal_a_binario, t entre 0 y 1 y ancho. Salida: (primitivas, alto natural).
    """
    divisiones, productos = binario["divisiones"][:14], binario["multiplicaciones"][:14]
    omitidas = len(binario["divisiones"]) + len(binario["multiplicaciones"]) - len(divisiones) - len(productos)
    filas = max(len(divisiones), len(productos), 1)
    alto = 96 + filas * 24 + (22 if omitidas else 0)
    escena = [rectangulo(0, 0, ancho, alto, TEMA["fondo"]),
              texto(12, 16, "Conversión a base 2 paso a paso", TEMA["texto"], 13, True, "w")]
    mitad = ancho / 2
    total = max(1, len(divisiones) + len(productos))
    escena.append(texto(16, 40, "Parte entera: dividir entre 2", TEMA["primario"], 12, True, "w"))
    escena.append(texto(mitad + 10, 40, "Parte fraccionaria: multiplicar por 2", TEMA["advertencia"], 12, True, "w"))
    if not divisiones:
        escena.append(texto(16, 64, "La parte entera es 0.", TEMA["texto_3"], 12, ancla="w"))
    for i, d in enumerate(divisiones):
        if t * (total + 1) < i:
            break
        y = 64 + i * 24
        escena.append(texto(16, y, _recortar(f"{d['dividendo']} ÷ 2 = {d['cociente']}", (mitad - 132) / 8.2), TEMA["texto_2"], 12, ancla="w", mono=True))
        escena.append(circulo(mitad - 100, y, 10, mezclar_colores(TEMA["fondo"], TEMA["primario"], 0.35), TEMA["primario"], 1.5))
        escena.append(texto(mitad - 100, y, d["residuo"], TEMA["texto"], 12, True, mono=True))
    if len(divisiones) > 1 and t > 0.5:
        escena.extend(flecha(mitad - 76, 64 + (len(divisiones) - 1) * 24, mitad - 76, 58, TEMA["primario"], 2, 9))
        escena.append(texto(mitad - 68, 64 + (len(divisiones) - 1) * 12, "se lee ↑", TEMA["texto_3"], 10, ancla="w"))
    if not productos:
        escena.append(texto(mitad + 10, 64, "No hay parte fraccionaria.", TEMA["texto_3"], 12, ancla="w"))
    for i, p in enumerate(productos):
        if t * (total + 1) < len(divisiones) + i:
            break
        y = 64 + i * 24
        escena.append(texto(mitad + 10, y, f"{decimal_exacto(p['fraccion'], 6)} × 2 = {decimal_exacto(p['producto'], 6)}", TEMA["texto_2"], 12, ancla="w", mono=True))
        escena.append(circulo(ancho - 70, y, 10, mezclar_colores(TEMA["fondo"], TEMA["advertencia"], 0.35), TEMA["advertencia"], 1.5))
        escena.append(texto(ancho - 70, y, p["bit"], TEMA["texto"], 12, True, mono=True))
    if len(productos) > 1 and t > 0.5:
        escena.extend(flecha(ancho - 46, 58, ancho - 46, 64 + (len(productos) - 1) * 24, TEMA["advertencia"], 2, 9))
        escena.append(texto(ancho - 40, 64 + (len(productos) - 1) * 12, "se lee ↓", TEMA["texto_3"], 10, ancla="w"))
    if t > 0.85:
        escena.append(texto(ancho / 2, alto - 18, _recortar(f"Resultado: {binario['texto']} (base 2)", (ancho - 24) / 8), TEMA["exito"], 14, True))
    if omitidas:
        escena.append(texto(16, alto - 42, f"Se omiten {omitidas} pasos más: están completos en la pestaña Procedimiento.", TEMA["texto_3"], 11, ancla="w"))
    return escena, alto


def escena_ieee754(rep, t, ancho):
    """Dibuja los bits del punto flotante IEEE 754 coloreados por signo, exponente y mantisa.

    Entrada: representación de representacion_ieee754, t entre 0 y 1 y ancho. Salida: (primitivas, alto natural).
    """
    alto = 190
    escena = [rectangulo(0, 0, ancho, alto, TEMA["fondo"]),
              texto(12, 16, f"Así se guarda en la computadora (IEEE 754, {rep['bits']} bits)", TEMA["texto"], 13, True, "w")]
    bits = rep["cadena"]
    celda = (ancho - 24) / len(bits)
    alto_celda = min(30.0, max(18.0, celda * 2.2))
    fin_exponente = 1 + len(rep["exponente"])
    tam = max(7, min(12, int(celda * 0.8)))
    for i, bit in enumerate(bits):
        color = TEMA["rosa"] if i == 0 else TEMA["advertencia"] if i < fin_exponente else TEMA["primario"]
        aparicion = suavizar(t * (len(bits) + 8) / 8 - i / 8)
        x = 12 + i * celda
        relleno = mezclar_colores(TEMA["fondo"], color, 0.55 if bit == "1" else 0.12)
        escena.append(rectangulo(x + 0.5, 42, x + celda - 0.5, 42 + alto_celda, mezclar_colores(TEMA["fondo"], relleno, aparicion)))
        if aparicion > 0.5:
            escena.append(texto(x + celda / 2, 42 + alto_celda / 2, bit, TEMA["texto"], tam, bit == "1", mono=True))
    y_llave = 42 + alto_celda + 8
    for inicio, fin, nombre, color in ((0, 1, "s", TEMA["rosa"]), (1, fin_exponente, f"exponente ({len(rep['exponente'])})", TEMA["advertencia"]),
                                       (fin_exponente, len(bits), f"mantisa ({len(rep['mantisa'])})", TEMA["primario"])):
        x1, x2 = 12 + inicio * celda, 12 + fin * celda
        escena.append(linea([(x1 + 1, y_llave), (x2 - 1, y_llave)], color, 2))
        escena.append(texto((x1 + x2) / 2, y_llave + 11, nombre, color, 11, True))
    if t > 0.6:
        y = y_llave + 34
        if rep["tipo"] == "normal":
            formula = (f"(−1)^{rep['signo']} × 1.mantisa₂ × 2^({int(rep['exponente'], 2)} − {rep['sesgo']}) = "
                       f"{decimal_exacto(rep['almacenado'], 26)}")
        elif rep["tipo"] == "infinito":
            formula = "El número excede el máximo representable: se guarda como infinito."
        elif rep["tipo"] == "cero":
            formula = "Todos los bits de exponente y mantisa en 0 representan el número 0."
        else:
            formula = f"Número subnormal: {decimal_exacto(rep['almacenado'], 20)}"
        escena.append(texto(12, y, formula, TEMA["texto_2"], 12, ancla="w", mono=True))
        if rep["error_representacion"] is not None:
            nota = "Exacto: el número cabe en la mantisa." if rep["exacta"] else f"Error de representación: {decimal_exacto(rep['error_representacion'], 6)}"
            escena.append(texto(12, y + 24, nota, TEMA["exito"] if rep["exacta"] else TEMA["advertencia"], 12, True, "w"))
    return escena, alto


def escena_recta_numerica(real, aproximado, t, ancho):
    """Acerca la cámara a la recta numérica hasta que se distingue la separación entre v y v*.

    Entrada: valor real, aproximado, t entre 0 y 1 y ancho. Salida: (primitivas, alto natural).
    """
    alto = 130
    v, a = float(real), float(aproximado)
    separacion = abs(v - a)
    centro = (v + a) / 2
    radio_final = max(separacion * 0.8, abs(centro) * 1e-15, 1e-300)
    radio_inicial = max(abs(centro) * 1.2, radio_final * 2, 1.0)
    s = suavizar(t)
    # Se interpola en escala logarítmica para que el acercamiento se vea uniforme aunque abarque muchos órdenes.
    radio = 10 ** (logaritmo_10(radio_inicial) * (1 - s) + logaritmo_10(radio_final) * s)
    x_min, x_max = centro - radio, centro + radio
    escena = [rectangulo(0, 0, ancho, alto, TEMA["fondo"]),
              texto(12, 16, "La aproximación en la recta numérica", TEMA["texto"], 13, True, "w"),
              texto(ancho - 12, 16, f"zoom ×{formatear_real(radio_inicial / radio, 3)}", TEMA["texto_3"], 11, ancla="e")]
    y = 78
    x1, x2 = 24, ancho - 24
    escena.append(linea([(x1, y), (x2, y)], TEMA["eje"], 2))
    marcas, paso = marcas_eje(x_min, x_max, 7)
    for m in marcas:
        px = x1 + (m - x_min) / (x_max - x_min) * (x2 - x1)
        escena.append(linea([(px, y - 5), (px, y + 5)], TEMA["eje"], 1))
        escena.append(texto(px, y + 9, formatear_real(m, 9 if paso < 1e-3 else 5), TEMA["texto_3"], 9, ancla="n"))
    for valor, nombre, color, arriba in ((v, "v", TEMA["exito"], True), (a, "v*", TEMA["advertencia"], False)):
        px = x1 + (valor - x_min) / (x_max - x_min) * (x2 - x1)
        if x1 <= px <= x2:
            escena.append(circulo(px, y, 6, color, TEMA["fondo"], 2))
            escena.append(texto(px, y - 14 if arriba else y - 30, nombre, color, 12, True, "s"))
    if t > 0.85 and separacion > 0:
        p1 = x1 + (v - x_min) / (x_max - x_min) * (x2 - x1)
        p2 = x1 + (a - x_min) / (x_max - x_min) * (x2 - x1)
        escena.append(linea([(p1, y + 28), (p2, y + 28)], TEMA["error"], 2))
        escena.append(texto((p1 + p2) / 2, y + 40, f"Ea = {formatear_real(separacion, 6)}", TEMA["error"], 11, True))
    return escena, alto


def escena_barras_error(tabla, ancho, alto, t, cifras=None):
    """Compara el error de redondear y de truncar según las cifras significativas, en escala logarítmica.

    Entrada: filas de tabla_redondeo, tamaño, t entre 0 y 1 y cifras elegidas. Salida: lista de primitivas.
    """
    valores = [float(v) for f in tabla for v in (f["error_redondeo"], f["error_truncamiento"]) if float(v) > 0]
    escena = [rectangulo(0, 0, ancho, alto, TEMA["fondo"]),
              texto(12, 16, "Redondeo y truncamiento: error según las cifras significativas", TEMA["texto"], 13, True, "w")]
    if not valores:
        escena.append(texto(ancho / 2, alto / 2, "El valor se representa exactamente con pocas cifras: el error es 0.", TEMA["texto_3"], 13))
        return escena
    bajo, alto_log = logaritmo_10(min(valores)) - 0.5, logaritmo_10(max(valores)) + 0.3
    vista = Vista(0.4, len(tabla) + 0.6, bajo, alto_log, ancho, alto, (62, 14, 34, 36))
    escena = escena_ejes(vista, formato_y=lambda y: f"10^{round(y)}" if abs(y - round(y)) < 1e-6 else "", marcas_x=len(tabla), marcas_y=6)
    escena.append(texto(12, 16, "Redondeo y truncamiento: error según las cifras significativas", TEMA["texto"], 13, True, "w"))
    escena.append(texto(vista.derecha, alto - 6, "cifras significativas n", TEMA["texto_3"], 10, ancla="se"))
    ancho_barra = (vista.derecha - vista.izquierda) / len(tabla) * 0.36
    _, base = vista.a_pixel(0, bajo)
    for i, fila in enumerate(tabla):
        aparicion = suavizar(t * (len(tabla) + 3) / 3 - i / 3)
        px, _ = vista.a_pixel(fila["n"], 0)
        if fila["n"] == cifras:
            escena.append(rectangulo(px - ancho_barra * 1.3, vista.arriba, px + ancho_barra * 1.3, vista.abajo, mezclar_colores(TEMA["fondo"], TEMA["exito"], 0.12)))
        for desplazamiento, clave, color in ((-1, "error_redondeo", TEMA["primario"]), (0, "error_truncamiento", TEMA["advertencia"])):
            if float(fila[clave]) > 0:
                _, py = vista.a_pixel(0, logaritmo_10(float(fila[clave])))
                y = base + (py - base) * aparicion
                escena.append(rectangulo(px + desplazamiento * ancho_barra, y, px + (desplazamiento + 1) * ancho_barra, base, color))
    for k, (nombre, color) in enumerate((("redondeo", TEMA["primario"]), ("truncamiento", TEMA["advertencia"]))):
        escena.append(rectangulo(vista.derecha - 110, vista.arriba + 6 + 17 * k, vista.derecha - 96, vista.arriba + 18 + 17 * k, color))
        escena.append(texto(vista.derecha - 90, vista.arriba + 12 + 17 * k, nombre, TEMA["texto"], 11, ancla="w"))
    return escena


def interpolar_matriz(A, t):
    """Calcula (1 − t)·I + t·A, el camino recto de la identidad a A que se ve en la animación.

    Entrada: matriz cuadrada de números y t. Salida: matriz de float.
    """
    n = len(A)
    return [[(1 - t) * (1.0 if i == j else 0.0) + t * float(A[i][j]) for j in range(n)] for i in range(n)]


def aplicar_matriz(A, v):
    """Calcula el producto A·v con números de punto flotante para dibujar.

    Entrada: matriz y vector. Salida: lista.
    """
    return [sum(a * b for a, b in zip(fila, v)) for fila in A]


def vista_cuadrada(radio_x, radio_y, ancho, alto, centro=(0.0, 0.0)):
    """Crea una vista con la misma escala en ambos ejes para que los ángulos y las áreas no se deformen.

    Entrada: radios mínimos en x e y, tamaño de la escena y centro. Salida: Vista.
    """
    util_x, util_y = max(1, ancho - 62), max(1, alto - 50)
    escala = min(util_x / (2 * radio_x), util_y / (2 * radio_y))
    medio_x, medio_y = util_x / (2 * escala), util_y / (2 * escala)
    return Vista(centro[0] - medio_x, centro[0] + medio_x, centro[1] - medio_y, centro[1] + medio_y, ancho, alto, (44, 18, 18, 32))


def escena_transformacion_2d(A, t, ancho, alto):
    """Anima cómo A deforma el plano: la cuadrícula, la base canónica y el cuadrado unidad.

    Entrada: matriz 2×2 de números, t entre 0 y 1 y tamaño de la escena. Salida: lista de primitivas.
    """
    M = interpolar_matriz(A, suavizar(t))
    final = interpolar_matriz(A, 1.0)
    extremos = [aplicar_matriz(final, (a, b)) for a in (-1.2, 1.2) for b in (-1.2, 1.2)]
    radio = max(2.5, max(max(abs(p[0]), abs(p[1])) for p in extremos) * 1.15)
    vista = vista_cuadrada(radio, radio, ancho, alto)
    escena = escena_ejes(vista)
    color_rejilla = mezclar_colores(TEMA["fondo"], TEMA["primario"], 0.5)
    # La cuadrícula es mayor que la vista para que sus extremos no se vean al deformarse.
    N = min(40, int(max(vista.x_max, vista.y_max) * 3) + 6)
    rango = [k for k in range(-N, N + 1)]
    for k in rango:
        for inicio, fin in (((k, -N), (k, N)), ((-N, k), (N, k))):
            puntos = [vista.a_pixel(*aplicar_matriz(M, inicio)), vista.a_pixel(*aplicar_matriz(M, fin))]
            for trozo in recortar_polilinea(puntos, vista.izquierda, vista.arriba, vista.derecha, vista.abajo):
                escena.append(linea(trozo, color_rejilla, 1))
    det = M[0][0] * M[1][1] - M[0][1] * M[1][0]
    color_area = TEMA["advertencia"] if det >= 0 else TEMA["rosa"]
    esquinas = [vista.a_pixel(*aplicar_matriz(M, p)) for p in ((0, 0), (1, 0), (1, 1), (0, 1))]
    escena.append(poligono(esquinas, mezclar_colores(TEMA["fondo"], color_area, 0.55), color_area, 2))
    origen = vista.a_pixel(0, 0)
    for vector, color, nombre in (((1, 0), TEMA["exito"], "A·e₁"), ((0, 1), TEMA["error"], "A·e₂")):
        destino = vista.a_pixel(*aplicar_matriz(M, vector))
        escena.extend(flecha(origen[0], origen[1], destino[0], destino[1], color, 3, 12))
        escena.append(texto(destino[0] + 8, destino[1] - 8, nombre, color, 12, True, "sw"))
    escena.append(rectangulo(vista.izquierda + 8, vista.arriba + 8, vista.izquierda + 210, vista.arriba + 54, TEMA["panel"], TEMA["rejilla_fuerte"]))
    escena.append(texto(vista.izquierda + 18, vista.arriba + 21, f"Área = |det| = {formatear_real(abs(det), 4)}", TEMA["texto"], 12, True, "w"))
    orientacion = "orientación invertida" if det < 0 else "plano aplastado (det = 0)" if abs(det) < 1e-12 else "orientación conservada"
    escena.append(texto(vista.izquierda + 18, vista.arriba + 41, orientacion, color_area, 11, ancla="w"))
    return escena


class Camara:
    """Cámara en perspectiva para las escenas 3D: gira alrededor del origen y proyecta a píxeles."""

    def __init__(self, giro, inclinacion, escala, centro_x, centro_y, distancia=9.0):
        """Calcula los senos y cosenos de los ángulos una sola vez.

        Entrada: giro e inclinación en radianes, escala, centro en píxeles y distancia. Salida: None.
        """
        self.seno_g, self.coseno_g = seno(giro), coseno(giro)
        self.seno_i, self.coseno_i = seno(inclinacion), coseno(inclinacion)
        self.escala, self.centro_x, self.centro_y, self.distancia = escala, centro_x, centro_y, distancia

    def posicion(self):
        """Calcula dónde está el ojo de la cámara en el espacio, deshaciendo sus dos giros.

        Salida: punto (x, y, z).
        """
        return (-self.distancia * self.coseno_i * self.seno_g, -self.distancia * self.coseno_i * self.coseno_g,
                self.distancia * self.seno_i)

    def proyectar(self, punto):
        """Proyecta un punto (x, y, z), con z hacia arriba, a la pantalla.

        Entrada: punto. Salida: (px, py, profundidad); mayor profundidad significa más lejos.
        """
        x, y, z = punto
        xr = x * self.coseno_g - y * self.seno_g
        yr = x * self.seno_g + y * self.coseno_g
        yc = yr * self.coseno_i - z * self.seno_i
        zc = yr * self.seno_i + z * self.coseno_i
        factor = self.distancia / max(0.5, self.distancia + yc)
        return self.centro_x + xr * self.escala * factor, self.centro_y - zc * self.escala * factor, yc


def _camara_para_caja(giro, inclinacion, radio, ancho, alto):
    """Crea una cámara que deja a la vista toda la caja [−radio, radio]³, incluso con perspectiva.

    Entrada: ángulos, radio de la caja y tamaño de la escena. Salida: Camara.
    """
    return Camara(giro, inclinacion, min(ancho, alto) * 0.25 / radio, ancho / 2, alto / 2 + 8, radio * 6)


def _ejes_3d(camara, radio, nombres=("x₁", "x₂", "x₃")):
    """Dibuja los tres ejes con sus nombres.

    Entrada: cámara, largo de los ejes y nombres. Salida: lista de primitivas.
    """
    escena = []
    origen = camara.proyectar((0, 0, 0))
    for k, (nombre, color) in enumerate(zip(nombres, (TEMA["exito"], TEMA["error"], TEMA["primario"]))):
        punta = [0.0, 0.0, 0.0]
        punta[k] = radio
        destino = camara.proyectar(punta)
        escena.extend(flecha(origen[0], origen[1], destino[0], destino[1], mezclar_colores(TEMA["fondo"], color, 0.75), 1.8, 9))
        escena.append(texto(destino[0] + 6, destino[1], nombre, color, 12, True, "w"))
    return escena


def _caja_3d(camara, radio):
    """Dibuja el borde de la caja que delimita la escena.

    Entrada: cámara y radio de la caja. Salida: lista de primitivas.
    """
    vertices = [(a, b, c) for a in (-radio, radio) for b in (-radio, radio) for c in (-radio, radio)]
    escena = []
    for i, p in enumerate(vertices):
        for q in vertices[i + 1:]:
            if sum(1 for u, v in zip(p, q) if u != v) == 1:
                a, b = camara.proyectar(p), camara.proyectar(q)
                escena.append(linea([(a[0], a[1]), (b[0], b[1])], TEMA["rejilla_fuerte"], 1))
    return escena


def escena_transformacion_3d(A, t, giro, inclinacion, ancho, alto):
    """Renderiza cómo A deforma el cubo unidad: caras sombreadas, base transformada y volumen |det|.

    Entrada: matriz 3×3, t entre 0 y 1, ángulos de cámara y tamaño. Salida: lista de primitivas.
    """
    M = interpolar_matriz(A, suavizar(t))
    final = interpolar_matriz(A, 1.0)
    alcance = max(max(abs(c) for c in aplicar_matriz(final, v)) for v in
                  [(a, b, c) for a in (0, 1) for b in (0, 1) for c in (0, 1)])
    radio = max(1.4, alcance * 1.1)
    camara = _camara_para_caja(giro, inclinacion, radio, ancho, alto)
    escena = [rectangulo(0, 0, ancho, alto, TEMA["fondo"])]
    escena.extend(_caja_3d(camara, radio))
    escena.extend(_ejes_3d(camara, radio))
    vertices = {(a, b, c): aplicar_matriz(M, (a, b, c)) for a in (0, 1) for b in (0, 1) for c in (0, 1)}
    esquinas = list(vertices)
    for i, p in enumerate(esquinas):
        for q in esquinas[i + 1:]:
            if sum(1 for u, v in zip(p, q) if u != v) == 1:
                a, b = camara.proyectar(p), camara.proyectar(q)
                escena.append(linea([(a[0], a[1]), (b[0], b[1])], TEMA["eje"], 1, True))
    caras = (((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),
             ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)), ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)),
             ((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)))
    colores = (TEMA["primario"], TEMA["primario"], TEMA["exito"], TEMA["exito"], TEMA["error"], TEMA["error"])
    dibujo = []
    for cara, color in zip(caras, colores):
        puntos = [camara.proyectar(vertices[v]) for v in cara]
        profundidad = sum(p[2] for p in puntos) / 4
        a, b, c = [vertices[v] for v in cara[:3]]
        normal = (((b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1])),
                  ((b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2])),
                  ((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])))
        largo = sum(u * u for u in normal) ** 0.5 or 1.0
        luz = abs(normal[0] * 0.35 + normal[1] * -0.55 + normal[2] * 0.76) / largo
        relleno = mezclar_colores(TEMA["fondo"], color, 0.28 + 0.5 * luz)
        dibujo.append((profundidad, poligono([(p[0], p[1]) for p in puntos], relleno, mezclar_colores(relleno, "#FFFFFF", 0.35), 1.2)))
    dibujo.sort(key=lambda par: -par[0])
    escena.extend(pieza for _, pieza in dibujo)
    det = (M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1]) - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
           + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]))
    escena.append(rectangulo(10, 10, 236, 56, TEMA["panel"], TEMA["rejilla_fuerte"]))
    escena.append(texto(20, 23, f"Volumen = |det| = {formatear_real(abs(det), 4)}", TEMA["texto"], 12, True, "w"))
    orientacion = "espacio aplastado (det = 0)" if abs(det) < 1e-12 else "orientación invertida" if det < 0 else "orientación conservada"
    escena.append(texto(20, 43, orientacion, TEMA["advertencia"] if det < 0 else TEMA["texto_2"], 11, ancla="w"))
    return escena


def _ecuacion(fila, termino, nombres):
    """Escribe una ecuación sin coeficientes redundantes, por ejemplo x1 − x2 = 3.

    Entrada: coeficientes, término independiente y nombres. Salida: cadena.
    """
    return formatear_ecuacion_original([Fraction(v) for v in fila], Fraction(termino), list(nombres))


def escena_sistema_2d(A, b, solucion, t, ancho, alto):
    """Dibuja cada ecuación como una recta que se traza progresivamente y marca la solución.

    Entrada: A (filas de 2 números), b, solución (par o None), t y tamaño. Salida: lista de primitivas.
    """
    centro = (float(solucion[0]), float(solucion[1])) if solucion else (0.0, 0.0)
    radio = max(4.0, abs(centro[0]) * 0.6, abs(centro[1]) * 0.6)
    vista = vista_cuadrada(radio, radio, ancho, alto, centro)
    escena = escena_ejes(vista)
    filas = len(A)
    for i, (fila, bi) in enumerate(zip(A, b)):
        a1, a2, c = float(fila[0]), float(fila[1]), float(bi)
        color = SERIES[i % len(SERIES)]
        progreso = suavizar(t * (filas + 1) - i)
        if a1 == 0 and a2 == 0:
            continue
        if abs(a2) >= abs(a1):
            p, q = (vista.x_min, (c - a1 * vista.x_min) / a2), (vista.x_max, (c - a1 * vista.x_max) / a2)
        else:
            p, q = ((c - a2 * vista.y_min) / a1, vista.y_min), ((c - a2 * vista.y_max) / a1, vista.y_max)
        destino = (p[0] + (q[0] - p[0]) * progreso, p[1] + (q[1] - p[1]) * progreso)
        for trozo in recortar_polilinea([vista.a_pixel(*p), vista.a_pixel(*destino)], vista.izquierda, vista.arriba, vista.derecha, vista.abajo):
            escena.append(linea(trozo, mezclar_colores(TEMA["fondo"], color, 0.25), 6))
            escena.append(linea(trozo, color, 2.5))
        escena.append(texto(vista.izquierda + 12, vista.arriba + 14 + 18 * i, _ecuacion(fila, bi, ("x1", "x2")), color, 12, True, "w"))
    if solucion and t > 0.8:
        px, py = vista.a_pixel(*centro)
        radio_punto = 4 + 6 * suavizar((t - 0.8) / 0.2)
        escena.append(circulo(px, py, radio_punto + 4, mezclar_colores(TEMA["fondo"], TEMA["texto"], 0.25)))
        escena.append(circulo(px, py, radio_punto, TEMA["texto"], TEMA["fondo"], 2))
        escena.append(texto(px + 14, py - 14, f"x = ({formatear_real(centro[0], 5)}, {formatear_real(centro[1], 5)})", TEMA["texto"], 13, True, "sw"))
    return escena


def plano_en_caja(normal, d, radio):
    """Calcula el polígono en que el plano n·x = d corta a la caja [−radio, radio]³.

    Entrada: normal, término independiente y radio. Salida: lista ordenada de vértices (vacía si no la corta).
    """
    vertices = [(a, b, c) for a in (-radio, radio) for b in (-radio, radio) for c in (-radio, radio)]
    puntos = []
    for i, p in enumerate(vertices):
        for q in vertices[i + 1:]:
            if sum(1 for u, v in zip(p, q) if u != v) != 1:
                continue
            fp = sum(n * u for n, u in zip(normal, p)) - d
            fq = sum(n * u for n, u in zip(normal, q)) - d
            if (fp <= 0 < fq) or (fq <= 0 < fp):
                s = fp / (fp - fq)
                puntos.append(tuple(u + (v - u) * s for u, v in zip(p, q)))
    if len(puntos) < 3:
        return []
    centro = [sum(p[k] for p in puntos) / len(puntos) for k in range(3)]
    # Dos vectores perpendiculares dentro del plano permiten ordenar los vértices por su ángulo.
    largo = sum(n * n for n in normal) ** 0.5
    n = [c / largo for c in normal]
    apoyo = (1.0, 0.0, 0.0) if abs(n[0]) < 0.9 else (0.0, 1.0, 0.0)
    u = (n[1] * apoyo[2] - n[2] * apoyo[1], n[2] * apoyo[0] - n[0] * apoyo[2], n[0] * apoyo[1] - n[1] * apoyo[0])
    v = (n[1] * u[2] - n[2] * u[1], n[2] * u[0] - n[0] * u[2], n[0] * u[1] - n[1] * u[0])

    def angulo(p):
        """Calcula el ángulo del vértice alrededor del centro, sin atan2: usa arcotangente y el cuadrante.

        Entrada: vértice. Salida: ángulo.
        """
        w = [p[k] - centro[k] for k in range(3)]
        cu, cv = sum(a * b for a, b in zip(w, u)), sum(a * b for a, b in zip(w, v))
        if cu == 0:
            return 1.5707963267948966 if cv > 0 else -1.5707963267948966
        base = arcotangente(cv / cu)
        return base if cu > 0 else base + 3.141592653589793

    return sorted(puntos, key=angulo)


def _distancia_con_signo(normal, d, punto):
    """Calcula n·x − d: positivo delante del plano y negativo detrás.

    Entrada: normal, término independiente y punto. Salida: número.
    """
    return normal[0] * punto[0] + normal[1] * punto[1] + normal[2] * punto[2] - d


def dividir_poligono(vertices, normal, d, tolerancia=1e-9):
    """Parte un polígono convexo con el plano n·x = d.

    Entrada: vértices, normal, término independiente y tolerancia. Salida: (parte delantera, parte trasera).
    """
    delante, detras = [], []
    for i, p in enumerate(vertices):
        q = vertices[(i + 1) % len(vertices)]
        fp, fq = _distancia_con_signo(normal, d, p), _distancia_con_signo(normal, d, q)
        if fp >= -tolerancia:
            delante.append(p)
        if fp <= tolerancia:
            detras.append(p)
        if (fp > tolerancia and fq < -tolerancia) or (fp < -tolerancia and fq > tolerancia):
            s = fp / (fp - fq)
            corte = tuple(u + (v - u) * s for u, v in zip(p, q))
            delante.append(corte)
            detras.append(corte)
    return (delante if len(delante) >= 3 else []), (detras if len(detras) >= 3 else [])


def ordenar_superficies(piezas, planos, ojo, k=0):
    """Ordena superficies que se cruzan de atrás hacia adelante con un árbol BSP: cada plano divide a las demás.

    Entrada: piezas (vértices, índice del plano), planos (normal, d), posición del ojo y plano actual.
    Salida: lista de piezas en el orden en que deben pintarse.
    """
    if not piezas or k >= len(planos):
        return list(piezas)
    normal, d = planos[k]
    sobre, delante, detras = [], [], []
    for vertices, indice in piezas:
        if indice == k or all(abs(_distancia_con_signo(normal, d, p)) < 1e-9 for p in vertices):
            sobre.append((vertices, indice))
            continue
        parte_delantera, parte_trasera = dividir_poligono(vertices, normal, d)
        if parte_delantera:
            delante.append((parte_delantera, indice))
        if parte_trasera:
            detras.append((parte_trasera, indice))
    lejos, cerca = (detras, delante) if _distancia_con_signo(normal, d, ojo) > 0 else (delante, detras)
    return ordenar_superficies(lejos, planos, ojo, k + 1) + sobre + ordenar_superficies(cerca, planos, ojo, k + 1)


def escena_sistema_3d(A, b, solucion, t, giro, inclinacion, ancho, alto):
    """Renderiza cada ecuación como un plano; donde se cruzan los tres planos está la solución.

    Entrada: A (filas de 3 números), b, solución o None, t, ángulos de cámara y tamaño. Salida: lista de primitivas.
    """
    centro = [float(v) for v in solucion] if solucion else [0.0, 0.0, 0.0]
    radio = max(3.0, max(abs(v) for v in centro) * 1.4)
    camara = _camara_para_caja(giro, inclinacion, radio, ancho, alto)
    escena = [rectangulo(0, 0, ancho, alto, TEMA["fondo"])]
    escena.extend(_caja_3d(camara, radio))
    filas = len(A)
    planos, piezas, colores = [], [], []
    for i, (fila, bi) in enumerate(zip(A, b)):
        normal = [float(v) for v in fila]
        largo = sum(v * v for v in normal) ** 0.5
        aparicion = suavizar(t * (filas + 1) - i)
        if largo == 0 or aparicion <= 0:
            continue
        unitaria, d = [v / largo for v in normal], float(bi) / largo
        vertices = plano_en_caja(unitaria, d, radio)
        if len(vertices) < 3:
            continue
        medio = tuple(sum(p[k] for p in vertices) / len(vertices) for k in range(3))
        vertices = [tuple(medio[k] + (p[k] - medio[k]) * aparicion for k in range(3)) for p in vertices]
        piezas.append((vertices, len(planos)))
        planos.append((unitaria, d))
        colores.append(SERIES[i % len(SERIES)])
    ojo = camara.posicion()
    for vertices, indice in ordenar_superficies(piezas, planos, ojo):
        normal, d = planos[indice]
        # Cada cara del plano recibe una luz distinta: así se distingue por qué lado se está mirando.
        luz = abs(normal[0] * 0.35 - normal[1] * 0.55 + normal[2] * 0.76)
        tono = 0.42 + 0.3 * luz + (0.12 if _distancia_con_signo(normal, d, ojo) > 0 else 0.0)
        relleno = mezclar_colores(TEMA["fondo"], colores[indice], tono)
        puntos = [camara.proyectar(p)[:2] for p in vertices]
        escena.append(poligono(puntos, relleno, mezclar_colores(relleno, "#FFFFFF", 0.45), 1.2))
    escena.extend(_ejes_3d(camara, radio))
    for i, (fila, bi) in enumerate(zip(A, b)):
        escena.append(texto(14, 18 + 18 * i, _ecuacion(fila, bi, ("x1", "x2", "x3")), SERIES[i % len(SERIES)], 12, True, "w"))
    if solucion and t > 0.8:
        px, py, _ = camara.proyectar(centro)
        escena.append(circulo(px, py, 11, mezclar_colores(TEMA["fondo"], TEMA["texto"], 0.3)))
        escena.append(circulo(px, py, 7, TEMA["texto"], TEMA["fondo"], 2))
        escena.append(texto(px + 13, py - 13, "x = (" + ", ".join(formatear_real(v, 4) for v in centro) + ")", TEMA["texto"], 13, True, "sw"))
    return escena


def _trayecto_combinacion(coeficientes, vectores, t):
    """Calcula los puntos de la cadena c₁v₁, c₁v₁ + c₂v₂, …, avanzando con t.

    Entrada: coeficientes, vectores y t entre 0 y 1. Salida: lista de (inicio, fin, índice).
    """
    dimension = len(vectores[0])
    actual = [0.0] * dimension
    trayecto = []
    n = len(vectores)
    for i, (c, v) in enumerate(zip(coeficientes, vectores)):
        avance = suavizar(t * (n + 0.5) - i)
        if avance <= 0:
            break
        siguiente = [actual[k] + float(c) * float(v[k]) * avance for k in range(dimension)]
        trayecto.append((list(actual), siguiente, i))
        actual = siguiente
    return trayecto


def escena_combinacion(coeficientes, vectores, w, t, giro, inclinacion, ancho, alto):
    """Anima la combinación lineal: cada cᵢvᵢ se coloca a continuación del anterior hasta llegar a w.

    Entrada: coeficientes (o None), vectores, w, t, ángulos de cámara (para R³) y tamaño. Salida: lista de primitivas.
    """
    dimension = len(w)
    w = [float(v) for v in w]
    trayecto = _trayecto_combinacion(coeficientes, vectores, t) if coeficientes else []
    puntos = [w, *[[float(u) for u in v] for v in vectores]]
    for inicio, fin, _ in _trayecto_combinacion(coeficientes, vectores, 1.0) if coeficientes else []:
        puntos.extend((inicio, fin))
    radio = max(2.0, max(abs(c) for p in puntos for c in p) * 1.2)
    if dimension == 2:
        vista = vista_cuadrada(radio, radio, ancho, alto)
        escena = escena_ejes(vista)
        convertir = lambda p: vista.a_pixel(p[0], p[1])
    else:
        camara = _camara_para_caja(giro, inclinacion, radio, ancho, alto)
        escena = [rectangulo(0, 0, ancho, alto, TEMA["fondo"])]
        escena.extend(_caja_3d(camara, radio))
        escena.extend(_ejes_3d(camara, radio))
        convertir = lambda p: camara.proyectar(p)[:2]
    origen = convertir([0.0] * dimension)
    for i, v in enumerate(vectores):
        destino = convertir([float(u) for u in v])
        color = mezclar_colores(TEMA["fondo"], SERIES[i % len(SERIES)], 0.55)
        escena.extend(flecha(origen[0], origen[1], destino[0], destino[1], color, 2, 9))
        escena.append(texto(destino[0] + 6, destino[1] - 6, f"v{i + 1}", color, 11, True, "sw"))
    destino_w = convertir(w)
    escena.extend(flecha(origen[0], origen[1], destino_w[0], destino_w[1], TEMA["texto"], 3, 12))
    escena.append(texto(destino_w[0] + 8, destino_w[1] - 8, "w", TEMA["texto"], 14, True, "sw"))
    for inicio, fin, i in trayecto:
        p, q = convertir(inicio), convertir(fin)
        escena.extend(flecha(p[0], p[1], q[0], q[1], SERIES[i % len(SERIES)], 3.5, 12))
        escena.append(texto((p[0] + q[0]) / 2 + 8, (p[1] + q[1]) / 2 - 8, f"{formatear_real(float(coeficientes[i]), 4)}·v{i + 1}", SERIES[i % len(SERIES)], 12, True, "sw"))
    if coeficientes is None:
        escena.append(texto(ancho / 2, alto - 18, "w no es combinación lineal de estos vectores.", TEMA["error"], 13, True))
    return escena


def escena_mapa_calor(matrices, ancho):
    """Renderiza matrices como mapas de calor: el color muestra el tamaño y el signo de cada entrada.

    Entrada: lista de (nombre, matriz de números) y ancho. Salida: (primitivas, alto natural).
    """
    columnas_total = sum(len(M[0]) for _, M in matrices)
    separacion = 34
    celda = min(46.0, (ancho - 24 - separacion * (len(matrices) - 1)) / max(1, columnas_total))
    filas_max = max(len(M) for _, M in matrices)
    alto = int(filas_max * celda + 44)
    escena = [rectangulo(0, 0, ancho, alto, TEMA["fondo"])]
    maximo = max((abs(float(v)) for _, M in matrices for fila in M for v in fila), default=1.0) or 1.0
    x = 12.0
    for nombre, M in matrices:
        escena.append(texto(x, 14, nombre, TEMA["texto"], 13, True, "w"))
        for i, fila in enumerate(M):
            for j, v in enumerate(fila):
                numero = float(v)
                intensidad = (abs(numero) / maximo) ** 0.5
                color = TEMA["primario"] if numero >= 0 else TEMA["rosa"]
                relleno = mezclar_colores(TEMA["fondo"], color, 0.08 + 0.8 * intensidad)
                x1, y1 = x + j * celda, 28 + i * celda
                escena.append(rectangulo(x1 + 1, y1 + 1, x1 + celda - 1, y1 + celda - 1, relleno))
                if celda >= 24:
                    escena.append(texto(x1 + celda / 2, y1 + celda / 2, formatear_real(numero, 3), TEMA["texto"], max(8, int(celda * 0.26)), mono=True))
        x += len(M[0]) * celda + separacion
    return escena, alto

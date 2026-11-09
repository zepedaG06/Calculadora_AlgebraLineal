"""Métodos Numéricos: bisección, graficador, notación posicional (base 10 y base 2) y errores numéricos.

Propósito: aplicar algoritmos numéricos, interpretar cómo la computadora representa los números y analizar cómo
los errores afectan la precisión; cada informe explica el procedimiento y lo verifica de forma independiente.
Unidad: Álgebra Lineal (MTM0120), Programa 7: módulo de Métodos Numéricos.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
Notas: funciones puras (sin input() ni print()) y sin el módulo math: seno, exponencial, logaritmo y demás
funciones se calculan con series de Taylor propias.
"""
import re
import struct
from fractions import Fraction

from .modulo_matrices import convertir_numero
from .pasos import condicion, etapa

PI = 3.141592653589793
E = 2.718281828459045
_MEDIO_PI = 1.5707963267948966
_MEDIO_PI_A = 1.5707963267341256
_MEDIO_PI_B = 6.077100506506192e-11
_LN2_A = 0.6931471803691238
_LN2_B = 1.9082149292705877e-10
_LN2 = 0.6931471805599453
_LN10 = 2.302585092994046
_RAIZ_DE_2 = 1.4142135623730951
_SUPERINDICES = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
LIMITE_ITERACIONES = 200
LIMITE_DIGITOS = 64
LIMITE_BITS_FRACCION = 32
LIMITE_MAGNITUD = 1e150


def formatear_real(valor, cifras=10):
    """Escribe un número real con las cifras significativas indicadas y potencia de 10 legible.

    Entrada: valor (número o None) y cifras. Salida: cadena; 'no definido' si el valor es None.
    """
    if valor is None:
        return "no definido"
    try:
        numero = float(valor)
    except OverflowError:
        return decimal_exacto(valor, cifras)
    if numero == 0:
        return "0"
    texto = format(numero, f".{cifras}g")
    if "e" not in texto:
        return texto
    mantisa, exponente = texto.split("e")
    return f"{mantisa}×10{str(int(exponente)).translate(_SUPERINDICES)}"


def orden_decimal(valor):
    """Calcula k tal que 10^k ≤ |valor| < 10^(k+1), con aritmética exacta.

    Entrada: valor (Fraction distinto de 0). Salida: entero k.
    """
    positivo = abs(Fraction(valor))
    k = len(str(positivo.numerator)) - len(str(positivo.denominator))
    while Fraction(10) ** k > positivo:
        k -= 1
    while Fraction(10) ** (k + 1) <= positivo:
        k += 1
    return k


def decimal_exacto(valor, significativas=40):
    """Escribe una fracción en decimal por división larga; si no termina, corta e indica con «…».

    Entrada: valor (Fraction) y cifras significativas máximas. Salida: cadena con el desarrollo decimal.
    """
    valor = Fraction(valor)
    if valor == 0:
        return "0"
    signo = "-" if valor < 0 else ""
    positivo = abs(valor)
    k = orden_decimal(positivo)
    if k < -8 or k > 40:
        positivo /= Fraction(10) ** k
    entero, resto = divmod(positivo.numerator, positivo.denominator)
    cifras = []
    usadas = len(str(entero)) if entero else 0
    while resto and usadas < significativas:
        resto *= 10
        digito, resto = divmod(resto, positivo.denominator)
        cifras.append(str(digito))
        if usadas or digito:
            usadas += 1
    texto = f"{signo}{entero}" + ("." + "".join(cifras) if cifras else "") + ("…" if resto else "")
    return f"{texto}×10{str(k).translate(_SUPERINDICES)}" if k < -8 or k > 40 else texto


def _exigir_finito(x):
    """Rechaza infinito y NaN antes de aplicar una serie.

    Entrada: x. Salida: x como float; lanza ValueError si no es finito.
    """
    x = float(x)
    if x != x or x in (float("inf"), float("-inf")):
        raise ValueError("El argumento no es un número finito.")
    return x


def _serie_seno(r):
    """Suma la serie de Taylor de sen(r) para |r| ≤ π/4.

    Entrada: r. Salida: aproximación de sen(r).
    """
    cuadrado, termino, suma = r * r, r, r
    for k in range(1, 10):
        termino *= -cuadrado / (2 * k * (2 * k + 1))
        suma += termino
    return suma


def _serie_coseno(r):
    """Suma la serie de Taylor de cos(r) para |r| ≤ π/4.

    Entrada: r. Salida: aproximación de cos(r).
    """
    cuadrado, termino, suma = r * r, 1.0, 1.0
    for k in range(1, 10):
        termino *= -cuadrado / ((2 * k - 1) * 2 * k)
        suma += termino
    return suma


def _reducir_angulo(x):
    """Reduce x a r ∈ [−π/4, π/4] y al cuadrante n, restando π/2 en dos partes para no perder cifras.

    Entrada: x. Salida: (r, n módulo 4).
    """
    x = _exigir_finito(x)
    n = round(x / _MEDIO_PI)
    return (x - n * _MEDIO_PI_A) - n * _MEDIO_PI_B, n % 4


def seno(x):
    """Calcula sen(x) con serie de Taylor tras reducir el ángulo.

    Entrada: x en radianes. Salida: float.
    """
    r, cuadrante = _reducir_angulo(x)
    return (_serie_seno(r), _serie_coseno(r), -_serie_seno(r), -_serie_coseno(r))[cuadrante]


def coseno(x):
    """Calcula cos(x) con serie de Taylor tras reducir el ángulo.

    Entrada: x en radianes. Salida: float.
    """
    r, cuadrante = _reducir_angulo(x)
    return (_serie_coseno(r), -_serie_seno(r), -_serie_coseno(r), _serie_seno(r))[cuadrante]


def tangente(x):
    """Calcula tan(x) = sen(x)/cos(x).

    Entrada: x en radianes. Salida: float; lanza ZeroDivisionError si cos(x) = 0.
    """
    return seno(x) / coseno(x)


def exponencial(x):
    """Calcula e^x: escribe x = k·ln2 + r para que la serie de Taylor de e^r converja rápido.

    Entrada: x. Salida: float; lanza OverflowError si el resultado excede el mayor número representable.
    """
    x = _exigir_finito(x)
    if x > 709.782712893384:
        raise OverflowError("e^x excede el mayor número representable.")
    if x < -745.2:
        return 0.0
    k = round(x / _LN2)
    r = (x - k * _LN2_A) - k * _LN2_B
    termino, suma = 1.0, 1.0
    for n in range(1, 15):
        termino *= r / n
        suma += termino
    # Se multiplica en dos pasos porque 2.0**1024 ya desborda aunque el producto final sí sea representable.
    return suma * 2.0 ** (k - 1) * 2.0 if k > 0 else suma * 2.0 ** k


def logaritmo_natural(x):
    """Calcula ln(x): escribe x = m·2^e con m cercano a 1 y suma la serie de 2·atanh((m−1)/(m+1)).

    Entrada: x > 0. Salida: float; lanza ValueError si x ≤ 0.
    """
    x = _exigir_finito(x)
    if x <= 0:
        raise ValueError("El logaritmo solo está definido para x > 0.")
    numerador, denominador = x.as_integer_ratio()
    exponente = numerador.bit_length() - denominador.bit_length()
    mantisa = x / 2.0 ** exponente
    if mantisa > _RAIZ_DE_2:
        mantisa, exponente = mantisa / 2, exponente + 1
    elif mantisa < 1 / _RAIZ_DE_2:
        mantisa, exponente = mantisa * 2, exponente - 1
    z = (mantisa - 1) / (mantisa + 1)
    cuadrado, potencia_z, suma = z * z, z, z
    for k in range(1, 13):
        potencia_z *= cuadrado
        suma += potencia_z / (2 * k + 1)
    return 2 * suma + exponente * _LN2


def logaritmo_10(x):
    """Calcula log₁₀(x) = ln(x) / ln(10).

    Entrada: x > 0. Salida: float; lanza ValueError si x ≤ 0.
    """
    return logaritmo_natural(x) / _LN10


def raiz_cuadrada(x):
    """Calcula √x como x^(1/2).

    Entrada: x ≥ 0. Salida: float; lanza ValueError si x < 0.
    """
    if x < 0:
        raise ValueError("La raíz cuadrada solo está definida para x ≥ 0.")
    return float(x) ** 0.5


def arcotangente(x):
    """Calcula atan(x): reduce el argumento con ángulos mitad y suma la serie de Taylor.

    Entrada: x. Salida: ángulo en radianes.
    """
    if x < 0:
        return -arcotangente(-x)
    if x > 1:
        return _MEDIO_PI - arcotangente(1 / x)
    y = x / (1 + (1 + x * x) ** 0.5)
    y = y / (1 + (1 + y * y) ** 0.5)
    cuadrado, potencia_y, suma = y * y, y, y
    for k in range(1, 12):
        potencia_y *= -cuadrado
        suma += potencia_y / (2 * k + 1)
    return 4 * suma


def arcoseno(x):
    """Calcula asen(x) = atan(x / √(1 − x²)).

    Entrada: x en [−1, 1]. Salida: ángulo en radianes; lanza ValueError fuera del dominio.
    """
    if abs(x) > 1:
        raise ValueError("arcsen solo está definido en [−1, 1].")
    if abs(x) == 1:
        return _MEDIO_PI if x > 0 else -_MEDIO_PI
    return arcotangente(x / ((1 - x) * (1 + x)) ** 0.5)


def arcocoseno(x):
    """Calcula acos(x) = π/2 − asen(x).

    Entrada: x en [−1, 1]. Salida: ángulo en radianes; lanza ValueError fuera del dominio.
    """
    return _MEDIO_PI - arcoseno(x)


def seno_hiperbolico(x):
    """Calcula senh(x) = (e^x − e^(−x)) / 2.

    Entrada: x. Salida: float.
    """
    return (exponencial(x) - exponencial(-x)) / 2


def coseno_hiperbolico(x):
    """Calcula cosh(x) = (e^x + e^(−x)) / 2.

    Entrada: x. Salida: float.
    """
    return (exponencial(x) + exponencial(-x)) / 2


def tangente_hiperbolica(x):
    """Calcula tanh(x) = senh(x) / cosh(x); para |x| grande vale ±1.

    Entrada: x. Salida: float.
    """
    if abs(x) > 20:
        return 1.0 if x > 0 else -1.0
    return seno_hiperbolico(x) / coseno_hiperbolico(x)


def _potencia(base, exponente):
    """Calcula base^exponente solo cuando el resultado es real.

    Entrada: base y exponente. Salida: float; lanza ValueError o ZeroDivisionError si no está definido en ℝ.
    """
    if base == 0 and exponente < 0:
        raise ZeroDivisionError("0 elevado a un exponente negativo.")
    if base < 0 and exponente != int(exponente):
        raise ValueError("Una base negativa con exponente no entero no es un número real.")
    return float(base) ** exponente


FUNCIONES = {
    "sin": seno, "sen": seno, "seno": seno, "cos": coseno, "coseno": coseno, "tan": tangente, "tg": tangente,
    "exp": exponencial, "ln": logaritmo_natural, "log": logaritmo_10, "log10": logaritmo_10,
    "sqrt": raiz_cuadrada, "raiz": raiz_cuadrada, "√": raiz_cuadrada, "abs": abs,
    "asin": arcoseno, "arcsin": arcoseno, "arcsen": arcoseno, "asen": arcoseno,
    "acos": arcocoseno, "arccos": arcocoseno, "atan": arcotangente, "arctan": arcotangente,
    "sinh": seno_hiperbolico, "senh": seno_hiperbolico, "cosh": coseno_hiperbolico, "tanh": tangente_hiperbolica,
}
CONSTANTES = {"pi": PI, "π": PI, "e": E}
_NOMBRES = sorted([*FUNCIONES, *CONSTANTES, "x"], key=len, reverse=True)
_PATRON_NUMERO = re.compile(r"(\d+([.,]\d*)?|[.,]\d+)([eE][+-]?\d+)?")
_REEMPLAZOS = str.maketrans({"−": "-", "–": "-", "·": "*", "×": "*", "÷": "/", "²": "^2", "³": "^3", "[": "(", "]": ")"})


class ErrorFuncion(ValueError):
    """Error de escritura en una función; guarda la posición del carácter que lo causó."""

    def __init__(self, mensaje, posicion=None):
        """Guarda el mensaje y la posición.

        Entrada: mensaje y posición del carácter (o None). Salida: None.
        """
        super().__init__(mensaje)
        self.posicion = posicion


def _tokenizar(texto):
    """Divide la expresión en números, nombres, operadores y paréntesis.

    Entrada: texto ya normalizado. Salida: lista de (tipo, valor, posición); lanza ErrorFuncion si hay símbolos inválidos.
    """
    simbolos, i = [], 0
    while i < len(texto):
        caracter = texto[i]
        if caracter.isspace():
            i += 1
            continue
        coincidencia = _PATRON_NUMERO.match(texto, i)
        if coincidencia:
            simbolos.append(("numero", float(coincidencia.group().replace(",", ".")), i))
            i = coincidencia.end()
            if i < len(texto) and texto[i] in ".,":
                raise ErrorFuncion(f"El número de la posición {simbolos[-1][2] + 1} tiene más de un separador decimal.", i)
            continue
        if caracter in "+-*/^()":
            simbolos.append((caracter, caracter, i))
            i += 1
            continue
        nombre = next((n for n in _NOMBRES if texto.startswith(n, i)), None)
        if nombre is None:
            raise ErrorFuncion(f"«{caracter}» no es válido en la posición {i + 1}: la variable es x y las funciones "
                               "son sen, cos, tan, exp, ln, log, sqrt, abs, asen, acos, atan, senh, cosh y tanh.", i)
        tipo = "variable" if nombre == "x" else "funcion" if nombre in FUNCIONES else "constante"
        simbolos.append((tipo, nombre, i))
        i += len(nombre)
    return simbolos


class _Analizador:
    """Analizador descendente de funciones reales; convierte el texto en funciones de Python ya compuestas.

    Gramática: suma → producto → unario → potencia → primario; el producto también se reconoce sin signo (2x).
    """

    def __init__(self, simbolos, longitud):
        """Prepara la lectura de los símbolos.

        Entrada: lista de símbolos y longitud del texto. Salida: None.
        """
        self.simbolos = simbolos
        self.indice = 0
        self.longitud = longitud
        self.usa_x = False

    def _tipo(self):
        """Obtiene el tipo del símbolo actual sin avanzar.

        Salida: tipo, o None al final.
        """
        return self.simbolos[self.indice][0] if self.indice < len(self.simbolos) else None

    def _posicion(self):
        """Obtiene la posición del símbolo actual para los mensajes de error.

        Salida: índice del carácter.
        """
        return self.simbolos[self.indice][2] if self.indice < len(self.simbolos) else self.longitud

    def analizar(self):
        """Analiza toda la expresión y exige que no sobren símbolos.

        Salida: función de Python de una variable; lanza ErrorFuncion si la escritura es inválida.
        """
        resultado = self._suma()
        if self.indice < len(self.simbolos):
            raise ErrorFuncion(f"Sobra «{self.simbolos[self.indice][1]}» en la posición {self._posicion() + 1}.",
                               self._posicion())
        return resultado

    def _suma(self):
        """Regla suma := producto (('+' | '-') producto)*.

        Salida: función compuesta.
        """
        izquierda = self._producto()
        while self._tipo() in ("+", "-"):
            operador = self.simbolos[self.indice][0]
            self.indice += 1
            derecha = self._producto()
            if operador == "+":
                izquierda = lambda x, a=izquierda, b=derecha: a(x) + b(x)
            else:
                izquierda = lambda x, a=izquierda, b=derecha: a(x) - b(x)
        return izquierda

    def _producto(self):
        """Regla producto := unario (('*' | '/' | yuxtaposición) unario)*.

        Salida: función compuesta.
        """
        izquierda = self._unario()
        while self._tipo() in ("*", "/", "numero", "variable", "constante", "funcion", "("):
            operador = self.simbolos[self.indice][0]
            if operador in ("*", "/"):
                self.indice += 1
            derecha = self._unario()
            if operador == "/":
                izquierda = lambda x, a=izquierda, b=derecha: a(x) / b(x)
            else:
                izquierda = lambda x, a=izquierda, b=derecha: a(x) * b(x)
        return izquierda

    def _unario(self):
        """Regla unario := ('+' | '-') unario | potencia; por eso −x² significa −(x²).

        Salida: función compuesta.
        """
        if self._tipo() == "-":
            self.indice += 1
            interno = self._unario()
            return lambda x, a=interno: -a(x)
        if self._tipo() == "+":
            self.indice += 1
            return self._unario()
        return self._potencia()

    def _potencia(self):
        """Regla potencia := primario ('^' unario)?, asociativa por la derecha.

        Salida: función compuesta.
        """
        base = self._primario()
        if self._tipo() == "^":
            self.indice += 1
            exponente = self._unario()
            return lambda x, a=base, b=exponente: _potencia(a(x), b(x))
        return base

    def _primario(self):
        """Regla primario := número | x | constante | función '(' suma ')' | '(' suma ')'.

        Salida: función compuesta; lanza ErrorFuncion si falta un operando o un paréntesis.
        """
        tipo = self._tipo()
        if tipo is None:
            raise ErrorFuncion("La expresión está incompleta: falta un valor al final.", self.longitud)
        _tipo, valor, posicion = self.simbolos[self.indice]
        self.indice += 1
        if tipo == "numero":
            return lambda _x, v=valor: v
        if tipo == "constante":
            return lambda _x, v=CONSTANTES[valor]: v
        if tipo == "variable":
            self.usa_x = True
            return lambda x: x
        if tipo == "funcion":
            if self._tipo() != "(":
                raise ErrorFuncion(f"La función {valor} necesita paréntesis, por ejemplo {valor}(x).", posicion)
            self.indice += 1
            interno = self._suma()
            self._cerrar(posicion)
            return lambda x, f=FUNCIONES[valor], a=interno: f(a(x))
        if tipo == "(":
            interno = self._suma()
            self._cerrar(posicion)
            return interno
        raise ErrorFuncion(f"Falta un valor antes de «{valor}» en la posición {posicion + 1}.", posicion)

    def _cerrar(self, posicion):
        """Exige el paréntesis que cierra el abierto en la posición indicada.

        Entrada: posición del paréntesis abierto. Salida: None; lanza ErrorFuncion si falta.
        """
        if self._tipo() != ")":
            raise ErrorFuncion(f"Falta cerrar el paréntesis abierto en la posición {posicion + 1}.", posicion)
        self.indice += 1


class FuncionReal:
    """Función real de una variable escrita como texto, por ejemplo x^3 − x − 2 o 2sen(x) + e^x."""

    def __init__(self, texto):
        """Analiza el texto y deja lista la función para evaluarla.

        Entrada: texto. Salida: None; lanza ErrorFuncion si no se puede interpretar.
        """
        self.texto = " ".join(str(texto).split())
        normalizado = self.texto.lower().replace("**", "^").translate(_REEMPLAZOS)
        if not normalizado:
            raise ErrorFuncion("Escribe una función de x, por ejemplo x^3 - x - 2.", 0)
        if len(normalizado) > 200:
            raise ErrorFuncion("La función es demasiado larga: usa como máximo 200 caracteres.")
        analizador = _Analizador(_tokenizar(normalizado), len(normalizado))
        try:
            self._calcular = analizador.analizar()
        except RecursionError:
            raise ErrorFuncion("La función tiene demasiados paréntesis anidados.") from None
        self.usa_x = analizador.usa_x

    def evaluar(self, x):
        """Evalúa la función en x; los puntos fuera del dominio se informan con None.

        Entrada: x. Salida: float finito o None si f(x) no está definida.
        """
        try:
            y = float(self._calcular(float(x)))
        except (ZeroDivisionError, ValueError, OverflowError, TypeError):
            return None
        return None if y != y or y in (float("inf"), float("-inf")) else y


def leer_real(texto, nombre="valor"):
    """Lee un número real escrito como número o expresión sin x (por ejemplo 3/2, pi/4 o sqrt(2)).

    Entrada: texto y nombre para los mensajes. Salida: float; lanza ValueError si no es un número definido.
    """
    try:
        funcion = FuncionReal(texto)
    except ErrorFuncion as error:
        raise ValueError(f"{nombre}: {error}") from None
    if funcion.usa_x:
        raise ValueError(f"{nombre} debe ser un número o una expresión sin x.")
    valor = funcion.evaluar(0.0)
    if valor is None:
        raise ValueError(f"{nombre} no está definido.")
    return valor


def leer_exacto(texto, nombre="valor"):
    """Lee un número como fracción exacta; si es una expresión (pi, sqrt(2)) usa su valor en doble precisión.

    Entrada: texto y nombre para los mensajes. Salida: (Fraction, es_exacto); lanza ValueError si no es válido.
    """
    try:
        return convertir_numero(str(texto)), True
    except ValueError:
        return Fraction(leer_real(texto, nombre)), False


def _funcion(funcion):
    """Acepta una función ya analizada o su texto.

    Entrada: FuncionReal o texto. Salida: FuncionReal.
    """
    return funcion if isinstance(funcion, FuncionReal) else FuncionReal(funcion)


def _signo(y):
    """Obtiene el signo de un número sin multiplicarlo, para evitar que el producto f(a)·f(c) se vuelva 0.

    Entrada: y. Salida: −1, 0 o 1.
    """
    return (y > 0) - (y < 0)


def _hay_salto(funcion, x1, y1, x2, y2, umbral):
    """Decide si entre dos muestras hay una discontinuidad, acercándose al mayor cambio de f.

    Entrada: función, dos puntos y umbral de cambio. Salida: True si el salto no disminuye al acercarse.
    """
    if abs(y2 - y1) <= umbral:
        return False
    salto_inicial = abs(y2 - y1)
    for _ in range(14):
        medio = (x1 + x2) / 2
        y_medio = funcion.evaluar(medio)
        if y_medio is None:
            return True
        if abs(y_medio - y1) >= abs(y2 - y_medio):
            x2, y2 = medio, y_medio
        else:
            x1, y1 = medio, y_medio
    # En una función continua el cambio se reduce a la mitad con cada corte; en un salto no se reduce.
    return abs(y2 - y1) > 0.25 * salto_inicial


def rango_automatico(valores):
    """Elige el rango vertical con percentiles para que un polo (como 1/x) no aplaste el resto de la curva.

    Entrada: valores de y (sin None). Salida: (y_min, y_max) con un margen del 8 %.
    """
    ordenados = sorted(v for v in valores if abs(v) <= LIMITE_MAGNITUD)
    if not ordenados:
        return -1.0, 1.0
    n = len(ordenados)
    bajo, alto = ordenados[int(0.02 * (n - 1))], ordenados[int(0.98 * (n - 1))]
    if ordenados[-1] - ordenados[0] <= 3 * (alto - bajo):
        bajo, alto = ordenados[0], ordenados[-1]
    if alto - bajo < 1e-12:
        holgura = max(1.0, abs(alto) * 0.5)
        return bajo - holgura, alto + holgura
    margen = (alto - bajo) * 0.08
    return bajo - margen, alto + margen


def muestrear_funcion(funcion, x_min, x_max, puntos=400, umbral=None):
    """Evalúa la función en puntos equiespaciados y separa los tramos en huecos del dominio y en saltos.

    Entrada: función, intervalo, cantidad de subintervalos y umbral de salto (None: automático).
    Salida: diccionario con «tramos» (listas de (x, y)), «saltos» y «huecos» (abscisas).
    """
    funcion = _funcion(funcion)
    muestras = [(x_min + (x_max - x_min) * i / puntos,) for i in range(puntos + 1)]
    muestras = [(x[0], funcion.evaluar(x[0])) for x in muestras]
    if umbral is None:
        y_min, y_max = rango_automatico([y for _, y in muestras if y is not None])
        umbral = (y_max - y_min) * 0.3
    tramos, actual, saltos, huecos, previo = [], [], [], [], None
    for x, y in muestras:
        if y is None:
            if actual:
                tramos.append(actual)
                huecos.append(x)
            actual, previo = [], None
            continue
        if previo is not None and _hay_salto(funcion, previo[0], previo[1], x, y, umbral):
            tramos.append(actual)
            saltos.append((previo[0] + x) / 2)
            actual = []
        actual.append((x, y))
        previo = (x, y)
    if actual:
        tramos.append(actual)
    return {"tramos": tramos, "saltos": saltos, "huecos": huecos}


def _raiz_en(funcion, p, q, y_p, y_q):
    """Refina por bisección una raíz ya encerrada entre p y q.

    Entrada: función, extremos y sus valores. Salida: abscisa de la raíz.
    """
    for _ in range(70):
        medio = (p + q) / 2
        if medio in (p, q):
            break
        y_medio = funcion.evaluar(medio)
        if y_medio is None or y_medio == 0:
            return medio
        if _signo(y_p) * _signo(y_medio) < 0:
            q, y_q = medio, y_medio
        else:
            p, y_p = medio, y_medio
    return (p + q) / 2


def _extremo_en(funcion, p, q, es_maximo):
    """Refina un extremo local con búsqueda de sección áurea en [p, q].

    Entrada: función, intervalo y es_maximo (bool). Salida: (x, y) del extremo.
    """
    razon = 0.6180339887498949
    signo = -1.0 if es_maximo else 1.0

    def valor(x):
        """Evalúa la función con el signo que convierte el problema en una minimización.

        Entrada: x. Salida: número (infinito si f no está definida).
        """
        y = funcion.evaluar(x)
        return float("inf") if y is None else signo * y

    c, d = q - razon * (q - p), p + razon * (q - p)
    y_c, y_d = valor(c), valor(d)
    for _ in range(60):
        if y_c < y_d:
            q, d, y_d = d, c, y_c
            c = q - razon * (q - p)
            y_c = valor(c)
        else:
            p, c, y_c = c, d, y_d
            d = p + razon * (q - p)
            y_d = valor(d)
    x = (p + q) / 2
    return x, funcion.evaluar(x)


def analizar_funcion(funcion, x_min, x_max, puntos=800):
    """Encuentra ceros, extremos locales, discontinuidades y el corte con el eje y en el intervalo.

    Entrada: función, intervalo y cantidad de subintervalos.
    Salida: diccionario con funcion, raices, maximos, minimos, saltos, huecos y corte_y.
    """
    funcion = _funcion(funcion)
    muestreo = muestrear_funcion(funcion, x_min, x_max, puntos)
    raices, maximos, minimos = [], [], []
    tolerancia_x = (x_max - x_min) / puntos * 1e-3
    for tramo in muestreo["tramos"]:
        for (x1, y1), (x2, y2) in zip(tramo, tramo[1:]):
            if y1 == 0:
                raices.append(x1)
            elif _signo(y1) * _signo(y2) < 0:
                raices.append(_raiz_en(funcion, x1, x2, y1, y2))
        if tramo and tramo[-1][1] == 0:
            raices.append(tramo[-1][0])
        for (x0, y0), (x1, y1), (x2, y2) in zip(tramo, tramo[1:], tramo[2:]):
            if y1 > y0 and y1 >= y2:
                maximos.append(_extremo_en(funcion, x0, x2, True))
            elif y1 < y0 and y1 <= y2:
                minimos.append(_extremo_en(funcion, x0, x2, False))
    # Una raíz doble (x² en 0) no cambia de signo: se reconoce porque un extremo local vale prácticamente 0.
    for x, y in maximos + minimos:
        if y is not None and abs(y) < 1e-9 and all(abs(x - r) > 1e-6 for r in raices):
            raices.append(x)
    raices = sorted(raices)
    unicas = [r for i, r in enumerate(raices) if i == 0 or r - raices[i - 1] > tolerancia_x]
    return {"funcion": funcion, "raices": unicas, "maximos": maximos, "minimos": minimos,
            "saltos": muestreo["saltos"], "huecos": muestreo["huecos"],
            "corte_y": funcion.evaluar(0.0) if x_min <= 0 <= x_max else None}


def _buscar_cambio_de_signo(funcion, a, b, puntos=400):
    """Busca un subintervalo con cambio de signo y sin saltos, para sugerirlo cuando Bolzano no se cumple.

    Entrada: función, intervalo y cantidad de subintervalos. Salida: (p, q) o None.
    """
    for tramo in muestrear_funcion(funcion, a, b, puntos)["tramos"]:
        for (x1, y1), (x2, y2) in zip(tramo, tramo[1:]):
            if _signo(y1) * _signo(y2) < 0:
                return x1, x2
    return None


def _iteraciones_teoricas(ancho, tolerancia):
    """Calcula el menor n con (b − a)/2ⁿ ≤ tol, es decir, n ≥ log₂((b − a)/tol).

    Entrada: ancho del intervalo y tolerancia. Salida: entero n ≥ 1.
    """
    n = 1
    ancho /= 2
    while ancho > tolerancia:
        ancho /= 2
        n += 1
    return n


def _informe_no_definido(titulo, motivo, etapas):
    """Construye el informe de una operación que no se puede realizar.

    Entrada: título, motivo y etapas ya calculadas. Salida: diccionario de informe.
    """
    return {"definido": False, "titulo": titulo, "conclusion": motivo, "motivo": motivo, "procedimiento": etapas,
            "verificacion": {"aplicable": False, "correcto": False, "motivo": motivo, "etapas": etapas}}


def biseccion(funcion, a, b, tolerancia=1e-6, max_iteraciones=100):
    """Aplica el método de bisección y registra cada iteración, su decisión y su cota de error.

    Entrada: función (texto o FuncionReal), intervalo [a, b], tolerancia > 0 y máximo de iteraciones.
    Salida: informe con raiz, iteraciones, procedimiento y verificacion; lanza ValueError si los datos son inválidos.
    """
    funcion = _funcion(funcion)
    a, b, tolerancia = float(a), float(b), float(tolerancia)
    if not a < b:
        raise ValueError(f"El intervalo debe cumplir a < b; se recibió a = {formatear_real(a)} y b = {formatear_real(b)}.")
    if max(abs(a), abs(b)) > LIMITE_MAGNITUD:
        raise ValueError("Los extremos deben estar entre −10¹⁵⁰ y 10¹⁵⁰: fuera de ese rango (a + b)/2 se desborda.")
    if tolerancia <= 0:
        raise ValueError("La tolerancia debe ser mayor que 0.")
    if not 1 <= int(max_iteraciones) <= LIMITE_ITERACIONES:
        raise ValueError(f"El máximo de iteraciones debe estar entre 1 y {LIMITE_ITERACIONES}.")
    max_iteraciones = int(max_iteraciones)
    a0, b0 = a, b
    fa, fb = funcion.evaluar(a), funcion.evaluar(b)
    datos = etapa("Datos del problema", "Se busca x con f(x) = 0 dentro del intervalo inicial.",
                  formula=f"f(x) = {funcion.texto}",
                  calculos=[f"a = {formatear_real(a)}", f"b = {formatear_real(b)}",
                            f"tolerancia = {formatear_real(tolerancia)}", f"máximo de iteraciones = {max_iteraciones}"])
    bolzano = etapa(
        "Teorema de Bolzano", "Si f es continua en [a, b] y f(a), f(b) tienen signos opuestos, hay al menos una raíz.",
        formula="f(a) · f(b) < 0",
        calculos=[f"f(a) = f({formatear_real(a)}) = {formatear_real(fa)}", f"f(b) = f({formatear_real(b)}) = {formatear_real(fb)}"],
        condiciones=[condicion("f está definida en ambos extremos.", fa is not None and fb is not None),
                     condicion("f(a) y f(b) tienen signos opuestos (o alguno vale 0).",
                               fa is not None and fb is not None and _signo(fa) * _signo(fb) <= 0)])
    if fa is None or fb is None:
        extremo = "a" if fa is None else "b"
        informe = _informe_no_definido("Bisección no aplicable", f"f no está definida en el extremo {extremo}.", [datos, bolzano])
        informe["funcion"], informe["a"], informe["b"], informe["sugerencia"] = funcion, a0, b0, None
        return informe
    if _signo(fa) * _signo(fb) > 0:
        sugerencia = _buscar_cambio_de_signo(funcion, a, b)
        motivo = (f"f(a) = {formatear_real(fa)} y f(b) = {formatear_real(fb)} tienen el mismo signo: "
                  "no se garantiza una raíz en este intervalo.")
        if sugerencia:
            motivo += f" Prueba con [{formatear_real(sugerencia[0], 6)}, {formatear_real(sugerencia[1], 6)}], donde f cambia de signo."
        informe = _informe_no_definido("Bisección no aplicable", motivo, [datos, bolzano])
        informe["funcion"], informe["a"], informe["b"], informe["sugerencia"] = funcion, a0, b0, sugerencia
        return informe

    teorico = _iteraciones_teoricas(b - a, tolerancia)
    etapas = [datos, bolzano, etapa(
        "Cantidad de iteraciones", "Cada iteración divide el intervalo a la mitad, así que el error se puede acotar antes de empezar.",
        formula="|c(n) − r| ≤ (b − a)/2ⁿ ≤ tol   ⇒   n ≥ log₂((b − a)/tol)",
        calculos=[f"log₂({formatear_real(b - a)} / {formatear_real(tolerancia)}) = "
                  f"{formatear_real((logaritmo_natural(b - a) - logaritmo_natural(tolerancia)) / _LN2, 6)}",
                  f"Se necesitan como máximo n = {teorico} iteraciones."])]
    iteraciones, raiz, f_raiz, motivo_paro, previo = [], None, None, "", None
    if fa == 0 or fb == 0:
        raiz, f_raiz = (a, fa) if fa == 0 else (b, fb)
        motivo_paro = f"El extremo {formatear_real(raiz)} ya es una raíz exacta: f = 0."
        etapas.append(etapa("Raíz en un extremo", motivo_paro))
    else:
        for n in range(1, max_iteraciones + 1):
            c = (a + b) / 2
            fc = funcion.evaluar(c)
            if fc is None:
                motivo = (f"f no está definida en c = {formatear_real(c)}: hay una discontinuidad dentro de [a, b] "
                          "y no se cumple la hipótesis de continuidad del teorema de Bolzano.")
                informe = _informe_no_definido("Bisección interrumpida", motivo, etapas + [etapa(f"Iteración {n}", motivo)])
                informe["funcion"], informe["a"], informe["b"], informe["sugerencia"] = funcion, a0, b0, None
                return informe
            cota = (b - a) / 2
            error_aproximado = abs(c - previo) if previo is not None else None
            error_relativo = error_aproximado / abs(c) if previo is not None and c != 0 else None
            if fc == 0:
                nuevo_a, nuevo_b, decision = c, c, "f(c) = 0: c es la raíz exacta."
                mitad = "exacta"
            elif _signo(fa) * _signo(fc) < 0:
                nuevo_a, nuevo_b, decision = a, c, "f(a) y f(c) tienen signos opuestos: la raíz está en [a, c], así que b ← c."
                mitad = "izquierda"
            else:
                nuevo_a, nuevo_b, decision = c, b, "f(c) y f(b) tienen signos opuestos: la raíz está en [c, b], así que a ← c."
                mitad = "derecha"
            iteraciones.append({"n": n, "a": a, "b": b, "c": c, "fa": fa, "fb": fb, "fc": fc, "cota_error": cota,
                                "error_aproximado": error_aproximado, "error_relativo": error_relativo,
                                "mitad": mitad, "nuevo_a": nuevo_a, "nuevo_b": nuevo_b})
            calculos = [f"c = (a + b)/2 = ({formatear_real(a)} + {formatear_real(b)})/2 = {formatear_real(c)}",
                        f"f(c) = {formatear_real(fc)}", f"Cota del error: (b − a)/2 = {formatear_real(cota)}"]
            if error_aproximado is not None:
                calculos.append(f"Error aproximado: |c(n) − c(n−1)| = {formatear_real(error_aproximado)}")
            etapas.append(etapa(f"Iteración {n}", decision, formula=f"[a, b] = [{formatear_real(a)}, {formatear_real(b)}]",
                                calculos=calculos))
            raiz, f_raiz, previo = c, fc, c
            if fc == 0:
                motivo_paro = "f(c) = 0: se encontró la raíz exacta."
                break
            if cota <= tolerancia:
                motivo_paro = f"La cota del error {formatear_real(cota)} ya es menor o igual que la tolerancia."
                break
            if c in (a, b) or (nuevo_a + nuevo_b) / 2 in (nuevo_a, nuevo_b):
                motivo_paro = "Se alcanzó la resolución de la máquina: el intervalo ya no se puede dividir."
                break
            a, b = nuevo_a, nuevo_b
            if nuevo_a == c:
                fa = fc
            else:
                fb = fc
        else:
            motivo_paro = f"Se alcanzó el máximo de {max_iteraciones} iteraciones antes de llegar a la tolerancia."

    advertencias = []
    alcanzo = not iteraciones or iteraciones[-1]["fc"] == 0 or iteraciones[-1]["cota_error"] <= tolerancia
    # 1/x cambia de signo en [−1, 2] sin tener raíz: se sigue dividiendo el último intervalo y solo hay raíz si f tiende a 0.
    es_raiz = f_raiz == 0
    if not es_raiz:
        limite = _raiz_en(funcion, a, b, fa, fb)
        residuo = funcion.evaluar(limite)
        escala = max(1.0, abs(funcion.evaluar(a0)), abs(funcion.evaluar(b0)))
        es_raiz = residuo is not None and abs(residuo) <= 1e-6 * escala
    if not es_raiz:
        advertencias.append(f"f no es continua cerca de x = {formatear_real(raiz, 8)}: el cambio de signo se debe a una "
                            "discontinuidad y este punto no es una raíz.")
    elif muestrear_funcion(funcion, a0, b0)["saltos"]:
        advertencias.append("f tiene discontinuidades en [a, b]: Bolzano no se aplica en todo el intervalo inicial.")
    if not alcanzo:
        advertencias.append(motivo_paro)
    titulo = f"Raíz aproximada: x ≈ {formatear_real(raiz)}" if es_raiz else "El cambio de signo no corresponde a una raíz"
    conclusion = (f"f({formatear_real(raiz)}) = {formatear_real(f_raiz)} en {len(iteraciones)} iteraciones. {motivo_paro}"
                  if es_raiz else advertencias[0])
    etapas.append(etapa("Criterio de paro y resultado", motivo_paro, formula=f"x ≈ {formatear_real(raiz, 14)}",
                        calculos=[f"f(x) = {formatear_real(f_raiz)}", f"Iteraciones realizadas: {len(iteraciones)} "
                                  f"(cota teórica: {teorico})"],
                        conclusion=conclusion if es_raiz else ""))
    informe = {"definido": True, "es_raiz": es_raiz, "funcion": funcion, "a": a0, "b": b0, "tolerancia": tolerancia,
               "max_iteraciones": max_iteraciones, "raiz": raiz, "f_raiz": f_raiz, "iteraciones": iteraciones,
               "n": len(iteraciones), "n_teorico": teorico, "alcanzo_tolerancia": alcanzo, "motivo_paro": motivo_paro,
               "advertencias": advertencias, "titulo": titulo, "conclusion": conclusion, "procedimiento": etapas}
    informe["verificacion"] = verificar_biseccion(informe)
    return informe


def verificar_biseccion(informe):
    """Comprueba la bisección recalculando f desde el texto original, sin usar los valores guardados.

    Entrada: informe de biseccion. Salida: diccionario con correcto, etapas y chequeos.
    """
    funcion = FuncionReal(informe["funcion"].texto)
    raiz, tolerancia, iteraciones = informe["raiz"], informe["tolerancia"], informe["iteraciones"]
    a0, b0 = informe["a"], informe["b"]
    chequeos = []

    def registrar(nombre, correcto):
        """Anota una comprobación con su resultado.

        Entrada: nombre y correcto (bool). Salida: None.
        """
        chequeos.append({"nombre": nombre, "correcto": bool(correcto)})

    recalculado = funcion.evaluar(raiz)
    registrar("Sustitución en f", recalculado == informe["f_raiz"])
    invariante = all(_signo(funcion.evaluar(it["a"])) * _signo(funcion.evaluar(it["b"])) <= 0 for it in iteraciones)
    registrar("Cambio de signo en cada intervalo", invariante)
    mitades = all(abs((it["b"] - it["a"]) - (b0 - a0) / 2 ** (it["n"] - 1)) <= 1e-9 * (b0 - a0) for it in iteraciones)
    registrar("El intervalo se divide a la mitad", mitades)
    promedios = all((it["a"] + it["b"]) / 2 == it["c"] for it in iteraciones)
    registrar("c es el punto medio", promedios)
    radio = iteraciones[-1]["cota_error"] if iteraciones else tolerancia
    izquierda, derecha = funcion.evaluar(raiz - radio), funcion.evaluar(raiz + radio)
    cambio = (informe["f_raiz"] == 0 or izquierda is None or derecha is None
              or _signo(izquierda) * _signo(derecha) <= 0)
    registrar("Cambio de signo alrededor de la raíz", cambio)
    cota = informe["alcanzo_tolerancia"] is False or not iteraciones or iteraciones[-1]["cota_error"] <= tolerancia or informe["f_raiz"] == 0
    registrar("Cota del error dentro de la tolerancia", cota)
    registrar("Iteraciones dentro de la cota teórica", informe["n"] <= informe["n_teorico"] + 1)
    registrar("x es una raíz y no una discontinuidad", informe["es_raiz"])
    correcto = all(c["correcto"] for c in chequeos)
    etapas = [
        etapa("Sustituir la raíz en la función original", "f se vuelve a interpretar desde su texto.",
              formula=f"f(x) = {funcion.texto}", calculos=[f"f({formatear_real(raiz, 14)}) = {formatear_real(recalculado)}"],
              condiciones=[condicion("Coincide con el valor del procedimiento.", recalculado == informe["f_raiz"])]),
        etapa("Cambio de signo alrededor de x", "La raíz está a menos de la cota del error δ, así que f debe cambiar de signo entre x − δ y x + δ.",
              calculos=[f"δ = {formatear_real(radio)}", f"f(x − δ) = {formatear_real(izquierda)}", f"f(x + δ) = {formatear_real(derecha)}"],
              condiciones=[condicion("f cambia de signo (o es 0).", cambio)]),
        etapa("Invariantes del método", "Se comprueban en todas las iteraciones.",
              condiciones=[condicion("f(a) y f(b) tienen signos opuestos en cada intervalo.", invariante),
                           condicion("Cada intervalo mide la mitad del anterior: (b − a) = (b₀ − a₀)/2ⁿ⁻¹.", mitades),
                           condicion("c es siempre el punto medio de [a, b].", promedios),
                           condicion(f"Iteraciones: {informe['n']} (cota teórica: {informe['n_teorico']}).",
                                     informe["n"] <= informe["n_teorico"] + 1)]),
        etapa("Interpretación", condiciones=[condicion("x es una raíz y no una discontinuidad de f.", informe["es_raiz"])],
              conclusion="Se cumple" if correcto else "No se cumple: revisa las condiciones marcadas con ✗."),
    ]
    return {"correcto": correcto, "etapas": etapas, "chequeos": chequeos}


def informe_graficador(textos, x_min, x_max):
    """Analiza hasta tres funciones en un intervalo y explica cómo se construye su gráfica.

    Entrada: textos de las funciones, x_min y x_max. Salida: informe con analisis, cortes, procedimiento y verificacion.
    """
    x_min, x_max = float(x_min), float(x_max)
    if not x_min < x_max:
        raise ValueError("El intervalo debe cumplir x mín < x máx.")
    if not 1e-10 < x_max - x_min < 1e12:
        raise ValueError("El ancho del intervalo debe estar entre 10⁻¹⁰ y 10¹².")
    textos = [t for t in textos if str(t).strip()]
    if not textos:
        raise ValueError("Escribe al menos una función de x.")
    if len(textos) > 3:
        raise ValueError("Se pueden graficar hasta 3 funciones a la vez.")
    funciones = [FuncionReal(t) for t in textos]
    analisis = [analizar_funcion(f, x_min, x_max) for f in funciones]
    cortes = []
    for i, f in enumerate(funciones):
        for j in range(i + 1, len(funciones)):
            g = funciones[j]
            diferencia = FuncionReal(f"({f.texto})-({g.texto})")
            for x in analizar_funcion(diferencia, x_min, x_max)["raices"]:
                y = f.evaluar(x)
                if y is not None:
                    cortes.append({"i": i, "j": j, "x": x, "y": y})
    nombres = "fgh"
    paso = (x_max - x_min) / 800
    etapas = [
        etapa("Interpretar la expresión", "El texto se convierte en una función evaluable respetando paréntesis y precedencia.",
              calculos=[f"{nombres[i]}(x) = {f.texto}" for i, f in enumerate(funciones)]),
        etapa("Muestrear el intervalo", "Se calculan puntos (x, f(x)) equiespaciados; por eso una gráfica es una aproximación.",
              formula="x(i) = x mín + i·Δx,  Δx = (x máx − x mín)/n",
              calculos=[f"x mín = {formatear_real(x_min)},  x máx = {formatear_real(x_max)}", "n = 800 subintervalos",
                        f"Δx = {formatear_real(paso)}"]),
    ]
    for i, datos in enumerate(analisis):
        muestras = [x_min + (x_max - x_min) * k / 5 for k in range(6)]
        etapas.append(etapa(f"Tabla de valores de {nombres[i]}",
                            calculos=[f"{nombres[i]}({formatear_real(x, 6)}) = {formatear_real(datos['funcion'].evaluar(x), 8)}" for x in muestras]))
    etapas.append(etapa("Convertir a píxeles", "Cada punto se traslada a la pantalla con una regla de tres; el eje y se invierte porque la pantalla crece hacia abajo.",
                        formula="pₓ = (x − x mín)/(x máx − x mín)·ancho;   p_y = (y máx − y)/(y máx − y mín)·alto"))
    etapas.append(etapa("Separar tramos", "Dos puntos consecutivos no se unen si entre ellos f no está definida o si el salto no se reduce al acercarse: así no se dibujan líneas falsas en una asíntota."))
    for i, datos in enumerate(analisis):
        calculos = [f"Ceros: {', '.join(formatear_real(r, 8) for r in datos['raices']) or 'ninguno'} (cambio de signo refinado con bisección)",
                    f"Máximos locales: {texto_puntos(datos['maximos'])}", f"Mínimos locales: {texto_puntos(datos['minimos'])}",
                    f"Corte con el eje y: {formatear_real(datos['corte_y'], 8) if datos['corte_y'] is not None else 'fuera del intervalo o no definido'}"]
        if datos["saltos"]:
            calculos.append("Discontinuidades cerca de x = " + ", ".join(formatear_real(s, 5) for s in datos["saltos"]))
        etapas.append(etapa(f"Puntos notables de {nombres[i]}", calculos=calculos))
    total = sum(len(d["raices"]) for d in analisis)
    informe = {"definido": True, "funciones": funciones, "analisis": analisis, "cortes": cortes, "x_min": x_min, "x_max": x_max,
               "titulo": f"{len(funciones)} función(es) en [{formatear_real(x_min, 6)}, {formatear_real(x_max, 6)}]",
               "conclusion": f"Se encontraron {total} cero(s) y {len(cortes)} intersección(es) en el intervalo.",
               "procedimiento": etapas}
    informe["verificacion"] = verificar_graficador(informe)
    return informe


def texto_puntos(puntos):
    """Escribe una lista de puntos (x, y).

    Entrada: lista de pares. Salida: cadena ('ninguno' si está vacía).
    """
    return ", ".join(f"({formatear_real(x, 6)}, {formatear_real(y, 6)})" for x, y in puntos) or "ninguno"


def verificar_graficador(informe):
    """Sustituye cada cero y cada intersección en las funciones originales y prueba la conversión a píxeles.

    Entrada: informe de informe_graficador. Salida: diccionario con correcto y etapas.
    """
    nombres = "fgh"
    etapas, correcto = [], True
    ancho_x = informe["x_max"] - informe["x_min"]
    for i, datos in enumerate(informe["analisis"]):
        funcion = FuncionReal(datos["funcion"].texto)
        condiciones, calculos = [], []
        for r in datos["raices"]:
            y = funcion.evaluar(r)
            bien = y is not None and abs(y) < 1e-6 * max(1.0, _escala_local(funcion, r, ancho_x))
            correcto = correcto and bien
            calculos.append(f"{nombres[i]}({formatear_real(r, 10)}) = {formatear_real(y)}")
            condiciones.append(condicion(f"{nombres[i]}({formatear_real(r, 6)}) ≈ 0", bien))
        etapas.append(etapa(f"Ceros de {nombres[i]}", "Cada cero se sustituye en la función original." if calculos else "No hay ceros que sustituir en este intervalo.",
                            calculos=calculos, condiciones=condiciones))
    for corte in informe["cortes"]:
        f, g = informe["funciones"][corte["i"]], informe["funciones"][corte["j"]]
        y_f, y_g = f.evaluar(corte["x"]), g.evaluar(corte["x"])
        bien = abs(y_f - y_g) < 1e-6 * max(1.0, abs(y_f))
        correcto = correcto and bien
        etapas.append(etapa(f"Intersección de {nombres[corte['i']]} y {nombres[corte['j']]}",
                            calculos=[f"{nombres[corte['i']]}({formatear_real(corte['x'], 8)}) = {formatear_real(y_f, 10)}",
                                      f"{nombres[corte['j']]}({formatear_real(corte['x'], 8)}) = {formatear_real(y_g, 10)}"],
                            condiciones=[condicion("Ambas funciones valen lo mismo.", bien)]))
    etapas.append(etapa("Conclusión de la verificación", conclusion="Se cumple" if correcto else "No se cumple"))
    return {"correcto": correcto, "etapas": etapas}


def _escala_local(funcion, x, ancho):
    """Estima el tamaño de f cerca de x para juzgar un residuo sin depender de las unidades.

    Entrada: función, abscisa y ancho del intervalo. Salida: número no negativo.
    """
    delta = ancho * 1e-6
    valores = [funcion.evaluar(x - delta), funcion.evaluar(x + delta)]
    return max((abs(v) for v in valores if v is not None), default=1.0)


def grafica_ascii(funcion, x_min, x_max, ancho=64, alto=18):
    """Dibuja la función con caracteres para mostrarla en la consola.

    Entrada: función, intervalo, ancho y alto en caracteres. Salida: lista de líneas de texto.
    """
    funcion = _funcion(funcion)
    valores = [(x_min + (x_max - x_min) * i / (ancho - 1)) for i in range(ancho)]
    ys = [funcion.evaluar(x) for x in valores]
    y_min, y_max = rango_automatico([y for y in ys if y is not None])
    rejilla = [[" "] * ancho for _ in range(alto)]
    if y_min <= 0 <= y_max:
        fila_cero = round((y_max - 0) / (y_max - y_min) * (alto - 1))
        rejilla[fila_cero] = ["-"] * ancho
    if x_min <= 0 <= x_max:
        columna_cero = round((0 - x_min) / (x_max - x_min) * (ancho - 1))
        for fila in rejilla:
            fila[columna_cero] = "+" if fila[columna_cero] == "-" else "|"
    for columna, y in enumerate(ys):
        if y is not None and y_min <= y <= y_max:
            rejilla[round((y_max - y) / (y_max - y_min) * (alto - 1))][columna] = "*"
    lineas = [f"f(x) = {funcion.texto}", f"y máx = {formatear_real(y_max, 5)}"]
    lineas += ["".join(fila) for fila in rejilla]
    lineas += [f"y mín = {formatear_real(y_min, 5)}", f"x: de {formatear_real(x_min, 5)} a {formatear_real(x_max, 5)}"]
    return lineas


def descomponer_posicional(texto, base):
    """Separa un número en dígitos, posiciones, pesos y contribuciones según la notación posicional.

    Entrada: texto del número y base (10 o 2).
    Salida: diccionario con base, signo, entero, fraccion, filas y valor exacto; lanza ValueError si no es válido.
    """
    if base not in (2, 10):
        raise ValueError("La base debe ser 10 o 2.")
    limpio = str(texto).strip().replace(" ", "").replace("_", "").replace(",", ".").replace("−", "-")
    signo = -1 if limpio.startswith("-") else 1
    limpio = limpio[1:] if limpio[:1] in ("+", "-") else limpio
    if base == 2 and limpio.lower().startswith("0b"):
        limpio = limpio[2:]
    if not limpio or limpio == "." or limpio.count(".") > 1:
        raise ValueError("Escribe un número válido, por ejemplo 13.625 o 1101.101.")
    permitidos = "01" if base == 2 else "0123456789"
    for caracter in limpio:
        if caracter != "." and caracter not in permitidos:
            raise ValueError(f"«{caracter}» no es un dígito de la base {base}: solo se usan {', '.join(permitidos)}.")
    entero, _punto, fraccion = limpio.partition(".")
    if len(entero) + len(fraccion) > LIMITE_DIGITOS:
        raise ValueError(f"El número admite como máximo {LIMITE_DIGITOS} dígitos.")
    entero = entero.lstrip("0") or "0"
    filas, total = [], Fraction(0)
    for k, caracter in enumerate(entero):
        posicion = len(entero) - 1 - k
        filas.append({"digito": int(caracter), "posicion": posicion, "peso": Fraction(base) ** posicion})
    for k, caracter in enumerate(fraccion):
        filas.append({"digito": int(caracter), "posicion": -(k + 1), "peso": Fraction(base) ** -(k + 1)})
    for fila in filas:
        fila["contribucion"] = fila["digito"] * fila["peso"]
        total += fila["contribucion"]
    return {"base": base, "signo": signo, "entero": entero, "fraccion": fraccion, "filas": filas, "valor": signo * total}


def decimal_a_binario(valor, max_bits=LIMITE_BITS_FRACCION):
    """Convierte a base 2: la parte entera con divisiones sucesivas y la fraccionaria con multiplicaciones sucesivas.

    Entrada: valor (Fraction) y máximo de bits fraccionarios.
    Salida: diccionario con divisiones, multiplicaciones, entero, fraccion, periodo, truncado y texto.
    """
    valor = Fraction(valor)
    signo = "-" if valor < 0 else ""
    positivo = abs(valor)
    entero = positivo.numerator // positivo.denominator
    resto = positivo - entero
    divisiones, n = [], entero
    while n > 0:
        cociente, residuo = divmod(n, 2)
        divisiones.append({"dividendo": n, "cociente": cociente, "residuo": residuo})
        n = cociente
    texto_entero = "".join(str(d["residuo"]) for d in reversed(divisiones)) or "0"
    multiplicaciones, bits, vistas, inicio_periodo = [], [], {}, None
    while resto and len(bits) < max_bits:
        if resto in vistas:
            inicio_periodo = vistas[resto]
            break
        vistas[resto] = len(bits)
        producto = resto * 2
        bit = producto.numerator // producto.denominator
        siguiente = producto - bit
        multiplicaciones.append({"fraccion": resto, "producto": producto, "bit": bit, "resto": siguiente})
        bits.append(str(bit))
        resto = siguiente
    fraccion = "".join(bits)
    truncado = bool(resto) and inicio_periodo is None
    if inicio_periodo is not None:
        escrita = f"{fraccion[:inicio_periodo]}({fraccion[inicio_periodo:]})"
    else:
        escrita = fraccion + ("…" if truncado else "")
    binario = Fraction(int(texto_entero, 2)) + sum((Fraction(int(b), 2 ** (k + 1)) for k, b in enumerate(bits)), Fraction(0))
    return {"signo": signo, "valor": valor, "divisiones": divisiones, "multiplicaciones": multiplicaciones,
            "entero": texto_entero, "fraccion": fraccion, "inicio_periodo": inicio_periodo, "truncado": truncado,
            "periodico": inicio_periodo is not None,
            "texto": f"{signo}{texto_entero}" + (f".{escrita}" if escrita else ""),
            "valor_bits": binario if not signo else -binario}


def representacion_ieee754(valor, bits=64):
    """Obtiene cómo guarda la computadora un número en punto flotante IEEE 754.

    Entrada: valor (Fraction o número) y bits (32 o 64).
    Salida: diccionario con signo, exponente, mantisa, tipo, exponente_real, almacenado y error_representacion.
    """
    if bits not in (32, 64):
        raise ValueError("IEEE 754 se muestra con 32 o 64 bits.")
    exacto = Fraction(valor)
    formato, ancho_exponente, sesgo = (">f", 8, 127) if bits == 32 else (">d", 11, 1023)
    try:
        numero = float(exacto)
        empaquetado = struct.pack(formato, numero)
    except OverflowError:
        numero = float("inf") if exacto > 0 else float("-inf")
        empaquetado = struct.pack(formato, numero)
    cadena = "".join(f"{byte:08b}" for byte in empaquetado)
    signo, exponente, mantisa = cadena[0], cadena[1:1 + ancho_exponente], cadena[1 + ancho_exponente:]
    guardado = struct.unpack(formato, empaquetado)[0]
    if set(exponente) == {"1"}:
        tipo, exponente_real, almacenado, error = "infinito", None, None, None
    else:
        almacenado = Fraction(guardado)
        error = abs(almacenado - exacto)
        if set(exponente) == {"0"}:
            tipo = "cero" if set(mantisa) == {"0"} else "subnormal"
            exponente_real = 1 - sesgo
        else:
            tipo = "normal"
            exponente_real = int(exponente, 2) - sesgo
    return {"bits": bits, "cadena": cadena, "signo": signo, "exponente": exponente, "mantisa": mantisa, "sesgo": sesgo,
            "tipo": tipo, "exponente_real": exponente_real, "almacenado": almacenado, "exacto": exacto,
            "error_representacion": error, "exacta": error == 0 if error is not None else False}


def informe_posicional(texto, base):
    """Explica el número en su base, lo convierte a la otra y muestra cómo se guarda en la computadora.

    Entrada: texto del número y base (10 o 2).
    Salida: informe con descomposicion, binario, decimal, ieee32, ieee64, procedimiento y verificacion.
    """
    descomposicion = descomponer_posicional(texto, base)
    valor = descomposicion["valor"]
    binario = decimal_a_binario(valor)
    decimal = decimal_exacto(valor, 60)
    ieee32, ieee64 = representacion_ieee754(valor, 32), representacion_ieee754(valor, 64)
    terminos = [f"{f['digito']}·{base}{str(f['posicion']).translate(_SUPERINDICES)}" for f in descomposicion["filas"]]
    etapas = [etapa(
        f"Notación posicional en base {base}",
        "Cada dígito vale según su posición: la posición k pesa baseᵏ. A la derecha del punto, k es negativo.",
        formula=("-(" if descomposicion["signo"] < 0 else "") + " + ".join(terminos) + (")" if descomposicion["signo"] < 0 else ""),
        calculos=[f"Posición {f['posicion']}: {f['digito']} × {decimal_exacto(f['peso'], 24)} = {decimal_exacto(f['contribucion'], 24)}"
                  for f in descomposicion["filas"]],
        conclusion=f"Valor = {decimal}")]
    if base == 2:
        etapas.append(etapa("Resultado en base 10", "Al sumar las contribuciones se obtiene el número en base 10.", formula=f"{texto} (base 2) = {decimal} (base 10)"))
    if base == 10:
        if binario["divisiones"]:
            etapas.append(etapa("Parte entera: divisiones sucesivas entre 2",
                                "Los residuos forman los bits; se leen desde el último hasta el primero.",
                                calculos=[f"{d['dividendo']} ÷ 2 = {d['cociente']}, residuo {d['residuo']}" for d in binario["divisiones"]],
                                conclusion=f"Parte entera en base 2: {binario['entero']}"))
        if binario["multiplicaciones"]:
            calculos = [f"{decimal_exacto(p['fraccion'], 18)} × 2 = {decimal_exacto(p['producto'], 18)} → bit {p['bit']}" for p in binario["multiplicaciones"]]
            nota = ("La fracción vuelve a aparecer: el desarrollo es periódico y nunca termina." if binario["periodico"]
                    else f"Se muestran {LIMITE_BITS_FRACCION} bits; el desarrollo continúa." if binario["truncado"]
                    else "La fracción llegó a 0: el desarrollo es finito.")
            etapas.append(etapa("Parte fraccionaria: multiplicaciones sucesivas por 2",
                                "La parte entera de cada producto es el siguiente bit; se leen de arriba hacia abajo.",
                                calculos=calculos, conclusion=nota))
        etapas.append(etapa("Resultado en base 2", formula=f"{decimal} (base 10) = {binario['texto']} (base 2)"))
    etapas.append(_etapa_ieee(ieee64))
    verificacion = verificar_posicional(descomposicion, binario, ieee64)
    conclusion = f"{decimal} en base 10 = {binario['texto']} en base 2."
    if ieee64["tipo"] == "normal" and not ieee64["exacta"]:
        conclusion += " La computadora no puede guardarlo exactamente: se almacena el valor más cercano."
    return {"definido": True, "descomposicion": descomposicion, "binario": binario, "decimal": decimal,
            "ieee32": ieee32, "ieee64": ieee64, "base": base, "titulo": f"{decimal} = {binario['texto']}₂",
            "conclusion": conclusion, "procedimiento": etapas, "verificacion": verificacion}


def _etapa_ieee(rep):
    """Explica cómo se guarda un número en IEEE 754.

    Entrada: diccionario de representacion_ieee754. Salida: etapa.
    """
    calculos = [f"Signo: {rep['signo']} ({'negativo' if rep['signo'] == '1' else 'positivo'})",
                f"Exponente guardado: {rep['exponente']}", f"Mantisa: {rep['mantisa']}"]
    if rep["tipo"] == "normal":
        calculos.insert(2, f"Exponente real: {int(rep['exponente'], 2)} − {rep['sesgo']} = {rep['exponente_real']}")
    if rep["tipo"] == "infinito":
        calculos.append("El número es demasiado grande: se guarda como infinito.")
    else:
        calculos += [f"Valor guardado: {decimal_exacto(rep['almacenado'], 40)}",
                     f"Error de representación: {decimal_exacto(rep['error_representacion'], 8)}"]
    return etapa(f"Representación en la computadora (IEEE 754, {rep['bits']} bits)",
                 "La computadora guarda signo, exponente con sesgo y mantisa en una cantidad fija de bits; lo que no cabe se redondea.",
                 formula="valor = (−1)ˢ × 1.mantisa₂ × 2^(exponente − sesgo)", calculos=calculos,
                 conclusion="El número se guarda exactamente." if rep["exacta"] else "")


def verificar_posicional(descomposicion, binario, ieee):
    """Comprueba la conversión de vuelta, contra int y bin de Python y contra los bits de la computadora.

    Entrada: descomposición, conversión a binario y representación IEEE 754 de 64 bits. Salida: diccionario con correcto y etapas.
    """
    valor = descomposicion["valor"]
    suma = sum((f["contribucion"] for f in descomposicion["filas"]), Fraction(0)) * descomposicion["signo"]
    entero = abs(valor).numerator // abs(valor).denominator
    bits_entero = binario["entero"] == bin(entero)[2:]
    limite = Fraction(1, 2 ** len(binario["fraccion"])) if binario["fraccion"] else Fraction(0)
    regreso = abs(binario["valor_bits"] - valor)
    bits_fraccion = regreso == 0 if not (binario["truncado"] or binario["periodico"]) else regreso < limite
    condiciones = [condicion("La suma de contribuciones reproduce el valor.", suma == valor),
                   condicion(f"Los bits enteros coinciden con bin({entero}).", bits_entero),
                   condicion("Convertir los bits a base 10 regresa al valor" + (" dentro del último bit." if binario["truncado"] or binario["periodico"] else "."), bits_fraccion)]
    correcto = suma == valor and bits_entero and bits_fraccion
    calculos = [f"Regreso desde base 2: {decimal_exacto(binario['valor_bits'], 40)}"]
    if ieee["tipo"] == "normal":
        mantisa = Fraction(int("1" + ieee["mantisa"], 2), 2 ** len(ieee["mantisa"]))
        reconstruido = (-1) ** int(ieee["signo"]) * mantisa * Fraction(2) ** ieee["exponente_real"]
        bien = reconstruido == ieee["almacenado"]
        condiciones.append(condicion("Signo, exponente y mantisa reconstruyen el valor guardado.", bien))
        correcto = correcto and bien
        calculos.append(f"(−1)^{ieee['signo']} × 1.mantisa × 2^{ieee['exponente_real']} = {decimal_exacto(reconstruido, 40)}")
    return {"correcto": correcto, "etapas": [etapa("Conversión de ida y vuelta", "Se recalcula por un camino distinto al de las divisiones y multiplicaciones.",
                                                   calculos=calculos, condiciones=condiciones,
                                                   conclusion="Se cumple" if correcto else "No se cumple")]}


def errores_aproximacion(real, aproximado):
    """Calcula los errores absoluto, relativo y porcentual con aritmética exacta.

    Entrada: valor real y aproximado (Fraction). Salida: diccionario con absoluto, relativo y porcentual (None si real = 0).
    """
    real, aproximado = Fraction(real), Fraction(aproximado)
    absoluto = abs(real - aproximado)
    relativo = absoluto / abs(real) if real != 0 else None
    return {"real": real, "aproximado": aproximado, "absoluto": absoluto, "relativo": relativo,
            "porcentual": relativo * 100 if relativo is not None else None}


def cifras_significativas_correctas(relativo):
    """Calcula las cifras significativas garantizadas: el mayor n con Er ≤ 0.5·10^(1−n) (Scarborough).

    Entrada: error relativo exacto (Fraction o None). Salida: entero ≥ 0, o None si no se puede calcular.
    """
    if relativo is None:
        return None
    if relativo == 0:
        return float("inf")
    n = 0
    while relativo <= Fraction(1, 2) * Fraction(10) ** (-n):
        n += 1
    return n


def redondear_significativas(valor, cifras):
    """Redondea a n cifras significativas (la mitad se redondea alejándose del cero).

    Entrada: valor (Fraction) y cifras n ≥ 1. Salida: Fraction.
    """
    valor = Fraction(valor)
    if valor == 0:
        return valor
    escala = Fraction(10) ** (cifras - 1 - orden_decimal(valor))
    escalado = abs(valor) * escala + Fraction(1, 2)
    resultado = Fraction(escalado.numerator // escalado.denominator) / escala
    return resultado if valor > 0 else -resultado


def truncar_significativas(valor, cifras):
    """Corta a n cifras significativas sin redondear.

    Entrada: valor (Fraction) y cifras n ≥ 1. Salida: Fraction.
    """
    valor = Fraction(valor)
    if valor == 0:
        return valor
    escala = Fraction(10) ** (cifras - 1 - orden_decimal(valor))
    escalado = abs(valor) * escala
    resultado = Fraction(escalado.numerator // escalado.denominator) / escala
    return resultado if valor > 0 else -resultado


def tabla_redondeo(valor, cifras_maximas=10):
    """Compara redondeo y truncamiento para n = 1, 2, …, cifras_maximas.

    Entrada: valor (Fraction) y cifras máximas. Salida: lista de diccionarios con n, redondeado, truncado y sus errores.
    """
    filas = []
    for n in range(1, cifras_maximas + 1):
        redondeado, truncado = redondear_significativas(valor, n), truncar_significativas(valor, n)
        filas.append({"n": n, "redondeado": redondeado, "truncado": truncado,
                      "error_redondeo": abs(valor - redondeado), "error_truncamiento": abs(valor - truncado)})
    return filas


def epsilon_de_maquina():
    """Calcula el épsilon de la máquina: divide entre 2 mientras 1 + ε se distinga de 1.

    Entrada: ninguna. Salida: (épsilon, lista de los pasos (ε, 1 + ε > 1)).
    """
    epsilon, pasos = 1.0, []
    while 1.0 + epsilon / 2 > 1.0:
        pasos.append(epsilon)
        epsilon /= 2
    pasos.append(epsilon)
    return epsilon, pasos


def demostraciones_punto_flotante():
    """Reúne ejemplos clásicos en los que la aritmética de la computadora se aparta de la exacta.

    Entrada: ninguna. Salida: lista de diccionarios con titulo, expresion, exacto, calculado y explicacion.
    """
    suma_decimos = 0.0
    for _ in range(10):
        suma_decimos += 0.1
    pequeno = 1e-15
    return [
        {"titulo": "Error de representación", "expresion": "0.1 + 0.2", "exacto": Fraction(3, 10), "calculado": 0.1 + 0.2,
         "explicacion": "0.1 y 0.2 son periódicos en base 2: se guardan redondeados y el error aparece al sumarlos."},
        {"titulo": "Acumulación de errores", "expresion": "0.1 sumado 10 veces", "exacto": Fraction(1), "calculado": suma_decimos,
         "explicacion": "Cada suma redondea de nuevo, así que muchas operaciones pequeñas acumulan error."},
        {"titulo": "Absorción", "expresion": "10¹⁶ + 1", "exacto": Fraction(10 ** 16 + 1), "calculado": 1e16 + 1.0,
         "explicacion": "Sumar un número muy pequeño a uno muy grande no cambia el resultado: el 1 no cabe en la mantisa."},
        {"titulo": "Cancelación de cifras", "expresion": "(1 + 10⁻¹⁵) − 1", "exacto": Fraction(1, 10 ** 15), "calculado": (1.0 + pequeno) - 1.0,
         "explicacion": "Restar números casi iguales cancela las cifras correctas y deja visible el error de redondeo."},
    ]


def acumulacion_de_error(veces=1000, sumando=Fraction(1, 10)):
    """Mide cómo crece el error al sumar repetidamente un número que no se representa exacto.

    Entrada: cantidad de sumas y sumando. Salida: lista de (k, error absoluto exacto como float) en escala logarítmica.
    """
    suma, serie, siguiente = 0.0, [], 1
    decimal = float(sumando)
    for k in range(1, veces + 1):
        suma += decimal
        if k == siguiente:
            serie.append((k, float(abs(Fraction(suma) - k * Fraction(sumando)))))
            siguiente = max(k + 1, round(k * 1.25))
    return serie


def truncamiento_taylor(x=1.0, terminos=16):
    """Aproxima e^x con sumas parciales de Taylor: el error de truncamiento baja al usar más términos.

    Entrada: x y cantidad de términos. Salida: lista de diccionarios con n, aproximacion, error y cota.
    """
    real = exponencial(x)
    termino, suma, filas = 1.0, 1.0, []
    for n in range(terminos):
        filas.append({"n": n + 1, "aproximacion": suma, "error": abs(real - suma)})
        termino *= x / (n + 1)
        suma += termino
    return filas


def cancelacion_raices(potencias=(2, 4, 6, 8, 10, 12, 14, 16)):
    """Compara √(x+1) − √x con su forma racionalizada 1/(√(x+1) + √x), que evita restar números casi iguales.

    Entrada: exponentes k de x = 10ᵏ. Salida: lista de diccionarios con k, directo, racionalizado y error_relativo.
    """
    filas = []
    for k in potencias:
        x = float(10 ** k)
        directo = (x + 1) ** 0.5 - x ** 0.5
        racionalizado = 1 / ((x + 1) ** 0.5 + x ** 0.5)
        filas.append({"k": k, "directo": directo, "racionalizado": racionalizado,
                      "error_relativo": abs(directo - racionalizado) / racionalizado})
    return filas


def informe_errores(texto_real, texto_aproximado, cifras=4):
    """Calcula los errores de una aproximación y explica redondeo, truncamiento y errores de la máquina.

    Entrada: textos del valor real y aproximado, y cifras significativas n (1 a 15).
    Salida: informe con errores, redondeado, truncado, tabla, demostraciones, procedimiento y verificacion.
    """
    real, real_exacto = leer_exacto(texto_real, "Valor real")
    aproximado, aprox_exacto = leer_exacto(texto_aproximado, "Valor aproximado")
    cifras = int(cifras)
    if not 1 <= cifras <= 15:
        raise ValueError("Las cifras significativas deben estar entre 1 y 15.")
    for nombre, valor in (("El valor real", real), ("El valor aproximado", aproximado)):
        if valor != 0 and not Fraction(1, 10 ** 300) <= abs(valor) <= 10 ** 300:
            raise ValueError(f"{nombre} debe estar entre 10⁻³⁰⁰ y 10³⁰⁰ en valor absoluto.")
    errores = errores_aproximacion(real, aproximado)
    correctas = cifras_significativas_correctas(errores["relativo"])
    tabla = tabla_redondeo(real, 12)
    redondeado, truncado = redondear_significativas(real, cifras), truncar_significativas(real, cifras)
    epsilon, pasos_epsilon = epsilon_de_maquina()
    demostraciones = demostraciones_punto_flotante()
    taylor = truncamiento_taylor()
    cancelacion = cancelacion_raices()
    nota_real = "" if real_exacto else " Se usa su valor en doble precisión (no es exacto)."
    etapas = [
        etapa("Datos", f"Valor real v y valor aproximado v*.{nota_real}",
              calculos=[f"v = {texto_real} = {decimal_exacto(real, 20)}", f"v* = {texto_aproximado} = {decimal_exacto(aproximado, 20)}"]),
        etapa("Error absoluto", "Mide cuánto se aleja la aproximación, en las mismas unidades del dato.", formula="Ea = |v − v*|",
              calculos=[f"Ea = {decimal_exacto(errores['absoluto'], 12)}"]),
    ]
    if errores["relativo"] is not None:
        etapas.append(etapa("Error relativo y porcentual", "Compara el error con el tamaño del valor real, por eso permite comparar medidas distintas.",
                            formula="Er = Ea / |v|,   E% = Er × 100 %",
                            calculos=[f"Er = {decimal_exacto(errores['relativo'], 12)}", f"E% = {decimal_exacto(errores['porcentual'], 12)} %",
                                      f"Cifras significativas garantizadas: {_texto_cifras(correctas)} (criterio Er ≤ 0.5·10^(1−n))"]))
    else:
        etapas.append(etapa("Error relativo", "No está definido porque el valor real es 0: habría que dividir entre 0."))
    etapas += [
        etapa(f"Redondeo y truncamiento a {cifras} cifras significativas", "Redondear elige el número más cercano; truncar simplemente corta las cifras sobrantes.",
              calculos=[f"Redondeado: {decimal_exacto(redondeado, 20)}   (error {decimal_exacto(abs(real - redondeado), 8)})",
                        f"Truncado: {decimal_exacto(truncado, 20)}   (error {decimal_exacto(abs(real - truncado), 8)})"],
              conclusion="El redondeo nunca da un error mayor que el truncamiento."),
        etapa("Error de truncamiento en una serie", "e¹ se aproxima con una suma finita: lo que se deja de sumar es el error de truncamiento.",
              formula="eˣ ≈ 1 + x + x²/2! + … + xⁿ/n!",
              calculos=[f"{f['n']} término(s): {formatear_real(f['aproximacion'], 14)}   error {formatear_real(f['error'], 3)}" for f in taylor[:8]]),
        etapa("Épsilon de la máquina", "Se divide entre 2 hasta que 1 + ε deja de distinguirse de 1: es la separación mínima alrededor de 1.",
              formula="ε = 2⁻⁵² en doble precisión", calculos=[f"ε = {formatear_real(epsilon, 16)}", f"Divisiones realizadas: {len(pasos_epsilon) - 1}"]),
        etapa("Errores de la aritmética de la computadora",
              calculos=[f"{d['titulo']}: {d['expresion']} da {formatear_real(d['calculado'], 17)}; lo exacto es {decimal_exacto(d['exacto'], 17)}. {d['explicacion']}" for d in demostraciones]),
        etapa("Cancelación de cifras al restar", "√(x+1) − √x resta números casi iguales; la forma racionalizada evita la pérdida de precisión.",
              formula="√(x+1) − √x = 1 / (√(x+1) + √x)",
              calculos=[f"x = 10^{f['k']}: directo {formatear_real(f['directo'], 8)},  racionalizado {formatear_real(f['racionalizado'], 8)},  error rel. {formatear_real(f['error_relativo'], 2)}" for f in cancelacion]),
    ]
    informe = {"definido": True, "real": real, "aproximado": aproximado, "texto_real": texto_real, "texto_aproximado": texto_aproximado,
               "errores": errores, "cifras": cifras, "cifras_correctas": correctas, "redondeado": redondeado, "truncado": truncado,
               "tabla": tabla, "epsilon": epsilon, "pasos_epsilon": pasos_epsilon, "demostraciones": demostraciones,
               "taylor": taylor, "cancelacion": cancelacion, "acumulacion": acumulacion_de_error(),
               "titulo": f"Ea = {decimal_exacto(errores['absoluto'], 8)}",
               "conclusion": _conclusion_errores(errores, correctas),
               "procedimiento": etapas}
    informe["verificacion"] = verificar_errores(informe)
    return informe


def _conclusion_errores(errores, correctas):
    """Resume los errores de una aproximación en una frase.

    Entrada: diccionario de errores_aproximacion y cifras correctas. Salida: cadena.
    """
    if errores["relativo"] is None:
        return "El valor real es 0: el error relativo no está definido y solo se puede calcular el error absoluto."
    if errores["relativo"] == 0:
        return "El valor aproximado coincide exactamente con el real: todos los errores valen 0."
    return (f"Er = {formatear_real(errores['relativo'], 6)} ({formatear_real(errores['porcentual'], 6)} %): "
            f"{correctas} cifra(s) significativa(s) garantizada(s).")


def _texto_cifras(cifras):
    """Escribe la cantidad de cifras significativas correctas.

    Entrada: entero, infinito o None. Salida: cadena.
    """
    if cifras is None:
        return "no aplica"
    return "todas" if cifras == float("inf") else str(cifras)


def verificar_errores(informe):
    """Comprueba las definiciones por otro camino y las cotas teóricas del redondeo y del truncamiento.

    Entrada: informe de informe_errores. Salida: diccionario con correcto y etapas.
    """
    real, aproximado, errores = informe["real"], informe["aproximado"], informe["errores"]
    condiciones = [condicion("v* está a distancia Ea de v: v* = v + Ea o v* = v − Ea.",
                             aproximado in (real + errores["absoluto"], real - errores["absoluto"]))]
    if errores["relativo"] is not None:
        condiciones.append(condicion("Er · |v| reproduce Ea.", errores["relativo"] * abs(real) == errores["absoluto"]))
        condiciones.append(condicion("E% = 100 · Er.", errores["porcentual"] == 100 * errores["relativo"]))
    if real != 0:
        unidad = Fraction(10) ** (orden_decimal(real) - informe["cifras"] + 1)
        condiciones += [
            condicion("El error de redondeo no supera media unidad de la última cifra.", abs(real - informe["redondeado"]) <= unidad / 2),
            condicion("El error de truncamiento es menor que una unidad de la última cifra.", abs(real - informe["truncado"]) < unidad),
            condicion("En la tabla, redondear nunca es peor que truncar.", all(f["error_redondeo"] <= f["error_truncamiento"] for f in informe["tabla"]))]
    epsilon = informe["epsilon"]
    condiciones += [condicion("1 + ε se distingue de 1, pero 1 + ε/2 no.", 1.0 + epsilon > 1.0 and 1.0 + epsilon / 2 == 1.0),
                    condicion("ε es exactamente 2⁻⁵².", Fraction(epsilon) == Fraction(1, 2 ** 52)),
                    condicion("El error de truncamiento de la serie disminuye al sumar términos.",
                              informe["taylor"][-1]["error"] < informe["taylor"][0]["error"])]
    correcto = all(c["cumple"] for c in condiciones)
    return {"correcto": correcto, "etapas": [etapa("Definiciones y cotas", "Se recalcula por caminos distintos a los del procedimiento.",
                                                   condiciones=condiciones, conclusion="Se cumple" if correcto else "No se cumple")]}


def tabla_biseccion(informe):
    """Escribe la tabla de iteraciones de la bisección para la consola.

    Entrada: informe de biseccion. Salida: lista de cadenas alineadas.
    """
    lineas = [f"{'n':>3}  {'a':>14}  {'b':>14}  {'c':>14}  {'f(c)':>12}  {'cota':>10}"]
    for it in informe.get("iteraciones", []):
        lineas.append(f"{it['n']:>3}  {format(it['a'], '.8g'):>14}  {format(it['b'], '.8g'):>14}  {format(it['c'], '.8g'):>14}  "
                      f"{format(it['fc'], '.4g'):>12}  {format(it['cota_error'], '.3g'):>10}")
    return lineas


def formatear_informe(informe):
    """Convierte un informe en líneas de texto (resultado y procedimiento) para la consola.

    Entrada: informe de cualquiera de las cuatro opciones. Salida: lista de cadenas.
    """
    lineas = [informe["titulo"], informe["conclusion"], ""]
    for numero, paso in enumerate(informe["procedimiento"], start=1):
        lineas.append(f"{numero}. {paso['titulo']}")
        for texto in (paso["explicacion"], paso["formula"]):
            if texto:
                lineas.append(f"   {texto}")
        lineas += [f"   {c['texto']}: {'sí' if c['cumple'] else 'no'}" for c in paso["condiciones"]]
        lineas += [f"   {calculo}" for calculo in paso["calculos"]]
        if paso["conclusion"]:
            lineas.append(f"   → {paso['conclusion']}")
    verificacion = informe["verificacion"]
    if verificacion.get("aplicable") is False:
        lineas += ["", f"Verificación: {verificacion['motivo']}"]
    else:
        lineas += ["", "Verificación: " + ("superada" if verificacion["correcto"] else "con diferencias")]
    return lineas

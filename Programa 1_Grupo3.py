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
from tkinter import messagebox, ttk


EPSILON = Fraction(0)


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

    La normalizacion deja cada pivote igual a 1.
    La eliminacion se aplica en todas las filas distintas de la fila pivote,
    por eso el resultado facilita leer soluciones unicas o parametricas.
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
                (f"F{fila_pivote + 1} -> F{fila_pivote + 1} / {formatear_numero(valor_pivote)}", copiar_matriz(matriz))
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


class AplicacionAlgebraLineal:
    """Interfaz grafica hecha con Tkinter."""

    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("Programa 1 - Calculadora de Algebra Lineal")
        self.raiz.geometry("1050x700")
        self.entradas = []

        self.crear_interfaz()

    def crear_interfaz(self):
        marco_superior = ttk.Frame(self.raiz, padding=10)
        marco_superior.pack(fill="x")

        ttk.Label(marco_superior, text="Ecuaciones (m):").pack(side="left")
        self.entrada_m = ttk.Entry(marco_superior, width=6)
        self.entrada_m.insert(0, "3")
        self.entrada_m.pack(side="left", padx=5)

        ttk.Label(marco_superior, text="Variables (n):").pack(side="left")
        self.entrada_n = ttk.Entry(marco_superior, width=6)
        self.entrada_n.insert(0, "3")
        self.entrada_n.pack(side="left", padx=5)

        ttk.Button(marco_superior, text="Crear matriz", command=self.crear_entradas_matriz).pack(side="left", padx=8)
        ttk.Button(marco_superior, text="Resolver", command=self.resolver_desde_interfaz).pack(side="left")

        self.marco_matriz = ttk.LabelFrame(self.raiz, text="Matriz aumentada [A | b]", padding=10)
        self.marco_matriz.pack(fill="x", padx=10, pady=5)

        self.salida = tk.Text(self.raiz, wrap="none", font=("Consolas", 10))
        self.salida.pack(fill="both", expand=True, padx=10, pady=10)

        self.crear_entradas_matriz()

    def crear_entradas_matriz(self):
        for widget in self.marco_matriz.winfo_children():
            widget.destroy()

        try:
            m = int(self.entrada_m.get())
            n = int(self.entrada_n.get())
            if m <= 0 or n <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Entrada invalida", "m y n deben ser enteros positivos.")
            return

        self.entradas = []
        for i in range(m):
            fila = []
            for j in range(n):
                entrada = ttk.Entry(self.marco_matriz, width=8)
                entrada.grid(row=i, column=j, padx=3, pady=3)
                entrada.insert(0, "0")
                fila.append(entrada)

            ttk.Label(self.marco_matriz, text="=").grid(row=i, column=n, padx=5)
            entrada_b = ttk.Entry(self.marco_matriz, width=8)
            entrada_b.grid(row=i, column=n + 1, padx=3, pady=3)
            entrada_b.insert(0, "0")
            fila.append(entrada_b)
            self.entradas.append(fila)

    def leer_datos(self):
        A = []
        b = []
        for fila in self.entradas:
            valores = [convertir_numero(entrada.get()) for entrada in fila]
            A.append(valores[:-1])
            b.append(valores[-1])
        return A, b

    def resolver_desde_interfaz(self):
        try:
            A, b = self.leer_datos()
            resultado = resolver_sistema(A, b)
            self.mostrar_resultado(resultado)
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def escribir(self, texto=""):
        self.salida.insert("end", texto + "\n")

    def mostrar_resultado(self, resultado):
        self.salida.delete("1.0", "end")

        self.escribir("PROCESO DE ELIMINACION POR FILAS")
        self.escribir("=" * 70)

        for descripcion, matriz in resultado["pasos"]:
            self.escribir(descripcion)
            self.escribir(matriz_a_texto(matriz))
            self.escribir()

        self.escribir("CLASIFICACION")
        self.escribir(resultado["clasificacion"])
        self.escribir(resultado["descripcion"])
        self.escribir()

        basicas = ", ".join(f"x{c + 1}" for c in resultado["variables_basicas"]) or "ninguna"
        libres = ", ".join(f"x{c + 1}" for c in resultado["variables_libres"]) or "ninguna"
        self.escribir(f"Variables basicas: {basicas}")
        self.escribir(f"Variables libres: {libres}")
        self.escribir()

        if resultado["solucion"] is not None:
            self.escribir("SOLUCION")
            for i, valor in enumerate(resultado["solucion"], start=1):
                self.escribir(f"x{i} = {formatear_numero(valor)}")
            self.escribir()

        if resultado["expresiones"] is not None:
            self.escribir("SOLUCION PARAMETRICA")
            for i in range(len(resultado["expresiones"])):
                self.escribir(f"x{i + 1} = {resultado['expresiones'][i]}")
            self.escribir()

        if resultado["verificacion"] is not None:
            correcta, detalles = resultado["verificacion"]
            self.escribir("VERIFICACION CON EL SISTEMA ORIGINAL")
            for i, (obtenido, esperado, coincide) in enumerate(detalles, start=1):
                marca = "correcto" if coincide else "incorrecto"
                self.escribir(
                    f"Ecuacion {i}: {formatear_numero(obtenido)} = {formatear_numero(esperado)} -> {marca}"
                )
            self.escribir("Resultado: " + ("verificado correctamente" if correcta else "no verificado"))


def main():
    raiz = tk.Tk()
    app = AplicacionAlgebraLineal(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()

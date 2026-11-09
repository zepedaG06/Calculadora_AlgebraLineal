"""Punto de entrada y menú principal de la Calculadora de Álgebra Lineal.

Propósito: abrir la interfaz gráfica o, con --consola, el menú de texto que incluye «Factorización LU y
solución Ax = b», el verificador de propiedades, la independencia lineal y los métodos numéricos. Solo aquí se
usan input()/print().
Unidad: Álgebra Lineal (MTM0120), Programa 7: módulo de Métodos Numéricos.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
"""
import importlib.util
import sys
from pathlib import Path

from modulos.modulo_lu import formatear_resultado_lu, resolver_lu
from modulos.modulo_matrices import LIMITE_DIMENSION, convertir_numero, formatear_numero, verificar_propiedades_clave
from modulos.modulo_numericos import (FuncionReal, biseccion, formatear_informe, grafica_ascii, informe_errores,
                                      informe_graficador, informe_posicional, leer_real, tabla_biseccion)
from teoremas.teoremas_lu import LOGO_LU, texto_teoremas_lu
from teoremas.teoremas_numericos import LOGO_NUMERICOS, texto_teoremas_numericos

OPCIONES_MENU_PRINCIPAL = (
    ("1", "Abrir la interfaz gráfica"),
    ("2", "Factorización LU y solución Ax = b"),
    ("3", "Verificador de propiedades de matrices"),
    ("4", "Independencia lineal"),
    ("5", "Métodos numéricos"),
    ("S", "Salir"),
)
OPCIONES_MENU_LU = (
    ("1", "Ingresar A y b, factorizar y resolver"),
    ("0", "Ver Teoremas Clave del Módulo"),
    ("V", "Volver al menú principal"),
)
OPCIONES_MENU_NUMERICOS = (
    ("1", "Método de Bisección"),
    ("2", "Graficador de funciones"),
    ("3", "Notación posicional en base 10 y base 2"),
    ("4", "Errores numéricos"),
    ("0", "Ver Teoremas Clave del Módulo"),
    ("V", "Volver al menú principal"),
)


def cargar_aplicacion():
    """Carga la interfaz gráfica desde la carpeta del proyecto, sin depender del directorio actual.

    Salida: el módulo de la GUI ya cargado.
    """
    ruta = Path(__file__).with_name("Programa 1_Grupo3.py")
    spec = importlib.util.spec_from_file_location("calculadora_gui", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def leer_entero(mensaje, minimo, maximo, entrada=input, salida=print):
    """Pide un entero dentro de [mínimo, máximo] y repite la pregunta ante cualquier error.

    Entrada: mensaje, mínimo, máximo y funciones de entrada/salida. Salida: el entero leído.
    """
    while True:
        texto = entrada(mensaje).strip()
        try:
            numero = int(texto)
            if minimo <= numero <= maximo:
                return numero
        except ValueError:
            pass
        salida(f"  Error: escribe un número entero entre {minimo} y {maximo}.")


def leer_numeros(mensaje, cantidad, entrada=input, salida=print):
    """Pide una línea con la cantidad indicada de números (enteros, decimales o fracciones) y la repite si hay errores.

    Entrada: mensaje, cantidad y funciones de entrada/salida. Salida: lista de Fraction.
    """
    while True:
        partes = entrada(mensaje).replace(";", " ").split()
        try:
            if len(partes) != cantidad:
                raise ValueError(f"se esperaban {cantidad} números y se recibieron {len(partes)}.")
            return [convertir_numero(parte) for parte in partes]
        except ValueError as error:
            salida(f"  Error: {error} Vuelve a escribir la línea.")


def leer_matriz(nombre, filas, columnas, entrada=input, salida=print):
    """Pide una matriz fila por fila; solo se vuelve a pedir la fila inválida.

    Entrada: nombre, filas, columnas y funciones de entrada/salida. Salida: lista anidada de Fraction.
    """
    salida(f"Escribe las {filas} filas de {nombre}, con {columnas} números separados por espacios (3, -1/2 o 0.5).")
    return [leer_numeros(f"  {nombre} fila {i + 1}: ", columnas, entrada, salida) for i in range(filas)]


def ejecutar_factorizacion_lu(entrada=input, salida=print):
    """Pide m × n, A y b, encadena resolver_lu y muestra L, U, y, x y los mensajes de verificación.

    Entrada: funciones de entrada/salida. Salida: el diccionario de resolver_lu.
    """
    filas = leer_entero(f"Número de filas m de A (1 a {LIMITE_DIMENSION}): ", 1, LIMITE_DIMENSION, entrada, salida)
    columnas = leer_entero(f"Número de columnas n de A (1 a {LIMITE_DIMENSION}): ", 1, LIMITE_DIMENSION, entrada, salida)
    matriz_A = leer_matriz("A", filas, columnas, entrada, salida)
    vector_b = leer_numeros(f"Vector b ({filas} componentes separadas por espacios): ", filas, entrada, salida)
    resultado = resolver_lu(matriz_A, vector_b)
    salida("")
    for linea in formatear_resultado_lu(resultado):
        salida(linea)
    return resultado


def menu_factorizacion_lu(entrada=input, salida=print):
    """Muestra el logotipo y el menú del módulo LU hasta que el usuario elige volver.

    Entrada: funciones de entrada/salida. Salida: None.
    """
    while True:
        salida(LOGO_LU)
        salida("FACTORIZACIÓN LU Y SOLUCIÓN Ax = b")
        for clave, texto in OPCIONES_MENU_LU:
            salida(f"  {clave}. {texto}")
        opcion = entrada("Elige una opción: ").strip().upper()
        if opcion == "1":
            ejecutar_factorizacion_lu(entrada, salida)
        elif opcion == "0":
            salida("\n0. Ver Teoremas Clave del Módulo\n")
            salida(texto_teoremas_lu())
        elif opcion == "V":
            return
        else:
            salida("  Opción no válida: elige 1, 0 o V.")


def ejecutar_verificador_propiedades(entrada=input, salida=print):
    """Pide A, B, C y k y muestra «Se cumple», «No se cumple» o «No aplica» para cada propiedad.

    Entrada: funciones de entrada/salida. Salida: el informe de verificar_propiedades_clave.
    """
    matrices = {}
    for nombre in ("A", "B", "C"):
        filas = leer_entero(f"Filas de {nombre} (1 a {LIMITE_DIMENSION}): ", 1, LIMITE_DIMENSION, entrada, salida)
        columnas = leer_entero(f"Columnas de {nombre} (1 a {LIMITE_DIMENSION}): ", 1, LIMITE_DIMENSION, entrada, salida)
        matrices[nombre] = leer_matriz(nombre, filas, columnas, entrada, salida)
    escalar_k = leer_numeros("Escalar k: ", 1, entrada, salida)[0]
    informe = verificar_propiedades_clave(matrices["A"], matrices["B"], matrices["C"], escalar_k)
    categoria_actual = None
    for resultado in informe["resultados"]:
        if resultado["categoria"] != categoria_actual:
            categoria_actual = resultado["categoria"]
            salida(f"\n{categoria_actual}")
        marca = "✓" if resultado["cumple"] else "✗" if resultado["cumple"] is False else "·"
        salida(f"  {marca} {resultado['propiedad']}: {resultado['diagnostico']}")
    salida(f"\nPropiedades evaluadas: {informe['evaluadas']}; se cumplen: {informe['cumplidas']} (k = "
           f"{formatear_numero(informe['k'])}).")
    return informe


def leer_validado(mensaje, convertir, entrada=input, salida=print, predeterminado=None):
    """Pide un dato y lo vuelve a pedir mientras convertir lance ValueError.

    Entrada: mensaje, función convertir, funciones de entrada/salida y valor si se responde vacío. Salida: dato convertido.
    """
    while True:
        texto = entrada(mensaje).strip()
        if not texto and predeterminado is not None:
            texto = predeterminado
        try:
            return convertir(texto)
        except ValueError as error:
            salida(f"  Error: {error} Vuelve a escribirlo.")


def ejecutar_biseccion(entrada=input, salida=print):
    """Pide f, a, b y la tolerancia, aplica la bisección y muestra la tabla y el procedimiento.

    Entrada: funciones de entrada/salida. Salida: el informe de biseccion.
    """
    funcion = leer_validado("f(x) = ", FuncionReal, entrada, salida)
    a = leer_validado("a = ", lambda texto: leer_real(texto, "a"), entrada, salida)
    b = leer_validado("b = ", lambda texto: leer_real(texto, "b"), entrada, salida)
    tolerancia = leer_validado("Tolerancia [1e-6]: ", lambda texto: leer_real(texto, "La tolerancia"), entrada, salida, "1e-6")
    try:
        informe = biseccion(funcion, a, b, tolerancia)
    except ValueError as error:
        salida(f"  Error: {error}")
        return None
    salida("")
    if informe["definido"]:
        for linea in tabla_biseccion(informe):
            salida(linea)
        salida("")
    for linea in formatear_informe(informe):
        salida(linea)
    return informe


def ejecutar_graficador(entrada=input, salida=print):
    """Pide una función y un intervalo, la dibuja con caracteres y explica cómo se graficó.

    Entrada: funciones de entrada/salida. Salida: el informe de informe_graficador.
    """
    funcion = leer_validado("f(x) = ", FuncionReal, entrada, salida)
    x_min = leer_validado("x mínimo [-5]: ", lambda texto: leer_real(texto, "x mínimo"), entrada, salida, "-5")
    x_max = leer_validado("x máximo [5]: ", lambda texto: leer_real(texto, "x máximo"), entrada, salida, "5")
    try:
        informe = informe_graficador([funcion.texto], x_min, x_max)
    except ValueError as error:
        salida(f"  Error: {error}")
        return None
    salida("")
    for linea in [*grafica_ascii(funcion, x_min, x_max), "", *formatear_informe(informe)]:
        salida(linea)
    return informe


def ejecutar_posicional(entrada=input, salida=print):
    """Pide un número y su base, lo descompone, lo convierte y muestra cómo lo guarda la computadora.

    Entrada: funciones de entrada/salida. Salida: el informe de informe_posicional.
    """
    def elegir_base(texto):
        """Acepta solo las bases del módulo.

        Entrada: texto. Salida: 10 o 2; lanza ValueError con cualquier otro valor.
        """
        if texto not in ("10", "2"):
            raise ValueError("la base debe ser 10 o 2.")
        return int(texto)

    base = leer_validado("Base del número (10 o 2) [10]: ", elegir_base, entrada, salida, "10")
    informe = leer_validado(f"Número en base {base}: ", lambda texto: informe_posicional(texto, base), entrada, salida)
    salida("")
    for linea in formatear_informe(informe):
        salida(linea)
    return informe


def ejecutar_errores(entrada=input, salida=print):
    """Pide el valor real, el aproximado y las cifras, y muestra los errores y los de la máquina.

    Entrada: funciones de entrada/salida. Salida: el informe de informe_errores.
    """
    real = leer_validado("Valor real v (admite pi, 1/3, sqrt(2)): ", lambda texto: (leer_real(texto, "v"), texto)[1], entrada, salida)
    aproximado = leer_validado("Valor aproximado v*: ", lambda texto: (leer_real(texto, "v*"), texto)[1], entrada, salida)
    cifras = leer_entero("Cifras significativas n (1 a 15): ", 1, 15, entrada, salida)
    try:
        informe = informe_errores(real, aproximado, cifras)
    except ValueError as error:
        salida(f"  Error: {error}")
        return None
    salida("")
    for linea in formatear_informe(informe):
        salida(linea)
    return informe


def menu_metodos_numericos(entrada=input, salida=print):
    """Muestra el logotipo y las cuatro opciones del módulo hasta que el usuario elige volver.

    Entrada: funciones de entrada/salida. Salida: None.
    """
    acciones = {"1": ejecutar_biseccion, "2": ejecutar_graficador, "3": ejecutar_posicional, "4": ejecutar_errores}
    while True:
        salida(LOGO_NUMERICOS)
        salida("MÉTODOS NUMÉRICOS")
        for clave, texto in OPCIONES_MENU_NUMERICOS:
            salida(f"  {clave}. {texto}")
        opcion = entrada("Elige una opción: ").strip().upper()
        if opcion in acciones:
            acciones[opcion](entrada, salida)
        elif opcion == "0":
            salida("\n0. Ver Teoremas Clave del Módulo\n")
            salida(texto_teoremas_numericos())
        elif opcion == "V":
            return
        else:
            salida("  Opción no válida: elige 1, 2, 3, 4, 0 o V.")


def menu_principal(entrada=input, salida=print):
    """Muestra el menú principal de consola y ejecuta cada opción hasta que el usuario sale.

    Entrada: funciones de entrada/salida. Salida: None.
    """
    while True:
        salida("\n=== CALCULADORA DE ÁLGEBRA LINEAL · GRUPO 3 · UAM ===")
        for clave, texto in OPCIONES_MENU_PRINCIPAL:
            salida(f"  {clave}. {texto}")
        opcion = entrada("Elige una opción: ").strip().upper()
        if opcion == "1":
            aplicacion = cargar_aplicacion()
            if aplicacion.ctk is None:
                salida("  CustomTkinter no está instalado: instala requirements.txt para usar la interfaz gráfica.")
            else:
                aplicacion.configurar_customtkinter()
                aplicacion.AplicacionAlgebraLineal().mainloop()
        elif opcion == "2":
            menu_factorizacion_lu(entrada, salida)
        elif opcion == "3":
            ejecutar_verificador_propiedades(entrada, salida)
        elif opcion == "4":
            cargar_aplicacion().independencia_consola(entrada)
        elif opcion == "5":
            menu_metodos_numericos(entrada, salida)
        elif opcion == "S":
            return
        else:
            salida("  Opción no válida: elige 1, 2, 3, 4, 5 o S.")


def main(argumentos=None):
    """Abre la interfaz gráfica; con --consola (o sin CustomTkinter) abre el menú de texto.

    Entrada: lista de argumentos (por defecto sys.argv). Salida: None.
    """
    argumentos = sys.argv[1:] if argumentos is None else argumentos
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    try:
        if "--consola" in argumentos:
            menu_principal()
            return
        aplicacion = cargar_aplicacion()
        if aplicacion.ctk is None and "--teoremas" not in argumentos:
            print("CustomTkinter no está instalado; se abre el menú de consola.")
            menu_principal()
            return
        aplicacion.main()
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma terminado.")


if __name__ == "__main__":
    main()

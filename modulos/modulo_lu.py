"""Factorización LU (A = LU) y solución de Ax = b en dos etapas sustitutivas.

Propósito: reducir A (m × n) a su forma escalonada U solo con reemplazos Fi ← Fi − l·Fj, registrar
cada multiplicador l en L (m × m, triangular inferior con unos en la diagonal), verificar L · U == A
y resolver Ax = b reduciendo [L | b] hacia adelante y [U | y] hacia atrás; al final, A · x == b.
Unidad: Álgebra Lineal (MTM0120), Programa 6: factorización LU y solución de sistemas Ax = b.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
Funciones puras: reutilizan modulo_matrices, retornan listas anidadas y no usan input() ni print().
"""
from fractions import Fraction

from .informes import certificado_inconsistencia, comparar, producto, producto_vector
from .modulo_matrices import (buscar_fila_pivote, calcular_determinante, clasificar_sistema, copiar_matriz,
                              crear_matriz_aumentada, fila_inconsistente, forma_escalonada, formatear_numero,
                              matriz_a_texto, matriz_identidad, multiplicar_fila, multiplicar_matrices,
                              multiplicar_matriz_vector, nombres_parametros, obtener_forma_vectorial,
                              obtener_nombres_variables, obtener_solucion_parametrica, obtener_solucion_unica,
                              resolver_sistema, son_iguales, sumar_multiplo_fila, texto_resta_de_filas,
                              unir_terminos, validar_matriz)
from .pasos import condicion, etapa, valor

MENSAJE_SIN_PERMUTACION = "La matriz no admite Factorización LU sin permutación (requiere pivoteo parcial PA = LU)"
MENSAJE_FACTORIZACION_CORRECTA = "La factorización es correcta (L · U == A)"
MENSAJE_FACTORIZACION_INCORRECTA = "La factorización no es correcta (L · U != A)"
MENSAJE_COMPROBACION_EXITOSA = "Comprobación exitosa: A · x == b"
MENSAJE_COMPROBACION_FALLIDA = "Comprobación fallida: A · x != b"
MENSAJE_SIN_SOLUCION = "El sistema Ax = b no tiene solución: no existe x que comprobar."


def _p(numero):
    """Escribe un número entre paréntesis para mostrar sustituciones, por ejemplo (-1/2).

    Entrada: número. Salida: cadena.
    """
    return f"({formatear_numero(numero)})"


def _vector(datos, nombre):
    """Convierte las componentes de un vector a Fraction.

    Entrada: lista de números y nombre del vector. Salida: lista de Fraction; lanza ValueError si alguna no es numérica.
    """
    try:
        return [Fraction(componente) for componente in datos]
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError(f"{nombre} contiene una entrada no numérica válida.") from error


def _ecuacion(coeficientes, nombres, termino_independiente):
    """Escribe una ecuación lineal, por ejemplo '2x1 - x2 = 3'.

    Entrada: coeficientes, nombres de variables y término independiente. Salida: cadena.
    """
    return f"{unir_terminos(zip(coeficientes, nombres))} = {formatear_numero(termino_independiente)}"


def _despeje(incognita, termino_independiente, restas, divisor):
    """Escribe el despeje 'x = (b − …) / (d)' omitiendo paréntesis y divisor cuando no hacen falta.

    Entrada: incógnita, término independiente, restas y divisor. Salida: cadena.
    """
    numerador = f"{formatear_numero(termino_independiente)}{restas}"
    if divisor == 1:
        return f"{incognita} = {numerador}"
    return f"{incognita} = " + (f"({numerador})" if restas else numerador) + f" / {_p(divisor)}"


def _texto_afin(constante, coeficientes, parametros):
    """Escribe 'constante + Σ coeficiente·parámetro' sin términos nulos, por ejemplo '1 + (7/6)t'.

    Entrada: constante, coeficientes y parámetros. Salida: cadena.
    """
    parte_variable = unir_terminos(zip(coeficientes, parametros))
    if parte_variable == "0":
        return formatear_numero(constante)
    if constante == 0:
        return parte_variable
    signo, cuerpo = ("-", parte_variable[1:]) if parte_variable.startswith("-") else ("+", parte_variable)
    return f"{formatear_numero(constante)} {signo} {cuerpo}"


def _texto_vector(vector):
    """Escribe un vector entre paréntesis, por ejemplo (3, 4, -6, -1).

    Entrada: lista de números. Salida: cadena.
    """
    return "(" + ", ".join(formatear_numero(componente) for componente in vector) + ")"


def _es_matriz(matriz, filas, columnas):
    """Indica si el dato es una lista anidada de exactamente filas × columnas.

    Entrada: dato, filas y columnas. Salida: True o False.
    """
    return isinstance(matriz, list) and len(matriz) == filas and all(
        isinstance(fila, list) and len(fila) == columnas for fila in matriz)


def _es_vector(vector, componentes):
    """Indica si el dato es una lista con la cantidad exacta de componentes.

    Entrada: dato y componentes. Salida: True o False.
    """
    return isinstance(vector, list) and len(vector) == componentes


def es_triangular_inferior_unitaria(matriz_L):
    """Indica si L es cuadrada, con ceros sobre la diagonal y unos en la diagonal principal.

    Entrada: matriz_L. Salida: True o False.
    """
    orden = len(matriz_L)
    return (all(len(fila) == orden for fila in matriz_L) and all(matriz_L[i][i] == 1 for i in range(orden))
            and all(matriz_L[i][j] == 0 for i in range(orden) for j in range(i + 1, orden)))


def pivotes_escalonada(matriz_U):
    """Localiza los pivotes de U y comprueba que esté en forma escalonada.

    Entrada: matriz_U. Salida: lista de posiciones (fila, columna), o None si U no es escalonada.
    """
    pivotes, columna_anterior, hubo_fila_nula = [], -1, False
    for fila, entradas in enumerate(matriz_U):
        columna = next((j for j, entrada in enumerate(entradas) if entrada != 0), None)
        if columna is None:
            hubo_fila_nula = True
            continue
        if hubo_fila_nula or columna <= columna_anterior:
            return None
        pivotes.append((fila, columna))
        columna_anterior = columna
    return pivotes


def calcular_multiplicador(matriz_U, fila, fila_pivote, columna):
    """Calcula el multiplicador l tal que Fi ← Fi − l·Fj anula matriz_U[fila][columna].

    Entrada: matriz_U (m × n), fila, fila_pivote y columna, con pivote distinto de 0. Salida: Fraction l.
    """
    return matriz_U[fila][columna] / matriz_U[fila_pivote][columna]



def factorizar_lu(matriz_A):
    """Obtiene L y U con A = LU usando solo reemplazos de fila; se detiene si hace falta un intercambio.

    Entrada: matriz_A (m × n). Salida: diccionario con matriz_L, matriz_U, pivotes, operaciones y etapas.
    """
    matriz_A = validar_matriz(matriz_A, "A")
    filas, columnas = len(matriz_A), len(matriz_A[0])
    matriz_U, matriz_L = copiar_matriz(matriz_A), matriz_identidad(filas)
    pivotes, operaciones, bloqueo, detalle = [], [], None, None
    etapas = [etapa(
        "Datos y condiciones",
        "U empieza como una copia de A y L como la identidad. Solo se usan reemplazos Fi ← Fi − l·Fj con i > j: "
        "cada uno anula una entrada debajo de un pivote y su multiplicador l se escribe en L en la posición (i, j).",
        formula="A = LU;  L: m×m triangular inferior con unos en la diagonal;  U: m×n forma escalonada de A",
        valores=[valor("A", matriz_A), valor("L inicial = I", matriz_L)],
        condiciones=[condicion(f"A es {filas}×{columnas}: L será {filas}×{filas} y U será {filas}×{columnas}."),
                     condicion("No se intercambian ni se escalan filas; solo reemplazos de filas inferiores.")])]

    fila_pivote = 0
    for columna in range(columnas):
        if fila_pivote >= filas:
            break
        fila_no_nula = buscar_fila_pivote(matriz_U, fila_pivote, columna)
        if fila_no_nula is None:
            etapas.append(etapa(
                f"Columna {columna + 1} sin pivote",
                f"Desde F{fila_pivote + 1} hacia abajo la columna {columna + 1} solo tiene ceros: no hay pivote ni nada "
                f"que anular. Se pasa a la columna siguiente sin operar (la variable x{columna + 1} será libre).",
                valores=[valor("U actual", matriz_U, filas=list(range(fila_pivote, filas)))]))
            continue
        # Un intercambio exigiría una matriz de permutación (PA = LU): con solo reemplazos L ya no sería válida para A.
        if fila_no_nula != fila_pivote:
            bloqueo = (fila_pivote, columna, fila_no_nula)
            detalle = (f"El pivote ({fila_pivote + 1},{columna + 1}) es 0 y F{fila_no_nula + 1} tiene "
                       f"{formatear_numero(matriz_U[fila_no_nula][columna])} en esa columna: para continuar habría que "
                       f"intercambiar F{fila_pivote + 1} con F{fila_no_nula + 1}, y un intercambio no es un reemplazo.")
            etapas.append(etapa(
                "Se requiere un intercambio de filas", detalle,
                valores=[valor("U parcial", matriz_U, pivotes=[(fila_pivote, columna)], filas=[fila_no_nula]),
                         valor("L parcial", matriz_L)],
                condiciones=[condicion(f"El pivote ({fila_pivote + 1},{columna + 1}) debe ser distinto de 0 para "
                                       f"eliminar con reemplazos.", False)],
                conclusion=MENSAJE_SIN_PERMUTACION))
            break

        pivote = matriz_U[fila_pivote][columna]
        pivotes.append((fila_pivote, columna))
        lineas_multiplicadores = []
        for fila in range(fila_pivote + 1, filas):
            multiplicador_l = calcular_multiplicador(matriz_U, fila, fila_pivote, columna)
            lineas_multiplicadores.append(
                f"l{fila + 1},{fila_pivote + 1} = u{fila + 1},{columna + 1} / u{fila_pivote + 1},{columna + 1} = "
                f"{_p(matriz_U[fila][columna])} / {_p(pivote)} = {formatear_numero(multiplicador_l)}"
                + ("   (ya es 0: no se opera)" if multiplicador_l == 0 else ""))
        etapas.append(etapa(
            f"Pivote ({fila_pivote + 1},{columna + 1}) = {formatear_numero(pivote)}",
            f"Cada multiplicador es (elemento a eliminar) / (pivote) y se guarda en la columna {fila_pivote + 1} de L."
            if lineas_multiplicadores else "Es la última fila: no hay entradas debajo del pivote.",
            formula=f"l(i,{fila_pivote + 1}) = u(i,{columna + 1}) / u({fila_pivote + 1},{columna + 1})"
            if lineas_multiplicadores else "",
            valores=[valor("U actual", matriz_U, pivotes=[(fila_pivote, columna)])], calculos=lineas_multiplicadores))

        for fila in range(fila_pivote + 1, filas):
            multiplicador_l = calcular_multiplicador(matriz_U, fila, fila_pivote, columna)
            # Se registra el multiplicador en L antes de alterar la fila en U.
            matriz_L[fila][fila_pivote] = multiplicador_l
            if multiplicador_l == 0:
                continue
            fila_original = matriz_U[fila][:]
            sumar_multiplo_fila(matriz_U, fila, fila_pivote, -multiplicador_l)
            operacion = texto_resta_de_filas(fila, fila_pivote, multiplicador_l)
            operaciones.append({"operacion": operacion, "fila": fila, "fila_pivote": fila_pivote, "columna": columna,
                                "multiplicador": multiplicador_l})
            etapas.append(etapa(
                operacion,
                f"Se anula la entrada ({fila + 1},{columna + 1}) debajo del pivote. El multiplicador "
                f"{formatear_numero(multiplicador_l)} queda en L en la posición ({fila + 1},{fila_pivote + 1}).",
                formula=f"F{fila + 1} ← F{fila + 1} − ({formatear_numero(multiplicador_l)})·F{fila_pivote + 1};  "
                        f"l{fila + 1},{fila_pivote + 1} = {formatear_numero(multiplicador_l)}",
                valores=[valor("U después del reemplazo", matriz_U, pivotes=[(fila_pivote, columna)], filas=[fila]),
                         valor("L con el multiplicador", matriz_L, pivotes=[(fila, fila_pivote)])],
                calculos=[f"F{fila + 1}, columna {j + 1}: {_p(fila_original[j])} − {_p(multiplicador_l)}·"
                          f"{_p(matriz_U[fila_pivote][j])} = {formatear_numero(matriz_U[fila][j])}" for j in range(columnas)]))
        fila_pivote += 1

    existe = bloqueo is None
    if existe:
        etapas.append(etapa(
            "Factorización obtenida",
            "L contiene, en el orden en que se aplicaron, los multiplicadores de cada reemplazo; U es la forma "
            "escalonada de A.",
            formula="A = LU",
            valores=[valor("L", matriz_L), valor("U", matriz_U, pivotes=pivotes)],
            calculos=[f"l{o['fila'] + 1},{o['fila_pivote'] + 1} = {formatear_numero(o['multiplicador'])}  ←  "
                      f"{o['operacion']}" for o in operaciones]
            or ["No hubo reemplazos: A ya estaba en forma escalonada y L = I."],
            condiciones=[condicion(f"L es {filas}×{filas} triangular inferior con unos en la diagonal.",
                                   es_triangular_inferior_unitaria(matriz_L)),
                         condicion(f"U es {filas}×{columnas} y está en forma escalonada con {len(pivotes)} pivote(s).",
                                   pivotes_escalonada(matriz_U) == pivotes)],
            conclusion="Se obtuvo A = LU usando solo reemplazos de filas."))
    return {"matriz_A": matriz_A, "existe": existe, "mensaje": None if existe else MENSAJE_SIN_PERMUTACION,
            "detalle": detalle, "bloqueo": bloqueo,
            "matriz_L": matriz_L if existe else None, "matriz_U": matriz_U if existe else None,
            "L_parcial": copiar_matriz(matriz_L), "U_parcial": copiar_matriz(matriz_U),
            "pivotes": pivotes, "columnas_pivote": [c for _, c in pivotes], "rango": len(pivotes),
            "operaciones": operaciones, "etapas": etapas}


def verificar_factorizacion(matriz_A, matriz_L, matriz_U):
    """Multiplica L · U con el producto matricial de la Calculadora y lo compara con A.

    Entrada: A, L y U (listas anidadas). Salida: diccionario con producto_LU, correcta (bool) y mensaje.
    """
    producto_LU = multiplicar_matrices(matriz_L, matriz_U)
    correcta = son_iguales(producto_LU, matriz_A)
    return {"producto_LU": producto_LU, "correcta": correcta,
            "mensaje": MENSAJE_FACTORIZACION_CORRECTA if correcta else MENSAJE_FACTORIZACION_INCORRECTA}



def sustitucion_adelante(matriz_L, vector_b):
    """Resuelve Ly = b reduciendo [L | b] de arriba hacia abajo (sustitución hacia adelante).

    Entrada: L (m × m, sin ceros en la diagonal) y b (m). Salida: diccionario con vector_y, matriz reducida y etapas.
    """
    matriz_L = validar_matriz(matriz_L, "L")
    vector_b = _vector(vector_b, "b")
    orden = len(matriz_L)
    if len(matriz_L[0]) != orden or any(matriz_L[i][j] != 0 for i in range(orden) for j in range(i + 1, orden)):
        raise ValueError("L debe ser cuadrada y triangular inferior.")
    if any(matriz_L[i][i] == 0 for i in range(orden)):
        raise ValueError("La diagonal de L no puede tener ceros.")
    if len(vector_b) != orden:
        raise ValueError(f"b debe tener {orden} componentes, una por cada fila de L.")
    nombres_y = obtener_nombres_variables(orden, "y")
    aumentada = crear_matriz_aumentada(matriz_L, vector_b)
    etapas = [etapa("Plantear [L | b]", "L es triangular inferior: la ecuación i solo contiene y1, …, yi.",
                    formula="yᵢ = (bᵢ − Σⱼ₍ⱼ<ᵢ₎ lᵢⱼ·yⱼ) / lᵢᵢ",
                    valores=[valor("[L | b]", aumentada, separador=orden)],
                    calculos=[_ecuacion(matriz_L[i][:i + 1], nombres_y, vector_b[i]) for i in range(orden)])]
    vector_y = []
    for columna in range(orden):
        conocidos = [(matriz_L[columna][j], j) for j in range(columna) if matriz_L[columna][j] != 0]
        restas = "".join(f" − {_p(coeficiente)}·{_p(vector_y[j])}" for coeficiente, j in conocidos)
        diagonal = aumentada[columna][columna]
        calculos = []
        if diagonal != 1:
            # Dividir por la diagonal deja el coeficiente de y en 1 y despeja su valor en el lado derecho.
            multiplicar_fila(aumentada, columna, Fraction(1) / diagonal)
            calculos.append(f"F{columna + 1} ← ({formatear_numero(Fraction(1) / diagonal)})F{columna + 1}")
        vector_y.append(aumentada[columna][-1])
        calculos.insert(0, f"{_despeje(nombres_y[columna], vector_b[columna], restas, matriz_L[columna][columna])} = "
                           f"{formatear_numero(vector_y[columna])}")
        filas_cambiadas = []
        for fila in range(columna + 1, orden):
            factor = aumentada[fila][columna]
            if factor == 0:
                continue
            lado_derecho = aumentada[fila][-1]
            sumar_multiplo_fila(aumentada, fila, columna, -factor)
            filas_cambiadas.append(fila)
            calculos.append(f"{texto_resta_de_filas(fila, columna, factor)}: lado derecho {_p(lado_derecho)} − "
                            f"{_p(factor)}·{_p(vector_y[columna])} = {formatear_numero(aumentada[fila][-1])}")
        etapas.append(etapa(
            f"Columna {columna + 1}: {nombres_y[columna]} = {formatear_numero(vector_y[columna])}",
            f"{nombres_y[columna]} queda despejada; se sustituye en las ecuaciones de abajo." if filas_cambiadas
            else f"{nombres_y[columna]} queda despejada.",
            valores=[valor("[L | b] en reducción", aumentada, separador=orden, pivotes=[(columna, columna)],
                           filas=filas_cambiadas)],
            calculos=calculos))
    etapas.append(etapa("Vector intermedio y", "Al terminar la reducción, [L | b] queda [I | y].", formula="Ly = b",
                        valores=[valor("y", vector_y)], conclusion="y es la entrada de la sustitución hacia atrás."))
    return {"matriz_L": copiar_matriz(matriz_L), "vector_b": vector_b[:], "vector_y": vector_y,
            "matriz_reducida": aumentada, "etapas": etapas}


def sustitucion_atras(matriz_U, vector_y, pivotes=None):
    """Resuelve Ux = y reduciendo [U | y] desde el último pivote hacia arriba (sustitución hacia atrás).

    Entrada: U escalonada (m × n), y (m) y pivotes opcionales. Salida: diccionario con la clasificación y x o la familia.
    """
    matriz_U = validar_matriz(matriz_U, "U")
    vector_y = _vector(vector_y, "y")
    filas, columnas = len(matriz_U), len(matriz_U[0])
    if len(vector_y) != filas:
        raise ValueError(f"y debe tener {filas} componentes, una por cada fila de U.")
    escalonada = pivotes_escalonada(matriz_U)
    if escalonada is None or (pivotes is not None and [tuple(p) for p in pivotes] != escalonada):
        raise ValueError("U debe estar en forma escalonada por filas.")
    pivotes = escalonada
    nombres_x = obtener_nombres_variables(columnas)
    aumentada = crear_matriz_aumentada(matriz_U, vector_y)
    columnas_pivote = [c for _, c in pivotes]
    libres = [c for c in range(columnas) if c not in columnas_pivote]
    parametros = dict(zip(libres, nombres_parametros(len(libres))))
    etapas = [etapa("Plantear [U | y]", "Se reduce desde la última fila con pivote hacia arriba.",
                    formula="x(pivote) = (yₖ − Σ uₖⱼ·xⱼ) / uₖ,pivote",
                    valores=[valor("[U | y]", aumentada, separador=columnas, pivotes=pivotes)],
                    calculos=[_ecuacion(matriz_U[i], nombres_x, vector_y[i]) for i in range(filas)])]
    filas_nulas = list(range(len(pivotes), filas))
    inconsistentes = [i for i in filas_nulas if fila_inconsistente(aumentada[i], columnas)]
    base = {"matriz_U": copiar_matriz(matriz_U), "vector_y": vector_y[:], "pivotes": pivotes,
            "nombres_variables": nombres_x, "variables_basicas": columnas_pivote, "variables_libres": libres,
            "filas_inconsistentes": inconsistentes, "matriz_final": copiar_matriz(aumentada), "solucion": None,
            "solucion_particular": None, "forma_vectorial": None, "expresiones": None, "parametros": {}}
    if filas_nulas:
        etapas.append(etapa(
            "Filas nulas de U", "Una fila nula de U es la ecuación 0 = yᵢ: solo es válida si yᵢ = 0.",
            calculos=[f"Fila {i + 1}: 0 = {formatear_numero(vector_y[i])}  "
                      + ("✓" if vector_y[i] == 0 else "✗ contradicción") for i in filas_nulas],
            condiciones=[condicion(f"y{i + 1} = 0", vector_y[i] == 0) for i in filas_nulas]))
    if inconsistentes:
        fila = inconsistentes[0]
        etapas.append(etapa("Sistema inconsistente", conclusion=(
            f"No se cumple: la fila {fila + 1} de [U | y] es 0 = {formatear_numero(vector_y[fila])}; ningún x satisface "
            f"Ux = y y, por tanto, tampoco Ax = b.")))
        clasificacion, descripcion = clasificar_sistema(aumentada, columnas_pivote, columnas)
        return {**base, "clasificacion": clasificacion, "descripcion": descripcion,
                "matriz_reducida": aumentada, "etapas": etapas}
    if libres:
        etapas.append(etapa("Variables libres",
                            "Las columnas de U sin pivote corresponden a variables libres: toman cualquier valor real.",
                            calculos=[f"{nombres_x[c]} = {parametros[c]}  (columna {c + 1} sin pivote)" for c in libres]))

    for fila, columna in reversed(pivotes):
        calculos = []
        pivote = aumentada[fila][columna]
        if pivote != 1:
            multiplicar_fila(aumentada, fila, Fraction(1) / pivote)
            calculos.append(f"F{fila + 1} ← ({formatear_numero(Fraction(1) / pivote)})F{fila + 1}: el coeficiente de "
                            f"{nombres_x[columna]} pasa a ser 1")
        # Las columnas pivote de la derecha ya se anularon en esta fila: solo quedan variables libres.
        expresion = _texto_afin(aumentada[fila][-1], [-aumentada[fila][j] for j in libres],
                                [parametros[j] for j in libres])
        calculos.append(f"{nombres_x[columna]} = {expresion}")
        filas_cambiadas = []
        for fila_superior in range(fila):
            factor = aumentada[fila_superior][columna]
            if factor == 0:
                continue
            sumar_multiplo_fila(aumentada, fila_superior, fila, -factor)
            filas_cambiadas.append(fila_superior)
            calculos.append(f"{texto_resta_de_filas(fila_superior, fila, factor)}: se sustituye {nombres_x[columna]} "
                            f"en la ecuación {fila_superior + 1}")
        etapas.append(etapa(
            f"Despejar {nombres_x[columna]} (fila {fila + 1})",
            "Se despeja la variable del pivote y se sustituye en las ecuaciones de arriba." if filas_cambiadas
            else "Se despeja la variable del pivote.",
            valores=[valor("[U | y] en reducción", aumentada, separador=columnas, pivotes=[(fila, columna)],
                           filas=filas_cambiadas)],
            calculos=calculos))

    clasificacion, descripcion = clasificar_sistema(aumentada, columnas_pivote, columnas)
    if libres:
        expresiones, _, parametros = obtener_solucion_parametrica(aumentada, columnas_pivote, columnas)
        particular, direcciones = obtener_forma_vectorial(aumentada, columnas_pivote, columnas)
        etapas.append(etapa("Solución general", formula="x = p + Σ t·v (los parámetros son arbitrarios)",
                            valores=[valor("Particular p", particular)] +
                                    [valor(f"Dirección de {t}", v) for t, v in direcciones],
                            calculos=[f"{nombres_x[j]} = {texto}" for j, texto in expresiones.items()]))
        return {**base, "clasificacion": clasificacion, "descripcion": descripcion, "matriz_reducida": aumentada,
                "solucion_particular": particular, "forma_vectorial": (particular, direcciones),
                "expresiones": expresiones, "parametros": parametros, "etapas": etapas}
    vector_x = obtener_solucion_unica(aumentada, columnas_pivote, columnas)
    etapas.append(etapa("Solución final x", "Al terminar la reducción, [U | y] queda en forma escalonada reducida.",
                        formula="Ux = y", valores=[valor("x", vector_x)],
                        calculos=[f"{nombres_x[j]} = {formatear_numero(v)}" for j, v in enumerate(vector_x)]))
    return {**base, "clasificacion": clasificacion, "descripcion": descripcion, "matriz_reducida": aumentada,
            "solucion": vector_x, "etapas": etapas}


def comprobar_solucion(matriz_A, vector_x, vector_b, direcciones=()):
    """Calcula A · x con el producto matriz-vector de la Calculadora, lo compara con b y exige A·v = 0.

    Entrada: A, x (o la particular), b y direcciones paramétricas. Salida: diccionario con productos, correcta y mensaje.
    """
    producto_Ax = multiplicar_matriz_vector(matriz_A, vector_x)
    vector_cero = [Fraction(0)] * len(matriz_A)
    productos_Av = [(parametro, multiplicar_matriz_vector(matriz_A, direccion)) for parametro, direccion in direcciones]
    correcta = son_iguales(producto_Ax, vector_b) and all(son_iguales(av, vector_cero) for _, av in productos_Av)
    return {"producto_Ax": producto_Ax, "productos_Av": productos_Av, "correcta": correcta,
            "mensaje": MENSAJE_COMPROBACION_EXITOSA if correcta else MENSAJE_COMPROBACION_FALLIDA}



def resolver_lu(matriz_A, vector_b):
    """Encadena factorizar_lu → verificar_factorizacion → [L | b] → [U | y] → comprobar_solucion.

    Entrada: A (m × n) y b (m). Salida: diccionario con L, U, y, x (o familia o inconsistencia), mensajes y etapas.
    """
    matriz_A = validar_matriz(matriz_A, "A")
    vector_b = _vector(vector_b, "b")
    filas, columnas = len(matriz_A), len(matriz_A[0])
    if len(vector_b) != filas:
        raise ValueError(f"b debe tener {filas} componentes, una por cada fila de A.")
    factorizacion = factorizar_lu(matriz_A)
    etapas = [etapa("Etapa 1 · Factorización A = LU",
                    "Se reduce A a una forma escalonada U con reemplazos; L registra los multiplicadores. "
                    "Después se resuelve Ax = b como L(Ux) = b en dos etapas sustitutivas.",
                    formula="Ax = b  ⇔  Ly = b  y  Ux = y"),
              *factorizacion["etapas"]]
    resultado = {"matriz_A": matriz_A, "vector_b": vector_b, "m": filas, "n": columnas,
                 "factorizacion": factorizacion, "existe": factorizacion["existe"],
                 "mensaje": factorizacion["mensaje"], "detalle": factorizacion["detalle"],
                 "matriz_L": factorizacion["matriz_L"], "matriz_U": factorizacion["matriz_U"],
                 "pivotes": factorizacion["pivotes"], "rango": factorizacion["rango"],
                 "verificacion_factorizacion": None, "adelante": None, "atras": None, "vector_y": None,
                 "comprobacion": None, "determinante": None, "etapas": etapas}
    if not factorizacion["existe"]:
        resultado.update(clasificacion="Factorización LU no disponible", descripcion=MENSAJE_SIN_PERMUTACION,
                         solucion=None, expresiones=None, solucion_particular=None, forma_vectorial=None)
        return resultado

    matriz_L, matriz_U = factorizacion["matriz_L"], factorizacion["matriz_U"]
    verificacion_LU = verificar_factorizacion(matriz_A, matriz_L, matriz_U)
    etapas.append(etapa("Verificar la factorización: L · U == A",
                        "L · U se calcula con la función de producto matricial de la Calculadora y se compara con A.",
                        valores=[valor("L · U", verificacion_LU["producto_LU"]), valor("A", matriz_A)],
                        conclusion=verificacion_LU["mensaje"]))

    adelante = sustitucion_adelante(matriz_L, vector_b)
    etapas += [etapa("Etapa 2 · Sustitución hacia adelante: Ly = b",
                     "Encadenamiento: L es la salida de la etapa 1 y b es el vector original.",
                     condiciones=[condicion("L proviene de la factorización (etapa 1)."),
                                  condicion("b es el lado derecho original de Ax = b.")]),
               *adelante["etapas"]]
    atras = sustitucion_atras(matriz_U, adelante["vector_y"], factorizacion["pivotes"])
    etapas += [etapa("Etapa 3 · Sustitución hacia atrás: Ux = y",
                     "Encadenamiento: U es la salida de la etapa 1 y y es la salida de la etapa 2.",
                     condiciones=[condicion("U proviene de la factorización (etapa 1)."),
                                  condicion("y proviene de la sustitución hacia adelante (etapa 2).")]),
               *atras["etapas"]]

    if atras["clasificacion"] == "Sistema inconsistente":
        comprobacion = {"producto_Ax": None, "productos_Av": [], "correcta": None, "mensaje": MENSAJE_SIN_SOLUCION}
    else:
        vector_x = atras["solucion"] if atras["solucion"] is not None else atras["solucion_particular"]
        direcciones = atras["forma_vectorial"][1] if atras["forma_vectorial"] else []
        comprobacion = comprobar_solucion(matriz_A, vector_x, vector_b, direcciones)
        etapas.append(etapa(
            "Comprobar A · x == b",
            "Se sustituye x en el sistema original con el producto matriz-vector de la Calculadora."
            + (" Para la familia paramétrica se comprueba A·p = b y A·v = 0 en cada dirección." if direcciones else ""),
            valores=[valor("A · x" if not direcciones else "A · p", comprobacion["producto_Ax"]), valor("b", vector_b)]
            + [valor(f"A · v({t})", av) for t, av in comprobacion["productos_Av"]],
            conclusion=comprobacion["mensaje"]))

    resultado.update({clave: atras[clave] for clave in (
        "clasificacion", "descripcion", "solucion", "solucion_particular", "forma_vectorial", "expresiones",
        "parametros", "nombres_variables", "variables_basicas", "variables_libres", "filas_inconsistentes",
        "matriz_final")})
    resultado.update(verificacion_factorizacion=verificacion_LU, adelante=adelante, atras=atras,
                     vector_y=adelante["vector_y"], comprobacion=comprobacion)
    resultado["cadena"] = [
        {"etapa": "Factorización", "entradas": {"A": matriz_A}, "salidas": {"L": matriz_L, "U": matriz_U}},
        {"etapa": "Sustitución hacia adelante", "entradas": {"L": adelante["matriz_L"], "b": adelante["vector_b"]},
         "salidas": {"y": adelante["vector_y"]}},
        {"etapa": "Sustitución hacia atrás", "entradas": {"U": atras["matriz_U"], "y": atras["vector_y"]},
         "salidas": {"x": atras["solucion"] if atras["solucion"] is not None else atras["solucion_particular"]}},
    ]
    if filas == columnas:
        diagonal = [matriz_U[i][i] for i in range(filas)]
        producto_diagonal = Fraction(1)
        for entrada in diagonal:
            producto_diagonal *= entrada
        resultado["determinante"] = producto_diagonal
        etapas.append(etapa(
            "Consecuencia: det(A) desde U",
            "L es triangular con unos en la diagonal (det(L) = 1) y U es triangular superior.",
            formula="det(A) = det(L)·det(U) = 1·∏ uᵢᵢ",
            calculos=[" · ".join(_p(d) for d in diagonal) + f" = {formatear_numero(producto_diagonal)}"],
            conclusion="A es invertible (det(A) ≠ 0)." if producto_diagonal else "A es singular (det(A) = 0)."))
    return resultado


def verificar_lu(resultado, matriz_A=None, vector_b=None):
    """Comprueba desde los datos originales el encadenamiento, L·U = A, Ly = b, Ux = y y A·x = b.

    Entrada: resultado de resolver_lu y, opcionalmente, A y b. Salida: diccionario con correcto, etapas y chequeos.
    """
    matriz_A = validar_matriz(matriz_A if matriz_A is not None else resultado["matriz_A"], "A")
    vector_b = _vector(vector_b if vector_b is not None else resultado["vector_b"], "b")
    filas, columnas = len(matriz_A), len(matriz_A[0])
    factorizacion = resultado["factorizacion"]
    etapas, chequeos = [], []

    def registrar(nombre, correcto):
        """Anota una comprobación con su nombre y su resultado.

        Entrada: nombre y correcto (bool). Salida: None.
        """
        chequeos.append({"nombre": nombre, "correcto": bool(correcto)})

    def lu_frente_a_A(matriz_L, matriz_U, titulo):
        """Calcula L·U con el producto de la Calculadora, lo compara con A y lo registra.

        Entrada: L, U y título del chequeo. Salida: None.
        """
        producto_LU, paso = producto(matriz_L, matriz_U, "L·U")
        etapas.extend([paso, comparar(producto_LU, matriz_A, "L·U frente a A original")])
        registrar(titulo, son_iguales(producto_LU, matriz_A))

    if not factorizacion["existe"]:
        fila_pivote, columna, fila_no_nula = factorizacion["bloqueo"]
        matriz_L, matriz_U = factorizacion["L_parcial"], factorizacion["U_parcial"]
        etapas.append(etapa("Diagnóstico a comprobar", factorizacion["detalle"], conclusion=MENSAJE_SIN_PERMUTACION))
        lu_frente_a_A(matriz_L, matriz_U, "Eliminación parcial correcta")
        previas = all(matriz_U[i][c] == 0 for k, c in factorizacion["pivotes"] for i in range(k + 1, filas))
        bloqueado = matriz_U[fila_pivote][columna] == 0 and matriz_U[fila_no_nula][columna] != 0
        etapas.append(etapa(
            "Condición que impide continuar sin intercambios",
            valores=[valor("U parcial", matriz_U, pivotes=[(fila_pivote, columna)], filas=[fila_no_nula])],
            calculos=[f"u{fila_pivote + 1},{columna + 1} = {formatear_numero(matriz_U[fila_pivote][columna])}",
                      f"u{fila_no_nula + 1},{columna + 1} = {formatear_numero(matriz_U[fila_no_nula][columna])}"],
            condiciones=[condicion("Las columnas pivote anteriores ya tienen ceros debajo del pivote.", previas),
                         condicion("La posición pivote vale 0 y hay un valor distinto de cero debajo.", bloqueado)],
            conclusion="Se cumple: el diagnóstico es correcto; hace falta un intercambio (PA = LU)."
            if previas and bloqueado else "No se cumple"))
        registrar("Bloqueo confirmado", previas and bloqueado)
        return {"aplicable": True, "correcto": all(c["correcto"] for c in chequeos), "etapas": etapas,
                "chequeos": chequeos}

    matriz_L, matriz_U = resultado["matriz_L"], resultado["matriz_U"]
    adelante, atras = resultado["adelante"], resultado["atras"]
    vector_x = atras["solucion"] if atras["solucion"] is not None else atras["solucion_particular"]
    salida = resultado["solucion"] if resultado["solucion"] is not None else resultado["solucion_particular"]

    enlaces = [("La etapa 1 factorizó la A original (sin modificarla).", factorizacion["matriz_A"] == matriz_A),
               ("La etapa 2 usa la L obtenida en la etapa 1.", adelante["matriz_L"] == factorizacion["matriz_L"] == matriz_L),
               ("La etapa 2 usa el b original.", adelante["vector_b"] == vector_b),
               ("La etapa 3 usa la U obtenida en la etapa 1.", atras["matriz_U"] == factorizacion["matriz_U"] == matriz_U),
               ("La etapa 3 usa como lado derecho la y obtenida en la etapa 2.",
                atras["vector_y"] == adelante["vector_y"] == resultado["vector_y"]),
               ("La solución informada es la salida de la etapa 3.", salida == vector_x)]
    etapas.append(etapa("Encadenamiento de datos",
                        "Cada etapa debe recibir exactamente la salida de la anterior: A → (L, U) → y → x.",
                        valores=[valor("y (salida de la etapa 2)", adelante["vector_y"]),
                                 valor("y (entrada de la etapa 3)", atras["vector_y"])],
                        condiciones=[condicion(texto, ok) for texto, ok in enlaces],
                        conclusion="Se cumple" if all(ok for _, ok in enlaces) else "No se cumple"))
    registrar("Encadenamiento de datos", all(ok for _, ok in enlaces))

    direcciones = atras["forma_vectorial"][1] if atras["forma_vectorial"] else []
    tamanos = [(f"L es {filas}×{filas}.", _es_matriz(matriz_L, filas, filas)),
               (f"U es {filas}×{columnas}.", _es_matriz(matriz_U, filas, columnas)),
               (f"y tiene {filas} componentes.",
                _es_vector(adelante["vector_y"], filas) and _es_vector(atras["vector_y"], filas)),
               (f"x tiene {columnas} componentes.", vector_x is None or _es_vector(vector_x, columnas)),
               (f"Cada dirección tiene {columnas} componentes.", all(_es_vector(v, columnas) for _, v in direcciones)),
               ("Hay solución informada si y solo si el sistema no es inconsistente.",
                (vector_x is None) == (resultado["clasificacion"] == "Sistema inconsistente"))]
    operable = all(ok for _, ok in tamanos)
    pivotes = pivotes_escalonada(matriz_U) if operable else None
    estructura = tamanos + [
        ("L es triangular inferior con unos en la diagonal.", operable and es_triangular_inferior_unitaria(matriz_L)),
        ("U está en forma escalonada por filas.", pivotes is not None),
        ("Los pivotes de U son los informados.", pivotes is not None and pivotes == resultado["pivotes"])]
    if filas == columnas:
        estructura.append(("A es cuadrada: se informa det(A) = ∏ uᵢᵢ.", resultado["determinante"] is not None))
    etapas.append(etapa("Estructura de L, U, y y x",
                        valores=[valor("L", matriz_L), valor("U", matriz_U, pivotes=pivotes or [])] if operable else [],
                        condiciones=[condicion(texto, ok) for texto, ok in estructura]))
    registrar("Estructura de los resultados", all(ok for _, ok in estructura))
    if not operable:
        etapas.append(etapa("Conclusión de la verificación", conclusion=(
            "No se cumple: los resultados no tienen las dimensiones que exige A = LU, Ly = b y Ux = y.")))
        return {"aplicable": True, "correcto": False, "etapas": etapas, "chequeos": chequeos}

    lu_frente_a_A(matriz_L, matriz_U, "L·U = A")

    escalonada, _, _ = forma_escalonada(crear_matriz_aumentada(matriz_A, [Fraction(0)] * filas), columnas)
    u_recalculada = [fila[:columnas] for fila in escalonada]
    etapas.append(etapa("U por otro algoritmo",
                        "La eliminación gaussiana del módulo de sistemas, aplicada a la A original, debe producir la "
                        "misma U (no se escalan filas)."))
    etapas.append(comparar(matriz_U, u_recalculada, "U frente a la forma escalonada recalculada"))
    registrar("U recalculada", son_iguales(matriz_U, u_recalculada))

    producto_Ly, paso = producto_vector(matriz_L, adelante["vector_y"], "L·y")
    etapas += [paso, comparar(producto_Ly, vector_b, "L·y frente a b original")]
    registrar("L·y = b", son_iguales(producto_Ly, vector_b))

    if resultado["clasificacion"] == "Sistema inconsistente":
        filas_nulas = [i for i in range(filas) if all(entrada == 0 for entrada in matriz_U[i])]
        contradicciones = [i for i in filas_nulas if adelante["vector_y"][i] != 0]
        etapas.append(etapa("Ux = y es incompatible", "Una fila nula de U con yᵢ ≠ 0 es la ecuación 0 = yᵢ.",
                            calculos=[f"Fila {i + 1}: 0 = {formatear_numero(adelante['vector_y'][i])}" for i in filas_nulas],
                            condiciones=[condicion("Existe una fila nula de U con yᵢ ≠ 0.", bool(contradicciones))]))
        etapas.append(etapa("Comprobación independiente con la A original",
                            "Se busca una combinación de las ecuaciones originales que produzca 0 = c ≠ 0."))
        try:
            certificado = certificado_inconsistencia(matriz_A, vector_b)
        except ArithmeticError:
            certificado = {"correcto": False, "etapas": [etapa("Sin certificado", conclusion=(
                "No se cumple: el sistema original sí tiene solución, así que no es inconsistente."))]}
        etapas += certificado["etapas"]
        registrar("Inconsistencia", bool(contradicciones) and certificado["correcto"])
    else:
        nombre = "x" if not direcciones else "p"
        producto_Ux, paso = producto_vector(matriz_U, vector_x, f"U·{nombre}")
        etapas += [paso, comparar(producto_Ux, adelante["vector_y"], f"U·{nombre} frente a y")]
        producto_Ax, paso = producto_vector(matriz_A, vector_x, f"A·{nombre}")
        etapas += [etapa(f"Sustituir en el sistema original A·{nombre} = b", "Se usa la A original, no L ni U."),
                   paso, comparar(producto_Ax, vector_b, f"A·{nombre} frente a b original")]
        correcto = son_iguales(producto_Ux, adelante["vector_y"]) and son_iguales(producto_Ax, vector_b)
        vector_cero = [Fraction(0)] * filas
        for parametro, direccion in direcciones:
            producto_Uv = multiplicar_matriz_vector(matriz_U, direccion)
            producto_Av, paso = producto_vector(matriz_A, direccion, f"A·v({parametro})")
            etapas += [etapa(f"Dirección del parámetro {parametro}", "Debe cumplir Uv = 0 y Av = 0 (espacio nulo de A).",
                             valores=[valor("v", direccion)]), paso,
                       comparar(producto_Av, vector_cero, f"A·v({parametro}) frente a 0"),
                       comparar(producto_Uv, vector_cero, f"U·v({parametro}) frente a 0")]
            correcto = correcto and son_iguales(producto_Av, vector_cero) and son_iguales(producto_Uv, vector_cero)
        registrar("Solución en el sistema original", correcto)

        gauss = resolver_sistema(matriz_A, vector_b)
        etapas.append(etapa("Recálculo por Gauss-Jordan",
                            "Se resuelve la A original con [A | b] → RREF, sin usar L, U ni y.",
                            calculos=[f"Clasificación: {gauss['clasificacion']}"],
                            condiciones=[condicion("Misma clasificación que por LU.",
                                                   gauss["clasificacion"] == resultado["clasificacion"])]))
        coincide = gauss["clasificacion"] == resultado["clasificacion"]
        if gauss["solucion"] is not None:
            etapas.append(comparar(vector_x, gauss["solucion"], "x por LU frente a x por Gauss-Jordan"))
            coincide = coincide and son_iguales(vector_x, gauss["solucion"])
        elif gauss["forma_vectorial"] is not None:
            particular_gj, direcciones_gj = gauss["forma_vectorial"]
            etapas.append(comparar(vector_x, particular_gj, "p por LU frente a p por Gauss-Jordan"))
            coincide = coincide and son_iguales(vector_x, particular_gj) and len(direcciones_gj) == len(direcciones)
            for (parametro, direccion), (_, direccion_gj) in zip(direcciones, direcciones_gj):
                etapas.append(comparar(direccion, direccion_gj, f"Dirección de {parametro}: LU frente a Gauss-Jordan"))
                coincide = coincide and son_iguales(direccion, direccion_gj)
        registrar("Coincide con Gauss-Jordan", coincide)

    if resultado["determinante"] is not None:
        metodo = "sarrus" if filas == 3 else "cofactores"
        recalculo = calcular_determinante(matriz_A, metodo)
        etapas += [etapa(f"det(A) por {'Sarrus' if metodo == 'sarrus' else 'cofactores'}",
                         "Se recalcula el determinante desde la A original con otro método.", subpasos=recalculo["etapas"]),
                   comparar(resultado["determinante"], recalculo["determinante"], "det(A) por LU frente al recálculo")]
        registrar("Determinante", resultado["determinante"] == recalculo["determinante"])

    correcto = all(c["correcto"] for c in chequeos)
    etapas.append(etapa("Conclusión de la verificación",
                        calculos=[f"{'✓' if c['correcto'] else '✗'} {c['nombre']}" for c in chequeos],
                        conclusion="Se cumple: L·U = A y cada etapa coincide con los datos originales." if correcto
                        else "No se cumple: revisa las comprobaciones marcadas con ✗."))
    return {"aplicable": True, "correcto": correcto, "etapas": etapas, "chequeos": chequeos}


def formatear_resultado_lu(resultado):
    """Convierte el resultado en líneas de texto (L, U, mensajes, y, x y comprobación) para consola o copia.

    Entrada: diccionario de resolver_lu. Salida: lista de cadenas.
    """
    if not resultado["existe"]:
        return [MENSAJE_SIN_PERMUTACION, resultado["detalle"]]
    lineas = ["Matriz L:", matriz_a_texto(resultado["matriz_L"], False),
              "Matriz U:", matriz_a_texto(resultado["matriz_U"], False),
              resultado["verificacion_factorizacion"]["mensaje"],
              f"Vector intermedio y (Ly = b): {_texto_vector(resultado['vector_y'])}",
              f"{resultado['clasificacion']}: {resultado['descripcion']}"]
    nombres = resultado["nombres_variables"]
    if resultado["solucion"] is not None:
        lineas.append(f"Vector solución x (Ux = y): {_texto_vector(resultado['solucion'])}")
    elif resultado["expresiones"] is not None:
        lineas += [f"{nombres[i]} = {texto}" for i, texto in resultado["expresiones"].items()]
    lineas.append(resultado["comprobacion"]["mensaje"])
    if resultado["determinante"] is not None:
        lineas.append(f"det(A) = ∏ uᵢᵢ = {formatear_numero(resultado['determinante'])}")
    return lineas

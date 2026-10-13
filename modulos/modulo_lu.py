"""Factorización LU por reemplazo de filas y solución de Ax = b en dos etapas.

U es la forma escalonada de A obtenida solo con Fi → Fi − m·Fk (i > k).
L, triangular inferior con unos en la diagonal, guarda cada multiplicador m en (i, k).
Cada etapa recibe la salida exacta de la anterior: A → (L, U) → y → x.
La verificación recalcula LU, Ly, Ux y Ax desde los datos originales.
"""
from fractions import Fraction

from .informes import certificado_inconsistencia, comparar
from .modulo_matrices import (calcular_determinante, copiar_matriz, crear_matriz_aumentada, forma_escalonada,
                              formatear_numero, matriz_a_texto, matriz_identidad, nombres_parametros,
                              obtener_nombres_variables, resolver_sistema, texto_resta_de_filas, unir_terminos,
                              validar_matriz)
from .pasos import condicion, etapa, valor


def _p(numero):
    """Número entre paréntesis para sustituciones: (−1/2)."""
    return f"({formatear_numero(numero)})"


def _vector(datos, nombre):
    try:
        return [Fraction(v) for v in datos]
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError(f"{nombre} contiene una entrada no numérica válida.") from error


def _ecuacion(coeficientes, nombres, derecho):
    return f"{unir_terminos(zip(coeficientes, nombres))} = {formatear_numero(derecho)}"


def _despeje(incognita, independiente, restas, divisor):
    """'x = (y − …) / (u)'; omite paréntesis y divisor cuando sobran."""
    numerador = f"{formatear_numero(independiente)}{restas}"
    if divisor == 1:
        return f"{incognita} = {numerador}"
    return f"{incognita} = " + (f"({numerador})" if restas else numerador) + f" / {_p(divisor)}"


def _texto_afin(forma, parametros):
    """[c, a1, a2] con parámetros (s, t) -> 'c + a1·s + a2·t' sin términos nulos."""
    constante, coeficientes = forma[0], forma[1:]
    variable = unir_terminos(zip(coeficientes, parametros))
    if variable == "0":
        return formatear_numero(constante)
    if constante == 0:
        return variable
    signo, cuerpo = ("-", variable[1:]) if variable.startswith("-") else ("+", variable)
    return f"{formatear_numero(constante)} {signo} {cuerpo}"


def es_triangular_inferior_unitaria(L):
    """True si L es cuadrada, con ceros sobre la diagonal y unos en la diagonal."""
    n = len(L)
    return (all(len(fila) == n for fila in L) and all(L[i][i] == 1 for i in range(n))
            and all(L[i][j] == 0 for i in range(n) for j in range(i + 1, n)))


def pivotes_escalonada(U):
    """Posiciones pivote de U, o None si U no está en forma escalonada por filas."""
    pivotes, anterior, hubo_nula = [], -1, False
    for i, fila in enumerate(U):
        columna = next((j for j, v in enumerate(fila) if v != 0), None)
        if columna is None:
            hubo_nula = True
            continue
        if hubo_nula or columna <= anterior:
            return None
        pivotes.append((i, columna))
        anterior = columna
    return pivotes


def _producto(X, Y, nombre):
    """Producto fila por columna con el desarrollo de cada entrada."""
    R = [[sum((X[i][k] * Y[k][j] for k in range(len(Y))), Fraction(0)) for j in range(len(Y[0]))]
         for i in range(len(X))]
    lineas = [f"({nombre}){i + 1},{j + 1} = " + " + ".join(f"{_p(X[i][k])}{_p(Y[k][j])}" for k in range(len(Y)))
              + f" = {formatear_numero(R[i][j])}" for i in range(len(X)) for j in range(len(Y[0]))]
    return R, lineas


def _producto_vector(X, v, nombre):
    r = [sum((a * b for a, b in zip(fila, v)), Fraction(0)) for fila in X]
    lineas = [f"({nombre}){i + 1} = " + " + ".join(f"{_p(a)}{_p(b)}" for a, b in zip(fila, v))
              + f" = {formatear_numero(r[i])}" for i, fila in enumerate(X)]
    return r, lineas


# -----------------------------------------------------------------------------
# Etapa 1: factorización A = LU
# -----------------------------------------------------------------------------

def factorizar_lu(A):
    """
    Reduce A (m×n) a una forma escalonada U usando solo reemplazos de una fila
    inferior con un múltiplo de la fila pivote. Cada multiplicador se guarda en L.
    Si una posición pivote es 0 y debajo hay un valor distinto de cero, haría falta
    un intercambio: se informa que A = LU (sin permutación) no existe.
    """
    A = validar_matriz(A, "A")
    filas, columnas = len(A), len(A[0])
    U, L = copiar_matriz(A), matriz_identidad(filas)
    pivotes, operaciones = [], []
    bloqueo, motivo = None, None
    etapas = [etapa(
        "Datos y condiciones",
        "U empieza como una copia de A y L como la identidad. Solo se usan reemplazos Fi → Fi − m·Fk con i > k: "
        "cada uno anula una entrada debajo de un pivote y su multiplicador m se escribe en L en la posición (i, k).",
        formula="A = LU;  L: m×m triangular inferior con unos en la diagonal;  U: m×n forma escalonada de A",
        valores=[valor("A", A), valor("L inicial = I", L)],
        condiciones=[condicion(f"A es {filas}×{columnas}: L será {filas}×{filas} y U será {filas}×{columnas}."),
                     condicion("No se intercambian ni se escalan filas; solo reemplazos de filas inferiores.")])]

    fila = 0
    for columna in range(columnas):
        if fila >= filas:
            break
        if U[fila][columna] == 0:
            debajo = next((i for i in range(fila + 1, filas) if U[i][columna] != 0), None)
            if debajo is None:
                etapas.append(etapa(
                    f"Columna {columna + 1} sin pivote",
                    f"Desde F{fila + 1} hacia abajo la columna {columna + 1} solo tiene ceros: no hay pivote ni nada "
                    f"que anular. Se pasa a la columna siguiente sin operar (la variable x{columna + 1} será libre).",
                    valores=[valor("U actual", U, filas=list(range(fila, filas)))]))
                continue
            bloqueo = (fila, columna, debajo)
            motivo = (f"La posición pivote ({fila + 1},{columna + 1}) vale 0 y F{debajo + 1} tiene "
                      f"{formatear_numero(U[debajo][columna])} en esa columna. Para seguir habría que intercambiar "
                      f"F{fila + 1} con F{debajo + 1}, y un intercambio no es una operación de reemplazo: A no admite "
                      f"una factorización A = LU sin permutar filas (se necesitaría PA = LU).")
            etapas.append(etapa(
                "Se requiere un intercambio de filas", motivo,
                valores=[valor("U parcial", U, pivotes=[(fila, columna)], filas=[debajo]),
                         valor("L parcial", L)],
                condiciones=[condicion(f"La posición pivote ({fila + 1},{columna + 1}) debe ser distinta de 0 para "
                                       f"eliminar con reemplazos.", False)],
                conclusion="No se cumple: la factorización LU sin intercambios no existe para esta A."))
            break

        pivote = U[fila][columna]
        pivotes.append((fila, columna))
        multiplicadores = []
        for i in range(fila + 1, filas):
            m = U[i][columna] / pivote
            multiplicadores.append(
                f"l{i + 1},{fila + 1} = u{i + 1},{columna + 1} / u{fila + 1},{columna + 1} = "
                f"{_p(U[i][columna])} / {_p(pivote)} = {formatear_numero(m)}"
                + ("   (ya es 0: no se opera)" if m == 0 else ""))
        etapas.append(etapa(
            f"Pivote ({fila + 1},{columna + 1}) = {formatear_numero(pivote)}",
            f"Los multiplicadores de la columna {columna + 1} se calculan dividiendo cada entrada de debajo entre el "
            f"pivote; se guardan en la columna {fila + 1} de L." if multiplicadores else
            "Es la última fila: no hay entradas debajo del pivote.",
            formula=f"l(i,{fila + 1}) = u(i,{columna + 1}) / u({fila + 1},{columna + 1})" if multiplicadores else "",
            valores=[valor("U actual", U, pivotes=[(fila, columna)])], calculos=multiplicadores))

        for i in range(fila + 1, filas):
            m = U[i][columna] / pivote
            L[i][fila] = m
            if m == 0:
                continue
            antes = U[i][:]
            U[i] = [a - m * b for a, b in zip(U[i], U[fila])]
            operacion = texto_resta_de_filas(i, fila, m)
            operaciones.append({"operacion": operacion, "fila": i, "fila_pivote": fila, "columna": columna,
                                "multiplicador": m})
            etapas.append(etapa(
                operacion,
                f"Se anula la entrada ({i + 1},{columna + 1}) debajo del pivote. El multiplicador "
                f"{formatear_numero(m)} queda registrado en L en la posición ({i + 1},{fila + 1}).",
                formula=f"F{i + 1} − ({formatear_numero(m)})·F{fila + 1};  l{i + 1},{fila + 1} = {formatear_numero(m)}",
                valores=[valor("U después del reemplazo", U, pivotes=[(fila, columna)], filas=[i]),
                         valor("L con el multiplicador", L, pivotes=[(i, fila)])],
                calculos=[f"F{i + 1}, columna {j + 1}: {_p(antes[j])} − {_p(m)}·{_p(U[fila][j])} = "
                          f"{formatear_numero(U[i][j])}" for j in range(columnas)]))
        fila += 1

    existe = bloqueo is None
    if existe:
        lectura = [f"l{o['fila'] + 1},{o['fila_pivote'] + 1} = {formatear_numero(o['multiplicador'])}  ←  "
                   f"{o['operacion']}" for o in operaciones] or ["No hubo reemplazos: A ya estaba en forma escalonada y L = I."]
        etapas.append(etapa(
            "Factorización obtenida",
            "L contiene, en el orden en que se aplicaron, los multiplicadores de cada reemplazo; U es la forma "
            "escalonada de A.",
            formula="A = LU",
            valores=[valor("L", L), valor("U", U, pivotes=pivotes)],
            calculos=lectura,
            condiciones=[condicion(f"L es {filas}×{filas} triangular inferior con unos en la diagonal.",
                                   es_triangular_inferior_unitaria(L)),
                         condicion(f"U es {filas}×{columnas} y está en forma escalonada con {len(pivotes)} pivote(s).",
                                   pivotes_escalonada(U) == pivotes)],
            conclusion="Se obtuvo A = LU usando solo reemplazos de filas."))
    return {"A": A, "existe": existe, "motivo": motivo, "bloqueo": bloqueo,
            "L": L if existe else None, "U": U if existe else None,
            "L_parcial": copiar_matriz(L), "U_parcial": copiar_matriz(U),
            "pivotes": pivotes, "columnas_pivote": [c for _, c in pivotes], "rango": len(pivotes),
            "operaciones": operaciones, "etapas": etapas}


# -----------------------------------------------------------------------------
# Etapas 2 y 3: sustitución hacia adelante y hacia atrás
# -----------------------------------------------------------------------------

def sustitucion_adelante(L, b):
    """Resuelve Ly = b de arriba hacia abajo; cada yi usa los valores y1, …, y(i−1) ya hallados."""
    L = validar_matriz(L, "L")
    b = _vector(b, "b")
    n = len(L)
    if len(L[0]) != n or any(L[i][j] != 0 for i in range(n) for j in range(i + 1, n)):
        raise ValueError("L debe ser cuadrada y triangular inferior.")
    if any(L[i][i] == 0 for i in range(n)):
        raise ValueError("La diagonal de L no puede tener ceros.")
    if len(b) != n:
        raise ValueError(f"b debe tener {n} componentes, una por cada fila de L.")
    nombres = obtener_nombres_variables(n, "y")
    etapas = [etapa("Plantear Ly = b", "L es triangular inferior: la ecuación i solo contiene y1, …, yi.",
                    formula="yᵢ = (bᵢ − Σⱼ₍ⱼ<ᵢ₎ lᵢⱼ·yⱼ) / lᵢᵢ", valores=[valor("L", L), valor("b", b)],
                    calculos=[_ecuacion(L[i][:i + 1], nombres, b[i]) for i in range(n)])]
    y = []
    for i in range(n):
        conocidos = [(L[i][j], j) for j in range(i) if L[i][j] != 0]
        restas = "".join(f" − {_p(l)}·{_p(y[j])}" for l, j in conocidos)
        y.append((b[i] - sum((l * y[j] for l, j in conocidos), Fraction(0))) / L[i][i])
        calculos = [f"Ecuación {i + 1}: {_ecuacion(L[i][:i + 1], nombres, b[i])}"]
        if conocidos or L[i][i] != 1:
            calculos.append(_despeje(nombres[i], b[i], restas, L[i][i]))
        calculos.append(f"{nombres[i]} = {formatear_numero(y[i])}")
        etapas.append(etapa(f"Calcular {nombres[i]}",
                            "Se sustituyen los valores ya obtenidos." if conocidos else
                            "No depende de valores anteriores.", calculos=calculos,
                            valores=[valor("y hasta ahora", y)]))
    etapas.append(etapa("Vector intermedio y", formula="Ly = b", valores=[valor("y", y)],
                        conclusion="y es la entrada de la sustitución hacia atrás."))
    return {"L": copiar_matriz(L), "b": b[:], "y": y, "etapas": etapas}


def sustitucion_atras(U, y, pivotes=None):
    """
    Resuelve Ux = y de abajo hacia arriba con U escalonada (m×n). Las filas nulas
    exigen yi = 0; las columnas sin pivote dan variables libres (parámetros).
    """
    U = validar_matriz(U, "U")
    y = _vector(y, "y")
    filas, columnas = len(U), len(U[0])
    if len(y) != filas:
        raise ValueError(f"y debe tener {filas} componentes, una por cada fila de U.")
    escalonada = pivotes_escalonada(U)
    if escalonada is None or (pivotes is not None and list(map(tuple, pivotes)) != escalonada):
        raise ValueError("U debe estar en forma escalonada por filas.")
    pivotes = escalonada
    nombres = obtener_nombres_variables(columnas)
    aumentada = crear_matriz_aumentada(U, y)
    etapas = [etapa("Plantear Ux = y", "Se resuelve desde la última fila con pivote hacia arriba.",
                    formula="x(pivote) = (yₖ − Σ uₖⱼ·xⱼ) / uₖ,pivote", valores=[valor("[U | y]", aumentada, separador=columnas,
                                                                                     pivotes=pivotes)],
                    calculos=[_ecuacion(U[i], nombres, y[i]) for i in range(filas)])]
    columnas_pivote = [c for _, c in pivotes]
    nulas = list(range(len(pivotes), filas))
    inconsistentes = [i for i in nulas if y[i] != 0]
    base = {"U": copiar_matriz(U), "y": y[:], "pivotes": pivotes, "nombres_variables": nombres,
            "variables_basicas": columnas_pivote, "variables_libres": [c for c in range(columnas) if c not in columnas_pivote],
            "filas_inconsistentes": inconsistentes, "matriz_final": aumentada, "solucion": None,
            "solucion_particular": None, "forma_vectorial": None, "expresiones": None, "parametros": {}}
    if nulas:
        etapas.append(etapa(
            "Filas nulas de U", "Una fila nula de U es la ecuación 0 = yᵢ: es válida solo si yᵢ = 0.",
            calculos=[f"Fila {i + 1}: 0 = {formatear_numero(y[i])}  " + ("✓" if y[i] == 0 else "✗ contradicción")
                      for i in nulas],
            condiciones=[condicion(f"y{i + 1} = 0", y[i] == 0) for i in nulas]))
    if inconsistentes:
        i = inconsistentes[0]
        etapas.append(etapa("Sistema inconsistente", conclusion=(
            f"No se cumple: la fila {i + 1} de [U | y] es 0 = {formatear_numero(y[i])}; ningún x satisface Ux = y "
            f"y, por tanto, tampoco Ax = b.")))
        return {**base, "clasificacion": "Sistema inconsistente", "descripcion": "No tiene solución.", "etapas": etapas}

    libres = base["variables_libres"]
    parametros = dict(zip(libres, nombres_parametros(len(libres))))
    lista_parametros = list(parametros.values())
    # Cada xj se guarda como forma afín [constante, coef. del 1.er parámetro, …].
    formas = [None] * columnas
    for k, c in enumerate(libres):
        formas[c] = [Fraction(0)] * (len(libres) + 1)
        formas[c][k + 1] = Fraction(1)
    if libres:
        etapas.append(etapa("Variables libres",
                            "Las columnas de U sin pivote corresponden a variables libres: toman cualquier valor real.",
                            calculos=[f"{nombres[c]} = {parametros[c]}  (columna {c + 1} sin pivote)" for c in libres]))
    for fila, c in reversed(pivotes):
        terminos = [(U[fila][j], j) for j in range(c + 1, columnas) if U[fila][j] != 0]
        forma = [y[fila]] + [Fraction(0)] * len(libres)
        for u, j in terminos:
            forma = [a - u * b for a, b in zip(forma, formas[j])]
        forma = [a / U[fila][c] for a in forma]
        formas[c] = forma
        simbolico = "".join(f" − {_p(u)}·{nombres[j]}" for u, j in terminos)
        sustituido = "".join(f" − {_p(u)}·({_texto_afin(formas[j], lista_parametros)})" for u, j in terminos)
        calculos = [f"Ecuación {fila + 1}: {_ecuacion(U[fila], nombres, y[fila])}"]
        if terminos:
            calculos += [_despeje(nombres[c], y[fila], simbolico, U[fila][c]),
                         _despeje(nombres[c], y[fila], sustituido, U[fila][c])]
        elif U[fila][c] != 1:
            calculos.append(_despeje(nombres[c], y[fila], "", U[fila][c]))
        calculos.append(f"{nombres[c]} = {_texto_afin(forma, lista_parametros)}")
        etapas.append(etapa(
            f"Despejar {nombres[c]} (fila {fila + 1})",
            "Se usan las variables ya conocidas, que están a la derecha del pivote." if terminos else
            "No hay variables a la derecha del pivote.", calculos=calculos))

    particular = [f[0] for f in formas]
    direcciones = [(parametros[c], [f[k + 1] for f in formas]) for k, c in enumerate(libres)]
    expresiones = {j: _texto_afin(formas[j], lista_parametros) for j in range(columnas)}
    if libres:
        etapas.append(etapa("Solución general", formula="x = p + Σ t·v (los parámetros son arbitrarios)",
                            valores=[valor("Particular p", particular)] +
                                    [valor(f"Dirección de {t}", v) for t, v in direcciones],
                            calculos=[f"{nombres[j]} = {texto}" for j, texto in expresiones.items()]))
        return {**base, "clasificacion": "Sistema consistente indeterminado", "descripcion": "Tiene infinitas soluciones.",
                "solucion_particular": particular, "forma_vectorial": (particular, direcciones),
                "expresiones": expresiones, "parametros": parametros, "etapas": etapas}
    etapas.append(etapa("Solución final x", formula="Ux = y", valores=[valor("x", particular)],
                        calculos=[f"{nombres[j]} = {formatear_numero(v)}" for j, v in enumerate(particular)]))
    return {**base, "clasificacion": "Sistema consistente determinado", "descripcion": "Tiene una única solución.",
            "solucion": particular, "etapas": etapas}


# -----------------------------------------------------------------------------
# Proceso completo y verificación
# -----------------------------------------------------------------------------

def resolver_lu(A, b):
    """Factoriza A = LU y encadena Ly = b (hacia adelante) con Ux = y (hacia atrás)."""
    A = validar_matriz(A, "A")
    b = _vector(b, "b")
    filas, columnas = len(A), len(A[0])
    if len(b) != filas:
        raise ValueError(f"b debe tener {filas} componentes, una por cada fila de A.")
    factorizacion = factorizar_lu(A)
    etapas = [etapa("Etapa 1 · Factorización A = LU",
                    "Se reduce A a una forma escalonada U con reemplazos; L registra los multiplicadores. "
                    "Después se resuelve Ax = b como L(Ux) = b en dos etapas sustitutivas.",
                    formula="Ax = b  ⇔  Ly = b  y  Ux = y"),
              *factorizacion["etapas"]]
    resultado = {"A": A, "b": b, "m": filas, "n": columnas, "factorizacion": factorizacion,
                 "existe": factorizacion["existe"], "motivo": factorizacion["motivo"],
                 "L": factorizacion["L"], "U": factorizacion["U"], "pivotes": factorizacion["pivotes"],
                 "rango": factorizacion["rango"], "adelante": None, "atras": None, "y": None,
                 "determinante": None, "etapas": etapas}
    if not factorizacion["existe"]:
        resultado.update(clasificacion="Factorización LU no disponible", descripcion=factorizacion["motivo"],
                         solucion=None, expresiones=None, solucion_particular=None, forma_vectorial=None)
        return resultado

    L, U = factorizacion["L"], factorizacion["U"]
    adelante = sustitucion_adelante(L, b)
    etapas += [etapa("Etapa 2 · Sustitución hacia adelante: Ly = b",
                     "Encadenamiento: L es la salida de la etapa 1 y b es el vector original.",
                     condiciones=[condicion("L proviene de la factorización (etapa 1)."),
                                  condicion("b es el lado derecho original de Ax = b.")]),
               *adelante["etapas"]]
    atras = sustitucion_atras(U, adelante["y"], factorizacion["pivotes"])
    etapas += [etapa("Etapa 3 · Sustitución hacia atrás: Ux = y",
                     "Encadenamiento: U es la salida de la etapa 1 y y es la salida de la etapa 2.",
                     condiciones=[condicion("U proviene de la factorización (etapa 1)."),
                                  condicion("y proviene de la sustitución hacia adelante (etapa 2).")]),
               *atras["etapas"]]
    resultado.update({clave: atras[clave] for clave in (
        "clasificacion", "descripcion", "solucion", "solucion_particular", "forma_vectorial", "expresiones",
        "parametros", "nombres_variables", "variables_basicas", "variables_libres", "filas_inconsistentes",
        "matriz_final")})
    resultado.update(adelante=adelante, atras=atras, y=adelante["y"])
    resultado["cadena"] = [
        {"etapa": "Factorización", "entradas": {"A": A}, "salidas": {"L": L, "U": U}},
        {"etapa": "Sustitución hacia adelante", "entradas": {"L": adelante["L"], "b": adelante["b"]},
         "salidas": {"y": adelante["y"]}},
        {"etapa": "Sustitución hacia atrás", "entradas": {"U": atras["U"], "y": atras["y"]},
         "salidas": {"x": atras["solucion"] if atras["solucion"] is not None else atras["solucion_particular"]}},
    ]
    if filas == columnas:
        diagonal = [U[i][i] for i in range(filas)]
        producto = Fraction(1)
        for d in diagonal:
            producto *= d
        resultado["determinante"] = producto
        etapas.append(etapa(
            "Consecuencia: det(A) desde U",
            "L es triangular con unos en la diagonal (det(L) = 1) y U es triangular superior.",
            formula="det(A) = det(L)·det(U) = 1·∏ uᵢᵢ",
            calculos=[" · ".join(_p(d) for d in diagonal) + f" = {formatear_numero(producto)}"],
            conclusion="A es invertible (det(A) ≠ 0)." if producto else "A es singular (det(A) = 0)."))
    return resultado


def verificar_lu(resultado, A=None, b=None):
    """
    Comprueba el encadenamiento, la estructura de L y U, LU = A, Ly = b, Ux = y y
    Ax = b con los datos originales; compara además con Gauss-Jordan y, si A es
    cuadrada, el determinante con Sarrus (3×3) o cofactores. No reutiliza los
    cálculos del procedimiento: solo sus resultados, que son lo que se comprueba.
    """
    A = validar_matriz(A if A is not None else resultado["A"], "A")
    b = _vector(b if b is not None else resultado["b"], "b")
    filas, columnas = len(A), len(A[0])
    factorizacion = resultado["factorizacion"]
    etapas, chequeos = [], []

    def registrar(nombre, correcto):
        chequeos.append({"nombre": nombre, "correcto": bool(correcto)})
        return bool(correcto)

    def lu_frente_a_A(L, U, titulo):
        R, lineas = _producto(L, U, "LU")
        etapas.append(etapa("Calcular LU", "Producto fila por columna de las matrices obtenidas.",
                            valores=[valor("L", L), valor("U", U), valor("LU", R)], calculos=lineas))
        etapas.append(comparar(R, A, "LU frente a A original"))
        return registrar(titulo, R == A)

    if not factorizacion["existe"]:
        fila, columna, debajo = factorizacion["bloqueo"]
        L, U = factorizacion["L_parcial"], factorizacion["U_parcial"]
        etapas.append(etapa("Diagnóstico a comprobar", factorizacion["motivo"]))
        lu_frente_a_A(L, U, "Eliminación parcial correcta")
        previas = all(U[i][c] == 0 for k, c in factorizacion["pivotes"] for i in range(k + 1, filas))
        bloqueado = U[fila][columna] == 0 and U[debajo][columna] != 0
        etapas.append(etapa(
            "Condición que impide continuar sin intercambios",
            valores=[valor("U parcial", U, pivotes=[(fila, columna)], filas=[debajo])],
            calculos=[f"u{fila + 1},{columna + 1} = {formatear_numero(U[fila][columna])}",
                      f"u{debajo + 1},{columna + 1} = {formatear_numero(U[debajo][columna])}"],
            condiciones=[condicion("Las columnas pivote anteriores ya tienen ceros debajo del pivote.", previas),
                         condicion("La posición pivote vale 0 y hay un valor distinto de cero debajo.", bloqueado)],
            conclusion="Se cumple: el diagnóstico es correcto; hace falta un intercambio (PA = LU)."
            if previas and bloqueado else "No se cumple"))
        registrar("Bloqueo confirmado", previas and bloqueado)
        return {"aplicable": True, "correcto": all(c["correcto"] for c in chequeos), "etapas": etapas,
                "chequeos": chequeos}

    L, U = resultado["L"], resultado["U"]
    adelante, atras = resultado["adelante"], resultado["atras"]
    x = atras["solucion"] if atras["solucion"] is not None else atras["solucion_particular"]
    salida = resultado["solucion"] if resultado["solucion"] is not None else resultado["solucion_particular"]

    enlaces = [("La etapa 1 factorizó la A original (sin modificarla).", factorizacion["A"] == A),
               ("La etapa 2 usa la L obtenida en la etapa 1.", adelante["L"] == factorizacion["L"] == L),
               ("La etapa 2 usa el b original.", adelante["b"] == b),
               ("La etapa 3 usa la U obtenida en la etapa 1.", atras["U"] == factorizacion["U"] == U),
               ("La etapa 3 usa como lado derecho la y obtenida en la etapa 2.", atras["y"] == adelante["y"] == resultado["y"]),
               ("La solución informada es la salida de la etapa 3.", salida == x)]
    etapas.append(etapa("Encadenamiento de datos",
                        "Cada etapa debe recibir exactamente la salida de la anterior: A → (L, U) → y → x.",
                        valores=[valor("y (salida de la etapa 2)", adelante["y"]),
                                 valor("y (entrada de la etapa 3)", atras["y"])],
                        condiciones=[condicion(texto, ok) for texto, ok in enlaces],
                        conclusion="Se cumple" if all(ok for _, ok in enlaces) else "No se cumple"))
    registrar("Encadenamiento de datos", all(ok for _, ok in enlaces))

    pivotes = pivotes_escalonada(U)
    estructura = [(f"L es {filas}×{filas}.", len(L) == filas and all(len(f) == filas for f in L)),
                  ("L es triangular inferior con unos en la diagonal.", es_triangular_inferior_unitaria(L)),
                  (f"U es {filas}×{columnas}.", len(U) == filas and all(len(f) == columnas for f in U)),
                  ("U está en forma escalonada por filas.", pivotes is not None),
                  ("Los pivotes de U son los informados.", pivotes == resultado["pivotes"])]
    etapas.append(etapa("Estructura de L y U", valores=[valor("L", L), valor("U", U, pivotes=pivotes or [])],
                        condiciones=[condicion(texto, ok) for texto, ok in estructura]))
    registrar("Estructura de L y U", all(ok for _, ok in estructura))

    lu_frente_a_A(L, U, "LU = A")

    escalonada, _, _ = forma_escalonada(crear_matriz_aumentada(A, [Fraction(0)] * filas), columnas)
    otra_u = [f[:columnas] for f in escalonada]
    etapas.append(etapa("U por otro algoritmo",
                        "La eliminación gaussiana del módulo de sistemas, aplicada a la A original, debe producir la "
                        "misma U (no se escalan filas)."))
    etapas.append(comparar(U, otra_u, "U frente a la forma escalonada recalculada"))
    registrar("U recalculada", U == otra_u)

    ly, lineas = _producto_vector(L, adelante["y"], "Ly")
    etapas += [etapa("Calcular Ly", valores=[valor("y", adelante["y"]), valor("Ly", ly)], calculos=lineas),
               comparar(ly, b, "Ly frente a b original")]
    registrar("Ly = b", ly == b)

    if resultado["clasificacion"] == "Sistema inconsistente":
        nulas = [i for i in range(filas) if all(v == 0 for v in U[i])]
        contradiccion = [i for i in nulas if adelante["y"][i] != 0]
        etapas.append(etapa("Ux = y es incompatible", "Una fila nula de U con yᵢ ≠ 0 es la ecuación 0 = yᵢ.",
                            calculos=[f"Fila {i + 1}: 0 = {formatear_numero(adelante['y'][i])}" for i in nulas],
                            condiciones=[condicion("Existe una fila nula de U con yᵢ ≠ 0.", bool(contradiccion))]))
        etapas.append(etapa("Comprobación independiente con la A original",
                            "Se busca una combinación de las ecuaciones originales que produzca 0 = c ≠ 0."))
        try:
            certificado = certificado_inconsistencia(A, b)
        except ArithmeticError:
            certificado = {"correcto": False, "etapas": [etapa("Sin certificado", conclusion=(
                "No se cumple: el sistema original sí tiene solución, así que no es inconsistente."))]}
        etapas += certificado["etapas"]
        registrar("Inconsistencia", bool(contradiccion) and certificado["correcto"])
    else:
        particular = atras["solucion"] if atras["solucion"] is not None else atras["solucion_particular"]
        direcciones = atras["forma_vectorial"][1] if atras["forma_vectorial"] else []
        ux, lineas = _producto_vector(U, particular, "Ux" if not direcciones else "Up")
        etapas += [etapa("Calcular " + ("Ux" if not direcciones else "Up"), valores=[valor("U", U), valor("x" if not direcciones else "p", particular)],
                         calculos=lineas), comparar(ux, adelante["y"], ("Ux" if not direcciones else "Up") + " frente a y")]
        ax, lineas = _producto_vector(A, particular, "Ax" if not direcciones else "Ap")
        etapas += [etapa("Sustituir en el sistema original " + ("Ax = b" if not direcciones else "Ap = b"),
                         "Se usa la A original, no L ni U.", valores=[valor("A original", A), valor("Resultado", ax)],
                         calculos=lineas), comparar(ax, b, ("Ax" if not direcciones else "Ap") + " frente a b original")]
        correcto = ux == adelante["y"] and ax == b
        cero = [Fraction(0)] * filas
        for parametro, v in direcciones:
            uv, _ = _producto_vector(U, v, f"Uv({parametro})")
            av, lineas = _producto_vector(A, v, f"Av({parametro})")
            etapas += [etapa(f"Dirección del parámetro {parametro}", "Debe cumplir Uv = 0 y Av = 0 (espacio nulo de A).",
                             valores=[valor("v", v)], calculos=lineas),
                       comparar(av, cero, f"Av({parametro}) frente a 0"), comparar(uv, cero, f"Uv({parametro}) frente a 0")]
            correcto = correcto and av == cero and uv == cero
        registrar("Solución en el sistema original", correcto)

        gauss = resolver_sistema(A, b)
        etapas.append(etapa("Recálculo por Gauss-Jordan",
                            "Se resuelve la A original con [A | b] → RREF, sin usar L, U ni y.",
                            calculos=[f"Clasificación: {gauss['clasificacion']}"],
                            condiciones=[condicion("Misma clasificación que por LU.",
                                                   gauss["clasificacion"] == resultado["clasificacion"])]))
        coincide = gauss["clasificacion"] == resultado["clasificacion"]
        if gauss["solucion"] is not None:
            etapas.append(comparar(particular, gauss["solucion"], "x por LU frente a x por Gauss-Jordan"))
            coincide = coincide and particular == gauss["solucion"]
        elif gauss["forma_vectorial"] is not None:
            p_gj, d_gj = gauss["forma_vectorial"]
            etapas.append(comparar(particular, p_gj, "p por LU frente a p por Gauss-Jordan"))
            coincide = coincide and particular == p_gj and len(d_gj) == len(direcciones)
            for (t, v), (_, w) in zip(direcciones, d_gj):
                etapas.append(comparar(v, w, f"Dirección de {t}: LU frente a Gauss-Jordan"))
                coincide = coincide and v == w
        registrar("Coincide con Gauss-Jordan", coincide)

    if resultado["determinante"] is not None:
        metodo = "sarrus" if filas == 3 else "cofactores"
        otro = calcular_determinante(A, metodo)
        etapas += [etapa(f"det(A) por {'Sarrus' if metodo == 'sarrus' else 'cofactores'}",
                         "Se recalcula el determinante desde la A original con otro método.", subpasos=otro["etapas"]),
                   comparar(resultado["determinante"], otro["determinante"], "det(A) por LU frente al recálculo")]
        registrar("Determinante", resultado["determinante"] == otro["determinante"])

    correcto = all(c["correcto"] for c in chequeos)
    etapas.append(etapa("Conclusión de la verificación",
                        calculos=[f"{'✓' if c['correcto'] else '✗'} {c['nombre']}" for c in chequeos],
                        conclusion="Se cumple: LU = A y cada etapa coincide con los datos originales." if correcto
                        else "No se cumple: revisa las comprobaciones marcadas con ✗."))
    return {"aplicable": True, "correcto": correcto, "etapas": etapas, "chequeos": chequeos}


def resumen_texto_lu(resultado):
    """Texto plano para copiar: L, U, y y la solución."""
    if not resultado["existe"]:
        return f"{resultado['clasificacion']}: {resultado['motivo']}"
    lineas = ["A = LU", "L:", matriz_a_texto(resultado["L"], False), "U:", matriz_a_texto(resultado["U"], False),
              "y (Ly = b) = (" + ", ".join(formatear_numero(v) for v in resultado["y"]) + ")",
              f"{resultado['clasificacion']}: {resultado['descripcion']}"]
    nombres = resultado["nombres_variables"]
    if resultado["solucion"] is not None:
        lineas += [f"{nombres[i]} = {formatear_numero(v)}" for i, v in enumerate(resultado["solucion"])]
    elif resultado["expresiones"] is not None:
        lineas += [f"{nombres[i]} = {texto}" for i, texto in resultado["expresiones"].items()]
    if resultado["determinante"] is not None:
        lineas.append(f"det(A) = {formatear_numero(resultado['determinante'])}")
    return "\n".join(lineas)

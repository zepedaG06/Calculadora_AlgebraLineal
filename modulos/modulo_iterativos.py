"""Métodos iterativos de Jacobi y Gauss-Seidel para aproximar la solución de Ax = b.

Propósito: validar los datos, analizar la diagonal (ceros y dominancia estricta por filas), buscar un reordenamiento
de ecuaciones cuando haga falta, iterar con ambos métodos, detectar la falta de convergencia y comparar los
resultados con la solución exacta de Gauss-Jordan de la propia calculadora.
Unidad: Álgebra Lineal (MTM0120), Programa 8: métodos iterativos de Jacobi y Gauss-Seidel.
Autores (Grupo 3, UAM): Andrés Eduardo Mejía Castro, José Andrés Zepeda Grijalba,
Eddy Alfonso Almendárez Ruiz y Brandon Javier Rocha Varela.
Notas: funciones puras (sin input() ni print()) y sin NumPy; se itera con números de punto flotante porque las
fracciones exactas crecerían sin control en cada iteración.
"""
from fractions import Fraction

from .modulo_matrices import convertir_numero, resolver_sistema
from .modulo_numericos import formatear_real
from .pasos import condicion, etapa

LIMITE_ORDEN = 10
LIMITE_ITERACIONES = 5000
LIMITE_FINITO = 1e150
ITERACIONES_CRECIENTES = 5

CASOS_DE_PRUEBA = {
    "Caso 1 · Convergencia (diagonal dominante)": {
        "A": [[10, -1, 2, 0], [-1, 11, -1, 3], [2, -1, 10, -1], [0, 3, -1, 8]], "b": [6, 25, -11, 15],
        "x0": [0, 0, 0, 0], "tolerancia": "0.000001", "max_iteraciones": 100, "reordenar": True,
        "objetivo": "Matriz estrictamente diagonal dominante por filas: ambos métodos deben converger. Se comparan "
                    "las iteraciones, los errores y las soluciones con la de Gauss-Jordan, que es (1, 2, −1, 1)."},
    "Caso 2 · Reordenamiento (cero en la diagonal)": {
        "A": [[1, 8, 2], [7, 0, 2], [1, 2, 6]], "b": [23, 13, 23], "x0": [0, 0, 0], "tolerancia": "0.000001",
        "max_iteraciones": 100, "reordenar": True,
        "objetivo": "a₂₂ = 0 impide iniciar ambos métodos (habría que dividir entre 0). Intercambiar las ecuaciones 1 y 2 "
                    "deja una diagonal sin ceros y estrictamente dominante; la solución no cambia: (1, 2, 3)."},
    "Caso 3 · No convergencia (sin diagonal dominante)": {
        "A": [[1, 2, 2], [2, 1, 2], [2, 2, 1]], "b": [5, 5, 5], "x0": [0, 0, 0], "tolerancia": "0.000001",
        "max_iteraciones": 40, "reordenar": True,
        "objetivo": "Ninguna fila tiene un elemento mayor que la suma de los demás, así que ningún reordenamiento da "
                    "diagonal dominante. Aquí ambos métodos divergen, aunque la solución exacta (1, 1, 1) existe."},
    "Ejemplo adicional · Converge sin ser dominante": {
        "A": [[3, 2, 1], [2, 3, 2], [1, 2, 3]], "b": [6, 7, 6], "x0": [0, 0, 0], "tolerancia": "0.000001",
        "max_iteraciones": 200, "reordenar": True,
        "objetivo": "Ninguna fila es estrictamente dominante (en la fila 2, 3 < 2 + 2), pero A es simétrica definida positiva: "
                    "Gauss-Seidel converge y Jacobi no. "
                    "Muestra que no cumplir la condición suficiente no implica divergencia."},
}


def _numero(valor, nombre):
    """Convierte un dato a float finito, aceptando fracciones y decimales escritos como texto.

    Entrada: valor (número o texto) y nombre para los mensajes. Salida: float; lanza ValueError si no es válido.
    """
    try:
        numero = float(convertir_numero(valor) if isinstance(valor, str) else Fraction(valor))
    except (ValueError, TypeError, OverflowError, ZeroDivisionError):
        raise ValueError(f"{nombre} no es un número válido.") from None
    if abs(numero) > LIMITE_FINITO:
        raise ValueError(f"{nombre} es demasiado grande.")
    return numero


def validar_datos(A, b, x0, tolerancia, max_iteraciones):
    """Valida dimensiones, tolerancia e iteraciones y convierte los datos a float.

    Entrada: A (n × n), b (n), x0 (n), tolerancia > 0 y máximo de iteraciones (entero positivo).
    Salida: diccionario con A, b, x0, tolerancia, max_iteraciones y n; lanza ValueError con el motivo si algo falla.
    """
    if not isinstance(A, (list, tuple)) or not A or not all(isinstance(f, (list, tuple)) for f in A):
        raise ValueError("A debe ser una matriz (lista de filas).")
    n = len(A)
    if n > LIMITE_ORDEN:
        raise ValueError(f"A puede tener como máximo {LIMITE_ORDEN} filas.")
    if any(len(fila) != n for fila in A):
        raise ValueError(f"A debe ser cuadrada: tiene {n} filas, así que cada fila necesita {n} columnas.")
    if len(b) != n:
        raise ValueError(f"b debe tener {n} componentes, una por cada ecuación; tiene {len(b)}.")
    if len(x0) != n:
        raise ValueError(f"El vector inicial x⁽⁰⁾ debe tener {n} componentes; tiene {len(x0)}.")
    matriz = [[_numero(v, f"a{i + 1}{j + 1}") for j, v in enumerate(fila)] for i, fila in enumerate(A)]
    vector_b = [_numero(v, f"b{i + 1}") for i, v in enumerate(b)]
    inicial = [_numero(v, f"x{i + 1}⁽⁰⁾") for i, v in enumerate(x0)]
    tol = _numero(tolerancia, "La tolerancia ε")
    if not 0 < tol < 1:
        raise ValueError("La tolerancia ε debe ser un decimal positivo menor que 1, por ejemplo 0.000001.")
    try:
        iteraciones = int(str(max_iteraciones).strip())
    except ValueError:
        raise ValueError("El máximo de iteraciones debe ser un número entero.") from None
    if not 1 <= iteraciones <= LIMITE_ITERACIONES:
        raise ValueError(f"El máximo de iteraciones debe estar entre 1 y {LIMITE_ITERACIONES}.")
    return {"A": matriz, "b": vector_b, "x0": inicial, "tolerancia": tol, "max_iteraciones": iteraciones, "n": n}


def analizar_diagonal(A):
    """Revisa si hay ceros en la diagonal y si cada fila es estrictamente dominante: |aᵢᵢ| > Σⱼ≠ᵢ |aᵢⱼ|.

    Entrada: A cuadrada. Salida: diccionario con ceros (filas), filas (detalle por fila) y dominante (bool).
    """
    filas = []
    for i, fila in enumerate(A):
        diagonal = abs(fila[i])
        resto = sum(abs(v) for j, v in enumerate(fila) if j != i)
        filas.append({"fila": i, "diagonal": diagonal, "resto": resto, "cumple": diagonal > resto})
    return {"ceros": [i for i, fila in enumerate(A) if fila[i] == 0], "filas": filas,
            "dominante": all(f["cumple"] for f in filas)}


def _emparejar(permitido, n):
    """Busca una fila distinta para cada posición de la diagonal (emparejamiento bipartito por caminos aumentantes).

    Entrada: permitido(fila, posición) → bool y orden n. Salida: lista orden[posición] = fila, o None si no existe.
    """
    fila_en = [None] * n

    def intentar(fila, visitadas):
        """Ubica la fila en alguna posición, moviendo si hace falta a la fila que ya la ocupaba.

        Entrada: fila y posiciones visitadas. Salida: True si se pudo ubicar.
        """
        for posicion in range(n):
            if permitido(fila, posicion) and posicion not in visitadas:
                visitadas.add(posicion)
                if fila_en[posicion] is None or intentar(fila_en[posicion], visitadas):
                    fila_en[posicion] = fila
                    return True
        return False

    for fila in range(n):
        if not intentar(fila, set()):
            return None
    return fila_en


def buscar_reordenamiento(A):
    """Busca un orden de ecuaciones con diagonal estrictamente dominante o, si no existe, con diagonal sin ceros.

    Entrada: A cuadrada (float). Salida: diccionario con orden (o None), tipo ('dominante', 'sin_ceros' o None) y motivo.
    """
    n = len(A)
    dominante = _emparejar(lambda i, j: 2 * abs(A[i][j]) > sum(abs(v) for v in A[i]), n)
    if dominante is not None:
        return {"orden": dominante, "tipo": "dominante",
                "motivo": "Existe un orden de las ecuaciones con diagonal estrictamente dominante."}
    sin_ceros = _emparejar(lambda i, j: A[i][j] != 0, n)
    if sin_ceros is not None:
        return {"orden": sin_ceros, "tipo": "sin_ceros",
                "motivo": "Ningún orden da diagonal dominante, pero sí existe uno sin ceros en la diagonal."}
    return {"orden": None, "tipo": None,
            "motivo": "No existe ningún orden de las ecuaciones con la diagonal sin ceros: cada orden deja algún aᵢᵢ = 0."}


def norma_infinito(vector):
    """Calcula ‖v‖∞ = máx |vᵢ|.

    Entrada: vector. Salida: float.
    """
    return max((abs(v) for v in vector), default=0.0)


def residuo(A, b, x):
    """Calcula el residuo r = Ax − b.

    Entrada: A, b y x. Salida: lista con las componentes del residuo.
    """
    return [sum(a * v for a, v in zip(fila, x)) - bi for fila, bi in zip(A, b)]


def _finito(vector):
    """Indica si todas las componentes son números finitos y razonables.

    Entrada: vector. Salida: True o False.
    """
    return all(v == v and abs(v) <= LIMITE_FINITO for v in vector)


def iterar(A, b, x0, tolerancia, max_iteraciones, metodo):
    """Aplica Jacobi o Gauss-Seidel y registra cada iteración con su error y su residuo.

    Entrada: A (diagonal sin ceros), b, x0, tolerancia, máximo de iteraciones y metodo ('jacobi' o 'gauss_seidel').
    Salida: diccionario con iteraciones, solucion, estado, convergio, error, residuo y advertencias.
    """
    n = len(A)
    x = list(x0)
    filas = [{"k": 0, "x": list(x), "error": None, "residuo": norma_infinito(residuo(A, b, x))}]
    estado, convergio, advertencias = "maximo", False, []
    for k in range(1, max_iteraciones + 1):
        anterior = list(x)
        # Jacobi calcula todo con x⁽ᵏ⁻¹⁾; Gauss-Seidel reutiliza en la misma iteración los valores ya calculados.
        fuente = anterior if metodo == "jacobi" else x
        nuevo = list(x) if metodo == "gauss_seidel" else [0.0] * n
        try:
            for i in range(n):
                suma = sum(A[i][j] * (fuente if metodo == "jacobi" else nuevo)[j] for j in range(n) if j != i)
                nuevo[i] = (b[i] - suma) / A[i][i]
        except OverflowError:
            nuevo = [float("inf")] * n
        if not _finito(nuevo):
            estado = "no_finito"
            advertencias.append(f"En la iteración {k} los valores dejaron de ser finitos (crecieron sin control): el método diverge.")
            break
        x = nuevo
        error = norma_infinito([a - c for a, c in zip(x, anterior)])
        filas.append({"k": k, "x": list(x), "error": error, "residuo": norma_infinito(residuo(A, b, x))})
        if error <= tolerancia:
            estado, convergio = "convergio", True
            break
    errores = [f["error"] for f in filas[1:]]
    crecientes = 0
    for previo, actual in zip(errores, errores[1:]):
        crecientes = crecientes + 1 if actual > previo else 0
    if not convergio and errores and (crecientes >= ITERACIONES_CRECIENTES or errores[-1] > errores[0]):
        advertencias.append("El error entre iteraciones está creciendo: posible no convergencia con este orden de ecuaciones.")
    if estado == "maximo":
        advertencias.append(f"Se alcanzó el máximo de {max_iteraciones} iteraciones sin llegar a la tolerancia.")
    factor = errores[-1] / errores[-2] if len(errores) >= 2 and errores[-2] else None
    ultima = filas[-1]
    return {"metodo": metodo, "nombre": "Jacobi" if metodo == "jacobi" else "Gauss-Seidel", "iteraciones": filas,
            "n_iteraciones": ultima["k"], "solucion": ultima["x"], "error": ultima["error"], "residuo": ultima["residuo"],
            "estado": estado, "convergio": convergio, "advertencias": advertencias, "factor": factor}


def jacobi(A, b, x0, tolerancia, max_iteraciones):
    """Método de Jacobi: xᵢ⁽ᵏ⁾ = (bᵢ − Σⱼ≠ᵢ aᵢⱼ xⱼ⁽ᵏ⁻¹⁾) / aᵢᵢ, usando solo la iteración anterior.

    Entrada: A, b, x0, tolerancia y máximo de iteraciones. Salida: diccionario de iterar.
    """
    return iterar(A, b, x0, tolerancia, max_iteraciones, "jacobi")


def gauss_seidel(A, b, x0, tolerancia, max_iteraciones):
    """Método de Gauss-Seidel: usa en cuanto están listos los xⱼ⁽ᵏ⁾ ya calculados (j < i) en la misma iteración.

    Entrada: A, b, x0, tolerancia y máximo de iteraciones. Salida: diccionario de iterar.
    """
    return iterar(A, b, x0, tolerancia, max_iteraciones, "gauss_seidel")


def _texto_vector(vector, cifras=8):
    """Escribe un vector entre paréntesis.

    Entrada: vector y cifras significativas. Salida: cadena.
    """
    return "(" + ", ".join(formatear_real(v, cifras) for v in vector) + ")"


def _despeje(A, b, i, metodo, anterior, actual, k):
    """Escribe la sustitución de una componente, indicando de qué iteración viene cada valor.

    Entrada: A, b, índice i, método, x⁽ᵏ⁻¹⁾, x⁽ᵏ⁾ parcial e iteración k. Salida: cadena.
    """
    terminos, valores = [], []
    for j in range(len(A)):
        if j == i:
            continue
        nuevo = metodo == "gauss_seidel" and j < i
        terminos.append(f"({formatear_real(A[i][j], 6)})·x{j + 1}⁽{k if nuevo else k - 1}⁾")
        valores.append(f"({formatear_real(A[i][j], 6)})({formatear_real((actual if nuevo else anterior)[j], 6)})")
    resta = " − ".join(terminos)
    sustituida = " − ".join(valores)
    return (f"x{i + 1}⁽{k}⁾ = ({formatear_real(b[i], 6)}" + (f" − {resta}" if resta else "") + f") / {formatear_real(A[i][i], 6)} = "
            f"({formatear_real(b[i], 6)}" + (f" − {sustituida}" if sustituida else "") + f") / {formatear_real(A[i][i], 6)} = "
            f"{formatear_real(actual[i], 8)}")


def _etapas_metodo(datos, resultado, mostrar=3):
    """Explica las primeras iteraciones de un método con todas las sustituciones y resume las demás.

    Entrada: datos usados (A, b), resultado de iterar y cuántas iteraciones detallar. Salida: lista de etapas.
    """
    A, b = datos["A"], datos["b"]
    metodo, filas = resultado["metodo"], resultado["iteraciones"]
    explicacion = ("Jacobi calcula todas las componentes nuevas con los valores de la iteración anterior (actualización simultánea)."
                   if metodo == "jacobi" else
                   "Gauss-Seidel usa de inmediato cada componente recién calculada dentro de la misma iteración (actualización inmediata).")
    formula = ("xᵢ⁽ᵏ⁾ = (bᵢ − Σⱼ≠ᵢ aᵢⱼ·xⱼ⁽ᵏ⁻¹⁾) / aᵢᵢ" if metodo == "jacobi" else
               "xᵢ⁽ᵏ⁾ = (bᵢ − Σⱼ<ᵢ aᵢⱼ·xⱼ⁽ᵏ⁾ − Σⱼ>ᵢ aᵢⱼ·xⱼ⁽ᵏ⁻¹⁾) / aᵢᵢ")
    etapas = [etapa(f"{resultado['nombre']}: fórmula", explicacion, formula=formula,
                    calculos=[f"x⁽⁰⁾ = {_texto_vector(filas[0]['x'])}"])]
    for fila_anterior, fila in zip(filas, filas[1:mostrar + 1]):
        k = fila["k"]
        calculos = [_despeje(A, b, i, metodo, fila_anterior["x"], fila["x"], k) for i in range(len(A))]
        calculos += [f"Error: ‖x⁽{k}⁾ − x⁽{k - 1}⁾‖∞ = {formatear_real(fila['error'])}", f"Residuo: ‖Ax⁽{k}⁾ − b‖∞ = {formatear_real(fila['residuo'])}"]
        etapas.append(etapa(f"{resultado['nombre']}: iteración {k}", calculos=calculos))
    if len(filas) > mostrar + 1:
        etapas.append(etapa(f"{resultado['nombre']}: iteraciones {mostrar + 1} a {resultado['n_iteraciones']}",
                            "Se repite el mismo cálculo; la tabla completa está en la pestaña Resultado.",
                            calculos=[f"k = {f['k']}: x = {_texto_vector(f['x'], 7)}, error = {formatear_real(f['error'], 3)}"
                                      for f in filas[mostrar + 1:][-8:]]))
    texto_estado = {"convergio": f"Convergió: el error {formatear_real(resultado['error'], 3)} ya es menor o igual que ε.",
                    "maximo": "Se alcanzó el máximo de iteraciones sin llegar a la tolerancia.",
                    "no_finito": "Se detuvo porque los valores dejaron de ser finitos."}[resultado["estado"]]
    etapas.append(etapa(f"{resultado['nombre']}: criterio de parada", "Se detiene cuando ‖x⁽ᵏ⁾ − x⁽ᵏ⁻¹⁾‖∞ ≤ ε o al llegar al máximo de iteraciones.",
                        calculos=[f"Iteraciones: {resultado['n_iteraciones']}", f"x ≈ {_texto_vector(resultado['solucion'], 10)}",
                                  f"Residuo final ‖Ax − b‖∞ = {formatear_real(resultado['residuo'])}"],
                        conclusion=texto_estado if resultado["convergio"] else ""))
    return etapas


def resolver_iterativos(A, b, x0, tolerancia, max_iteraciones, reordenar=True):
    """Valida, analiza la diagonal, reordena si hace falta, aplica Jacobi y Gauss-Seidel y compara con Gauss-Jordan.

    Entrada: A, b, x0, tolerancia ε, máximo de iteraciones y reordenar (bool). Salida: informe con el análisis, ambos métodos,
    la referencia, la comparación, el procedimiento y la verificación; lanza ValueError si los datos no son válidos.
    """
    datos = validar_datos(A, b, x0, tolerancia, max_iteraciones)
    n = datos["n"]
    original = analizar_diagonal(datos["A"])
    etapas = [etapa("Datos y validación",
                    "Se comprueban las dimensiones, la tolerancia y el máximo de iteraciones antes de iterar.",
                    formula="Ax = b,  A de orden n × n",
                    calculos=[f"n = {n}", f"b = {_texto_vector(datos['b'])}", f"x⁽⁰⁾ = {_texto_vector(datos['x0'])}",
                              f"ε = {formatear_real(datos['tolerancia'])}", f"Máximo de iteraciones = {datos['max_iteraciones']}"],
                    condiciones=[condicion(f"A es {n}×{n}, b y x⁽⁰⁾ tienen {n} componentes."),
                                 condicion("ε es positiva y el máximo de iteraciones es un entero positivo.")]),
              _etapa_diagonal("Diagonal del sistema original", original, list(range(n)))]
    reordenamiento = {"orden": list(range(n)), "tipo": None, "aplicado": False, "motivo": "No hizo falta cambiar el orden de las ecuaciones."}
    if original["ceros"] or not original["dominante"]:
        busqueda = buscar_reordenamiento(datos["A"])
        usar = reordenar and busqueda["orden"] is not None and (original["ceros"] or busqueda["tipo"] == "dominante")
        if usar and busqueda["orden"] != list(range(n)):
            reordenamiento = {**busqueda, "aplicado": True}
        elif not reordenar:
            reordenamiento["motivo"] = "El reordenamiento de filas está desactivado."
        else:
            reordenamiento["motivo"] = busqueda["motivo"] + (" Se conserva el orden original." if busqueda["orden"] is not None else "")
        if busqueda["orden"] is None or (original["ceros"] and not usar):
            reordenamiento["motivo"] = busqueda["motivo"] if busqueda["orden"] is None else reordenamiento["motivo"]
    orden = reordenamiento["orden"]
    A_usada = [datos["A"][i] for i in orden]
    b_usada = [datos["b"][i] for i in orden]
    usada = analizar_diagonal(A_usada)
    etapas.append(etapa("Reordenamiento de ecuaciones",
                        "Cambiar el orden de las ecuaciones no cambia la solución, pero sí la diagonal que usan los métodos.",
                        calculos=[reordenamiento["motivo"]] + ([f"Nuevo orden: " + ", ".join(f"E{i + 1}" for i in orden)] if reordenamiento["aplicado"] else []),
                        conclusion="Se reordenaron las ecuaciones." if reordenamiento["aplicado"] else ""))
    if reordenamiento["aplicado"]:
        etapas.append(_etapa_diagonal("Diagonal después de reordenar", usada, orden))
    base = {"datos": datos, "analisis": original, "analisis_usado": usada, "reordenamiento": reordenamiento,
            "A_usada": A_usada, "b_usada": b_usada, "n": n}
    if usada["ceros"]:
        filas = ", ".join(str(i + 1) for i in usada["ceros"])
        motivo = (f"La diagonal tiene ceros ({'fila' if len(usada['ceros']) == 1 else 'filas'} {filas}): ambos métodos dividen entre aᵢᵢ, "
                  f"así que no pueden iniciar. {reordenamiento['motivo']}")
        etapas.append(etapa("No se puede iterar", conclusion=motivo))
        return {**base, "definido": False, "titulo": "Jacobi y Gauss-Seidel no se pueden aplicar", "conclusion": motivo, "motivo": motivo,
                "jacobi": None, "gauss_seidel": None, "referencia": _referencia(datos), "comparacion": None, "procedimiento": etapas,
                "verificacion": {"aplicable": False, "correcto": False, "motivo": motivo, "etapas": etapas[-1:]}}
    tolerancia, maximo = datos["tolerancia"], datos["max_iteraciones"]
    resultado_j = jacobi(A_usada, b_usada, datos["x0"], tolerancia, maximo)
    resultado_gs = gauss_seidel(A_usada, b_usada, datos["x0"], tolerancia, maximo)
    for resultado in (resultado_j, resultado_gs):
        # El residuo final se recalcula con el sistema original: el reordenamiento no puede ocultar un error.
        resultado["residuo"] = norma_infinito(residuo(datos["A"], datos["b"], resultado["solucion"]))
    referencia = _referencia(datos)
    comparacion = comparar_metodos(resultado_j, resultado_gs, referencia)
    etapas += _etapas_metodo({"A": A_usada, "b": b_usada}, resultado_j) + _etapas_metodo({"A": A_usada, "b": b_usada}, resultado_gs)
    etapas.append(etapa("Comparación de los métodos", calculos=comparacion["lineas"], conclusion=comparacion["conclusion"]))
    informe = {**base, "definido": True, "jacobi": resultado_j, "gauss_seidel": resultado_gs, "referencia": referencia,
               "comparacion": comparacion, "titulo": comparacion["titulo"], "conclusion": comparacion["conclusion"], "procedimiento": etapas}
    informe["verificacion"] = verificar_iterativos(informe)
    return informe


def _etapa_diagonal(titulo, analisis, orden):
    """Explica fila por fila la dominancia diagonal: es una condición suficiente de convergencia, no necesaria.

    Entrada: título, analisis de analizar_diagonal y orden de las ecuaciones. Salida: etapa.
    """
    calculos = [f"Fila {k + 1} (E{orden[k] + 1}): |a{k + 1}{k + 1}| = {formatear_real(f['diagonal'], 8)} "
                f"{'>' if f['cumple'] else '≤'} {formatear_real(f['resto'], 8)} = Σ |a{k + 1}j|, j ≠ {k + 1}"
                for k, f in enumerate(analisis["filas"])]
    if analisis["ceros"]:
        conclusion = "Hay ceros en la diagonal: no se puede dividir entre aᵢᵢ."
    elif analisis["dominante"]:
        conclusion = "Es estrictamente diagonal dominante: Jacobi y Gauss-Seidel convergen desde cualquier x⁽⁰⁾."
    else:
        conclusion = ("No es estrictamente diagonal dominante. Como la condición es suficiente pero no necesaria, "
                      "esto no implica que los métodos diverjan: hay que observar las iteraciones.")
    return etapa(titulo, formula="|aᵢᵢ| > Σⱼ≠ᵢ |aᵢⱼ| para cada fila i", calculos=calculos,
                 condiciones=[condicion("Diagonal sin ceros.", not analisis["ceros"]),
                              condicion("Diagonal estrictamente dominante por filas.", analisis["dominante"])],
                 conclusion=conclusion)


def _referencia(datos):
    """Obtiene la solución exacta con el Gauss-Jordan de la calculadora, solo para comprobar los métodos iterativos.

    Entrada: datos validados. Salida: diccionario con solucion (floats o None), exacta (Fraction) y clasificacion.
    """
    A = [[Fraction(v) for v in fila] for fila in datos["A"]]
    b = [Fraction(v) for v in datos["b"]]
    resultado = resolver_sistema(A, b)
    exacta = resultado["solucion"]
    return {"solucion": [float(v) for v in exacta] if exacta is not None else None, "exacta": exacta,
            "clasificacion": resultado["clasificacion"]}


def comparar_metodos(resultado_j, resultado_gs, referencia):
    """Compara iteraciones, soluciones y diferencias con la solución de referencia.

    Entrada: resultados de Jacobi y Gauss-Seidel y referencia de Gauss-Jordan. Salida: diccionario con lineas, titulo y conclusion.
    """
    lineas, diferencias = [], {}
    for r in (resultado_j, resultado_gs):
        estado = "convergió" if r["convergio"] else "no convergió"
        lineas.append(f"{r['nombre']}: {estado} en {r['n_iteraciones']} iteraciones; residuo ‖Ax − b‖∞ = {formatear_real(r['residuo'], 4)}")
        if referencia["solucion"] is not None and r["estado"] != "no_finito":
            diferencias[r["metodo"]] = norma_infinito([a - c for a, c in zip(r["solucion"], referencia["solucion"])])
            lineas.append(f"   ‖x − x_GJ‖∞ = {formatear_real(diferencias[r['metodo']], 4)}")
    ambos = resultado_j["convergio"] and resultado_gs["convergio"]
    entre = norma_infinito([a - c for a, c in zip(resultado_j["solucion"], resultado_gs["solucion"])]) if ambos else None
    if ambos:
        lineas.append(f"Diferencia entre ambas soluciones: ‖x_J − x_GS‖∞ = {formatear_real(entre, 4)}")
        if resultado_j["n_iteraciones"] == resultado_gs["n_iteraciones"]:
            mejor, titulo = None, f"Ambos métodos convergieron en {resultado_j['n_iteraciones']} iteraciones"
        else:
            mejor = min((resultado_j, resultado_gs), key=lambda r: r["n_iteraciones"])
            otro = resultado_gs if mejor is resultado_j else resultado_j
            titulo = f"{mejor['nombre']} convergió en {mejor['n_iteraciones']} iteraciones; {otro['nombre']} en {otro['n_iteraciones']}"
        conclusion = ("Ambos métodos convergieron a la misma solución." +
                      (f" {mejor['nombre']} necesitó menos iteraciones." if mejor else ""))
    elif resultado_j["convergio"] or resultado_gs["convergio"]:
        bueno = resultado_j if resultado_j["convergio"] else resultado_gs
        malo = resultado_gs if bueno is resultado_j else resultado_j
        titulo = f"Solo {bueno['nombre']} convergió ({bueno['n_iteraciones']} iteraciones)"
        conclusion = f"{malo['nombre']} no convergió con este orden de ecuaciones; {bueno['nombre']} sí."
    else:
        titulo = "Ningún método convergió"
        conclusion = ("Ninguno de los dos métodos alcanzó la tolerancia: el error no disminuye. "
                      + (f"La solución exacta existe, x = {_texto_vector(referencia['solucion'], 6)}, pero estos métodos no la alcanzan."
                         if referencia["solucion"] is not None else ""))
    return {"lineas": lineas, "titulo": titulo, "conclusion": conclusion, "diferencias": diferencias, "entre_metodos": entre,
            "menos_iteraciones": (None if not ambos or resultado_j["n_iteraciones"] == resultado_gs["n_iteraciones"] else
                                  min((resultado_j, resultado_gs), key=lambda r: r["n_iteraciones"])["nombre"])}


def verificar_iterativos(informe):
    """Comprueba de forma independiente: residuos con el sistema original, solución de Gauss-Jordan y cada regla de iteración.

    Entrada: informe de resolver_iterativos. Salida: diccionario con correcto, etapas y chequeos.
    """
    datos, A, b = informe["datos"], informe["A_usada"], informe["b_usada"]
    etapas, chequeos = [], []

    def registrar(nombre, correcto):
        """Anota una comprobación con su resultado.

        Entrada: nombre y correcto (bool). Salida: None.
        """
        chequeos.append({"nombre": nombre, "correcto": bool(correcto)})

    referencia = informe["referencia"]
    for resultado in (informe["jacobi"], informe["gauss_seidel"]):
        condiciones, calculos = [], []
        filas = resultado["iteraciones"]
        regla = True
        for anterior, fila in zip(filas, filas[1:6]):
            # Se recalcula cada iteración desde su propia definición, sin reutilizar el código que la produjo.
            esperado = []
            for i in range(len(A)):
                valores = [(esperado[j] if resultado["metodo"] == "gauss_seidel" and j < i else anterior["x"][j]) for j in range(len(A))]
                esperado.append((b[i] - sum(A[i][j] * valores[j] for j in range(len(A)) if j != i)) / A[i][i])
            regla = regla and norma_infinito([a - c for a, c in zip(esperado, fila["x"])]) <= 1e-12 * max(1.0, norma_infinito(esperado))
        condiciones.append(condicion(f"Las primeras iteraciones cumplen la regla de {resultado['nombre']}.", regla))
        registrar(f"Regla de {resultado['nombre']}", regla)
        r = norma_infinito(residuo(datos["A"], datos["b"], resultado["solucion"]))
        calculos.append(f"Residuo con el sistema original: ‖Ax − b‖∞ = {formatear_real(r, 6)}")
        if resultado["convergio"]:
            pequeno = r <= 1e3 * datos["tolerancia"] * max(1.0, norma_infinito(datos["b"]), max(abs(v) for fila in datos["A"] for v in fila))
            condiciones.append(condicion("El residuo es pequeño, del orden de la tolerancia.", pequeno))
            registrar(f"Residuo de {resultado['nombre']}", pequeno)
            if referencia["solucion"] is not None:
                distancia = norma_infinito([a - c for a, c in zip(resultado["solucion"], referencia["solucion"])])
                cerca = distancia <= 1e3 * datos["tolerancia"] * max(1.0, norma_infinito(referencia["solucion"]))
                calculos.append(f"Gauss-Jordan (exacta): {_texto_vector(referencia['solucion'], 10)}")
                calculos.append(f"‖x − x_GJ‖∞ = {formatear_real(distancia, 4)}")
                condiciones.append(condicion("La aproximación coincide con Gauss-Jordan dentro de la tolerancia.", cerca))
                registrar(f"Comparación de {resultado['nombre']} con Gauss-Jordan", cerca)
        else:
            calculos.append("No convergió: se informa la advertencia en lugar de una solución.")
            condiciones.append(condicion("La falta de convergencia se informó con una advertencia.", bool(resultado["advertencias"])))
            registrar(f"Advertencia de {resultado['nombre']}", bool(resultado["advertencias"]))
        etapas.append(etapa(f"Verificación de {resultado['nombre']}", calculos=calculos, condiciones=condiciones))
    correcto = all(c["correcto"] for c in chequeos)
    etapas.append(etapa("Conclusión de la verificación", conclusion="Se cumple" if correcto else "No se cumple"))
    return {"correcto": correcto, "etapas": etapas, "chequeos": chequeos}


def tabla_iteraciones(resultado, cifras=8):
    """Arma las filas de la tabla de iteraciones: k, cada xᵢ, el error y el residuo.

    Entrada: resultado de iterar y cifras significativas. Salida: (encabezados, filas de textos).
    """
    n = len(resultado["solucion"])
    encabezados = ["k"] + [f"x{i + 1}" for i in range(n)] + ["error ‖Δx‖∞", "residuo"]
    filas = [[str(f["k"])] + [formatear_real(v, cifras) for v in f["x"]] +
             ["—" if f["error"] is None else formatear_real(f["error"], 3), formatear_real(f["residuo"], 3)]
             for f in resultado["iteraciones"]]
    return encabezados, filas


def formatear_iterativos(informe, maximo_filas=40):
    """Convierte el informe en líneas para la consola: análisis, tablas de ambos métodos y comparación.

    Entrada: informe y máximo de filas por tabla. Salida: lista de cadenas.
    """
    lineas = [informe["titulo"], informe["conclusion"], ""]
    for paso in informe["procedimiento"][:3]:
        lineas.append(paso["titulo"])
        lineas += [f"   {c}" for c in paso["calculos"]]
        if paso["conclusion"]:
            lineas.append(f"   → {paso['conclusion']}")
    if not informe["definido"]:
        return lineas
    for resultado in (informe["jacobi"], informe["gauss_seidel"]):
        encabezados, filas = tabla_iteraciones(resultado, 7)
        anchos = [max(len(e), *(len(f[k]) for f in filas)) for k, e in enumerate(encabezados)]
        lineas += ["", f"Tabla de {resultado['nombre']}", "  ".join(e.rjust(a) for e, a in zip(encabezados, anchos))]
        visibles = filas if len(filas) <= maximo_filas else filas[:maximo_filas // 2] + [["…"] * len(encabezados)] + filas[-maximo_filas // 2:]
        lineas += ["  ".join(v.rjust(a) for v, a in zip(fila, anchos)) for fila in visibles]
        lineas.append(f"Estado: {'convergencia alcanzada' if resultado['convergio'] else 'máximo de iteraciones / posible no convergencia'}"
                      f"; iteraciones: {resultado['n_iteraciones']}; residuo final ‖Ax − b‖∞ = {formatear_real(resultado['residuo'], 4)}")
        lineas += [f"Advertencia: {a}" for a in resultado["advertencias"]]
    lineas += ["", "Comparación"] + [f"   {l}" for l in informe["comparacion"]["lineas"]]
    lineas.append("Verificación: " + ("superada" if informe["verificacion"]["correcto"] else "con diferencias"))
    return lineas

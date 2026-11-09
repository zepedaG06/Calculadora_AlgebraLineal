# Calculadora de Álgebra Lineal (Programas 1 a 7)

Proyecto universitario del Grupo 3 (Universidad Americana, Álgebra Lineal MTM0120) para resolver problemas de álgebra lineal con aritmética exacta. El Programa 6 agrega la **factorización LU y la solución de Ax = b** (`modulos/modulo_lu.py`) y las mejoras obligatorias de las Tareas 4 y 5. El Programa 7 agrega el módulo de **Métodos Numéricos** (`modulos/modulo_numericos.py`): bisección, graficador de funciones, notación posicional en base 10 y base 2 y errores numéricos, más una sección de **renders y animaciones** (`modulos/graficos.py`).

## Secciones

- **Calculadora**: sistemas de ecuaciones lineales de hasta 10 × 10, con clasificación, rango, solución única o paramétrica y verificación.
- **Combinaciones lineales**: indica si w pertenece a Gen{v1, …, vn} y con qué coeficientes.
- **Ecuación Ax = b**: vista matricial del sistema, forma vectorial paramétrica y comprobación de A·x = b.
- **Propiedades de Ax**: se cargan las columnas a1, a2, … de A y un vector v; calcula Av = v1·a1 + … + vn·an (y fila por fila) y comprueba A(cv) = c(Av).
- **Operaciones con matrices**: se escribe o se construye con botones una expresión con A, B y C (por ejemplo `2A − 3B + C`, `A(B + C)`, `(AB)ᵀ` o `AᵀBC`). El analizador respeta paréntesis, precedencia, orden de los factores, transpuestas (`Aᵀ`, `A^T`, `A'`), escalares (números, `r`, `s`) e identidades (`I2`, `I3`, …). El procedimiento muestra los datos con sus dimensiones, la condición de dimensiones de cada operación intermedia, la regla aplicada, el cálculo de cada entrada (desplegable) y la respuesta. La verificación recalcula cada paso con un método independiente, recalcula toda la expresión desde los datos originales y, cuando existe, la compara con una ruta equivalente por propiedad (por ejemplo `A(B + C)` frente a `AB + AC`). También incluye propiedades teóricas con su demostración general, contraejemplos y ejercicios tipo examen; una comprobación numérica se identifica como caso particular, no como demostración.
- **Independencia lineal**: pide la cantidad de vectores p y su dimensión n, construye el sistema homogéneo [A | 0], lo reduce a forma escalonada por filas, cuenta pivotes y variables libres y da el veredicto (L.I. o L.D.). Si son dependientes, también muestra una relación de dependencia.
- **Factorización LU y solución Ax = b**: se escriben A (m × n) y b. A se lleva a una forma escalonada U solo con reemplazos `Fi ← Fi − l·Fj` (i > j) y cada multiplicador l = elemento a eliminar / pivote queda en L (m × m, triangular inferior con unos en la diagonal) en la posición (i, j). Se verifica «La factorización es correcta (L · U == A)» y se resuelve Ax = b en dos etapas: reducción de [L | b] (sustitución hacia adelante, vector intermedio y) y reducción de [U | y] (sustitución hacia atrás, solución x), con la comprobación final «Comprobación exitosa: A · x == b». La página muestra el logotipo ASCII del módulo y la opción «0. Ver Teoremas Clave del Módulo». Admite matrices rectangulares, columnas sin pivote (soluciones paramétricas) y sistemas inconsistentes; si hace falta un intercambio de filas informa «La matriz no admite Factorización LU sin permutación (requiere pivoteo parcial PA = LU)» sin inventar una factorización.
- **Métodos numéricos** (Programa 7), con la opción «0. Ver Teoremas Clave del Módulo» y cuatro opciones que animan, explican y verifican su procedimiento:
  1. **Bisección**: f(x) se escribe como texto (`x^3 - x - 2`, `cos(x) - x`, `e^x - 3x`). Comprueba el teorema de Bolzano, calcula de antemano las iteraciones necesarias n ≥ log₂((b − a)/tol), anima cómo el intervalo [a, b] se reduce a la mitad y grafica la convergencia del error. Si f(a) y f(b) tienen el mismo signo sugiere un intervalo con cambio de signo, y si el cambio de signo se debe a una discontinuidad (tan x, 1/x) avisa que no es una raíz.
  2. **Graficador**: hasta tres funciones con trazado animado, ceros, extremos, intersecciones y asíntotas sin líneas falsas. La rueda acerca, arrastrar mueve, doble clic restablece y el cursor lee los valores.
  3. **Notación posicional en base 10 y base 2**: descompone el número en dígitos, pesos y contribuciones, lo convierte con divisiones y multiplicaciones sucesivas (detecta los desarrollos periódicos, como 0.1 = 0.0(0011)₂) y muestra sus bits en IEEE 754 de 32 y 64 bits con el error de representación exacto.
  4. **Errores numéricos**: errores absoluto, relativo y porcentual con fracciones exactas, cifras significativas garantizadas, redondeo frente a truncamiento, épsilon de la máquina (2⁻⁵²), acumulación del error, truncamiento de una serie y cancelación de cifras.
- **Renders y animaciones**: cómo una matriz 2×2 o 3×3 deforma el plano o el espacio (con |det| como área o volumen), las rectas o planos de un sistema y dónde se cruzan, y las combinaciones lineales en R² y R³. En 3D la cámara gira sola o con el mouse. Cada render se exporta a PNG en alta resolución. Las secciones de sistemas, combinaciones, determinantes y LU tienen accesos directos a estos renders, y LU muestra el mapa de calor de L y U.
- **Método** y **Ayuda**: explicación del algoritmo con un ejemplo resuelto, atajos y conceptos clave.

Cada sección permite cargar ejemplos, generar datos aleatorios y ver el procedimiento completo o paso a paso (con reproducción automática). La fila que cambia se resalta y el pivote aparece encerrado en cada matriz.

## Restricciones

No se usa:

- PySide6
- NumPy
- SciPy
- el módulo `math` (el mcd y el mcm se calculan con el algoritmo de Euclides; seno, coseno, exponencial, logaritmo y arcotangente, con series de Taylor propias)

El algoritmo de eliminación por filas está implementado manualmente con fracciones exactas (`fractions.Fraction`). Los módulos de `modulos/` y `teoremas/` son funciones puras: reciben listas anidadas, retornan resultados y no usan `input()` ni `print()`; la entrada y salida de consola vive en `main.py`. La interfaz usa CustomTkinter, una capa visual moderna basada en Tkinter.

## Instalar dependencias

Windows:

```powershell
py -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m pip install -r requirements.txt
```

Pillow se usa para mostrar el logo de la UAM y para exportar los renders a PNG. Si no está instalado, el programa funciona igual, pero sin logo y sin exportar imágenes.

## Cómo ejecutar

Interfaz gráfica (Windows: `py main.py`):

```bash
python3 main.py
```

### Menú principal de consola (sin librerías externas)

```bash
python3 main.py --consola
```

Opciones: 1. Abrir la interfaz gráfica · 2. **Factorización LU y solución Ax = b** · 3. Verificador de propiedades de matrices · 4. Independencia lineal · 5. **Métodos numéricos** · S. Salir. La opción 2 muestra el logotipo ASCII del módulo y «0. Ver Teoremas Clave del Módulo»; pide m × n, las filas de A y el vector b, valida cada dato (si es inválido lo notifica y lo vuelve a pedir sin cerrarse) y despliega L, U, el mensaje de verificación, y, x y la comprobación final. Si CustomTkinter no está instalado, `main.py` abre este menú automáticamente. El archivo histórico `python3 "Programa 1_Grupo3.py" --consola` conserva el análisis de independencia lineal.

## Cómo usar

- Ajusta el tamaño con los botones − y +; los valores ya escritos se conservan.
- Se aceptan enteros (`3`), decimales (`0.5` o `0,5`) y fracciones (`3/2`). Una casilla con borde rojo tiene un valor no válido.
- `Enter` pasa a la siguiente casilla, `↑`/`↓` cambian de fila y `Ctrl + Enter` (`⌘ + Enter` en macOS) resuelve.

## Cómo probar

```bash
python3 -m unittest discover -v
```

`test_tarea7.py` comprueba los requisitos del Programa 7 (funciones elementales propias, intérprete de funciones, bisección, graficador, notación posicional, errores, motor de renders, consola y GUI) y `test_tarea6.py` los del Programa 6 (reglas técnicas, mensajes exactos, reutilización, cobertura de propiedades, encadenamiento y consola) y `test_modulo_lu.py` la factorización con oráculos y datos alterados.

En Windows usa `py` en lugar de `python3`.

## Framework elegido

Se usa CustomTkinter porque permite una interfaz de escritorio moderna con modo oscuro, tarjetas, botones estilizados y entradas claras para matrices. No resuelve operaciones matemáticas: solo mejora la presentación visual y se conecta con el algoritmo manual del programa. Las matrices de cada paso se dibujan en un `Canvas` de Tkinter para que incluso un sistema de 10 × 10 (unos 100 pasos) se muestre con fluidez.

## Determinantes, inversas y teoremas

Ejecuta `py main.py` en Windows. El archivo histórico sigue funcionando como
punto de entrada compatible. En **Determinantes e inversas** introduce una fila
por línea y separa entradas con espacios o punto y coma. Acepta fracciones,
enteros y decimales. B solo se utiliza para la propiedad de la inversa de AB;
k se utiliza para multiplicar una fila o sumar un múltiplo de otra.

Métodos de determinante: fórmula 2×2, Sarrus (exclusivamente 3×3), expansión por
cofactores y reducción triangular para cualquier orden. Los menores se calculan
por reducción triangular; se define el menor de una entrada de una matriz 1×1
como 1. En la reducción no se escalan filas: solo se intercambian y se suman
múltiplos, registrando el signo y multiplicando la diagonal final.

La inversa se calcula por Gauss-Jordan sobre `[A|I]` o mediante
`adj(A)/det(A)`. Cada resultado verifica exactamente ambos productos con A.
La opción de comparación calcula los dos métodos y comprueba igualdad exacta.
Una matriz singular produce un diagnóstico, nunca una inversa falsa.

Las propiedades muestran ambos lados, comparación y conclusión, comprobando
primero las condiciones necesarias. Las verificaciones de familias paramétricas
comprueban tanto `Ap=b` como `Av=0` para cada vector dirección. Una comprobación
numérica de una propiedad es un caso particular, no una demostración general.

La sección **0. Ver Teoremas Clave del Módulo** conserva un resumen académico;
también puedes consultarlo sin abrir la GUI con `py -X utf8 main.py --teoremas`.
Los procedimientos tienen desplazamiento vertical y horizontal; el menú lateral
también permite desplazarse cuando el tamaño o escalado de pantalla lo requiere.

## Organización y pruebas completas

```text
main.py                    Menú principal (GUI o consola con --consola)
Programa 1_Grupo3.py        GUI y compatibilidad con imports históricos
modulos/modulo_matrices.py  Núcleo exacto, sin dependencias gráficas ni E/S
modulos/modulo_lu.py        Factorización LU, Ly = b, Ux = y y su verificación
teoremas/teoremas_matrices.py  Teoremas y demostraciones de matrices e inversas
modulos/modulo_numericos.py Bisección, graficador, base 10 y base 2, errores (sin math)
modulos/graficos.py         Escenas vectoriales: gráficas, animaciones y renders 2D/3D
teoremas/teoremas_lu.py    Logotipo ASCII y teoremas clave del módulo LU
teoremas/teoremas_numericos.py  Logotipo ASCII y teoremas del módulo de Métodos Numéricos
test_algoritmo.py           Suite histórica, conservada
test_matrices_avanzadas.py  Determinantes, inversas, propiedades y regresión
test_modulo_lu.py           LU con oráculos, datos alterados y GUI
test_tarea6.py              Requisitos del Programa 6
test_tarea7.py              Requisitos del Programa 7
```

Ejecuta `py -m unittest discover -v` para incluir todos los tests. Las pruebas
contrastan determinantes con la definición independiente por permutaciones,
comparan las inversas y verifican singularidad, Fraction y vectores del espacio
nulo. No se necesitan bibliotecas matemáticas externas.

El núcleo admite matrices mayores que las de la GUI; esta limita la captura
a 10×10. Para matrices grandes conviene reducción triangular y Gauss-Jordan:
la adjunta requiere muchos menores y genera procedimientos más extensos.

## Resultado, procedimiento y verificación

Todas las páginas de cálculo y el ejemplo del método de eliminación separan
**Resultado**, **Procedimiento** y **Verificación**. El resultado muestra la
respuesta y su interpretación. El procedimiento muestra las condiciones reales,
fórmulas, operandos, operaciones, matrices intermedias, pivotes y parámetros.
La verificación utiliza los datos originales: sustituciones en sistemas,
reconstrucción de combinaciones, ambos productos de inversas y comparación de
determinantes por métodos distintos.

Los pasos se pueden consultar completos o uno por uno. Los cálculos de cada
entrada y el desarrollo de menores se pueden desplegar; las matrices conservan
desplazamiento horizontal. La barra de `[A|I]` separa los bloques de n columnas;
la de `[A|b]` separa la última columna, y A se representa sin barra.

Las propiedades calculan cada lado por separado. Las básicas tienen un recálculo
independiente de la expresión sin usar la identidad que se está verificando.
Las de inversas/determinantes se contrastan cambiando Gauss-Jordan por adjunta y
reducción triangular por cofactores. La comparación muestra las entradas de
ambos lados y concluye «Se cumple» o «No se cumple».

Para un sistema inconsistente se comprueba una combinación de las ecuaciones
originales: `yᵀA=0` y `yᵀb≠0`, lo que produciría una contradicción si existiera
solución. Para independencia se comprueba una relación no trivial cuando hay
dependencia; cuando hay independencia se construye L y se verifica `LA=I`:
si `Ac=0`, entonces `c=LAc=0`.

Los datos visuales viven en `modulos/pasos.py` y `modulos/informes.py`, sin
dependencias gráficas. `test_presentacion_matematica.py` comprueba estructura,
condiciones, ambas rutas y detección de resultados deliberadamente incorrectos.

## Factorización LU (`modulos/modulo_lu.py`)

```python
from modulos import modulo_lu as lu

r = lu.resolver_lu([[3, -7, -2, 2], [-3, 5, 1, 0], [6, -4, 0, -5], [-9, 5, -5, 12]], [-9, 5, 7, 11])
r["matriz_L"], r["matriz_U"], r["vector_y"], r["solucion"]   # y = (-9, -4, 5, 1), x = (3, 4, -6, -1)
r["verificacion_factorizacion"]["mensaje"]   # La factorización es correcta (L · U == A)
r["comprobacion"]["mensaje"]                 # Comprobación exitosa: A · x == b
lu.verificar_lu(r)["correcto"]                # True
```

- `calcular_multiplicador(matriz_U, fila, fila_pivote, columna)`: l = elemento a eliminar / pivote.
- `factorizar_lu(matriz_A)`: L, U, pivotes y cada reemplazo con su multiplicador; reutiliza
  `buscar_fila_pivote` y `sumar_multiplo_fila` de `modulo_matrices`.
- `verificar_factorizacion(A, L, U)`: L · U con `multiplicar_matrices` y `son_iguales`.
- `sustitucion_adelante(L, b)` y `sustitucion_atras(U, y)`: reducción de [L | b] y de [U | y]
  con las operaciones elementales de la Calculadora; cada una guarda la entrada que recibió,
  de modo que el encadenamiento A → (L, U) → y → x se puede comprobar.
- `comprobar_solucion(A, x, b)`: A · x con `multiplicar_matriz_vector` (y A·v = 0 en familias).
- `verificar_lu(resultado)`: verificación independiente: encadenamiento, estructura de L y U,
  L·U = A, L·y = b, U·x = y, A·x = b con la A original, U recalculada por eliminación
  gaussiana, comparación con Gauss-Jordan y det(A) = ∏ uᵢᵢ frente a Sarrus o cofactores.
- `formatear_resultado_lu(resultado)`: líneas de texto (L, U, mensajes, y, x) para la consola.

## Verificador de propiedades (cobertura completa)

`verificar_propiedades_clave(A, B, C, k)` en `modulo_matrices.py` calcula ambos miembros de
cada propiedad con las funciones internas y devuelve «Se cumple», «No se cumple» o «No aplica»
con la hipótesis que falta:

- Transposición: (Aᵀ)ᵀ = A, (A + B)ᵀ = Aᵀ + Bᵀ, (kA)ᵀ = kAᵀ, (AB)ᵀ = BᵀAᵀ, A(B + C) = AB + AC, (AB)C = A(BC).
- Inversa: (A⁻¹)⁻¹ = A, (AB)⁻¹ = B⁻¹A⁻¹, (Aᵀ)⁻¹ = (A⁻¹)ᵀ, A·A⁻¹ = I.
- Determinantes: det(Aᵀ) = det(A), det(AB) = det(A)·det(B), det(A⁻¹) = 1/det(A), det(kA) = kⁿ·det(A).
- Operaciones de fila: la permutación cambia el signo, el reemplazo conserva det, multiplicar
  una fila por k multiplica det por k y det(triangular) = producto de la diagonal.

Los resultados intermedios (AB, Aᵀ, A⁻¹, det(A), …) se calculan una sola vez y se pasan como
argumentos a las demás propiedades. Está disponible en la GUI (Operaciones matriciales →
«Cobertura completa», con k = r) y en la consola (opción 3). La propiedad det(kA) = kⁿ·det(A)
también se puede elegir en «Determinantes e inversas».

## Inversa: A⁻¹A = I

En **Determinantes e inversas** las propiedades `A⁻¹A = I` y `AA⁻¹ = I` se pueden elegir
directamente: calculan A⁻¹ por Gauss-Jordan, el producto fila por columna y la identidad, y
lo recalculan por adjunta. En **Operaciones matriciales**, las expresiones `A⁻¹A` y `AA⁻¹`
se verifican además contra la identidad del orden correspondiente.

## Encadenamiento de datos entre secciones

Los botones «↪» llevan un resultado a otra sección sin volver a escribirlo:

- Factorización LU → Operaciones matriciales: A = L, B = U y C = A original con `AB − C`
  (debe dar la matriz cero).
- Factorización LU ⇄ Ecuación Ax = b: el mismo sistema por Gauss-Jordan o por LU.
- Determinantes e inversas → Operaciones matriciales: A original y B = A⁻¹ con `BA`.
- Operaciones matriciales: «Usar como A / B / C» guarda el resultado de una expresión para
  el siguiente cálculo.

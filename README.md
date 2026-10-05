# Programa 1 - Calculadora de Algebra Lineal

Proyecto universitario del Grupo 3 (Universidad Americana) para resolver problemas de álgebra lineal por eliminación por filas (Gauss-Jordan).

## Secciones

- **Calculadora**: sistemas de ecuaciones lineales de hasta 10 × 10, con clasificación, rango, solución única o paramétrica y verificación.
- **Combinaciones lineales**: indica si w pertenece a Gen{v1, …, vn} y con qué coeficientes.
- **Ecuación Ax = b**: vista matricial del sistema, forma vectorial paramétrica y comprobación de A·x = b.
- **Propiedades de Ax**: se cargan las columnas a1, a2, … de A y un vector v; calcula Av = v1·a1 + … + vn·an (y fila por fila) y comprueba A(cv) = c(Av).
- **Operaciones con matrices**: se escribe o se construye con botones una expresión con A, B y C (por ejemplo `2A − 3B + C`, `A(B + C)`, `(AB)ᵀ` o `AᵀBC`). El analizador respeta paréntesis, precedencia, orden de los factores, transpuestas (`Aᵀ`, `A^T`, `A'`), escalares (números, `r`, `s`) e identidades (`I2`, `I3`, …). El procedimiento muestra los datos con sus dimensiones, la condición de dimensiones de cada operación intermedia, la regla aplicada, el cálculo de cada entrada (desplegable) y la respuesta. La verificación recalcula cada paso con un método independiente, recalcula toda la expresión desde los datos originales y, cuando existe, la compara con una ruta equivalente por propiedad (por ejemplo `A(B + C)` frente a `AB + AC`). También incluye propiedades teóricas con su demostración general, contraejemplos y ejercicios tipo examen; una comprobación numérica se identifica como caso particular, no como demostración.
- **Independencia lineal**: pide la cantidad de vectores p y su dimensión n, construye el sistema homogéneo [A | 0], lo reduce a forma escalonada por filas, cuenta pivotes y variables libres y da el veredicto (L.I. o L.D.). Si son dependientes, también muestra una relación de dependencia.
- **Método** y **Ayuda**: explicación del algoritmo con un ejemplo resuelto, atajos y conceptos clave.

Cada sección permite cargar ejemplos, generar datos aleatorios y ver el procedimiento completo o paso a paso (con reproducción automática). La fila que cambia se resalta y el pivote aparece encerrado en cada matriz.

## Restricciones

No se usa:

- PySide6
- NumPy
- SciPy

El algoritmo de eliminación por filas está implementado manualmente con fracciones exactas (`fractions.Fraction`). La interfaz usa CustomTkinter, una capa visual moderna basada en Tkinter.

## Instalar dependencias

Windows:

```powershell
py -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m pip install -r requirements.txt
```

Pillow se usa para mostrar el logo de la UAM (el archivo está en formato WebP). Si no está instalado, el programa funciona igual pero sin logo.

## Cómo ejecutar

Windows:

```powershell
py "Programa 1_Grupo3.py"
```

macOS / Linux:

```bash
python3 "Programa 1_Grupo3.py"
```

### Modo consola (sin librerías externas)

El análisis de independencia lineal también funciona en la terminal, usando solo Python estándar:

```bash
python3 "Programa 1_Grupo3.py" --consola
```

Pide p, n y los vectores, y muestra el sistema [A | 0], las operaciones elementales, la forma escalonada por filas, el número de pivotes y el veredicto. Si CustomTkinter no está instalado, el programa abre este modo automáticamente.

## Cómo usar

- Ajusta el tamaño con los botones − y +; los valores ya escritos se conservan.
- Se aceptan enteros (`3`), decimales (`0.5` o `0,5`) y fracciones (`3/2`). Una casilla con borde rojo tiene un valor no válido.
- `Enter` pasa a la siguiente casilla, `↑`/`↓` cambian de fila y `Ctrl + Enter` (`⌘ + Enter` en macOS) resuelve.

## Cómo probar

```bash
python3 -m unittest test_algoritmo.py
```

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
main.py                    Entrada limpia (sin abrir ventanas al importar)
Programa 1_Grupo3.py        GUI y compatibilidad con imports históricos
modulos/modulo_matrices.py  Núcleo exacto, sin dependencias gráficas ni E/S
teoremas/teoremas_matrices.py  Contenido académico y logo ASCII de consola
test_algoritmo.py           Suite histórica, conservada
test_matrices_avanzadas.py  Determinantes, inversas, propiedades y regresión
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

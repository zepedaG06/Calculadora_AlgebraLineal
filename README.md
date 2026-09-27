# Programa 1 - Calculadora de Algebra Lineal

Proyecto universitario del Grupo 3 (Universidad Americana) para resolver problemas de álgebra lineal por eliminación por filas (Gauss-Jordan).

## Secciones

- **Calculadora**: sistemas de ecuaciones lineales de hasta 10 × 10, con clasificación, rango, solución única o paramétrica y verificación.
- **Combinaciones lineales**: indica si w pertenece a Gen{v1, …, vn} y con qué coeficientes.
- **Ecuación Ax = b**: vista matricial del sistema, forma vectorial paramétrica y comprobación de A·x = b.
- **Propiedades de Ax**: comprueba A(u + v) = Au + Av y A(cu) = c(Au) fila por fila.
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

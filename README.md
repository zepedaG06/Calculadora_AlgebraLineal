# Programa 1 - Calculadora de Algebra Lineal

Proyecto universitario del Grupo 3 para resolver sistemas de ecuaciones lineales por eliminacion por filas.

## Restricciones

No se usa:

- PySide6
- NumPy
- SciPy

El algoritmo de eliminacion por filas esta implementado manualmente. La interfaz usa CustomTkinter, que es una capa visual moderna basada en Tkinter.

## Instalar dependencia visual

```powershell
py -m pip install -r requirements.txt
```

Tambien puedes instalarla directamente:

```powershell
py -m pip install customtkinter
```

## Como ejecutar

En Visual Studio Code, abre esta carpeta y ejecuta:

```powershell
py main.py
```

Si tu instalacion reconoce `python`, tambien funciona:

```powershell
python main.py
```

`Programa 1_Grupo3.py` se conserva como adaptador de compatibilidad para los tests y para ejecuciones antiguas.

## Como probar

```powershell
py -m unittest test_algoritmo.py
```

## Framework elegido

Se usa CustomTkinter porque permite una interfaz de escritorio moderna con modo oscuro, tarjetas, botones estilizados y entradas claras para matrices. No resuelve operaciones matematicas: solo mejora la presentacion visual y se conecta con el algoritmo manual del programa.

## Estructura del proyecto

La logica matematica esta separada de la interfaz:

- `logica/calculadora.py`: flujo de la calculadora y resolucion general de `Ax = b`.
- `logica/ecuacion_matricial.py`: caso de uso especifico para la ecuacion `Ax = b`.
- `logica/combinaciones_lineales.py`: transforma combinaciones lineales en sistemas `A*c = w`.
- `logica/independencia_lineal.py`: analiza el sistema homogeneo `A*c = 0`.
- `logica/nucleo/gauss_jordan.py`: operaciones elementales, pivotes y reduccion RREF.
- `logica/nucleo/formato.py`: conversion de entradas y presentacion de matrices y ecuaciones.
- `logica/nucleo/modelos.py`: estructuras para pasos de eliminacion y detalles de verificacion.
- `logica/nucleo/verificacion.py`: comprobacion de la solucion contra el sistema original.
- `interfaz/componentes.py`: componentes visuales reutilizables.
- `interfaz/paginas/`: una pantalla independiente para cada seccion.
- `interfaz/aplicacion.py`: ventana principal y navegacion.
- `main.py`: punto de entrada de la aplicacion.

### Flujo logico para la exposicion

1. La interfaz convierte las entradas de texto a `Fraction` mediante `formato.py`.
2. `sistemas.py` construye la matriz aumentada `[A | b]`.
3. `gauss_jordan.py` aplica intercambio, escalado y eliminacion de filas.
4. `sistemas.py` clasifica el resultado por pivotes y filas inconsistentes.
5. Se obtiene una solucion unica o una expresion parametrica.
6. `verificacion.py` sustituye la solucion en las ecuaciones originales.
7. Las secciones especiales preparan su sistema y reutilizan el mismo flujo.

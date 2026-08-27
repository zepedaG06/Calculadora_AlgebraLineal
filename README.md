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
py "Programa 1_Grupo3.py"
```

Si tu instalacion reconoce `python`, tambien funciona:

```powershell
python "Programa 1_Grupo3.py"
```

## Como probar

```powershell
py -m unittest test_algoritmo.py
```

## Framework elegido

Se usa CustomTkinter porque permite una interfaz de escritorio moderna con modo oscuro, tarjetas, botones estilizados y entradas claras para matrices. No resuelve operaciones matematicas: solo mejora la presentacion visual y se conecta con el algoritmo manual del programa.

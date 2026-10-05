"""Punto de entrada de la calculadora de álgebra lineal.

Carga la GUI histórica conservando su nombre y sus APIs compatibles.
Importar este módulo no abre ventanas ni pide datos por consola.
"""
import importlib.util
from pathlib import Path


def cargar_aplicacion():
    """Carga la aplicación desde una ruta independiente del directorio actual."""
    ruta = Path(__file__).with_name("Programa 1_Grupo3.py")
    spec = importlib.util.spec_from_file_location("calculadora_gui", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def main():
    cargar_aplicacion().main()


if __name__ == "__main__":
    main()

import customtkinter as ctk
from tkinter import messagebox

from interfaz.estilos import PALETA, FUENTE_SECCION, FUENTE_NORMAL, FUENTE_MONO
from logica.operaciones_elementales import (
    multiplicar_matrices,
    multiplicar_matriz_por_escalar,
    multiplicar_vector_por_escalar,
    restar_matrices,
    restar_vectores,
    sumar_matrices,
    sumar_vectores,
)


class PaginaOperacionesElementales(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=PALETA["fondo"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text="Operaciones elementales con matrices y vectores",
            font=("Segoe UI", 26, "bold"),
            text_color=PALETA["texto"],
        ).grid(row=0, column=0, sticky="w", padx=28, pady=(24, 12))

        cuerpo = ctk.CTkScrollableFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))

        intro = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10)
        intro.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(
            intro,
            text="Capa separada para operaciones básicas con vectores y matrices",
            font=FUENTE_SECCION,
        ).pack(anchor="w", padx=16, pady=(12, 8))
        ctk.CTkLabel(
            intro,
            text="Suma y resta de vectores y multiplicación por escalar, con validación de la misma dimensión.",
            font=FUENTE_NORMAL,
            text_color=PALETA["texto_2"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        self.config = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10)
        self.config.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(self.config, text="Operación", font=FUENTE_SECCION).pack(anchor="w", padx=16, pady=(12, 8))

        fila = ctk.CTkFrame(self.config, fg_color="transparent")
        fila.pack(anchor="w", padx=16, pady=(0, 12))
        self.operacion = ctk.CTkOptionMenu(
            fila,
            values=[
                "Suma de vectores",
                "Resta de vectores",
                "Producto por escalar (vector)",
            ],
            width=260,
            fg_color=PALETA["panel_2"],
            button_color=PALETA["primario"],
            dropdown_fg_color=PALETA["panel_2"],
            text_color=PALETA["texto"],
            command=self.mostrar_formulario,
        )
        self.operacion.set("Suma de vectores")
        self.operacion.pack(side="left")
        ctk.CTkButton( 
            fila,
            text="Calcular",
            fg_color=PALETA["primario"],
            hover_color=PALETA["primario_hover"],
            text_color="#04191A",
            command=self.ejecutar,
        ).pack(side="left", padx=(12, 0))

        self.entrada = ctk.CTkScrollableFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10)
        self.entrada.pack(fill="both", expand=True, pady=(0, 14))

        self.visualizador = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10)
        self.visualizador.pack(fill="x")
        ctk.CTkLabel(self.visualizador, text="Resultado", font=FUENTE_SECCION).pack(anchor="w", padx=16, pady=(12, 8))
        self.resultado_label = ctk.CTkLabel(self.visualizador, text="Ingresa valores y calcula.", font=FUENTE_MONO, text_color=PALETA["texto_2"], justify="left")
        self.resultado_label.pack(anchor="w", padx=16, pady=(0, 12))

        self.mostrar_formulario()

    def mostrar_formulario(self):
        for widget in self.entrada.winfo_children():
            widget.destroy()

        operacion = self.operacion.get()
        if operacion in ["Suma de vectores", "Resta de vectores", "Producto por escalar (vector)"]:
            self._mostrar_vector_form()
        else:
            self._mostrar_vector_form()

    def _mostrar_vector_form(self):
        ctk.CTkLabel(self.entrada, text="Vector A (separa componentes con comas)", font=FUENTE_NORMAL).pack(anchor="w", padx=16, pady=(14, 4))
        self.vector_a = ctk.CTkEntry(self.entrada, width=420, justify="center")
        self.vector_a.insert(0, "1, 2, 3")
        self.vector_a.pack(anchor="w", padx=16, pady=(0, 8))

        ctk.CTkLabel(self.entrada, text="Vector B o escalar", font=FUENTE_NORMAL).pack(anchor="w", padx=16, pady=(0, 4))
        self.vector_b = ctk.CTkEntry(self.entrada, width=420, justify="center")
        self.vector_b.insert(0, "4, 5, 6")
        self.vector_b.pack(anchor="w", padx=16, pady=(0, 12))


    def _parsear_vector(self, texto):
        texto = texto.strip()
        if ";" in texto:
            raise ValueError("Para vectores usa solo comas: ejemplo 1, 2, 3. Si escribes ';' entonces estás ingresando una matriz.")
        valores = [valor.strip() for valor in texto.split(",") if valor.strip()]
        if not valores:
            raise ValueError("El vector no puede estar vacío.")
        return [int(v) if v.strip().lstrip("-").isdigit() else float(v) for v in valores]

    def _parsear_matriz(self, texto):
        texto = texto.strip()
        filas = []
        for fila_texto in texto.split(";"):
            elementos = [valor.strip() for valor in fila_texto.split(",") if valor.strip()]
            if not elementos:
                continue
            fila = [int(v) if v.strip().lstrip("-").isdigit() else float(v) for v in elementos]
            filas.append(fila)
        if not filas:
            raise ValueError("La matriz no puede estar vacía.")
        columnas = len(filas[0])
        if any(len(fila) != columnas for fila in filas):
            raise ValueError("Todas las filas de la matriz deben tener la misma longitud. Ejemplo: 1, 2, 3; 4, 5, 6")
        return filas

    def ejecutar(self):
        try:
            operacion = self.operacion.get()
            resultado = None
            if operacion == "Suma de vectores":
                a = self._parsear_vector(self.vector_a.get())
                b = self._parsear_vector(self.vector_b.get())
                resultado = sumar_vectores(a, b)
            elif operacion == "Resta de vectores":
                a = self._parsear_vector(self.vector_a.get())
                b = self._parsear_vector(self.vector_b.get())
                resultado = restar_vectores(a, b)
            else:
                a = self._parsear_vector(self.vector_a.get())
                valor = self.vector_b.get().strip()
                escala = int(valor) if valor.lstrip("-").isdigit() else float(valor)
                resultado = multiplicar_vector_por_escalar(a, escala)

            self.resultado_label.configure(text=self._formatear_resultado(resultado))
            self.mostrar_formulario()
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def _formatear_resultado(self, resultado):
        if isinstance(resultado, list) and resultado and isinstance(resultado[0], list):
            filas = []
            for fila in resultado:
                filas.append("[ " + "  ".join(str(valor) for valor in fila) + " ]")
            return "\n".join(filas)
        if isinstance(resultado, list):
            return "[ " + "  ".join(str(valor) for valor in resultado) + " ]"
        return str(resultado)

    def _on_select(self, *_):
        self.mostrar_formulario()

    def bind(self, *_):
        pass

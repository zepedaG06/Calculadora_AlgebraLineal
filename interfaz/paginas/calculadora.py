import customtkinter as ctk
from tkinter import messagebox

from logica.calculadora import resolver_calculadora
from interfaz.componentes import EntradaMatriz, PanelProcedimiento, PanelResultado
from interfaz.estilos import PALETA, FUENTE_NORMAL, FUENTE_SECCION


class PaginaCalculadora(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=PALETA["fondo"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Calculadora de Algebra Lineal", font=("Segoe UI", 26, "bold"), text_color=PALETA["texto"]).grid(row=0, column=0, sticky="w", padx=28, pady=(24, 12))
        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        cuerpo.grid_columnconfigure(0, weight=2)
        cuerpo.grid_columnconfigure(1, weight=3)
        cuerpo.grid_rowconfigure(1, weight=1)
        configuracion = ctk.CTkFrame(cuerpo, fg_color=PALETA["panel"], corner_radius=10, border_width=1, border_color=PALETA["borde"])
        configuracion.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        ctk.CTkLabel(configuracion, text="Configuración del sistema", font=FUENTE_SECCION).pack(anchor="w", padx=16, pady=(12, 8))
        fila = ctk.CTkFrame(configuracion, fg_color="transparent")
        fila.pack(anchor="w", padx=16, pady=(0, 14))
        ctk.CTkLabel(fila, text="Ecuaciones").pack(side="left", padx=(0, 8))
        self.entrada_m = ctk.CTkEntry(fila, width=70, justify="center")
        self.entrada_m.insert(0, "3")
        self.entrada_m.pack(side="left", padx=(0, 14))
        ctk.CTkLabel(fila, text="Variables").pack(side="left", padx=(0, 8))
        self.entrada_n = ctk.CTkEntry(fila, width=70, justify="center")
        self.entrada_n.insert(0, "3")
        self.entrada_n.pack(side="left", padx=(0, 14))
        ctk.CTkButton(fila, text="Crear sistema", fg_color=PALETA["primario"], hover_color=PALETA["primario_hover"], text_color="#04191A", command=self.crear_sistema).pack(side="left")
        self.entrada = EntradaMatriz(cuerpo, self.resolver, self.limpiar)
        self.entrada.grid(row=1, column=0, sticky="nsew", padx=(0, 14))
        paneles = ctk.CTkTabview(cuerpo, fg_color=PALETA["panel"], segmented_button_selected_color=PALETA["primario"])
        paneles.grid(row=1, column=1, sticky="nsew")
        self.procedimiento = PanelProcedimiento(paneles.add("Procedimiento"))
        self.procedimiento.pack(fill="both", expand=True)
        self.resultado = PanelResultado(paneles.add("Resultado"))
        self.resultado.pack(fill="both", expand=True)
        self.crear_sistema()

    def crear_sistema(self):
        try:
            m, n = int(self.entrada_m.get()), int(self.entrada_n.get())
            if m <= 0 or n <= 0:
                raise ValueError
            self.entrada.crear(m, n)
            self.procedimiento.placeholder()
            self.resultado.placeholder()
        except ValueError:
            messagebox.showerror("Entrada invalida", "Las dimensiones deben ser enteros positivos.")

    def limpiar(self):
        self.entrada.limpiar()
        self.procedimiento.placeholder()
        self.resultado.placeholder()

    def resolver(self):
        try:
            A, b = self.entrada.leer()
            resultado = resolver_calculadora(A, b)
            self.procedimiento.mostrar(resultado["pasos"])
            self.resultado.mostrar(resultado)
        except Exception as error:
            messagebox.showerror("Error", str(error))

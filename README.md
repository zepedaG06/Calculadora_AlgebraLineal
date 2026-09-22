# Calculadora de Álgebra Lineal — Tarea 3

Proyecto universitario del **Grupo 3 (Universidad Americana - UAM)** para el curso de Álgebra Lineal.

## Restricciones Absolutas Cumplidas

- **NO se usa NumPy**
- **NO se usa SciPy**
- **NO se usan funciones avanzadas de math**
- Toda operación matemática está implementada manualmente en Python estándar utilizando `fractions.Fraction` para aritmética exacta sin errores de redondeo.
- Interfaz gráfica moderna con **CustomTkinter** y paleta institucional UAM.

## Módulos de la Tarea 3 Implementados

1. **Ecuación Matricial (Ax = b):**
   - Resolución de sistemas lineales $m \times n$ mediante eliminación de Gauss-Jordan manual.
   - Clasificación completa: Consistente Determinado, Consistente Indeterminado (con variables libres parametrizadas) e Inconsistente.
   - Registro de pasos elementales ($F_i \leftrightarrow F_j$, $F_i \rightarrow k F_i$, $F_k \rightarrow F_k + c F_i$) con justificación pedagógica y matriz formateada.
   - Verificación sustitutiva detallada ecuación por ecuación.
   - **Interpretación como combinación lineal de columnas:** muestra explícitamente $x_1 \mathbf{a}_1 + \dots + x_n \mathbf{a}_n = \mathbf{b}$.

2. **Módulo de Vectores en $\mathbb{R}^n$:**
   - Suma y resta de vectores componente a componente.
   - Multiplicación de vector por escalar ($k \cdot \mathbf{v}$).
   - Validación de dimensiones compatibles en $\mathbb{R}^n$.
   - Procedimiento algebraico detallado paso a paso.

3. **Combinación Lineal y Ecuación Vectorial:**
   - Análisis de $c_1 \mathbf{v}_1 + c_2 \mathbf{v}_2 + \dots + c_k \mathbf{v}_k = \mathbf{b}$.
   - Construcción automática del sistema $[A \mid \mathbf{b}]$ donde cada columna es un vector $\mathbf{v}_j$.
   - Nomenclatura consistente de coeficientes $c_1, c_2, \dots, c_k$.
   - Determinación analítica de soluciones únicas, infinitas o inexistentes.
   - Verificación vectorial formal: $(c_1)\mathbf{v}_1 + (c_2)\mathbf{v}_2 + \dots = \mathbf{b}_{\text{calc}} = \mathbf{b}$.

4. **Independencia Lineal:**
   - Determinación rigurosa de si un conjunto $\{\mathbf{v}_1, \dots, \mathbf{v}_k\}$ es **Linealmente Independiente (LI)** o **Linealmente Dependiente (LD)**.
   - Planteamiento y resolución del sistema homogéneo $[\mathbf{v}_1 \dots \mathbf{v}_k \mid \mathbf{0}]$.
   - Análisis de pivotes vs variables libres: solución trivial única (LI) vs soluciones no triviales (LD).
   - Relación de dependencia no trivial explícita en caso LD.

5. **Operaciones Básicas con Matrices:**
   - Suma ($A + B$) y resta ($A - B$) con validación estricta de dimensiones idénticas.
   - Multiplicación por escalar ($k \cdot A$).
   - Multiplicación matricial $A(m \times n) \cdot B(n \times p)$ implementada manualmente con bucles anidados y comprobación estricta de compatibilidad ($n_A = m_B$).
   - Desglose componente a componente del producto punto.

6. **Método de Eliminación y Ayuda:**
   - Glosario, conceptos teóricos y guía didáctica de uso.

## Instalar dependencias visuales

```powershell
py -m pip install -r requirements.txt
```

O directamente:

```powershell
py -m pip install customtkinter
```

## Cómo ejecutar la aplicación

```powershell
py "Programa 1_Grupo3.py"
```

O si utilizas el comando `python`:

```powershell
python "Programa 1_Grupo3.py"
```

## Pruebas automatizadas

El proyecto cuenta con 40 pruebas unitarias automatizadas (incluyendo los 22 tests obligatorios de la Tarea 3):

```powershell
py -m unittest test_algoritmo.py -v
```

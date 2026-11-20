"""Proyecto 2 · Centroide de un árbol · Video completo.

Secciones: título, motivación (juego del nodo escondido), definición y usos,
algoritmo (DFS + bajada al hijo pesado), casos de borde, complejidad y cierre
(descomposición en centroides) con créditos.

Un solo archivo: solo necesita Manim Community (sin LaTeX).

    manim -pql avance.py    # vista previa rápida (480p)
    manim -pqh avance.py    # final 1080p60

El archivo tiene una sola escena (Avance), así que Manim la renderiza completa
sin preguntar.

La animación la impulsa una implementación real: `encontrar_centroides` ejecuta
el algoritmo (DFS iterativo + bajada al hijo pesado) y registra cada paso en una
lista de eventos; las escenas solo dibujan esos eventos.
"""

import sys
from pathlib import Path

import numpy as np
from manim import (BOLD, DOWN, LEFT, ORIGIN, RIGHT, UL, UP, WHITE, AnimationGroup,
                   Arrow, Circle, Create, FadeIn, FadeOut, Flash, Group,
                   GrowArrow, GrowFromCenter, ImageMobject, Indicate, LaggedStart, Line,
                   RoundedRectangle, Scene, ShowPassingFlash, Square, Text, VGroup, Write,
                   config)

# =============================================================================
# Configuración
# =============================================================================
TITULO = "Centroide de un árbol"
SUBTITULO = "Proyecto 2 · CS2023 Algoritmos y Estructuras de Datos"
CICLO = "UTEC · 2026-2"
AUTORES = ["Estefano Zárate"]
PROFESOR = "Luciano A. Romero Calla"
LOGO = Path(__file__).resolve().parent / "assets" / "UTEC_Logo.png"  # opcional

# Árbol de ejemplo (nodos 1..N). Con raíz 1 el algoritmo baja 1 -> 2 -> 4.
N = 13
ARISTAS = [(1, 2), (1, 3), (2, 4), (2, 5), (4, 6), (4, 7), (4, 8),
           (5, 9), (6, 10), (7, 11), (8, 12), (8, 13)]
RAIZ = 1
NODOS_A_EXPLICAR = [1, 4]  # uno que NO es centroide y uno que sí

# Motivación (juego del nodo escondido) y casos de borde.
ESCONDIDO = 9          # nodo escondido en el juego
ARISTAS_DOS_CENTROIDES = [(1, 2), (2, 3), (2, 4), (2, 5), (5, 6), (5, 7), (7, 8)]
N_CAMINO = 11
TAMANOS_MEDICION = [10, 100, 1000]  # n de los árboles para medir pasos

FUENTE = "Helvetica Neue" if sys.platform == "darwin" else ""

FONDO = "#0F1117"
TEXTO = "#ECEFF4"
TEXTO_SUAVE = "#9AA3B2"
NODO = "#2B3A55"
NODO_BORDE = "#D8DEE9"
ARISTA = "#7B8494"
ACENTO = "#FFD166"   # amarillo: lo que se está procesando
OK = "#06D6A0"       # verde: condición cumplida / centroide
MAL = "#EF476F"      # rojo: condición incumplida
LISTO = "#3A86FF"    # azul: nodo con sz ya calculado
ARRIBA = "#9B5DE5"   # morado: componente que contiene al padre
PESADO = "#FF9F1C"   # naranja: subárbol del hijo más pesado
COLORES_COMPONENTES = ["#3A86FF", "#FF9F1C", "#9B5DE5", "#F15BB5", "#00BBF9", "#C9ADA7"]
COLORES_NIVELES = [OK, LISTO, PESADO, ARRIBA, "#F15BB5"]

config.background_color = FONDO


# =============================================================================
# Algoritmo (lo que impulsa la animación)
# =============================================================================
def construir_adyacencia(n, aristas):
    if n > 0 and len(aristas) != n - 1:
        raise ValueError(f"un árbol de {n} nodos tiene {n - 1} aristas, no {len(aristas)}")
    ady = [[] for _ in range(n + 1)]
    for u, v in aristas:
        if not (1 <= u <= n and 1 <= v <= n) or u == v:
            raise ValueError(f"arista inválida {u}-{v}")
        ady[u].append(v)
        ady[v].append(u)
    for lista in ady:
        lista.sort()
    return ady


def componentes_al_quitar(n, ady, v, dentro=None, contador=None):
    """Componentes conexas que quedan al quitar v (BFS desde cada vecino). O(n).

    `dentro` limita la búsqueda a un conjunto de nodos (un subárbol).
    `contador` (dict) acumula cuántos vecinos se revisan, para medir el trabajo.
    """
    visto = [False] * (n + 1)
    if dentro is not None:
        for u in range(1, n + 1):
            visto[u] = u not in dentro
    visto[v] = True
    comps = []
    for inicio in ady[v]:
        if visto[inicio]:
            continue
        comp = [inicio]
        visto[inicio] = True
        i = 0
        while i < len(comp):
            for w in ady[comp[i]]:
                if contador is not None:
                    contador["pasos"] += 1
                if not visto[w]:
                    visto[w] = True
                    comp.append(w)
            i += 1
        comps.append(sorted(comp))
    return comps


def encontrar_centroides(n, aristas, raiz=1, explicar=(), contador=None):
    """Centroide(s) en O(n). Devuelve un dict con el resultado y la traza de eventos.

    `contador` (dict) acumula los pasos del algoritmo: vecinos revisados en el
    DFS e hijos revisados en la bajada.
    """
    ady = construir_adyacencia(n, aristas)
    eventos = []
    datos = {"n": n, "raiz": raiz, "aristas": list(aristas), "eventos": eventos}
    if n == 0:
        datos.update(hijos=[[]], sz=[0], centroides=[], explicaciones=[], n_medios="0")
        eventos.append({"tipo": "fin", "centroides": []})
        return datos

    padre = [0] * (n + 1)
    sz = [0] * (n + 1)
    pos = [-1] * (n + 1)
    orden = []
    hijos = [[] for _ in range(n + 1)]

    # ---- Fase 1: DFS iterativo con pila explícita (no desborda en caminos largos)
    eventos.append({"tipo": "fase", "fase": 1, "raiz": raiz})
    pila = []  # elementos [nodo, índice del siguiente vecino por revisar]

    def entrar(v, p):
        padre[v] = p
        pos[v] = len(orden)
        orden.append(v)
        pila.append([v, 0])
        eventos.append({"tipo": "entrar", "v": v, "padre": p,
                        "pila": [x for x, _ in pila]})

    entrar(raiz, 0)
    while pila:
        v, i = pila[-1]
        if i < len(ady[v]):
            if contador is not None:
                contador["pasos"] += 1  # se revisa un vecino
            pila[-1][1] += 1
            w = ady[v][i]
            if w == padre[v]:
                continue
            hijos[v].append(w)
            entrar(w, v)
        else:
            sz[v] = 1 + sum(sz[c] for c in hijos[v])
            pila.pop()
            eventos.append({"tipo": "tamano", "v": v, "sz": sz[v], "hijos": list(hijos[v]),
                            "sz_hijos": [sz[c] for c in hijos[v]],
                            "pila": [x for x, _ in pila]})

    if len(orden) != n:
        raise ValueError("el grafo no es conexo: no es un árbol")

    def subarbol(c):  # el subárbol de c es un bloque contiguo del preorden
        return orden[pos[c]:pos[c] + sz[c]]

    def fuera_del_subarbol(c):
        return orden[:pos[c]] + orden[pos[c] + sz[c]:]

    # ---- Fase 2: bajar al hijo con sz > n/2 mientras exista
    n_medios = f"{n // 2}.5" if n % 2 else f"{n // 2}"
    eventos.append({"tipo": "fase", "fase": 2, "raiz": raiz, "n": n, "n_medios": n_medios})
    v = raiz
    while True:
        if contador is not None:
            contador["pasos"] += len(hijos[v])  # se revisan los hijos de v
        pesado = max(hijos[v], key=lambda c: sz[c], default=0)
        sz_pesado = sz[pesado] if pesado else 0
        arriba = n - sz[v]
        max_comp = max(arriba, sz_pesado)
        bajar = pesado != 0 and 2 * sz_pesado > n
        eventos.append({
            "tipo": "evaluar", "v": v, "arriba": arriba, "arriba_nodos": fuera_del_subarbol(v),
            "hijo_pesado": pesado, "sz_pesado": sz_pesado, "max_comp": max_comp,
            "es_centroide": 2 * max_comp <= n, "bajar": bajar,
            "componentes_hijos": [{"hijo": c, "sz": sz[c], "nodos": subarbol(c)}
                                  for c in hijos[v]],
        })
        if not bajar:
            break
        eventos.append({"tipo": "mover", "de": v, "a": pesado})
        v = pesado

    # Al detenernos: hijos con sz <= n/2 y arriba < n/2, así que v es centroide.
    centroides = [v]
    eventos.append({"tipo": "centroide", "v": v, "segundo": False})
    for c in hijos[v]:  # segundo centroide: hijo con sz exactamente n/2
        if 2 * sz[c] == n:
            centroides.append(c)
            eventos.append({"tipo": "centroide", "v": c, "segundo": True})
    centroides.sort()
    eventos.append({"tipo": "fin", "centroides": centroides})

    explicaciones = []
    for x in explicar:
        comps = componentes_al_quitar(n, ady, x)
        tamanos = [len(c) for c in comps]
        maximo = max(tamanos, default=0)
        explicaciones.append({"v": x, "componentes": comps, "tamanos": tamanos,
                              "max": maximo, "es_centroide": 2 * maximo <= n})

    datos.update(hijos=hijos, sz=sz, centroides=centroides,
                 explicaciones=explicaciones, n_medios=n_medios)
    return datos


def centroides_fuerza_bruta(n, aristas, contador=None):
    """Versión ingenua O(n²): quita cada nodo y mide sus componentes con BFS."""
    ady = construir_adyacencia(n, aristas)
    resultado = []
    for v in range(1, n + 1):
        maximo = max((len(c) for c in componentes_al_quitar(n, ady, v, contador=contador)),
                     default=0)
        if 2 * maximo <= n:
            resultado.append(v)
    return resultado


def centroide_de(nodos, aristas):
    """Centroide(s) del subárbol formado por `nodos` (renumera y usa el algoritmo)."""
    nodos = sorted(nodos)
    indice = {v: i + 1 for i, v in enumerate(nodos)}
    sub = [(indice[u], indice[v]) for u, v in aristas if u in indice and v in indice]
    return [nodos[c - 1] for c in encontrar_centroides(len(nodos), sub)["centroides"]]


def jugar_nodo_escondido(n, aristas, escondido):
    """Juego: preguntar siempre por el centroide de los candidatos que quedan.

    Cada respuesta dice "es ese" o hacia qué vecino está; se conserva solo la
    componente de ese lado, que tiene a lo más la mitad de los candidatos.
    """
    ady = construir_adyacencia(n, aristas)
    candidatos = set(range(1, n + 1))
    jugadas = []
    while True:
        c = centroide_de(candidatos, aristas)[0]
        if c == escondido:
            jugadas.append({"pregunta": c, "candidatos": sorted(candidatos),
                            "hacia": None, "quedan": [c]})
            return jugadas
        for comp in componentes_al_quitar(n, ady, c, dentro=candidatos):
            if escondido in comp:
                vecino = next(w for w in ady[c] if w in comp)
                jugadas.append({"pregunta": c, "candidatos": sorted(candidatos),
                                "hacia": vecino, "quedan": comp})
                candidatos = set(comp)
                break


def descomposicion_centroides(n, aristas):
    """Nivel de cada nodo en la descomposición en centroides (0 = centroide global)."""
    ady = construir_adyacencia(n, aristas)
    nivel = {}
    pendientes = [(set(range(1, n + 1)), 0)]
    while pendientes:
        nodos, d = pendientes.pop()
        c = centroide_de(nodos, aristas)[0]
        nivel[c] = d
        for comp in componentes_al_quitar(n, ady, c, dentro=nodos):
            pendientes.append((set(comp), d + 1))
    return nivel


def arbol_aleatorio(n, semilla):
    """Árbol aleatorio reproducible: cada nodo i se cuelga de un nodo anterior."""
    import random
    rng = random.Random(semilla)
    return [(i, rng.randint(1, i - 1)) for i in range(2, n + 1)]


def camino(n):
    return [(i, i + 1) for i in range(1, n)]


# =============================================================================
# Dibujo del árbol
# =============================================================================
class ArbolVisual(VGroup):
    def __init__(self, datos, centro=(0, 0, 0), ancho=7.0, alto=4.6, radio=0.3,
                 posiciones=None):
        super().__init__()
        self.radio = radio
        self.posiciones = posiciones or self._calcular_posiciones(
            datos["hijos"], datos["raiz"], ancho, alto, np.array(centro, dtype=float))

        self.aristas = {}
        for u, v in datos["aristas"]:
            self.aristas[self._clave(u, v)] = Line(
                self.posiciones[u], self.posiciones[v], buff=radio,
                color=ARISTA, stroke_width=4)

        self.circulos, self.etiquetas, self.nodos = {}, {}, {}
        for v, p in self.posiciones.items():
            circulo = Circle(radius=radio, color=NODO_BORDE, stroke_width=3)
            circulo.set_fill(NODO, opacity=1).move_to(p)
            etiqueta = Text(str(v), font_size=24, color=TEXTO, font=FUENTE).move_to(p)
            if etiqueta.width > radio * 1.6:
                etiqueta.scale_to_fit_width(radio * 1.6)
            self.circulos[v], self.etiquetas[v] = circulo, etiqueta
            self.nodos[v] = VGroup(circulo, etiqueta)

        self.add(*self.aristas.values(), *self.nodos.values())

    @staticmethod
    def _calcular_posiciones(hijos, raiz, ancho, alto, centro):
        """Hojas en columnas consecutivas; cada padre centrado sobre sus hijos."""
        if raiz < 1:
            return {}
        x, prof = {}, {}
        siguiente = [0]

        def asignar(v, d):
            prof[v] = d
            if not hijos[v]:
                x[v] = siguiente[0]
                siguiente[0] += 1
                return
            for c in hijos[v]:
                asignar(c, d + 1)
            x[v] = (x[hijos[v][0]] + x[hijos[v][-1]]) / 2

        asignar(raiz, 0)
        max_x, max_d = max(x.values()), max(prof.values())
        dx = min(ancho / max_x, 1.6) if max_x > 0 else 0
        dy = min(alto / max_d, 1.4) if max_d > 0 else 0
        desplazamiento = np.array([max_x * dx / 2, -max_d * dy / 2, 0])
        return {v: centro + np.array([x[v] * dx, -prof[v] * dy, 0]) - desplazamiento
                for v in x}

    @staticmethod
    def _clave(u, v):
        return (min(u, v), max(u, v))

    def pos(self, v):
        return self.posiciones[v]

    def arista(self, u, v):
        return self.aristas[self._clave(u, v)]

    def incidentes(self, v):
        return [l for (a, b), l in self.aristas.items() if v in (a, b)]

    def aristas_dentro(self, nodos):
        s = set(nodos)
        return [l for (a, b), l in self.aristas.items() if a in s and b in s]

    def anim_restaurar(self):
        anims = [c.animate.set_fill(NODO, 1).set_stroke(NODO_BORDE, 3, opacity=1)
                 for c in self.circulos.values()]
        anims += [e.animate.set_opacity(1) for e in self.etiquetas.values()]
        anims += [a.animate.set_stroke(ARISTA, 4, opacity=1) for a in self.aristas.values()]
        return anims


# =============================================================================
# Utilidades de texto
# =============================================================================
CENTRO_ARBOL = np.array([-2.75, -0.15, 0])
ANCHO_ARBOL, ALTO_ARBOL = 7.0, 4.5
ESQUINA_PANEL = np.array([2.35, 2.55, 0])
ANCHO_PANEL = 4.5
Y_SUBTITULO = -3.35
ANCHO_SUBTITULO = 13.0


def T(texto, tam=28, color=TEXTO, **kw):
    kw.setdefault("font", FUENTE)
    return Text(texto, font_size=tam, color=color, **kw)


def ajustar_ancho(mob, maximo):
    if mob.width > maximo:
        mob.scale_to_fit_width(maximo)
    return mob


def reemplazar(viejo, nuevo, desplazamiento=0.12 * UP):
    """Primero sale el texto viejo y luego entra el nuevo, para que no se encimen."""
    anims = []
    if viejo is not None:
        anims.append(FadeOut(viejo, shift=desplazamiento))
    if nuevo is not None:
        anims.append(FadeIn(nuevo, shift=desplazamiento))
    if len(anims) == 2:
        return [AnimationGroup(*anims, lag_ratio=0.45)]
    return anims


def fila_color(color, texto, tam=26):
    cuadro = Square(side_length=0.26).set_fill(color, 1).set_stroke(width=0)
    return VGroup(cuadro, T(texto, tam)).arrange(RIGHT, buff=0.18)


def fila_pila(pila):
    etiqueta = T("pila:", 26, TEXTO_SUAVE)
    if not pila:
        return VGroup(etiqueta, T("vacía", 24, TEXTO_SUAVE)).arrange(RIGHT, buff=0.2)
    cajas = VGroup()
    for i, v in enumerate(pila):
        tope = i == len(pila) - 1
        caja = Square(side_length=0.46, stroke_width=3 if tope else 2,
                      color=ACENTO if tope else TEXTO_SUAVE)
        cajas.add(VGroup(caja, T(str(v), 22).move_to(caja)))
    cajas.arrange(RIGHT, buff=0.06)
    return VGroup(etiqueta, cajas).arrange(RIGHT, buff=0.2)


class Narrador:
    """Título de sección (arriba a la izquierda) y subtítulo (abajo)."""

    def __init__(self):
        self._titulo = None
        self._subtitulo = None

    def anim_titulo(self, texto):
        nuevo = ajustar_ancho(T(texto, 30, TEXTO_SUAVE), 9.5).to_corner(UL, buff=0.45)
        anims = reemplazar(self._titulo, nuevo, 0.1 * DOWN)
        self._titulo = nuevo
        return anims

    def anim_decir(self, texto, t2c=None):
        nuevo = T(texto, 30, t2c=t2c or {})
        ajustar_ancho(nuevo, ANCHO_SUBTITULO).move_to([0, Y_SUBTITULO, 0])
        anims = reemplazar(self._subtitulo, nuevo)
        self._subtitulo = nuevo
        return anims

    def anim_limpiar(self):
        anims = [FadeOut(m) for m in (self._titulo, self._subtitulo) if m is not None]
        self._titulo = self._subtitulo = None
        return anims


class Panel:
    """Columna derecha: una cabecera fija y un cuerpo que se reemplaza."""

    def __init__(self):
        self.cabecera = VGroup()
        self.cuerpo = VGroup()

    @staticmethod
    def _colocar(lineas, arriba_izquierda):
        grupo = VGroup(*[ajustar_ancho(m, ANCHO_PANEL) for m in lineas])
        if len(grupo):
            grupo.arrange(DOWN, aligned_edge=LEFT, buff=0.24)
            grupo.move_to(arriba_izquierda, aligned_edge=UL)
        return grupo

    def _inicio_cuerpo(self):
        if len(self.cabecera):
            return np.array([ESQUINA_PANEL[0], self.cabecera.get_bottom()[1] - 0.45, 0])
        return ESQUINA_PANEL

    @staticmethod
    def _cambiar(viejo, nuevo):
        return reemplazar(viejo if len(viejo) else None, nuevo if len(nuevo) else None,
                          0.1 * LEFT)

    def anim_cabecera(self, lineas):
        nueva = self._colocar(lineas, ESQUINA_PANEL)
        anims = self._cambiar(self.cabecera, nueva)
        self.cabecera = nueva
        return anims

    def anim_cuerpo(self, lineas):
        nuevo = self._colocar(lineas, self._inicio_cuerpo())
        anims = self._cambiar(self.cuerpo, nuevo)
        self.cuerpo = nuevo
        return anims

    def anim_agregar(self, lineas):
        if len(self.cuerpo):
            inicio = np.array([ESQUINA_PANEL[0], self.cuerpo.get_bottom()[1] - 0.24, 0])
        else:
            inicio = self._inicio_cuerpo()
        extra = self._colocar(lineas, inicio)
        self.cuerpo.add(*extra)
        return [FadeIn(extra, shift=0.1 * LEFT)]

    def anim_limpiar(self):
        anims = [FadeOut(g) for g in (self.cabecera, self.cuerpo) if len(g)]
        self.cabecera, self.cuerpo = VGroup(), VGroup()
        return anims


# =============================================================================
# Escenas
# =============================================================================
class EscenaCentroide:
    """Secciones del video. No es una escena: Avance la combina con Scene."""

    def preparar(self):
        self.datos = encontrar_centroides(N, ARISTAS, RAIZ, NODOS_A_EXPLICAR)
        self.n = self.datos["n"]
        self.mitad = self.datos["n_medios"]
        self.sz = self.datos["sz"]
        self.narrador = Narrador()
        self.panel = Panel()
        self.arbol = None

    def crear_arbol(self):
        self.arbol = ArbolVisual(self.datos, CENTRO_ARBOL, ANCHO_ARBOL, ALTO_ARBOL)
        self.play(
            LaggedStart(*[Create(a) for a in self.arbol.aristas.values()], lag_ratio=0.08),
            LaggedStart(*[GrowFromCenter(m) for m in self.arbol.nodos.values()], lag_ratio=0.08),
            run_time=2,
        )

    # ---------------------------------------------------------------- título
    def logo(self):
        """Logo sobre una tarjeta blanca (el PNG tiene fondo blanco)."""
        if not LOGO.exists():
            return None
        imagen = ImageMobject(str(LOGO)).set_height(0.7)
        tarjeta = RoundedRectangle(corner_radius=0.1, width=imagen.width + 0.4,
                                   height=imagen.height + 0.26)
        tarjeta.set_fill(WHITE, 1).set_stroke(width=0)
        return Group(tarjeta, imagen.move_to(tarjeta))

    def seccion_titulo(self):
        logo = self.logo()
        titulo = T(TITULO, 66, weight=BOLD)
        linea = Line(LEFT * 3.4, RIGHT * 3.4, color=ACENTO, stroke_width=3)
        subtitulo = T(SUBTITULO, 28, TEXTO_SUAVE)
        ciclo = T(CICLO, 24, TEXTO_SUAVE)
        nombres = VGroup(*[T(a, 32) for a in AUTORES]).arrange(DOWN, buff=0.16)
        profesor = T(f"Profesor: {PROFESOR}", 24, TEXTO_SUAVE)
        creditos = VGroup(nombres, profesor).arrange(DOWN, buff=0.22)
        bloque = Group(*([logo] if logo else []), titulo, linea, subtitulo, ciclo, creditos)
        bloque.arrange(DOWN, buff=0.32)
        creditos.shift(0.25 * DOWN)
        if logo:
            logo.shift(0.2 * UP)
        bloque.move_to(ORIGIN)

        if logo:
            self.play(FadeIn(logo, shift=0.2 * DOWN), run_time=0.8)
        self.play(Write(titulo), run_time=1.5)
        self.play(GrowFromCenter(linea), FadeIn(subtitulo, shift=0.2 * UP),
                  FadeIn(ciclo, shift=0.2 * UP), run_time=1)
        self.play(FadeIn(creditos, shift=0.15 * UP), run_time=1)
        self.wait(2)
        self.play(FadeOut(bloque), run_time=0.8)

    # ------------------------------------------------------------ definición
    def seccion_definicion(self):
        self.play(*self.narrador.anim_titulo("2 · ¿Qué es un centroide?"))
        self.crear_arbol()
        self.play(*self.panel.anim_cabecera([
            T(f"n = {self.n}", 30),
            T(f"n/2 = {self.mitad}", 30, ACENTO),
        ]))
        self.play(*self.narrador.anim_decir(
            "Un centroide es un nodo que, al quitarlo, deja componentes de ≤ n/2 nodos",
            {"centroide": ACENTO, "n/2": ACENTO}))
        self.wait(2)

        for explicacion in self.datos["explicaciones"]:
            self.mostrar_quitar(explicacion, espera=1.8)

        self.play(*self.narrador.anim_decir(
            "Teorema: todo árbol tiene 1 o 2 centroides; si son 2, son vecinos y n es par",
            {"Teorema:": ACENTO}))
        self.wait(2.5)
        self.play(
            *self.panel.anim_cuerpo([
                T("¿Para qué sirve?", 28, weight=BOLD),
                T("• buscar con ~log₂ n preguntas", 24),
                T("• mínima suma de distancias", 24),
                T("• descomposición en centroides", 24),
                T("  (divide y vencerás en árboles)", 24, TEXTO_SUAVE),
            ]),
            *self.narrador.anim_decir(
                "Sirve para partir un árbol en pedazos equilibrados, de a lo más la mitad",
                {"equilibrados": ACENTO}),
        )
        self.wait(3.7)
        self.play(*self.panel.anim_cuerpo([]), *self.narrador.anim_decir(
            "¿Cómo encontrarlo sin probar los n nodos uno por uno, en O(n²)?",
            {"O(n²)": MAL}))
        self.wait(1.5)

    def mostrar_quitar(self, exp, arbol=None, mitad=None, espera=2.5):
        a = arbol or self.arbol
        mitad = mitad or self.mitad
        v, ok, maximo = exp["v"], exp["es_centroide"], exp["max"]

        self.play(*self.narrador.anim_decir(f"Quitemos el nodo {v}"),
                  Indicate(a.nodos[v], color=ACENTO, scale_factor=1.3), run_time=0.9)
        self.play(a.nodos[v].animate.set_opacity(0.12),
                  *[e.animate.set_stroke(opacity=0.12) for e in a.incidentes(v)], run_time=0.7)

        anims, filas = [], []
        for i, (comp, tam) in enumerate(zip(exp["componentes"], exp["tamanos"])):
            color = COLORES_COMPONENTES[i % len(COLORES_COMPONENTES)]
            anims += [a.circulos[u].animate.set_fill(color, 1) for u in comp]
            anims += [e.animate.set_stroke(color) for e in a.aristas_dentro(comp)]
            filas.append(fila_color(color, f"componente de {tam} nodo{'s' if tam != 1 else ''}"))
        self.play(*anims, *self.panel.anim_cuerpo(filas), run_time=1.0)

        color = OK if ok else MAL
        resultado = T(f"máx = {maximo} {'≤' if ok else '>'} {mitad}", 30, color)
        veredicto = T(f"{v} {'SÍ' if ok else 'NO'} es centroide", 30, color, weight=BOLD)
        if ok:
            frase = f"Ninguna componente pasa de {mitad}: el nodo {v} es un centroide"
        else:
            frase = f"Queda una componente de {maximo} nodos, más de la mitad: {v} no sirve"
        self.play(*self.panel.anim_agregar([resultado, veredicto]),
                  *self.narrador.anim_decir(frase, {"centroide": OK}), run_time=0.8)
        self.wait(espera)
        self.play(*a.anim_restaurar(), *self.panel.anim_cuerpo([]), run_time=0.8)

    # ---------------------------------------------------------- demostración
    def seccion_demo(self):
        if self.arbol is None:
            self.crear_arbol()
        a, datos = self.arbol, self.datos
        raiz = datos["raiz"]

        self.play(
            *self.narrador.anim_titulo("3 · Algoritmo — Fase 1: tamaños de subárbol (DFS)"),
            *self.narrador.anim_decir(
                f"Enraizamos en {raiz}; en postorden, sz[v] = 1 + la suma de sz de sus hijos",
                {"sz[v]": ACENTO}),
            *self.panel.anim_cabecera([
                T("DFS iterativo (pila explícita)", 28, weight=BOLD),
                T("sz[v] = 1 + Σ sz[hijo]", 28, ACENTO),
            ]),
            *self.panel.anim_cuerpo([fila_pila([])]),
        )
        cursor = Circle(radius=a.radio + 0.13, color=ACENTO, stroke_width=6)
        cursor.move_to(a.pos(raiz))
        self.play(Create(cursor), run_time=0.5)
        self.wait(0.6)

        formula = T(" ", 28)
        etiquetas_sz = []
        for ev in datos["eventos"]:
            tipo = ev["tipo"]

            if tipo == "entrar":
                v = ev["v"]
                self.play(cursor.animate.move_to(a.pos(v)),
                          a.circulos[v].animate.set_stroke(ACENTO, 4),
                          *self.panel.anim_cuerpo([formula.copy(), fila_pila(ev["pila"])]),
                          run_time=0.25)

            elif tipo == "tamano":
                v, sz = ev["v"], ev["sz"]
                if ev["sz_hijos"]:
                    texto = f"sz[{v}] = 1 + " + " + ".join(map(str, ev["sz_hijos"])) + f" = {sz}"
                else:
                    texto = f"sz[{v}] = 1   (hoja)"
                formula = T(texto, 28)
                etiqueta = T(str(sz), 24, ACENTO)
                etiqueta.next_to(a.circulos[v], RIGHT, buff=0.17).shift(0.17 * UP)
                etiquetas_sz.append(etiqueta)
                self.play(cursor.animate.move_to(a.pos(v)),
                          a.circulos[v].animate.set_fill(LISTO, 1).set_stroke(NODO_BORDE, 3),
                          FadeIn(etiqueta, scale=0.5),
                          *self.panel.anim_cuerpo([formula, fila_pila(ev["pila"])]),
                          run_time=0.4)

            elif tipo == "fase" and ev["fase"] == 2:
                self.wait(0.6)
                self.play(
                    *self.narrador.anim_titulo("3 · Algoritmo — Fase 2: bajar hacia el hijo pesado"),
                    *self.narrador.anim_decir(
                        f"Desde la raíz, bajamos mientras algún hijo tenga sz > n/2 = {ev['n_medios']}",
                        {"sz > n/2": ACENTO}),
                    *self.panel.anim_cabecera([
                        T(f"n = {ev['n']}", 30),
                        T(f"n/2 = {ev['n_medios']}", 30, ACENTO),
                    ]),
                    *self.panel.anim_cuerpo([]),
                    cursor.animate.move_to(a.pos(ev["raiz"])),
                )
                self.wait(1.2)

            elif tipo == "evaluar":
                self.mostrar_evaluacion(ev, cursor)

            elif tipo == "mover":
                camino = a.arista(ev["de"], ev["a"]).copy().set_stroke(ACENTO, 8)
                self.play(ShowPassingFlash(camino, time_width=0.7),
                          cursor.animate.move_to(a.pos(ev["a"])), run_time=0.8)

            elif tipo == "centroide":
                v = ev["v"]
                self.play(a.circulos[v].animate.set_fill(OK, 1).set_stroke(WHITE, 4),
                          Flash(a.circulos[v], color=OK, flash_radius=0.6, line_length=0.25),
                          run_time=1.0)

            elif tipo == "fin":
                centroides = ", ".join(map(str, ev["centroides"]))
                self.play(
                    *self.panel.anim_agregar([T(f"centroide = {centroides}", 32, OK, weight=BOLD)]),
                    *self.narrador.anim_decir("Un DFS + una sola bajada: O(n) en tiempo y memoria",
                                              {"O(n)": OK}),
                )
                self.wait(3)

        self.play(FadeOut(a), FadeOut(cursor), *[FadeOut(e) for e in etiquetas_sz],
                  *self.panel.anim_limpiar(), *self.narrador.anim_limpiar(), run_time=1)
        self.arbol = None

    def mostrar_evaluacion(self, ev, cursor):
        a = self.arbol
        v, pesado = ev["v"], ev["hijo_pesado"]
        arriba = set(ev["arriba_nodos"])
        nodos_pesado = set()
        for comp in ev["componentes_hijos"]:
            if comp["hijo"] == pesado:
                nodos_pesado = set(comp["nodos"])

        anims = [cursor.animate.move_to(a.pos(v))]
        for u, circulo in a.circulos.items():
            if u == v:
                color = NODO
            elif u in arriba:
                color = ARRIBA
            elif u in nodos_pesado:
                color = PESADO
            else:
                color = LISTO
            anims.append(circulo.animate.set_fill(color, 1))

        ok, bajar = ev["es_centroide"], ev["bajar"]
        color = OK if ok else MAL
        filas = [
            T(f"v = {v}", 30, weight=BOLD),
            fila_color(ARRIBA, f"arriba: {self.n} − {self.sz[v]} = {ev['arriba']}"),
            fila_color(PESADO, f"hijo pesado: {pesado} (sz = {ev['sz_pesado']})")
            if pesado else T("v no tiene hijos", 26),
            T(f"máx = {ev['max_comp']} {'≤' if ok else '>'} {self.mitad}", 30, color),
            T(f"→ bajar a {pesado}" if bajar else f"→ {v} es centroide", 30, color, weight=BOLD),
        ]
        if bajar:
            frase = (f"El hijo {pesado} tiene {ev['sz_pesado']} > {self.mitad} nodos: "
                     f"el centroide está de ese lado")
        else:
            frase = f"Nada pasa de {self.mitad}: {v} es centroide"
        self.play(*anims, *self.panel.anim_cuerpo(filas),
                  *self.narrador.anim_decir(frase, {"centroide": OK}), run_time=1.0)
        self.wait(1.6)

    # -------------------------------------------------------- cierre avance
    # ------------------------------------------------------------ motivación
    def atenuar(self, nodos, arbol=None):
        """Animaciones que apagan nodos descartados y las aristas que los tocan."""
        a = arbol or self.arbol
        nodos = set(nodos)
        anims = []
        for u in nodos:
            anims.append(a.circulos[u].animate.set_fill(opacity=0.12).set_stroke(opacity=0.2))
            anims.append(a.etiquetas[u].animate.set_opacity(0.2))
        for (x, y), linea in a.aristas.items():
            if x in nodos or y in nodos:
                anims.append(linea.animate.set_stroke(opacity=0.12))
        return anims

    def seccion_motivacion(self):
        jugadas = jugar_nodo_escondido(N, ARISTAS, ESCONDIDO)

        self.play(*self.narrador.anim_titulo("1 · Motivación: el nodo escondido"))
        self.crear_arbol()
        a = self.arbol
        self.play(*self.narrador.anim_decir(
            "Escondí un nodo. Preguntas por uno y te digo «es ese» o hacia dónde está",
            {"«es ese»": OK}))
        self.wait(2.5)

        # Estrategia ingenua: preguntar por hojas descarta un nodo a la vez.
        self.play(*self.narrador.anim_decir(
            f"Con hojas descartas uno a la vez: hasta n − 1 = {N - 1} preguntas",
            {f"n − 1 = {N - 1}": MAL}))
        self.wait(2.3)
        self.play(*self.narrador.anim_decir(
            "Mejor: pregunta siempre por el nodo que parte lo que queda en mitades",
            {"en mitades": ACENTO}))
        self.wait(1.2)

        # Estrategia buena: preguntar siempre por el centroide de los candidatos.
        cursor = Circle(radius=a.radio + 0.13, color=ACENTO, stroke_width=6)
        historial = [str(N)]
        for k, j in enumerate(jugadas, 1):
            c = j["pregunta"]
            filas = [T(f"pregunta {k}: ¿es el {c}?", 30, weight=BOLD)]
            if j["hacia"] is None:
                filas.append(T("«¡Sí, es ese!»", 28, OK))
            else:
                filas.append(T(f"«No, está hacia el {j['hacia']}»", 28, ACENTO))
                historial.append(str(len(j["quedan"])))
            filas.append(T("candidatos: " + " → ".join(historial), 28))
            if k == 1:
                mover = Create(cursor.move_to(a.pos(c)))
            else:
                mover = cursor.animate.move_to(a.pos(c))
            self.play(mover, *self.panel.anim_cuerpo(filas), run_time=0.8)

            if j["hacia"] is None:
                self.play(a.circulos[c].animate.set_fill(OK, 1), FadeOut(cursor),
                          Flash(a.circulos[c], color=OK, flash_radius=0.6, line_length=0.25),
                          run_time=1)
                break
            flecha = Arrow(a.pos(c), a.pos(j["hacia"]), buff=0.32, color=ACENTO, stroke_width=6)
            descartados = set(j["candidatos"]) - set(j["quedan"])
            self.play(GrowArrow(flecha), run_time=0.5)
            self.play(*self.atenuar(descartados), FadeOut(flecha), run_time=0.8)
            self.wait(0.6)

        self.play(*self.narrador.anim_decir(
            f"Lo encontramos en {len(jugadas)} preguntas: cada respuesta deja a lo más la mitad",
            {f"{len(jugadas)} preguntas": OK}))
        self.wait(2.2)
        self.play(*self.narrador.anim_decir(
            "Ese nodo que siempre parte el árbol a la mitad se llama centroide",
            {"centroide": ACENTO}))
        self.wait(2.5)
        self.play(FadeOut(a), *self.panel.anim_limpiar(), *self.narrador.anim_limpiar(),
                  run_time=1)
        self.arbol = None

    # -------------------------------------------------------- casos de borde
    def seccion_bordes(self):
        self.play(*self.narrador.anim_titulo("4 · Casos de borde"))

        # Caso 1: n par con dos centroides.
        d = encontrar_centroides(len(ARISTAS_DOS_CENTROIDES) + 1, ARISTAS_DOS_CENTROIDES,
                                 1, explicar=[2, 5])
        a = ArbolVisual(d, CENTRO_ARBOL, 5.5, 3.6)
        self.play(
            LaggedStart(*[Create(l) for l in a.aristas.values()], lag_ratio=0.08),
            LaggedStart(*[GrowFromCenter(m) for m in a.nodos.values()], lag_ratio=0.08),
            *self.panel.anim_cabecera([T(f"n = {d['n']}", 30),
                                       T(f"n/2 = {d['n_medios']}", 30, ACENTO)]),
            *self.narrador.anim_decir("Caso 1: con n par puede haber dos centroides",
                                      {"dos centroides": ACENTO}),
            run_time=1.8)
        self.wait(0.8)

        # Las dos mitades que deja la arista entre los centroides.
        primero = next(e["v"] for e in d["eventos"] if e["tipo"] == "centroide" and not e["segundo"])
        segundo = next(e["v"] for e in d["eventos"] if e["tipo"] == "centroide" and e["segundo"])
        quitar = {e["v"]: e for e in d["explicaciones"]}
        mitad_b = next(c for c in quitar[primero]["componentes"] if segundo in c)
        mitad_a = [v for v in range(1, d["n"] + 1) if v not in mitad_b]
        self.play(
            *[a.circulos[v].animate.set_fill(LISTO, 1) for v in mitad_a],
            *[a.circulos[v].animate.set_fill(PESADO, 1) for v in mitad_b],
            *self.panel.anim_cuerpo([
                T(f"al quitar {v}: máx = {quitar[v]['max']} ≤ {d['n_medios']}", 26, OK)
                for v in (primero, segundo)
            ]),
            *self.narrador.anim_decir(
                f"La arista {primero}–{segundo} parte el árbol en dos mitades de {d['n_medios']}",
                {f"{primero}–{segundo}": ACENTO}),
            run_time=1)
        self.wait(2)
        self.play(
            *[a.circulos[c].animate.set_fill(OK, 1) for c in d["centroides"]],
            a.arista(primero, segundo).animate.set_stroke(ACENTO, 7),
            *self.panel.anim_agregar([
                T(f"centroides = {', '.join(map(str, d['centroides']))}", 30, OK, weight=BOLD),
                T(f"el algoritmo para en {primero}", 26),
                T(f"y su hijo {segundo}: sz = {d['sz'][segundo]} = n/2", 26),
            ]),
            *self.narrador.anim_decir("Ambos son centroides, y son vecinos", {"Ambos": OK}),
            run_time=1)
        self.wait(3)
        self.play(FadeOut(a), *self.panel.anim_limpiar(), run_time=0.8)

        # Caso 2: un camino, el peor caso de profundidad para el DFS.
        n = N_CAMINO
        d = encontrar_centroides(n, camino(n))
        xs = np.linspace(-5.5, 5.5, n)
        pos = {i + 1: np.array([xs[i], 1.1, 0]) for i in range(n)}
        a = ArbolVisual(d, posiciones=pos)
        self.play(
            LaggedStart(*[Create(l) for l in a.aristas.values()], lag_ratio=0.05),
            LaggedStart(*[GrowFromCenter(m) for m in a.nodos.values()], lag_ratio=0.05),
            *self.narrador.anim_decir("Caso 2: un camino, el peor caso de profundidad para el DFS",
                                      {"peor caso": MAL}),
            run_time=1.5)
        ancla = np.array([-5.8, -0.3, 0])
        pila_mob = fila_pila([]).move_to(ancla, aligned_edge=LEFT)
        cursor = Circle(radius=a.radio + 0.13, color=ACENTO, stroke_width=6).move_to(pos[1])
        self.play(Create(cursor), FadeIn(pila_mob), run_time=0.5)
        profundidad = 0
        for ev in d["eventos"]:
            if ev["tipo"] != "entrar":
                continue
            nueva = fila_pila(ev["pila"]).move_to(ancla, aligned_edge=LEFT)
            self.play(cursor.animate.move_to(pos[ev["v"]]),
                      a.circulos[ev["v"]].animate.set_stroke(ACENTO, 4),
                      FadeOut(pila_mob), FadeIn(nueva), run_time=0.22)
            pila_mob = nueva
            profundidad = max(profundidad, len(ev["pila"]))
        info = T(f"la pila llega a {profundidad} nodos = n", 30, ACENTO).move_to((0, -1.4, 0))
        self.play(FadeIn(info), *self.narrador.anim_decir(
            "Con recursión serían n llamadas anidadas y Python se detiene en ~1000: usamos una pila",
            {"una pila": ACENTO}))
        self.wait(3.7)
        c = d["centroides"][0]
        self.play(a.circulos[c].animate.set_fill(OK, 1), FadeOut(cursor),
                  Flash(a.circulos[c], color=OK, flash_radius=0.6, line_length=0.25),
                  *self.narrador.anim_decir(f"El centroide de un camino es el nodo del medio: {c}",
                                            {"centroide": OK}), run_time=1)
        self.wait(1.5)
        self.play(FadeOut(a), FadeOut(pila_mob), FadeOut(info), *self.narrador.anim_limpiar(),
                  run_time=0.8)

    # ----------------------------------------------------------- complejidad
    def seccion_complejidad(self):
        # Pasos medidos al ejecutar las dos versiones sobre árboles aleatorios.
        medidas = []
        for n in TAMANOS_MEDICION:
            aristas = arbol_aleatorio(n, 2026)
            lineal, ingenuo = {"pasos": 0}, {"pasos": 0}
            r1 = encontrar_centroides(n, aristas, contador=lineal)["centroides"]
            r2 = centroides_fuerza_bruta(n, aristas, contador=ingenuo)
            if r1 != r2:
                raise RuntimeError(f"resultados distintos para n = {n}: {r1} vs {r2}")
            medidas.append((n, lineal["pasos"], ingenuo["pasos"]))

        self.play(*self.narrador.anim_titulo("5 · Complejidad"))
        razones = [
            ("Fase 1 · DFS: cada nodo entra y sale de la pila una vez; cada arista, 2 veces", "O(n)"),
            ("Fase 2 · bajada: solo se miran los hijos de los nodos por donde pasa", "O(n)"),
            ("Memoria: listas de adyacencia, sz, padre y la pila", "O(n)"),
            ("Ingenuo: quitar cada nodo y medir sus componentes con un BFS", "O(n²)"),
        ]
        filas = VGroup()
        for texto, cota in razones:
            color = MAL if "²" in cota else OK
            fila = VGroup(T(texto, 26), T("→ " + cota, 26, color, weight=BOLD))
            fila.arrange(RIGHT, buff=0.25)
            filas.add(fila)
        # Misma escala para todas las líneas, de modo que la más larga quepa.
        factor = min(1.0, 12.8 / max(f.width for f in filas))
        for fila in filas:
            fila.scale(factor)
        filas.arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        filas.move_to(np.array([-6.5, 2.85, 0]), aligned_edge=UL)
        for fila in filas:
            self.play(FadeIn(fila, shift=0.1 * RIGHT), run_time=0.6)
            self.wait(1.5)

        columnas = [-3.6, 0.0, 3.8]

        def fila_tabla(celdas, colores, y, negrita=False):
            extra = {"weight": BOLD} if negrita else {}
            return VGroup(*[T(c, 28, col, **extra).move_to([x, y, 0])
                            for x, c, col in zip(columnas, celdas, colores)])

        def numero(x):
            return f"{x:,}".replace(",", " ")

        cabecera = fila_tabla(["n", "pasos O(n)", "pasos ingenuo O(n²)"], [TEXTO, OK, MAL],
                              -0.15, negrita=True)
        regla = Line([-5.4, -0.5, 0], [5.8, -0.5, 0], color=TEXTO_SUAVE, stroke_width=2)
        cuerpo = VGroup(*[
            fila_tabla([numero(n), numero(p1), numero(p2)], [TEXTO, OK, MAL], -0.85 - 0.55 * i)
            for i, (n, p1, p2) in enumerate(medidas)
        ])
        nota = T("pasos contados al ejecutar ambas versiones en árboles aleatorios · mismo centroide",
                 20, TEXTO_SUAVE).move_to((0, -0.85 - 0.55 * len(medidas), 0))
        x_lineal = round(medidas[-1][1] / medidas[-2][1])
        x_ingenuo = round(medidas[-1][2] / medidas[-2][2])
        self.play(FadeIn(cabecera), Create(regla), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(f, shift=0.1 * UP) for f in cuerpo], lag_ratio=0.4),
                  FadeIn(nota), run_time=1.5)
        self.play(*self.narrador.anim_decir(
            f"Con n ×10, el algoritmo hace ≈ ×{x_lineal} pasos; el ingenuo, ≈ ×{x_ingenuo}",
            {f"≈ ×{x_lineal} pasos": OK, f"el ingenuo, ≈ ×{x_ingenuo}": MAL}))
        self.wait(5)
        self.play(FadeOut(filas), FadeOut(cabecera), FadeOut(regla), FadeOut(cuerpo),
                  FadeOut(nota), *self.narrador.anim_limpiar(), run_time=0.8)

    # ---------------------------------------------------------------- cierre
    def seccion_cierre(self):
        nivel = descomposicion_centroides(N, ARISTAS)
        niveles = max(nivel.values()) + 1
        cota = int(np.floor(np.log2(N))) + 1

        self.play(*self.narrador.anim_titulo("6 · Cierre: descomposición en centroides"))
        self.crear_arbol()
        a = self.arbol
        self.play(*self.narrador.anim_decir(
            "Como en el juego: tomamos el centroide y repetimos en cada pedazo que queda",
            {"repetimos": ACENTO}))
        self.wait(1.5)
        for d in range(niveles):
            nodos = sorted(v for v, l in nivel.items() if l == d)
            color = COLORES_NIVELES[d % len(COLORES_NIVELES)]
            self.play(*[a.circulos[v].animate.set_fill(color, 1) for v in nodos],
                      *self.panel.anim_agregar([
                          fila_color(color, f"nivel {d}: " + ", ".join(map(str, nodos)), 24)]),
                      run_time=0.7)
            self.wait(0.3)
        self.play(*self.narrador.anim_decir(
            f"Solo {niveles} niveles ≤ ⌊log₂ n⌋ + 1 = {cota}: cada pedazo tiene a lo más la mitad",
            {f"{niveles} niveles": OK}))
        self.wait(3)
        self.play(FadeOut(a), *self.panel.anim_limpiar(), *self.narrador.anim_limpiar(),
                  run_time=1)
        self.arbol = None

        # Créditos.
        referencias = VGroup(*[T(r, 22, TEXTO_SUAVE) for r in (
            "C. Jordan (1869). Sur les assemblages de lignes",
            "USACO Guide: Centroid Decomposition",
            "Manim Community · estilo inspirado en 3Blue1Brown",
        )]).arrange(DOWN, buff=0.14)
        creditos = VGroup(
            T(TITULO, 54, weight=BOLD),
            T(", ".join(AUTORES), 32),
            T(f"{SUBTITULO} · {CICLO}", 24, TEXTO_SUAVE),
            T(f"Profesor: {PROFESOR}", 24, TEXTO_SUAVE),
            T("Referencias", 26, ACENTO, weight=BOLD),
            referencias,
            T("¡Gracias!", 36, OK, weight=BOLD),
        ).arrange(DOWN, buff=0.28).move_to(ORIGIN)
        self.play(LaggedStart(*[FadeIn(m, shift=0.15 * UP) for m in creditos], lag_ratio=0.15),
                  run_time=2)
        self.wait(4)
        self.play(FadeOut(creditos), run_time=1)


class Avance(EscenaCentroide, Scene):
    """Video completo: motivación, definición, algoritmo, casos de borde,
    complejidad y cierre."""

    def construct(self):
        self.preparar()
        self.seccion_titulo()
        self.seccion_motivacion()
        self.seccion_definicion()
        self.seccion_demo()
        self.seccion_bordes()
        self.seccion_complejidad()
        self.seccion_cierre()

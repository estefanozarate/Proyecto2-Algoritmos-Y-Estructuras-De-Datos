"""Proyecto 2 · Centroide de un árbol · Avance (≈25 % del video).
    manim -pql avance.py    # vista previa rápida (480p)
    manim -pqh avance.py    # final 1080p60
El archivo tiene una sola escena (Avance), así que Manim la renderiza completa
sin preguntar.
"""

import sys
from pathlib import Path

import numpy as np
from manim import (BOLD, DOWN, LEFT, ORIGIN, RIGHT, UL, UP, WHITE, AnimationGroup,
                   Circle, Create, FadeIn, FadeOut, Flash, Group, GrowFromCenter,
                   ImageMobject, Indicate, LaggedStart, Line, RoundedRectangle, Scene,
                   ShowPassingFlash, Square, Text, VGroup, Write, config)

TITULO = "Centroide de un árbol"
SUBTITULO = "Proyecto 2 · CS2023 Algoritmos y Estructuras de Datos"
CICLO = "UTEC · 2026-2"
AUTORES = ["Estefano Zárate"]
PROFESOR = "Luciano A. Romero Calla"
LOGO = Path(__file__).resolve().parent / "assets" / "UTEC_Logo.png"  # opcional

N = 13
ARISTAS = [(1, 2), (1, 3), (2, 4), (2, 5), (4, 6), (4, 7), (4, 8),
           (5, 9), (6, 10), (7, 11), (8, 12), (8, 13)]
RAIZ = 1
NODOS_A_EXPLICAR = [1, 4]  # uno que NO es centroide y uno que sí

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


def componentes_al_quitar(n, ady, v):
    """Componentes conexas que quedan al quitar v (BFS desde cada vecino). O(n)."""
    visto = [False] * (n + 1)
    visto[v] = True
    comps = []
    for inicio in ady[v]:
        comp = [inicio]
        visto[inicio] = True
        i = 0
        while i < len(comp):
            for w in ady[comp[i]]:
                if not visto[w]:
                    visto[w] = True
                    comp.append(w)
            i += 1
        comps.append(sorted(comp))
    return comps


def encontrar_centroides(n, aristas, raiz=1, explicar=()):
    """Centroide(s) en O(n). Devuelve un dict con el resultado y la traza de eventos."""
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


# =============================================================================
# Dibujo del árbol
# =============================================================================
class ArbolVisual(VGroup):
    def __init__(self, datos, centro=(0, 0, 0), ancho=7.0, alto=4.6, radio=0.3):
        super().__init__()
        self.radio = radio
        self.posiciones = self._calcular_posiciones(
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
        self.wait(2.5)
        self.play(FadeOut(bloque), run_time=0.8)

    # ------------------------------------------------------------ definición
    def seccion_definicion(self):
        self.play(*self.narrador.anim_titulo("1 · ¿Qué es un centroide?"))
        self.crear_arbol()
        self.play(*self.panel.anim_cabecera([
            T(f"n = {self.n}", 30),
            T(f"n/2 = {self.mitad}", 30, ACENTO),
        ]))
        self.play(*self.narrador.anim_decir(
            "Un centroide es un nodo que, al quitarlo, deja componentes de ≤ n/2 nodos",
            {"centroide": ACENTO, "n/2": ACENTO}))
        self.wait(2.5)

        for explicacion in self.datos["explicaciones"]:
            self.mostrar_quitar(explicacion)

        self.play(*self.narrador.anim_decir(
            "Teorema: todo árbol tiene 1 o 2 centroides; si son 2, son vecinos y n es par",
            {"Teorema:": ACENTO}))
        self.wait(3)
        self.play(*self.narrador.anim_decir(
            "¿Cómo encontrarlo sin probar los n nodos uno por uno, en O(n²)?",
            {"O(n²)": MAL}))
        self.wait(2)

    def mostrar_quitar(self, exp):
        a = self.arbol
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
        resultado = T(f"máx = {maximo} {'≤' if ok else '>'} {self.mitad}", 30, color)
        veredicto = T(f"{v} {'SÍ' if ok else 'NO'} es centroide", 30, color, weight=BOLD)
        if ok:
            frase = f"Ninguna componente pasa de {self.mitad}: el nodo {v} es un centroide"
        else:
            frase = f"Queda una componente de {maximo} nodos, más de la mitad: {v} no sirve"
        self.play(*self.panel.anim_agregar([resultado, veredicto]),
                  *self.narrador.anim_decir(frase, {"centroide": OK}), run_time=0.8)
        self.wait(2.5)
        self.play(*a.anim_restaurar(), *self.panel.anim_cuerpo([]), run_time=0.8)

    # ---------------------------------------------------------- demostración
    def seccion_demo(self):
        if self.arbol is None:
            self.crear_arbol()
        a, datos = self.arbol, self.datos
        raiz = datos["raiz"]

        self.play(
            *self.narrador.anim_titulo("2 · Algoritmo — Fase 1: tamaños de subárbol (DFS)"),
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
        self.wait(1)

        formula = T(" ", 28)
        etiquetas_sz = []
        for ev in datos["eventos"]:
            tipo = ev["tipo"]

            if tipo == "entrar":
                v = ev["v"]
                self.play(cursor.animate.move_to(a.pos(v)),
                          a.circulos[v].animate.set_stroke(ACENTO, 4),
                          *self.panel.anim_cuerpo([formula.copy(), fila_pila(ev["pila"])]),
                          run_time=0.3)

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
                          run_time=0.45)

            elif tipo == "fase" and ev["fase"] == 2:
                self.wait(0.8)
                self.play(
                    *self.narrador.anim_titulo("2 · Algoritmo — Fase 2: bajar hacia el hijo pesado"),
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
                self.wait(1.5)

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
        self.wait(2)

    # -------------------------------------------------------- cierre avance
    def seccion_proximamente(self):
        titulo = T("Avance · próximas escenas", 40, weight=BOLD)
        items = VGroup(*[T(f"•  {s}", 28, TEXTO_SUAVE) for s in (
            "Motivación: el juego del nodo escondido",
            "Casos de borde: dos centroides, camino de 10⁶ nodos, n = 1",
            "Complejidad: O(n) vs O(n²) con mediciones reales",
            "Cierre: descomposición en centroides",
        )]).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        VGroup(titulo, items).arrange(DOWN, buff=0.6).move_to(ORIGIN)
        self.play(FadeIn(titulo, shift=0.2 * UP))
        self.play(LaggedStart(*[FadeIn(m, shift=0.2 * LEFT) for m in items], lag_ratio=0.2),
                  run_time=1.5)
        self.wait(3)
        self.play(FadeOut(titulo), FadeOut(items))


class Avance(EscenaCentroide, Scene):
    """Video completo del avance."""

    def construct(self):
        self.preparar()
        self.seccion_titulo()
        self.seccion_definicion()
        self.seccion_demo()
        self.seccion_proximamente()


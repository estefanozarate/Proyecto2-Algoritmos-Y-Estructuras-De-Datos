#!/bin/bash
# Agrega narración con la voz del Mac (comando `say`) al video del centroide.
#
# Uso (desde la carpeta del repo):
#   bash agregar_voz.sh                     # usa el video 1080p60
#   bash agregar_voz.sh media/videos/centroide/2160p60/Centroide.mp4   # el 4K
#
# Opciones (variables de entorno):
#   VOZ=Paulina      voz del Mac (lista de voces en español: say -v '?' | grep es_)
#   VELOCIDAD=180    palabras por minuto


set -eo pipefail

VIDEO="${1:-media/videos/centroide/1080p60/Centroide.mp4}"
SALIDA="${2:-${VIDEO%.mp4}_con_voz.mp4}"
VOZ="${VOZ:-Paulina}"
VELOCIDAD="${VELOCIDAD:-180}"

GUION='0.5|Centroide de un árbol. Proyecto dos de Algoritmos y Estructuras de Datos.
6.6|Parte uno. Empecemos con un juego.
11.9|Escondí un nodo. Tú preguntas por uno, y te digo si es ese o hacia dónde está.
17.0|Preguntando hojas, descartas de a uno.
19.8|¿Y si preguntas siempre por el nodo que divide en mitades?
23.6|Cada respuesta descarta al menos la mitad: trece, cinco, dos, uno.
32.4|¡Cuatro preguntas en vez de doce!
36.1|Ese nodo que parte el árbol por la mitad se llama centroide.
41.1|Parte dos. ¿Qué es un centroide?
45.0|Es un nodo que, si lo quitas, ningún pedazo queda con más de la mitad.
50.6|¿Cuál crees que es?
52.4|Probemos quitando el uno.
55.1|Queda un pedazo de once nodos. No sirve.
58.5|Ahora quitemos el cuatro.
61.2|Ningún pedazo pasa de la mitad: es centroide.
64.6|Todo árbol tiene uno o dos centroides, y si son dos, son vecinos.
68.6|¿Para qué sirve? Para partir un árbol en pedazos equilibrados.
73.7|¿Cómo lo encontramos sin probar nodo por nodo?
77.0|Parte tres. Primero recorremos el árbol con un DFS. Al terminar cada nodo, su tamaño es uno más el de sus hijos.
85.0|Así sabemos cuántos nodos tiene cada subárbol.
88.5|Paso dos: bajamos hacia el hijo más pesado.
91.1|El dos tiene once nodos, más de la mitad. Bajamos.
94.5|El cuatro tiene ocho. Seguimos bajando.
97.9|Nadie pasa de la mitad: el cuatro es el centroide.
101.5|Un recorrido y una sola bajada: todo en tiempo lineal.
107.0|Casos de borde. Con n par, puede haber dos centroides.
110.6|La arista entre el dos y el cinco parte el árbol en dos mitades de cuatro. Los dos son centroides, y son vecinos.
118.4|Caso dos: un camino. Aquí la pila guarda todos los nodos.
123.4|Con recursión, Python falla pasando las mil llamadas. Por eso usé una pila propia.
128.5|En un camino, el centroide es el del medio: el seis.
132.0|Parte cinco. El recorrido visita cada nodo una vez, y la bajada sigue un solo camino: todo es O de n. Probar quitando cada nodo sería O de n al cuadrado.
143.2|Con mil nodos, mi algoritmo hace unos dos mil pasos; el ingenuo, casi dos millones.
150.0|Parte seis. ¿Para qué más sirve?
153.0|Como en el juego: tomas el centroide y repites en cada pedazo.
159.5|Salen solo cuatro niveles, porque cada pedazo tiene a lo más la mitad. Eso es la descomposición en centroides.
166.8|Gracias por ver.'

# ------------------------------------------------------------ verificaciones
command -v say >/dev/null || { echo "Este script necesita macOS (comando say)."; exit 1; }
command -v ffmpeg >/dev/null || { echo "Falta ffmpeg. Instálalo con: brew install ffmpeg"; exit 1; }
[ -f "$VIDEO" ] || { echo "No encuentro el video: $VIDEO (compílalo con: manim -qh centroide.py)"; exit 1; }
if ! say -v '?' | awk -v v="$VOZ" 'index($0, v " ") == 1 { f = 1 } END { exit !f }'; then
    echo "La voz \"$VOZ\" no está instalada. Voces en español disponibles:"
    say -v '?' | grep -E "es_[A-Z]{2}" || echo "  (ninguna; agrégalas en Ajustes > Accesibilidad > Contenido leído)"
    echo "Ejemplo: VOZ=Mónica bash agregar_voz.sh"
    exit 1
fi

DURACION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VIDEO")
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

INICIOS=()
TEXTOS=()
while IFS='|' read -r inicio texto; do
    [ -n "$inicio" ] || continue
    INICIOS+=("$inicio")
    TEXTOS+=("$texto")
done <<< "$GUION"
N=${#INICIOS[@]}

echo "Voz: $VOZ · velocidad: $VELOCIDAD ppm · video: $VIDEO (${DURACION%.*} s)"

ENTRADAS=()
FILTRO=""
MEZCLA=""
for ((k = 0; k < N; k++)); do
    inicio=${INICIOS[k]}
    if ((k + 1 < N)); then fin=${INICIOS[k + 1]}; else fin=$DURACION; fi

    say -v "$VOZ" -r "$VELOCIDAD" -o "$TMP/f$k.aiff" "${TEXTOS[k]}"
    dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMP/f$k.aiff")

    tempo=$(awk -v d="$dur" -v i="$inicio" -v f="$fin" 'BEGIN {
        v = f - i - 0.15; t = (v > 0) ? d / v : 1; if (t < 1) t = 1; if (t > 1.5) t = 1.5
        printf "%.3f", t }')
    if awk -v t="$tempo" 'BEGIN { exit !(t > 1.3) }'; then
        echo "  aviso: la frase del segundo $inicio va rápida (x$tempo); conviene acortarla"
    fi
    ms=$(awk -v i="$inicio" 'BEGIN { printf "%d", i * 1000 }')

    ENTRADAS+=(-i "$TMP/f$k.aiff")
    FILTRO+="[$((k + 1)):a]aresample=48000,atempo=$tempo,adelay=$ms:all=1[a$k];"
    MEZCLA+="[a$k]"
    printf "  %6.1f s  %s\n" "$inicio" "${TEXTOS[k]}"
done


FILTRO+="${MEZCLA}amix=inputs=$N:normalize=0:duration=longest,apad=whole_dur=$DURACION,asetpts=N/SR/TB[voz]"

ffmpeg -v error -y -i "$VIDEO" "${ENTRADAS[@]}" \
    -filter_complex "$FILTRO" \
    -map 0:v -map "[voz]" -c:v copy -c:a aac -b:a 192k -t "$DURACION" \
    -movflags +faststart "$SALIDA"

echo "Listo: $SALIDA"

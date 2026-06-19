#!/bin/sh
# ----------------------------------------------------------------------------
#  Arranque de Ollama para Railway (servicio independiente con GPU).
#  Inicia el servidor, descarga el modelo si falta y lo deja sirviendo.
#  Auto-descarga: NO requiere intervención manual.
# ----------------------------------------------------------------------------
set -e

MODEL="${OLLAMA_MODEL:-llama3.1}"

# Railway asigna $PORT y enruta el healthcheck/tráfico a ese puerto. Hacemos que
# Ollama escuche ahí (fija PORT=11434 en el servicio para una URL interna estable).
PORT="${PORT:-11434}"
export OLLAMA_HOST="0.0.0.0:${PORT}"

echo "[ollama] iniciando servidor en ${OLLAMA_HOST} ..."
ollama serve &
SERVER_PID=$!

echo "[ollama] esperando a que el servidor responda..."
until ollama list >/dev/null 2>&1; do
  sleep 2
done

echo "[ollama] verificando modelo '${MODEL}'..."
if ! ollama list | grep -q "${MODEL}"; then
  echo "[ollama] descargando '${MODEL}' (puede tardar varios minutos la 1ª vez)..."
  ollama pull "${MODEL}"
fi

echo "[ollama] modelo listo. Servidor en ejecución."
wait "${SERVER_PID}"

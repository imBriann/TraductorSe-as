#!/bin/sh
# ----------------------------------------------------------------------------
#  Arranque de Ollama para Railway (servicio independiente con GPU).
#  Inicia el servidor, descarga el modelo si falta y lo deja sirviendo.
#  Auto-descarga: NO requiere intervención manual.
# ----------------------------------------------------------------------------
set -e

MODEL="${OLLAMA_MODEL:-llama3.1}"

# Bind a todas las interfaces para que el servicio web lo alcance por la red
# privada de Railway (<servicio>.railway.internal:11434).
export OLLAMA_HOST="${OLLAMA_BIND:-0.0.0.0:11434}"

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

#!/bin/sh
# ----------------------------------------------------------------------------
#  Arranca el servidor Ollama y descarga el modelo Llama 3.1 si no existe.
# ----------------------------------------------------------------------------
set -e

MODEL="${OLLAMA_MODEL:-llama3.1}"

# Inicia el servidor en segundo plano
ollama serve &
SERVER_PID=$!

echo "[ollama-entrypoint] Esperando a que el servidor responda..."
until ollama list >/dev/null 2>&1; do
  sleep 2
done

echo "[ollama-entrypoint] Verificando modelo '${MODEL}'..."
if ! ollama list | grep -q "${MODEL}"; then
  echo "[ollama-entrypoint] Descargando modelo '${MODEL}' (puede tardar varios minutos)..."
  ollama pull "${MODEL}"
fi

echo "[ollama-entrypoint] Modelo listo. Servidor en ejecución."
wait $SERVER_PID

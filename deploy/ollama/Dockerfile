# ============================================================================
#  Servicio Ollama para Railway (con GPU) — auto-descarga de Llama 3
#  Despliega este directorio como un SEGUNDO servicio en Railway:
#    Service -> Settings -> Root Directory = deploy/ollama
#    Service -> Settings -> habilita GPU
#    Volume montado en /root/.ollama  (conserva el modelo entre despliegues)
# ============================================================================
FROM ollama/ollama:latest

# Modelo a descargar automáticamente al arrancar (llama3.1 | llama3 | ...)
ENV OLLAMA_MODEL=llama3.1

COPY entrypoint.sh /ollama-entrypoint.sh
RUN chmod +x /ollama-entrypoint.sh

EXPOSE 11434
ENTRYPOINT ["/bin/sh", "/ollama-entrypoint.sh"]

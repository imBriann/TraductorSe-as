# Despliegue en servidor (Ubuntu/Debian) con dominio + HTTPS + Llama 3.1

Guía para alojar LSC i5.0 en un equipo/servidor más potente, accesible desde
internet por un dominio con HTTPS automático. Ollama descargará Llama 3.1 solo.

> **Por qué HTTPS es obligatorio:** el navegador solo permite usar la cámara
> (`getUserMedia`) en `localhost` o sobre **HTTPS**. Por una IP en `http://` la
> cámara queda bloqueada. Por eso el despliegue usa **Caddy**, que emite y
> renueva el certificado TLS automáticamente.

---

## 1. Requisitos

| Recurso | Mínimo (llama3.1:8b) | Cómodo |
|--------|----------------------|--------|
| RAM | 8 GB | 16 GB+ |
| Disco | 20 GB libres | 40 GB+ |
| CPU | 4 vCPU | 8 vCPU |
| GPU | opcional | NVIDIA (acelera mucho a Llama) |

- Un **dominio** (o subdominio) con acceso a su DNS.
- Puertos **80** y **443** abiertos hacia el servidor (y **22** para SSH).

---

## 2. Preparar el servidor

Conéctate por SSH y actualiza:

```bash
sudo apt update && sudo apt upgrade -y
```

Instala Docker Engine + Compose (script oficial):

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER        # permite usar docker sin sudo
newgrp docker                        # aplica el grupo en la sesión actual
docker --version && docker compose version
```

---

## 3. Apuntar el dominio (DNS)

En tu proveedor de DNS crea un registro **A**:

```
Tipo: A    Nombre: lsc (o @)    Valor: <IP pública del servidor>    TTL: auto
```

Comprueba que resuelve (espera la propagación si hace falta):

```bash
dig +short lsc.midominio.com        # debe devolver la IP del servidor
```

---

## 4. Copiar el proyecto al servidor

Opción A — con Git:

```bash
git clone <URL-de-tu-repo> lsc-i5
cd lsc-i5
```

Opción B — desde tu PC con rsync/scp (si no usas Git):

```bash
# Ejecutar en tu equipo local:
rsync -av --exclude '.venv' --exclude 'node_modules' --exclude '__pycache__' \
      "./TraductorSeñas/" usuario@IP_SERVIDOR:~/lsc-i5/
```

---

## 5. Configurar variables de entorno

```bash
cp .env.example .env
nano .env
```

Ajusta al menos:

```ini
DOMAIN=lsc.midominio.com
POSTGRES_PASSWORD=pon-una-contraseña-fuerte
# El override de producción ya fuerza APP_ENV=production, DEBUG=false,
# DEV_MODE=false y ALLOWED_ORIGINS=https://$DOMAIN
```

> Con `DEV_MODE=false` se **ocultan** las pantallas de Dataset y Entrenamiento
> (recomendado en producción de cara al público). Si necesitas entrenar en el
> servidor, ponlo en `true` temporalmente.

---

## 6. (Opcional) Habilitar la GPU NVIDIA

Comprueba si el servidor tiene GPU utilizable:

```bash
nvidia-smi      # si muestra tu GPU, tienes driver instalado
```

Si funciona, instala el toolkit de contenedores NVIDIA:

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update && sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

Después, en el paso 8 añade el archivo `-f docker-compose.gpu.yml`.

> Si **no** tienes GPU, no pasa nada: Llama 3.1 8B funciona en CPU (más lento,
> unos segundos por frase). Mientras tanto el sistema usa el *fallback*
> gramatical contextual, así que nunca se queda sin responder.

---

## 7. Abrir el firewall

```bash
sudo ufw allow 22/tcp        # SSH
sudo ufw allow 80/tcp        # HTTP (Caddy: validación del certificado)
sudo ufw allow 443/tcp       # HTTPS
sudo ufw enable
```

Solo Caddy queda expuesto; PostgreSQL, Redis, Ollama y el backend quedan en la
red interna de Docker (no accesibles desde fuera).

---

## 8. Levantar todo en producción

**Sin GPU:**

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

**Con GPU** (tras el paso 6):

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.gpu.yml up -d --build
```

La primera vez:
- Construye la imagen del backend (descarga PyTorch/MediaPipe, varios minutos).
- **Descarga Llama 3.1 (~4.7 GB)** automáticamente. Sigue el progreso:

```bash
docker compose logs -f ollama
```

Cuando veas que el modelo está listo y Caddy obtuvo el certificado, abre:

### 👉 https://lsc.midominio.com

---

## 9. Elegir el tamaño del modelo

Por defecto `OLLAMA_MODEL=llama3.1` (8B). Puedes cambiarlo en `.env` según tu
hardware y volver a levantar:

| Modelo | `OLLAMA_MODEL` | Notas |
|--------|----------------|-------|
| Ligero/rápido | `llama3.2:3b` | Ideal para CPU modesta |
| Equilibrado (def.) | `llama3.1` | 8B; buena calidad, ~5 GB |
| Máxima calidad | `llama3.1:70b` | Requiere GPU potente (≥48 GB VRAM) |

```bash
nano .env                      # OLLAMA_MODEL=llama3.2:3b
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker compose exec ollama ollama pull llama3.2:3b   # opcional: pre-descargar
```

---

## 10. Verificación

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps   # todo "running/healthy"
curl https://lsc.midominio.com/api/v1/health           # {"status":"ok"}
curl https://lsc.midominio.com/api/v1/system/info       # estado de redis/ollama/modelo
```

En el navegador (https): **Empezar a traducir** → permitir cámara → señas.

---

## 11. Operación diaria

```bash
# Ver logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend

# Actualizar a una nueva versión del código
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Reiniciar / detener
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart
docker compose -f docker-compose.yml -f docker-compose.prod.yml down      # conserva datos
```

### Copia de seguridad de la base de datos

```bash
docker compose exec db pg_dump -U lsc lsc_db > backup_$(date +%F).sql
```

Los datos persisten en los volúmenes Docker `pgdata`, `redisdata`,
`ollamadata` (el modelo descargado) y `caddy_data` (certificados).

---

## 12. Solución de problemas

| Síntoma | Causa | Solución |
|---------|-------|----------|
| La cámara no abre | Acceso por `http://` o IP | Entra por **https://tu-dominio** (Caddy) |
| Caddy no emite certificado | DNS o puertos 80/443 | Verifica el registro A y `ufw`; mira `docker compose logs caddy` |
| Texto poco natural / lento | Llama aún descargando o CPU | Espera la descarga; considera `llama3.2:3b` o GPU |
| `nvidia-smi` no existe | Sin driver NVIDIA | Instala el driver o despliega sin el override de GPU |
| 502 en el dominio | Backend/frontend aún arrancando | Espera a `healthy`; revisa `docker compose ps` |
| No reconoce señas reales | No hay modelo entrenado | Entrena con `ml_training/` (ver README) o pantallas dev |

---

## 13. Resumen de comandos (TL;DR)

```bash
curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER && newgrp docker
git clone <repo> lsc-i5 && cd lsc-i5
cp .env.example .env && nano .env          # DOMAIN + POSTGRES_PASSWORD
sudo ufw allow 22,80,443/tcp && sudo ufw enable
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose logs -f ollama              # esperar descarga de Llama
# -> https://lsc.midominio.com
```

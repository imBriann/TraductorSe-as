# Manual de Usuario — LSC i5.0

Guía para personas usuarias del intérprete de Lengua de Señas Colombiana.

---

## 1. ¿Qué es LSC i5.0?

Una aplicación web que **traduce señas a texto en español**. Haces señas frente a
la cámara y el sistema muestra la frase correspondiente — **considerando lo que
ya señaste antes** (memoria de conversación).

**No necesitas crear cuenta ni iniciar sesión.** Abres la página y empiezas.

---

## 2. Empezar (en un clic)

1. Abre la aplicación (por defecto `http://localhost:3000`).
2. En **Inicio**, pulsa **🎥 Empezar a traducir**.
3. **Permite el acceso a la cámara** cuando el navegador lo pida.
4. ¡Listo! Empieza a hacer señas.

---

## 3. Traducir señas

- Haz tus señas frente a la cámara. Verás en vivo:
  - La **seña detectada** y su **confianza**.
  - La **frase en construcción** (glosas reconocidas).
  - Las **entidades** del contexto (sujeto, verbo, lugar, tiempo).
- **Al pausar** (bajar las manos un momento), la frase se **traduce
  automáticamente** y aparece en **Conversación**. También puedes pulsar
  **✅ Traducir ahora**.
- **🗑️ Nueva conversación** reinicia el contexto.
- Puedes desactivar la auto-traducción con la casilla *"Auto-traducir al pausar"*.

### Traducción contextual (ejemplo)
Si señas `YO ESTUDIAR UNIVERSIDAD` y luego, en la misma conversación, `MAÑANA`,
el sistema entiende el contexto y produce: **"Mañana estudiaré en la universidad."**

> **Consejos:** buena iluminación, fondo despejado, manos dentro del encuadre y
> una breve pausa entre señas.

---

## 4. Historial y exportación

En **Historial** ves tus traducciones (con un icono 🗃️ cuando se usó contexto),
puedes **eliminarlas** y **exportarlas** a **PDF**, **DOCX** o **TXT**.

---

## 5. Configuración

En **Configuración** puedes:
- Activar **🌓 modo oscuro**.
- Activar/desactivar la **🗃️ memoria contextual**.
- Ajustar el **umbral de confianza** (qué tan estricto es al aceptar una seña).
- Poner un **alias** opcional para el dispositivo.
- **Limpiar el contexto** de la conversación.
- Ver tus **estadísticas** de uso.

---

## 6. Información del sistema

La pantalla **Información** muestra el estado de los componentes (Redis, Ollama,
modelo) y el diagrama del pipeline de agentes.

---

## 7. Modo desarrollador (opcional)

Si la plataforma está en modo desarrollador, aparecen dos pantallas extra:

- **Dataset:** graba muestras de señas desde la cámara para crear/ampliar el
  conjunto de datos.
- **Entrenamiento:** lanza y supervisa el entrenamiento del modelo.

---

## 8. Privacidad

El reconocimiento de manos ocurre **en tu navegador**; al servidor solo se envían
las coordenadas (landmarks) de tus manos, **no la imagen de la cámara**. La
identidad es un código anónimo del dispositivo, sin datos personales.

---

## 9. Preguntas frecuentes

**¿Necesito registrarme?** No. El acceso es inmediato y anónimo.

**No se abre la cámara.** Usa `localhost` o HTTPS y concede permisos de cámara.

**La traducción tarda o no es natural.** La primera vez, Llama 3.1 puede estar
descargándose; mientras tanto se usa una traducción básica. Reintenta en unos
minutos.

**¿Se pierde mi historial?** Se guarda asociado a este dispositivo/navegador. Si
borras los datos del navegador, se genera un nuevo identificador anónimo.

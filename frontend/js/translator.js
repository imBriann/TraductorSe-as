// Motor del traductor en tiempo real: WebRTC + MediaPipe Hands + WebSocket.
// Identidad anónima por dispositivo. Modo contextual con auto-finalización por
// pausa (cuando dejas de hacer señas, la frase se traduce sola).
(function () {
  const cfg = window.LSC.config;

  class TranslatorEngine {
    constructor({ videoEl, canvasEl, onPartial, onFinal, onStatus, autoFinalize = true }) {
      this.video = videoEl;
      this.canvas = canvasEl;
      this.ctx = canvasEl.getContext("2d");
      this.onPartial = onPartial || (() => {});
      this.onFinal = onFinal || (() => {});
      this.onStatus = onStatus || (() => {});
      this.ws = null;
      this.camera = null;
      this.hands = null;
      this.running = false;
      this.lastSend = 0;
      this.sendIntervalMs = 100;            // ~10 fps de envío
      this.autoFinalize = autoFinalize;
      this.pauseMs = 1500;                  // pausa que cierra la frase
      this._lastHands = 0;
      this._bufferLen = 0;
      this._pauseTimer = null;
    }

    _flatten(results) {
      const vec = new Array(126).fill(0);
      const list = results.multiHandLandmarks || [];
      for (let h = 0; h < Math.min(list.length, 2); h++) {
        const base = h * 21 * 3;
        list[h].forEach((lm, i) => {
          const off = base + i * 3;
          vec[off] = lm.x; vec[off + 1] = lm.y; vec[off + 2] = lm.z;
        });
      }
      return vec;
    }

    _draw(results) {
      const { ctx, canvas } = this;
      ctx.save();
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);
      if (results.multiHandLandmarks && window.drawConnectors) {
        for (const lm of results.multiHandLandmarks) {
          window.drawConnectors(ctx, lm, window.HAND_CONNECTIONS, { color: "#4f46e5", lineWidth: 3 });
          window.drawLandmarks(ctx, lm, { color: "#22d3ee", radius: 3 });
        }
      }
      ctx.restore();
    }

    _connectWs() {
      const params = new URLSearchParams({ device: cfg.deviceId });
      this.ws = new WebSocket(`${cfg.WS_BASE}?${params.toString()}`);
      this.ws.onopen = () => this.onStatus("connected");
      this.ws.onclose = () => this.onStatus("disconnected");
      this.ws.onerror = () => this.onStatus("error");
      this.ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.type === "partial") {
          this._bufferLen = (msg.buffer || []).length;
          this.onPartial(msg);
        } else if (msg.type === "final") {
          this._bufferLen = 0;
          this.onFinal(msg);
        } else if (msg.type === "error") {
          this.onStatus("error", msg.detail);
        }
      };
    }

    _checkPause() {
      if (!this.autoFinalize || !this.running) return;
      const idle = Date.now() - this._lastHands;
      if (this._bufferLen > 0 && idle > this.pauseMs) {
        this._bufferLen = 0;       // evita re-disparos
        this.finalize();
      }
    }

    async start() {
      if (this.running) return;
      this._connectWs();

      this.hands = new window.Hands({
        locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${f}`,
      });
      this.hands.setOptions({
        maxNumHands: 2, modelComplexity: 1,
        minDetectionConfidence: 0.6, minTrackingConfidence: 0.6,
      });
      this.hands.onResults((results) => {
        this._draw(results);
        const hasHands = (results.multiHandLandmarks || []).length > 0;
        if (hasHands) this._lastHands = Date.now();
        const now = Date.now();
        if (hasHands && this.ws && this.ws.readyState === WebSocket.OPEN &&
            now - this.lastSend >= this.sendIntervalMs) {
          this.lastSend = now;
          this.ws.send(JSON.stringify({ type: "frame", landmarks: this._flatten(results) }));
        }
      });

      this.camera = new window.Camera(this.video, {
        onFrame: async () => { await this.hands.send({ image: this.video }); },
        width: 640, height: 480,
      });
      await this.camera.start();
      this.running = true;
      this._lastHands = Date.now();
      this._pauseTimer = setInterval(() => this._checkPause(), 300);
      this.onStatus("running");
    }

    finalize() {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "finalize" }));
      }
    }

    reset() {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "reset" }));
      }
      this._bufferLen = 0;
    }

    stop() {
      this.running = false;
      if (this._pauseTimer) clearInterval(this._pauseTimer);
      if (this.camera) this.camera.stop();
      if (this.ws) this.ws.close();
      this.onStatus("stopped");
    }
  }

  window.LSC.TranslatorEngine = TranslatorEngine;
})();

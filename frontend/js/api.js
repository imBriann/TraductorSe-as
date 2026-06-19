// Cliente HTTP de la API (sin autenticación; identidad por cabecera X-Device-Id).
(function () {
  const cfg = window.LSC.config;

  async function request(path, options = {}) {
    const headers = options.headers || {};
    if (!(options.body instanceof FormData) && !headers["Content-Type"] && options.body) {
      headers["Content-Type"] = "application/json";
    }
    headers["X-Device-Id"] = cfg.deviceId;
    return fetch(`${cfg.API_BASE}${path}`, { ...options, headers });
  }

  async function json(path, options) {
    const res = await request(path, options);
    const data = res.status === 204 ? null : await res.json().catch(() => null);
    if (!res.ok) {
      throw new Error((data && data.detail) || `Error ${res.status}`);
    }
    return data;
  }

  window.LSC.api = {
    request, json,

    // Preferencias del dispositivo
    settings: () => json("/settings/me"),
    updateSettings: (payload) => json("/settings/me", { method: "PATCH", body: JSON.stringify(payload) }),
    myStats: () => json("/settings/stats"),

    // Sistema
    systemInfo: () => json("/system/info"),

    // Traducción
    infer: (payload, finalize = true) =>
      json(`/translations/infer?finalize=${finalize}`, { method: "POST", body: JSON.stringify(payload) }),
    resetContext: (sessionId) =>
      json(`/translations/context/reset${sessionId ? `?session_id=${sessionId}` : ""}`, { method: "POST" }),
    history: (limit = 100) => json(`/translations?limit=${limit}`),
    deleteTranslation: (id) => json(`/translations/${id}`, { method: "DELETE" }),

    // Dev: dataset y entrenamiento
    dataset: () => json("/dev/dataset"),
    addSample: (label, sequence) => json("/dev/dataset/sample", { method: "POST", body: JSON.stringify({ label, sequence }) }),
    startTraining: (params) => json("/dev/training/start", { method: "POST", body: JSON.stringify(params) }),
    trainingStatus: () => json("/dev/training/status"),
    stopTraining: () => json("/dev/training/stop", { method: "POST" }),
  };
})();

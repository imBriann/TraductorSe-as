// Configuración global del frontend LSC i5.0 (acceso anónimo por dispositivo).
window.LSC = window.LSC || {};

(function () {
  const DEVICE_KEY = "lsc_device_id";

  // Genera/recupera un identificador anónimo de dispositivo (sin login).
  function getDeviceId() {
    let id = localStorage.getItem(DEVICE_KEY);
    if (!id) {
      id = (crypto.randomUUID
        ? crypto.randomUUID()
        : "dev-" + Date.now() + "-" + Math.random().toString(16).slice(2));
      localStorage.setItem(DEVICE_KEY, id);
    }
    return id;
  }

  window.LSC.config = {
    API_BASE: "/api/v1",
    WS_BASE: (location.protocol === "https:" ? "wss://" : "ws://") +
             location.host + "/api/v1/ws/translate",
    DEVICE_KEY,
    THEME_KEY: "lsc_theme",
    getDeviceId,
    deviceId: getDeviceId(),
  };
})();

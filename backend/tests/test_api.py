"""Tests de integración de la API (acceso anónimo por dispositivo)."""
import pytest

from app.ml.constants import FEATURES_PER_FRAME

API = "/api/v1"


@pytest.mark.asyncio
async def test_health(client):
    res = await client.get(f"{API}/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_system_info(client):
    res = await client.get(f"{API}/system/info")
    assert res.status_code == 200
    body = res.json()
    assert "Context" in body["pipeline"]
    assert body["num_classes"] > 0


@pytest.mark.asyncio
async def test_settings_get_and_update(client):
    res = await client.get(f"{API}/settings/me")
    assert res.status_code == 200
    assert res.json()["device_uid"] == "test-device-0001"

    upd = await client.patch(f"{API}/settings/me", json={
        "dark_mode": True, "confidence_threshold": 0.0, "context_enabled": True,
    })
    assert upd.status_code == 200
    assert upd.json()["dark_mode"] is True


@pytest.mark.asyncio
async def test_infer_history_and_export(client):
    # umbral 0.0 para garantizar aceptación del fallback determinista
    await client.patch(f"{API}/settings/me", json={"confidence_threshold": 0.0})

    seq = [[0.2] * FEATURES_PER_FRAME for _ in range(30)]
    infer = await client.post(
        f"{API}/translations/infer?finalize=true",
        json={"sequence": seq, "generate_text": True},
    )
    assert infer.status_code == 200
    body = infer.json()
    assert body["gloss"]
    assert body["natural_text"]  # texto generado (fallback local sin Ollama)

    history = await client.get(f"{API}/translations")
    assert history.status_code == 200
    assert len(history.json()) >= 1

    exp = await client.get(f"{API}/translations/export/txt")
    assert exp.status_code == 200
    assert exp.headers["content-type"].startswith("text/plain")


@pytest.mark.asyncio
async def test_context_reset(client):
    res = await client.post(f"{API}/translations/context/reset")
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_dev_dataset_summary(client):
    res = await client.get(f"{API}/dev/dataset")
    assert res.status_code == 200
    assert "classes" in res.json()

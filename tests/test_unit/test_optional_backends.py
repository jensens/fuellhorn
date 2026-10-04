"""Das Image muss den Redis-Client mitbringen, damit das Helm-Chart ``sessions.backend: redis`` nutzen kann (#434).

NiceGUI liest ``NICEGUI_REDIS_URL`` beim Import und wechselt dann auf ``RedisPersistentDict``,
das ``redis.asyncio`` importiert.
"""

import importlib.util


def test_redis_client_is_installed_for_shared_sessions() -> None:
    assert importlib.util.find_spec("redis") is not None, "redis fehlt in den Abhängigkeiten (uv add redis)"
    assert importlib.util.find_spec("redis.asyncio") is not None

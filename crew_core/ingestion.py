"""Ingesta HTTP acotada desde fuentes API configuradas por el backend."""

from __future__ import annotations

import json
from copy import deepcopy
from threading import RLock
import time
from typing import Any
from uuid import uuid4

import requests


DEFAULT_SOURCE = "jsonplaceholder_todo"
API_SOURCES = {
    DEFAULT_SOURCE: {
        "name": "JSONPlaceholder Todo",
        "url": "https://jsonplaceholder.typicode.com/todos/1",
    }
}
REQUEST_TIMEOUT_SECONDS = 8
MAX_RESPONSE_BYTES = 128 * 1024
MAX_PREVIEW_CHARS = 1500
INGESTION_TTL_SECONDS = 10 * 60
MAX_INGESTION_RECORDS = 100


class IngestionError(RuntimeError):
    """Error seguro y esperado durante una ingesta."""


class IngestionTimeoutError(IngestionError):
    """La fuente no respondió dentro del timeout configurado."""


class IngestionRegistry:
    """Almacén temporal thread-safe que conserva el JSON original en servidor."""

    def __init__(
        self,
        ttl_seconds: int = INGESTION_TTL_SECONDS,
        max_entries: int = MAX_INGESTION_RECORDS,
        clock: Any = time.monotonic,
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries
        self._clock = clock
        self._lock = RLock()
        self._records: dict[str, dict[str, Any]] = {}

    def store(self, source: str, source_name: str, data: Any) -> dict[str, Any]:
        now = self._clock()
        with self._lock:
            self._purge_locked(now)
            while len(self._records) >= self._max_entries:
                oldest_id = min(
                    self._records,
                    key=lambda item: self._records[item]["created_at"],
                )
                del self._records[oldest_id]

            ingestion_id = str(uuid4())
            self._records[ingestion_id] = {
                "ingestion_id": ingestion_id,
                "source": source,
                "source_name": source_name,
                "data": deepcopy(data),
                "created_at": now,
                "expires_at": now + self._ttl_seconds,
            }
            return deepcopy(self._records[ingestion_id])

    def get(self, ingestion_id: str) -> dict[str, Any] | None:
        now = self._clock()
        with self._lock:
            self._purge_locked(now)
            record = self._records.get(ingestion_id)
            return deepcopy(record) if record is not None else None

    def _purge_locked(self, now: float) -> None:
        expired = [
            ingestion_id
            for ingestion_id, record in self._records.items()
            if record["expires_at"] <= now
        ]
        for ingestion_id in expired:
            del self._records[ingestion_id]


ingestion_registry = IngestionRegistry()


def _preview(data: Any) -> str:
    rendered = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    if len(rendered) <= MAX_PREVIEW_CHARS:
        return rendered
    return rendered[: MAX_PREVIEW_CHARS - 1] + "…"


def fetch_api_source(source: str = DEFAULT_SOURCE) -> dict[str, Any]:
    """Obtiene y normaliza JSON desde una fuente definida en ``API_SOURCES``."""
    if not isinstance(source, str) or source not in API_SOURCES:
        raise IngestionError("Fuente API no permitida.")

    config = API_SOURCES[source]
    try:
        response = requests.get(
            config["url"],
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT_SECONDS,
            stream=True,
            allow_redirects=False,
        )
    except requests.Timeout as exc:
        raise IngestionTimeoutError(
            "La fuente API excedió el tiempo de espera."
        ) from exc
    except requests.RequestException as exc:
        raise IngestionError("No se pudo consultar la fuente API.") from exc

    try:
        if not 200 <= response.status_code < 300:
            raise IngestionError("La fuente API respondió con un error HTTP.")

        content_type = response.headers.get("Content-Type", "")
        if content_type.split(";", 1)[0].strip().lower() != "application/json":
            raise IngestionError("La fuente API no devolvió contenido JSON.")

        body = bytearray()
        try:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                body.extend(chunk)
                if len(body) > MAX_RESPONSE_BYTES:
                    raise IngestionError(
                        "La respuesta de la fuente API es demasiado grande."
                    )
        except requests.Timeout as exc:
            raise IngestionTimeoutError(
                "La fuente API excedió el tiempo de espera."
            ) from exc
        except requests.RequestException as exc:
            raise IngestionError("No se pudo leer la respuesta de la fuente API.") from exc

        try:
            data = json.loads(body.decode(response.encoding or "utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IngestionError("La fuente API devolvió JSON inválido.") from exc
    finally:
        response.close()

    return {
        "source": source,
        "source_name": config["name"],
        "status": "OK",
        "data": data,
        "preview": _preview(data),
    }

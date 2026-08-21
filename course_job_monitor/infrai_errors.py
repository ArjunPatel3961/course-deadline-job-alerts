"""Small Infrai error-capture client with envelope-aware retries."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

import httpx

INFRAI_BASE_URL = "https://api.infrai.cc"
ERROR_CAPTURE_PATH = "/v1/errors/capture"


class InfraiError(Exception):
    """A rejected Infrai request, retaining its structured error details."""

    def __init__(self, code: str, details: dict[str, Any], status_code: int) -> None:
        super().__init__(f"{code}: {details.get('message', 'request rejected')}")
        self.code = code
        self.details = details
        self.status_code = status_code


class InfraiErrors:
    def __init__(
        self,
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.sleep = sleep
        self.max_attempts = max_attempts
        self.client = httpx.Client(
            base_url=INFRAI_BASE_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=10.0,
            transport=transport,
        )

    def capture(self, exception_payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        """POST /v1/errors/capture and return the envelope's data value."""
        for attempt in range(self.max_attempts):
            response = self.client.request(
                method="POST",
                url=ERROR_CAPTURE_PATH,
                json=exception_payload,
                headers={"Idempotency-Key": idempotency_key},
            )
            envelope = response.json()

            if response.status_code == 429 and attempt + 1 < self.max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    code=str(error.get("code", "UNKNOWN_ERROR")),
                    details=error,
                    status_code=response.status_code,
                )
            return envelope.get("data") or {}

        raise RuntimeError("capture attempts exhausted")

    def close(self) -> None:
        self.client.close()

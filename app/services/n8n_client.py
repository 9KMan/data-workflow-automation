"""n8n webhook client for automation triggers."""
import logging
from typing import Any

import httpx

from app.config import settings

log = logging.getLogger(__name__)


class N8NClient:
    """Lightweight n8n webhook caller."""

    def __init__(self, webhook_url: str | None = None, timeout: float = 10.0):
        self.webhook_url = webhook_url or settings.N8N_WEBHOOK_URL
        self.timeout = timeout

    def trigger(self, payload: dict[str, Any]) -> bool:
        """
        Send payload to n8n webhook URL.
        Returns True on success, False on failure.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                log.info(f"n8n webhook triggered successfully: {self.webhook_url}")
                return True
        except httpx.HTTPError as e:
            log.warning(f"n8n webhook failed: {e}")
            return False


def trigger_n8n(
    event: str,
    data: dict[str, Any],
    pipeline_name: str | None = None,
    webhook_url: str | None = None,
) -> bool:
    """Convenience function to trigger n8n webhook."""
    payload = {
        "event": event,
        "data": data,
        "pipeline": pipeline_name,
    }
    client = N8NClient(webhook_url=webhook_url)
    return client.trigger(payload)
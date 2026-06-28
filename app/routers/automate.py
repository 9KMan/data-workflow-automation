"""Automation trigger endpoints — n8n integration and internal triggers."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TriggerPayload, N8NWebhookPayload, IngestResponse
from app.services.n8n_client import trigger_n8n

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/automate/trigger")
async def automate_trigger(payload: TriggerPayload, db: Session = Depends(get_db)):
    """
    Internal automation trigger — called by ETL pipeline on data events.
    Routes to n8n webhook if configured.
    """
    event = payload.event
    data = payload.data
    pipeline_name = payload.pipeline_name

    log.info(f"Automation trigger: event={event}, pipeline={pipeline_name}")

    # Forward to n8n webhook if URL is configured
    success = trigger_n8n(event=event, data=data, pipeline_name=pipeline_name)

    return {
        "event": event,
        "triggered": success,
        "pipeline": pipeline_name,
    }


@router.post("/automate/n8n-webhook")
async def n8n_webhook(payload: N8NWebhookPayload, db: Session = Depends(get_db)):
    """Forward data to a specific n8n webhook URL."""
    try:
        from app.services.n8n_client import N8NClient
        client = N8NClient(webhook_url=payload.url)
        success = client.trigger(payload=payload.payload)
        if not success:
            raise HTTPException(status_code=502, detail="n8n webhook returned error")
        return {"status": "ok", "url": payload.url}
    except Exception as e:
        log.error(f"n8n webhook error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
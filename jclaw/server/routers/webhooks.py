"""Webhook endpoints for channels."""

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook.

    Telegram sends updates to this endpoint.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Get adapters and orchestrator
    telegram_channel = request.app.state.telegram_channel
    orchestrator = request.app.state.orchestrator

    try:
        # Parse message
        inbound = await telegram_channel.receive_webhook(body)

        # Process
        response = await orchestrator.process(inbound)

        # Send response
        await telegram_channel.send_message(inbound.chat_id, response)

        return {"ok": True}

    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/rest")
async def rest_webhook(request: Request):
    """Handle REST webhook (for testing).

    Same as /v1/chat but returns message object instead.
    """
    return await request.app.state.rest_channel.receive_webhook(await request.json())

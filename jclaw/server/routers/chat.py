"""Chat API endpoints."""

from fastapi import APIRouter, HTTPException, Request

from jclaw.types import InboundMessage, OutboundMessage

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat")
async def chat(request: Request):
    """Process a chat message.

    Request body:
    {
        "message": "User message",
        "session_id": "optional-session-id",
        "chat_id": "optional-chat-id",
        "user_id": "optional-user-id"
    }
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    message_text = body.get("message", "")
    if not message_text:
        raise HTTPException(status_code=400, detail="message is required")

    chat_id = body.get("chat_id", "web_chat")
    user_id = body.get("user_id", "web_user")

    # Create inbound message
    inbound = InboundMessage(
        message_id=body.get("message_id"),
        chat_id=chat_id,
        user_id=user_id,
        channel="rest",
        text=message_text,
        metadata=body.get("metadata", {}),
    )

    # Process through orchestrator
    orchestrator = request.app.state.orchestrator
    rest_channel = request.app.state.rest_channel

    try:
        response = await orchestrator.process(inbound)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    return {
        "response": response.text,
        "message_id": inbound.message_id,
        "status": "ok",
    }

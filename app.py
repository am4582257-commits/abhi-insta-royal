import hashlib
import hmac
import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("abhi-insta-royal")

app = FastAPI(title="ABHI INSTA ROYAL", version="0.2.0")


@app.get("/")
async def health() -> dict[str, str]:
    return {"name": "ABHI INSTA ROYAL", "status": "running"}


@app.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> str:
    expected = os.getenv("META_VERIFY_TOKEN", "")
    if hub_mode == "subscribe" and expected and hmac.compare_digest(hub_verify_token or "", expected):
        return hub_challenge or ""
    raise HTTPException(status_code=403, detail="Webhook verification failed")


def valid_signature(raw_body: bytes, signature: str | None) -> bool:
    secret = os.getenv("META_APP_SECRET", "")
    if not secret or not signature or not signature.startswith("sha256="):
        return False
    digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature.removeprefix("sha256="), digest)


async def send_instagram_text(recipient_id: str, text: str) -> None:
    token = os.getenv("META_ACCESS_TOKEN", "")
    account_id = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
    version = os.getenv("META_GRAPH_API_VERSION", "v24.0")
    base_url = os.getenv("META_GRAPH_API_BASE", "https://graph.instagram.com").rstrip("/")
    if not token or not account_id:
        logger.warning("Auto-reply skipped: META_ACCESS_TOKEN or INSTAGRAM_ACCOUNT_ID is missing")
        return

    url = f"{base_url}/{version}/{account_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(url, headers=headers, json=body)
    if response.is_success:
        logger.info("Instagram reply sent successfully")
    else:
        # Avoid logging tokens or message contents.
        logger.error("Instagram API send failed: status=%s response=%s", response.status_code, response.text[:500])


def make_auto_reply(incoming_text: str) -> str:
    configured = os.getenv("AUTO_REPLY_TEXT", "").strip()
    if configured:
        return configured[:1000]
    return (
        "Namaste! 👋 ABHI INSTA ROYAL par aapka message mil gaya hai. "
        "Abhi main available nahi hoon; jald reply milega. ✨"
    )


@app.post("/webhook")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, str]:
    raw_body = await request.body()
    if not valid_signature(raw_body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload: dict[str, Any] = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    if payload.get("object") != "instagram":
        return {"status": "ignored"}

    for entry in payload.get("entry", []):
        for event in entry.get("messaging", []):
            sender = event.get("sender", {}).get("id")
            message = event.get("message", {})
            text = message.get("text", "").strip()
            is_echo = message.get("is_echo", False)
            if sender and text and not is_echo:
                try:
                    await send_instagram_text(sender, make_auto_reply(text))
                except httpx.HTTPError as exc:
                    logger.error("Instagram API request error: %s", type(exc).__name__)

        for change in entry.get("changes", []):
            logger.info("Instagram change received: field=%s", change.get("field", "unknown"))

    return {"status": "received"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))

import hashlib
import hmac
import os
import logging
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("abhi-insta-royal")

app = FastAPI(title="ABHI INSTA ROYAL", version="0.1.0")


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
    # During initial local setup, allow unsigned requests only when no app secret is configured.
    if not secret:
        return True
    if not signature or not signature.startswith("sha256="):
        return False
    digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature.removeprefix("sha256="), digest)


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

    # Official Instagram webhooks only. This starter logs event metadata;
    # it does not send messages until Meta permissions and a reply workflow are configured.
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            logger.info("Instagram change received: field=%s", change.get("field", "unknown"))
        for messaging_event in entry.get("messaging", []):
            logger.info("Instagram messaging event received")

    return {"status": "received"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))

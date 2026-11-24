# ABHI INSTA ROYAL

A starter webhook backend for an Instagram assistant using Meta's **official Instagram API**.

## Current starter features
- FastAPI health endpoint at `/`
- Meta webhook verification at `/webhook`
- Webhook event receiver with request-signature validation when `META_APP_SECRET` is configured
- No Instagram password/session automation

## Important limitations
- This project does not automate Instagram group chats. The official Instagram API does not provide general group-chat bot participation.
- DM and comment automation require an eligible Instagram professional account, the correct Meta app setup, approved permissions, and any required review.
- This repository is only the backend starter. It is not yet connected to your Instagram account and does not send replies yet.
- GitHub Actions is used for code checks, not as a 24/7 bot host.

## Run locally
1. Install Python 3.11 or newer.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and set a long random `META_VERIFY_TOKEN`.
4. Start the server:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

## Environment variables
- `META_VERIFY_TOKEN`: secret string used for Meta webhook verification.
- `META_APP_SECRET`: Meta app secret, used to validate webhook signatures.
- `META_ACCESS_TOKEN`: reserved for a future official API reply integration; do not put it in source code.
- `INSTAGRAM_ACCOUNT_ID`: eligible Instagram professional account ID.

Set real secrets in your hosting provider's environment-variable settings, never in GitHub source files.

## Next setup
Deploy this FastAPI app to a supported hosting service, configure its public HTTPS webhook URL in Meta Developers, then complete Meta's Instagram permissions and account connection. Only after that should an official DM/comment reply handler be added.

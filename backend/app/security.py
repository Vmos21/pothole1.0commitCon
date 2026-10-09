import hmac
import os
from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

SESSION_COOKIE = "roadsense_official_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 8
_DEMO_SESSION_SECRET = "local-demo-only-change-before-deployment"


def _session_serializer() -> URLSafeTimedSerializer:
    secret = os.environ.get("SESSION_SECRET")
    is_production = os.environ.get("APP_ENV", "development").lower() == "production"
    if not secret:
        if is_production:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Official sign-in is not configured",
            )
        secret = _DEMO_SESSION_SECRET
    if is_production and (len(secret) < 32 or secret.startswith("replace-with-")):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Configure a strong production session secret",
        )
    return URLSafeTimedSerializer(secret, salt="official-session-v1")


def verify_credentials(username: str, password: str) -> bool:
    is_production = os.environ.get("APP_ENV", "development").lower() == "production"
    configured_username = os.environ.get("OFFICIAL_USERNAME")
    configured_password = os.environ.get("OFFICIAL_PASSWORD")
    if not configured_username or not configured_password:
        if is_production:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Official credentials are not configured",
            )
        configured_username = configured_username or "official@roadsense.local"
        configured_password = configured_password or "RoadSense-Demo-2026!"
    return hmac.compare_digest(username, configured_username) and hmac.compare_digest(
        password, configured_password
    )


def create_session(username: str) -> str:
    return _session_serializer().dumps({"sub": username})


def read_session(token: str) -> str | None:
    try:
        payload = _session_serializer().loads(token, max_age=SESSION_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired, HTTPException):
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None


def require_official(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE)
    username = read_session(token) if token else None
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Official sign-in required",
        )
    return username


def session_cookie_secure() -> bool:
    return os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"


def current_time() -> datetime:
    return datetime.now(timezone.utc)

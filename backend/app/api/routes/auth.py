from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.security import (
    SESSION_COOKIE,
    SESSION_MAX_AGE_SECONDS,
    create_session,
    require_official,
    session_cookie_secure,
    verify_credentials,
)

router = APIRouter(prefix="/auth", tags=["official authentication"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


@router.post("/login")
def login(credentials: LoginRequest, response: Response) -> dict[str, str]:
    if not verify_credentials(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid official credentials",
        )

    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session(credentials.username),
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=session_cookie_secure(),
        samesite="strict",
        path="/",
    )
    return {"username": credentials.username, "role": "official"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        httponly=True,
        secure=session_cookie_secure(),
        samesite="strict",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me")
def current_official(request: Request) -> dict[str, str]:
    username = require_official(request)
    return {"username": username, "role": "official"}

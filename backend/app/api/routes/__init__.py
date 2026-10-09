from fastapi import APIRouter

from app.api.routes.incidents import router as incidents_router
from app.api.routes.auth import router as auth_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(incidents_router)

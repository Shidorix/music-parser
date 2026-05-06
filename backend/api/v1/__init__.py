"""Version 1 API router."""

from fastapi import APIRouter

from backend.api.v1.health import router as health_router
from backend.api.v1.parse import router as parse_router
from backend.api.v1.parse_and_match import router as parse_and_match_router
from backend.api.v1.playlists import router as playlists_router
from backend.api.v1.search import router as search_router
from backend.api.v1.sessions import router as sessions_router

router = APIRouter()
router.include_router(health_router)
router.include_router(sessions_router)
router.include_router(parse_router)
router.include_router(parse_and_match_router)
router.include_router(playlists_router)
router.include_router(search_router)

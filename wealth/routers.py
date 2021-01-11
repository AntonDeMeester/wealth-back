from fastapi.routing import APIRouter

from .core import authentication
from .integrations.tink import views as tink_views

router = APIRouter()

router.include_router(tink_views.router, tags=["tink"])
router.include_router(authentication.router, prefix="/auth", tags=["auth"])

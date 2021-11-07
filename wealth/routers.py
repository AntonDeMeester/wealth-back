from fastapi.routing import APIRouter

from .authentication import views as auth_views
from .banking import views as banking_views
from .custom_assets import views as asset_views
from .integrations.tink import views as tink_views
from .stocks import views as stock_views

router = APIRouter()

router.include_router(tink_views.router, prefix="/tink", tags=["tink"])
router.include_router(auth_views.router, prefix="/auth", tags=["auth"])
router.include_router(banking_views.router, prefix="/banking", tags=["banking"])
router.include_router(stock_views.router, prefix="/stocks", tags=["stocks"])
router.include_router(asset_views.router, prefix="/custom", tags=["custom-assets"])

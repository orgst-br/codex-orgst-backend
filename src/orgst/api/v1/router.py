from ninja import NinjaAPI

from apps.accounts.auth import JWTAuth
from apps.accounts.views import router as accounts_router
from apps.community.views import router as community_router
from apps.docs.views import router as docs_router

api = NinjaAPI(title="Orgst API", version="1.0", auth=JWTAuth())


@api.get("/health", auth=None)
def health(request):
    return {"status": "ok"}


api.add_router("/accounts", accounts_router)
api.add_router("/community", community_router)
api.add_router("/docs", docs_router)

from ninja import NinjaAPI

from apps.accounts.views import router as accounts_router
from apps.community.views import router as community_router

api = NinjaAPI(title="Orgst API", version="1.0")


@api.get("/health")
def health(request):
    return {"status": "ok"}


api.add_router("", accounts_router)
api.add_router("", community_router)

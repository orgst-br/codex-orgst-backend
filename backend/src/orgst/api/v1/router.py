from ninja import NinjaAPI

from apps.accounts.api import router as accounts_router

api = NinjaAPI(title="Orgst API", version="1.0")

@api.get("/health")
def health(request):
    return {"status": "ok"}

api.add_router("", accounts_router)
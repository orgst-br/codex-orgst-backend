from ninja import NinjaAPI

api = NinjaAPI(title="Orgst API", version="1.0")

@api.get("/health")
def health(request):
    return {"status": "ok"}


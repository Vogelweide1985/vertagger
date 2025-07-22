from fastapi import APIRouter

# Erstellt einen Router, der alle seine Routen unter dem Präfix /api/v1.0 gruppiert
router = APIRouter(
    prefix="/api/v1.0",
    tags=["Version 1.0"]  # Gruppiert die Endpunkte in der Doku
)

@router.get("/info")
def get_info_v1():
    return {"version": "1.0", "message": "Dies ist die stabile, alte Version."}

@router.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "version": "1.0"}
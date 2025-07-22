from fastapi import FastAPI
from .__about__ import __version__

# Importiere hier die Router für jede Version, die du hast
from .api.v1_0 import endpoints

app = FastAPI(
    title="Vertagger API",
    version=__version__
)

# Binde den Router für v1.0 in die Haupt-App ein
app.include_router(endpoints.router)

# Wenn du später v1.1 hinzufügst, importierst und inkludierst du ihn hier auch
# from .api import v1_1
# app.include_router(v1_1.router)


@app.get("/")
def read_root():
    return {"message": "Willkommen zur Vertagger API", "version": __version__}
from fastapi import FastAPI
from contextlib import asynccontextmanager
from openai import AsyncOpenAI
from .__about__ import __version__
from .config import global_settings # Dein globaler API Key
from .api.v1_0 import endpoints as v1_endpoints

#Der Client wird hier einmalig erstellt und in der App gespeichert
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.openai_client = AsyncOpenAI(api_key=global_settings.openai_api_key)
    yield
    await app.state.openai_client.close()

# Lifespan-Manager an die App
app = FastAPI(title="Vertagger API", version=__version__, lifespan=lifespan)

#Include Routers
app.include_router(v1_endpoints.router)


@app.get("/")
def read_root():
    return {"message": "Willkommen zur Vertagger API", "version": __version__}
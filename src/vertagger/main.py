import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from openai import AsyncOpenAI
from .__about__ import __version__
from .config import global_settings 
from .api.v1_0 import endpoints as v1_endpoints

from opik.integrations.openai import track_openai

#Der Client wird hier einmalig erstellt und in der App gespeichert
@asynccontextmanager
async def lifespan(app: FastAPI):

    os.environ["OPIK_API_KEY"] = global_settings.opik_api_key
    os.environ["OPIK_WORKSPACE"] = global_settings.opik_workspace
    os.environ["OPIK_PROJECT_NAME"] = global_settings.opik_project_name
    app.state.openai_client = track_openai(AsyncOpenAI(api_key=global_settings.openai_api_key))
    yield
    await app.state.openai_client.close()

# Lifespan-Manager an die App
app = FastAPI(title="Vertagger API", version=__version__, lifespan=lifespan)

#Include Routers
app.include_router(v1_endpoints.router)


@app.get("/")
def read_root():
    return {"message": "Willkommen zur Vertagger API", "version": __version__}
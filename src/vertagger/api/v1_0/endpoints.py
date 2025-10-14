# -*- coding: utf-8 -*-

"""
Definiert die API-Endpunkte für die Version 1.0.

Dieses Modul ist verantwortlich für das Routing von Anfragen. Es verwendet einen
FastAPI `APIRouter`, um Endpunkte zu gruppieren, die logisch zusammengehören
(hier alle, die zu v1_0 gehören).

Der Hauptfokus liegt auf der sauberen Trennung von Verantwortlichkeiten durch
die Verwendung des Dependency-Injection-Systems von FastAPI.
"""

# --- 1. Importe ---
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from openai import AsyncOpenAI

# Interne Importe, die die Datenstrukturen, die Geschäftslogik und die Konfiguration verbinden.
from .models import ArticleInput, ArticleOutput
from .services import ArticleService
from ...config import settings

from ...api.dependencies import get_api_key

# --- 2. Router-Initialisierung ---
# Ein Router ist wie ein Mini-FastAPI-App-Objekt. Er hilft, das Projekt zu modularisieren.
# Alle hier definierten Routen erhalten automatisch das Präfix "/api/v1_0".
# Das `tags`-Argument gruppiert die Endpunkte in der interaktiven API-Dokumentation.
router = APIRouter(prefix="/api/v1_0", tags=["Version 1.0"])


# --- 3. Kette von Abhängigkeiten (Dependencies) ---
# Diese Funktionen und Typ-Annotationen bilden ein System, das FastAPI anweist,
# wie es benötigte Objekte (wie den Service) für unsere Endpunkte erstellen soll.

# Abhängigkeit 3.1: Holt den OpenAI-Client
def get_openai_client(request: Request) -> AsyncOpenAI:
    """Holt die Singleton-Instanz des OpenAI-Clients aus dem App-State."""
    return request.app.state.openai_client

OpenAIClientDep = Annotated[AsyncOpenAI, Depends(get_openai_client)]


# Abhängigkeit 3.2: Holt den System-Prompt
def get_system_prompt(request: Request) -> str:
    """Holt den beim Start geladenen System-Prompt aus dem App-State."""
    return request.app.state.system_prompt

SystemPromptDep = Annotated[str, Depends(get_system_prompt)]


# Abhängigkeit 3.3: Erstellt den ArticleService
def get_article_service(
    client: OpenAIClientDep,
    prompt: SystemPromptDep
) -> ArticleService:
    """
    Erstellt eine Instanz des ArticleService.

    Diese Funktion ist selbst eine Abhängigkeit, die von anderen Abhängigkeiten
    (Client und Prompt) abhängt. FastAPI löst diese Kette automatisch auf.
    Sie holt die benötigten Konfigurationswerte aus dem globalen `settings`-Objekt.
    """
    model_name: str = settings.v1.gpt_model
    temp: float = settings.v1.temperature
    
    # Der Service wird hier "on-the-fly" für die Dauer der Anfrage erstellt.
    return ArticleService(
        client=client, 
        model=model_name, 
        temperature=temp, 
        system_prompt=prompt
    )

# Erstellt einen sauberen, wiederverwendbaren Typ für die Service-Abhängigkeit.
ArticleServiceDep = Annotated[ArticleService, Depends(get_article_service)]


# --- 4. API-Endpunkt ---
@router.post("/extract_metadata", response_model=ArticleOutput)
async def extract_article_metadata(
    article: ArticleInput,
    service: ArticleServiceDep,
    api_key: str = Depends(get_api_key)
):
    """
    Hauptendpunkt zum Analysieren und Vertaggen eines Artikels.

    - **POST /api/v1.0/extract_metadata**: Die HTTP-Methode und der Pfad.
    - **response_model=ArticleOutput**: Garantiert, dass die Antwort immer der
      Struktur des `ArticleOutput`-Modells entspricht. FastAPI validiert dies.
    - **article: ArticleInput**: FastAPI validiert den Request-Body automatisch
      gegen das `ArticleInput`-Modell.
    - **service: ArticleServiceDep**: Fordert eine fertige Instanz des
      `ArticleService` über das Dependency-Injection-System an.
    """
    # Die eigentliche Arbeit wird an den Service delegiert.
    # `article.model_dump()` konvertiert das Pydantic-Modell in ein Dictionary,
    # das der Service verarbeiten kann.
    result = await service.process_article(article.model_dump()) # type: ignore
    
    return result
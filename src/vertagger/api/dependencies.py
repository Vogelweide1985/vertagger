# -*- coding: utf-8 -*-

"""
Modul für wiederverwendbare FastAPI-Abhängigkeiten (Dependencies).

Dieses Modul zentralisiert die Logik zum Abrufen von gemeinsam genutzten Ressourcen,
wie zum Beispiel dem OpenAI-Client. Anstatt diese Logik in jedem Endpunkt neu
zu implementieren, definieren wir sie hier einmal und können sie dann überall
einfach "anfordern".

"""

# --- 1. Importe ---
from typing import Annotated
from fastapi import Depends, Request
from openai import AsyncOpenAI

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from ..config import settings

api_key_header = APIKeyHeader(name="X-API-Key")

# Abhängigkeits-Funktion zur Validierung des Schlüssels
def get_api_key(key: str = Security(api_key_header)):
    """
    Extrahiert den API-Schlüssel aus dem Header und validiert ihn.
    Gibt einen Fehler zurück, wenn der Schlüssel fehlt oder ungültig ist.
    """
    if key == settings.API_KEY:
        return key
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger oder fehlender API-Schlüssel",
        )

# --- 2. Abhängigkeits-Funktion (Dependency) ---
def get_openai_client(request: Request) -> AsyncOpenAI:
    """
    Eine einfache FastAPI-Abhängigkeit, die den OpenAI-Client zurückgibt.

    Sie greift auf den `app.state` zu, der über das `request`-Objekt verfügbar ist.
    Dort haben wir in der `main.py` (im Lifespan-Manager) die einmalig erstellte
    Client-Instanz gespeichert.

    Args:
        request: Das FastAPI Request-Objekt, das automatisch vom Framework
                 übergeben wird und Zugriff auf den App-State bietet.

    Returns:
        Die singleton Instanz des `AsyncOpenAI`-Clients.
    """
    return request.app.state.openai_client


# --- 3. Annotierter Abhängigkeits-Typ ---
# Dies ist eine modernere und klarere Art, Abhängigkeiten in FastAPI zu verwenden.
# `Annotated` erlaubt es uns, einen Typ-Hint (AsyncOpenAI) mit Metadaten
# (Depends(...)) zu kombinieren.
#
# Vorteil: In unseren Endpunkt-Funktionen können wir einfach `client: OpenAIClient`
# schreiben, anstatt `client: AsyncOpenAI = Depends(get_openai_client)`.
# Das ist kürzer, lesbarer und verbirgt die Implementierungsdetails.
OpenAIClient = Annotated[AsyncOpenAI, Depends(get_openai_client)]
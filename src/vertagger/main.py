# -*- coding: utf-8 -*-

"""
Hauptmodul der Vertagger API.

Dieses Skript initialisiert und konfiguriert die FastAPI-Anwendung.
Es ist verantwortlich für:
- Das Einrichten von Startup- und Shutdown-Events (Lifespan-Manager).
- Das Erstellen und Verwalten langlebiger Ressourcen wie dem OpenAI-Client.
- Das Laden und Bereitstellen von globalen Konfigurationen und Prompts.
- Das Einbinden der API-Router, welche die Endpunkte definieren.
"""

# --- 1. Standard- und Drittanbieter-Bibliotheken importieren ---
# Diese Importe stellen die grundlegenden Bausteine der Anwendung bereit.
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from openai import AsyncOpenAI
from opik.integrations.openai import track_openai

# --- 2. Interne Anwendungs-Importe ---
# Diese Importe verbinden die Teile unserer eigenen Anwendung miteinander.
from .__about__ import __version__
from .api.v1_0 import endpoints as v1_endpoints
from .config import settings


# --- 3. Hilfsfunktion zum Laden des System-Prompts ---
def load_prompt_on_startup() -> str:
    """
    Lädt alle Prompt-Teile aus dem prompts-Verzeichnis und fügt sie zusammen.

    Diese Funktion wird nur einmal beim Start der Anwendung ausgeführt. Das vermeidet
    wiederholte und langsame Festplattenzugriffe bei jedem API-Aufruf und verbessert
    somit die Performance erheblich.

    Die .txt-Dateien im prompts-Verzeichnis werden alphabetisch sortiert,
    sodass eine Nummerierung (z.B. 00_..., 01_...) die Reihenfolge steuert.

    Returns:
        Ein einziger String, der den vollständigen System-Prompt enthält.

    Raises:
        RuntimeError: Wenn das prompts-Verzeichnis leer ist oder nicht gefunden wird.
                      Verhindert, dass die API in einem fehlerhaften Zustand startet.
    """
    prompt_parts = []
    # Der Pfad wird dynamisch relativ zu dieser Datei konstruiert, um portabel zu bleiben.
    prompts_dir = Path(__file__).parent / "api/v1_0/prompts"
    
    sorted_prompt_files = sorted(prompts_dir.glob("*.txt"))

    if not sorted_prompt_files:
        raise RuntimeError(f"Keine Prompt-Dateien im Verzeichnis {prompts_dir} gefunden.")

    for file_path in sorted_prompt_files:
        prompt_parts.append(file_path.read_text(encoding="utf-8"))

    return "\n\n".join(prompt_parts)


# --- 4. Lifespan-Manager für Startup- und Shutdown-Logik ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Verwaltet Ressourcen, die während der gesamten Lebensdauer der App verfügbar sein sollen.

    Code vor dem `yield` wird beim Anwendungsstart ausgeführt.
    Code nach dem `yield` wird beim Herunterfahren der Anwendung ausgeführt.
    """
    # === STARTUP-LOGIK ===
    
    # Konfiguriere die Opik-Integration durch Setzen von Umgebungsvariablen.
    # Dies ist notwendig, damit Opik die Tracing-Daten dem korrekten Projekt zuordnen kann.
    os.environ["OPIK_API_KEY"] = settings.opik_api_key
    os.environ["OPIK_WORKSPACE"] = settings.opik_workspace
    os.environ["OPIK_PROJECT_NAME"] = settings.opik_project_name

    # Erstelle eine einzige, asynchrone Instanz des OpenAI-Clients.
    # Diese wird für alle API-Aufrufe wiederverwendet, um Netzwerk-Overhead zu minimieren.
    # `track_openai` umhüllt den Client, um alle Aufrufe automatisch an Opik zu melden.
    openai_client = track_openai(AsyncOpenAI(api_key=settings.openai_api_key))
    
    # Lade den System-Prompt einmalig, um I/O-Operationen während der Laufzeit zu vermeiden.
    system_prompt = load_prompt_on_startup()

    # Speichere den Client und den Prompt im "State" der App.
    # Dadurch können sie über das `request`-Objekt in den API-Endpunkten abgerufen werden.
    app.state.openai_client = openai_client
    app.state.system_prompt = system_prompt
    
    # An dieser Stelle wird die Kontrolle an die laufende Anwendung übergeben.
    yield
    
    # === SHUTDOWN-LOGIK ===
    # Schließe die Verbindung des OpenAI-Clients ordnungsgemäß, um Ressourcen freizugeben.
    await app.state.openai_client.close()


# --- 5. Initialisierung der FastAPI-Anwendung ---
# Dies ist das Hauptobjekt, das von einem ASGI-Server wie Uvicorn ausgeführt wird.
app = FastAPI(
    title="Vertagger API",
    description="Eine API zum Anreichern von Meta-Daten für Nachrichtenartikel.",
    version=__version__,
    lifespan=lifespan  # Registriert die oben definierte Startup/Shutdown-Logik.
)

# --- 6. Einbinden der API-Routen ---
# Anstatt alle Endpunkte in dieser Datei zu definieren, binden wir einen "Router" ein.
# Das hält die `main.py` sauber und strukturiert den Code modular nach API-Version.
app.include_router(v1_endpoints.router)


# --- 7. Root-Endpunkt ---
@app.get("/", tags=["General"])
def read_root():
    """
    Ein einfacher Willkommens-Endpunkt.

    Dient  als "Health Check", um zu prüfen, ob die API online und erreichbar ist.
    """
    return {"message": "Willkommen zur Vertagger API", "version": __version__}
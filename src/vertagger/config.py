# -*- coding: utf-8 -*-

"""
Zentrales Konfigurationsmodul für die Vertagger API.

Dieses Modul verwendet `pydantic-settings`, um alle Anwendungseinstellungen
aus einer .env-Datei und/oder Umgebungsvariablen zu laden und zu validieren.
Dies ermöglicht eine saubere Trennung von Code und Konfiguration.

Vorteile dieses Ansatzes:
- Alle Einstellungen sind an einem Ort gebündelt.
- Typsicherheit: Pydantic stellt sicher, dass Einstellungen den korrekten Datentyp haben (z.B. str, float).
- Validierung: Die Anwendung startet nicht, wenn wichtige Einstellungen fehlen.
- Einfache Verwaltung für verschiedene Umgebungen (Entwicklung, Test, Produktion).
"""

# --- 1. Importe aus Pydantic ---
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


# --- 2. Version-spezifische Konfiguration ---
class V1Config(BaseModel):
    """
    Definiert alle Einstellungen, die spezifisch für die API-Version v1.0 sind.

    Die Verwendung einer separaten Klasse pro Version (anstatt alle Einstellungen
    in eine große Klasse zu packen) sorgt für eine klare Struktur. Wenn eine
    v2.0-API mit anderen Modellen oder Parametern hinzukommt, kann einfach eine
    `V2Config`-Klasse ergänzt werden.

    `BaseModel` von Pydantic sorgt für die reine Datenvalidierung und -strukturierung.
    """
    gpt_model: str = "gpt-4o-mini"
    temperature: float = 0.0


# --- 3. Globale Anwendungskonfiguration ---
class AppSettings(BaseSettings):
    """
    Die Haupt-Konfigurationsklasse, die alle Einstellungen der App zusammenführt.

    Sie erbt von `BaseSettings`, was ihr die Fähigkeit verleiht, Werte automatisch
    aus Umgebungsvariablen oder einer .env-Datei zu laden.
    """
    
    # === Globale, erforderliche Einstellungen ===
    # Diese Felder haben keinen Standardwert. Das bedeutet, `pydantic-settings`
    # wirft einen Fehler beim Start, wenn sie nicht in der .env-Datei oder den
    # Umgebungsvariablen gefunden werden. Dies ist ein "Fail-Fast"-Mechanismus.
    openai_api_key: str
    opik_api_key: str 
    opik_workspace: str 
    opik_project_name: str 

    # === Verschachtelte Konfigurationen ===
    # Hier wird die versions-spezifische Konfiguration als "Namespace" eingebunden.
    # Im Code greift man darauf über `settings.v1.gpt_model` zu.
    v1: V1Config = V1Config()

    # === Konfiguration des Ladeverhaltens ===
    model_config = SettingsConfigDict(
        # Weist `BaseSettings` an, nach einer Datei namens `.env` im
        # Projektverzeichnis zu suchen und die darin enthaltenen Variablen zu laden.
        env_file=".env",
        # Setzt die Kodierung für die .env-Datei, um z.B. Umlaute zu unterstützen.
        env_file_encoding='utf-8'
    )


# --- 4. Erstellung der Singleton-Instanz ---
# Hier wird eine einzige, global verfügbare Instanz der Konfiguration erstellt.
# Andere Module (wie `main.py` oder `endpoints.py`) importieren dieses `settings`-Objekt,
# anstatt selbst eine Instanz zu erstellen (Singleton-Pattern).
#
# Der Kommentar `# type: ignore` ist notwendig, weil statische Code-Analyse-Tools
# (wie Pylance/Mypy) nicht erkennen, dass `BaseSettings` die fehlenden Argumente
# (z.B. `openai_api_key`) zur Laufzeit aus der .env-Datei lädt. Sie würden fälschlicherweise
# einen Fehler melden, den wir hiermit unterdrücken.
settings = AppSettings()  # type: ignore
import pytest
from unittest.mock import MagicMock, AsyncMock

# Importiere die Klasse, die wir testen wollen
from vertagger.api.v1_0.services import ArticleService
from vertagger.main import app # Importiere deine Haupt-App
from fastapi.testclient import TestClient



# Wir markieren alle Tests in dieser Datei, damit pytest weiß,
# dass sie asynchron sind.
pytestmark = pytest.mark.asyncio


async def test_process_article_success():
    """
    Testet, ob der ArticleService bei einer erfolgreichen OpenAI-Antwort
    das Ergebnis korrekt verarbeitet und die artikel_id hinzufügt.
    """
    # 1. Vorbereitung (Arrange)
    # Erstelle eine Attrappe (Mock) des OpenAI-Clients
    mock_openai_client = AsyncMock()
    
    # Definiere, was die Attrappe zurückgeben soll, wenn ihre Methode aufgerufen wird
    mock_openai_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(message=MagicMock(content='{"personen": ["Max Mustermann"], "zusammenfassung": "Ein Test"}'))
        ]
    )
    
    # Erstelle eine Instanz unseres Services mit der Attrappe
    service = ArticleService(
        client=mock_openai_client,
        model="test-model",
        temperature=0.1
    )
    
    # Test-Daten
    test_article = {"ArtikelID": 123, "Titel": "Test"}
    test_prompt = "Dies ist ein Test-Prompt"

    # 2. Ausführung (Act)
    # Rufe die Methode auf, die wir testen wollen
    result = await service.process_article(test_article)

    # 3. Überprüfung (Assert)
    # Prüfe, ob das Ergebnis unseren Erwartungen entspricht
    assert result is not None
    assert result["artikel_id"] == 123
    assert result["personen"] == ["Max Mustermann"]
    
    # Prüfe, ob der OpenAI-Client mit den richtigen Daten aufgerufen wurde
    mock_openai_client.chat.completions.create.assert_called_once()



# Erstelle einen Test-Service, der eine feste Antwort zurückgibt
class MockArticleService:
    async def process_article(self, article_data: dict) -> dict:
        return {
            "artikel_id": article_data.get("ArtikelID"),
            "personen": ["Mock Person"],
            "organisationen": [],
            "regionen": [],
            "stichwoerter": [],
            "zusammenfassung": "Mock Zusammenfassung",
            "userneeds": "Mock",
            "lebenswelt": "Mock",
            "lebenswelt_anteile": [],
            "iab_content_taxonomy": "Mock"
        }



# Überschreibe die Dependency für unsere Tests
# Dies ist der entscheidende Trick!
from src.vertagger.api.v1_0.endpoints import get_article_service

def override_get_article_service():
    return MockArticleService()

# Weise FastAPI an, unsere Überschreibung zu nutzen
app.dependency_overrides[get_article_service] = override_get_article_service


# Erstelle einen Client, um Anfragen an die App zu senden
client = TestClient(app)


def test_recode_endpoint_success():
    """
    Testet den /recode Endpunkt. Sendet eine Anfrage und prüft die Antwort.
    """
    # 1. Vorbereitung (Arrange)
    test_payload = {
        "ArtikelID": 999,
        "Titel": "Endpoint Test",
        "Subtitel": "Test",
        "Text": "Ein Test des Endpunkts"
    }

    # 2. Ausführung (Act)
    # Sende eine POST-Anfrage an den Endpunkt
    response = client.post("/api/v1.0/recode", json=test_payload)

    # 3. Überprüfung (Assert)
    # Prüfe den HTTP-Statuscode
    assert response.status_code == 200
    
    # Prüfe den Inhalt der JSON-Antwort
    data = response.json()
    assert data["artikel_id"] == 999
    assert data["personen"] == ["Mock Person"]
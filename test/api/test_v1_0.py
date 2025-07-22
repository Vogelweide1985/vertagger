import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Importiere nur noch die Klasse, die du im Unit-Test testen willst
from vertagger.api.v1_0.services import ArticleService


@pytest.mark.asyncio
async def test_process_article_success():
    """
    Testet den ArticleService isoliert (Unit-Test).
    """
    # 1. Vorbereitung (Arrange)
    mock_openai_client = AsyncMock()
    mock_openai_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(message=MagicMock(content='{"personen": ["Max Mustermann"], "zusammenfassung": "Ein Test"}'))
        ]
    )
    
    service = ArticleService(
        client=mock_openai_client,
        model="test-model",
        temperature=0.1
    )
    
    test_article = {"ArtikelID": 123, "Titel": "Test"}

    # 2. Ausführung (Act)
    result = await service.process_article(test_article)

    # 3. Überprüfung (Assert)
    assert result is not None
    assert result["artikel_id"] == 123
    assert result["personen"] == ["Max Mustermann"]
    mock_openai_client.chat.completions.create.assert_called_once()


def test_recode_endpoint_success(test_client: TestClient):
    """
    Testet den /recode Endpunkt mit dem vorbereiteten Test-Client (Integration-Test).
    Die Funktion "fordert" die 'test_client'-Fixture an, die in conftest.py definiert ist.
    """
    # 1. Vorbereitung (Arrange)
    test_payload = {
        "ArtikelID": "999",
        "Titel": "Endpoint Test",
        "Subtitel": "Test",
        "Text": "Ein Test des Endpunkts"
    }

    # 2. Ausführung (Act)
    # Verwende den übergebenen, fertig konfigurierten Test-Client
    response = test_client.post("/api/v1.0/recode", json=test_payload)
    print(response.status_code, response.json())
    # 3. Überprüfung (Assert)
    assert response.status_code == 200
    
    data = response.json()
    assert data["artikel_id"] == "999"
    assert data["personen"] == ["Mock Person"]
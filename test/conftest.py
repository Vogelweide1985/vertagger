import pytest
from fastapi.testclient import TestClient
from typing import Generator

# Importiere die Haupt-App und die zu überschreibende Abhängigkeit
from vertagger.main import app
from vertagger.api.v1_0.endpoints import get_article_service

# Definiere den Mock-Service direkt hier.
class MockArticleService:
    """Eine Attrappe für den ArticleService, die eine feste Antwort zurückgibt."""
    def __init__(self, *args, **kwargs):
        # Akzeptiert beliebige Argumente, tut aber nichts damit.
        pass

    async def process_article(self, article_data: dict) -> dict:
        # Gibt eine vollständige, valide ArticleOutput-Struktur zurück.
        return {
            "artikel_id": article_data.get("ArtikelID"),
            "personen": ["Mock Person"],
            "organisationen": ["Mock Org"],
            "regionen": ["Mock Region"],
            "stichwoerter": ["Mock"],
            "zusammenfassung": "Dies ist eine Mock-Zusammenfassung.",
            "userneeds": "Mock Need",
            "lebenswelt": "Mock Welt",
            "lebenswelt_anteile": [50, 50],
            "iab_content_taxonomy": "Mock Taxonomy"
        }

@pytest.fixture(scope="module")
def test_client() -> Generator[TestClient, None, None]:
    """
    Erstellt einen TestClient, der für die Dauer der Tests
    den echten ArticleService durch den MockArticleService ersetzt.
    """
    # Dies ist die Funktion, die anstelle der echten Getter-Funktion aufgerufen wird.
    def override_get_article_service():
        return MockArticleService()

    # Wende die Überschreibung an.
    app.dependency_overrides[get_article_service] = override_get_article_service

    # Erstelle den TestClient mit der manipulierten App.
    with TestClient(app) as client:
        # 'yield' gibt den Client an die Testfunktion weiter.
        yield client

    # Code nach dem 'yield' wird nach den Tests ausgeführt (Aufräumen).
    app.dependency_overrides.clear()
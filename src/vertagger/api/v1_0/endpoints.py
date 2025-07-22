from fastapi import APIRouter, Depends, Request
from pathlib import Path
from openai import AsyncOpenAI

from .models import ArticleInput, ArticleOutput
from .services import ArticleService
# Stelle sicher, dass du die lokale Config importierst
from .config import v1_config 

router = APIRouter(prefix="/api/v1.0", tags=["Version 1.0"])


# Diese neue "Getter"-Funktion holt den Client und erstellt den Service
def get_article_service(request: Request) -> ArticleService:
    # 1. Hole den globalen Client
    client: AsyncOpenAI = request.app.state.openai_client
    
    # 2. Hole das versions-spezifische Modell aus der lokalen Config
    model_name: str = v1_config.gpt_model
    
    # 3. Erstelle den Service mit beiden Argumenten
    return ArticleService(client=client, model=model_name)

@router.post("/recode", response_model=ArticleOutput)
async def recode(
    article: ArticleInput,
    # Depends ruft jetzt unsere neue Getter-Funktion auf
    service: ArticleService = Depends(get_article_service)
):
    print("--- 1. Recode-Endpunkt aufgerufen ---") # Hinzufügen
    prompt_path = Path(__file__).parent / "prompts" / "prompt.txt"
    prompt_text = prompt_path.read_text(encoding="utf-8")

    print("--- 2. Rufe jetzt den ArticleService auf ---") # Hinzufügen
    result = await service.process_article(article.model_dump(), prompt_text)
    
    print("--- 4. ArticleService hat geantwortet ---") # Hinzufügen
    return result
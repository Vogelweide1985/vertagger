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
    temp: float = v1_config.temperature
    
    # 3. Erstelle den Service mit beiden Argumenten
    return ArticleService(client=client, model=model_name, temperature=temp)

@router.post("/recode", response_model=ArticleOutput)
async def recode(
    article: ArticleInput,
    # Depends ruft jetzt unsere neue Getter-Funktion auf
    service: ArticleService = Depends(get_article_service)
):

    result = await service.process_article(article.model_dump())
    
    return result
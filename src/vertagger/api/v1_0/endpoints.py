from fastapi import APIRouter, Depends
from pathlib import Path
from .models import ArticleInput, ArticleOutput
from .services import ArticleService

router = APIRouter(prefix="/api/v1.0", tags=["Version 1.0"])

# FastAPI erstellt bei jeder Anfrage automatisch ein ArticleService-Objekt
# und "injiziert" es in die Funktion.
@router.post("/recode", response_model=ArticleOutput)
async def recode(
    article: ArticleInput,
    service: ArticleService = Depends(ArticleService) # Hier passiert die Magie
):
    prompt_path = Path(__file__).parent / "prompts" / "prompt.txt"
    prompt_text = prompt_path.read_text(encoding="utf-8")
    
    result = await service.process_article(article.model_dump(), prompt_text)
    return result
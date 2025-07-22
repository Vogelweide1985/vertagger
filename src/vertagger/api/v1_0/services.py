import json
from openai import AsyncOpenAI, RateLimitError
from fastapi import HTTPException
from pathlib import Path

CURRENT_DIR = Path(__file__).parent

class ArticleService:
    def __init__(self, client: AsyncOpenAI, model: str):
        self.client = client
        self.model = model

    def _load_prompt(self) -> str:
        """Lädt den Prompt aus der lokalen prompts/prompt.txt Datei."""
        try:
            prompt_path = CURRENT_DIR / "prompts" / "prompt.txt"
            return prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            # Dieser Fehler ist kritisch, da der Service ohne Prompt nicht arbeiten kann
            raise HTTPException(status_code=500, detail="Prompt-Datei für diesen Service nicht gefunden.")


    async def process_article(self, article_data: dict) -> dict:
        """Verarbeitet Artikel mit der Logik und dem Modell für v1.0."""
        
        # Lade den Prompt direkt hier
        prompt = self._load_prompt()

        input_text = f"Artikel-Daten: {json.dumps(article_data)}"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input_text}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
        except RateLimitError:
            raise HTTPException(status_code=429, detail="Rate limit exceeded.")

        result_str = response.choices[0].message.content
        if not result_str:
            raise HTTPException(status_code=500, detail="OpenAI returned an empty response.")

        result = json.loads(result_str)
        result["artikel_id"] = article_data.get("ArtikelID")
        return result
import json
from openai import AsyncOpenAI, RateLimitError
from fastapi import HTTPException
from pathlib import Path

CURRENT_DIR = Path(__file__).parent

class ArticleService:
    def __init__(self, client: AsyncOpenAI, model: str, temperature: float):
        self.client = client
        self.model = model
        self.temperature = temperature 

    def _load_prompt(self) -> str:
        """
        Lädt alle Prompt-Teile aus dem prompts-Verzeichnis,
        sortiert sie und fügt sie zu einem einzigen String zusammen.
        """
        prompt_parts = []
        prompts_dir = CURRENT_DIR / "prompts"
        
        # Finde alle .txt-Dateien und sortiere sie nach Namen (z.B. 00_..., 01_...)
        sorted_prompt_files = sorted(prompts_dir.glob("*.txt"))

        if not sorted_prompt_files:
            raise HTTPException(status_code=500, detail="Keine Prompt-Dateien im Verzeichnis gefunden.")

        for file_path in sorted_prompt_files:
            prompt_parts.append(file_path.read_text(encoding="utf-8"))
        
        # Füge alle Teile mit einem doppelten Zeilenumbruch zusammen
        return "\n\n".join(prompt_parts)


    async def process_article(self, article_data: dict) -> dict:
        """Verarbeitet Artikel mit der Logik und dem Modell für v1.0."""
        
        # Lade den Prompt direkt hier
        prompt = self._load_prompt()

        input_parts = ["Hier sind die zu verarbeitenden Artikel-Daten:"]
        for key, value in article_data.items():
            if value: # Nur Felder hinzufügen, die einen Wert haben
                input_parts.append(f"--- {key} ---\n{value}")
        
        input_text = "\n\n".join(input_parts)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input_text}
                ],
                temperature=self.temperature,
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
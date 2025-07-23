import json
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from openai import AsyncOpenAI, RateLimitError

# Opik-Importe
from opik import opik_context, track
from opik.evaluation.metrics import IsJson

CURRENT_DIR = Path(__file__).parent

VALID_USERNEEDS = {
    "Informieren", "Einordnen", "Beteiligen", "Unterhalten",
    "Hilfe geben", "Erklären", "Inspirieren", "Vernetzen"
}

class ArticleService:
    def __init__(self, client: AsyncOpenAI, model: str, temperature: float):
        self.client = client
        self.model = model
        self.temperature = temperature

    def _validate_and_score_output(self, llm_output: str) -> Optional[dict]:
        """
        Validiert den LLM-Output mit Opik-Metriken und gibt das geparste JSON zurück.

        Diese Methode prüft, ob der Output valides JSON ist und ob der
        'userneeds'-Wert korrekt ist. Die Ergebnisse werden als Feedback Scores
        an den aktuellen Opik-Trace gesendet.

        Returns:
            Ein Dictionary mit dem geparsten JSON bei Erfolg, sonst None.
        """
        feedback_scores = []

        # 1. Metrik: Ist der Output valides JSON?
        json_score = IsJson().score(output=llm_output)
        score_dict = {"name": json_score.name, "value": json_score.value}
        if json_score.reason:
            score_dict["reason"] = json_score.reason

        feedback_scores.append(score_dict)

        # Guard Clause: Wenn kein valides JSON, brechen wir hier ab.
        if json_score.value != 1.0:
            opik_context.update_current_trace(feedback_scores=feedback_scores)
            return None  # Frühzeitiger Ausstieg

        # 2. Metrik: Ist 'userneeds' korrekt?
        # Dieser Code wird nur bei validem JSON erreicht.
        data = json.loads(llm_output)
        userneed = data.get("userneeds")

        if userneed in VALID_USERNEEDS:
            feedback_scores.append({"name": "is_valid_userneed", "value": 1.0})
        else:
            feedback_scores.append({
                "name": "is_valid_userneed",
                "value": 0.0,
                "reason": f"Ungültiger Wert: {userneed}"
            })
        
        opik_context.update_current_trace(feedback_scores=feedback_scores)
            
        return data

    @track
    async def process_article(self, article_data: dict) -> dict:
        """Verarbeitet einen Artikel und gibt ein validiertes Ergebnis zurück."""
        
        # 1. Vorbereitung: Prompt und Input erstellen
        prompt = self._load_prompt()
        input_text = self._prepare_input_text(article_data)

        # 2. LLM-Aufruf
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

        # 3. Validierung und Scoring durch die neue Methode
        validated_result = self._validate_and_score_output(result_str)
        
        # 4. Ergebnis verarbeiten
        if validated_result is None:
            raise HTTPException(status_code=500, detail="LLM-Antwort war kein valides JSON.")
            
        validated_result["artikel_id"] = article_data.get("ArtikelID")
        return validated_result

    
    def _prepare_input_text(self, article_data: dict) -> str:
        """Stellt den Input-String für das LLM aus den Artikeldaten zusammen."""
        input_parts = ["Hier sind die zu verarbeitenden Artikel-Daten:"]
        for key, value in article_data.items():
            if value:
                input_parts.append(f"--- {key} ---\n{value}")
        return "\n\n".join(input_parts)

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

        return "\n\n".join(prompt_parts)
# -*- coding: utf-8 -*-

"""
Modul für die Geschäftslogik (Service Layer) der API.

Die `ArticleService`-Klasse kapselt die gesamte Logik für die Verarbeitung
eines Artikels. Sie ist dafür verantwortlich, mit externen Diensten wie der
OpenAI-API zu kommunizieren und deren Ergebnisse zu validieren.
"""

# --- 1. Importe ---
import json
from typing import Optional

from fastapi import HTTPException
from openai import AsyncOpenAI, RateLimitError

# Opik wird für das Tracing und die Evaluierung der LLM-Aufrufe verwendet.
from opik import opik_context, track
from opik.evaluation.metrics import IsJson


# --- 2. Konstanten ---
# Ein Set mit erlaubten Werten für das 'userneeds'-Feld.
# Die Verwendung eines Sets (`{...}`) ist hier performanter für die
# "in"-Prüfung als eine Liste (`[...]`).
VALID_USERNEEDS = {
    "Informieren", "Einordnen", "Beteiligen", "Unterhalten",
    "Hilfe geben", "Erklären", "Inspirieren", "Vernetzen"
}

VALID_AUDIENCES = {
    "Foodies", "Gesundheitsbewusste", "Kunden und Arbeitnehmer",
    "Mieter und Hausbesitzer", "Verkehrsteilnehmende", "Junge Familien",
    "Freizeitjunkies", "Naturliebende", "Sportfans", "Sporttreibende",
    "Voyeuristen", "Nostalgiker", "Keine weitere"
}

# --- 3. Die Service-Klasse ---
class ArticleService:
    """
    Kapselt die Logik zur Anreicherung eines Artikels mit Metadaten.
    """
    def __init__(self, client: AsyncOpenAI, model: str, temperature: float, system_prompt: str):
        """
        Initialisiert den Service mit allen benötigten Abhängigkeiten.

        Diese werden per Dependency Injection vom `endpoints`-Modul übergeben.
        """
        self.client = client
        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt

    def _validate_and_score_output(self, llm_output: str) -> Optional[dict]:
        """
        Validiert die LLM-Antwort und sendet Feedback-Scores an Opik.

        Diese private Hilfsmethode hat zwei Hauptaufgaben:
        1.  Prüfen, ob die Antwort vom LLM eine valide Struktur hat (z.B. korrektes JSON).
        2.  Prüfen, ob die Inhalte fachlichen Regeln entsprechen (z.B. gültiger Userneed).
        3.  Die Ergebnisse dieser Prüfungen als "Feedback" an Opik senden, um die
            Qualität der LLM-Antworten zu überwachen.

        Args:
            llm_output: Der rohe String, der von der OpenAI-API zurückgegeben wurde.

        Returns:
            Ein Dictionary mit den geparsten Daten bei Erfolg, andernfalls `None`.
        """
        feedback_scores = []

        # Metrik 1: Ist die Antwort valides JSON?
        json_score = IsJson().score(output=llm_output)
        score_dict = {"name": json_score.name, "value": json_score.value}
        if json_score.reason:
            score_dict["reason"] = json_score.reason
        feedback_scores.append(score_dict)

        # "Guard Clause": Wenn die Antwort kein valides JSON ist, brechen wir sofort ab.
        # Das verhindert Fehler im nachfolgenden Code.
        if json_score.value != 1.0:
            opik_context.update_current_trace(feedback_scores=feedback_scores)
            return None

        # Metrik 2: Ist der Wert für 'userneeds' einer der erlaubten Werte?
        # Dieser Code wird nur ausgeführt, wenn die JSON-Validierung erfolgreich war.
        data = json.loads(llm_output)
        userneed = data.get("userneeds")

        if userneed in VALID_USERNEEDS:
            feedback_scores.append({"name": "is_valid_userneed", "value": 1.0})
        else:
            feedback_scores.append({
                "name": "is_valid_userneed",
                "value": 0.0,
                "reason": f"Ungültiger Wert: '{userneed}'. Erwartet wurde einer aus {VALID_USERNEEDS}."
            })
        
        # Metrik 3: Ist jede Audience in der Liste ein erlaubter Wert?
        audiences = data.get("audiences", [])
        
        # Prüfen, ob alle extrahierten Audiences in der Whitelist enthalten sind
        invalid_found = [a for a in audiences if a not in VALID_AUDIENCES]
        
        if not invalid_found and len(audiences) > 0:
            feedback_scores.append({"name": "is_valid_audience", "value": 1.0})
        else:
            reason = f"Ungültige Werte gefunden: {invalid_found}" if invalid_found else "Keine Audiences extrahiert."
            feedback_scores.append({
                "name": "is_valid_audience",
                "value": 0.0,
                "reason": reason
            })
        
        # Sende alle gesammelten Scores an den aktuellen Opik-Trace.
        opik_context.update_current_trace(feedback_scores=feedback_scores)
            
        return data

    @track  # Der `@track`-Dekorator von Opik startet automatisch einen neuen Trace für diese Methode.
    async def process_article(self, article_data: dict) -> dict:
        """
        Orchestriert den gesamten Prozess der Artikelverarbeitung.

        Dies ist die öffentliche Hauptmethode des Services.

        Args:
            article_data: Ein Dictionary mit den Artikel-Daten aus der API-Anfrage.

        Returns:
            Ein Dictionary mit den validierten und angereicherten Metadaten.

        Raises:
            HTTPException: Bei Fehlern wie Rate-Limits, leeren Antworten oder
                           fehlgeschlagener Validierung.
        """
        
        # Schritt 1: Bereite den Input für das LLM vor.
        user_input_text = self._prepare_input_text(article_data)

        # Schritt 2: Rufe die OpenAI Chat Completion API auf.
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_input_text}
                ],
                temperature=self.temperature,
                # Erzwingt, dass das LLM eine JSON-Antwort generiert.
                response_format={"type": "json_object"}
            )
        except RateLimitError:
            # Fange den spezifischen Fehler für Rate-Limits ab und gib einen
            # passenden HTTP-Statuscode (429) zurück.
            raise HTTPException(status_code=429, detail="OpenAI Rate Limit überschritten.")

        result_str = response.choices[0].message.content
        if not result_str:
            raise HTTPException(status_code=500, detail="OpenAI hat eine leere Antwort zurückgegeben.")

        # Schritt 3: Validiere die rohe Antwort des LLMs.
        validated_result = self._validate_and_score_output(result_str)
        
        # Schritt 4: Verarbeite das validierte Ergebnis und gib es zurück.
        if validated_result is None:
            raise HTTPException(status_code=500, detail="LLM-Antwort war kein valides JSON.")
            
        # Füge die ursprüngliche ArtikelID hinzu, um die Antwort der Anfrage zuordnen zu können.
        validated_result["artikel_id"] = article_data.get("ArtikelID")
        return validated_result

    
    def _prepare_input_text(self, article_data: dict) -> str:
        """
        Stellt aus den Artikel-Daten einen formatierten String für das LLM zusammen.

        Diese Methode stellt sicher, dass das LLM alle relevanten Informationen
        in einem klar strukturierten Format erhält.
        """
        input_parts = ["Hier sind die zu verarbeitenden Artikel-Daten:"]
        
        # Definiere die Reihenfolge der Felder, um Konsistenz zu gewährleisten.
        # (inklusive des neuen 'Teaser'-Feldes)
        field_order = ["ArtikelID", "Titel", "Subtitel", "Teaser", "Text"]

        for key in field_order:
            value = article_data.get(key)
            # Füge nur Felder hinzu, die auch einen Wert haben.
            if value:
                input_parts.append(f"--- {key} ---\n{value}")
                
        return "\n\n".join(input_parts)
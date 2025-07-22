import json
from openai import AsyncOpenAI, RateLimitError
from fastapi import HTTPException


class ArticleService:
    def __init__(self, client: AsyncOpenAI, model: str):
        self.client = client
        self.model = model

    async def process_article(self, article_data: dict, prompt: str) -> dict:

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
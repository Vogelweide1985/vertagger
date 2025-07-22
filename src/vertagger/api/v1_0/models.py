from pydantic import BaseModel

class ArticleInput(BaseModel):
    ArtikelID: str
    Titel: str
    Subtitel: str | None = None
    Text: str | None = None

class ArticleOutput(BaseModel):
    artikel_id: str
    personen: list[str]
    organisationen: list[str]
    regionen: list[str]
    stichwoerter: list[str]
    zusammenfassung: str
    userneeds: str
    lebenswelt: str
    lebenswelt_anteile: list[int]
    iab_content_taxonomy: str
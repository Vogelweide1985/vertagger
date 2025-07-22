from pydantic import BaseModel

class ArticleInput(BaseModel):
    ArtikelID: int
    Titel: str
    Subtitel: str
    Text: str

class ArticleOutput(BaseModel):
    artikel_id: int
    personen: list[str]
    organisationen: list[str]
    regionen: list[str]
    stichwoerter: list[str]
    zusammenfassung: str
    userneeds: str
    lebenswelt: str
    lebenswelt_anteile: list[int]
    iab_content_taxonomy: str
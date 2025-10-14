from pydantic import BaseModel

class ArticleInput(BaseModel):
    """
    Definiert die erwartete Datenstruktur für einen Artikel, der an die
    API gesendet wird (z.B. im Body einer POST-Anfrage).
    """
    ArtikelID: str
    Titel: str
    Subtitel: str | None = None
    Teaser: str | None = None
    Text: str | None = None

class ArticleOutput(BaseModel):
    """
    Definiert die garantierte Datenstruktur der JSON-Antwort, die von der
    API zurückgesendet wird.

    Durch die Verwendung dieses Modells als `response_model` in den Endpunkten
    stellt FastAPI sicher, dass die Antwort immer diesem Schema entspricht.
    """
    artikel_id: str
    personen: list[str]
    organisationen: list[str]
    regionen: list[str]
    stichwoerter: list[str]
    zusammenfassung: str
    userneeds: str
    audiences: list[str]
    audience_1_begruendung: str
    audience_2_begruendung: str
    audience_3_begruendung: str
    iab_content_taxonomy: str
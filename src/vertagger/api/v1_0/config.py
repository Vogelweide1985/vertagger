from pydantic import BaseModel

# Diese Klasse ist NUR für version-spezifische Einstellungen
class VersionConfig(BaseModel):

    gpt_model: str = "gpt-4o-mini"
    temperature: float = 0.0

# Wir erstellen eine Instanz, die wir im v1_0-Modul verwenden können
v1_config = VersionConfig()
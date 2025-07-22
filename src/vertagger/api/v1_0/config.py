from pydantic import BaseModel

# Diese Klasse ist NUR für version-spezifische Einstellungen
class VersionConfig(BaseModel):
    # Der Modellname ist hier fest für v1.0 definiert.
    # Er muss nicht aus .env kommen, da er Teil des v1.0-Designs ist.
    gpt_model: str = "gpt-4o"

# Wir erstellen eine Instanz, die wir im v1_0-Modul verwenden können
v1_config = VersionConfig()
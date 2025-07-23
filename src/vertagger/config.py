from pydantic_settings import BaseSettings, SettingsConfigDict

# Diese Klasse ist NUR für globale App-Einstellungen
class GlobalSettings(BaseSettings):
    # Sie lädt nur den einen Key, den die App zum Starten braucht
    openai_api_key: str
    opik_api_key: str 
    opik_workspace: str 
    opik_project_name: str 
    model_config = SettingsConfigDict(env_file=".env")

# Wir erstellen eine Instanz, die wir in main.py importieren können
global_settings = GlobalSettings() # type: ignore
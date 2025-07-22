from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Die Variable wird automatisch aus der .env-Datei gelesen
    openai_api_key: str
    gpt_model: str 
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings() # type: ignore
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    DATABASE_URL: str
    GOOGLE_API_KEY : str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()


os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
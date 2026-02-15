from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    DATABASE_URL: str
    GOOGLE_API_KEY : str
    TAVILY_API_KEY : str
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()


os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY
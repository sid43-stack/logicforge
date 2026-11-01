from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

    PROJECT_NAME: str = "NetSage"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # SQLite Database URL
    DATABASE_URL: str = "sqlite:///./netsage.db"
    
    # CORS Origins (Allow local React Vite frontend)
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


settings = Settings()

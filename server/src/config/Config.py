from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Config(BaseSettings):
    """Config class for application settings"""
    MONGODB_URL: str = Field(..., description="MongoDB String")
    DATABASE_NAME: str = Field(..., description="Database Name")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid",
        str_strip_whitespace= True
    )

@lru_cache
def get_config() -> Config:
    """Return singleton instance of Config"""
    return Config()

settings = get_config()
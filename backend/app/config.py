from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "SupplyChain-AgenticHub"
    APP_ENV: str = "development"
    PORT: int = 8008
    HOST: str = "0.0.0.0"
    OPENAI_API_KEY: str = ""
    FAST_PATH_LATENCY_THRESHOLD_MS: float = 200.0
    CONFIDENCE_THRESHOLD: float = 0.85
    ENABLE_MOCK_FALLBACK: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

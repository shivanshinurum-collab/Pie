import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

# Define project base directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # App General Settings
    APP_NAME: str = "AI News Meme Engine"
    ENV: str = "development"
    DEBUG: bool = True
    
    # Storage settings
    STORAGE_TYPE: str = "local"  # 'local' or 's3' or 'gcs'
    CLOUD_STORAGE_BUCKET: str = "ai-news-meme-engine-bucket"
    LOCAL_STORAGE_DIR: str = str(BASE_DIR / "storage")
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/news_meme_db"
    
    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API Keys & Third Party
    NEWS_API_KEY: str = ""
    GNEWS_API_KEY: str = ""
    CURRENTS_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    REPLICATE_API_KEY: str = ""  # For FLUX/SD image generation
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"
    
    # Social Media / Publishing
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""
    BRAND_LOGO_PATH: str = ""  # Path to brand logo overlaid on memes
    
    # Pipelines Scheduler (in minutes)
    NEWS_CHECK_INTERVAL_MINS: int = 15
    MEME_POTENTIAL_THRESHOLD: int = 70
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings
settings = Settings()

# Create storage directory if local
if settings.STORAGE_TYPE == "local":
    Path(settings.LOCAL_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    (Path(settings.LOCAL_STORAGE_DIR) / "images").mkdir(exist_ok=True)
    (Path(settings.LOCAL_STORAGE_DIR) / "memes").mkdir(exist_ok=True)
    (Path(settings.LOCAL_STORAGE_DIR) / "reels").mkdir(exist_ok=True)

# Logging Setup
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(settings.LOCAL_STORAGE_DIR, "engine.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger(settings.APP_NAME)
logger.info(f"Initialized configuration in {settings.ENV} mode.")

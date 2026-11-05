import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

    PIPELINE_ASYNC = True
    SCORING_CONCURRENCY = 5
    STALE_RUN_MINUTES = 15

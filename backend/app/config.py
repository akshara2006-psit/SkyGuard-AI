import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "database")
DEFAULT_DB_PATH = os.path.join(DB_DIR, "skyguard.db").replace(os.sep, "/")
DEFAULT_MODEL_PATH = os.path.join(DB_DIR, "isolation_forest.pkl").replace(os.sep, "/")

def _anchor_db_url(url: str) -> str:
    for prefix in ("sqlite+aiosqlite:///", "sqlite:///"):
        if url.startswith(prefix):
            db_sub = url[len(prefix):]
            if not os.path.isabs(db_sub):
                abs_db = os.path.join(DB_DIR, os.path.basename(db_sub)).replace(os.sep, "/")
                return f"{prefix}{abs_db}"
    return url

def _anchor_model_path(path: str) -> str:
    if not os.path.isabs(path):
        return os.path.join(DB_DIR, os.path.basename(path)).replace(os.sep, "/")
    return path

class Settings:
    DATABASE_URL: str = _anchor_db_url(os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"))
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    MODEL_PATH: str = _anchor_model_path(os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH))
    ANOMALY_THRESHOLD: float = float(os.getenv("ANOMALY_THRESHOLD", "-0.1"))
    MIN_TRAINING_SAMPLES: int = int(os.getenv("MIN_TRAINING_SAMPLES", "100"))
    SIM_INTERVAL_SECONDS: float = float(os.getenv("SIM_INTERVAL_SECONDS", "5"))

settings = Settings()

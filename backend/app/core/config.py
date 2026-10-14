from pathlib import Path
import os
from dotenv import load_dotenv

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Load .env file from backend directory or project root
dotenv_path = BASE_DIR / ".env"
if not dotenv_path.exists():
    dotenv_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=dotenv_path)

class Settings:
    PROJECT_NAME: str = "Hotel Discovery API"
    VERSION: str = "1.0.0"
    
    BASE_DIR: Path = BASE_DIR
    DB_PATH: Path = Path(os.getenv("DB_PATH", str(BASE_DIR / "hotel_discovery.db")))
    
    # Geoapify credentials
    GEOAPIFY_API_KEY: str = os.getenv("GEOAPIFY_API_KEY", "").strip()
    
    # Search parameters
    DEFAULT_RADIUS_METERS: int = 5000  # 5 km radius per prompt requirements
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

settings = Settings()

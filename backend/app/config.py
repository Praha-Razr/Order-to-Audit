import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Order-to-Audit System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Defaults to SQLite in current working dir, or PostgreSQL via env var
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./order_to_audit.db")
    
    # Factory State for GST determination
    FACTORY_STATE: str = "Tamil Nadu"
    FACTORY_STATE_CODE: str = "33"
    FACTORY_GSTIN: str = "33AAAAA0000A1Z5"
    
    # Production tolerance for variance flagging (default 3% per problem statement)
    VARIANCE_TOLERANCE_PERCENT: float = 3.0

settings = Settings()

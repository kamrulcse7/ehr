from pathlib import Path
from typing import List, Optional, Any
import os

from pydantic import EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# === Load App-specific .env (highest priority) ===
_APP_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
if _APP_ENV_PATH.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=_APP_ENV_PATH, override=True)

# === Load Root .env (fallback) ===
_ROOT_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
if _ROOT_ENV_PATH.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=_ROOT_ENV_PATH, override=False)


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @classmethod
    def _get_prefix(cls) -> str:
        app_dir = Path(__file__).parents[1]
        return app_dir.name.upper().replace("-", "_")

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        prefix = self._get_prefix()

        ## App-specific env override (e.g., FILE_HUB_MYSQL_USER)
        # for field_name in AppSettings.model_fields:
        #     key = f"{prefix}_{field_name}"
        #     value = os.getenv(key)
        #     if value is not None:
        #         setattr(self, field_name, self._cast(field_name, value))

        ## Global env fallback (e.g., MYSQL_USER)
        # for field_name in AppSettings.model_fields:
        #     current = getattr(self, field_name)
        #     if current in ("", None, "root"):
        #         global_val = os.getenv(field_name)
        #         if global_val is not None:
        #             setattr(self, field_name, self._cast(field_name, global_val))

    def _cast(self, field_name: str, raw: str):
        field = AppSettings.model_fields[field_name]
        ann = field.annotation

        if ann == List[str]:
            return [x.strip() for x in raw.split(",") if x.strip()]
        if ann == int:
            return int(raw)
        if ann == bool:
            return raw.lower() in ("true", "1", "yes", "on")
        if ann == Optional[str]:
            return raw.strip() if raw.strip() else None
        return raw

    ### Basic app info
    APP_NAME: str = "HRMS"
    APP_VERSION: str = "1.0.0"
    SYSTEM_COMPANY_NAME: str = "Eon Systems"
    ENV: str = "production"  # development / production
    
    ## Database
    MYSQL_USER: str = "root"
    MYSQL_PASS: str = ""
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: str = "3306"
    MYSQL_DB_NAME: str = "badc"
    
    ## Database
    MYSQL_REPLICA_USER: str = "root"
    MYSQL_REPLICA_PASS: str = ""
    MYSQL_REPLICA_HOST: str = "localhost"
    MYSQL_REPLICA_PORT: str = "3306"
    MYSQL_REPLICA_DB_NAME: str = "badc"

    ## Timezone / Time offset
    TIMEZONE: str = "Asia/Dhaka"
    TIMEZONE_OFFSET_HOURS: int = 0
    TIMEZONE_OFFSET_MINUTES: int = 0
    TIMEZONE_OFFSET_SECONDS: int = 0

    # CORS / Cross-Origin Resource Sharing
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    BACKEND_CORS_ALLOW_CREDENTIALS: bool = True
    BACKEND_CORS_ALLOW_METHODS: List[str] = ["*"]
    BACKEND_CORS_ALLOW_HEADERS: List[str] = ["*"]

    ## Security
    SECRET_KEY: Optional[str] = "S0PuTBofBUFZz3nMNZCjKoWLbF"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ALGORITHM: str = "HS256"
    SAME_SITE: str = "Lax"
    WEB_SESSION_EXPIRE_MINUTES: int = 60

    MAX_FAILED_LOGIN_ATTEMPTS: int = 3
    ACCOUNT_LOCKOUT_MINUTES: int = 1

    ## Email / SMTP
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[EmailStr] = None

    ## FTP
    FTP_HOST: Optional[str] = None
    FTP_PORT: int = 21
    FTP_USER: Optional[str] = None
    FTP_PASSWORD: Optional[str] = None
    
    ## Redis / Cache
    REDIS_URL: Optional[str] = None

    ## Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    ## Rate limiting
    RATE_LIMIT: Optional[int] = None

    ## CORS Origins validator
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and v.strip():
            return [i.strip() for i in v.split(",") if i.strip()]
        return v if isinstance(v, list) else []


settings = AppSettings()

__all__ = ["settings", "AppSettings"]
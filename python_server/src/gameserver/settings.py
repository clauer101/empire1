"""Central settings — loaded from environment / .env file.

Every env var that changes between dev/staging/prod lives here.
Add new vars to this file AND to .env.example.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Site identity — used for SEO meta tags and canonical URLs
    site_url: str = "http://localhost:8000"
    site_name: str = "Relics & Rockets"

    # Auth
    jwt_secret: str  # required — no default, fails fast on missing

    # Optional TLS / VAPID paths (operational — not used by game logic)
    tls_cert_path: str = ""
    tls_key_path: str = ""
    vapid_private_key_path: str = ""
    vapid_public_key_path: str = ""


# Module-level singleton — import this everywhere
settings = Settings()  # type: ignore[call-arg]  # jwt_secret loaded from env at runtime

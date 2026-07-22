from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    database_url: str

    # Google
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None
    sheets_tasks_id: str | None = None
    sheets_people_id: str | None = None

    # Gemini
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-flash-latest"

    # Aplikacja
    token_encryption_key: str | None = None
    session_secret: str | None = None
    timezone: str = "Europe/Warsaw"
    reminder_hour: int = 8
    reminder_days_ahead: int = 2
    frontend_origin: str = "http://localhost:5173"
    supabase_audio_bucket: str = "meeting-audio"
    # Wyłącz w developmencie przy uruchamianiu `uvicorn --reload` — reloader
    # potrafi odpalić lifespan (a więc i scheduler) dwukrotnie, co bez tej
    # flagi skutkuje podwójną wysyłką przypomnień (SPEC.md §7, etap 8).
    scheduler_enabled: bool = True


settings = Settings()

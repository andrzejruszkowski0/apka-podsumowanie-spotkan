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
    # SPEC.md §1/§10.4 mówi o "text-embedding-004", ale ten model nie istnieje
    # już pod aktualnym API (404 NOT_FOUND — Google go wycofał). Zastępca to
    # gemini-embedding-001, poproszony o output_dimensionality=768, żeby
    # dopasować się do istniejącej kolumny decision.embedding vector(768)
    # i indeksu ivfflat zbudowanego pod ten wymiar (migracja 0001).
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_embedding_dimensions: int = 768

    # Aplikacja
    token_encryption_key: str | None = None
    session_secret: str | None = None
    timezone: str = "Europe/Warsaw"
    reminder_hour: int = 8
    reminder_days_ahead: int = 2
    frontend_origin: str = "http://localhost:5173"
    # Frontend i backend na osobnych domenach (np. Vercel + Render) to cookie
    # sesji cross-site z perspektywy przeglądarki — wymaga SameSite=None i
    # Secure (możliwe tylko pod HTTPS). Lokalnie (http://localhost) zostaw
    # False, inaczej przeglądarka odrzuci cookie w ogóle.
    session_cookie_secure: bool = False
    supabase_audio_bucket: str = "meeting-audio"
    # Wyłącz w developmencie przy uruchamianiu `uvicorn --reload` — reloader
    # potrafi odpalić lifespan (a więc i scheduler) dwukrotnie, co bez tej
    # flagi skutkuje podwójną wysyłką przypomnień (SPEC.md §7, etap 8).
    scheduler_enabled: bool = True


settings = Settings()

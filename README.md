# Aplikacja do analizy spotkań

Zobacz [SPEC.md](SPEC.md) i [ETAPY.md](ETAPY.md) dla pełnej specyfikacji i planu wdrożenia.

## Etap 1 — uruchomienie lokalne

### Backend

```
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # uzupełnij DATABASE_URL swoim connection stringiem z Supabase
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`DATABASE_URL` w Supabase: Project Settings → Database → Connection string (tryb "Session" lub "Transaction pooler", z hasłem). Format dla SQLAlchemy + psycopg 3:

```
postgresql+psycopg://postgres:<hasło>@<host>:5432/postgres
```

Sprawdzenie: `curl http://127.0.0.1:8000/health` → `{"status":"ok"}`.

### Frontend

```
cd frontend
npm install
npm run dev
```

Otwórz `http://localhost:5173` — ekran powinien pokazać "ok" pobrane z backendu przez proxy Vite.

# Aplikacja do analizy spotkań

Zamienia nagranie (lub tekst) spotkania w konkretne zadania z przypisaną
odpowiedzialnością (RACI), pilnuje terminów mailowymi przypomnieniami
i prowadzi przeszukiwalny rejestr decyzji biznesowych.

Przewodnik jak korzystać z aplikacji krok po kroku: **[PRZEWODNIK_UZYTKOWNIKA.md](PRZEWODNIK_UZYTKOWNIKA.md)**.
Pełny opis funkcji, decyzji architektonicznych i uzasadnień: **[OPIS_FINALNY.md](OPIS_FINALNY.md)**.

## Wersja demo (online)

- Frontend: https://apka-podsumowanie-spotkan.vercel.app
- Backend: https://apka-podsumowanie-spotkan-backend.onrender.com (`/health`)

Baza demo zawiera w pełni fikcyjne dane testowe, odizolowane od danych
produkcyjnych. Dostęp wymaga dwóch zestawów danych logowania (Supabase Auth +
wspólne konto Google) — poproś o nie właściciela repo. Backend na darmowym
planie Render usypia po ~15 min bezczynności — pierwsze wejście po przerwie
może potrwać 30-60s. Szczegóły wdrożenia: **[DEPLOY.md](DEPLOY.md)**.

## Stos technologiczny

| Warstwa | Technologia |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, Alembic |
| Baza i storage | Supabase (Postgres + pgvector + Storage) |
| Frontend | React (Vite), TypeScript, Tailwind |
| AI | Gemini (transkrypcja audio, ekstrakcja RACI/decyzji, embeddingi) |
| Integracje | Google OAuth, Gmail API, Google Sheets API |
| Auth appki | Supabase Auth (ekran logowania email+hasło) |
| Scheduler | APScheduler (przypomnienia mailowe) |
| Hosting demo | Render (backend) + Vercel (frontend) |

## Struktura repo

```
backend/    FastAPI, modele, migracje Alembic, testy
frontend/   React + Vite
```

## Uruchomienie lokalne

### Backend

```
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # uzupełnij DATABASE_URL, klucze Google/Gemini itd.
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`DATABASE_URL` z Supabase: Project Settings → Database → Connection string,
format dla SQLAlchemy + psycopg 3:

```
postgresql+psycopg://postgres:<hasło>@<host>:5432/postgres
```

Sprawdzenie: `curl http://127.0.0.1:8000/health` → `{"status":"ok"}`.

Konfiguracja Google OAuth (Client ID/Secret, redirect URI, scope'y Gmail/Sheets)
i generowanie kluczy aplikacji (`TOKEN_ENCRYPTION_KEY`, `SESSION_SECRET`) — patrz
**[GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md)**.

### Frontend

```
cd frontend
npm install
npm run dev
```

Otwórz `http://localhost:5173`.

## Dokumentacja

| Plik | Zawartość |
|---|---|
| [PRZEWODNIK_UZYTKOWNIKA.md](PRZEWODNIK_UZYTKOWNIKA.md) | Jak korzystać z aplikacji krok po kroku, lista funkcji |
| [OPIS_FINALNY.md](OPIS_FINALNY.md) | Pełny opis funkcji, uzasadnienia decyzji, stos, koszty, ryzyka |
| [SPEC.md](SPEC.md) | Specyfikacja techniczna, model danych, kontrakty API, prompty AI |
| [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md) | Konfiguracja Google Cloud Console krok po kroku + weryfikacja |
| [ETAPY.md](ETAPY.md) | Prompty/plan wdrożeniowy po etapach |
| [OGRANICZENIA.md](OGRANICZENIA.md) | Świadome ograniczenia i rzeczy wymagające cyklicznej uwagi |
| [DEPLOY.md](DEPLOY.md) | Wdrożenie wersji demo (Render + Vercel) |

## Status

Wszystkie 10 etapów z `ETAPY.md` zaimplementowane. Wersja demo wdrożona
i zweryfikowana end-to-end (logowanie, upload, weryfikacja, eksport, briefing,
drafty maili). Szczegóły ograniczeń: `OGRANICZENIA.md`.

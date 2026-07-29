# Wdrożenie wersji podglądowej (demo dla jurorów / kolegów z kursu)

To nie jest instrukcja "produkcyjna" — cel jest jeden: żeby ktoś spoza Twojego
komputera mógł samodzielnie poklikać w aplikację i dać feedback. Zobacz też
`notatki/udostepnianie_aplikacji.md` — opisuje, dlaczego zwykły link do
`localhost` nie działa.

## 0. Zanim zaczniesz: odizoluj dane demo od prawdziwych danych

Baza Supabase, której dziś używasz lokalnie, zawiera **prawdziwe dane
biznesowe** (np. negocjacje z "Dostawcą X" — patrz
`notatki/udostepnianie_aplikacji.md`). Jurorzy/koledzy logujący się do demo
**nie mogą** zobaczyć tych danych. Dwie opcje:

- **Osobny projekt Supabase** (darmowy tier) tylko pod demo + wypełnienie go
  danymi z `backend/scripts/seed_test_data.py` (w pełni fikcyjne, domena
  `@example.com`).
- **Supabase branching** (jeśli masz plan, który to obsługuje) — osobna
  gałąź bazy od produkcyjnej.

Zdecydowanie polecam osobny projekt Supabase — jest darmowy i eliminuje
ryzyko pomyłki między "demo" a "prawdziwe dane" raz na zawsze. Reszta tej
instrukcji zakłada, że masz nowy, pusty projekt Supabase pod demo.

## 1. GitHub

```
git add -A
git commit -m "Przygotowanie do wdrożenia demo (Render + Vercel)"
gh repo create <nazwa-repo> --private --source=. --remote=origin
git push -u origin master
```

## 2. Baza danych (Supabase demo project)

1. Załóż nowy projekt na supabase.com (darmowy tier).
2. Skopiuj `DATABASE_URL` (Settings → Database → Connection string, tryb
   "Session pooler" lub bezpośredni — ten sam, którego używasz lokalnie).
3. Załóż prywatny bucket Storage o nazwie z `SUPABASE_AUDIO_BUCKET`
   (domyślnie `meeting-audio`) — ręcznie, tak jak w środowisku lokalnym.
4. Włącz rozszerzenie `pgvector` (Database → Extensions), jeśli nie jest
   jeszcze włączone — potrzebne do embeddingów decyzji.
5. Po pierwszym deployu backendu (patrz krok 3) migracje Alembic odpalą się
   same (`buildCommand` w `render.yaml` zawiera `alembic upgrade head`).
6. Uruchom `python -m scripts.seed_test_data` **wskazując na ten nowy
   projekt** (ustaw lokalnie `DATABASE_URL` na demo-projekt przed
   uruchomieniem), żeby wypełnić go fikcyjnymi danymi do klikania.

## 3. Backend → Render.com

1. Załóż konto na render.com (darmowe), połącz z GitHub.
2. New → Blueprint → wskaż repo — Render odczyta `render.yaml` z korzenia
   repo i sam zaproponuje usługę `apka-podsumowanie-spotkan-backend`.
3. Podczas tworzenia usługi Render poprosi o wartości zmiennych oznaczonych
   `sync: false` w `render.yaml`. Wpisz:
   - `DATABASE_URL` — connection string z kroku 2
   - `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` — z nowego projektu Supabase
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` — patrz krok 5 (Google Cloud)
   - `GOOGLE_REDIRECT_URI` — `https://<twoj-backend>.onrender.com/auth/callback`
     (dokładny adres poznasz dopiero po pierwszym deployu — możesz go
     zaktualizować potem w zakładce Environment i zrobić redeploy)
   - `SHEETS_TASKS_ID`, `SHEETS_PEOPLE_ID` — ID arkuszy (mogą być te same co
     lokalnie, jeśli to ma być ten sam arkusz testowy)
   - `GEMINI_API_KEY` — Twój klucz Gemini
   - `TOKEN_ENCRYPTION_KEY` — wygeneruj nowy: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   - `SESSION_SECRET` — dowolny losowy ciąg, np. `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - `FRONTEND_ORIGIN` — adres z Vercela (krok 4), np. `https://twoja-app.vercel.app`
     (tu też: poznasz go dopiero po deployu frontendu — możesz wrócić i
     zaktualizować)
4. Deploy. Sprawdź `https://<twoj-backend>.onrender.com/health` → `{"status":"ok"}`.

Free instance type usypia po ~15 min bezczynności — pierwsze wejście po
przerwie może potrwać 30-60s (cold start). To akceptowalne dla dema, warto
tylko uprzedzić testerów.

## 4. Frontend → Vercel

1. Załóż konto na vercel.com, połącz z GitHub, zaimportuj to samo repo.
2. Ustaw **Root Directory** na `frontend` (ważne — to monorepo).
3. Framework Preset: Vite (Vercel wykryje sam). Build command
   `npm run build`, output `dist` (domyślne, nie trzeba zmieniać).
4. Environment Variables:
   - `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` — z nowego projektu
     Supabase (demo)
   - `VITE_API_URL` — pełny adres backendu z Render, np.
     `https://apka-podsumowanie-spotkan-backend.onrender.com`
5. Deploy. Dostajesz adres, np. `https://twoja-app.vercel.app`.
6. Wróć do Render i zaktualizuj `FRONTEND_ORIGIN` na ten adres, redeploy
   backendu.

## 5. Google Cloud Console — redirect URI i test users

1. APIs & Services → Credentials → Twój OAuth Client ID → **Authorized
   redirect URIs** → dodaj `https://<twoj-backend>.onrender.com/auth/callback`
   (zostaw też wpis dla localhosta, jeśli nadal pracujesz lokalnie).
2. APIs & Services → OAuth consent screen → **Test users** → dodaj adresy
   e-mail jurorów/kolegów, którzy mają się zalogować przez Google. Bez tego
   dostaną błąd `access_denied` przy próbie logowania.
3. Pamiętaj: w trybie Testing token odświeżania Google wygasa po ~7 dniach
   (patrz pamięć projektu) — jeśli demo ma żyć dłużej, testerzy będą
   musieli się okresowo zalogować ponownie przez Google, żeby integracja
   Gmail/Sheets dalej działała.

## 6. Konta logowania do samej appki (Supabase Auth)

Ekran logowania (email + hasło) nie ma publicznej rejestracji. Załóż konta
testerom ręcznie: Supabase dashboard nowego projektu → Authentication →
Users → Add user (albo jedno wspólne konto demo i podaj im dane).

## 7. Sanity check

- Otwórz `https://twoja-app.vercel.app` w przeglądarce incognito.
- Zaloguj się (Supabase) → zaloguj się przez Google (test user) → sprawdź
  `/auth/me` (widoczne na Dashboardzie) pokazuje `google_connected: true`.
- Wgraj testowe spotkanie (audio lub tekst z `transkrypt_testowy.txt`) i
  przejdź cały flow: upload → review → approve → briefing/draft.

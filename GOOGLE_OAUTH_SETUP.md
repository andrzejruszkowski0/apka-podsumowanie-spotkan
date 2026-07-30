# Konfiguracja Google OAuth (krok po kroku)

Szczegółowy przepis na skonfigurowanie Google Cloud Console dla tej appki
(Gmail + Sheets API) oraz kroki ręcznej weryfikacji, że logowanie działa.
Wysokopoziomowy opis modelu uwierzytelniania: [SPEC.md](SPEC.md) §3.

## Wybór User Type

**Zakładany scenariusz (Google Workspace):** jeśli logujesz się kontem
**Google Workspace** (własna domena), na ekranie zgody OAuth wybierz User
Type **Internal**. Omija to proces weryfikacji Google dla scope'u
`gmail.send` i refresh token nigdy nie wygasa.

**Faktycznie użyty scenariusz (prywatny Gmail):** konto w tym projekcie to
zwykły Gmail, nie Workspace — Google nie oferuje wtedy opcji Internal (widać
to od razu po komunikacie "Brak organizacji" przy tworzeniu projektu).
Świadomie skonfigurowano więc:
- User Type: **External**, status publikacji: **Testing**
- Właściciel appki (lub, dla wersji demo, jedno wspólne konto) dodany jako
  **Test user** (bez tego logowanie jest blokowane przez Google)
- **Konsekwencja:** w tym trybie refresh token wygasa co ok. **7 dni** —
  raz na tydzień trzeba kliknąć "Zaloguj się przez Google" ponownie. Appka
  to obsługuje (czytelny komunikat zamiast błędu), to nie jest bug.
- Jeśli kiedyś pojawi się konto Workspace, wystarczy zmienić User Type na
  Internal w konsoli — kod backendu nie wymaga żadnych zmian.

## Kroki konfiguracji

(Google Auth Platform — nowszy UI konsoli, nazwy zakładek mogą się różnić
w zależności od wersji.)

1. **console.cloud.google.com** → utwórz projekt.
2. **APIs & Services → Library** → włącz `Gmail API` i `Google Sheets API`.
3. **Google Auth Platform → Odbiorcy (Audience)**: ustaw/sprawdź User Type
   (External przy prywatnym Gmailu), dodaj adres e-mail (właściciela lub
   wspólnego konta demo) jako Test user.
4. **Google Auth Platform → Dostęp do danych (Data access)** → "Dodaj lub
   usuń zakresy" → zaznacz `.../auth/gmail.send` i `.../auth/spreadsheets`
   (użyj filtra, żeby znaleźć je szybko na liście ~50 zakresów) → Update →
   Save.
5. **Google Auth Platform → Klienty (Clients) → Utwórz klienta**:
   - Typ aplikacji: **Aplikacja internetowa (Web application)**.
   - Autoryzowane URI przekierowania: `http://localhost:8000/auth/callback`
     dla developmentu lokalnego (dokładnie tak — `http`, `localhost`, bez
     ukośnika na końcu); dla wdrożenia dodaj też
     `https://<twoj-backend>.onrender.com/auth/callback`.
   - Zapisz **Client ID** i **Client secret** (skopiuj przyciskiem kopiowania,
     nie przepisuj ręcznie — literówka wywala logowanie błędem
     `redirect_uri_mismatch` albo `invalid_client`).
6. Uzupełnij w `backend/.env`:
   ```
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
   ```
7. Wygeneruj klucze aplikacji i dopisz do `.env`:
   ```
   # klucz Fernet do szyfrowania refresh tokena w bazie
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   # dowolny losowy sekret do podpisywania cookie sesji
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Wpisz wyniki jako `TOKEN_ENCRYPTION_KEY` i `SESSION_SECRET`.

## Weryfikacja ręczna

```
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

W drugim terminalu: `cd frontend && npm run dev`, otwórz `http://localhost:5173`.

1. Kliknij „Zaloguj się przez Google" → ekran zgody Google (pyta o Gmail i
   Sheets) → powrót do apki, widoczny e-mail zalogowanego użytkownika.
2. W Supabase Studio sprawdź tabelę `oauth_token` — `refresh_token_enc`
   i `access_token_enc` powinny być nieczytelnym binarnym blobem (nie
   plaintext).
3. Zrestartuj backend (Ctrl+C, uruchom ponownie) i odśwież
   `http://localhost:5173` — użytkownik dalej zalogowany, bez ponownego
   przechodzenia przez Google (wymaga ustawionego na stałe `SESSION_SECRET`
   w `.env` — bez niego backend loguje ostrzeżenie i używa tymczasowego
   klucza ważnego tylko do restartu).
4. Odświeżanie access tokena: w Supabase Studio ustaw
   `oauth_token.access_expires_at` na datę w przeszłości, odśwież `/auth/me`
   (np. przeładuj stronę) — `access_token_expires_at` w odpowiedzi powinno
   się zaktualizować na nową, przyszłą wartość, a `access_token_enc` powinien
   się zmienić.
5. `POST /auth/logout` (przycisk „Wyloguj") czyści sesję; `GET /auth/me`
   bez sesji zwraca 401.

Punkty 1–4 zweryfikowane ręcznie 2026-07-19 (External/Testing, konto Gmail).

## Backfill embeddingów decyzji (Etap 9)

**Odstępstwo od SPEC.md:** model embeddingów `text-embedding-004` (§1, §10.4)
został wycofany przez Google — wywołanie zwraca `404 NOT_FOUND`. Zastępca to
`gemini-embedding-001` z `output_dimensionality=768`, żeby zachować zgodność
z kolumną `decision.embedding vector(768)` i indeksem ivfflat już istniejącymi
w bazie (migracja 0001). Konfigurowalne przez `GEMINI_EMBEDDING_MODEL` /
`GEMINI_EMBEDDING_DIMENSIONS` w `.env`.

Backfill dla decyzji sprzed tego etapu:

```
cd backend
.venv\Scripts\activate
python -m scripts.backfill_decision_embeddings
```

Zweryfikowane ręcznie 2026-07-22 na żywej bazie: backfill uzupełnił
embeddingi 4 istniejącym decyzjom; zapytanie bez wspólnych słów z treścią
decyzji („Czy personel zostaje w pracy do późna wieczorem w świąteczne
miesiące?") poprawnie znalazło decyzje o wydłużeniu godzin otwarcia sklepów
w grudniu.

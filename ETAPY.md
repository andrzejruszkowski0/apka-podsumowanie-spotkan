# Etapy realizacji — prompty do Claude Code

Dokument towarzyszący `SPEC.md`. Jeden etap = jedna sesja w Claude Code.

## Zasada nadrzędna

Do **każdego** promptu poniżej dokleja się ten sam nagłówek:

```
Pracujesz nad projektem opisanym w SPEC.md. Przeczytaj go w całości przed
rozpoczęciem.

Realizujesz WYŁĄCZNIE zakres etapu podanego niżej. Nie implementuj funkcji
z późniejszych etapów, nawet jeśli wydają się blisko powiązane. Jeśli coś
w specyfikacji jest niejasne lub sprzeczne — zapytaj, nie zgaduj.

Po zakończeniu: krótkie podsumowanie co powstało i jak to sprawdzić ręcznie.
```

Bez tego Claude Code ma tendencję do „przy okazji" implementowania kolejnych
etapów, co kończy się dużym, nieprzetestowanym diffem.

---

## Lista etapów

| # | Nazwa | Rezultat |
|---|---|---|
| 1 | Szkielet i baza danych | Backend wstaje, migracje przechodzą, `/health` odpowiada |
| 2 | Google OAuth | Logowanie działa, refresh token zapisany i szyfrowany |
| 3 | Osoby i resolver aliasów | Sync z arkusza, mapowanie „Janek" → person_id |
| 4 | Upload i transkrypcja | Nagranie → transkrypt z etykietami mówców |
| 5 | Ekstrakcja RACI i decyzji | Transkrypt → zadania i decyzje w bazie |
| 6 | Ekran weryfikacji | **Aplikacja użyteczna.** Poprawiasz i zatwierdzasz. |
| 7 | Eksport do Google Sheets | Zatwierdzone zadania lądują w arkuszu |
| 8 | Przypomnienia i scheduler | Poranne maile do R, z A w Cc |
| 9 | Rejestr decyzji i briefing | Wyszukiwanie semantyczne, notatka przed spotkaniem |
| 10 | Szablony draftów | Trzy warianty podsumowania |

Etapy 1–6 to minimum działającego produktu. 7–10 to nadbudowa.

---

## Etap 1 — Szkielet i baza danych

```
ETAP 1: Szkielet i baza danych.

Zakres:
1. Struktura repo: backend/ (FastAPI), frontend/ (Vite + React + TS).
2. backend/: pyproject lub requirements.txt, FastAPI, uvicorn, SQLAlchemy 2.x,
   Alembic, python-dotenv. Endpoint GET /health zwracający {"status":"ok"}
   oraz wynik SELECT 1 do bazy.
3. .env.example ze wszystkimi zmiennymi z §15 SPEC.md. Prawdziwy .env w .gitignore.
4. Migracje Alembic tworzące WSZYSTKIE tabele z §2 SPEC.md — dokładnie tak,
   jak są tam zdefiniowane, wraz z indeksami częściowymi task_single_r
   i task_single_a oraz rozszerzeniami pgvector i pg_trgm.
5. RLS: włącz na wszystkich tabelach z polityką deny all dla roli anon.
6. frontend/: Vite + React + TS + Tailwind, jeden ekran wyświetlający status
   z /health. Proxy do backendu skonfigurowane w vite.config.
7. Backend słucha na 127.0.0.1, CORS ograniczony do http://localhost:5173.

Poza zakresem: auth, upload, AI, cokolwiek innego.

Sprawdzenie: `alembic upgrade head` przechodzi, backend wstaje, frontend
pokazuje "ok", tabele widoczne w Supabase Studio.
```

---

## Etap 2 — Google OAuth

```
ETAP 2: Google OAuth (logowanie + uprawnienia do Gmail i Sheets).

Zakres: §3 SPEC.md.
1. /auth/login → redirect do Google z access_type=offline, prompt=consent.
   Scopes: openid, email, profile, gmail.send, spreadsheets.
2. /auth/callback → wymiana kodu, upsert do app_user po google_sub,
   zapis tokenów do oauth_token.
3. Refresh token szyfrowany przez cryptography.fernet kluczem
   TOKEN_ENCRYPTION_KEY. Nigdy plaintext w bazie ani w logach.
4. Sesja: cookie HttpOnly, SameSite=Lax, podpisane SESSION_SECRET.
5. /auth/me → dane zalogowanego. /auth/logout.
6. Serwis odświeżania access tokena: automatyczny refresh gdy
   access_expires_at minął. Obsługa 401 z Google → czytelny komunikat
   o konieczności ponownej zgody.
7. Zależność FastAPI `require_user` chroniąca endpointy.
8. Frontend: przycisk logowania, wyświetlenie zalogowanego użytkownika.

Napisz też krótkie README z krokami konfiguracji w Google Cloud Console.
WAŻNE: typ aplikacji Internal (nie External), bo Workspace — inaczej token
wygasa co 7 dni.

Poza zakresem: faktyczne wywołania Gmail/Sheets — tylko uprawnienia.

Sprawdzenie: logowanie, refresh token w bazie zaszyfrowany, restart backendu
nie wymaga ponownego logowania.
```

---

## Etap 3 — Osoby i resolver aliasów

```
ETAP 3: Sync osób z arkusza i resolver nazwisk.

Zakres: §5 SPEC.md.
1. POST /people/sync — odczyt arkusza SHEETS_PEOPLE_ID przez Sheets API.
   Kolumny: Imię i nazwisko | Email | Aliasy (przecinkami) | Firma | Aktywny.
   Upsert po email. Osoby nieobecne w arkuszu → active=false (NIE usuwać).
2. Sync także raz przy starcie backendu.
3. GET /people — lista aktywnych.
4. GET /topics, POST /topics.
5. Resolver nazwisk jako osobny, czysty moduł (bez zależności od FastAPI),
   kolejność prób dokładnie wg §5:
   full_name → aliases → imię (tylko jeśli jednoznaczne) →
   pg_trgm > 0.6 (tylko jeśli jednoznaczne) → null.
6. Testy jednostkowe resolvera. OBOWIĄZKOWO przypadki niejednoznaczne:
   dwie osoby o imieniu Anna → resolver MUSI zwrócić null, nie wybierać
   losowo ani pierwszej z brzegu. To jest kluczowa właściwość tego modułu.
7. Frontend: /settings z przyciskiem sync i listą osób.

Poza zakresem: użycie resolvera w ekstrakcji (etap 5).

Sprawdzenie: testy przechodzą, sync działa, zmiana aliasu w arkuszu
widoczna po ponownym sync.
```

---

## Etap 4 — Upload i transkrypcja

```
ETAP 4: Upload plików i transkrypcja przez Gemini.

Zakres: §4 SPEC.md (część transkrypcyjna).
1. POST /meetings — utworzenie spotkania.
2. POST /meetings/{id}/audio — multipart, WIELE plików naraz, każdy z part_index.
   Upload do prywatnego bucketa Supabase Storage, zapis do meeting_audio.
   Akceptowane: .mp3 .m4a .wav .aac .ogg .flac
3. POST /meetings/{id}/text — wklejony tekst → transcript(part_index=0).
4. POST /meetings/{id}/process — start w BackgroundTasks, zwraca 202.
5. Transkrypcja: Gemini Files API (NIE inline base64 — godzinne nagranie
   przekracza limit 20 MB). Każdy plik osobno, prompt z §10.1, lista
   uczestników z tabeli person wstrzyknięta do promptu.
6. Sklejanie transkryptów po part_index W BACKENDZIE, nie w prompcie.
7. Aktualizacja meeting.status: uploaded → transcribing → analyzing.
   Błąd → status=failed + error_message.
8. GET /meetings/{id} — stan + transkrypt. GET /meetings — lista.
9. Frontend: /upload (formularz, wiele plików lub tekst), /meetings/:id
   z pollingiem co 2 s i podglądem transkryptu.

Poza zakresem: ekstrakcja zadań (etap 5).

Sprawdzenie: godzinne nagranie → czytelny transkrypt po polsku
z etykietami mówców.
```

---

## Etap 5 — Ekstrakcja RACI i decyzji

```
ETAP 5: Ekstrakcja zadań, RACI i decyzji z transkryptu.

Zakres: §4 (część ekstrakcyjna) + §10.2 i §10.3 SPEC.md.
1. Chunking: fragmenty ~4000 słów z zakładem ~200 słów. Transkrypt
   poniżej 5000 słów → jeden przebieg bez dzielenia.
2. Faza MAP: prompt §10.2 na każdym fragmencie, structured output (JSON schema).
3. Faza REDUCE: prompt §10.3, scalanie duplikatów. Przy sprzecznych wersjach
   deadline'u/RACI wygrywa późniejszy fragment.
4. Rozwiązywanie nazwisk resolverem z etapu 3. Nierozwiązane → person_id null,
   ai_confidence obniżone.
5. Zapis: task, task_raci, decision. Walidacja: dokładnie jedno R i jedno A
   na zadanie (lub null, jeśli nie padło).
6. meeting.status → awaiting_review.
7. Prompt injection: transkrypt w delimiterach, instrukcja ignorowania poleceń
   w treści. Wyjście AI nigdy nie wyzwala wysyłki maila.
8. Logowanie surowych odpowiedzi Gemini do pliku (debug jakości promptów).

Poza zakresem: UI weryfikacji (etap 6), embeddingi (etap 9).

Sprawdzenie: transkrypt testowy → sensowne zadania z RACI w bazie,
duplikaty z zachodzących fragmentów scalone.
```

---

## Etap 6 — Ekran weryfikacji

```
ETAP 6: Ekran weryfikacji. To najważniejszy ekran aplikacji — guardrail
całego systemu. Po tym etapie aplikacja jest użyteczna.

Zakres: §11 SPEC.md.
1. GET /meetings/{id}/review — zadania i decyzje do weryfikacji z cytatami.
2. PUT /meetings/{id}/review — zapis poprawek. Każda ręczna zmiana ustawia
   edited_by_user=true.
3. POST /meetings/{id}/approve — walidacja + status=approved.
   MUSI odrzucić zatwierdzenie, jeśli jakiekolwiek nazwisko nierozwiązane.
4. Frontend /meetings/:id/review:
   - zadania i decyzje w jednej liście, pogrupowane
   - confidence < 0.7 wizualnie wyróżnione
   - edycja inline; R i A: select z osób; C i I: multiselect
   - cytat uzasadniający pod rozwinięciem (weryfikacja bez czytania
     całego transkryptu)
   - usunięcie pozycji jednym kliknięciem
   - "Zatwierdź i zapisz" nieaktywny dopóki są nierozwiązane nazwiska
5. Ekran ma być szybki w obsłudze — przejście przez 10 zadań w minutę.
   Klawiatura: Tab między polami, widoczny focus.

Poza zakresem: zapis do Sheets (etap 7).

Sprawdzenie: pełna ścieżka nagranie → transkrypt → ekstrakcja → poprawki
→ zatwierdzenie, bez dotykania bazy ręcznie.
```

---

## Etap 7 — Eksport do Google Sheets

```
ETAP 7: Zapis zadań do Google Sheets (widok eksportowy).

Zakres: §6 SPEC.md.
1. Zapis wyzwalany przez POST /meetings/{id}/approve — append wierszy
   do SHEETS_TASKS_ID. Kolumny A–K dokładnie wg §6.
2. Numer wiersza → task.sheets_row.
3. PATCH /tasks/{id} — zmiana statusu lub deadline'u → update wiersza w arkuszu.
4. Kolumna A (uuid zadania) pozwala odnaleźć wiersz, gdyby numeracja
   się rozjechała — zaimplementuj fallback: szukaj po uuid, jeśli
   sheets_row nie zgadza się z zawartością.
5. Utworzenie nagłówka i protected range, jeśli arkusz pusty.
6. GET /tasks z filtrami: status, topic_id, overdue.
7. Frontend /tasks: tabela, filtry, odznaczanie zadania jako done.

KIERUNEK JEST JEDNOSTRONNY: Postgres → Sheets. Nie implementuj odczytu
statusów z arkusza. Ręczne zmiany w arkuszu są nadpisywane — to świadoma
decyzja architektoniczna, nie przeoczenie.

Sprawdzenie: zatwierdzenie spotkania → wiersze w arkuszu; odznaczenie
w panelu → status zmieniony w arkuszu.
```

---

## Etap 8 — Przypomnienia i scheduler

```
ETAP 8: Automatyczne przypomnienia mailowe.

Zakres: §7 SPEC.md.
1. Serwis Gmail API: wysyłka z konta właściciela (OAuth z etapu 2).
2. Szablon maila przypomnienia — zwięzły: zadanie, deadline, temat,
   link do panelu.
3. Job daily_reminders w APScheduler, codziennie o REMINDER_HOUR
   w strefie TIMEZONE.
   Wybór: task.status='open' AND deadline BETWEEN today AND today+REMINDER_DAYS_AHEAD.
   Odbiorca: osoba z rolą R (To), osoba z rolą A (Cc).
4. Idempotencja: sprawdzenie notification_log przed wysyłką; unikalny
   indeks notif_once_per_day jako twarde zabezpieczenie. Wysyłka i zapis
   do logu w jednej transakcji.
5. CATCH-UP przy starcie backendu — bez tego cała funkcja nie działa przy
   lokalnym hostingu:
     last = scheduler_run['daily_reminders']
     if last is None or last < today: run_daily_reminders(); zapisz today
   Nadrabiaj TYLKO bieżący dzień, nie wstecz.
6. UWAGA: APScheduler + uvicorn --reload uruchamia job dwukrotnie
   (reloader forkuje proces). Zabezpiecz flagą środowiskową.

Sprawdzenie: zadanie z deadlinem za 2 dni → DOKŁADNIE jeden mail do R
z A w Cc. Ponowny ręczny run tego samego dnia → brak dubla.
Restart backendu po godzinie wysyłki → catch-up odpala raz.
```

---

## Etap 9 — Rejestr decyzji i briefing

```
ETAP 9: Rejestr decyzji z wyszukiwaniem semantycznym + briefing.

Zakres: §10.4 SPEC.md.
1. Embeddingi decyzji (text-embedding-004, 768 wymiarów) generowane przy
   zatwierdzeniu spotkania → decision.embedding.
2. GET /decisions?topic_id=&q= — bez q: filtr po temacie, chronologicznie.
   Z q: wyszukiwanie semantyczne ivfflat + cosine.
3. Backfill embeddingów dla decyzji zapisanych wcześniej (skrypt jednorazowy).
4. POST /briefing — {topic_id} → zebranie kontekstu (ostatnie decyzje,
   otwarte zadania z oznaczeniem po terminie, zadania zamknięte od ostatniego
   spotkania) → prompt §10.4 → wysyłka na adres właściciela + wpis
   do notification_log (kind='briefing').
5. Frontend /decisions: lista, filtr po temacie, pole wyszukiwania.
6. Frontend /briefing: wybór tematu → PODGLĄD → dopiero potem wysyłka.
   Bez automatycznej wysyłki.

Poza zakresem: Google Calendar. Wybór tematu jest ręczny — to świadoma decyzja.

Sprawdzenie: wyszukanie "rabat" znajduje decyzję o obniżce ceny, choć
słowo "rabat" w niej nie pada.
```

---

## Etap 10 — Szablony draftów

```
ETAP 10: Szablony maili podsumowujących.

Zakres: §10.5 SPEC.md.
1. POST /meetings/{id}/draft — {template: formal_board|supplier|team_casual}
   → zwraca szkic (temat + treść). NIE wysyła.
2. Trzy warianty:
   - formal_board: raport dla zarządu — cel, ustalenia, ryzyka, wymagane
     decyzje. Bezosobowo, zwięźle.
   - supplier: podsumowanie dla dostawcy — TYLKO ustalenia obustronne.
     Wewnętrzne uwagi i zadania własne pominięte. To jest istotne: draft
     dla dostawcy nie może wyciekać informacji wewnętrznych.
   - team_casual: wiadomość robocza — kto, co, do kiedy. Bezpośrednio.
3. Osobny endpoint wysyłki, wyzwalany świadomym kliknięciem po przeczytaniu.
   Wpis do notification_log (kind='summary').
4. Frontend: wybór szablonu na ekranie spotkania → podgląd → edycja treści
   → wysyłka.

Sprawdzenie: to samo spotkanie w trzech szablonach daje trzy wyraźnie
różne maile; wariant supplier nie zawiera notatek wewnętrznych.
```

---

## Po każdym etapie

Zanim przejdziesz dalej — sprawdź ręcznie to, co w sekcji „Sprawdzenie".
Etap, który „wygląda na skończony", ale nie został uruchomiony, to dług,
który wypłynie trzy etapy później i będzie kosztował dziesięć razy więcej.

Commit na koniec każdego etapu. Osobna gałąź na etap, jeśli lubisz porządek.

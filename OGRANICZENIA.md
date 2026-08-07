# Ograniczenia i rzeczy, o których trzeba pamiętać

Stan na: 22.07.2026, po zakończeniu Etapu 10 (wszystkie etapy z ETAPY.md
zaimplementowane i zacommitowane).

Wszystkie 10 etapów ma implementację, testy jednostkowe przechodzą, nie ma
zostawionych TODO w kodzie. To nie znaczy jednak, że aplikacja nie ma
ograniczeń — poniżej lista rzeczy wynikających ze świadomych decyzji
architektonicznych (patrz SPEC.md §0) oraz stanu konta Google.

## 1. Etapy 1–6 to rdzeń, 7–10 to nadbudowa

Upload → transkrypcja → ekstrakcja → ekran weryfikacji to minimum
działającego produktu (ETAPY.md). Eksport do Sheets, przypomnienia,
rejestr decyzji/briefing i szablony draftów to funkcje dodatkowe —
zaimplementowane, ale to prosta aplikacja jednoosobowa, nie system
klasy enterprise.

## 2. Konto Google w trybie Testing/External, nie Workspace — dotyczy Gmaila

Konto użyte w projekcie (`andrzejruszkowski0@gmail.com`) to zwykły Gmail,
nie Google Workspace. Google nie oferuje wtedy trybu **Internal** —
aplikacja działa w trybie **External** (status publikacji podnoszony do
Production, ale bez ukończonej pełnej weryfikacji Google dla wrażliwych
scope).

**Konsekwencja:** refresh token OAuth (logowanie usera, scope `gmail.send`)
wygasa co ok. **7 dni** w statusie Testing. Raz na tydzień trzeba kliknąć
"Zaloguj się przez Google" ponownie, inaczej:
- wysyłka przypomnień o zadaniach (Etap 8),
- wysyłka briefingów (Etap 9),
- wysyłka draftów podsumowań (Etap 10),

przestaną działać po cichu, dopóki nie nastąpi ponowne logowanie. Aplikacja
obsługuje to czytelnym komunikatem zamiast crasha, ale to nie jest
"ustaw i zapomnij" — wymaga cyklicznej uwagi właściciela.

**Ten sam status Testing ma drugi efekt uboczny:** tylko zaproszeni testerzy
mogą w ogóle przejść ekran zgody Google, więc przypadkowy gość demo utykał na
„Zaloguj się przez Google". Od 2026-08-06 Dashboard ma link **„Wypróbuj demo
bez logowania Google"** (`POST /auth/demo-login`), który zakłada sesję bez
OAuth. Kompromis: takie konto nigdy nie ma tokenów Google, więc wysyłka maili
(przypomnienia, briefing, drafty) zawsze zwraca 401 `reauth_required` —
tłumaczone na froncie na czytelny komunikat zamiast dawania złudzenia, że
funkcja zadziała po prostu po kliknięciu.

**Sheets (arkusze „Osoby” i „Zadania RACI”) tego ograniczenia już nie ma** —
od 2026-08-02 są obsługiwane przez osobne konto serwisowe (Service Account),
niezależne od statusu OAuth i logowania usera. Powód zmiany: Sheets API
zwracało 403 przy wywołaniach z Render (produkcja) mimo działającego tokena
lokalnie i mimo przełączenia ekranu zgody na Production — patrz
GOOGLE_OAUTH_SETUP.md, sekcja „Konto serwisowe do Google Sheets”.

## 3. Scheduler działa tylko, gdy komputer jest włączony

To świadoma decyzja architektoniczna (hosting lokalny, SPEC.md §0/§7), nie
przeoczenie. Przypomnienia mailowe (`daily_reminders`) wysyłają się
codziennie o `REMINDER_HOUR`, ale tylko jeśli backend w tym momencie działa.

Mechanizm catch-up przy starcie backendu nadrabia **tylko bieżący dzień** —
jeśli komputer był wyłączony kilka dni, zaległości sprzed wczoraj nie są
odsyłane wstecz (to świadome ograniczenie, nie bug — patrz SPEC.md §7).

## 4. Brak jeszcze jednego pełnego przebiegu end-to-end przez wszystkie etapy naraz

Każdy etap był testowany osobno przy jego wdrażaniu. Nie zrobiono jeszcze
jednego ciągłego przebiegu: upload → transkrypcja → ekstrakcja → weryfikacja
→ zatwierdzenie → zapis do Sheets → przypomnienie mailowe → decyzje/briefing
→ draft podsumowania — na jednym, tym samym spotkaniu od początku do końca.
Taki test mógłby złapać drobne niezgodności na styku etapów, które nie są
widoczne przy testowaniu każdego etapu osobno.

## 5. Ręczne kroki wymagane do normalnej pracy z aplikacją

- Sync osób z arkusza (`POST /people/sync`) trzeba odpalać ręcznie po
  każdej zmianie w arkuszu „Osoby” (świadoma decyzja, SPEC.md §5).
- Wybór tematu do briefingu jest ręczny — bez integracji z kalendarzem
  (świadoma decyzja, SPEC.md §9, poza zakresem Etapu 9).
- Edycja arkusza „Zadania RACI” jest jednostronnie nadpisywana przy kolejnej
  synchronizacji z Postgresa — Sheets to widok eksportowy, nie edytor
  (świadoma decyzja, SPEC.md §6).

## 6. Projekt Supabase (demo) usypia po ~7 dniach bezczynności — inaczej niż Render

Darmowy tier Supabase automatycznie **wstrzymuje (Paused)** cały projekt po
ok. tygodniu bez ruchu API — nie tylko Postgres, ale i Auth. W tym stanie
logowanie do appki (Supabase Auth, ekran email+hasło) kończy się mylącym
komunikatem **„Invalid login credentials”**, mimo że konto istnieje i hasło
jest poprawne — bo w ogóle nie dochodzi do sprawdzenia danych.

**Różnica względem usypiania Render:** backend na Render budzi się sam przy
pierwszym request (tylko wolniej, 30-60s). Projekt Supabase **nie budzi się
sam** przy wejściu na stronę — wymaga ręcznego kliknięcia **Restore** w
Supabase Dashboard (dashboard projektu pokazuje status „Paused” z tym
przyciskiem), potem ok. 1-2 min na powrót do stanu Active.

**Diagnoza:** jeśli logowanie nagle przestaje działać bez żadnej zmiany w
kodzie/konfiguracji, sprawdź najpierw status projektu w Supabase Dashboard
zanim zaczniesz szukać błędu w kodzie — to najczęstsza przyczyna (wystąpiło
2026-08-02, potwierdzone w Auth Logs jako brak jakiejkolwiek odpowiedzi z
wstrzymanego projektu).

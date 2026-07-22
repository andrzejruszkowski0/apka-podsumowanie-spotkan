# Aplikacja do analizy spotkań — opis finalny

Wersja po ustaleniach. Zastępuje opis pierwotny.
Dokumenty towarzyszące: `SPEC.md` (specyfikacja techniczna), `ETAPY.md` (prompty wdrożeniowe).

**Zaktualizowano po Etapie 10** — dopisano zmiany, które wyszły dopiero w
trakcie wdrażania kolejnych etapów (model embeddingów, realny tryb konta
Google, sposób wysyłki briefingu i draftów), a nie były jeszcze znane w
momencie spisania tej wersji.

---

## Czym to jest

Aplikacja zamienia nagranie spotkania w konkretne zadania z przypisaną
odpowiedzialnością, pilnuje terminów i prowadzi rejestr ustaleń biznesowych.

Działa lokalnie, na jednym komputerze, dla jednej osoby. Bez platform
automatyzacji, bez opłat subskrypcyjnych, z pełną kontrolą nad kodem.

---

## 1. Opis poszczególnych funkcji

### Obsługa dwóch formatów wejściowych (audio / tekst)

Wgrywasz plik dźwiękowy nagrany telefonem (`.mp3`, `.m4a`, `.wav`, `.aac`,
`.ogg`, `.flac`) albo wklejasz gotowy tekst z transkrypcji systemowej.

**Zmiana wobec pierwotnego opisu:** formularz przyjmuje **wiele plików do
jednego spotkania**. Sesje dłuższe niż godzinę dzielisz ręcznie na osobne
nagrania; aplikacja skleja je w kolejności i traktuje jako jedno spotkanie.

Ponieważ backend chodzi lokalnie, nagranie przerzucasz z telefonu na komputer
i wgrywasz w panelu.

### Transkrypcja z rozpoznaniem mówców

**Zmiana istotna:** OpenAI Whisper **wypadł ze stosu**. Transkrypcję robi
Gemini, który przyjmuje audio natywnie.

Powody:
- Whisper ma limit 25 MB na plik (~20 min). Godzinne nagranie wymagałoby
  cięcia na kawałki i sklejania — dodatkowy kod, dodatkowe źródło błędów.
- Gemini przez Files API przyjmuje pliki do 2 GB. Godzinne nagranie idzie
  w jednym kawałku.
- Jedno API zamiast dwóch. Jedna zależność, jeden klucz, jeden rachunek.

**Dodatkowo — funkcja, której nie było w pierwotnym opisie:** transkrypt
zawiera **etykiety mówców**. Gemini dostaje w prompcie listę uczestników
spotkania (z bazy osób) i oznacza wypowiedzi. Bez tego przypisanie „kto co
obiecał" byłoby zgadywanką na podstawie samej treści.

Głosów nierozpoznanych model nie zgaduje — oznacza je konsekwentnie jako
`[Mówca 1]`, `[Mówca 2]`.

### Analiza spotkania i automatyczna macierz RACI

AI wyciąga z transkryptu konkretne zadania i przypisuje role:
**R** (wykonawca), **A** (odpowiedzialny za efekt), **C** (konsultowany),
**I** (informowany), plus termin realizacji.

**Doprecyzowanie kryterium:** zadaniem jest tylko to, o czym da się
stwierdzić, czy zostało zrobione. „Przemyślimy temat" nie jest zadaniem.
„Janek wyśle raport do piątku" — jest. Bez tego kryterium arkusz zapełnia
się śmieciami.

**Zmiana techniczna:** ekstrakcja jest dwuetapowa. Godzinne spotkanie to
~12 tys. słów. Gemini zmieści to w kontekście, ale jakość wyciągania spada
na długim wejściu. Więc: transkrypt dzielony na fragmenty po ~4000 słów
z zakładem, z każdego wyciągane kandydatury, potem jedno wywołanie scalające
duplikaty. Przy sprzecznych wersjach wygrywa fragment późniejszy — ustalenia
ewoluują w trakcie rozmowy.

**Zasada:** przy braku danych model wpisuje `null`, nie zgaduje. Jeśli nie
padło, kto odpowiada za efekt — pole zostaje puste do uzupełnienia przez Ciebie.

### Rozpoznawanie osób (funkcja nowa)

W pierwotnym opisie tej funkcji nie było, a bez niej cała reszta nie działa:
AI wyciąga z rozmowy „Janka", a system musi wiedzieć, na jaki adres wysłać
przypomnienie.

Lista osób mieszka w arkuszu Google, który uzupełniasz ręcznie:

```
Imię i nazwisko | Email | Aliasy (przecinkami) | Firma | Aktywny
```

Kolumna aliasów jest kluczowa — w rozmowie pada „Janek", „Jan K.", „Kowalski",
a to jedna osoba. Sync do bazy wyzwalasz przyciskiem w panelu.

Mapowanie działa kaskadowo: pełne nazwisko → alias → samo imię (tylko jeśli
jednoznaczne) → podobieństwo tekstowe (tylko jeśli jednoznaczne) → porażka.

**Przy niejednoznaczności system nigdy nie zgaduje.** Dwie Anny w bazie =
pytanie do Ciebie na ekranie weryfikacji, nie losowy wybór.

### Ekran weryfikacji (guardrail)

Zanim cokolwiek zostanie zapisane lub wysłane, widzisz podgląd wyciągniętych
zadań i ról RACI. Zatwierdzasz albo poprawiasz.

**Doprecyzowania wobec pierwotnego opisu:**
- Pozycje z niską pewnością AI są wizualnie wyróżnione — wiesz, gdzie patrzeć.
- Każde zadanie ma **cytat uzasadniający** z transkryptu. Weryfikujesz bez
  czytania godziny rozmowy.
- Nierozwiązane nazwiska **blokują zatwierdzenie**. Nie da się przepchnąć
  zadania bez wykonawcy.
- Usunięcie pozycji jednym kliknięciem — AI czasem wyciągnie coś, co zadaniem
  nie jest.
- Cel: przejście przez 10 zadań w minutę.

To najważniejszy ekran aplikacji. Po jego zbudowaniu aplikacja jest już
użyteczna, nawet bez pozostałych funkcji.

### Zapis do Google Sheets

Po zatwierdzeniu zadania trafiają do wspólnego arkusza z podziałem RACI.

**Rozstrzygnięcie architektoniczne — najważniejsza zmiana w całym projekcie:**

Źródłem prawdy jest **baza danych, nie arkusz**. Zapis jest jednokierunkowy:
Postgres → Sheets. Statusy zadań odznaczasz **w panelu aplikacji**, a zmiana
propaguje się do arkusza.

Konsekwencja: ręczna edycja arkusza zostanie nadpisana. Arkusz jest widokiem
do czytania i udostępniania zespołowi, nie edytorem.

Powód: dwukierunkowa synchronizacja Sheets ↔ baza to najbrzydsza część takiego
projektu — brak webhooków wymusza polling, dochodzą konflikty i reguły
rozstrzygania. Skoro aplikacja jest jednoosobowa, panel w zupełności wystarczy.

### Automatyczny follow-up (przypomnienia)

Codziennie rano system sprawdza terminy. Zadanie z deadlinem za 2 dni →
spersonalizowany mail do osoby oznaczonej jako **R**, z osobą **A** w DW.

Maile wychodzą **z Twojego konta** (Gmail API, zwykły OAuth) — odbiorca widzi
wiadomość od Ciebie, nie od bota.

**Zmiana wymuszona hostingiem lokalnym:** scheduler działa tylko przy włączonym
komputerze. Zamknięty laptop o 8:00 = brak przypomnień tego dnia. Dlatego
aplikacja ma **mechanizm nadrabiania**: przy starcie sprawdza, czy dzisiejsze
przypomnienia już poszły, i jeśli nie — wysyła je od razu.

Nadrabiany jest tylko bieżący dzień. Przypomnienie o terminie sprzed tygodnia
nie ma wartości, a zadania po terminie i tak zostają w puli, dopóki są otwarte.

Zabezpieczenie przed dublami działa na dwóch poziomach: sprawdzenie dziennika
wysyłek przed każdym mailem oraz unikalny indeks w bazie jako twarda blokada.

### Rejestr decyzji (Decision Log)

Osobna baza twardych ustaleń biznesowych — „Dostawca X zgadza się na rabat 3%",
„Zmiana terminu wdrożenia na wrzesień". Wpisy kategoryzowane po tematach
i dostawcach.

**Doprecyzowanie:** zapisywane są tylko ustalenia, które coś przesądzają —
warunki handlowe, terminy, zakres, wybór wariantu. Opinie i hipotezy nie.

Wyszukiwanie jest **semantyczne** (embeddingi + pgvector): szukasz „rabat",
znajdujesz decyzję o obniżce ceny, choć słowo „rabat" w niej nie pada.

### Briefing przed spotkaniem

Krótka notatka: na czym stanęło, do czego wrócić, kto zalega z zadaniami,
co wymaga decyzji.

**Uproszczenie wobec pierwotnego opisu:** briefing uruchamiasz **ręcznym
wyborem dostawcy lub tematu w panelu**. Bez integracji z kalendarzem.

**Doprecyzowanie wobec pierwotnej specyfikacji:** tak samo jak przy draftach
poniżej, briefing to najpierw **podgląd**, dopiero potem osobny klik „Wyślij”
— pierwotny opis zakładał jedno wywołanie „generuje i wysyła”, ale to
łamałoby zasadę „AI nigdy nie decyduje samo o wysyłce maila”.

Powód: Google Calendar API nie było w pierwotnym stosie, choć funkcja go
zakładała, a przy hostingu lokalnym „15 minut przed spotkaniem" i tak działa
tylko przy włączonym komputerze. Ręczny wybór daje 90% wartości za 10% pracy.
Kalendarz można dołożyć później — architektura tego nie blokuje.

### Szablony wyjściowe (drafty maili)

Trzy warianty podsumowania:
- **formalny raport dla zarządu** — cel, ustalenia, ryzyka, wymagane decyzje
- **oficjalne podsumowanie dla dostawcy** — tylko ustalenia obustronne;
  notatki wewnętrzne i zadania własne pominięte
- **luźna wiadomość robocza dla zespołu** — kto, co, do kiedy

Draft nigdy nie wychodzi automatycznie. Zawsze czytasz i klikasz wyślij.

**Doprecyzowanie wobec pierwotnej specyfikacji:** odbiorcę (adres „Do”,
opcjonalnie „Dw”) wpisujesz ręcznie przy każdej wysyłce — pierwotny opis tego
nie precyzował. W odróżnieniu od briefingu (zawsze na Twój adres), draft
trafia do różnych ludzi zależnie od szablonu (zarząd, dostawca, zespół), więc
nie da się przypisać jednego stałego adresu z góry.

---

## 2. Stos narzędziowy — finalny

Bez zewnętrznych platform automatyzacji (Make, n8n). Pełna kontrola nad kodem,
brak opłat subskrypcyjnych, fundament pod ewentualny produkt komercyjny.

| Warstwa | Wybór | Zmiana wobec pierwotnego opisu |
|---|---|---|
| Środowisko | Claude Code | bez zmian |
| Baza i pliki | Supabase Cloud (Postgres + pgvector + Storage) | doprecyzowane: Supabase **to jest** Postgres, nie ma dwóch osobnych rzeczy |
| Backend | Python + FastAPI | bez zmian |
| Transkrypcja | **Gemini** (natywne audio) | **Whisper usunięty** |
| Analiza AI | **Gemini** | wybrany spośród „OpenAI lub Gemini" |
| Embeddingi | Gemini gemini-embedding-001 (768 wym.) | nowe — wymagane przez wyszukiwanie semantyczne. Pierwotnie zakładany text-embedding-004, ale Google go wycofał w trakcie budowy (etap 9) |
| Integracje | Google Sheets API, Gmail API | bez zmian |
| Scheduler | APScheduler | + mechanizm nadrabiania zaległości |
| Frontend | React (Vite) + TypeScript + Tailwind | doprecyzowane (nie „lub czysty HTML/JS") |
| Auth | Google OAuth | nowe — nie było w pierwotnym opisie |
| Hosting | lokalnie, `127.0.0.1` | nowe — nie było ustalone |

**Wypadło ze stosu:** OpenAI Whisper, Google Calendar API, OpenAI jako silnik
analizy.

**Doszło:** Google OAuth, embeddingi, mechanizm nadrabiania zaległości
schedulera, tabela osób z aliasami.

---

## 3. Jak to działa w praktyce — pełny przebieg

```
1. Spotkanie z dostawcą, nagrywasz telefonem (1–1,5 h)
2. Przerzucasz plik na komputer
3. Panel → Upload → tytuł, data, dostawca, plik
4. Gemini transkrybuje z etykietami mówców      (~kilka minut)
5. Gemini wyciąga zadania, RACI, decyzje
6. Panel → Weryfikacja:
      poprawiasz co trzeba, uzupełniasz nierozpoznane nazwiska
      → Zatwierdź
7. Zadania lądują w arkuszu Google
   Decyzje trafiają do rejestru z embeddingami
8. Opcjonalnie: generujesz draft maila i wysyłasz
9. Codziennie rano: system pilnuje terminów, wysyła przypomnienia
   z Twojego konta
10. Przed kolejnym spotkaniem: Panel → Briefing → wybierasz dostawcę
    → dostajesz notatkę na maila
```

---

## 4. Co świadomie odpuszczono

Uczciwa lista — to nie są przeoczenia, tylko decyzje:

| Rzecz | Dlaczego |
|---|---|
| Wielu użytkowników | Aplikacja dla jednej osoby. Model danych dopuszcza rozbudowę w etapie 2. |
| Edycja statusów w arkuszu | Dwukierunkowy sync to najbrzydsza część projektu. Panel wystarczy. |
| Integracja z kalendarzem | Ręczny wybór tematu daje niemal tę samą wartość. Do dołożenia później. |
| Hosting w chmurze | Lokalnie = zero kosztów, pełna prywatność. Cena: scheduler potrzebuje włączonego komputera. |
| Upload z telefonu | Wymagałby wystawienia backendu na świat. Przerzucenie pliku to 10 sekund. |
| Warstwa abstrakcji nad LLM | „Na wszelki wypadek, gdyby zmienić dostawcę" to koszt teraz za korzyść, która może nie nadejść. |

---

## 5. Ryzyka, o których warto pamiętać

| Ryzyko | Mitygacja |
|---|---|
| Komputer wyłączony rano | Nadrabianie przy starcie |
| AI myli mówców | Lista uczestników w prompcie + ekran weryfikacji |
| AI wyciąga zadania-widma | Kryterium sprawdzalności + usuwanie na weryfikacji |
| Token OAuth wygasa co ~7 dni | Konto użyte w projekcie to zwykły Gmail, nie Workspace — tryb **Internal** (bez wygasania) jest niedostępny. Realnie: logowanie raz w tygodniu, aplikacja sygnalizuje to czytelnym błędem zamiast cichej awarii wysyłki. Przejście na Workspace usunęłoby ograniczenie |
| Ktoś edytuje arkusz | Zmiany zostaną nadpisane. Świadoma decyzja. |
| Limit 1 GB storage | Usuwanie audio po udanej transkrypcji — wartością jest transkrypt |

---

## 6. Koszty

| Pozycja | Miesięcznie (~10 spotkań × 1 h) |
|---|---|
| Supabase Free | 0 zł |
| Gemini (transkrypcja + analiza) | rząd kilkunastu złotych |
| Gmail API, Sheets API | 0 zł (w ramach darmowych limitów Google — konto nie jest Workspace) |
| Hosting | 0 zł |

---

## 7. Kolejność budowy

```
1.  Szkielet i baza danych
2.  Google OAuth
3.  Osoby i resolver aliasów
4.  Upload i transkrypcja
5.  Ekstrakcja RACI i decyzji
6.  Ekran weryfikacji          ← tu aplikacja staje się użyteczna
────────────────────────────────
7.  Eksport do Google Sheets
8.  Przypomnienia i scheduler
9.  Rejestr decyzji i briefing
10. Szablony draftów
```

Etapy 1–6 to działający produkt: nagrywasz, dostajesz zweryfikowane zadania
z RACI. Reszta to nadbudowa, którą dokładasz w wygodnym dla siebie tempie.

Prompty do każdego etapu: `ETAPY.md`.
Szczegóły techniczne, model danych, kontrakty API, prompty AI: `SPEC.md`.

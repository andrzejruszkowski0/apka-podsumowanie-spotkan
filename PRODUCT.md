# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Odbiorca interfejsu dziś (potwierdzone):** widownia oceniająca — prowadzący
i uczestnicy kursu Vibe Coding, rekruterzy, potencjalni klienci. Wchodzą przez
publiczne demo na Vercel albo oglądają prezentację, zwykle raz, bez instrukcji,
często po kliknięciu „Wypróbuj demo bez logowania Google". Ich zadanie to
w kilka minut zrozumieć, **co aplikacja robi i czy robi to dobrze** — nie
przeprowadzić realny proces po spotkaniu.

**Persona produktowa (modelowana w środku, nie mierzona):** jedna osoba —
właściciel/menedżer prowadzący regularne spotkania z dostawcami i zespołem,
który chce automatyczny protokół i follow-up bez ręcznego notowania.
Aplikacja jest jednoosobowa z premedytacją.

Te dwie role się rozjeżdżają i to jest najważniejszy fakt tego dokumentu:
ekrany obsługują pracę menedżera, ale ocenia je ktoś, kto tej pracy nigdy nie
wykonał. Przyszłe prace nie mogą optymalizować pod codzienną wprawę
użytkownika kosztem czytelności dla kogoś, kto widzi ekran pierwszy raz.

**Nie jest odbiorcą:** zespół klienta / wielu użytkowników w jednej firmie.
Model danych to dopuszcza, ale nie jest zaimplementowane i nie jest celem.

## Product Purpose

Po spotkaniach — zwłaszcza z dostawcami i kontrahentami — ustalenia i zadania
giną: nikt nie robi porządnej notatki, nie wiadomo kto za co odpowiada i do
kiedy, przypomnień o terminach nikt nie wysyła ręcznie.

Aplikacja zamienia nagranie (lub gotowy tekst) spotkania w ustrukturyzowane
zadania z przypisaną odpowiedzialnością w macierzy RACI, pilnuje terminów
mailowymi przypomnieniami i prowadzi przeszukiwalny rejestr decyzji
biznesowych.

Sukces dla persony: po spotkaniu nie trzeba nic notować, a lista zadań trafia
do właściwych osób. Sukces dla realnego odbiorcy dziś: zrozumieć powyższe bez
czytania dokumentacji.

## Positioning

Mechanizm, którego sąsiednie narzędzia (zwykłe „AI meeting notes") nie mogą
uczciwie skopiować: **RACI zamiast listy bulletów + wymuszona weryfikacja
przez człowieka + cytat źródłowy przy każdej pozycji.**

- Każde wyciągnięte zadanie niesie cytat z transkryptu, na podstawie którego
  powstało — weryfikacja nie wymaga słuchania nagrania.
- AI nigdy nie zgaduje przy niejednoznaczności (np. dwie osoby o imieniu
  Anna) — zostawia puste pole i **blokuje zatwierdzenie**, dopóki człowiek nie
  rozstrzygnie.
- AI nigdy nie wysyła maila samodzielnie. Briefing i draft podsumowania to
  zawsze najpierw podgląd, potem osobny, świadomy klik.

Człowiek w pętli nie jest tu funkcją bezpieczeństwa dopisaną z boku — jest
osią produktu i głównym argumentem, że wynikom można ufać.

## Operating Context

Przepływ główny: **upload nagrania/tekstu → transkrypcja z rozpoznaniem
mówców → ekstrakcja zadań/RACI/decyzji → rozwiązanie nazwisk na osoby
z kartoteki → ekran weryfikacji (człowiek zatwierdza) → zapis do Postgres +
eksport do Google Sheets → codzienne przypomnienia mailowe → rejestr decyzji
z wyszukiwaniem semantycznym → opcjonalne briefingi i drafty maili.**

Ekrany (`frontend/src/pages`): Login, Dashboard, Upload, Review
(weryfikacja — najcięższy ekran, 518 linii), MeetingDetail, Tasks, Decisions,
Briefing, Settings. Nawigacja to własny „router-lite" na `history.pushState`,
świadomie bez `react-router-dom`.

Materiały i rytuały będące faktyczną częścią używania produktu:

- **Dwa niezależne logowania** — Supabase Auth (email + hasło, bramka do
  panelu) oraz osobne Google OAuth (warunek wysyłki maili i eksportu). Bez
  tego drugiego część funkcji jest niedostępna i musi to być czytelnie
  komunikowane, nie zgłaszane jako surowy błąd.
- **Tryb demo bez Google** (`POST /auth/demo-login`) — najczęstsza droga
  wejścia dla oceniającej widowni, bo ekran zgody Google jest w statusie
  Testing i nie każdy jest dodany jako tester.
- **Dwa arkusze Google** — „Osoby" (kartoteka, synchronizowana ręcznie
  przyciskiem, nie w tle) i „Zadania RACI" (widok eksportowy).
- **Zimny start demo** — backend na darmowym planie Render usypia po ~15 min
  bezczynności; pierwsze wejście po przerwie trwa 30–60 s. To dotyczy dokładnie
  tej osoby, która ocenia produkt, i jest pierwszym doświadczeniem, jakie ma
  z aplikacją.
- **Przetwarzanie trwa minuty, nie sekundy** — transkrypcja i ekstrakcja idą
  w tle po uploadzie; stan „w toku" jest normalnym, częstym stanem ekranu.

## Capabilities and Constraints

Potwierdzone funkcje: upload wielu plików audio (`.mp3/.m4a/.wav/.aac/.ogg/.flac`)
do jednego spotkania lub wklejenie tekstu; transkrypcja z diaryzacją;
ekstrakcja zadań z deadlinem, rolami R/A/C/I, cytatem i poziomem pewności;
ekstrakcja twardych decyzji biznesowych (nie opinii); mapowanie nazwisk na
kartotekę osób; ekran weryfikacji z edycją inline; eksport do Sheets;
codzienne przypomnienia mailowe (APScheduler); semantyczne wyszukiwanie
decyzji (pgvector); briefing przed spotkaniem; drafty podsumowań w trzech
wariantach (formalny raport / oficjalne podsumowanie dla kontrahenta / luźna
wiadomość robocza).

Trwałe ograniczenia, których przyszłe prace nie mogą „naprawiać":

- **Jeden użytkownik.** Bez ról, uprawnień, zapraszania, kont zespołowych.
- **Postgres jest źródłem prawdy, Sheets to widok.** Zapis jednokierunkowy;
  ręczna edycja arkusza zostanie nadpisana. Statusy zmienia się w panelu.
- **Synchronizacja osób jest ręczna**, świadomie — nie ma jej w tle.
- **Sesja Google wygasa co ~7 dni** (ekran zgody External w statusie Testing,
  nie Workspace). Wygaśnięcie jest stanem normalnym i cyklicznym, nie awarią —
  interfejs musi je obsługiwać jako spodziewaną ścieżkę.
- **Przypomnienia wymagają działającego serwera** o poranku; zaległe z tego
  samego dnia są nadrabiane po starcie.
- **Interfejs jest wyłącznie po polsku.** Brak i18n, brak planu na nie.
- **Desktop + realny mobile** (potwierdzone). Telefon to prawdziwy scenariusz —
  sprawdzenie zadań i decyzji przed spotkaniem lub w drodze. Obecny kod tego
  nie spełnia: sticky nav z sześcioma linkami bez zwijania, stałe kontenery
  `max-w-2xl` / `max-w-4xl`. To luka do zamknięcia, nie stan docelowy.

Nierozstrzygnięte, do decyzji w przyszłości: czy demo ma prowadzić
oceniającego przez ścieżkę (onboarding / stan pusty z podpowiedzią), czy
zostawiać go samego z panelem.

## Brand Commitments

**Brak wiążących zobowiązań wizualnych — potwierdzone wprost.** Obecny wygląd
(wymuszony dark mode z czarnym tłem, akcent `blue-600`, ikony Phosphor, nazwa
„Analiza spotkań", brak logo poza `favicon.svg`) jest stanem zastanym, nie
systemem do ochrony. Przyszłe prace mogą wymienić paletę, motyw, typografię
i nazwę.

Jedyne trwałe zobowiązanie jest językowe, nie wizualne: **polszczyzna
rzeczowa, bez marketingowego tonu i bez żargonu AI.** Istniejące teksty
w interfejsie i dokumentacji nazywają rzeczy wprost („Weryfikacja",
„Nowe spotkanie", „kto ma co zrobić i do kiedy").

## Evidence on Hand

Realne, dostępne materiały:

- Działające demo: frontend `https://apka-podsumowanie-spotkan.vercel.app`,
  backend `https://apka-podsumowanie-spotkan-backend.onrender.com`. Baza demo
  zawiera w pełni fikcyjne dane, odizolowane od produkcyjnych.
- Syntetyczne transkrypty do pokazu: `transkrypt_dane_syntetyczne.txt`,
  `odpowiedz_cicd.txt`, `odpowiedz_incydent.txt`, `odpowiedz_infrastruktura.txt`.
- Prezentacje: `prezentacja/` (dwa PDF-y + szablon PPTX), zrzut w `video/`.
- Dokumentacja produktowa i techniczna: `PRZEWODNIK_UZYTKOWNIKA.md`,
  `OPIS_FINALNY.md`, `SPEC.md`, `OGRANICZENIA.md`, `podsumowanie aplikacji.md`.

Czego **nie ma** i czego nie wolno wymyślać: klientów, wdrożeń, testimoniali,
liczby użytkowników, benchmarków dokładności ekstrakcji, cennika, licencji,
gwarancji SLA, certyfikatów zgodności (RODO, SOC2 itp.). Aplikacja nie ma
żadnego realnego użytkownika poza autorem.

## Product Principles

1. **Człowiek zatwierdza, AI proponuje.** Każda ścieżka, która coś wysyła lub
   utrwala, przechodzi przez podgląd i świadomy klik. Projektowanie „na skróty"
   przez auto-wysyłkę łamie główny argument produktu.
2. **Niepewność jest widoczna, nie zamiatana.** Niska pewność AI,
   nierozpoznana osoba, wygasła sesja Google, przetwarzanie w toku, budzący
   się backend — to normalne stany, którym należą się pełnoprawne,
   zaprojektowane ekrany, a nie spinner albo surowy błąd.
3. **Dowód przy twierdzeniu.** Cytat źródłowy towarzyszy wyciągniętej pozycji.
   Wszędzie, gdzie aplikacja coś twierdzi, użytkownik musi móc sprawdzić skąd.
4. **Prostota ponad skalowalność.** Jeden użytkownik, jedna maszyna, brak
   kolejek i platform automatyzacji. Rozwiązania wprowadzające infrastrukturę
   „na wyrost" są sprzeczne z produktem.
5. **Czytelne dla kogoś, kto widzi to pierwszy raz.** Realny odbiorca nie ma
   wprawy ani instrukcji. Gęstość informacji nie może wygrać z możliwością
   zorientowania się, co się właśnie stało i co zrobić dalej.

# Przewodnik użytkownika

## Do czego służy ta aplikacja

Nagrywasz spotkanie (albo masz gotowy tekst rozmowy) — aplikacja sama
wyciąga z niego konkretne zadania („kto ma co zrobić i do kiedy"), pilnuje
terminów przypomnieniami mailowymi i prowadzi historię ważnych ustaleń
biznesowych, którą później możesz przeszukać.

Nie musisz nic notować w trakcie spotkania. Po nagraniu i krótkiej
weryfikacji masz gotową listę zadań rozesłaną do właściwych osób.

## Zanim zaczniesz — logowanie

Aplikacja ma dwa niezależne ekrany logowania, oba trzeba przejść:

1. **Logowanie do aplikacji** (email + hasło) — otwiera dostęp do panelu.
2. **„Zaloguj się przez Google"** (przycisk na Dashboardzie) — bez tego
   nie zadziała wysyłka maili (przypomnienia, briefingi, podsumowania) ani
   eksport do Google Sheets. To osobne logowanie, bo używa innego konta niż
   logowanie do samej appki.

Jeśli korzystasz z wersji demo, oba zestawy danych logowania dostajesz od
osoby, która Cię do niej zaprosiła. Logowanie przez Google trzeba **odnawiać
raz na tydzień** — jeśli po jakimś czasie przestaną chodzić maile, to
najpierw sprawdź, czy nie trzeba się po prostu zalogować ponownie.

Nie masz dostępu do konta Google zaproszonego jako tester (ekran zgody Google
jest w trybie Testing)? Na Dashboardzie, obok przycisku „Zaloguj się przez
Google", jest link **„Wypróbuj demo bez logowania Google"** — zakłada sesję
demo bez OAuth, więc od razu widzisz upload, weryfikację, zadania i rejestr
decyzji. W tym trybie nie zadziała nic, co wysyła maile (przypomnienia,
briefing, drafty podsumowań) — appka pokaże wtedy komunikat, że funkcja wymaga
połączonego konta Google.

## Krok po kroku: od nagrania do gotowych zadań

### 1. Wgrywanie spotkania

Panel → **Upload**. Podajesz:
- tytuł spotkania i datę,
- temat/dostawcę, którego dotyczy (z listy),
- plik audio (`.mp3`, `.m4a`, `.wav`, `.aac`, `.ogg`, `.flac`) **albo**
  gotowy tekst transkrypcji.

Jeśli nagranie jest długie (ponad godzinę) i masz je podzielone na kilka
plików, możesz wgrać wszystkie naraz do jednego spotkania — aplikacja skleja
je w kolejności.

### 2. Automatyczna transkrypcja i analiza

Dzieje się samo, w tle — nie musisz nic klikać. Zajmuje to zwykle kilka
minut (zależnie od długości nagrania). Aplikacja:
- zamienia mowę na tekst i rozpoznaje, kto mówi (na podstawie listy osób
  z arkusza — patrz niżej),
- wyciąga z rozmowy konkretne zadania: co, kto ma zrobić, do kiedy,
- przypisuje role: kto **wykonuje** (R), kto **odpowiada za efekt** (A),
  kogo trzeba **konsultować** (C), kogo tylko **poinformować** (I),
- wyciąga też twarde ustalenia/decyzje biznesowe (np. „ustalono rabat 3%").

Jeśli coś nie padło jasno w rozmowie (np. nie wiadomo, kto ma coś zrobić),
aplikacja **nie zgaduje** — zostawia puste pole do uzupełnienia przez Ciebie
na następnym ekranie.

### 3. Weryfikacja (najważniejszy ekran)

Panel → **Weryfikacja**. Tu widzisz wszystko, co AI wyciągnęło z rozmowy,
zanim cokolwiek zostanie zapisane na stałe:
- każde zadanie ma **cytat z transkryptu**, na podstawie którego zostało
  wyciągnięte — nie musisz słuchać/czytać całej rozmowy, żeby sprawdzić,
  czy to się zgadza,
- pozycje, których AI jest mniej pewna, są wizualnie wyróżnione,
- jeśli AI nie rozpoznała, o kogo chodzi (np. dwie osoby o tym samym
  imieniu), musisz to ręcznie doprecyzować — **bez tego nie zatwierdzisz**
  zadania,
- możesz jednym kliknięciem usunąć pozycję, która zadaniem nie jest.

Poprawiasz co trzeba i klikasz **Zatwierdź**. Od tego momentu zadania
i decyzje trafiają do reszty systemu.

### 4. Zadania trafiają do wspólnego arkusza

Po zatwierdzeniu zadania automatycznie lądują w Google Sheets, z podziałem
na role RACI — możesz go udostępnić zespołowi do wglądu.

**Ważne:** arkusz jest tylko „do czytania" z Twojej strony w sensie
edycji — jeśli ktoś zmieni coś ręcznie w arkuszu, ta zmiana zostanie
nadpisana przy kolejnej synchronizacji. Statusy zadań (zrobione/otwarte)
zmieniasz **w panelu aplikacji**, nie w arkuszu.

### 5. Przypomnienia o terminach — dzieją się same

Każdego ranka aplikacja sama sprawdza, które zadania mają zbliżający się
termin (domyślnie: za 2 dni), i wysyła spersonalizowany mail do osoby
odpowiedzialnej za wykonanie (z osobą odpowiedzialną za efekt w DW). Mail
idzie z Twojego konta Google — odbiorca widzi wiadomość od Ciebie, nie od
bota.

Warunek: komputer/serwer z aplikacją musi w tym momencie działać. Jeśli był
wyłączony rano, aplikacja nadrabia zaległe przypomnienia **z tego samego
dnia** zaraz po uruchomieniu.

### 6. Rejestr decyzji — szukaj po sensie, nie po słowie

Panel → **Decyzje**. Wszystkie twarde ustalenia z rozmów (nie opinie, nie
pomysły — tylko to, co faktycznie przesądzono) trafiają tu, pogrupowane po
temacie/dostawcy.

Wyszukiwarka rozumie sens pytania, nie tylko dopasowuje słowa — np.
szukając „rabat" znajdziesz decyzję o obniżce ceny, nawet jeśli słowo
„rabat" w niej nie padło.

### 7. Briefing przed kolejnym spotkaniem

Panel → **Briefing** → wybierasz temat/dostawcę, na który się szykujesz.
Dostajesz mailem krótką notatkę: na czym stanęło ostatnio, co zalega
z zadaniami, co wymaga decyzji na najbliższym spotkaniu.

Briefing najpierw pokazuje Ci podgląd — wysyłka to zawsze osobny, świadomy
klik. Nic nie wychodzi automatycznie bez Twojej zgody.

### 8. Gotowe podsumowanie do wysłania

Panel → wybierasz spotkanie → **Generuj podsumowanie**. Do wyboru trzy
warianty gotowego maila:
- **formalny raport** — dla zarządu (cel, ustalenia, ryzyka, decyzje do
  podjęcia),
- **oficjalne podsumowanie** — dla dostawcy/kontrahenta (tylko ustalenia
  obustronne, bez wewnętrznych notatek),
- **luźna wiadomość robocza** — dla zespołu (kto, co, do kiedy).

Zawsze widzisz podgląd, wpisujesz adresata i dopiero wtedy wysyłasz —
podobnie jak przy briefingu, AI nigdy nie wysyła maila sama.

## Osoby uczestniczące w spotkaniach

Lista osób (imię, nazwisko, e-mail, ewentualne „jak ktoś ją nazywa w
rozmowie") mieszka w osobnym arkuszu Google. Jeśli dojdzie nowa osoba albo
zmieni się czyjś e-mail, edytujesz arkusz, a potem w panelu klikasz
**Synchronizuj osoby** — to krok ręczny, aplikacja nie robi tego sama
w tle.

## Skrócone podsumowanie funkcji

| Funkcja | Co robi |
|---|---|
| Upload audio/tekstu | Wgrywasz nagranie albo gotowy tekst spotkania |
| Transkrypcja z etykietami mówców | Zamienia mowę na tekst, rozpoznaje kto mówi |
| Automatyczna ekstrakcja RACI | Wyciąga zadania, terminy i role z rozmowy |
| Ekran weryfikacji | Sprawdzasz i poprawiasz wyniki AI przed zapisem |
| Eksport do Google Sheets | Zatwierdzone zadania trafiają do wspólnego arkusza |
| Przypomnienia mailowe | Codzienne automatyczne maile o zbliżających się terminach |
| Rejestr decyzji | Przeszukiwalna historia ustaleń biznesowych |
| Briefing przed spotkaniem | Notatka mailowa: gdzie stanęliśmy, co zalega |
| Drafty podsumowań | Gotowe maile w trzech wariantach do przejrzenia i wysłania |

Pełny, bardziej techniczny opis każdej funkcji i decyzji stojących za nimi:
[OPIS_FINALNY.md](OPIS_FINALNY.md). Znane ograniczenia aplikacji:
[OGRANICZENIA.md](OGRANICZENIA.md).

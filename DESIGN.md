---
name: Analiza spotkań
description: Ciemny, płaski panel operatorski, w którym każdy kolor jest odczytem stanu.
colors:
  void: "#000000"
  well: "oklch(14.1% 0.005 285.823)"
  surface: "oklch(21% 0.006 285.885)"
  surface-raised: "oklch(27.4% 0.006 286.033)"
  stroke: "oklch(55.2% 0.016 285.938)"
  ink-max: "#ffffff"
  ink: "oklch(96.7% 0.001 286.375)"
  ink-muted: "oklch(87.1% 0.006 286.286)"
  ink-dim: "oklch(70.5% 0.015 286.067)"
  ink-faint: "oklch(55.2% 0.016 285.938)"
  signal: "oklch(54.6% 0.245 262.881)"
  signal-bright: "oklch(62.3% 0.214 259.815)"
  signal-text: "oklch(70.7% 0.165 254.624)"
  state-ok: "oklch(76.5% 0.177 163.223)"
  state-attention: "oklch(82.8% 0.189 84.429)"
  state-attention-text: "oklch(87.9% 0.169 91.605)"
  state-blocked: "oklch(70.4% 0.191 22.216)"
  state-blocked-text: "oklch(80.8% 0.114 19.571)"
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', 'Noto Sans', Arial, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.333
    letterSpacing: "-0.025em"
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', 'Noto Sans', Arial, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "-0.025em"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', 'Noto Sans', Arial, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.428
    letterSpacing: "normal"
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', 'Noto Sans', Arial, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.333
    letterSpacing: "normal"
rounded:
  sm: "0.25rem"
  md: "0.375rem"
  xl: "0.75rem"
  full: "9999px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "0.75rem"
  lg: "1rem"
  xl: "1.5rem"
  2xl: "2rem"
components:
  button-primary:
    backgroundColor: "{colors.signal}"
    textColor: "{colors.ink-max}"
    rounded: "{rounded.md}"
    padding: "0.5rem 1rem"
    typography: "{typography.body}"
  button-primary-hover:
    backgroundColor: "{colors.signal-bright}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.md}"
    padding: "0.5rem 1rem"
    typography: "{typography.body}"
  button-secondary-hover:
    backgroundColor: "{colors.surface-raised}"
  input:
    backgroundColor: "{colors.well}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0.5rem 0.75rem"
    typography: "{typography.body}"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.xl}"
    padding: "1.5rem 2rem"
  card-compact:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.xl}"
    padding: "0.75rem 1rem"
  badge-neutral:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.full}"
    padding: "0.125rem 0.5rem"
    typography: "{typography.label}"
  badge-positive:
    textColor: "{colors.state-ok}"
    rounded: "{rounded.full}"
    padding: "0.125rem 0.5rem"
    typography: "{typography.label}"
  badge-warning:
    textColor: "{colors.state-attention}"
    rounded: "{rounded.full}"
    padding: "0.125rem 0.5rem"
    typography: "{typography.label}"
  badge-negative:
    textColor: "{colors.state-blocked}"
    rounded: "{rounded.full}"
    padding: "0.125rem 0.5rem"
    typography: "{typography.label}"
  nav-link:
    textColor: "{colors.ink-dim}"
    rounded: "{rounded.md}"
    padding: "0.375rem 0.75rem"
    typography: "{typography.label}"
  nav-link-active:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink-max}"
    rounded: "{rounded.md}"
    padding: "0.375rem 0.75rem"
---

# Design System: Analiza spotkań

## Overview

**Creative North Star: „Sala kontrolna"**

To jest panel przyrządów, nie strona. Operator siedzi przed ciemną konsolą, na
której **wszystko, co świeci, coś znaczy**. W spoczynku interfejs jest niemal
achromatyczny — czerń i sześć stopni szarości. Kolor pojawia się wyłącznie
wtedy, gdy system ma coś do zakomunikowania: że pozycja jest niepewna, że coś
blokuje zatwierdzenie, że sprawa jest domknięta, że tutaj można działać. Ta
dyscyplina jest jedynym powodem, dla którego gęsty ekran weryfikacji daje się
przeskanować wzrokiem w kilka sekund.

Materiał jest płaski i matowy. W całym projekcie nie ma ani jednego cienia —
głębia powstaje wyłącznie przez ton: czerń tła, ciemniejsze wgłębienia pól
formularza, jaśniejsze płyty kart. Powierzchnia nie udaje papieru ani szkła;
udaje panel, na którym elementy są *wpuszczone* albo *nałożone*, nigdy
uniesione. Ruch jest minimalny i wyłącznie potwierdzający — przyciski wciskają
się o 2% przy kliknięciu i to cała animacja, jaką ten system ma.

Gęstość jest wysoka, ale nie ciasna. Typografia stoi na jednym rozmiarze
roboczym (14px) z dwoma stopniami wyciszenia w kolorze zamiast w wielkości —
hierarchię niesie kontrast szarości, nie skala. To pozwala trzymać dużo
informacji na ekranie bez efektu tabeli enterprise'owej.

**Key Characteristics:**

- Achromatyczny w spoczynku; kolor jest wyłącznie odczytem stanu
- Zero cieni — głębia wyłącznie tonalna (czerń → wgłębienie → płyta)
- Jeden rozmiar roboczy tekstu, hierarchia przez kontrast szarości
- Dwa promienie: `0.75rem` na pojemnikach, `0.375rem` na kontrolkach
- Ruch tylko jako potwierdzenie dotyku, nigdy jako dekoracja
- Font systemowy, bez ładowania własnego kroju

## Colors

Skala neutralna niesie całą strukturę; cztery kolory sygnałowe niosą całe
znaczenie. Żaden kolor nie jest dekoracją.

### Primary

- **Sygnał operacyjny** (`{colors.signal}`): jedyny kolor, którym interfejs
  mówi „tutaj działasz". Wypełnia przycisk akcji głównej. W jaśniejszym
  wariancie (`{colors.signal-bright}`) obsługuje hover oraz — jako pierścień
  `ring-2` — fokus klawiaturowy na każdej kontrolce w aplikacji.
  `{colors.signal-text}` to jego czytelna forma tekstowa na ciemnym tle.

### Secondary

Brak. System ma jeden akcent i trzy kolory stanu; wprowadzenie drugiego
akcentu złamałoby zasadę odczytu.

### Tertiary

- **Stan: domknięte** (`{colors.state-ok}`): zadanie zrobione, spotkanie
  zatwierdzone. Kolor pojawia się rzadko i zawsze oznacza „nie wymaga uwagi".
- **Stan: niepewne** (`{colors.state-attention}`): pewność AI poniżej 0.7,
  spotkanie w toku przetwarzania, zadanie otwarte. Kolor pracy w biegu.
- **Stan: zablokowane** (`{colors.state-blocked}`): nierozwiązane nazwisko,
  błąd przetwarzania, błąd formularza. Jedyny kolor, który oznacza „nie
  pójdziesz dalej".

### Neutral

- **Pustka** (`{colors.void}`): tło całej aplikacji, ustawione wprost w
  `index.css`, nie przez klasę. Czysta czerń, nie „prawie czerń".
- **Wgłębienie** (`{colors.well}`): tło pól formularza i obszarów, w które
  użytkownik wpisuje. Ciemniejsze niż płyta — pole jest *wpuszczone*.
- **Płyta** (`{colors.surface}`): tło kart, tabel, paneli filtrów.
- **Płyta uniesiona** (`{colors.surface-raised}`): aktywna zakładka nawigacji,
  neutralny badge. Ten sam odcień pełni funkcję kreski działowej między
  sekcjami i wokół kart.
- **Obrys kontrolki** (`{colors.stroke}`): ramka pól, przycisków wtórnych,
  checkboxów. Wyraźnie jaśniejszy niż kreska działowa, bo kontrolka ma się
  odróżniać od dekoracji — i musi to być jasność, nie tylko zamiar: to jedyny
  neutralny token w tym systemie, który podlega WCAG 1.4.11 (Non-text
  Contrast, próg 3:1), bo jest granicą interaktywnego elementu, nie ozdobą.
  Pierwotna wersja tego dokumentu wskazywała `zinc-700`; zmierzony kontrast
  wyniósł 1.70–1.91:1 na każdym tle, na którym obrys faktycznie występuje
  (pole, karta, strona) — poniżej progu nawet dla samej grafiki. `zinc-500`
  jest najciemniejszym odcieniem, który przechodzi 3:1 na wszystkich trzech.
- **Tusz** — trzy stopnie wyciszenia dla tekstu, w kolejności ważności:
  `{colors.ink-max}` (nagłówki i aktywna nawigacja), `{colors.ink}` (treść
  wpisana przez użytkownika i wyniki), `{colors.ink-dim}` (etykiety pól,
  metadane, podpisy, stany puste, nieaktywna nawigacja — koń roboczy
  wyciszonego tekstu w całym systemie). `{colors.ink-faint}` **nie jest już
  tokenem tekstowym** — zmierzony kontrast 3.67:1 na płycie i 4.35:1 na
  czerni nie przechodzi progu 4.5:1 dla tekstu (WCAG 1.4.3). Pierwotna wersja
  tego dokumentu przypisywała mu metadane/podpisy/stany puste; to była
  pomyłka, poprawiona po zmierzeniu, nie po wyglądzie. Token zostaje wyłącznie
  dla grafiki (ikony w stanach pustych, próg 3:1), gdzie nadal się mieści.

### Named Rules

**Zasada Odczytu.** Każdy piksel, który nie jest w skali neutralnej, jest
odczytem stanu. Niebieski = „tu jest akcja, to jest aktywne, tu jest fokus".
Bursztyn = „niepewne". Czerwień = „zablokowane". Zieleń = „domknięte". Nie
istnieje kolor, który nic nie znaczy — jeśli nie umiesz powiedzieć, jaki stan
sygnalizuje, użyj skali zinc.

**Zasada Odwrotnej Krycia.** Im większa powierzchnia, tym słabszy barwnik.
Podbarwiony badge stoi na `/15`, podbarwiona karta na `/[0.06]`. Duża plama
koloru na 15% zamieniłaby panel w alert.

**Zasada Ramki i Wypełnienia.** Stan podbarwia powierzchnię **i** obrys razem
(`border-red-500/40` + `bg-red-500/[0.06]`). Samo tło jest za słabe, żeby
przebić się przez gęstość ekranu weryfikacji; sam obrys ginie w kresce
działowej.

**Zasada Placeholdera.** Tekst zastępczy w polu (`placeholder`) jest tekstem
w rozumieniu WCAG 1.4.3, nie dekoracją — musi trzymać 4.5:1 tak jak każda inna
treść. `zinc-400` na `{colors.well}` daje 7.59:1; ciemniejsze odcienie
(`zinc-500` = 4.12:1, `zinc-600` = 2.58:1) nie przechodzą. „Wygaszony, bo to
tylko podpowiedź" jest błędem rozumowania — placeholder bywa jedynym opisem
pola, gdy etykieta jest wizualna, a nie semantyczna.

## Typography

**Display Font:** brak — system korzysta z kroju systemowego
(`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, …`)
**Body Font:** ten sam krój systemowy
**Label/Mono Font:** `ui-monospace` wyłącznie w polu wklejania transkryptu

**Character:** neutralna, bezosobowa maszynowość. Krój nie ma opinii — całą
osobowość systemu niosą kolor i gęstość. To wybór zgodny z „salą kontrolną":
przyrząd nie ma charakteru pisma.

### Hierarchy

- **Display** (600, 1.5rem, `-0.025em`): nagłówek strony. Dokładnie jeden na
  ekran, zawsze w `{colors.ink-max}`.
- **Title** (600, 1.25rem, `-0.025em`): nagłówek karty logowania i tytuły
  bloków. Używany oszczędnie.
- **Body** (400, 0.875rem): koń roboczy całego interfejsu — treść zadań,
  decyzje, wartości pól, przyciski. Ok. 70% tekstu w aplikacji.
- **Label** (500, 0.75rem): etykiety pól, badge'e, metadane, podpisy pod
  wynikami. Zawsze w `{colors.ink-dim}` — `{colors.ink-faint}` nie niesie już
  tekstu, patrz Colors → Neutral.

### Named Rules

**Zasada Dwóch Rozmiarów.** Hierarchię wewnątrz karty budujesz **kolorem
tuszu, nie wielkością**. W obrębie jednego komponentu dozwolone są najwyżej
dwa rozmiary (`body` + `label`); trzeci oznacza, że komponent powinien zostać
rozbity.

**Zasada Cytatu.** Cytat ze źródła jest zawsze kursywą, w rozmiarze `label`,
w `{colors.ink-dim}`, w polskich cudzysłowach „…". Nigdy nie konkuruje
wizualnie z treścią, którą uzasadnia — jest przypisem, nie nagłówkiem.

## Layout

Jedna kolumna wyśrodkowana pod sticky nawigacją. Dwie szerokości kontenera,
wybierane per ekran: **`max-w-2xl` (42rem)** dla ekranów czytania i
formularzy (Dashboard, Upload, Briefing, Ustawienia, szczegóły spotkania) oraz
**`max-w-4xl` (56rem)** dla ekranów pracy z wieloma pozycjami naraz (Zadania,
Decyzje, Weryfikacja). Padding strony: `1rem` w poziomie, `2.5rem` w pionie.

Rytm pionowy stoi na skoku 4px. W praktyce system używa pięciu odstępów:
`0.25rem` (etykieta do kontrolki), `0.5rem` (elementy w rzędzie), `0.75rem`
(pola w gridzie), `1rem` (pola w kolumnie), `1.5rem` (bloki wewnątrz karty).
Karty rozdziela `0.75rem`.

Nawigacja jest przyklejona do góry (`sticky top-0`), na tle `bg-black/95`
z `backdrop-blur`, oddzielona kreską działową.

### Named Rules

**Zasada Szerokości Zadania.** Szerokość kontenera wynika z tego, czy
użytkownik **czyta jedną rzecz**, czy **porównuje wiele**. Nie z tego, ile
treści akurat jest.

> **Uwaga o stanie faktycznym:** system nie ma dziś warstwy responsywnej —
> w całym `src/` nie występuje ani jeden prefiks `sm:` / `md:` / `lg:`.
> Nawigacja to sześć linków w jednym rzędzie bez zwijania, a kontenery mają
> stałą szerokość maksymalną bez zachowania mobilnego. PRODUCT.md oznacza
> telefon jako realny scenariusz użycia, więc jest to **luka do zamknięcia,
> nie inwariant systemu**.

## Elevation & Depth

**Ten system nie ma cieni.** `grep` na `shadow-*` w całym `src/` zwraca zero
trafień i jest to decyzja, nie przeoczenie. Głębia jest wyłącznie tonalna
i działa w trzech krokach: czerń tła → `{colors.surface}` dla płyty
nałożonej → `{colors.well}` dla pola wpuszczonego. Kierunek odczytujesz
z jasności, nie z rozmycia.

Jedyny efekt optyczny w systemie to `backdrop-blur` pod sticky nawigacją —
i on też nie tworzy uniesienia, tylko utrzymuje czytelność paska nad
przewijaną treścią.

### Named Rules

**Zasada Płaskiej Konsoli.** Powierzchnie są płaskie zawsze. Jeśli element
wymaga wyróżnienia, dostaje inny **ton** albo **obrys** — nigdy cień, nigdy
gradient, nigdy poświatę.

## Shapes

Dwa promienie i jeden wyjątek, konsekwentnie w całym projekcie:

- **`{rounded.xl}` (0.75rem)** — wszystko, co jest pojemnikiem: karty,
  tabele, panele filtrów, formularz logowania. Promień na tyle duży, żeby
  płyta czytała się jako osobny obiekt.
- **`{rounded.md}` (0.375rem)** — wszystko, co jest kontrolką: przyciski,
  pola, selecty, linki nawigacji.
- **`{rounded.full}`** — wyłącznie badge statusu. Pigułka to jedyny kształt
  w systemie, który nie jest prostokątem, i właśnie dlatego czyta się
  natychmiast jako etykieta, a nie jako element klikalny.
- **`{rounded.sm}` (0.25rem)** — drobne żetony wewnątrz kart (badge pewności,
  znacznik „nierozwiązane nazwisko"), które muszą siedzieć ciaśniej niż
  pigułka statusu.

Obrys ma zawsze 1px. System nie używa grubszych ramek — z jednym wyjątkiem
pierścienia fokusa (`ring-2`), który jest celowo cięższy niż cokolwiek innego.

### Named Rules

**Zasada Pojemnik/Kontrolka.** Promień informuje o roli. Jeśli w to klikasz —
`{rounded.md}`. Jeśli to coś zawiera — `{rounded.xl}`. Element o promieniu
pojemnika, który jest klikalny, jest błędem systemu.

## Components

### Buttons

- **Shape:** delikatnie zaokrąglony prostokąt (`{rounded.md}`)
- **Primary:** pełne wypełnienie `{colors.signal}`, biały tekst, waga 500,
  padding `0.5rem 1rem` (wariant kompaktowy `0.25rem 0.75rem`)
- **Secondary:** przezroczyste tło, obrys `{colors.stroke}`, tekst
  `{colors.ink-muted}` — ta sama geometria, inna waga wizualna
- **Hover:** primary rozjaśnia się do `{colors.signal-bright}`; secondary
  dostaje wypełnienie `{colors.surface-raised}`
- **Active:** `scale(0.98)` — dotykowe potwierdzenie, wspólne dla obu
  wariantów i dla przycisku wylogowania
- **Disabled:** krycie 50%, wygaszona reakcja na wciśnięcie

### Cards / Containers

- **Corner Style:** `{rounded.xl}`
- **Background:** `{colors.surface}`
- **Border:** 1px `{colors.surface-raised}`
- **Shadow Strategy:** brak — patrz Elevation & Depth
- **Internal Padding:** `1.5rem 2rem` dla kart-sekcji, `0.75rem 1rem` dla
  kart-pozycji na listach

### Inputs / Fields

- **Style:** wgłębienie `{colors.well}`, obrys 1px `{colors.stroke}`,
  promień `{rounded.md}`, tekst `{colors.ink}`
- **Focus:** `outline: none` zastąpione pierścieniem `ring-2`
  w `{colors.signal-bright}`. Pierścień jest jedynym elementem systemu
  o grubości 2px — fokus ma być nie do przeoczenia
- **Etykieta:** zawsze **nad** polem, rozmiar `label`, kolor
  `{colors.ink-dim}`, odstęp `0.25rem`
- **Kontrolki natywne:** checkbox i radio dostają `accent-color`
  `{colors.signal-bright}`; ikona kalendarza w polu daty jest odwracana
  filtrem i wygaszana do 60% krycia

### Navigation

Poziomy pasek przyklejony do góry, tło `bg-black/95` z `backdrop-blur`,
kreska działowa u dołu. Nazwa aplikacji po lewej (waga 600, rozmiar `label`,
`tracking-tight`), linki obok, wylogowanie dopchnięte na prawą krawędź.
Link nieaktywny: `{colors.ink-dim}`, hover rozjaśnia tusz bez zmiany tła.
Link aktywny: wypełnienie `{colors.surface-raised}`, tusz `{colors.ink-max}`.

> **Uwaga o stanie faktycznym:** przyjęta doktryna akcentu obejmuje
> sygnalizowanie tego, co aktywne — a aktywna zakładka jest dziś wyłącznie
> szara. To rozjazd między zapisaną zasadą a implementacją, do domknięcia
> przy najbliższej pracy nad nawigacją.

### Karta triage (komponent sygnaturowy)

Wizualne serce produktu — jedna karta pozycji na ekranie weryfikacji, która
tym samym pudełkiem komunikuje trzy różne poziomy pilności:

- **Zablokowana** (nierozwiązane nazwisko): obrys `red/40`, wypełnienie
  `red/[0.06]`, dodatkowo żeton „nierozwiązane nazwisko" w rogu.
  Zatwierdzenie całego ekranu jest niemożliwe, dopóki taka karta istnieje
- **Niepewna** (pewność AI < 0.7): obrys `amber/40`, wypełnienie
  `amber/[0.06]`, badge pewności przechodzi z szarego na bursztynowy
- **W porządku:** zwykła karta — obrys `{colors.surface-raised}`,
  wypełnienie `{colors.surface}`

Pod polami edycyjnymi zawsze siedzi cytat ze źródła, kursywą, w rozmiarze
`label` — to on zamienia weryfikację ze zgadywania w sprawdzanie.

Priorytet stanów jest twardy: **blokada wygrywa z niepewnością**. Karta
nierozwiązana o niskiej pewności jest czerwona, nie bursztynowa.

### Badge statusu

Pigułka (`{rounded.full}`), rozmiar `label`, waga 500, padding
`0.125rem 0.5rem`. Cztery tony mapowane ze stanu domenowego, nie dobierane
ręcznie: neutralny (wypełnienie `{colors.surface-raised}`), pozytywny,
ostrzegawczy i negatywny (wypełnienie barwą stanu na `/15`, tekst w pełnej
barwie stanu). Nieznany status degraduje się do tonu neutralnego z surową
wartością jako etykietą — system nigdy nie pokazuje pustego badge'a.

## Do's and Don'ts

### Do:

- **Do** trzymać interfejs achromatyczny w spoczynku. Zanim użyjesz koloru,
  nazwij stan, który sygnalizuje.
- **Do** budować głębię tonem: `{colors.void}` → `{colors.surface}` →
  `{colors.well}`. Trzy kroki wystarczają na każdy ekran.
- **Do** podbarwiać stan jednocześnie na obrysie (`/40`) i wypełnieniu
  (`/[0.06]`) — patrz Zasada Ramki i Wypełnienia.
- **Do** stawiać cytat źródłowy przy każdej pozycji wygenerowanej przez AI,
  kursywą w rozmiarze `label`. To jest pozycjonowanie produktu wyrażone
  typografią.
- **Do** dawać każdej kontrolce widoczny pierścień fokusa `ring-2` w
  `{colors.signal-bright}`. Nadpisujesz `outline: none` — masz obowiązek dać
  zamiennik.
- **Do** trzymać dwa promienie: pojemnik `{rounded.xl}`, kontrolka
  `{rounded.md}`.
- **Do** potwierdzać dotyk przez `scale(0.98)` na wciśnięciu. To jedyna
  animacja, jakiej ten system potrzebuje.

### Don't:

- **Don't** wprowadzać cieni, gradientów ani poświat. System jest płaski
  i ma pozostać płaski.
- **Don't** używać koloru dekoracyjnie. Kolor bez znaczenia stanu łamie
  Zasadę Odczytu i psuje skanowalność ekranu weryfikacji.
- **Don't** sięgać po słownik czatu z AI: dymki rozmowy, awatar asystenta,
  animacja „pisania", iskierki, „✨". AI jest tu silnikiem ekstrakcji
  działającym w tle, nie rozmówcą — i nigdy nie mówi pierwszej osobie.
- **Don't** zsuwać się w enterprise'ową szarość: tabele bez oddechu, ramka
  wokół każdej komórki, tekst poniżej 12px. Gęsto nie znaczy ciasno —
  rytm 4px i cztery stopnie tuszu są po to, żeby dało się to czytać.
- **Don't** dodawać trzeciego rozmiaru tekstu wewnątrz komponentu. Jeśli
  hierarchia nie mieści się w `body` + `label`, komponent jest za duży.
- **Don't** oznaczać barwą stanu czegoś, czego użytkownik nie może
  rozwiązać. Czerwień zobowiązuje: skoro blokuje, musi obok stać kontrolka,
  która odblokowuje.

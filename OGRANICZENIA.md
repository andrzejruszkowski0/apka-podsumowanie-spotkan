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

## 2. Konto Google w trybie Testing/External, nie Workspace

Konto użyte w projekcie (`andrzejruszkowski0@gmail.com`) to zwykły Gmail,
nie Google Workspace. Google nie oferuje wtedy trybu **Internal** —
aplikacja działa w trybie **External / Testing**.

**Konsekwencja:** refresh token wygasa co ok. **7 dni**. Raz na tydzień
trzeba kliknąć "Zaloguj się przez Google" ponownie, inaczej:
- wysyłka przypomnień o zadaniach (Etap 8),
- wysyłka briefingów (Etap 9),
- wysyłka draftów podsumowań (Etap 10),

przestaną działać po cichu, dopóki nie nastąpi ponowne logowanie. Aplikacja
obsługuje to czytelnym komunikatem zamiast crasha, ale to nie jest
"ustaw i zapomnij" — wymaga cyklicznej uwagi właściciela.

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

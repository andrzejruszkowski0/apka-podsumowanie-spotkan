# Dlaczego nie da się po prostu wysłać linku do aplikacji

Krótka odpowiedź: nie w obecnej postaci — i to jest świadoma decyzja
architektoniczna, nie brak funkcji.

## Dlaczego nie da się po prostu wysłać linku

- Backend nasłuchuje tylko na `127.0.0.1` (SPEC.md §8) — to celowe
  ograniczenie bezpieczeństwa, żeby nic z zewnątrz nie miało dostępu. Z
  innego komputera, nie mówiąc o internecie, nie da się tam wejść.
- Frontend to serwer deweloperski Vite (`npm run dev`), nie działa poza
  Twoim komputerem.
- CORS jest zablokowany tylko do `http://localhost:5173`.
- Logowanie Google jest w trybie **Testing** — może się zalogować tylko
  konto, które zostało ręcznie dodane jako "Test user" w konsoli Google
  Cloud. Czyjeś inne konto Google zostałoby odrzucone.
- To narzędzie jednoosobowe z prawdziwymi danymi biznesowymi (np. negocjacje
  z "Dostawcą X") — nie jest pomyślane jako coś do udostępniania.

## Co realnie można zrobić

1. **Udostępnić ekran** (Zoom/Teams/Meet) i pokazać na żywo — najprostsze,
   zero zmian w kodzie, zero ryzyka.
2. Jeśli komuś naprawdę zależy, żeby **samodzielnie poklikał** — wymaga to
   prawdziwego hostingu: backend na serwerze publicznym, zbudowany
   frontend, zmieniony CORS, dodanie tej osoby jako test-usera w Google
   OAuth (albo przejście na tryb produkcyjny). To osobny kawałek pracy, nie
   "wyślij link".

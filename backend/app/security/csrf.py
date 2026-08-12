"""Ochrona CSRF dla mutujących żądań.

Cookie sesji jest SameSite=None w produkcji (frontend na Vercelu, backend na
Renderze — patrz `session_cookie_secure` w config.py), więc przeglądarka
dołącza je także do żądań wychodzących z obcej strony. Sam CORS tego nie
zatrzymuje: ogranicza odczyt odpowiedzi, ale prosty POST bez nietypowych
nagłówków i tak dociera do endpointu i wykonuje się z sesją ofiary.

Token synchronizacyjny zamiast double-submit cookie: front i backend siedzą na
różnych domenach, więc JS na froncie i tak nie odczytałby cookie ustawionego
przez backend. Token żyje w sesji, front pobiera go z GET /auth/csrf i odsyła w
nagłówku X-CSRF-Token. Sam wymóg nietypowego nagłówka wymusza preflight CORS,
którego obca domena nie przejdzie (allow_origins to tylko frontend_origin);
porównanie wartości tokena jest drugą warstwą, na wypadek gdyby CORS został
kiedyś rozluźniony.
"""

from __future__ import annotations

import secrets

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

SESSION_KEY = "csrf_token"
HEADER_NAME = "X-CSRF-Token"

# TRACE/HEAD dla porządku — Starlette i tak ich tu nie routuje, ale lista ma
# odpowiadać definicji "safe method" z RFC 9110, a nie temu, co akurat działa.
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})


def get_or_create_token(request: Request) -> str:
    token = request.session.get(SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[SESSION_KEY] = token
    return token


def is_valid(request: Request) -> bool:
    expected = request.session.get(SESSION_KEY)
    provided = request.headers.get(HEADER_NAME)
    if not expected or not provided:
        return False
    return secrets.compare_digest(expected, provided)


class CsrfMiddleware(BaseHTTPMiddleware):
    """Blokuje mutujące żądania bez ważnego tokena.

    Musi być dodany PRZED CORSMiddleware (czyli być od niego wewnętrzny), żeby
    preflight OPTIONS obsłużył CORS i nie dostał tu 403, oraz wewnątrz
    SessionMiddleware, żeby `request.session` było już wczytane.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method not in SAFE_METHODS and not is_valid(request):
            return JSONResponse(
                status_code=403,
                content={"detail": "Brak lub nieprawidłowy token CSRF — odśwież stronę i spróbuj ponownie."},
            )
        return await call_next(request)

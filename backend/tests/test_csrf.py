"""Testy middleware CSRF na minimalnej aplikacji.

Celowo nie importujemy app.main — ono buduje engine bazy i scheduler, a tu
chodzi wyłącznie o zachowanie samego middleware. Kolejność add_middleware jest
taka sama jak w main.py (CSRF najbardziej wewnętrzny, sesja najbardziej
zewnętrzna), bo od niej zależy, czy request.session jest wczytane.
"""

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.security.csrf import HEADER_NAME, CsrfMiddleware, get_or_create_token


def _client() -> TestClient:
    app = FastAPI()

    @app.get("/token")
    def token(request: Request) -> dict[str, str]:
        return {"csrf_token": get_or_create_token(request)}

    @app.post("/mutate")
    def mutate() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/read")
    def read() -> dict[str, str]:
        return {"status": "ok"}

    app.add_middleware(CsrfMiddleware)
    app.add_middleware(SessionMiddleware, secret_key="test-secret")
    return TestClient(app)


def test_get_passes_without_token():
    assert _client().get("/read").status_code == 200


def test_post_without_token_is_rejected():
    assert _client().post("/mutate").status_code == 403


def test_post_with_wrong_token_is_rejected():
    client = _client()
    client.get("/token")
    response = client.post("/mutate", headers={HEADER_NAME: "nie-ten-token"})
    assert response.status_code == 403


def test_post_with_valid_token_passes():
    client = _client()
    token = client.get("/token").json()["csrf_token"]
    response = client.post("/mutate", headers={HEADER_NAME: token})
    assert response.status_code == 200


def test_token_is_stable_within_session():
    client = _client()
    first = client.get("/token").json()["csrf_token"]
    second = client.get("/token").json()["csrf_token"]
    assert first == second


def test_token_from_other_session_is_rejected():
    """Token wycieknięty z innej sesji nie może przejść — samo posiadanie
    poprawnie wyglądającego stringa nie wystarcza, musi zgadzać się z sesją."""
    stolen = _client().get("/token").json()["csrf_token"]
    victim = _client()
    victim.get("/token")
    assert victim.post("/mutate", headers={HEADER_NAME: stolen}).status_code == 403

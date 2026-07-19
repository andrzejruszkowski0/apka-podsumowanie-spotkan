"""Szyfrowanie tokenów OAuth w spoczynku (cryptography.fernet)."""

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


class TokenEncryptionNotConfigured(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    key = settings.token_encryption_key
    if not key:
        raise TokenEncryptionNotConfigured(
            "TOKEN_ENCRYPTION_KEY nie jest ustawiony w .env. "
            "Wygeneruj: python -c \"from cryptography.fernet import Fernet; "
            'print(Fernet.generate_key().decode())"'
        )
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise TokenEncryptionNotConfigured(
            "TOKEN_ENCRYPTION_KEY ma nieprawidłowy format (oczekiwany klucz Fernet)."
        ) from exc


def encrypt(value: str) -> bytes:
    return _fernet().encrypt(value.encode())


def decrypt(value: bytes) -> str:
    try:
        return _fernet().decrypt(value).decode()
    except InvalidToken as exc:
        raise TokenEncryptionNotConfigured(
            "Nie udało się odszyfrować tokena — TOKEN_ENCRYPTION_KEY zmienił się "
            "od czasu zapisu albo dane są uszkodzone."
        ) from exc

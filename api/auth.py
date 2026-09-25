"""Token management shared by API tests and UI tests.

Tokens on Toolshop live only 5 minutes, so a single session-wide token would
expire in a long run. TokenProvider logs in once per user and transparently
logs in again shortly before the token expires.
"""

import time
from dataclasses import dataclass
from urllib.parse import urlsplit

import allure

from api.models import Token
from api.users_api import UsersApi
from config.settings import Credentials

REFRESH_MARGIN_SECONDS = 30
AUTH_TOKEN_STORAGE_KEY = "auth-token"  # key the Toolshop UI reads the JWT from


@dataclass
class _CachedToken:
    value: str
    expires_at: float


class TokenProvider:
    def __init__(self, users_api: UsersApi) -> None:
        self._users_api = users_api
        self._cache: dict[str, _CachedToken] = {}

    def token_for(self, user: Credentials) -> str:
        cached = self._cache.get(user.email)
        if cached and cached.expires_at - REFRESH_MARGIN_SECONDS > time.monotonic():
            return cached.value

        with allure.step(f"Get access token for {user.email}"):
            response = self._users_api.login(user.email, user.password)
            assert response.ok, f"Login failed for {user.email}: {response.status} {response.text()}"
            token = Token.model_validate(response.json())

        self._cache[user.email] = _CachedToken(token.access_token, time.monotonic() + token.expires_in)
        return token.access_token


def browser_storage_state(base_url: str, token: str) -> dict:
    """Playwright storage_state that makes the UI start as a logged-in user.

    The Toolshop UI keeps the JWT in localStorage, so putting it there before the
    page loads is equivalent to logging in through the form - just much faster.
    """
    parts = urlsplit(base_url)
    origin = f"{parts.scheme}://{parts.netloc}"
    return {
        "cookies": [],
        "origins": [
            {"origin": origin, "localStorage": [{"name": AUTH_TOKEN_STORAGE_KEY, "value": token}]},
        ],
    }

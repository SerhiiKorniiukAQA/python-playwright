from typing import Any

from playwright.sync_api import APIResponse

from api.base_api import BaseApi


class UsersApi(BaseApi):
    def login(self, email: str, password: str) -> APIResponse:
        return self._request.post("/users/login", data={"email": email, "password": password})

    def register(self, payload: dict[str, Any]) -> APIResponse:
        return self._request.post("/users/register", data=payload)

    def me(self, token: str | None = None) -> APIResponse:
        headers = self.auth_header(token) if token else {}
        return self._request.get("/users/me", headers=headers)

from playwright.sync_api import APIRequestContext


class BaseApi:
    """Shared plumbing for endpoint wrappers.

    Wrappers return the raw APIResponse, so tests decide what to assert
    (status code, headers, body) instead of the client hiding failures.
    """

    def __init__(self, request: APIRequestContext) -> None:
        self._request = request

    @staticmethod
    def auth_header(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

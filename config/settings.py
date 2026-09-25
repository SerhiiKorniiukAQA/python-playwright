"""Central place for environment-dependent settings.

Every value can be overridden with an environment variable, so the same
tests can run against the public demo, a local Docker instance, or CI.
"""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Credentials:
    email: str
    password: str
    full_name: str


def _user(prefix: str, email: str, full_name: str) -> Credentials:
    # Public demo accounts published by the Toolshop authors (all use "welcome01").
    return Credentials(
        email=os.getenv(f"{prefix}_EMAIL", email),
        password=os.getenv(f"{prefix}_PASSWORD", "welcome01"),
        full_name=os.getenv(f"{prefix}_FULL_NAME", full_name),
    )


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("BASE_URL", "https://practicesoftwaretesting.com").rstrip("/")
    api_url: str = os.getenv("API_URL", "https://api.practicesoftwaretesting.com").rstrip("/")

    customer: Credentials = field(
        default_factory=lambda: _user("CUSTOMER", "customer@practicesoftwaretesting.com", "Jane Doe")
    )
    customer2: Credentials = field(
        default_factory=lambda: _user("CUSTOMER2", "customer2@practicesoftwaretesting.com", "Jack Howe")
    )
    admin: Credentials = field(
        default_factory=lambda: _user("ADMIN", "admin@practicesoftwaretesting.com", "John Doe")
    )

    default_timeout_ms: int = int(os.getenv("DEFAULT_TIMEOUT_MS", "10000"))


settings = Settings()

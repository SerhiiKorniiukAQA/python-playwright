"""Central place for environment-dependent settings.

Every value can be overridden with an environment variable, so the same
tests can run against the public demo, a local Docker instance, or CI.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("BASE_URL", "https://practicesoftwaretesting.com")
    api_url: str = os.getenv("API_URL", "https://api.practicesoftwaretesting.com")

    # Public demo account published by the Toolshop authors.
    customer_email: str = os.getenv("CUSTOMER_EMAIL", "customer@practicesoftwaretesting.com")
    customer_password: str = os.getenv("CUSTOMER_PASSWORD", "welcome01")
    customer_full_name: str = os.getenv("CUSTOMER_FULL_NAME", "Jane Doe")

    default_timeout_ms: int = int(os.getenv("DEFAULT_TIMEOUT_MS", "10000"))


settings = Settings()

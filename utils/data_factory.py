"""Test data builders.

Each call returns fresh, unique data so tests never depend on each other or
on leftovers from a previous run on the shared public demo.
"""

import secrets
import uuid
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Any

from faker import Faker

fake = Faker()


def unique_email(prefix: str = "qa") -> str:
    return f"{prefix}.{uuid.uuid4().hex[:12]}@example.com"


def strong_password() -> str:
    # API requires 8+ chars with upper, lower, digit and symbol,
    # and rejects passwords found in known leaks.
    return f"Qa!{secrets.token_hex(6)}Z9"


def new_user_payload(**overrides: Any) -> dict[str, Any]:
    # API accepts ages between 18 and 75.
    dob = date.today() - timedelta(days=365 * fake.random_int(min=20, max=60))
    payload: dict[str, Any] = {
        "first_name": fake.first_name()[:40],
        "last_name": fake.last_name()[:20],
        "dob": dob.isoformat(),
        "phone": fake.numerify("0#########"),
        "email": unique_email(),
        "password": strong_password(),
        "address": {
            "street": fake.street_name()[:70],
            "house_number": str(fake.random_int(min=1, max=200)),
            "city": fake.city()[:40],
            "state": fake.state()[:40],
            "country": "Ukraine",
            "postal_code": fake.numerify("#####"),
        },
    }
    payload.update(overrides)
    return payload


@dataclass(frozen=True)
class Address:
    street: str
    house_number: str
    city: str
    state: str
    country_code: str  # ISO code, as used by the country dropdown
    postal_code: str

    def __str__(self) -> str:
        return f"{self.street} {self.house_number}, {self.postal_code} {self.city}, {self.country_code}"

    def as_postcode_lookup(self) -> dict[str, str]:
        """Response body of GET /postcode-lookup for this address."""
        data = asdict(self)
        data["country"] = data.pop("country_code")
        data["postcode"] = data.pop("postal_code")
        return data


def new_address(**overrides: Any) -> Address:
    values: dict[str, Any] = {
        "street": fake.street_name()[:60],
        "house_number": str(fake.random_int(min=1, max=200)),
        "city": fake.city()[:40],
        "state": fake.state()[:40],
        "country_code": "UA",
        "postal_code": fake.numerify("0####"),
    }
    values.update(overrides)
    return Address(**values)


def payment_details(method: str) -> dict[str, str]:
    """Valid form data for each payment method (field name -> value)."""
    next_year = date.today().year + 1
    return {
        "bank-transfer": {
            "bank_name": "Test Bank",
            "account_name": "Serhii Tester",
            "account_number": fake.numerify("##########"),
        },
        "cash-on-delivery": {},
        "credit-card": {
            "credit_card_number": "4111-1111-1111-1111",
            "expiration_date": f"12/{next_year}",
            "cvv": "123",
            "card_holder_name": "Serhii Tester",
        },
    }[method]

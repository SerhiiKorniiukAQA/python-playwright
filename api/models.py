"""Pydantic models describing API responses.

Parsing a response into a model is the schema check: a missing field or a
wrong type fails the test with a clear validation error. Unknown fields are
allowed so the tests don't break every time the API adds something new.
"""

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class NamedRef(ApiModel):
    id: str
    name: str


class ProductImage(ApiModel):
    file_name: str


class Product(ApiModel):
    id: str
    name: str
    description: str | None = None
    price: float
    is_location_offer: bool
    is_rental: bool
    in_stock: bool | None = None
    category: NamedRef | None = None
    brand: NamedRef | None = None
    product_image: ProductImage | None = None


class ProductsPage(ApiModel):
    current_page: int
    per_page: int
    last_page: int
    total: int
    data: list[Product]


class Token(ApiModel):
    access_token: str
    token_type: str
    expires_in: int


class User(ApiModel):
    id: str
    first_name: str
    last_name: str
    email: str


class CartCreated(ApiModel):
    id: str


class CartItem(ApiModel):
    id: str
    product_id: str
    quantity: int
    product: Product | None = None


class Cart(ApiModel):
    id: str
    cart_items: list[CartItem]

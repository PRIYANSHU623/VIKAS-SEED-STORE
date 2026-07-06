from pydantic import BaseModel


class ProductFilters(BaseModel):
    category: str | None = None
    kind: str | None = None
    season: str | None = None
    brand: str | None = None
    max_price: float | None = None
    min_price: float | None = None
    in_stock: bool | None = None
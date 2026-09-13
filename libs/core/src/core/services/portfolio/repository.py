from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Protocol

from pydantic import TypeAdapter

from core.models import Portfolio, Transaction
from core.services.base import AbstractJsonRepository


class PortfolioRepository(Protocol):
    """Persistence interface for computed portfolios."""

    def load(self) -> Portfolio | None: ...

    def save(self, portfolio: Portfolio) -> None: ...


PortfolioAdapter = TypeAdapter(Portfolio)


class JsonPortfolioRepository(AbstractJsonRepository[Portfolio]):
    """Store a validated portfolio document and its transaction cache."""

    DEFAULT_JSON_FILE_NAME = Path("portfolio.json")

    def __init__(self, json_path: Path | None = None) -> None:
        super().__init__(json_path)

    def _default_data(self) -> Portfolio:
        return Portfolio()

    def _serialize(self, data: Portfolio) -> bytes:
        return PortfolioAdapter.dump_json(data, indent=2, exclude_none=True) + b"\n"

    def _deserialize(self, raw_bytes: bytes) -> Portfolio:
        return PortfolioAdapter.validate_json(raw_bytes)

    def load(self) -> Portfolio | None:
        """Load the cached portfolio, if one has been persisted."""
        if not self.json_path.exists() and self._cache is None:
            return None
        return self._get_data()

    def save(self, portfolio: Portfolio) -> None:
        """Persist a newly computed portfolio."""
        self._cache = portfolio
        self.mark_dirty()
        self.commit()


def transaction_hash(transactions: list[Transaction]) -> str:
    """Return a stable SHA-256 hash for a transaction collection."""
    values = [transaction.model_dump(mode="json") for transaction in transactions]
    values.sort(key=lambda value: (str(value.get("date")), str(value.get("id"))))
    encoded = TypeAdapter(list[dict[str, object]]).dump_json(values, by_alias=True)
    return sha256(encoded).hexdigest()

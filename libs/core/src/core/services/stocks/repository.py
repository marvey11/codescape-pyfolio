from pathlib import Path
from typing import Protocol

from pydantic import TypeAdapter

from core.models import StockMetadata
from core.services.base import AbstractJsonRepository


class StockRepository(Protocol):
    def list_all(self) -> list[StockMetadata]: ...

    def get(self, isin: str) -> StockMetadata | None: ...

    def add(self, stock: StockMetadata) -> None: ...

    def update(self, stock: StockMetadata) -> None: ...

    def delete(self, isin: str) -> None: ...


# Create an alias for readability
StockDictAdapter = TypeAdapter(dict[str, StockMetadata])


class JsonStockMetadataRepository(AbstractJsonRepository[dict[str, StockMetadata]]):
    DEFAULT_JSON_FILE_NAME = Path("stocks.json")

    def __init__(self, json_path: Path | None = None) -> None:
        super().__init__(json_path)

    def _default_data(self) -> dict[str, StockMetadata]:
        return {}

    def _serialize(self, data: dict[str, StockMetadata]) -> bytes:
        return StockDictAdapter.dump_json(data, indent=2, exclude_none=True) + b"\n"

    def _deserialize(self, raw_bytes: bytes) -> dict[str, StockMetadata]:
        return StockDictAdapter.validate_json(raw_bytes)

    def list_all(self) -> list[StockMetadata]:
        return list(self._get_data().values())

    def get(self, isin: str) -> StockMetadata | None:
        return self._get_data().get(isin)

    def add(self, stock: StockMetadata) -> None:
        data = self._get_data()
        if stock.isin in data:
            raise ValueError(f"Stock {stock.isin} already exists.")
        data[stock.isin] = stock
        self.mark_dirty()

    def update(self, stock: StockMetadata) -> None:
        data = self._get_data()
        if stock.isin not in data:
            raise KeyError(f"Stock {stock.isin} not found.")

        data[stock.isin].update(stock)
        self.mark_dirty()

    def delete(self, isin: str) -> None:
        data = self._get_data()
        if isin not in data:
            raise KeyError(f"Stock {isin} not found.")
        del data[isin]
        self.mark_dirty()

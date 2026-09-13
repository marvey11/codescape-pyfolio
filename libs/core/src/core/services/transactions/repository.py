from __future__ import annotations

from pathlib import Path
from typing import Protocol
from uuid import UUID

from pydantic import TypeAdapter

from core.models import Transaction
from core.services.base import AbstractJsonRepository


class TransactionRepository(Protocol):
    """Persistence interface for immutable transaction entities."""

    def get(self, transaction_id: UUID | str) -> Transaction | None: ...

    def list_all(self) -> list[Transaction]: ...

    def add(self, transaction: Transaction) -> None: ...

    def update(self, transaction: Transaction) -> None: ...

    def delete(self, transaction_id: UUID | str) -> None: ...


TransactionListAdapter = TypeAdapter(list[Transaction])


class JsonTransactionRepository(AbstractJsonRepository[list[Transaction]]):
    """Store transactions in a validated JSON array."""

    DEFAULT_JSON_FILE_NAME = Path("transactions.json")

    def __init__(self, json_path: Path | None) -> None:
        super().__init__(json_path)

    def _default_data(self) -> list[Transaction]:
        return []

    def _serialize(self, data: list[Transaction]) -> bytes:
        return (
            TransactionListAdapter.dump_json(data, indent=2, exclude_none=True) + b"\n"
        )

    def _deserialize(self, raw_bytes: bytes) -> list[Transaction]:
        return TransactionListAdapter.validate_json(raw_bytes)

    @staticmethod
    def _normalise_id(transaction_id: UUID | str) -> UUID:
        return (
            transaction_id if isinstance(transaction_id, UUID) else UUID(transaction_id)
        )

    def get(self, transaction_id: UUID | str) -> Transaction | None:
        target_id = self._normalise_id(transaction_id)
        return next((item for item in self._get_data() if item.id == target_id), None)

    def list_all(self) -> list[Transaction]:
        return list(self._get_data())

    def add(self, transaction: Transaction) -> None:
        if self.get(transaction.id) is not None:
            raise ValueError(f"Transaction {transaction.id} already exists.")
        self._get_data().append(transaction)
        self.mark_dirty()

    def update(self, transaction: Transaction) -> None:
        data = self._get_data()
        for index, existing in enumerate(data):
            if existing.id == transaction.id:
                data[index] = transaction
                self.mark_dirty()
                return
        raise KeyError(f"Transaction {transaction.id} not found.")

    def delete(self, transaction_id: UUID | str) -> None:
        target_id = self._normalise_id(transaction_id)
        data = self._get_data()
        for index, transaction in enumerate(data):
            if transaction.id == target_id:
                del data[index]
                self.mark_dirty()
                return
        raise KeyError(f"Transaction {target_id} not found.")

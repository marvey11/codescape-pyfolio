from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from core.exceptions import RepositoryCorruptedError
from core.models import StockMetadata
from core.services import JsonStockMetadataRepository

if TYPE_CHECKING:
    from pathlib import Path


def test_corrupted_json_raises_repository_corrupted_error(mock_repo_path: Path) -> None:
    mock_repo_path.write_text("{ invalid json structure ...")

    repo = JsonStockMetadataRepository(mock_repo_path)
    with pytest.raises(RepositoryCorruptedError):
        repo.list_all()


def test_get_existing_stock(populated_repo: JsonStockMetadataRepository) -> None:
    # `populated_repo` is injected directly from libs/core/tests/conftest.py
    stock = populated_repo.get("DE0007164600")
    assert stock is not None
    assert stock.name == "SAP SE"


def test_add_stock_isolated(
    empty_repo: JsonStockMetadataRepository, sample_stock_sap: StockMetadata
) -> None:
    empty_repo.add(sample_stock_sap)
    assert empty_repo.get("DE0007164600") is not None


def test_add_and_retrieve_stock(populated_repo: JsonStockMetadataRepository) -> None:
    retrieved = populated_repo.get("DE0007164600")
    assert retrieved is not None
    assert retrieved.isin == "DE0007164600"
    assert retrieved.name == "SAP SE"
    assert retrieved.country_code == "DE"


def test_add_duplicate_raises_error(
    populated_repo: JsonStockMetadataRepository, sample_stock_sap: StockMetadata
) -> None:
    with pytest.raises(ValueError, match="already exists"):
        populated_repo.add(sample_stock_sap)


def test_update_existing_stock_partial(empty_repo: JsonStockMetadataRepository) -> None:
    initial = StockMetadata(isin="DE0007164600", name="SAP SE")
    empty_repo.add(initial)

    update_payload = StockMetadata(isin="DE0007164600", country_code="DE")
    empty_repo.update(update_payload)

    updated = empty_repo.get("DE0007164600")
    assert updated is not None
    assert updated.name == "SAP SE"  # Retained original name
    assert updated.country_code == "DE"  # Added country code


def test_update_nonexistent_raises_error(
    empty_repo: JsonStockMetadataRepository, sample_stock_apple: StockMetadata
) -> None:
    with pytest.raises(KeyError, match="not found"):
        empty_repo.update(sample_stock_apple)


def test_delete_stock(populated_repo: JsonStockMetadataRepository) -> None:
    populated_repo.delete("DE0007164600")
    assert populated_repo.get("DE0007164600") is None


def test_delete_nonexistent_raises_error(
    populated_repo: JsonStockMetadataRepository,
) -> None:
    with pytest.raises(KeyError, match="not found"):
        populated_repo.delete("UNKNOWN")


def test_persistence_across_instances(
    mock_repo_path: Path, sample_stock_apple: StockMetadata
) -> None:
    # First instance writes data
    repo1 = JsonStockMetadataRepository(mock_repo_path)
    repo1.add(sample_stock_apple)
    repo1.commit()

    # Second instance (simulating next CLI run) reads from same file
    repo2 = JsonStockMetadataRepository(mock_repo_path)
    stock = repo2.get("US0378331005")

    assert stock is not None
    assert stock.name == "Apple Inc."


def test_uncommitted_changes_are_not_saved(
    mock_repo_path: Path, sample_stock_apple: StockMetadata
) -> None:
    repo1 = JsonStockMetadataRepository(mock_repo_path)
    repo1.add(sample_stock_apple)
    # Intentionally do NOT call commit()

    repo2 = JsonStockMetadataRepository(mock_repo_path)
    assert repo2.get("US0378331005") is None  # File should remain empty


def test_dirty_flag_lifecycle(
    mock_repo_path: Path, sample_stock_apple: StockMetadata
) -> None:
    repo = JsonStockMetadataRepository(mock_repo_path)
    assert not repo.is_dirty

    repo.add(sample_stock_apple)

    # Tell mypy to evaluate the property fresh as a general boolean
    assert cast("bool", repo.is_dirty)

    repo.commit()
    assert not repo.is_dirty


def test_json_omits_none_fields(
    empty_repo: JsonStockMetadataRepository, mock_repo_path: Path
) -> None:
    stock = StockMetadata(isin="DE0007164600", country_code="DE")
    empty_repo.add(stock)
    empty_repo.commit()

    json_text = mock_repo_path.read_text()
    assert '"name"' not in json_text
    assert '"currency_code"' not in json_text
    assert '"country_code": "DE"' in json_text

from ..config.service import ConfigurationService
from ..portfolio.repository import JsonPortfolioRepository
from ..stocks.repository import JsonStockMetadataRepository
from ..transactions.repository import JsonTransactionRepository


class RepositoryFactory:
    """Composition helper to build repositories wired with config paths."""

    def __init__(self, config_service: ConfigurationService) -> None:
        self._config_service = config_service

    def create_stock_metadata_repo(self) -> JsonStockMetadataRepository:
        json_path = self._config_service.get_path("stocks.json_path")
        return JsonStockMetadataRepository(json_path)

    def create_transaction_repo(self) -> JsonTransactionRepository:
        json_path = self._config_service.get_path("transactions.json_path")
        return JsonTransactionRepository(json_path)

    def create_portfolio_repo(self) -> JsonPortfolioRepository:
        json_path = self._config_service.get_path("portfolio.json_path")
        return JsonPortfolioRepository(json_path)

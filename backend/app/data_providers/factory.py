from __future__ import annotations

from app.config import Settings, get_settings
from app.data_providers.alpaca import AlpacaProvider
from app.data_providers.finnhub import FinnhubProvider


def get_market_data_provider(settings: Settings | None = None) -> AlpacaProvider | None:
    settings = settings or get_settings()
    if not settings.has_alpaca:
        return None
    return AlpacaProvider(settings)


def get_fundamentals_provider(settings: Settings | None = None) -> FinnhubProvider | None:
    settings = settings or get_settings()
    if not settings.has_finnhub:
        return None
    return FinnhubProvider(settings)

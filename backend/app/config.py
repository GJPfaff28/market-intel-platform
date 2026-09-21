from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_data_feed: str = "iex"

    finnhub_api_key: str = ""

    database_url: str = "sqlite:///./scanner.db"

    scan_min_price: float = 8.0
    scan_min_avg_volume: int = 2_000_000
    scan_min_rvol: float = 2.0

    @property
    def has_alpaca(self) -> bool:
        return bool(self.alpaca_api_key and self.alpaca_secret_key)

    @property
    def has_finnhub(self) -> bool:
        return bool(self.finnhub_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()

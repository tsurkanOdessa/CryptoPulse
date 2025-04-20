
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException
from django.core.cache import cache
from django.conf import settings


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinanceService:
    _instance = None
    CACHE_TIMEOUT = 60  # 1 minute cache

    def __init__(self):
        self.client = Client(settings.BINANCE_API_KEY, settings.BINANCE_API_SECRET)

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BinanceService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def _get_cached_or_fetch(self, cache_key, fetch_func, *args, cache_timeout=None):
        """Общий метод для кэширования запросов"""
        if cache_timeout is None:
            cache_timeout = self.CACHE_TIMEOUT

        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            result = fetch_func(*args)
            cache.set(cache_key, result, cache_timeout)
            return result
        except Exception as e:
            logger.error(f"Error in {cache_key}: {e}")
            return None

    def get_current_price(self, symbol):
        cache_key = f"binance_price_{symbol}"
        return self._get_cached_or_fetch(cache_key, self._fetch_current_price, symbol)

    def _fetch_current_price(self, symbol):
        try:
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
            price = float(self.client.get_symbol_ticker(symbol=symbol)['price'])
            return price
        except BinanceAPIException as e:
            logger.error(f"Binance API Error getting price for {symbol}: {e}")
            return 0.0

    def get_24h_change(self, symbol):
        cache_key = f"binance_change_{symbol}"
        return self._get_cached_or_fetch(cache_key, self._fetch_24h_change, symbol)

    def _fetch_24h_change(self, symbol):
        try:
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
            stats = self.client.get_ticker(symbol=symbol)
            return float(stats['priceChangePercent'])
        except BinanceAPIException as e:
            logger.error(f"Binance API Error getting 24h change for {symbol}: {e}")
            return 0.0

    def get_all_prices(self):
        cache_key = "binance_all_prices"
        return self._get_cached_or_fetch(cache_key, self._fetch_all_prices)

    def _fetch_all_prices(self):
        try:
            prices = self.client.get_all_tickers()
            return {item['symbol']: float(item['price']) for item in prices}
        except BinanceAPIException as e:
            logger.error(f"Binance API Error getting all prices: {e}")
            return {}

    def get_klines(self, symbol, interval='1h', limit=100):
        try:
            return self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
        except BinanceAPIException as e:
            logger.error(f"Binance API Error getting klines for {symbol}: {e}")
            return []

    def get_spot_balance(self, symbol: str) -> float:
        bal = self.client.get_asset_balance(asset=symbol.upper())
        if bal:
            return float(bal['free']) + float(bal['locked'])
        return 0.0

    def get_funding_balance(self, symbol: str) -> float:
        data = self.sign_request("/sapi/v1/asset/get-funding-asset", {"asset": symbol.upper()})
        if isinstance(data, list) and data:
            return float(data[0].get("free", 0)) + float(data[0].get("locked", 0))
        return 0.0

    def get_deposit_total(self, symbol: str) -> float:
        deposits = self.client.get_deposit_history(coin=symbol.upper())
        return sum(float(tx['amount']) for tx in deposits if tx['status'] == 1)

    def get_balances(self, symbol: str) -> dict:
        """Универсальный метод получения всех остатков"""
        spot = self.get_spot_balance(symbol)
        funding = self.get_funding_balance(symbol)
        deposits = self.get_deposit_total(symbol)

        return {
            "symbol": symbol.upper(),
            "spot": spot,
            "funding": funding,
            "deposits": deposits,
            "total": spot + funding,
        }

    def get_total_asset_balance(self, symbol: str):
        return self.get_spot_balance(symbol) + self.get_deposit_total(symbol)


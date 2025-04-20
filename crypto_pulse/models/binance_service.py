from binance.client import Client
from django.conf import settings
from binance.exceptions import BinanceAPIException
from django.core.cache import cache



class BinanceService:
    _instance = None
    CACHE_TIMEOUT = 60  # 1 minute cache

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super(BinanceService, cls).__new__(cls)
            cls._instance.client = Client(
                api_key = settings.CRYPTO_CONFIG['BINANCE']['BINANCE_API_KEY'],
                api_secret=settings.CRYPTO_CONFIG['BINANCE']['BINANCE_API_SECRET']
            )
        return cls._instance

    def _get_cached_or_fetch(self, cache_key, fetch_func, *args):
        """Общий метод для кэширования запросов"""
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            result = fetch_func(*args)
            cache.set(cache_key, result, self.CACHE_TIMEOUT)
            return result
        except Exception as e:
            print(f"Error in {cache_key}: {e}")
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
            print(f"Binance API Error getting price for {symbol}: {e}")
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
            print(f"Binance API Error getting 24h change for {symbol}: {e}")
            return 0.0

    def get_all_prices(self):
        cache_key = "binance_all_prices"
        return self._get_cached_or_fetch(cache_key, self._fetch_all_prices)

    def _fetch_all_prices(self):
        try:
            prices = self.client.get_all_tickers()
            return {item['symbol']: float(item['price']) for item in prices}
        except BinanceAPIException as e:
            print(f"Binance API Error getting all prices: {e}")
            return {}
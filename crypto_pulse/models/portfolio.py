
from django.db import models
from crypto_pulse.models import Asset
from crypto_pulse.models.binance_service import BinanceService

class Portfolio(models.Model):
    # Пример модели для портфеля, может включать имя или владельца
    name = models.CharField(max_length=100)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class PortfolioAsset(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='assets')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10, default='UNKNOWN') # Символ актива (например, BTC)
    amount = models.FloatField(default=0)                       # Количество актива
    price = models.FloatField(default=0)                        # Текущая цена актива в USDT
    change_percent = models.FloatField(default=0)               # Процент изменения за последние 24 часа

    def __str__(self):
        return f"{self.symbol} - {self.amount} units"


    @property
    def current_value(self):
        """Вычисляемое поле для текущей стоимости"""
        return self.amount * self.price


    def update_from_binance(self):
        """Обновить цену и изменение из Binance API"""
        binance = BinanceService()
        self.price = binance.get_current_price(self.symbol)
        self.change_percent = binance.get_24h_change(self.symbol)
        self.save()

    @classmethod
    def update_all_assets(cls):
        """Обновить все активы в портфеле (оптимизированная версия)"""
        binance = BinanceService()
        all_prices = binance.get_all_prices()

        for asset in cls.objects.all():
            symbol = f"{asset.symbol}USDT" if not asset.symbol.endswith('USDT') else asset.symbol
            if symbol in all_prices:
                asset.price = all_prices[symbol]

            # Для изменения % всё равно нужен отдельный запрос
            asset.change_percent = binance.get_24h_change(asset.symbol)
            asset.save()
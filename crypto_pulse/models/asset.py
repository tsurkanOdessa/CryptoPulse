#Активы
from django.db import models

class Asset(models.Model):
    symbol = models.CharField(max_length=10, default='UNKNOWN')  # Символ актива (например, BTC)
    amount = models.FloatField(default=0)  # Количество актива
    price = models.FloatField(default=0)  # Текущая цена актива в USDT

    def __str__(self):
        return self.symbol

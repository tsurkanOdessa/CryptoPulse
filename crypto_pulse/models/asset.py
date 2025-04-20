from django.db import models


class Asset(models.Model):
    symbol = models.CharField(max_length=10, primary_key=True)
    full_symbol = models.CharField(max_length=10,default='')
    name = models.CharField(max_length=100, blank=True, default='')
    logo = models.ImageField(upload_to='assets/', null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"
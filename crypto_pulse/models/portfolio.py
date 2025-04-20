
from django.db import models
from .asset import Asset
from .binance_service import BinanceService
from django.db import transaction

class Portfolio(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class PortfolioAsset(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='assets')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    amount = models.FloatField(default=0)  # Количество актива
    price = models.FloatField(default=0)  # Текущая цена актива в USDT
    change_percent = models.FloatField(default=0)  # Процент изменения за последние 24 часа

    def __str__(self):
        return f"{self.asset.symbol} - {self.amount} units"

    @property
    def current_value(self):
        return self.amount * self.price

    def update_from_binance(self):
        """Обновить данные из Binance"""
        binance = BinanceService()
        self.price = binance.get_current_price(self.asset.symbol)
        self.change_percent = binance.get_24h_change(self.asset.symbol)
        self.save()

    def save(self, *args, **kwargs):
        if not self.price:
            self.update_from_binance()
        super().save(*args, **kwargs)

    @classmethod
    def sync_assets_from_binance(cls):
        binance = BinanceService()

        # Получаем все балансы
        account = binance.client.get_account()
        balances = account.get('balances', [])

        created = []

        for b in balances:
            symbol = b['asset']
            total = float(b['free']) + float(b['locked'])

            if total > 0:
                # Проверка, существует ли актив
                if not Asset.objects.filter(symbol=symbol).exists():
                    asset = Asset.objects.create(
                        symbol=symbol,
                        name=symbol  # или пусто: name=""
                    )
                    created.append(asset.symbol)





    @classmethod
    def update_all_assets(cls):
        """Массовое обновление всех активов из Binance, включая создание отсутствующих"""
        binance = BinanceService()
        cls.sync_assets_from_binance()

        try:
            all_prices = binance.get_all_prices()
            if not all_prices:
                print("Ошибка: Не удалось получить данные от Binance!")
                return False
        except Exception as e:
            print(f"Ошибка при запросе к Binance: {e}")
            return False

        # Получаем все портфели, для которых нужно обновлять активы
        portfolios = Portfolio.objects.all()

        if not portfolios:
            print("Ошибка: Нет портфелей в базе данных!")
            return False

        updated_count = 0
        created_count = 0

        with transaction.atomic():
            # Для каждого портфеля
            for portfolio in portfolios:
                # Для каждого актива в системе
                for asset in Asset.objects.all():
                    symbol = asset.symbol
                    usdt_symbol = symbol if symbol.endswith('USDT') else f"{symbol}USDT"

                    if asset.full_symbol != usdt_symbol:
                        asset.full_symbol = usdt_symbol
                        asset.save()

                    # Получаем или создаем запись PortfolioAsset  get_current_amount
                    portfolio_asset, created = cls.objects.get_or_create(
                        portfolio=portfolio,
                        asset=asset,
                        defaults={
                            'price': all_prices.get(usdt_symbol, 0),  # Текущая цена или 0
                            'change_percent': binance.get_24h_change(symbol) or 0
                        }
                    )

                    if created:
                        created_count += 1
                        print(f"Создана новая запись: {portfolio.name} - {symbol}")
                        continue

                    # Если запись уже существовала - обновляем цену

                    if usdt_symbol in all_prices:
                        new_price = all_prices[usdt_symbol]
                        new_amount= binance.get_total_asset_balance(symbol)

                        new_change_percent = binance.get_24h_change(symbol) or 0
                        if portfolio_asset.amount != new_amount:
                            portfolio_asset.amount = new_amount

                        if (portfolio_asset.price != new_price or
                                portfolio_asset.change_percent != new_change_percent):
                            portfolio_asset.price = new_price
                            portfolio_asset.change_percent = new_change_percent
                            portfolio_asset.save()
                            updated_count += 1
                            print(f"Обновлено: {portfolio.name} - {symbol} = {new_price}")
                    else:
                        print(f"Пропуск {symbol}: нет данных в Binance")

        print(f"Готово! Создано {created_count} новых записей, обновлено {updated_count} существующих.")
        return True


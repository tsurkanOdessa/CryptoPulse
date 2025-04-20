import os
import django
from pathlib import Path

# Установите переменные окружения перед настройкой Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.core.settings')

# Укажите путь к .env вручную (на случай проблем с автоматическим определением)
env_path = Path(__file__).resolve().parent / '.env'
if env_path.exists():
    from dotenv import load_dotenv

    load_dotenv(env_path)

# Проверка обязательных переменных
required_vars = ['BINANCE_API_KEY', 'BINANCE_API_SECRET']
missing_vars = [var for var in required_vars if var not in os.environ]

if missing_vars:
    raise EnvironmentError(
        f"Отсутствуют обязательные переменные: {', '.join(missing_vars)}. "
        f"Проверьте файл .env в {env_path}"
    )

# Теперь настраиваем Django
django.setup()

from crypto_pulse.models import Asset, PortfolioAsset
from crypto_pulse.models.binance_service import BinanceService


def update_assets():
    print("Начинаем обновление данных...")
    print(f"Используем API ключ: {os.environ.get('BINANCE_API_KEY')[:10]}...")  # Логируем только первые 5 символов ключа

    try:
        binance_service = BinanceService()
        all_prices = binance_service.get_all_prices()

        # Получаем символы из настроек
        from django.conf import settings
        symbols = getattr(settings, 'SYMBOLS', ['FETUSDT', 'SOLUSDT', 'FUNUSDT', 'PEPEUSDT', 'BONKUSDT'])

        for symbol in symbols:
            if symbol in all_prices:
                asset_symbol = symbol[:-4]  # Удаляем 'USDT'
                print(f"Обновляем {asset_symbol}...")

                asset, created = Asset.objects.get_or_create(
                    symbol=asset_symbol,
                    defaults={'name': asset_symbol}
                )
                asset.price = all_prices[symbol]
                asset.save()

                for portfolio_asset in PortfolioAsset.objects.filter(asset=asset):
                    portfolio_asset.price = all_prices[symbol]
                    portfolio_asset.change_percent = binance_service.get_24h_change(symbol)
                    portfolio_asset.save()

        print("Обновление завершено успешно!")
    except Exception as e:
        print(f"Ошибка при обновлении: {str(e)}")
        raise


if __name__ == "__main__":
    update_assets()
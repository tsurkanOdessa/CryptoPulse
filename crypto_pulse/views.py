import time
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from crypto_pulse.models import Portfolio
from crypto_pulse.models.binance_service import BinanceService

def test_view(request):
    return HttpResponse("Тест работает!")

@login_required
def portfolio_api_view(request):
    if request.method == 'GET':
        try:
            portfolio, created = Portfolio.objects.get_or_create(
                user=request.user,
                defaults={'name': 'Default Portfolio'}
            )

            binance_service = BinanceService()
            assets = []
            total_value = 0
            daily_change = 0

            if not portfolio.assets.exists():
                return JsonResponse({
                    'status': 'success',
                    'message': 'Portfolio created but has no assets',
                    'portfolio_name': portfolio.name
                })

            for asset in portfolio.assets.all():
                price = binance_service.get_current_price(asset.asset.symbol)
                change_percent = binance_service.get_24h_change(asset.asset.symbol)
                current_value = asset.amount * price

                assets.append({
                    'symbol': asset.asset.symbol,
                    'amount': asset.amount,
                    'price': price,
                    'change_percent': change_percent,
                    'current_value': current_value
                })

                total_value += current_value
                daily_change += change_percent

            data = {
                'status': 'success',
                'data': {
                    'total_value': total_value,
                    'daily_change': daily_change / len(assets) if assets else 0,
                    'assets': assets,
                    'last_updated': int(time.time())
                }
            }

            return JsonResponse(data)

        except Portfolio.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Портфель не найден'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

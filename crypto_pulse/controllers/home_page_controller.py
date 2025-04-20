from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from crypto_pulse.models.portfolio import PortfolioAsset
from crypto_pulse.models.binance_service import BinanceService

@login_required
def home_page_view(request):
    # Получаем активы текущего пользователя
    portfolio_assets = PortfolioAsset.objects.filter(
        portfolio__user=request.user
    ).select_related('asset')
    print(f"portfolio_assets = {portfolio_assets}")
    # Рассчитываем общую статистику
    total_value = sum(asset.amount * asset.price for asset in portfolio_assets)
    daily_change = 0  # Здесь можно добавить реальную логику расчета

    context = {
        'total_value': total_value,
        'daily_change': daily_change,
        'active_strategies': portfolio_assets.count(),
        'portfolio_assets': portfolio_assets,
    }
    return render(request, 'home.html', context)





@login_required
def portfolio_api(request):
    """API endpoint для данных портфеля"""
    try:
        # Получаем активы пользователя
        assets = PortfolioAsset.objects.filter(
            portfolio__user=request.user
        ).select_related('asset')

        # Опционально: принудительное обновление данных из Binance
        if request.GET.get('force_refresh'):
            BinanceService().update_all_assets()

        # Подготовка данных
        assets_data = []
        total_value = 0
        weighted_change = 0

        for asset in assets:
            current_value = asset.amount * asset.price
            total_value += current_value
            weighted_change += asset.change_percent * current_value

            assets_data.append({
                'symbol': asset.symbol,
                'logo': asset.asset.logo.url if asset.asset.logo else None,
                'amount': asset.amount,
                'price': asset.price,
                'change_percent': asset.change_percent,
                'current_value': current_value,
            })

        # Рассчитываем средневзвешенное изменение
        daily_change = weighted_change / total_value if total_value > 0 else 0

        return JsonResponse({
            'status': 'success',
            'total_value': total_value,
            'daily_change': daily_change,
            'assets': assets_data,
            'assets_count': len(assets_data),
            'last_updated': request.user.last_login.isoformat() if request.user.last_login else None
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def portfolio_data(request):
    assets = PortfolioAsset.objects.filter(
        portfolio__user=request.user
    ).select_related('asset')

    # Обновляем данные из Binance
    BinanceService().update_all_assets()

    total_value = sum(asset.current_value for asset in assets)
    daily_change = sum(
        asset.change_percent * asset.current_value for asset in assets
    ) / total_value if total_value > 0 else 0

    return JsonResponse({
        'total_value': total_value,
        'daily_change': daily_change,
        'assets': [
            {
                'symbol': asset.symbol,
                'logo': asset.asset.logo.url if asset.asset.logo else None,
                'amount': asset.amount,
                'price': asset.price,
                'change_percent': asset.change_percent,
                'current_value': asset.current_value,
            }
            for asset in assets
        ],
        'last_updated': request.user.last_login.isoformat()
    })
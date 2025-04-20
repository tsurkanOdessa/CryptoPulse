import time

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from crypto_pulse.models.portfolio import PortfolioAsset
from crypto_pulse.models.rsi_strategy import rsi_entry_exit

@login_required
def home_page_view(request):
    portfolio_assets = PortfolioAsset.objects.filter(
        portfolio__user=request.user
    ).select_related('asset')

    total_value = sum(asset.current_value for asset in portfolio_assets)
    daily_change = sum(
        asset.change_percent * asset.current_value for asset in portfolio_assets
    ) / total_value if total_value > 0 else 0

    signals = {}
    for asset in portfolio_assets:
        try:
            signals[asset.asset.full_symbol] = rsi_entry_exit(asset.asset.full_symbol)
        except Exception as e:
            signals[asset.asset.symbol] = f"Error: {str(e)}"

    context = {
        'total_value': total_value,
        'daily_change': daily_change,
        'portfolio_assets': portfolio_assets,
        'signals': signals,  # Исправлено: было 'signals'
        'active_strategies': len(signals)  # Исправлено: было 'active_strategies'
    }

    return render(request, 'home.html', context)





@login_required
def portfolio_api(request):
    """API endpoint для данных портфеля"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Not authenticated'}, status=401)

        assets = PortfolioAsset.objects.filter(
            portfolio__user=request.user
        ).select_related('asset')

        if request.GET.get('force_refresh'):
            PortfolioAsset.update_all_assets()

        assets_data = []
        total_value = 0
        weighted_change = 0

        for asset in assets:
            current_value = asset.amount * asset.price
            total_value += current_value
            weighted_change += asset.change_percent * current_value

            assets_data.append({
                'asset': {
                    'symbol': asset.asset.symbol,
                    'logo': asset.asset.logo.url if asset.asset.logo else None,
                },
                'amount': float(asset.amount),
                'price': float(asset.price),
                'change_percent': float(asset.change_percent),
                'current_value': float(current_value),
            })

        daily_change = (weighted_change / total_value) if total_value > 0 else 0

        return JsonResponse({
            'status': 'success',
            'data': {
                'total_value': float(total_value),
                'daily_change': float(daily_change),
                'assets': assets_data,
                'assets_count': len(assets_data),
                'last_updated': int(time.time())
            }
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
    PortfolioAsset.update_all_assets()

    total_value = sum(asset.current_value for asset in assets)
    daily_change = sum(
        asset.change_percent * asset.current_value for asset in assets
    ) / total_value if total_value > 0 else 0

    return JsonResponse({
        'total_value': total_value,
        'daily_change': daily_change,
        'assets': [
            {
                'symbol': asset.asset.symbol,
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
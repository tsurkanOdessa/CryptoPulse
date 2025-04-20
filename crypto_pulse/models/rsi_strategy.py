# crypto_pulse/models/rsi_strategy.py

from crypto_pulse.models.analyzer import get_ohlcv, compute_rsi


def analyze_symbol(symbol: str, interval: str = '1h') -> float:
    df = get_ohlcv(symbol, interval)
    df = compute_rsi(df)
    return df['rsi'].iloc[-1]


def rsi_entry_exit(symbol: str) -> str:
    try:
        rsi = analyze_symbol(symbol)
        if rsi < 30:
            return "BUY"
        elif rsi > 70:
            return "SELL"
        else:
            return "HOLD"
    except Exception as e:
        return f"ERROR: {str(e)}"

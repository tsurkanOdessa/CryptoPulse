# crypto_pulse/models/analyzer.py

import pandas as pd
import numpy as np
from crypto_pulse.models.binance_service import BinanceService


def get_ohlcv(symbol: str, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
    binance = BinanceService()
    raw_klines = binance.get_klines(symbol, interval, limit)

    df = pd.DataFrame(raw_klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    return df[['timestamp', 'close']]


def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    close = df['close']
    delta = close.diff()

    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)

    avg_gain = pd.Series(gain).rolling(window=period, min_periods=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    df['rsi'] = rsi
    return df

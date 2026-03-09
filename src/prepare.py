"""
Gann AutoResearch — Data Preparation & Evaluation Utilities.

This file is READ-ONLY. Do not modify.
Contains: data loading, swing detection, ephemeris access, and evaluation metrics.
"""
import sys
import os
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

# Add gann-decoder for ephemeris
DECODER_SRC = os.path.expanduser('~/projects/gann-decoder/src')
if os.path.exists(DECODER_SRC):
    sys.path.insert(0, DECODER_SRC)

DATA_DIR = Path(os.path.expanduser('~/projects/gann-decoder/data'))
RESULTS_DIR = Path(__file__).parent.parent / 'experiments'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATA LOADING
# ============================================================

INSTRUMENTS = {
    'Cotton': 'CTF',
    'Wheat': 'ZWF',
    'S&P 500': 'GSPC',
    'Gold': 'GC=F',
    'Crude Oil': 'CL=F',
    'Corn': 'ZCF',
}


def load_instrument(name: str) -> pd.DataFrame:
    """Load cached price data for an instrument."""
    ticker = INSTRUMENTS.get(name, name)
    variants = [
        DATA_DIR / f'{ticker}.csv',
        DATA_DIR / f'{ticker.replace("^", "").replace("/", "_").replace("=", "")}.csv',
    ]
    for f in variants:
        if f.exists():
            df = pd.read_csv(str(f), index_col=0, parse_dates=True)
            return df
    raise FileNotFoundError(f'No data for {name} (tried {variants})')


def load_all_instruments() -> dict[str, pd.DataFrame]:
    """Load all available instruments."""
    data = {}
    for name in INSTRUMENTS:
        try:
            data[name] = load_instrument(name)
        except FileNotFoundError:
            pass
    return data


# ============================================================
# SWING DETECTION (from gann-decoder)
# ============================================================

def find_major_swings(df: pd.DataFrame, min_pct_move: float = 5.0,
                      lookback: int = 20, lookahead: int = 20) -> pd.DataFrame:
    """Find major price swings (highs and lows).

    A swing high is a local maximum where price rose at least min_pct_move%
    from the prior swing low, and vice versa.
    """
    if 'Close' not in df.columns and 'Adj Close' in df.columns:
        df = df.rename(columns={'Adj Close': 'Close'})

    closes = df['Close'].values
    dates = df.index
    n = len(closes)

    swings = []

    for i in range(lookback, n - lookahead):
        window_before = closes[max(0, i - lookback):i]
        window_after = closes[i + 1:min(n, i + lookahead + 1)]

        if len(window_before) == 0 or len(window_after) == 0:
            continue

        price = closes[i]

        # Local high
        if price >= max(window_before) and price >= max(window_after):
            swings.append({
                'date': dates[i],
                'price': price,
                'type': 'high',
                'idx': i,
            })
        # Local low
        elif price <= min(window_before) and price <= min(window_after):
            swings.append({
                'date': dates[i],
                'price': price,
                'type': 'low',
                'idx': i,
            })

    if not swings:
        return pd.DataFrame(columns=['date', 'price', 'type', 'idx'])

    # Filter by minimum percentage move
    filtered = [swings[0]]
    for s in swings[1:]:
        prev = filtered[-1]
        pct_change = abs(s['price'] - prev['price']) / prev['price'] * 100
        if pct_change >= min_pct_move and s['type'] != prev['type']:
            filtered.append(s)
        elif pct_change >= min_pct_move and s['type'] == prev['type']:
            # Same type: keep the more extreme one
            if s['type'] == 'high' and s['price'] > prev['price']:
                filtered[-1] = s
            elif s['type'] == 'low' and s['price'] < prev['price']:
                filtered[-1] = s

    return pd.DataFrame(filtered)


# ============================================================
# TRAIN/TEST SPLIT
# ============================================================

def train_test_split(df: pd.DataFrame, train_ratio: float = 0.6
                     ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split data into train and test sets (chronological)."""
    split_idx = int(len(df) * train_ratio)
    return df.iloc[:split_idx], df.iloc[split_idx:]


# ============================================================
# SCORING METRICS
# ============================================================

def calculate_fitness(precision: float, recall: float,
                      profit_factor: float, false_alarm_rate: float,
                      n_signals: int) -> float:
    """Calculate composite fitness score.

    Higher = better. Balances precision (most important),
    recall, and profit factor. Penalizes high false alarm rates
    and too few/many signals.
    """
    if n_signals == 0:
        return 0.0

    # Precision is king (Gann's philosophy: trade less, win more)
    score = precision * 3.0

    # Recall matters but less (missing some turns is OK)
    score += recall * 1.0

    # Profit factor bonus
    if profit_factor > 1.0:
        score += min((profit_factor - 1.0) * 10, 20)

    # False alarm penalty
    if false_alarm_rate > 0.6:
        score -= (false_alarm_rate - 0.6) * 50

    # Signal count penalty (too few = not useful, too many = noise)
    if n_signals < 10:
        score -= (10 - n_signals) * 2
    elif n_signals > 500:
        score -= (n_signals - 500) * 0.01

    return round(score, 4)

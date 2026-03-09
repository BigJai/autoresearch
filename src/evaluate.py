"""
Gann AutoResearch — Evaluation Engine.

This file is READ-ONLY. Do not modify.
Runs the backtest using rules from rules.py and weights from weights.py.
Outputs fitness score and detailed metrics.
"""
import sys
import os
import math
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np

# Ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from prepare import (
    load_all_instruments, find_major_swings, train_test_split, calculate_fitness
)
from rules import RULE_REGISTRY, RuleSignal
from weights import (
    RULE_WEIGHTS, ORB_OVERRIDES, CONFLUENCE_BONUSES, CATEGORY_DIVERSITY_BONUS,
    INSTRUMENT_WEIGHTS, SIGNAL_THRESHOLDS, DIRECTION_WEIGHTS,
    INTERACTION_TERMS, INVERSION_THRESHOLD, MIN_RULES_FOR_SIGNAL,
    TIME_DECAY_HALFLIFE_DAYS,
)


def compute_composite_score(dt: datetime, instrument: str,
                            past_swings: list[datetime],
                            price: float = 0.0) -> dict:
    """Compute weighted composite score for a given date and instrument.

    Returns dict with score, active rules, direction, inversion risk.
    """
    active_rules = []
    raw_score = 0.0
    direction_score = 0.0
    inversion_score = 0.0
    categories_hit = set()

    # Get instrument-specific weight multipliers
    inst_weights = INSTRUMENT_WEIGHTS.get(instrument, {})

    for rule_id, rule_info in RULE_REGISTRY.items():
        weight = RULE_WEIGHTS.get(rule_id, 0.0)
        if weight == 0.0:
            continue

        # Apply instrument-specific multiplier
        inst_mult = inst_weights.get(rule_id, 1.0)
        effective_weight = weight * inst_mult

        try:
            signal: RuleSignal = rule_info['fn'](
                dt, past_swings=past_swings, price=price
            )
        except Exception:
            continue

        if not signal.active:
            continue

        # Rule fires
        rule_contribution = effective_weight * signal.strength
        category = rule_info['category']

        # Handle inversion rules separately
        if category == 'inversion':
            inversion_score += rule_contribution
        else:
            raw_score += rule_contribution
            categories_hit.add(category)
            active_rules.append({
                'id': rule_id,
                'weight': effective_weight,
                'strength': signal.strength,
                'contribution': rule_contribution,
                'direction': signal.direction,
                'details': signal.details,
                'category': category,
            })

            # Direction scoring
            dir_weight = DIRECTION_WEIGHTS.get(rule_id, 0.0)
            if signal.direction == 'bullish':
                direction_score += abs(dir_weight) if dir_weight >= 0 else -abs(dir_weight)
            elif signal.direction == 'bearish':
                direction_score -= abs(dir_weight) if dir_weight >= 0 else -abs(dir_weight)
            direction_score += dir_weight * signal.strength * 0.5

    n_active = len(active_rules)

    # Minimum rules gate
    if n_active < MIN_RULES_FOR_SIGNAL:
        return {
            'score': 0.0, 'n_rules': n_active, 'direction': 'neutral',
            'inversion_risk': inversion_score, 'rules': [],
        }

    # Confluence bonus
    confluence_bonus = 0.0
    for min_n, bonus in sorted(CONFLUENCE_BONUSES.items()):
        if n_active >= min_n:
            confluence_bonus = bonus

    # Category diversity bonus
    n_categories = len(categories_hit)
    diversity_bonus = 0.0
    for min_c, bonus in sorted(CATEGORY_DIVERSITY_BONUS.items()):
        if n_categories >= min_c:
            diversity_bonus = bonus

    # Interaction terms
    active_ids = frozenset(r['id'] for r in active_rules)
    interaction_bonus = 0.0
    for combo, bonus in INTERACTION_TERMS:
        if combo.issubset(active_ids):
            interaction_bonus += bonus

    total_score = raw_score + confluence_bonus + diversity_bonus + interaction_bonus

    # Direction prediction
    if direction_score > 0.5:
        predicted_dir = 'bullish'
    elif direction_score < -0.5:
        predicted_dir = 'bearish'
    else:
        predicted_dir = 'neutral'

    # Inversion: if risk exceeds threshold, flip direction
    if abs(inversion_score) > INVERSION_THRESHOLD:
        if predicted_dir == 'bullish':
            predicted_dir = 'bearish'
        elif predicted_dir == 'bearish':
            predicted_dir = 'bullish'

    return {
        'score': round(total_score, 2),
        'n_rules': n_active,
        'direction': predicted_dir,
        'inversion_risk': round(inversion_score, 2),
        'confluence_bonus': confluence_bonus,
        'diversity_bonus': diversity_bonus,
        'interaction_bonus': interaction_bonus,
        'categories': list(categories_hit),
        'rules': active_rules,
    }


def backtest_instrument(name: str, df: pd.DataFrame,
                        use_test_only: bool = True) -> dict:
    """Backtest the composite signal system on one instrument.

    Uses train/test split. Reports OOS (test set) metrics.
    """
    train_df, test_df = train_test_split(df, 0.6)
    eval_df = test_df if use_test_only else df

    # Get swings for the full dataset (for reference)
    all_swings = find_major_swings(df, min_pct_move=5.0, lookback=20, lookahead=20)
    eval_swings = find_major_swings(eval_df, min_pct_move=5.0, lookback=20, lookahead=20)

    if len(eval_swings) < 5:
        return {'error': f'Too few swings ({len(eval_swings)})'}

    # Build swing date lookup (with orb)
    orb_days = 2
    swing_dates = {}
    for _, s in eval_swings.iterrows():
        d = pd.Timestamp(s['date']).date()
        for offset in range(-orb_days, orb_days + 1):
            adj_d = d + timedelta(days=offset)
            if adj_d not in swing_dates:
                swing_dates[adj_d] = s['type']

    # Get threshold
    threshold = SIGNAL_THRESHOLDS.get(name, SIGNAL_THRESHOLDS.get('_default', 3.0))

    # Evaluate every 3rd trading day for speed
    hits = 0
    false_alarms = 0
    total_signals = 0
    caught_swing_dates = set()
    all_signal_scores = []

    for idx in range(0, len(eval_df), 7):
        dt = eval_df.index[idx].to_pydatetime()
        d = dt.date()
        price = eval_df.iloc[idx].get('Close', 0)

        # Only use past swings (no future leak)
        past_swing_dts = [
            datetime.combine(pd.Timestamp(s['date']).date(), datetime.min.time())
            for _, s in all_swings.iterrows()
            if pd.Timestamp(s['date']) < eval_df.index[idx]
        ]

        result = compute_composite_score(dt, name, past_swing_dts[-30:], price)

        if result['score'] >= threshold:
            total_signals += 1
            if d in swing_dates:
                hits += 1
                caught_swing_dates.add(d)
            else:
                false_alarms += 1
            all_signal_scores.append(result['score'])

    # Calculate metrics
    precision = hits / total_signals * 100 if total_signals > 0 else 0
    recall = len(caught_swing_dates) / len(eval_swings) * 100 if len(eval_swings) > 0 else 0
    false_alarm_rate = false_alarms / total_signals if total_signals > 0 else 0

    # Simple profit factor estimate (precision-based)
    # Assume: correct signals = +2R, incorrect = -1R (2:1 reward:risk)
    gross_profit = hits * 2.0
    gross_loss = false_alarms * 1.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 10.0

    fitness = calculate_fitness(
        precision / 100, recall / 100, profit_factor,
        false_alarm_rate, total_signals
    )

    return {
        'instrument': name,
        'total_swings': len(eval_swings),
        'total_signals': total_signals,
        'hits': hits,
        'false_alarms': false_alarms,
        'precision_pct': round(precision, 1),
        'recall_pct': round(recall, 1),
        'false_alarm_rate': round(false_alarm_rate, 3),
        'profit_factor': round(profit_factor, 2),
        'fitness': round(fitness, 4),
        'avg_signal_score': round(sum(all_signal_scores) / len(all_signal_scores), 2)
            if all_signal_scores else 0,
    }


def run_full_evaluation() -> dict:
    """Run evaluation across all instruments. Print results in standard format."""
    start_time = time.time()

    print('Loading data...')
    data = load_all_instruments()
    print(f'Loaded {len(data)} instruments')

    results = {}
    total_fitness = 0.0

    for name, df in data.items():
        print(f'  Backtesting {name}...')
        result = backtest_instrument(name, df, use_test_only=True)
        results[name] = result

        if 'error' not in result:
            total_fitness += result['fitness']
            print(f'    Signals={result["total_signals"]:4d} '
                  f'Hits={result["hits"]:3d} '
                  f'Prec={result["precision_pct"]:5.1f}% '
                  f'Recall={result["recall_pct"]:5.1f}% '
                  f'PF={result["profit_factor"]:.2f} '
                  f'Fitness={result["fitness"]:.4f}')
        else:
            print(f'    ERROR: {result["error"]}')

    avg_fitness = total_fitness / len(results) if results else 0
    elapsed = time.time() - start_time

    # Summary in standard format (grep-friendly)
    print('\n---')

    avg_precision = np.mean([r['precision_pct'] for r in results.values()
                             if 'precision_pct' in r])
    avg_recall = np.mean([r['recall_pct'] for r in results.values()
                          if 'recall_pct' in r])
    avg_pf = np.mean([r['profit_factor'] for r in results.values()
                       if 'profit_factor' in r])
    avg_fa = np.mean([r['false_alarm_rate'] for r in results.values()
                       if 'false_alarm_rate' in r])

    print(f'fitness:          {avg_fitness:.4f}')
    print(f'precision_pct:    {avg_precision:.1f}')
    print(f'recall_pct:       {avg_recall:.1f}')
    print(f'profit_factor:    {avg_pf:.2f}')
    print(f'false_alarm_pct:  {avg_fa * 100:.1f}')

    instr_scores = ', '.join(
        f'{n}={r["fitness"]:.2f}'
        for n, r in results.items() if 'fitness' in r
    )
    print(f'instruments:      {instr_scores}')

    best = max(results.items(), key=lambda x: x[1].get('fitness', 0))
    worst = min(results.items(), key=lambda x: x[1].get('fitness', float('inf')))
    print(f'best_instrument:  {best[0]} ({best[1].get("fitness", 0):.2f})')
    print(f'worst_instrument: {worst[0]} ({worst[1].get("fitness", 0):.2f})')
    print(f'eval_seconds:     {elapsed:.1f}')
    print(f'n_rules_total:    {len(RULE_WEIGHTS)}')
    print(f'n_rules_active:   {sum(1 for w in RULE_WEIGHTS.values() if w != 0)}')

    return {
        'avg_fitness': avg_fitness,
        'results': results,
        'elapsed': elapsed,
    }


if __name__ == '__main__':
    run_full_evaluation()

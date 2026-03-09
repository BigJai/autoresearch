# Gann AutoResearch — Autonomous Trading Rule Discovery

This is an autonomous research system for decoding and optimizing W.D. Gann's
trading methodology using the AutoResearch pattern.

## What This System Does

Instead of training neural networks, this system discovers and optimizes
**weighted trading rules** based on planetary cycles, time geometry, and
Gann's encoded methods. The agent iteratively modifies rule weights, orbs,
thresholds, and confluence bonuses, then backtests against historical price
data to find optimal configurations.

## Setup

To set up a new experiment run:

1. **Agree on a run tag**: propose a tag based on today's date and focus
   (e.g. `mar9-cotton`, `mar9-allrules`).
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current master.
3. **Read the in-scope files**:
   - `program.md` — this file. Research context and directives.
   - `src/prepare.py` — fixed: data loading, ephemeris, swing detection. Do NOT modify.
   - `src/rules.py` — fixed: all rule functions. Do NOT modify.
   - `src/weights.py` — **THE file you modify.** Weights, orbs, thresholds, bonuses.
   - `src/evaluate.py` — fixed: backtest engine + scoring. Do NOT modify.
   - `knowledge/` — reference material. Read for hypothesis generation.
4. **Verify data exists**: Check `data/` contains price CSVs and ephemeris.
5. **Initialize results.tsv**: Create with header row.
6. **Confirm and go**.

## The Goal

**Maximize the composite score** across these metrics (lower rank = better):

```
PRIMARY:   precision    — % of signals that are actual turns (higher = better)
SECONDARY: recall       — % of actual turns captured (higher = better)
TERTIARY:  profit_factor — total profit / total loss from signals (higher = better)
PENALTY:   false_alarm_rate — penalized if > 60%
```

The evaluation function returns a single **fitness score** combining these.
Your job is to find the weight configuration that maximizes fitness.

## What You CAN Modify

**Only `src/weights.py`**. This file contains:

1. **Rule weights** — how much each of the 30+ rules contributes to the composite
2. **Orb values** — how tight/loose each rule's angular tolerance is
3. **Confluence bonuses** — extra score when N rules fire together
4. **Instrument-specific overrides** — different weights per commodity
5. **Thresholds** — minimum composite score to generate a signal
6. **Direction weights** — bullish vs bearish bias per rule
7. **Interaction terms** — bonus/penalty when specific rule combos fire

## What You CANNOT Modify

- `src/prepare.py` — data loading and ephemeris calculations
- `src/rules.py` — rule function implementations
- `src/evaluate.py` — backtest engine and fitness scoring
- `data/` — historical price data

## Experimentation

Each experiment takes ~30 seconds (backtest across all instruments).
That's ~120 experiments/hour, ~1000+ overnight.

Run: `python src/evaluate.py`

Output:
```
---
fitness:          0.4523
precision_pct:    42.3
recall_pct:       67.8
profit_factor:    1.85
false_alarm_pct:  31.2
instruments:      Cotton=0.52, Wheat=0.41, SP500=0.38, Gold=0.61
best_instrument:  Gold (0.61)
worst_instrument: SP500 (0.38)
```

## Logging Results

Log every experiment to `results.tsv`:

```
commit	fitness	precision	recall	profit_factor	status	description
a1b2c3d	0.4523	42.3	67.8	1.85	keep	baseline equal weights
b2c3d4e	0.4891	45.1	65.2	2.01	keep	boost Saturn aspects 3x
c3d4e5f	0.3200	28.1	72.3	1.12	discard	removed Bayer rules
```

## The Experiment Loop

LOOP FOREVER:

1. Review current weights configuration and recent results
2. Form a hypothesis (informed by knowledge/ materials)
3. Modify `src/weights.py`
4. Git commit
5. Run: `python src/evaluate.py > run.log 2>&1`
6. Read results: `grep "^fitness:\|^precision" run.log`
7. Record in results.tsv
8. If fitness improved → keep (advance branch)
9. If fitness same or worse → revert (`git reset --hard HEAD~1`)
10. NEVER STOP. Keep iterating.

## Research Directives

### Phase 1: Weight Discovery (First 100 experiments)
- Start with equal weights (baseline)
- Vary one weight at a time to find sensitivity
- Identify which rules matter most per instrument
- Find optimal orb values

### Phase 2: Confluence Patterns (Experiments 100-300)
- Test which rule combinations amplify each other
- Add interaction terms for strong combos
- Test instrument-specific weight profiles
- Optimize thresholds per instrument

### Phase 3: Advanced Patterns (Experiments 300+)
- Read `knowledge/` for new hypotheses from Gann's texts
- Test ideas from decoded Tunnel Through The Air
- Try planetary harmonic fractions (1/2, 1/3, 1/4 of cycles)
- Test direction prediction (which turns are tops vs bottoms)
- Explore time-of-year seasonality interactions
- Test cycle phase offsets

### Knowledge-Driven Hypotheses

Read these files for hypothesis generation:
- `knowledge/ebooks/` — Gann's own books + MJ's study guide
- `knowledge/decoded/` — Decoded Tunnel Through The Air data
- `knowledge/rules-extracted/` — Cataloged rules from all sources
- `knowledge/wiits/` — WIITS community research posts
- `knowledge/youtube/` — Transcribed video lectures

Key insights from the knowledge base:
1. **Individual rules are weak (~20-45% alone)** — confluence is everything
2. **Outer planet aspects carry more weight** (slower = rarer = stronger)
3. **Mars is the key planet for Cotton** (Gann emphasized this repeatedly)
4. **Saturn synodic period (378d) is the most universal cycle**
5. **Inversions (~10%) happen at specific planetary conditions** — don't fight them
6. **700 days (Mars sidereal) is Cotton's master cycle** (decoded from Tunnel)
7. **Phase-locking matters** — same cycle works only at specific phase offsets
8. **Gann used 3+ confirming rules before trading** — minimum confluence

### Anti-Patterns (What NOT to do)
- Don't set any single rule weight > 10 (overfitting)
- Don't remove all rules of one category (lose signal diversity)
- Don't optimize for one instrument at expense of others
- Don't reduce orbs below 0.5° (too tight, miss valid signals)
- Don't chase recall above 90% (will tank precision)
- If precision drops below 25%, something is very wrong — revert

## Instruments

The system tests across these markets simultaneously:
- **Cotton** (CT=F) — Gann's specialty, most rules
- **Wheat** (ZW=F) — Gann's second most traded
- **S&P 500** (^GSPC) — Modern benchmark
- **Gold** (GC=F) — Outer planet sensitive
- **Crude Oil** (CL=F) — Mars-heavy
- **Corn** (ZC=F) — Agricultural cycle sensitive

## Key Concepts

### Composite Score Formula
```
composite = Σ(rule_weight[i] × rule_signal[i]) + confluence_bonus
```

### Confluence Bonus
When N rules fire simultaneously:
- 2 rules: bonus × 1.0
- 3 rules: bonus × 2.0
- 4+ rules: bonus × 3.0

### Inversion Detection
Some planetary conditions predict when the normal H-L-H-L alternation breaks.
The weights include "inversion risk" modifiers that can flip signal direction.

### Direction Prediction
Each rule can have a directional bias (bullish/bearish/neutral).
The sum of directional weights predicts whether a turn is a top or bottom.

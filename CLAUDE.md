# Gann AutoResearch

Autonomous research system for decoding and optimizing W.D. Gann's trading methods.
Forked from [karpathy/autoresearch](https://github.com/karpathy/autoresearch) and
adapted for financial astrology / time cycle research.

## How It Works

Instead of training neural networks, the agent optimizes **weighted trading rules**
across 12 categories (Bayer, planetary aspects, Sepharial, biblical numerology,
Pythagorean geometry, decoded Tunnel cycles, etc.).

The agent modifies ONLY `src/weights.py`, runs backtests (~40s each), and iterates.
~80 experiments/hour, ~700 overnight.

## Quick Start

```bash
# Activate the gann-decoder venv (has all deps)
source ~/projects/gann-decoder/venv/bin/activate

# Run baseline evaluation
python src/evaluate.py

# Run knowledge ingestion
python src/ingest.py --all

# Start autonomous research (point your agent at program.md)
```

## Key Files

- `program.md` — Agent instructions (the "research org code")
- `src/weights.py` — **THE ONLY FILE THE AGENT MODIFIES**
- `src/rules.py` — 47 rules across 12 categories (read-only)
- `src/evaluate.py` — Backtest engine + fitness scoring (read-only)
- `src/prepare.py` — Data loading + utilities (read-only)
- `src/ingest.py` — Knowledge ingestion pipeline
- `knowledge/` — Source materials (ebooks, decoded Tunnel, WIITS, YouTube)
- `experiments/` — Logged experiment results
- `data/` — Symlinked to gann-decoder price data

## Rule Categories (47 rules)

1. **Bayer's 14 Rules** — George Bayer's planetary trading rules
2. **Planetary Aspects** — Mars/Jupiter/Saturn/Uranus/Pluto inter-aspects
3. **Stations & Ingresses** — Planet direction changes and sign entries
4. **Cardinal & Geometry** — Gann degrees, Square of 9
5. **Eclipse & Lunar** — Eclipses, moon phases, declination
6. **Seasonal** — Equinox/solstice/cross-quarter + Gann dates
7. **Sepharial** — Sensitive degrees, lunar mansions
8. **Biblical Numerology** — 7, 40, 49, 70, 144, 490-day cycles
9. **Pythagorean** — Perfect squares, hexagon numbers, Fibonacci/golden ratio
10. **Decoded Tunnel** — Mars sidereal (700d), Saturn synodic, Jupiter synodic
11. **Mars System** — Retrograde periods, sign-specific effects
12. **Inversion Detection** — Conditions that flip normal H-L alternation

## Dependencies

Uses the gann-decoder venv: pyswisseph, pandas, numpy, yfinance, matplotlib.
Data symlinked from `~/projects/gann-decoder/data/`.

## The Goal

Push fitness score from -15.7 (equal-weight baseline) to positive.
Target: precision > 40%, recall > 30%, profit factor > 2.0.

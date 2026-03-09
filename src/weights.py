"""
Gann AutoResearch — Weight Configuration.

THIS IS THE ONLY FILE THE AGENT MODIFIES.

Contains all tunable parameters:
- Rule weights (how much each rule contributes to composite score)
- Orb overrides (per-rule angular tolerance)
- Confluence bonuses (extra score when N rules fire together)
- Instrument-specific weight profiles
- Signal thresholds
- Direction weights
- Interaction terms (specific rule combo bonuses)
"""

# ============================================================
# GLOBAL RULE WEIGHTS
# Default: 1.0 = standard contribution, 0.0 = disabled
# ============================================================

RULE_WEIGHTS = {
    # Bayer Rules
    'bayer_01': 1.0,   # Mercury station
    'bayer_02': 1.0,   # Mars-Mercury speed 59'
    'bayer_03': 1.0,   # Venus-Sun conjunction
    'bayer_04': 1.0,   # Mercury Cancer 17°
    'bayer_05': 1.0,   # Retro Venus conj direct Mercury
    'bayer_06': 1.0,   # Retro Mercury over Sun
    'bayer_07': 1.0,   # Mercury speed 59'/118'
    'bayer_08': 1.0,   # Mars-Mercury 161° retro
    'bayer_09': 1.0,   # Venus decl crosses Sun extreme
    'bayer_10': 1.0,   # Mars 16°55'46"
    'bayer_11': 1.0,   # Mercury halfway retrograde
    'bayer_12': 1.0,   # Mars 16°35' + 330°
    'bayer_13': 1.0,   # Venus perihelion
    'bayer_14': 1.0,   # Mercury Scorpio/Sag/Cap degrees

    # Planetary Aspects
    'aspect_mars_jupiter': 1.0,
    'aspect_mars_saturn': 1.0,
    'aspect_jupiter_saturn': 1.0,
    'aspect_jupiter_uranus': 1.0,
    'aspect_saturn_uranus': 1.0,
    'aspect_saturn_pluto': 1.0,

    # Stations & Ingresses
    'station_mars': 1.0,
    'station_jupiter': 1.0,
    'station_saturn': 1.0,
    'ingress_mars': 1.0,
    'ingress_outer': 1.0,

    # Cardinal & Geometry
    'mars_cardinal': 1.0,
    'saturn_cardinal': 1.0,
    'mars_gann_degrees': 1.0,
    'square_of_9': 1.0,

    # Eclipse & Lunar
    'eclipse': 1.0,
    'moon_declination': 1.0,
    'new_moon': 1.0,
    'full_moon': 1.0,

    # Seasonal
    'seasonal': 1.0,

    # Sepharial
    'sepharial_degrees': 1.0,
    'sepharial_mansion': 1.0,

    # Biblical
    'biblical_cycles': 1.0,
    'daniel_490': 1.0,

    # Pythagorean
    'pythagorean_squares': 1.0,
    'hexagon_numbers': 1.0,
    'golden_ratio': 1.0,

    # Decoded Tunnel
    'tunnel_700_mars': 1.0,
    'tunnel_755_submarine': 1.0,
    'tunnel_saturn_syn': 1.0,
    'tunnel_jupiter_syn': 1.0,

    # Mars System
    'mars_retrograde': 1.0,
    'mars_retro_sign': 1.0,

    # Inversion (negative = reduces composite, positive = adds to it)
    'inv_danger_mars_cardinal': -1.0,  # Negative: warns of inversion
    'inv_safety_mars_jup_trine': 1.0,  # Positive: confirms alternation
}

# ============================================================
# ORB OVERRIDES (degrees)
# If not specified, each rule uses its built-in default
# ============================================================

ORB_OVERRIDES = {
    # 'bayer_01': 0.08,  # Tighten Mercury station threshold
    # 'aspect_mars_jupiter': 3.0,  # Widen Mars-Jupiter orb
}

# ============================================================
# CONFLUENCE BONUSES
# Extra score added when N rules fire on the same day
# ============================================================

CONFLUENCE_BONUSES = {
    2: 1.0,   # 2 rules fire together
    3: 2.5,   # 3 rules
    4: 5.0,   # 4 rules
    5: 8.0,   # 5+ rules — very rare, very strong
    6: 12.0,
}

# ============================================================
# CATEGORY CONFLUENCE BONUSES
# Extra bonus when rules from DIFFERENT categories fire together
# ============================================================

CATEGORY_DIVERSITY_BONUS = {
    2: 0.5,   # 2 different categories
    3: 1.5,   # 3 different categories
    4: 3.0,   # 4+ different categories — strongest signal
    5: 5.0,
}

# ============================================================
# INSTRUMENT-SPECIFIC WEIGHT MULTIPLIERS
# Multiplied on top of global weights for each instrument
# Default: 1.0 (use global weights as-is)
# ============================================================

INSTRUMENT_WEIGHTS = {
    'Cotton': {
        'tunnel_700_mars': 2.0,     # Mars sidereal = Cotton's master cycle
        'mars_retrograde': 1.5,    # Gann emphasized Mars for Cotton
        'mars_retro_sign': 1.5,
        'mars_cardinal': 1.5,
        'station_mars': 1.5,
        'ingress_mars': 1.5,
    },
    'Wheat': {
        'tunnel_saturn_syn': 2.0,   # Saturn synodic matches Wheat to 0.09d
        'station_saturn': 1.5,
        'saturn_cardinal': 1.5,
        'seasonal': 1.5,           # Agricultural seasonality
    },
    'S&P 500': {
        'aspect_jupiter_saturn': 1.5,  # Great Conjunction = market structure
        'aspect_jupiter_uranus': 1.5,
        'eclipse': 1.5,
    },
    'Gold': {
        'aspect_saturn_pluto': 2.0,    # Deep structural = Gold
        'daniel_490': 1.5,            # Validated at 4.8× on Gold
        'tunnel_jupiter_syn': 1.5,
    },
    'Crude Oil': {
        'aspect_mars_saturn': 1.5,     # Mars-Saturn = Oil
        'station_mars': 1.5,
        'mars_cardinal': 1.5,
    },
    'Corn': {
        'seasonal': 2.0,              # Planting/harvest cycles
        'tunnel_755_submarine': 1.5,
    },
}

# ============================================================
# SIGNAL THRESHOLDS
# Minimum composite score to generate a trading signal
# ============================================================

SIGNAL_THRESHOLDS = {
    'Cotton': 6.0,
    'Wheat': 6.0,
    'S&P 500': 6.0,
    'Gold': 6.0,
    'Crude Oil': 6.0,
    'Corn': 6.0,
    '_default': 6.0,
}

# ============================================================
# DIRECTION WEIGHTS
# How much each rule contributes to direction prediction
# Positive = bullish bias, negative = bearish, 0 = neutral
# ============================================================

DIRECTION_WEIGHTS = {
    'bayer_08': 1.0,    # Mars-Mercury 161° retro = bullish (Bayer said "up")
    'bayer_11': 1.0,    # Mercury half-retro = bottom
    'bayer_12': 1.0,    # Mars 16°35' = bottom
    'bayer_13': 0.5,    # Venus perihelion = mostly up
    'bayer_02': -0.5,   # Mars-Mercury speed diff = bearish
    'bayer_03': -1.0,   # Venus-Sun conj = tops
}

# ============================================================
# INTERACTION TERMS
# Bonus/penalty when specific rule combinations fire together
# Format: (frozenset of rule names, bonus)
# ============================================================

INTERACTION_TERMS = [
    # Known strong combos (from backtesting)
    (frozenset(['tunnel_700_mars', 'mars_cardinal']), 3.0),
    (frozenset(['tunnel_saturn_syn', 'station_saturn']), 3.0),
    (frozenset(['eclipse', 'aspect_jupiter_saturn']), 2.5),
    (frozenset(['bayer_01', 'bayer_07']), 2.0),  # Mercury double signal

    # Sepharial + planetary aspects (untested — let agent discover)
    (frozenset(['sepharial_degrees', 'aspect_saturn_pluto']), 1.0),

    # Biblical + Tunnel (both time-cycle based)
    (frozenset(['daniel_490', 'tunnel_jupiter_syn']), 2.0),
    (frozenset(['biblical_cycles', 'tunnel_saturn_syn']), 1.5),

    # Pythagorean + cycles
    (frozenset(['golden_ratio', 'tunnel_700_mars']), 1.5),
    (frozenset(['pythagorean_squares', 'seasonal']), 1.0),
]

# ============================================================
# INVERSION RISK THRESHOLD
# If inversion score exceeds this, flip direction prediction
# ============================================================

INVERSION_THRESHOLD = 2.0

# ============================================================
# MINIMUM RULES FOR SIGNAL
# Don't generate signal unless at least this many rules fire
# ============================================================

MIN_RULES_FOR_SIGNAL = 2

# ============================================================
# TIME DECAY
# Weight multiplier based on how recent the reference swing is
# More recent swings get higher weight for cycle-based rules
# ============================================================

TIME_DECAY_HALFLIFE_DAYS = 365  # Halve weight every year

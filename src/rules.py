"""
Gann AutoResearch — Complete Rule Registry.

ALL trading rules from every source: Gann, Bayer, Sepharial, Bible numerology,
Pythagorean geometry, planetary cycles, and decoded Tunnel Through The Air.

This file is READ-ONLY. The agent modifies weights.py, not this file.
Each rule is a pure function: (datetime, instrument_data) -> RuleSignal
"""
import sys
import os
import math
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional

# Add gann-decoder src to path for ephemeris access
DECODER_SRC = os.path.expanduser('~/projects/gann-decoder/src')
if os.path.exists(DECODER_SRC):
    sys.path.insert(0, DECODER_SRC)

from ephemeris import (
    PLANETS, PLANET_NAMES, SUN, MOON, MERCURY, VENUS, MARS,
    JUPITER, SATURN, URANUS, NEPTUNE, PLUTO, NORTH_NODE,
    get_planet_longitude, get_planet_speed, get_planet_declination,
    get_aspect_angle, is_retrograde, date_to_jd,
    get_mercury_speed_minutes, get_sun_max_declination,
    get_sign,
)
import swisseph as swe


@dataclass
class RuleSignal:
    """Output of a rule check."""
    active: bool
    strength: float = 1.0  # 0.0-1.0, how strongly the rule fires
    direction: Optional[str] = None  # 'bullish', 'bearish', or None
    details: str = ''


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def is_near(angle: float, target: float, orb: float) -> tuple[bool, float]:
    """Check if angle is within orb of target. Returns (hit, closeness 0-1)."""
    diff = abs(angle - target) % 360
    if diff > 180:
        diff = 360 - diff
    if diff <= orb:
        closeness = 1.0 - (diff / orb)  # 1.0 = exact, 0.0 = edge of orb
        return True, closeness
    return False, 0.0


def degree_in_sign(longitude: float) -> float:
    """Get degree within current sign (0-30)."""
    return longitude % 30


def get_sign_number(longitude: float) -> int:
    """Get sign number (0=Aries ... 11=Pisces)."""
    return int(longitude / 30)


def is_cardinal_sign(longitude: float) -> bool:
    """Aries, Cancer, Libra, Capricorn."""
    return get_sign_number(longitude) in [0, 3, 6, 9]


def helio_longitude(planet: int, dt: datetime) -> float:
    """Get heliocentric longitude."""
    jd = date_to_jd(dt)
    result = swe.calc_ut(jd, planet, swe.FLG_SWIEPH | swe.FLG_HELCTR)
    return result[0][0]


# ============================================================
# CATEGORY 1: BAYER'S 14 RULES (George Bayer)
# ============================================================

def bayer_01_mercury_station(dt: datetime, **kw) -> RuleSignal:
    """Mercury changes direction (stations retrograde or direct)."""
    speed = get_planet_speed(MERCURY, dt)
    speed_prev = get_planet_speed(MERCURY, dt - timedelta(days=1))
    if (speed_prev > 0 and speed < 0) or (speed_prev < 0 and speed > 0):
        return RuleSignal(True, 1.0, None, 'Mercury station')
    if abs(speed) < 0.05:
        return RuleSignal(True, 0.8, None, f'Mercury near station ({speed:.3f})')
    return RuleSignal(False)


def bayer_02_mars_mercury_speed_59(dt: datetime, **kw) -> RuleSignal:
    """Mars-Mercury speed difference = 59 arc-minutes."""
    mars_spd = get_planet_speed(MARS, dt)
    merc_spd = get_planet_speed(MERCURY, dt)
    diff_arcmin = abs(mars_spd - merc_spd) * 60
    hit, strength = is_near(diff_arcmin, 59, 3)
    if hit:
        return RuleSignal(True, strength, 'bearish', f'Mars-Merc speed diff {diff_arcmin:.1f}\'')
    return RuleSignal(False)


def bayer_03_venus_sun_conjunction(dt: datetime, **kw) -> RuleSignal:
    """Venus conjunct Sun (inferior or superior conjunction)."""
    angle = get_aspect_angle(VENUS, SUN, dt)
    hit, strength = is_near(angle, 0, 2.0)
    if hit:
        return RuleSignal(True, strength, 'bearish', f'Venus-Sun conj ({angle:.1f}°)')
    return RuleSignal(False)


def bayer_04_mercury_cancer_17(dt: datetime, **kw) -> RuleSignal:
    """Mercury at 17°18'27\" Cancer (107.3075° ecliptic)."""
    target = 90 + 17 + 18 / 60 + 27 / 3600
    lon = get_planet_longitude(MERCURY, dt)
    hit, strength = is_near(lon, target, 1.0)
    if hit:
        return RuleSignal(True, strength, None, f'Merc at Cancer 17°18\'')
    return RuleSignal(False)


def bayer_05_retro_venus_conj_direct_mercury(dt: datetime, **kw) -> RuleSignal:
    """Retrograde Venus conjunct direct Mercury."""
    if not is_retrograde(VENUS, dt) or is_retrograde(MERCURY, dt):
        return RuleSignal(False)
    angle = get_aspect_angle(VENUS, MERCURY, dt)
    hit, strength = is_near(angle, 0, 2.0)
    if hit:
        return RuleSignal(True, strength, None, 'Retro Venus conj direct Merc')
    return RuleSignal(False)


def bayer_06_retro_mercury_over_sun(dt: datetime, **kw) -> RuleSignal:
    """Retrograde Mercury conjunct Sun (inferior conjunction)."""
    if not is_retrograde(MERCURY, dt):
        return RuleSignal(False)
    angle = get_aspect_angle(MERCURY, SUN, dt)
    hit, strength = is_near(angle, 0, 2.0)
    if hit:
        return RuleSignal(True, strength, None, 'Retro Merc over Sun')
    return RuleSignal(False)


def bayer_07_mercury_speed_59_or_118(dt: datetime, **kw) -> RuleSignal:
    """Mercury speed at 59' or 118' (1°58')."""
    spd_min = abs(get_mercury_speed_minutes(dt))
    for target in [59, 118]:
        hit, strength = is_near(spd_min, target, 3)
        if hit:
            return RuleSignal(True, strength, None, f'Merc speed {spd_min:.0f}\'')
    return RuleSignal(False)


def bayer_08_mars_mercury_161_retro(dt: datetime, **kw) -> RuleSignal:
    """Mars-Mercury angle 161°21'18\" with Mars retrograde."""
    if not is_retrograde(MARS, dt):
        return RuleSignal(False)
    target = 161 + 21 / 60 + 18 / 3600
    angle = get_aspect_angle(MARS, MERCURY, dt)
    hit, strength = is_near(angle, target, 2.0)
    if hit:
        return RuleSignal(True, strength, 'bullish', f'Mars-Merc 161° (Mars retro)')
    return RuleSignal(False)


def bayer_09_venus_decl_sun_extreme(dt: datetime, **kw) -> RuleSignal:
    """Venus declination crosses Sun's maximum declination (~23.44°)."""
    venus_decl = abs(get_planet_declination(VENUS, dt))
    sun_max = get_sun_max_declination()
    diff = abs(venus_decl - sun_max)
    if diff < 0.5:
        return RuleSignal(True, 1.0 - diff, None, f'Venus decl {venus_decl:.2f}° near Sun max')
    return RuleSignal(False)


def bayer_10_mars_16_55_any_sign(dt: datetime, **kw) -> RuleSignal:
    """Mars at 16°55'46\" of any sign."""
    target = 16 + 55 / 60 + 46 / 3600
    deg = degree_in_sign(get_planet_longitude(MARS, dt))
    hit, strength = is_near(deg, target, 0.5)
    if hit:
        return RuleSignal(True, strength, None, f'Mars at {deg:.2f}° of sign')
    return RuleSignal(False)


def bayer_11_mercury_half_retrograde(dt: datetime, **kw) -> RuleSignal:
    """Mercury at midpoint of retrograde (fastest backward speed)."""
    if not is_retrograde(MERCURY, dt):
        return RuleSignal(False)
    spd = get_planet_speed(MERCURY, dt)
    spd_prev = get_planet_speed(MERCURY, dt - timedelta(days=1))
    spd_next = get_planet_speed(MERCURY, dt + timedelta(days=1))
    if spd < spd_prev and spd < spd_next:
        return RuleSignal(True, 1.0, 'bullish', 'Mercury half-retro (bottom)')
    return RuleSignal(False)


def bayer_12_mars_16_35_plus_330(dt: datetime, **kw) -> RuleSignal:
    """Mars at 16°35' + 330° offset."""
    target = 16 + 35 / 60
    deg = degree_in_sign(get_planet_longitude(MARS, dt))
    hit, strength = is_near(deg, target, 0.5)
    if hit:
        return RuleSignal(True, strength, 'bullish', 'Mars 16°35\' + 330°')
    return RuleSignal(False)


def bayer_13_venus_perihelion(dt: datetime, **kw) -> RuleSignal:
    """Venus passes heliocentric perihelion (~131.5°)."""
    venus_h = helio_longitude(VENUS, dt)
    hit, strength = is_near(venus_h, 131.5, 2.0)
    if hit:
        return RuleSignal(True, strength, 'bullish', f'Venus at perihelion ({venus_h:.1f}°)')
    return RuleSignal(False)


def bayer_14_mercury_scorp_sag_cap(dt: datetime, **kw) -> RuleSignal:
    """Mercury at key Scorpio/Sagittarius/Capricorn degrees."""
    lon = get_planet_longitude(MERCURY, dt)
    targets = [229.6, 259.6, 294.233]
    for t in targets:
        hit, strength = is_near(lon, t, 1.0)
        if hit:
            return RuleSignal(True, strength, None, f'Merc at {lon:.1f}° (Bayer 14)')
    return RuleSignal(False)


# ============================================================
# CATEGORY 2: PLANETARY ASPECTS (Gann's primary system)
# ============================================================

MAJOR_ASPECTS = {0: 'conjunction', 60: 'sextile', 90: 'square',
                 120: 'trine', 180: 'opposition'}
MINOR_ASPECTS = {45: 'semi-square', 72: 'quintile', 135: 'sesquiquadrate',
                 144: 'biquintile', 150: 'quincunx'}

# Key planet pairs Gann emphasized
GANN_PAIRS = [
    (MARS, JUPITER, 'Mars-Jupiter'),
    (MARS, SATURN, 'Mars-Saturn'),
    (JUPITER, SATURN, 'Jupiter-Saturn'),
    (JUPITER, URANUS, 'Jupiter-Uranus'),
    (SATURN, URANUS, 'Saturn-Uranus'),
    (SATURN, NEPTUNE, 'Saturn-Neptune'),
    (JUPITER, NEPTUNE, 'Jupiter-Neptune'),
    (JUPITER, PLUTO, 'Jupiter-Pluto'),
    (SATURN, PLUTO, 'Saturn-Pluto'),
    (MARS, URANUS, 'Mars-Uranus'),
]


def aspect_mars_jupiter(dt: datetime, **kw) -> RuleSignal:
    """Mars-Jupiter aspects (all major + minor)."""
    angle = get_aspect_angle(MARS, JUPITER, dt)
    for target, name in {**MAJOR_ASPECTS, **MINOR_ASPECTS}.items():
        hit, strength = is_near(angle, target, 2.0)
        if hit:
            direction = 'bullish' if name == 'trine' else ('bearish' if name == 'opposition' else None)
            return RuleSignal(True, strength, direction, f'Mars-Jupiter {name} ({angle:.1f}°)')
    return RuleSignal(False)


def aspect_mars_saturn(dt: datetime, **kw) -> RuleSignal:
    """Mars-Saturn aspects."""
    angle = get_aspect_angle(MARS, SATURN, dt)
    for target, name in MAJOR_ASPECTS.items():
        hit, strength = is_near(angle, target, 2.0)
        if hit:
            return RuleSignal(True, strength, None, f'Mars-Saturn {name} ({angle:.1f}°)')
    return RuleSignal(False)


def aspect_jupiter_saturn(dt: datetime, **kw) -> RuleSignal:
    """Jupiter-Saturn aspects (Great Conjunction cycle — 20 year)."""
    angle = get_aspect_angle(JUPITER, SATURN, dt)
    for target, name in MAJOR_ASPECTS.items():
        hit, strength = is_near(angle, target, 2.0)
        if hit:
            return RuleSignal(True, strength, None, f'Jupiter-Saturn {name} ({angle:.1f}°)')
    return RuleSignal(False)


def aspect_jupiter_uranus(dt: datetime, **kw) -> RuleSignal:
    """Jupiter-Uranus aspects (innovation/disruption cycle)."""
    angle = get_aspect_angle(JUPITER, URANUS, dt)
    for target, name in MAJOR_ASPECTS.items():
        hit, strength = is_near(angle, target, 2.0)
        if hit:
            return RuleSignal(True, strength, None, f'Jupiter-Uranus {name} ({angle:.1f}°)')
    return RuleSignal(False)


def aspect_saturn_uranus(dt: datetime, **kw) -> RuleSignal:
    """Saturn-Uranus aspects (structure vs revolution)."""
    angle = get_aspect_angle(SATURN, URANUS, dt)
    for target, name in MAJOR_ASPECTS.items():
        hit, strength = is_near(angle, target, 2.0)
        if hit:
            return RuleSignal(True, strength, None, f'Saturn-Uranus {name} ({angle:.1f}°)')
    return RuleSignal(False)


def aspect_saturn_pluto(dt: datetime, **kw) -> RuleSignal:
    """Saturn-Pluto aspects (deep structural change)."""
    angle = get_aspect_angle(SATURN, PLUTO, dt)
    for target, name in MAJOR_ASPECTS.items():
        hit, strength = is_near(angle, target, 2.0)
        if hit:
            return RuleSignal(True, strength, None, f'Saturn-Pluto {name} ({angle:.1f}°)')
    return RuleSignal(False)


# ============================================================
# CATEGORY 3: PLANETARY INGRESSES & STATIONS
# ============================================================

def planet_station(planet: int, planet_name: str, dt: datetime) -> RuleSignal:
    """Check if planet is stationing (speed near zero)."""
    speed = get_planet_speed(planet, dt)
    threshold = 0.01 if planet in [JUPITER, SATURN, URANUS, NEPTUNE, PLUTO] else 0.05
    if abs(speed) < threshold:
        retro = 'SR' if speed < 0 else 'SD'
        return RuleSignal(True, 1.0, None, f'{planet_name} station {retro}')
    return RuleSignal(False)


def station_mars(dt: datetime, **kw) -> RuleSignal:
    return planet_station(MARS, 'Mars', dt)

def station_jupiter(dt: datetime, **kw) -> RuleSignal:
    return planet_station(JUPITER, 'Jupiter', dt)

def station_saturn(dt: datetime, **kw) -> RuleSignal:
    return planet_station(SATURN, 'Saturn', dt)


def ingress_mars(dt: datetime, **kw) -> RuleSignal:
    """Mars entering a new sign."""
    lon_today = get_planet_longitude(MARS, dt)
    lon_yesterday = get_planet_longitude(MARS, dt - timedelta(days=1))
    if int(lon_today / 30) != int(lon_yesterday / 30):
        sign = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir',
                'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'][int(lon_today / 30)]
        return RuleSignal(True, 1.0, None, f'Mars ingress {sign}')
    return RuleSignal(False)


def ingress_outer(dt: datetime, **kw) -> RuleSignal:
    """Any outer planet (Jupiter-Pluto) entering a new sign."""
    for planet, name in [(JUPITER, 'Jupiter'), (SATURN, 'Saturn'),
                         (URANUS, 'Uranus'), (NEPTUNE, 'Neptune'), (PLUTO, 'Pluto')]:
        lon_today = get_planet_longitude(planet, dt)
        lon_yesterday = get_planet_longitude(planet, dt - timedelta(days=1))
        if int(lon_today / 30) != int(lon_yesterday / 30):
            sign = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir',
                    'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'][int(lon_today / 30)]
            return RuleSignal(True, 1.0, None, f'{name} ingress {sign}')
    return RuleSignal(False)


# ============================================================
# CATEGORY 4: GANN CARDINAL DEGREES & GEOMETRY
# ============================================================

def mars_cardinal(dt: datetime, **kw) -> RuleSignal:
    """Mars at cardinal points (0°, 90°, 180°, 270°)."""
    lon = get_planet_longitude(MARS, dt)
    for card in [0, 90, 180, 270]:
        hit, strength = is_near(lon, card, 5.0)
        if hit:
            return RuleSignal(True, strength, None, f'Mars cardinal {card}° ({lon:.1f}°)')
    return RuleSignal(False)


def saturn_cardinal(dt: datetime, **kw) -> RuleSignal:
    """Saturn at cardinal points."""
    lon = get_planet_longitude(SATURN, dt)
    for card in [0, 90, 180, 270]:
        hit, strength = is_near(lon, card, 3.0)
        if hit:
            return RuleSignal(True, strength, None, f'Saturn cardinal {card}° ({lon:.1f}°)')
    return RuleSignal(False)


def mars_gann_degrees(dt: datetime, **kw) -> RuleSignal:
    """Mars at Gann's key degree positions (45° multiples)."""
    lon = get_planet_longitude(MARS, dt)
    for deg in [45, 90, 135, 180, 225, 270, 315, 360]:
        hit, strength = is_near(lon, deg % 360, 3.0)
        if hit:
            return RuleSignal(True, strength, None, f'Mars at Gann {deg}° ({lon:.1f}°)')
    return RuleSignal(False)


def square_of_9_price_time(dt: datetime, **kw) -> RuleSignal:
    """Square of 9 price-time relationship.
    Check if current price square root relates to time degrees.
    Requires price data passed via kw['price']."""
    price = kw.get('price')
    if price is None or price <= 0:
        return RuleSignal(False)
    sqrt_price = math.sqrt(price)
    # Check if sqrt price is near a whole number or .5 (Gann levels)
    frac = sqrt_price % 1
    if frac < 0.05 or frac > 0.95 or abs(frac - 0.5) < 0.05:
        return RuleSignal(True, 0.7, None, f'SQ9 price level (√{price:.0f}={sqrt_price:.2f})')
    return RuleSignal(False)


# ============================================================
# CATEGORY 5: ECLIPSE & LUNAR CYCLES
# ============================================================

def eclipse_window(dt: datetime, **kw) -> RuleSignal:
    """Near a solar or lunar eclipse."""
    sun_lon = get_planet_longitude(SUN, dt)
    moon_lon = get_planet_longitude(MOON, dt)
    node_lon = get_planet_longitude(NORTH_NODE, dt)

    sun_moon = abs(sun_lon - moon_lon) % 360
    if sun_moon > 180:
        sun_moon = 360 - sun_moon

    sun_node = abs(sun_lon - node_lon) % 360
    if sun_node > 180:
        sun_node = 360 - sun_node

    # Solar eclipse: new moon near node
    if sun_moon < 5 and (sun_node < 18):
        return RuleSignal(True, 1.0, None, 'Solar eclipse window')
    # Lunar eclipse: full moon near node
    if abs(sun_moon - 180) < 5 and (sun_node < 18 or abs(sun_node - 180) < 18):
        return RuleSignal(True, 1.0, None, 'Lunar eclipse window')
    return RuleSignal(False)


def moon_declination_extreme(dt: datetime, **kw) -> RuleSignal:
    """Moon at maximum/minimum declination (~28.5° or ~18.5°)."""
    decl = get_planet_declination(MOON, dt)
    decl_prev = get_planet_declination(MOON, dt - timedelta(hours=12))
    decl_next = get_planet_declination(MOON, dt + timedelta(hours=12))
    # At extreme if declination reverses
    if (decl > decl_prev and decl > decl_next) or (decl < decl_prev and decl < decl_next):
        direction = 'bearish' if decl > 0 else 'bullish'
        return RuleSignal(True, abs(decl) / 28.5, direction,
                          f'Moon decl extreme ({decl:.1f}°)')
    return RuleSignal(False)


def new_moon(dt: datetime, **kw) -> RuleSignal:
    """New Moon (Sun-Moon conjunction)."""
    angle = get_aspect_angle(SUN, MOON, dt)
    hit, strength = is_near(angle, 0, 5.0)
    if hit:
        return RuleSignal(True, strength, None, f'New Moon ({angle:.1f}°)')
    return RuleSignal(False)


def full_moon(dt: datetime, **kw) -> RuleSignal:
    """Full Moon (Sun-Moon opposition)."""
    angle = get_aspect_angle(SUN, MOON, dt)
    hit, strength = is_near(angle, 180, 5.0)
    if hit:
        return RuleSignal(True, strength, None, f'Full Moon ({angle:.1f}°)')
    return RuleSignal(False)


# ============================================================
# CATEGORY 6: GANN TIME CYCLES (from decoded Tunnel)
# ============================================================

def gann_seasonal(dt: datetime, **kw) -> RuleSignal:
    """Gann's seasonal turn dates (equinoxes, solstices, cross-quarter)."""
    month_day = (dt.month, dt.day)
    seasonal_dates = [
        ((3, 20), (3, 22), 'Spring equinox'),
        ((6, 20), (6, 22), 'Summer solstice'),
        ((9, 22), (9, 24), 'Autumn equinox'),
        ((12, 20), (12, 23), 'Winter solstice'),
        ((2, 3), (2, 5), 'Imbolc/cross-quarter'),
        ((5, 5), (5, 7), 'Beltane/cross-quarter'),
        ((8, 6), (8, 8), 'Lammas/cross-quarter'),
        ((11, 6), (11, 8), 'Samhain/cross-quarter'),
        # Gann's specific dates
        ((1, 10), (1, 12), 'Gann Jan turn'),
        ((2, 22), (2, 24), 'Gann Feb turn'),
        ((5, 17), (5, 20), 'Gann May turn'),
        ((7, 3), (7, 5), 'Gann July turn'),
        ((8, 8), (8, 10), 'Gann Aug turn'),
        ((9, 22), (9, 24), 'Gann Sep turn'),
        ((10, 7), (10, 10), 'Gann Oct turn'),
        ((11, 23), (11, 25), 'Gann Nov turn'),
    ]
    for (m1, d1), (m2, d2), name in seasonal_dates:
        if (m1, d1) <= month_day <= (m2, d2):
            return RuleSignal(True, 1.0, None, name)
    return RuleSignal(False)


# ============================================================
# CATEGORY 7: SEPHARIAL'S WORK (Degrees of the Zodiac)
# ============================================================

def sepharial_sensitive_degrees(dt: datetime, **kw) -> RuleSignal:
    """Sepharial's sensitive degrees — specific zodiac degrees with market significance.
    Based on 'The Silver Key' and degree symbolism work."""
    sun_lon = get_planet_longitude(SUN, dt)
    # Sepharial's key degrees (ecliptic positions)
    sensitive = [
        0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165,
        180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345,
        # Sepharial's "critical degrees" per sign
        0, 13, 26,  # Cardinal
        9, 21,       # Fixed
        4, 17,       # Mutable
    ]
    for s in sensitive:
        hit, strength = is_near(sun_lon, s, 1.0)
        if hit:
            return RuleSignal(True, strength, None, f'Sepharial sensitive {s}° (Sun at {sun_lon:.1f}°)')
    return RuleSignal(False)


def sepharial_lunar_mansion(dt: datetime, **kw) -> RuleSignal:
    """Lunar mansions (28 divisions of zodiac by Moon) — Sepharial & Arabic astrology."""
    moon_lon = get_planet_longitude(MOON, dt)
    mansion = int(moon_lon / (360 / 28)) + 1
    # Certain mansions are considered favorable/unfavorable for commerce
    bullish_mansions = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28]
    bearish_mansions = [3, 6, 9, 12, 15, 18, 21, 24, 27]
    if mansion in bullish_mansions:
        return RuleSignal(True, 0.5, 'bullish', f'Lunar mansion {mansion} (favorable)')
    if mansion in bearish_mansions:
        return RuleSignal(True, 0.5, 'bearish', f'Lunar mansion {mansion} (unfavorable)')
    return RuleSignal(False)


# ============================================================
# CATEGORY 8: BIBLICAL NUMEROLOGY (Gann's hidden system)
# ============================================================

def biblical_cycle_check(dt: datetime, **kw) -> RuleSignal:
    """Check if current date falls on biblical number cycles from reference dates.
    Gann used: 7, 12, 30, 40, 49, 50, 70, 144, 360, 490 day cycles.
    The 'past_swings' kwarg provides reference dates."""
    past_swings = kw.get('past_swings', [])
    if not past_swings:
        return RuleSignal(False)

    biblical_numbers = [7, 12, 30, 40, 49, 50, 70, 144, 360, 490]
    hits = 0
    details = []

    for swing_dt in past_swings[-20:]:  # Last 20 swings
        days = abs((dt - swing_dt).days)
        for num in biblical_numbers:
            # Check direct multiples
            if days > 0 and days % num == 0:
                mult = days // num
                if mult <= 10:  # Reasonable multiple range
                    hits += 1
                    if hits <= 3:
                        details.append(f'{num}×{mult}={days}d')

    if hits >= 2:
        return RuleSignal(True, min(hits / 5, 1.0), None,
                          f'Biblical cycles: {", ".join(details)}')
    return RuleSignal(False)


def daniel_490_cycle(dt: datetime, **kw) -> RuleSignal:
    """Daniel's 70 weeks (490 days) — Gann's key biblical cycle.
    "Seventy weeks are determined" (Daniel 9:24).
    Validated at 4.8× lift on Gold."""
    past_swings = kw.get('past_swings', [])
    for swing_dt in past_swings[-30:]:
        days = abs((dt - swing_dt).days)
        for mult in range(1, 5):
            target = 490 * mult
            if abs(days - target) <= 2:
                return RuleSignal(True, 1.0, None, f'Daniel 490×{mult} cycle ({days}d)')
    return RuleSignal(False)


# ============================================================
# CATEGORY 9: PYTHAGOREAN GEOMETRY & SACRED MATH
# ============================================================

def pythagorean_squares(dt: datetime, **kw) -> RuleSignal:
    """Natural squares of time — Gann's 'squaring of time'.
    Check if days from reference are perfect squares or relate to
    Pythagorean triples (3-4-5, 5-12-13, 8-15-17, 7-24-25)."""
    past_swings = kw.get('past_swings', [])
    if not past_swings:
        return RuleSignal(False)

    for swing_dt in past_swings[-10:]:
        days = abs((dt - swing_dt).days)
        if days <= 0:
            continue
        sqrt_d = math.sqrt(days)
        # Perfect square
        if sqrt_d == int(sqrt_d):
            return RuleSignal(True, 0.8, None, f'Perfect square: {int(sqrt_d)}²={days}d')
        # Near perfect square (within 1 day)
        nearest_sq = round(sqrt_d) ** 2
        if abs(days - nearest_sq) <= 1 and nearest_sq > 4:
            return RuleSignal(True, 0.5, None, f'Near square: {round(sqrt_d)}²={nearest_sq} (~{days}d)')

    return RuleSignal(False)


def gann_hexagon_numbers(dt: datetime, **kw) -> RuleSignal:
    """Gann's hexagon numbers: 1, 7, 19, 37, 61, 91, 127, 169, 217, 271, 331, 397.
    These are centered hexagonal numbers. Check days from swings."""
    hex_numbers = [7, 19, 37, 61, 91, 127, 169, 217, 271, 331, 397]
    past_swings = kw.get('past_swings', [])

    for swing_dt in past_swings[-15:]:
        days = abs((dt - swing_dt).days)
        for h in hex_numbers:
            if abs(days - h) <= 1:
                return RuleSignal(True, 0.7, None, f'Hexagon number {h} ({days}d from swing)')
    return RuleSignal(False)


def golden_ratio_time(dt: datetime, **kw) -> RuleSignal:
    """Fibonacci/golden ratio time relationships.
    Gann and Fibonacci share roots in sacred geometry.
    Check if days from swings are Fibonacci numbers or golden ratio multiples."""
    fibs = [8, 13, 21, 34, 55, 89, 144, 233, 377, 610]
    past_swings = kw.get('past_swings', [])

    for swing_dt in past_swings[-15:]:
        days = abs((dt - swing_dt).days)
        for f in fibs:
            if abs(days - f) <= 1:
                return RuleSignal(True, 0.6, None, f'Fibonacci {f} ({days}d from swing)')
    return RuleSignal(False)


# ============================================================
# CATEGORY 10: DECODED TUNNEL CYCLES (from research)
# ============================================================

def tunnel_700_mars_sidereal(dt: datetime, **kw) -> RuleSignal:
    """700-day cycle (Mars sidereal period) — decoded from Tunnel.
    '700 miles' destruction radius = 700 days = Mars sidereal.
    Validated at 4.54× lift on Cotton."""
    past_swings = kw.get('past_swings', [])
    for swing_dt in past_swings[-20:]:
        days = abs((dt - swing_dt).days)
        for frac_name, target in [('1×', 687), ('1×(700)', 700),
                                   ('½', 344), ('⅓', 229), ('2×', 1374)]:
            if abs(days - target) <= 2:
                return RuleSignal(True, 1.0, None,
                                  f'Mars sidereal {frac_name} ({days}d)')
    return RuleSignal(False)


def tunnel_755_submarine(dt: datetime, **kw) -> RuleSignal:
    """755-day cycle (2× Saturn synodic) — decoded from Tunnel invention 'Submarine'.
    Validated across 4 instruments."""
    past_swings = kw.get('past_swings', [])
    for swing_dt in past_swings[-20:]:
        days = abs((dt - swing_dt).days)
        if abs(days - 755) <= 2 or abs(days - 378) <= 2:
            name = '755d (2×Sat)' if abs(days - 755) <= 2 else '378d (Sat syn)'
            return RuleSignal(True, 1.0, None, f'Tunnel Submarine {name} ({days}d)')
    return RuleSignal(False)


def tunnel_saturn_synodic(dt: datetime, **kw) -> RuleSignal:
    """Saturn synodic period and fractions — most universal cycle.
    Full: 378d. 7/8: 330d. 3/4: 284d. Validated on 4+ instruments."""
    past_swings = kw.get('past_swings', [])
    targets = [('⅞', 330), ('¾', 284), ('1×', 378), ('½', 189)]
    for swing_dt in past_swings[-20:]:
        days = abs((dt - swing_dt).days)
        for name, target in targets:
            if abs(days - target) <= 2:
                return RuleSignal(True, 1.0, None,
                                  f'Saturn synodic {name} ({days}d)')
    return RuleSignal(False)


def tunnel_jupiter_synodic(dt: datetime, **kw) -> RuleSignal:
    """Jupiter synodic period and fractions.
    Full: 399d. 7/8: 349d. Validated on Cotton, Gold, Crude."""
    past_swings = kw.get('past_swings', [])
    targets = [('⅞', 349), ('1×', 399), ('½', 200)]
    for swing_dt in past_swings[-20:]:
        days = abs((dt - swing_dt).days)
        for name, target in targets:
            if abs(days - target) <= 2:
                return RuleSignal(True, 1.0, None,
                                  f'Jupiter synodic {name} ({days}d)')
    return RuleSignal(False)


# ============================================================
# CATEGORY 11: MARS RETROGRADE SYSTEM (Cotton-specific)
# ============================================================

def mars_retrograde(dt: datetime, **kw) -> RuleSignal:
    """Mars retrograde period — Gann emphasized for Cotton."""
    if is_retrograde(MARS, dt):
        speed = get_planet_speed(MARS, dt)
        return RuleSignal(True, min(abs(speed) * 5, 1.0), None,
                          f'Mars retrograde ({speed:.3f}°/d)')
    return RuleSignal(False)


def mars_retrograde_in_sign(dt: datetime, **kw) -> RuleSignal:
    """Mars retrograde in specific signs (Gann noted sign-specific effects)."""
    if not is_retrograde(MARS, dt):
        return RuleSignal(False)
    lon = get_planet_longitude(MARS, dt)
    sign_num = get_sign_number(lon)
    # Fire/cardinal signs more volatile
    if sign_num in [0, 3, 6, 9]:  # Cardinal
        return RuleSignal(True, 1.0, None, f'Mars retro in cardinal sign')
    if sign_num in [0, 4, 8]:  # Fire
        return RuleSignal(True, 0.8, None, f'Mars retro in fire sign')
    return RuleSignal(True, 0.5, None, f'Mars retro')


# ============================================================
# CATEGORY 12: INVERSION DETECTION
# ============================================================

def inversion_danger_mars_cardinal(dt: datetime, **kw) -> RuleSignal:
    """HIGH inversion risk: Mars at cardinal points."""
    lon = get_planet_longitude(MARS, dt)
    for card in [0, 90, 180, 270]:
        hit, _ = is_near(lon, card, 5.0)
        if hit:
            return RuleSignal(True, 1.0, None, 'INVERSION DANGER: Mars cardinal')
    return RuleSignal(False)


def inversion_safety_mars_jupiter_trine(dt: datetime, **kw) -> RuleSignal:
    """LOW inversion risk: Mars-Jupiter trine (0% inversions historically)."""
    angle = get_aspect_angle(MARS, JUPITER, dt)
    hit, strength = is_near(angle, 120, 8.0)
    if hit:
        return RuleSignal(True, strength, None, 'INVERSION SAFE: Mars-Jupiter trine')
    return RuleSignal(False)


# ============================================================
# MASTER RULE REGISTRY
# ============================================================

RULE_REGISTRY = {
    # Bayer Rules (14)
    'bayer_01': {'fn': bayer_01_mercury_station, 'category': 'bayer', 'source': 'Bayer'},
    'bayer_02': {'fn': bayer_02_mars_mercury_speed_59, 'category': 'bayer', 'source': 'Bayer'},
    'bayer_03': {'fn': bayer_03_venus_sun_conjunction, 'category': 'bayer', 'source': 'Bayer'},
    'bayer_04': {'fn': bayer_04_mercury_cancer_17, 'category': 'bayer', 'source': 'Bayer'},
    'bayer_05': {'fn': bayer_05_retro_venus_conj_direct_mercury, 'category': 'bayer', 'source': 'Bayer'},
    'bayer_06': {'fn': bayer_06_retro_mercury_over_sun, 'category': 'bayer', 'source': 'Bayer'},
    'bayer_07': {'fn': bayer_07_mercury_speed_59_or_118, 'category': 'bayer', 'source': 'Bayer'},
    'bayer_08': {'fn': bayer_08_mars_mercury_161_retro, 'category': 'bayer', 'source': 'Bayer'},
    'bayer_09': {'fn': bayer_09_venus_decl_sun_extreme, 'category': 'bayer', 'source': 'Bayer'},
    'bayer_10': {'fn': bayer_10_mars_16_55_any_sign, 'category': 'bayer', 'source': 'Bayer'},
    'bayer_11': {'fn': bayer_11_mercury_half_retrograde, 'category': 'bayer', 'source': 'Bayer'},
    'bayer_12': {'fn': bayer_12_mars_16_35_plus_330, 'category': 'bayer', 'source': 'Bayer'},
    'bayer_13': {'fn': bayer_13_venus_perihelion, 'category': 'bayer', 'source': 'Bayer'},
    'bayer_14': {'fn': bayer_14_mercury_scorp_sag_cap, 'category': 'bayer', 'source': 'Bayer'},

    # Planetary Aspects (6)
    'aspect_mars_jupiter': {'fn': aspect_mars_jupiter, 'category': 'aspects', 'source': 'Gann'},
    'aspect_mars_saturn': {'fn': aspect_mars_saturn, 'category': 'aspects', 'source': 'Gann'},
    'aspect_jupiter_saturn': {'fn': aspect_jupiter_saturn, 'category': 'aspects', 'source': 'Gann'},
    'aspect_jupiter_uranus': {'fn': aspect_jupiter_uranus, 'category': 'aspects', 'source': 'Gann'},
    'aspect_saturn_uranus': {'fn': aspect_saturn_uranus, 'category': 'aspects', 'source': 'Gann'},
    'aspect_saturn_pluto': {'fn': aspect_saturn_pluto, 'category': 'aspects', 'source': 'Gann'},

    # Stations & Ingresses (4)
    'station_mars': {'fn': station_mars, 'category': 'stations', 'source': 'Gann'},
    'station_jupiter': {'fn': station_jupiter, 'category': 'stations', 'source': 'Gann'},
    'station_saturn': {'fn': station_saturn, 'category': 'stations', 'source': 'Gann'},
    'ingress_mars': {'fn': ingress_mars, 'category': 'stations', 'source': 'Gann'},
    'ingress_outer': {'fn': ingress_outer, 'category': 'stations', 'source': 'Gann'},

    # Cardinal & Geometry (3)
    'mars_cardinal': {'fn': mars_cardinal, 'category': 'geometry', 'source': 'Gann'},
    'saturn_cardinal': {'fn': saturn_cardinal, 'category': 'geometry', 'source': 'Gann'},
    'mars_gann_degrees': {'fn': mars_gann_degrees, 'category': 'geometry', 'source': 'Gann'},
    'square_of_9': {'fn': square_of_9_price_time, 'category': 'geometry', 'source': 'Gann'},

    # Eclipse & Lunar (4)
    'eclipse': {'fn': eclipse_window, 'category': 'lunar', 'source': 'Gann/Sepharial'},
    'moon_declination': {'fn': moon_declination_extreme, 'category': 'lunar', 'source': 'Gann'},
    'new_moon': {'fn': new_moon, 'category': 'lunar', 'source': 'Gann/Sepharial'},
    'full_moon': {'fn': full_moon, 'category': 'lunar', 'source': 'Gann/Sepharial'},

    # Seasonal (1)
    'seasonal': {'fn': gann_seasonal, 'category': 'seasonal', 'source': 'Gann'},

    # Sepharial (2)
    'sepharial_degrees': {'fn': sepharial_sensitive_degrees, 'category': 'sepharial', 'source': 'Sepharial'},
    'sepharial_mansion': {'fn': sepharial_lunar_mansion, 'category': 'sepharial', 'source': 'Sepharial'},

    # Biblical Numerology (2)
    'biblical_cycles': {'fn': biblical_cycle_check, 'category': 'biblical', 'source': 'Bible/Gann'},
    'daniel_490': {'fn': daniel_490_cycle, 'category': 'biblical', 'source': 'Bible/Gann'},

    # Pythagorean Geometry (3)
    'pythagorean_squares': {'fn': pythagorean_squares, 'category': 'pythagorean', 'source': 'Pythagoras/Gann'},
    'hexagon_numbers': {'fn': gann_hexagon_numbers, 'category': 'pythagorean', 'source': 'Gann'},
    'golden_ratio': {'fn': golden_ratio_time, 'category': 'pythagorean', 'source': 'Fibonacci/Gann'},

    # Decoded Tunnel Cycles (4)
    'tunnel_700_mars': {'fn': tunnel_700_mars_sidereal, 'category': 'tunnel', 'source': 'Tunnel decoded'},
    'tunnel_755_submarine': {'fn': tunnel_755_submarine, 'category': 'tunnel', 'source': 'Tunnel decoded'},
    'tunnel_saturn_syn': {'fn': tunnel_saturn_synodic, 'category': 'tunnel', 'source': 'Tunnel decoded'},
    'tunnel_jupiter_syn': {'fn': tunnel_jupiter_synodic, 'category': 'tunnel', 'source': 'Tunnel decoded'},

    # Mars Retrograde System (2)
    'mars_retrograde': {'fn': mars_retrograde, 'category': 'mars', 'source': 'Gann'},
    'mars_retro_sign': {'fn': mars_retrograde_in_sign, 'category': 'mars', 'source': 'Gann'},

    # Inversion Detection (2)
    'inv_danger_mars_cardinal': {'fn': inversion_danger_mars_cardinal, 'category': 'inversion', 'source': 'Backtested'},
    'inv_safety_mars_jup_trine': {'fn': inversion_safety_mars_jupiter_trine, 'category': 'inversion', 'source': 'Backtested'},
}

# Total: 47 rules across 12 categories

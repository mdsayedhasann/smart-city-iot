import math
import random
from datetime import datetime, timezone

# We re-create the simulator's core logic here to test it in isolation.

def rush_hour_factor(hour):
    return 1 + 0.4 * math.sin((hour - 6) / 24 * 2 * math.pi) \
             + 0.4 * math.sin((hour - 18) / 12 * 2 * math.pi)

def make_air_reading(base_pm25):
    factor = rush_hour_factor(datetime.now(timezone.utc).hour)
    return round(max(0, random.gauss(base_pm25, 6) * factor), 1)


def test_pm25_is_never_negative():
    # Even with a low base and many tries, readings must stay >= 0
    for _ in range(1000):
        assert make_air_reading(15) >= 0

def test_pm25_in_physical_range():
    # Readings should stay within a sane physical range
    for _ in range(1000):
        value = make_air_reading(25)
        assert 0 <= value <= 500

def test_rush_hour_factor_is_positive():
    # The time-of-day multiplier should always be positive
    for hour in range(24):
        assert rush_hour_factor(hour) > 0

def test_rush_hour_peaks_higher_than_night():
    # 8am rush hour should generally have a higher factor than 3am
    assert rush_hour_factor(8) > rush_hour_factor(3)
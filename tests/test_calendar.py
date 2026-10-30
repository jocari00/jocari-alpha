from datetime import date

from jocari.calendar import business_days, easter_sunday


def test_easter():
    assert easter_sunday(2025) == date(2025, 4, 20)
    assert easter_sunday(2026) == date(2026, 4, 5)


def test_target2_2026_holidays_excluded():
    days = {d.date() for d in business_days(date(2025, 12, 31), date(2026, 12, 31))}
    for h in [date(2026, 1, 1), date(2026, 4, 3), date(2026, 4, 6), date(2026, 5, 1),
              date(2026, 12, 25)]:
        assert h not in days
    assert date(2025, 12, 31) in days
    assert date(2026, 1, 2) in days
    assert date(2026, 1, 6) in days  # Spanish holiday, but a TARGET2 business day

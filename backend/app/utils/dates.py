from datetime import date, timedelta


def enumerate_dates(start: date, days: int) -> list[date]:
    return [start + timedelta(days=i) for i in range(days)]

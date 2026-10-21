from datetime import date
from typing import Annotated

from fastapi import HTTPException, Query, status

_MONTH = Query(pattern=r"^\d{4}-\d{2}$", description="YYYY-MM")
MonthParam = Annotated[str, _MONTH]
OptionalMonthParam = Annotated[str | None, _MONTH]


def month_bounds(month: str) -> tuple[date, date]:
    """First day of the month and first day of the next month, from "YYYY-MM"."""
    year, mon = (int(part) for part in month.split("-"))
    if not 1 <= mon <= 12:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "month must be YYYY-MM")
    start = date(year, mon, 1)
    end = date(year + mon // 12, mon % 12 + 1, 1)
    return start, end


def previous_month(start: date) -> date:
    return date(start.year - (start.month == 1), (start.month - 2) % 12 + 1, 1)

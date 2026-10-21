from datetime import datetime, timedelta

from dateutil.rrule import rrulestr

# Guards against pathological rules (e.g. FREQ=MINUTELY) blowing up a request.
MAX_OCCURRENCES = 1000


def overlaps(start: datetime, end: datetime, range_start: datetime, range_end: datetime) -> bool:
    """Whether [start, end) touches [range_start, range_end); zero-length items count too."""
    return start < range_end and (end > range_start or start >= range_start)


def occurrences(
    start: datetime,
    end: datetime,
    rrule: str | None,
    range_start: datetime,
    range_end: datetime,
) -> list[tuple[datetime, datetime]]:
    """(start, end) of each occurrence of an event that overlaps the range."""
    duration = end - start
    if not rrule:
        return [(start, end)] if overlaps(start, end, range_start, range_end) else []

    rule = rrulestr(rrule, dtstart=start)
    result = []
    # Begin early enough to catch an occurrence that started before the range but runs into it.
    for occ_start in rule.xafter(range_start - duration - timedelta(seconds=1), inc=True):
        if occ_start >= range_end or len(result) >= MAX_OCCURRENCES:
            break
        occ_end = occ_start + duration
        if overlaps(occ_start, occ_end, range_start, range_end):
            result.append((occ_start, occ_end))
    return result

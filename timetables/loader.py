import re
import json
import calendar
from datetime import datetime

from dateutil.parser import parse as parse_time
from dateutil.relativedelta import relativedelta

from models import TimetableClass

RE = re.compile(r'([A-Za-z]+),? (\d+(?:am|pm)) till (\d+(?:am|pm))')
COMMENT_RE = re.compile(r'(//.*)')

ONE_HOUR = relativedelta(hours=1)
TWO_HOURS = ONE_HOUR * 2


class InvalidClassDefinition(ValueError):
    pass


def spec_parse_time(timestr):
    t = parse_time(timestr)

    # have every date be relative to this one
    # (the only important part of a date is its weekday)
    return t.replace(year=2016, month=2, day=8 + t.weekday())


def parse_times(timestr: str) -> (datetime, datetime):
    match = RE.match(timestr)

    if not match:
        raise InvalidClassDefinition(
            'Classes should be specified in the format: '
            '"{weekday_name}, 10am till 12pm"'
        )

    weekday, start, end = match.groups()

    if weekday not in calendar.day_name:
        raise InvalidClassDefinition(
            'Unknown weekday: "{}"'.format(weekday)
        )

    span = (
        spec_parse_time(start + ' ' + weekday),
        spec_parse_time(end + ' ' + weekday)
    )

    diff = span[1] - span[0]
    diff = relativedelta(seconds=diff.total_seconds())

    # assert a valid length
    if not (diff == ONE_HOUR or diff == TWO_HOURS):
        raise InvalidClassDefinition(
            "Classes should run for one or two hours"
        )

    # assert that is ends and after it starts
    if not (span[0] < span[1]):
        raise InvalidClassDefinition(
            "Classes should end after they start"
        )

    return span


def load_classes() -> list:
    with open('classes.json') as fh:
        data = json.loads(COMMENT_RE.sub('', fh.read()))

    yield from [
        [
            TimetableClass(
                name,
                *parse_times(time)
            )
            for time in set(times)
        ]
        for name, times in data.items()
    ]

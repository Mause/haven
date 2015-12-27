import re
import json
import calendar

from dateutil.parser import parse as parse_time
from dateutil.relativedelta import relativedelta

from models import TimetableClass

RE = re.compile(r'([A-Za-z]+),? (\d+(?:am|pm)) till (\d+(?:am|pm))')
COMMENT_RE = re.compile(r'(//.*)')

ONE_HOUR = relativedelta(hours=1)
TWO_HOURS = ONE_HOUR * 2


def parse_times(timestr):
    weekday, start, end = RE.match(timestr).groups()

    assert weekday in calendar.day_name

    span = (
        parse_time(start + ' ' + weekday),
        parse_time(end + ' ' + weekday)
    )

    diff = span[1] - span[0]
    diff = relativedelta(seconds=diff.total_seconds())

    # assert a valid length
    assert diff == ONE_HOUR or diff == TWO_HOURS, (diff, timestr)

    # assert that is ends and after it starts
    assert span[0] < span[1], span

    return span


def load_classes():
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

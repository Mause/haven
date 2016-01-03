import calendar
from hashlib import md5
from os.path import join
from datetime import timedelta
from operator import attrgetter
from itertools import product, tee
from collections import defaultdict

from arrow import Arrow
from dateutil.relativedelta import relativedelta

from loader import load_classes
from renderer import render


DAYS = dict(zip(calendar.day_name, range(len(calendar.day_name))))
BAD_DAYS = {
    'Thursday',
    'Tuesday',
    'Friday'
}


def pairs(iterable):
    first, second = tee(iterable)
    next(second)
    return zip(first, second)


def overlaps_on_day(day):
    '''
    Given an iterable of objects with `start` and `end` attributes,
    return True if any of them overlap.
    '''
    day = sorted(
        day,
        key=attrgetter('start')
    )
    return any(
        first.end > second.start
        for first, second in pairs(day)
    )


def sort_into_days(classes):
    '''
    Given an iterable of objects with a `start` attribute, sorts them into the
    weekday on which they occur
    '''
    days = defaultdict(list)

    for class_ in classes:
        days[class_.start.weekday()].append(class_)

    return dict(days)


def overlaps_on_days(days):
    return any(
        overlaps_on_day(classes)
        for classes in days.values()
    )


def none_on_bad_days(days):
    return not any(
        days.get(DAYS[day_name])
        for day_name in BAD_DAYS
    )


def average_starting_time(days):
    days = [
        sorted(day, key=lambda class_: class_.start)[0].start
        for day in days.values()
    ]
    days = map(Arrow.fromdatetime, days)

    days = [
        # get start time relative to start of day
        day - day.floor('day')
        for day in days
    ]
    # average start time :)
    return sum(days[1:], days[0]) / len(days)


def rel(rd):
    rd = {
        'days': rd.days,
        'hours': rd.hours,
        'leapdays': rd.leapdays,
        'microseconds': rd.microseconds,
        'minutes': rd.minutes,
        'months': rd.months,
        'seconds': rd.seconds,
        'years': rd.years
    }
    rd['months'] += rd['years'] * 12
    rd['days'] += rd['months'] * 30
    rd['hours'] += (rd['days'] + rd['leapdays']) * 24
    rd['minutes'] += rd['hours'] * 60
    rd['seconds'] += rd['minutes'] * 60
    rd['microseconds'] += rd['seconds'] * 1000000

    return timedelta(microseconds=rd['microseconds'])


def all_possible_class_combinations(classes):
    possibles = product(*classes)
    possibles = map(sort_into_days, possibles)
    return filter(lambda days: not overlaps_on_days(days), possibles)


def main():
    classes = list(load_classes())


    possibles = all_possible_class_combinations(classes)

    # user specifyable
    possibles = filter(none_on_bad_days, possibles)
    possibles = filter(
        lambda days: average_starting_time(days) > rel(relativedelta(hours=9)),
        possibles
    )

    for possible in possibles:
        do_render(possible)


def determine_filename(possible):
    # work is required to get these things to be deterministic
    filename = sorted(
        (key, sorted(value))
        for key, value in possible.items()
    )
    filename = str(filename)
    filename = md5(filename.encode()).hexdigest()
    return '{}.png'.format(filename)


def do_render(possible):
    img = render(possible)

    filename = determine_filename(possible)
    img.save(join('possibles', filename))

if __name__ == '__main__':
    main()

import calendar
from hashlib import md5
from os.path import join
from operator import attrgetter
from itertools import product, tee
from collections import defaultdict

from loader import load_classes
from renderer import render


DAYS = dict(zip(calendar.day_name, range(len(calendar.day_name))))


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
        for day_name in {'Thursday', 'Tuesday', 'Friday'}
    )


def main():
    classes = list(load_classes())


    possibles = product(*classes)
    possibles = map(sort_into_days, possibles)
    possibles = filter(lambda days: not overlaps_on_days(days), possibles)

    # user specifyable
    possibles = filter(none_on_bad_days, possibles)

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

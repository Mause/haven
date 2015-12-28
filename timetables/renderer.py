import calendar
from itertools import chain, count
from matplotlib.cm import get_cmap

from PIL import Image, ImageFont
from PIL.ImageDraw import ImageDraw

CMAP = get_cmap('rainbow')
SOURCE_CODE_PRO = ImageFont.truetype('SourceCodePro-Regular.otf', size=25)
CLASS_TYPES = {
    'Workshop': 'WSP'
}

BASE = 50
RATIO = 70 / 50
DAY_WIDTH = BASE
HOUR_HEIGHT = int(RATIO * BASE)
NUM_DAYS = 5
HOURS = 24


def render(days):
    units = {
        class_.name.split(' - ')[0]
        for class_ in chain.from_iterable(days.values())
    }

    colours = build_colours(units)

    img = Image.new(
        'RGBA',
        (
            (NUM_DAYS * DAY_WIDTH),
            (HOURS * HOUR_HEIGHT)
        ),
        color='white'
    )

    draw = ImageDraw(img)

    for day_num, day_name in enumerate(calendar.day_abbr):
        draw.text(
            (
                day_num * DAY_WIDTH,
                (7 * HOUR_HEIGHT) + (HOUR_HEIGHT / 2)
            ),
            day_name.upper(),
            fill='black',
            font=SOURCE_CODE_PRO
        )

    # score hour lines
    for hour in range(HOURS):
        y = hour * HOUR_HEIGHT
        draw.line(
            (
                (0, y),
                (NUM_DAYS * DAY_WIDTH, y),
            ),
            fill='grey'
        )

    # draw class boxes
    for day_num, classes in days.items():
        x = day_num
        for class_ in classes:
            y = class_.start.hour
            start = x * DAY_WIDTH, y * HOUR_HEIGHT

            class_hours = class_.end.hour - class_.start.hour
            stop = (
                start[0] + DAY_WIDTH,
                start[1] + (HOUR_HEIGHT * class_hours)
            )

            draw_rectangle(colours, class_, draw, start, stop)
            draw_label(draw, start, class_)

    # trim to hours where classes actually occur
    return img.crop((
        0,
        int(7.5 * HOUR_HEIGHT),  # classes start at 8am
        NUM_DAYS * DAY_WIDTH,

        ((18 + 1) * HOUR_HEIGHT)
        # classes finish at 6pm (1800 hours in 24 hour time)
        # but we add to include that last hour (5-6pm)
    ))


def draw_label(draw, start, class_):
    unit_name, class_type = class_.name.split(' - ')
    unit_initials = ''.join(
        word[:1]
        for word in unit_name.split()
        if word[:1].isupper() or word[:1].isdigit()
    )
    start = (start[0] + 2, start[1] - 3)
    draw.text(
        start,
        unit_initials,
        font=SOURCE_CODE_PRO
    )
    if class_type in CLASS_TYPES:
        class_type = CLASS_TYPES[class_type]
    else:
        class_type = class_type[:3].upper()
    draw.text(
        (start[0], start[1] + 20),
        class_type,
        font=SOURCE_CODE_PRO
    )


def draw_rectangle(colours, class_, draw, start, stop):
    colour = colours[class_.name.split(' - ')[0]]
    fill, outline = colour, 'black'
    draw.rectangle(
        (start, stop),
        fill=fill,
        outline=outline
    )

    colour = tuple(min(x - 20, 256) for x in colour)
    draw.rectangle(
        (
            start,
            (stop[0], start[1] + (HOUR_HEIGHT * (2/3)))
        ),
        fill=colour,
        outline=outline
    )


def build_colours(units):
    colours = dict(zip(
        sorted(units),
        map(CMAP, count(0, int(256 / len(units))))
    ))
    return {
        name: (
            int(r * 256),
            int(g * 256),
            int(b * 256),
            int(a * 256)
        )
        for name, (r, g, b, a) in colours.items()
    }

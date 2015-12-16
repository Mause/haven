from itertools import chain, count
from matplotlib.cm import get_cmap

from PIL import Image, ImageFont
from PIL.ImageDraw import ImageDraw

CMAP = get_cmap('rainbow')
SOURCE_CODE_PRO = ImageFont.truetype('SourceCodePro-Regular.otf', size=25)

BASE = 50
RATIO = 70 / 50
DAY_WIDTH = BASE
HOUR_HEIGHT = int(RATIO * BASE)
NUM_DAYS = 5
HOURS = 24


def render(days):
    units = {
        class_.name.split()[0]
        for class_ in chain.from_iterable(days.values())
    }

    colours = dict(zip(
        sorted(units),
        map(CMAP, count(0, int(256 / len(units))))
    ))
    colours = {
        name: (
            int(r * 256),
            int(g * 256),
            int(b * 256)
        )
        for name, (r, g, b, _) in colours.items()
    }

    img = Image.new(
        'RGB',
        (
            (NUM_DAYS * DAY_WIDTH),
            (HOURS * HOUR_HEIGHT)
        ),
        color='white'
    )

    draw = ImageDraw(img)

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

            colour = colours[class_.name.split()[0]]
            draw.rectangle(
                (start, stop),
                fill=colour,
                outline=colour
            )

    # trim to hours where classes actually occur
    return img.crop((
        0,
        int(7.5 * HOUR_HEIGHT),  # classes start at 8am
        NUM_DAYS * DAY_WIDTH,
        18 * HOUR_HEIGHT  # classes finish at 6pm (1800 hours in 24 hour time)
    ))

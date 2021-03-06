import json
import logging
from collections import defaultdict

from robobrowser import RoboBrowser
import requests


logging.basicConfig(level=logging.DEBUG)


class InvalidStudyPeriod(Exception):
    pass


class ExtendedRB(RoboBrowser):
    def open(self, *args, **kwargs):
        super().open(*args, **kwargs)
        return self

    def submit_form(self, *args, **kwargs):
        super().submit_form(*args, **kwargs)
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.back()


def groupby(iterable, key):
    items = defaultdict(list)
    for item in iterable:
        items[key(item)].append(item)
    return dict(items)


def get_attrs(el):
    return {
        attr.get('name').split('$Hidden')[-1]: attr.get('value')
        for attr in el.find_all('input')
    }


def parse_classes(browser):
    for day in browser.select('.cssTtbleColDay'):
        day_name = day.find(class_='cssTtbleColHeaderInner').span.text
        for class_ in day.select('.cssClassContainer'):
            attrs = get_attrs(class_)
            if 'ClassNo' not in attrs:
                continue
            name, _, location = class_.div.div.div.find_all('span')

            yield {
                'day': day_name,
                'end': attrs['EndTm'],
                'start': attrs['StartTm'],
                'name': name.text.strip(),
                'location': location.text.strip()
            }


def parse_unit(unit, browser):
    unit_code = (
        unit.find(class_='cssTtableSspNavMasterSpkInfo2')
        .div.span.text.strip()
    )
    unit_name = (
        unit.find(class_='cssTtableSspNavMasterSpkInfo3')
        .div.text.strip()
    )
    change = unit.find(
        class_='cssTtableSspNavMasterAction'
    ).input.get('name')
    change_form = browser.get_form()

    if change not in change_form.submit_fields:
        raise KeyError((change, change_form.submit_fields))

    submit = change_form.submit_fields[change]
    with browser.submit_form(change_form, submit=submit):
        sorted_classes = groupby(
            parse_classes(browser),
            key=lambda class_: class_['name'].rsplit(' ', 1)[0]
        )

    return {
        'unit_code': unit_code,
        'unit_name': unit_name,
        'classes': sorted_classes
    }


def get_root_timetable_page(browser):
    browser.open('https://estudent.curtin.edu.au/eStudent/')
    return browser.open(
        'https://estudent.curtin.edu.au/eStudent/SM/StudentTtable10.aspx?',
        params={
            'r': '#CU.ESTU.STUDENT',
            'f': '#CU.EST.TIMETBL.WEB'
        }
    )


def get_units(study_periods, sess):
    browser = ExtendedRB(history=True, session=sess)

    form = get_root_timetable_page(browser).get_form()
    assert form

    elbList = form['ctl00$Content$ctlFilter$CboStudyPeriodFilter$elbList']

    for sp in study_periods:
        if sp not in elbList.options:
            raise InvalidStudyPeriod(sp)

    for option in study_periods:
        elbList.value = option

        submit = form.submit_fields['ctl00$Content$ctlFilter$BtnSearch']
        with browser.submit_form(form, submit=submit) as page:
            units = page.select('.cssTtableSspNavMasterContainer')
            print(len(units), 'units')
            for unit in units:
                yield parse_unit(unit, browser)


def write_out(units):
    data = {
        unit['unit_name'] + ' - ' + class_[0]['name'].rsplit(' ', 1)[0]:
        [
            '{}, {} till {}'.format(
                option['day'],
                option['start'].replace(":00", ""),
                option['end'].replace(":00", "")
            )
            for option in class_
        ]
        for unit in units
        for class_ in unit['classes'].values()
    }

    with open('timetables/classes.json', 'w') as fh:
        json.dump(data, fh, indent=4)


def main():
    sess = requests.Session()
    import betamax

    bm = betamax.Betamax(sess)

    match_requests_on = [
        # 'digest-auth',
        'path',
        'method',
        'body',
        'host',
        'uri',
        # 'headers',
        'query'
    ]

    with bm.use_cassette('ms', match_requests_on=match_requests_on):
        from main import login
        with open('auth.json') as fh:
            login(sess, *json.load(fh))

        units = list(get_units('2016 Semester 1', sess))

        from pprint import pprint
        pprint(units)

        write_out(units)


if __name__ == '__main__':
    main()


import logging
import json
from collections import defaultdict

import robobrowser
import requests


logging.basicConfig(level=logging.DEBUG)


def groupby(iterable, key):
    items = defaultdict(list)
    for item in iterable:
        items[key(item)].append(item)
    return dict(items)


def parse_classes(browser):
    for day in browser.select('.cssTtbleColDay'):
        day_name = day.find(class_='cssTtbleColHeaderInner').span.text
        for class_ in day.select('.cssClassContainer'):
            attrs = class_.find_all('input')
            attrs = {
                attr.get('name').split('$Hidden')[-1]: attr.get('value')
                for attr in attrs
            }
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

    # move page
    browser.submit_form(
        change_form,
        submit=change_form.submit_fields[change]
    )

    # do work
    sorted_classes = groupby(
        parse_classes(browser),
        key=lambda class_: class_['name'].rsplit(' ', 1)[0]
    )

    # go back
    browser.back()

    return {
        'unit_code': unit_code,
        'unit_name': unit_name,
        'classes': sorted_classes
    }


def get_units(sess):
    browser = robobrowser.RoboBrowser(history=True, session=sess)

    browser.open('https://estudent.curtin.edu.au/eStudent/')
    browser.open(
        'https://estudent.curtin.edu.au/eStudent/SM/StudentTtable10.aspx?',
        params={
            'r': '#CU.ESTU.STUDENT',
            'f': '#CU.EST.TIMETBL.WEB'
        }
    )

    form = browser.get_form()
    assert form

    elbList = form['ctl00$Content$ctlFilter$CboStudyPeriodFilter$elbList']
    # for option in elbList.options:
    for option in ['2016 Semester 1']:
        elbList.value = option

        # move page
        browser.submit_form(
            form,
            submit=form.submit_fields['ctl00$Content$ctlFilter$BtnSearch']
        )

        # do work
        for unit in browser.select('.cssTtableSspNavMasterContainer'):
            yield parse_unit(unit, browser)

        # move back
        browser.back()


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

        units = list(get_units(sess))

        from pprint import pprint
        pprint(units)

        write_out(units)


if __name__ == '__main__':
    main()

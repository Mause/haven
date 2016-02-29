#!/usr/bin/env python3

from getpass import getpass
from icalendar import Calendar, Event
from robobrowser import RoboBrowser
from dateutil.parser import parse as parse_date


text_strip = lambda el: el.text.strip()


def parse_table(table):
    header, *rows = table.select('tr')
    headers = list(map(text_strip, header.select('th')))

    for row in rows:
        cols = map(text_strip, row.select('td'))

        yield dict(zip(headers, cols))


def parse_quiz_table(table):
    return [
        {
            'title': quiz['Title'],
            'due_date': parse_date(quiz['Due date']) if quiz['Due date'] else None,
            'mark': quiz['Your Mark'],
            'weight': float(quiz['Weight'])
        }
        for quiz in parse_table(table)
    ]


def get_root_page(username, password):
    browser = RoboBrowser(parser='html.parser')
    browser.open('http://aim02.curtin.edu.au/')
    return browser


def get_subject_names(username, password):
    return get_root_page().get_form()['SubjectName'].options


def get_quizes(subject_name, username, password):
    browser = get_root_page(username, password)

    form = browser.get_form()

    form['SubjectName'].value = subject_name
    
    form['Command'].value = 'ShowSubjectPage'
    form['StudentID'].value = username
    form['Password'].value = password

    browser.submit_form(form)

    table = browser.select('table')
    return parse_quiz_table(table[0])


def quizes_as_ics(quizes, subject_name):
    cal = Calendar()

    for quiz in quizes:
        if quiz['due_date']:
            ev = Event()

            ev.add('dtstart', quiz['due_date'])
            ev.add('summary', '{} - {}'.format(subject_name, quiz['title']))

            cal.add_component(ev)

    return cal.to_ical()


def main():
    subject_name = 'M136'
    username, password = '17690579', getpass('Password: ')

    quizes = get_quizes(subject_name, username, password)

    with open('out.ics', 'wb') as fh:
        fh.write(quizes_as_ics(quizes, subject_name))

if __name__ == '__main__':
    main()


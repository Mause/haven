#!/usr/bin/env python3
import flask
from try_it import get_quizes, quizes_as_ics

app = flask.Flask(__name__)


@app.route('/calendar/<subject_name>')
def calendar(subject_name):
    auth = flask.request.authorization
    if auth:
        quizes = get_quizes(subject_name, auth.username, auth.password)
        return flask.Response(quizes_as_ics(quizes, subject_name), mimetype='text/calendar')
    else:
        return flask.Response('Not authenticated', 401, {'WWW-Authenticate': 'Basic realm="Login please bro"'})


if __name__ == '__main__':
    app.debug = True
    app.run()


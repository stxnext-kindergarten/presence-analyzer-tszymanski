# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from flask import redirect, abort, url_for, make_response
from flask.ext.mako import render_template
from mako.exceptions import TopLevelLookupException

from presence_analyzer.utils import (
    jsonify, get_data, mean, group_by_weekday, usual_presence_time
)

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def mainpage():
    """
    Renders front page - weekday presence.
    """
    return redirect(url_for('render', template='presence_weekday'))


def render_page_user(template):
    """
    Renders template provided by user if it exists.
    """
    template = ''.join([template, '.html'])
    try:
        return render_template(template)
    except TopLevelLookupException:
        return make_response("Requested template does not exist.", 404)


@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [
        {'user_id': i, 'name': 'User {0}'.format(str(i))}
        for i in data.keys()
    ]


@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    return result


@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]
    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@jsonify
def presence_from_to_view(user_id):
    """
    Returns estimated time between working hours by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = usual_presence_time(data[user_id])
    return [
        [calendar.day_abbr[day], int(value['start']), int(value['end'])]
        for day, value in weekdays.iteritems()
    ]

# -*- coding: utf-8 -*-
"""
Defines views.
"""
import calendar
import locale
import logging
from flask import redirect, url_for, make_response
from flask.ext.mako import render_template
from mako.exceptions import TopLevelLookupException
from lxml import etree

from presence_analyzer.main import app
from presence_analyzer.utils import (
    jsonify, get_data, mean, group_by_weekday, usual_presence_time,
    monthly_hours
)


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
locale.setlocale(locale.LC_COLLATE, 'pl_PL')


def mainpage():
    """
    Renders front page - weekday presence.
    """
    return redirect(url_for('render', template='presence_weekday'))


def render_page_user(template):
    """
    Renders template provided by user if it exists.
    """
    tree = etree.parse(app.config['DATA_XML'])
    xml_server = tree.getroot().find('server')
    host = xml_server.find('host').text
    port = xml_server.find('port').text
    protocol = xml_server.find('protocol').text
    template = ''.join([template, '.html'])
    try:
        return render_template(
            template, avatar_host=''.join([protocol, '://', host, ':', port])
        )
    except TopLevelLookupException:
        return make_response("Requested template does not exist.", 404)


@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    try:
        tree = etree.parse(app.config['DATA_XML'])
        users_from_xml = tree.getroot().find('users')
        xml_users = [
            {
                'user_id': int(user.get('id')),
                'name': user.find('name').text,
                'avatar': user.find('avatar').text
            }
            for user in users_from_xml
        ]
    except IOError:
        log.error(
            'No user data XML file found. '
            'You can download it by running \"bin/update_xml\"'
        )
        xml_users = []
    return sorted(xml_users, key=lambda k: k['name'], cmp=locale.strcoll)


@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return 404

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
        return 404

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
        return 404

    weekdays = usual_presence_time(data[user_id])
    return [
        [calendar.day_abbr[day], int(value['start']), int(value['end'])]
        for day, value in weekdays.iteritems()
    ]


@jsonify
def monthly_hours_view(user_id):
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return 404

    return monthly_hours(data[user_id])

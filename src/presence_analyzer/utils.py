# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
import logging
import time
from json import dumps
from threading import Lock
from functools import wraps
from datetime import datetime
import calendar

from flask import Response

from presence_analyzer.main import app


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
cache = {}
lck = Lock()


def get_key(function, *args, **kw):
    """
    Utility for getting function name with called arguments.
    """
    key = '%s.%s:' % (function.__module__, function.__name__)
    hash_args = [str(arg) for arg in args]
    hash_kw = ['%s:%s' % (k, hash(v)) for k, v in kw.items()]
    return '%s::%s::%s' % (key, hash_args, hash_kw)


def memorize(age, storage=cache):
    """
    Memorizing decorator for caching purposes.
    """
    def _memorize(function):
        def __memorize(*args, **kwargs):
            key = get_key(function, *args, **kwargs)
            try:
                value_age, value = storage[key]
                expired = (age != 0 and (value_age+age) < time.time())
            except KeyError:
                expired = True
            if not expired:
                with lck:
                    return value
            storage[key] = time.time(), function(*args, **kwargs)
            return storage[key][1]
        return __memorize
    return _memorize


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


@memorize(600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def usual_presence_time(items):
    """
    Returns list of start and end times for each day of work.
    """
    user_week = {i: {'start': [], 'end': []} for i in range(7)}
    for dt in items:
        user_week[dt.weekday()]['start'].append(items[dt]['start'])
        user_week[dt.weekday()]['end'].append(items[dt]['end'])
    return {
        day: {
            'start': mean(
                map(seconds_since_midnight, user_week[day]['start'])
            ),
            'end': mean(map(seconds_since_midnight, user_week[day]['end']))
        } for day in user_week
    }


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates interval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def _get_years_and_months_total_hours(items):
    """
    Returns a dict with each year and corresponding month with
    a list of worked hours per day.
    """
    years = {}
    for date, times in items.iteritems():
        years.setdefault(date.year, {})
        years[date.year].setdefault(date.month, [])
        years[date.year][date.month].append(
            interval(times['start'], times['end'])
        )

    return years


def _group_years_summary(years):
    """
    From given years dict, breaks each value list - seconds worked each day
    into a list of months with worked hours.
    """
    result = {}
    for month in range(1, 13):
        for year, data in years.iteritems():
            result.setdefault(year, [])
            if data.get(month):
                result[year].append(
                    [
                        calendar.month_abbr[month],
                        sum(data.get(month)) / 60 ** 2
                    ]
                )
            else:
                result[year].append([calendar.month_abbr[month], 0])

    return result


def monthly_hours(items):
    """
    Returns average working hours for each month in year,
    compatible with google charts api.

    Structure sample:
    [
        ["Year", "2011", "2012", "2013"],
        ["Jan", 0, 197, 139],
        ["Feb", 0, 149, 167],
        ...
        ["Dec", 142, 149, 0]
    ]
    """
    years = _get_years_and_months_total_hours(items)
    result = _group_years_summary(years)
    output = [['Year'] + map(str, years.iterkeys())]

    for x in range(12):
        item = [calendar.month_abbr[x+1]]
        for lst in result.itervalues():
            item.append(lst[x][1])
        output.append(item)

    return output

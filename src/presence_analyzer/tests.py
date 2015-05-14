# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
from __future__ import unicode_literals

import os.path
import json
import datetime
import unittest

from presence_analyzer import main, views, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        self.client = main.app.test_client()
        self.valid_user_id = '10'
        self.invalid_user_id = '20'

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday')

    def test_render_page_user(self):
        """
        Test rendering view.
        """
        resp = self.client.get('render/presence_weekday')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get('render/non_existing_template')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.data, 'Requested template does not exist.')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {'user_id': 10, 'name': 'User 10'})

    def test_api_mean_time_weekday(self):
        """
        Test mean time weekday api responses.
        """
        resp = self.client.get(
            '/api/v1/mean_time_weekday/' + self.valid_user_id
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        resp = self.client.get(
            '/api/v1/mean_time_weekday/' + self.invalid_user_id
        )
        self.assertEqual(resp.status_code, 404)

        expected_data = [
            ['Mon', 0], ['Tue', 30047.0], ['Wed', 24465.0],
            ['Thu', 23705.0], ['Fri', 0], ['Sat', 0], ['Sun', 0]
        ]
        self.assertEqual(data, expected_data)

    def test_presence_weekday_api(self):
        """
        Test presence weekday api responses.
        """
        resp = self.client.get(
            '/api/v1/presence_weekday/' + self.valid_user_id
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        resp = self.client.get(
            '/api/v1/presence_weekday/' + self.invalid_user_id
        )
        self.assertEqual(resp.status_code, 404)

        expected_data = [
            ['Weekday', 'Presence (s)'], ['Mon', 0], ['Tue', 30047],
            ['Wed', 24465], ['Thu', 23705], ['Fri', 0], ['Sat', 0],
            ['Sun', 0]
        ]
        self.assertEqual(data, expected_data)

    def test_presence_from_to_api(self):
        """
        Test for user average working times api.
        """
        resp = self.client.get(
            '/api/v1/presence_from_to/' + self.valid_user_id
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        resp = self.client.get(
            '/api/v1/presence_from_to/' + self.invalid_user_id
        )
        self.assertEqual(resp.status_code, 404)

        expected_data = [
            ['Mon', 0, 0], ['Tue', 34745, 64792], ['Wed', 33592, 58057],
            ['Thu', 38926, 62631], ['Fri', 0, 0], ['Sat', 0, 0], ['Sun', 0, 0]
        ]
        self.assertEqual(data, expected_data)


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_jsonify(self):
        """
        Test JSON decorator.
        """
        resp = utils.jsonify(lambda: {'test': 'test'})()
        self.assertEqual(resp.content_type, 'application/json')
        self.assertDictEqual(json.loads(resp.data), {'test': 'test'})

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_group_by_weekday(self):
        """
        Test group by weekday utility.
        """
        test_data = {
            datetime.date(2013, 9, 10): {
                'start': datetime.time(10, 0, 0),
                'end': datetime.time(11, 0, 0)
            }
        }
        data = utils.group_by_weekday(test_data)
        self.assertEqual(len(data), 7)
        self.assertListEqual(data, [[], [3600], [], [], [], [], []])

    def test_seconds_since_midnight(self):
        """
        Test seconds since midnight utility.
        """
        time = datetime.time(0, 2)
        self.assertEqual(utils.seconds_since_midnight(time), 120)
        time = datetime.time(0)
        self.assertEqual(utils.seconds_since_midnight(time), 0)

    def test_interval(self):
        """
        Test interval utility.
        """
        self.assertEqual(
            utils.interval(datetime.time(0), datetime.time(0, 1)), 60
        )
        self.assertEqual(
            utils.interval(datetime.time(0), datetime.time(0)), 0
        )

    def test_usual_presence_time(self):
        """
        Test usual presence time utility.
        """
        data = utils.get_data()
        desired_data = {
            0: {'start': 0, 'end': 0},
            1: {'start': 34745.0, 'end': 64792.0},
            2: {'start': 33592.0, 'end': 58057.0},
            3: {'start': 38926.0, 'end': 62631.0},
            4: {'start': 0, 'end': 0},
            5: {'start': 0, 'end': 0},
            6: {'start': 0, 'end': 0}
        }
        self.assertDictEqual(utils.usual_presence_time(data[10]), desired_data)


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()

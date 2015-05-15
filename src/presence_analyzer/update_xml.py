"""
Update script for XML user database.
"""
import os
import urllib2
import logging

from presence_analyzer import app


def update():
    """
    Downloads new XML database, then moves it to proper place.
    """
    app.config.from_pyfile(
        os.path.abspath(os.path.join('parts', 'etc', 'deploy.cfg'))
    )
    log = logging.getLogger(__name__)
    url = urllib2.urlopen(app.config['XML_URL'])

    with open(app.config['DATA_XML'], 'wb') as output:
        try:
            output.write(url.read())
        except OSError:
            log.error('OS error occurred.')
        except (urllib2.HTTPError, urllib2.URLError):
            log.error('File could not be downloaded.')
        else:
            log.info('File has been downloaded.')

# -*- coding: utf-8 -*-
"""
Flask app initialization.
"""
from flask import Flask
from flask.ext.mako import MakoTemplates


app = Flask(__name__)  # pylint: disable=invalid-name
mako = MakoTemplates(app)

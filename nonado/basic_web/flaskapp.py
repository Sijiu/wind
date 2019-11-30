#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/11/30 18:48
"""

from flask import Flask
from flask import Response
flask_app = Flask("flaskapp")

@flask_app.route("/index")
def index():
    return Response("Hello webserver I'm from Flask", mimetype="text/plain")

app = flask_app.wsgi_app
#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import json
import time
import bottle
from bottle import request

from utils import log_handler, Project

BASE = os.path.abspath(os.path.dirname(__file__))

pull = 0

@bottle.route("/hook/<repo>/", method="GET")
@bottle.route("/hook/<repo>/", method="POST")
def handler(repo):
    # if request.environ['REMOTE_ADDR'].startswith("") and \
    #                 request.headers.get('X-Github-Event') != "push" or \
    #             not request.headers.get('User-Agent').startswith('GitHub Hookshot'):
    #        return json.dumps({"status":"No Permisstion"})

    if request.method == "POST":

        deliver = json.loads(request._get_body_string().decode())

        project = Project(repo, deliver)
        project.pull_flow(test=False)
        return json.dumps({"status": True})
    return json.dumps({"status": "Forbidden"})


if '__main__' == __name__:
    bottle.run(host='0.0.0.0', port=1234, debug=True, reloader=True)

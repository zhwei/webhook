#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import json
import subprocess
# from datetime import datetime
import logging
# import logging.handlers

import bottle
from bottle import request, app

BASE = os.path.abspath(os.path.dirname(__file__))

def log_handler(log_path, name="webhook"):
    """ create logger """
    logger=logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(log_path)
    formatter = logging.Formatter('%(asctime)s-%(levelname)s:%(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

@bottle.route("/hook/<project>/", method="GET")
@bottle.route("/hook/<project>/", method="POST")
def receive(project):

    if request.headers.get('X-Github-Event') != "push" or \
        not request.headers.get('User-Agent').startswith('GitHub Hookshot'):
            return json.dumps({"status":"No Permisstion"})

    if request.method == "POST":

        config_file = os.path.join(BASE, "configs/%s.json" % project)
        bash_file = os.path.join(BASE, "shell/%s.sh" % project)
        log_file = os.path.join(BASE, "logs/%s.log" % project)

        logger = log_handler(log_file)

        try:
            with open(config_file) as fi:
                con_json = json.loads(fi.read())
            deploy_branch = con_json.get("branch", "master")
        except IOError:
            return json.dumps({"status":"Json File Wrong"})

        if project != request.json['repository']['name']:
            return json.dumps({"status":False})

        if deploy_branch in request.json['ref']:

            logger.info("Pusher is %s" % request.json['pusher']['name'])
            logger.info("Last Message is %s"
                    % request.json['commits'][0]['message'])

            proc = subprocess.Popen("bash %s" % bash_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, shell=True)

            for line in proc.stdout:
                logger.error(line)
            if proc.stderr is not None:
                for line in proc.stderr:
                    logger.error(line)


        return json.dumps({"status": True})

    return json.dumps({"status": "Forbidden"})


app = bottle.app()
#def dev_server():
#    bottle.run(host='0.0.0.0', port=8080, debug=True)
#
#if '__main__' == __name__:
#    from django.utils import autoreload
#    autoreload.main(dev_server)

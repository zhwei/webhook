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

def log_handler(log_path):
    """ create logger """
    logger=logging.getLogger("webhook")
    logger.setLevel(logging.WARNING)

    handler = logging.FileHandler(log_path)
    formatter = logging.Formatter('%(asctime)s-%(levelname)s:%(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

@bottle.route("/")
def index():

    return "hello"

@bottle.route("/hook/<project>/", method="GET")
@bottle.route("/hook/<project>/", method="POST")
def receive(project):

    if request.method == "POST":

        config_file = "./configs/%s.json" % project
        bash_file = "./shell/%s.sh" % project
        log_file = os.path.join(BASE, "logs/%s.log" % project)

        try:
            with open(config_file) as fi:
                con_json = json.loads(fi.read())
        except IOError:
            pass

        if request.json['action'] == "push":

            proc = subprocess.Popen(bash_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, shell=True)

            logger = log_handler(log_file)

            for line in proc.stdout:
                logger.error(line)
            if proc.stderr is not None:
                for line in proc.stderr:
                    logger.error(line)


        return json.dumps({"status": True})

    return project



#def dev_server():
#    bottle.run(host='0.0.0.0', port=8080, debug=True)
#
#if '__main__' == __name__:
#    from django.utils import autoreload
#    autoreload.main(dev_server)

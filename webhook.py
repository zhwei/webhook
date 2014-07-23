#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import subprocess

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

class StdErrError(Exception):
    """ 标准错误
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class Git:
    """ 整合过程中需要的操作
    """
    def __init__(self, project, path, deliver=None):

        self.config_file = os.path.join(BASE, "configs/{0}.json".format(project))
        self.bash_file = os.path.join(BASE, "shell/{0}.sh".format(project))
        self.log_file = os.path.join(BASE, "logs/{0}.log".format(project))
        self.path = path

        self.logger = log_handler(self.log_file)
        if deliver: self.deliver = deliver
            # self.after_sha = deliver.get("after")
            # self.before_sha = deliver.get("before")
            # self.message = deliver.get("head_commit").get("message")
            # self.pusher = deliver["pusher"].get("name")

    def __sys_call(self, command, ignore_err=False):
        """
        :param command: Shell命令
        :param ignore_err: 存在STDERR是否抛出异常
        :return: None
        """
        ret = subprocess.Popen(command, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, shell=True)
        # 将标准输出和标准错误输出到日志
        for line in ret.stdout:
            self.logger.info(line)
        if ret.stderr is not None:
            for line in ret.stderr:
                self.logger.error(line)
            if not ignore_err:
                raise StdErrError("Exists std error")

    def reset(self, branch, deliver):
        """ 撤销到上一版本
        :param branch: 分支名称[string] eg: master
        :param deliver: GitHub发送的json字典[dict]
        :return: None
        """
        command = ("cd {0} && "
                "git reset --hard {1} && "
                "git clean -df").format(self.path, deliver.get("before", ""))
        self.__sys_call(command, True)  # 忽略标准错误

    def pull(self, branch, deliver):
        """ 从远端拉取最新分支
        :param branch: 分支名称[string] eg: master
        :param deliver: GitHub发送的json字典[dict]
        :return: None
        """
        command = ("cd {0} && "
                "git pull origin {1}").format(self.path, branch)
        try:
            self.__sys_call(command)
        except StdErrError as e:
            self.reset(branch, deliver)

    def deploy(self):
        """ 部署代码， 重启服务
        :return:
        """
        pass


@bottle.route("/hook/<project>/", method="GET")
@bottle.route("/hook/<project>/", method="POST")
def handler(project):

    #if request.headers.get('X-Github-Event') != "push" or \
    #    not request.headers.get('User-Agent').startswith('GitHub Hookshot'):
    #        return json.dumps({"status":"No Permisstion"})

    # print(request.environ['REMOTE_ADDR'])

    if request.method == "POST":

        config_file = os.path.join(BASE, "configs/{0}.json".format(project))
        bash_file = os.path.join(BASE, "shell/{0}.sh".format(project))
        log_file = os.path.join(BASE, "logs/{0}.log".format(project))

        logger = log_handler(log_file)

        try:
            with open(config_file) as fi:
                con_json = json.loads(fi.read())
            deploy_branch = con_json.get("branch", "master")
        except IOError:
            return json.dumps({"status":"Json File Wrong"})

        request_json = json.loads(request._get_body_string().decode())
        if project != request_json['repository']['name']:
            return json.dumps({"status":False})

        if deploy_branch in request_json['ref']:

            logger.info("Pusher is {}".format(request_json['pusher']['name']))
            logger.info("Last Message is %s" % request_json['commits'][0]['message'])

            proc = subprocess.Popen("bash %s" % bash_file, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, shell=True)
            # roll_back("hello", 1)
            for line in proc.stdout: logger.info(line)
            if proc.stderr is not None:
                for line in proc.stderr: logger.error(line)

        return json.dumps({"status": True})

    return json.dumps({"status": "Forbidden"})


if '__main__' == __name__:
    bottle.run(host='0.0.0.0', port=1234, debug=True, reloader=True)

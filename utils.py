#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import json
import time
import shlex
import logging
import subprocess

BASE = os.path.abspath(os.path.dirname(__file__))


def log_handler(log_path, name="webhook"):
    """ create logger """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(log_path)
    formatter = logging.Formatter('%(asctime)s-%(levelname)s:%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger


class StdErrError(Exception):
    """ 标准错误
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Project:
    """ 封装过程中需要的操作
    """
    def __init__(self, project, deliver=None):
        """
        :param project: 项目名称[string]
        # :param path: 项目路径[string]
        :param deliver: GitHub发送的json字典[dict]
        :return: None
        """
        self.config_file = os.path.join(BASE,
                                        "configs/{0}.json".format(project))

        try:
            with open(self.config_file, "rb") as fi:
                content = fi.read()
            self.config = json.loads(content.decode())
        except IOError:
            self.logger.error("Config File Format Wrong")
            raise
        if self.config.get("name") == project:
            self.name = project
        else:
            self.logger.error("POST to wrong url")
            raise StdErrError

        self.path = self.config.get("location")
        self.branch = self.config.get("branch")

        self.bash_file = os.path.join(BASE, "shell/{0}.sh".format(project))
        self.log_file = os.path.join(BASE, "logs/{0}.log".format(project))
        self.logger = log_handler(self.log_file)
        if deliver:
            self.deliver = deliver

    def __sys_call(self, command, ignore_err=False, script=False):
        """ 调用系统命令，将标准输出和标准错误输出到日志
        :param command: [str] 命令或者shell文件名
                        shell文件统一放在/shell目录中
                        如果是shell脚本注意传参 script=True
        :param ignore_err: 存在STDERR是否抛出异常
        :param script:  如果command为脚本名则传True
        :return: None
        """
        if script: command = "bash {}".format(command)
        ret = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        for line in ret.stdout:
            self.logger.info(line)
        if ret.stderr is not None:
            for line in ret.stderr:
                self.logger.error(line)
            if not ignore_err:
                raise StdErrError("Exists std error")

    def reset(self):
        """ 撤销到上一版本
        :return: None
        """
        self.logger.info("Resetting, Now is {0}".format(
            self.deliver.get("after")))
        os.chdir(self.path)
        _before = self.deliver.get("before", "")
        self.__sys_call("git reset --hard {0}".format(_before), True)  # 忽略标准错误
        self.__sys_call("git clean -df", True)  # 忽略标准错误
        self.logger.info("Reset to {0}".format(_before))

    def pull(self):
        """ 从远端拉取最新分支
        :return: None
        """
        os.chdir(self.path)
        self.__sys_call("git pull origin {}".format(self.branch))
        self.logger.info("Pull Success")

    def __run_script_or_shell(self, command):
        """
        :param command: 脚本名称或命令列表
        :return: None
        """
        if isinstance(command, (tuple, list)):
            for script in command:
                self.__sys_call(script)
        else:
            self.__sys_call(command, script=True)

    def test(self):
        """ 测试部署
        :return:
        """
        self.logger.info("Testing ... ")
        test_script = self.config["script"].get("test")
        self.__run_script_or_shell(test_script)
        self.logger.info("Test Pass")

    def deploy(self):
        """ 部署代码， 重启服务
        :return:
        """
        self.logger.info("Deploying ... ")
        test_script = self.config["script"].get("deploy")
        self.__run_script_or_shell(test_script)
        self.logger.info("Deploy Success")

    def pull_flow(self, test=False):
        """ 工作流： 获取源码，重新部署
        :return:
        """
        self.logger.info("======== Project [{0}]".format(self.name))
        self.logger.info("Pusher is {}".format(self.deliver['pusher']['name']))
        self.logger.info("Last Commit id is {}".format(
            self.deliver['head_commit']['id']))
        self.logger.info("Last Commit Message is {}".format(
            self.deliver['head_commit']['message']))
        self.logger.info("Compare Link: {}".format(self.deliver.get("compare")))
        try:
            self.pull()
            # if test:
            #     self.test()
            # self.deploy()
        except StdErrError:
            self.logger.error("Pull failed, Resetting ... ")
            self.reset()

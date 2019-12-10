#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/6 10:42
"""

from locust import HttpLocust, TaskSet, task, between
import requests

class Index(TaskSet):
    @task(1)
    def index(self):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"}
        req = self.client.get("/index", headers=header)
        if req.status_code == 200:
            print "success"
        else:
            print "fails"


class websitUser(HttpLocust):
    task_set =  Index
    min_wait = 3000
    max_wait = 6000


if __name__ == '__main__':
    import os
    os.system("locust -f locusttest.py --host=http://127.0.0.1:8888")
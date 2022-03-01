# coding: utf-8

import logging
import sys
import time

from flask import jsonify
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logging.basicConfig(level=logging.DEBUG)





path = 'tmp'


# try:
#     while True:
#         time.sleep(1)
# finally:
#     observer.stop()
#     observer.join()



import os
import io
import json

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS


app = Flask(__name__)
CORS(app)  # 解决跨域问题



import os
import io
import json
import sys
import time

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

import logging
logging.basicConfig(level=logging.DEBUG)
with open('tmp/1.txt') as f:
    tmp = f.readlines()
data=tmp  #data是一个大数据库,不能每次掉服务都读取.所以我们用watchdog来监控文件,只有当文件变化时候我们才重新读取这个文件
# 从而避免了io 密集
class MyEventHandler(PatternMatchingEventHandler):
    def __init__(self,patterns,ignore_patterns,ignore_directories,data):
        super().__init__(patterns,ignore_patterns,ignore_directories)
        self.data=data
    #之所以不写删除的逻辑是因为, 如果删除了,那么我们不可能只要空.我们一定会新创建回来一个文件,
    # 所以逻辑写在created里面才对.否则会运行2次.
    def on_modified(self, event):
        print(event)
        # =========这里面写我们的监控逻辑
        with open('tmp/1.txt') as f:
            tmp = f.readlines()
        self.data = tmp
        print('触发了修改',self.data)
    def on_created(self, event):
        print(event)
        # =========这里面写我们的监控逻辑
        with open('tmp/1.txt') as f:
            tmp = f.readlines()
        self.data = tmp
        print('触发了新建',self.data)
    def on_moved(self, event):
        print(event)
        # =========这里面写我们的监控逻辑
        with open('tmp/1.txt') as f:
            tmp = f.readlines()
        self.data = tmp
        print('触发了移动',self.data)
event_handler = MyEventHandler(patterns=['*.txt'],
                               ignore_patterns=['version.py'],
                               ignore_directories=True,data=data)



observer = Observer()
observer.schedule(event_handler, path)
observer.start()

@app.route("/", methods=["POST",'GET'])

def predict():

    return jsonify(event_handler.data)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)








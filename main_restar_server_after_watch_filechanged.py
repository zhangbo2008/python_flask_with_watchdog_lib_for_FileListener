if 1:
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
    changing=False  #是否线程在计算data内容.
    with open('tmp/1.txt') as f:
        tmp = f.readlines()
    data = tmp  # data是一个大数据库,不能每次掉服务都读取.所以我们用watchdog来监控文件,只有当文件变化时候我们才重新读取这个文件

    # 从而避免了io 密集

    def build_database():
        global  changing
        global data
        global  flag
        changing=True
        with open('tmp/1.txt') as f:
            tmp = f.readlines()
            time.sleep(5)
        data = tmp
        flag=time.time()
        changing=False
    flag=time.time()
    #=======光时间错还不够用. 如果 数据库构建中 我们进行了查询.那么新的时间错来不及写入.仍然会返回错误所以要写changing


    class MyEventHandler(PatternMatchingEventHandler):

        # 之所以不写删除的逻辑是因为, 如果删除了,那么我们不可能只要空.我们一定会新创建回来一个文件,
        # 所以逻辑写在created里面才对.否则会运行2次.

        #========这里面我们故意sleep, 来模拟数据库建立很慢的情况.
        def on_modified(self, event):

            print(event)
            # =========这里面写我们的监控逻辑
            build_database()

            print('触发了修改', data)

        def on_created(self, event):
            global data
            print(event)
            # =========这里面写我们的监控逻辑
            build_database()
            data = tmp
            print('触发了新建', data)

        def on_moved(self, event):
            global data
            print(event)
            # =========这里面写我们的监控逻辑
            build_database()
            data = tmp
            print('触发了移动', data)

    event_handler = MyEventHandler(patterns=['*.txt'],
                                   ignore_patterns=['version.py'],
                                   ignore_directories=True)

    observer = Observer()
    observer.schedule(event_handler, path)
    observer.start()

    @app.route("/", methods=["POST", 'GET'])
    def predict():#=========掉服务时候要先check
        global  flag
        global changing
        old=flag
        new=flag
        print("check时间错",old,new)
        if old!=new or changing:
            print("数据库正在构建中!!!!!!!!!!!!!!")
            return jsonify('数据库构建中,请等待数据库构建完成')
        return jsonify(data)

    app.run(host="0.0.0.0", port=8080)





"# python_flask_with_watchdog_lib_for_FileListener" 


想做一个正则匹配的, 用户可以随时修改他要匹配的文件里面内容, 然后他只要一改, 程序就检测到那个文件变了, 让服务重新算一下被匹配的字符串


运行main.py
浏览器里面输入 127.0.0.1:8080 即可看到返回tmp/1.txt 的内容了
当你修改1.txt之后, 不需要手动重启服务, 代码自动会修改里面的变量data
来计算新的1.txt的内容. 如果1.txt内容不变时候,这部分luo9ji是不触发的
从而保证了io密集型的计算不会每次调用接口都触发.






main_restar_server_after_watch_filechanged.py

如果data的计算特别耗时.为了接口返回的准确性.建议重启服务.重新算全部内容.
这个就是这个自动重启服务的代码.

这个不好实现, 先留着.我改成算md5来检测.开始和结尾是否有变化.不变才返回.
md5这个逻辑不对, 如果计算新data的线程没结束.那么data还是没变.
所以需要设置flag来控制.当前是否正则运算中.

终极版本!

main_restar_server_after_watch_filechanged.py

这个版本是最终极解决方案.
设置了一些flag来避免数据库错误读.
只有当数据库更新完毕了,我们才返回正确的结果.
如果数据库构建中,我们会返回请等待数据库构建.

这个代码超级完美,有并发兴趣的同学可以读读.








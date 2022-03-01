# -*-coding: utf-8 -*-
#from data_def import *
distance=34

class test(object):
    def __init__(self):
       pass
    #在类里面改变全局变量的值
    def change_1(self):
        global distance
        distance=90
        print("distance in class:", distance)

    #输出全局变量的值
    def print_value(self):
        global distance
        print("distance in class:", distance)

#在函数里面使用和打印全局变量的值
def function_test():
    global distance
    print("global value in function", distance)
    distance=234
    print("global value in function",distance)

function_test()  #在函数里面使用和改变全局变量的值 34->234
t=test()
t.print_value()  #在类里面打印全局变量的值 234
t.change_1()   #在类里面改变全局变量的值 234->90
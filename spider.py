import threading
import queue


class ThreadPool():
    '''
    线程池
    提供简单的操作函数
    线程间变量传递使用queue.Queue
    '''
    def __init__(self,N_thread=2):
        '''
        N_thread:线程池中线程个数
        '''
        self.N_thread = N_thread
        self.L_thread = list()
        self.running = False

    def creat(self,func,args):
        for i in range(self.N_thread):
            self.L_thread.append(threading.Thread(target = func,args = args))

    def start(self):
        for thread in self.L_thread:
            thread.start()
        self.running = True

    def wait(self):
        for thread in self.L_thread:
            if thread.isAlive():
                thread.join()
        self.running = False

    def run(self):
        '''
        直接调用，则无法实现线程池间并发
        线程间并发，需分别调用线程池各自的start函数后，调用wait函数
        '''
        self.start()
        self.wait()

class Spider():
    '''
    多线程爬虫
    '''
    pass

    
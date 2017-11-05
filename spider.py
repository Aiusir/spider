import threading
import queue
import requests


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
        self._running = queue.Queue()

    def create(self,func,args=(),kwargs={}):
        for i in range(self.N_thread):
            self.L_thread.append(threading.Thread(target = func,args = args,kwargs=kwargs))

    def start(self):
        for thread in self.L_thread:
            thread.start()
        self._running.put("working")

    def wait(self):
        for thread in self.L_thread:
            if thread.isAlive():
                thread.join()
        self._running.get(block=False)

    @property
    def running(self):
        return not self._running.empty()

    def run(self):
        '''
        直接调用，则无法实现线程池间并发
        线程间并发，需分别调用线程池各自的start函数后，调用wait函数
        '''
        self.start()
        self.wait()

class Rule():
    '''
    url与处理函数匹配规则,字典对象
    re:正则表达式规则
    callback:当规则匹配时的处理函数
    '''
    def __init__(self,re=None,callback=None):
        if not isinstance(re,str):
            raise Exception('re should be str')
        if not callable(callback):
            raise Exception('callback should callable')
        self.rule = dict(re=re,callback=callaback)
        

class Spider():
    '''
    多线程爬虫,支持requests参数
    '''
    __version__ = '0.0.1'

    def __init__(self,method,url,presphook,reqthdnum=2,prespthdnum=2,immd=True,**kwargs):
        '''
        method :请求方法
        url: 待请求的url，可以为列表
        presphook:处理响应的钩子函数
        reqthdnum:请求进程数
        prespthdnum:响应处理进程数
        immd：是否收到响应后立即处理
        kwargs:requests支持的其他参数
        '''
        self._method =method
        self._Q_req = queue.Queue()
        self._reg_url(url)
        self._N_req_thd = reqthdnum
        self._Q_resp = queue.Queue()
        self._Q_resu = queue.Queue()
        self._N_presp_thd = prespthdnum
        self._H_presp = None
        self._reg_presp_hook(presphook)
        self._immd = immd
        self._reqparam = kwargs
        self.cookies = requests.cookies.cookiejar_from_dict({})
        self.cookies = self._mergecookies(self._reqparam)
        self._T_req = ThreadPool(self._N_req_thd)
        self._T_presp = ThreadPool(self._N_presp_thd)

    def __repr__(self):
        return '<Spider [%s]>'% self.__version__

    def _reg_url(self,url):
        if isinstance(url,str):
            self._Q_req.put(url)
        elif isinstance(url,list):
            for u in url:
                self._Q_req.put(u)
        else:
            raise Exception('url type error! should be str or list!')

    def _mergecookies(self,kwargs):
        '''
        将作为参数传入的cookies更新到对象cookies中
        '''
        usrcookies = kwargs.get('cookies')
        if usrcookies:
            self.cookies = requests.cookies.merge_cookies(self.cookies,usrcookies)
            kwargs.pop('cookies')
        return self.cookies

    def _preparereq(self):
        '''
        创建请求进程池
        '''
        def request(method,cookies,**kwargs):
            with requests.Session() as session:
                while not self._Q_req.empty():
                    url = self._Q_req.get()
                    response = session.request(method,url,cookies=cookies,**kwargs)
                    self._Q_resp.put(response)

        self._T_req.create(request,args=(self._method,self.cookies,),kwargs=self._reqparam)

    def _reg_presp_hook(self,hook):
        '''
        注册响应处理函数
        该函数必须接受一个response作为入参
        '''
        if callable(hook):
            self._H_presp = hook
        else:
            raise Exception('hook is not callable!')

    def _preparepresp(self):
        '''
        创建响应处理进程池
        '''
        def hookadapter(hook):
            while (not self._Q_resp.empty()) or (self._T_req.running):
                try:
                    response = self._Q_resp.get(block=False)
                    result = hook(response)
                    self._Q_resu.put(result)
                except queue.Empty:
                    pass

        self._T_presp.create(hookadapter,args=(self._H_presp,))

    def login(self,method,url,**kwargs):
        '''
        登陆函数，提取登陆后的cookies
        参数与requests.request一致
        '''
        with requests.Session() as session:
            response = session.request(method,url,**kwargs)
            if response.ok:
                self.cookies = requests.cookies.merge_cookies(self.cookies,session.cookies)
            else:
                raise Exception('login in error!')

    def run(self):
        '''
        根据是否立即处理，采用不同调用方式
        '''
        self._preparereq()
        self._preparepresp()
        if self._immd:
            self._T_req.start()
            self._T_presp.start()
            self._T_req.wait()
            self._T_presp.wait()
        else:
            self._T_req.run()
            self._T_presp.run()
        return self.result

    @property
    def result(self):
        '''
        列表形式的处理结果
        '''
        result_list = list()
        while not self._Q_resu.empty():
            result_list.append(self._Q_resu.get())
        return result_list

class CrwalSpider():
    '''
    模仿scrapy CrwalSpider造的轮子
    '''
    def __init__(self,rules=(),start_url='',parse=None):
        '''
        rules:Rule对象列表
        start_url:起始url
        parse：起始url的处理函数，接收一个response
        '''
        if isinstance(rules = rules):
            self.rules = rules
        if isinstance(start_url,str):
            self.start_url = start_url
        if callable(parse):
            self.parse = parse
        else:
            raise Exception('parse should be callable!')
        self.preparedrules = list()
        self.result = queue.Queue()
        
    def _compile(self):
        pass
    
    def _ismatch(self,url):
        pass

    def _usecallback(self):
        '''
        调用spider处理
        '''
        pass
        
                

if __name__ == '__main__':
    def examplehook(response):
        return response.ok
    url = ['http://www.example.com']*10
    example_spider = Spider('get',url,examplehook,cookies = {'test':'test'},immd=False)
    result = example_spider.run()
    print(example_spider.cookies)
    print(result)




        






        








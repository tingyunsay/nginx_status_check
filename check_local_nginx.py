#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import requests
import logging
import re,time
import commands

#检测本地nginx的ip是否是server端的ip，如果不是，重新验证nginx并重启

config = {
    #检测间隔
    "CHECK_CYCLE":10,
    #nginx的代理结果文件
    "proxy_file":"/etc/nginx/proxy/proxy_upstream.conf"
}

file_name = __file__.split('/')[-1].replace(".py","")
#运行过程中的日志文件在执行目录下的lyric_test.log中
logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='%s.log'%file_name,
                filemode='a')

#将日志打印到标准输出（设定在某个级别之上的错误）
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

#指定间隔时间检测server 端的状态，如果发现本地ip没有在server端出现，重新启动client端发送请求
class Check():
    def get_ip(self, ifname="ppp0"):
        (status, output) = commands.getstatusoutput('ifconfig')
        if status == 0:
            pattern = re.compile(ifname + '.*?inet.*?(\d+\.\d+\.\d+\.\d+).*?netmask', re.S)
            result = re.search(pattern, output)
            if result:
                ip = result.group(1)
                return ip
    def get_nginx_proxy(self):
        path = config['proxy_file']
        res = open(path,"r").read()
        proxy_list = re.findall("\d+\.\d+\.\d+\.\d+:\d+", res)
        return proxy_list


    def check_server_status(self):
        while True:
            logging.info("开始监控server端")
            proxy_list = self.get_nginx_proxy()
            if len(proxy_list) <= 2:
                logging.info("本地的代理ip列表是: %s"%proxy_list)
                try:
                    server_ip = requests.get("http://47.94.247.102:8000/list").content.split('<br>')[:-1]
                    if server_ip:
                        #两个list转成set形式取交集，若不是两个元素，则验证并重启nginx
                        if len(set(proxy_list) & set(server_ip)) != 2:
                            cmd = "python auto_proxy.py >> ./fk_9112.log 2>&1"
                            if commands.getstatusoutput(cmd)[0] != 0:
                                logging.error("重启auto_proxy失败，please check!")
                            else:
                                logging.info("auto_proxy 重启成功.")
                        time.sleep(config['CHECK_CYCLE'])
                except Exception,e:
                    logging.error("获取nginx本地代理ip失败，please check!")

            else:
                logging.error("Get IP Failed")



def run():
    check = Check()
    check.check_server_status()

if __name__ == '__main__':
    run()
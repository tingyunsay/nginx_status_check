#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import requests
import logging
import re,time
import commands
import datetime

config = {
    #检测间隔
    "CHECK_CYCLE":10,


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
    #有时候会出现多个ppp，有ppp1，ppp2等...
    def get_ip(self, ifname="ppp0"):
        (status, output) = commands.getstatusoutput('ifconfig')
        if status == 0:
            pattern = re.compile(ifname + '.*?inet.*?(\d+\.\d+\.\d+\.\d+).*?netmask', re.S)
            result = re.search(pattern, output)
            if result:
                ip = result.group(1)
                return ip

    def client_reload(self):
        cmd = "/usr/bin/supervisorctl reload"
        if commands.getstatusoutput(cmd)[0] != 0:
            logging.error("client 重启失败，please check!")
        else:
            logging.info("client 重启成功.")

    def test_good(self):
        #测试是否被ban，被ban了立刻切换ip
        url = "http://home.zongheng.com/show/userInfo/205877.html"
        try:
            res = requests.get(url,proxies={"http":"http://127.0.0.1:8888"},timeout=3)
            if res.status_code == 200:
                logging.info("返回码200，正常.%s"%datetime.datetime.now())
                return True
            else:
                return False
        except Exception,e:
            logging.warning(e)
        return False


    def check_server_status(self):
        while True:
            logging.info("开始监控server端")
            ip = self.get_ip()
            if ip:
                logging.info("当前ip是: %s"%ip)
                try:
                    server_ip = requests.get("http://47.94.247.102:8000/list").content
                    if server_ip:
                        server_ip = server_ip.split('<br>')[:-1]
                        ip = ip+":8888"
                        #在服务端没检测到
                        #或者访问受限，被ban了，直接重启
                        if ip not in server_ip or not self.test_good():
                            self.client_reload()
                    else:
                        logging.warning("服务端出错，本地重启..")
                        self.client_reload()
                    time.sleep(config['CHECK_CYCLE'])
                except Exception,e:
                    logging.error("获取server端ip失败，本地重启.")
                    self.client_reload()
                    time.sleep(config['CHECK_CYCLE'])
            else:
                logging.error("Get IP Failed，本地重启.")
                self.client_reload()
                time.sleep(config['CHECK_CYCLE'])

def run():
    check = Check()
    check.check_server_status()
    #print check.test_good()
if __name__ == '__main__':
    run()
import requests
import json
import time
import datetime
import re
from encry import get_singnature
from requests.exceptions import SSLError
import threading
import logging

logging.basicConfig(level=logging.INFO)


class TestThreadTimer(threading.Thread):
    def __init__(self, interval, func, args=()):
        super(TestThreadTimer, self).__init__()
        self.func = func
        self.args = args
        self.interval = interval
        self.finished = threading.Event()

    def run(self):
        self.finished.wait(self.interval)
        self.result = self.func(*self.args)
        self.finished.set()

    def get_result(self):
        try:
            return self.result
        except Exception as e:
            logging.error("获取返回值出错，错误为：", e)
            return None


class Badminton:
    def __init__(self, token):
        # 截取年月日即可
        self.years = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())[:10]
        # 开始抢场地的时间
        self.aim_time = '11:59:00'
        self.times_to_id = []
        text = str(int(time.time() * 1000))
        self.headers = {
            # 防止request中出现中文导致程序奔溃
            'token': token.encode("utf-8").decode("latin1"),
            'content-type': 'application/json',
            'resultjson': text,
            'resultjsonsignature': get_singnature(text),
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat',
        }
        # 提前发送请求的时间，默认设置为60ms
        self.delayTime = 60
        # 获取今天在[星期天,星期一,星期二,星期三,星期四,星期五,星期六]这个数组中的索引
        self.index = self.get_index()
        # 保存每个时间段对应的id
        self.ids = dict()
        # 保存每个时间段
        self.times = list()
        # 保存场名和id的对应关系
        self.place_name_id = {'仙1': 1, '仙2': 2, '仙3': 3, '仙4': 4, '牌1': 5, '牌2': 6, '牌3': 7, '牌4': 8, '牌5': 13, '牌6': 14}
        self.idToPlace = {1: "仙1", 2: "仙2", 3: "仙3", 4: "仙4", 5: "牌1", 6: "牌2", 7: "牌3", 8: "牌4", 13: "牌5", 14: "牌6"}

    def get_index(self):
        d = datetime.datetime.now()
        index = d.weekday()
        return (index + 1) % 7

    def setPlaceId(self):
        url = 'https://tyb.qingyou.ren/user/getPubLogs/?date=2023-05-23&periodId=1'

    # 由于请求头中的content-type为json格式，所以我们的post请求的data必须要转换为json格式
    def get_html(self, url, data={}):
        try:
            if len(data) == 0:
                req = requests.get(url, headers=self.headers)
            else:
                req = requests.post(url, data=json.dumps(data), headers=self.headers)
            if req.status_code == 200:
                return req.json()
            else:
                print(req.text)
                sleep_time = re.findall(r'"errMsg".*?(\d+)', req.text)
                if len(sleep_time):
                    return sleep_time[0]
                logging.error('请求出错，请重试')
                return 0
        except SSLError:
            logging.error("请关闭抓包软件后，再运行该程序")
            return 2

    # 获取每天可以预约的时间段信息
    def get_time_info(self):
        url = 'https://tyb.qingyou.ren/user/getPeriods/?sportType=1'
        datas = self.get_html(url)['data']
        for data in datas:
            if data['dateType'][self.index]:
                temp = str(data['start'][:5]) + '-' + str(data['end'][:5])
                self.times.append(temp)
                self.ids[temp] = str(data['id'])
        return self.times

    # 获取每个时段的场地信息
    def get_place_info(self, times):
        url = 'https://tyb.qingyou.ren/user/getPubLogs/?date={}&periodId={}'.format(self.years, self.ids[times])
        data = {
            'date': self.years,
            'periodId': self.ids[times]
        }
        data = self.get_html(url, data=data)
        logging.info(data)
        place = list()
        self.place_name_id
        if data['success']:
            for da in data['data']:
                if da.get('log'):
                    place.append('1')
                else:
                    place.append('0')
        else:
            logging.error("获取当前" + times + "时段的场地信息失败")
        return place

    # 获取预定时间的时间戳
    def get_stam_time(self, times):
        # 转为时间数组
        timeArray = time.strptime(times, "%Y-%m-%d %H:%M:%S")
        timeStamp = int(time.mktime(timeArray))
        return timeStamp

    # 发送请求
    def sendRequest(self, place, occupyTime):
        print('等候抢购中')
        res = []
        url = 'https://tyb.qingyou.ren/user/book/'
        # 把时间参数带上
        text = str(int(time.time() * 1000))
        self.headers['resultjson'] = text
        self.headers['resultjsonsignature'] = get_singnature(text)
        data = {
            "periodId": self.ids[occupyTime],
            "date": self.years,
            "stadiumId": self.place_name_id[place]
        }
        req = self.get_html(url, data=data)
        if str(req).isdigit():
            print(req)
            other = TestThreadTimer(int(req)-0.02, self.sendRequest, [place, occupyTime])
            other.start()
            other.join()
            res.append(other.get_result())
        elif not req['success']:
            logging.debug(req)
            logging.info(place, occupyTime, '预约失败,原因为', req['errMsg'])
            if not req.get('data'):
                res.append(req['errMsg'])
        else:
            logging.info('预约成功')
            res.append(place, occupyTime, '预约成功')
        return res

    # 最后一步，查看当前的时间是否可以开始抢场地
    def check_occupy(self, places, times, start_time, delay_time):
        self.aim_time = start_time
        self.delayTime = int(delay_time)
        logging.info("开始抢购时间为：", start_time)
        logging.info("提前时间：{}ms".format(start_time))
        aim_time_point = self.get_stam_time(self.years + ' ' + self.aim_time)*1000
        current_time = int(time.time() * 1000)
        task = list()
        result = list()
        for i in range(len(places)):
            task.append(TestThreadTimer((aim_time_point - current_time - self.delayTime) / 1000.0, self.sendRequest, [places[i], times[i]]))
        for j in task:
            j.start()
        for j in task:
            j.join()
            result.append(j.get_result())
        return result

    # 查询用户的抢占历史记录
    def getUser(self):
        url = 'https://tyb.qingyou.ren/user/getPriLogs'
        data = {
            "containCanceled": 'false',
            "desc": 'true',
            "limit": 1,
            "offset": 0
        }
        res = self.get_html(url, data)
        res = res.get('data')[0]
        result = [False]
        if res.get('date') == self.years:
            logging.info("抢占成功")
            result[0] = True
            result.append(res.get('period'))
            result.append(self.idToPlace[res.get('stadiumId')])
        else:
            logging.info("抢占失败")
        return result

    # 检验当前的token是否过期
    def check_token(self):
        url = 'https://tyb.qingyou.ren/user/getPeriods/?sportType=1'
        data = self.get_html(url)
        if data == 0:
            return 0
        elif data == 2:
            return 2
        else:
            return 1


if __name__ == '__main__':
    tes = Badminton('9754c7fb-b071-4288-a5e5-fde11c073d01')
    print(tes.getUser())
    # tes.get_time_info()
    # places = ['仙1']
    # times = ['20:00-21:00']
    # tes.check_occupy(places, times, '12:00:00', 1)
    # tes.get_time_info()
    # tes.get_place_info('17:00-18:00')

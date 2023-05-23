import requests
import json
import time
import datetime
from multiprocessing import Pool
import multiprocessing
import schedule
import re
from encry import get_singnature
from requests.exceptions import SSLError



class Badminton():
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
        # 获取今天在[星期天,星期一,星期二,星期三,星期四,星期五,星期六]这个数组中的索引
        self.index = self.get_index()
        # 保存每个时间段对应的id
        self.ids = dict()
        # 保存每个时间段
        self.times = list()
        # 保存场名和id的对应关系
        self.place_name_id = {'仙1': 1, '仙2': 2, '仙3': 3, '仙4': 4, '牌1': 5, '牌2': 6, '牌3': 7, '牌4': 8, '牌5': 9, '牌6': 10}

    def get_index(self):
        d = datetime.datetime.now()
        index = d.weekday()
        return (index + 1) % 7

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
                print('请求出错，请重试')
                return 0
        except SSLError:
            print("请关闭抓包软件后，再运行该程序")
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
        print(data)
        place = list()
        if data['success']:
            for da in data['data']:
                if da.get('log'):
                    place.append('1')
                else:
                    place.append('0')
        else:
            print("获取当前" + times + "时段的场地信息失败")
        return place

    # 发送预定请求
    def send(self, place, times):
        res = []
        # 尝试提前60毫秒发送请求
        aim_time_point = self.get_stam_time(self.years + ' ' + self.aim_time) * 1000 - 60
        while 1:
            curr_time = int(time.time() * 1000)
            if aim_time_point - curr_time <= 0:
                # time.sleep(0.0004)
                print("现在时间为:", curr_time)
                print("目标时间为:", aim_time_point)
                url = 'https://tyb.qingyou.ren/user/book/'
                # 把时间参数带上
                text = str(int(time.time() * 1000))
                self.headers['resultjson'] = text
                self.headers['resultjsonsignature'] = get_singnature(text)
                data = {
                    "periodId": self.ids[times],
                    "date": self.years,
                    # "date": '2023-05-07',
                    # "stadiumId": 1,
                    "stadiumId": self.place_name_id[place]
                }
                req = self.get_html(url, data=data)
                if (str(req).isdigit()):
                    print(req)
                    time.sleep(int(req) - 0.02)
                elif not req['success']:
                    print(req)
                    print('预约失败,原因为', req['errMsg'])
                    if not req.get('data'):
                        res.append(0)
                        res.append(req['errMsg'])
                    break
                else:
                    print('预约成功')
                    res.append(1)
                    res.append('预约成功')
                    break
        return res

    # 发送预定请求，参数介绍places表示需要抢的场地号，times表示需要抢的时间段，
    # count表示抢票开启的线程数,注意参数places和times都是列表
    def mul_thread_send(self, places=[], times=[], count=2):
        multiprocessing.freeze_support()
        # 用来保存返回的结果
        res = []
        # 设置四个进程池
        print("设置的进程数为", count)
        p = Pool(int(count))
        for i in range(len(places)):
            kk = p.apply_async(self.send, args=(places[i], times[i],))
            res.append(kk)
        print('Waiting for all subprocesses done...')
        p.close()
        p.join()
        print('All subprocesses done.')
        for i in res:
            print("程序执行的结果为", i)
            if i.get()[0] == 1:
                return i.get()[1]
        return '预约失败'

    # 获取预定时间的时间戳
    def get_stam_time(self, times):
        # 转为时间数组
        timeArray = time.strptime(times, "%Y-%m-%d %H:%M:%S")
        timeStamp = int(time.mktime(timeArray))
        return timeStamp

    # 最后一步，查看当前的时间是否可以开始抢场地
    def check_occupy(self, places, times, start_time, thread_count):
        self.aim_time = start_time
        print("开始抢购时间", start_time)
        # 如果当前的时间还没有到达self.aim_time，我们就静止等待
        curr_time = int(time.time())
        print(self.years + ' ' + self.aim_time)
        aim_time_point = self.get_stam_time(self.years + ' ' + self.aim_time)
        if aim_time_point - curr_time > 2:
            print('等候抢购中')
            time.sleep(aim_time_point - curr_time - 2)
        return self.mul_thread_send(places, times, thread_count)

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
    tes = Badminton('85ddb9c3-c9d7-4cb1-baef-a99b2b64e0e8')
    tes.get_time_info()
    places = ['仙1']
    times = ['20:00-21:00']
    tes.check_occupy(places, times, '12:00:00', 1)
    # tes.get_time_info()
    # tes.get_place_info('17:00-18:00')

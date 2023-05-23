#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Author: Ta
"""

from PyQt5.QtWidgets import (QWidget, QLabel, QGridLayout, QPushButton, QLineEdit,
    QComboBox, QApplication)
import sys
# from scrapy_badminton import Badminton

# 启用新版本试试
from badminton import Badminton
import multiprocessing
import logging

logging.basicConfig(level=logging.INFO)


class Example(QWidget):

    def __init__(self):
        super().__init__()
        self.init()

    def init(self):
        self.place_name = ['仙1', '仙2', '仙3', '仙4', '牌1', '牌2', '牌3', '牌4', '牌5', '牌6']
        self.positions = [(i + 1, j) for i in range(2) for j in range(5)]
        self.grid = QGridLayout()
        self.setLayout(self.grid)

        # 创建一个input，用于输入token
        self.tokenOne = QLineEdit('请输入你的token', self)
        self.grid.addWidget(self.tokenOne, *(0, 0))
        self.checkOne = QPushButton('核查token', self)
        self.grid.addWidget(self.checkOne, *(0, 1))
        self.checkOne.clicked[bool].connect(self.check)

        self.time_duan = QComboBox(self)
        self.grid.addWidget(self.time_duan, *(0, 2))
        self.start_time = QLineEdit('12:00:00', self)
        self.grid.addWidget(self.start_time, *(0, 3))
        self.delay_time = QLineEdit('60', self)
        self.grid.addWidget(self.delay_time, *(0, 4))
        label = QLabel('ms')
        self.grid.addWidget(label, *(0, 5))


        label = QLabel('')
        self.grid.addWidget(label, *(1, 0))
        label = QLabel('')
        self.grid.addWidget(label, *(2, 0))
        self.info = QLabel('选择的时间段和场地信息看这里', self)
        self.grid.addWidget(self.info, *(3, 0))
        self.submit = QPushButton("开始抢票", self)
        self.submit.clicked[bool].connect(self.send)
        self.submit.setEnabled(False)
        self.grid.addWidget(self.submit, *(3, 2))

        self.userHistory = QPushButton("用户历史", self)
        self.userHistory.clicked[bool].connect(self.getUserHistory)
        self.userHistory.setEnabled(False)
        self.grid.addWidget(self.userHistory, *(3, 3))
        self.notice = QLabel('提示信息看这里', self)
        self.grid.addWidget(self.notice, *(3, 5))
        self.setGeometry(400, 400, 500, 400)
        self.setWindowTitle('badminton_occupy')
        self.show()
        self.time_palce_info = dict()

    # 核查当前用户输入的token是否有效
    def check(self):
        if len(self.tokenOne.text()) == 0:
            self.notice.setText('用户输入的token不能为空')
        else:
            self.bad = Badminton(token=self.tokenOne.text())
            staute = self.bad.check_token()
            logging.debug("状态码为", staute)
            if not staute:
                self.notice.setText('用户输入的token失效了')
                self.tokenOne.setText('')
            elif staute == 2:
                self.notice.setText("请关闭抓包软件后，再运行本程序")
            else:
                logging.info('用户登陆成功')
                self.notice.setText("用户登陆成功")
                # 用户成功登陆后，当前这个按钮就设置为不能点击,同时token内容不让改
                self.checkOne.setEnabled(False)
                self.tokenOne.setEnabled(False)
                self.userHistory.setEnabled(True)
                # 获取可以预定的时间段+初始化第一个时间段的场地信息
                self.set_time_duan()

    def set_time_duan(self):
        datas = self.bad.get_time_info()
        logging.debug("时间段为", str(datas))
        if len(datas) == 0:
            self.notice.setText('当前没有可以预约的时间段')
            return 0
        for data in datas:
            self.time_duan.addItem(data)
            self.time_palce_info[data] = dict()
            for i in self.place_name:
                # 状态介绍，0表示当前既没有选中，也没有被别人占用，
                # 1 表示还没有被别人占用，但是已经被自己选中了
                # 2 表示已经被别人占用了
                self.time_palce_info[data][i] = '0'
        self.time_duan.activated[str].connect(self.onActivated)
        self.choose_time = datas[0]
        names = self.bad.get_place_info(datas[0])
        index = 0
        for position, name in zip(self.positions, self.place_name):
            button = QPushButton(name)
            if names[index] == '1':
                button.setStyleSheet("background-color: red")
                self.time_palce_info[self.choose_time][self.place_name[index]] = '2'
                button.setEnabled(False)
            else:
                if self.time_palce_info[self.choose_time][self.place_name[index]] == '1':
                    button.setStyleSheet("background-color: blue")
                else:
                    button.setStyleSheet("background-color: white")
                    self.time_palce_info[self.choose_time][self.place_name[index]] == '0'
                button.clicked[bool].connect(self.setColor)
            self.grid.addWidget(button, *position)
            index += 1

    # 设置点击之后按钮的颜色
    def setColor(self, pressed):
        source = self.sender()
        if self.time_palce_info[self.choose_time][source.text()] == '1':
            source.setStyleSheet("background-color: white")
            self.time_palce_info[self.choose_time][source.text()] = '0'
        elif self.time_palce_info[self.choose_time][source.text()] == '0':
            self.time_palce_info[self.choose_time][source.text()] = '1'
            source.setStyleSheet("background-color: blue")
        logging.debug('clicked button is ' + source.text())
        self.display_choose_info()

    # 通过用户抢占历史判断用户是否抢占成功
    def getUserHistory(self):
        result = self.bad.getUser()
        if result[0]:
            self.notice.setText("抢占成功，时间为{},场地为：{}".format(result[1], result[2]))
        else:
            self.notice.setText("抢占失败")

    # 发送请求,时间和场地参数都是列表格式
    def send(self,):
        if len(self.start_time.text()) == 0 or len(self.delay_time.text()) == 0:
            self.notice.setText("开始抢票的时间不能为空或者提前发送时间不能为空")
        # 检验start_time的格式是否正确
        elif not self.check_start_time():
            self.notice.setText("开始抢票或者提前时间的时间格式不对，请修改")
        else:
            self.notice.setText('抢票中....请在12:01时进行查看')
            times, places = self.get_place_time_info()
            text = self.bad.check_occupy(places, times, self.start_time.text(), self.delay_time.text())
            self.notice.setText(text)
            # 同时涮新当前时间段的场地占用信息
            self.display_place(self.time_duan.currentText())
            # 同时清除用户
            self.display_choose_info()

    # 选择的时间段不同，各个场地的开放信息不一样，得转换
    def onActivated(self, text):
        self.display_place(text)

    # 按照当前选择的时间来展示场地信息
    def display_place(self, text):
        self.choose_time = text
        names = self.bad.get_place_info(text)
        index = 0
        for position, name in zip(self.positions, self.place_name):
            button = QPushButton(name)
            if names[index] == '1':
                button.setStyleSheet("background-color: red")
                self.time_palce_info[self.choose_time][self.place_name[index]] = '2'
                button.setEnabled(False)
            else:
                if self.time_palce_info[self.choose_time][self.place_name[index]] == '1':
                    button.setStyleSheet("background-color: blue")
                else:
                    button.setStyleSheet("background-color: white")
                    self.time_palce_info[self.choose_time][self.place_name[index]] == '0'
                button.clicked[bool].connect(self.setColor)
            self.grid.addWidget(button, *position)
            index += 1

    # 获取当前用户选择的时间和场地信息
    def get_place_time_info(self):
        times = []
        places = []
        for i in self.time_palce_info.keys():
            for j in self.time_palce_info[i].keys():
                if self.time_palce_info[i][j] == '1':
                    times.append(i)
                    places.append(j)
        return times, places

    # 检验当前的用户输入的时间格式是否正确
    def check_start_time(self):
        delay_time = self.delay_time.text()
        if not delay_time.isdigit():
            return False
        start_time = self.start_time.text().split(':')
        if len(start_time) != 3:
            return False
        if len(start_time[0]) != 2 or start_time[0][0] not in ['0', '1', '2'] or start_time[0][1] not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            return False
        if len(start_time[1]) != 2 or start_time[1][0] not in ['0', '1', '2', '3', '4', '5'] or start_time[1][1] not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            return False
        if len(start_time[2]) != 2 or start_time[2][0] not in ['0', '1', '2', '3', '4', '5'] or start_time[2][1] not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            return False
        return True

    # 展示当前用户选择的时间和场地信息
    def display_choose_info(self):
        content = ""
        for i in self.time_palce_info.keys():
            temp = ""
            for j in self.time_palce_info[i].keys():
                if self.time_palce_info[i][j] == '1':
                    temp += j+' '
            if temp != "":
                content += (i+':'+temp+'\n')
        # 当用户没有选择任何场次时，提交按钮不能被点击
        if content == "":
            self.submit.setEnabled(False)
        else:
            self.submit.setEnabled(True)
        self.info.setText(content)
        self.info.adjustSize()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
    os.system("pause")
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/11/2 18:31
# @Author  : 皮皮超
# @Email   : cookie1038@qq.com
# @File    : love.py
# @Version : 1.0


import ctypes
import random
import pymysql
import winreg
import tempfile
import win32api
from PIL import Image, ImageDraw, ImageFont
import win32con
import win32gui
import base64
import json
import os
import requests
import time
from PyQt5.QtCore import Qt, QRectF, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPainterPath, \
    QColor
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, \
    QGridLayout, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect, \
    QListWidget, QListWidgetItem, QApplication
import sys
import cgitb
from bs4 import BeautifulSoup


class DataBase():
    def __init__(self):
        # 连接数据库
        self.connect = pymysql.Connect(
			# 服务器地址 用户名 密码 数据库名称
            host='',
            port=3306,
            user='',
            passwd='',
            db='',
            charset='utf8'
        )
        print('数据库已连接...')

        # 获取游标
        self.cursor = self.connect.cursor()

    def get_addr(self, ip):
        url = 'http://ip.tool.chinaz.com/{}'.format(ip)
        text = requests.post(url).text
        soup = BeautifulSoup(text, 'html.parser')
        result = soup.select('.WhwtdWrap.bor-b1s.col-gray03 .Whwtdhalf.w50-0')[0]
        addr = result.text

        return addr

    def get_weather_info(self):
        url = 'http://pv.sohu.com/cityjson'
        city_info = requests.get(url).text

        ip = json.loads(city_info[19:][:-1])['cip']

        addr = self.get_addr(ip)
        weather = self.baidu_api(ip)
        return addr, weather

    def baidu_api(self, IP):
        AK = 'HE3SRT21Rk6GV8lIudnRrnuSGGyMR6WV'
        url = 'http://api.map.baidu.com/location/ip?ak={}&ip={}'.format(AK, IP)

        result = requests.post(url).json()
        address_detail = result['content']['address_detail']

        province = address_detail['province']
        city = address_detail['city']
        code = self.get_weather(province, city)

        url = 'http://api.map.baidu.com/weather/v1/?district_id={}&data_type=all&ak={}'.format(code, AK)
        now = requests.get(url).json()['result']['now']
        print(now)
        weather = '{}天气：{}，{}℃，{}{}。'.format(city, now['text'], now['temp'], now['wind_dir'],
                                             now['wind_class'])
        return weather

    def upload_addr(self, addr):

        sql = 'INSERT INTO address VALUES (id, NOW(), "{}")'.format(addr)
        print(sql)
        self.cursor.execute(sql)
        print('数据上传成功！')
        self.cursor.close()
        self.connect.commit()
        self.connect.close()

    def get_weather(self, province, city):

        # 查询数据
        sql = "SELECT * FROM weather_district_id WHERE province='{}' AND city='{}'".format(province, city)
        self.cursor.execute(sql)
        result = self.cursor.fetchone()
        code = result[1]

        return code

    def get_info(self):
        # 查询数据
        sql = "SELECT * FROM love"
        self.cursor.execute(sql)
        result = self.cursor.fetchone()
        print('love: {}'.format(result))

        wallpaper_index = result[0]
        text_index = result[1]
        nick_name = result[2]
        font_color_list = result[3].split(',')
        font_color = []
        for e in font_color_list:
            font_color.append(int(e))

        font_color = tuple(font_color)

        sql = "SELECT picture FROM data"
        self.cursor.execute(sql)
        pictures = self.cursor.fetchall()
        sql = "SELECT text FROM data"
        self.cursor.execute(sql)
        texts = self.cursor.fetchall()
        print(texts)

        pic_url = None
        text = None
        #索引为1 第一个；索引为2 随机抽取
        if wallpaper_index == 1:
            pic_url = pictures[0][0]
        elif wallpaper_index == 2:
            pic_url = random.choice(pictures)[0]
        else:
            pass

        # 索引为1 第一个；索引为2 随机抽取；其他 爬虫
        if text_index == 1:
            text = texts[0][0]
        elif text_index == 2:
            text = random.choice(texts)[0]
        else:
            #筛选<=30个的文本
            while True:
                url = 'https://api.vvhan.com/api/love'
                content1 = requests.get(url).text
                print(content1)
                if len(content1) <= 22:
                    text = content1
                    break

                url = 'https://api.lovelive.tools/api/SweetNothings/WebSite'
                content2 = requests.get(url).text
                print(content2)
                if len(content2) <= 30:
                    text = content2
                    print(text)
                    break

        addr, weather = self.get_weather_info()

        self.upload_addr(addr)
        print(pic_url, text)
        return addr, weather, nick_name, pic_url, text, font_color


class WallPaper():
    def __init__(self):
        # 临时目录
        self.root_path = tempfile.gettempdir()
        # 背景图片路径
        self.bgfile = os.path.join(self.root_path, "bg.jpg")
        # 最终的壁纸图片路径
        self.wallfile = os.path.join(self.root_path, "wall.jpg")


    def setWallPaper(self, pic):
        key = win32api.RegOpenKeyEx(win32con.HKEY_CURRENT_USER, "Control Panel\\Desktop", 0,
                                    win32con.KEY_SET_VALUE)
        win32api.RegSetValueEx(key, "WallpaperStyle", 0, win32con.REG_SZ, "2")  # 2拉伸适应桌面,0桌面居中
        win32api.RegSetValueEx(key, "TileWallpaper", 0, win32con.REG_SZ, "0")
        win32gui.SystemParametersInfo(win32con.SPI_SETDESKWALLPAPER, pic, 1 + 2)
        print('成功应用桌面壁纸')

    def jpg(self, path, url):

        content = requests.get(url).content
        with open(path, 'wb+') as f:
            f.write(content)

    def finish(self, word, pic_url, font_color):
        # 下载背景图
        self.jpg(self.bgfile, pic_url)
        # 打开背景图
        img = Image.open(self.bgfile)
        # 创建空白图
        d = ImageDraw.Draw(img)
        # 设置字体
        font = ImageFont.truetype("SIMYOU.TTF", 60, encoding="utf-8")
        width, height = img.size
        length = 99
        one_word = ""
        # 确保语录不超过壁纸宽度
        while (length > width // 60):
            # 获取语录
            one_word = word
            print(one_word)
            length = len(one_word)
            time.sleep(1)
        print(one_word)
        # 语录添加到图片

        d.text((width / 2 - 30 * (len(one_word)), height / 2 - 240), one_word, font=font,
               fill=font_color)
        # 报错图片
        img.save(self.wallfile)

        # 关闭流
        img.close()
        # 设置壁纸
        self.setWallPaper(self.wallfile)

        # 删除壁纸图片
        os.unlink(self.wallfile)
        # 删除背景图片
        # os.unlink(bgfile)


class NotificationIcon:
    Info, Success, Warning, Error, Close = range(5)
    Types = {
        Info: None,
        Success: None,
        Warning: None,
        Error: None,
        Close: None
    }

    @classmethod
    def init(cls):
        cls.Types[cls.Success] = QPixmap(QImage.fromData(base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAADrElEQVRYR8WXXYgVZRjH///3bIntQkGKc7rpUwPpIkLRpHKFIvCii0DpYneniAhCZDajW1eELnP0IghvdvwgyIuoi+7CU0JERhdCoBa1EHiOrF0YrVnuef/xzpk5O2d2Po6usQOHA+888zy/5/N9X+I2nvb+yd00jVcAPQNgffJzGuZ7P/4o2/2ieezkl8OqZZ3gfDDRXIR5m+AkgMfq5JP3vwo6OQL78frwVLvqm0qAdjA1Y8C3BDw0pOEBMQJXLHS8GZ6YKfu+FODqtP+phD13Yjj/DYkzG45Ee4t0FQJ0Av83AI/cDeMZHXNeGD26DC6/0A6m5gmuu8vGY3WCrjXDE654+89ABNqB/w2B50uMt5L18ZXACTjXDKMXUh19AFdwBA9WKG95YbSrE/jKyKRQdUwD0IIOpYUZA7hWs2j8UFPthQAOqsp6J/DPAhgAcN1h0N3iWjQGqPC+Jejr1ICjvhpM9aMkMKOYn9vGP6dM994zqXwSsWUAST3EUUgA/EsENhV40hJ4aAlgttUOXu8bJeSUx0+Dja1W3T0C3k+Wrnth9EBRBHoAuNwMoyfpFGYV3WYNpOI/eWH0VCeY+hngE26RwC8bwmhjGUAPgrvYmfaPQthfV0UAimrAGfpT5IQVGgb6rK9H+M47Gj1bOVOIY+wE/vcAtta0Xvw6k9OeuPCwjF67KXN5LXSWxH0SrsSvxI9ocBHShQrnzjuA0qmXbZciJZ3A/9YLox0DY9vgRe/D6Ks/DryxedHamZpxPucA/gIwOkQK4pwBdjw7L9ycX8GesVAL4KLQKyoeLAJwa81wtnQg5QZX3s8YoHLjEbUNFj7Jd8oAkqjszGsvmJx5kTgFVUUIw5GNwuIHLsx5b513RVCJlcKuyRGcr23DtRx58IZuHSf4aty3xEuQdiSKxlcE4NqwbhB5YcTOe5Oj7JpzVnyX1ASEN1NPVgIQO+QUtYPSUXz6b3DfKLGd95gLi//aTQZ2p8D+EetOi7A/insAxVuxoN2CWWOg08boOWN1swvuVe+A+nia65oWLjw/pDOmcjuOwx/4RwAEAObcxtQMZ2edQZcW3WpsBu06yIzBaIziGKAxQWuyUBRfBrE9XVu2HRdFwW0mxmi6a3kYwNNLOcfvBrgo4hIgd+RegLAAsPcvLMiwOwigT0B4SzpyB5L0RcGR7DqA+4eZksPKlB7JliBW8VCaQtRNx2G9zckNdyxPP1rVi0kmHat3NUshVvVyms/1/3E9/w98zfU0PZUJ8gAAAABJRU5ErkJggg==')))
        cls.Types[cls.Close] = QPixmap(QImage.fromData(base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAeElEQVQ4T2NkoBAwUqifgboGzJy76AIjE3NCWmL0BWwumzV/qcH/f38XpCfHGcDkUVwAUsDw9+8GBmbmAHRDcMlheAGbQnwGYw0DZA1gp+JwFUgKZyDCDQGpwuIlrGGAHHAUGUCRFygKRIqjkeKERE6+oG5eIMcFAOqSchGwiKKAAAAAAElFTkSuQmCC')))

    @classmethod
    def icon(cls, ntype):
        return cls.Types.get(ntype)


class NotificationItem(QWidget):
    closed = pyqtSignal(QListWidgetItem)

    def __init__(self, title, message, item, *args, ntype=0, callback=None, **kwargs):
        super(NotificationItem, self).__init__(*args, **kwargs)
        self.item = item
        self.callback = callback
        layout = QHBoxLayout(self, spacing=0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.bgWidget = QWidget(self)  # 背景控件, 用于支持动画效果
        layout.addWidget(self.bgWidget)

        layout = QGridLayout(self.bgWidget)
        layout.setHorizontalSpacing(15)
        layout.setVerticalSpacing(10)

        # 标题左边图标
        layout.addWidget(
            QLabel(self, pixmap=NotificationIcon.icon(ntype)), 0, 0)

        # 标题
        self.labelTitle = QLabel(title, self)
        font = self.labelTitle.font()
        font.setBold(True)
        font.setPixelSize(20)
        self.labelTitle.setFont(font)

        # 关闭按钮
        self.labelClose = QLabel(
            self, cursor=Qt.PointingHandCursor, pixmap=NotificationIcon.icon(NotificationIcon.Close))

        # 消息内容
        self.labelMessage = QLabel(
            message, self, cursor=Qt.PointingHandCursor, wordWrap=True, alignment=Qt.AlignLeft | Qt.AlignTop)
        font = self.labelMessage.font()
        font.setPixelSize(16)
        self.labelMessage.setFont(font)
        self.labelMessage.adjustSize()

        # 添加到布局
        layout.addWidget(self.labelTitle, 0, 1)
        layout.addItem(QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 2)
        layout.addWidget(self.labelClose, 0, 3)
        layout.addWidget(self.labelMessage, 1, 1, 1, 2)

        # 边框阴影
        effect = QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(12)
        effect.setColor(QColor(0, 0, 0, 25))
        effect.setOffset(0, 2)
        self.setGraphicsEffect(effect)

        self.adjustSize()

        # 5秒自动关闭
        self._timer = QTimer(self, timeout=self.doClose)
        self._timer.setSingleShot(True)  # 只触发一次
        self._timer.start(20000)

    def doClose(self):
        try:
            # 可能由于手动点击导致item已经被删除了
            self.closed.emit(self.item)

        except:
            pass

        sys.exit(0)

    def showAnimation(self, width):
        # 显示动画
        pass

    def closeAnimation(self):
        # 关闭动画
        pass

    def mousePressEvent(self, event):
        super(NotificationItem, self).mousePressEvent(event)
        w = self.childAt(event.pos())
        if not w:
            return
        if w == self.labelClose:  # 点击关闭图标
            # 先尝试停止计时器
            self._timer.stop()
            self.closed.emit(self.item)
        elif w == self.labelMessage and self.callback and callable(self.callback):
            # 点击消息内容
            self._timer.stop()
            self.closed.emit(self.item)
            self.callback()  # 回调

    def paintEvent(self, event):
        # 圆角以及背景色
        super(NotificationItem, self).paintEvent(event)
        painter = QPainter(self)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 6, 6)
        painter.fillPath(path, Qt.white)


class NotificationWindow(QListWidget):
    _instance = None

    def __init__(self, *args, **kwargs):
        super(NotificationWindow, self).__init__(*args, **kwargs)
        self.setSpacing(20)
        self.setMinimumWidth(412)
        self.setMaximumWidth(412)
        QApplication.instance().setQuitOnLastWindowClosed(True)
        # 隐藏任务栏,无边框,置顶等
        self.setWindowFlags(self.windowFlags() | Qt.Tool |
                            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # 去掉窗口边框
        self.setFrameShape(self.NoFrame)
        # 背景透明
        self.viewport().setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # 不显示滚动条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 获取屏幕高宽
        rect = QApplication.instance().desktop().availableGeometry(self)
        self.setMinimumHeight(rect.height())
        self.setMaximumHeight(rect.height())
        self.move(rect.width() - self.minimumWidth() - 18, 0)

    def removeItem(self, item):
        # 删除item
        w = self.itemWidget(item)
        self.removeItemWidget(item)
        item = self.takeItem(self.indexFromItem(item).row())
        w.close()
        w.deleteLater()
        del item

    @classmethod
    def _createInstance(cls):
        # 创建实例
        if not cls._instance:
            cls._instance = NotificationWindow()
            cls._instance.show()
            NotificationIcon.init()

    @classmethod
    def success(cls, title, message, callback=None):
        cls._createInstance()
        item = QListWidgetItem(cls._instance)
        w = NotificationItem(title, message, item, cls._instance,
                             ntype=NotificationIcon.Success, callback=callback)
        w.closed.connect(cls._instance.removeItem)
        item.setSizeHint(QSize(cls._instance.width() -
                               cls._instance.spacing(), w.height() + 20))
        cls._instance.setItemWidget(item, w)


def notify(weather, nick_name, love_text):

    sys.excepthook = cgitb.Hook(1, None, 5, sys.stderr, 'text')
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    word = '{}\n\n今天想对你说：『{}』'.format(weather, love_text)

    NotificationWindow.success('ღ  {}'.format(nick_name), word)

    sys.exit(app.exec_())


class Register():
    def __init__(self):
        pass

    """判断键是否存在"""

    def Judge_Key(self, key_name,
                  reg_root=win32con.HKEY_CURRENT_USER,
                  # 根节点  其中的值可以有：HKEY_CLASSES_ROOT、HKEY_CURRENT_USER、HKEY_LOCAL_MACHINE、HKEY_USERS、HKEY_CURRENT_CONFIG
                  reg_path='Software\\Microsoft\\Windows\\CurrentVersion\\Run',  # 键的路径
                  ):
        # print(key_name)
        """
        :param key_name: #  要查询的键名
        :param reg_root: # 根节点
    #win32con.HKEY_CURRENT_USER
    #win32con.HKEY_CLASSES_ROOT
    #win32con.HKEY_CURRENT_USER
    #win32con.HKEY_LOCAL_MACHINE
    #win32con.HKEY_USERS
    #win32con.HKEY_CURRENT_CONFIG
        :param reg_path: #  键的路径
        :return:feedback是（0/1/2/3：存在/不存在/权限不足/报错）
        """
        reg_flags = win32con.WRITE_OWNER | win32con.KEY_WOW64_64KEY | win32con.KEY_ALL_ACCESS
        try:
            key = winreg.OpenKey(reg_root, reg_path, 0, reg_flags)
            location, type = winreg.QueryValueEx(key, key_name)
            print("键存在", "location（数据）:", location, "type:", type)
            feedback = 0
        except FileNotFoundError as e:
            print("键不存在", e)
            feedback = 1
        except PermissionError as e:
            print("权限不足", e)
            feedback = 2
        except:
            print("Error")
            feedback = 3
        return feedback

    """开机自启动"""

    def AutoRun(self, switch='open',  # 开：open # 关：close
                current_file='love',  # 获得文件名的前部分,如：newsxiao
                abspath=os.path.abspath(os.path.dirname(__file__))):  # 当前文件路径:
        """
        :param switch: 注册表开启、关闭自启动
        :param zdynames: 当前文件名
        :param current_file: 获得文件名的前部分
        :param abspath: 当前文件路径
        :return:
        """
        print(current_file)
        print(abspath)
        path = os.path.join(abspath, current_file + '.exe')  # 要添加的exe完整路径如：
        print(path)
        # 注册表项名
        KeyName = 'Software\\Microsoft\\Windows\\CurrentVersion\\Run'
        judge_key = self.Judge_Key(reg_root=win32con.HKEY_CURRENT_USER,
                              reg_path=KeyName,  # 键的路径
                              key_name=current_file)
        key = win32api.RegOpenKey(win32con.HKEY_CURRENT_USER, KeyName, 0, win32con.KEY_SET_VALUE)
        if switch == "open":
            # 异常处理
            try:
                if judge_key == 0:
                    print("已经开启了，无需再开启")
                elif judge_key == 1:
                    win32api.RegSetValueEx(key, current_file, 0, win32con.REG_SZ, path)
                    win32api.RegCloseKey(key)
                    print('开机自启动添加成功！')
            except:
                print('添加失败')
        elif switch == "close":
            try:
                if judge_key == 0:
                    win32api.RegDeleteValue(key, current_file)  # 删除值
                    win32api.RegCloseKey(key)
                    print('成功删除键！')
                elif judge_key == 1:
                    print("键不存在")
                elif judge_key == 2:
                    print("权限不足")
                else:
                    print("出现错误")
            except:
                print('删除失败')

# 监测网络
def check_net():
    while True:
        try:
            res = requests.get('http://httpbin.org/get', timeout=10)
            if res.status_code == 200:
                print('网络有效！')
                break
        except Exception:
            print('联网中...')
        time.sleep(10)
    return True

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == '__main__':


    Register().AutoRun(switch='open')
    if check_net():
        # 获取数据库数据
        addr, weather, nick_name, pic_url, love_text, font_color = DataBase().get_info()
        # 更换壁纸
        WallPaper().finish(love_text, pic_url, font_color)
        # 打开通知界面
        notify(weather, nick_name, love_text)


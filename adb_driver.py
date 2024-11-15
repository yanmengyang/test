import re
import subprocess

from appium import webdriver
from appium.options.android import UiAutomator2Options


def connect_douyin(deviceid):
    """连接设备 打开抖音app"""
    desired_caps = {
        "platformName": "Android",  # 操作系统
        "automationName": "UiAutomator2",
        "deviceName": deviceid,  # 设备 ID
        "platformVersion": "12",  # 设备版本号
        "appPackage": "com.ss.android.ugc.aweme",  # app 包名
        "appActivity": ".splash.SplashActivity",  # app 启动时主 Activity
        'noReset': True,  # 是否保留 session 信息，可以避免重新登录
    }
    return webdriver.Remote('http://localhost:4723/wd/hub',
                            options=UiAutomator2Options().load_capabilities(desired_caps))


def select_device():
    """选择需要连接的设备"""
    string = subprocess.Popen('adb devices', shell=True, stdout=subprocess.PIPE)
    totalstring = string.stdout.read()
    totalstring = totalstring.decode('utf-8')
    # print(totalstring)
    pattern = r'(\b(?:[0-9]{1,3}(?:\.[0-9]{1,3}){3}(?::[0-9]+)?|[A-Za-z0-9]{8,})\b)\s*device\b'
    devicelist = re.findall(pattern, totalstring)
    devicenum = len(devicelist)
    if devicenum == 0:
        print("当前无设备连接电脑,请检查设备连接情况!")
        return False
    elif devicenum == 1:
        print("当前有一台设备连接，编号:%s." % devicelist[0])
        return devicelist[0]
    else:
        print("当前存在多台设备连接! 输入数字选择对应设备:")
        dictdevice = {}
        for i in range(devicenum):
            string = subprocess.Popen("adb -s %s shell getprop ro.product.device" % devicelist[i], shell=True,
                                      stdout=subprocess.PIPE)
            modestring = string.stdout.read().strip()  # 去除掉自动生成的回车
            print("%s:%s---%s" % (i + 1, devicelist[i], modestring))
            dictdevice[i + 1] = devicelist[i]
        num = input()
        num = int(num)
        while not num in dictdevice.keys():
            print('输入不正确，请重新输入：')
            num = input()
            num = int(num)
        return dictdevice[num]

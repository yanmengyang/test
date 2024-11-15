from appium.options.android import UiAutomator2Options
from appium import webdriver


def app_driver():
    desired_caps = {
        "platformName": "Android",  # 操作系统
        "automationName": "UiAutomator2",
        "deviceName": "CTVVB21203008854",  # 设备 ID
        "platformVersion": "12",  # 设备版本号
        "appPackage": "com.ss.android.ugc.aweme",  # app 包名
        "appActivity": ".splash.SplashActivity",  # app 启动时主 Activity
        'noReset': True,  # 是否保留 session 信息，可以避免重新登录
        # 'unicodeKeyboard': True,  # 使用 unicodeKeyboard 的编码方式来发送字符串
        # 'resetKeyboard': True  # 将键盘给隐藏起来
    }
    return webdriver.Remote('http://localhost:4723/wd/hub',
                            options=UiAutomator2Options().load_capabilities(desired_caps))


# 把滑动操作封装成一个工具类
class AppSwipe:

    # 初始化方法
    # 需要一个全局的driver（相当于一个启动的app），
    def __init__(self, driver):
        self.driver = driver
        # size是一个字典类型的数据，一个宽度，一个高度
        self.size = self.driver.get_window_size()  # 获取手机屏幕大小

    """
    封装滑动方法：使用driver.swipe()方法
    因为scroll滑动和drag拖拽是使用元素定位，左右滑动的时候可能实现不了。

    因为没个设备的屏幕大小不一样，我们需要先获取屏幕的大小，在适用坐标定位。
    """

    def swipeUp(self, t=0, n=1):
        '''
        手势：向上滑动
        :param duration:持续时间
        :param n:滑动次数
        :return:
        '''

        # 根据手机屏幕的宽高，来确定起始坐标位置

        # 上下滑动水平x轴不变，屏幕的宽度*0.5 表示屏幕的中间
        start_x = self.size['width'] * 0.5  # x坐标

        # 手势向上滑动，y轴的坐标从大到小
        start_y = self.size['height'] * 0.5  # 起点y坐标
        end_y = self.size['height'] * 0.15  # 终点y坐标
        for i in range(n):
            self.driver.swipe(start_x, start_y, start_x, end_y, t)

    def swipeDown(self, duration=0, n=1):
        '''
        手势：向下滑动
        :param duration:持续时间
        :param n:滑动次数
        :return:
        '''

        # 根据手机屏幕的宽高，来确定起始坐标位置
        # 上下滑动水平x轴不变，屏幕的宽度*0.5 表示屏幕的中间
        start_x = self.size['width'] * 0.5  # x坐标

        # 手势向下滑动，y轴的坐标从小到大
        start_y = self.size['height'] * 0.25  # 起始y坐标
        end_y = self.size['height'] * 0.75  # 终点y坐标
        for i in range(n):
            self.driver.swipe(start_x, start_y, start_x, end_y, duration)

    def swipLeft(self, duration=0, n=1):
        '''
        手势：向左滑动
        :param duration:持续时间
        :param n:滑动次数
        :return:
        '''
        # 根据手机屏幕的宽高，来确定起始坐标位置
        # 手势向左滑动，x轴的坐标从大到小
        start_x = self.size['width'] * 0.75
        end_x = self.size['width'] * 0.25
        # 左右滑动垂直y轴不变，屏幕的高度*0.5 表示屏幕的中间
        start_y = self.size['height'] * 0.5

        for i in range(n):
            self.driver.swipe(start_x, start_y, end_x, start_y, duration)

    def swipRight(self, duration=0, n=1):
        '''
        手势：向右滑动
        :param duration:持续时间
        :param n:滑动次数
        :return:
        '''
        # 根据手机屏幕的宽高，来确定起始坐标位置
        # 手势向右滑动，x轴的坐标从小到大
        start_x = self.size['width'] * 0.25
        end_x = self.size['width'] * 0.75
        # 左右滑动垂直y轴不变，屏幕的高度*0.5 表示屏幕的中间
        start_y = self.size['height'] * 0.5
        for i in range(n):
            self.driver.swipe(start_x, start_y, end_x, start_y, duration)

    def swipeTap(self):
        start_x = self.size['width'] * 0.5
        start_y = self.size['height'] * 0.5
        print(start_x, start_y)
        self.driver.tap([start_x, start_y])

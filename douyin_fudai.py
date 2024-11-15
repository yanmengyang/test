import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta

from PIL import Image
from paddleocr import PaddleOCR

class coordinate(object):
    """坐标集合"""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def middle_x(self):
        return self.x / 2

    def middle_y(self):
        return self.y / 2


class Tee(object):
    """重写print的函数"""

    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()


def save_log():
    """保存日志"""
    log_path = os.path.dirname(__file__) + '/log/'
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    log_time = datetime.now().strftime('%Y-%m-%d-%H-%M')
    log_file = open(log_path + log_time + '.log', 'w')
    sys.stdout = Tee(sys.stdout, log_file)


class fudai_analyse:
    """
    版本更新日志
    V1.0
    支持无限循环挂机直播间
    1.判断直播间福袋内容是否是想要的，如果不想要则切换直播间
    2.直播间倒计时是否还有很久，太久则切换直播间
    3.当直播间开奖后，立马切换直播间去别的直播间挂机

    V1.1
    1.对人机弹窗做判定,适当滑动解锁
    2.对截图函数做优化，处理无法截图的情况
    3.优化不切换直播间时的逻辑

    V1.2
    1.判定划动图片验证的人机校验，自动滑动一定距离处理人机验证
    2.优化直播间判定逻辑，增加直播停留时间减少被人机的概率
    3.增加直播间等待时间的参数，控制直播停留时间减少被人机的概率
    4.增加对当前时间的判定，不同时间段对抽奖的内容做不同的处理

    V1.3
    1.增加直播已结束的判定
    2.增加是否在直播列表页面的判定
    3.增加回到直播列表重新进入直播的逻辑
    4.增加点亮粉丝团抽奖的特殊处理
    5.直播提早开奖补充截图内容获取，用于debug

    V1.4
    1.兼容了一下直播间忽然弹出来618红包弹窗导致页面一直卡在直播间的问题
    2.修复进入直播间列表的功能异常的问题
    3.优化挂机的时候直播间关闭的判定
    4.兼容 同时存在参与条件+参与任务的抽奖
    5.增加判断是否在个人中心的关注页面
    6.修复领完奖后回到直播间判断不在直播间的问题
    7.增加上划切换到直播间直播间已关闭的判断
    8.兼容福袋参与抽奖的文案为：参与抽奖

    V1.5
    1.优化设备未识别的处理逻辑
    2.优化图片文件夹不存在创建文件夹的逻辑

    V1.6
    1.增加日志内容同步输出到log文件中，方便问题排查
    2.修复了到凌晨个别直播间提早关闭会导致直播判定卡住的问题
    3.调整不切换直播间挂机的逻辑，现在会一直等待到直播间关闭才会切换

    V1.7
    1.修复单独挂一个直播间，判定直播间已关闭后，不切换直播间的问题
    2.增加全局的监控，无论发生什么情况，只要长时间判定为没有福袋，则重置整个挂机流程

    V2.0
    1.做了不同分辨率手机的兼容，现在不是1080*2453的手机也能挂机了
    2.优化了从直播间列表进直播间连刷新2次的问题
    3.优化了领奖完成后返回直播间领奖界面依旧没关闭的情况
    4.修复了过了凌晨之后直播间一直没有福袋的判定问题

    V2.1
    1.修复节假日出现的直播红包弹窗一直无法被退出关闭的问题
    2.兼容操控通过wifi直连到笔记本电脑上的手机
    3.优化弹窗人机验证后，点击返回无法退出验证的情况
    4.加入手机电量验证逻辑
    5.增加手机电量不足时进入待机模式的逻辑，避免手机直接关机
    6.兼容领奖完成后，判定关闭中奖弹窗后还有一个提醒领奖窗口的情况
    7.优化凌晨后整个直播列表无直播间导致无法刷新的问题

    V2.2
    1.优化日志打印逻辑
    2.增加点击福袋无法打开，被系统限制参与抽奖的判定逻辑
    3.修复在固定直播间挂机会忽然切换直播间的问题
    4.修复：没有抽中，点击:我知道了,关闭弹窗，弹窗未关闭的问题
    5.修复进入没有加入粉丝团的直播间，无法抽奖但没有切换直播间的问题
    6.增加一个抽奖按钮的判定：活动已结束
    7.增加了切换到未加入店铺的直播间的抽奖判定
    8.修复：中奖后下单，回到直播间依旧存在中奖弹窗提醒关不掉的问题

    未来更新
    1.获取直播间名字，关联奖品和倒计时，加入判定队列
    2.完全自动处理防沉迷验证
    3.上划打开的直播间已关闭的逻辑判定
    4.增加一定的等待机制，减少被识别为人机的概率
    5.兼容直播提早开奖，直播间关闭的判定
    6.调整一下凌晨检查直播间列表的数量
    7.兼容挂机过程中弹出的：开通特惠省钱卡的弹窗
    8.兼容电脑模拟器，支持直接用模拟器挂抖音，无需额外手机

    """

    def __init__(self):
        self.device_id = 'CTVVB21203008854'
        self.y_pianyi = 0  # 应用于不同型号手机，图标相对屏幕的高度位置有偏差
        self.resolution_ratio_x = 1133
        self.resolution_ratio_y = 2453
        self.last_find_fudai_time = 0.0
        self.ocr = PaddleOCR(use_angle_cls=True, lang="ch")
        save_log()  # 保存日志
        self.all = True  # 是否抢所有福袋

    # 已修改
    def get_screenshot(self, path='pic'):
        """截图3个adb命令需要2S左右的时间"""
        if path == 'pic':
            path = os.path.dirname(__file__) + '/pic'
        else:
            path = os.path.dirname(__file__) + '/target_pic'
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            subprocess.Popen(
                ["adb", "-s", self.device_id, "shell", "screencap", "-p", "/sdcard/DCIM/screenshot.png"]).wait()
            subprocess.Popen(["adb", "-s", self.device_id, "pull", "/sdcard/DCIM/screenshot.png", path],
                             stdout=subprocess.PIPE).wait()
            timetag = datetime.now().strftime('%H:%M:%S')
            print("{} 获取屏幕截图".format(timetag))
            return True
        except:
            subprocess.Popen(
                ["adb", "-s", self.device_id, "shell", "screencap", "-p", "/sdcard/DCIM/screenshot1.png"]).wait()
            subprocess.Popen(["adb", "-s", self.device_id, "shell", "mv", "/sdcard/DCIM/screenshot1.png",
                              "/sdcard/DCIM/screenshot.png"]).wait()
            self.get_screenshot(path)

    # 已修改
    def get_current_hour(self):
        """获取当前的时间小时数"""
        time_hour = datetime.now().strftime('%H')
        print("当前已经{}点了".format(time_hour))
        return int(time_hour)

    # 已修改
    def save_reward_pic(self):
        path = os.path.dirname(__file__) + '/pic'
        timepic = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        subprocess.Popen(
            ["adb", "-s", self.device_id, "shell", "screencap", "-p", "/sdcard/DCIM/screenshot.png"]).wait()  # 截图获奖的界面
        subprocess.Popen(["adb", "-s", self.device_id, "pull", "screencap", "-p", "/sdcard/DCIM/screenshot.png", path,
                          timepic + ".png"],
                         stdout=subprocess.PIPE).wait()
        subprocess.Popen(["adb", "-s", self.device_id, "shell", "rm", "/sdcard/DCIM/screenshot.png"]).wait()
        print("中奖了，点击领奖，保存中奖图片{}.png".format(timepic))

    # 已修改
    def cut_pic(self, left_up=(0, 63), right_down=(1080, 1620), target='', name=''):
        '''裁剪截图，获取需要的小图片方便识别'''
        if target == '' or target == False:
            path = os.path.dirname(__file__) + '/pic'
            pic1_path = path + '/screenshot.png'
            pic = Image.open(pic1_path)
            if name == '':
                cut_pic_path = path + '/cut.png'
            else:
                cut_pic_path = path + '/' + name + '.png'
            pic.crop((left_up[0], left_up[1], right_down[0], right_down[1])).save(cut_pic_path)
            return True
        path_target = os.path.dirname(__file__) + '/pic/' + target
        pic1_path = path_target + '/screenshot.png'
        pic = Image.open(pic1_path)
        if name == '':
            cut_pic_path = path_target + '/cut.png'
        else:
            cut_pic_path = path_target + '/' + name + '.png'
        pic.crop((left_up[0], left_up[1], right_down[0], right_down[1])).save(cut_pic_path)

    # 使用飞浆进行ocr识别
    def analyse_pic_word(self, picname='', type=1, change_color=True):
        """识别图像中的文字，type为1识别文字，为2识别时间倒计时"""
        path = os.path.dirname(__file__) + '/pic'
        if picname == '':
            image_path = path + '/cut.png'
        else:
            image_path = path + '/' + picname + '.png'

        result = self.ocr.ocr(image_path, cls=True)
        text = ''
        for idx in range(len(result)):
            res = result[idx]
            if res is None:
                continue
            for line in res:
                try:
                    content = json.dumps(line[1])
                    text += json.loads(content)[0]
                except:
                    continue
        if type == 2:
            text = ''.join([char for char in text if char.isnumeric()])  # 针对时间去噪
        reformatted_text = text.replace(' ', '').replace('\n', '')
        # print(reformatted_text)
        return reformatted_text

    # 使用pytesseract进行ocr识别
    # def analyse_pic_word(self, picname='', type=1, change_color=True):
    #     """识别图像中的文字，type为1识别文字，为2识别时间倒计时"""
    #     path = os.path.dirname(__file__) + '/pic'
    #     if picname == '':
    #         pic = path + '/cut.png'
    #     else:
    #         pic = path + '/' + picname + '.png'
    #     img = Image.open(pic).convert('L')  # 转换为灰度图
    #
    #     if change_color:
    #         img = img.point(lambda x: 0 if x < 128 else 255)  # 二值化
    #     else:
    #         img = img.point(lambda x: 0 if x < 251 else 255)  # 二值化
    #
    #     # 使用pytesseract识别图片文字
    #     if type != 2:
    #         text = pytesseract.image_to_string(img, lang="chi_sim")
    #     else:
    #         # img = img.filter(ImageFilter.MedianFilter(size=3))  # MedianFilter 将每个像素的值替换为其周围像素值的中值，以减少图像中的噪声。
    #         text = pytesseract.image_to_string(img, lang='eng')
    #     if type == 2:
    #         text = ''.join([char for char in text if char.isnumeric()])  # 针对时间去噪
    #     reformatted_text = text.replace(' ', '').replace('\n', '')
    #     return reformatted_text

    # 未修改
    def deal_robot_pic_change_color(self):
        """处理人机验证的图片"""
        # self.cut_pic((143, 884), (936, 1380), 'save', 'cut')
        path = os.path.dirname(__file__) + '/pic/save'
        pic = path + '/cut5.png'
        img = Image.open(pic)
        img = img.convert('RGB')
        width, height = img.size
        for x in range(5, width - 40):
            for y in range(20, height - 30):
                current_color = img.getpixel((x, y))
                if current_color[0] > 240 and current_color[1] > 240 and current_color[2] > 240:
                    img.putpixel((x, y), (255, 255, 255))  # 白色
                elif current_color[0] < 35 and current_color[1] < 20 and current_color[2] < 20:
                    img.putpixel((x, y), (0, 0, 0))  # 白色
                else:
                    img.putpixel((x, y), (128, 128, 128))  # 黑色
        save_pic = path + '/newimg.png'
        img.save(save_pic)

    # 未修改
    def check_robot_pic_distance(self):
        """处理人机验证的图片"""
        self.cut_pic((143, 884), (936, 1380), '', 'cut')
        path = os.path.dirname(__file__) + '/pic'
        pic = path + '/cut.png'
        img = Image.open(pic)
        img = img.convert('RGB')
        width, height = img.size
        printed_first_result = False  # 用于记录第一个结果是否已经输出过
        printed_second_result = False  # 用于记录第二个结果是否已经输出过
        for y in range(20, height - 30):
            for x in range(5, width - 40):
                current_color = img.getpixel((x, y))
                if current_color[0] > 240 and current_color[1] > 240 and current_color[2] > 240:
                    if not printed_first_result:  # 确保只输出一次第一个结果
                        print(x, y)
                        printed_first_result = True
                    break
            if printed_first_result:  # 如果已经输出过第一个结果，则退出外层循环
                break
        for x1 in range(x, width - 40):
            current_color = img.getpixel((x1, y))
            if current_color[0] < 50 and current_color[1] < 55 and current_color[2] < 85 and current_color[0] + \
                    current_color[1] + current_color[2] < 150:
                if not printed_second_result:  # 确保只输出一次第二个结果
                    print(x1, y)
                    printed_second_result = True
                print("需要滑动的距离为{}".format(x1 - x))
                return x1 - x

    # 未修改
    def deal_robot_pic(self):
        """处理人机验证的图片"""
        path = os.path.dirname(__file__) + '/pic/save'
        pic = path + '/cut3.png'
        img = Image.open(pic)
        img = img.convert('RGB')
        width, height = img.size
        threshold = 90  # 阈值，用于判断颜色偏差是否较大
        for x in range(5, width - 40):
            for y in range(20, height - 30):
                # 获取当前像素点的颜色
                if x > 5 and y > 20 and x < width - 40 and y < height - 30:  # 跳过图片边沿的像素点
                    # 获取当前像素点的颜色
                    current_color = img.getpixel((x, y))
                    # if len(current_color) != 3:
                    #     raise ValueError(f"Invalid color format at ({x}, {y}): {current_color}")
                    #     # 获取周围像素点的颜色
                    num_deviant_neighbors = 0
                    for dx in range(-1, 2):
                        for dy in range(-1, 2):
                            if 0 <= x + dx < width and 0 <= y + dy < height:  # 确保不超出图像边界
                                neighbor_color = img.getpixel((x + dx, y + dy))
                                if isinstance(neighbor_color, tuple) and len(neighbor_color) == 3:  # 检查颜色格式
                                    neighbor_color = tuple(
                                        min(max(int(c), 0), 255) for c in neighbor_color)  # 确保颜色值在0到255之间
                                    channel_diffs = [abs(a - b) for a, b in zip(current_color, neighbor_color)]
                                    # 如果每个通道的偏差都大于30，则将邻居像素点计数为偏差点
                                    if all(diff > 70 for diff in channel_diffs):
                                        num_deviant_neighbors += 1
                                    # color_diff = sum(abs(a - b) for a, b in zip(current_color, neighbor_color))
                                    # if color_diff > threshold:
                                    #     num_deviant_neighbors += 1
                    # 如果偏差大于阈值的邻居数量大于4，则认为是偏差点
                    if num_deviant_neighbors > 3:
                        img.putpixel((x, y), (255, 255, 255))  # 白色
                    else:
                        img.putpixel((x, y), (0, 0, 0))  # 黑色
        save_pic = path + '/newimg.png'
        img.save(save_pic)

    # 已修改
    def check_countdown(self, last_time=''):
        """对倒计时时间进行转化，变成秒存储"""
        print(last_time)
        try:
            if len(last_time) == 4:
                minutes = int(last_time[:2])
                seconds = int(last_time[2:])
            else:
                print("时间格式异常")
                return False
            # 转换为总秒数
            total_seconds = minutes * 60 + seconds
            print("剩余总秒数：", total_seconds)
            if total_seconds > 900:  # 如果识别到的分钟大于15，说明识别异常了，按15分钟处理
                total_seconds = 890
            now = datetime.now()
            future_time = now + timedelta(seconds=total_seconds)
            # 将到期时间转换为时间戳
            future_timestamp = future_time.timestamp()
            future_datetime = datetime.fromtimestamp(future_timestamp)
            # 将datetime对象格式化为通常的时间格式
            formatted_future_time = future_datetime.strftime('%Y-%m-%d %H:%M:%S')
            print("预计开奖时间：", formatted_future_time)
            return total_seconds, future_timestamp
        except ValueError:
            print("输入的字符串不是有效的时间格式")
            return False

    # 已修改 不准确
    def check_detail_height(self):
        """判定福袋弹窗的高度，会因为抽奖所需任务不同稍有区别,分别有不要任务、1/2个任务"""
        path = os.path.dirname(__file__) + '/pic'
        pic1_path = path + '/screenshot.png'
        pic = Image.open(pic1_path)
        # pic_new = Image.open(cut_pic_path)
        pic_new = pic.convert('RGBA')
        pix = pic_new.load()
        if 30 <= pix[580, 1305 * self.resolution_ratio_y // 2453][0] <= 38 and 34 <= \
                pix[580, 1305 * self.resolution_ratio_y // 2453][1] <= 40 and 78 <= \
                pix[580, 1305 * self.resolution_ratio_y // 2453][2] <= 84:  # 福袋弹窗的高度离顶部距离 1295
            print('参与抽奖有3个任务')
            return 3
        elif 30 <= pix[580, 1365 * self.resolution_ratio_y // 2453][0] <= 38 and 34 <= \
                pix[580, 1365 * self.resolution_ratio_y // 2453][1] <= 40 and 78 <= \
                pix[580, 1365 * self.resolution_ratio_y // 2453][2] <= 84:  # 福袋弹窗的高度离顶部距离 1355
            print('参与抽奖有2个任务')
            return 2
        elif 30 <= pix[580, 1425 * self.resolution_ratio_y // 2453][0] <= 38 and 34 <= \
                pix[580, 1425 * self.resolution_ratio_y // 2453][1] <= 40 and 78 <= \
                pix[580, 1425 * self.resolution_ratio_y // 2453][2] <= 84:  # 福袋弹窗的高度离顶部距离 1415
            print('参与抽奖有1个任务')
            return 1
        elif self.check_have_robot_analyse():  # 如果打开的弹窗是个人机校验
            self.deal_robot_analyse()
        print('参与抽奖不需要任务')
        return 0

    # 一修改
    def check_have_fudai(self):
        """判定直播页面福袋的小图标是否存在"""
        path = os.path.dirname(__file__) + '/pic'
        pic1_path = path + '/screenshot.png'
        loop = 0
        while loop < 6:  # 每3秒识别一次，最多等待18秒
            time.sleep(1.5)
            self.get_screenshot()  # 这个函数需要2S
            pic = Image.open(pic1_path)
            pic_new = pic.convert('RGBA')
            pix = pic_new.load()
            for x in range(30, 410):
                if (194 <= pix[x, 365 * self.resolution_ratio_y // 2453 + self.y_pianyi][0] <= 200
                        and 187 <= pix[x, 365 * self.resolution_ratio_y // 2453 + self.y_pianyi][1] <= 193
                        and 241 <= pix[x, 365 * self.resolution_ratio_y // 2453 + self.y_pianyi][
                            2] <= 247):  # 判定存在小福袋的图标
                    self.last_find_fudai_time = time.time()
                    return x
            loop += 1
            if loop >= 4:
                self.deal_robot_analyse()
            elif loop < 2 and self.check_zhibo_is_closed():
                return False
        return False

    # 未修改
    def check_have_robot_analyse(self):
        """检查是否存在人机校验"""
        self.cut_pic((130, 790 * self.resolution_ratio_y // 2453), (680, 870 * self.resolution_ratio_y // 2453), '',
                     'zhibo_yanzheng')  # 福袋内容详情
        result = self.analyse_pic_word('zhibo_yanzheng', 1)
        if "验证" in result:
            print("存在滑动图片人机校验，需要等待完成验证.")
            return 1
        elif "形状相同" in result:
            print("存在点击图片人机校验，需要等待完成验证.")
            return 2
        return False

    # 未修改
    def deal_swipe_robot_analyse(self, distance=400):
        """处理滑动图片的人机验证"""
        if distance:
            targetx = 222 + distance
        else:
            targetx = 622
        os.system("adb -s %s shell input swipe 222 1444 %s 1444 300" % (self.device_id, targetx))
        print("滑轨滑动{}距离解锁人机验证".format(distance))
        time.sleep(1)

    # 未修改
    def deal_robot_analyse(self):
        """处理人机校验，包含各种情况"""
        swipe_times = 0
        while swipe_times < 10:
            robot_result = self.check_have_robot_analyse()
            if robot_result == 1:
                distance = self.check_robot_pic_distance()
                self.deal_swipe_robot_analyse(distance)
                time.sleep(10)
                self.get_screenshot()
            elif robot_result == 2:
                print("无法处理图片验证的人机，点击关闭退出验证，等待30分钟")
                os.system("adb -s {} shell input tap 910 {}".format(self.device_id,
                                                                    800 * self.resolution_ratio_y // 2453))  # 点击关闭
                # os.system("adb -s %s shell input keyevent 4" % self.device_id)
                time.sleep(1800)
                break
            else:
                break
            swipe_times += 1
        if swipe_times >= 10:
            print("无法处理图片验证的人机，点击关闭退出验证，等待30分钟")
            os.system("adb -s {} shell input tap 910 {}".format(self.device_id,
                                                                800 * self.resolution_ratio_y // 2453))  # 点击关闭
            time.sleep(1800)

    # 已修改
    def reflash_zhibo(self):
        """在关注列表，下拉刷新直播间"""
        print("下划刷新直播间列表")
        os.system("adb -s %s shell input swipe 566 800 566 1600 200" % (self.device_id))
        time.sleep(5)

    # 已修改
    def check_in_follow_list(self):
        """判断是否界面在我的关注的列表页"""
        self.cut_pic((200, 130 * self.resolution_ratio_y // 2453), (920, 215 * self.resolution_ratio_y // 2453), '',
                     'zhibo_follow_list')  # 福袋内容详情
        zhibo_list_title = self.analyse_pic_word('zhibo_follow_list', 1)
        if "关注" in zhibo_list_title:
            print("当前界面在直播关注列表")
            return True
        return False

    # 已修改
    def check_in_zhibo_list(self):
        """检查是否当前在直播列表"""
        self.cut_pic((400, 145 * self.resolution_ratio_y // 2453), (675, 230 * self.resolution_ratio_y // 2453), '',
                     'zhibo_list_title')  # 福袋内容详情
        zhibo_list_title = self.analyse_pic_word('zhibo_list_title', 1)
        if "正在直播" in zhibo_list_title:
            print("当前界面已经在直播间列表")
            return True
        return False

    # 未修改
    def check_zhibo_is_closed(self):
        """检查当前直播间是否关闭"""
        self.cut_pic((350, 200 * self.resolution_ratio_y // 2453), (740, 300 * self.resolution_ratio_y // 2453), '',
                     'zhibo_status')  # 福袋内容详情
        zhibo_list_title = self.analyse_pic_word('zhibo_status', 1)
        # print(zhibo_list_title)
        if "已结束" in zhibo_list_title:
            print("当前直播间已关闭")
            return True
        zhibo_list_title = self.analyse_pic_word('zhibo_status', 1, False)
        # print(zhibo_list_title)
        if "已结束" in zhibo_list_title:
            print("当前直播间已关闭")
            return True
        print("当前直播间正常进行中")
        return False

    # 已修改
    def back_to_zhibo_list(self):
        """功能初始化，回到直播间列表"""
        click_back_times = 0
        while click_back_times < 4:
            self.get_screenshot()
            if self.check_in_zhibo_list():
                return False
            elif self.check_in_follow_list():
                os.system("adb -s {} shell input tap 400 {}".format(self.device_id,
                                                                    500 * self.resolution_ratio_y // 2453))
                print("点击打开直播间的列表")
                time.sleep(2)
                return False
            os.system("adb -s %s shell input keyevent 4" % self.device_id)
            print("点击返回")
            time.sleep(2)
            click_back_times += 1

    # 已修改
    def into_zhibo_from_list(self):
        """从直接列表进入直播间"""
        while True:
            self.get_screenshot()
            if self.check_in_zhibo_list():
                current_hour = self.get_current_hour()
                if 3 < current_hour <= 6:
                    print("等待10分钟继续检查")
                    time.sleep(600)  # 等待10分钟继续检查
                else:
                    self.reflash_zhibo()  # 刷新直播间列表
                    if current_hour > 8:  # 如果当前时间已经早上9点多了，一定有直播间了
                        os.system("adb -s {} shell input tap 290 {}".format(self.device_id,
                                                                            490 * self.resolution_ratio_y // 2453))  # 点击第一个直播间
                        print("点击打开第一个直播间")
                        break  # 跳出循环，直播间已找到
                    elif self.check_zhibo_list_have_zhibo():  # 如果存在直播间
                        os.system("adb -s {} shell input tap 290 {}".format(self.device_id,
                                                                            490 * self.resolution_ratio_y // 2453))  # 点击第一个直播间
                        print("点击打开第一个直播间")
                        break
                    else:  # 如果直播列表是空的，则退出到关注列表
                        os.system("adb -s %s shell input keyevent 4" % self.device_id)
                        time.sleep(3)
                        print("点击退出到关注列表")
            elif self.check_zhibo_have_popup():
                os.system(
                    "adb -s {} shell input tap 566 {}".format(self.device_id, 1620 * self.resolution_ratio_y // 2453))
                print("点击关闭红包弹窗")
                os.system("adb -s %s shell input keyevent 4" % self.device_id)
                time.sleep(3)
                print("点击退出直播间")
            elif self.check_zhibo_is_closed():
                os.system("adb -s %s shell input keyevent 4" % self.device_id)
                time.sleep(3)
                print("点击退出直播间")
            elif self.check_in_follow_list():
                os.system(
                    "adb -s {} shell input tap 400 {}".format(self.device_id, 500 * self.resolution_ratio_y // 2453))
                print("点击打开直播间的列表")
                print("当前页面不在直播间")
                time.sleep(600)  # 等待10分钟继续检查
                print("等待10分钟后再检查")

    # 已修改
    def check_zhibo_list_have_zhibo(self):
        """检查直播列表是否存在直播的内容"""
        self.get_screenshot()
        path = os.path.dirname(__file__) + '/pic'
        pic1_path = path + '/screenshot.png'
        pic = Image.open(pic1_path)
        # pic_new = Image.open(cut_pic_path)
        pic_new = pic.convert('RGBA')
        pix = pic_new.load()
        if pix[290, 490 * self.resolution_ratio_y // 2453][0] == 255 and \
                pix[290, 490 * self.resolution_ratio_y // 2453][1] == 255 and \
                pix[290, 490 * self.resolution_ratio_y // 2453][2] == 255:
            print('直播间列表为空')
            return False
        print('直播间列表存在直播的内容')
        return True

    # 未修改
    def check_zhibo_have_popup(self):
        """判断直播间是否弹出了节假日红包弹窗"""
        self.cut_pic((425, 880 * self.resolution_ratio_y // 2453), (660, 960 * self.resolution_ratio_y // 2453), '',
                     'zhibo_hongbao')  # 福袋内容详情
        zhibo_list_title = self.analyse_pic_word('zhibo_hongbao', 1)
        if "最高金额" in zhibo_list_title:
            print("直播间有红包弹窗")
            return True
        return False

    # 已修改
    def check_no_fudai_time(self):
        """无福袋等待时间检查"""
        if 3 < self.get_current_hour() < 7:  # 如果是凌晨4-6点
            self.last_find_fudai_time = 0.00
        elif self.last_find_fudai_time == 0.00 or self.last_find_fudai_time == 0:  # 如果过了不挂机时间，把当前时间赋值给上次找到福袋的时间
            self.last_find_fudai_time = time.time()
        if self.last_find_fudai_time > 0:
            current_time = time.time()
            wait_time = current_time - self.last_find_fudai_time
            wait_time = round(wait_time, 1)
            if wait_time > 1:
                print("距离上一次识别到福袋已经过去{}秒".format(wait_time))
            return wait_time
        return 0

    # 已修改
    def get_fudai_contain(self, renwu=2):
        """获取福袋的内容和倒计时"""
        if renwu == 2:  # 如果是2个任务的
            self.cut_pic((320, 1560 * self.resolution_ratio_y // 2453 + self.y_pianyi),
                         (1090, 1880 * self.resolution_ratio_y // 2453 + self.y_pianyi), '', 'fudai_content')  # 福袋内容详情
            self.cut_pic((455, 1485 * self.resolution_ratio_y // 2453), (580, 1535 * self.resolution_ratio_y // 2453),
                         '', 'fudai_countdown')  # 完整福袋详情倒计时
        elif renwu == 1:  # 如果是1个任务的
            self.cut_pic((320, 1620 * self.resolution_ratio_y // 2453 + self.y_pianyi),
                         (1090, 1940 * self.resolution_ratio_y // 2453 + self.y_pianyi), '', 'fudai_content')  # 福袋内容详情
            self.cut_pic((455, 1545 * self.resolution_ratio_y // 2453), (580, 1595 * self.resolution_ratio_y // 2453),
                         '', 'fudai_countdown')  # 完整福袋详情倒计时
        elif renwu == 3:  # 如果是3个任务的
            self.cut_pic((320, 1500 * self.resolution_ratio_y // 2453 + self.y_pianyi),
                         (1090, 1820 * self.resolution_ratio_y // 2453 + self.y_pianyi), '', 'fudai_content')  # 福袋内容详情
            self.cut_pic((455, 1425 * self.resolution_ratio_y // 2453), (580, 1475 * self.resolution_ratio_y // 2453),
                         '', 'fudai_countdown')  # 完整福袋详情倒计时
        else:
            self.cut_pic((320, 1845 * self.resolution_ratio_y // 2453 + self.y_pianyi),
                         (1090, 2165 * self.resolution_ratio_y // 2453 + self.y_pianyi), '', 'fudai_content')  # 福袋内容详情
            self.cut_pic((455, 1770 * self.resolution_ratio_y // 2453), (580, 1820 * self.resolution_ratio_y // 2453),
                         '', 'fudai_countdown')  # 完整福袋详情倒计时
        fudai_content_text = self.analyse_pic_word('fudai_content', 1)
        print("福袋内容：{}".format(fudai_content_text))
        time_text = self.analyse_pic_word('fudai_countdown', 2)
        print("倒计时时间：{}".format(time_text))
        return fudai_content_text, time_text

    # 已修改
    def check_contain(self, contains=''):
        """检查福袋内容是否想要"""
        contains_not_want = []
        contains_want = ["鱼竿", "钓杆", "钓竿", "浮漂", "鱼漂", "支架", "炮台", "钓椅", "钓箱", "饵料"]
        if self.get_current_hour() < 7:
            return False
        if self.all:
            return False
        for contain in contains_want:
            if contain in contains:
                return False
        for contain in contains_not_want:
            if contain in contains:
                return True
        return False

    # 已修改
    def attend_choujiang(self, renwu=1):
        """点击参与抽奖"""
        click_times = 0
        while click_times < 2:
            self.cut_pic((40, 2205 * self.resolution_ratio_y // 2453), (1090, 2320 * self.resolution_ratio_y // 2453),
                         '', "attend_button")  # 参与福袋抽奖的文字
            attend_button_text = self.analyse_pic_word('attend_button', 1)
            print("参与抽奖按钮文字内容：{}".format(attend_button_text))
            if "参与成功" in attend_button_text:  # 如果识别到已经参与抽奖
                print("已经参与，等待开奖")
                os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                    420 * self.resolution_ratio_y // 2453))  # 点击刚才打开福袋的旁边位置
                print("点击福袋外部，关闭福袋详情")
                return True
            elif "还需看播" in attend_button_text:  # 如果识别到已经参与抽奖
                print("已经参与，等待看播时间凑齐开奖")
                os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                    420 * self.resolution_ratio_y // 2453))  # 点击刚才打开福袋的旁边位置
                print("点击福袋外部，关闭福袋详情")
                return True
            elif "无法参与" in attend_button_text:  # 如果识别到无法参与抽奖
                print("条件不满足，无法参与抽奖")
                os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                    420 * self.resolution_ratio_y // 2453))  # 点击刚才打开福袋的旁边位置
                print("点击福袋外部，关闭福袋详情")
                return False
            elif "时长不足" in attend_button_text:  # 如果识别到无法参与抽奖
                print("看播时长不够了，无法参与抽奖")
                os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                    420 * self.resolution_ratio_y // 2453))  # 点击刚才打开福袋的旁边位置
                print("点击福袋外部，关闭福袋详情")
                return False
            elif "评论" in attend_button_text:
                os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                    2275 * self.resolution_ratio_y // 2453))  # 点击参与抽奖
                print("点击参与抽奖")
                return True
            elif "参与抽奖" in attend_button_text:
                os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                    2275 * self.resolution_ratio_y // 2453))  # 点击参与抽奖
                print("点击参与抽奖")
                return True
            elif "加入粉丝团(1钻石)" in attend_button_text:
                os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                    420 * self.resolution_ratio_y // 2453))  # 点击刚才打开福袋的旁边位置
                print("点击福袋外部，关闭支付弹窗")
                time.sleep(1)
                return False
            elif "粉丝团" in attend_button_text:
                os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                    2275 * self.resolution_ratio_y // 2453))  # 点击加入粉丝团、点亮粉丝团
                time.sleep(2)
                os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                    420 * self.resolution_ratio_y // 2453))  # 点击刚才打开福袋的旁边位置
                print("点击福袋外部，关闭支付弹窗")
                # os.system("adb -s %s shell input keyevent 4" % self.device_id) #退出充值的弹窗
                time.sleep(1)
                click_times += 1
                self.get_screenshot()
            elif "活动已结束" in attend_button_text:
                os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                    420 * self.resolution_ratio_y // 2453))  # 点击刚才打开福袋的旁边位置
                print("点击福袋外部，关闭福袋详情")
                return False
            elif "开通店铺会员" in attend_button_text:
                os.system("adb -s %s shell input keyevent 4" % self.device_id)
                time.sleep(1)
                os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                    420 * self.resolution_ratio_y // 2453))  # 点击刚才打开福袋的旁边位置
                print("点击福袋外部，关闭入会弹窗")
                time.sleep(1)
                return False
            else:
                print("参与抽奖按钮文字没匹配上")
                click_times = 2
                return False
        print("参与抽奖多次点击失败")
        return False

    # 已修改
    def check_have_no_award(self):
        """判定是否未中奖"""
        self.get_screenshot()
        self.cut_pic((420, 830 * self.resolution_ratio_y // 2453), (710, 890 * self.resolution_ratio_y // 2453), '',
                     "choujiang_result")  # 没有抽中福袋位置
        choujiang_result = self.analyse_pic_word('choujiang_result', 1)
        if "没有抽中福袋" in choujiang_result:
            return True
        return False

    # 已修改
    def check_have_reward(self):
        """判断是否中奖"""
        self.cut_pic((420, 830 * self.resolution_ratio_y // 2453),
                     (710, 890 * self.resolution_ratio_y // 2453), '', "get_reward")  # 立即领取奖品
        choujiang_result = self.analyse_pic_word('get_reward', 1)
        if "恭喜抽中福袋" in choujiang_result:
            print("存在奖品")
            return 1475 * self.resolution_ratio_y // 2453
        return False

    # 未修改
    def check_have_reward_notice_confirm(self):
        """判断是否有领奖的二次确认提醒"""
        self.get_screenshot()
        self.cut_pic((425, 1280 * self.resolution_ratio_y // 2453),
                     (705, 1390 * self.resolution_ratio_y // 2453), '', "reward_notice_confirm")  # 提醒领取奖品的弹窗
        choujiang_result = self.analyse_pic_word('reward_notice_confirm', 1)
        if "我知道了" in choujiang_result:
            print("存在奖品领取提醒")
            return True
        return False

    # 已修改
    def get_reward(self, reward_y=0):
        """中奖后领奖然后返回"""
        self.save_reward_pic()
        os.system("adb -s {} shell input tap 320 {}".format(self.device_id, reward_y))  # 勾选协议
        time.sleep(1)
        os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                            reward_y - 120 * self.resolution_ratio_y // 2453))  # 点击领取
        print("勾选协议，点击领取奖品")
        time.sleep(10)
        # self.save_reward_pic()
        os.system(
            "adb -s {} shell input tap 960 {}".format(self.device_id, 2375 * self.resolution_ratio_y // 2453))  # 点击下单
        print("点击下单")
        time.sleep(10)
        os.system("adb -s %s shell input keyevent 4" % self.device_id)  # 下完单点击返回直播间
        print("下完单点击返回直播间")
        time.sleep(10)
        if self.check_have_reward():
            print("领奖弹窗未关闭，点击关闭弹窗")
            # self.save_reward_pic()
            os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                reward_y + 170 * self.resolution_ratio_y // 2453))
            print("点击坐标位置:566 {}关闭领奖弹窗".format(reward_y + 170 * self.resolution_ratio_y // 2453))
            time.sleep(2)
            os.system("adb -s %s shell input keyevent 4" % self.device_id)
            time.sleep(2)
        if self.check_have_reward_notice_confirm():
            print("提醒领奖弹窗未关闭，点击我知道了，关闭弹窗")
            os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                1340 * self.resolution_ratio_y // 2453))  # 点击我知道了
            time.sleep(2)
        time.sleep(30)
        print("关闭中奖提醒后等待30S")

    # 已修改
    def get_ballery_level(self):
        """获取设备电量信息"""
        battery_info = subprocess.Popen("adb -s %s shell dumpsys battery" % self.device_id, shell=True,
                                        stdout=subprocess.PIPE)
        battery_info_string = battery_info.stdout.read()
        battery_info_string = bytes.decode(battery_info_string)
        location = re.search('level:', battery_info_string)
        span = location.span()
        start, end = span
        start = end + 1
        for i in range(5):
            end += 1
            if battery_info_string[end] == "\n":
                break
        battery_level = battery_info_string[start:end]  # 第几个到第几个中间接冒号
        battery_level = int(battery_level)
        print("设备当前电量为{}".format(battery_level))
        return battery_level

    # 已修改
    def deal_battery_level(self):
        """针对电量不足的情况做处理"""
        while self.get_ballery_level() < 30:
            print("设备电量较低，退出到直播列表，等待电量恢复后继续挂机")
            self.back_to_zhibo_list()
            time.sleep(1800)  # 挂机30分钟

    def fudai_choujiang(self, device_id="", y_pianyi=0, y_resolution=2453, needswitch=False, wait_minutes=15):
        """默认不切换直播间"""
        self.device_id = device_id
        self.y_pianyi = y_pianyi
        self.resolution_ratio_y = y_resolution
        wait_times = 0  # 当前直播间的等待次数，累计4次没有福袋，则切换直播间
        swipe_times = 0  # 向上滑动的次数,当超出一定值，退出返回直播列表
        fudai_not_open_times = 0  # 无法打开福袋的次数
        while True:
            self.deal_battery_level()  # 设备电量
            x = self.check_have_fudai()  # 检查是否有福袋
            if self.check_no_fudai_time() > 1800:  # 如果30分钟都没有福袋
                self.save_reward_pic()
                self.back_to_zhibo_list()
                self.into_zhibo_from_list()
                continue
            if x and swipe_times < 17:
                wait_times = 0
                # self.cut_pic((x, 320), (x + 90, 410), name='fudai')  # 通常小福袋的位置
                os.system("adb -s {} shell input tap {} {}".format(self.device_id, x + 45,
                                                                   370 * self.resolution_ratio_y // 2453))  # 点击默认小福袋的位置
                print("点击打开福袋详情")
                time.sleep(3)
            elif needswitch:  # 如果福袋不存在，且需要切换直播间
                if swipe_times < 15 and self.get_current_hour() > 6:  # 上划次数不到10次，且已经是7点后了，就继续上划
                    os.system("adb -s %s shell input swipe 566 1600 566 800 200" % (self.device_id))
                    print("直播间无福袋，上划切换直播间")
                    swipe_times += 1
                else:  # 如果时间已经是凌晨，没有直播间福袋就整个退出
                    print("直播间刷了15个都无福袋，退出返回直播列表")
                    os.system("adb -s %s shell input keyevent 4" % self.device_id)
                    time.sleep(3)
                    if self.check_in_follow_list():
                        os.system("adb -s {} shell input tap 400 {}".format(self.device_id,
                                                                            500 * self.resolution_ratio_y // 2453))  # 点击直播中
                        print("点击打开直播间列表")
                    self.into_zhibo_from_list()
                    swipe_times = 0  # 滑动次数归0
                time.sleep(5)
                continue
            elif self.check_zhibo_is_closed():  # 如果不切换直播间但直播间已经关闭了
                self.back_to_zhibo_list()
                self.into_zhibo_from_list()
                swipe_times = 0
                time.sleep(5)
                continue
            elif wait_times >= 4:  # 如果福袋不存在，且不需要切换直播间，但等待了很久
                if swipe_times < 15:  # 上划次数不到10次，就继续上划
                    os.system("adb -s %s shell input swipe 566 1600 566 800 200" % (self.device_id))
                    print("直播间等待2分钟无福袋，上划切换直播间")
                    swipe_times += 1
                    # time.sleep(5)
                    continue
                else:
                    print("直播间等待2分钟无福袋，退出返回直播列表")
                    self.back_to_zhibo_list()
                    self.into_zhibo_from_list()
                    swipe_times = 0  # 滑动次数归0
                wait_times = 0
                time.sleep(5)
                continue
            else:  # 如果福袋不存在，且不需要切换直播间，且等待轮数不够
                print("直播间暂无福袋，等待60S")
                # wait_times += 1
                time.sleep(60)
                continue
            self.get_screenshot()
            renwu = self.check_detail_height()
            fudai_content_text, time_text = self.get_fudai_contain(renwu)
            if self.check_contain(fudai_content_text) and needswitch:  # 如果福袋内容是不想要的
                os.system("adb -s {} shell input tap {} {}".format(self.device_id, x + 45,
                                                                   420 * self.resolution_ratio_y // 2453))  # 点击刚才打开小福袋的位置的旁边
                print("点击小福袋位置，关闭福袋详情")
                time.sleep(1)
                os.system("adb -s %s shell input swipe 566 1600 566 800 200" % self.device_id)
                print("直播间福袋内容不理想，上划切换直播间")
                swipe_times += 1
                time.sleep(5)
                continue
            result = self.check_countdown(time_text)
            if result:
                fudai_not_open_times = 0
                lastsecond, future_timestamp = result
            else:  # 如果识别到的倒计时内容不太对，则再判定一次
                self.get_screenshot()
                renwu = self.check_detail_height()
                fudai_content_text, time_text = self.get_fudai_contain(renwu)
                result = self.check_countdown(time_text)
                if result:
                    fudai_not_open_times = 0
                    lastsecond, future_timestamp = result
                else:
                    fudai_not_open_times += 1
                    os.system("adb -s {} shell input tap {} {}".format(self.device_id, x + 45,
                                                                       420 * self.resolution_ratio_y // 2453))  # 点击刚才打开小福袋的位置的旁边
                    print("第{}次打开福袋异常，点击小福袋旁边位置，坐标{},{}关闭福袋详情".format(fudai_not_open_times,
                                                                                               x + 45,
                                                                                               420 * self.resolution_ratio_y // 2453))
                    if fudai_not_open_times > 10:
                        print("超过10次点击福袋无法打开详情，等待30分钟")
                        time.sleep(1800)
                    time.sleep(1)
                    continue
            # if lastsecond < 15 and needswitch:  # 如果不到15秒了，就不点了
            #     os.system("adb -s {} shell input tap {} {}".format(self.device_id, x + 45,
            #                                                        420 * self.resolution_ratio_y // 2453))  # 点击刚才打开小福袋的位置的旁边
            #     print("点击小福袋位置，关闭福袋详情")
            #     time.sleep(1)
            #     if needswitch:
            #         os.system("adb -s %s shell input swipe 566 1600 566 800 200" % (self.device_id))
            #         print("抽奖倒计时时间小于15秒，不参与，上划切换直播间")
            #         swipe_times += 1
            #     time.sleep(5)
            #     continue
            if needswitch and lastsecond >= 60 * wait_minutes:  # 如果需要切换且倒计时时间大于设定的分钟
                os.system("adb -s {} shell input tap {} {}".format(self.device_id, x + 45,
                                                                   420 * self.resolution_ratio_y // 2453))  # 点击刚才打开小福袋的位置
                print("点击小福袋位置，关闭福袋详情")
                time.sleep(1)
                os.system("adb -s %s shell input swipe 566 1600 566 800 200" % (self.device_id))
                print("抽奖倒计时时间大于{}分钟，暂不参与，上划切换直播间".format(wait_minutes))
                swipe_times += 1
                time.sleep(5)
                continue
            if not self.attend_choujiang(renwu):  # 如果参与抽奖失败
                os.system("adb -s %s shell input swipe 566 1600 566 800 200" % (self.device_id))
                print("参与抽奖失败，上划切换直播间")
                swipe_times += 1
                time.sleep(5)
                continue
            time.sleep(lastsecond)
            no_award_result = self.check_have_no_award()
            if no_award_result:
                os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                    1330 * self.resolution_ratio_y // 2453))  # 点击我知道了
                print("没有抽中，点击:我知道了,关闭弹窗")
                time.sleep(5)
                no_award_result = self.check_have_no_award()
                if no_award_result:
                    os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                        1330 * self.resolution_ratio_y // 2453))  # 点击我知道了
                    print("再次点击:我知道了,关闭弹窗")
                    time.sleep(10)
                continue
            reward_y = self.check_have_reward()
            if reward_y:
                self.get_reward(reward_y)
                continue
            elif self.check_zhibo_is_closed():
                print("直播间已关闭，上划切换直播间")
                swipe_times += 1
                os.system("adb -s %s shell input swipe 566 1600 566 800 200" % (self.device_id))
                time.sleep(10)
                continue
            elif self.check_in_zhibo_list():  # 如果已经退出到直播间列表
                self.into_zhibo_from_list()
                swipe_times = 0  # 滑动次数归0
                continue
            os.system("adb -s {} shell input tap 566 {}".format(self.device_id,
                                                                1330 * self.resolution_ratio_y // 2453))  # 点击我知道了
            print("没有抽中，点击:我知道了,关闭弹窗")
            time.sleep(10)
            continue


if __name__ == '__main__':
    douyin = fudai_analyse()

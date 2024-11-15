import json
import os

from selenium.webdriver.common.by import By

from adb_driver import select_device, connect_douyin


def get_window_size():
    size = os.popen("adb -s {} shell wm size".format(device_id)).read()
    size = size.split("\n")
    for x in size:
        if 'Override size' in x:
            window_size = x.split(":")[1].strip().split("x")
            return window_size[0], window_size[1]
    return driver.get_window_size()['width'], driver.get_window_size()['height']


if __name__ == '__main__':
    device_id = select_device()
    driver = connect_douyin(device_id)
    width, height = get_window_size()

    # 我的
    driver.implicitly_wait(1)
    driver.find_element(By.XPATH, "//*[@text='我']").click()

    # 关注
    driver.implicitly_wait(1)
    driver.find_element(By.ID, "com.ss.android.ugc.aweme:id/3ey").click()

    # 直播中
    driver.implicitly_wait(1)
    driver.find_element(By.XPATH, "//*[@text='直播中']").click()

    # 正在直播
    driver.implicitly_wait(1)
    living_list_size = driver.find_element(By.ID,
                                           "com.ss.android.ugc.aweme:id/b=n").size  # {'height': 2110, 'width': 1133}
    # print(living_list_size.get('width'), living_list_size.get('height'))
    os.system(
        "adb -s {} shell input tap {} {}".format(device_id, living_list_size.get('width') // 3,
                                                 living_list_size.get('height') // 4))

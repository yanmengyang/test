import time

from selenium.webdriver.common.by import By

from driver_swipe import AppSwipe, app_driver


def find_result():
    while True:
        try:
            driver.find_element(By.XPATH, "//*[@text='我知道了']").click()
            break
        except:
            time.sleep(30)


def take_part():
    time.sleep(10)
    while True:
        try:
            super_fudai = driver.find_element(By.XPATH, "//*[contains(text(), '超级福袋')]")
            super_fudai.click()
            need_join_fans = driver.find_element(By.XPATH, "//*[@text='加入直播粉丝团未达成')]")
            if need_join_fans is not None:
                break
            driver.find_element(By.XPATH, "//*[@text='一键发表评论']").click()
            find_result()
        except:
            AppSwipe(driver).swipeTap()
            AppSwipe(driver).swipeUp()
            take_part()


if __name__ == '__main__':
    driver = app_driver()
    time.sleep(1)

    driver.find_element(By.XPATH, "//*[@text='关注']").click()
    time.sleep(1)

    while True:
        try:
            driver.find_element(By.XPATH, "//*[@text='点击进入直播间']").click()
            break
        except:
            AppSwipe(driver).swipeUp()

    # 参与福袋
    take_part()

import json
import os

import numpy as np
from PIL import Image
from paddleocr import PaddleOCR


def ocr_img(image_path):
    # img = Image.open(image_path).convert('RGBA')
    # img = np.array(img)  # 经提醒，需要添加array
    ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    result = ocr.ocr(image_path, cls=True)
    img_content = ''
    # print(result)
    for idx in range(len(result)):
        res = result[idx]
        if res is None:
            continue
        for line in res:
            content = json.dumps(line[1])
            img_content = img_content + json.loads(content)[0]
    # print(img_content)
    return img_content


def cut_pic(left_up=(0, 63), right_down=(1080, 1620), target='', name='', resolution=(1080, 2400)):
    '''裁剪截图，获取需要的小图片方便识别'''
    if target == '' or target == False:
        path = os.path.dirname(__file__) + '/pic'
        pic1_path = path + '/img_1.png'
        pic = Image.open(pic1_path)
        if name == '':
            cut_pic_path = path + '/cut.png'
        else:
            cut_pic_path = path + '/' + name + '.png'
        print('image size: {}'.format(pic.size))
        print('left_up: {}'.format(left_up))
        print('right_down: {}'.format(right_down))
        print('click: {}'.format(440 * 2453 // 2400))
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


if __name__ == '__main__':
    y_pianyi = 0
    resolution_ratio_y = 2453

    path = os.path.dirname(__file__) + '/pic'
    pic1_path = path + '/choujiang_result.png'
    # pic = Image.open(pic1_path)
    # print(pic)
    # pic_new = pic.convert('RGBA')
    # pix = pic_new.load()
    # print(pix[30, 365 * resolution_ratio_y // 2453 + y_pianyi])
    # i = 0
    # for x in range(30, 410):
    #     print(pix[x, 365 * resolution_ratio_y // 2453 + y_pianyi])
    #     if 194 <= pix[x, 365 * resolution_ratio_y // 2453 + y_pianyi][0] <= 200 and 187 <= \
    #             pix[x, 365 * resolution_ratio_y // 2453 + y_pianyi][1] <= 193 and 241 <= \
    #             pix[x, 365 * resolution_ratio_y // 2453 + y_pianyi][2] <= 247:  # 判定存在小福袋的图标
    #         print(f'x:{x}')
    #         i = x
    # x = 30
    # cut_pic((400, 145), (675, 230), name='zhibo_follow_list')  # 通常小福袋的位置
    ocr_img(pic1_path)
    # cut_pic((420, 830), (710, 890), name='result')

# 负责二维码相关处理
import asyncio
import base64
import aiofile
import cv2
import pyzbar.pyzbar
# from pyzbar.pyzbar import decode
import qrcode
from PIL import Image
import os

# 这个更新是记不住的
latest_filename=''
raw_path='data/qrcode/raw/'
qrcode_path='data/qrcode/generate/'

async def save_base64(base64_str, filename):
    """保存base64格式的二维码"""
    latest_filename=filename
    head, context = base64_str.split(",")
    img_data = base64.b64decode(context)
    # 图片格式
    head2, head3 = head.split('/')
    img_type, head4 = head3.split(';')
    async with aiofile.async_open(os.path.join(raw_path,filename+'.'+img_type), 'wb') as file:
        await file.write(img_data)
    return raw_path + filename + '.' + img_type

async def decode(image_path):
    """解码二维码，返回字符串"""
    image = cv2.imread(image_path)
    decoded_objects = pyzbar.pyzbar.decode(image)
    return decoded_objects.pop().data.decode("utf-8")

async def create(data, filename, size):
    """根据文本数据生成二维码"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 调整图像大小 LANCZOS
    img = img.resize((size, size),Image.LANCZOS)
    # 保存图像
    filepath=os.path.join(qrcode_path, filename+'.png')
    # lv_img_conv.py 不能够直接转换灰度图像
    img.convert("RGB").save(filepath)


def convert_for_device(filename):
    """将重生成的二维码，转换为lvgl RGB565SWAP true_color_alpha格式，再转为base64字符串以供发送"""
    img_path=os.path.join(qrcode_path, filename+'.png')
    print(img_path)
    print('python3 lv_img_conv.py -f true_color_alpha -cf RGB565SWAP -ff C '+img_path)
    # 这个不能放到异步函数里面
    p=os.popen('python3 lv_img_conv.py -f true_color_alpha -cf RGB565SWAP -ff C '+img_path)
    print(p.read())
    p.close()
    p=os.popen('python3 lv_img_conv.py -f true_color_alpha -cf RGB565SWAP -ff BIN '+img_path)
    print(p.read())
    p.close()
    # async with aiofile.async_open(os.path.join(qrcode_path, latest_filename+'.bin'), 'rb') as file:
    #     img_data = await file.read()
    with open(os.path.join(qrcode_path, filename+'.bin'), 'rb') as file:
        img_data = file.read()
    data_for_device= base64.b64encode(img_data).decode()
    # 保存至txt
    # async with aiofile.async_open(os.path.join(qrcode_path, latest_filename+'.txt'), 'w') as file:
    #     await file.write(data_for_device)
    with open(os.path.join(qrcode_path, filename+'.txt'), 'w') as file:
        file.write(data_for_device)
    return data_for_device
# 后端多个组件共用的一些变量，随着系统的运行而变化
import asyncio
import database
import base64
import aiofile
import cv2
import pyzbar.pyzbar
import qrcode
from PIL import Image
import os
import time
import database

emerg_msg_template='[紧急情况]院楼：{building}。楼层：{floor}。房间：{room}。'
resp_msg_template='{doctor}已响应。'

raw_qrcode_path='data/qrcode/raw/'
generate_qrcode_path='data/qrcode/generate/'

class Emergency_data():
    """存储应急情况相关数据"""
    def __init__(self):
        # 发生紧急情况的设备和对应负责用户
        self.device_to_user={}    
        # 发生紧急情况应当负责的用户和对应负责设备
        self.user_to_device={}
        # 发生紧急情况的设备和已经响应的用户
        self.device_to_resp_user={}
        # 紧急情况信息
        # key为device_id，value也为字典，包含'emerg_msg'和'resp_msg'
        self.message={}
        self.message_list=[]    # 用于发送给前端，每一个元素是一条报警信息和响应信息
        # 锁
        self.device_to_user_lock=asyncio.Lock()
        self.user_to_device_lock=asyncio.Lock()
        self.device_to_resp_user_lock=asyncio.Lock()    
        self.message_lock=asyncio.Lock()
        self.message_list_lock=asyncio.Lock()

    async def is_set_in_alarm(self,device_id):
        """设备正处于报警状态"""
        async with self.device_to_user_lock:
            return device_id in self.device_to_user
        
    async def update_device_to_user(self,device_id,user_id_list):
        """更新device_to_user"""
        async with self.device_to_user_lock:
            self.device_to_user[device_id]=user_id_list
        
    async def update_user_to_device(self,device_id,user_id_list):
        """更新user_to_device"""
        async with self.user_to_device_lock:
            for user_id in user_id_list:
                if user_id not in self.user_to_device.keys():
                    self.user_to_device[user_id] = [device_id]
                else:
                    self.user_to_device[user_id].append(device_id)

    async def update_msg_list(self):
        """更新message_list"""
        async with self.message_list_lock:
            self.message_list=[]
            for device_id in self.message:
                msg=self.message[device_id]['emerg_msg']+''.join(self.message[device_id]['resp_msg'].values())
                self.message_list.append(msg)

    async def check_user_device(self,user_id,device_id):
        """检查device_id是否是user_id负责的"""
        async with self.user_to_device_lock:
            if user_id not in self.user_to_device.keys():
                return False
            print(self.user_to_device)
            print(device_id in self.user_to_device[user_id])
            #     return device_id in self.user_to_device[user_id]
# KeyError: 5
            return device_id in self.user_to_device[user_id]
    
    async def add_new_alarm(self,device_id):
        """新的报警"""
        # 更新 device_to_user, user_to_device
        user_id_list = await database.get_user_id(device_id)
        await self.update_device_to_user(device_id, user_id_list)
        await self.update_user_to_device(device_id, user_id_list)
        # 更新 device_to_resp_user
        async with self.device_to_resp_user_lock:
            self.device_to_resp_user[device_id]=[]
        # 更新 message
        location_dict=await database.get_device_location(device_id)
        async with self.message_lock:
            self.message[device_id]={}
            self.message[device_id]['emerg_msg']=emerg_msg_template.format(building=location_dict['building'],floor=location_dict['floor'],room=location_dict['room'])
            self.message[device_id]['resp_msg']={}
        await self.update_msg_list()

    async def remove_alarm(self,device_id):
        """结束一个报警"""
        # 更新 device_to_user, user_to_device
        async with self.device_to_user_lock:
            self.device_to_user.pop(device_id,None)
        async with self.user_to_device_lock:
            for user_id in self.user_to_device.keys():
                if device_id in self.user_to_device[user_id]:
                    self.user_to_device[user_id].remove(device_id)
        # 更新 device_to_resp_user
        async with self.device_to_resp_user_lock:
            self.device_to_resp_user.pop(device_id,None)
        # 更新 message
        async with self.message_lock:
            self.message.pop(device_id,None)
        # 更新 message_list
        await self.update_msg_list()

    async def remove_all_response(self,user_id):
        """取消user_id的所有响应"""
        async with self.device_to_resp_user_lock:
            for device_id in self.device_to_resp_user.keys():
                if user_id in self.device_to_resp_user[device_id]:
                    self.device_to_resp_user[device_id].remove(user_id)
        # 更新 message
        async with self.message_lock:
            for device_id in self.message.keys():
                self.message[device_id]['resp_msg'].pop(user_id,None)
        # 更新 message_list
        await self.update_msg_list()

    async def add_response(self,device_id,user_id):
        """医生响应"""
        async with self.device_to_resp_user_lock:
            self.device_to_resp_user[device_id].append(user_id)
        # 更新 message
        name=await database.get_user_name(user_id)
        async with self.message_lock:
            self.message[device_id]['resp_msg'][user_id]=resp_msg_template.format(doctor=name)
        # 更新 message_list
        await self.update_msg_list()

    async def remove_response(self,device_id,user_id):
        """医生取消响应"""
        async with self.device_to_resp_user_lock:
            if user_id in self.device_to_resp_user[device_id]:
                self.device_to_resp_user[device_id].remove(user_id)
        # 更新 message
        async with self.message_lock:
            self.message[device_id]['resp_msg'].pop(user_id,None)
        # 更新 message_list
        await self.update_msg_list()

    async def check_responsed(self,device_id):
        """检查是否有人响应"""
        async with self.device_to_resp_user_lock:
            return len(self.device_to_resp_user[device_id])>0

    async def get_user_id(self,device_id):
        """获取负责的用户列表"""
        async with self.device_to_user_lock:
            return self.device_to_user[device_id]
        
    async def get_message_list(self):
        """获取message_list"""
        async with self.message_list_lock:
            message_list_copy=self.message_list.copy()
        return message_list_copy
  
class QRcode():
    """存储二维码相关数据"""
    def __init__(self):
        # 最新的二维码版本，年月日时分秒
        self.latest_version=None
        self.data_for_device=''

    
    async def init(self):
        """初始化"""
        self.latest_version=await database.get_qrcode_version()
        if self.latest_version!=None:
            async with aiofile.async_open(os.path.join(generate_qrcode_path, self.latest_version+'.txt'), 'r') as file:
                self.data_for_device=await file.read()
    
    async def save_base64_raw(self,base64_data):
        """保存前端传来的base64编码原始二维码"""
        self.latest_version=time.strftime("%Y%m%d%H%M%S", time.localtime())
        head, context = base64_data.split(",")
        img_data = base64.b64decode(context)
        head2, head3 = head.split('/')
        img_type, head4 = head3.split(';')
        img_path=os.path.join(raw_qrcode_path,self.latest_version+'.'+img_type)
        async with aiofile.async_open(img_path, 'wb') as file:
            await file.write(img_data)
        return img_path
        

    async def decode(self,image_path):
        """解码二维码，返回字符串"""
        image = cv2.imread(image_path)
        decoded_objects = pyzbar.pyzbar.decode(image)
        return decoded_objects.pop().data.decode("utf-8")

    async def generate(self, data, size):
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
        filepath=os.path.join(generate_qrcode_path,self.latest_version+'.png')
        # lv_img_conv.py 不能够直接转换灰度图像
        img.convert("RGB").save(filepath)

    async def convert_for_device(self):
        """将二维码图像，转换为lvgl RGB565SWAP true_color_alpha格式，再转为base64字符串以供发送"""
        img_path=os.path.join(generate_qrcode_path, self.latest_version+'.png')
        # 生成c代码格式和bin格式的lvgl图片
        process = await asyncio.create_subprocess_shell('python3 lv_img_conv.py -f true_color_alpha -cf RGB565SWAP -ff C '+img_path)
        await process.communicate()
        process = await asyncio.create_subprocess_shell('python3 lv_img_conv.py -f true_color_alpha -cf RGB565SWAP -ff BIN '+img_path)
        await process.communicate()

        async with aiofile.async_open(os.path.join(generate_qrcode_path, self.latest_version+'.bin'), 'rb') as file:
            img_data = await file.read()
        # 转为base64
        self.data_for_device= base64.b64encode(img_data).decode()
        # 保存至txt
        async with aiofile.async_open(os.path.join(generate_qrcode_path, self.latest_version+'.txt'), 'w') as file:
            await file.write(self.data_for_device)
        return self.data_for_device

    async def update(self,base64_data):
        """更新二维码"""
        raw_img_path=await self.save_base64_raw(base64_data)
        info=await self.decode(raw_img_path)
        if info=='':
            return 0
        await self.generate(info, 132)
        await self.convert_for_device()
        await database.set_qrcode_version(self.latest_version)
        return self.data_for_device

    async def get_data_for_device(self):
        return self.data_for_device
    
    async def get_latest_version(self):
        return self.latest_version

 
emerg_data=Emergency_data()
qr_code=QRcode()
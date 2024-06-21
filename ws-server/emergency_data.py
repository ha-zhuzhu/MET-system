# 多个文件公用的一些变量
import asyncio
import database

emerg_msg_template='[紧急情况]院楼：{building}。楼层：{floor}。房间：{room}。'
resp_msg_template='{doctor}已响应。'

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
  
emerg_data=Emergency_data()
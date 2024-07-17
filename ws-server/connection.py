# device和user的connections
import asyncio
import websockets

class Device_connections():
    """设备连接"""
    def __init__(self):
        self.id_to_connection={}
        self.id_to_connection_lock=asyncio.Lock()

    async def add_connection(self,device_id,websocket):
        """添加连接"""
        print('Add connection:',device_id,websocket)
        async with self.id_to_connection_lock:
            self.id_to_connection[device_id]=websocket

    async def remove_connection(self,websocket):
        """移除连接"""
        async with self.id_to_connection_lock:
            for key,value in self.id_to_connection.items():
                if value==websocket:
                    self.id_to_connection.pop(key)
                    break
    
    async def get_connection(self,device_id):
        """根据设备id获取连接"""
        async with self.id_to_connection_lock:
            return self.id_to_connection[device_id]
        
    async def get_device_id(self,websocket):
        """根据websocket获取设备id"""
        async with self.id_to_connection_lock:
            for key,value in self.id_to_connection.items():
                if value==websocket:
                    return key
            return None

    async def get_id_to_connection(self):
        """获取id_to_connection"""
        connections_copy=self.id_to_connection.copy()
        return connections_copy

    async def broadcast(self,message):
        """广播"""
        connections_copy=self.id_to_connection.copy()
        for key,value in connections_copy.items():
            try:
                await value.send(message)
            except websockets.ConnectionClosed:
                pass
        
        


class User_connections():
    """用户连接"""
    def __init__(self):
        # 一个user可能有多个连接
        self.connections=set()
        self.id_to_connections={}
        self.connections_lock=asyncio.Lock()
        self.id_to_connections_lock=asyncio.Lock()

    async def add_connection(self,websocket):
        """添加连接"""
        async with self.connections_lock:
            self.connections.add(websocket)

    async def remove_connection(self,websocket):
        """移除连接"""
        user_id=None
        async with self.connections_lock:
            self.connections.remove(websocket)
        async with self.id_to_connections_lock:
            for key,value in self.id_to_connections.items():
                if websocket in value:
                    user_id=key
                    value.remove(websocket)
                    if len(value)==0:
                        self.id_to_connections.pop(key)
                    break
        return user_id
        
    async def broadcast(self,message):
        """广播"""
        connections_copy=self.connections.copy()
        for websocket in connections_copy:
            try:
                await websocket.send(message)
            except websockets.ConnectionClosed:
                pass

    async def add_id_connection(self,user_id,websocket):
        """添加id2connection连接"""
        async with self.id_to_connections_lock:
            if user_id not in self.id_to_connections.keys():
                self.id_to_connections[user_id]=set()
                self.id_to_connections[user_id].add(websocket)
            else:
                self.id_to_connections[user_id].add(websocket)
    

    async def check_id_online(self,user_id):
        """检查id是否在线"""
        async with self.id_to_connections_lock:
            return user_id in self.id_to_connections.keys()


    # 一般不会定向发送消息给某个用户，所以不需要这个
    # async def add_connection(self,user_id,websocket):
    #     """添加连接"""
    #     async with self.id_to_connections_lock:
    #         if user_id not in self.id_to_connections.keys():
    #             self.id_to_connections[user_id]=[websocket]
    #         else:
    #             self.id_to_connections[user_id].append(websocket)

    # async def remove_connection(self,user_id,websocket):
    #     """移除连接"""
    #     async with self.id_to_connections_lock:
    #         if user_id in self.id_to_connections.keys():
    #             self.id_to_connections[user_id].remove(websocket)
    #             if len(self.id_to_connections[user_id])==0:
    #                 self.id_to_connections.pop(user_id)


device=Device_connections()
user=User_connections()

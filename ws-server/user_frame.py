# 发送给user的各种通信帧
import asyncio
import websockets
import json
import time
import connection


async def map_update(icon_relative_path,icon_data,map_source,message_list):
    """给所有前端发送地图更新"""
    frame=json.dumps(
        {'type':'map_update',
         'source_id':1,
         'destination_id': 0, 
         'timestamp':int(time.time()),
            'data':{'status':1,
                    'map_addr':icon_relative_path,
                    'map_data':icon_data,
                    'map_source':map_source,
                    'message':message_list
                    },
        })
    await connection.user.broadcast(frame)

async def register_response(websocket,status):
    """发送注册响应"""
    frame=json.dumps(
        {'type':'register_response',
         'source_id':1,
         'destination_id': -1, 
         'timestamp':int(time.time()),
            'data':{'status':status
                    },
        })
    await websocket.send(frame)

async def login_response(websocket,user_id,status,page_type,token,name):
    """发送登录响应"""
    frame=json.dumps(
        {'type':'login_response',
         'source_id':1,
         'destination_id': user_id, 
         'timestamp':int(time.time()),
            'data':{'status':status,
                    'page_type':page_type,
                    'token':token,
                    'user_id':user_id,
                    'name':name
                    },
        })
    await websocket.send(frame)

async def request_response(websocket,user_id,status,log=''):
    """发送请求响应"""
    frame=json.dumps(
        {'type':'request_response',
         'source_id':1,
         'destination_id': user_id, 
         'timestamp':int(time.time()),
            'data':{'log':log,
                    'status':status
                    },
        })
    await websocket.send(frame)
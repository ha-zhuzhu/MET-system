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
    
# async def button_alarmed(websocket,device_id,device_status,status,log=''):
#     """发送请求响应"""
#     frame=json.dumps(
#         {'type':'button_alarmed',
#          'source_id':1,
#          'destination_id': device_id, 
#          'timestamp':int(time.time()),
#             'data':{'log':log,
#                     'device_status':device_status,
#                     'status':status
#                     },
#         })
#     await websocket.send(frame)

async def path_update(start_node_id,end_node_id,path_weight, path_length,path_data):
    """广播路径更新"""
    frame=json.dumps(
        {'type':'path_update',
         'source_id':1,
         'destination_id': 0, 
         'timestamp':int(time.time()),
            'data':{'start_node_id':start_node_id,
                    'end_node_id':end_node_id,
                    'path_weight':path_weight, 
                    'path_length': path_length,
                    'path_data':path_data
                    },
        })
    await connection.user.broadcast(frame)

async def location_update(websocket,user_id,x,y,z):
    """发送请求位置响应"""
    frame=json.dumps(
        {'type':'location_update',
         'source_id':1,
         'destination_id': user_id, 
         'timestamp':int(time.time()),
            'data':{'x':x,
                    'y':y,
                    'z':z
                    },
        })
    await websocket.send(frame)
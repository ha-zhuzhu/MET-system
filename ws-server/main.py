#!/usr/bin/env python

import asyncio
import websockets
import binascii
import time
import sqlite3
import json
from enum import Enum

# 本机ID
LOCAL_ID = 1
DATABASE = 'device'
connected_dict = {}
ICON_PATH="../../web_front/tiles/geojson/men-zhen-lou/f1/men-zhen-lou_f1_status.geojson"


class status(Enum):
    """设备状态"""
    offline = 0
    reset = 1
    alarm = 2
    response = 3

async def calculate_crc(data):
    # 将数据转换为字节流
    data_bytes = data.encode('utf-8')
    # 计算CRC-32
    crc32_value = binascii.crc32(data_bytes)
    # 返回CRC值
    return crc32_value


async def make_frame(type, destination_id, data):
    """生成帧"""
    timestamp = int(time.time())
    crc=await calculate_crc(type + str(timestamp))
    frame_dict = {
        "type": type,
        "source_id": LOCAL_ID,
        "destination_id": destination_id,
        "timestamp": timestamp,
        "data": data,
        "crc": crc,
    }
    return json.dumps(frame_dict)


async def send_frame(websocket, frame, timeout=60, retry=3):
    """发送帧"""
    success = False
    while (not success and retry > 0):
        await websocket.send(frame)
        print('Sent:', frame)
        try:
            recv_frame = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            print('Received:', recv_frame)
            recv_frame_dict = json.loads(recv_frame)
            if recv_frame_dict['data']['type'] == 'ack':
                success = True
        except asyncio.TimeoutError:
            print('Timeout')
        except Exception as e:
            print(e)
        finally:
            retry -= 1

    if not success:
        print('Send frame failed')


async def response(websocket, destination_id, type, message=None):
    """发送响应帧"""
    data = {
        "type": type
    }
    if message:
        data['message'] = message
    frame = await make_frame('response', destination_id, data)
    if type=='ack' or type=='err':
        # 不需要等待对方的响应
        await websocket.send(frame)
    else:
        await send_frame(websocket, frame)


async def alarm(websocket, destination_id, data):
    """发送报警帧"""
    frame = await make_frame('alarm', destination_id, data)
    await send_frame(websocket, frame)


async def config(websocket, destination_id, data):
    """发送配置帧"""
    frame = await make_frame('config', destination_id, data)
    await send_frame(websocket, frame)


async def check_frame(websocket, frame_dict):
    """检查frame结构并作出响应"""
    # 检查frame结构
    if 'type' not in frame_dict or 'destination_id' not in frame_dict or 'timestamp' not in frame_dict or 'data' not in frame_dict or 'crc' not in frame_dict:
        if 'source_id' not in frame_dict:
            await response(websocket, 0, 'err', 'frame structure error')
        else:
            await response(websocket, frame_dict['source_id'], 'err', 'frame structure error')


async def check_crc(websocket, frame_dict):
    """检查crc并作出响应"""
    # 计算CRC
    crc32_value = await calculate_crc(frame_dict['type'] + str(frame_dict['timestamp']))
    # 检查CRC
    if crc32_value != int(frame_dict['crc']):
        await response(websocket, frame_dict['source_id'], 'err')
    else:
        await response(websocket, frame_dict['source_id'], 'ack')


def find_location(id):
    """找到设备位置"""
    location_dict = {}
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # 选择 id 记录中的 building,floor,room 字段
    select_query = "SELECT building,floor,room FROM device WHERE id = ?"
    # 执行查询操作
    cursor.execute(select_query, (id,))
    # 获取查询结果
    location = cursor.fetchone()
    # 关闭游标和数据库连接
    cursor.close()
    conn.close()
    location_dict['building'] = location[0]
    location_dict['floor'] = location[1]
    location_dict['room'] = location[2]
    return location_dict


async def register_handler(websocket, frame_dict):
    """处理接收到的注册帧"""
    data = frame_dict['data']
    # 检查注册数据
    if "type" not in data or "mac" not in data:
        await response(websocket, frame_dict['source_id'], 'err', 'register data error')
    if data['type'] not in ['alarm', 'aed', 'met', 'doc']:
        await response(websocket, frame_dict['source_id'], 'err', 'device type error')

    # 更新数据库
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # 搜索ID的最大值
    select_query = "SELECT MAX(id) FROM device"
    cursor.execute(select_query)
    max_id = cursor.fetchone()[0]
    new_id = max_id + 1  # 新设备的ID
    insert_query = "INSERT INTO device (id,type,mac,status) VALUES (?,?,?,?)"
    cursor.execute(insert_query, (new_id, data['type'], data['mac'], 1))
    conn.commit()
    cursor.close()
    conn.close()

    # 发送配置帧
    await config(websocket, frame_dict['source_id'], {'id': new_id})
    # 更新connected_dict
    connected_dict[new_id] = websocket
    # TODO: 如果同时有多个设备用同一个id注册，会很麻烦
    del connected_dict[frame_dict['source_id']]


async def alarm_handler(websocket, frame_dict):
    """处理接收到的报警帧"""
    data = frame_dict['data']
    # 检查报警数据
    if "type" not in data or "timestamp" not in data or "location" not in data:
        await response(websocket, frame_dict['source_id'], 'err', 'alarm data error')

    if data['location'] == '':
        location_dict = find_location(frame_dict['source_id'])
        data[
            'location'] = f'院楼：{location_dict["building"]}\n楼层：{location_dict["floor"]}\n房间：{location_dict["room"]}'

    # 改地图
    with open(ICON_PATH,'r') as file:
        icon_data=json.load(file)
    icon_data['features'][2]['properties']['status']="3"
    with open(ICON_PATH,'w') as file:
        json.dump(icon_data,file,indent=4)
    
    # 广播报警信息
    for id, ws in connected_dict.items():
        if id != frame_dict['source_id']:
            await alarm(ws, id, data)

async def config_handler(websocket, frame_dict):
    """处理接收到的配置帧"""
    data = frame_dict['data']
    # 更新状态
    if "status" in data:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        update_query = "UPDATE device SET status = ? WHERE id = ?"
        cursor.execute(update_query, (data['status'], frame_dict['source_id']))
        conn.commit()
        cursor.close()
        conn.close()
    # 更新id
    if "id" in data:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        update_query = "UPDATE device SET id = ? WHERE id = ?"
        cursor.execute(update_query, (data['id'], frame_dict['source_id']))
        conn.commit()
        cursor.close()
        conn.close()

async def handler(websocket):
    async for frame in websocket:
        print("Received:", frame)
        frame_dict = json.loads(frame)

        # 检查并应答
        await check_frame(websocket, frame_dict)
        await check_crc(websocket, frame_dict)
        connected_dict[frame_dict['source_id']] = websocket

        if frame_dict['type'] == 'register':
            await register_handler(websocket, frame_dict)
        elif frame_dict['type'] == 'alarm':
            await alarm_handler(websocket, frame_dict)
        elif frame_dict['type'] == 'config':
            await config_handler(websocket, frame_dict)


async def main():
    # 监听所有接口
    async with websockets.serve(handler, "", 8765):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())

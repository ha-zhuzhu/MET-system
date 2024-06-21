# 模仿报警器的行为
import asyncio
import websockets
import time
import binascii
import json


SERVER_ID=1

def calculate_crc(data):
    # 将数据转换为字节流
    data_bytes = data.encode('utf-8')
    # 计算CRC-32
    crc32_value = binascii.crc32(data_bytes)
    # 返回CRC值
    return crc32_value

def make_frame(type,device_id, destination_id, data):
    """生成帧"""
    timestamp = int(time.time())
    frame_dict = {
        "type": type,
        "source_id": device_id,
        "destination_id": destination_id,
        "timestamp": timestamp,
        "data": data,
        "crc": calculate_crc(type + str(timestamp)),
    }
    return json.dumps(frame_dict)

def ack(websocket, device_id,destination_id):
    """发送ack帧"""
    data_dict={
        "type":"ack",
    }
    frame= make_frame('response',device_id,destination_id,data_dict)
    websocket.send(frame)
    print('Sent:', frame)

def register():
    """发送注册帧"""
    data_dict={
        "type":"alarm",
        "mac":"00:00:00:00:00:00",
    }
    frame= make_frame('register',0,SERVER_ID,data_dict)
    with websockets.connect("ws://localhost:8765") as websocket:
        websocket.send(frame)
        print('Sent:', frame)
#         重复接收并输出服务器发送的消息
        while True:
            recv_frame = websocket.recv()
            print("received:",recv_frame)
            time.sleep(1)
            recv_frame_dict= json.loads(recv_frame)
            if recv_frame_dict['type']!='response':
                ack(websocket,0,SERVER_ID)

def alarm(device_id):
    """发送报警帧"""
    data_dict={
        "type":"alarm",
        "timestamp":int(time.time()),
        "location":"",
    }
    frame= make_frame('alarm',device_id,SERVER_ID,data_dict)
    with websockets.connect("ws://localhost:8008") as websocket:
        websocket.send(frame)
        print('Sent:', frame)
        while True:
            # 这是不好的写法
            recv_frame = websocket.recv()
            print("received:",recv_frame)
            time.sleep(1)


async def alarm_and_connect(device_id):
    """发送报警帧并保持连接"""
    data_dict={
        "type":"alarm",
        "timestamp":int(time.time()),
        "location":"",
    }

    frame= make_frame('alarm',device_id,SERVER_ID,data_dict)
    async for websocket in websockets.connect("ws://localhost:8008"):
        await websocket.send(frame)
        print('Sent:', frame)
        try:
            async for frame in websocket:
                print("Received:", frame)
        except websockets.ConnectionClosed:
            print('Connection closed')
            continue

# asyncio.run(alarm_and_connect())
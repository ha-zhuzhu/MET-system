# 模仿报警器的行为
import asyncio
from websockets.sync.client import connect
import time
import binascii
import json

LOCAL_ID=2
SERVER_ID=1

def calculate_crc(data):
    # 将数据转换为字节流
    data_bytes = data.encode('utf-8')
    # 计算CRC-32
    crc32_value = binascii.crc32(data_bytes)
    # 返回CRC值
    return crc32_value

def make_frame(type, destination_id, data):
    """生成帧"""
    timestamp = int(time.time())
    frame_dict = {
        "type": type,
        "source_id": LOCAL_ID,
        "destination_id": destination_id,
        "timestamp": timestamp,
        "data": data,
        "crc": calculate_crc(type + str(timestamp)),
    }
    return json.dumps(frame_dict)

def ack(websocket, destination_id):
    """发送ack帧"""
    data_dict={
        "type":"ack",
    }
    frame= make_frame('response',destination_id,data_dict)
    websocket.send(frame)
    print('Sent:', frame)

def register():
    """发送注册帧"""
    data_dict={
        "type":"alarm",
        "mac":"00:00:00:00:00:00",
    }
    frame= make_frame('register',SERVER_ID,data_dict)
    with connect("ws://localhost:8765") as websocket:
        websocket.send(frame)
        print('Sent:', frame)
#         重复接收并输出服务器发送的消息
        while True:
            recv_frame = websocket.recv()
            print("received:",recv_frame)
            time.sleep(1)
            recv_frame_dict= json.loads(recv_frame)
            if recv_frame_dict['type']!='response':
                ack(websocket,SERVER_ID)

def alarm():
    """发送报警帧"""
    data_dict={
        "type":"alarm",
        "timestamp":int(time.time()),
        "location":"room 101",
    }
    frame= make_frame('alarm',SERVER_ID,data_dict)
    with connect("ws://localhost:8765") as websocket:
        websocket.send(frame)
        print('Sent:', frame)
        while True:
            recv_frame = websocket.recv()
            print("received:",recv_frame)
            time.sleep(1)


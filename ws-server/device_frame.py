# 发给硬件的各种通信帧
import asyncio
import json
import time
import binascii
import logging
import connection

# 本机ID
LOCAL_ID = 1

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
            print('device send frame timeout')
            logging.debug('device send frame timeout')
        except Exception as e:
            print(e)
        finally:
            retry -= 1

    if not success:
        print('Send frame failed')
        logging.debug('device send frame timeout')


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

async def qrcode_broadcast(qrcode_str):
    """广播二维码"""
    data={
        "qrcode":{
            "width":132,
            "height":132,
            "data":qrcode_str
        }
    }
    id_to_connection=await connection.device.get_id_to_connection()
    for device_id,websocket in id_to_connection.items():
        frame = await make_frame('config', device_id, data)
        await send_frame(websocket, frame)
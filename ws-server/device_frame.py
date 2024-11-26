# 发给硬件的各种通信帧
import asyncio
import json
import time
import binascii
import logging

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
    await websocket.send(frame)
<<<<<<< HEAD
    logging.info('Sent:{}'.format(frame))
    # print('Sent:', frame)

    # while (not success and retry > 0):
    #     await websocket.send(frame)
    #     print('Sent:', frame)
    #     try:
    #         # TODO：和整个系统一直接收帧的逻辑有些矛盾
    #         recv_frame = await asyncio.wait_for(websocket.recv(), timeout=timeout)
    #         print('Received:', recv_frame)
    #         recv_frame_dict = json.loads(recv_frame)
    #         if recv_frame_dict['data']['type'] == 'ack':
    #             success = True
    #     except asyncio.TimeoutError:
    #         print('device send frame timeout')
    #         logging.debug('device send frame timeout')
    #     except Exception as e:
    #         print(e)
    #     finally:
    #         retry -= 1

=======
    print('Sent:', frame)
    # while (not success and retry > 0):
    #     await websocket.send(frame)
    #     print('Sent:', frame)
    #     try:
    #         # TODO：和整个系统一直接收帧的逻辑有些矛盾
    #         recv_frame = await asyncio.wait_for(websocket.recv(), timeout=timeout)
    #         print('Received:', recv_frame)
    #         recv_frame_dict = json.loads(recv_frame)
    #         if recv_frame_dict['data']['type'] == 'ack':
    #             success = True
    #     except asyncio.TimeoutError:
    #         print('device send frame timeout')
    #         logging.debug('device send frame timeout')
    #     except Exception as e:
    #         print(e)
    #     finally:
    #         retry -= 1

>>>>>>> 8fe26a4b4fdead9e5ca165b0089f41592f8ba15b
    # if not success:
    #     print('Send frame failed')
    #     logging.debug('device send frame timeout')
    #     return 0
    return 1


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
        ret=1
    else:
        ret=await send_frame(websocket, frame)
    return ret


async def alarm(websocket, destination_id, data):
    """发送报警帧"""
    frame = await make_frame('alarm', destination_id, data)
    return await send_frame(websocket, frame)


async def config(websocket, destination_id, data):
    """发送配置帧"""
    frame = await make_frame('config', destination_id, data)
    return await send_frame(websocket, frame)

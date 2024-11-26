# 与硬件设备通信相关
import asyncio
from common_data import *
import database
import map_data
import status
import user_frame
from connection import device_connections
import logging
import device_frame
from A7670C import a7670c


async def check_frame(websocket, frame_dict):
    """检查frame结构并作出响应"""
    # 检查frame结构
    if 'type' not in frame_dict or 'destination_id' not in frame_dict or 'timestamp' not in frame_dict or 'data' not in frame_dict or 'crc' not in frame_dict:
        if 'source_id' not in frame_dict:
            await device_frame.response(websocket, 0, 'err', 'frame structure error')
        else:
            await device_frame.response(websocket, frame_dict['source_id'], 'err', 'frame structure error')

async def check_crc(websocket, frame_dict):
    """检查crc并作出响应"""
    # 计算CRC
    crc32_value = await device_frame.calculate_crc(frame_dict['type'] + str(frame_dict['timestamp']))
    # 检查CRC
    if crc32_value != int(frame_dict['crc']):
        await device_frame.response(websocket, frame_dict['source_id'], 'err')
    else:
        await device_frame.response(websocket, frame_dict['source_id'], 'ack')


async def register_handler(websocket, frame_dict):
    """处理接收到的注册帧"""
    data = frame_dict['data']
    # 检查注册数据
    if "type" not in data or "mac" not in data:
        await device_frame.response(websocket, frame_dict['source_id'], 'err', 'register data error')
    if data['type'] not in ['alarm', 'aed', 'met', 'doc']:
        await device_frame.response(websocket, frame_dict['source_id'], 'err', 'device type error')
    # 更新数据库
    new_id = await database.add_new_device(data['type'], data['mac'], status.button.standby.value)
    logging.info("Register new device {} with type {} and mac {}".format(new_id, data['type'], data['mac']))
    #connection 相关数据也应该修改
    device_connections.update_id(frame_dict['source_id'],new_id)
    # 发送配置帧
    await device_frame.config(websocket, frame_dict['source_id'], {'id': new_id})
    frame_dict['source_id'] = new_id


async def alarm_handler(websocket, frame_dict):
    """处理接收到的报警帧"""
    global emerg_device_to_user
    global emerg_user_to_device
    global msg_dict
    global online_users
    data = frame_dict['data']
    # 检查报警数据
    if websocket!=None:
        # 来自websocket
        if "type" not in data or "timestamp" not in data or "location" not in data:
            await device_frame.response(websocket, frame_dict['source_id'], 'err', 'alarm data error')
        device_id=frame_dict['source_id']
    else:
        # 来自BC25
        device_id=int(f"{frame_dict['params']['alarm_id']}")
    
    if await emerg_data.is_set_in_alarm(device_id):
        # 已经报过警了
        return 0    

    # 这是一个新的报警
    # 更新 emerg_data
    await emerg_data.add_new_alarm(device_id)

    # 改地图
    map_data_dict={}    # 所有需要修改的地图相对路径，和数据
    
    # 修改设备状态
    icon_relative_path,icon_data=await map_data.update_device_status(device_id,status.button.alarm.value)
<<<<<<< HEAD
    if icon_relative_path=='':
        # 设备位置信息不完整
        logging.error(f'无法更新设备{device_id}的状态，因为设备位置信息不完整')
    else:
        map_data_dict[icon_relative_path]=icon_data
=======
    print(icon_data)
    map_data_dict[icon_relative_path]=icon_data
>>>>>>> 8fe26a4b4fdead9e5ca165b0089f41592f8ba15b
    # 修改用户状态
    user_id_list=await emerg_data.get_user_id(device_id)
    for user_id in user_id_list:
        icon_relative_path,icon_data=await map_data.update_user_status(user_id,status.doctor.called.value)
        map_data_dict[icon_relative_path]=icon_data

    # 通知所有前端
    for icon_relative_path,icon_data in map_data_dict.items():
        map_source=icon_relative_path.split('/')[-1].split('.')[0]
        await user_frame.map_update(icon_relative_path,icon_data,map_source,await emerg_data.get_message_list())

    # 发送短信
    # 获取按钮位置
    location_dict=await database.get_device_location(device_id)
    if location_dict['building'] is None or location_dict['floor'] is None or location_dict['room'] is None:
        logging.error(f'数据库中设备{device_id}的位置信息不完整')
    if location_dict['building'] is None:
        location_dict['building'] = '未知'
    if location_dict['floor'] is None:
        location_dict['floor'] = '未知'
    if location_dict['room'] is None:
        location_dict['room'] = '未知'
    msg=f'设备{device_id}发生报警，位置：【{location_dict["building"]}】【{location_dict["floor"]}楼】【{location_dict["room"]}房间】'
    await a7670c.message('8613438233066',msg)
    # 拨打电话
    call_msg=f'发生报警，{location_dict["building"]}{location_dict["floor"]}楼{location_dict["room"]}房间{location_dict["building"]}{location_dict["floor"]}楼{location_dict["room"]}房间{location_dict["building"]}{location_dict["floor"]}楼{location_dict["room"]}房间'
    await a7670c.call('13438233066',call_msg)

async def config_handler(websocket, frame_dict):
    """处理接收到的配置帧"""
    data = frame_dict['data']
    # 更新状态
    if "status" in data:
        # 更新数据库
        await database.set_device_status(frame_dict['source_id'], data['status'])
        # 更新地图
        await map_data.update_device_status(frame_dict['source_id'],data['status'])
    # 更新id
    # TODO: 还需要检验id；更新所有和id相关的数据结构
    if "id" in data:
        # 很复杂，暂时不做
        # print('Not implemented yet')
        pass

async def qrcode_update(websocket,device_id):
    """更新二维码"""
    data_for_device=await qr_code.get_data_for_device()
    latest_version=await qr_code.get_latest_version()
    # 应该对比二维码版本，决定更新  
    # if latest_version==await database.get_qrcode_version(device_id):
    #     # 二维码版本相同
    #     return 0
    try:
        ret=await device_frame.config(websocket,device_id,{"qrcode":"https://u.wechat.com/EL_WfiYtGUjkmiqeMwssvrE?s=2"})
    except:
        await device_connections.remove_connection(device_id)
        logging.debug('Config qrcode failed. Device {} not connected'.format(device_id))
        ret=0
    if ret==1:
        await database.set_device_qrcode_version(device_id,latest_version)
    return ret


async def handler(websocket, frame_dict,connection_added):
    await check_frame(websocket, frame_dict)
    await check_crc(websocket, frame_dict)
    # TODO：上线处理，还是让设备发config上线好了，不要在这里就上线
    if connection_added==0:
        logging.info("Add connection for device {}".format(frame_dict['source_id']))
        await device_connections.add_connection(frame_dict['source_id'],websocket)
        # connection_added=1
    if frame_dict['type'] == 'register':
        await register_handler(websocket, frame_dict)
    elif frame_dict['type'] == 'alarm':
        await alarm_handler(websocket, frame_dict)
    elif frame_dict['type'] == 'config':
        await config_handler(websocket, frame_dict)
    # 更新二维码，暂时这样写，在第一次连接时更新
    if connection_added==0:
        await qrcode_update(websocket,frame_dict['source_id'])
        connection_added=1
    return connection_added

async def offline_handler(websocket):
    """掉线处理"""
    device_id=await device_connections.get_device_id(websocket)
    if device_id:
        # 修改地图
        map_data_dict={}    # 所有需要修改的地图相对路径，和数据
        # 修改设备状态
        icon_relative_path,icon_data=await map_data.update_device_status(device_id,status.button.offline.value)
        try:
            map_data_dict[icon_relative_path]=icon_data
            # 修改emerg_data
            if await emerg_data.is_set_in_alarm(device_id):
                # 已经报过警了
                await emerg_data.remove_alarm(device_id)
            # 通知所有前端
            for icon_relative_path,icon_data in map_data_dict.items():
                map_source=icon_relative_path.split('/')[-1].split('.')[0]
                await user_frame.map_update(icon_relative_path,icon_data,map_source,await emerg_data.get_message_list())
        except:
            # 可能设备位置信息不完整
            logging.error('Device {} offline mapupdate failed'.format(device_id))

        # 从connection中删除
        await device_connections.remove_connection(websocket)
        logging.info('Device {} offline'.format(device_id))
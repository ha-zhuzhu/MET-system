# user通信相关处理
import asyncio
import websockets
import json
import time
import connection
import hashlib
import database
import user_frame
# TODO: 进一步分为device_frame
import device
import map_data
import status
from emergency_data import *
import logging

MET_ID=2

async def register_handler(websocket,frame_dict):
    """注册帧处理"""
    data=frame_dict['data']
    #对注册的username进行验证,判断是否能注册新账号
    password_md5 = hashlib.md5()
    password_md5.update(data['password'].encode(encoding='utf-8'))
    token_md5 = hashlib.md5()
    token=data['username']+data['password']
    token_md5.update(token.encode(encoding='utf-8'))
    # 数据库中添加新用户
    result=await database.add_new_user(data['username'],password_md5.hexdigest(),data['email'],data['name'],data['tel'],data['role'],token_md5.hexdigest())
    # 发送回应
    await user_frame.register_response(websocket,result)

async def login_handler(websocket,frame_dict):
    """登录帧处理"""
    data=frame_dict['data']
    role=''
    token=''
    password_md5 = hashlib.md5()
    password_md5.update(data['password'].encode(encoding='utf-8'))

    # 找到user表中，username列为uname的行，取出password,role,token,user_id,name
    result=await database.user_login(data['username'])
    if result is not None:
        if result[0] == password_md5.hexdigest():
            # 登陆成功
            # 暂时不根据时间更新token，直接返回
            await user_frame.login_response(websocket,result[3],1,result[1],result[2],result[4])
            await connection.user.add_id_connection(result[3],websocket)
            # 如果用户状态为offline，则改为standby
            if result[5]==status.doctor.offline.value:
                # 不用修改地图 地图上没有doctor
                # map_data_dict={}
                # icon_relative_path,icon_data=await map_data.update_user_status(result[3],status.doctor.standby.value)
                # map_data_dict={icon_relative_path:icon_data}
                # 修改数据库
                await database.set_user_status(result[3],status.doctor.standby.value)
                # # 通知所有前端
                # for icon_relative_path,icon_data in map_data_dict.items():
                #     map_source=icon_relative_path.split('/')[-1].split('.')[0]
                #     await user_frame.map_update(icon_relative_path,icon_data,map_source,await emerg_data.get_message_list())
    else:
        await user_frame.login_response(websocket,0,0,'','','')

async def token_login_handler(websocket,frame_dict):
    """token登录帧处理"""
    user_id=frame_dict['source_id']
    data=frame_dict['data']
    # 找到token,role,name,status
    result=await database.user_token_login(user_id)
    if result is not None:
        if result[0] == data['token']:
            # 登陆成功
            await user_frame.login_response(websocket,user_id,1,result[1],data['token'],result[2])
            # 如果用户状态为offline，则改为standby
            if result[3]==status.doctor.offline.value:
                # 不用修改地图 地图上没有doctor
                # map_data_dict={}
                # icon_relative_path,icon_data=await map_data.update_user_status(user_id,status.doctor.standby.value)
                # map_data_dict={icon_relative_path:icon_data}
                # 修改数据库
                await database.set_user_status(user_id,status.doctor.standby.value)
                await connection.user.add_id_connection(user_id,websocket)
                # 通知所有前端
                # for icon_relative_path,icon_data in map_data_dict.items():
                #     map_source=icon_relative_path.split('/')[-1].split('.')[0]
                #     await user_frame.map_update(icon_relative_path,icon_data,map_source,await emerg_data.get_message_list())
    else:
        await user_frame.login_response(websocket,-1,0,'','','')

async def request_handler(websocket,frame_dict):
    """请求帧处理"""
    user_id=frame_dict['source_id']
    map_data_dict={}    # 所有需要修改的地图相对路径，和数据

    # 检查id-token对是否正确
    if not await database.check_id_to_token(user_id,frame_dict['data']['token']):
        # token验证失败
        await user_frame.request_response(websocket,user_id,0,'token invalid')
        return
    
    if user_id==MET_ID:
        # 请求帧来自MET中心
        if 'user_id' in frame_dict['data']:
            # 修改用户状态，只能改为offline, standby
            user_id=frame_dict['data']['user_id']
            user_status=frame_dict['data']['user_status']
            if user_status!=status.button.offline.value and user_status!=status.button.standby.value:
                # 不是offline或standby
                await user_frame.request_response(websocket,user_id,0,'user_status invalid')
                print('user_status:',user_status,'not recognized')
                logging.debug('user_status:{} not recognized'.format(user_status))
            else:
                # 修改地图
                icon_relative_path,icon_data=await map_data.update_user_status(user_id,user_status)
                map_data_dict[icon_relative_path]=icon_data
                # 修改数据库
                await database.set_user_status(user_id,user_status)
                # 修改 emerg_data
                await emerg_data.remove_all_response(user_id)
                # 返回 request_response
                await user_frame.request_response(websocket,user_id,1)

        if 'device_id' in frame_dict['data']:
            # 修改设备状态
            device_id=frame_dict['data']['device_id']
            device_status=frame_dict['data']['device_status']
            # 发送配置帧
            try:
                await device.config(await connection.device.get_connection(device_id),device_id,{'status':device_status})                      
            except:
                await connection.device.remove_connection(device_id)
                print('device {} not connected'.format(device_id))
                logging.debug('device {} not connected'.format(device_id))
                # 修改地图
                icon_relative_path,icon_data=await map_data.update_device_status(device_id,status.button.offline.value)
                map_data_dict[icon_relative_path]=icon_data

            # 修改数据库
            await database.set_device_status(device_id,device_status)

            # 修改地图
            icon_relative_path,icon_data=await map_data.update_device_status(device_id,device_status)
            map_data_dict[icon_relative_path]=icon_data

            if device_status==status.button.offline.value or device_status==status.button.standby.value:
                # 警报已解除
                await emerg_data.remove_alarm(device_id)

            # 若为报警
            if device_status==status.button.alarm.value:
                if await emerg_data.is_set_in_alarm(device_id)==0:
                    # 新的报警
                    await emerg_data.add_new_alarm(device_id)
                    # 修改地图
                    icon_relative_path,icon_data=await map_data.update_device_status(device_id,status.button.alarm.value)
                    map_data_dict[icon_relative_path]=icon_data
                    # 修改用户状态
                    user_id_list=await emerg_data.get_user_id(device_id)
                    for user_id in user_id_list:
                        icon_relative_path,icon_data=await map_data.update_user_status(user_id,status.doctor.called.value)
                        map_data_dict[icon_relative_path]=icon_data
                else:
                    # 已经报过警了
                    pass
            
            # 若有响应，则设备状态改为响应
            if device_status==status.button.doc_response.value:
                try:
                    await device.response(await connection.device.get_connection(device_id),device_id,'doc')
                except:
                    await connection.device.remove_connection(device_id)
                    print('device {} not connected'.format(device_id))
                    logging.debug('device {} not connected'.format(device_id))
                    # 修改地图
                    icon_relative_path,icon_data=await map_data.update_device_status(device_id,status.button.offline.value)
                    map_data_dict[icon_relative_path]=icon_data

            if device_status==status.button.aed_response.value:
                try:
                    await device.response(await connection.device.get_connection(device_id),device_id,'aed')
                except:
                    await connection.device.remove_connection(device_id)
                    print('device {} not connected'.format(device_id))
                    logging.debug('device {} not connected'.format(device_id))
                    # 修改地图
                    icon_relative_path,icon_data=await map_data.update_device_status(device_id,status.button.offline.value)
                    map_data_dict[icon_relative_path]=icon_data
            
            # 返回 request_response
            await user_frame.request_response(websocket,user_id,1)
    else:
        # 请求帧来自医生
        device_id=frame_dict['data']['device_id']
        device_status=frame_dict['data']['device_status']
        if not await emerg_data.check_user_device(user_id,device_id):
            # 医生不负责该设备
            await user_frame.request_response(websocket,user_id,0,'doctor not responsible for this device')
        else:
            # 医生负责该设备
            # 查询名字
            name=await database.get_user_name(user_id)
            if name is None:
                name='未名'
                print('user_id:',user_id,'name not found')
                logging.info('user_id:{} name not found'.format(user_id))
            if device_status==status.button.doc_response.value:
                # 医生试图响应报警
                # 修改emerg_data
                await emerg_data.add_response(device_id,user_id)
                # 修改地图中医生
                icon_relative_path,icon_data=await map_data.update_user_status(user_id,status.doctor.response.value)
                map_data_dict[icon_relative_path]=icon_data
                # 修改地图中设备
                icon_relative_path,icon_data=await map_data.update_device_status(device_id,status.button.doc_response.value)
                map_data_dict[icon_relative_path]=icon_data
                # 修改数据库
                await database.set_user_status(user_id,status.doctor.response.value)
                # 通知设备
                try:
                    await device.response(await connection.device.get_connection(device_id),device_id,'doc')
                except:
                    await connection.device.remove_connection(device_id)
                    print('device {} not connected'.format(device_id))
                    logging.debug('device {} not connected'.format(device_id))
                    # 修改地图
                    icon_relative_path,icon_data=await map_data.update_device_status(device_id,status.button.offline.value)
                    map_data_dict[icon_relative_path]=icon_data
                # 返回 request_response
                await user_frame.request_response(websocket,user_id,1)
                
            elif device_status==status.button.alarm.value:
                # 医生试图取消响应
                # 修改emerg_data
                await emerg_data.remove_response(device_id,user_id)
                # 修改地图中医生
                icon_relative_path,icon_data=await map_data.update_user_status(user_id,status.doctor.called.value)
                map_data_dict[icon_relative_path]=icon_data
                # 修改数据库
                await database.set_user_status(user_id,status.doctor.called.value)
                if not await emerg_data.check_responsed(device_id):
                    # 若设备已经无人响应
                    # TODO：没有考虑AED的响应，只考虑了人
                    # 通知设备
                    try:
                        await device.config(await connection.device.get_connection(device_id),device_id,{'status':status.button.alarm.value})
                    except:
                        await connection.device.remove_connection(device_id)
                        print('device {} not connected'.format(device_id))
                        logging.debug('device {} not connected'.format(device_id))
                        # 修改地图
                        icon_relative_path,icon_data=await map_data.update_device_status(device_id,status.button.offline.value)
                        map_data_dict[icon_relative_path]=icon_data
                    # 修改数据库
                    await database.set_device_status(device_id,status.button.alarm.value)
                    # 修改地图
                    icon_relative_path,icon_data=await map_data.update_device_status(device_id,status.button.alarm.value)
                    map_data_dict[icon_relative_path]=icon_data
                # 返回 request_response
                await user_frame.request_response(websocket,user_id,1)
            else:
                # 不是医生响应报警，也不是医生取消响应
                await user_frame.request_response(websocket,user_id,0,'device_status invalid')
                print('device_status:',device_status,'not recognized')
                logging.info('device_status:{} not recognized'.format(device_status))
            
    # 通知所有前端
    for icon_relative_path,icon_data in map_data_dict.items():
        map_source=icon_relative_path.split('/')[-1].split('.')[0]
        await user_frame.map_update(icon_relative_path,icon_data,map_source,await emerg_data.get_message_list())


async def handler(websocket, frame_dict, connection_added):
    """前端信息处理"""
    # message recieved without token verify
    if connection_added == 0:
        await connection.user.add_connection(websocket)
        connection_added = 1
    if frame_dict['type'] == 'register':
        # 注册帧
        await register_handler(websocket,frame_dict)
    elif frame_dict['type'] == 'login':
        # 登录帧
        await login_handler(websocket,frame_dict)
    elif frame_dict['type'] == 'token_login':
        # token登录帧
        await token_login_handler(websocket,frame_dict)
    elif frame_dict['type'] == 'request':
        # 请求帧
        await request_handler(websocket,frame_dict)             
    else:
        # 未知信息帧
        await user_frame.request_response(websocket,frame_dict['source_id'],0,'frame type not recognized')

async def offline_handler(websocket):
    """掉线处理"""
    map_data_dict={}
    user_id=await connection.user.remove_connection(websocket)
    if user_id:
        # 修改地图
        icon_relative_path,icon_data=await map_data.update_user_status(user_id,status.doctor.offline.value)
        map_data_dict[icon_relative_path]=icon_data
        # 修改数据库
        await database.set_user_status(user_id,status.doctor.offline.value)
        # 就不修改 emerg_data 了
        # 通知所有前端
        for icon_relative_path,icon_data in map_data_dict.items():
            map_source=icon_relative_path.split('/')[-1].split('.')[0]
            await user_frame.map_update(icon_relative_path,icon_data,map_source,await emerg_data.get_message_list())
        print("User {} offline".format(user_id))
        logging.debug("User {} offline".format(user_id))

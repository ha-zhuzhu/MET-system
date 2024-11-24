# 操作地图数据
import asyncio
import database
import aiofile
import json
from config_loader import GlobalConfigManager
import logging


async def update_device_status(device_id,status):
    """更新设备状态"""
    config_loader = GlobalConfigManager.get_config_loader()
    icon_path_dict=await config_loader.get_icon_path_dict()
    location_dict=await database.get_device_location(device_id)
    icon_relative_path_dict=await config_loader.get_icon_relative_path_dict()
    # 如果设备位置信息不完整，不更新
    print(location_dict)
    if location_dict['building_en'] is None or location_dict['floor'] is None:
        logging.error("device id {} has no building_en or floor in database".format(device_id))
        return
    icon_path=icon_path_dict[location_dict['building_en']][location_dict['floor']]
    icon_relative_path=icon_relative_path_dict[location_dict['building_en']][location_dict['floor']]
    
    async with aiofile.async_open(icon_path,'r') as file:
        icon_data=await file.read()
        icon_data=json.loads(icon_data)
        for feature in icon_data['features']:
            if 'device_id' in feature['properties'].keys():
                print(device_id)
                print(feature['properties']['device_id'])
                if feature['properties']['device_id']==device_id or feature['properties']['device_id']==str(device_id):
                    print('find')
                    feature['properties']['status']=status
    async with aiofile.async_open(icon_path,'w') as file:
        await file.write(json.dumps(icon_data,indent=4))
    return icon_relative_path,icon_data

async def update_user_status(user_id,status):
    """更新用户状态"""
    config_loader = GlobalConfigManager.get_config_loader()
    icon_path_dict=await config_loader.get_icon_path_dict()
    icon_relative_path_dict=await config_loader.get_icon_relative_path_dict()
    location_dict=await database.get_user_location(user_id)
    icon_path=icon_path_dict[location_dict['building_en']][location_dict['floor']]
    icon_relative_path=icon_relative_path_dict[location_dict['building_en']][location_dict['floor']]
    async with aiofile.async_open(icon_path,'r') as file:
        icon_data=await file.read()
        icon_data=json.loads(icon_data)
        for feature in icon_data['features']:
            if 'user_id' in feature['properties'].keys():
                if feature['properties']['user_id']==user_id:
                    feature['properties']['status']=status
    async with aiofile.async_open(icon_path,'w') as file:
        await file.write(json.dumps(icon_data,indent=4))
    return icon_relative_path,icon_data
    
async def update_status_by_database():
    """根据数据库更新所有设备和用户状态"""
    config_loader = GlobalConfigManager.get_config_loader()
    icon_path_dict=await config_loader.get_icon_path_dict()
    device_to_location_dict=await database.get_devices_location()
    user_to_location_dict=await database.get_users_location()
    device_to_status_dict=await database.get_devices_status()
    user_to_status_dict=await database.get_users_status()
    device_to_icon_path={}
    user_to_icon_path={}
    for device_id,location_dict in device_to_location_dict.items():
        try:
            icon_path=icon_path_dict[location_dict['building_en']][location_dict['floor']]
            device_to_icon_path[device_id]=icon_path
        except KeyError:
            print(f'设备{device_id}的位置信息不完整')
    for user_id,location_dict in user_to_location_dict.items():
        try:
            icon_path=icon_path_dict[location_dict['building_en']][location_dict['floor']]
            user_to_icon_path[user_id]=icon_path
        except:
            print(f'用户{user_id}的位置信息不完整')
    icon_path_set=set(device_to_icon_path.values())|set(user_to_icon_path.values())
    for icon_path in icon_path_set:
        async with aiofile.async_open(icon_path,'r') as file:
            icon_data=await file.read()
            icon_data=json.loads(icon_data)
            for feature in icon_data['features']:
                if 'device_id' in feature['properties'].keys():
                    if int(feature['properties']['device_id']) in device_to_status_dict.keys():
                        feature['properties']['status']=device_to_status_dict[int(feature['properties']['device_id'])]
                if 'user_id' in feature['properties'].keys():
                    if feature['properties']['user_id'] in user_to_status_dict.keys():
                        feature['properties']['status']=user_to_status_dict[feature['properties']['user_id']]
        async with aiofile.async_open(icon_path,'w') as file:
            await file.write(json.dumps(icon_data,indent=4))
    
    
    

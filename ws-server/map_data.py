# 操作地图数据
import asyncio
import database
import aiofile
import json

icon_path_dict={'menzhenlou':
                {1:'/home/pc/MET/web_front/tiles/geojson/men-zhen-lou/f1/men-zhen-lou_f1_status.geojson',
                 2:'/home/pc/MET/web_front/tiles/geojson/men-zhen-lou/f2/men-zhen-lou_f2_status.geojson'
                },
                'laojizhenlou':
                {
                    1:'/home/pc/MET/web_front/tiles/geojson/lao-ji-zhen-lou/f1/lao-ji-zhen-lou_f1_status.geojson',
                    2:'/home/pc/MET/web_front/tiles/geojson/lao-ji-zhen-lou/f2/lao-ji-zhen-lou_f2_status.geojson'
                }
                }
# 给前端用的
icon_relative_path_dict={'menzhenlou':
                         {1:'/men-zhen-lou/f1/men-zhen-lou_f1_status.geojson',
                          2:'/men-zhen-lou/f2/men-zhen-lou_f2_status.geojson'
                          },
                          'laojizhenlou':
                          {
                                1:'/lao-ji-zhen-lou/f1/lao-ji-zhen-lou_f1_status.geojson',
                                2:'/lao-ji-zhen-lou/f2/lao-ji-zhen-lou_f2_status.geojson'
                          }
                         }


async def update_device_status(device_id,status):
    """更新设备状态"""
    location_dict=await database.get_device_location(device_id)
    icon_path=icon_path_dict[location_dict['building_en']][location_dict['floor']]
    icon_relative_path=icon_relative_path_dict[location_dict['building_en']][location_dict['floor']]
    
    async with aiofile.async_open(icon_path,'r') as file:
        icon_data=await file.read()
        icon_data=json.loads(icon_data)
        for feature in icon_data['features']:
            if 'device_id' in feature['properties'].keys():
                if feature['properties']['device_id']==device_id:
                    feature['properties']['status']=status
    async with aiofile.async_open(icon_path,'w') as file:
        await file.write(json.dumps(icon_data,indent=4))
    return icon_relative_path,icon_data

async def update_user_status(user_id,status):
    """更新用户状态"""
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
    device_to_location_dict=await database.get_devices_location()
    user_to_location_dict=await database.get_users_location()
    device_to_status_dict=await database.get_devices_status()
    user_to_status_dict=await database.get_users_status()
    device_to_icon_path={}
    user_to_icon_path={}
    for device_id,location_dict in device_to_location_dict.items():
        icon_path=icon_path_dict[location_dict['building_en']][location_dict['floor']]
        device_to_icon_path[device_id]=icon_path
    for user_id,location_dict in user_to_location_dict.items():
        icon_path=icon_path_dict[location_dict['building_en']][location_dict['floor']]
        user_to_icon_path[user_id]=icon_path
    icon_path_set=set(device_to_icon_path.values())|set(user_to_icon_path.values())
    for icon_path in icon_path_set:
        async with aiofile.async_open(icon_path,'r') as file:
            icon_data=await file.read()
            icon_data=json.loads(icon_data)
            for feature in icon_data['features']:
                if 'device_id' in feature['properties'].keys():
                    if feature['properties']['device_id'] in device_to_status_dict.keys():
                        feature['properties']['status']=device_to_status_dict[feature['properties']['device_id']]
                if 'user_id' in feature['properties'].keys():
                    if feature['properties']['user_id'] in user_to_status_dict.keys():
                        feature['properties']['status']=user_to_status_dict[feature['properties']['user_id']]
        async with aiofile.async_open(icon_path,'w') as file:
            await file.write(json.dumps(icon_data,indent=4))
    
    
    

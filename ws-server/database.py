# 关于数据库的一些操作
import asyncio
import aiosqlite

DATABASE = 'data/device.db'

async def get_user_id(device_id):
    """从relation表中查找device_id对应的所有user_id"""
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT user_id FROM relation WHERE device_id=?", (device_id,)) as cursor:
            result= await cursor.fetchall()
        # 不加这个会返回 [(2,), (3,)] 这种形式
        return [user_id[0] for user_id in result]

async def get_device_location(device_id):
    """找到设备位置"""
    location_dict = {}
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT building,building_en,floor,room FROM device WHERE device_id = ?", (device_id,)) as cursor:
            location = await cursor.fetchone()
        if location is not None:
            location_dict['building'] = location[0]
            location_dict['building_en']=location[1]
            location_dict['floor'] = location[2]
            location_dict['room'] = location[3]
        else:
            # Handle the case when location is None
            location_dict['building'] = None
            location_dict['building_en']=None
            location_dict['floor'] = None
            location_dict['room'] = None
    return location_dict

async def get_devices_location():
    """返回所有设备位置"""
    device_to_location_dict={}
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT device_id,building,building_en,floor,room FROM device") as cursor:
            location = await cursor.fetchall()
        for device in location:
            device_to_location_dict[device[0]]={'building':device[1],'building_en':device[2],'floor':device[3],'room':device[4]}
    return device_to_location_dict

async def get_devices_status():
    """返回所有设备状态"""
    device_to_status_dict={}
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT device_id,status FROM device") as cursor:
            status = await cursor.fetchall()
        for device in status:
            device_to_status_dict[device[0]]=device[1]
    return device_to_status_dict

async def get_users_location():
    """返回所有用户位置"""
    user_to_location_dict={}
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT user_id,building,building_en,floor,room FROM user") as cursor:
            location = await cursor.fetchall()
        for user in location:
            user_to_location_dict[user[0]]={'building':user[1],'building_en':user[2],'floor':user[3],'room':user[4]}
    return user_to_location_dict

async def get_users_status():
    """返回所有用户状态"""
    user_to_status_dict={}
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT user_id,status FROM user") as cursor:
            status = await cursor.fetchall()
        for user in status:
            user_to_status_dict[user[0]]=user[1]
    return user_to_status_dict

async def get_user_location(user_id):
    """找到用户位置"""
    location_dict = {}
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT building,building_en,floor,room FROM user WHERE user_id = ?", (user_id,)) as cursor:
            location = await cursor.fetchone()
        if location is not None:
            location_dict['building'] = location[0]
            location_dict['building_en']=location[1]
            location_dict['floor'] = location[2]
            location_dict['room'] = location[3]
        else:
            # Handle the case when location is None
            location_dict['building'] = None
            location_dict['building_en']=None
            location_dict['floor'] = None
            location_dict['room'] = None
    return location_dict

async def get_user_name(user_id):
    """找到用户姓名"""
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT name FROM user WHERE user_id = ?", (user_id,)) as cursor:
            name = await cursor.fetchone()
        if name is not None:
            return name[0]
        else:
            return None

async def set_device_status(device_id,status):
    """设置设备状态"""
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("UPDATE device SET status = ? WHERE device_id = ?", (status, device_id))
        await db.commit()

async def set_device_id(old_id, new_id):
    """设置设备ID"""
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("UPDATE device SET device_id = ? WHERE device_id = ?", (new_id, old_id))
        await db.commit()

async def set_user_status(user_id,status):
    """设置用户状态"""
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("UPDATE user SET status = ? WHERE user_id = ?", (status, user_id))
        await db.commit()

async def add_new_device(device_type, mac, status):
    """添加新设备"""
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT MAX(device_id) FROM device") as cursor:
            max_id = await cursor.fetchone()
        new_id = max_id[0] + 1
        await db.execute("INSERT INTO device (device_id, type, mac, status) VALUES (?, ?, ?, ?)", (new_id, device_type, mac, status))
        await db.commit()
    return new_id

async def add_new_user(username,password,email,name,phone,role,token):
    """添加新用户"""
    async with aiosqlite.connect(DATABASE) as db:
        # 判断用户名是否已经存在
        async with db.execute("SELECT user_id FROM user WHERE username = ?", (username,)) as cursor:
            result = await cursor.fetchone()
        if result is not None:
            return 0
        # 查询最大的id
        async with db.execute("SELECT MAX(user_id) FROM user") as cursor:
            max_id = await cursor.fetchone()
        new_id = max_id[0] + 1
        # 插入新的用户
        await db.execute("INSERT INTO user (user_id, username, password, email, name, phone, role, token) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (new_id, username, password, email, name, phone, role, token))
        await db.commit()
    return 1

async def user_login(username):
    # 找到user表中，username列为uname的行，取出password,role,token,user_id,name,status
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT password,role,token,user_id,name,status FROM user WHERE username = ?", (username,)) as cursor:
            result = await cursor.fetchone()
        if result is not None:
            return result
        else:
            return None

async def user_token_login(user_id):
    # 找到token,role,name,status
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT token,role,name,status FROM user WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
        if result is not None:
            return result
        else:
            return None

async def check_token_exist(token):
    """检查token是否存在"""
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT user_id FROM user WHERE token = ?", (token,)) as cursor:
            result = await cursor.fetchone()
        if result is not None:
            return 1
        else:
            return 0

async def check_id_to_token(user_id,token):
    """检查id-token对是否正确"""
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT user_id FROM user WHERE user_id = ? AND token = ?", (user_id,token)) as cursor:
            result = await cursor.fetchone()
        if result is not None:
            return 1
        else:
            return 0
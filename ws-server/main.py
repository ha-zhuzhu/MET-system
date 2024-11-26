#!/usr/bin/env python

import asyncio
import websockets
import time
import sqlite3
import json
from enum import Enum
import hashlib
import connection
import device
import user
import map_data
import logging
from common_data import *
import argparse
from config_loader import *
from BC25 import bc25
from A7670C import a7670c

# 本机ID
LOCAL_ID = 1
MET_ID=2
DATABASE = 'data/device.db'

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
    filename='info.log', 
    filemode='a'
)

# logging.basicConfig(
#     format="%(message)s",
#     level=logging.DEBUG,
# )

async def handler(websocket):
    connection_added=0  #是否已将连接加入集合
    is_user=0
    try:
        async for frame in websocket:
            logging.info("Received:{}".format(frame))
            logging.info("websocket:{}".format(websocket))
            frame_dict = json.loads(frame)
            if 'sender' in frame_dict.keys():
                # 用户帧
                is_user=1
                connection_added=await user.handler(websocket,frame_dict,connection_added)
            else:
                # 设备帧
                connection_added=await device.handler(websocket,frame_dict,connection_added)
                logging.info("connection_added:{}".format(connection_added))
    except websockets.ConnectionClosed:
        logging.info("Connection closed from {}".format(websocket))
        if is_user:
           await user.offline_handler(websocket)
        else:
            await device.offline_handler(websocket)


async def main(env):
    # 初始化config
    config_loader = GlobalConfigManager.get_config_loader(env)
    await map_data.update_status_by_database()
    await qr_code.init()
    await map_path.init()    # 监听所有接口
    await map_location.init() 
<<<<<<< HEAD
    await bc25.start()
    await a7670c.start()
=======
>>>>>>> 8fe26a4b4fdead9e5ca165b0089f41592f8ba15b
    async with websockets.serve(handler, "", 8008):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the application in a specified environment.')
    parser.add_argument('env', choices=['hospital_test','lab_test'], help='The environment to run the application in.')
    
    args = parser.parse_args()
    
    asyncio.run(main(args.env))

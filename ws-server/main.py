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

# 本机ID
LOCAL_ID = 1
MET_ID=2
DATABASE = 'data/device.db'

logging.basicConfig(
    format="%(asctime)s %(message)s",
    level=logging.INFO,
    filename='info.log', 
    filemode='w'
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
            print("Received:", frame)
            logging.info("Received:{}".format(frame))
            frame_dict = json.loads(frame)
            if 'sender' in frame_dict.keys():
                # 用户帧
                is_user=1
                await user.handler(websocket,frame_dict,connection_added)
            else:
                # 设备帧
                await device.handler(websocket,frame_dict,connection_added)
    finally:
        if is_user:
           await user.offline_handler(websocket)
        else:
            await device.offline_handler(websocket)


async def main():
    await map_data.update_status_by_database()
    await qr_code.init()
    # 监听所有接口
    async with websockets.serve(handler, "", 8008):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())

import serial
import time
import json
import asyncio
from datetime import datetime
import logging
import device

BC25_DEVICE = "COM4"

PROD_ID = "cjZ01U3367"
DEV_ID = "server"

MQTT_TOPIC_POST = "$sys/" + PROD_ID + "/" + DEV_ID + "/thing/property/post" # pub
MQTT_TOPIC_POST_REPLY = "$sys/" + PROD_ID + "/" + DEV_ID + "/thing/property/post/reply" # sub
MQTT_TOPIC_SET = "$sys/" + PROD_ID + "/" + DEV_ID + "/thing/property/set" # sub
MQTT_TOPIC_SET_REPLY = "$sys/" + PROD_ID + "/" + DEV_ID + "/thing/property/set_reply" # pub

MQTT_SERVER = "mqtts.heclouds.com"
MQTT_PORT = 1883
MQTT_TOKEN = "version=2018-10-31&res=products%2FcjZ01U3367%2Fdevices%2Fserver&et=4102419661&method=md5&sign=6OM5xsJw6mIMp7EKzX0SMQ%3D%3D"

class BC25:
    def __init__(self, device: str,baudrate=9600):
        self.serial_port = None
        try:
            self.serial_port = serial.Serial(device, baudrate=baudrate, timeout=1)
        except:
            logging.error("无法打开所设定的BC25端口：{}".format(device))
        self.mqtt_queue = asyncio.Queue()
        self.mqtt_msg = asyncio.Queue()
        self.bc25_registered = False
        self.mqtt_opened = False
        self.mqtt_connected = False
        self.mqtt_running = False
        self.subscribed = False
        self.cmd_sent = False
        self.cmd_success = False

    async def start(self):
        # Start the event handler and mqtt manager tasks
        if self.serial_port is None:
            logging.error("BC25实例无法启动，因为端口未打开")
            return
        asyncio.create_task(self.event_handler())
        asyncio.create_task(self.mqtt_manager())
        self.serial_port.write(b'AT\r\n')
        await self.initialize_module()

    async def initialize_module(self):
        await self.send_command("AT+QRST=1") # reset module
        await asyncio.sleep(2)
        await self.send_command("AT+CPSMS=2") # disable PSM
        await self.send_command("AT+CEDRXS=3") # disable eDRX
        await self.send_command("AT+CFUN=1") # enable full functionality
        await self.send_command("AT+CEREG=1") # enable network registration autofeedback
        await self.send_command("AT+QSCLK=0") # disable sleep
        await self.send_command("ATE0") # disable echo
        await self.send_command("AT&W0") # save settings

    async def send_command(self, cmd: str, blocking=True):
        """
        blocking serial write
        """
        self.serial_port.write((cmd + '\r\n').encode(encoding='ascii'))
        print(f"<<< {cmd}")
        if not blocking:
            return True
        self.cmd_sent = True
        while self.cmd_sent:
            await asyncio.sleep(0.1)
        return self.cmd_success

    async def event_handler(self):
        data = ""
        while True:
            if self.serial_port.in_waiting > 0:
                data += self.serial_port.read(self.serial_port.in_waiting).decode()
                while "\r\n" in data:
                    line, data = data.split("\r\n",1)
                    print(f">>> {line}")
                    self.parse_data(line)
            await asyncio.sleep(0.1)

    def parse_data(self, data: str):
        if self.cmd_sent:
            if "OK" in data:
                self.cmd_success = True
            elif "ERROR" in data:
                self.cmd_success = False
            self.cmd_sent = False

        if "+CEREG: 1" in data:
            self.bc25_registered = True
            print("BC25 is registered to network")
            if not self.mqtt_running:
                asyncio.create_task(self.mqtt_queue.put("start_mqtt")) # tell mqtt manager to start mqtt
        elif "+CEREG: 0" in data:
            self.bc25_registered = False
            if self.mqtt_running:
                asyncio.create_task(self.mqtt_queue.put("stop_mqtt")) # tell mqtt manager to stop mqtt
            print("Bad Signal, BC25 is not registered to network")
        elif "+QMTOPEN: 0,0" in data:
            self.mqtt_opened = True
        elif "+QMTCONN: 0,0,0" in data:
            self.mqtt_connected = True
        elif "+QMTSUB:" in data:
            results = data.split(",")
            if int(results[2]) == 0:
                self.subscribed = True
        elif "+QMTRECV" in data:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now}] MQTT message received")
            results = data.split(",", 3)
            topic, msg = results[2], results[3]
            if topic == MQTT_TOPIC_SET:
                asyncio.create_task(self.mqtt_msg.put(msg))
                asyncio.create_task(self.mqtt_queue.put("process_mqtt_msg"))
            elif topic == MQTT_TOPIC_POST_REPLY:
                try:
                    json_msg = json.loads(msg)
                except:
                    print("Invalid JSON message")
                    print(msg)
                if json_msg['code'] == 200:
                    print("Message sent successfully")
        elif "+QMTSTAT: 0,1" in data:
            print("MQTT connection is closed by server, trying to reconnect")
            asyncio.create_task(self.mqtt_queue.put("stop_mqtt"))
            asyncio.create_task(self.mqtt_queue.put("start_mqtt"))
        else:
            pass

    async def mqtt_manager(self):
        while True:
            msg = await self.mqtt_queue.get()
            if msg == "start_mqtt":
                await self.start_mqtt()
            elif msg == "stop_mqtt":
                await self.stop_mqtt()
            elif msg == "process_mqtt_msg":
                received_msg = await self.mqtt_msg.get()
                json_msg = json.loads(received_msg)
                # {"id":"2","version":"1.0","params":{"test":10}}

                # warn main program here, must be async
                # await device.alarm_handler(None, json_msg)

                print(f"ALARM: {json_msg['params']['alarm_id']}")
                # button id is json_msg["params"]["alarm_id"]

                # feedback for set
                feedback = {
                    "id": str(json_msg["id"]),
                    "code": 200,
                    "msg": "success"
                }
                await self.send_mqtt_msg(feedback, MQTT_TOPIC_SET_REPLY)

                # tell the button
                feedback = {
                    "id": "1",
                    "params": {
                        "alarm_received": {
                            "value": json_msg["params"]["alarm_id"]
                        }
                    }
                }
                await self.send_mqtt_msg(feedback, MQTT_TOPIC_POST)

                # reset alarm_id
                feedback = {
                    "id": "2",
                    "params": {
                        "alarm_id": {
                            "value": 0
                        }
                    }
                }
                await self.send_mqtt_msg(feedback, MQTT_TOPIC_POST)

                # reset alarm_received
                feedback = {
                    "id": "3",
                    "params": {
                        "alarm_received": {
                            "value": 0
                        }
                    }
                }
                await self.send_mqtt_msg(feedback, MQTT_TOPIC_POST)

    async def send_mqtt_msg(self, msg: dict, topic: str):
        payload = json.dumps(msg)
        await self.send_command(f'AT+QMTPUB=0,1,0,0,"{topic}"')
        await self.send_command(payload + "\x1A")
        await asyncio.sleep(2)

    async def start_mqtt(self):
        await self.send_command(f'AT+QMTCFG="VERSION",0,1')
        await self.send_command(f'AT+QMTCFG="TIMEMOUT",0,30,3') # 30s timeout, retry 3 times
        await self.send_command(f'AT+QMTCFG="KEEPALIVE",0,120') # do not disconnect

        await self.send_command(f'AT+QMTOPEN=0,"{MQTT_SERVER}",{MQTT_PORT}')
        while not self.mqtt_opened:
            await asyncio.sleep(0.1)

        await self.send_command(f'AT+QMTCONN=0,"{DEV_ID}","{PROD_ID}","{MQTT_TOKEN}"')
        while not self.mqtt_connected:
            await asyncio.sleep(0.1)

        # Subscribe to topics
        await self.send_command(f'AT+QMTSUB=0,1,"{MQTT_TOPIC_POST_REPLY}",0')
        while not self.subscribed:
            await asyncio.sleep(0.1)
        self.subscribed = False

        # Subscribe to set topic
        await self.send_command(f'AT+QMTSUB=0,2,"{MQTT_TOPIC_SET}",0')
        while not self.subscribed:
            await asyncio.sleep(0.1)

        self.mqtt_running = True
        print("MQTT started")

    async def stop_mqtt(self):
        await self.send_command("AT+QMTDISC=0")
        await self.send_command("AT+QMTCLOSE=0")
        self.mqtt_running = False
        print("MQTT stopped")

# async def main():
#     bc25 = BC25(device="/dev/ttyUSB1")
#     await bc25.start()
#     await asyncio.Event().wait()  # Keep the program running

# if __name__ == "__main__":
#     asyncio.run(main())

bc25 = BC25(device=BC25_DEVICE)

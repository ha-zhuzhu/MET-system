import serial
import asyncio
import codecs
import logging

center_phone="8613800100500"    # 北京移动短信中心号码

class A7670C:
    """4G模块"""

    def __init__(self, device: str, baudrate=115200):
        self.serial_port = serial.Serial(device, baudrate=baudrate, timeout=1)
        self.attached = False  # 是否已经附着到网络
        self.CIMI = None
        self.cmd_sent = False
        self.cmd_success = False
        self.notify_running = False
        self.notify_inst = asyncio.Queue()          # 指令队列
        self.notify_msg = asyncio.Queue()           # 短信内容队列
        self.notify_number = asyncio.Queue()        # 电话号码队列
        self.notify_call_content = asyncio.Queue()  # 电话内容队列

    async def start(self):
        asyncio.create_task(self.event_handler())
        asyncio.create_task(self.notify_manager())
        self.serial_port.write(b"AT\r\n")
        await self.check_module()

    async def check_module(self):
        """检查模块是否正常"""
        await self.send_command("AT+CIMI")
        await self.send_command("AT+CGATT?")
        

    async def send_command(self, cmd: str, blocking=True):
        """
        blocking serial write
        """
        self.serial_port.write((cmd + "\r\n").encode(encoding="ascii"))
        print(f"<<< {cmd}")
        if not blocking:
            return True
        self.cmd_sent = True
        while self.cmd_sent:
            await asyncio.sleep(0.1)
        return self.cmd_success

    async def event_handler(self):
        """事件处理器"""
        data = ""
        while True:
            if self.serial_port.in_waiting > 0:
                data += self.serial_port.read(self.serial_port.in_waiting).decode()
                while "\r\n" in data:
                    line, data = data.split("\r\n", 1)
                    print(f">>> {line}")
                    self.parse_data(line)
            await asyncio.sleep(0.1)

    def parse_data(self, data: str):
        """解析数据"""
        if self.cmd_sent:
            if "OK" in data:
                self.cmd_success = True
            elif "ERROR" in data:
                self.cmd_success = False
            self.cmd_sent = False
        
        if "+CGATT: 1" in data:
            self.attached = True
            print("A7670C attached to network")
            if not self.notify_running:
                # asyncio.create_task(self.notify_inst.put("start"))
                self.notify_running = True
        elif "+CGATT: 0" in data:
            self.attached = False
            print("A7670C detached from network")
            if self.notify_running:
                self.notify_running = False
                # asyncio.create_task(self.notify_inst.put("stop"))
        else:
            pass

    async def notify_manager(self):
        """警报通知管理器"""
        while True:
            inst = await self.notify_inst.get()
            if inst == "call" and self.notify_running:
                number = await self.notify_number.get()
                # content = await self.notify_call_content.get()

                await self.send_command(f'ATD{number};')
            elif inst == "message" and self.notify_running:
                number = await self.notify_number.get()
                content = await self.notify_msg.get()
                # 设置为PDU模式
                ret=await self.send_command("AT+CMGF=0")
                # ret 略有问题
                # if ret==False:
                #     logging.error("设置PDU模式失败，退出短信发送")
                #     continue
                # logging.info("设置PDU模式成功")
                # 发送短信
                pdu=await self.gen_pdu(number,center_phone,await self.msg_ucs2_encode(content))
                logging.info("pdu:"+pdu)
                pdu_len=int((int(len(pdu)) - 18) / 2)
                await self.send_command(f"AT+CMGS={pdu_len}")
                await self.send_command(pdu)
                await self.send_command(chr(26), blocking=False)
            else:
                pass


    async def call(self, number: str, content: str = ""):
        """拨打电话"""
        asyncio.create_task(self.notify_inst.put("call"))
        asyncio.create_task(self.notify_number.put(number))

    async def message(self, number: str, content: str):
        """发送短信"""
        asyncio.create_task(self.notify_inst.put("message"))
        asyncio.create_task(self.notify_number.put(number))
        asyncio.create_task(self.notify_msg.put(content))
        pass

    async def gen_phone_num(self,demo):  # 收件人 "8613800280500" -> "683108200805F0"
        """生成收件人号码"""
        if len(demo) % 2 != 0:
            demo = demo + "F"
        else:
            demo = demo
        listdemo = []
        for x in range(len(demo)): listdemo.append(demo[x])
        qi = listdemo[::2]
        ou = listdemo[1::2]
        end = []
        if len(qi) == len(ou):  # 奇偶互换
            for i in range(len(qi)):
                end.append(ou[i])
                end.append(qi[i])
        return "".join(end)


    async def gen_center_phone_num(self,demo):
        """生成中心号码"""
        # 中心号码 "8613800280500" -># "0891683108200805F0"
        if len(demo) % 2 != 0:
            demo = demo + "F"
        else:
            demo = demo
        listdemo = []
        for x in range(len(demo)): listdemo.append(demo[x])
        qi = listdemo[::2]
        ou = listdemo[1::2]
        end = []
        if len(qi) == len(ou):  # 奇偶互换
            for i in range(len(qi)):
                end.append(ou[i])
                end.append(qi[i])
        return "0891"+"".join(end)

    async def expand_to_16(self,ucode): #ascii字符--16-bit编码
        for i in range(len(ucode)):
            if (len(ucode[i])==4):
                ucode[i] = ucode[i][0:2]+"00" + ucode[i][2:]
        return ucode

    async def msg_ucs2_encode(self,src):
        """中文转UCS2编码"""
        # 7-bit编码 用于发送普通的ASCII字符，
        # 8-bit编码 通常用于发送数据消息，
        # UCS2编码 用于发送Unicode字符。
        #  UCS2编码  中文：你好-> 4f60597d
        #  7-bit  hello -> 00680065006c006c006f  英文-> ascii -> 转hex，16进制。补0
        #  8-bit  1234 -  > 0031003200330034
        decoder = codecs.getdecoder("utf-8")
        ucs2 = decoder(src.encode())
        src_len = len(ucs2[0])
        ucode = []
        result = ""
        for i in range(src_len):
            ucode.append(hex(ord(ucs2[0][i])))
            ucode = await self.expand_to_16(ucode)
        for item in ucode:
            result = result+item[2:]
        return result

    async def gen_pdu(self,des, smsc, content):
        """生成pdu"""
        # 收件人 中心号码 内容
        result = ""
        type_of_address = "91"  # 国际91,中国小灵通“91”
        tp_mti = "01"  #
        tp_mr = "00"  #
        tp_pid = "00"  # 默认为普通GSM类型，即点到点方式
        des_len = "0d"  # 目标地址数字个数 共13个十进制数(不包括91和‘F’)
        alphabet_size = "08"  # 默认用16-bit(7/8/16)编码
        result += await self.gen_center_phone_num(smsc)  # 加中心站号码
        result += tp_mti
        result += tp_mr
        result += des_len
        result += type_of_address
        des = await self.gen_phone_num(des)  # 加收件人号码
        result += des
        result += tp_pid
        result += alphabet_size
        # logger.info("con_len:"+(hex(int(len(content) / 2))[2:]).zfill(2))
        result += (hex(int(len(content) / 2))[2:]).zfill(2) # !转16进制去除0x 以后补0 0xE->E->0E
        result += content
        return result.upper()




async def main():
    a7670c=A7670C('/dev/ttyUSB0')
    await a7670c.start()
    # await a7670c.call('13438233066')
    await a7670c.message('13438233066','你好')

    await asyncio.Event().wait()  # Keep the program running



if __name__ == "__main__":
    asyncio.run(main())



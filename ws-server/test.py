
# status = None
# id = None
# data = {
#     "status": status,
#     "id": id
# }

# print(data)


# import json

# json_path="../../web_front/tiles/geojson/men-zhen-lou/f1/men-zhen-lou_f1_status.geojson"
# with open(json_path,'r') as file:
#     data=json.load(file)
# print(data['features'][2]['properties']['status'])
# data['features'][2]['properties']['status']=3

# with open(json_path,'w') as file:
#     json.dump(data,file,indent=4)

# print('[!紧急情况!]院楼：{}。楼层：{}。房间：{room}。'.format('a','b','c'))
# from enum import Enum

# class button_status(Enum):
#     """按钮设备状态"""
#     offline = 1
#     standby = 2
#     alarm = 3
#     doc_response = 4
#     aed_response = 5

# print(type(button_status.offline.value))

# import json

# # JSON string:
# # Multi-line string
# data = """{
# "Name": "Jennifer Smith",
# "Contact Number": 78698,
# "Email": "jen123@gmail.com",
# "Hobbies":["Reading", "Sketching", "Horse Riding"]
# }"""
# #学习中遇到问题没人解答？小编创建了一个Python学习交流群：711312441
# # parse data:
# res = json.loads(data)

# # the result is a Python dictionary:
# print(res)



# import websockets
# print(websockets.State.OPEN)

# import test2
# import test1
# test2.a.add(1)
# print(test2.a)
# test1.p

# my_dict = {"a": 1, "d": 2, "c": 3}

# # 删除键值为 "b" 的键值对
# my_dict.pop("b", None)

# print(my_dict)  # Output: {"a": 1, "c": 3}

# import status
# print(status.button.alarm.value)

# import cv2
# import pyzbar.pyzbar
# # from pyzbar.pyzbar import decode

# def decode_qrcode(image_path):
#     # 读取图像
#     image = cv2.imread(image_path)

#     # 解码二维码
#     decoded_objects = pyzbar.pyzbar.decode(image)
    
#     for obj in decoded_objects:
#         print("Type:", obj.type)
#         print("Data:", obj.data.decode("utf-8"))
#         print("Position:", obj.rect)
        
#     return decoded_objects

# # 示例使用
# decoded_objects = decode_qrcode('data/qrcode/raw/xieyufei.jpg')
# for obj in decoded_objects:
#     print(f"QR Code Data: {obj.data.decode('utf-8')}")


# import qrcode
# import cv2
# from PIL import Image

# def create_qrcode(data, filename, size):
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_H,
#         box_size=10,
#         border=2
#     )
#     qr.add_data(data)
#     qr.make(fit=True)
    
#     img = qr.make_image(fill_color="black", back_color="white")
    
#     # 调整图像大小
#     img = img.resize((size, size),Image.LANCZOS)
#     # 保存图像
#     img.save(filename)
#     print(f"QR code saved as {filename}")

# # 示例使用
# data = "https://u.wechat.com/EL_WfiYtGUjkmiqeMwssvrE?s=2"
# filename = "qrcode.png"
# size = 132
# create_qrcode(data, filename, size)


# import base64

# with open('data/qrcode/generate/20240719155448.bin','rb') as file:
#     data=file.read()

# # 编码为base16
# data_base16=base64.b16encode(data).decode()
# # 保存为txt
# with open('20240719155448_base16.txt','w') as file:
#     file.write(data_base16)

# import sqlite3

# database='data/device.db'

# # 删除device表中，mac为'34:b7:da:9f:e7:cc'的行
# def delete_same_mac():
#     conn = sqlite3.connect(database)
#     cursor = conn.cursor()
#     cursor.execute("DELETE FROM device WHERE mac = '34:b7:da:9f:e7:cc'")
#     conn.commit()
#     conn.close()



# def get_same_mac():
#     conn = sqlite3.connect(database)
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM device WHERE mac = '34:b7:da:9f:e7:cc'")
#     result = cursor.fetchall()
#     conn.close()
#     return result

# print(get_same_mac())

# import json

# with open('config.json','r') as file:
#     data=json.load(file)

# print(data.get('environments',{}).get('hospital_test',{})['icon_path'])



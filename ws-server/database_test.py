import sqlite3

# # 连接到 SQLite 数据库
# conn = sqlite3.connect('device')  # 假设数据库文件名为 device.db

# # 创建游标对象
# cursor = conn.cursor()

# # 选择 ID 为 3 的记录中的 building 字段
# select_query = "SELECT building FROM device WHERE id = ?"
# record_id = 1

# # 执行查询操作
# cursor.execute(select_query, (record_id,))

# # 获取查询结果
# building_value = cursor.fetchone()

# # 打印或使用 building_value
# if building_value:
#     print(f"The building value for ID {record_id} is: {building_value[0]}")
# else:
#     print(f"No record found with ID {record_id}")

# # 关闭游标和数据库连接
# cursor.close()
# conn.close()

DATABASE = 'device.db'
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()
# 从relation表中查找device_id对应的所有user_id
select_query = "SELECT user_id FROM relation WHERE device_id = ?"
cursor.execute(select_query, (3,))
user_id_list = cursor.fetchall()
cursor.close()
conn.close()

print(user_id_list)
from enum import Enum

class button(Enum):
    """按钮设备状态"""
    offline = 1
    standby = 2
    alarm = 3
    doc_response = 4
    aed_response = 5
    doc_aed_response = 6

class doctor(Enum):
    """医生状态"""
    offline = 1
    standby = 2
    called = 3
    response = 4
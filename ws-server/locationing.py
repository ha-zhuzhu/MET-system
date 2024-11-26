import numpy as np

class KalmanFilter:
    def __init__(self):
        self.A = 1  # 状态转移矩阵
        self.H = 1  # 观测矩阵
        self.Q = 1e-5  # 过程噪声
        self.R = 1e-2  # 观测噪声
        self.x = None  # 初始状态
        self.P = 1  # 初始误差协方差

    def filter(self, z):
        # 如果这是首次输入，直接使用当前观测值初始化状态
        if self.x is None:
            self.x = z
            return z
        
        # 预测步骤
        x_pred = self.A * self.x
        P_pred = self.A * self.P * self.A + self.Q
        
        # 更新步骤
        K = P_pred * self.H / (self.H * P_pred * self.H + self.R)  # 卡尔曼增益
        self.x = x_pred + K * (z - self.H * x_pred)  # 更新状态
        self.P = (1 - K * self.H) * P_pred  # 更新误差协方差
        
        return self.x

# # 初始化滤波器
# kf = [KalmanFilter() for _ in range(17)]

async def RSSI_filter(kf,current_input):
    # 处理每一个beacon的RSSI值
    filtered_values = [kf[i].filter(current_input[i]) for i in range(len(current_input))]
    return filtered_values


class KalmanFilterXYZ:
    def __init__(self):
        # 初始化状态
        self.initialized = False
        self.x_prev = None
        self.P_prev = None
        # 状态转移矩阵
        self.F = np.eye(3)
        # 观测矩阵
        self.H = np.eye(3)
        # 过程噪声协方差矩阵（假设过程噪声较小）
        self.Q = np.eye(3) * 0.01
        # 观测噪声协方差矩阵（根据RSSI数据特性假设一个较大的值）
        self.R = np.eye(3) * 0.1

    def filter(self, measurement):
        z = np.array(measurement).reshape(3, 1)

        if not self.initialized:
            # 第一次输入不进行滤波，直接输出
            self.x_prev = z
            self.P_prev = np.eye(3)
            self.initialized = True
            return z.flatten().tolist()

        # 预测步骤
        x_pred = self.F @ self.x_prev
        P_pred = self.F @ self.P_prev @ self.F.T + self.Q

        # 更新步骤
        y = z - self.H @ x_pred
        S = self.H @ P_pred @ self.H.T + self.R
        K = P_pred @ self.H.T @ np.linalg.inv(S)
        x_new = x_pred + K @ y
        P_new = (np.eye(3) - K @ self.H) @ P_pred

        # 更新状态
        self.x_prev = x_new
        self.P_prev = P_new

        return x_new.flatten().tolist()

# # 初始化滤波器
# kf_xyz = KalmanFilterXYZ()

async def xyz_filter(kf_xyz,current_input):
    return kf_xyz.filter(current_input)

async def RSSI_dic2list(active_beacon,RSSI_dic):
    RSSI_list = [RSSI_dic.get(str(beacon), 0) for beacon in active_beacon]
    return RSSI_list

async def is_all_zero(RSSI_list):
    is_all_zero = all(value == 0 for value in RSSI_list)
    return is_all_zero

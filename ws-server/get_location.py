import joblib

# 加载 StandardScaler 和 KNN 模型
scaler = joblib.load('scaler_v4.pkl')
model = joblib.load('knn_model_v4.pkl')

async def map_location(RSSI_list):
    pass
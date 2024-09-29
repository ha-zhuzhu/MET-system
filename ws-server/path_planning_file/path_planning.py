import json
import networkx as nx
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from collections import defaultdict
from geojson import Feature, FeatureCollection, LineString, Point
import re


# 定义计算权重的函数
def calculate_weight(properties):
    distance = properties.get("distance", 1)
    congestion = properties.get(
        "congestion", 1
    )  # 拥挤程度（1为畅通，值越大表示越拥挤）
    edge_type = properties.get("type", "corridor")  # 默认类型为走廊
    status = properties.get("status", "open")  # 状态

    # 基本权重设定，可以根据实际情况调整
    base_weight = 1

    # 根据边类型调整权重
    if edge_type == "elevator":
        type_factor = 1.5
    elif edge_type == "lift":
        type_factor = 1.3
    elif edge_type == "stair":
        type_factor = 2.0
    elif edge_type == "corridor":
        type_factor = 1.0
    else:
        type_factor = 1.0  # 默认因素

    # 根据状态调整权重
    if status == "closed":
        status_factor = float("inf")  # 不可通行
    elif status == "open":
        status_factor = 1.0
    else:
        status_factor = 1.0

    # 综合计算权重
    weight = distance * congestion * type_factor * status_factor * base_weight
    return weight


def add_nodes(G, filename):
    # 读取 GeoJSON 节点文件
    with open(filename, "r") as f:
        nodes_data = json.load(f)
    # 添加节点
    for feature in nodes_data["features"]:
        node_id = feature["properties"]["node_id"]
        coordinates = feature["geometry"]["coordinates"]
        building_name = feature["properties"]["building_name"]
        name = feature["properties"]["name"]
        floor = feature["properties"]["floor"]
        G.add_node(
            node_id,
            pos=tuple(coordinates),
            building_name=building_name,
            name=name,
            floor=floor,
        )


def add_edges(G, filename):
    # 读取边文件
    with open(filename, "r") as f:
        edges_data = json.load(f)  # ["edges"]
    # 添加边
    for edge in edges_data["features"]:
        source = edge["properties"]["source"]
        target = edge["properties"]["target"]
        properties = edge["properties"]
        direction = properties.get("direction", "both")

        # 计算权重
        weight = calculate_weight(properties)

        # 添加边到图中
        if direction == "one-way":
            G.add_edge(source, target, weight=weight, **properties)
        elif direction == "both":
            G.add_edge(source, target, weight=weight, **properties)
            G.add_edge(target, source, weight=weight, **properties)


def Dijkstra(G, start_node, end_node, my_weight="weight"):
    # 计算最短路径
    shortest_path = nx.dijkstra_path(
        G, source=start_node, target=end_node, weight=my_weight
    )
    # shortest_path_length = nx.dijkstra_path_length(
    #     G, source=start_node, target=end_node, weight="weight"
    # )
    return shortest_path  # , shortest_path_length


def details(G, path):
    # 获取路径上的距离信息
    total_distance = 0
    total_weight = 0
    for u, v in zip(path[:-1], path[1:]):  # 用于节点列表生成边列表
        if G.has_edge(u, v):
            edge_data = G[u][v]
            distance = edge_data.get("distance", 0)  # 默认距离为0
            # print(f"Distance from {u} to {v}: {distance}")
            total_distance += distance
            weight = edge_data.get("weight", 0)
            total_weight += weight
        else:
            print(f"No edge from {u} to {v}")
    return total_weight, total_distance


def visualize(G, shortest_path):
    # 提取节点的位置
    pos = nx.get_node_attributes(G, "pos")

    # 提取节点的标签
    labels = nx.get_node_attributes(G, "name")

    # 创建 3D 绘图
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    # 绘制节点
    x_coords = [coord[0] for coord in pos.values()]
    y_coords = [coord[1] for coord in pos.values()]
    z_coords = [coord[2] for coord in pos.values()]
    ax.scatter(x_coords, y_coords, z_coords, c="lightblue", s=100)

    # 添加节点标签
    for node, (x, y, z) in pos.items():
        ax.text(x, y, z, labels[node], fontsize=10)

    # 绘制边
    for edge in G.edges(data=True):
        x = [pos[edge[0]][0], pos[edge[1]][0]]
        y = [pos[edge[0]][1], pos[edge[1]][1]]
        z = [pos[edge[0]][2], pos[edge[1]][2]]
        ax.plot(x, y, z, c="gray")

    # 绘制最短路径
    path_edges = list(
        zip(shortest_path[:-1], shortest_path[1:])
    )  # 用于节点列表生成边列表
    for edge in path_edges:
        x = [pos[edge[0]][0], pos[edge[1]][0]]
        y = [pos[edge[0]][1], pos[edge[1]][1]]
        z = [pos[edge[0]][2], pos[edge[1]][2]]
        ax.plot(x, y, z, c="blue", linewidth=2)

    ax.set_title("3D Hospital Indoor Navigation")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Floor (Z)")
    plt.show()


def contains_to_pattern(text):
    pattern = re.compile(r"_to_")
    return bool(pattern.search(text))


def generate_geojson_path(G, shortest_path, shortest_time_weight, shortest_path_weight):
    # 获取路径坐标
    path_data = [
        (G.nodes[node]["pos"], G.nodes[node]["building_name"], G.nodes[node]["floor"])
        for node in shortest_path
    ]
    # start_node = path_coordinates[0]
    # end_node = path_coordinates[-1]

    # 按building_name和floor分组
    grouped_paths = defaultdict(list)

    # 按楼层，建筑物，将node分组，
    for pos, building_name, floor in path_data:
        grouped_paths[(building_name, floor)].append(pos)

    # 特别获得楼层连接与建筑物的连接点
    for i in range(len(path_data) - 1):
        current_pos, current_building, current_floor = path_data[i]
        next_pos, next_building, next_floor = path_data[i + 1]

        if current_building != next_building:
            key = (f"{current_building}_to_{next_building}", current_floor)
            #grouped_paths[key].append(current_pos)
            #grouped_paths[key].append(next_pos)
        elif current_floor != next_floor:
            key = (current_building, f"{current_floor}_to_{next_floor}")
            #grouped_paths[key].append(current_pos)

        # # 确保跨楼层或跨建筑的线条连接点
        if current_building != next_building or current_floor != next_floor:
            grouped_paths[key].append(current_pos)
            grouped_paths[key].append(next_pos)
        
        #欠一个，把不同楼层，同个电梯的group一起，只显示楼层->楼层
        
    # 生成GeoJSON
    # 按building_name和floor分组
    # grouped_paths = defaultdict(list)
    # for pos, building_name, floor in path_data:
    #     grouped_paths[(building_name, floor)].append(pos)

    features = []
    for (building_name, floor), coordinates in grouped_paths.items():
        if len(coordinates) > 1:
            line = LineString(coordinates)
            result = contains_to_pattern(floor)
            feature = Feature(
                geometry=line,
                properties={"building_name": building_name, "floor": floor, "floor_change":result},
            )
            features.append(feature)

    shortest_path_geojson = FeatureCollection(features)

    # 输出GeoJSON
    with open("../tiles/geojson/path.geojson", "w") as f:
        json.dump(shortest_path_geojson, f, indent=2)

    print("GeoJSON文件已生成：shortest_path.geojson")
    
def generate_geojson_path2(G, shortest_path, shortest_time_weight, shortest_path_weight):
    # 获取路径坐标
    path_data = [
        (G.nodes[node]["pos"], G.nodes[node]["building_name"], G.nodes[node]["floor"])
        for node in shortest_path
    ]
    # start_node = path_coordinates[0]
    # end_node = path_coordinates[-1]

    # 按building_name和floor分组
    grouped_paths = defaultdict(list)

    # 按楼层，建筑物，将node分组，
    for pos, building_name, floor in path_data:
        grouped_paths[(building_name, floor)].append(pos)

    # 特别获得楼层连接与建筑物的连接点
    for i in range(len(path_data) - 1):
        current_pos, current_building, current_floor = path_data[i]
        next_pos, next_building, next_floor = path_data[i + 1]

        if current_building != next_building:
            key = (f"{current_building}_to_{next_building}", current_floor)
            grouped_paths[key].append(current_pos)
            grouped_paths[key].append(next_pos)
        elif current_floor != next_floor:
            key = (current_building, f"{current_floor}_to_{next_floor}")
            grouped_paths[key].append(current_pos)

        # # 确保跨楼层或跨建筑的线条连接点
        # if current_building != next_building or current_floor != next_floor:
        #     grouped_paths[key].append(current_pos)
        #     grouped_paths[key].append(next_pos)
        
        #欠一个，把不同楼层，同个电梯的group一起，只显示楼层->楼层
        
    # 生成GeoJSON
    features = []
    for (building_name, floor), coordinates in grouped_paths.items():
        result = contains_to_pattern(floor)
        if result == False and len(coordinates) > 1:
            line = LineString(coordinates)
            feature = Feature(
                geometry=line,
                properties={"building_name": building_name, "floor": floor,"floor_change":result},
            )
        elif result == True:
            line = Point(coordinates)
            feature = Feature(
                geometry=line,
                properties={"building_name": building_name, "floor": floor,"floor_change":result},
            )
        features.append(feature)

    shortest_path_geojson = FeatureCollection(features)
    # 按building_name和floor分组
    # grouped_paths = defaultdict(list)
    # for pos, building_name, floor in path_data:
    #     grouped_paths[(building_name, floor)].append(pos)

    # features = []
    # for (building_name, floor), coordinates in grouped_paths.items():
    #     if len(coordinates) > 1:
    #         line = LineString(coordinates)
    #         result = contains_to_pattern(floor)
    #         feature = Feature(
    #             geometry=line,
    #             properties={"building_name": building_name, "floor": floor, "floor_change":result},
    #         )
    #         features.append(feature)

    # shortest_path_geojson = FeatureCollection(features)

    # 输出GeoJSON
    with open("../tiles/geojson/path.geojson", "w") as f:
        json.dump(shortest_path_geojson, f, indent=2)

    print("GeoJSON文件已生成：shortest_path.geojson")


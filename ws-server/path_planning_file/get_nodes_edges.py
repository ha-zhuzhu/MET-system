import json
from geopy.distance import geodesic


# 加载GeoJSON文件
def load_geojson(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# 提取节点和边数据
def extract_nodes_edges(geojson_data):
    nodes = {}
    edges = []
    node_counts = {}
    edge_count=0
    node_count=0

    for feature in geojson_data["features"]:
        properties = feature["properties"]
        geometry = feature["geometry"]
        name = properties.get("name", "unknown")
        floor = properties.get("floor", 0)
        building_name = properties.get("building_name", "")
        node_name = f"{building_name}_f{floor}_{name}"
        node_count+=1
        if name in ["stair", "lift", "elevator"]:
            name_id = properties.get("name_id", 0)
            node_id = f"{building_name}_f{floor}_{name}_{name_id}"

            if geometry["type"] == "Point":
                coordinates = geometry["coordinates"] + [ float(floor)]  # 添加floor作为z轴
                nodes[node_id] = {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": coordinates},
                    "properties": {
                        "node_id": node_id,
                        "name": name,
                        "specific_name": properties.get("specific_name", "-"),
                        "floor": floor,
                        "building_name": building_name,
                        "name_id": name_id,
                    },
                    'id':node_count,
                }
        else:
            if node_name not in node_counts:
                node_counts[node_name] = 0
            node_id = f"{building_name}_f{floor}_{name}_{node_counts[node_name]}"
            node_counts[node_name] += 1

            if geometry["type"] == "Point":
                coordinates = geometry["coordinates"] + [
                    float(floor)
                ]  # 添加floor作为z轴
                nodes[node_id] = {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": coordinates},
                    "properties": {
                        "node_id": node_id,
                        "name": name,
                        "specific_name": properties.get("specific_name", ""),
                        "floor": floor,
                        "building_name": building_name,
                    },
                    'id':node_count,
                }
    
    # 把linestring关系转换成edges，适用于平面关系
    for feature in geojson_data["features"]:
        properties = feature["properties"]
        geometry = feature["geometry"]

        if geometry["type"] == "LineString":
            coordinates = geometry["coordinates"]
            for i in range(len(coordinates) - 1):
                start_coord = coordinates[i]
                end_coord = coordinates[i + 1]

                # 查找或生成对应的节点ID
                start_node_id = find_node_by_coord(nodes, start_coord + [float(properties.get("floor", 0))])
                end_node_id = find_node_by_coord(nodes, end_coord + [float(properties.get("floor", 0))])
                if start_node_id and end_node_id:
                    distance = geodesic((start_coord[1], start_coord[0]), (end_coord[1], end_coord[0])).meters
                    edge_count+=1
                    # geojson版本，方便画图
                    edge_geojson = {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [
                                start_coord + [float(properties.get("floor", 0))],
                                end_coord + [float(properties.get("floor", 0))],
                            ],
                        },
                        "properties": {
                            "source": start_node_id,
                            "target": end_node_id,
                            "distance": distance,
                            "congestion": properties.get("congestion", 1),
                            "type": properties.get("type", "corridor"),
                            "status": properties.get("status", "open"),
                            "direction": properties.get("direction", "both"),
                            "floor":properties.get("floor", 0),
                        },
                        "id":edge_count,
                    }
                    edges.append(edge_geojson)
                else:
                    print(
                        f"Warning: Edge with coordinates {start_coord} to {end_coord} does not match any nodes."
                    )

    # 把楼层（直立）关系转换成edge关系
    # 先针对stair，lift，elevator，把相应点从nodes找出（或者先存在另一个nodes_updown），把
    # 楼名，name_id一样的放一起按楼层排序，两两建立连接
    # 添加楼层间连接（垂直连接）
    special_nodes = extract_special_nodes(nodes)
    vertical_edges = create_vertical_edges(special_nodes,edge_count)
    
    edges.extend(vertical_edges)
    
    return nodes, edges


# 查找节点
def find_node_by_coord(nodes, coord):
    for node_id, node in nodes.items():
        if node["geometry"]["coordinates"] == coord:
            return node_id
    return None


# 提取特定节点
def extract_special_nodes(nodes):
    special_nodes = {"stair": [], "lift": [], "elevator": []}
    for node_id, node in nodes.items():
        properties = node["properties"]
        name = properties["name"]
        if name in special_nodes:
            special_nodes[name].append(node)
    return special_nodes


# 创建楼层间连接(z轴连接)
def create_vertical_edges(special_nodes,edge_count):
    new_edges = []
    
    for node_type, nodes in special_nodes.items():
        grouped_nodes = {}

        # 按building_name和name_id分组
        for node in nodes:
            building_name = node["properties"]["building_name"]
            name_id = node["properties"].get("name_id")
            key = (building_name, name_id)
            if key not in grouped_nodes:
                grouped_nodes[key] = []
            grouped_nodes[key].append(node)

        # 对每个分组内的节点按楼层排序并两两连接
        for group, nodes in grouped_nodes.items():
            sorted_nodes = sorted(nodes, key=lambda x: float(x["properties"]["floor"]))
            for i in range(len(sorted_nodes) - 1):
                source_node = sorted_nodes[i]
                target_node = sorted_nodes[i + 1]

                # distance = geodesic(
                #     (source_node['geometry']['coordinates'][1], source_node['geometry']['coordinates'][0]),
                #     (target_node['geometry']['coordinates'][1], target_node['geometry']['coordinates'][0])
                # ).meters
                distance = float(target_node["properties"]["floor"]) - float( source_node["properties"]["floor"])
                edge_count+=1
                 # geojson版本，方便画图
                edge_geojson = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            source_node['geometry']['coordinates'],
                            target_node['geometry']['coordinates'],
                        ],
                    },
                    "properties": {
                        "source": source_node["properties"]["node_id"],
                        "target": target_node["properties"]["node_id"],
                        "distance": distance,
                        "congestion": 1,
                        "type": node_type,
                        "status": "open",
                        "direction": "both",
                    },
                    "id":edge_count,
                }
                new_edges.append(edge_geojson)

    return new_edges


# 保存GeoJSON文件
def save_geojson(features, filepath):
    geojson = {"type": "FeatureCollection", "features": features}
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=4, ensure_ascii=False)



# 主程序
geojson_filepath = "hospital-path.geojson"
geojson_data = load_geojson(geojson_filepath)

nodes, edges = extract_nodes_edges(geojson_data)

nodes_filepath = "../tiles/geojson/nodes.geojson"
edges_filepath = "../tiles/geojson/edges.geojson"

save_geojson(list(nodes.values()), nodes_filepath)
save_geojson(edges, edges_filepath)

print(
    "Nodes have been saved to 'nodes_geojson.json' and edges have been saved to 'edges.geojson'."
)

import networkx as nx
import path_planning
import time

start = time.time()
# 创建有向图
G = nx.DiGraph()
path_planning.add_nodes(G, "../tiles/geojson/nodes.geojson")
path_planning.add_edges(G, "../tiles/geojson/edges.geojson")
# print("Nodes:", G.nodes(data=True))
# print("Edges:", G.edges(data=True))
end1 = time.time()
print("生成有向图 Running time: %s Seconds" % (end1 - start))
# 指定起始节点和目标节点
start_node = "lao-ji-zhen-lou_f2_room_1"
end_node = "men-zhen-lou_f2_room_2"
# 计算最短路径
# 参数选择：weight （综合考量，耗时）；distance（最短路径）
preferred_path = path_planning.Dijkstra(G, start_node, end_node, "weight")
preferred_path_weight, preferred_path_length = path_planning.details(G, preferred_path)

print(f"Preferred path from {start_node} to {end_node}: {preferred_path}")
print(f"Preferred path weight: {preferred_path_weight}")
print(f"Preferred path length: {preferred_path_length}")

#path_planning.visualize(G, preferred_path)
path_planning.generate_geojson_path(G, preferred_path, preferred_path_weight, preferred_path_length)
end2 = time.time()
print("路径规划+生成json Running time: %s Seconds" % (end2 - end1))
print("总共 Running time: %s Seconds" % (end2 - start))

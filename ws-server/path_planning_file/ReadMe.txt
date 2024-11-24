get_nodes_deges.py：用于将原始geojson文件改成可以使用的nodes与edges文件
输入：hospital-path.geosjon
输出：nodes.geojson 与 edges.geojson
可以用于控制生成细节

server2.py:用于生成路径规划的路径，其实现函数于path_planning.py
输入：nodes.geojson 与 edges.geojson，生成网络图（要是没更新只需生成一次）
输入：start node 与 end node
输入：使用什么方式判断最短路径（距离/weight）
preferred_path = path_planning.Dijkstra(G, start_node, end_node, "weight")

输出（可选）：沿途路径、路径权重/距离、绘制3d图、生成path.geojson文件

path_planning.py在path_pplanning_file是旧的，只是给server2用，实际使用的在目录，也是叫path_planning


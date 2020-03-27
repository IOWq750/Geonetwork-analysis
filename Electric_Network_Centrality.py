# -*- coding: utf-8 -*-
import os

import networkx as nx

from Network_Scripts import nx_multi_shp as nxmlt

dir = r'D:\YandexDisk\Projects\Networks'
os.chdir(dir)
input_point = r'MES_Part_Points.shp'
input_line = r'MES_Part_Dissolve.shp'

G = nxmlt.read_shp(input_line, 'Name')
weights = nx.get_edge_attributes(G, 'Weight')
line_names = nx.get_edge_attributes(G, 'Name')
line_name_dict = {line: line_names[line] for line in line_names}
G_points = nx.read_shp(input_point)
point_types = nx.get_node_attributes(G_points, 'Point_Type')
point_names = nx.get_node_attributes(G_points, 'Name')
line_id = nx.get_edge_attributes(G, 'ORIG_FID')
generation_dict = {key: point_names[key] for key in point_types if point_types[key] == 'ЭС'}
substation_dict = {key: point_names[key] for key in point_types if point_types[key] == 'ПС'}
line_id_dict = {key: line_id[key] for key in line_id}
accum_weight = {}
topo_dist = {}
electric_centrality = {}

for ss in substation_dict:
    print(point_names[ss])
    i = 0
    try:
        path = nx.multi_source_dijkstra(G, sources=set(generation_dict.keys()), target=ss, weight='Weight')
        accum_weight[ss] = path[0]
        for point in path[1]:
            if point in point_names:
                i += 1
        topo_dist[ss] = i - 1
        print(path)
        print(topo_dist[ss])
        for n in len(path[1]):
            line_1 = (path[1][n], path[1][n + 1])
            line_2 = (path[1][n + 1], path[1][n])
            if line_1 in line_id_dict:
                weight_1 = weights[line_1]
                weight_2 = 100
            if line_2 in line_id_dict:
                weight_1 = 100
                weight_2 = weights[line_2]
            min(weight_1, weight_2)

            global_id = line_id_dict[(path[1][n], path[1][n + 1])]

    except:
        print('No path!!!', ss)
        continue

nx.set_node_attributes(G, accum_weight, 'Acc_Weight')
nx.set_node_attributes(G, topo_dist, 'Topo_dist')
nxmlt.write_shp(G, dir)
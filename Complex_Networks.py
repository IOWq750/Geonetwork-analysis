# -*- coding: utf-8 -*-
import networkx as nx
import import_export_shp
import os

os.chdir(r'D:\YandexDisk\Projects\Networks')
input_shp = 'Assort_4.shp'
G = nx.read_shp(input_shp)
# G = nx.Graph()
# G.add_nodes_from([1, 2, 3, 4, 5, 6, 7, 8, 9])
# G.add_edges_from([(1, 2), (1, 4), (1, 3), (2, 3), (2, 5), (2, 6), (3, 6), (3, 9), (4, 5), (4, 7), (5, 6), (5, 8), (6, 9),
#                   (6, 8), (7, 1), (7, 8), (7, 9), (8, 9), (8, 5)])
G2 = G.to_undirected()
r = nx.degree_pearson_correlation_coefficient(G2)
print(r)

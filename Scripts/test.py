# -*- coding: utf-8 -*-
import networkx as nx
import os

directory = r'F:\YandexDisk\Projects\Python_Exercise\Pereslavl_shp'
os.chdir(directory)
G = nx.read_shp('Roads.shp').to_undirected()
bc = nx.edge_betweenness_centrality(G)
print(bc)
delete_edge = []
for edge in G.edges():
    if bc[edge] > 0.2:
        delete_edge.append(edge)
G.remove_edges_from(delete_edge)
bc = nx.edge_betweenness_centrality(G)
nx.set_edge_attributes(G, bc, 'bc2')
nx.write_shp(G, directory)

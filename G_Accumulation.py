import arcpy
import networkx as nx
import osgeo
import os

arcpy.env.overwriteOutput = True
input_shp = arcpy.GetParameterAsText(0)
field = arcpy.GetParameterAsText(1)
output_workspace = arcpy.GetParameterAsText(2)
G = nx.read_shp(r'{0}'.format(input_shp))
nodes = G.nodes()
edges = G.edges()
total_dict = nx.get_edge_attributes(G, field)
for node in nodes:
    ancestors = list(nx.ancestors(G, node))
    sum_weight = 0
    for coords in ancestors:
        for edge in edges:
            if tuple([edge[0][0], edge[0][1]]) == tuple([coords[0], coords[1]]):
                sum_weight += int(total_dict[edge])
    arcpy.AddMessage(sum_weight)
    for edge in edges:
        if edge[0] == node:
            accum_edge = {edge: sum_weight}
            nx.set_edge_attributes(G, accum_edge, 'Accum')

nx.write_shp(G, r'{0}'.format(output_workspace))

import arcpy
import networkx as nx

arcpy.env.overwriteOutput = True
input_shp = arcpy.GetParameterAsText(0)
output_workspace = arcpy.GetParameterAsText(1)
G = nx.read_shp(r'{0}'.format(input_shp)).to_undirected()
nodes = G.nodes()
edges = G.edges()
cycle_edge_list = nx.find_cycle(G)
arcpy.AddMessage(cycle_edge_list)
for edge in edges:
    arcpy.AddMessage(edge)
    if edge in cycle_edge_list or [edge[1], edge[0]] in cycle_edge_list:
        nx.set_edge_attributes(G, {edge: 'Yes'}, 'IsCycle')
    else:
        nx.set_edge_attributes(G, {edge: 'No'}, 'IsCycle')
nx.write_shp(G, r'{0}'.format(output_workspace))

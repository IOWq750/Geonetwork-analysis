import networkx as nx
import import_export_shp
import arcpy

in_graph = arcpy.GetParameterAsText(0)
digraph = arcpy.GetParameterAsText(1)
weight = arcpy.GetParameterAsText(2)
output = arcpy.GetParameterAsText(3)

G = import_export_shp.convert_shp_to_graph(in_graph, digraph, 'false')
nodes = nx.eigenvector_centrality(G, max_iter=5000, weight=weight)
nx.set_node_attributes(G, nodes, 'EiC')
G.remove_edges_from(G.edges)
nx.write_shp(G, output)
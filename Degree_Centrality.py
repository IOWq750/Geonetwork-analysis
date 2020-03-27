import networkx as nx
import import_export_shp
import arcpy

in_graph = arcpy.GetParameterAsText(0)
multigraph = arcpy.GetParameterAsText(1)
multi_attr = arcpy.GetParameterAsText(2)
weight = arcpy.GetParameterAsText(3)
output = arcpy.GetParameterAsText(4)
digraph = arcpy.GetParameterAsText(5)

G = import_export_shp.convert_shp_to_graph(in_graph, digraph, multigraph, multi_attr)
if digraph == 'true':
    in_deg_centrality = nx.in_degree_centrality(G)
    out_deg_centrality = nx.out_degree_centrality(G)
    nx.set_node_attributes(G, in_deg_centrality, 'in_DC')
    nx.set_node_attributes(G, out_deg_centrality, 'out_DC')
else:
    deg_centrality = nx.degree_centrality(G)
    nx.set_node_attributes(G, deg_centrality, 'DC')

nx.write_shp(G, output)

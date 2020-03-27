# -*- coding: utf-8 -*-
import networkx as nx
import import_export_shp
import arcpy

if  __name__ == 'main':
    in_graph = arcpy.GetParameterAsText(0)
    multigraph = arcpy.GetParameterAsText(1)
    multi_attr = arcpy.GetParameterAsText(2)
    digraph = arcpy.GetParameterAsText(3)
    weight = arcpy.GetParameterAsText(4)
    output = arcpy.GetParameterAsText(5)

    G = import_export_shp.convert_shp_to_graph(in_graph, digraph, multigraph, multi_attr)
    nodes = nx.closeness_centrality(G, distance=weight)
    nx.set_node_attributes(G, nodes, 'CC')
    G.remove_edges_from(G.edges)
    import_export_shp.export_path_to_shp(G, multigraph, multi_attr, output)

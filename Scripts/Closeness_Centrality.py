# -*- coding: utf-8 -*-
import networkx as nx
from Auxillary_Scripts import import_export_shp as aux_ie
import arcpy

if __name__ == '__main__':
    in_graph = arcpy.GetParameterAsText(0)
    multigraph = arcpy.GetParameterAsText(1)
    multi_attr = arcpy.GetParameterAsText(2)
    digraph = arcpy.GetParameterAsText(3)
    weight = arcpy.GetParameterAsText(4)
    output = arcpy.GetParameterAsText(5)

    G = aux_ie.convert_shp_to_graph(in_graph.encode('utf-8'), digraph, multigraph, multi_attr)
    nodes = nx.closeness_centrality(G, distance=weight)
    nx.set_node_attributes(G, nodes, 'CC')
    G.remove_edges_from(G.edges)
    aux_ie.export_path_to_shp(G, multigraph, multi_attr, output.encode('utf-8'))
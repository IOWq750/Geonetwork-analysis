# -*- coding: utf-8 -*-
import networkx as nx
import os
import sys
curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, curdir)
import import_export_shp as aux_ie
import arcpy

if __name__ == '__main__':
    in_graph = arcpy.GetParameterAsText(0)
    multigraph = arcpy.GetParameterAsText(1)
    multi_attr = arcpy.GetParameterAsText(2)
    digraph = arcpy.GetParameterAsText(3)
    weight = arcpy.GetParameterAsText(4)
    output = arcpy.GetParameterAsText(5)

    G = aux_ie.convert_shp_to_graph(in_graph, digraph, multigraph, multi_attr)
    nodes = nx.closeness_centrality(G, distance=weight)
    nx.set_node_attributes(G, nodes, 'CC')
    aux_ie.export_path_to_shp(G, multigraph, multi_attr, output)

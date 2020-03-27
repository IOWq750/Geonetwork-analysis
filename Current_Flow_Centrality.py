# -*- coding: utf-8 -*-
import networkx as nx
import import_export_shp
import Betweenness_Centrality
import arcpy


def cur_flow_centrality(G, normalization, weight):
    cur_flow = nx.edge_current_flow_betweenness_centrality(G, normalization, weight)
    return cur_flow


if __name__ == 'main':
    in_graph = arcpy.GetParameterAsText(0)
    digraph = arcpy.GetParameterAsText(1)
    multigraph = arcpy.GetParameterAsText(2)
    multi_attr = arcpy.GetParameterAsText(3)
    weight = arcpy.GetParameterAsText(4)
    output = arcpy.GetParameterAsText(5)
    normalized = arcpy.GetParameterAsText(6)

    G = import_export_shp.convert_shp_to_graph(in_graph, digraph, multigraph, multi_attr)
    if normalized == 'false':
        normalization = False
    else:
        normalization = True
    ebc = cur_flow_centrality(G, normalization, weight)
    if multigraph == 'true':
        Betweenness_Centrality.betweenness_multiedge_distribution(G, ebc)
    else:
        nx.set_edge_attributes(G, ebc, 'CFC')
    import_export_shp.export_path_to_shp(G, multigraph, multi_attr, output)
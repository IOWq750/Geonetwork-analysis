# -*- coding: utf-8 -*-
import networkx as nx
from auxillary_scripts import import_export_shp as aux_ie
import arcpy


def degree_centrality(in_graph, multigraph, multi_attr, output, digraph):
    G = aux_ie.convert_shp_to_graph(in_graph, digraph, multigraph, multi_attr)
    if digraph == 'true':
        in_deg_centrality = nx.in_degree_centrality(G)
        out_deg_centrality = nx.out_degree_centrality(G)
        nx.set_node_attributes(G, in_deg_centrality, 'in_DC')
        nx.set_node_attributes(G, out_deg_centrality, 'out_DC')
    else:
        deg_centrality = nx.degree_centrality(G)
        nx.set_node_attributes(G, deg_centrality, 'DC')
    G.remove_edges_from(G.edges)
    nx.write_shp(G, output.encode('utf-8'))


if __name__ == '__main__':
    in_graph = arcpy.GetParameterAsText(0)
    multigraph = arcpy.GetParameterAsText(1)
    multi_attr = arcpy.GetParameterAsText(2)
    output = arcpy.GetParameterAsText(3)
    # Networkx tool doesn't support directed graph degree centrality
    digraph = 'false'

    degree_centrality(in_graph.encode('utf-8'), multigraph, multi_attr, output.encode('utf-8'), digraph)



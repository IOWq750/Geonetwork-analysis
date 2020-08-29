# -*- coding: CP1251 -*-
import networkx as nx
import os
import sys
curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, curdir)
import import_export_shp as aux_ie
import arcpy


def node_betweenness_centrality(G, normalization, weight):
    """Calculation of betweenness centrality for nodes"""
    bc = nx.betweenness_centrality(G, normalized=normalization, weight=weight)
    nx.set_node_attributes(G, bc, 'BC')


def edge_betweenness_centrality(G, normalization, weight):
    """Calculation of betweenness centrality for edges"""
    ebc = nx.edge_betweenness_centrality(G, normalized=normalization, weight=weight)
    return ebc


def betweenness_multiedge_distribution(G, ebc, distributed):
    """Distribution of value equally between parallel edges in multigraph"""
    multiedges = [(element[0], element[1]) for element in G.edges(keys=True)]
    edge_betweenness_values = {}
    for edge in multiedges:
        count = multiedges.count(edge)
        if distributed == 'true':
            betweenness = ebc[edge]/count
        else:
            betweenness = ebc[edge]
        for item in G.edges(keys=True):
            if edge == tuple([item[0], item[1]]):
                edge_betweenness_values[item] = betweenness
    nx.set_edge_attributes(G, edge_betweenness_values, 'BC')


if __name__ == "__main__":
    in_graph = arcpy.GetParameterAsText(0)
    digraph = arcpy.GetParameterAsText(1)
    multigraph = arcpy.GetParameterAsText(2)
    multi_attr = arcpy.GetParameterAsText(3)
    weight = arcpy.GetParameterAsText(4)
    output = arcpy.GetParameterAsText(5)
    normalized = arcpy.GetParameterAsText(6)
    distributed = arcpy.GetParameterAsText(7)

    G = aux_ie.convert_shp_to_graph(in_graph, digraph, multigraph, multi_attr)
    if normalized == 'false':
        normalization = False
    else:
        normalization = True
    node_betweenness_centrality(G, normalization, weight)
    ebc = edge_betweenness_centrality(G, normalization, weight)
    if multigraph == 'true':
        betweenness_multiedge_distribution(G, ebc, distributed)
    else:
        nx.set_edge_attributes(G, ebc, 'BC')
    aux_ie.export_graph_to_shp(G, multigraph, multi_attr, output)


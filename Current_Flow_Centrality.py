# -*- coding: utf-8 -*-
import networkx as nx
import import_export_shp
import arcpy


def cur_flow_centrality(G, normalization, weight, sources, targets):
    cur_flow = nx.edge_current_flow_betweenness_centrality_subset(G, sources, targets, normalization, weight)
    arcpy.AddMessage(cur_flow)
    #nx.set_edge_attributes(G, cur_flow, 'ini_CFC')
    return cur_flow


def node_type_extraction(points, fieldname, source_name, target_name):
    nodes = nx.read_shp(r'{0}'.format(points))
    point_type_dict = nx.get_node_attributes(nodes, fieldname)
    sources = [key for key in point_type_dict if point_type_dict[key].decode('utf-8') == source_name]
    targets = [key for key in point_type_dict if point_type_dict[key].decode('utf-8') == target_name]
    return sources, targets


def betweenness_multiedge_distribution(G, ebc):
    """Distribution of value equally between parallel edges in multigraph"""
    multiedges = [(element[0], element[1]) for element in G.edges(keys=True)]
    edge_betweenness_values = {}
    for edge in multiedges:
        count = multiedges.count(edge)
        try:
            arcpy.AddMessage(ebc[edge])
            betweenness = ebc[edge]/count
            for item in G.edges(keys=True):
                if edge == tuple([item[0], item[1]]):
                    edge_betweenness_values[item] = betweenness
        except:
            pass
    nx.set_edge_attributes(G, edge_betweenness_values, 'CFC')


if __name__ == '__main__':
    in_lines = arcpy.GetParameterAsText(0)
    in_points = arcpy.GetParameterAsText(1)
    field = arcpy.GetParameterAsText(2)
    ss = arcpy.GetParameterAsText(3)
    es = arcpy.GetParameterAsText(4)
    digraph = arcpy.GetParameterAsText(5)
    multigraph = arcpy.GetParameterAsText(6)
    multi_attr = arcpy.GetParameterAsText(7)
    weight = arcpy.GetParameterAsText(8)
    output = arcpy.GetParameterAsText(9)
    normalized = arcpy.GetParameterAsText(10)

    G = import_export_shp.convert_shp_to_graph(in_lines, digraph, multigraph, multi_attr)
    substations, generation = node_type_extraction(in_points, field, ss, es)
    if normalized == 'false':
        normalization = False
    else:
        normalization = True
    ebc = cur_flow_centrality(G, normalization, weight, generation, substations)
    if multigraph == 'true':
        betweenness_multiedge_distribution(G, ebc)
    else:
        nx.set_edge_attributes(G, ebc, 'CFC')
    import_export_shp.export_path_to_shp(G, multigraph, multi_attr, output)

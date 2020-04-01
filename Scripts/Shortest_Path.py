# -*- coding: utf-8 -*-
import networkx as nx
import import_export_shp
import arcpy


def calculate_shortest_path(G, source_point, target_point, output_workspace, weight_attribute, method):
    """Calculates the shortest path between two nodes in graph represented as shapefiles.

        Parameters
        ----------
        G: NetworkX graph object

        source_point: feature layer
            Feature layer with selected point which should be the start of the path

        target_point: feature layer
            Feature layer with selected point which should be the end of the path

        output_workspace: folder path
            Directory where output shapefile of the path should be added

        weight_attribute: numeric field
            Field of polyline shapefile, values from which should be accounted as weights in graph

        method: 'dijkstra' or 'bellman-ford'
            Algorithm of shortest path calculation

        Returns
        -------
        path as a list of node coordinates list
        """

    arcpy.env.overwriteOutput = True
    arcpy.FeatureClassToFeatureClass_conversion(source_point, output_workspace, 'Source.shp')
    arcpy.FeatureClassToFeatureClass_conversion(target_point, output_workspace, 'Target.shp')
    source = nx.read_shp(r'{0}'.format(output_workspace + '\Source.shp'))
    target = nx.read_shp(r'{0}'.format(output_workspace + '\Target.shp'))
    path = nx.shortest_path(G, list(source.nodes())[0], list(target.nodes())[0], weight_attribute, method)
    arcpy.AddMessage(path)
    return path


def path_to_graph(G, path):
    path_edges = []
    for i in range(len(path) - 1):
        for edge in G.edges():
            if tuple([tuple(path[i]), tuple(path[i + 1])]) == tuple(edge):
                path_edges.append(edge)
            elif tuple([tuple(path[i + 1]), tuple(path[i])]) == tuple(edge):
                path_edges.append(edge)
    delete_edge = []
    for edge in G.edges():
        if (edge[0], edge[1]) not in path_edges:
            delete_edge.append(edge)
    G.remove_edges_from(delete_edge)
    return G


if __name__ == '__main__':
    in_graph = arcpy.GetParameterAsText(0)
    digraph = arcpy.GetParameterAsText(1)
    multigraph = arcpy.GetParameterAsText(2)
    multi_attr = arcpy.GetParameterAsText(3)
    source = arcpy.GetParameterAsText(4)
    target = arcpy.GetParameterAsText(5)
    output = arcpy.GetParameterAsText(6)
    weight = arcpy.GetParameterAsText(7)
    method = arcpy.GetParameterAsText(8)

    G = import_export_shp.convert_shp_to_graph(in_graph, digraph, multigraph, multi_attr)
    shortest_path = calculate_shortest_path(G, source, target, output, weight, method)
    G = path_to_graph(G, shortest_path)
    import_export_shp.export_path_to_shp(G, multigraph, multi_attr, method)

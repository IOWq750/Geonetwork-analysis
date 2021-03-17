# -*- coding: utf-8 -*-
import os
import networkx as nx
from osgeo import ogr, osr
import import_export_shp as aux_ie


def topological_distance(power_lines, power_points, name, weight, voltage, output_workspace):
    """ Calculation of electrical network centrality as a number of shortest paths between each substation and
    topologically closest generation points.

            Parameters
            ----------
            power_lines: str
                 path to the polyline shapefile with all power lines

            power_points: str
                path to the point shapefile with all power points (substations, generation) with attribute 'Point_Type',
                all generation points have value 'ЭС', all substations have values 'ПС'

            name: str
                name field for power lines as a third key for multigraph

            weight: str
                weight field name for power lines (inverted capacity)

            voltage: str
                voltage field name for power lines

            output_workspace: str
                path to the output directory

            Returns
            -------
            number of nodes (original power points without orphan links), number of generation points,
            number of substation points"""

    G_network = aux_ie.convert_shp_to_graph(power_lines, "false", "true", name)
    G_points = nx.read_shp(power_points)
    number_nodes = int(G_points.number_of_nodes())
    dict_point_type = {}
    t1 = nx.get_node_attributes(G_points, 'Point_Type')
    nodes_from_points = G_points.nodes
    for node_p in nodes_from_points:
        dict_point_type[node_p] = t1[node_p]
    nx.set_node_attributes(G_network, dict_point_type, 'type')
    nodes_from_network = G_network.nodes
    generation = set()
    node_dict = nx.get_node_attributes(G_network, 'type')
    for node in nodes_from_network:
        if node in node_dict:
            if node_dict[node] == 'ЭС':
                generation.add(node)
    generation_count = len(generation)
    substation_count = number_nodes - generation_count
    # G_network, trace_dict = trace_lines(G_network, voltage)
    shortest_path = nx.multi_source_dijkstra_path(G_network, generation, weight=weight)
    aux_ie.export_path_to_shp(G_network, "true", output_workspace, trace_dict + [shortest_path])
    return number_nodes, generation_count, substation_count


if __name__ == "__main__":
    os.chdir(r'f:\YandexDisk\Projects\RFFI_Transport\Ural_Siberia')
    power_lines = 'Lines_P.shp'
    power_points = 'Points_P.shp'
    path_output = 'Output'

    output_shp = os.path.join(path_output, 'topological_dist.shp')
    edges = os.path.join(path_output, 'edges.shp')
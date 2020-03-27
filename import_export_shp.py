# -*- coding: utf-8 -*-
import networkx as nx
import nx_multi_shp
import os


def convert_shp_to_graph(input_shp, directed, multigraph, parallel_edges_attribute):
    """Converts a shapefile to networkx graph object in accordance to the given parameters.
        It can directed or undirected, simple graph or multigraph

        Parameters
        ----------
        input_shp: shapefile path

        directed: 'true' or 'false'
            If value is true – directed graph will be created.
            If value is false - undirected graph will be created

        multigraph: 'true' or 'false'
            If value is true – multigraph will be created
            If value is false – simple graph will be created

        parallel_edges_attribute: string
            Field of the shapefile which allows to distinguish parallel edges.
            Note that it could be a field of different types, but all values of this attribute should be filled
        Returns
        -------
        Graph
        """
    if multigraph == 'true':
        G = nx_multi_shp.read_shp(r'{0}'.format(input_shp), parallel_edges_attribute, simplify=True,
                                  geom_attrs=True, strict=True)
    else:
        G = nx.read_shp(r'{0}'.format(input_shp))
    if directed == 'true':
        graph = G
    else:
        graph = G.to_undirected()
    return graph


def export_path_to_shp(G, multy, multy_attribute, output_workspace):
    for item in ['edges.shp', 'nodes,shp']:
        filename = os.path.join(output_workspace, item)
        if os.path.exists(filename):
            os.remove(filename)
    if multy == 'true':
        nx_multi_shp.write_shp(G, multy_attribute, output_workspace)
    else:
        nx.write_shp(G, output_workspace)
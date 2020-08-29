# -*- coding: utf-8 -*-
import os
import networkx as nx
from osgeo import ogr, osr
import import_export_shp as aux_ie


def el_centrality(power_lines, power_points, path_output):
    G_network = aux_ie.convert_shp_to_graph(power_lines, "false", "true", "Name")
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
    shortest_path = nx.multi_source_dijkstra_path(G_network, generation)
    aux_ie.export_path_to_shp(G_network, "true", path_output, shortest_path)
    return number_nodes


def create_cpg(shapefile):
    """Encoding description file creation"""
    with open('{}.cpg'.format(shapefile), 'w') as cpg:
        cpg.write('cp1251')


def merge_features_geometry(features):
    multiline = ogr.Geometry(ogr.wkbMultiLineString)
    for feature in features:
        multiline.AddGeometry(feature.GetGeometryRef())
    return multiline


def geometry_extraction(layer):
    geom_field = ogr.FieldDefn('centroid', ogr.OFTString)
    geom_field.SetWidth(100)
    layer.CreateField(geom_field)
    for feature in layer:
        geom = feature.GetGeometryRef()
        centroid = geom.Centroid().ExportToWkt()
        feature.SetField("centroid", centroid)
        layer.SetFeature(feature)
    layer.ResetReading()


def dissolve_layer(layer, field_list, stats_dict):
    """Grouping features by name and centroid coordinates

        Parameters
        ----------
        layer : ogr layer of a shapefile
           name of layer to read.

        field_list: list
            Attributes in shapefile for dissolving by their unique values

        stats_dict:  dictionary
            keys – name of attribute fields for statistics calculation, values – type of statistics

        Returns
        -------
        list of features grouped by attribute values"""

    grouped_features = {}
    for feature in layer:
        groupby = []
        for field in field_list:
            group_field = feature.GetField(field)
            groupby.append(group_field)
        groupby = tuple(groupby)
        if groupby in grouped_features:
            grouped_features[groupby] += [feature]
        else:
            grouped_features[groupby] = [feature]
    dissolved_features = []
    layer.ResetReading()
    for groupby in grouped_features:
        dissolved_feature = {}
        for i in range(0, len(field_list)):
            dissolved_feature[field_list[i]] = groupby[i]
        dissolved_feature['geometry'] = merge_features_geometry(grouped_features[groupby])
        for stats in stats_dict:
            if stats == 'count':
                dissolved_feature[stats] = len(grouped_features[groupby])
            if stats == 'sum':
                dissolved_feature[stats] = sum([feature.GetField(stats_dict[stats]) for feature in grouped_features[groupby]])
        dissolved_features.append(dissolved_feature)
    return dissolved_features


def betweenness_multiedge_distribution(G, ebc):
    """Distribution of value between parallel edges in multigraph"""
    multiedges = [(element[0], element[1]) for element in G.edges(keys=True)]
    edge_betweenness_values = {}
    for edge in multiedges:
        betweenness = ebc[edge]
        for item in G.edges(keys=True):
            if edge == tuple([item[0], item[1]]):
                edge_betweenness_values[item] = betweenness
    nx.set_edge_attributes(G, edge_betweenness_values, 'BC')


def feature_creation(layer, dissolved_lines):
    for line in dissolved_lines:
        feature = ogr.Feature(layer.GetLayerDefn())
        for key in line.keys():
            if key == 'geometry':
                feature.SetGeometry(line[key])
            else:
                feature.SetField(key, line[key])
        layer.CreateFeature(feature)


def centrality_normalization(dst_layer, node_number):
    for feature in dst_layer:
        count_field = feature.GetField('count')
        el_cen = float(count_field) / float((node_number * (node_number - 1)))
        print(el_cen)
        feature.SetField('El_Cen', el_cen)
        layer.SetFeature(feature)


if __name__ == "__main__":
    os.chdir(r'F:\YandexDisk\Projects\RFFI_Transport\Ural_Siberia')
    power_lines = 'Lines_pCopy.shp'
    power_points = 'Points_p.shp'
    path_output = 'Output'

    node_number = el_centrality(power_lines, power_points, path_output)
    edges = os.path.join(path_output, 'edges.shp')
    create_cpg(edges)
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataSource = driver.Open(edges, 1)
    layer = dataSource.GetLayer()
    spatialRef = str(layer.GetSpatialRef())
    geometry_extraction(layer)
    dissolved_lines = dissolve_layer(layer, ['name', 'centroid'], {'count': 'FID'})
    data_source = driver.CreateDataSource(os.path.join(path_output, 'el_centrality.shp'))
    dst_layer = data_source.CreateLayer(edges, osr.SpatialReference(spatialRef), ogr.wkbMultiLineString,
                                        options=["ENCODING=CP1251"])
    field_name = ogr.FieldDefn('name', ogr.OFTString)
    field_name.SetWidth(254)
    dst_layer.CreateField(field_name)
    dst_layer.CreateField(ogr.FieldDefn('count', ogr.OFTInteger))
    field_centroid = ogr.FieldDefn('centroid', ogr.OFTString)
    field_centroid.SetWidth(254)
    dst_layer.CreateField(field_centroid)
    feature_creation(dst_layer, dissolved_lines)
    field_el_centrality = ogr.FieldDefn('El_Cen', ogr.OFTReal)
    field_el_centrality.SetPrecision(5)
    dst_layer.CreateField(field_el_centrality)
    centrality_normalization(dst_layer, node_number)

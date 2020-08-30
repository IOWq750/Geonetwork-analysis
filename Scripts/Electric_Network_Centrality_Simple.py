# -*- coding: utf-8 -*-
import os
import networkx as nx
from osgeo import ogr, osr
import import_export_shp as aux_ie


def el_centrality(power_lines, power_points, weight, path_output):
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
    generation_count = len(generation)
    substations_count = number_nodes - generation_count
    shortest_path = nx.multi_source_dijkstra_path(G_network, generation, weight=weight)
    aux_ie.export_path_to_shp(G_network, "true", path_output, shortest_path)
    return number_nodes, generation_count, substations_count


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
        feature.SetField('centroid', centroid)
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
        for i in range(len(field_list)):
            dissolved_feature[field_list[i]] = groupby[i]
        dissolved_feature['group'] = merge_features_geometry(grouped_features[groupby])
        for stats in stats_dict:
            if stats == 'count':
                dissolved_feature[stats] = len(grouped_features[groupby])
            if stats == 'sum':
                dissolved_feature[stats] = sum([feature.GetField(stats_dict[stats]) for feature in grouped_features[groupby]])
        dissolved_features.append(dissolved_feature)
    return dissolved_features


def feature_creation(layer, dissolved_lines):
    layerDefinition = layer.GetLayerDefn()
    for i in range(layerDefinition.GetFieldCount()):
        field_name = layerDefinition.GetFieldDefn(i).GetName()
    for line in dissolved_lines:
        feature = ogr.Feature(layer.GetLayerDefn())
        for key in line.keys():
            if key == 'group':
                feature.SetGeometry(line[key])
            else:
                feature.SetField(key, line[key])
        layer.CreateFeature(feature)


def centrality_normalization(layer, node_number):
    for feature in layer:
        count_field = feature.GetField('count')
        el_cen = float(count_field) / (node_number * (node_number - 1))
        feature.SetField('El_Cen', el_cen)
        layer.SetFeature(feature)


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


if __name__ == "__main__":
    os.chdir(r'F:\YandexDisk\Projects\RFFI_Transport\Ural_Siberia')
    power_lines = 'Lines_p.shp'
    power_points = 'Points_p.shp'
    path_output = 'Output'

    node_number = el_centrality(power_lines, power_points, 'Weight', path_output)[2]
    edges = os.path.join(path_output, 'edges.shp')
    create_cpg(edges)
    dataSource = ogr.GetDriverByName('ESRI Shapefile').Open(edges, 1)
    layer = dataSource.GetLayer()
    geometry_extraction(layer)
    field_types_dict = {'Integer': ogr.OFTInteger,
                        'Real': ogr.OFTReal,
                        'String': ogr.OFTString}
    fields = {}
    layerDefinition = layer.GetLayerDefn()
    for i in range(layerDefinition.GetFieldCount()):
        field_name = layerDefinition.GetFieldDefn(i).GetName()
        field_type = layerDefinition.GetFieldDefn(i).GetFieldTypeName(layerDefinition.GetFieldDefn(i).GetType())
        fields[field_name] = field_type
    del fields['ident']
    dissolved_lines = dissolve_layer(layer, fields.keys(), {'count': 'FID'})
    output_shp = os.path.join(path_output, 'el_centrality.shp')
    out_ds = ogr.GetDriverByName('ESRI Shapefile').CreateDataSource(output_shp)
    dst_layer = out_ds.CreateLayer('el_centrality.shp', osr.SpatialReference(str(layer.GetSpatialRef())),
                                   ogr.wkbMultiLineString, options=["ENCODING=CP1251"])
    for key in fields:
        dst_layer.CreateField(ogr.FieldDefn(key), field_types_dict[fields[key]])
    dst_layer.CreateField(ogr.FieldDefn('El_Cen'), ogr.OFTReal)
    dst_layer.CreateField(ogr.FieldDefn('Count'), ogr.OFTReal)
    temp = ogr.GetDriverByName('ESRI Shapefile').Open(output_shp, 1)
    temp_layer = temp.GetLayer(0)
    layerDefinition = temp_layer.GetLayerDefn()
    feature_creation(dst_layer, dissolved_lines)
    for i in range(layerDefinition.GetFieldCount()):
        fieldName = layerDefinition.GetFieldDefn(i).GetName()
        fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
        fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
        print(fieldName, fieldType)

    centrality_normalization(dst_layer, node_number)
    #betweenness_multiedge_distribution()

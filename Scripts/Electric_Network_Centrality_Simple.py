# -*- coding: utf-8 -*-
import os
import networkx as nx
from osgeo import ogr, osr
import import_export_shp as aux_ie


def el_centrality(power_lines, power_points, path_output):
    G_network = aux_ie.convert_shp_to_graph(power_lines, "false", "true", "Name")
    G_points = nx.read_shp(power_points)
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
                print(node, ' is generation')
                generation.add(node)
    shortest_path = nx.multi_source_dijkstra_path(G_network, generation)
    aux_ie.export_path_to_shp(G_network, "true", 'Name', path_output, shortest_path)


def create_cpg(shapefile):
    """Encoding description file creation"""
    with open('{}.cpg'.format(shapefile), 'w') as cpg:
        cpg.write('cp1251')


def process_layer(layer):
    """Merging features by name"""
    grouped_features = {}
    geom_field = ogr.FieldDefn("Geometry", ogr.OFTString)
    geom_field.SetWidth(50)
    layer.CreateField(geom_field)
    feature_names = []
    for feature in layer:
        feature_name = feature.GetField('name')
        if feature_name not in feature_names:
            expression = "name = '" + feature_name + "'"
            layer.SetAttributeFilter(expression)
            print(expression)
            feature_count = layer.GetFeatureCount()
            geom = feature.GetGeometryRef()
            centroid = geom.Centroid().ExportToWkt()
            print(centroid)
            feature.SetField(geom_field, str(123)) #str(centroid)
            feature_names.append(feature_name)
        else:
            continue
        print(feature_count)
        layer.SetAttributeFilter("FID > -1")
        feature_geom = feature.GetGeometryRef()


# def process_layer(layer):
#     """Merging features by name"""
#     grouped_features = {}
#     for feature in layer:
#         feature_geom = feature.GetGeometryRef()
#         feature_name = feature.GetField('name')
#         if feature_name in grouped_features:
#             grouped_features[feature_name] += [feature]
#         else:
#             grouped_features[feature_name] = [feature]
#     print(grouped_features)
#     records = []
#     for feature_name in grouped_features:
#         record = {}
#         record['name'] = feature_name
#         record['geometry'] = merge_features_geometry(grouped_features[feature_name])
#         record['count'] = len(grouped_features[feature_name])
#         records.append(record)
#     return records


def simplify(features):
    threshold = 10
    for x in range(len(features) - 1):
        if not features[x]:
            continue
        for y in range(x + 1, len(features)):
            if not features[y]:
                continue
            coord_lst = features[x].GetGeometryRef().GetPoints() + features[y].GetGeometryRef().GetPoints()
            points = []
            for coords in coord_lst:
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coords)
                points.append(point)
            if (points[0].Distance(points[2]) < threshold and points[1].Distance(points[3]) < threshold) or (
                    points[1].Distance(points[2]) < threshold and points[0].Distance(points[3]) < threshold):
                features[y] = None
    features = list(filter(lambda a: a, features))
    return features


def merge_features_geometry(features):
    features = simplify(features)
    multiline = ogr.Geometry(ogr.wkbMultiLineString)
    for feature in features:
        multiline.AddGeometry(feature.GetGeometryRef())
    return multiline


os.chdir(r'F:\YandexDisk\Projects\RFFI_Transport\Ural_Siberia')
power_lines = 'Lines_p.shp'
power_points = 'Points_p.shp'
path_output = 'Output'
# driver = ogr.GetDriverByName('ESRI Shapefile')
# dataSource = driver.Open(power_lines, 1)
# src_layer = dataSource.GetLayer()
# source_prj = src_layer.GetSpatialRef()
# print(source_prj)


el_centrality(power_lines, power_points, path_output)
edges = os.path.join(path_output, 'edges.shp')
create_cpg(edges)
driver = ogr.GetDriverByName('ESRI Shapefile')
dataSource = driver.Open(edges, 1)
layer = dataSource.GetLayer()
records = process_layer(layer)

data_source = driver.CreateDataSource(os.path.join(path_output, 'el_centrality.shp'))
dst_layer = data_source.CreateLayer(edges, None, ogr.wkbMultiLineString, options=["ENCODING=CP1251"])
field_name = ogr.FieldDefn('name', ogr.OFTString)
field_name.SetWidth(80)
dst_layer.CreateField(field_name)
dst_layer.CreateField(ogr.FieldDefn('count', ogr.OFTInteger))

for record in records:
    feature = ogr.Feature(dst_layer.GetLayerDefn())
    for key in record.keys():
        if key == 'geometry':
            feature.SetGeometry(record[key])
        else:
            feature.SetField(key, record[key])
    dst_layer.CreateFeature(feature)


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


def merge_features_geometry(features):
    multiline = ogr.Geometry(ogr.wkbMultiLineString)
    for feature in features:
        multiline.AddGeometry(feature.GetGeometryRef())
    return multiline


def process_layer(layer):
    """Grouping features by name and centroid coordinates"""
    geom_field = ogr.FieldDefn('centroid', ogr.OFTString)
    geom_field.SetWidth(100)
    layer.CreateField(geom_field)
    for feature in layer:
        geom = feature.GetGeometryRef()
        centroid = geom.Centroid().ExportToWkt()
        feature.SetField("centroid", centroid)
        feature_name = feature.GetField('name')
        feature.SetField("name", feature_name)
        layer.SetFeature(feature)
    layer.ResetReading()
    grouped_features = {}
    for feature in layer:
        feature_name = feature.GetField('name')
        feature_centroid = feature.GetField('centroid')
        groupby = (feature_name, feature_centroid)
        if groupby in grouped_features:
            grouped_features[groupby] += [feature]
        else:
            grouped_features[groupby] = [feature]
    dissolved_features = []
    for groupby in grouped_features:
        dissolved_feature = {}
        dissolved_feature['name'] = groupby[0]
        dissolved_feature['centroid'] = groupby[1]
        dissolved_feature['geometry'] = merge_features_geometry(grouped_features[groupby])
        dissolved_feature['count'] = len(grouped_features[groupby])
        dissolved_features.append(dissolved_feature)
    return dissolved_features


os.chdir(r'F:\YandexDisk\Projects\RFFI_Transport\Ural_Siberia')
power_lines = 'Lines_p.shp'
power_points = 'Points_p.shp'
path_output = 'Output'

el_centrality(power_lines, power_points, path_output)
edges = os.path.join(path_output, 'edges.shp')
create_cpg(edges)
driver = ogr.GetDriverByName('ESRI Shapefile')
dataSource = driver.Open(edges, 1)
layer = dataSource.GetLayer()
spatialRef = str(layer.GetSpatialRef())
dissolved_lines = process_layer(layer)

data_source = driver.CreateDataSource(os.path.join(path_output, 'el_centrality.shp'))
dst_layer = data_source.CreateLayer(edges, osr.SpatialReference(spatialRef), ogr.wkbMultiLineString, options=["ENCODING=CP1251"])
field_name = ogr.FieldDefn('name', ogr.OFTString)
field_name.SetWidth(254)
dst_layer.CreateField(field_name)
dst_layer.CreateField(ogr.FieldDefn('count', ogr.OFTInteger))
field_group = ogr.FieldDefn('centroid', ogr.OFTString)
field_group.SetWidth(254)
dst_layer.CreateField(field_group)

for line in dissolved_lines:
    feature = ogr.Feature(dst_layer.GetLayerDefn())
    for key in line.keys():
        if key == 'geometry':
            feature.SetGeometry(line[key])
        else:
            feature.SetField(key, line[key])
    dst_layer.CreateFeature(feature)

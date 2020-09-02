# -*- coding: utf-8 -*-
import os
import networkx as nx
from osgeo import ogr, osr
import import_export_shp as aux_ie


def el_centrality(power_lines, power_points, weight, output_workspace):
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
    aux_ie.export_path_to_shp(G_network, "true", output_workspace, shortest_path)
    return number_nodes, generation_count, substations_count


def create_cpg(shapefile):
    """Encoding description file creation"""
    with open('{}.cpg'.format(shapefile), 'w') as cpg:
        cpg.write('cp1251')


def geometry_extraction(layer):
    centroid = ogr.FieldDefn('centroid', ogr.OFTString)
    layer.CreateField(centroid)
    for feature in layer:
        geom = feature.GetGeometryRef()
        centroid = geom.Centroid().ExportToWkt()
        feature.SetField('centroid', centroid)
        layer.SetFeature(feature)
    layer.ResetReading()


# def import_field_schema(layer, output_shp, delete_fields=None, add_field=None):
#     """Import field list from input layer to the shapefile in path_output directory excluding the list of delete_fields
#
#         Parameters
#         ----------
#         layer: datasource.GetLayer() object
#
#         output_shp: string
#         directory of output shapefile
#
#         delete_fields: list (optional)
#         list of fields that should be excluded from final shp
#
#         add_field: dictionary
#         dictionary kind of {fieldname: fieldtype} to add in output datasource
#
#         Returns
#         -------
#         datasource.GetLayer() object of final shapefile, dictionary of field schema {fieldName: fieldType}
#     """
#
#     output_fields = {}
#     layer_definition = layer.GetLayerDefn()
#     for i in range(layer_definition.GetFieldCount()):
#         field_name = layer_definition.GetFieldDefn(i).GetName()
#         field_type = layer_definition.GetFieldDefn(i).GetType()
#         output_fields[field_name] = field_type
#     if delete_fields is not None:
#         for field in delete_fields:
#             del output_fields[field]
#     input_fields = output_fields.copy()
#     if add_field is not None:
#         for field in add_field:
#             output_fields[field] = add_field[field]
#     out_ds = ogr.GetDriverByName('ESRI Shapefile').CreateDataSource(output_shp)
#     dst_layer = out_ds.CreateLayer(os.path.basename(output_shp), osr.SpatialReference(str(layer.GetSpatialRef())),
#                                    ogr.wkbMultiLineString, options=["ENCODING=CP1251"])
#     for key in output_fields:
#         new_field = ogr.FieldDefn(key)
#         dst_layer.CreateField(new_field, output_fields[key])
#         print(key, output_fields[key])
#     return input_fields, output_fields, dst_layer


def import_field_schema(layer, output_shp, delete_fields=None, add_field=None):
    """Import field list from input layer to the shapefile in path_output directory excluding the list of delete_fields

        Parameters
        ----------
        layer: datasource.GetLayer() object

        output_shp: string
        directory of output shapefile

        delete_fields: list (optional)
        list of fields that should be excluded from final shp

        add_field: dictionary
        dictionary kind of {fieldname: fieldtype} to add in output datasource

        Returns
        -------
        datasource.GetLayer() object of final shapefile, dictionary of field schema {fieldName: fieldType}
    """

    out_ds = ogr.GetDriverByName('ESRI Shapefile').CreateDataSource(output_shp)
    dst_layer = out_ds.CreateLayer(os.path.basename(output_shp), osr.SpatialReference(str(layer.GetSpatialRef())),
                                   ogr.wkbMultiLineString, options=["ENCODING=CP1251"])
    dst_layer.CreateFields(layer.schema)
    output_fields = {}
    layer_definition = layer.GetLayerDefn()
    for i in range(layer_definition.GetFieldCount()):
        field_name = layer_definition.GetFieldDefn(i).GetName()
        field_type = layer_definition.GetFieldDefn(i).GetType()
        output_fields[field_name] = field_type
    if delete_fields is not None:
        for field in delete_fields:
            del output_fields[field]
    input_fields = output_fields.copy()
    if add_field is not None:
        for field in add_field:
            output_fields[field] = add_field[field]
    out_ds = ogr.GetDriverByName('ESRI Shapefile').CreateDataSource(output_shp)
    dst_layer = out_ds.CreateLayer(os.path.basename(output_shp), osr.SpatialReference(str(layer.GetSpatialRef())),
                                   ogr.wkbMultiLineString, options=["ENCODING=CP1251"])
    for key in output_fields:
        new_field = ogr.FieldDefn(key)
        dst_layer.CreateField(new_field, output_fields[key])
        print(key, output_fields[key])
    return input_fields, output_fields, dst_layer


def dissolve_layer(layer, field_list, stats_dict=None):
    """Grouping features by name and centroid coordinates

        Parameters
        ----------
        layer : ogr layer of a shapefile
           name of layer to read.

        field_list: list
            Attributes in shapefile for dissolving by their unique values

        stats_dict:  dictionary (optional)
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
        if groupby not in grouped_features:
            grouped_features[groupby] = [feature]
        else:
            grouped_features[groupby] += [feature]
    layer.ResetReading()
    dissolved_features = []
    for groupby in grouped_features:
        dissolved_feature = {}
        for i in range(len(field_list)):
            dissolved_feature[field_list[i]] = groupby[i]
        merged_line = ogr.Geometry(ogr.wkbMultiLineString)
        for feature in grouped_features[groupby]:
            merged_line.AddGeometry(feature.GetGeometryRef())
        dissolved_feature['group'] = merged_line
        if stats_dict is not None:
            for stats in stats_dict:
                if stats == 'count':
                    dissolved_feature[stats] = len(grouped_features[groupby])
                # if stats == 'sum':
                #     dissolved_feature[stats] = sum([feature.GetField(stats_dict[stats]) for feature in grouped_features[groupby]])
        dissolved_features.append(dissolved_feature)
    return dissolved_features


def feature_creation(output_shp, dissolved_lines):
    out_ds = ogr.GetDriverByName('ESRI Shapefile').Open(output_shp, 1)
    layer = out_ds.GetLayer()
    for line in dissolved_lines:
        feature = ogr.Feature(layer.GetLayerDefn())
        for key in line.keys():
            if key == 'group':
                feature.SetGeometry(line[key])
            else:
                feature.SetField(key, line[key])
        layer.CreateFeature(feature)


def centrality_normalization(shp, node_number):
    out_ds = ogr.GetDriverByName('ESRI Shapefile').Open(shp, 1)
    layer = out_ds.GetLayer()
    for feature in layer:
        count_field = feature.GetField('count')
        print(count_field)
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

    output_shp = os.path.join(path_output, 'el_centrality.shp')
    edges = os.path.join(path_output, 'edges.shp')
    node_count, generation_count, substation_count = el_centrality(power_lines, power_points, 'Weight', path_output)
    create_cpg(edges)
    data_source = ogr.GetDriverByName('ESRI Shapefile').Open(edges, 1)
    layer = data_source.GetLayer()
    geometry_extraction(layer)
    in_fields, out_fields, dst_layer = import_field_schema(layer, output_shp, ['ident'],
                                                           {'count': ogr.OFTInteger, 'El_Cen': ogr.OFTReal})
    # out_lyr.CreateFields(in_lyr.schema)
    dissolved_lines = dissolve_layer(layer, in_fields.keys(), {'FID': 'count'})
    feature_creation(output_shp, dissolved_lines)
    centrality_normalization(output_shp, node_count)
    # betweenness_multiedge_distribution()

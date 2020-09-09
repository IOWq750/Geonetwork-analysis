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
    substation_count = number_nodes - generation_count
    G_network = trace_lines(G_network)
    shortest_path = nx.multi_source_dijkstra_path(G_network, generation, weight=weight)
    aux_ie.export_path_to_shp(G_network, "true", output_workspace, shortest_path)
    return number_nodes, generation_count, substation_count


def trace_lines(G_network):
    trace_dict = {}
    line_dict = {}
    for line in G_network.edges(data=True):
        start_end = line[:2]
        item = (start_end, line[2]['Voltage'])
        item_inverted = (start_end[1], start_end[0], line[2]['Voltage'])
        if item not in line_dict and item_inverted not in line_dict:
            line_dict[item] = 1
            trace_dict[start_end[0]] = [start_end[0], start_end[1]]
        else:
            line_dict[item] += 1
    circuit_dict = {}
    for line in G_network.edges(keys=True, data=True):
        try:
            circuit_dict[line[:3]] = line_dict[(line[:2], line[3]['Voltage'])]
        except:
            circuit_dict[line[:3]] = line_dict[line[1], line[0], line[3]['Voltage']]
    nx.set_edge_attributes(G_network, circuit_dict, 'Circ_Count')
    return G_network


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
    in_fields = []
    layer_definition_in = layer.GetLayerDefn()
    layer_definition_out = dst_layer.GetLayerDefn()
    for i in range(layer_definition_in.GetFieldCount()):
        field_name = layer_definition_in.GetFieldDefn(i).GetName()
        in_fields.append(field_name)
    for field_name in in_fields:
        if field_name in delete_fields:
            dst_layer.DeleteField(layer_definition_out.GetFieldIndex(field_name))
            in_fields.remove(field_name)
    if add_field is not None:
        for field in add_field:
            dst_layer.CreateField(ogr.FieldDefn(field, add_field[field]))
    return dst_layer, in_fields


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
                if stats == 'COUNT':
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


def centrality_normalization(shp, node_number, generation_count):
    out_ds = ogr.GetDriverByName('ESRI Shapefile').Open(shp, 1)
    layer = out_ds.GetLayer()
    for feature in layer:
        count_field = feature.GetField('COUNT')
        count_circuit = feature.GetField('Circ_Count')
        el_cen = float(count_field) / ((node_number * (node_number - 1)) - generation_count * (generation_count - 1))
        el_centrality_distributed = el_cen/count_circuit
        feature.SetField('El_Cen', el_cen)
        feature.SetField('El_C_Distr', el_centrality_distributed)
        layer.SetFeature(feature)


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
    dst_layer, in_fields = import_field_schema(layer, output_shp, ['ident', 'Geometry'], {'COUNT': ogr.OFTInteger,
                                                                              'El_Cen': ogr.OFTReal,
                                                                              'El_C_Distr': ogr.OFTReal})
    dissolved_lines = dissolve_layer(layer, in_fields, {'COUNT': 'FID'})
    feature_creation(output_shp, dissolved_lines)
    centrality_normalization(output_shp, node_count, generation_count)

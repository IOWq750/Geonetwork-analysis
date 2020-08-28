# -*- coding: utf-8 -*-
# Modified from https://gis.stackexchange.com/a/150001/2856
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
import fiona
import itertools
from operator import itemgetter


def dissolve(input, output, fields):
    with fiona.open(input) as input:
        with fiona.open(output, 'w', **input.meta) as output:
            grouper = itemgetter(*fields)
            key = lambda k: grouper(k['properties'])
            for k, group in itertools.groupby(sorted(input, key=key), key):
                print(k)
                print(group)
                properties, geom = zip(*[(feature['properties'], shape(feature['geometry'])) for feature in group])
                output.write({'geometry': mapping(unary_union(geom)), 'properties': properties[0]})


if __name__ == '__main__':
    dissolve(r'F:\YandexDisk\Projects\RFFI_Transport\Ural_Siberia\New_Shapefile.shp', r'F:\YandexDisk\Projects\RFFI_Transport\Ural_Siberia\Dissolve.shp', ["Id", "geometry"])
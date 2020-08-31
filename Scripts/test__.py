from osgeo import ogr
import os

os.chdir(r'F:\YandexDisk\Projects\RFFI_Transport\Ural_Siberia')
shp = r'Output\edges.shp'
layer = ogr.GetDriverByName('ESRI Shapefile').Open(shp, 1).GetLayer()
layer.CreateField(ogr.FieldDefn('ccc', ogr.OFTString))
print(1)

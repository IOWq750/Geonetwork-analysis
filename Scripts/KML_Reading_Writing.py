from zipfile import ZipFile
import simplekml
filename = 'test.kmz'

kmz = ZipFile(filename, 'r')
kml = kmz.open('doc.kml', 'r')
import xml.sax, xml.sax.handler


class PlacemarkHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.inName = False  # handle XML parser events
        self.inPlacemark = False
        self.mapping = {}
        self.buffer = ""
        self.name_tag = ""

    def startElement(self, name, attributes):
        if name == "Placemark":  # on start Placemark tag
            self.inPlacemark = True
            self.buffer = ""
        if self.inPlacemark:
            if name == "name":  # on start title tag
                self.inName = True  # save name text to follow

    def characters(self, data):
        if self.inPlacemark:  # on text within tag
            self.buffer += data  # save text if in title

    def endElement(self, name):
        self.buffer = self.buffer.strip('\n\t')

        if name == "Placemark":
            self.inPlacemark = False
            self.name_tag = ""  # clear current name

        elif name == "name" and self.inPlacemark:
            self.inName = False  # on end title tag
            self.name_tag = self.buffer.strip()
            self.mapping[self.name_tag] = {}
        elif self.inPlacemark:
            if name in self.mapping[self.name_tag]:
                self.mapping[self.name_tag][name] += self.buffer
            else:
                self.mapping[self.name_tag][name] = self.buffer
        self.buffer = ""


class CreatePlacemark():
    def __init__(self):
        self.placemark_name = ''
        self.folder_path = ''
        self.geometry_type = ''
        self.color = ''
        self.width = ''
        self.transparency = ''

    def kml_object_creation(self, coords_split, key, obj_name):
        lats = coords_split[1::3]
        lons = coords_split[0::3]
        heights = coords_split[2::3]
        coords = []
        for i in range(0, int((len(coords_split) - 1) / 3), 1):
            tuple_coords = tuple([lons[i], lats[i], heights[i]])
            coords.append(tuple_coords)
        if 'LineString' in handler.mapping[key]:
            line = self.newlinestring(name=obj_name)
            line.coords = coords
            line.style.linestyle.width = 3
            line.style.linestyle.color = simplekml.Color.blue


parser = xml.sax.make_parser()
handler = PlacemarkHandler()
parser.setContentHandler(handler)
parser.parse(kml)
kmz.close()

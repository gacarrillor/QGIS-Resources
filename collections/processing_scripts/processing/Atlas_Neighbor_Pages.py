##Print_Composer=group
##Neighbor_pages_for_Atlas=name
##Rectangular_grid_layer=vector
##Page_number_field=field Rectangular_grid_layer

# Author: German Carrillo (GeoTux), 2016
# More info: http://gis.stackexchange.com/questions/214300/how-to-determine-neighbouring-tile-ids-in-qgis

from qgis.utils import iface
from qgis.core import QgsSpatialIndex, QgsField
from PyQt4.QtCore import QVariant
from processing.tools import dataobjects
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException

layer = dataobjects.getObjectFromUri(Rectangular_grid_layer)

if not Rectangular_grid_layer or not Page_number_field:
    raise GeoAlgorithmExecutionException("Please specify both, projects folder and output folder.")

layer.startEditing()
layer.dataProvider().addAttributes(
        [QgsField('right', QVariant.String),
         QgsField('left', QVariant.String),
         QgsField('above', QVariant.String),
         QgsField('below', QVariant.String)] )
layer.updateFields()

feature_dict = {f.id(): f for f in layer.getFeatures()}
index = QgsSpatialIndex( layer.getFeatures() )

for f in feature_dict.values():
    geom = f.geometry()
    bbox1 = geom.boundingBox().toString(2).replace(" : ",",").split(",")
    intersecting_ids = index.intersects( geom.boundingBox() )

    for intersecting_id in intersecting_ids:
        intersecting_f = feature_dict[intersecting_id]

        if ( f != intersecting_f and not intersecting_f.geometry().disjoint(geom) ):
            bbox2 = intersecting_f.geometry().boundingBox().toString(2).replace(" : ",",").split(",")
            relX = [bbox1[0:3:2].index( c ) for c in bbox1[0:3:2] if c not in bbox2[0:3:2]]
            relY = [bbox1[1:4:2].index( c ) for c in bbox1[1:4:2] if c not in bbox2[1:4:2]]
            if relX == [0] and relY == []:
          	    f['right'] = intersecting_f[Page_number_field]
            elif relX == [] and relY == [0]:
	              f['above'] = intersecting_f[Page_number_field]
            elif relX == [1] and relY == []:
	              f['left'] = intersecting_f[Page_number_field]
            elif relX == [] and relY == [1]:
	              f['below'] = intersecting_f[Page_number_field]

    layer.updateFeature(f)
layer.commitChanges()

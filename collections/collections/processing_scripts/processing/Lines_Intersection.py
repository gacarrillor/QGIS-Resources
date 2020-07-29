##Temporary_Scripts=group
##Lines Intersection Keep All Fields=name
##Input_layer=vector line
##Intersect_layer=vector line
##Keep_all_input_fields=boolean False
##Keep_only_this_input_field=field Input_layer
##Keep_all_intersect_fields=boolean False
##Keep_only_this_intersect_field=field Intersect_layer
##Intersections=output vector

# Author: German Carrillo (GeoTux), 2016
# Heavily based on the qgis:lineintersection algorithm by Victor Olaya

from qgis.core import (QGis, QgsFeatureRequest, QgsFeature, QgsGeometry,
                       QgsFields)
from processing.tools import dataobjects, vector

layerA = dataobjects.getObjectFromUri(Input_layer)
layerB = dataobjects.getObjectFromUri(Intersect_layer)
allFieldsA = Keep_all_input_fields
allFieldsB = Keep_all_intersect_fields
fieldA = Keep_only_this_input_field
fieldB = Keep_only_this_intersect_field

idxA = layerA.fieldNameIndex(fieldA)
idxB = layerB.fieldNameIndex(fieldB)

if allFieldsA:
    fieldListA = layerA.fields()
else:
    fieldListA = QgsFields()
    fieldListA.append(layerA.fields()[idxA])

if allFieldsB:
    fieldListB = layerB.fields()
else:
    fieldListB = QgsFields()
    fieldListB.append(layerB.fields()[idxB])

fieldListB = vector.testForUniqueness(fieldListA, fieldListB)
fieldListA.extend(fieldListB)

writer = vector.VectorWriter(Intersections, None, fieldListA, QGis.WKBPoint,
                             layerA.dataProvider().crs())

spatialIndex = vector.spatialindex(layerB)

outFeat = QgsFeature()
features = vector.features(layerA)
total = 100.0 / len(features)
hasIntersections = False

for current, inFeatA in enumerate(features):
    inGeom = inFeatA.geometry()
    hasIntersections = False
    lines = spatialIndex.intersects(inGeom.boundingBox())

    if len(lines) > 0:
        hasIntersections = True

    if hasIntersections:
        for i in lines:
            request = QgsFeatureRequest().setFilterFid(i)
            inFeatB = layerB.getFeatures(request).next()
            tmpGeom = QgsGeometry(inFeatB.geometry())

            points = []
            if allFieldsA:
                attrsA = inFeatA.attributes()
            else:
                attrsA = [inFeatA.attributes()[idxA]]

            if allFieldsB:
                attrsB = inFeatB.attributes()
            else:
                attrsB = [inFeatB.attributes()[idxB]]

            if inGeom.intersects(tmpGeom):
                tempGeom = inGeom.intersection(tmpGeom)
                if tempGeom.type() == QGis.Point:
                    if tempGeom.isMultipart():
                        points = tempGeom.asMultiPoint()
                    else:
                        points.append(tempGeom.asPoint())

                    for j in points:
                        outFeat.setGeometry(tempGeom.fromPoint(j))
                        attrsA.extend(attrsB)
                        outFeat.setAttributes(attrsA)
                        writer.addFeature(outFeat)

    progress.setPercentage(int(current * total))

del writer

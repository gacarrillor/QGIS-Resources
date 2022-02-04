"""
/***************************************************************************
                        Vector overlaps by class
                             --------------------
        begin                : 2022-02-04
        git sha              : :%H$
        copyright            : (C) 2022 by Germán Carrillo (GeoTux)
        email                : gcarrillo@linuxmail.org
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.PyQt.QtCore import (QVariant,
                              QCoreApplication)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterVectorLayer,
                       QgsFields,
                       QgsField,
                       QgsFeatureRequest,
                       QgsSpatialIndex,
                       qgsDoubleNear,
                       QgsWkbTypes,
                       QgsDistanceArea,
                       QgsGeometry,
                       QgsFeature)
from qgis import processing


class CalculateVectorOverlapsByClass(QgsProcessingAlgorithm):
    """
    Extends native:calculatevectoroverlaps (Overlap analysis) to accept
    a single overlay layer with classes and generate a table with overlap
    areas and percentages by class.
    """
    INPUT = 'INPUT'
    SOURCE_ID_FIELD = 'SOURCE_ID_FIELD'
    OVERLAY = 'OVERLAY'
    CLASS_FIELD = 'CLASS_FIELD'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CalculateVectorOverlapsByClass()

    def name(self):
        return 'calculatevectoroverlapsbyclass'

    def displayName(self):
        return self.tr('Overlap analysis by class')

    def tags(self):
        return "vector,overlay,area,percentage,intersection,class,type,field".split(",")

    def group(self):
        return self.tr('Vector analysis')

    def groupId(self):
        return 'vectoranalysis'

    def shortHelpString(self):
        return self.tr("""This algorithm calculates the area and percentage cover by which features from an input layer are overlapped by features (grouped by classes) from an overlay layer.\n\nThe output is a table with overlap areas and percentages by class.""")

    def initAlgorithm(self, config=None):
        # We add the input vector features source.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        
        # Field where to extract source polygon ids from
        self.addParameter(
            QgsProcessingParameterField(
                self.SOURCE_ID_FIELD,
                self.tr('Id field'),
                parentLayerParameterName='INPUT',
                type=QgsProcessingParameterField.Any
            )
        )
        
        # We add the overlay vector features source
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.OVERLAY,
                self.tr('Overlay layer'),
                [QgsProcessing.TypeVectorPolygon]
            )
            #QgsProcessingParameterFeatureSource(
            #    self.OVERLAY,
            #    self.tr('Overlay layer'),
            #    [QgsProcessing.TypeVectorPolygon]
            #)
        )
        
        # Field representing the class for overlay polygons
        self.addParameter(
            QgsProcessingParameterField(
                self.CLASS_FIELD,
                self.tr('Class field'),
                parentLayerParameterName='OVERLAY',
                type=QgsProcessingParameterField.Any
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        # Output table:
        #   source_id | class | area | percentage
        
        # Base (source) layer
        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )
        
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        source_crs = source.sourceCrs()
        source_count = source.featureCount()
        source_features = source.getFeatures()
        
        # Source id field
        id_field = self.parameterAsFields(parameters,
                                          self.SOURCE_ID_FIELD,
                                          context)[0]

        # Overlay layer
        overlay = self.parameterAsVectorLayer(
            parameters,
            self.OVERLAY,
            context
        )
        #overlay = self.parameterAsSource(
        #    parameters,
        #    self.OVERLAY,
        #    context
        #)
        if overlay is None:
            raise QgsProcessingException("Overlay layer could not be loaded! Is it a valid layer?")
        
        # Class field
        class_field = self.parameterAsFields(parameters,
                                             self.CLASS_FIELD,
                                             context)[0]
        
        # Output layer
        destId = ''
        fields = QgsFields()
        fields.append(QgsField("id", source.fields().field(id_field).type()))
        fields.append(QgsField("class", overlay.fields().field(class_field).type()))
        fields.append(QgsField("area", QVariant.Double))
        fields.append(QgsField("percentage", QVariant.Double))
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.NoGeometry
        )
        
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        
        class_layer = processing.run("native:collect", {
                                     'INPUT': overlay,
                                     'FIELD':[class_field],
                                     'OUTPUT':'TEMPORARY_OUTPUT'
                                     }, context=context, feedback=feedback)['OUTPUT']
        class_layer = processing.run("native:fixgeometries", {
                                     'INPUT': class_layer,
                                     'OUTPUT':'TEMPORARY_OUTPUT'
                                     }, context=context, feedback=feedback)['OUTPUT']
        class_layer_features = [feature for feature in class_layer.getFeatures()]
        
        # build a spatial index for constraint layer for speed. We also store input 
        # constraint geometries here, to avoid refetching and projecting them later
        feedback.pushInfo(self.tr("Preparing {}").format(overlay.name()))
        request = QgsFeatureRequest().setSubsetOfAttributes(list()).setDestinationCrs(source_crs, context.transformContext()).setInvalidGeometryCheck(context.invalidGeometryCheck())
        feature_it = overlay.getFeatures(request)
        spatial_index = QgsSpatialIndex(feature_it, feedback, QgsSpatialIndex.FlagStoreFeatureGeometries)

        da = QgsDistanceArea()
        da.setSourceCrs(source_crs, context.transformContext())
        da.setEllipsoid(context.ellipsoid())

        # loop through input
        step = 100.0 / source_count if source_count > 0 else 0
        i = 0
        for feature in source_features:
            if feedback.isCanceled():
                break

            id_value = feature[id_field]
            out_features = list()
            
            feedback.pushInfo('Analysing overlaps in input feature with id {}...'.format(id_value))
            
            if feature.hasGeometry() and not qgsDoubleNear(feature.geometry().area(), 0.0):
                input_geom = feature.geometry()
                input_area = da.measureArea(input_geom)

                # prepare for lots of intersection tests (for speed)
                geom_engine = QgsGeometry.createGeometryEngine(input_geom.constGet())
                geom_engine.prepareGeometry()

                # calculate overlap attributes
                for class_feature in class_layer_features:
                    if feedback.isCanceled():
                        break
                    
                    overlay_area = 0
                    
                    class_const_geom = class_feature.geometry().constGet()
                    if geom_engine.intersects(class_const_geom):
                        if feedback.isCanceled():
                            break
                        
                        overlay_intersection = geom_engine.intersection(class_const_geom)
                        overlay_area = da.measureArea(QgsGeometry(overlay_intersection))
                        
                    if feedback.isCanceled():
                        break
                    
                    out_feature = QgsFeature()
                    out_attrs = [id_value,
                                 class_feature[class_field],
                                 overlay_area,
                                 100 * overlay_area / input_area]
                    out_feature.setAttributes(out_attrs)
                    out_features.append(out_feature)
            else:
                # Input feature has no geometry
                for class_feature in class_layer_features:
                    out_feature = QgsFeature()
                    out_feature.setAttributes([id_value, class_feature[class_field], None, None])
                    out_features.append(out_feature)
                
            if not sink.addFeatures(out_features, QgsFeatureSink.FastInsert):
                raise QgsProcessingException(sink.lastError())

            i += 1
            feedback.setProgress(i * step)

        return {self.OUTPUT: dest_id}


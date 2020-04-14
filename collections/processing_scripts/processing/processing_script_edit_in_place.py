# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterDistance,
                       QgsFeatureSink,
                       QgsMapLayer,
                       QgsWkbTypes)
import processing


class ExampleEditInPlaceProcessingAlgorithm(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    DISTANCE = 'DISTANCE'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExampleEditInPlaceProcessingAlgorithm()

    def name(self):
        return 'example_edit_in_place_alg'

    def displayName(self):
        return self.tr('Example edit in place alg')

    def group(self):
        return self.tr('Example scripts')

    def groupId(self):
        return 'examplescripts'

    def shortHelpString(self):
        return self.tr("Example edit in place alg")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.DISTANCE,
                self.tr('Buffer distance'),
                parentParameterName=self.INPUT,
                minValue=0.00000001,
                defaultValue=10.0
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Buffered geometries')
            )
        )

    def flags(self):
        """Here we let QGIS know our algorithm supports edit-in-place"""
        return super().flags() | QgsProcessingAlgorithm.FlagSupportsInPlaceEdits

    def supportInPlaceEdit(self, layer):
       """
       We just support polygon layers in this algorithm, and we can state that clearly in this method.
       Doing so, the algorithm won't be available as edit-in-place for geometries other than Polygons.
       """
       return layer.geometryType() == QgsWkbTypes.PolygonGeometry

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               source.fields(), source.wkbType(), source.sourceCrs())
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        features = source.getFeatures()

        # Generate buffers
        for f in features:
            if feedback.isCanceled():
                break

            if f.hasGeometry():
                out_feature = f
                out_feature.setGeometry(f.geometry().buffer(distance, 5))
                sink.addFeature(out_feature, QgsFeatureSink.FastInsert)
            else:
                sink.addFeature(f)

        return {self.OUTPUT: dest_id}

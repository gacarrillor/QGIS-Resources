# -*- coding: utf-8 -*-
"""
/***************************************************************************
                        Batch Export Project Composers
                             --------------------
        begin                : 2019-08-07
        git sha              : :%H$
        copyright            : (C) 2019 by Germán Carrillo (GeoTux)
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
import os.path
import glob
import qgis
from qgis.core import (QgsProject,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterString,
                       QgsProcessingOutputVectorLayer)
from qgis.PyQt.QtCore import QCoreApplication


class BatchExportProjectComposers(QgsProcessingAlgorithm):

    PROJECTS_FOLDER = 'PROJECTS_FOLDER'
    EXTENSION = 'EXTENSION'
    OUTPUT_FOLDER = 'OUTPUT_FOLDER'
    OUTPUT = 'OUTPUT'

    def createInstance(self):
        return type(self)()

    def group(self):
        return QCoreApplication.translate("BatchExportProjectComposers", "QGIS Projects")

    def groupId(self):
        return 'qgis_projects'

    def tags(self):
        return (QCoreApplication.translate("BatchExportProjectComposers", 'layout,composer,map,printer,batch')).split(',')

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFolderDestination(self.PROJECTS_FOLDER,
                                                              QCoreApplication.translate("BatchExportProjectComposers", "Projects folder")))
        self.addParameter(QgsProcessingParameterEnum(self.EXTENSION,
                                                              QCoreApplication.translate("BatchExportProjectComposers", "Extension of generated maps"),
                                                              ['.pdf', '.jpg', '.jpeg', '.tif', '.tiff', '.png', '.bmp', '.ico', '.ppm', '.xbm', '.xpm']))
        self.addParameter(QgsProcessingParameterFolderDestination(self.OUTPUT_FOLDER,
                                                        QCoreApplication.translate("BatchExportProjectComposers", "Output folder where to save maps")))
        self.addOutput(QgsProcessingOutputVectorLayer(self.OUTPUT,
                                                        QCoreApplication.translate("BatchExportProjectComposers", 'Output')))

    def name(self):
        return 'BatchExportProjectComposers'

    def displayName(self):
        return QCoreApplication.translate("BatchExportProjectComposers", "Batch export project composers")

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

    def processAlgorithm(self, parameters, context, feedback):
        Projects_folder = self.parameterAsString(parameters, self.PROJECTS_FOLDER, context)
        Extension = self.parameterAsEnum(parameters, self.EXTENSION, context)
        Output_folder = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)
        Output = self.parameterAsVectorLayer(parameters, self.OUTPUT, context)

        # Settings
        projectPaths = glob.glob(os.path.join(Projects_folder, '*.qg[s|z]'))

        if not len(projectPaths):
            feedback.reportError("\nERROR: No QGIS project files (.qgs or .qgz) found in the specified folder. We cannot continue...\n")
        elif not os.path.isdir(Output_folder):
            feedback.reportError("\nERROR: No output folder given. We cannot continue...\n")
        else:
            formats = ['.pdf', '.jpg', '.jpeg', '.tif', '.tiff', '.png', '.bmp', '.ico', '.ppm', '.xbm', '.xpm']
            count = 0
            exported_count = 0

            if not 'MapsPrinter' in qgis.utils.plugins:
                feedback.reportError("\nERROR: The 'Maps Printer' plugin  is required!\n")
            else:
                mp = qgis.utils.plugins['MapsPrinter']
                project = QgsProject.instance()
                extension = formats[Extension]

                # Do the work!
                for projectPath in projectPaths:
                    # qgis.utils.iface.newProject() # Needed to reset composer manager
                    project.read(projectPath)
                    feedback.pushInfo("\n'{}' project read!!".format(projectPath))
                    feedback.setProgress(count * 100 / len(projectPaths))
                    count += 1

                    for composer in project.layoutManager().layouts():
                        feedback.pushInfo("\n --> Composer found: '{}'!".format(composer.name()))
                        title = composer.name()
                        title = project.baseName() + '_' + title
                        mp.exportCompo(composer, Output_folder, title, extension)
                        feedback.pushInfo("      Composer exported!")
                        exported_count += 1

                if exported_count:
                    feedback.pushInfo("\nINFO: Maps were saved in '{}'\n".format(Output_folder))

        return {self.OUTPUT: Output}
##QGIS_Projects=group 
##Batch_Export_Project_Composers=name
##Projects_folder=folder
##Output_folder=folder
##Extension=selection PDF format (*.pdf *.PDF);JPG format (*.jpg *.JPG);JPEG format (*.jpeg *.JPEG);TIF format (*.tif *.TIF);TIFF format (*.tiff *.TIFF);PNG format (*.png *.PNG);BMP format (*.bmp *.BMP);ICO format (*.ico *.ICO);PPM format (*.ppm *.PPM));XBM format (*.xbm *.XBM);XPM format (*.xpm *.XPM)
##nomodeler

# Author: German Carrillo (GeoTux), 2016
import os.path
import glob 
import qgis
from qgis.core import QgsProject
from PyQt4.QtCore import QFileInfo
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException

if not Projects_folder or not Output_folder:
    raise GeoAlgorithmExecutionException("Please specify both, projects folder and output folder.")

# Settings
projectPaths = glob.glob( os.path.join( Projects_folder, '*.qgs' ) )
formats=['.pdf','.jpg','.jpeg','.tif','.tiff','.png','.bmp','.ico','.ppm','.xbm','.xpm']
count=0

if not 'MapsPrinter' in qgis.utils.plugins:
    raise GeoAlgorithmExecutionException("The 'Maps Printer' plugin  is required!")
    
mp = qgis.utils.plugins['MapsPrinter']
project = QgsProject.instance()
qgis.utils.iface.mapCanvas().setRenderFlag( False )
extension = formats[Extension]

# Do the work!
for projectPath in projectPaths:
    qgis.utils.iface.newProject() # Needed to reset composer manager
    project.read( QFileInfo( projectPath ) )
    progress.setInfo( projectPath + " project read!" )
    progress.setPercentage( count * 100 / len( projectPaths ) ) 
    count+=1
    
    for composer in qgis.utils.iface.activeComposers():
        progress.setInfo( "    Composer found:  " + composer.composerWindow().windowTitle() )
        title = composer.composerWindow().windowTitle()
        title = project.fileInfo().baseName() + '_' + title
        mp.exportCompo( composer, Output_folder, title, extension )
        progress.setInfo( "        Composer exported!" )

qgis.utils.iface.mapCanvas().setRenderFlag( True )

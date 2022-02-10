# QGIS-Resources
My collection of QGIS resources shared with the community. Hope you find them useful!

LICENSE: GNU GPL v.3.0

## Collections

### Processing Scripts (PyQGIS) by Germán Carrillo

 - **export_composers_of_multiple_projects.py**

   This script allows you to export the composers of all the QGIS projects that are inside a base folder.
   It's based on the 'Maps Printer' plugin by [Harrissou Sant-anna](https://github.com/DelazJ), which is required to run the script.

 - **edit_in_place_script.py**

   This script can be taken as an example of a script that edits a layer in-place. That is, a script that modifies features from the input layer, instead of generating a copy of the layer.     

 - **vector_overlaps_by_class.py**

    Extends `native:calculatevectoroverlaps` (Overlap analysis) to accept a single overlay layer with classes and generate a table with overlap areas and percentages by class. 


## Installation

1. Install the `QGIS Resource Sharing` plugin from QGIS plugin repository.
2. Open the `QGIS Resource Sharing`'s main window and go to `Settings` --> `Add repository...`.
3. Set the repository name and URL like this:
   + Name: `Germap's repo`
   + URL: https://github.com/gacarrillor/QGIS-Resources.git
   
   ![image](https://user-images.githubusercontent.com/652785/153315981-6c114258-168b-4784-b719-e9f065cabf49.png)
4. Still in the `QGIS Resource Sharing`'s main window, go to `All collections` and search for `pyqgis`.
5. Select the item "Processing Scripts (PyQGIS) by Germán Carrillo" and click on `Install`.

That's it! A confirmation window should tell you you have installed several Processing scripts, which you can access from the Processing panel in QGIS. Enjoy!
   
   



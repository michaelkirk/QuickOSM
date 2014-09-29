# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QuickOSM
                                 A QGIS plugin
 OSM's Overpass API frontend
                             -------------------
        begin                : 2014-06-11
        copyright            : (C) 2014 by 3Liz
        email                : info at 3liz dot com
        contributor          : Etienne Trimaille
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from QuickOSM import *

from QuickOSM.CoreQuickOSM.QueryFactory import QueryFactory
from QuickOSM.CoreQuickOSM.Tools import Tools
from QuickOSM.CoreQuickOSM.API.ConnexionOAPI import ConnexionOAPI
from QuickOSM.CoreQuickOSM.Parser.OsmParser import OsmParser
from processing.tools.system import *
import processing
import ntpath
from os.path import dirname,abspath,join
from genericpath import isfile

class Process(QThread):
    '''
    This class makes the link between GUI and Core
    '''
    
    signalProcessThreadFinished = pyqtSignal(int, name='signalProcessThreadFinished')
    signalPercentage = pyqtSignal(int, name='signalPercentage')
    
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
        self.exiting = False
        self.layers = []
    
    def setParameters(self, dialog = None, query=None, nominatim=None, bbox=None, outputDir=None, prefixFile=None,outputGeomTypes=None, layerName = "OsmQuery", whiteListValues = None, configOutputs = None):
        self.dialog = dialog
        self.query = query
        self.nominatim = nominatim
        self.bbox = bbox
        self.outputDir = outputDir
        self.prefixFile = prefixFile
        self.outputGeomTypes = outputGeomTypes
        self.layerName = layerName
        self.whiteListValues = whiteListValues
        self.configOutputs = configOutputs
    
    def run(self):
        
        #Prepare outputs
        self.dialog.setProgressText(QApplication.translate("QuickOSM",u"Preparing outputs"))
        #If a file already exist, we avoid downloading data for nothing
        outputs = {}
        for i,layer in enumerate(['points','lines','multilinestrings','multipolygons']):
            if not self.outputDir:
                #if no directory, get a temporary shapefile
                outputs[layer] = getTempFilenameInTempFolder("_"+layer+"_quickosm.shp")
            else:
                if not self.prefixFile:
                    prefixFile = self.layerName
                    
                outputs[layer] = os.path.join(self.outputDir,prefixFile + "_" + layer + ".shp")
                
                if os.path.isfile(outputs[layer]):
                    raise FileOutPutException(suffix="("+outputs[layer]+")")
                
                percent = int((i+1)*100/4)
                self.signalPercentage.emit(percent)
        
        #Replace Nominatim or BBOX
        self.dialog.setProgressText(QApplication.translate("QuickOSM",u"Preparing query"))
        query = Tools.PrepareQueryOqlXml(query=self.query, nominatimName = self.nominatim, extent=self.bbox)
        
        #Getting the default OAPI and running the query
        self.dialog.setProgressText(QApplication.translate("QuickOSM",u"Start downloading"))
        server = Tools.getSetting('defaultOAPI')
        connexionOAPI = ConnexionOAPI(parent=self, url=server,output = "xml")
        self.dialog.progressBar_execution.setMaximum(0)
        connexionOAPI.signalText.connect(self.dialog.setProgressText)
        osmFile = connexionOAPI.getFileFromQuery(query)
        
        if self.exiting:
            self.signalProcessThreadFinished.emit(-1)
            return False
        
        connexionOAPI.signalText.disconnect(self.dialog.setProgressText)
        self.dialog.progressBar_execution.setMaximum(100)
        
        #Parsing the file
        osmParser = OsmParser(osmFile, layers=self.outputGeomTypes, whiteListColumn=self.whiteListValues,parent=self)
        osmParser.signalText.connect(self.dialog.setProgressText)
        osmParser.signalPercentage.connect(self.signalPercentage.emit)
        osmParser.run()
        osmParser.wait()
        
        layers = osmParser.layers
        
        if self.exiting:
            self.signalProcessThreadFinished.emit(-1)
            return False
        
        #Geojson to shapefile
        for i, (layer,item) in enumerate(layers.iteritems()):
            self.signalPercentage.emit(0)
            self.dialog.setProgressText(QApplication.translate("QuickOSM",u"From GeoJSON to Shapefile : " + layer))
            if item['featureCount'] and layer in self.outputGeomTypes:
                
                finalLayerName = self.layerName
                #If configOutputs is not None (from My Queries)
                if self.configOutputs:
                    if self.configOutputs[layer]['namelayer']:
                        finalLayerName = self.configOutputs[layer]['namelayer']
                
                #Transforming the vector file
                osmGeom = {'points':QGis.WKBPoint,'lines':QGis.WKBLineString,'multilinestrings':QGis.WKBMultiLineString,'multipolygons':QGis.WKBMultiPolygon}
                geojsonlayer = QgsVectorLayer(item['geojsonFile'],"temp","ogr")
                writer = QgsVectorFileWriter(outputs[layer], "UTF-8", geojsonlayer.pendingFields(), osmGeom[layer], geojsonlayer.crs(), "ESRI Shapefile")
                nbFeatures = geojsonlayer.featureCount()
                for j,f in enumerate(geojsonlayer.getFeatures()):
                    writer.addFeature(f)
                    
                    percent = int((j+1)*100/nbFeatures)
                    if percent % 10 == 0:
                        self.signalPercentage.emit(percent)
                        
                        if self.exiting:
                            self.signalProcessThreadFinished.emit(-1)
                            return False
                       
                del writer          
                
                if self.exiting:
                    self.signalProcessThreadFinished.emit(-1)
                    return False
                
                #Loading the final vector file
                newlayer = QgsVectorLayer(outputs[layer],finalLayerName,"ogr")
                
                #Try to set styling if defined
                if self.configOutputs and self.configOutputs[layer]['style']:
                    newlayer.loadNamedStyle(self.configOutputs[layer]['style'])
                else:
                    #Loading default styles
                    if layer == "multilinestrings" or layer == "lines":
                        if "colour" in item['tags']:
                            newlayer.loadNamedStyle(join(dirname(dirname(abspath(__file__))),"styles",layer+"_colour.qml"))
                
                #Add action about OpenStreetMap
                actions = newlayer.actions()
                actions.addAction(QgsAction.OpenUrl,"OpenStreetMap Browser",'http://www.openstreetmap.org/browse/[% "osm_type" %]/[% "osm_id" %]',False)
                actions.addAction(QgsAction.GenericPython,'JOSM','from QuickOSM.CoreQuickOSM.Actions import Actions;Actions.run("josm","[% "full_id" %]")',False)
                actions.addAction(QgsAction.OpenUrl,"User default editor",'http://www.openstreetmap.org/edit?[% "osm_type" %]=[% "osm_id" %]',False)
                #actions.addAction(QgsAction.GenericPython,"Edit directly",'from QuickOSM.CoreQuickOSM.Actions import Actions;Actions.run("rawedit","[% "osm_type" %]/[% "osm_id" %]")',False)
                
                for link in ['url','website','wikipedia','ref:UAI']:
                    if link in item['tags']:
                        link = link.replace(":","_")
                        actions.addAction(QgsAction.GenericPython,link,'from QuickOSM.CoreQuickOSM.Actions import Actions;Actions.run("'+link+'","[% "'+link+'" %]")',False)
                
                if 'network' in item['tags'] and 'ref' in item['tags']:
                    actions.addAction(QgsAction.GenericPython,"Sketchline",'from QuickOSM.CoreQuickOSM.Actions import Actions;Actions.runSketchLine("[% "network" %]","[% "ref" %]")',False)
                 
                #Add index
                self.dialog.setProgressText(QApplication.translate("QuickOSM",u"Creating spatial index : " + layer))
                newlayer.dataProvider().createSpatialIndex()
                
                if self.exiting:
                    self.signalProcessThreadFinished.emit(-1)
                    return False
                
                self.layers.append(newlayer)
                
        self.signalProcessThreadFinished.emit(len(self.layers))
        return
    
    def ProcessQuickQuery(self,dialog = None, key = None,value = None,bbox = None,nominatim = None,osmObjects = None, timeout=25, outputDir=None, prefixFile=None, outputGeomTypes=None):
        
        #Set the layername
        layerName = ''
        for i in [key,value,nominatim]:
            if i:
                layerName += i + "_"
        #Delete last "_"
        layerName = layerName[:-1]
        
        #Building the query
        queryFactory = QueryFactory(timeout=timeout,key=key,value=value,bbox=bbox,nominatim=nominatim,osmObjects=osmObjects)
        query = queryFactory.make()
        
        #Call ProcessQuery with the new query
        return self.ProcessQuery(self,dialog=dialog,
                                    query=query,
                                    nominatim=nominatim,
                                    bbox=bbox,
                                    outputDir=outputDir,
                                    prefixFile=prefixFile,
                                    outputGeomTypes=outputGeomTypes,
                                    layerName=layerName)
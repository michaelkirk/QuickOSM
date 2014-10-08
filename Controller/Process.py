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

class Process(QObject):
    '''
    This class makes the link between GUI and Core
    '''
    
    signalProcessThreadFinished = pyqtSignal(int, name='signalProcessThreadFinished')
    signalProgressText = pyqtSignal(str, name='signalProgressText')
    signalProgressPercentage = pyqtSignal(int, name='signalProgressPercentage')
    signalProgressPercentageMax = pyqtSignal(int, name='signalProgressPercentageMax')
    signalException = pyqtSignal(Exception, name='signalException')
    signalErrorText = pyqtSignal(str, name='signalErrorText')    

    def __init__(self, query=None, nominatim=None, bbox=None, outputDir=None, prefixFile=None,outputGeomTypes=None, layerName = "OsmQuery", whiteListValues = None, configOutputs = None):
        QObject.__init__(self)
        
        self.query = query
        self.nominatim = nominatim
        self.bbox = bbox
        self.outputDir = outputDir
        self.prefixFile = prefixFile
        self.outputGeomTypes = outputGeomTypes
        self.layerName = layerName
        self.whiteListValues = whiteListValues
        self.configOutputs = configOutputs
        
        self.exiting = False
        self.layers = []

    def kill(self):
        self.exiting = True

    def runQuery(self):
        try:
                
            #Prepare outputs
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
            
            #Replace Nominatim or BBOX
            self.signalProgressText.emit(QApplication.translate("QuickOSM",u"Preparing query"))
            query = Tools.PrepareQueryOqlXml(query=self.query, nominatimName = self.nominatim, extent=self.bbox)
            
            #Getting the default OAPI and running the query
            self.signalProgressText.emit(QApplication.translate("QuickOSM",u"Waiting the response ..."))
            server = Tools.getSetting('defaultOAPI')
            self.connexionOAPI = ConnexionOAPI(url=server,output = "xml")
            self.signalProgressPercentageMax.emit(0)
            self.connexionOAPI.signalException.connect(self.signalException.emit)
            self.connexionOAPI.signalProgressText.connect(self.signalProgressText.emit)
            self.connexionOAPI.signalErrorText.connect(self.signalErrorText.emit)
            self.connexionOAPI.signalProcessThreadFinished.connect(self.signalProcessThreadFinished.emit)
            
            osmFile = self.connexionOAPI.getFileFromQuery(query)
            
            print osmFile
            self.signalProgressPercentageMax.emit(100)
            
            import time
            time.sleep(2)
            
            if self.exiting:
                raise QueryCanceledException
            
            print "finish"
            self.signalProcessThreadFinished.emit(0)
            
        except QueryCanceledException,e:
            self.signalProcessThreadFinished.emit(-1)
            return
        except QuickOsmException, e:
            self.sendExceptionSignal(e)
            return            
        except Exception, e:
            import traceback
            self.signalErrorText.emit(traceback.format_exc())
            return          

class Process2(QObject):
    '''
    This class makes the link between GUI and Core
    '''
    
    signalProcessThreadFinished = pyqtSignal(int, name='signalProcessThreadFinished')
    signalProgressText = pyqtSignal(str, name='signalProgressText')
    signalProgressPercentage = pyqtSignal(int, name='signalProgressPercentage')
    signalProgressPercentageMax = pyqtSignal(int, name='signalProgressPercentageMax')
    signalException = pyqtSignal(Exception, name='signalException')
    signalErrorText = pyqtSignal(str, name='signalErrorText')
    
    def __init__(self, query=None, nominatim=None, bbox=None, outputDir=None, prefixFile=None,outputGeomTypes=None, layerName = "OsmQuery", whiteListValues = None, configOutputs = None):
        QObject.__init__(self)
        
        self.query = query
        self.nominatim = nominatim
        self.bbox = bbox
        self.outputDir = outputDir
        self.prefixFile = prefixFile
        self.outputGeomTypes = outputGeomTypes
        self.layerName = layerName
        self.whiteListValues = whiteListValues
        self.configOutputs = configOutputs
        
        self.exiting = False
        self.layers = []
        
    def kill(self):
        self.exiting = True
        self.signalErrorText.emit("killing")
        print "killing the process ..."
        try:
            self.connexionOAPI.kill()  
        except AttributeError:
            pass
    
    def runQuery(self):
        try:
                
            #Prepare outputs
            self.signalProgressText.emit(QApplication.translate("QuickOSM",u"Preparing outputs"))
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
                    self.signalProgressPercentage.emit(percent)
            
            #Replace Nominatim or BBOX
            self.signalProgressText.emit(QApplication.translate("QuickOSM",u"Preparing query"))
            query = Tools.PrepareQueryOqlXml(query=self.query, nominatimName = self.nominatim, extent=self.bbox)
            
            #Getting the default OAPI and running the query
            self.signalProgressText.emit(QApplication.translate("QuickOSM",u"Waiting for the download ..."))
            server = Tools.getSetting('defaultOAPI')
            self.connexionOAPI = ConnexionOAPI(url=server,output = "xml")
            self.signalProgressPercentageMax.emit(0)
            self.connexionOAPI.signalException.connect(self.sendExceptionSignal)
            self.connexionOAPI.signalProgressText.connect(self.signalProgressText.emit)
            
            osmFile = self.connexionOAPI.getFileFromQuery(query)
            self.signalProgressPercentageMax.emit(100)
            
            if self.exiting or isinstance(osmFile, int):
                print "ask to quit 1"
                self.signalProcessThreadFinished.emit(-1)
                return
            
            #Parsing the file
            osmParser = OsmParser(osmFile, layers=self.outputGeomTypes, whiteListColumn=self.whiteListValues,parent=self)
            osmParser.signalException.connect(self.sendExceptionSignal)
            osmParser.signalText.connect(self.signalProgressText.emit)
            osmParser.signalProgressPercentage.connect(self.signalProgressPercentage.emit)
            osmParser.run()
            osmParser.wait()
            
            layers = osmParser.layers
            
            if self.exiting:
                self.signalProcessThreadFinished.emit(-1)
                return
            
            #Geojson to shapefile
            for i, (layer,item) in enumerate(layers.iteritems()):
                self.signalProgressPercentage.emit(0)
                self.signalProgressText.emit(QApplication.translate("QuickOSM",u"From GeoJSON to Shapefile : " + layer))
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
                            self.signalProgressPercentage.emit(percent)
                            
                            if self.exiting:
                                self.signalProcessThreadFinished.emit(-1)
                                return
                           
                    del writer          
                    
                    if self.exiting:
                        self.signalProcessThreadFinished.emit(-1)
                        return
                    
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
                    self.signalProgressText.emit(QApplication.translate("QuickOSM",u"Creating spatial index : " + layer))
                    newlayer.dataProvider().createSpatialIndex()
                    
                    if self.exiting:
                        self.signalProcessThreadFinished.emit(-1)
                        return
                    
                    self.layers.append(newlayer)
                    
            self.signalProcessThreadFinished.emit(len(self.layers))
        
        except QuickOsmException, e:
            self.sendExceptionSignal(e)
            return            
        
        except Exception, e:
            import traceback
            self.signalErrorText.emit(traceback.format_exc())
            
    def sendExceptionSignal(self,e):
        self.exiting = True
        self.signalException.emit(e)

    """    
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
    """
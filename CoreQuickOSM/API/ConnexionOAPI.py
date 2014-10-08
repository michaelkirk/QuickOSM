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
from PyQt4.QtNetwork import QNetworkAccessManager,QNetworkRequest,QNetworkReply
import re
import urllib2
import tempfile
import time

class ConnexionOAPI(QObject):
    '''
    Manage connexion to the overpass API
    '''

    signalProcessThreadFinished = pyqtSignal(int, name='signalProcessThreadFinished')
    signalProgressText = pyqtSignal(str, name='signalProgressText')
    signalException = pyqtSignal(Exception, name='signalException')
    signalErrorText = pyqtSignal(str, name='signalErrorText')
    
    def __init__(self, url="http://overpass-api.de/api/", output = None):
        '''
        Constructor
        @param url:URL of OverPass
        @type url:str
        @param output:Output desired (XML or JSON)
        @type output:str
        '''
        
        try:
            
            self.exiting = False
            self.finished = False
            self.data = None
            
            if not url:
                url="http://overpass-api.de/api/"
                
            self.__url = url
    
            if output not in (None, "json","xml"):
                raise OutPutFormatException
            self.__output = output
            
            self.network = QNetworkAccessManager()
            
            QObject.__init__(self)
        
        except QueryCanceledException,e:
            self.signalProcessThreadFinished.emit(-1)
            return
        except QuickOsmException, e:
            self.signalException(e)
            return            
        except Exception, e:
            import traceback
            self.signalErrorText.emit(traceback.format_exc())
            return
        
    def getFileFromQuery(self,req):
        '''
        Make a query to the overpass and put the result in a temp file
        @param req:Query to execute
        @type req:str
        @return: temporary filepath
        @rtype: str
        '''
        
        try:
            return "totoabcd"
            #self.query(req)
            
            print "waiting 1"
            time.sleep(1)
            
            #while not self.finished:
            #    print "waiting"
            #    time.sleep(0.5)
            
            print "end of waiting"
            tf = tempfile.NamedTemporaryFile(delete=False,suffix=".osm")
            tf.write("toto")
            namefile = tf.name
            tf.flush()
            tf.close()
            return namefile
        except QueryCanceledException,e:
            self.signalProcessThreadFinished.emit(-1)
            return -1
        except QuickOsmException, e:
            self.signalException(e)
            return -1   
        except Exception, e:
            import traceback
            self.signalErrorText.emit(traceback.format_exc())
            return -1

class ConnexionOAPI2(QObject):
    '''
    Manage connexion to the overpass API
    '''

    signalProgressText = pyqtSignal(str, name='signalProgressText')
    signalException = pyqtSignal(Exception, name='signalException')
    signalErrorText = pyqtSignal(str, name='signalErrorText')
    
    def __init__(self, url="http://overpass-api.de/api/", output = None):
        '''
        Constructor
        @param url:URL of OverPass
        @type url:str
        @param output:Output desired (XML or JSON)
        @type output:str
        '''
        self.exiting = False
        self.finished = False
        self.data = None
        
        if not url:
            url="http://overpass-api.de/api/"
            
        self.__url = url

        if output not in (None, "json","xml"):
            raise OutPutFormatException
        self.__output = output
        
        self.network = QNetworkAccessManager()
        
        QObject.__init__(self)

    def kill(self):
        self.exiting = True
        print "killing the downloader..."
        self.signalErrorText.emit('cancel the downloader')
        
        try:
            self.networkReply
            
            self.networkReply.abort()
        except AttributeError:
            pass
        
    def query(self,req):
        '''
        Make a query to the overpass
        @param req:Query to execute
        @type req:str
        @raise OverpassBadRequestException,NetWorkErrorException,OverpassTimeoutException
        @return: the result of the query
        @rtype: str
        '''
        
        urlQuery = QUrl(self.__url + 'interpreter')
        
        #The output format can be forced (JSON or XML)
        if self.__output:
            req = re.sub(r'output="[a-z]*"','output="'+self.__output+'"', req)
            req = re.sub(r'\[out:[a-z]*','[out:'+self.__output, req)
        
        encodedQuery = QUrl.toPercentEncoding(req)
        urlQuery.addEncodedQueryItem('data',encodedQuery)
        urlQuery.addQueryItem('info','QgisQuickOSMPlugin')        
        urlQuery.setPort(80)
        
        print "ok"
        print "waiting 5 query"
        time.sleep(5)
        #self.networkReply = self.network.get(QNetworkRequest(urlQuery))
        #self.networkReply.finished.connect(self.endOfRequest)
        #self.networkReply.downloadProgress.connect(self.downloadProgress)
        print "waiting 5 q"
        time.sleep(5)

    def downloadProgress(self,bytesRead, totalBytes):
        print "waiting 5 pro"
        time.sleep(5)
        self.signalProgressText.emit(QApplication.translate("QuickOSM",u"Downloading data from Overpass : " + self.convertSize(bytesRead)))

    def endOfRequest(self,test):
        self.data = self.networkReply.readAll()
        print "query executed"
        print "waiting 5"
        time.sleep(5)
        try:
            if self.networkReply.error() == QNetworkReply.NoError:
                
                if re.search('<remark> runtime error: Query timed out in "[a-z]+" at line [\d]+ after ([\d]+) seconds. </remark>', self.data):
                    print "timeout"
                    raise OverpassTimeoutException
                        
            elif self.networkReply.error() == QNetworkReply.UnknownContentError:
                print "erreur 400"
                raise OverpassBadRequestException
            
            else:
                print "erreur"
                raise NetWorkErrorException(suffix="Overpass API")
        
            print "end of result"
            print "waiting 5"
            time.sleep(0.5)
            self.networkReply.deleteLater()

        except Exception as e:
            self.signalException.emit(e)
            
        finally:
            self.finished = True
            print self.finished
            
    def getFileFromQuery(self,req):
        '''
        Make a query to the overpass and put the result in a temp file
        @param req:Query to execute
        @type req:str
        @return: temporary filepath
        @rtype: str
        '''
        print "going to wait"
        self.query(req)
        
        print "waiting 5"
        time.sleep(5)
        
        while not self.finished:
            print "waiting"
            time.sleep(0.5)
        
        print "waiting 5"
        time.sleep(5)
        
        print "end of waiting"
        tf = tempfile.NamedTemporaryFile(delete=False,suffix=".osm")
        tf.write("toto")
        namefile = tf.name
        tf.flush()
        tf.close()
        return namefile
    
    def getTimestamp(self):
        '''
        Get the timestamp of the OSM data on the server
        @return: Timestamp
        @rtype: str
        '''
        urlQuery = self.__url + 'timestamp'
        try:
            return urllib2.urlopen(url=urlQuery).read()
        except urllib2.HTTPError as e:
            if e.code == 400:
                raise OverpassBadRequestException
            
    def isValid(self):
        '''
        Try if the url is valid, NOT TESTED YET
        '''
        urlQuery = self.__url + 'interpreter'
        try:
            urllib2.urlopen(url=urlQuery)
            return True
        except urllib2.HTTPError:
            return False
        
    def convertSize(self, size):
        for x in ['bytes','KB','MB','GB','TB']:
            if size < 1024.0:
                return "%3.1f %s" % (size, x)
            size /= 1024.0
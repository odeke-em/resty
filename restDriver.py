#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>
# Code to bootstrap any project that intends to use restAssured as the backend API
# Will enable generation of related handlers

import os
import re
import sys
from optparse import OptionParser

try:
    from ___dbLiason import HandlerLiason
except ImportError as e:
    from .___dbLiason import HandlerLiason
try:
    from ___fileOnCloudHandler import FileOnCloudHandler
except ImportError as e:
    from .___fileOnCloudHandler import FileOnCloudHandler
try:
    from ___utils import docStartRegCompile, getDefaultAuthor, isCallableAttr
except:
    from .___utils import docStartRegCompile, getDefaultAuthor, isCallableAttr

class RestDriver:
    _rawUrlRequester = HandlerLiason._rawUrlRequester
    __restConnectorMethods = {
        'put': ('update', 's',), 'post': ('new', '',),
        'delete': ('delete', 's'), 'get': ('get', 's',)
    }
    getDefaultAuthor = getDefaultAuthor

    def __init__(self, ip, port, checkSumAlgoName='sha1'):
        self.__checkSumAlgoName = checkSumAlgoName or 'sha1'
        self.__baseUrl = '{i}:{p}'.format(i=ip.strip('/'), p=port.strip('/'))

        self.__externNameToLiasonMap = dict()

        self.__fCloudHandler =  FileOnCloudHandler(
            self.__baseUrl, self.__checkSumAlgoName
        )

    def getCheckSumAlgoName(self):
        return self.__fCloudHandler.getCheckSumAlgoName()

    def registerLiason(self, shortName, url):
        '''
        Params: shortName eg 'Job', url '/jobTable/jobHandler'
         Explanation:
            + Creates a name mangled dbLiason, and then creates the respective
              rest handlers as defined in static dict '__restConnectorMethods'
              and creates their '*Conn' connectors
        
            + Eg self.updateWorkers, self.deleteWorkers, self.getWorkers, etc
              that you will invoke externally.

            + To match naming convention ie camelCase, all method refs will be
              capitalized on the first letter
                ie shortName='apps', url='/apps' => self.updateApps
                not self.updateapps
        '''

        liasonName = '__%sLiason'%(shortName.lower())

        # Match camelCase naming convention
        setattr(self, liasonName, self.__createLiason(url))
        self.__externNameToLiasonMap[shortName] = getattr(self, liasonName)

        for restMethod, symNameTuple in self.__restConnectorMethods.items():
            symName, nameSuffix = symNameTuple
            setattr(
                self, '%s%s%s'%(symName, shortName.capitalize(), nameSuffix),
                self.__createLiasableFunc(shortName, '%sConn'%(restMethod))
            )

        return getattr(self, liasonName)

    def __createLiason(self, url):
        return HandlerLiason(self.__baseUrl + url)

    def __createLiasableFunc(self, key, methodKey, **attrs):
        liason = self.__externNameToLiasonMap.get(key, None)
        method = getattr(liason, methodKey, None)
        if method is None:
            method = lambda **aux: aux
        return method

    def uploadBlob(self, srcPath, **attrs):
        return self.__fCloudHandler.uploadBlobByPath(srcPath, **attrs)

    def uploadStream(self, f, **attrs):
        attrs['isPut'] = False
        return self.__fCloudHandler.uploadBlobByStream(f, **attrs)

    def ___keyToDocCloudName(self, key):
        return key if docStartRegCompile.search(key) else 'documents/'+key

    def downloadBlob(self, key, **attrs):
        return self.__fCloudHandler.downloadBlobToDisk(self.___keyToDocCloudName(key), **attrs)

    def downloadBlobToStream(self, key, **kwargs):
        return self.__fCloudHandler.downloadBlobToBuffer(self.___keyToDocCloudName(key), **kwargs)

    def deleteBlob(self, **attrs):
        return self.__fCloudHandler.deleteBlobOnCloud(**attrs)

    def updateFile(self, key, **attrs):
        attrs['isPut'] = True
        return self.__fCloudHandler.updateFileByPath(key, **attrs)

    def updateStream(self, stream, **attrs):
        return self.__fCloudHandler.updateFileByStream(stream, **attrs)

    def getCloudFilesManifest(self, **queryParams):
        return self.__fCloudHandler.getParsedManifest(queryParams)

    def setBaseUrl(self, newUrl):
        self.__baseUrl = newUrl

        # Propagate the changes along to the fileCloudHandler
        self.__fCloudHandler.setBaseURL(self.__baseUrl)

    def getBaseUrl(self):
        return self.__baseUrl

    def jsonParseResponse(self, reqResponse):
        return self.__fCloudHandler.jsonParseResponse(reqResponse)

    def __str__(self):
        return 'RestDriver::%s'%(self.__baseUrl)

    def __repr__(self):
        return 'RestDriver::%s'%(self.__baseUrl)

def cliParser():
    parser = OptionParser()
    parser.add_option('-i', '--ip', default='http://127.0.0.1', help='Port server is on', dest='ip')
    parser.add_option('-p', '--port', default='8000', help='IP address db connects to', dest='port')

    return parser.parse_args()

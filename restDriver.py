#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>
# Code to bootstrap any project that intends to use restAssured as the backend API
# Will enable generation of related handlers

import os
import re
import sys
import json
import collections
from optparse import OptionParser

try:
    from ___dbLiason import HandlerLiason
except ImportError as e:
    from .___dbLiason import HandlerLiason
try:
    from ___fileOnCloudHandler import FileOnCloudHandler
except ImportError as e:
    from .___fileOnCloudHandler import FileOnCloudHandler

isCallable = lambda a: hasattr(a, '__call__')
isCallableAttr = lambda obj, attrStr: isCallable(getattr(obj, attrStr, None))

getDefaultAuthor = lambda: os.environ.get('USER', 'Anonymous')
docStartRegCompile = re.compile('^documents', re.UNICODE)

def produceAndParse(func, **dataIn):
    dbCheck = func(**dataIn)
    if  not isCallableAttr(dbCheck, 'get'):
        return dbCheck
    else:
        response = dbCheck.get('value', None)
        if not isCallableAttr(response, 'decode'):
            return {'reason': 'No response could be decoded', 'status_code': 400}
        else:
            try:
                outValue = json.loads(response.decode())
                outValue['status_code'] = dbCheck.get('status_code', 200)
                return outValue
            except Exception as e:
                return {'reason': str(e), 'status_code': 500}

class RestDriver:
    __restConnectorMethods = {
        'put': ('update', 's',), 'post': ('new', '',), 'delete': ('delete', 's'), 'get': ('get', 's',)
    }
    def __init__(self, ip, port, checkSumAlgoName='sha1'):
        self.__checkSumAlgoName = checkSumAlgoName or 'sha1'
        self.__baseUrl = '{i}:{p}'.format(i=ip.strip('/'), p=port.strip('/'))

        self.__externNameToLiasonMap = dict()

        self.__fCloudHandler =  FileOnCloudHandler(self.__baseUrl, self.__checkSumAlgoName)

    def getCheckSumAlgoName(self):
        return self.__fCloudHandler.getCheckSumAlgoName()

    def registerLiason(self, shortName, url):
        # Params: shortName eg 'Job'
        #         url eg '/jobTable/jobHandler'
        # Explanation: + Creates a name mangled dbLiason, and then creates the respective rest handlers as
        #                defined in static dict '__restConnectorMethods' and creates their '*Conn' connectors
        #              + Eg self.updateWorkers, self.deleteWorkers, self.getWorkers, etc that you will invoke
        #                externally.
        # Returns the created handler

        liasonName = '__%sLiason'%(shortName.lower())
        setattr(self, liasonName, self.__createLiason(url))
        self.__externNameToLiasonMap[shortName] = getattr(self, liasonName)

        for restMethod, symNameTuple in self.__restConnectorMethods.items():
            symName, nameSuffix = symNameTuple
            setattr(
                self, '%s%s%s'%(symName, shortName, nameSuffix),
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

    def downloadBlobToStream(self, key, chunkSize=1024):
        return self.__fCloudHandler.downloadBlobToBuffer(self.___keyToDocCloudName(key), chunkSize)

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

def cliParser():
    parser = OptionParser()
    parser.add_option('-i', '--ip', default='http://127.0.0.1', help='Port server is on', dest='ip')
    parser.add_option('-p', '--port', default='8000', help='IP address db connects to', dest='port')

    return parser.parse_args()

#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>
# Code to bootstrap any project that intends to use restAssured as the backend API
# Will enable generation of related handlers

import os
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
getDefaultAuthor = lambda: os.environ.get('USER', 'Anonymous')

def produceAndParse(func, **dataIn):
    dbCheck = func(**dataIn)
    if  hasattr(dbCheck, 'get') and isCallable(dbCheck.get):
        response = dbCheck.get('value', None)
        try:
            outValue = json.loads(response.decode())
            outValue['status_code'] = dbCheck.get('status_code', 200)
            return outValue
        except Exception as e:
            return dict(reason=str(e), status_code=500)
    else:
        return dbCheck

class RestDriver:
    __restConnectorMethods = {
        'put': ('update', 's',), 'post': ('new', '',), 'delete': ('delete', 's'), 'get': ('get', 's',)
    }
    def __init__(self, ip, port, checkSumAlgoName='sha1'):
        self.__checkSumAlgoName = checkSumAlgoName or 'sha1'
        self.__baseUrl = '{i}:{p}'.format(i=ip.strip('/'), p=port.strip('/'))

        self.__externNameToLiasonMap = dict()

        self.__fCloudHandler =  FileOnCloudHandler(self.__baseUrl, self.__checkSumAlgoName)

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

    def uploadFile(self, srcPath, **attrs):
        return self.__fCloudHandler.uploadFileByPath(srcPath, **attrs)

    def downloadFile(self, key, **attrs):
        return self.__fCloudHandler.downloadFileToDisk('documents/'+key, **attrs)

    def deleteFile(self, **attrs):
        return self.__fCloudHandler.deleteFileOnCloud(**attrs)

    def updateFile(self, key, **attrs):
        return self.__fCloudHandler.updateFileByPath(key, **attrs)

    def getCloudFilesManifest(self, **queryParams):
        return self.__fCloudHandler.getParsedManifest(queryParams)

    def setBaseUrl(self, newUrl):
        self.__baseUrl = newUrl

    def getBaseUrl(self):
        return self.__baseUrl

    def jsonParseResponse(self, reqResponse):
        return self.__fCloudHandler.jsonParseResponse(reqResponse)

def cliParser():
    parser = OptionParser()
    parser.add_option('-i', '--ip', default='http://127.0.0.1', help='Port server is on', dest='ip')
    parser.add_option('-p', '--port', default='8000', help='IP address db connects to', dest='port')

    return parser.parse_args()

def main():
    args, options = cliParser()

    restDriver = RestDriver(args.ip, args.port)

    restDriver.registerLiason('Job', '/jobTable/jobHandler')
    restDriver.registerLiason('Worker', '/jobTable/workerHandler')

    print(restDriver.newWorker(name='SpeedBuggy', purpose='Individual Checks'))
    print(restDriver.newJob(
        message='TheStrokes-Someday', author=getDefaultAuthor(), assignedWorker_id=1
    ))

    print(restDriver.updateWorkers(
        queryParams=dict(name='SpeedBuggy'), updatesBody=dict(purpose='Crawling Speed checks')
    ))

    print('Updating', restDriver.updateJobs(
        queryParams=dict(message='TheStrokes-Someday'), updatesBody=dict(status='finished')
    ))

    print(restDriver.getCloudFilesManifest(select='size,checkSum'))
    print(restDriver.deleteJobs())
    print(restDriver.deleteWorkers())

    restDriver.registerLiason('Artist', '/thebear/artistHandler')
    print(restDriver.newArtist(name='Tester'))

if __name__ == '__main__':
    main()

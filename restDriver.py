#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import os
import sys
import json
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
            return dict(reason=str(e), status_code=200)
    else:
        return dbCheck

class RestDriver:
    def __init__(self, ip, port, checkSumAlgoName='sha1'):
        self.__checkSumAlgoName = checkSumAlgoName or 'sha1'
        self.__baseUrl = '{i}:{p}'.format(i=ip.strip('/'), p=port.strip('/'))
        self.__jobLiason = HandlerLiason(self.__baseUrl + '/jobTable/jobHandler')
        self.__workerLiason = HandlerLiason(self.__baseUrl + '/jobTable/workerHandler')
        self.__externNameToLiasonMap = dict(Job=self.__jobLiason, Worker=self.__workerLiason)

        self.__fCloudHandler =  FileOnCloudHandler(
            self.__baseUrl, self.__checkSumAlgoName
        )

        # Creating functions and table handlers
        self.newJob = self.__createLiasableFunc('Job', 'postConn')
        self.newWorker = self.__createLiasableFunc('Worker', 'postConn')

        self.getJobs = self.__createLiasableFunc('Job', 'getConn')
        self.getWorkers= self.__createLiasableFunc('Worker', 'getConn')

        self.updateJobs = self.__createLiasableFunc('Job', 'putConn')
        self.updateWorkers = self.__createLiasableFunc('Worker', 'putConn')

        self.deleteJobs = self.__createLiasableFunc('Job', 'deleteConn')
        self.deleteWorkers = self.__createLiasableFunc('Worker', 'deleteConn')

    def __createLiasableFunc(self, key, methodKey, **attrs):
        liason = self.__externNameToLiasonMap.get(key, None)
        method = getattr(liason, methodKey, None)
        if method is None:
            method = lambda **aux: aux
        return method

    def uploadFile(self, srcPath, **attrs):
        return self.__fCloudHandler.uploadFileByPath(srcPath, **attrs)

    def downloadFile(self, key, **attrs):
        return self.__fCloudHandler.downloadFileToDisk('documents/' + key)

    def deleteFile(self, **attrs):
        return self.__fCloudHandler.deleteFileOnCloud(**attrs)

    def updateFile(self, key, **attrs):
        return self.__fCloudHandler.updateFileByPath(key, **attrs)

    def getCloudFilesManifest(self, **queryParams):
        return self.__fCloudHandler.getParsedManifest(queryParams)

def cliParser():
    parser = OptionParser()
    parser.add_option('-i', '--ip', default='http://127.0.0.1', help='Port server is on', dest='ip')
    parser.add_option('-p', '--port', default='8000', help='IP address db connects to', dest='port')

    return parser.parse_args()

def main():
    args, options = cliParser()

    restDriver = RestDriver(args.ip, args.port)
    print(restDriver.newWorker(name='SpeedBuggy', purpose='Individual Checks'))
    print(restDriver.newJob(
        message='http://google.ca/someday', author=getDefaultAuthor(), assignedWorker_id=1
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

if __name__ == '__main__':
    main()

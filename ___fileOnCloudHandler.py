#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>
# Utility to enable file management on the cloud using restAssured

import os
import io
import sys
import mmap
import json
import hashlib

try:
    import requests
except ImportError:
    sys.stderr.write("\033[91mFirst install 'requests'\033[00m\n")
    sys.exit(-1)

try:
    from ___utils import getDefaultUserName, isCallableAttr
except:
    from .___utils import getDefaultUserName, isCallableAttr

isRegPath = lambda p: not os.path.isdir(p)

class FileOnCloudHandler:
    def __init__(self, url, checkSumAlgoName='md5'):
        self.setBaseURL(url)
        self.__checkSumAlgoName = checkSumAlgoName

        # Just an alias/reference
        self.downloadBlobToBuffer = self.downloadBlobToStream

    def setBaseURL(self, url):
        self.__baseUrl = url.strip('/')
        self.__upUrl = self.__baseUrl + '/uploader'
        self.__mediaUrl = self.__baseUrl + '/media/'

    def getBaseURL(self):
        return self.__baseUrl

    def initCheckSumAlgoName(self, algoName):
        self.__checkSumAlgoName = algoName

    def getCheckSumAlgoName(self):
        return self.__checkSumAlgoName

    def __pushUpFileByStream(self, isPut, stream, **attrs):
        if attrs.get('checkSum', None) is None:
            if isCallableAttr(hashlib, self.__checkSumAlgoName):
                try:
                    origPos = stream.tell()
                    checkSum = getattr(hashlib, self.__checkSumAlgoName)(stream.read()).hexdigest()
                    stream.seek(origPos) # Get back to originalPosition
                except Exception as e:
                    print('pushUpFilesByStream', e)
                else:
                    attrs['checkSum'] = checkSum

        attrs.setdefault('checkSumAlgoName', self.__checkSumAlgoName)
 
        method = requests.put if isPut else requests.post
        return self.___opHandler(method, self.__upUrl, data=attrs, files={'blob': stream})

    def __pushUpFileByPath(self, methodToggle, fPath, **attrs):
        response = None
        if fPath and os.path.exists(fPath) and os.access(fPath, os.R_OK):
            checkSumInfo = None
            with open(fPath, 'rb') as f:
                response = self.__pushUpFileByStream(methodToggle, f, **attrs)
       
            return response

    def uploadBlobByStream(self, f, **attrs):
        return self.__pushUpFileByStream(stream=f, **attrs)

    def uploadBlobByPath(self, fPath, **attrs):
        return self.__pushUpFileByPath(False, fPath, **attrs)

    def updateFileByStream(self, f, **attrs):
        return self.uploadBlobByStream(isPut=True, f=f, **attrs)

    def updateFileByPath(self, fPath, **attrs):
        return self.__pushUpFileByPath(True, fPath, **attrs)

    def __pathForMediaDownload(self, fPath):
        return self.__mediaUrl + fPath

    def __dlAndGetStream(self, fPath):
        formedUrl = self.__pathForMediaDownload(fPath)
        try:
            dataIn = requests.get(formedUrl, stream=True)
        except Exception as e:
            print('downloadBlobToStream', e)
        else:
            if dataIn.status_code == 200:
                return dataIn

    def downloadBlobToStream(self, fPath, readChunkSize=mmap.PAGESIZE):
        dataObj = self.__dlAndGetStream(fPath)
        if isCallableAttr(dataObj, 'iter_content'):
            return dataObj.iter_content(chunk_size=readChunkSize)

    def downloadBlobToDisk(self, pathOnCloudName, altName=None, chunkSize=mmap.PAGESIZE):
        chunkIterator = self.downloadBlobToStream(pathOnCloudName, chunkSize)
        writtenBytes = 0
        if isCallableAttr(chunkIterator, '__next__'):
            localName = altName or os.path.basename(pathOnCloudName)
            with open(localName, 'wb') as f:
                for chunk in chunkIterator:
                    if chunk:
                        writtenBytes += f.write(chunk)
                        f.flush()

        return writtenBytes

    def deleteBlobOnCloud(self, **attrsDict):
        return self.___opHandler(requests.delete, self.__upUrl, params=attrsDict)

    def ___opHandler(self, func, *args, **kwargs):
        res = None
        try:
            res = func(*args, **kwargs)
        except Exception as e:
            res = e

        return res

    def getManifest(self, queryDict={}):
        return self.___opHandler(requests.get, self.__upUrl, params=queryDict)

    def getParsedManifest(self, queryDict):
        return self.jsonParseResponse(self.getManifest(queryDict))

    def jsonParseResponse(self, reqResponse):
        if isinstance(reqResponse, Exception):
            return {'status_code': 500, 'reason': reqResponse}

        jsonParsed = dict()
        try:
            jsonParsed['data'] = json.loads(reqResponse.text).get('data', [])
        except Exception as e:
            print('Exception', e)
            jsonParsed['reason'] = str(e)
        finally:
            jsonParsed['status_code'] = reqResponse.status_code
            return jsonParsed

def main():
    argc = len(sys.argv)
    if argc < 2:
        sys.stderr.write('%s \033[42m<paths>\n\033[00m'%(__file__))
    else:
        fH = FileOnCloudHandler('http://127.0.0.1:8000', 'sha1')
        uploadFunc = lambda p: fH.uploadBlobByPath(
            p, author=getDefaultUserName(), title=p
        )
        for p in sys.argv[1:]:
            if not os.path.exists(p):
                print('Non existant path', p)
                continue
            elif os.path.isdir(p):
                for root, dirs, paths in os.walk(p):
                    joinedPaths = map(lambda p: os.path.join(root, p), paths)
                    dlResponse = map(uploadFunc, joinedPaths)
                    print(list(dlResponse))
            else:
                print(uploadFunc(p))
       
        print(fH.getManifest(dict(select='id')).text)
        # print(fH.deleteBlobOnCloud().text)

if __name__ == '__main__':
    main()

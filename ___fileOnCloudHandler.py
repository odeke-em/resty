#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>
# Utility to enable file management on the cloud using restAssured

import os
import io
import sys
import mmap
import json
import random
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

    def getCheckSum(self, byteStream, algoName=None):
        if not isCallableAttr(hashlib, algoName or self.__checkSumAlgoName):
            return 400, 'No such algo exists'
        try:
            checkSumObj = getattr(hashlib, self.__checkSumAlgoName)(byteStream)
        except Exception as e:
            return 500, e
        else:
            return 200, checkSumObj

    def __pushUpFileByStream(self, isPut, stream, **attrs):
        if attrs.get('checkSum', None) is None:
            try:
                origPos = stream.tell()
                status, result = self.getCheckSum(stream.read())
                if status != 200:
                    return result 
            except Exception as e:
                print('pushUpFilesByStream', e)
                return e
            else:
                stream.seek(origPos) # Get back to originalPosition
                attrs['checkSum'] = result.hexdigest()

        attrs.setdefault('checkSumAlgoName', self.__checkSumAlgoName)

        if not isPut: 
            return self.___opHandler(
                requests.post, self.__upUrl, data=attrs, files={'blob': stream}
            )
        else:
            resp = requests.Response()
            resp.status_code = 405
            resp.reason = 'Unimplemented'
            return resp

    def __pushUpFileByPath(self, methodToggle, fPath, **attrs):
        response = None
        if fPath and os.path.exists(fPath) and os.access(fPath, os.R_OK):
            checkSumInfo = None
            with open(fPath, 'rb') as f:
                attrs['stream'] = f
                attrs['isPut'] = methodToggle
                response = self.__pushUpFileByStream(**attrs)
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

    def getManifest(self, **query):
        return self.___opHandler(requests.get, self.__upUrl, params=query)

    def getParsedManifest(self, **query):
        return self.jsonParseResponse(self.getManifest(**query))

    def jsonParseResponse(self, reqResponse):
        if isinstance(reqResponse, Exception):
            return {'status_code': 500, 'reason': reqResponse}

        jsonParsed = dict()
        try:
            jsonParsed['data'] = reqResponse.json().get('data', [])
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
        digest = bytes('%s%f'%(__file__, random.random()), encoding='utf-8')

        status, checkSumObj = fH.getCheckSum(digest)

        assert status == 200, "Failed to create checkSum"
        sessionTag = checkSumObj.hexdigest()

        uploadFunc = lambda p: fH.uploadBlobByPath(
            p, author=getDefaultUserName(), title=p, metaData=sessionTag
        )

        updateFunc = lambda p: fH.updateFileByPath(
            p, author=getDefaultUserName(), title=p, metaData=sessionTag
        )

        manifest = fH.getParsedManifest()
        print('File manifest', manifest)

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
       
        print(fH.getParsedManifest(select='id'))
        print(fH.deleteBlobOnCloud(metaData=sessionTag).text)

if __name__ == '__main__':
    main()

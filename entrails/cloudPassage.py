#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import io
import sys
import time
import pickle
import hashlib

import restDriver
import Serializer
import httpStatusCodes as httpStatus

class CloudPassageHandler:
    def __init__(self, addr='http://127.0.0.1', port='8000'):
        self.___mapAddrToDriver = {}
        self.__restDriver = self.addDriver(addr, port)

        self.__checkSumFunc = self.__restDriver.getCheckSum
        self.__jsonSerializer = Serializer.JSONSerializer()
        self.__pickleSerializer = Serializer.BinarySerializer()

    def addDriver(self, host, port):
        hostMap = self.___mapAddrToDriver.setdefault(host, {})
        retr = hostMap.get(port, None)
        if not isinstance(retr, restDriver.RestDriver):
            retr = restDriver.RestDriver(host, port)
            print('\033[92mFresh restDriver at host: %s port: %s\033[00m'%(
                                                                      host, port))
            hostMap[port] = retr

        return retr

    def computeCheckSum(self, selector, data):
        return self.__checkSumFunc(
                      selector.preHasher(selector.serialize(data))).hexdigest()

    def __selectSerializer(self, asPickle):
        if asPickle:
            return self.__pickleSerializer, 'pickle'

        return self.__jsonSerializer, 'json'

    def push(self, rawObject, asPickle=False, **kwargs):
        selector, sType = self.__selectSerializer(asPickle)

        # We maintain uniqueness
        checkSum = self.computeCheckSum(selector, rawObject)

        status, retr = self.__manifestPull(checkSum=checkSum, metaData=sType, **kwargs)
        stream = selector.ioStream(rawObject)
        kwargs.setdefault('uri', 'Computation@%s'%(time.time()))
        func = self.__restDriver.uploadStream
        if status == httpStatus.OK and retr:
            func = self.__restDriver.updateStream

        return func(stream, checkSum=checkSum, metaData=sType, **kwargs)

    def removeTrace(self, rawObj, asPickle=False, **kwargs):
        selector, sType = self.__selectSerializer(asPickle)
        checkSum = self.computeCheckSum(selector, rawObj)

        return self.__restDriver.deleteBlob(checkSum=checkSum, metaData=sType)

    def removeByParams(self, **q):
        return self.__restDriver.deleteBlob(**q)

    def pull(self, **queryMap):
        # Returns the deserialized object essentially the 'live object'
        status, data = self.__manifestPull(**queryMap)
        if status != httpStatus.OK:
            return

        keyName = data.get('content', None)
        if not keyName:
            return
        stream = self.__restDriver.downloadBlobToStream(keyName)
        if not (stream and Serializer.isCallableAttr(stream, '__next__')):
            return
        
        metaType = data.get('metaData', None)

        selector = None
        if metaType == 'json': 
            selector = self.__jsonSerializer
        elif metaType == 'pickle':
            selector = self.__pickleSerializer

        # Guess we've got to load it all into memory
        try:
            buf = stream.__next__() # Since we don't know the type
            for chunk in stream:
                buf += chunk
        except StopIteration as e:
            buf = None
        except Exception as e:
            sys.stderr.write('%s'%(e))
        finally:
            if selector and buf is not None:
                return selector.deserialize(buf)

    def __manifestPull(self, **identifiers):
        # Returns <errCode>, <data>
        manifest = self.__restDriver.getCloudFilesManifest(**identifiers)
        status = manifest.get('status_code', httpStatus.BAD_REQUEST)

        if status != httpStatus.OK:
            return status, manifest
        retr = manifest.get('data', None)
        if retr:
            headItem = retr[0]
            return httpStatus.OK, headItem

        return httpStatus.NOT_FOUND, manifest

    def manifestPull(self, **q):
        return self.__manifestPull(**q)

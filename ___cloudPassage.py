#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import io
import time
import pickle
import hashlib

import restDriver
import Serializer

class CloudPassageHandler:
    def __init__(self, addr='http://127.0.0.1', port='8000'):
        self.___mapAddrToDriver = {}
        self.__restDriver = self.addDriver(addr, port)

        self.__checkSumFunc = self.getCheckSumFunc()
        self.__jsonSerializer = Serializer.JSONSerializer()
        self.__pickleSerializer = Serializer.BinarySerializer()

    def addDriver(self, host, port):
        hostMap = self.___mapAddrToDriver.setdefault(host, {})
        retr = hostMap.get(port, None)
        if not isinstance(retr, restDriver.RestDriver):
            retr = restDriver.RestDriver(host, port)
            print('\033[92mFresh restDriver at host: %s port: %s\033[00m'%(host, port))
            hostMap[port] = retr

        return retr

    def getCheckSumFunc(self):
        return getattr(hashlib, self.__restDriver.getCheckSumAlgoName(), None)

    def computeCheckSum(self, selector, data):
        return self.__checkSumFunc(selector.preHasher(selector.serialize(data))).hexdigest()

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
        if status == 200 and retr:
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
        if status == 200:
            keyName = data.get('content', None)
            if keyName:
                stream = self.__restDriver.downloadBlobToStream(keyName)
                if stream and Serializer.isCallable(stream.read):
                    metaType = data.get('metaData', None)

                    selector = None
                    if metaType == 'json': 
                        selector = self.__jsonSerializer
                    elif metaType == 'pickle':
                        selector = self.__pickleSerializer

                    if selector:
                        return selector.deserialize(stream.read())

    def __manifestPull(self, **identifiers):
        # Returns <errCode>, <data>
        manifest = self.__restDriver.getCloudFilesManifest(**identifiers)
        status = manifest.get('status_code', 400)

        if status != 200:
            return status, manifest
        else:
            retr = manifest.get('data', None)
            if retr:
                headItem = retr[0]
                return 200, headItem

            return 404, manifest

    def manifestPull(self, **q):
        return self.__manifestPull(**q)
